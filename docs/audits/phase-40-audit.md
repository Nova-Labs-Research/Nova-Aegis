# Nova Aegis Audit - Phase 40

## Scope

- **Phases reviewed:** Phases 36-39
- **Change range:** Working tree since the Phase 35 audit
- **Auditor:** GitHub Copilot
- **Date:** 2026-08-14
- **Operating profile:** Single-process, local SQLite, synthetic workstation proof. No real MCP HTTP/OAuth transport, distributed worker fleet, protected key service, protected approval authority, independent external evidence witness, or consequential external tool.

This mandatory audit reviews the unified local recovery transaction, authenticated journal records, versioned key rotation and retirement, concurrent recovery finalization, restart replay, and fail-closed behavior. It does not certify production recovery authority, distributed transactions, real MCP Tasks, protected key management, or external execution evidence.

## Validation

- `$env:PYTHONPATH='src'; pytest -q` -> **88 passed**.
- `$env:PYTHONPATH='src'; pytest -q tests/test_mcp_gateway.py -k 'unified_recovery_store or journal or key_rotation or concurrent_finalizer'` -> **7 passed, 24 deselected**.
- `python -m compileall -q src tests` -> **passed**.
- `git diff --check` -> **passed**.
- Editor diagnostics for touched source and tests -> **no errors**.
- Direct probes cover atomic success, transaction rollback, restart replay, journal tampering, wrong-key rejection, key overlap, retired-key rejection, active-key protection, concurrent finalization, single-use approval, and no handler replay.

## Findings

| ID | Severity | Area | Finding | Required action | Owner | Due date |
|---|---|---|---|---|---|---|
| AUD40-001 | High | Human recovery authority | Approval state and journal keys remain locally configured SQLite/process state rather than protected, authenticated organizational authority. | Add protected reviewer identity, key custody, rotation authorization, revocation governance, retention, conflict handling, and immutable anchoring before consequential recovery. | Nova Aegis | Before consequential recovery |
| AUD40-002 | High | Distributed transactionality | `SQLiteRecoveryStore` provides one local transaction and serializes contenders, but it does not establish multi-host coordination, failover semantics, or durable power-loss evidence. | Introduce a protected transaction/coordinator boundary and test failover, split-brain, recovery, and durability behavior before production workers or multi-node recovery. | Nova Aegis | Before production recovery |
| AUD40-003 | High | External evidence | Receipts remain produced and verified by a local synthetic registry; successful reconciliation does not independently prove an external side effect. | Integrate an independently queryable, durable, cryptographically trusted receipt authority with conflict and revocation handling. | Nova Aegis | Before consequential recovery |
| AUD40-004 | Medium | Key lifecycle | Versioned HMAC overlap and retirement work locally, but key material is supplied in process and key destruction, escrow, rotation authorization, and restart loading are not governed. | Add protected key management and lifecycle audit before protected audit deployment. | Nova Aegis | Before protected audit deployment |
| AUD40-005 | Medium | Transport and worker boundary | MCP transport remains in-process and worker identity remains caller-supplied; OAuth, real Tasks, distributed leases, and network failure modes remain unimplemented. | Preserve the synthetic-only gate and separately audit each networked or distributed boundary before enablement. | Nova Aegis | Before networked MCP or real workers |

## Confirmed Vulnerabilities

No new Critical vulnerability was confirmed for the evaluated synthetic profile. The High findings are release blockers if local synthetic controls are treated as production authority, distributed coordination, or independent evidence.

The tested recovery path reduces authority on missing, expired, revoked, consumed, mismatched, forged, unauthenticated, retired-key, failed-transaction, and contended recovery attempts. Verified replay updates task bookkeeping only and never invokes the external handler.

## Confirmed Bugs

No unresolved correctness bug was found in the evaluated synthetic profile. Phases 36-39 close the local cross-store commit gap, add authenticated/versioned journal verification, and establish single-use behavior under concurrent finalization.

The focused command initially had a malformed `-k` expression and ran no tests; it was corrected and rerun successfully. This was a validation-command error, not an implementation defect.

## Invariant Coverage

### Passed or directly exercised

- `INV-HUMAN-001` through `INV-HUMAN-003`: recovery remains approval-gated, owner self-approval is rejected, and no replay invokes the handler.
- `INV-FAIL-002`: transaction failure, missing keys, retired keys, forged journal data, and contention reduce authority rather than auto-executing.
- `INV-AUD-001` through `INV-AUD-003`: approval, revocation, blocked replay, key failures, replay, reconciliation, and transaction failures remain auditable.
- `INV-MCP-001` through `INV-MCP-004`: existing gateway authorization, scope, task binding, and request validation remain covered.

### Not implemented or not fully testable

- protected reviewer, worker, and key-management identity;
- distributed task, approval, journal, lease, and fencing authority;
- power-loss durability, database failover, split-brain, and multi-host recovery;
- independent external receipt witness, public-key trust, revocation, and conflict resolution;
- immutable audit anchoring and governed retention;
- MCP HTTP/OAuth/Tasks/Apps deployment surfaces; and
- cancellation or transactional rollback of already-running external effects.

## Technical Debt Decision

- TD-036 through TD-039 remain mitigated synthetic controls with production integration debt.
- AUD40-001 through AUD40-003 are High release blockers for consequential recovery, production workers, or multi-node deployment.
- AUD40-004 and AUD40-005 remain Medium prerequisites for protected audit storage and networked/distributed deployment.

## Architecture and Gate Decision

**Decision:** `CONTINUE` for synthetic-only work; **REFACTOR** required before real integrations.

The Phase 36-39 recovery boundary is coherent and fail-closed under the tested local profile. The unified transaction and keyed journal lifecycle improve local correctness but do not establish protected human authority, distributed transactionality, independent external evidence, or networked MCP security.

- **Human approval required:** Yes for consequential recovery, real workers, networked MCP, external identity, live semantic evaluation, organizational data, or consequential tools.
- **Blocking conditions:** Do not enable those boundaries until AUD40-001 through AUD40-003 are resolved or explicitly re-audited. Retain AUD40-004 and AUD40-005 until their corresponding deployment surfaces are tested.
- **Follow-up audit:** Before any boundary expansion, after a serious security event, after model/runtime replacement, or at the next mandatory five-phase checkpoint.

> **Audit conclusion:** Phases 36-39 provide a stronger synthetic recovery boundary with local atomicity, authenticated/versioned journal records, and single-use concurrency guarantees. Nova Aegis remains a research boundary, not a production recovery authority, protected key service, independent evidence service, distributed worker platform, or networked MCP deployment.
