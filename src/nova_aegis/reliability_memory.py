"""Non-authoritative operational history for synthetic routing experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class ReliabilityRecord:
    subject_id: str
    task_class: str
    outcome: str
    observed_at: int


@dataclass(frozen=True)
class RoutingDecision:
    selected_subject: str
    baseline_subject: str
    used_reliability: bool
    reason: str
    success_rates: tuple[tuple[str, float], ...]
    candidate_subjects: tuple[str, ...] = ()
    eligible_subjects: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RoutingWorkloadCase:
    case_id: str
    subjects: tuple[str, ...]
    task_class: str
    expected_subject: str
    now: int
    max_age: int


@dataclass(frozen=True)
class RoutingExperimentResult:
    case_ids: tuple[str, ...]
    baseline_accuracy: float
    reliability_accuracy: float
    accuracy_delta: float
    reliability_changes: int
    fallback_count: int
    baseline_subjects: tuple[str, ...]
    reliability_subjects: tuple[str, ...]
    false_route_changes: int = 0
    genuine_improvements: int = 0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class LocalReliabilityMemory:
    """Append-only reliability history; never evidence, provenance, or assurance input."""

    def __init__(self, records: Iterable[ReliabilityRecord] = ()) -> None:
        self._records = list(records)

    def record(self, entry: ReliabilityRecord) -> None:
        if not entry.subject_id.strip() or not entry.task_class.strip():
            raise ValueError("Reliability records require a subject and task class")
        if entry.outcome.casefold() not in {"success", "failure"}:
            raise ValueError("Reliability outcome must be success or failure")
        if entry.observed_at < 0:
            raise ValueError("Reliability observation time cannot be negative")
        self._records.append(entry)

    def history(self, subject_id: str, task_class: str) -> tuple[ReliabilityRecord, ...]:
        return tuple(
            entry
            for entry in self._records
            if entry.subject_id == subject_id and entry.task_class == task_class
        )

    def success_rate(self, subject_id: str, task_class: str) -> float | None:
        entries = self.history(subject_id, task_class)
        if not entries:
            return None
        successes = sum(entry.outcome.casefold() == "success" for entry in entries)
        return successes / len(entries)

    def route(
        self,
        subjects: Iterable[str],
        task_class: str,
        *,
        now: int,
        max_age: int,
        minimum_observations: int = 2,
    ) -> RoutingDecision:
        candidates = tuple(dict.fromkeys(subjects))
        if not candidates:
            raise ValueError("At least one routing subject is required")
        if not task_class.strip() or now < 0 or max_age < 0 or minimum_observations < 1:
            raise ValueError("Invalid routing experiment parameters")
        baseline = candidates[0]
        rates: list[tuple[str, float]] = []
        for subject in candidates:
            entries = self.history(subject, task_class)
            if len(entries) < minimum_observations:
                continue
            if any(now - entry.observed_at > max_age for entry in entries):
                continue
            successes = sum(entry.outcome.casefold() == "success" for entry in entries)
            rates.append((subject, successes / len(entries)))
        eligible_subjects = tuple(subject for subject, _ in rates)
        if not rates:
            return RoutingDecision(
                selected_subject=baseline,
                baseline_subject=baseline,
                used_reliability=False,
                reason="Reliability history is missing or stale; baseline routing retained",
                success_rates=(),
                candidate_subjects=candidates,
                eligible_subjects=eligible_subjects,
            )
        best_rate = max(rate for _, rate in rates)
        best = tuple(subject for subject, rate in rates if rate == best_rate)
        if len(best) != 1:
            return RoutingDecision(
                selected_subject=baseline,
                baseline_subject=baseline,
                used_reliability=False,
                reason="Reliability history is tied or ambiguous; baseline routing retained",
                success_rates=tuple(rates),
                candidate_subjects=candidates,
                eligible_subjects=eligible_subjects,
            )
        return RoutingDecision(
            selected_subject=best[0],
            baseline_subject=baseline,
            used_reliability=best[0] != baseline,
            reason="Fresh reliability history selected the highest observed success rate",
            success_rates=tuple(rates),
            candidate_subjects=candidates,
            eligible_subjects=eligible_subjects,
        )

    def replay(
        self, workload: Iterable[RoutingWorkloadCase], *, minimum_observations: int = 2
    ) -> RoutingExperimentResult:
        cases = tuple(workload)
        if not cases:
            raise ValueError("Routing workload must contain at least one case")
        if len({case.case_id for case in cases}) != len(cases):
            raise ValueError("Routing workload case IDs must be unique")
        decisions = tuple(
            self.route(
                case.subjects,
                case.task_class,
                now=case.now,
                max_age=case.max_age,
                minimum_observations=minimum_observations,
            )
            for case in cases
        )
        baseline_subjects = tuple(case.subjects[0] for case in cases)
        reliability_subjects = tuple(decision.selected_subject for decision in decisions)
        baseline_hits = sum(
            subject == case.expected_subject
            for subject, case in zip(baseline_subjects, cases)
        )
        reliability_hits = sum(
            subject == case.expected_subject
            for subject, case in zip(reliability_subjects, cases)
        )
        changed_decisions = tuple(
            decision.used_reliability for decision in decisions
        )
        false_route_changes = sum(
            changed and selected != case.expected_subject
            for changed, selected, case in zip(changed_decisions, reliability_subjects, cases)
        )
        genuine_improvements = sum(
            changed
            and selected == case.expected_subject
            and baseline != case.expected_subject
            for changed, baseline, selected, case in zip(
                changed_decisions, baseline_subjects, reliability_subjects, cases
            )
        )
        return RoutingExperimentResult(
            case_ids=tuple(case.case_id for case in cases),
            baseline_accuracy=baseline_hits / len(cases),
            reliability_accuracy=reliability_hits / len(cases),
            accuracy_delta=(reliability_hits - baseline_hits) / len(cases),
            reliability_changes=sum(changed_decisions),
            fallback_count=sum(not decision.used_reliability for decision in decisions),
            baseline_subjects=baseline_subjects,
            reliability_subjects=reliability_subjects,
            false_route_changes=false_route_changes,
            genuine_improvements=genuine_improvements,
        )

    @property
    def records(self) -> tuple[ReliabilityRecord, ...]:
        return tuple(self._records)
