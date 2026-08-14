from __future__ import annotations

import pytest

from nova_aegis import profile_pipeline


def test_profile_pipeline_measures_all_explicit_stages() -> None:
    calls: list[str] = []

    def stage(name: str):
        def run() -> None:
            calls.append(name)

        return run

    profile = profile_pipeline(
        retrieval=stage("retrieval"),
        context_assembly=stage("context"),
        prefill=stage("prefill"),
        generation=stage("generation"),
        repeats=3,
        repeated_context=True,
    )

    assert [timing.stage for timing in profile.stages] == [
        "retrieval",
        "context_assembly",
        "prefill",
        "generation",
    ]
    assert all(len(timing.samples_ns) == 3 for timing in profile.stages)
    assert calls == [
        "retrieval",
        "retrieval",
        "retrieval",
        "context",
        "context",
        "context",
        "prefill",
        "prefill",
        "prefill",
        "generation",
        "generation",
        "generation",
    ]
    assert profile.total_ns == sum(timing.total_ns for timing in profile.stages)
    prefill_total = profile.stages[2].total_ns
    assert profile.prefill_share == pytest.approx(prefill_total / profile.total_ns)
    assert profile.repeated_context


def test_profile_pipeline_rejects_nonpositive_repeats() -> None:
    noop = lambda: None

    with pytest.raises(ValueError, match="positive"):
        profile_pipeline(
            retrieval=noop,
            context_assembly=noop,
            prefill=noop,
            generation=noop,
            repeats=0,
        )
