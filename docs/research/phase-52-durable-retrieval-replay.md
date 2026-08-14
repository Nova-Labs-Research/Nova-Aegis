# Nova Aegis Phase 52 - Durable Retrieval-Trace Replay

## Scope

Phase 52 hardens Phase 43 retrieval reconstruction by making retrieval traces serializable and replayable from durable audit records.

This remains a local synthetic control. It does not make hierarchy metadata authoritative, add vector retrieval, or allow stored memory to substitute for current evidence.

## Change

`RetrievalTrace` now supports:

- deterministic dictionary serialization;
- validated deserialization from durable JSON details; and
- replay through `LocalRetriever.replay_trace`.

Replay recomputes retrieval from the persisted question, authority scope, hierarchy scope, candidate corpus, filter stages, ranked identifiers and scores, and selected identifiers. Any mismatch raises `AuditIntegrityError`.

`SQLiteAuditLog` already provides a local append-only hash chain, so a retrieval trace can be persisted as `retrieval_completed` event details and replayed after reopening the database.

## Controlled Results

- A trace persisted through SQLite audit JSON replays to the same citation.
- A tampered selected-source list fails replay.
- A changed source corpus fails replay.
- Audit hash-chain verification continues to protect the durable event record.

## Decision

`ADAPT`

Retain durable trace serialization and deterministic replay as a bounded local auditability capability. Do not treat replay success as proof that the hierarchy metadata, source authority, or audit store is independently trusted.

## Remaining Risks

- The local audit chain is not an immutable external anchor.
- Hierarchy and authority metadata remain caller-supplied and unauthenticated.
- Replay verifies consistency with the current supplied corpus; it does not recreate unavailable historical source content.
- Cross-process and distributed replay semantics remain untested.
