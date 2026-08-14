"""Synthetic policy-authority and approval binding experiments."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import sqlite3
from typing import Any, Mapping, Protocol

from .boundary_preflight import BoundaryPreflightReport


class PolicyAuthorityKeyProvider(Protocol):
    def get(self, key_id: str) -> bytes | None: ...
    def rotate(self, key_id: str, secret: bytes, *, authority: str) -> None: ...
    def retire(self, key_id: str, *, authority: str) -> None: ...

    def active(self) -> tuple[str, bytes] | None: ...


class PolicyIdentityRegistry(Protocol):
    def is_active(self, identity_id: str) -> bool: ...


class PolicyAuthorityError(RuntimeError):
    """Raised when a synthetic policy release cannot be trusted."""


class LocalSyntheticPolicyKeyProvider:
    """Process-local policy key lifecycle for synthetic rotation experiments."""

    def __init__(
        self,
        keys: dict[str, bytes] | None = None,
        *,
        active_key_id: str | None = None,
        rotation_authority: str = "synthetic-policy-key-admin",
    ) -> None:
        self._keys = {key_id: bytes(secret) for key_id, secret in (keys or {}).items()}
        self._active_key_id = active_key_id or (next(iter(self._keys)) if self._keys else None)
        self._rotation_authority = rotation_authority
        if self._active_key_id is not None and self._active_key_id not in self._keys:
            raise PolicyAuthorityError("Active policy key is not trusted")

    def get(self, key_id: str) -> bytes | None:
        return self._keys.get(key_id)

    def active(self) -> tuple[str, bytes] | None:
        if self._active_key_id is None:
            return None
        return self._active_key_id, self._keys[self._active_key_id]

    def rotate(self, key_id: str, secret: bytes, *, authority: str) -> None:
        self._require_authority(authority)
        if not key_id.strip() or not secret:
            raise PolicyAuthorityError("Policy key rotation requires a key ID and secret")
        self._keys[key_id] = bytes(secret)
        self._active_key_id = key_id

    def retire(self, key_id: str, *, authority: str) -> None:
        self._require_authority(authority)
        if key_id == self._active_key_id:
            raise PolicyAuthorityError("Cannot retire the active policy key")
        self._keys.pop(key_id, None)

    def _require_authority(self, authority: str) -> None:
        if authority != self._rotation_authority:
            raise PolicyAuthorityError("Policy key lifecycle authority is invalid")


class LocalSyntheticIdentityRegistry:
    """Process-local identity registry for synthetic authority experiments."""

    def __init__(self, identities: set[str] | None = None) -> None:
        self._active: set[str] = set(identities or ())
        self._revoked: set[str] = set()

    def register(self, identity_id: str) -> None:
        if not identity_id.strip() or identity_id in self._revoked:
            raise PolicyAuthorityError("Policy identity cannot be registered")
        self._active.add(identity_id)

    def revoke(self, identity_id: str) -> None:
        if not identity_id.strip() or identity_id not in self._active:
            raise PolicyAuthorityError("Policy identity is not registered")
        self._active.remove(identity_id)
        self._revoked.add(identity_id)

    def is_active(self, identity_id: str) -> bool:
        return identity_id in self._active


class SQLiteSyntheticIdentityRegistry:
    """Append-only local identity lifecycle events for synthetic replay."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS policy_identity_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                identity_id TEXT NOT NULL,
                event_type TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def register(self, identity_id: str) -> None:
        if not identity_id.strip():
            raise PolicyAuthorityError("Policy identity cannot be registered")
        if self.is_active(identity_id) or self._is_revoked(identity_id):
            raise PolicyAuthorityError("Policy identity cannot be registered")
        self._connection.execute(
            "INSERT INTO policy_identity_events(identity_id, event_type) VALUES (?, ?)",
            (identity_id, "register"),
        )
        self._connection.commit()

    def revoke(self, identity_id: str) -> None:
        if not identity_id.strip() or not self.is_active(identity_id):
            raise PolicyAuthorityError("Policy identity is not registered")
        self._connection.execute(
            "INSERT INTO policy_identity_events(identity_id, event_type) VALUES (?, ?)",
            (identity_id, "revoke"),
        )
        self._connection.commit()

    def is_active(self, identity_id: str) -> bool:
        row = self._connection.execute(
            "SELECT event_type FROM policy_identity_events WHERE identity_id = ? ORDER BY event_id DESC LIMIT 1",
            (identity_id,),
        ).fetchone()
        return row is not None and row[0] == "register"

    def _is_revoked(self, identity_id: str) -> bool:
        row = self._connection.execute(
            "SELECT 1 FROM policy_identity_events WHERE identity_id = ? AND event_type = 'revoke' LIMIT 1",
            (identity_id,),
        ).fetchone()
        return row is not None


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

    def __init__(
        self,
        key_provider: PolicyAuthorityKeyProvider,
        identity_registry: PolicyIdentityRegistry,
    ) -> None:
        self._key_provider = key_provider
        self._identity_registry = identity_registry
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
        self._validate_identities(signer_id, approval.approver_id)
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
        self._validate_identities(release.signer_id, release.approver_id)
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

    def _validate_identities(self, signer_id: str, approver_id: str) -> None:
        if not self._identity_registry.is_active(signer_id):
            raise PolicyAuthorityError("Policy signer identity is unknown or revoked")
        if not self._identity_registry.is_active(approver_id):
            raise PolicyAuthorityError("Policy approver identity is unknown or revoked")


def _sign(payload: Mapping[str, Any], secret: bytes) -> str:
    serialized = json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hmac.new(secret, serialized, hashlib.sha256).hexdigest()
