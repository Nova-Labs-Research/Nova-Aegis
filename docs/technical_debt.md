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

### TD-012 - Praetor response-path hybrid integration

- **Phase:** 12
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Integrated injected deterministic and semantic evaluators into `Praetor.evaluate_response_with_trace`. The response path now fuses both verdicts and audits evaluator statuses and reasons with the final assurance decision.
- **What broke or was discovered:** The Phase 11 fusion contract was standalone, so response assurance neither invoked both evaluators nor retained their separate verdicts in the audit trail.
- **Root cause:** The original Praetor response path performed deterministic evidence checks inline and returned a single untraceable decision.
- **Fix applied or proposed:** Route response assurance through labeled evaluator contracts and `HybridAssurance`. Convert evaluator exception or mislabeled output to `REVIEW` before fusion.
- **Why this fix:** A semantic evaluator must be independently observable and unable to convert uncertainty, failure, or injection into an approved response.
- **Remaining risk:** The semantic evaluator is a synthetic default; Agent K is not separately implemented; no evaluator isolation, prompt construction, suppression layer, confidence calibration, or real model/provider lifecycle exists.
- **Refactor required:** Yes before live semantic evaluation or any claim of production hybrid assurance; no before continued synthetic governance work.
- **Related controls:** High-level architecture Section 13, threat model Sections 19-21, INV-GOV-001 through INV-GOV-004, INV-AUD-001, INV-AUD-002.
- **Tests added:** Response-path semantic concern, deterministic hard failure, semantic evaluator outage, evaluator-kind mismatch, and audit-verdict assertions.
- **Tests still missing:** Live semantic evaluator isolation, evaluator prompt injection, repeated-run behavior, deterministic Agent K traces, evaluator model provenance, and tool-path hybrid fusion.
- **Owner:** Nova Aegis
- **Review date:** Phase 15 audit or before live semantic evaluator integration.

### TD-011 - Fixed hybrid assurance fusion contract

- **Phase:** 11
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Added typed semantic and deterministic evaluation contracts plus `HybridAssurance`, a fixed fusion boundary that permits `PASS` only when both independent evaluators pass, returns `REVIEW` on disagreement or uncertainty, and preserves deterministic `FAIL` as terminal.
- **What broke or was discovered:** Praetor had one undifferentiated decision type, so it could not represent evaluator provenance or mechanically prevent unsafe disagreement fusion.
- **Root cause:** The hybrid architecture was documented but no executable fusion contract existed.
- **Fix applied or proposed:** Use evaluator-labeled immutable decisions and explicit fixed rules; reject mislabeled evaluator inputs. The local research PDF is hash-recorded as design input, not treated as authority.
- **Why this fix:** It makes the Phase 10 hybrid-fusion requirement testable without connecting a live semantic model or weakening deterministic governance.
- **Remaining risk:** No semantic evaluator, Agent K implementation, evaluator isolation, suppression layer, confidence calibration, or integrated Praetor response path exists. The report’s judge configuration metadata is incomplete and its findings are not independently reproduced here.
- **Refactor required:** Yes before real semantic evaluation or production governance; no before further synthetic hybrid testing.
- **Related controls:** High-level architecture Section 13, threat model Sections 19-21, INV-GOV-002, INV-GOV-003, INV-GOV-004, STRIDE-AI AI-specific manipulation.
- **Tests added:** Dual-PASS, semantic misrepresentation, structural-tag omission, hard safety boundary, evaluator injection, semantic review, and evaluator-label mismatch.
- **Tests still missing:** Live evaluator isolation, stochastic repeatability, semantic prompt injection, Agent K traces, integrated response/tool fusion, confidence thresholds, and human-review workflow.
- **Owner:** Nova Aegis
- **Review date:** Phase 15 audit or before live semantic evaluator integration.

### TD-010 - Phase 10 mandatory audit findings

- **Phase:** 10
- **Status:** Accepted for synthetic MVP; blocking before real integrations
- **Severity:** Medium
- **What changed:** Audited Phases 6-9 across evidence assurance, STRIDE-AI/ATLAS coverage, durable audit, identity, policy integrity, source, tests, and invariant behavior.
- **What broke or was discovered:** No Critical or High issue was confirmed for the synthetic profile, but identity, policy, audit, MCP, and provenance controls remain process-local or application-only.
- **Root cause:** The implementation is still a deliberately bounded local proof and retains compatibility paths that are not trusted security roots.
- **Fix applied or proposed:** Continue synthetic-only work; block real data, real tools, and production inference until AUD10-001 through AUD10-005 are re-audited at their actual integration boundaries.
- **Why this fix:** It preserves momentum without treating passing unit tests as evidence of production security.
- **Remaining risk:** A deployment outside the evaluated profile would inherit unprotected identity, policy, audit, MCP, and provenance boundaries.
- **Refactor required:** Yes before real integrations; no before synthetic Phase 11.
- **Related controls:** `docs/audits/phase-10-audit.md`, INV-ID-001, INV-ID-002, INV-AUD-003, INV-MCP-001, INV-EVID-004, STRIDE-AI and MITRE ATLAS crosswalk.
- **Tests added:** Mandatory audit validation, direct identity/policy/audit probes, and the Phase 9 identity-policy suite.
- **Tests still missing:** Enterprise identity, protected policy administration, gateway enforcement, external audit anchoring, verified provenance, memory, graph, model supply chain, network isolation, and concurrency.
- **Owner:** Nova Aegis
- **Review date:** Phase 15 audit or before any real integration.

