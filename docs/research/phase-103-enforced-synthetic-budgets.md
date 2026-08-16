# Nova Aegis Phase 103 - Enforced Synthetic Budgets

## Objective

Address AUD100-003 by converting attempt budgets from terminal metadata into pre-operation authorization limits.

## Implementation

`SyntheticWorkloadCoordinator.authorize_consumption` validates the exact active worker lease and fencing token, checks expiry, refuses duplicate operation IDs, atomically debits positive units, and refuses consumption beyond the work-item budget. Successful debit produces an HMAC-signed usage permit containing operation, ownership, units, cumulative usage, remaining budget, authorization time, and key ID. Terminal receipts include consumed units.

## Evidence

Six focused Phase 103 tests cover signed pre-operation debit, exact exhaustion, over-budget refusal without mutation, duplicate operations, forged and expired leases, terminal attempts, terminal accounting, tampered receipts, and unknown keys. Existing Phase 98 tests continue to cover scheduling, crash, timeout, and no replay.

## Decision

`ADAPT` for synthetic operations routed through the coordinator. AUD100-003 is mitigated inside this API. The application cannot prevent an out-of-band worker or tool from executing without a permit; execution-gateway enforcement and protected budget keys remain Phase 104 blockers.