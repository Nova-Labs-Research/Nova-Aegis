# Nova Aegis Phase 72 - Durable Witness Retention

## Experiment

Receipt witness attestations are persisted as append-only SQLite events. Close/reopen replay restores the attestation, duplicate content is idempotent, conflicting content is rejected, and revocation blocks later verification.

## Decision

`ADAPT` for local durability testing. SQLite replay does not establish power-loss durability, protected retention, failover, or independent external evidence.
