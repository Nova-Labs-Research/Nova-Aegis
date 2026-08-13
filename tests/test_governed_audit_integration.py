from __future__ import annotations

from nova_aegis import Evidence, NovaAegisMVP, SQLiteAuditLog


def verified_evidence() -> list[Evidence]:
    return [
        Evidence(
            source_id="PROC-001",
            title="Restart Procedure",
            text="Restarting Service A requires operator approval.",
            revision_id="7",
            authority="operations-policy",
            provenance_verified=True,
        )
    ]


def test_sqlite_audit_records_governed_response_and_tool_lifecycle(tmp_path) -> None:
    audit_log = SQLiteAuditLog(str(tmp_path / "audit.db"))
    app = NovaAegisMVP(verified_evidence(), audit_log=audit_log)

    response = app.answer("What approval does restarting Service A require?")
    tool_result = app.execute_synthetic_tool(
        target="service-a",
        value="restart",
        authorized_tools=frozenset({"synthetic_status_update"}),
    )
    events = audit_log.events

    assert response["assurance"] == "PASS"
    assert tool_result["assurance"] == "PASS"
    assert [event["event_type"] for event in events] == [
        "request_received",
        "retrieval_completed",
        "response_proposed",
        "response_assured",
        "tool_authorized",
        "tool_executed",
    ]
    response_event = events[3]
    assert response_event["deterministic_status"] == "PASS"
    assert response_event["semantic_status"] == "PASS"
    assert events[4]["request_id"] == events[5]["request_id"]
    audit_log.close()


def test_sqlite_audit_records_blocked_tool_without_authorization_event(tmp_path) -> None:
    audit_log = SQLiteAuditLog(str(tmp_path / "audit.db"))
    app = NovaAegisMVP([], audit_log=audit_log)

    result = app.execute_synthetic_tool(
        target="service-a",
        value="restart",
        authorized_tools=frozenset(),
    )

    assert result["assurance"] == "FAIL"
    assert [event["event_type"] for event in audit_log.events] == ["tool_blocked"]
    assert app.synthetic_tool.executions == []
    audit_log.close()


def test_audit_preflight_failure_blocks_execution() -> None:
    class FailingAuditLog:
        def __init__(self) -> None:
            self.events: list[dict[str, object]] = []

        def append(self, event_type: str, **details: object) -> None:
            if event_type == "tool_authorized":
                raise RuntimeError("synthetic audit storage outage")
            self.events.append({"event_type": event_type, **details})

    audit_log = FailingAuditLog()
    app = NovaAegisMVP([], audit_log=audit_log)

    result = app.execute_synthetic_tool(
        target="service-a",
        value="restart",
        authorized_tools=frozenset({"synthetic_status_update"}),
    )

    assert result["assurance"] == "FAIL"
    assert "Audit authorization recording failed" in result["warning"]
    assert app.synthetic_tool.executions == []
    assert [event["event_type"] for event in audit_log.events] == []
