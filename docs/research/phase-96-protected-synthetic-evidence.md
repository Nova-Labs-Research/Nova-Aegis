# Nova Aegis Phase 96 - Authenticated Synthetic Evidence Boundary

## Reopening decision

Phase 95 froze future implementation pending deliberate human review. On 2026-08-16, the project owner clarified that the freeze was a weekend pause and explicitly reopened **Phase 96 only**. Phases 97-100 remain frozen. This decision does not change the Phase 95 production blockers or authorize real integrations.

## Hypothesis

Synthetic transcripts and failure receipts can be replayed more safely when every SQLite event is authenticated and chained to the complete prior history. Missing, reordered, modified, malformed, partially written, or signed-by-unknown-key evidence must prevent all replay and further append.

## Experiment

`SQLiteSyntheticEvidenceStore` accepts only `transcript` and `failure_receipt` evidence. Each row contains a canonical JSON payload, monotonic sequence, previous-event digest, key ID, digest, and HMAC-SHA256 signature. Append first verifies the complete existing chain. Replay verifies sequence continuity, unique IDs, canonical payloads, chain links, retained historical keys, digests, and signatures before returning any records.

## Restart and power-loss model

- Each evidence row is committed in one SQLite transaction.
- A committed complete chain can be replayed after reopening the database.
- A missing, malformed, partial, or contradictory row fails closed.
- This does not prove filesystem durability across hardware failure, guarantee `fsync` behavior, or recover an interrupted external storage layer.

## Retention assumptions

- The complete event history and every historical verification key must remain available.
- Events are append-only through the public API; deletion and compaction are unsupported.
- Database files, backups, and process-local keys are not protected custody or immutable retention.
- Direct database access can corrupt or delete evidence; verification detects tested corruption but cannot prevent it.

## Evidence

Six focused tests cover restart replay, payload tampering, missing middle events, unknown historical keys, append refusal after corruption, duplicate IDs, invalid evidence types, and partial rows.

## Decision

`ADAPT` for authenticated local synthetic evidence only. Phase 96 reduces undetected local corruption risk but does not provide protected authority, independent evidence, protected key custody, immutable storage, distributed ordering, or production recovery. Phases 97-100 remain frozen pending separate human review.