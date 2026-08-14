# Nova Aegis Phase 83 - Durable Synthetic Identity Replay

## Hypothesis

A synthetic identity lifecycle should survive process restart and preserve terminal revocation without relying on in-memory state. Append-only local SQLite events can test replay deterministically.

## Experiment

`SQLiteSyntheticIdentityRegistry` stores registration and revocation events and reconstructs the latest state on every lookup. Registration after revocation is rejected, and closing and reopening the same database preserves active identities.

## Decision

`ADAPT` for local synthetic replay only. SQLite durability does not provide protected retention, tamper resistance, distributed ordering, or organizational identity. Phase 85 remains the next mandatory audit checkpoint.
