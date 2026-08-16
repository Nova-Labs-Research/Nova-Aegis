# Nova Aegis Phase 99 - Pre-Production Boundary Review

## Scope

Phase 99 is review-only. It introduces no credentials, external identities, network transport, real data, workers, deployment hooks, consequential tools, or production enablement. It reviews whether evidence from Phases 96-98 can support a proposed integration boundary.

No concrete production deployment target or integration request has been submitted. The only valid current outcome is therefore **`BLOCKED`**.

## Review outcomes

- `APPROVED_REVIEW_ONLY`: documentation may proceed, but no integration or execution is authorized.
- `REVIEW_REQUIRED`: evidence or accountable human decisions are incomplete.
- `BLOCKED`: one or more required controls are absent or unverified.
- `REFUSED`: the request conflicts with an invariant, production hard-disable, or explicit non-goal.

A boolean approval is not valid evidence and must not be interpreted as authority.

## Proposed interface contract

Any future integration proposal must bind all of the following before review:

- request ID, accountable owner, and expiry;
- exact deployment target and environment identity;
- allowed operations, resources, parameters, and explicit non-goals;
- initiating identities, service identities, roles, and delegated authority;
- policy, schema, invariant, model, runtime, and code versions;
- evidence record IDs, terminal chain anchor, witness attestations, and retention policy;
- attempt, cost, time, concurrency, and action-depth budgets;
- data classification, permitted storage, and network paths;
- credential and key references without embedding secret material;
- expected effects, failure modes, unresolved disagreements, and residual risk;
- rollback, credential revocation, worker drain, evidence preservation, and refusal plan; and
- exact human approvals bound to the complete proposal digest.

Missing, stale, conflicting, malformed, expired, or partially bound fields produce `BLOCKED` or `REFUSED`.

## Threat-model delta

| Boundary change | New threat or assumption | Required enforceable control | Current status |
|---|---|---|---|
| Local process to deployment host | Host compromise, bypass, privilege escalation | OS/container isolation, least privilege, measured deployment policy, bypass tests | **Blocked** |
| Process-local HMAC to protected custody | Key theft, substitution, unauthorized rotation | Protected key service, identity-bound use, rotation/revocation, audit | **Blocked** |
| Local SQLite to retained evidence | Tail/full deletion, rollback, backup tampering | Externally anchored terminal digest, immutable retention, restore verification | **Blocked** |
| Caller-supplied record to witnessed evidence | Witness signs fabricated or unverified evidence | Witness-owned verified replay and independent evidence retrieval | **Blocked** |
| In-process witness to independent authority | Shared compromise and collusion | Separate principals, custody, storage, revocation, quorum governance | **Blocked** |
| Caller-clocked leases to worker coordination | Time forgery, duplicate ownership, stale fencing | Trusted time, durable leases, transactional claims, external fencing | **Blocked** |
| Budget metadata to bounded execution | Unenforced consumption and action depth | Metered execution with hard exhaustion and signed accounting | **Blocked** |
| Offline synthetic calls to network transport | Spoofing, replay, interception, exposure | Mutual identity, channel binding, replay defense, egress controls | **Blocked** |
| Synthetic data to organizational data | Disclosure, poisoning, retention breach | Classification, minimization, authorization, DLP, deletion policy | **Blocked** |
| Benign tools to consequential actions | Real-world harm and ambiguous replay | Parameter authorization, human approval, idempotency, receipts, no replay | **Blocked** |

## Confirmed review findings

1. Phase 96 detects modified and middle-missing events but cannot detect deletion of the final event or the complete history without an external anchor.
2. Phase 97 verifies exact witness bindings after attestation but permits a local caller to request attestation for a constructed record that the witness has not independently replayed.
3. Phase 98 records budget metadata but does not meter or enforce budget consumption.
4. Witness persistence is separate but locally mutable and not itself an authenticated append-only chain.
5. Evidence append and workload coordination do not establish concurrent-writer or process-crash safety.

These findings do not invalidate the bounded synthetic experiments, but they prohibit stronger retention, independence, budget-enforcement, coordination, or readiness claims.

## Human approval contract

Any future boundary proposal requires named accountable human approval. High-impact scope requires two distinct active approvers. Approval must be cryptographically bound to the complete proposal digest, target, versions, identities, evidence, expiry, rollback plan, unresolved findings, expected effects, and residual risk.

Approval is invalid when self-approved, stale, revoked, incomplete, inherited from a roadmap, or detached from the exact proposal. Human approval cannot waive a security invariant through omission.

## Rollback and refusal plan

1. Start and deploy in default-deny state.
2. Verify target identity, policy versions, credentials, evidence anchors, witness quorum, budgets, and approvals before enablement.
3. Enable only the smallest staged scope and verify health without consequential action.
4. On mismatch or partial failure, stop workers, revoke credentials, preserve evidence, and return an explicit refusal code.
5. Do not retry, replay, silently repair, downgrade controls, or reinterpret ambiguous external outcomes.
6. Require a new exactly bound approval before any subsequent attempt.

## Deployment blocker checklist

- [ ] Protected identity and key custody with rotation and revocation
- [ ] Externally anchored append-only evidence and immutable backups
- [ ] Detectable tail deletion, full-history deletion, and rollback
- [ ] Witness-owned evidence verification and independent witness authority
- [ ] Witness revocation, conflict resolution, and compromise handling
- [ ] Trusted time, durable leases, transactional claims, and external fencing
- [ ] Enforced budgets, action depth, and cost accounting
- [ ] Concurrency, crash, power-loss, restore, and failover tests
- [ ] Enforced authorization for complete tool parameters
- [ ] Network identity, replay defense, egress policy, and transport security
- [ ] Data classification, minimization, retention, deletion, and DLP controls
- [ ] Operational ownership, incident response, rollback, and recovery runbooks
- [ ] Production hard-disable verification and deployment bypass tests
- [ ] Full regression and Phase 100 audit disposition

## Decision

**Phase 99 outcome: `BLOCKED`.**

The interface contract and review process are suitable as a planning artifact, but every production boundary remains blocked. Phase 99 does not authorize implementation, deployment, credentials, real data, network access, workers, or consequential tools. Phase 100 must retain or strengthen these blockers unless independently verified evidence resolves them.