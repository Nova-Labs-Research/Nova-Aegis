# Nova Aegis Phases 86-89 Roadmap

## Governing boundary

Phases 86-89 remain synthetic-only experiments following the Phase 85 audit. They may improve local durability, integrity checks, approval separation, and deployment-boundary testing, but must not create protected authority, real identity, production key custody, network access, or consequential execution.

## Sequence

| Phase | Focus | Primary question | Required evidence | Gate |
|---|---|---|---|---|
| 86 | Durable synthetic policy-key lifecycle | Can policy-key rotation and retirement survive process restart with deterministic active-key replay? | Append-only local lifecycle events, close/reopen replay, successor signing, retired-key refusal, malformed-event refusal | No protected custody claim |
| 87 | Synthetic lifecycle integrity and corruption refusal | Can tampered, truncated, duplicated, or contradictory key/identity events fail closed without reconstructing authority? | Event digest or integrity binding, corruption probes, contradiction tests, unavailable-state refusal, no silent repair | No immutable-retention claim |
| 88 | Synthetic two-person rotation ceremony | Can key rotation require two distinct active identities and a bound approval rather than a caller-supplied lifecycle string? | Signed rotation request, distinct proposer/approver, identity and approval revocation, stale-request refusal, production-disabled state | No organizational approval claim |
| 89 | Synthetic deployment-boundary enforcement | Can a release be rejected when deployment context, policy epoch, key state, or approval state is inconsistent, even if the local signature is valid? | Explicit synthetic deployment context, exact epoch binding, retired-key refusal, revoked approval refusal, production hard block, no action replay | No production enablement |

## Dependencies

- Phase 86 depends on the Phase 84 synthetic key provider and Phase 83 append-only replay patterns.
- Phase 87 depends on Phase 86 event shape and must preserve fail-closed behavior on unavailable or malformed state.
- Phase 88 depends on the Phase 82 identity registry and Phase 81 signed approval binding.
- Phase 89 composes Phases 86-88 but remains a local preflight experiment, not a deployment control plane.

## Required tests

Each phase requires happy-path and adversarial tests. The minimum matrix is:

- restart replay and active-key reconstruction;
- unknown, revoked, retired, malformed, truncated, duplicated, and contradictory lifecycle state;
- distinct active proposer and approver identities;
- tampered or stale rotation approvals;
- approval and identity revocation during verification;
- epoch or deployment-context mismatch; and
- explicit production request rejection with no handler replay.

## Explicit non-goals

These phases do not introduce external identity, HSM/KMS custody, certificate trust roots, network transport, distributed consensus, immutable audit storage, organizational approval, real deployment authorization, or consequential tools.

## Audit checkpoint

Phase 90 remains the next mandatory audit. It must review Phases 85-89 and re-evaluate every High blocker before any boundary expansion.
