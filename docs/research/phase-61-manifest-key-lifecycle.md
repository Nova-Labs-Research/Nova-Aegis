# Nova Aegis Phase 61 - Corpus Manifest Key Lifecycle

## Scope

Phase 61 evaluates key overlap, rotation, and retirement for synthetic corpus manifests. It uses the existing local `LocalJournalKeyProvider` only as an injected test authority.

## Experiment

A manifest signed with an active key must verify during trusted overlap. After rotation, a new manifest uses the new active key while the old key can verify retained historical manifests. Retiring the old key must fail closed for those historical manifests. Unauthorized lifecycle operations must be rejected.

## Decision

`ADAPT`

Retain the lifecycle behavior for local testing. It does not establish protected key custody, organizational authorization, immutable anchoring, or distributed key consistency.
