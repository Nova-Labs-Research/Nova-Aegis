# Threat model

This is a research threat model for architectural discipline, not a certification or production security assessment.

## Assets

- Raw inputs and their provenance
- Evidence, claims, contradictions, and uncertainty state
- Identity and authorization decisions
- Execution traces, audit records, and evaluation artifacts
- Local data and connector credentials

## Threats and failure modes

| Threat | Failure mode | Required response |
| --- | --- | --- |
| Provenance loss | A transformed or summarized item no longer points to its origin | Preserve immutable source references and transformation lineage |
| Epistemic collapse | Observation, interpretation, and speculation are presented as one kind of fact | Keep typed boundaries visible in storage and discourse |
| False corroboration | Similar or repeated material is treated as independent confirmation | Track lineage and independence explicitly |
| Contradiction suppression | Conflicting evidence disappears during retrieval or synthesis | Preserve and surface contradiction sets |
| Unauthorized action | A context or model output crosses an execution boundary without approval | Require explicit identity, authorization, and bounded routing |
| Data overexposure | Local or connector-backed material leaves its permitted boundary | Minimize transfer and record export decisions |
| Audit opacity | A result cannot be reconstructed from inputs and decisions | Persist reviewable event and decision lineage |
| Salience bias | Attention or memory reinforcement is mistaken for validity | Label salience as attention state only |

## Out of scope

This baseline does not claim resistance to every implementation vulnerability, side-channel attack, compromised host, malicious model, or organizational process failure. Those require later, scoped studies with explicit assumptions and test evidence.

