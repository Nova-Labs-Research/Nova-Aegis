# Nova Aegis Synthetic Trust Boundary Transition

## Status

**HERE BEGINS THE SYNTHETIC-TO-ENFORCED TRANSITION.**

The synthetic trust model does not end all at once. Each transition may replace exactly one synthetic assumption with an externally enforced control while consequential authority remains unchanged. Passing a transition does not imply production readiness or authorize the next transition.

| Transition | Boundary | Status | Audit requirement |
|---|---|---|---|
| T1 | Protected signing identity and key custody | Planning approved; implementation blocked pending service setup | Mandatory before T2 |
| T2 | Independently retained anchored state | Planned | Mandatory before T3 |
| T3 | Authenticated transport | Planned | Mandatory before T4 |
| T4 | Isolated real worker with synthetic tools | Planned | Mandatory before T5 |
| T5 | Trusted time, durable leases, and external fencing | Planned | Mandatory before T6 |
| T6 | Governed minimal credential and tool boundary | Planned | Mandatory before T7 |
| T7 | Consequential authority | `BLOCKED`; separate explicit authorization required | Dedicated authorization and audit |

## Transition rules

After each transition:

1. Identify the synthetic assumption replaced.
2. Identify every new trust assumption and attack surface introduced.
3. Run focused adversarial and complete regression tests.
4. Update the threat model, invariants, technical debt, and assurance claims.
5. Exercise refusal, unavailability, revocation, and rollback behavior.
6. Perform an audit before expanding the next boundary.
7. Preserve production hard-disable unless separately authorized.

A passing test suite does not grant authority. A real control inherits only the claims directly supported under its tested deployment conditions.