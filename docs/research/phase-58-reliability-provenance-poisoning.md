# Nova Aegis Phase 58 - Reliability Provenance and Poisoning Gate

## Scope

Phase 58 tests whether reliability routing can reject unverified operational history without allowing reliability metadata to influence factual assurance or governance.

## Change

`ReliabilityRecord` now carries synthetic provenance metadata: source, verification status, and observation ID. Routing accepts an explicit `require_provenance` gate. When enabled, a subject with missing, unverified, or incomplete observations is excluded from eligible history and the decision records the rejected subjects.

## Controlled Results

- Verified observations can support the isolated routing experiment.
- Caller-supplied unverified history is rejected by the provenance gate.
- Adding a forged observation to an otherwise verified subject causes conservative baseline fallback.
- Existing default behavior remains available for non-authoritative research comparisons.

## Decision

`ADAPT`

Retain provenance-gated routing as a synthetic research control. Do not treat the provenance fields as independent witnessing, truth evidence, assurance, approval authority, or execution authority.

## Remaining Risks

- Verification is caller-supplied and has no protected witness.
- Calibration, fairness, representative utility, review burden, and multi-party attestation remain open.
- Reliability can still be poisoned when the synthetic boundary is misconfigured.
