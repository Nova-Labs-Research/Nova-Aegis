# Nova Aegis Phase 92 - Outcome Validity and Shortcut Resistance

## Hypothesis

A synthetic evaluation can report success safely only when an independent reviewer observes one exact goal signal emitted by the boundary. Subject self-attestation, fixture leakage, evaluator-authored signals, alternate paths, and malformed transcripts must not count as success.

## Experiment

`SyntheticOutcomeReviewer` reviews an immutable in-memory transcript against a `SyntheticGoalSignal`. A valid result requires exactly one event from the `boundary` source with event type `goal_signal` and exact capability, operation, and value equality. Subject, fixture, and evaluator sources, shortcut event types, duplicate signals, wrong values, missing signals, and ambiguous sequence numbers fail closed.

## Evidence

The focused Phase 92 tests cover the exact success path and adversarial negative controls. The reviewer returns a structured result containing validity, reason, signal observation, shortcut detection, and event count for audit-oriented callers.

## Decision

`ADAPT` for benign synthetic evaluation only. The transcript remains caller-supplied and process-local, so this does not prove independent evidence, prevent a compromised host from fabricating events, establish real containment, or support generalized agent capability claims. Durable append-only transcripts and independent witness verification remain future work.
