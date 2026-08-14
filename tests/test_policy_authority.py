from __future__ import annotations

from dataclasses import replace
import sqlite3

import pytest

from nova_aegis import (
    BoundaryPreflightReport,
    LocalSyntheticPolicyAuthority,
    LocalSyntheticIdentityRegistry,
    LocalSyntheticPolicyKeyProvider,
    PolicyApproval,
    PolicyAuthorityError,
    SQLiteSyntheticIdentityRegistry,
)


class StaticPolicyKeys:
    def __init__(self, keys: dict[str, bytes], active_key: str | None) -> None:
        self._keys = keys
        self._active_key = active_key

    def get(self, key_id: str) -> bytes | None:
        return self._keys.get(key_id)

    def active(self) -> tuple[str, bytes] | None:
        if self._active_key is None:
            return None
        return self._active_key, self._keys[self._active_key]


def _authority() -> tuple[LocalSyntheticPolicyAuthority, BoundaryPreflightReport, PolicyApproval]:
    keys = StaticPolicyKeys({"policy-1": b"policy-secret"}, "policy-1")
    identities = LocalSyntheticIdentityRegistry({"signer-1", "reviewer-1"})
    authority = LocalSyntheticPolicyAuthority(keys, identities)
    report = BoundaryPreflightReport("local-witness", "CONTINUE_SYNTHETIC", (), False)
    approval = PolicyApproval("approval-1", "local-witness", "CONTINUE_SYNTHETIC", "reviewer-1")
    return authority, report, approval


def test_policy_authority_binds_distinct_signer_and_approver() -> None:
    authority, report, approval = _authority()
    release = authority.issue(report, approval, signer_id="signer-1")

    authority.verify(release, report, approval)
    assert release.signer_id != release.approver_id
    assert release.production_enabled is False


def test_policy_authority_rejects_self_approval_and_mismatched_approval() -> None:
    authority, report, approval = _authority()
    with pytest.raises(PolicyAuthorityError, match="distinct"):
        authority.issue(report, approval, signer_id="reviewer-1")

    mismatched = replace(approval, decision="REFACTOR")
    with pytest.raises(PolicyAuthorityError, match="match"):
        authority.issue(report, mismatched, signer_id="signer-1")


def test_policy_authority_rejects_revoked_or_tampered_release() -> None:
    authority, report, approval = _authority()
    release = authority.issue(report, approval, signer_id="signer-1")
    authority.revoke_approval(approval.approval_id)
    with pytest.raises(PolicyAuthorityError, match="revoked"):
        authority.verify(release, report, approval)

    authority, report, approval = _authority()
    release = authority.issue(report, approval, signer_id="signer-1")
    forged = replace(release, decision="REFACTOR")
    with pytest.raises(PolicyAuthorityError, match="signature"):
        authority.verify(forged, report, approval)


def test_policy_authority_rejects_production_release_and_missing_key() -> None:
    authority, report, approval = _authority()
    with pytest.raises(PolicyAuthorityError, match="production"):
        authority.issue(
            replace(report, production_enabled=True),
            replace(approval, production_enabled=True),
            signer_id="signer-1",
        )

    no_key_authority = LocalSyntheticPolicyAuthority(
        StaticPolicyKeys({}, None), LocalSyntheticIdentityRegistry({"signer-1", "reviewer-1"})
    )
    with pytest.raises(PolicyAuthorityError, match="active"):
        no_key_authority.issue(report, approval, signer_id="signer-1")


def test_policy_authority_rejects_unknown_and_revoked_identities() -> None:
    keys = StaticPolicyKeys({"policy-1": b"policy-secret"}, "policy-1")
    identities = LocalSyntheticIdentityRegistry({"signer-1", "reviewer-1"})
    authority = LocalSyntheticPolicyAuthority(keys, identities)
    report = BoundaryPreflightReport("local-witness", "CONTINUE_SYNTHETIC", (), False)
    approval = PolicyApproval("approval-1", "local-witness", "CONTINUE_SYNTHETIC", "reviewer-1")

    with pytest.raises(PolicyAuthorityError, match="signer identity"):
        authority.issue(report, approval, signer_id="unknown-signer")

    release = authority.issue(report, approval, signer_id="signer-1")
    identities.revoke("reviewer-1")
    with pytest.raises(PolicyAuthorityError, match="approver identity"):
        authority.verify(release, report, approval)


def test_identity_registry_rejects_re_registration_after_revocation() -> None:
    identities = LocalSyntheticIdentityRegistry()
    identities.register("reviewer-1")
    identities.revoke("reviewer-1")

    with pytest.raises(PolicyAuthorityError, match="cannot be registered"):
        identities.register("reviewer-1")


def test_sqlite_identity_registry_replays_lifecycle_after_reopen(tmp_path) -> None:
    database_path = tmp_path / "identities.sqlite"
    connection = sqlite3.connect(database_path)
    identities = SQLiteSyntheticIdentityRegistry(connection)
    identities.register("signer-1")
    identities.register("reviewer-1")
    connection.close()

    replay_connection = sqlite3.connect(database_path)
    replay_identities = SQLiteSyntheticIdentityRegistry(replay_connection)
    assert replay_identities.is_active("signer-1") is True
    assert replay_identities.is_active("reviewer-1") is True


def test_sqlite_identity_registry_revocation_is_terminal() -> None:
    connection = sqlite3.connect(":memory:")
    identities = SQLiteSyntheticIdentityRegistry(connection)
    identities.register("reviewer-1")
    identities.revoke("reviewer-1")

    assert identities.is_active("reviewer-1") is False
    with pytest.raises(PolicyAuthorityError, match="cannot be registered"):
        identities.register("reviewer-1")

def test_policy_key_rotation_signs_with_successor_and_retirement_rejects_old_key() -> None:
    keys = LocalSyntheticPolicyKeyProvider({"policy-1": b"old"})
    identities = LocalSyntheticIdentityRegistry({"signer-1", "reviewer-1"})
    authority = LocalSyntheticPolicyAuthority(keys, identities)
    report = BoundaryPreflightReport("local-witness", "CONTINUE_SYNTHETIC", (), False)
    approval = PolicyApproval("approval-1", "local-witness", "CONTINUE_SYNTHETIC", "reviewer-1")

    first = authority.issue(report, approval, signer_id="signer-1")
    keys.rotate("policy-2", b"new", authority="synthetic-policy-key-admin")
    successor = authority.issue(report, replace(approval, approval_id="approval-2"), signer_id="signer-1")
    authority.verify(successor, report, replace(approval, approval_id="approval-2"))
    assert first.key_id == "policy-1"
    assert successor.key_id == "policy-2"

    keys.retire("policy-1", authority="synthetic-policy-key-admin")
    with pytest.raises(PolicyAuthorityError, match="not trusted"):
        authority.verify(first, report, approval)

def test_policy_key_lifecycle_requires_synthetic_rotation_authority() -> None:
    keys = LocalSyntheticPolicyKeyProvider({"policy-1": b"old"})
    with pytest.raises(PolicyAuthorityError, match="authority"):
        keys.rotate("policy-2", b"new", authority="unknown")
    with pytest.raises(PolicyAuthorityError, match="active"):
        keys.retire("policy-1", authority="synthetic-policy-key-admin")
