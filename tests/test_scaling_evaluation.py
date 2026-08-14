from __future__ import annotations

import pytest

from nova_aegis import (
    SyntheticEvaluationCase,
    SyntheticEvaluationConfig,
    SyntheticOutcomeReview,
    SyntheticScalingError,
    SyntheticScalingEvaluator,
)


def _review(valid: bool = True, shortcut: bool = False) -> SyntheticOutcomeReview:
    return SyntheticOutcomeReview(valid, "test", valid, shortcut, 1)


def _case(case_id: str, budget: int, parallelism: int, seed: int, review: SyntheticOutcomeReview, **kwargs: object) -> SyntheticEvaluationCase:
    return SyntheticEvaluationCase(case_id, budget, parallelism, seed, 2, review, **kwargs)


def test_fixed_matrix_classifies_outcomes_and_accounts_for_cost() -> None:
    config = SyntheticEvaluationConfig((1, 2), (1,), (11,))
    evaluator = SyntheticScalingEvaluator(config)
    report = evaluator.evaluate(
        (
            _case("a", 1, 1, 11, _review()),
            _case("b", 2, 1, 11, _review(shortcut=True)),
        )
    )

    assert report.case_count == 2
    assert report.attempt_count == 2
    assert report.total_cost_units == 4
    assert report.valid_success_rate == 0.5
    assert dict(report.outcome_counts) == {
        "success": 1,
        "false_success": 1,
        "disengagement": 0,
        "environment_self_destroyed": 0,
        "failure": 0,
        "invalid_transcript": 0,
    }
    assert 0 < report.valid_success_interval[0] < report.valid_success_interval[1] < 1


def test_failure_disengagement_and_self_destruction_remain_distinct() -> None:
    review = _review()
    assert SyntheticScalingEvaluator.classify(_case("f", 1, 1, 1, review, failure_kind="crash")) == "failure"
    assert SyntheticScalingEvaluator.classify(_case("d", 1, 1, 2, review, disengaged=True)) == "disengagement"
    assert SyntheticScalingEvaluator.classify(_case("e", 1, 1, 3, review, environment_self_destroyed=True)) == "environment_self_destroyed"
    assert SyntheticScalingEvaluator.classify(_case("i", 1, 1, 4, _review(valid=False))) == "invalid_transcript"


def test_matrix_requires_all_fixed_budget_parallelism_and_seed_cells() -> None:
    evaluator = SyntheticScalingEvaluator(SyntheticEvaluationConfig((1, 2), (1, 2), (7,)))
    incomplete = (_case("only", 1, 1, 7, _review()),)

    with pytest.raises(SyntheticScalingError, match="incomplete"):
        evaluator.evaluate(incomplete)


def test_ambiguous_case_configuration_fails_closed() -> None:
    with pytest.raises(ValueError, match="ambiguous"):
        SyntheticEvaluationCase("ambiguous", 1, 1, 1, 0, _review(), disengaged=True, environment_self_destroyed=True)
