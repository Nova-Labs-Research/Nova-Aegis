# Nova Aegis Phase 62 - Historical Corpus Snapshots

## Experiment

A local snapshot sorts evidence deterministically, records a version and full corpus digest, round-trips through a serialized shape, and refuses rollback or content drift before restoration.

## Decision

`ADAPT` for synthetic local replay only. Snapshot restoration is not historical truth, independent evidence, or protected archival custody.
