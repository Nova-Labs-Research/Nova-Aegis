# Design principles

## Evidence before synthesis

Raw inputs, normalized observations, interpretations, associations, and discourse outputs remain distinguishable. A later layer may reference an earlier layer, but must not erase it.

## Provenance travels with data

Every evidence-bearing object should retain its source, transformation history, timing, and relevant custody or authorization context. Lineage is part of the object, not an afterthought in a log.

## Uncertainty remains visible

Unknown, incomplete, conflicting, and low-confidence states are valid states. The architecture should make them inspectable rather than forcing a single value for convenience.

## Contradictions are useful state

Contradictory observations and claims should be preserved, linked, and surfaced for review. They should not be silently averaged away or resolved by rhetorical fluency.

## Association is not support

Retrieval, semantic similarity, co-occurrence, salience, and memory reinforcement can guide attention. None of them independently establishes corroboration, validity, or truth.

## Reasoning is bounded and review-oriented

Reasoning should expose its inputs, assumptions, uncertainty, and stopping conditions. It should support human inspection rather than imply autonomous authority.

## Local-first is a boundary, not a guarantee

Local execution can reduce unnecessary exposure, but it does not by itself make data safe, correct, authorized, or private. Storage, connectors, exports, and execution paths still require explicit controls.

## Small public surface

Core primitives should remain intentional. Experimental modules, adversarial harnesses, and documentation artifacts should not automatically become public API.

