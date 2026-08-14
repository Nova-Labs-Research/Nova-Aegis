from __future__ import annotations

from dataclasses import replace

import pytest
import threading
import sqlite3

from nova_aegis import (
    IdentityAuthority,
    LocalExternalReceiptRegistry,
    McpGateway,
    McpGatewayError,
    McpGatewayRequest,
    McpToolDescriptor,
    Praetor,
    SQLiteTaskStore,
    SQLiteApprovalStore,
    SQLiteRecoveryStore,
    LocalJournalKeyProvider,
    TaskRecord,
    RecoveryApprovalRecord,
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
    approval_store=None,
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
        approval_store=approval_store,
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
        worker_id="worker-a",
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
                worker_id="worker-a",
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


def test_shared_durable_task_has_one_worker_owner(tmp_path) -> None:
    database = str(tmp_path / "tasks.db")
    identity = IdentityAuthority(secret=b"lease-race-identity-secret")
    started = threading.Event()
    release = threading.Event()
    executions: list[dict[str, str]] = []

    def blocking_handler(parameters):
        executions.append(dict(parameters))
        started.set()
        assert release.wait(timeout=1)
        return {"tool": "synthetic_status_update", **dict(parameters)}

    first_store = SQLiteTaskStore(database)
    _, first_gateway, _, credential, _ = gateway_setup(
        identity_authority=identity,
        task_store=first_store,
        handler_override=blocking_handler,
    )
    second_store = SQLiteTaskStore(database)
    _, second_gateway, _, _, _ = gateway_setup(
        identity_authority=identity,
        task_store=second_store,
        handler_override=blocking_handler,
    )
    token = issue_tool_token(first_gateway, credential)
    second_token = issue_tool_token(second_gateway, credential)
    request = stateless_request(first_gateway, token)
    headers = {"Mcp-Method": "tools/call", "Mcp-Name": "synthetic_status_update"}
    results: list[dict[str, object]] = []

    first_worker = threading.Thread(
        target=lambda: results.append(
            first_gateway.run_task(
                access_token=token,
                headers=headers,
                request=request,
                worker_id="worker-a",
            )
        )
    )
    first_worker.start()
    assert started.wait(timeout=1)

    second = second_gateway.run_task(
        access_token=second_token,
        headers=headers,
        request=request,
        worker_id="worker-b",
    )
    release.set()
    first_worker.join(timeout=1)

    assert not first_worker.is_alive()
    assert results[0]["assurance"] == "PASS"
    assert second["assurance"] == "FAIL"
    assert "already in progress" in second["warning"] or "claimed" in second["warning"]
    assert len(executions) == 1
    assert first_gateway.task_status(request.task_state) == "completed"
    first_gateway.close()
    second_gateway.close()


def test_gateway_renews_active_worker_lease(tmp_path) -> None:
    started = threading.Event()
    release = threading.Event()

    def blocking_handler(parameters):
        started.set()
        assert release.wait(timeout=1)
        return {"tool": "synthetic_status_update", **dict(parameters)}

    store = SQLiteTaskStore(str(tmp_path / "tasks.db"))
    _, gateway, audit, credential, _ = gateway_setup(
        handler_override=blocking_handler,
        task_store=store,
    )
    token = issue_tool_token(gateway, credential)
    request = stateless_request(gateway, token)
    result_holder = []
    worker = threading.Thread(
        target=lambda: result_holder.append(
            gateway.run_task(
                access_token=token,
                headers={"Mcp-Method": "tools/call", "Mcp-Name": "synthetic_status_update"},
                request=request,
                worker_id="worker-a",
            )
        )
    )
    worker.start()
    assert started.wait(timeout=1)
    record = store.get(request.task_state.task_id)
    assert record is not None and record.fencing_token == 1
    assert gateway.renew_task(
        access_token=token,
        task_state=request.task_state,
        worker_id="worker-a",
        fencing_token=record.fencing_token,
    )
    release.set()
    worker.join(timeout=1)

    assert not worker.is_alive()
    assert result_holder[0]["assurance"] == "PASS"
    assert audit.events[-2]["event_type"] == "mcp_task_lease_renewed"
    gateway.close()


def test_expired_worker_lease_requires_recovery_and_rejects_stale_finish(tmp_path) -> None:
    store = SQLiteTaskStore(str(tmp_path / "tasks.db"))
    store.create(TaskRecord("task-1", "operator-01", 100, "pending"))

    fencing_token = store.claim("task-1", worker_id="worker-a", lease_expires_at=10)
    assert fencing_token == 1
    assert not store.claim("task-1", worker_id="worker-b", lease_expires_at=20)
    store.expire(10)

    record = store.get("task-1")
    assert record is not None
    assert record.status == "recovery_required"
    assert not store.finish(
        "task-1",
        worker_id="worker-a",
        fencing_token=fencing_token,
        status="completed",
        result={"status": "unsafe stale result"},
        now=10,
    )
    store.close()


def test_worker_lease_renewal_and_fencing_reject_stale_worker(tmp_path) -> None:
    store = SQLiteTaskStore(str(tmp_path / "tasks.db"))
    store.create(TaskRecord("task-1", "operator-01", 100, "pending"))

    first_token = store.claim("task-1", worker_id="worker-a", lease_expires_at=10)
    assert first_token == 1
    assert store.renew(
        "task-1",
        worker_id="worker-a",
        fencing_token=first_token,
        lease_expires_at=20,
        now=5,
    )
    assert not store.renew(
        "task-1",
        worker_id="worker-a",
        fencing_token=first_token + 1,
        lease_expires_at=30,
        now=6,
    )

    store.update("task-1", status="pending")
    second_token = store.claim("task-1", worker_id="worker-b", lease_expires_at=30)
    assert second_token == 2
    assert not store.finish(
        "task-1",
        worker_id="worker-a",
        fencing_token=first_token,
        status="completed",
        result={"status": "stale"},
        now=7,
    )
    assert store.finish(
        "task-1",
        worker_id="worker-b",
        fencing_token=second_token,
        status="completed",
        result={"status": "current"},
        now=7,
    )
    store.close()


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

    first = first_gateway.run_task(
        access_token=token, headers=headers, request=request, worker_id="worker-a"
    )
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
        worker_id="worker-b",
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
        worker_id="worker-b",
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
    approver = identity.issue("operator-02", "operator")
    approver_token = second_gateway.issue_token(
        approver,
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
    with pytest.raises(McpGatewayError, match="independent"):
        second_gateway.approve_recovery(
            access_token=recovery_token,
            task_state=request.task_state,
            resolution="completed",
            external_receipt_id=receipt.receipt_id,
            result={"status": "restart confirmed"},
        )
    approval = second_gateway.approve_recovery(
        access_token=approver_token,
        task_state=request.task_state,
        resolution="completed",
        external_receipt_id=receipt.receipt_id,
        result={"status": "restart confirmed"},
    )
    alternate_receipt = receipts.create(
        task_id=request.task_state.task_id,
        tool_name="synthetic_status_update",
        user_id="operator-01",
        audience=RESOURCE_URI,
        status="completed",
        parameters_hash=request.task_state.parameters_hash,
        result={"status": "different confirmed outcome"},
    )
    mismatched_approval = second_gateway.resolve_recovery(
        access_token=recovery_token,
        task_state=request.task_state,
        resolution="completed",
        external_receipt_id=alternate_receipt.receipt_id,
        result={"status": "different confirmed outcome"},
        approval_id=approval.approval_id,
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
        approval_id=approval.approval_id,
    )
    replay = second_gateway.run_task(
        access_token=normal_token,
        headers={"Mcp-Method": "tools/call", "Mcp-Name": "synthetic_status_update"},
        request=request,
        worker_id="worker-b",
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
    assert mismatched_approval["assurance"] == "FAIL"
    assert "approval does not match" in mismatched_approval["warning"]
    assert resolved["assurance"] == "PASS"
    assert second_gateway.task_status(request.task_state) == "reconciled_completed"
    assert resolved["result"]["external_receipt_id"] == receipt.receipt_id
    assert replay["assurance"] == "PASS"
    assert replay["result"] == resolved["result"]
    assert executions == []
    assert audit.events[-1]["event_type"] == "mcp_task_reconciled"
    second_gateway.close()


def test_recovery_approval_survives_gateway_restart_and_is_single_use(tmp_path) -> None:
    database = str(tmp_path / "tasks.db")
    approval_database = str(tmp_path / "approvals.db")
    identity = IdentityAuthority(secret=b"durable-approval-identity-secret")
    first_store = SQLiteTaskStore(database)
    _, first_gateway, _, credential, _ = gateway_setup(
        identity_authority=identity,
        task_store=first_store,
    )
    task_token = issue_tool_token(first_gateway, credential)
    request = stateless_request(first_gateway, task_token)
    first_store.update(request.task_state.task_id, status="in_progress")
    first_gateway.close()

    receipts = LocalExternalReceiptRegistry(secret=b"durable-approval-receipt-secret")
    second_gateway = gateway_setup(
        identity_authority=identity,
        task_store=SQLiteTaskStore(database),
        receipt_verifier=receipts,
        approval_store=SQLiteApprovalStore(approval_database),
    )[1]
    approver = identity.issue("operator-02", "operator")
    approver_token = second_gateway.issue_token(
        approver,
        audience=RESOURCE_URI,
        scopes=frozenset({SCOPE, second_gateway.RECOVERY_SCOPE}),
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
    approval = second_gateway.approve_recovery(
        access_token=approver_token,
        task_state=request.task_state,
        resolution="completed",
        external_receipt_id=receipt.receipt_id,
        result={"status": "restart confirmed"},
    )
    second_gateway.close()

    third_gateway = gateway_setup(
        identity_authority=identity,
        task_store=SQLiteTaskStore(database),
        receipt_verifier=receipts,
        approval_store=SQLiteApprovalStore(approval_database),
    )[1]
    owner_token = third_gateway.issue_token(
        credential,
        audience=RESOURCE_URI,
        scopes=frozenset({SCOPE, third_gateway.RECOVERY_SCOPE}),
    )
    resolved = third_gateway.resolve_recovery(
        access_token=owner_token,
        task_state=request.task_state,
        resolution="completed",
        external_receipt_id=receipt.receipt_id,
        result={"status": "restart confirmed"},
        approval_id=approval.approval_id,
    )
    replay = third_gateway.resolve_recovery(
        access_token=owner_token,
        task_state=request.task_state,
        resolution="completed",
        external_receipt_id=receipt.receipt_id,
        result={"status": "restart confirmed"},
        approval_id=approval.approval_id,
    )

    assert resolved["assurance"] == "PASS"
    assert replay["assurance"] == "FAIL"
    assert "not awaiting recovery" in replay["warning"]
    third_gateway.close()


def test_durable_approval_consume_allows_only_one_consumer(tmp_path) -> None:
    store = SQLiteApprovalStore(str(tmp_path / "approvals.db"))
    approval = RecoveryApprovalRecord(
        approval_id="approval-1",
        task_id="task-1",
        approver_id="operator-02",
        resolution="completed",
        external_receipt_id="receipt-1",
        result_hash="hash-1",
        issued_at=1,
        expires_at=100,
        signature="signature-1",
    )
    store.create(approval)
    results: list[bool] = []
    threads = [
        threading.Thread(target=lambda: results.append(store.consume("approval-1", now=2)))
        for _ in range(2)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=1)

    assert sorted(results) == [False, True]
    assert store.get("approval-1") is None
    store.close()


def test_recovery_journal_tampering_fails_integrity_check(tmp_path) -> None:
    database = str(tmp_path / "approvals.db")
    store = SQLiteApprovalStore(database)
    approval = RecoveryApprovalRecord(
        approval_id="approval-journal-integrity",
        task_id="task-1",
        approver_id="operator-02",
        resolution="completed",
        external_receipt_id="receipt-1",
        result_hash="hash-1",
        issued_at=1,
        expires_at=100,
        signature="signature-1",
    )
    store.create(approval)
    assert store.begin_recovery(
        approval.approval_id,
        task_id=approval.task_id,
        status="reconciled_completed",
        result={"status": "confirmed"},
        now=2,
    )
    store.close()

    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE mcp_recovery_journal SET result_json = ? WHERE journal_id = ?",
            ('{"status":"forged"}', approval.approval_id),
        )
        connection.commit()

    reopened = SQLiteApprovalStore(database)
    journal = reopened.pending_recoveries()[0]
    assert not journal.verify_integrity()
    reopened.close()


def test_unified_recovery_store_commits_approval_and_task_together(tmp_path) -> None:
    identity = IdentityAuthority(secret=b"unified-recovery-identity-secret")
    receipts = LocalExternalReceiptRegistry(secret=b"unified-recovery-receipt-secret")
    store = SQLiteRecoveryStore(str(tmp_path / "recovery.db"))
    _, gateway, _, credential, executions = gateway_setup(
        identity_authority=identity,
        task_store=store,
        receipt_verifier=receipts,
        approval_store=store,
    )
    owner_token = gateway.issue_token(
        credential,
        audience=RESOURCE_URI,
        scopes=frozenset({SCOPE, gateway.RECOVERY_SCOPE}),
    )
    request = stateless_request(gateway, issue_tool_token(gateway, credential))
    store.update(request.task_state.task_id, status="recovery_required")
    approver = identity.issue("operator-02", "operator")
    approval_token = gateway.issue_token(
        approver,
        audience=RESOURCE_URI,
        scopes=frozenset({SCOPE, gateway.RECOVERY_SCOPE}),
    )
    receipt = receipts.create(
        task_id=request.task_state.task_id,
        tool_name="synthetic_status_update",
        user_id="operator-01",
        audience=RESOURCE_URI,
        status="completed",
        parameters_hash=request.task_state.parameters_hash,
        result={"status": "atomic"},
    )
    approval = gateway.approve_recovery(
        access_token=approval_token,
        task_state=request.task_state,
        resolution="completed",
        external_receipt_id=receipt.receipt_id,
        result={"status": "atomic"},
    )

    resolved = gateway.resolve_recovery(
        access_token=owner_token,
        task_state=request.task_state,
        resolution="completed",
        external_receipt_id=receipt.receipt_id,
        result={"status": "atomic"},
        approval_id=approval.approval_id,
    )

    assert resolved["assurance"] == "PASS"
    assert store.get(request.task_state.task_id).status == "reconciled_completed"
    assert store.get(approval.approval_id) is None
    assert store.pending_recoveries() == ()
    assert executions == []
    gateway.close()


def test_unified_recovery_store_rolls_back_on_transaction_failure(tmp_path) -> None:
    class FailingRecoveryStore(SQLiteRecoveryStore):
        def _insert_journal(self, journal_id, task_id, status, result):
            raise ValueError("synthetic unified transaction failure")

    identity = IdentityAuthority(secret=b"unified-rollback-identity-secret")
    receipts = LocalExternalReceiptRegistry(secret=b"unified-rollback-receipt-secret")
    store = FailingRecoveryStore(str(tmp_path / "recovery.db"))
    _, gateway, _, credential, _ = gateway_setup(
        identity_authority=identity,
        task_store=store,
        receipt_verifier=receipts,
        approval_store=store,
    )
    request = stateless_request(gateway, issue_tool_token(gateway, credential))
    store.update(request.task_state.task_id, status="recovery_required")
    approver = identity.issue("operator-02", "operator")
    approval_token = gateway.issue_token(
        approver,
        audience=RESOURCE_URI,
        scopes=frozenset({SCOPE, gateway.RECOVERY_SCOPE}),
    )
    owner_token = gateway.issue_token(
        credential,
        audience=RESOURCE_URI,
        scopes=frozenset({SCOPE, gateway.RECOVERY_SCOPE}),
    )
    receipt = receipts.create(
        task_id=request.task_state.task_id,
        tool_name="synthetic_status_update",
        user_id="operator-01",
        audience=RESOURCE_URI,
        status="completed",
        parameters_hash=request.task_state.parameters_hash,
        result={"status": "rollback"},
    )
    approval = gateway.approve_recovery(
        access_token=approval_token,
        task_state=request.task_state,
        resolution="completed",
        external_receipt_id=receipt.receipt_id,
        result={"status": "rollback"},
    )

    failed = gateway.resolve_recovery(
        access_token=owner_token,
        task_state=request.task_state,
        resolution="completed",
        external_receipt_id=receipt.receipt_id,
        result={"status": "rollback"},
        approval_id=approval.approval_id,
    )

    assert failed["assurance"] == "FAIL"
    assert store.get(request.task_state.task_id).status == "recovery_required"
    assert store.get(approval.approval_id) is not None
    assert store.pending_recoveries() == ()
    gateway.close()


def test_authenticated_recovery_journal_rejects_wrong_key(tmp_path) -> None:
    database = str(tmp_path / "authenticated-recovery.db")
    approval = RecoveryApprovalRecord(
        approval_id="approval-authenticated-journal",
        task_id="task-authenticated-journal",
        approver_id="operator-02",
        resolution="completed",
        external_receipt_id="receipt-1",
        result_hash="hash-1",
        issued_at=1,
        expires_at=100,
        signature="signature-1",
    )
    writer = SQLiteRecoveryStore(database, journal_secret=b"journal-key-one")
    writer.create(approval)
    assert writer.begin_recovery(
        approval.approval_id,
        task_id=approval.task_id,
        status="reconciled_completed",
        result={"status": "authenticated"},
        now=2,
    )
    writer.close()

    wrong_key = SQLiteRecoveryStore(database, journal_secret=b"journal-key-two")
    journal = wrong_key.pending_recoveries()[0]
    assert not wrong_key.verify_journal(journal)
    assert wrong_key.get(approval.approval_id) is None
    wrong_key.close()


def test_recovery_journal_key_rotation_preserves_overlap_then_retires_old_key(tmp_path) -> None:
    database = str(tmp_path / "rotating-recovery.db")
    first = RecoveryApprovalRecord(
        approval_id="approval-old-key",
        task_id="task-old-key",
        approver_id="operator-02",
        resolution="completed",
        external_receipt_id="receipt-old",
        result_hash="hash-old",
        issued_at=1,
        expires_at=100,
        signature="signature-old",
    )
    store = SQLiteRecoveryStore(database, journal_secret=b"key-old")
    store.create(first)
    assert store.begin_recovery(
        first.approval_id,
        task_id=first.task_id,
        status="reconciled_completed",
        result={"status": "old"},
        now=2,
    )
    store.rotate_journal_key("journal-v2", b"key-new")
    second = RecoveryApprovalRecord(
        approval_id="approval-new-key",
        task_id="task-new-key",
        approver_id="operator-02",
        resolution="completed",
        external_receipt_id="receipt-new",
        result_hash="hash-new",
        issued_at=1,
        expires_at=100,
        signature="signature-new",
    )
    store.create(second)
    assert store.begin_recovery(
        second.approval_id,
        task_id=second.task_id,
        status="reconciled_completed",
        result={"status": "new"},
        now=2,
    )
    journals = store.pending_recoveries()
    assert {journal.key_id for journal in journals} == {"journal-v1", "journal-v2"}
    assert all(store.verify_journal(journal) for journal in journals)

    store.retire_journal_key("journal-v1")
    old_journal = next(journal for journal in journals if journal.key_id == "journal-v1")
    new_journal = next(journal for journal in journals if journal.key_id == "journal-v2")
    assert not store.verify_journal(old_journal)
    assert store.verify_journal(new_journal)
    with pytest.raises(ValueError, match="active journal key"):
        store.retire_journal_key("journal-v2")
    store.close()


def test_journal_key_provider_requires_authorized_rotation_and_retirement() -> None:
    provider = LocalJournalKeyProvider(
        {"journal-v1": b"key-one"},
        rotation_authority="key-admin",
    )
    with pytest.raises(PermissionError, match="authority"):
        provider.rotate("journal-v2", b"key-two", authority="operator")
    provider.rotate("journal-v2", b"key-two", authority="key-admin")
    assert provider.active() == ("journal-v2", b"key-two")
    with pytest.raises(PermissionError, match="authority"):
        provider.retire("journal-v1", authority="operator")
    provider.retire("journal-v1", authority="key-admin")
    assert provider.get("journal-v1") is None


def test_journal_key_provider_unknown_key_fails_closed(tmp_path) -> None:
    database = str(tmp_path / "provider-recovery.db")
    writer = SQLiteRecoveryStore(
        database,
        key_provider=LocalJournalKeyProvider({"journal-v1": b"key-one"}),
    )
    approval = RecoveryApprovalRecord(
        approval_id="approval-provider-key",
        task_id="task-provider-key",
        approver_id="operator-02",
        resolution="completed",
        external_receipt_id="receipt-provider",
        result_hash="hash-provider",
        issued_at=1,
        expires_at=100,
        signature="signature-provider",
    )
    writer.create(approval)
    assert writer.begin_recovery(
        approval.approval_id,
        task_id=approval.task_id,
        status="reconciled_completed",
        result={"status": "provider"},
        now=2,
    )
    writer.close()

    reader = SQLiteRecoveryStore(
        database,
        key_provider=LocalJournalKeyProvider({"journal-v2": b"key-two"}),
    )
    journal = reader.pending_recoveries()[0]
    assert journal.key_id == "journal-v1"
    assert not reader.verify_journal(journal)
    reader.close()


def test_unified_recovery_transaction_allows_one_concurrent_finalizer(tmp_path) -> None:
    store = SQLiteRecoveryStore(str(tmp_path / "concurrent-recovery.db"))
    task = TaskRecord(
        task_id="task-concurrent-recovery",
        user_id="operator-01",
        expires_at=100,
        status="recovery_required",
    )
    approval = RecoveryApprovalRecord(
        approval_id="approval-concurrent-recovery",
        task_id=task.task_id,
        approver_id="operator-02",
        resolution="completed",
        external_receipt_id="receipt-concurrent",
        result_hash="hash-concurrent",
        issued_at=1,
        expires_at=100,
        signature="signature-concurrent",
    )
    store.create(task)
    store.create(approval)
    results: list[bool] = []
    threads = [
        threading.Thread(
            target=lambda: results.append(
                store.finalize_recovery(
                    approval.approval_id,
                    task_id=task.task_id,
                    status="reconciled_completed",
                    result={"status": "concurrent"},
                    now=2,
                )
            )
        )
        for _ in range(2)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=1)

    assert sorted(results) == [False, True]
    assert store.get(task.task_id).status == "reconciled_completed"
    assert store.get(approval.approval_id) is None
    assert store.pending_recoveries() == ()
    store.close()


def test_approval_revocation_blocks_recovery(tmp_path) -> None:
    store = SQLiteApprovalStore(str(tmp_path / "approvals.db"))
    approval = RecoveryApprovalRecord(
        approval_id="approval-revoked",
        task_id="task-1",
        approver_id="operator-02",
        resolution="completed",
        external_receipt_id="receipt-1",
        result_hash="hash-1",
        issued_at=1,
        expires_at=100,
        signature="signature-1",
    )
    store.create(approval)

    assert store.revoke(approval.approval_id, now=2)
    assert store.get(approval.approval_id) is None
    assert not store.consume(approval.approval_id, now=2)
    store.close()


def test_recovery_consumes_approval_before_task_commit_failure() -> None:
    class FailingTaskStore:
        def __init__(self, delegate):
            self.delegate = delegate

        def __getattr__(self, name):
            return getattr(self.delegate, name)

        def update(self, task_id, *, status, result=None):
            if status.startswith("reconciled_"):
                raise ValueError("synthetic task commit failure")
            return self.delegate.update(task_id, status=status, result=result)

    identity, gateway, _, credential, _ = gateway_setup()
    token = issue_tool_token(gateway, credential)
    request = stateless_request(gateway, token)
    gateway._task_store = FailingTaskStore(gateway._task_store)
    gateway._task_store.update(request.task_state.task_id, status="in_progress")
    gateway._task_store.update(request.task_state.task_id, status="recovery_required")
    approver = identity.issue("operator-02", "operator")
    approver_token = gateway.issue_token(
        approver,
        audience=RESOURCE_URI,
        scopes=frozenset({SCOPE, gateway.RECOVERY_SCOPE}),
    )
    recovery_token = gateway.issue_token(
        credential,
        audience=RESOURCE_URI,
        scopes=frozenset({SCOPE, gateway.RECOVERY_SCOPE}),
    )
    verifier = LocalExternalReceiptRegistry(secret=b"failure-receipt-secret")
    gateway._receipt_verifier = verifier
    receipt = verifier.create(
        task_id=request.task_state.task_id,
        tool_name="synthetic_status_update",
        user_id="operator-01",
        audience=RESOURCE_URI,
        status="completed",
        parameters_hash=request.task_state.parameters_hash,
        result={"status": "restart confirmed"},
    )
    approval = gateway.approve_recovery(
        access_token=approver_token,
        task_state=request.task_state,
        resolution="completed",
        external_receipt_id=receipt.receipt_id,
        result={"status": "restart confirmed"},
    )

    failed = gateway.resolve_recovery(
        access_token=recovery_token,
        task_state=request.task_state,
        resolution="completed",
        external_receipt_id=receipt.receipt_id,
        result={"status": "restart confirmed"},
        approval_id=approval.approval_id,
    )

    assert failed["assurance"] == "FAIL"
    assert "synthetic task commit failure" in failed["warning"]
    assert gateway.task_status(request.task_state) == "recovery_required"
    assert gateway._approval_store.get(approval.approval_id) is None
    gateway.close()


def test_recovery_journal_replays_after_restart_without_handler_replay(tmp_path) -> None:
    task_database = str(tmp_path / "tasks.db")
    approval_database = str(tmp_path / "approvals.db")
    identity = IdentityAuthority(secret=b"journal-replay-identity-secret")
    receipts = LocalExternalReceiptRegistry(secret=b"journal-replay-receipt-secret")
    first_store = SQLiteTaskStore(task_database)
    _, gateway, _, credential, executions = gateway_setup(
        identity_authority=identity,
        task_store=first_store,
        receipt_verifier=receipts,
        approval_store=SQLiteApprovalStore(approval_database),
    )
    token = issue_tool_token(gateway, credential)
    request = stateless_request(gateway, token)
    gateway._task_store.update(request.task_state.task_id, status="recovery_required")
    approver = identity.issue("operator-02", "operator")
    approver_token = gateway.issue_token(
        approver,
        audience=RESOURCE_URI,
        scopes=frozenset({SCOPE, gateway.RECOVERY_SCOPE}),
    )
    owner_token = gateway.issue_token(
        credential,
        audience=RESOURCE_URI,
        scopes=frozenset({SCOPE, gateway.RECOVERY_SCOPE}),
    )
    receipt = receipts.create(
        task_id=request.task_state.task_id,
        tool_name="synthetic_status_update",
        user_id="operator-01",
        audience=RESOURCE_URI,
        status="completed",
        parameters_hash=request.task_state.parameters_hash,
        result={"status": "journal confirmed"},
    )
    approval = gateway.approve_recovery(
        access_token=approver_token,
        task_state=request.task_state,
        resolution="completed",
        external_receipt_id=receipt.receipt_id,
        result={"status": "journal confirmed"},
    )

    class FailingTaskStore:
        def __init__(self, delegate):
            self.delegate = delegate

        def __getattr__(self, name):
            return getattr(self.delegate, name)

        def update(self, task_id, *, status, result=None):
            if status == "reconciled_completed":
                raise ValueError("synthetic restart crash")
            return self.delegate.update(task_id, status=status, result=result)

    gateway._task_store = FailingTaskStore(gateway._task_store)
    failed = gateway.resolve_recovery(
        access_token=owner_token,
        task_state=request.task_state,
        resolution="completed",
        external_receipt_id=receipt.receipt_id,
        result={"status": "journal confirmed"},
        approval_id=approval.approval_id,
    )
    assert failed["assurance"] == "FAIL"
    gateway.close()

    restarted = gateway_setup(
        identity_authority=identity,
        task_store=SQLiteTaskStore(task_database),
        receipt_verifier=receipts,
        approval_store=SQLiteApprovalStore(approval_database),
    )[1]
    assert restarted.task_status(request.task_state) == "reconciled_completed"
    assert restarted._approval_store.pending_recoveries() == ()
    assert restarted._approval_store.get(approval.approval_id) is None
    assert executions == []
    restarted.close()
