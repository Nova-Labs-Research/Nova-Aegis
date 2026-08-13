from __future__ import annotations

from nova_aegis import (
    AssuranceStatus,
    EvaluationDecision,
    EvaluatorKind,
    Evidence,
    NovaAegisMVP,
    Praetor,
)


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


def semantic(status: AssuranceStatus, reason: str):
    def evaluate(_citations):
        return EvaluationDecision(EvaluatorKind.SEMANTIC, status, reason)

    return evaluate


def deterministic(status: AssuranceStatus, reason: str):
    def evaluate(_citations):
        return EvaluationDecision(EvaluatorKind.DETERMINISTIC, status, reason)

    return evaluate


def test_semantic_concern_routes_praetor_response_to_review_and_audits_verdicts() -> None:
    app = NovaAegisMVP(
        verified_evidence(),
        praetor=Praetor(
            semantic_evaluator=semantic(
                AssuranceStatus.FAIL,
                "Source wording materially misrepresents the policy",
            )
        ),
    )

    result = app.answer("What approval does restarting Service A require?")
    audit_event = app.audit_log.events[-1]

    assert result["assurance"] == "REVIEW"
    assert result["answer"] is None
    assert "semantic=FAIL" in result["warning"]
    assert audit_event["event_type"] == "response_assured"
    assert audit_event["deterministic_status"] == "PASS"
    assert audit_event["semantic_status"] == "FAIL"
    assert audit_event["semantic_reason"] == "Source wording materially misrepresents the policy"


def test_deterministic_hard_failure_blocks_semantic_pass_on_response_path() -> None:
    app = NovaAegisMVP(
        verified_evidence(),
        praetor=Praetor(
            deterministic_evaluator=deterministic(
                AssuranceStatus.FAIL,
                "Hard provenance boundary failed",
            ),
            semantic_evaluator=semantic(AssuranceStatus.PASS, "Response is coherent"),
        ),
    )

    result = app.answer("What approval does restarting Service A require?")

    assert result["assurance"] == "FAIL"
    assert result["answer"] is None
    assert "Deterministic governance blocked" in result["warning"]


def test_semantic_evaluator_exception_requires_review_without_pass() -> None:
    def unavailable(_citations):
        raise RuntimeError("synthetic judge outage")

    app = NovaAegisMVP(
        verified_evidence(),
        praetor=Praetor(semantic_evaluator=unavailable),
    )

    result = app.answer("What approval does restarting Service A require?")

    assert result["assurance"] == "REVIEW"
    assert result["answer"] is None
    assert "Semantic evaluator is unavailable" in result["warning"]


def test_mislabeled_semantic_evaluator_requires_review_without_pass() -> None:
    app = NovaAegisMVP(
        verified_evidence(),
        praetor=Praetor(
            semantic_evaluator=deterministic(AssuranceStatus.PASS, "Forged evaluator kind")
        ),
    )

    result = app.answer("What approval does restarting Service A require?")

    assert result["assurance"] == "REVIEW"
    assert result["answer"] is None
    assert "Semantic evaluator returned an invalid decision" in result["warning"]
