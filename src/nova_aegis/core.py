"""Dependency-free vertical slice for the Nova Aegis MVP.

The implementation deliberately keeps retrieval, assurance, execution, and audit
as separate objects so the security path is visible and directly testable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import re
import sqlite3
import secrets
import time
from uuid import uuid4
from typing import Any, Callable, Iterable, Mapping


class AssuranceStatus(str, Enum):
    PASS = "PASS"
    REVIEW = "REVIEW"
    FAIL = "FAIL"


class EvaluatorKind(str, Enum):
    DETERMINISTIC = "deterministic"
    SEMANTIC = "semantic"


class GovernanceUnavailable(RuntimeError):
    """Raised when a governed operation cannot obtain a Praetor decision."""


class AuditIntegrityError(RuntimeError):
    """Raised when a durable audit chain is missing or has been altered."""


class IdentityError(RuntimeError):
    """Raised when an identity credential is invalid or revoked."""


class PolicyIntegrityError(RuntimeError):
    """Raised when the loaded policy set no longer matches its fingerprint."""


@dataclass(frozen=True)
class Evidence:
    source_id: str
    title: str
    text: str
    revision_id: str = "unknown"
    authority: str = "unclassified"
    claim_group: str | None = None
    claim: str | None = None
    status: str = "current"
    provenance_verified: bool = False
    hierarchy: tuple[str, ...] = ()


@dataclass(frozen=True)
class Provenance:
    source_id: str
    title: str
    revision_id: str
    authority: str
    status: str
    provenance_verified: bool


@dataclass(frozen=True)
class Citation:
    source_id: str
    title: str
    excerpt: str
    retrieval_score: int
    provenance: Provenance
    claim_group: str | None = None
    claim: str | None = None


@dataclass(frozen=True)
class RetrievalTrace:
    question: str
    authority_scope: tuple[str, ...]
    hierarchy_scope: tuple[str, ...]
    candidate_source_ids: tuple[str, ...]
    authority_filtered_source_ids: tuple[str, ...]
    hierarchy_filtered_source_ids: tuple[str, ...]
    ranked_source_ids: tuple[str, ...]
    ranked_scores: tuple[tuple[str, int], ...]
    selected_source_ids: tuple[str, ...]
    corpus_digest: str = ""
    trace_digest: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def canonical_payload(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("trace_digest", None)
        return payload

    def calculate_digest(self) -> str:
        serialized = json.dumps(
            self.canonical_payload(), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> RetrievalTrace:
        try:
            return cls(
                question=str(value["question"]),
                authority_scope=tuple(value["authority_scope"]),
                hierarchy_scope=tuple(value["hierarchy_scope"]),
                candidate_source_ids=tuple(value["candidate_source_ids"]),
                authority_filtered_source_ids=tuple(value["authority_filtered_source_ids"]),
                hierarchy_filtered_source_ids=tuple(value["hierarchy_filtered_source_ids"]),
                ranked_source_ids=tuple(value["ranked_source_ids"]),
                ranked_scores=tuple(
                    (str(source_id), int(score))
                    for source_id, score in value["ranked_scores"]
                ),
                selected_source_ids=tuple(value["selected_source_ids"]),
                corpus_digest=str(value.get("corpus_digest", "")),
                trace_digest=str(value.get("trace_digest", "")),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Retrieval trace has an invalid serialized shape") from error


@dataclass(frozen=True)
class Response:
    answer: str | None
    evidence: tuple[Citation, ...]
    assurance: AssuranceStatus
    warning: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "evidence": [asdict(citation) for citation in self.evidence],
            "assurance": self.assurance.value,
            "warning": self.warning,
        }


@dataclass(frozen=True)
class Decision:
    status: AssuranceStatus
    reason: str


@dataclass(frozen=True)
class EvaluationDecision:
    evaluator: EvaluatorKind
    status: AssuranceStatus
    reason: str


@dataclass(frozen=True)
class RuleEvaluation:
    rule_id: str
    status: AssuranceStatus
    reason: str


@dataclass(frozen=True)
class DeterministicTrace:
    decision: EvaluationDecision
    rules: tuple[RuleEvaluation, ...]


@dataclass(frozen=True)
class ExecutionReceipt:
    idempotency_key: str
    request_id: str
    tool: str
    target: str
    value: str
    user_id: str
    role: str
    status: str
    result: dict[str, str] | None


class AgentK:
    """Deterministic evidence evaluator with inspectable ordered rule results."""

    def evaluate(self, citations: tuple[Citation, ...]) -> EvaluationDecision:
        return self.evaluate_with_trace(citations).decision

    def evaluate_with_trace(self, citations: tuple[Citation, ...]) -> DeterministicTrace:
        rules = (
            RuleEvaluation(
                "AK-EVID-001",
                AssuranceStatus.REVIEW if not citations else AssuranceStatus.PASS,
                "No supporting evidence was retrieved" if not citations else "Evidence was retrieved",
            ),
            RuleEvaluation(
                "AK-PROV-001",
                AssuranceStatus.REVIEW
                if any(citation.provenance.authority == "unclassified" for citation in citations)
                else AssuranceStatus.PASS,
                "Evidence provenance is not classified"
                if any(citation.provenance.authority == "unclassified" for citation in citations)
                else "Evidence authority is classified",
            ),
            RuleEvaluation(
                "AK-REV-001",
                AssuranceStatus.REVIEW
                if any(citation.provenance.status != "current" for citation in citations)
                else AssuranceStatus.PASS,
                "Retrieved evidence is not current"
                if any(citation.provenance.status != "current" for citation in citations)
                else "Evidence is current",
            ),
            RuleEvaluation(
                "AK-PROV-002",
                AssuranceStatus.REVIEW
                if any(not citation.provenance.provenance_verified for citation in citations)
                else AssuranceStatus.PASS,
                "Evidence provenance could not be independently verified"
                if any(not citation.provenance.provenance_verified for citation in citations)
                else "Evidence provenance is verified",
            ),
            self._conflict_rule(citations),
        )
        blocking_rule = next((rule for rule in rules if rule.status is not AssuranceStatus.PASS), None)
        decision = EvaluationDecision(
            EvaluatorKind.DETERMINISTIC,
            blocking_rule.status if blocking_rule else AssuranceStatus.PASS,
            f"{blocking_rule.rule_id}: {blocking_rule.reason}"
            if blocking_rule
            else "Agent K evidence rules passed",
        )
        return DeterministicTrace(decision=decision, rules=rules)

    @staticmethod
    def _conflict_rule(citations: tuple[Citation, ...]) -> RuleEvaluation:
        claims_by_group: dict[str, set[str]] = {}
        for citation in citations:
            if citation.claim_group and citation.claim:
                claims_by_group.setdefault(citation.claim_group, set()).add(
                    citation.claim.strip().casefold()
                )
        if any(len(claims) > 1 for claims in claims_by_group.values()):
            return RuleEvaluation(
                "AK-CLAIM-001",
                AssuranceStatus.REVIEW,
                "Retrieved evidence contains unresolved conflicting claims",
            )
        return RuleEvaluation(
            "AK-CLAIM-001",
            AssuranceStatus.PASS,
            "No unresolved conflicting claims were found",
        )


class HybridAssurance:
    """Fuses independent semantic and deterministic evaluation conservatively."""

    def fuse(
        self,
        deterministic: EvaluationDecision,
        semantic: EvaluationDecision,
    ) -> Decision:
        if deterministic.evaluator is not EvaluatorKind.DETERMINISTIC:
            raise ValueError("Deterministic evaluation must identify its evaluator")
        if semantic.evaluator is not EvaluatorKind.SEMANTIC:
            raise ValueError("Semantic evaluation must identify its evaluator")
        if deterministic.status is AssuranceStatus.FAIL:
            return Decision(
                AssuranceStatus.FAIL,
                f"Deterministic governance blocked the decision: {deterministic.reason}",
            )
        if (
            deterministic.status is AssuranceStatus.PASS
            and semantic.status is AssuranceStatus.PASS
        ):
            return Decision(AssuranceStatus.PASS, "Independent evaluators agreed to PASS")
        return Decision(
            AssuranceStatus.REVIEW,
            "Independent evaluators did not jointly support PASS: "
            f"deterministic={deterministic.status.value}; "
            f"semantic={semantic.status.value}; "
            f"deterministic_reason={deterministic.reason}; "
            f"semantic_reason={semantic.reason}",
        )


@dataclass(frozen=True)
class AuthorizationContext:
    user_id: str
    role: str


@dataclass(frozen=True)
class IdentityCredential:
    token: str
    user_id: str
    role: str
    issued_at: int
    expires_at: int
    signature: str


class IdentityAuthority:
    """Synthetic server-side issuer and validator for authorization context."""

    def __init__(self, *, secret: bytes | None = None, lifetime_seconds: int = 300) -> None:
        if lifetime_seconds < 1:
            raise ValueError("Identity lifetime must be positive")
        self._secret = secret or secrets.token_bytes(32)
        self._lifetime_seconds = lifetime_seconds
        self._issued_tokens: set[str] = set()
        self._revoked_tokens: set[str] = set()

    def issue(self, user_id: str, role: str) -> IdentityCredential:
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("Identity user ID must be a non-empty string")
        if not isinstance(role, str) or not role.strip():
            raise ValueError("Identity role must be a non-empty string")
        issued_at = int(time.time())
        expires_at = issued_at + self._lifetime_seconds
        token = secrets.token_urlsafe(24)
        signature = self._sign(token, user_id, role, issued_at, expires_at)
        self._issued_tokens.add(token)
        return IdentityCredential(token, user_id, role, issued_at, expires_at, signature)

    def authenticate(self, credential: IdentityCredential) -> AuthorizationContext:
        if not isinstance(credential, IdentityCredential):
            raise IdentityError("Identity credential is invalid")
        now = int(time.time())
        if credential.token not in self._issued_tokens:
            raise IdentityError("Identity credential was not issued by this authority")
        if credential.token in self._revoked_tokens:
            raise IdentityError("Identity credential is revoked")
        if credential.expires_at <= now:
            raise IdentityError("Identity credential is expired")
        expected = self._sign(
            credential.token,
            credential.user_id,
            credential.role,
            credential.issued_at,
            credential.expires_at,
        )
        if not secrets.compare_digest(credential.signature, expected):
            raise IdentityError("Identity credential signature is invalid")
        return AuthorizationContext(user_id=credential.user_id, role=credential.role)

    def revoke(self, credential: IdentityCredential) -> None:
        if credential.token not in self._issued_tokens:
            raise IdentityError("Identity credential was not issued by this authority")
        self._revoked_tokens.add(credential.token)

    def _sign(self, token: str, user_id: str, role: str, issued_at: int, expires_at: int) -> str:
        payload = f"{token}|{user_id}|{role}|{issued_at}|{expires_at}".encode("utf-8")
        return hashlib.blake2b(payload, key=self._secret, digest_size=32).hexdigest()


@dataclass(frozen=True)
class ToolPolicy:
    tool_name: str
    allowed_roles: frozenset[str]
    allowed_targets: frozenset[str]
    allowed_values: frozenset[str]

    def evaluate(
        self,
        context: AuthorizationContext,
        parameters: Mapping[str, str],
    ) -> Decision:
        if context.role not in self.allowed_roles:
            return Decision(
                AssuranceStatus.FAIL,
                f"Role is not authorized for tool: {context.role}",
            )
        if parameters.get("target") not in self.allowed_targets:
            return Decision(
                AssuranceStatus.FAIL,
                f"Target is not authorized: {parameters.get('target')}",
            )
        if parameters.get("value") not in self.allowed_values:
            return Decision(
                AssuranceStatus.FAIL,
                f"Operation value is not authorized: {parameters.get('value')}",
            )
        return Decision(AssuranceStatus.PASS, "Tool, role, target, and operation are authorized")


def _policy_fingerprint(policies: Mapping[str, ToolPolicy]) -> str:
    serialized = [
        {
            "tool_name": name,
            "allowed_roles": sorted(policy.allowed_roles),
            "allowed_targets": sorted(policy.allowed_targets),
            "allowed_values": sorted(policy.allowed_values),
        }
        for name, policy in sorted(policies.items())
    ]
    return hashlib.sha256(
        json.dumps(serialized, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


class AuditLog:
    """Append-only in-memory audit log for the workstation MVP."""

    EVENT_TYPES = frozenset(
        {
            "request_received",
            "retrieval_completed",
            "response_proposed",
            "response_assured",
            "response_blocked",
            "tool_authorized",
            "tool_blocked",
            "tool_executed",
            "tool_recovery_required",
            "mcp_request_blocked",
            "mcp_tool_executed",
            "mcp_task_replay_returned",
            "mcp_task_created",
            "mcp_task_cancelled",
            "mcp_task_started",
            "mcp_task_lease_renewed",
            "mcp_task_failed",
            "mcp_task_recovery_required",
            "mcp_task_recovery_approved",
            "mcp_task_recovery_revoked",
            "mcp_task_recovery_replayed",
            "mcp_task_recovery_replay_blocked",
            "mcp_task_reconciled",
            "mcp_task_reconciliation_blocked",
        }
    )

    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []

    def append(self, event_type: str, **details: Any) -> None:
        if event_type not in self.EVENT_TYPES:
            raise ValueError(f"Unsupported audit event type: {event_type}")
        self._events.append(
            {
                "event_id": str(uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                **details,
            }
        )

    @property
    def events(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._events)

class SQLiteAuditLog:
    """Local durable audit log with a tamper-evident hash chain."""

    EVENT_TYPES = AuditLog.EVENT_TYPES
    _RESERVED_FIELDS = frozenset({"event_id", "timestamp", "event_type", "event_hash"})

    def __init__(self, database: str) -> None:
        self._connection = sqlite3.connect(database)
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                details_json TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                event_hash TEXT NOT NULL UNIQUE
            )
            """
        )
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS execution_receipts (
                idempotency_key TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                tool TEXT NOT NULL,
                target TEXT NOT NULL,
                value TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL,
                result_json TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
            """
        )
        self._connection.commit()

    def prepare_execution(
        self,
        *,
        idempotency_key: str,
        request_id: str,
        tool: str,
        target: str,
        value: str,
        user_id: str,
        role: str,
    ) -> tuple[ExecutionReceipt, bool]:
        if not isinstance(idempotency_key, str) or not idempotency_key.strip():
            raise ValueError("Execution idempotency key must be a non-empty string")
        existing = self.get_execution_receipt(idempotency_key)
        if existing is not None:
            if (existing.tool, existing.target, existing.value, existing.user_id) != (
                tool,
                target,
                value,
                user_id,
            ):
                raise ValueError("Execution idempotency key was reused for a different operation")
            return existing, False
        self._connection.execute(
            """
            INSERT INTO execution_receipts
                (idempotency_key, request_id, tool, target, value, user_id, role, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'authorized', ?)
            """,
            (
                idempotency_key,
                request_id,
                tool,
                target,
                value,
                user_id,
                role,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self._connection.commit()
        receipt = self.get_execution_receipt(idempotency_key)
        if receipt is None:
            raise AuditIntegrityError("Execution receipt could not be persisted")
        return receipt, True

    def complete_execution(
        self,
        idempotency_key: str,
        result: Mapping[str, str],
    ) -> ExecutionReceipt:
        receipt = self.get_execution_receipt(idempotency_key)
        if receipt is None:
            raise ValueError("Execution receipt does not exist")
        if receipt.status == "completed":
            return receipt
        self._connection.execute(
            """
            UPDATE execution_receipts
            SET status = 'completed', result_json = ?, completed_at = ?
            WHERE idempotency_key = ? AND status = 'authorized'
            """,
            (
                json.dumps(dict(result), sort_keys=True, separators=(",", ":")),
                datetime.now(timezone.utc).isoformat(),
                idempotency_key,
            ),
        )
        self._connection.commit()
        completed = self.get_execution_receipt(idempotency_key)
        if completed is None or completed.status != "completed":
            raise AuditIntegrityError("Execution receipt completion could not be persisted")
        return completed

    def get_execution_receipt(self, idempotency_key: str) -> ExecutionReceipt | None:
        row = self._connection.execute(
            """
            SELECT idempotency_key, request_id, tool, target, value, user_id, role, status, result_json
            FROM execution_receipts WHERE idempotency_key = ?
            """,
            (idempotency_key,),
        ).fetchone()
        if row is None:
            return None
        result_json = row[8]
        return ExecutionReceipt(
            *row[:8],
            json.loads(result_json) if result_json else None,
        )

    def pending_execution_receipts(self) -> tuple[ExecutionReceipt, ...]:
        rows = self._connection.execute(
            "SELECT idempotency_key FROM execution_receipts WHERE status = 'authorized' ORDER BY created_at"
        ).fetchall()
        return tuple(self.get_execution_receipt(row[0]) for row in rows if row)

    def append(self, event_type: str, **details: Any) -> None:
        if event_type not in self.EVENT_TYPES:
            raise ValueError(f"Unsupported audit event type: {event_type}")
        if self._RESERVED_FIELDS.intersection(details):
            raise ValueError("Audit details cannot overwrite reserved event fields")
        self.verify_integrity()
        event = {
            "event_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            **details,
        }
        details_json = json.dumps(details, sort_keys=True, separators=(",", ":"))
        previous_hash = self._connection.execute(
            "SELECT event_hash FROM audit_events ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
        previous_hash_value = previous_hash[0] if previous_hash else "GENESIS"
        event_hash = self._hash_event(
            event,
            details_json=details_json,
            previous_hash=previous_hash_value,
        )
        self._connection.execute(
            """
            INSERT INTO audit_events
                (event_id, timestamp, event_type, details_json, previous_hash, event_hash)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event["event_id"],
                event["timestamp"],
                event_type,
                details_json,
                previous_hash_value,
                event_hash,
            ),
        )
        self._connection.commit()

    @property
    def events(self) -> tuple[dict[str, Any], ...]:
        self.verify_integrity()
        rows = self._connection.execute(
            """
            SELECT event_id, timestamp, event_type, details_json, event_hash
            FROM audit_events ORDER BY sequence
            """
        ).fetchall()
        return tuple(
            {
                "event_id": event_id,
                "timestamp": timestamp,
                "event_type": event_type,
                **json.loads(details_json),
                "event_hash": event_hash,
            }
            for event_id, timestamp, event_type, details_json, event_hash in rows
        )

    def retrieval_traces(self) -> tuple[Mapping[str, Any], ...]:
        self.verify_integrity()
        traces: list[Mapping[str, Any]] = []
        for event in self.events:
            if event["event_type"] != "retrieval_completed":
                continue
            trace = event.get("retrieval_trace")
            if not isinstance(trace, Mapping):
                raise AuditIntegrityError("Retrieval audit event has no valid trace")
            traces.append(trace)
        return tuple(traces)

    def verify_integrity(self) -> None:
        rows = self._connection.execute(
            """
            SELECT event_id, timestamp, event_type, details_json, previous_hash, event_hash
            FROM audit_events ORDER BY sequence
            """
        ).fetchall()
        expected_previous_hash = "GENESIS"
        for row in rows:
            event_id, timestamp, event_type, details_json, previous_hash, event_hash = row
            if previous_hash != expected_previous_hash:
                raise AuditIntegrityError("Audit hash chain predecessor is invalid")
            event = {
                "event_id": event_id,
                "timestamp": timestamp,
                "event_type": event_type,
                **json.loads(details_json),
            }
            expected_hash = self._hash_event(
                event,
                details_json=details_json,
                previous_hash=previous_hash,
            )
            if event_hash != expected_hash:
                raise AuditIntegrityError("Audit event integrity verification failed")
            expected_previous_hash = event_hash

    @staticmethod
    def _hash_event(
        event: Mapping[str, Any],
        *,
        details_json: str,
        previous_hash: str,
    ) -> str:
        payload = json.dumps(
            {
                "event_id": event["event_id"],
                "timestamp": event["timestamp"],
                "event_type": event["event_type"],
                "details": details_json,
                "previous_hash": previous_hash,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def close(self) -> None:
        self._connection.close()


class LocalRetriever:
    """Simple local lexical retrieval over an approved document corpus."""

    _STOP_WORDS = frozenset(
        {
            "a",
            "an",
            "and",
            "does",
            "for",
            "is",
            "of",
            "the",
            "what",
        }
    )

    def __init__(self, documents: Iterable[Evidence]) -> None:
        self._documents = tuple(documents)

    @property
    def corpus_digest(self) -> str:
        serialized = json.dumps(
            [asdict(document) for document in sorted(self._documents, key=lambda item: item.source_id)],
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    def retrieve(self, question: str, limit: int = 3) -> tuple[Citation, ...]:
        citations, _ = self.retrieve_with_trace(question, limit=limit)
        return citations

    def retrieve_with_trace(
        self,
        question: str,
        limit: int = 3,
        *,
        authorities: Iterable[str] | None = None,
        hierarchy_prefix: Iterable[str] | None = None,
    ) -> tuple[tuple[Citation, ...], RetrievalTrace]:
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question must be a non-empty string")
        if limit < 1:
            raise ValueError("Retrieval limit must be positive")
        authority_scope = tuple(dict.fromkeys(authorities or ()))
        scope = tuple(hierarchy_prefix or ())
        question_terms = self._terms(question)
        candidate_source_ids = tuple(document.source_id for document in self._documents)
        authority_filtered = tuple(
            document
            for document in self._documents
            if not authority_scope or document.authority in authority_scope
        )
        hierarchy_filtered = tuple(
            document
            for document in authority_filtered
            if not scope or document.hierarchy[: len(scope)] == scope
        )
        ranked: list[tuple[int, Evidence]] = []
        for document in hierarchy_filtered:
            document_terms = self._terms(f"{document.title} {document.text}")
            score = len(question_terms & document_terms)
            if score:
                ranked.append((score, document))
        ranked.sort(key=lambda item: (-item[0], item[1].source_id))
        citations = tuple(
            Citation(
                source_id=document.source_id,
                title=document.title,
                excerpt=document.text,
                retrieval_score=score,
                provenance=Provenance(
                    source_id=document.source_id,
                    title=document.title,
                    revision_id=document.revision_id,
                    authority=document.authority,
                    status=document.status,
                    provenance_verified=document.provenance_verified,
                ),
                claim_group=document.claim_group,
                claim=document.claim,
            )
            for score, document in ranked[:limit]
        )
        trace = RetrievalTrace(
            question=question,
            authority_scope=authority_scope,
            hierarchy_scope=scope,
            candidate_source_ids=candidate_source_ids,
            authority_filtered_source_ids=tuple(
                document.source_id for document in authority_filtered
            ),
            hierarchy_filtered_source_ids=tuple(
                document.source_id for document in hierarchy_filtered
            ),
            ranked_source_ids=tuple(document.source_id for _, document in ranked),
            ranked_scores=tuple((document.source_id, score) for score, document in ranked),
            selected_source_ids=tuple(citation.source_id for citation in citations),
            corpus_digest=self.corpus_digest,
        )
        trace = RetrievalTrace(
            **{**trace.to_dict(), "trace_digest": trace.calculate_digest()}
        )
        return citations, trace

    def replay_trace(self, trace: RetrievalTrace | Mapping[str, Any]) -> tuple[Citation, ...]:
        expected = (
            RetrievalTrace.from_dict(trace) if isinstance(trace, Mapping) else trace
        )
        if not isinstance(expected, RetrievalTrace):
            raise ValueError("Retrieval trace must be a RetrievalTrace or mapping")
        if expected.corpus_digest != self.corpus_digest:
            raise AuditIntegrityError("Retrieval trace replay corpus identity does not match")
        if not expected.trace_digest or expected.trace_digest != expected.calculate_digest():
            raise AuditIntegrityError("Retrieval trace replay digest is invalid")
        citations, actual = self.retrieve_with_trace(
            expected.question,
            limit=max(1, len(expected.selected_source_ids)),
            authorities=expected.authority_scope,
            hierarchy_prefix=expected.hierarchy_scope,
        )
        if actual != expected:
            raise AuditIntegrityError("Retrieval trace replay does not match persisted trace")
        return citations

    @staticmethod
    def _terms(text: str) -> set[str]:
        return {
            term
            for term in re.findall(r"[a-z0-9]+", text.lower())
            if term not in LocalRetriever._STOP_WORDS
        }


class Praetor:
    """Deterministic assurance boundary for responses and tool proposals."""

    def __init__(
        self,
        available: bool = True,
        tool_policies: Mapping[str, ToolPolicy] | None = None,
        deterministic_evaluator: Callable[[tuple[Citation, ...]], EvaluationDecision] | None = None,
        semantic_evaluator: Callable[[tuple[Citation, ...]], EvaluationDecision] | None = None,
        agent_k: AgentK | None = None,
    ) -> None:
        self.available = available
        self.tool_policies = dict(
            tool_policies
            or {
                "synthetic_status_update": ToolPolicy(
                    tool_name="synthetic_status_update",
                    allowed_roles=frozenset({"default", "operator"}),
                    allowed_targets=frozenset({"service-a"}),
                    allowed_values=frozenset({"restart", "status"}),
                )
            }
        )
        self._policy_fingerprint = _policy_fingerprint(self.tool_policies)
        self.agent_k = agent_k or AgentK()
        self._deterministic_evaluator = (
            deterministic_evaluator or self.agent_k.evaluate
        )
        self._semantic_evaluator = semantic_evaluator or self._default_semantic_evaluator
        self.hybrid_assurance = HybridAssurance()

    def evaluate_response(self, citations: tuple[Citation, ...]) -> Decision:
        _, _, decision = self.evaluate_response_with_trace(citations)
        return decision

    def evaluate_response_with_trace(
        self,
        citations: tuple[Citation, ...],
    ) -> tuple[EvaluationDecision, EvaluationDecision, Decision]:
        self._require_available()
        deterministic = self._run_response_evaluator(
            self._deterministic_evaluator,
            EvaluatorKind.DETERMINISTIC,
            citations,
        )
        semantic = self._run_response_evaluator(
            self._semantic_evaluator,
            EvaluatorKind.SEMANTIC,
            citations,
        )
        return deterministic, semantic, self.hybrid_assurance.fuse(deterministic, semantic)

    @staticmethod
    def _default_semantic_evaluator(
        citations: tuple[Citation, ...],
    ) -> EvaluationDecision:
        return EvaluationDecision(
            EvaluatorKind.SEMANTIC,
            AssuranceStatus.PASS,
            "Synthetic semantic evaluator found no additional concern",
        )

    @staticmethod
    def _run_response_evaluator(
        evaluator: Callable[[tuple[Citation, ...]], EvaluationDecision],
        expected_kind: EvaluatorKind,
        citations: tuple[Citation, ...],
    ) -> EvaluationDecision:
        try:
            decision = evaluator(citations)
        except Exception as error:
            return EvaluationDecision(
                expected_kind,
                AssuranceStatus.REVIEW,
                f"{expected_kind.value.capitalize()} evaluator is unavailable: {error}",
            )
        if not isinstance(decision, EvaluationDecision) or decision.evaluator is not expected_kind:
            return EvaluationDecision(
                expected_kind,
                AssuranceStatus.REVIEW,
                f"{expected_kind.value.capitalize()} evaluator returned an invalid decision",
            )
        return decision

    def authorize_tool(
        self,
        tool_name: str,
        authorized_tools: frozenset[str],
        *,
        context: AuthorizationContext,
        parameters: Mapping[str, str],
    ) -> Decision:
        self._require_available()
        self.verify_policy_integrity()
        if tool_name not in authorized_tools:
            return Decision(
                AssuranceStatus.FAIL,
                f"Tool is not authorized: {tool_name}",
            )
        policy = self.tool_policies.get(tool_name)
        if policy is None:
            return Decision(AssuranceStatus.FAIL, f"No policy is defined for tool: {tool_name}")
        return policy.evaluate(context, parameters)

    def verify_policy_integrity(self) -> None:
        if _policy_fingerprint(self.tool_policies) != self._policy_fingerprint:
            raise PolicyIntegrityError("Loaded tool policy integrity verification failed")

    def _require_available(self) -> None:
        if not self.available:
            raise GovernanceUnavailable("Praetor is unavailable; authorization is unavailable")


class SyntheticTool:
    """Safe test operation used to prove governed execution behavior."""

    name = "synthetic_status_update"

    def __init__(self) -> None:
        self.executions: list[dict[str, str]] = []

    def execute(self, target: str, value: str) -> dict[str, str]:
        result = {"tool": self.name, "target": target, "value": value}
        self.executions.append(result)
        return result


class NovaAegisMVP:
    """Coordinates the local retrieval, response assurance, tool, and audit flow."""

    def __init__(
        self,
        documents: Iterable[Evidence],
        *,
        praetor: Praetor | None = None,
        identity_authority: IdentityAuthority | None = None,
        audit_log: AuditLog | None = None,
        synthetic_tool: SyntheticTool | None = None,
    ) -> None:
        self.retriever = LocalRetriever(documents)
        self.praetor = praetor or Praetor()
        self.identity_authority = identity_authority or IdentityAuthority()
        self.audit_log = audit_log or AuditLog()
        self.synthetic_tool = synthetic_tool or SyntheticTool()

    def answer(self, question: str) -> dict[str, Any]:
        request_id = str(uuid4())
        self.audit_log.append("request_received", request_id=request_id, question=question)
        citations, retrieval_trace = self.retriever.retrieve_with_trace(question)
        self.audit_log.append(
            "retrieval_completed",
            request_id=request_id,
            source_ids=[citation.source_id for citation in citations],
            retrieval_trace=asdict(retrieval_trace),
        )
        proposed_answer = self._propose_answer(question, citations)
        self.audit_log.append(
            "response_proposed",
            request_id=request_id,
            has_answer=proposed_answer is not None,
        )
        try:
            deterministic, semantic, decision = self.praetor.evaluate_response_with_trace(citations)
        except GovernanceUnavailable as error:
            self.audit_log.append(
                "response_blocked",
                request_id=request_id,
                question=question,
                reason=str(error),
            )
            return Response(
                answer=None,
                evidence=citations,
                assurance=AssuranceStatus.REVIEW,
                warning=str(error),
            ).to_dict()

        response = Response(
            answer=proposed_answer if decision.status is AssuranceStatus.PASS else None,
            evidence=citations,
            assurance=decision.status,
            warning=None if decision.status is AssuranceStatus.PASS else decision.reason,
        )
        self.audit_log.append(
            "response_assured",
            request_id=request_id,
            question=question,
            assurance=decision.status.value,
            source_ids=[citation.source_id for citation in citations],
            deterministic_status=deterministic.status.value,
            deterministic_reason=deterministic.reason,
            semantic_status=semantic.status.value,
            semantic_reason=semantic.reason,
        )
        return response.to_dict()

    def execute_synthetic_tool(
        self,
        *,
        target: str,
        value: str,
        authorized_tools: frozenset[str] = frozenset(),
        user_id: str = "anonymous",
        role: str = "default",
        credential: IdentityCredential | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        request_id = str(uuid4())
        if not isinstance(target, str) or not target.strip():
            self.audit_log.append(
                "tool_blocked",
                request_id=request_id,
                tool=self.synthetic_tool.name,
                reason="Tool target must be a non-empty string",
            )
            raise ValueError("Tool target must be a non-empty string")
        if not isinstance(value, str) or not value.strip():
            self.audit_log.append(
                "tool_blocked",
                request_id=request_id,
                tool=self.synthetic_tool.name,
                target=target,
                reason="Tool value must be a non-empty string",
            )
            raise ValueError("Tool value must be a non-empty string")
        try:
            context = (
                self.identity_authority.authenticate(credential)
                if credential is not None
                else AuthorizationContext(user_id=user_id, role=role)
            )
            decision = self.praetor.authorize_tool(
                self.synthetic_tool.name,
                authorized_tools,
                context=context,
                parameters={"target": target, "value": value},
            )
        except (GovernanceUnavailable, IdentityError, PolicyIntegrityError) as error:
            self.audit_log.append(
                "tool_blocked",
                request_id=request_id,
                tool=self.synthetic_tool.name,
                target=target,
                user_id=user_id,
                role=role,
                reason=str(error),
            )
            if isinstance(error, GovernanceUnavailable):
                raise
            return {
                "result": None,
                "assurance": AssuranceStatus.FAIL.value,
                "warning": str(error),
            }

        if decision.status is not AssuranceStatus.PASS:
            self.audit_log.append(
                "tool_blocked",
                request_id=request_id,
                tool=self.synthetic_tool.name,
                target=target,
                user_id=context.user_id,
                role=context.role,
                assurance=decision.status.value,
                reason=decision.reason,
            )
            return {
                "result": None,
                "assurance": decision.status.value,
                "warning": decision.reason,
            }

        receipt: ExecutionReceipt | None = None
        if isinstance(self.audit_log, SQLiteAuditLog):
            receipt_key = idempotency_key or request_id
            receipt, created = self.audit_log.prepare_execution(
                idempotency_key=receipt_key,
                request_id=request_id,
                tool=self.synthetic_tool.name,
                target=target,
                value=value,
                user_id=context.user_id,
                role=context.role,
            )
            if not created:
                if receipt.status == "completed":
                    return {
                        "result": receipt.result,
                        "assurance": AssuranceStatus.PASS.value,
                        "warning": "Execution already completed for this idempotency key",
                    }
                self.audit_log.append(
                    "tool_recovery_required",
                    request_id=receipt.request_id,
                    tool=receipt.tool,
                    target=receipt.target,
                    idempotency_key=receipt.idempotency_key,
                    reason="Execution receipt is authorized but has no completion record",
                )
                return {
                    "result": None,
                    "assurance": AssuranceStatus.REVIEW.value,
                    "warning": "Execution recovery is required before retrying this operation",
                }

        try:
            self.audit_log.append(
                "tool_authorized",
                request_id=request_id,
                tool=self.synthetic_tool.name,
                target=target,
                user_id=context.user_id,
                role=context.role,
                assurance=decision.status.value,
                idempotency_key=receipt.idempotency_key if receipt else None,
            )
        except Exception as error:
            return {
                "result": None,
                "assurance": AssuranceStatus.FAIL.value,
                "warning": f"Audit authorization recording failed: {error}",
            }

        result = self.synthetic_tool.execute(target, value)
        try:
            if receipt is not None:
                receipt = self.audit_log.complete_execution(receipt.idempotency_key, result)
            self.audit_log.append(
                "tool_executed",
                request_id=request_id,
                tool=self.synthetic_tool.name,
                target=target,
                user_id=context.user_id,
                role=context.role,
                assurance=decision.status.value,
                idempotency_key=receipt.idempotency_key if receipt else None,
            )
        except Exception as error:
            try:
                self.audit_log.append(
                    "tool_recovery_required",
                    request_id=request_id,
                    tool=self.synthetic_tool.name,
                    target=target,
                    idempotency_key=receipt.idempotency_key if receipt else None,
                    reason=f"Execution completed but durable completion handling failed: {error}",
                )
            except Exception:
                pass
            return {
                "result": None,
                "assurance": AssuranceStatus.REVIEW.value,
                "warning": "Execution completed but recovery is required before reporting success",
            }
        return {
            "result": result,
            "assurance": decision.status.value,
            "warning": None,
        }

    @staticmethod
    def _propose_answer(question: str, citations: tuple[Citation, ...]) -> str | None:
        if not citations:
            return None
        evidence_text = " ".join(citation.excerpt for citation in citations)
        return f"Based on local evidence for '{question}': {evidence_text}"
