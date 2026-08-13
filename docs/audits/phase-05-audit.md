# Nova Aegis Audit - Phase 05

## Scope

- **Phases reviewed:** Phases 1-4
- **Change range:** `31b7ca1..a94be54`
- **Auditor:** GitHub Copilot
- **Date:** 2026-08-13
- **Operating profile:** Single-workstation synthetic MVP with in-memory state, no real external tools, and no production confidential data.

This audit evaluates the implemented slice against the problem statement, architecture, threat model, security invariants, and technical-debt policy. It does not certify production security, Foundry Local integration, or enterprise readiness.

## Validation

Commands and results:

- `$env:PYTHONPATH='src'; pytest -q` -> **17 passed**.
- `python -m compileall -q src` -> **passed**.
- Editor diagnostics for `src` and `tests` -> **no errors**.
- Direct invariant probes for unauthorized tool execution, out-of-scope target, Praetor outage, and network provisioning -> **passed**.
- Git working tree and branch -> `main`, clean, synchronized with `origin/main`.

## Findings

| ID | Severity | Area | Finding | Required action | Owner | Due date |
|---|---|---|---|---|---|---|
| AUD-001 | Medium | Identity and authorization | User identity, role, and capability set are caller-supplied values in the in-memory MVP. There is no authenticated identity provider or independent delegated-authority check. | Keep real tools out of scope. Add authenticated identity and server-side policy resolution before real MCP execution or multi-user deployment. | Nova Aegis | Before real MCP phase |
| AUD-002 | Medium | MCP boundary | The synthetic tool is guarded in the application path, but there is no real MCP Gateway or server-side rejection of calls missing authorization context. | Implement gateway-side authorization enforcement before connecting any consequential or external tool. | Nova Aegis | Before real MCP phase |
| AUD-003 | Medium | Audit integrity | Audit records are append-only only within process memory. They are not durable, tamper-evident, or independently verifiable. | Add durable protected storage, integrity evidence, retention policy, and audit recovery tests. | Nova Aegis | Before persistence phase |
| AUD-004 | Medium | Evidence provenance | Provenance metadata is caller-supplied and not hash-verified. The MVP has no independent source-object or revision verification. | Add canonical source hashing, verified revisions, and provenance validation before treating evidence as authoritative. | Nova Aegis | Before authoritative corpus phase |
| AUD-005 | Medium | Inference supply chain | The Foundry Local adapter enforces an offline API boundary but does not verify artifacts, manage a trusted cache, or integrate the actual SDK. | Add controlled provisioning, artifact verification, cache integrity checks, exact model identity, and provider compatibility tests before model deployment. | Nova Aegis | Before real model phase |
| AUD-006 | Low | Retrieval assurance | Retrieval is lexical and title-aware but does not yet model contradiction, stale revisions, graph authority, or vector-candidate separation. | Add synthetic conflicting and incomplete corpus behavior in the next phase; preserve REVIEW for unresolved evidence. | Nova Aegis | Phase 6 |

### Finding interpretation

These are bounded MVP limitations, not evidence of a Critical invariant failure in the evaluated profile. Findings AUD-001 through AUD-005 become High or blocking concerns if the system is connected to real organizational data, real external tools, or production inference without the required controls.

## Confirmed Vulnerabilities

No Critical or High vulnerability was confirmed for the tested synthetic workstation profile.

The following production-relevant exposure classes remain unimplemented controls rather than closed vulnerabilities in this profile:

- authenticated identity and delegated authority;
- gateway-enforced MCP authorization;
- durable and tamper-evident audit;
- independent provenance verification;
- model artifact and cache verification; and
- operating-system or process-level network isolation.

These gaps must not be represented as solved by the current tests.

## Confirmed Bugs

One Phase 2 retrieval defect was found and fixed before this audit: title-referenced documents were not discoverable because only document text was indexed. The fix includes titles in lexical discovery, and the resulting test suite passes.

No unresolved correctness bug was found in the current tested slice.

## Security Invariant Coverage

### Passed in the evaluated profile

- `INV-AUTH-001`: unauthorized synthetic action is blocked.
- `INV-AUTH-002`: capability alone does not pass role, target, and operation policy checks.
- `INV-AUTH-003`: out-of-scope target and operation are blocked.
- `INV-GOV-001`: Praetor outage blocks sensitive synthetic execution.
- `INV-EVID-001`: instruction-like retrieved content remains evidence and does not execute a tool.
- `INV-MCP-001`: the application path requires Praetor before synthetic execution.
- `INV-NET-001`: network-enabled provider provisioning is rejected; no cloud fallback path exists.
- `INV-NET-002`: the provider adapter does not require outbound network access for its tested lifecycle.
- `INV-MODEL-001`: inference results expose provider and model identity.
- `INV-FAIL-001`: unavailable authorization does not become PASS.
- `INV-FAIL-003`: malformed questions and tool parameters are rejected and audited where applicable.
- `INV-AUD-001`: successful synthetic execution creates an audit event.
- `INV-AUD-002`: blocked synthetic execution creates an audit event.

