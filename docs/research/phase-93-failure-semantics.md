# Nova Aegis Phase 93 - Crash and Destructive-Failure Semantics

## Hypothesis

A synthetic boundary evaluation must classify a crashed, hung, corrupted, self-invalidated, or unavailable attempt as a terminal failure. Recording the failure must not trigger hidden retry, silent repair, or automatic replay.

## Experiment

`SyntheticFailureLedger` accepts a positive bounded timeout and tracks unique attempts. It records one append-only `SyntheticFailureReceipt` for the fixed failure taxonomy: `crash`, `timeout`, `corruption`, `self_invalidated`, and `unavailable`. The receipt captures the attempt, failure detail, timeout budget, and teardown-verification state. Unknown attempts, invalid failure kinds, duplicate terminal failures, and replay requests fail closed.

## Evidence

The focused Phase 93 tests exercise every failure kind, bounded timeout validation, unknown and invalid state, duplicate terminal recording, immutable receipt exposure, teardown verification, and explicit replay refusal.

## Decision

`ADAPT` for benign synthetic failure accounting only. The ledger is process-local and not durable protected storage; it does not provide crash recovery, timeout enforcement for arbitrary code, repair, external coordination, or production recovery assurance. Phase 94 may use the receipt contract for explicit repeated-attempt accounting.
