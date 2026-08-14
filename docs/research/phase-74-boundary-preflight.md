# Nova Aegis Phase 74 - Boundary Preflight

## Experiment

A deterministic synthetic preflight reports missing controls by boundary. Any missing control produces `REFACTOR`; complete local controls produce only `CONTINUE_SYNTHETIC`. The report cannot enable production.

## Decision

`CONTINUE` as a governance guard. This makes blockers explicit and reviewable without weakening the existing synthetic-only gate.
