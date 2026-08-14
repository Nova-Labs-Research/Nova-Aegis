# Nova Aegis Phase 73 - Witness Conflict Arbitration

## Experiment

A synthetic arbiter requires a configured number of distinct witness identities. Each attestation is verified against its witness key; duplicate, unknown, invalid, or insufficient attestations fail closed.

## Decision

`ADAPT` for local contradiction handling. A quorum of injected local keys is not independent evidence, and no external action replay or consequential recovery is enabled.
