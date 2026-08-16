# Nova Aegis Phases 96-100 - Frozen Research Map

## Status

Phase 96 was explicitly reopened by human decision on 2026-08-16 after the project owner clarified that the Phase 95 freeze was a weekend pause. **Phases 97-100 remain frozen.** Reopening any later phase requires a separate deliberate human review, preservation of the Phase 95 production blockers, and a new focused scope decision.

## Sequence

| Phase | Focus | Research question | Required evidence | Gate |
|---|---|---|---|---|
| 96 | Authenticated synthetic evidence boundary | Can synthetic transcripts and failure receipts be persisted with authenticated integrity and explicit corruption refusal? | Append-only SQLite event chain, restart/power-loss model, tamper tests, retention assumptions | Implemented locally; no protected authority claim |
| 97 | Independent synthetic witness | Can a distinct local witness verify outcome and failure evidence without sharing the evaluator's signing or storage path? | Exact binding, witness separation, quorum/refusal tests, conflict handling | No independent external evidence claim |
| 98 | Bounded workload coordination | Can fixed-budget attempts be coordinated across local workers without hidden retry, duplicate accounting, or ambiguous ownership? | Explicit leases, deterministic scheduling, crash/timeout matrix, no-replay receipts | No distributed reliability claim |
| 99 | Pre-production boundary review | Can all synthetic evidence and unresolved blockers be reviewed against a proposed integration boundary without silently expanding authority? | Threat-model delta, interface contract, human approval, rollback/refusal plan, deployment blocker checklist | No production enablement |
| 100 | Mandatory audit and freeze review | Does evidence from Phases 95-99 justify reopening any scope, or do blockers remain? | Full regression, integrity review, debt disposition, explicit gate, roadmap decision | Audit gate |

## Dependencies and constraints

- Phase 96 depends on the existing local receipt, witness, identity, and audit schemas but must not treat local signatures as protected custody.
- Phase 97 must preserve distinct signer/witness identities and must refuse self-witnessing, conflicting attestations, and missing evidence.
- Phase 98 must not introduce network transport or automatic action replay; local coordination remains synthetic unless separately approved.
- Phase 99 is review-only unless a human-approved integration scope exists. It must not create production credentials, real data access, or consequential tools.
- Phase 100 is the next mandatory audit and may close, defer, or narrowly reopen work. It does not authorize production by default.

## Freeze rules

1. Do not implement Phase 97-100 code from this map without a new explicit phase request and human review.
2. Do not change the `FREEZE` gate, production hard-disable, or next-audit checkpoint through roadmap edits alone.
3. Any boundary expansion, invariant failure, serious security event, or runtime replacement triggers an earlier audit and pauses work.
4. Research notes must distinguish local metadata, independent evidence, protected custody, and deployment enforcement.
