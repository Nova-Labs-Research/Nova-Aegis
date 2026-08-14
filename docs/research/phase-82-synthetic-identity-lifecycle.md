# Nova Aegis Phase 82 - Synthetic Identity Lifecycle

## Hypothesis

Phase 81 signer and approver fields must be checked against an explicit identity source. A local registry with terminal revocation can test that unknown or revoked identities fail closed without claiming protected organizational identity.

## Experiment

`LocalSyntheticIdentityRegistry` tracks explicitly registered identities and terminal revocations. `LocalSyntheticPolicyAuthority` receives the registry as an injected dependency and validates both signer and approver during issue and verify. Re-registration after revocation is rejected.

## Decision

`ADAPT` for synthetic governance testing only. The registry provides a deterministic local identity boundary, but it is not protected identity, key custody, organizational authorization, or deployment enforcement. Phase 85 remains the next mandatory audit checkpoint.
