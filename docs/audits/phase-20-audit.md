# Nova Aegis Audit - Phase 20

## Scope

- **Phases reviewed:** Phases 16-19
- **Change range:** `0845bf9..68c1791`, plus the Phase 20 replay repair under review
- **Auditor:** GitHub Copilot
- **Date:** 2026-08-13
- **Operating profile:** Single-process synthetic workstation MVP; no real MCP HTTP server, OAuth provider, live semantic model, organizational corpus, or consequential external action.

This mandatory audit reviews debt reconciliation, idempotent execution receipts, the synthetic MCP Gateway, and stateless MCP task/routing controls. It does not certify conformance with the 2026-07-28 MCP revision or production readiness.

## Validation

- `$env:PYTHONPATH='src'; pytest -q` -> **66 passed**.
- `python -m compileall -q src tests` -> **passed**.
- Editor diagnostics for `src`, `tests`, `docs`, and `README.md` -> **no errors**.
- `git diff --check` -> **passed**.
- Direct Phase 20 probes -> passed for signed state, routing desynchronization, metadata privilege claim, and execution non-bypass.
- Replay probe -> initially found two executions for one signed task envelope; fixed before this gate with a process-local replay registry and regression test.

## Findings

| ID | Severity | Area | Finding | Required action | Owner | Due date |
|---|---|---|---|---|---|---|
| AUD20-001 | High, resolved | Stateless MCP task replay | A valid signed client-held task state could be invoked more than once, causing duplicate synthetic execution. | Fixed before the gate: completed task IDs return stored results and do not execute again. Add durable/distributed replay control before real MCP tasks. | Nova Aegis | Before real MCP task integration |
| AUD20-002 | Medium | Stateless task durability | Replay protection is process-local and does not survive restart or work across gateway instances. | Add a durable, expiry-aware task/replay store and distributed concurrency controls before real stateless MCP deployment. | Nova Aegis | Before real MCP task integration |
| AUD20-003 | Medium | MCP 2026 surface | No HTTP transport, OAuth 2.1/PKCE, Protected Resource Metadata, consent, state/redirect validation, or token storage/rotation exists. | Implement and test the actual protocol boundary before claiming MCP authorization support. | Nova Aegis | Before real MCP integration |
| AUD20-004 | Medium | Gateway desync and metadata | Header/body consistency and `_meta` controls are local contract checks only; no proxy, HTTP header canonicalization, namespace policy, or proxy/server desync tests exist. | Add transport and proxy integration tests before network deployment. | Nova Aegis | Before networked gateway phase |
| AUD20-005 | Medium | Apps and Tasks | MCP Apps sandboxing/XSS controls, task quotas, cancellation, durable task state machine, and resource exhaustion controls are not implemented. | Treat Apps and long-running Tasks as separate governed features with quotas and sandbox policies. | Nova Aegis | Before enabling Apps or Tasks |
| AUD20-006 | Medium | Prior integration blockers | Identity, evidence provenance, protected audit storage, live semantic evaluation, Agent K policy scope, and real execution receipts remain synthetic/local-only. | Retain existing blocking conditions and resolve at the actual integration boundaries. | Nova Aegis | Before corresponding real integration |

### Finding interpretation

AUD20-001 was a High correctness and authority risk in the synthetic state-changing gateway path. It was corrected and regression-tested before the audit decision. No unresolved Critical or High finding remains for the evaluated synthetic profile. All Medium items become release blockers if their related real integration is introduced.

## Confirmed Vulnerabilities

- **Resolved:** a replayed valid task envelope could execute a state-changing synthetic tool twice.
- **No unresolved Critical/High vulnerability** was confirmed for the synthetic profile after the repair.
- The gateway must not be described as a real MCP 2026-07-28 server, OAuth resource server, or distributed stateless task implementation.

## Confirmed Bugs

- The Phase 20 replay flaw was found by a direct repeated-invocation probe and fixed before the gate.
- No other unresolved correctness bug was found in Phases 16-19.

## Invariant Coverage

### Passed or directly exercised

