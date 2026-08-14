# Nova Aegis Phases 61-70 Roadmap

## Governing gate

Phase 60 permits synthetic-only research. Protected identity, key custody, independent evidence, distributed coordination, trusted reliability routing, performance optimization, and networked MCP remain blocked until separately refactored and audited.

## Sequence

| Phase | Focus | Output | Gate |
|---|---|---|---|
| 61 | Corpus-manifest key lifecycle | Synthetic rotation, overlap, retirement, and fail-closed manifest verification | Continue only locally |
| 62 | Historical corpus snapshots | Versioned local snapshots bound to replay and unavailable-source refusal | Continue only locally |
| 63 | SQLite interruption and corruption probes | Recovery behavior for interrupted reads/writes and malformed trace records | Continue only locally |
| 64 | Reliability attestation experiment | Synthetic attestation envelope, contradiction handling, and poisoning metrics | Adoption remains deferred |
| 65 | Mandatory audit | Review Phases 60-64 and recheck all High blockers | Audit gate |
| 66 | Durable receipt lifecycle | Local receipt persistence, revocation retention, and conflict replay | No independent evidence claim |
| 67 | Synthetic transport envelope | Request/response metadata consistency, audience binding, and no-replay checks | No network enablement |
| 68 | Runtime performance evidence | Measurement fixture for prefill, repeated context, memory, and quality deltas | No optimization without bottleneck |
| 69 | Human review burden and fairness | Synthetic review-load and routing fairness evaluation | Reliability adoption remains deferred |
| 70 | Mandatory audit | Review Phases 65-69 and all unresolved production blockers | Audit gate |

Each phase requires a focused experiment, failure-mode tests, a research decision record, and a technical-debt update. No phase may convert synthetic metadata into authority.
