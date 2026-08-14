# Nova Aegis Phase 43 - Retrieval Reconstruction and Scope Experiment

## Scope

Phase 43 implements the first Phase 42 experiment: determine whether retrieval decisions can be reconstructed and whether authority and hierarchy can constrain the candidate set before lexical ranking.

This remains a local synthetic experiment. It does not add vector retrieval, external memory, autonomous routing, or new authority.

## Change

`Evidence` now supports an optional ordered `hierarchy`. `LocalRetriever.retrieve_with_trace` applies the following order:

```text
Authority scope
    -> Hierarchy prefix
    -> Lexical ranking
    -> Limit / activated citations
```

The trace records:

- the original question;
- authority and hierarchy scopes;
- all source candidates;
- candidates remaining after authority filtering;
- candidates remaining after hierarchy filtering;
- ranked source identifiers and scores; and
- selected source identifiers.

`NovaAegisMVP` includes this trace in the `retrieval_completed` audit event. The existing `retrieve` API remains compatible and uses the same implementation without optional scopes.

## Hypothesis

Aegis can reconstruct why evidence entered activated context when the audit trail records the query, scopes, candidate set, filtering stages, ranking inputs, scores, and selected identifiers. Authority and hierarchy filtering before ranking should prevent semantically similar but out-of-scope evidence from competing with in-scope evidence.

## Controlled Test

The adversarial corpus contains:

- one in-scope, trusted document;
- one semantically similar document with the wrong authority; and
- one semantically similar document in the wrong hierarchy branch.

The retrieval request allows only the trusted authority and the `corp / ops` hierarchy prefix.

## Observed Evidence

- The trusted document is selected.
- The wrong-authority document is removed before hierarchy filtering and ranking.
- The wrong-branch document is removed before ranking.
- The trace identifies each stage and the selected source deterministically.
- Existing retrieval, assurance, adversarial, and Agent K tests remain passing.

## Decision

`ADAPT`

Adopt the trace and pre-ranking scope mechanism as a bounded retrieval capability. Do not treat this as proof of complete memory auditability or hierarchical retrieval quality. The current lexical ranker remains intentionally simple, and callers must provide trusted scopes explicitly.

## Acceptance Status

- Reconstruction of the tested retrieval path: **passed**.
- Authority filtering before ranking: **passed**.
- Hierarchy filtering before ranking: **passed**.
- Out-of-scope semantic-neighbor exclusion: **passed**.
- Retrieval quality across broad corpora: **not established**.
- Persistence and independent replay of retrieval traces: **not established**.
- Vector, graph, and memory integration: **not implemented**.

## Remaining Risks

- A caller that supplies an overly broad scope can still retrieve overly broad evidence.
- The in-memory audit path is inspectable, but durable audit replay of retrieval traces is not yet separately tested.
- Hierarchy metadata is caller-supplied and is not independently authenticated.
- Retrieval traces explain selection mechanics but do not make evidence authoritative.

## Next Gate

Phase 44 should focus on memory-integrity perturbation and reliability-boundary experiments only if they remain justified. No semantic-memory trust, reliability-based factual scoring, or performance optimization follows automatically from this result.
