from __future__ import annotations

from dataclasses import replace

import pytest

from nova_aegis import (
    BoundaryPreflightReport,
    LocalSyntheticPolicyAuthority,
    LocalSyntheticIdentityRegistry,
    PolicyApproval,
    PolicyAuthorityError,
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
