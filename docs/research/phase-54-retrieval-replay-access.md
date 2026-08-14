# Nova Aegis Phase 54 - Verified Retrieval Replay Access

## Scope

Phase 54 makes the durable replay path explicit at the SQLite audit boundary. Reviewers can retrieve only `retrieval_completed` traces after the audit hash chain has been verified, close the writer, reopen the database, and replay against a supplied local corpus.

## Change

`SQLiteAuditLog.retrieval_traces()`:

- verifies the complete local hash chain before reading trace records;
- returns only retrieval trace mappings from retrieval-completed events; and
- fails closed when a retrieval event does not contain a mapping-shaped trace.

The replay contract also covers altered authority scopes. A scope change with a recomputed trace digest still fails because the recorded corpus and trace metadata no longer match the replayed selection.

## Controlled Results

- A trace survives SQLite close and reopen.
- The verified accessor returns the durable trace without exposing unrelated audit events.
- Scope alteration fails closed.
- Existing audit tampering detection remains in force before trace access.

## Decision

`ADAPT`

Keep verified durable replay as a reviewer-facing local capability. Do not interpret successful reopening or hash-chain verification as distributed durability, authenticated hierarchy, independent evidence, or permission to replay external actions.

## Remaining Risks

- SQLite remains process-local and lacks distributed failover semantics.
- The local hash-chain root is not independently anchored.
- Caller-supplied scopes are not organizationally authenticated.
- This feature replays retrieval computation only; it never replays tools, handlers, or external effects.
