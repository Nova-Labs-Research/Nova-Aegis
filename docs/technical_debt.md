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
