# Nova Aegis Phase 44 - Memory Integrity and Reliability Boundary

## Scope

Phase 44 tests whether degraded evidence and operational history reduce assurance conservatively. It also introduces an isolated local reliability-memory record for future routing experiments without connecting reliability to factual truth.

## Perturbation Matrix

| Perturbation | Expected behavior | Observed control |
|---|---|---|
| Stale evidence | `REVIEW`, no answer | Passed by existing assurance test |
| Poisoned or instruction-like evidence | Evidence remains untrusted; `REVIEW` | Passed by adversarial test |
| Contradictory claims | `REVIEW`, no silent collapse | Passed by conflict test |
| Unverified provenance | `REVIEW` | Passed by provenance test |
| Incorrect authority | Excluded when an explicit scope is supplied | Passed by Phase 43 scope test |
| Semantic-neighbor wrong hierarchy | Excluded before ranking | Passed by Phase 43 scope test |
| Reliability history | May describe operational performance only; cannot alter factual assurance | Passed by isolation test |

## Change

`LocalReliabilityMemory` stores append-only synthetic operational records keyed by subject and task class. It exposes history and success rate for future routing experiments. It is deliberately not accepted by `Evidence`, `Citation`, `Praetor`, `AgentK`, or response assurance.

## Hypothesis

As evidence integrity decreases, uncertainty and human review increase. Historical reliability may eventually improve routing, but it must not become factual evidence, provenance, or a proxy for claim truth.

## Observed Evidence

- Existing stale, unverified, poisoned, and contradictory evidence tests remain fail-closed.
- Authority and hierarchy scope controls exclude wrong-boundary semantic neighbors before ranking.
- Reliability history can be recorded and queried without changing the factual response or adding reliability fields to citations.
- No reliability signal is currently used to select evidence or authorize actions.

## Decision

`ADAPT` the explicit separation boundary and retain reliability history as an isolated experiment surface. Do not use reliability to change evidence scores, assurance outcomes, approval requirements, or factual claims.

## Remaining Risks

- The reliability store is process-local and synthetic.
- Reliability outcomes are caller-supplied and not independently witnessed.
- No routing experiment has demonstrated benefit, calibration, fairness, or resistance to poisoning.
- Memory integrity remains dependent on provenance and authority metadata that are not externally authenticated in the synthetic profile.

## Phase 45 Input

The mandatory audit must review the combined Phase 40-44 changes, confirm fail-closed behavior, and retain `REFACTOR` requirements for protected identity, key custody, distributed coordination, independent external evidence, and networked MCP boundaries.
