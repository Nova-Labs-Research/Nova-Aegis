# Nova Aegis Technical Debt Ledger

## Purpose

This ledger records implementation debt, discovered defects, broken behavior, temporary decisions, and architectural questions. It prevents temporary MVP choices from becoming invisible permanent constraints.

Every phase must update this document before it is considered complete.

## Phase Record

Each phase record must answer:

- What changed?
- What broke or was discovered?
- What is the root cause?
- What fix was applied or proposed?
- Why was that fix chosen?
- What risk remains?
- Is refactoring required?
- Which threat, invariant, or architecture section is related?
- Which tests were added?
- Which tests are still missing?

## Status Values

- **Open:** known debt or defect remains.
- **In progress:** an owned fix is being implemented.
- **Mitigated:** risk is reduced, but the underlying debt remains.
- **Resolved:** the cause is fixed and validated.
- **Accepted:** consciously retained with rationale, owner, and review date.
- **Blocked:** cannot be resolved until a named dependency or decision is available.

## Severity Values

- **Critical:** threatens confidentiality, authorization, governance, or a security invariant.
- **High:** can cause unsafe behavior, material data exposure, incorrect assurance, or architectural boundary failure.
- **Medium:** meaningful defect or maintainability risk without immediate critical impact.
- **Low:** localized cleanup or minor usability/clarity issue.

## Current Phase Records

### TD-006 - Phase 6 adversarial evidence assurance

- **Phase:** 6
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Added explicit claim-group, claim, lifecycle-status, and provenance-verification metadata to evidence and citations. Praetor now returns `REVIEW` for unresolved conflicting claims, stale or superseded evidence, unclassified authority, and unverified provenance.
- **What broke or was discovered:** The earlier MVP treated any retrieved citation as sufficient for `PASS`, including instruction-like, stale, unverified, or contradictory material.
- **Root cause:** Retrieval presence was used as a proxy for evidence quality; conflict and lifecycle semantics were not represented in the evidence contract.
- **Fix applied or proposed:** Make evidence quality explicit and keep ambiguous evidence visible to the reviewer while withholding the proposed answer from `PASS`.
- **Why this fix:** It directly exercises INV-EVID-003 through INV-EVID-006 and preserves the rule that retrieval is evidence gathering, not truth establishment.
- **Remaining risk:** Claim metadata and verification flags are still supplied by the in-memory corpus; source objects, hashes, revision relationships, graph authority, and contradiction semantics are not independently validated.
- **Refactor required:** Yes before authoritative corpus or production deployment; no before the next synthetic phase.
- **Related controls:** INV-EVID-001, INV-EVID-003, INV-EVID-004, INV-EVID-005, INV-EVID-006, INV-FAIL-003.
- **Tests added:** Conflicting claims, stale evidence, unverified provenance, and unclassified instruction-like evidence all require `REVIEW`.
- **Tests still missing:** Source-object verification, hash and revision checks, supersession relationships, contradictory evidence across retrieval limits, and durable provenance storage.
- **Owner:** Nova Aegis
- **Review date:** Before Phase 10 audit or any real corpus integration.

### TD-005 - Phase 5 full audit findings

- **Phase:** 5
- **Status:** Accepted for synthetic MVP; blocking before real integrations
- **Severity:** Medium
- **What changed:** Audited Phases 1-4 against the architecture, threat model, security invariants, tests, and technical-debt ledger.
- **What broke or was discovered:** The synthetic slice has no authenticated identity, gateway-enforced MCP boundary, durable tamper-evident audit, independent provenance verification, verified model cache, or operating-system network enforcement.
- **Root cause:** The MVP intentionally uses in-memory state and injected metadata to test the control flow before introducing platform infrastructure.
- **Fix applied or proposed:** Preserve the synthetic-only boundary; require these controls before real data, consequential tools, or production inference. Detailed findings are in `docs/audits/phase-05-audit.md`.
- **Why this fix:** The current tests demonstrate bounded behavior in the evaluated profile, but application conventions are not sufficient security roots for real deployment.
- **Remaining risk:** The MVP is not production-ready and must not be connected to real organizational data or high-impact tools.
- **Refactor required:** Yes before real integrations; no before Phase 6 synthetic corpus work.
- **Related controls:** Phase 5 audit, INV-ID-001, INV-ID-002, INV-MCP-001, INV-EVID-003, INV-AUD-003, INV-NET-002.
- **Tests added:** Full 17-test suite, compilation, diagnostics, and direct invariant probes.
- **Tests still missing:** Authenticated identity, gateway rejection, durable audit integrity, source/artifact verification, network isolation, memory, graph, conflict, and human-review tests.

### TD-004 - Provider-abstract local inference boundary

- **Phase:** 4
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Added the provider-neutral inference lifecycle and a Foundry Local adapter boundary with explicit model manifests, offline provisioning, load, ready, infer, and unload states.
- **What broke or was discovered:** Foundry Local model acquisition and execution-provider provisioning can involve network-hosted catalog or platform services, which conflicts with Nova Aegis normal-operation offline requirements if left implicit.
- **Root cause:** The earlier architecture named Foundry Local as the initial runtime but had no executable lifecycle or provisioning enforcement.
- **Fix applied or proposed:** Require an explicit local `ModelManifest`, reject network-enabled provisioning, inject the actual runtime function behind the adapter, and fail when no local inference implementation is available.
- **Why this fix:** It preserves provider independence and makes offline provisioning a testable boundary instead of an assumption.
- **Remaining risk:** The adapter does not yet call the Foundry Local SDK, verify artifact hashes, manage a persistent cache, validate execution providers, or record model lifecycle events in the audit store.
- **Refactor required:** Yes before real model inference or production deployment; no before the synthetic corpus and governance tests.
- **Related controls:** INV-NET-001, INV-NET-002, INV-MODEL-001, INV-MODEL-002, INV-FAIL-002.
- **Tests added:** Offline provisioning rejection, lifecycle success, load-before-provision rejection, missing-runtime rejection, and manifest validation.
- **Tests still missing:** Real Foundry Local integration, artifact hash verification, cache integrity, provider compatibility, model audit events, and network isolation enforcement.

