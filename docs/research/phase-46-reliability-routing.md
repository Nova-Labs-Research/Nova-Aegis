# Nova Aegis Phase 46 - Controlled Reliability-Aware Routing Experiment

## Scope

Phase 46 tests whether non-authoritative reliability history can improve routing while factual evidence, provenance, assurance, approvals, and tool execution remain unchanged.

This is a local synthetic experiment. Reliability is not evidence and is not connected to `Evidence`, `Citation`, `AgentK`, `Praetor`, or MCP execution.

## Experimental Contract

`LocalReliabilityMemory.route` compares a fixed candidate list against the first candidate as the deterministic baseline.

Reliability may select a different candidate only when:

- the history has the minimum required observations;
- observations are fresh under the supplied age bound;
- outcomes are valid `success` or `failure` values; and
- exactly one candidate has the highest observed success rate.

Missing, stale, tied, or ambiguous history retains the baseline route. Invalid outcomes are rejected rather than interpreted.

## Hypothesis

Fresh reliability history can reduce routing to historically weaker candidates without becoming a proxy for factual truth, provided uncertain history falls back to the baseline and the routing result remains separate from assurance.

## Controlled Results

- A candidate with a higher fresh success rate is selected over the baseline candidate.
- Missing history retains the baseline route.
- Stale history retains the baseline route.
- Tied history retains the baseline route.
- Invalid or poisoned outcome labels are rejected.
- The same evidence receives the same factual assurance independently of reliability records.

## Decision

`EXPERIMENT`

The routing mechanism is suitable for continued measurement, but not adoption. The current test demonstrates control separation and a possible routing signal; it does not establish real-world utility, calibration, fairness, or resistance to an operator who fabricates history.

## Acceptance Status

- Fresh-history routing benefit: **demonstrated synthetically**.
- Missing/stale/ambiguous fallback: **passed**.
- Invalid-history rejection: **passed**.
- Factual assurance isolation: **passed**.
- Poisoning resistance: **not established beyond invalid-label rejection**.
- Calibration and fairness: **not measured**.
- Durable or independently witnessed reliability: **not implemented**.

## Required Follow-up

Phase 47 should compare baseline and reliability-aware routing over a fixed replay workload and decide `ADOPT`, `ADAPT`, `DEFER`, or `REJECT`. The comparison must measure routing quality and review burden while proving identical evidence and assurance outcomes for identical factual inputs.
