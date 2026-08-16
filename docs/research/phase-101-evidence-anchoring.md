# Nova Aegis Phase 101 - Signed Evidence Anchoring

## Objective

Address AUD100-001 by detecting tail deletion, complete evidence deletion, anchor rollback, and unanchored history when the evidence database and checkpoint history are retained separately.

## Implementation

`AnchoredSQLiteSyntheticEvidenceStore` wraps the Phase 96 store. After each evidence append, `SQLiteSyntheticEvidenceAnchorStore` writes a separately signed checkpoint containing the store ID, event count, terminal evidence digest, previous anchor digest, and key ID. Replay returns evidence only when the complete evidence history matches the latest authenticated checkpoint. Evidence payloads now reject non-finite JSON values.

The evidence row is committed before its anchor. Interruption between those commits leaves unanchored evidence and causes refusal rather than silent acceptance.

## Evidence

Six focused Phase 101 tests cover restart replay, tail deletion, complete evidence deletion, anchor rollback/deletion, anchor signature tampering, unanchored history, append refusal after corruption, and non-finite JSON.

## Decision

`ADAPT` for local anchored synthetic evidence. AUD100-001 is mitigated when anchor storage survives independently. Deletion or rollback of both local databases together remains undetectable without protected external retention, so immutable anchoring remains a Phase 104 blocker.