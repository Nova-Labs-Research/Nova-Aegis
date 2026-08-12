# Nova Aegis

*Local-first governed AI architecture for evidence-grounded, auditable work.*

> Private by location. Grounded by evidence. Governed by design.

Nova Aegis is an experimental architecture under development by **Nova Labs Research**. It explores how local-first systems can preserve evidence, provenance, uncertainty, authorization boundaries, and reviewability while coordinating AI-assisted work.

This repository captures the architecture, threat model, security invariants, and initial design requirements. It is not a production platform, an autonomous investigator, or a system for determining truth. The documents describe intended boundaries and research questions; they do not claim that those mechanisms are implemented or validated.

## Architectural Frame

The intended flow is:

```text
raw input
  -> ingestion / normalization
  -> evidence, provenance, and lineage
  -> memory / graph / claims
  -> associative retrieval / attention
  -> activated context
  -> bounded reasoning
  -> discourse / review output
  -> persistence / evaluation / adversarial testing
```

The main conceptual areas are:

- **NIC** - evidence and graph-oriented knowledge representation
- **Cortex** - cognition, orchestration, retrieval, and selective memory
- **Praetor** - governance, assurance, authorization, and review boundaries
- **Nova Aegis Core** - identity, routing, execution boundaries, and audit

These names describe research boundaries, not independent products or claims of capability.

## Repository Status

**Status: Architecture and threat-modeling phase**

The implementation surface is intentionally small while the conceptual contract is being tested. New mechanisms should fit the canonical flow, preserve uncertainty and lineage, and be introduced as core, auxiliary, or experimental work.

## Documents

- [Problem statement](docs/problem_statement.md)
- [Design principles](docs/design_principles.md)
- [High-level architecture](docs/high_level_architecture.md)
- [Threat model](docs/threat_model.md)
- [Security invariants](docs/security_invariants.md)
- [Conceptual heritage](references/conceptual_heritage.md)
- [Canonical flow](architecture/diagrams/canonical-flow.md)

## Epistemic Boundary

Nova Aegis must not silently turn ingestion into confirmation, retrieval into support, similarity into corroboration, salience into validity, repeated lineage into independent evidence, or discourse into a flattened narrative. Contradictions and uncertainty are first-class research state.

## License and Contribution Status

No license or contribution policy has been selected yet. Until that decision is made, treat this as a research archive and do not assume permission to reuse it.
