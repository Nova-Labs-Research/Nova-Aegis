# Nova Aegis Phase 48 - SIFT Performance Profiling Gate

## Scope

Phase 48 evaluates whether prefill or repeated-context computation is a meaningful local-first bottleneck before attempting any SIFT-like optimization.

This phase adds measurement tooling only. It does not add caching, selective indexing, context reuse, model changes, or retrieval changes.

## Measurement Boundary

`profile_pipeline` measures four explicit stages supplied by the caller:

```text
retrieval -> context_assembly -> prefill -> generation
```

It records per-stage nanosecond samples, totals, averages, total pipeline time, prefill share, and whether the workload intentionally repeats context.

The current `InferenceProvider` exposes only `infer(prompt)`. It does not expose an independently measurable prefill phase, so no production prefill attribution is claimed by this phase.

## Hypothesis

SIFT-like reuse should be prototyped only if measured local workloads show that prefill is a meaningful share of end-to-end latency and repeated context is common enough to justify memory and quality tradeoffs.

## Observed Evidence

- The profiler executes each explicit stage in a fixed order and records repeated samples.
- Repeated-context status is explicit metadata rather than inferred from timing.
- Invalid profile parameters fail closed.
- No runtime optimization or cache was introduced.
- A production prefill bottleneck was **not established** because the current provider boundary does not expose prefill separately.

## Decision

`DEFER`

Retain the profiler as an experiment tool. Do not prototype SIFT-like optimization until a local inference runtime exposes trustworthy prefill instrumentation and a representative repeated-context workload is measured.

## Acceptance Criteria for Reopening

- A representative local workload is defined.
- Retrieval quality, evidence identity, provenance, and audit traces are captured before and after any prototype.
- Prefill share and repeated-context frequency are measured directly.
- RAM, latency, and quality tradeoffs are reported together.
- No cache can substitute remembered context for current evidence or bypass governance.
