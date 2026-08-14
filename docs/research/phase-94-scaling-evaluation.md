# Nova Aegis Phase 94 - Persistence, Scaling, and False-Success Evaluation

## Hypothesis

Repeated synthetic attempts should be compared with a fixed budget, parallelism, and deterministic seed matrix. Valid success, false success, disengagement, environment self-destruction, execution failure, and invalid transcripts must remain separate, with cost and attempt counts reported explicitly.

## Experiment

`SyntheticScalingEvaluator` validates a complete matrix of budget, parallelism, and unique seed cells. It aggregates immutable case observations, classifies outcomes using Phase 92 review evidence and Phase 93 failure state, accounts for cost units and attempts, and reports a deterministic Wilson interval for valid success rate. It does not retry, rewrite, or infer success from self-attestation.

## Evidence

Focused tests cover complete-matrix accounting, false-success detection, distinct failure classes, invalid transcript classification, missing matrix cells, and ambiguous case state.

## Decision

`ADAPT` for bounded synthetic measurement only. The evaluator does not run real parallel workloads, establish persistence across process loss, provide frontier capability measurements, or prove statistical independence. Further work is frozen pending later human review and the Phase 100 audit gate.
