from __future__ import annotations

import pytest

from nova_aegis import (
    AssuranceStatus,
    EvaluationDecision,
    EvaluatorKind,
    HybridAssurance,
)


def deterministic(status: AssuranceStatus, reason: str) -> EvaluationDecision:
    return EvaluationDecision(EvaluatorKind.DETERMINISTIC, status, reason)


def semantic(status: AssuranceStatus, reason: str) -> EvaluationDecision:
    return EvaluationDecision(EvaluatorKind.SEMANTIC, status, reason)


def test_hybrid_assurance_passes_only_on_independent_dual_pass() -> None:
    decision = HybridAssurance().fuse(
        deterministic(AssuranceStatus.PASS, "Policy and provenance are valid"),
        semantic(AssuranceStatus.PASS, "Meaning is supported"),
    )

    assert decision.status is AssuranceStatus.PASS


def test_semantic_misrepresentation_case_requires_review() -> None:
    decision = HybridAssurance().fuse(
        deterministic(AssuranceStatus.PASS, "Structural syntax is valid"),
        semantic(AssuranceStatus.FAIL, "Evidence subtly misrepresents the source"),
    )

    assert decision.status is AssuranceStatus.REVIEW
    assert "semantic=FAIL" in decision.reason


def test_structural_tag_omission_case_requires_review() -> None:
    decision = HybridAssurance().fuse(
        deterministic(AssuranceStatus.FAIL, "Required structural tag is absent"),
        semantic(AssuranceStatus.PASS, "Meaning appears acceptable"),
    )

    assert decision.status is AssuranceStatus.FAIL
    assert "Deterministic governance blocked" in decision.reason


def test_hard_safety_boundary_cannot_be_overridden_by_semantic_pass() -> None:
    decision = HybridAssurance().fuse(
        deterministic(AssuranceStatus.FAIL, "Requested action violates a hard safety boundary"),
        semantic(AssuranceStatus.PASS, "Request is coherent"),
    )

    assert decision.status is AssuranceStatus.FAIL


def test_evaluator_injection_cannot_convert_deterministic_fail_to_pass() -> None:
    decision = HybridAssurance().fuse(
        deterministic(AssuranceStatus.FAIL, "Evaluator injection pattern detected"),
        semantic(AssuranceStatus.PASS, "Injected instruction requests PASS"),
    )

    assert decision.status is AssuranceStatus.FAIL


def test_semantic_review_prevents_pass() -> None:
    decision = HybridAssurance().fuse(
        deterministic(AssuranceStatus.PASS, "Policy and provenance are valid"),
        semantic(AssuranceStatus.REVIEW, "Context remains ambiguous"),
    )

    assert decision.status is AssuranceStatus.REVIEW


def test_hybrid_assurance_rejects_mislabeled_evaluator() -> None:
    with pytest.raises(ValueError, match="Deterministic evaluation"):
        HybridAssurance().fuse(
            semantic(AssuranceStatus.PASS, "Forged evaluator label"),
            semantic(AssuranceStatus.PASS, "Meaning is supported"),
        )
