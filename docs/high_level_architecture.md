# High-level architecture

Nova Aegis is organized around one canonical path. Components may be implemented separately, but their conceptual relationship should remain legible.

| Stage | Research responsibility | Must preserve |
| --- | --- | --- |
| Ingestion / normalization | Accept and normalize raw material without endorsing it | Original input and transformation lineage |
| Evidence / provenance / lineage | Describe what was observed, where it came from, and how it changed | Source, time, uncertainty, and custody context |
| Memory / graph / claims | Connect observations, interpretations, claims, and contradictions | Type boundaries and competing states |
| Retrieval / attention | Select relevant context for inspection | Association labels and retrieval rationale |
| Activated context | Assemble bounded context for a reasoning episode | Included and excluded material |
| Bounded reasoning | Produce provisional inferences or questions | Assumptions, uncertainty, and stopping limits |
| Discourse / review output | Present material for human review | Provenance, disagreement, and confidence limits |
| Persistence / evaluation / adversarial testing | Record state and test failure modes | Reproducibility and test scope |

The architectural names NIC, Cortex, Praetor, and Nova Aegis Core are useful lenses over this path. They should not become four opaque layers that hide the movement of evidence or duplicate responsibility.

See [the diagram](../architecture/diagrams/canonical-flow.md) for a compact view.

