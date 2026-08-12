# Security invariants

These invariants are intended to constrain future implementation and review.

1. **No silent endorsement:** ingestion and normalization must not mark an input as true, supported, or corroborated.
2. **Lineage preservation:** every derived evidence-bearing object must retain a link to its source objects and transformations.
3. **Contradiction preservation:** conflicting observations and claims must remain representable and retrievable.
4. **Typed epistemic state:** observation, interpretation, speculation, association, support, contradiction, and discourse must not be interchangeable labels.
5. **No association inflation:** retrieval, similarity, salience, and reinforcement must not increase evidentiary status by implication.
6. **Bounded execution:** reasoning and external actions must have explicit scope, identity, authorization, and stopping conditions.
7. **Reviewable decisions:** security- and governance-relevant decisions must leave enough context to be reconstructed and challenged.
8. **Minimal exposure:** data should cross local or connector boundaries only for an explicit, authorized purpose.
9. **Public API restraint:** internal or experimental concepts must not become public interfaces without a documented research need.
10. **Honest status:** documentation and evaluation must distinguish intended behavior, local tests, and evidence from external reality.

An implementation that cannot preserve these invariants should be treated as an experiment requiring explicit documentation, not silently folded into the main path.

