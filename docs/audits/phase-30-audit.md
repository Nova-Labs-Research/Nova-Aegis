# Nova Aegis Audit - Phase 30

## Scope

- **Phases reviewed:** Phases 26-29
- **Change range:** `a848313..working tree`
- **Auditor:** GitHub Copilot
- **Date:** 2026-08-13
- **Operating profile:** Single-process, local SQLite, synthetic workstation proof. No real MCP HTTP/OAuth transport, distributed worker fleet, live semantic evaluator, authoritative organizational corpus, protected approval service, or consequential external tool.

This mandatory audit reviews verifiable recovery receipts, durable worker ownership, renewable leases, fencing, and dual-operator recovery approval. It does not certify real MCP Tasks, distributed worker infrastructure, production recovery authority, or external execution evidence.

## Validation

- `$env:PYTHONPATH='src'; pytest -q` -> **77 passed**.
- `pytest -q tests/test_mcp_gateway.py -k "renew or fencing or recovery or shared_durable"` -> **6 passed, 14 deselected**.
- `python -m compileall -q src tests` -> **passed**.
- Editor diagnostics for touched source and tests -> **no errors**.
- `git diff --check` -> **passed**.
- Direct Phase 30 probes -> **passed** for shared durable ownership, lease renewal, stale renewal rejection, monotonic fencing, stale completion rejection, independent recovery approval, owner self-approval rejection, approval/evidence binding, and no handler replay.
- Repository state -> `main...origin/main`; Phase 28-29 changes are uncommitted in the working tree. The supplied research PDF remains deliberately untracked.

## Findings

| ID | Severity | Area | Finding | Required action | Owner | Due date |
|---|---|---|---|---|---|---|
| AUD30-001 | High | Recovery authority | Recovery approvals are signed and dual-controlled inside one gateway process, but approval state is not durable or protected. Restart, process compromise, or gateway divergence can lose or isolate approval records. | Move approvals to a protected durable authority with reviewer identity, revocation, retention, conflict handling, and immutable audit anchoring before consequential recovery. | Nova Aegis | Before real recovery integration |
| AUD30-002 | High | Worker identity and leases | `worker_id` is caller-supplied and not authenticated by an organizational worker authority. SQLite claim/fence coordination is local and does not establish trust across hosts or failure domains. | Add authenticated worker identity and protected distributed lease/fencing authority before real workers or multi-node execution. | Nova Aegis | Before real worker integration |
| AUD30-003 | High | External execution evidence | The verifier boundary and local signed registry bind receipts correctly for the synthetic profile, but the registry is not an independent external execution service or durable evidence witness. | Integrate independently queryable, durable, cryptographically trusted external receipts and conflict handling before consequential recovery. | Nova Aegis | Before consequential recovery |
| AUD30-004 | Medium | Lease failure semantics | Fencing rejects stale result publication, but a stale handler may continue performing an external side effect after lease loss. There is no cancellation interrupt or transactional external adapter. | Require cancellable/transactional tool adapters or treat lease loss as explicit recovery ambiguity with protected operator handling. | Nova Aegis | Before real external tools |
| AUD30-005 | Medium | Task durability | Task payloads, approval records, worker credentials, and lease history are not independently retained as a complete durable execution journal. | Persist canonical task payload, approval history, worker identity evidence, and fence transitions in protected append-only storage. | Nova Aegis | Before production task runtime |
| AUD30-006 | Medium | MCP transport and deployment | Gateway protections remain in-process contracts. HTTP transport, OAuth 2.1/PKCE, Protected Resource Metadata, consent, proxy desynchronization defenses, Apps sandboxing, and real Tasks interoperability remain absent. | Implement and separately audit the actual networked MCP boundary before describing the system as MCP transport support. | Nova Aegis | Before networked MCP phase |
| AUD30-007 | Medium | Broader assurance boundaries | External identity, verified source provenance, protected audit storage, live semantic isolation, Agent K policy/risk rules, memory, graph, and network enforcement remain synthetic or absent. | Retain prior integration blockers and re-audit each boundary at its real deployment surface. | Nova Aegis | Before corresponding integration |

### Finding interpretation

No unresolved Critical vulnerability was confirmed for the evaluated synthetic profile. AUD30-001 through AUD30-003 are High release blockers for real recovery or worker deployment, not failures of the local proof. AUD30-004 through AUD30-007 remain integration blockers at their corresponding boundaries.

## Confirmed Vulnerabilities

No new Critical vulnerability was confirmed in the synthetic profile. The audit confirms three High boundary risks if the local contracts are mistaken for production controls:

- worker identity and lease authority are not independently authenticated or distributed;
- dual recovery approval is process-local rather than protected human authority; and
- local receipt signatures do not prove an independent external execution event.

These risks are fail-closed in the tested path: missing or mismatched evidence returns `FAIL`, stale workers cannot publish results, and recovery without the required approval returns `FAIL`.

## Confirmed Bugs

No unresolved correctness bug was found in the evaluated Phase 26-29 implementation.

The tested controls preserve the intended behavior:

