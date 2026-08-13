from __future__ import annotations

from nova_aegis import AgentK, AssuranceStatus, Evidence, NovaAegisMVP


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


def test_agent_k_emits_ordered_pass_trace_for_verified_evidence() -> None:
    app = NovaAegisMVP(verified_evidence())
    citations = app.retriever.retrieve("What approval does restarting Service A require?")

    trace = AgentK().evaluate_with_trace(citations)

    assert trace.decision.status is AssuranceStatus.PASS
    assert trace.decision.reason == "Agent K evidence rules passed"
    assert [rule.rule_id for rule in trace.rules] == [
        "AK-EVID-001",
        "AK-PROV-001",
        "AK-REV-001",
        "AK-PROV-002",
        "AK-CLAIM-001",
    ]
    assert {rule.status for rule in trace.rules} == {AssuranceStatus.PASS}


def test_agent_k_trace_identifies_first_blocking_provenance_rule() -> None:
    app = NovaAegisMVP(
        [
            Evidence(
                source_id="DOC-UNTRUSTED",
                title="Untrusted Procedure",
                text="Restarting Service A requires operator approval.",
            )
        ]
    )
    citations = app.retriever.retrieve("What approval does restarting Service A require?")

    trace = AgentK().evaluate_with_trace(citations)

    assert trace.decision.status is AssuranceStatus.REVIEW
    assert trace.decision.reason.startswith("AK-PROV-001:")
    assert trace.rules[1].status is AssuranceStatus.REVIEW


def test_agent_k_trace_preserves_conflicting_claim_rule() -> None:
    app = NovaAegisMVP(
        [
            Evidence(
                source_id="PROC-001",
                title="Restart Approval Procedure",
                text="Restarting Service A requires operator approval.",
                authority="operations-policy",
                claim_group="service-a-restart-approval",
                claim="operator approval required",
                provenance_verified=True,
            ),
            Evidence(
                source_id="PROC-002",
                title="Restart Approval Exception",
                text="Restarting Service A does not require operator approval.",
                authority="operations-policy",
                claim_group="service-a-restart-approval",
                claim="operator approval not required",
                provenance_verified=True,
            ),
        ]
    )
    citations = app.retriever.retrieve("What approval does restarting Service A require?")

    trace = AgentK().evaluate_with_trace(citations)

    assert trace.decision.status is AssuranceStatus.REVIEW
    assert trace.decision.reason.startswith("AK-CLAIM-001:")
    assert trace.rules[-1].status is AssuranceStatus.REVIEW


def test_praetor_default_response_uses_agent_k_rule_reason() -> None:
    app = NovaAegisMVP([])

    result = app.answer("What approval does restarting Service A require?")

    assert result["assurance"] == "REVIEW"
    assert "AK-EVID-001: No supporting evidence was retrieved" in result["warning"]
    assert app.audit_log.events[-1]["deterministic_reason"].startswith("AK-EVID-001:")
