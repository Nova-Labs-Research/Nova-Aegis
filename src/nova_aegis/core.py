"""Dependency-free vertical slice for the Nova Aegis MVP.

The implementation deliberately keeps retrieval, assurance, execution, and audit
as separate objects so the security path is visible and directly testable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
import re
from uuid import uuid4
from typing import Any, Iterable


class AssuranceStatus(str, Enum):
    PASS = "PASS"
    REVIEW = "REVIEW"
    FAIL = "FAIL"


class GovernanceUnavailable(RuntimeError):
    """Raised when a governed operation cannot obtain a Praetor decision."""


@dataclass(frozen=True)
class Evidence:
    source_id: str
    title: str
    text: str
    revision_id: str = "unknown"
    authority: str = "unclassified"


@dataclass(frozen=True)
class Provenance:
    source_id: str
    title: str
    revision_id: str
    authority: str


@dataclass(frozen=True)
class Citation:
    source_id: str
    title: str
    excerpt: str
    retrieval_score: int
    provenance: Provenance


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


class AuditLog:
    """Append-only in-memory audit log for the workstation MVP."""

    EVENT_TYPES = frozenset(
        {
            "request_received",
            "retrieval_completed",
            "response_proposed",
            "response_assured",
            "response_blocked",
            "tool_blocked",
            "tool_executed",
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

    def retrieve(self, question: str, limit: int = 3) -> tuple[Citation, ...]:
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question must be a non-empty string")
        if limit < 1:
            raise ValueError("Retrieval limit must be positive")
        question_terms = self._terms(question)
        ranked: list[tuple[int, Evidence]] = []
        for document in self._documents:
            document_terms = self._terms(f"{document.title} {document.text}")
            score = len(question_terms & document_terms)
            if score:
                ranked.append((score, document))
        ranked.sort(key=lambda item: (-item[0], item[1].source_id))
        return tuple(
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
                ),
            )
            for score, document in ranked[:limit]
        )

    @staticmethod
    def _terms(text: str) -> set[str]:
        return {
            term
            for term in re.findall(r"[a-z0-9]+", text.lower())
            if term not in LocalRetriever._STOP_WORDS
        }


class Praetor:
    """Deterministic assurance boundary for responses and tool proposals."""

    def __init__(self, available: bool = True) -> None:
        self.available = available

    def evaluate_response(self, citations: tuple[Citation, ...]) -> Decision:
        self._require_available()
        if not citations:
            return Decision(AssuranceStatus.REVIEW, "No supporting evidence was retrieved")
        return Decision(AssuranceStatus.PASS, "Response has local supporting evidence")

    def authorize_tool(self, tool_name: str, authorized_tools: frozenset[str]) -> Decision:
        self._require_available()
        if tool_name not in authorized_tools:
            return Decision(
                AssuranceStatus.FAIL,
                f"Tool is not authorized: {tool_name}",
            )
        return Decision(AssuranceStatus.PASS, "Tool is authorized for this request")

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
        audit_log: AuditLog | None = None,
        synthetic_tool: SyntheticTool | None = None,
    ) -> None:
        self.retriever = LocalRetriever(documents)
        self.praetor = praetor or Praetor()
        self.audit_log = audit_log or AuditLog()
        self.synthetic_tool = synthetic_tool or SyntheticTool()

    def answer(self, question: str) -> dict[str, Any]:
        request_id = str(uuid4())
        self.audit_log.append("request_received", request_id=request_id, question=question)
        citations = self.retriever.retrieve(question)
        self.audit_log.append(
            "retrieval_completed",
            request_id=request_id,
            source_ids=[citation.source_id for citation in citations],
        )
        proposed_answer = self._propose_answer(question, citations)
        self.audit_log.append(
            "response_proposed",
            request_id=request_id,
            has_answer=proposed_answer is not None,
        )
        try:
            decision = self.praetor.evaluate_response(citations)
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
        )
        return response.to_dict()

    def execute_synthetic_tool(
        self,
        *,
        target: str,
        value: str,
        authorized_tools: frozenset[str] = frozenset(),
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
            decision = self.praetor.authorize_tool(
                self.synthetic_tool.name,
                authorized_tools,
            )
        except GovernanceUnavailable as error:
            self.audit_log.append(
                "tool_blocked",
                request_id=request_id,
                tool=self.synthetic_tool.name,
                target=target,
                reason=str(error),
            )
            raise

        if decision.status is not AssuranceStatus.PASS:
            self.audit_log.append(
                "tool_blocked",
                request_id=request_id,
                tool=self.synthetic_tool.name,
                target=target,
                assurance=decision.status.value,
                reason=decision.reason,
            )
            return {
                "result": None,
                "assurance": decision.status.value,
                "warning": decision.reason,
            }

        result = self.synthetic_tool.execute(target, value)
        self.audit_log.append(
            "tool_executed",
            request_id=request_id,
            tool=self.synthetic_tool.name,
            target=target,
            assurance=decision.status.value,
        )
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