- signed receipts bind task, tool, owner, audience, parameters, resolution, and result;
- only one durable worker claim succeeds;
- lease renewal requires the current worker and fencing token;
- stale or expired workers cannot publish terminal results;
- lease ambiguity becomes `recovery_required` rather than automatic retry;
- owner self-approval is rejected;
- approval must match the exact verified receipt and result; and
- successful reconciliation consumes approval and never invokes the handler.

## Invariant Coverage

### Passed or directly exercised

- `INV-MCP-001` through `INV-MCP-004`: server-side authorization, scope checks, task identity, request validation, and malformed/bypassed request rejection remain covered.
- `INV-AUD-001` through `INV-AUD-003`: task starts, lease renewal, recovery approval, failures, reconciliation, and blocked paths are auditable.
- `INV-FAIL-001` through `INV-FAIL-003`: missing verifier, invalid receipt, stale lease, stale fence, missing approval, and approval mismatch reduce authority.
- `INV-HUMAN-001` through `INV-HUMAN-003`: recovery remains review-gated, owner self-approval is rejected, and reconciliation does not replay the handler.
- `INV-LOOP-001`: per-user active-task quota remains enforced.

### Not implemented or not fully testable

- authenticated worker identity and distributed lease/fence authority;
- protected durable approval service, reviewer authentication, revocation, and quorum policy;
- independent external receipt service, public-key trust, durable witness, and conflict resolution;
- crash injection during external execution, cancellation interruption, transactional adapters, and clock/failure-domain testing;
- complete durable task payload and execution journal;
- MCP HTTP/OAuth/Tasks/Apps deployment surfaces;
- protected audit storage, external identity, verified source provenance, live semantic isolation, Agent K policy/risk rules, memory, graph, and network enforcement.

## Threat Coverage

### Tested or partially exercised

- concurrent durable task claim race;
- lease renewal and stale renewal rejection;
- monotonic fencing and stale completion rejection;
- restart quarantine and no automatic replay;
- independent operator approval and owner self-approval rejection;
- receipt/result/resolution approval binding;
- single-use approval after successful reconciliation; and
- no handler replay after reconciliation.

### Not tested or not implemented

- worker credential forgery, worker impersonation, distributed split-brain, clock skew, database failover, and lease service compromise;
- approval service compromise, reviewer account takeover, revocation races, conflicting approvals, and protected audit tampering;
- external receipt witness compromise, public-key rotation, receipt conflicts, and external query failure;
- running-task interruption, transactional tool rollback, queue starvation, resource exhaustion at scale;
- MCP proxy/server desynchronization, OAuth/consent/redirect attacks, Apps XSS, SSRF, and local-server compromise.

## Technical Debt Decision

### Added or updated

- TD-026 through TD-029 are mitigated synthetic controls with remaining integration debt.
- AUD30-001 through AUD30-003 are active High release blockers for real workers or consequential recovery.
- AUD30-004 through AUD30-007 remain Medium integration prerequisites.

### Resolved for evaluated profile

- recovery receipt claims are independently verified within the injected synthetic verifier boundary;
- durable worker claims are exclusive;
- lease renewal and fencing prevent stale result publication;
- dual approval is required and bound to exact recovery evidence; and
- ambiguous work remains review-gated without automatic replay.

### Accepted

Local SQLite coordination, process-local approvals, synthetic receipt registry, caller-supplied worker identity, and in-process MCP contracts are accepted only for local research. Owner: Nova Aegis. Review: before any corresponding real integration.

### Escalated

Real workers, consequential recovery, networked MCP, live Foundry semantic evaluation, organizational data, or external tools before AUD30-001 through AUD30-007 are resolved or explicitly re-audited is a release-blocking architecture violation.

## Architecture Decision

**Decision:** `CONTINUE` for synthetic-only Phase 30/31 work; `REFACTOR` required before real integrations.

Phases 26-29 form a coherent local proof for evidence-bound recovery and fenced worker state. The implementation correctly reduces authority on missing, stale, or conflicting evidence. It does not yet provide independent worker identity, protected human authority, distributed coordination, or external execution proof.

## Final Gate

- **Decision:** `CONTINUE` for synthetic-only work; **do not enable real workers, consequential recovery, or networked MCP**.
- **Human approval required:** Yes for any real worker, recovery, MCP Tasks/Apps, networked MCP, external identity, live semantic evaluation, organizational data, or consequential tool.
- **Follow-up audit:** Before any boundary expansion, after a serious security event, after model/runtime replacement, or at the next mandatory five-phase checkpoint.
- **Blocking conditions:** Resolve or re-audit AUD30-001 through AUD30-003 before real workers or consequential recovery. Resolve or re-audit AUD30-004 before real external tools. Resolve or re-audit AUD30-006 before networked MCP. Retain AUD30-007 until each corresponding integration is verified.

> **Audit conclusion:** Phases 26-29 strengthen Nova Aegis with verifiable synthetic receipts, durable fenced leases, and dual recovery authority. The local proof is coherent and fail-closed under the tested profile. It remains a research boundary, not a production worker platform, recovery authority, external evidence service, or networked MCP deployment.