# Nova Aegis Phase 49 - Experiment Hardening and Decision Provenance

## Scope

Phase 49 hardens the Phase 43-48 research tooling before the Phase 50 mandatory audit. It does not introduce a new runtime authority or enable reliability-driven production routing.

## Changes

Reliability routing decisions now expose:

- the complete candidate subject list;
- the subset with sufficiently fresh and valid history;
- the observed success rates;
- the selected subject and baseline subject;
- whether reliability changed the route; and
- the conservative fallback reason.

Routing decisions and fixed-workload replay results provide stable dictionary serialization for audit and research records. The serialization is explanatory metadata only; it does not authorize execution or alter factual assurance.

## Hardening Hypothesis

A routing experiment is safer to evaluate when a reviewer can reconstruct not only the selected subject, but also which candidates were considered eligible and why baseline routing was retained.

## Observed Evidence

- Existing routing behavior remains unchanged.
- Missing and stale history records all candidates but no eligible subjects.
- Fresh history records the eligible subjects and success rates used for selection.
- Fixed-workload results retain their case IDs and measured subjects when serialized.
- Factual evidence and assurance remain outside the routing decision contract.

## Decision

`ADAPT`

Adopt the reconstruction and serialization hardening for synthetic research tooling. Do not connect the result to Praetor, MCP execution, approval authority, evidence scoring, or autonomous action.

## Remaining Risks

- Reliability records remain local, caller-supplied, and unauthenticated.
- Serialization is not an immutable external audit anchor.
- The experiment still lacks representative workload coverage, poisoning resistance, calibration, fairness, and independent witnessing.
- SIFT-like optimization remains deferred because prefill is not independently exposed or measured.

## Phase 50 Input

The mandatory audit should review Phases 45-49, confirm the synthetic-only gate, and decide whether any research result is mature enough for a new controlled experiment or whether further evidence is required.
