"""Synthetic policy-authority and approval binding experiments."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
from typing import Any, Mapping, Protocol

from .boundary_preflight import BoundaryPreflightReport


class PolicyAuthorityKeyProvider(Protocol):
    def get(self, key_id: str) -> bytes | None: ...

    def active(self) -> tuple[str, bytes] | None: ...


class PolicyAuthorityError(RuntimeError):
    """Raised when a synthetic policy release cannot be trusted."""


@dataclass(frozen=True)
class PolicyApproval:
    approval_id: str
    boundary: str
    decision: str
    approver_id: str
    production_enabled: bool = False

    def payload(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "boundary": self.boundary,
            "decision": self.decision,
            "approver_id": self.approver_id,
            "production_enabled": self.production_enabled,
        }


@dataclass(frozen=True)
class SignedPolicyRelease:
    boundary: str
    decision: str
    signer_id: str
    approver_id: str
    approval_id: str
    production_enabled: bool
    key_id: str
    signature: str

    def payload(self) -> dict[str, Any]:
        return {
            "boundary": self.boundary,
            "decision": self.decision,
            "signer_id": self.signer_id,
            "approver_id": self.approver_id,
            "approval_id": self.approval_id,
            "production_enabled": self.production_enabled,
            "key_id": self.key_id,
        }


class LocalSyntheticPolicyAuthority:
    """Injected local authority used only to test approval separation."""

    def __init__(self, key_provider: PolicyAuthorityKeyProvider) -> None:
        self._key_provider = key_provider
        self._revoked_approvals: set[str] = set()

    def issue(
        self,
        report: BoundaryPreflightReport,
        approval: PolicyApproval,
        *,
        signer_id: str,
    ) -> SignedPolicyRelease:
        if not signer_id.strip() or not approval.approver_id.strip():
            raise PolicyAuthorityError("Policy signer and approver identities are required")
        if signer_id == approval.approver_id:
            raise PolicyAuthorityError("Policy signer and approver must be distinct")
        self._validate_approval(report, approval)
        if approval.production_enabled or report.production_enabled:
            raise PolicyAuthorityError("Policy release cannot enable production")
        active = self._key_provider.active()
        if active is None:
            raise PolicyAuthorityError("Policy release requires an active signing key")
        key_id, secret = active
        unsigned = SignedPolicyRelease(
            report.boundary,
            report.decision,
            signer_id,
            approval.approver_id,
            approval.approval_id,
            False,
            key_id,
            "",
        )
        return SignedPolicyRelease(
            **{**unsigned.__dict__, "signature": _sign(unsigned.payload(), secret)}
        )

    def revoke_approval(self, approval_id: str) -> None:
        if not approval_id.strip():
            raise ValueError("Policy approval ID is required")
        self._revoked_approvals.add(approval_id)

    def verify(
        self,
        release: SignedPolicyRelease,
        report: BoundaryPreflightReport,
        approval: PolicyApproval,
    ) -> None:
        if release.approval_id in self._revoked_approvals:
            raise PolicyAuthorityError("Policy approval is revoked")
        secret = self._key_provider.get(release.key_id)
        if secret is None:
            raise PolicyAuthorityError("Policy release signing key is not trusted")
        if not hmac.compare_digest(release.signature, _sign(release.payload(), secret)):
            raise PolicyAuthorityError("Policy release signature is invalid")
        self._validate_approval(report, approval)
        if release.boundary != report.boundary or release.decision != report.decision:
            raise PolicyAuthorityError("Policy release does not match preflight report")
        if release.approver_id != approval.approver_id or release.signer_id == release.approver_id:
            raise PolicyAuthorityError("Policy release approval identities are invalid")
        if release.approval_id != approval.approval_id:
            raise PolicyAuthorityError("Policy release approval does not match")
        if release.production_enabled or approval.production_enabled or report.production_enabled:
            raise PolicyAuthorityError("Policy release cannot enable production")

    @staticmethod
    def _validate_approval(
        report: BoundaryPreflightReport,
        approval: PolicyApproval,
    ) -> None:
        if approval.boundary != report.boundary or approval.decision != report.decision:
            raise PolicyAuthorityError("Policy approval does not match preflight report")
        if not approval.approval_id.strip():
            raise PolicyAuthorityError("Policy approval ID is required")


def _sign(payload: Mapping[str, Any], secret: bytes) -> str:
    serialized = json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hmac.new(secret, serialized, hashlib.sha256).hexdigest()
