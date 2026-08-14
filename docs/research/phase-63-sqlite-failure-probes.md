# Nova Aegis Phase 63 - SQLite Failure Probes

## Experiment

Use the existing verified SQLite replay boundary as the recovery subject. Malformed serialized traces, digest mismatches, and tampered audit chains must fail closed rather than produce a replay result. This phase records the failure-probe contract without simulating a false guarantee of power-loss durability.

## Decision

`CONTINUE` with the existing local boundary. Actual power-loss and filesystem recovery remain deployment-specific prerequisites and are not claimed by synthetic tests.
