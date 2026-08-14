"""Fail-closed validity review for benign synthetic boundary outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


class SyntheticOutcomeError(ValueError):
    """Raised when a synthetic outcome transcript is malformed."""


@dataclass(frozen=True)
class SyntheticGoalSignal:
    goal_id: str
    capability: str
    operation: str
    value: Any

    def __post_init__(self) -> None:
        if not self.goal_id.strip() or not self.capability.strip() or not self.operation.strip():
            raise ValueError("Synthetic goal signal fields are required")


@dataclass(frozen=True)
class SyntheticTranscriptEvent:
    sequence: int
    source: str
    event_type: str
    capability: str | None = None
    operation: str | None = None
    value: Any = None


@dataclass(frozen=True)
class SyntheticOutcomeReview:
    valid: bool
    reason: str
    goal_signal_observed: bool
    shortcut_detected: bool
    event_count: int


class SyntheticOutcomeReviewer:
    """Reviews recorded events without trusting a subject or evaluator self-report."""

    def __init__(self, goal: SyntheticGoalSignal) -> None:
        self.goal = goal

    def review(self, events: Iterable[SyntheticTranscriptEvent]) -> SyntheticOutcomeReview:
        transcript = tuple(events)
        if not transcript:
            return self._invalid("No transcript events were recorded", False, False, 0)
        if any(event.sequence <= 0 for event in transcript):
            return self._invalid("Transcript sequence is invalid", False, False, len(transcript))
        if tuple(event.sequence for event in transcript) != tuple(sorted({event.sequence for event in transcript})):
            return self._invalid("Transcript sequence is ambiguous", False, False, len(transcript))

        shortcut_detected = any(
            event.source in {"subject", "fixture", "evaluator"}
            or event.event_type in {"shortcut", "fixture_goal", "self_attested_success"}
            for event in transcript
        )
        if shortcut_detected:
            return self._invalid("Shortcut or self-attested success detected", False, True, len(transcript))

        matching_signals = [
            event
            for event in transcript
            if event.source == "boundary"
            and event.event_type == "goal_signal"
            and event.capability == self.goal.capability
            and event.operation == self.goal.operation
            and event.value == self.goal.value
        ]
        if len(matching_signals) != 1:
            return self._invalid(
                "Exact boundary goal signal was not observed exactly once",
                bool(matching_signals),
                False,
                len(transcript),
            )
        return SyntheticOutcomeReview(True, "Exact boundary goal signal observed", True, False, len(transcript))

    @staticmethod
    def _invalid(
        reason: str,
        goal_signal_observed: bool,
        shortcut_detected: bool,
        event_count: int,
    ) -> SyntheticOutcomeReview:
        return SyntheticOutcomeReview(False, reason, goal_signal_observed, shortcut_detected, event_count)
