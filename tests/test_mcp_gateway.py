from __future__ import annotations

from dataclasses import replace

from nova_aegis import (
    IdentityAuthority,
    McpGateway,
    McpToolDescriptor,
    Praetor,
    ToolPolicy,
)


RESOURCE_URI = "https://gateway.nova-aegis.local/mcp"
SCOPE = "mcp:tool:synthetic-status-update"
READ_SCOPE = "mcp:tool:diagnostic-read"


def gateway_setup():
    identity = IdentityAuthority(secret=b"mcp-gateway-identity-secret")
    policy = ToolPolicy(
        tool_name="synthetic_status_update",
        allowed_roles=frozenset({"operator"}),
        allowed_targets=frozenset({"service-a"}),
        allowed_values=frozenset({"restart", "status"}),
    )
    praetor = Praetor(tool_policies={policy.tool_name: policy})
    executions: list[dict[str, str]] = []

    def handler(parameters):
        result = {"tool": "synthetic_status_update", **dict(parameters)}
        executions.append(result)
        return result

    from nova_aegis import AuditLog

    audit = AuditLog()
    gateway = McpGateway(
        resource_uri=RESOURCE_URI,
        identity_authority=identity,
        praetor=praetor,
        audit_log=audit,
        tools={
            policy.tool_name: McpToolDescriptor(
                name=policy.tool_name,
                required_scope=SCOPE,
                allowed_parameters=frozenset({"target", "value"}),
                handler=handler,
            ),
            "diagnostic_read": McpToolDescriptor(
                name="diagnostic_read",
                required_scope=READ_SCOPE,
                allowed_parameters=frozenset({"target", "value"}),
                handler=handler,
            ),
        },
        secret=b"mcp-gateway-token-secret",
    )
    credential = identity.issue("operator-01", "operator")
    return identity, gateway, audit, credential, executions


def issue_tool_token(gateway, credential):
    return gateway.issue_token(
        credential,
        audience=RESOURCE_URI,
        scopes=frozenset({SCOPE}),
    )


def test_gateway_executes_authorized_scoped_request_and_audits() -> None:
    _, gateway, audit, credential, executions = gateway_setup()
    token = issue_tool_token(gateway, credential)

    result = gateway.invoke(
        access_token=token,
        tool_name="synthetic_status_update",
        parameters={"target": "service-a", "value": "restart"},
    )

    assert result["assurance"] == "PASS"
    assert result["result"]["target"] == "service-a"
    assert len(executions) == 1
    assert audit.events[-1]["event_type"] == "mcp_tool_executed"
    assert audit.events[-1]["audience"] == RESOURCE_URI
    assert audit.events[-1]["scopes"] == [SCOPE]


def test_gateway_rejects_wrong_audience_token() -> None:
    _, gateway, audit, credential, executions = gateway_setup()
    token = issue_tool_token(gateway, credential)
    wrong_audience = replace(token, audience="https://other.example/mcp")

    result = gateway.invoke(
        access_token=wrong_audience,
        tool_name="synthetic_status_update",
        parameters={"target": "service-a", "value": "restart"},
    )

    assert result["assurance"] == "FAIL"
    assert "audience" in result["warning"]
    assert executions == []
    assert audit.events[-1]["event_type"] == "mcp_request_blocked"


def test_gateway_rejects_missing_scope_and_unknown_schema_field() -> None:
    _, gateway, audit, credential, executions = gateway_setup()
    narrow_token = gateway.issue_token(
        credential,
        audience=RESOURCE_URI,
        scopes=frozenset({READ_SCOPE}),
    )
    token = issue_tool_token(gateway, credential)

    scope_result = gateway.invoke(
        access_token=narrow_token,
        tool_name="synthetic_status_update",
        parameters={"target": "service-a", "value": "restart"},
    )
    schema_result = gateway.invoke(
        access_token=token,
        tool_name="synthetic_status_update",
        parameters={"target": "service-a", "value": "restart", "admin": "true"},
    )

    assert scope_result["assurance"] == "FAIL"
    assert "scope" in scope_result["warning"]
    assert schema_result["assurance"] == "FAIL"
    assert "schema" in schema_result["warning"]
    assert executions == []
    assert [event["event_type"] for event in audit.events] == [
        "mcp_request_blocked",
        "mcp_request_blocked",
    ]


def test_gateway_revalidates_revoked_identity_on_every_request() -> None:
    identity, gateway, audit, credential, executions = gateway_setup()
    token = issue_tool_token(gateway, credential)
    identity.revoke(credential)

    result = gateway.invoke(
        access_token=token,
        tool_name="synthetic_status_update",
        parameters={"target": "service-a", "value": "restart"},
    )

    assert result["assurance"] == "FAIL"
    assert "identity is invalid" in result["warning"]
    assert executions == []
    assert audit.events[-1]["event_type"] == "mcp_request_blocked"


def test_gateway_discovery_is_limited_by_role_and_unknown_tools_are_blocked() -> None:
    identity, gateway, audit, credential, executions = gateway_setup()
    reader = identity.issue("reader-01", "reader")
    token = issue_tool_token(gateway, credential)

    assert gateway.discover_tools(reader) == ()
    result = gateway.invoke(
        access_token=token,
        tool_name="unregistered_tool",
        parameters={"target": "service-a", "value": "restart"},
    )

    assert result["assurance"] == "FAIL"
    assert "not registered" in result["warning"]
    assert executions == []
    assert audit.events[-1]["event_type"] == "mcp_request_blocked"
