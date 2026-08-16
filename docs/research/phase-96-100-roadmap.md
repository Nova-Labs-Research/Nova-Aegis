# Nova Aegis Phases 96-100 - Research Map

## Status

On 2026-08-16, the project owner clarified that the Phase 95 freeze was a weekend break and explicitly authorized continued work. Phases 96-100 are unfrozen under the existing synthetic-only constraints. The Phase 95 production blockers and Phase 100 mandatory audit remain unchanged.

## Sequence

| Phase | Focus | Research question | Required evidence | Gate |
|---|---|---|---|---|
| 96 | Authenticated synthetic evidence boundary | Can synthetic transcripts and failure receipts be persisted with authenticated integrity and explicit corruption refusal? | Append-only SQLite event chain, restart/power-loss model, tamper tests, retention assumptions | Implemented locally; no protected authority claim |
| 97 | Independent synthetic witness | Can a distinct local witness verify outcome and failure evidence without sharing the evaluator's signing or storage path? | Exact binding, witness separation, quorum/refusal tests, conflict handling | Implemented locally; no independent external evidence claim |
| 98 | Bounded workload coordination | Can fixed-budget attempts be coordinated across local workers without hidden retry, duplicate accounting, or ambiguous ownership? | Explicit leases, deterministic scheduling, crash/timeout matrix, no-replay receipts | Implemented locally; no distributed reliability claim |
| 99 | Pre-production boundary review | Can all synthetic evidence and unresolved blockers be reviewed against a proposed integration boundary without silently expanding authority? | Threat-model delta, interface contract, human approval, rollback/refusal plan, deployment blocker checklist | Completed review-only; `BLOCKED` |
| 100 | Mandatory audit and gate review | Does evidence from Phases 95-99 justify reopening any scope, or do blockers remain? | Full regression, integrity review, debt disposition, explicit gate, roadmap decision | Completed; `CONTINUE_SYNTHETIC`, pre-production `BLOCKED` |

## Dependencies and constraints

- Phase 96 depends on the existing local receipt, witness, identity, and audit schemas but must not treat local signatures as protected custody.
- Phase 97 must preserve distinct signer/witness identities and must refuse self-witnessing, conflicting attestations, and missing evidence.
- Phase 98 must not introduce network transport or automatic action replay; local coordination remains synthetic unless separately approved.
- Phase 99 is review-only unless a human-approved integration scope exists. It must not create production credentials, real data access, or consequential tools.
- Phase 100 completed the mandatory audit and did not authorize production. Phase 105 is the next mandatory audit if a bounded Phase 101-104 roadmap is approved.

## Continuation rules

1. Implement each remaining phase as a separate bounded change with focused adversarial evidence.
2. Do not change the production hard-disable or next-audit checkpoint through roadmap edits alone.
3. Any boundary expansion, invariant failure, serious security event, or runtime replacement triggers an earlier audit and pauses work.
4. Research notes must distinguish local metadata, independent evidence, protected custody, and deployment enforcement.
