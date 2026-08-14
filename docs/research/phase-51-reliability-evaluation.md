# Nova Aegis Phase 51 - Representative Reliability Evaluation

## Scope

Phase 51 expands the Phase 47 fixed-workload comparison with metrics that distinguish genuine improvements from false reliability-driven route changes.

This remains a local synthetic experiment. Reliability history is not evidence, provenance, assurance, approval authority, or execution authority.

## Added Metrics

The replay result now reports:

- baseline accuracy;
- reliability-aware accuracy;
- accuracy delta;
- reliability-driven route changes;
- conservative fallback count;
- false route changes, where reliability changes the route to the wrong expected subject; and
- genuine improvements, where reliability changes an incorrect baseline route to the expected subject.

## Adversarial Coverage

The representative workload includes:

- fresh history supporting a genuine improvement;
- missing history requiring baseline fallback;
- a single-candidate unchanged route;
- tied history requiring baseline fallback; and
- valid-looking fabricated history that produces a measurable false route change.

Invalid outcome labels remain rejected at record time rather than interpreted.

## Observed Evidence

The replay evaluator can now expose whether a reliability signal helped, did nothing, or actively harmed the fixed workload. This is important because aggregate accuracy alone could hide unsafe route changes.

A false route change is observable and counted. The experiment does not silently convert it into a review or claim that the history was trustworthy.

## Decision

`DEFER`

Defer reliability-routing adoption. Continue only as controlled research until representative workloads, poisoning resistance, calibration, fairness, review burden, and independent history witnessing are evaluated.

## Remaining Risks

- Valid-looking fabricated history can still cause a false route change.
- Reliability records remain local and caller-supplied.
- Expected subjects in this experiment are synthetic labels, not independent ground truth.
- No reliability signal affects factual assurance or governance, which remains the required safety boundary.
