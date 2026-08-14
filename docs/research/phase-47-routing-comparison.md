# Nova Aegis Phase 47 - Fixed-Workload Routing Comparison

## Scope

Phase 47 compares deterministic baseline routing with reliability-aware routing over the same fixed synthetic workload. The experiment measures routing accuracy and conservative fallback behavior without changing evidence, provenance, assurance, approval, or execution decisions.

## Workload

The workload contains three cases:

1. A fresh-history case where the non-baseline candidate has the higher success rate.
2. A missing-history case where baseline routing must be retained.
3. An unchanged single-candidate case where routing cannot change.

Each case has a unique identifier, fixed candidates, task class, expected subject, evaluation time, and maximum history age.

## Observed Results

| Metric | Result |
|---|---:|
| Baseline accuracy | `2/3` |
| Reliability-aware accuracy | `3/3` |
| Accuracy delta | `+1/3` |
| Reliability-driven route changes | `1` |
| Conservative fallbacks | `2` |

The result is deterministic and reproducible from the fixed workload and local reliability records.

## Safety Checks

- Identical factual inputs are not modified by routing metadata.
- Reliability remains outside evidence, provenance, claims, and assurance.
- Missing history retains the baseline route.
- Duplicate workload identifiers are rejected.
- No routing decision authorizes a tool, changes approval requirements, or increases autonomy.

## Decision

`ADAPT`

Retain the fixed-workload replay evaluator as an experiment and measurement tool. The observed synthetic improvement justifies continued controlled evaluation, but not production reliability-driven routing. The workload is too small to establish calibration, fairness, poisoning resistance, or general utility.

## Required Follow-up

Before adoption, expand the replay corpus with adversarial and representative cases, measure review burden and false routing, test fabricated and stale history, and prove that reliability cannot alter factual assurance or governance outcomes. Phase 48 should remain performance profiling only if SIFT is still justified by measured latency evidence.