### TD-009 - Synthetic identity and policy integrity boundary

- **Phase:** 9
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Added `IdentityAuthority` and short-lived `IdentityCredential` contracts with issuer membership, signature, expiry, and revocation checks. Added Praetor policy fingerprints and fail-closed detection of post-load policy mutation.
- **What broke or was discovered:** Tool authorization previously accepted caller-supplied `user_id` and `role`, and mutable in-memory policies had no integrity signal.
- **Root cause:** The MVP modeled identity and policy as function inputs and convenience dictionaries rather than controlled security boundaries.
- **Fix applied or proposed:** Preserve legacy calls for synthetic compatibility, but provide an explicit credential path that resolves server-issued authorization context before Praetor evaluation. Refuse execution when policy integrity changes.
- **Why this fix:** It demonstrates the authority boundary and tests spoofing, revocation, expiry, confused-deputy resistance, and policy tampering without introducing an unverified external identity dependency.
- **Remaining risk:** The issuer secret is process-local; credentials are not externally authenticated; policy fingerprints are not externally anchored; legacy caller-supplied context remains available for the synthetic MVP; and no real MCP gateway enforces the contract.
- **Refactor required:** Yes before multi-user deployment, real MCP tools, or production authorization; no before the Phase 10 audit.
- **Related controls:** High-level architecture Section 21A, threat model identity spoofing, policy tampering, confused deputy, INV-ID-001, INV-ID-002, INV-AUTH-002, INV-AUTH-003.
- **Tests added:** Issued identity authorization, forged credential rejection, revocation, expiry, policy mutation, and direct fingerprint verification.
- **Tests still missing:** External identity integration, credential transport protection, key rotation, policy version persistence, delegated authority constraints, gateway-side enforcement, and concurrent revocation.
- **Owner:** Nova Aegis
- **Review date:** Phase 10 audit and before any real integration.

### TD-008 - Durable tamper-evident audit boundary

- **Phase:** 8
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Added `SQLiteAuditLog`, a dependency-free local durable audit store with event allowlisting, transactional persistence, deterministic JSON serialization, and a SHA-256 predecessor hash chain. Exported it through the public package API.
- **What broke or was discovered:** The prior audit implementation lost all events when the process ended and provided no integrity signal after database modification.
- **Root cause:** The initial vertical slice intentionally stored audit events only in memory.
- **Fix applied or proposed:** Preserve the existing audit interface while allowing `NovaAegisMVP` to receive a SQLite-backed store. Verify the chain before reads and before appends; refuse operations after integrity failure.
- **Why this fix:** It establishes a small local persistence boundary without introducing a service dependency, while making silent post-write changes detectable within the database trust model.
- **Remaining risk:** The SQLite file is not yet encrypted, access-controlled, externally anchored, independently replicated, or protected against a privileged database administrator. Recovery, retention, key management, and concurrent-writer behavior remain unimplemented.
- **Refactor required:** Yes before production, multi-user deployment, or claiming durable audit assurance; no before the next local storage slice.
- **Related controls:** High-level architecture Sections 21-22 and 26-27, INV-AUD-001 through INV-AUD-004, STRIDE-AI repudiation and tampering.
- **Tests added:** Persistence across reopen, hash-chain verification, tamper detection, append refusal after tampering, and unsupported event rejection.
- **Tests still missing:** Concurrent writers, crash recovery, retention/deletion policy, encrypted storage, external anchoring, authorization to read audit data, and sensitive-log minimization.
- **Owner:** Nova Aegis
- **Review date:** Phase 10 audit or before production audit storage.

### TD-007 - STRIDE-AI and MITRE ATLAS adversarial coverage

- **Phase:** 7
- **Status:** In progress
- **Severity:** Medium
- **What changed:** Added a STRIDE-AI working crosswalk and MITRE ATLAS technique-area mapping to the threat model. Added dedicated Praetor and NIC adversarial tests for mixed trust, duplicate unverified claims, unknown lifecycle state, unknown roles, and unknown tools.
- **What broke or was discovered:** The mapping exposes that real Cortex memory, MCP tool-result validation, authenticated identity, and model/artifact integrity controls are still absent. The MVP previously had no dedicated adversarial suite boundary for these components.
- **Root cause:** The implementation is still a local vertical slice; several architecture components remain contracts or named boundaries rather than executable services.
- **Fix applied or proposed:** Keep the crosswalk explicit about partial and unimplemented coverage. Require executable tests before marking an ATLAS technique covered.
- **Why this fix:** Threat-framework labels are useful only when tied to a concrete asset, boundary, control, and test result.
- **Remaining risk:** ATLAS coverage is incomplete and the live matrix may evolve. No production security or framework conformance claim is made.
- **Refactor required:** Yes before real MCP, memory, model supply-chain, or multi-user integration; no before continued synthetic testing.
- **Related controls:** Threat model Sections 42A-44, INV-EVID-003 through INV-EVID-006, INV-AUTH-001 through INV-AUTH-003, INV-MCP-001, INV-NET-001.
- **Tests added:** Dedicated NIC and Praetor adversarial suite; full suite remains pytest-discoverable.
- **Tests still missing:** Memory poisoning, tool-description poisoning, tool-result validation, authenticated identity spoofing, artifact substitution, exfiltration, resource exhaustion, and evaluator disagreement.
- **Owner:** Nova Aegis
- **Review date:** Phase 10 audit or before any real integration.

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