### TD-003 - Policy-driven tool authorization

- **Phase:** 3
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Added explicit `ToolPolicy` and `AuthorizationContext` contracts. Praetor now evaluates capability, role, target, and operation value before synthetic-tool execution.
- **What broke or was discovered:** The Phase 1/2 capability allowlist did not constrain parameters or identity context; an authorized tool name could otherwise be reused for an unintended target or operation.
- **Root cause:** Authorization was modeled as tool availability rather than authorization of the complete requested operation.
- **Fix applied or proposed:** Require a named policy and evaluate user role, target, and operation value after the capability check. Preserve fail-closed behavior when Praetor is unavailable.
- **Why this fix:** It directly enforces INV-AUTH-002, INV-AUTH-003, and the confused-deputy boundary without giving the model or tool self-granted authority.
- **Remaining risk:** Policies are in-memory and caller-provided; user identity is recorded but not authenticated; delegated authority, policy versioning, resource hierarchies, and real MCP enforcement remain absent.
- **Refactor required:** Yes before real tools, persistent policy administration, or multi-user deployment; no before the synthetic corpus phase.
- **Related controls:** INV-AUTH-001, INV-AUTH-002, INV-AUTH-003, INV-ID-002, INV-MCP-001.
- **Tests added:** Out-of-scope target, out-of-scope operation, denied role, custom policy scope, and audit authorization context.
- **Tests still missing:** Policy persistence and integrity, authenticated identity, delegation limits, policy conflict resolution, and real gateway-side enforcement.

### TD-002 - Structured evidence and audit contracts

- **Phase:** 2
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Added structured response and provenance contracts, retrieval scores, typed audit events, request correlation IDs, input validation, and adversarial evidence tests.
- **What broke or was discovered:** Title-referenced documents were not discoverable because retrieval initially indexed document text only. The initial audit events also had no stable event taxonomy or correlation identifier.
- **Root cause:** The first vertical slice optimized for the shortest behavior path and left evidence metadata and event contracts implicit.
- **Fix applied or proposed:** Include document titles in lexical retrieval; add `Provenance`, `Response`, supported audit event types, event IDs, request IDs, and explicit validation for empty questions and tool parameters.
- **Why this fix:** Evidence must be discoverable and traceable, while audit records must be structurally recognizable across the request path.
- **Remaining risk:** Provenance is currently caller-supplied and in-memory; citations are not yet independently hash-verified, persisted, or conflict-aware.
- **Refactor required:** Yes before persistent or multi-user deployment; no before the next synthetic-corpus phase.
- **Related controls:** INV-EVID-001, INV-EVID-003, INV-EVID-004, INV-AUD-001, INV-FAIL-003.
- **Tests added:** Provenance and score assertions, audit event sequence, instruction-like evidence isolation, malformed tool parameters, and invalid-question rejection.
- **Tests still missing:** Source hashing, revision conflict handling, durable audit storage, schema serialization, and independent provenance verification.

### TD-001 - Dependency-free MVP infrastructure

- **Phase:** 1
- **Status:** Accepted for MVP
- **Severity:** Medium
- **What changed:** Added a dependency-free local retrieval, evidence citation, response assurance, audit, and synthetic-tool slice.
- **What broke or was discovered:** The MVP does not yet use a persistent document store, graph database, vector index, Foundry Local, or a real MCP transport.
- **Root cause:** The first vertical slice intentionally minimizes infrastructure so the authority boundary can be tested before platform integration.
- **Fix or next step:** Keep the provider, storage, and tool interfaces replaceable; introduce each dependency only behind a tested boundary.
- **Why this fix:** It validates governance behavior without prematurely coupling the architecture to runtime or storage choices.
- **Remaining risk:** In-memory state is not durable, multi-user safe, or production-ready.
- **Refactor required:** Yes before production or multi-session deployment; no before the next MVP behavior slice.
- **Related controls:** High-level architecture, INV-AUTH-001, INV-GOV-001, INV-NET-001.
- **Tests added:** Local evidence PASS, missing evidence REVIEW, unauthorized tool BLOCK, authorized tool execution, Praetor outage fail-closed.
- **Tests still missing:** Persistence isolation, concurrent sessions, real MCP boundary, model-provider contract, and network enforcement.

## Phase Entry Template

Copy this section for each completed phase.

### TD-XXX - Short title

- **Phase:**
- **Status:** Open | In progress | Mitigated | Resolved | Accepted | Blocked
- **Severity:** Critical | High | Medium | Low
- **What changed:**
- **What broke or was discovered:**
- **Root cause:**
- **Fix applied or proposed:**
- **Why this fix:**
- **Remaining risk:**
- **Refactor required:** Yes | No | Reassess at audit
- **Related controls:**
- **Tests added:**
- **Tests still missing:**
- **Owner:**
- **Review date:**

## Debt Rules

1. Critical debt cannot be silently accepted.
2. A security-invariant failure is tracked as a release blocker for the affected operating profile.
3. A workaround must include the reason it exists and the condition that permits its removal.
4. Debt discovered during a phase is recorded in the same phase, even when the fix is deferred.
5. Accepted debt receives an owner and review date.
6. Resolved debt requires an executable validation result.
7. The five-phase audit reviews every open, mitigated, accepted, and blocked item.
