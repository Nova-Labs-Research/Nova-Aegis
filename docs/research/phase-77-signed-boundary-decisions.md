# Nova Aegis Phase 77 - Signed Boundary Decisions

## Hypothesis

A local preflight decision should be tamper-evident when persisted or reviewed, but signing must not turn synthetic metadata into production authority. Binding a decision to its exact preflight report should reject mutation, unknown keys, and production state.

## Experiment

`SignedBoundaryDecision` signs the canonical boundary, decision, blockers, production-disabled state, and key identity. Verification requires a trusted injected key and an exact report match. Production-enabled state is always rejected.

## Decision

`ADAPT` for synthetic auditability only. The signer remains local and injected; it is not a protected policy authority, deployment control plane, organizational approval, or permission to enable real integrations.
