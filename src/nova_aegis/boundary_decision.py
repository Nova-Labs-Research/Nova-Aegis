"""Synthetic signed boundary decisions for local governance experiments."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
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


def _sign(payload: Mapping[str, Any], secret: bytes) -> str:
    serialized = json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hmac.new(secret, serialized, hashlib.sha256).hexdigest()
