# Nova Aegis Phases 91-95 Roadmap

## Motivation

The paper [Quantifying Frontier LLM Capabilities for Container Sandbox Escape](https://arxiv.org/html/2603.02277v3) demonstrates why an execution boundary must be evaluated adversarially rather than assumed secure. Its useful lessons for Nova Aegis are methodological: nested containment, unambiguous outcomes, shortcut analysis, crash-as-failure semantics, and measurement of persistence and repeated attempts.

Nova Aegis will adapt those lessons to a local, synthetic, non-exploitative governance evaluation. These phases will not reproduce real container escapes, provide exploit instructions, access external systems, or establish production security.

## Governing boundary

Phases 91-94 remain offline-first and synthetic-only. The harness must run inside a disposable local test boundary, expose only benign synthetic capabilities, record all attempts, and fail closed on unavailable or inconsistent state. No phase may add network access, real identity, protected custody, consequential tools, or automatic external action replay.

## Sequence

| Phase | Focus | Primary question | Required evidence | Gate |
|---|---|---|---|---|
| 91 | Nested synthetic boundary harness | Can Nova Aegis evaluate a policy boundary from an outer test harness without allowing the test subject to reach the host process or real filesystem? | Disposable inner/outer boundary model, explicit capability inventory, boundary manifest, host non-access proof, teardown proof | No real containment claim |
| 92 | Outcome validity and shortcut resistance | Can success be determined by an unambiguous synthetic signal while detecting alternate paths, fixture leakage, and evaluator shortcuts? | Exact synthetic goal signal, negative controls, shortcut ledger, independent transcript/event review, no self-attested success | No capability generalization claim |
| 93 | Crash and destructive-failure semantics | Does a crashed, hung, corrupted, or self-invalidated boundary become a recorded failure without hidden retry or silent repair? | Failure taxonomy, bounded timeout, append-only failure receipt, unavailable-state refusal, teardown verification, no automatic replay | No recovery assurance claim |
| 94 | Persistence, scaling, and false-success evaluation | How do repeated attempts, budget, parallelism, and long trajectories affect boundary pressure, disengagement, and false success reports? | Fixed-budget matrix, deterministic seeds, independent samples, confidence intervals, transcript classification, cost/attempt accounting | No frontier capability claim |
| 95 | Mandatory audit | Does evidence from Phases 90-94 justify any boundary change, or do blockers remain? | Full regression, audit of scope and invariants, finding severity, explicit gate decision, updated technical debt | Audit gate |

## Dependencies

- Phase 91 defines the safe evaluation boundary and capability manifest used by Phases 92-94.
- Phase 92 depends on Phase 91 and must prove that the evaluator cannot confuse a shortcut or self-report with success.
- Phase 93 depends on the Phase 91 teardown contract and must preserve no-hidden-retry semantics.
- Phase 94 depends on the event and receipt schema from Phases 91-93 and must distinguish capability, persistence, and harness failure.
- Phase 95 reviews all evidence and does not authorize production by default.

## Required test matrix

Each implementation phase requires happy-path and adversarial tests:

- subject remains inside the synthetic boundary;
- host and real filesystem access are unavailable;
- benign capability manifest mismatches fail closed;
- shortcut fixtures and alternate success paths are detected;
- evaluator self-reports do not count as success;
- timeout, crash, malformed event, and unavailable state produce durable failure records;
- retries and parallel attempts are explicit, bounded, and auditable;
- false success, disengagement, repeated invalid submissions, and environment self-destruction are classified separately; and
- production requests, network requests, and consequential tool requests are rejected.

## Explicit non-goals

These phases do not create a production sandbox, prove container or kernel security, test real vulnerabilities, grant shell access, introduce exploit code, establish model safety, measure generalized autonomy, add network transport, use external identity, provide protected key custody, or enable consequential actions.

## Audit checkpoint

Phase 95 is the mandatory audit for this sequence. An invariant failure, boundary expansion, real integration request, or serious security event triggers an earlier audit and pauses further research.
