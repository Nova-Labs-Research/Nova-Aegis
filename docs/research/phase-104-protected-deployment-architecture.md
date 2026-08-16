# Nova Aegis Phase 104 - Protected Deployment Architecture Map

## Status

**Architecture map only.** Phase 104 does not implement or claim protected deployment controls. It defines the best offline-first path for addressing AUD100-004 and the remaining Phase 101-103 limitations.

## Target boundary

The application process must stop being its own trust root. Identity, keys, evidence anchors, witness authority, time, leases, fencing, budget enforcement, deployment policy, and rollback authority must be enforced by components outside the model and worker processes.

## Recommended architecture

### 1. Identity and key custody

- Run evaluator, witness, worker, and deployment controller under distinct least-privilege OS identities.
- Store signing keys in a local hardware-backed or OS-protected non-exportable key service suitable for air-gapped operation.
- Bind every signing operation to service identity, purpose, environment, and policy version.
- Require two distinct active humans for rotation, recovery, production scope changes, and trust-root replacement.
- Support explicit rotation, revocation, retirement, backup, restore, and compromise procedures.

### 2. Evidence and anchor retention

- Retain evidence and terminal checkpoints in separate failure domains.
- Use append-only or WORM-capable local retention with authenticated export to offline backup media or an air-gapped evidence appliance.
- Anchor store identity, event count, terminal digest, policy version, and trusted timestamp.
- Verify restore against an independently retained checkpoint before making evidence available.
- Detect tail deletion, full deletion, rollback, forked history, stale backup, and conflicting writers.

### 3. Independent witness authority

- Give witnesses separate principals, non-exportable keys, storage, and operational ownership.
- Require witness-owned retrieval from the retained evidence boundary; never accept caller-supplied records.
- Bind attestations to deployment identity, evidence checkpoint, policy version, expiry, and revocation state.
- Define quorum loss, disagreement, compromise, replacement, and emergency refusal behavior.

### 4. Durable coordination and trusted time

- Persist claims, leases, fencing tokens, usage, and terminal outcomes transactionally.
- Use a trusted monotonic time source controlled outside workers.
- Make the target resource enforce fencing tokens; application metadata alone is insufficient.
- Refuse stale owners, duplicate claims, clock rollback, expired leases, split brain, and ambiguous recovery.
- Never automatically replay an attempt after crash, timeout, or uncertain external outcome.

### 5. Execution-gateway budget enforcement

- Require a valid signed budget permit before every tool or worker operation.
- Debit units atomically before dispatch and bind permits to exact parameters, worker, lease, operation ID, and expiry.
- Have the execution gateway reject missing, stale, duplicated, exhausted, or mismatched permits.
- Define deterministic units for each tool and retain signed usage and terminal receipts.
- Prevent direct alternate tool paths that bypass the gateway.

### 6. Deployment enforcement

- Deploy from a signed manifest binding code, model, policy, schema, identities, keys, network policy, data classification, and rollback plan.
- Keep production disabled unless an external deployment controller verifies the complete manifest and human approvals.
- Default deny startup on missing custody, anchor, witness, clock, lease, budget, audit, or policy state.
- Enforce network deny-by-default, explicit local/intranet allowlists, and no implicit online dependency.
- Preserve evidence and revoke credentials before rollback; do not silently repair or replay.

## Implementation sequence

1. Select and threat-model the concrete offline deployment platform and protected key facility.
2. Prototype non-exportable signing and distinct service identities without real data or tools.
3. Add independently retained evidence anchors and restore verification.
4. Move witness verification into a separate service identity and storage failure domain.
5. Add durable transactional coordination, trusted time, and resource-enforced fencing.
6. Put every synthetic operation behind the permit-enforcing execution gateway.
7. Add signed deployment manifests, default-deny startup, revocation, rollback, and incident runbooks.
8. Run adversarial concurrency, power-loss, restore, rollback, key-compromise, bypass, and no-replay tests before any integration review.

## Acceptance gates

- Keys are non-exportable and lifecycle operations are identity-bound and audited.
- Evidence truncation, rollback, fork, full deletion, and restore mismatch are detected across failure domains.
- Witnesses cannot read evaluator keys or storage credentials and independently verify retained evidence.
- Leases survive process loss; trusted time and fencing are enforced outside workers.
- No operation executes without a valid unspent permit, including alternate endpoints.
- Production startup fails closed when any required control is absent or inconsistent.
- Recovery never automatically replays ambiguous external actions.
- A human-reviewed threat-model delta, rollback exercise, full regression, and Phase 105 audit approve the exact boundary.

## Decision

`REFACTOR` before implementation against a chosen deployment platform. Local process simulations cannot resolve AUD100-004. Phase 104 should proceed only after concrete platform, custody, retention, identity, and operational ownership decisions are supplied and reviewed.