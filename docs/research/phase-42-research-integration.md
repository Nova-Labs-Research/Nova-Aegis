# Nova Aegis Phase 42 - Research Integration and Architecture Gap Review

## Purpose

Evaluate research ideas against the Phase 41 architecture before introducing new capabilities. A paper is evidence that an idea deserves investigation, not evidence that Nova Aegis needs the feature.

This phase is documentation-only. It produces architecture comparisons, falsifiable hypotheses, controlled experiment designs, and research decisions. It does not change runtime behavior.

## Baseline: Phase 41

Phase 41 provides an offline-first, local-first, fail-closed synthetic control boundary. The current system includes:

- evidence and provenance-aware retrieval foundations;
- bounded reasoning through Praetor and explicit assurance outcomes;
- local task, approval, recovery journal, and audit persistence;
- authenticated and versioned synthetic recovery journals;
- injectable journal-key lookup and lifecycle authority;
- human approval requirements for recovery;
- no automatic replay of ambiguous external actions; and
- explicit production blockers for protected identity, key custody, distributed coordination, real transport, and independent external evidence.

The reference flow is:

```text
Evidence
   -> Provenance / Lineage
   -> Memory / Graph / Claims
   -> Retrieval
   -> Activated Context
   -> Bounded Reasoning
   -> Governance / Review
   -> Audit / Persistence
```

The baseline rule for all candidates is:

> Memory may help locate evidence. Memory does not become evidence merely because it was remembered.

## Research Questions

### MOSS: Auditable Structured Memory

**Comparison:** MOSS structured memory should be compared with Aegis provenance, claims, retrieval, recovery journal, and audit records. The relevant gap is not whether Aegis uses the same terminology, but whether a memory decision is inspectable and reproducible.

**Hypothesis:** Aegis can reconstruct why evidence entered activated context only when retrieval records the query, authority scope, candidate set, ranking inputs, selected identifiers, and provenance links. Existing audit records must be checked before claiming this property.

**Experiment required:** Trace one retrieval-to-context path and attempt deterministic reconstruction from persisted records alone.

**Acceptance criteria:** An independent reviewer can identify the selected memory, its source evidence, authority, ranking decision, and exclusions without relying on model narration.

**Provisional decision:** `EXPERIMENT`.

### Directory-Aware Retrieval: Hierarchical Evidence Scope

**Comparison:** Compare the proposed hierarchy of corpus, system, subsystem, document, revision, section, and evidence with the current document and provenance model.

**Hypothesis:** Authority and structural scope should constrain the candidate set before semantic similarity is allowed to rank evidence. This will reduce semantically similar but contextually or authoritatively incorrect results.

**Experiment required:** Construct an adversarial corpus containing same-topic evidence across systems, revisions, and authority levels. Compare unrestricted semantic retrieval with authority-first and hierarchy-first retrieval.

**Acceptance criteria:** Scoped retrieval reduces incorrect cross-boundary selections without suppressing valid in-scope evidence, and every exclusion is explainable.

**Provisional decision:** `EXPERIMENT`.

### Sigma-Mem: Reliability-Aware Agent History

**Comparison:** Reliability history is operational metadata about agents or tools, not factual evidence. It must remain separate from claims, provenance, and evidence confidence.

**Hypothesis:** Historical reliability can improve routing or review allocation when used only as an orchestration signal, while factual truth remains determined by current evidence and authority.

**Experiment required:** Replay a fixed routing workload with and without reliability signals. Keep factual inputs identical and measure routing quality, review burden, and authority leakage.

**Acceptance criteria:** Reliability improves routing metrics without changing evidence truth values, claim provenance, assurance rules, or approval requirements.

**Provisional decision:** `EXPERIMENT`, only after the evidence boundary is instrumented.

### SIFT: Selective Prefill Reuse

**Comparison:** SIFT is a performance optimization candidate, not a memory or governance capability.

**Hypothesis:** Prefill or repeated-context computation is not a justified optimization target until local measurements show it is a meaningful share of end-to-end latency and reuse does not weaken context integrity.

**Experiment required:** Profile retrieval, context assembly, inference prefill, generation, memory use, and repeated-document workloads.

**Acceptance criteria:** A measured bottleneck exists; a prototype improves latency or resource use; retrieval quality, evidence identity, provenance, and deterministic audit behavior remain unchanged.

**Provisional decision:** `DEFER` pending profiling.

## Memory Integrity and Perturbation Plan

Before expanding memory capabilities, test stale, poisoned, contradictory, superseded, unavailable, provenance-less, metadata-corrupted, incorrectly-authorized, semantically-neighboring, and conflicting current/historical memory.

Expected behavior:

```text
Evidence integrity decreases
        -> uncertainty increases
        -> authority and autonomy decrease
        -> abstention or human review increases
```

A failed perturbation test is evidence against adoption, not a reason to add a silent fallback.

## Research Decision Records

Each candidate must retain this record before implementation:

```text
Reference:
Concept:
Existing Aegis Equivalent:
Observed Gap:
Potential Benefit:
New Attack Surface:
Reliability Implications:
Hypothesis:
Experiment Required:
Acceptance Criteria:
Decision:
Evidence Supporting Decision:
Known Limitations:
```

No candidate receives a phase number merely because it is interesting. The sequence is:

```text
Research -> gap -> hypothesis -> experiment -> evidence -> decision -> implementation
```

## Phase 42 Gate

- Runtime implementation: none permitted in this phase.
- Required outputs: baseline comparison, gap analysis, hypotheses, experiment designs, and decision records.
- Phase 43 may implement only an experiment justified by Phase 42 evidence.
- Phase 45 remains the next mandatory five-phase audit checkpoint.
- Human review is required before any candidate changes retrieval authority, memory trust, routing authority, or inference behavior.

## Initial Recommendation

Prioritize the candidates in this order:

1. MOSS architecture-gap experiment: determine whether retrieval decisions are reconstructable.
2. Directory-aware retrieval experiment: test authority and hierarchy filtering before semantic ranking.
3. Sigma-Mem isolated routing experiment: enforce the factual-memory versus reliability-memory boundary.
4. SIFT profiling: defer optimization until measurements identify a real bottleneck.
