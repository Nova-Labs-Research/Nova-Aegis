# Nova Aegis Phase 97 - Independent Synthetic Evidence Witness

## Reopening decision

On 2026-08-16, the project owner explicitly requested Phase 97 after completing Phase 96. This reopens **Phase 97 only**. Phases 98-100 remain frozen, and the Phase 95 production blockers remain unchanged.

## Hypothesis

A local witness can provide a distinct corroboration path when it has a different identity, signing key, and SQLite store from the evaluator evidence boundary. The witness must bind the exact evidence ID, sequence, type, digest, evaluator identity, and witness identity. Self-witnessing, substituted evidence, invalid signatures, duplicate witnesses, unknown witnesses, insufficient quorum, conflicts, and missing attestations must fail closed.

## Experiment

`LocalSyntheticEvidenceWitness` signs an exact Phase 96 evidence binding with a witness-only HMAC key. `SQLiteSyntheticEvidenceWitnessStore` persists attestations in a separate caller-supplied SQLite connection. `SyntheticEvidenceWitnessArbiter` verifies every attestation against the actual evidence record and requires a configurable quorum of distinct known witnesses.

## Separation assumptions

- Evaluator and witness identities must be distinct.
- Witness keys are supplied directly to witness instances and are not obtained from the Phase 96 evidence key provider.
- Witness attestations are tested in a separate SQLite database from evaluator evidence.
- The caller remains responsible for deploying genuinely separate storage paths and principals.
- Local process compromise can still control the evaluator, witnesses, keys, and both databases.

## Evidence

Six focused tests cover separate-store restart replay, self-witness refusal, exact-binding substitution refusal, signature tampering, distinct quorum, duplicate/unknown/insufficient witnesses, conflicting persistence, and missing attestations.

## Decision

`ADAPT` for synthetic witness-separation experiments only. Phase 97 adds a distinct local verification path but does not establish independent external evidence, organizational authority, protected key custody, immutable storage, or compromise independence. Phases 98-100 remain frozen pending separate human review.