# Nova Aegis Phase 84 - Synthetic Policy Key Lifecycle

## Hypothesis

Synthetic policy release signing needs explicit key rotation and retirement semantics so successor releases can use a new key while retired keys fail closed. A caller-provided lifecycle authority can test the boundary without claiming protected key custody.

## Experiment

`LocalSyntheticPolicyKeyProvider` supports injected keys, active-key rotation, and non-active-key retirement. Rotation and retirement require the configured synthetic lifecycle authority. Releases issued after rotation use the successor key; verification of releases signed by a retired key fails.

## Decision

`ADAPT` for synthetic key-lifecycle testing only. Keys remain process-local and injected, with no protected custody, hardware backing, distributed propagation, or deployment enforcement. Real policy authority remains blocked.
