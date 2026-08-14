# Nova Aegis Phase 78 - Durable Signed Boundary Replay

## Hypothesis

A signed boundary decision must remain reviewable after process restart without becoming mutable deployment authority. Append-only local persistence should replay the exact decision and fail closed on report drift, conflicting content, revocation, unknown keys, malformed events, or signature failure.

## Experiment

`SQLiteBoundaryDecisionStore` persists registration and revocation events. Replay reconstructs the signed decision, rejects revoked or malformed state, verifies the injected signing key, and compares the decision to the exact preflight report.

## Decision

`ADAPT` for synthetic local durability and auditability. SQLite persistence does not establish protected retention, power-loss durability, distributed policy consistency, or production authorization.