### Not implemented or not fully testable yet

- `INV-EVID-002`: no vector retrieval exists; authority separation remains architectural.
- `INV-EVID-003` and `INV-EVID-004`: provenance is structured but not independently verified.
- `INV-EVID-005` and `INV-EVID-006`: contradiction and supersession handling are not implemented.
- `INV-MEM-001` through `INV-MEM-004`: persistent Cortex memory is not implemented.
- `INV-GOV-002` through `INV-GOV-004`: Agent K, semantic judge, and hybrid fusion are not implemented.
- `INV-MCP-002` through `INV-MCP-004`: no real MCP discovery, response validation, or gateway exists.
- `INV-ID-001` and `INV-ID-002`: identity is represented as input, not authenticated or independently delegated.
- `INV-AUD-003` and `INV-AUD-004`: audit failure policy and sensitive-content minimization are not fully implemented.
- `INV-LOOP-001`: no agent loop exists yet; bounded loop controls are not implemented.
- `INV-HUMAN-001` through `INV-HUMAN-003`: no human approval workflow exists.
- `INV-CORE-001` and `INV-CORE-002`: no separate Core service or production debug path exists.

## Threat Coverage

### Tested or partially exercised

- direct unauthorized tool execution;
- parameter and target abuse;
- role-based denial;
- Praetor outage;
- instruction-like evidence;
- malformed input;
- no-network inference provisioning;
- model identity exposure;
- basic audit events.

### Not tested or not implemented

- prompt injection chains across multiple components;
- graph poisoning;
- vector retrieval manipulation;
- memory poisoning and cross-session leakage;
- semantic judge manipulation and evaluator disagreement;
- compromised MCP server behavior;
- supply-chain artifact tampering;
- durable audit tampering;
- resource exhaustion and agent loops;
- human approval failure; and
- operating-system network enforcement.

### New threats or assumptions

The audit confirms that caller-supplied identity, policy, provenance, and model-manifest metadata are acceptable only for the synthetic single-process profile. They are not trusted security roots for future deployments.

## Technical Debt Decision

### Added

- AUD-001 through AUD-006 are recorded as audit findings.
- Phase 4 provider limitations remain tracked in `TD-004`.
- The need for authenticated identity, gateway enforcement, durable audit, verified provenance, and artifact verification is promoted as a precondition for real integrations.

### Resolved

- The Phase 2 title-retrieval defect is resolved and covered by passing tests.
- The Phase 1-4 focused test suite and compilation baseline are passing.

### Accepted for current profile

- In-memory stores and caller-provided metadata are accepted only for the synthetic workstation MVP.
- No real confidential organizational data or high-impact tool may be connected under this acceptance.

### Escalated

Any attempt to connect real organizational data, a consequential MCP tool, or unverified model artifacts before the AUD-001 through AUD-005 controls exist is a release-blocking architecture violation.

## Architecture and Refactor Assessment

**Decision:** `CONTINUE` for the synthetic MVP; `REFACTOR` required before real integrations or production deployment.

The current separation between retrieval, Praetor authorization, synthetic execution, audit, and inference provider remains coherent. No refactor is required before Phase 6's synthetic corpus work.

The following boundaries must be refactored or strengthened before real integrations:

- replace caller-supplied identity and policy with authenticated Core-controlled context;
- enforce authorization at the MCP Gateway/server boundary;
- replace in-memory audit with protected durable storage;
- verify evidence sources and model artifacts independently; and
- enforce network restrictions outside application convention.

Adding real tools or real data before those boundaries are implemented would violate the architecture and security invariants.

## Final Gate

- **Decision:** `CONTINUE` for Phase 6 synthetic corpus and evidence-conflict work.
- **Human approval required:** Yes for any scope expansion to real organizational data, consequential tools, external network access, or unverified model/runtime artifacts.
- **Follow-up audit:** Phase 10, or earlier if a real integration, model/runtime replacement, serious security event, or invariant failure occurs.
- **Blocking condition:** Before real integrations, resolve or explicitly re-audit AUD-001 through AUD-005.

> **Audit conclusion:** The first four phases demonstrate a coherent governed workstation slice with passing focused tests. They do not yet demonstrate production security. Continue narrowly, preserve the synthetic boundary, and treat the identified controls as prerequisites for future integration.
