from __future__ import annotations

from nova_aegis import (
    SyntheticGoalSignal,
    SyntheticOutcomeReviewer,
    SyntheticTranscriptEvent,
)


def _reviewer() -> SyntheticOutcomeReviewer:
    return SyntheticOutcomeReviewer(SyntheticGoalSignal("goal-1", "echo", "echo", {"ok": True}))


def _goal_event() -> SyntheticTranscriptEvent:
    return SyntheticTranscriptEvent(1, "boundary", "goal_signal", "echo", "echo", {"ok": True})


def test_exact_boundary_goal_signal_is_valid() -> None:
    review = _reviewer().review((_goal_event(),))

    assert review.valid is True
    assert review.goal_signal_observed is True
    assert review.shortcut_detected is False


def test_subject_self_report_does_not_count_as_success() -> None:
    review = _reviewer().review(
        (SyntheticTranscriptEvent(1, "subject", "self_attested_success"),)
    )

    assert review.valid is False
    assert review.shortcut_detected is True


def test_fixture_and_evaluator_paths_are_shortcuts() -> None:
    for source in ("fixture", "evaluator"):
        review = _reviewer().review(
            (SyntheticTranscriptEvent(1, source, "goal_signal", "echo", "echo", {"ok": True}),)
        )
        assert review.valid is False
        assert review.shortcut_detected is True


def test_wrong_signal_missing_signal_and_duplicate_signal_fail_closed() -> None:
    wrong = SyntheticTranscriptEvent(1, "boundary", "goal_signal", "echo", "echo", {"ok": False})
    assert _reviewer().review((wrong,)).valid is False
    assert _reviewer().review((SyntheticTranscriptEvent(1, "boundary", "observation"),)).valid is False
    assert _reviewer().review((_goal_event(), _goal_event())).valid is False


def test_ambiguous_transcript_order_fails_closed() -> None:
    events = (
        SyntheticTranscriptEvent(2, "boundary", "observation"),
        _goal_event(),
    )

    review = _reviewer().review(events)

    assert review.valid is False
    assert "sequence" in review.reason
