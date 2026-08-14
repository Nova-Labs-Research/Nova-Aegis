"""Synthetic signed boundary decisions for local governance experiments."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import sqlite3
from typing import Any, Mapping, Protocol

from .boundary_preflight import BoundaryPreflightReport


class BoundaryDecisionKeyProvider(Protocol):
    def get(self, key_id: str) -> bytes | None: ...

    def active(self) -> tuple[str, bytes] | None: ...


class BoundaryDecisionError(RuntimeError):
    """Raised when a signed boundary decision cannot be trusted locally."""


@dataclass(frozen=True)
class SignedBoundaryDecision:
    boundary: str
    decision: str
    blockers: tuple[str, ...]
    production_enabled: bool
    key_id: str
    signature: str

    def payload(self) -> dict[str, Any]:
        return {
            "boundary": self.boundary,
            "decision": self.decision,
            "blockers": self.blockers,
            "production_enabled": self.production_enabled,
            "key_id": self.key_id,
        }

    @classmethod
    def from_report(
        cls,
        report: BoundaryPreflightReport,
        key_provider: BoundaryDecisionKeyProvider,
    ) -> SignedBoundaryDecision:
        active = key_provider.active()
        if active is None:
            raise BoundaryDecisionError("Boundary decision requires an active signing key")
        key_id, secret = active
        unsigned = cls(
            report.boundary,
            report.decision,
            report.blockers,
            report.production_enabled,
            key_id,
            "",
        )
        return cls(
            boundary=unsigned.boundary,
            decision=unsigned.decision,
            blockers=unsigned.blockers,
            production_enabled=unsigned.production_enabled,
            key_id=unsigned.key_id,
            signature=_sign(unsigned.payload(), secret),
        )

    def verify(
        self,
        report: BoundaryPreflightReport,
        key_provider: BoundaryDecisionKeyProvider,
    ) -> None:
        secret = key_provider.get(self.key_id)
        if secret is None:
            raise BoundaryDecisionError("Boundary decision signing key is not trusted")
        if not hmac.compare_digest(self.signature, _sign(self.payload(), secret)):
            raise BoundaryDecisionError("Boundary decision signature is invalid")
        expected = (
            report.boundary,
            report.decision,
            report.blockers,
            report.production_enabled,
        )
        actual = (
            self.boundary,
            self.decision,
            self.blockers,
            self.production_enabled,
        )
        if actual != expected:
            raise BoundaryDecisionError("Boundary decision does not match preflight report")
        if self.production_enabled or self.decision == "CONTINUE_PRODUCTION":
            raise BoundaryDecisionError("Boundary decision cannot enable production")


class SQLiteBoundaryDecisionStore:
    """Append-only local decision events for synthetic replay experiments."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS boundary_decision_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                boundary TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def register(self, decision: SignedBoundaryDecision) -> None:
        current = self._current(decision.boundary)
        if current is not None and current != decision:
            raise BoundaryDecisionError("Boundary decision has conflicting content")
        if current == decision:
            return
        self._connection.execute(
            "INSERT INTO boundary_decision_events(boundary, event_type, payload) VALUES (?, ?, ?)",
            (decision.boundary, "register", _decision_payload(decision)),
        )
        self._connection.commit()

    def revoke(self, boundary: str) -> None:
        if self._current(boundary) is None:
            raise BoundaryDecisionError("Boundary decision is not registered")
        if self._is_revoked(boundary):
            return
        self._connection.execute(
            "INSERT INTO boundary_decision_events(boundary, event_type, payload) VALUES (?, ?, ?)",
            (boundary, "revoke", "{}"),
        )
        self._connection.commit()

    def supersede(
        self,
        previous_boundary: str,
        successor: SignedBoundaryDecision,
    ) -> None:
        current = self._current(previous_boundary)
        if current is None:
            raise BoundaryDecisionError("Boundary decision is not registered")
        if self._is_revoked(previous_boundary):
            raise BoundaryDecisionError("revoked boundary decision cannot be superseded")
        if successor.boundary != previous_boundary:
            raise BoundaryDecisionError("Boundary decision successor does not match boundary")
        if successor == current:
            raise BoundaryDecisionError("Boundary decision successor must change content")
        self._connection.execute(
            "INSERT INTO boundary_decision_events(boundary, event_type, payload) VALUES (?, ?, ?)",
            (previous_boundary, "supersede", _decision_payload(successor)),
        )
        self._connection.commit()

    def replay(
        self,
        boundary: str,
        report: BoundaryPreflightReport,
        key_provider: BoundaryDecisionKeyProvider,
    ) -> SignedBoundaryDecision:
        decision = self._current(boundary)
        if decision is None:
            raise BoundaryDecisionError("Boundary decision is not registered")
        if self._is_revoked(boundary):
            raise BoundaryDecisionError("Boundary decision is revoked")
        decision.verify(report, key_provider)
        return decision

    def _current(self, boundary: str) -> SignedBoundaryDecision | None:
        rows = self._connection.execute(
            "SELECT event_type, payload FROM boundary_decision_events WHERE boundary = ? ORDER BY event_id",
            (boundary,),
        ).fetchall()
        current: SignedBoundaryDecision | None = None
        for event_type, payload in rows:
            if event_type in {"register", "supersede"}:
                current = _decision_from_payload(payload)
        return current

    def _is_revoked(self, boundary: str) -> bool:
        row = self._connection.execute(
            "SELECT 1 FROM boundary_decision_events WHERE boundary = ? AND event_type = 'revoke' LIMIT 1",
            (boundary,),
        ).fetchone()
        return row is not None


def _decision_payload(decision: SignedBoundaryDecision) -> str:
    return json.dumps(
        {**decision.payload(), "signature": decision.signature},
        sort_keys=True,
        separators=(",", ":"),
    )


def _decision_from_payload(payload: str) -> SignedBoundaryDecision:
    try:
        value = json.loads(payload)
        return SignedBoundaryDecision(
            boundary=str(value["boundary"]),
            decision=str(value["decision"]),
            blockers=tuple(str(blocker) for blocker in value["blockers"]),
            production_enabled=bool(value["production_enabled"]),
            key_id=str(value["key_id"]),
            signature=str(value["signature"]),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise BoundaryDecisionError("Boundary decision event is malformed") from error


def _sign(payload: Mapping[str, Any], secret: bytes) -> str:
    serialized = json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hmac.new(secret, serialized, hashlib.sha256).hexdigest()
