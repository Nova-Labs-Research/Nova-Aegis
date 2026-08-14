# Nova Aegis Phase 56 - Protected Corpus Manifest Experiment

## Scope

Phase 56 tests whether retrieval replay can bind a local corpus to a versioned, signed manifest without treating the manifest signer as production authority.

## Change

Added `CorpusManifest` with:

- canonical source-ID ordering;
- complete corpus SHA-256 binding;
- positive manifest versions;
- injected HMAC key selection;
- serialized round-trip support; and
- fail-closed verification for signature tampering, unknown keys, rollback below a required version, source changes, and corpus changes.

## Decision

`ADAPT`

Retain the manifest contract as a synthetic experiment. It provides an explicit integrity and version boundary for local retrieval, but the `LocalJournalKeyProvider` remains process-local synthetic custody and does not establish organizational identity or protected key management.

## Remaining Risks

- HMAC keys are not held by a protected service.
- Manifest roots are not externally anchored or independently witnessed.
- A valid manifest can still describe incorrect or unauthorized evidence.
- Key rotation, revocation, retention, and multi-node distribution remain unimplemented.