- `INV-AUTH-001` through `INV-AUTH-003`: synthetic capability, role, target, and operation checks remain enforced.
- `INV-ID-001` and `INV-ID-002`: gateway tokens revalidate issued identity and revocation on every request.
- `INV-MCP-001`: server-side gateway invokes Praetor authorization.
- `INV-MCP-002`: discovery is role-limited and unregistered tools are rejected.
- `INV-MCP-003`: request parameter schemas and stateless routing fields are validated.
- `INV-MCP-004`: malformed, audience-mismatched, scope-mismatched, metadata-poisoned, and desynchronized requests are blocked.
- `INV-AUD-001` through `INV-AUD-003`: gateway allow/deny events, preflight audit, execution receipts, and recovery signals are tested.
- `INV-FAIL-001` through `INV-FAIL-003`: invalid token, identity, scope, state, metadata, header/body, and audit conditions reduce authority.

### Not implemented or not fully testable

- real MCP 2026-07-28 HTTP transport and protocol negotiation;
- OAuth 2.1/PKCE, Protected Resource Metadata, consent, redirects, and token lifecycle;
- durable/distributed task state, replay control, cancellation, quotas, and task recovery;
- Apps sandboxing, XSS/output encoding, and browser UI policy;
- proxy/server header canonicalization and desynchronization behavior;
- real MCP tool response validation, receipts, and external reconciliation;
- verified evidence source objects, external identity, protected audit storage, live semantic isolation, memory, graph, and network controls.

## Threat Coverage

### Tested or partially exercised

- audience confusion and token passthrough prevention;
- least-privilege scope denial and role-limited discovery;
- revoked identity, unregistered tool, and malformed parameter rejection;
- stateless task-state parameter tampering;
- header/body routing desynchronization;
- `_meta` identity/audience/scope privilege claims;
- task replay and duplicate-execution prevention; and
- execution receipt recovery behavior.

### Not tested or not implemented

- HTTP proxy desync, stateful/durable task abuse, task quota exhaustion, cancellation races, Apps XSS, SSRF, consent/redirect attacks, local server compromise, and distributed gateway concurrency.

## Technical Debt Decision

### Added or updated

- TD-019 now records the discovered and resolved High task replay flaw.
- AUD20-002 through AUD20-006 remain Medium prerequisites for real integrations.
- TD-017 and TD-018 remain synthetic/local boundaries, not production controls.

### Resolved for evaluated profile

- Completed stateless task envelopes return the stored result without replaying the handler.
- Signed task state, routing consistency, and restricted `_meta` inputs are enforced in the synthetic gateway.

### Accepted

The process-local replay registry, local identity, local audit, synthetic semantic evaluator, and synthetic MCP contracts are accepted only for continued local research. Owner: Nova Aegis. Review: Phase 25 or before any real integration.

### Escalated

Enabling real MCP HTTP transport, stateless Tasks, Apps, organizational data, live semantic models, or consequential tools before AUD20-002 through AUD20-006 are resolved or re-audited is a release-blocking architecture violation.

## Architecture Decision

**Decision:** `CONTINUE` for synthetic Phase 21 work; `REFACTOR` required before real integrations.

The audit confirms that the synthetic gateway now has explicit defense for both integrity and replay of client-held task state. The correction was made before the gate, not accepted as debt. The current task replay registry is deliberately narrow and must not be mistaken for a durable stateless task service.

## Final Gate

- **Decision:** `CONTINUE` for synthetic-only Phase 21 work.
- **Human approval required:** Yes for networked MCP, OAuth/identity integration, Apps, Tasks, real data, live semantic evaluation, or consequential tools.
- **Follow-up audit:** Phase 25, or earlier for any boundary expansion, model/runtime replacement, serious security event, or invariant failure.
- **Blocking conditions:** Before real MCP or Tasks integration, resolve or explicitly re-audit AUD20-002 through AUD20-005; retain all prior real-integration blockers.

> **Audit conclusion:** Phases 16-19 strengthened execution recovery and the MCP boundary. The Phase 20 audit caught and repaired a task replay flaw before real tool integration. Nova Aegis remains a controlled local proof, not a networked MCP platform.
