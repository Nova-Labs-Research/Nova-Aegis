# Nova Aegis Phase 76 - Enforceable Boundary Preflight

## Hypothesis

An advisory boundary report is insufficient because callers can ignore a `REFACTOR` decision. A local enforcement gate should reject blocked synthetic continuation and every production request while allowing only explicitly cleared synthetic work.

## Experiment

`SyntheticBoundaryPreflight.enforce` raises for missing controls, invalid modes, and any production request. A report with satisfied local controls can continue only in synthetic mode; `production_enabled` remains false.

## Decision

`ADAPT` for local governance enforcement. The gate is not a protected policy authority, cannot enforce deployment outside the process, and does not authorize real identity, external evidence, distributed recovery, networked MCP, or consequential tools.
