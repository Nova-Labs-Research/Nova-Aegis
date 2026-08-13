from __future__ import annotations

from dataclasses import replace

from nova_aegis import (
    IdentityAuthority,
    IdentityError,
    NovaAegisMVP,
    Praetor,
    PolicyIntegrityError,
    ToolPolicy,
)


def test_server_issued_identity_authorizes_tool() -> None:
    authority = IdentityAuthority(secret=b"phase-9-test-secret")
    credential = authority.issue("operator-01", "operator")
    app = NovaAegisMVP([], identity_authority=authority)

    result = app.execute_synthetic_tool(
        target="service-a",
        value="restart",
        authorized_tools=frozenset({"synthetic_status_update"}),
        credential=credential,
    )

    assert result["assurance"] == "PASS"
    assert result["result"]["target"] == "service-a"
    assert app.audit_log.events[-1]["user_id"] == "operator-01"


def test_forged_identity_credential_fails_closed() -> None:
    authority = IdentityAuthority(secret=b"phase-9-test-secret")
    credential = authority.issue("operator-01", "operator")
    forged = replace(credential, role="admin")
    app = NovaAegisMVP([], identity_authority=authority)

    result = app.execute_synthetic_tool(
        target="service-a",
        value="restart",
        authorized_tools=frozenset({"synthetic_status_update"}),
        credential=forged,
    )

    assert result["assurance"] == "FAIL"
    assert "signature is invalid" in result["warning"]
    assert app.synthetic_tool.executions == []


def test_revoked_identity_cannot_execute() -> None:
    authority = IdentityAuthority(secret=b"phase-9-test-secret")
    credential = authority.issue("operator-01", "operator")
    authority.revoke(credential)
    app = NovaAegisMVP([], identity_authority=authority)

    result = app.execute_synthetic_tool(
        target="service-a",
        value="restart",
        authorized_tools=frozenset({"synthetic_status_update"}),
        credential=credential,
    )

    assert result["assurance"] == "FAIL"
    assert "revoked" in result["warning"]
    assert app.synthetic_tool.executions == []


def test_identity_authority_rejects_expired_credential() -> None:
    authority = IdentityAuthority(secret=b"phase-9-test-secret", lifetime_seconds=1)
    credential = authority.issue("operator-01", "operator")
    expired = replace(credential, expires_at=credential.issued_at)

    try:
        authority.authenticate(expired)
    except IdentityError as error:
        assert "expired" in str(error)
    else:
        raise AssertionError("Expired identity was accepted")


def test_policy_mutation_fails_closed_before_execution() -> None:
    app = NovaAegisMVP([])
    app.praetor.tool_policies["synthetic_status_update"] = ToolPolicy(
        tool_name="synthetic_status_update",
        allowed_roles=frozenset({"default"}),
        allowed_targets=frozenset({"service-b"}),
        allowed_values=frozenset({"restart"}),
    )

    result = app.execute_synthetic_tool(
        target="service-a",
        value="restart",
        authorized_tools=frozenset({"synthetic_status_update"}),
    )

    assert result["assurance"] == "FAIL"
    assert "integrity verification failed" in result["warning"]
    assert app.synthetic_tool.executions == []


def test_direct_praetor_policy_integrity_check_detects_mutation() -> None:
    policy = ToolPolicy(
        tool_name="synthetic_status_update",
        allowed_roles=frozenset({"operator"}),
        allowed_targets=frozenset({"service-a"}),
        allowed_values=frozenset({"restart"}),
    )
    praetor = Praetor(tool_policies={policy.tool_name: policy})
    praetor.tool_policies[policy.tool_name] = ToolPolicy(
        tool_name=policy.tool_name,
        allowed_roles=frozenset({"admin"}),
        allowed_targets=policy.allowed_targets,
        allowed_values=policy.allowed_values,
    )

    try:
        praetor.verify_policy_integrity()
    except PolicyIntegrityError as error:
        assert "integrity verification failed" in str(error)
    else:
        raise AssertionError("Mutated policy was accepted")
