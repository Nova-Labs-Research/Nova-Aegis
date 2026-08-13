from __future__ import annotations

from nova_aegis import NovaAegisMVP, SQLiteAuditLog


def test_completed_receipt_prevents_duplicate_execution_and_returns_stored_result(tmp_path) -> None:
    audit_log = SQLiteAuditLog(str(tmp_path / "audit.db"))
    app = NovaAegisMVP([], audit_log=audit_log)
    key = "restart-service-a-001"

    first = app.execute_synthetic_tool(
        target="service-a",
        value="restart",
        authorized_tools=frozenset({"synthetic_status_update"}),
        idempotency_key=key,
    )
    second = app.execute_synthetic_tool(
        target="service-a",
        value="restart",
        authorized_tools=frozenset({"synthetic_status_update"}),
        idempotency_key=key,
    )

    assert first["assurance"] == "PASS"
    assert second["assurance"] == "PASS"
    assert "already completed" in second["warning"]
    assert len(app.synthetic_tool.executions) == 1
    receipt = audit_log.get_execution_receipt(key)
    assert receipt is not None
    assert receipt.status == "completed"
    assert receipt.result == first["result"]
    audit_log.close()


def test_pending_receipt_requires_recovery_and_never_replays_execution(tmp_path) -> None:
    audit_log = SQLiteAuditLog(str(tmp_path / "audit.db"))
    key = "restart-service-a-interrupted"
    receipt, created = audit_log.prepare_execution(
        idempotency_key=key,
        request_id="request-interrupted",
        tool="synthetic_status_update",
        target="service-a",
        value="restart",
        user_id="anonymous",
        role="default",
    )
    assert created
    assert receipt.status == "authorized"

    app = NovaAegisMVP([], audit_log=audit_log)
    result = app.execute_synthetic_tool(
        target="service-a",
        value="restart",
        authorized_tools=frozenset({"synthetic_status_update"}),
        idempotency_key=key,
    )

    assert result["assurance"] == "REVIEW"
    assert "recovery is required" in result["warning"]
    assert app.synthetic_tool.executions == []
    assert audit_log.pending_execution_receipts()[0].idempotency_key == key
    assert audit_log.events[-1]["event_type"] == "tool_recovery_required"
    audit_log.close()


def test_completion_persistence_failure_returns_review_after_single_execution(tmp_path) -> None:
    class FailingCompletionAuditLog(SQLiteAuditLog):
        def complete_execution(self, idempotency_key, result):
            raise RuntimeError("synthetic receipt completion outage")

    audit_log = FailingCompletionAuditLog(str(tmp_path / "audit.db"))
    app = NovaAegisMVP([], audit_log=audit_log)

    result = app.execute_synthetic_tool(
        target="service-a",
        value="restart",
        authorized_tools=frozenset({"synthetic_status_update"}),
        idempotency_key="restart-service-a-completion-failure",
    )

    assert result["assurance"] == "REVIEW"
    assert "recovery is required" in result["warning"]
    assert len(app.synthetic_tool.executions) == 1
    assert audit_log.pending_execution_receipts()[0].status == "authorized"
    assert audit_log.events[-1]["event_type"] == "tool_recovery_required"
    audit_log.close()


def test_idempotency_key_cannot_be_reused_for_different_operation(tmp_path) -> None:
    audit_log = SQLiteAuditLog(str(tmp_path / "audit.db"))
    app = NovaAegisMVP([], audit_log=audit_log)
    key = "single-operation-key"
    app.execute_synthetic_tool(
        target="service-a",
        value="restart",
        authorized_tools=frozenset({"synthetic_status_update"}),
        idempotency_key=key,
    )

    try:
        app.execute_synthetic_tool(
            target="service-a",
            value="status",
            authorized_tools=frozenset({"synthetic_status_update"}),
            idempotency_key=key,
        )
    except ValueError as error:
        assert "different operation" in str(error)
    else:
        raise AssertionError("Idempotency key reuse was accepted")
    audit_log.close()
