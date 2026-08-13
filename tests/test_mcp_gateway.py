from __future__ import annotations

from dataclasses import replace

from nova_aegis import (
    IdentityAuthority,
    McpGateway,
    McpGatewayRequest,
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


def stateless_request(gateway, token, *, parameters=None, meta=None):
    parameters = parameters or {"target": "service-a", "value": "restart"}
    return McpGatewayRequest(
        method="tools/call",
        name="synthetic_status_update",
        parameters=parameters,
        task_state=gateway.create_task_state(
            access_token=token,
            tool_name="synthetic_status_update",
            parameters=parameters,
        ),
        meta=meta,
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


def test_stateless_gateway_validates_signed_task_state_and_ignores_safe_meta() -> None:
    _, gateway, audit, credential, executions = gateway_setup()
    token = issue_tool_token(gateway, credential)
    request = stateless_request(gateway, token, meta={"client_hint": "untrusted"})

    result = gateway.invoke_stateless(
        access_token=token,
        headers={"Mcp-Method": "tools/call", "Mcp-Name": "synthetic_status_update"},
        request=request,
    )

    assert result["assurance"] == "PASS"
    assert len(executions) == 1
    assert audit.events[-1]["event_type"] == "mcp_tool_executed"


def test_stateless_gateway_rejects_tampered_task_state_and_operation_change() -> None:
    _, gateway, audit, credential, executions = gateway_setup()
    token = issue_tool_token(gateway, credential)
    request = stateless_request(gateway, token)
    altered_parameters = McpGatewayRequest(
        method=request.method,
        name=request.name,
        parameters={"target": "service-a", "value": "status"},
        task_state=request.task_state,
    )

    result = gateway.invoke_stateless(
        access_token=token,
        headers={"Mcp-Method": "tools/call", "Mcp-Name": "synthetic_status_update"},
        request=altered_parameters,
    )

    assert result["assurance"] == "FAIL"
    assert "task state does not match" in result["warning"]
    assert executions == []
    assert audit.events[-1]["event_type"] == "mcp_request_blocked"


def test_stateless_gateway_rejects_header_body_desync_and_authorization_meta() -> None:
    _, gateway, audit, credential, executions = gateway_setup()
    token = issue_tool_token(gateway, credential)
    request = stateless_request(gateway, token)

    desync = gateway.invoke_stateless(
        access_token=token,
        headers={"Mcp-Method": "tools/call", "Mcp-Name": "diagnostic_read"},
        request=request,
    )
    poisoned_meta = gateway.invoke_stateless(
        access_token=token,
        headers={"Mcp-Method": "tools/call", "Mcp-Name": "synthetic_status_update"},
        request=McpGatewayRequest(
            method=request.method,
            name=request.name,
            parameters=request.parameters,
            task_state=request.task_state,
            meta={"role": "admin"},
        ),
    )

    assert desync["assurance"] == "FAIL"
    assert "routing fields do not match" in desync["warning"]
    assert poisoned_meta["assurance"] == "FAIL"
    assert "_meta cannot supply identity" in poisoned_meta["warning"]
    assert executions == []
    assert [event["event_type"] for event in audit.events] == [
        "mcp_request_blocked",
        "mcp_request_blocked",
    ]
