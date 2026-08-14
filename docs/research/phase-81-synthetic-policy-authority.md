# Nova Aegis Phase 81 - Synthetic Policy Authority

## Hypothesis

A signed boundary decision needs a separate approval binding before it can be treated as a governed local release decision. The signer and approver must be distinct, the approval must match the exact preflight decision, and revoked or production-enabled approvals must fail closed.

## Experiment

`LocalSyntheticPolicyAuthority` issues and verifies signed policy releases using an injected key provider. It binds boundary, decision, signer, approver, approval ID, and production-disabled state. It rejects self-approval, mismatched approvals, revoked approvals, unknown keys, tampering, missing keys, and production state.

## Decision

`ADAPT` for synthetic governance testing only. The authority remains local, caller-labeled, and injected; it is not protected organizational policy authority, an approval control plane, or permission to enable real integrations.
