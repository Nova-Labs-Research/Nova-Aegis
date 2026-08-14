# Nova Aegis

*Local-first governed AI architecture for evidence-grounded, auditable work.*

> Private by location. Grounded by evidence. Governed by design.

Nova Aegis is an experimental architecture under development by **Nova Labs Research**. It explores how local-first systems can preserve evidence, provenance, uncertainty, authorization boundaries, and reviewability while coordinating AI-assisted work.

This repository captures the architecture, threat model, security invariants, and a dependency-free synthetic implementation of core governed-flow controls. It is not a production platform, an autonomous investigator, a real MCP server, or a system for determining truth.

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

**Status: Synthetic governed-workstation proof**

The executable slice currently demonstrates local retrieval/evidence assurance and replay, corpus-bound integrity, Agent K rule traces, semantic/deterministic fusion, synthetic identity and policy checks, tamper-evident local audit, idempotent execution receipts, witness separation and local witness replay, deterministic boundary preflight, and a synthetic MCP Gateway.

It does **not** implement a real MCP HTTP/OAuth server, a live semantic evaluator, a verified authoritative corpus, external identity, protected production audit storage, distributed task state, or real consequential tools.

## Current Validation

Run the local test suite from the repository root:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
pytest -q
```

The current audit gate is [Phase 80](docs/audits/phase-80-audit.md), with Phase 82 continuing synthetic research. The latest full validation reports 139 passing tests; compilation and diff integrity checks also pass. Synthetic work may continue, while protected identity and key custody, independent external evidence, distributed recovery, trusted reliability routing, networked MCP, real data, live semantic evaluation, and consequential tools remain blocked pending their documented controls.

## Documents

- [Problem statement](docs/problem_statement.md)
- [Design principles](docs/design_principles.md)
- [High-level architecture](docs/high_level_architecture.md)
- [Threat model](docs/threat_model.md)
- [Security invariants](docs/security_invariants.md)
- [Technical debt ledger](docs/technical_debt.md)
- [Five-phase audit policy](docs/audit_policy.md)
- [Phases 61-75 roadmap](docs/research/phase-61-70-roadmap.md)
- [Phase 76 boundary preflight research](docs/research/phase-76-enforceable-boundary-preflight.md)
- [Phase 77 signed boundary decision research](docs/research/phase-77-signed-boundary-decisions.md)
- [Phase 78 durable signed boundary replay research](docs/research/phase-78-durable-signed-boundary-replay.md)
- [Phase 79 decision revocation and supersession research](docs/research/phase-79-decision-revocation-supersession.md)
- [Phase 5 audit](docs/audits/phase-05-audit.md)
- [Phase 10 audit](docs/audits/phase-10-audit.md)
- [Phase 15 audit](docs/audits/phase-15-audit.md)
- [Phase 20 audit](docs/audits/phase-20-audit.md)
- [Phase 25 audit](docs/audits/phase-25-audit.md)
- [Phase 30 audit](docs/audits/phase-30-audit.md)
- [Phase 35 audit](docs/audits/phase-35-audit.md)
- [Phase 40 audit](docs/audits/phase-40-audit.md)
- [Phase 45 audit](docs/audits/phase-45-audit.md)
- [Phase 50 audit](docs/audits/phase-50-audit.md)
- [Phase 55 audit](docs/audits/phase-55-audit.md)
- [Phase 60 audit](docs/audits/phase-60-audit.md)
- [Phase 65 audit](docs/audits/phase-65-audit.md)
- [Phase 70 audit](docs/audits/phase-70-audit.md)
- [Phase 75 audit](docs/audits/phase-75-audit.md)
- [Phase 80 audit](docs/audits/phase-80-audit.md)
- [Phase 81 synthetic policy authority research](docs/research/phase-81-synthetic-policy-authority.md)
- [Phase 82 synthetic identity lifecycle research](docs/research/phase-82-synthetic-identity-lifecycle.md)
- [Conceptual heritage](references/conceptual_heritage.md)
- [Canonical flow](architecture/diagrams/canonical-flow.md)

## Epistemic Boundary

Nova Aegis must not silently turn ingestion into confirmation, retrieval into support, similarity into corroboration, salience into validity, repeated lineage into independent evidence, or discourse into a flattened narrative. Contradictions and uncertainty are first-class research state.

## License and Contribution Status

No license or contribution policy has been selected yet. Until that decision is made, treat this as a research archive and do not assume permission to reuse it.
