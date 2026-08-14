from __future__ import annotations

from dataclasses import replace

import pytest
import threading

from nova_aegis import (
    IdentityAuthority,
    LocalExternalReceiptRegistry,
    McpGateway,
    McpGatewayError,
    McpGatewayRequest,
    McpToolDescriptor,
    Praetor,
    SQLiteTaskStore,
    ToolPolicy,
)


RESOURCE_URI = "https://gateway.nova-aegis.local/mcp"
SCOPE = "mcp:tool:synthetic-status-update"
READ_SCOPE = "mcp:tool:diagnostic-read"


def gateway_setup(
    max_active_tasks_per_user=2,
    handler_override=None,
    identity_authority=None,
    task_store=None,
    receipt_verifier=None,
):
    identity = identity_authority or IdentityAuthority(secret=b"mcp-gateway-identity-secret")
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

    selected_handler = handler_override or handler

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
                handler=selected_handler,
            ),
            "diagnostic_read": McpToolDescriptor(
                name="diagnostic_read",
                required_scope=READ_SCOPE,
                allowed_parameters=frozenset({"target", "value"}),
                handler=selected_handler,
            ),
        },
        secret=b"mcp-gateway-token-secret",
        max_active_tasks_per_user=max_active_tasks_per_user,
        task_store=task_store,
        receipt_verifier=receipt_verifier,
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
    assert [event["event_type"] for event in audit.events[-2:]] == [
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
    assert [event["event_type"] for event in audit.events[-2:]] == [
        "mcp_request_blocked",
        "mcp_request_blocked",
    ]


def test_stateless_gateway_returns_stored_result_without_replaying_task() -> None:
    _, gateway, audit, credential, executions = gateway_setup()
    token = issue_tool_token(gateway, credential)
    request = stateless_request(gateway, token)
    headers = {"Mcp-Method": "tools/call", "Mcp-Name": "synthetic_status_update"}

    first = gateway.invoke_stateless(
        access_token=token,
        headers=headers,
        request=request,
    )
    replay = gateway.invoke_stateless(
        access_token=token,
        headers=headers,
        request=request,
    )

    assert first["assurance"] == "PASS"
    assert replay["assurance"] == "PASS"
    assert replay["result"] == first["result"]
    assert "already completed" in replay["warning"]
    assert len(executions) == 1
    assert audit.events[-1]["event_type"] == "mcp_task_replay_returned"


def test_gateway_enforces_per_user_active_task_quota() -> None:
    _, gateway, audit, credential, _ = gateway_setup(max_active_tasks_per_user=1)
    token = issue_tool_token(gateway, credential)
    parameters = {"target": "service-a", "value": "restart"}

    first = gateway.create_task_state(
        access_token=token,
        tool_name="synthetic_status_update",
        parameters=parameters,
    )

    with pytest.raises(McpGatewayError, match="quota is exhausted"):
        gateway.create_task_state(
            access_token=token,
            tool_name="synthetic_status_update",
            parameters=parameters,
        )

    assert gateway.task_status(first) == "pending"
    assert audit.events[-1]["event_type"] == "mcp_task_created"


def test_gateway_cancellation_blocks_signed_task_before_execution() -> None:
    _, gateway, audit, credential, executions = gateway_setup()
    token = issue_tool_token(gateway, credential)
    request = stateless_request(gateway, token)
    gateway.cancel_task(access_token=token, task_state=request.task_state)

    result = gateway.invoke_stateless(
        access_token=token,
        headers={"Mcp-Method": "tools/call", "Mcp-Name": "synthetic_status_update"},
        request=request,
    )

    assert gateway.task_status(request.task_state) == "cancelled"
    assert result["assurance"] == "FAIL"
    assert "not active" in result["warning"]
    assert executions == []
    assert [event["event_type"] for event in audit.events[-2:]] == [
        "mcp_task_cancelled",
        "mcp_request_blocked",
    ]


def test_worker_task_failure_is_terminal_and_audited() -> None:
    def failing_handler(_parameters):
        raise RuntimeError("synthetic worker failure")

    _, gateway, audit, credential, _ = gateway_setup(handler_override=failing_handler)
    token = issue_tool_token(gateway, credential)
    request = stateless_request(gateway, token)

    result = gateway.run_task(
        access_token=token,
        headers={"Mcp-Method": "tools/call", "Mcp-Name": "synthetic_status_update"},
        request=request,
    )

    assert result["assurance"] == "FAIL"
    assert "task execution failed" in result["warning"]
    assert gateway.task_status(request.task_state) == "failed"
    assert [event["event_type"] for event in audit.events[-2:]] == [
        "mcp_task_started",
        "mcp_task_failed",
    ]


def test_cancellation_race_cannot_cancel_running_task() -> None:
    started = threading.Event()
    release = threading.Event()

    def blocking_handler(parameters):
        started.set()
        assert release.wait(timeout=1)
        return {"tool": "synthetic_status_update", **dict(parameters)}

    _, gateway, _, credential, _ = gateway_setup(handler_override=blocking_handler)
    token = issue_tool_token(gateway, credential)
    request = stateless_request(gateway, token)
    result_holder = []

    worker = threading.Thread(
        target=lambda: result_holder.append(
            gateway.run_task(
                access_token=token,
                headers={"Mcp-Method": "tools/call", "Mcp-Name": "synthetic_status_update"},
                request=request,
            )
        )
    )
    worker.start()
    assert started.wait(timeout=1)

    with pytest.raises(McpGatewayError, match="cannot be cancelled"):
        gateway.cancel_task(access_token=token, task_state=request.task_state)

    release.set()
    worker.join(timeout=1)
    assert not worker.is_alive()
    assert result_holder[0]["assurance"] == "PASS"
    assert gateway.task_status(request.task_state) == "completed"


def test_completed_task_result_survives_gateway_restart(tmp_path) -> None:
    database = str(tmp_path / "tasks.db")
    identity = IdentityAuthority(secret=b"durable-task-identity-secret")
    first_store = SQLiteTaskStore(database)
    _, first_gateway, _, credential, first_executions = gateway_setup(
        identity_authority=identity,
        task_store=first_store,
    )
    token = issue_tool_token(first_gateway, credential)
    request = stateless_request(first_gateway, token)
    headers = {"Mcp-Method": "tools/call", "Mcp-Name": "synthetic_status_update"}

    first = first_gateway.run_task(access_token=token, headers=headers, request=request)
    first_gateway.close()

    second_store = SQLiteTaskStore(database)
    _, second_gateway, _, _, second_executions = gateway_setup(
        identity_authority=identity,
        task_store=second_store,
    )
    resumed_token = issue_tool_token(second_gateway, credential)
    replay = second_gateway.run_task(
        access_token=resumed_token,
        headers=headers,
        request=request,
    )

    assert first["assurance"] == "PASS"
    assert replay["assurance"] == "PASS"
    assert replay["result"] == first["result"]
    assert "already completed" in replay["warning"]
    assert len(first_executions) == 1
    assert second_executions == []
    second_gateway.close()


def test_interrupted_durable_task_requires_recovery_after_restart(tmp_path) -> None:
    database = str(tmp_path / "tasks.db")
    identity = IdentityAuthority(secret=b"durable-task-identity-secret")
    first_store = SQLiteTaskStore(database)
    _, first_gateway, _, credential, _ = gateway_setup(
        identity_authority=identity,
        task_store=first_store,
    )
    token = issue_tool_token(first_gateway, credential)
    request = stateless_request(first_gateway, token)
    first_store.update(request.task_state.task_id, status="in_progress")
    first_gateway.close()

    second_store = SQLiteTaskStore(database)
    _, second_gateway, second_audit, _, executions = gateway_setup(
        identity_authority=identity,
        task_store=second_store,
    )
    resumed_token = issue_tool_token(second_gateway, credential)
    result = second_gateway.run_task(
        access_token=resumed_token,
        headers={"Mcp-Method": "tools/call", "Mcp-Name": "synthetic_status_update"},
        request=request,
    )

    assert second_gateway.task_status(request.task_state) == "recovery_required"
    assert result["assurance"] == "REVIEW"
    assert "recovery is required" in result["warning"]
    assert executions == []
    assert second_audit.events[-1]["event_type"] == "mcp_task_recovery_required"
    second_gateway.close()


def test_recovery_resolution_requires_scope_receipt_and_never_replays_handler(tmp_path) -> None:
    database = str(tmp_path / "tasks.db")
    identity = IdentityAuthority(secret=b"recovery-resolution-identity-secret")
    first_store = SQLiteTaskStore(database)
    _, first_gateway, _, credential, _ = gateway_setup(
        identity_authority=identity,
        task_store=first_store,
    )
    task_token = issue_tool_token(first_gateway, credential)
    request = stateless_request(first_gateway, task_token)
    first_store.update(request.task_state.task_id, status="in_progress")
    first_gateway.close()

    second_store = SQLiteTaskStore(database)
    receipts = LocalExternalReceiptRegistry(secret=b"recovery-receipt-secret")
    _, second_gateway, audit, _, executions = gateway_setup(
        identity_authority=identity,
        task_store=second_store,
        receipt_verifier=receipts,
    )
    normal_token = issue_tool_token(second_gateway, credential)
    missing_scope = second_gateway.resolve_recovery(
        access_token=normal_token,
        task_state=request.task_state,
        resolution="completed",
        external_receipt_id="external-001",
    )
    recovery_token = second_gateway.issue_token(
        credential,
        audience=RESOURCE_URI,
        scopes=frozenset({SCOPE, second_gateway.RECOVERY_SCOPE}),
    )
    missing_receipt = second_gateway.resolve_recovery(
        access_token=recovery_token,
        task_state=request.task_state,
        resolution="completed",
        external_receipt_id="",
    )
    wrong_receipt = second_gateway.resolve_recovery(
        access_token=recovery_token,
        task_state=request.task_state,
        resolution="completed",
        external_receipt_id="unknown",
        result={"status": "restart confirmed"},
    )
    receipt = receipts.create(
        task_id=request.task_state.task_id,
        tool_name="synthetic_status_update",
        user_id="operator-01",
        audience=RESOURCE_URI,
        status="completed",
        parameters_hash=request.task_state.parameters_hash,
        result={"status": "restart confirmed"},
    )
    wrong_result = second_gateway.resolve_recovery(
        access_token=recovery_token,
        task_state=request.task_state,
        resolution="completed",
        external_receipt_id=receipt.receipt_id,
        result={"status": "tampered outcome"},
    )
    wrong_resolution = second_gateway.resolve_recovery(
        access_token=recovery_token,
        task_state=request.task_state,
        resolution="abandoned",
        external_receipt_id=receipt.receipt_id,
        result={"status": "restart confirmed"},
    )
    resolved = second_gateway.resolve_recovery(
        access_token=recovery_token,
        task_state=request.task_state,
        resolution="completed",
        external_receipt_id=receipt.receipt_id,
        result={"status": "restart confirmed"},
    )
    replay = second_gateway.run_task(
        access_token=normal_token,
        headers={"Mcp-Method": "tools/call", "Mcp-Name": "synthetic_status_update"},
        request=request,
    )

    assert missing_scope["assurance"] == "FAIL"
    assert "recovery scope" in missing_scope["warning"]
    assert missing_receipt["assurance"] == "FAIL"
    assert "receipt reference" in missing_receipt["warning"]
    assert wrong_receipt["assurance"] == "FAIL"
    assert "not registered" in wrong_receipt["warning"]
    assert wrong_result["assurance"] == "FAIL"
    assert "result does not match" in wrong_result["warning"]
    assert wrong_resolution["assurance"] == "FAIL"
    assert "resolution does not match" in wrong_resolution["warning"]
    assert resolved["assurance"] == "PASS"
    assert second_gateway.task_status(request.task_state) == "reconciled_completed"
    assert resolved["result"]["external_receipt_id"] == receipt.receipt_id
    assert replay["assurance"] == "PASS"
    assert replay["result"] == resolved["result"]
    assert executions == []
    assert audit.events[-1]["event_type"] == "mcp_task_reconciled"
    second_gateway.close()
