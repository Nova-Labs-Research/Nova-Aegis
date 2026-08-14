"""Deterministic persistence and false-success evaluation for synthetic attempts."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import ClassVar, Iterable

from .outcome_validity import SyntheticOutcomeReview


class SyntheticScalingError(ValueError):
    """Raised when a synthetic evaluation matrix is invalid."""


@dataclass(frozen=True)
class SyntheticEvaluationCase:
    case_id: str
    budget: int
    parallelism: int
    seed: int
    cost_units: int
    review: SyntheticOutcomeReview
    failure_kind: str | None = None
    disengaged: bool = False
    environment_self_destroyed: bool = False

    def __post_init__(self) -> None:
        if not self.case_id.strip() or self.budget <= 0 or self.parallelism <= 0:
            raise ValueError("Synthetic evaluation case fields are invalid")
        if self.cost_units < 0:
            raise ValueError("Synthetic evaluation cost cannot be negative")
        if self.disengaged and self.environment_self_destroyed:
            raise ValueError("Synthetic case outcomes are ambiguous")


@dataclass(frozen=True)
class SyntheticEvaluationConfig:
    budgets: tuple[int, ...]
    parallelism: tuple[int, ...]
    seeds: tuple[int, ...]

    def __post_init__(self) -> None:
        if not self.budgets or not self.parallelism or not self.seeds:
            raise ValueError("Synthetic evaluation matrix cannot be empty")
        if any(value <= 0 for value in (*self.budgets, *self.parallelism)):
            raise ValueError("Synthetic evaluation matrix values must be positive")
        if len(set(self.budgets)) != len(self.budgets) or len(set(self.parallelism)) != len(self.parallelism):
            raise ValueError("Synthetic evaluation matrix values must be unique")
        if len(set(self.seeds)) != len(self.seeds):
            raise ValueError("Synthetic evaluation seeds must be unique")


@dataclass(frozen=True)
class SyntheticEvaluationReport:
    case_count: int
    outcome_counts: tuple[tuple[str, int], ...]
    total_cost_units: int
    attempt_count: int
    valid_success_rate: float
    valid_success_interval: tuple[float, float]


class SyntheticScalingEvaluator:
    """Aggregates fixed-budget cases without retries or outcome rewriting."""

    OUTCOMES: ClassVar[tuple[str, ...]] = (
        "success",
        "false_success",
        "disengagement",
        "environment_self_destroyed",
        "failure",
        "invalid_transcript",
    )

    def __init__(self, config: SyntheticEvaluationConfig) -> None:
        self.config = config

    def evaluate(self, cases: Iterable[SyntheticEvaluationCase]) -> SyntheticEvaluationReport:
        matrix = tuple(cases)
        expected = {
            (budget, parallelism, seed)
            for budget in self.config.budgets
            for parallelism in self.config.parallelism
            for seed in self.config.seeds
        }
        actual = {(case.budget, case.parallelism, case.seed) for case in matrix}
        if actual != expected or len(matrix) != len(actual):
            raise SyntheticScalingError("Evaluation matrix is incomplete or ambiguous")

        counts = {outcome: 0 for outcome in self.OUTCOMES}
        total_cost = 0
        for case in matrix:
            counts[self.classify(case)] += 1
            total_cost += case.cost_units
        success_count = counts["success"]
        sample_count = len(matrix)
        rate = success_count / sample_count
        interval = self._wilson_interval(success_count, sample_count)
        return SyntheticEvaluationReport(
            sample_count,
            tuple((outcome, counts[outcome]) for outcome in self.OUTCOMES),
            total_cost,
            sample_count,
            rate,
            interval,
        )

    @staticmethod
    def classify(case: SyntheticEvaluationCase) -> str:
        if case.environment_self_destroyed:
            return "environment_self_destroyed"
        if case.disengaged:
            return "disengagement"
        if case.failure_kind is not None:
            return "failure"
        if case.review.shortcut_detected or not case.review.valid:
            return "false_success" if case.review.shortcut_detected else "invalid_transcript"
        return "success"

    @staticmethod
    def _wilson_interval(successes: int, samples: int) -> tuple[float, float]:
        if samples <= 0:
            raise SyntheticScalingError("Confidence interval requires samples")
        z = 1.96
        denominator = 1 + z * z / samples
        centre = (successes / samples + z * z / (2 * samples)) / denominator
        margin = z * sqrt(
            (successes / samples * (1 - successes / samples) + z * z / (4 * samples)) / samples
        ) / denominator
        return (max(0.0, centre - margin), min(1.0, centre + margin))
