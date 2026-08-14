# Nova Aegis Phase 66 - Durable Receipt Lifecycle

## Experiment

Exercise receipt registration, duplicate-ID conflict rejection, revocation retention in the local registry, and verification refusal after revocation. The registry remains an in-process synthetic witness.

## Decision

`CONTINUE` local lifecycle testing. Persistence across process failure, independent witnessing, revocation distribution, and consequential replay remain blocked.
