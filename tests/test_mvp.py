from __future__ import annotations

import pytest

from nova_aegis import Evidence, GovernanceUnavailable, NovaAegisMVP, Praetor


@pytest.fixture
def documents() -> list[Evidence]:
    return [
        Evidence(
            source_id="PROC-001",
            title="Restart Procedure",
            text="Restarting Service A requires operator approval.",
        ),
        Evidence(
            source_id="POL-001",
            title="Change Policy",
            text="Production changes must be recorded in the change log.",
        ),
    ]


def test_supported_question_returns_cited_pass_and_audit_event(documents: list[Evidence]) -> None:
    app = NovaAegisMVP(documents)

    result = app.answer("What approval does restarting Service A require?")

    assert result["assurance"] == "PASS"
    assert result["answer"]
    assert result["evidence"][0]["source_id"] == "PROC-001"
    assert app.audit_log.events[-1]["event_type"] == "response_assured"


def test_missing_evidence_returns_review_without_answer(documents: list[Evidence]) -> None:
    app = NovaAegisMVP(documents)

    result = app.answer("What is the retention period for archived telemetry?")

    assert result["assurance"] == "REVIEW"
    assert result["answer"] is None
    assert "No supporting evidence" in result["warning"]


def test_unauthorized_synthetic_tool_is_blocked_and_audited(documents: list[Evidence]) -> None:
    app = NovaAegisMVP(documents)

    result = app.execute_synthetic_tool(
        target="service-a",
        value="restart",
        authorized_tools=frozenset(),
    )

    assert result["assurance"] == "FAIL"
    assert result["result"] is None
    assert app.synthetic_tool.executions == []
    assert app.audit_log.events[-1]["event_type"] == "tool_blocked"


def test_authorized_synthetic_tool_executes_and_is_audited(documents: list[Evidence]) -> None:
    app = NovaAegisMVP(documents)

    result = app.execute_synthetic_tool(
        target="service-a",
        value="restart",
        authorized_tools=frozenset({"synthetic_status_update"}),
    )

    assert result["assurance"] == "PASS"
    assert result["result"]["target"] == "service-a"
    assert len(app.synthetic_tool.executions) == 1
    assert app.audit_log.events[-1]["event_type"] == "tool_executed"


def test_praetor_unavailable_blocks_tool_without_execution(documents: list[Evidence]) -> None:
    app = NovaAegisMVP(documents, praetor=Praetor(available=False))

    with pytest.raises(GovernanceUnavailable):
        app.execute_synthetic_tool(
            target="service-a",
            value="restart",
            authorized_tools=frozenset({"synthetic_status_update"}),
        )

    assert app.synthetic_tool.executions == []
    assert app.audit_log.events[-1]["event_type"] == "tool_blocked"
    assert "authorization is unavailable" in app.audit_log.events[-1]["reason"]
