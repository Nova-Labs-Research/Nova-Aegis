"""Measurement-only profiling for local retrieval and inference experiments."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Callable


@dataclass(frozen=True)
class StageTiming:
    stage: str
    samples_ns: tuple[int, ...]
    total_ns: int
    average_ns: float


@dataclass(frozen=True)
class PipelineProfile:
    stages: tuple[StageTiming, ...]
    total_ns: int
    prefill_share: float
    repeated_context: bool


StageFunction = Callable[[], object]


def profile_pipeline(
    *,
    retrieval: StageFunction,
    context_assembly: StageFunction,
    prefill: StageFunction,
    generation: StageFunction,
    repeats: int = 1,
    repeated_context: bool = False,
) -> PipelineProfile:
    """Measure explicit pipeline stages without changing their behavior."""
    if repeats < 1:
        raise ValueError("Profile repeats must be positive")
    functions = (
        ("retrieval", retrieval),
        ("context_assembly", context_assembly),
        ("prefill", prefill),
        ("generation", generation),
    )
    timings: list[StageTiming] = []
    for name, function in functions:
        samples: list[int] = []
        for _ in range(repeats):
            started = time.perf_counter_ns()
            function()
            samples.append(time.perf_counter_ns() - started)
        total = sum(samples)
        timings.append(StageTiming(name, tuple(samples), total, total / repeats))
    total_ns = sum(timing.total_ns for timing in timings)
    prefill_ns = next(timing.total_ns for timing in timings if timing.stage == "prefill")
    return PipelineProfile(
        stages=tuple(timings),
        total_ns=total_ns,
        prefill_share=prefill_ns / total_ns if total_ns else 0.0,
        repeated_context=repeated_context,
    )
