# Nova Aegis Phase 79 - Decision Revocation and Supersession

## Hypothesis

Append-only decision history needs explicit lifecycle semantics. Revocation must remain terminal, while a non-revoked decision may be replaced only by a signed successor for the same boundary. Replay must return only the current successor and reject stale reports.

## Experiment

`SQLiteBoundaryDecisionStore.supersede` appends a successor event. It rejects missing decisions, revoked predecessors, cross-boundary successors, and identical content. Replay reconstructs the latest decision event and verifies it against the successor report and injected key.

## Decision

`ADAPT` for synthetic local lifecycle testing. This does not provide protected revocation authority, distributed supersession ordering, organizational policy approval, or production deployment enforcement.
