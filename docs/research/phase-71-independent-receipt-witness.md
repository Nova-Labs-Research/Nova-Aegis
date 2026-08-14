# Nova Aegis Phase 71 - Independent Receipt Witness Boundary

## Hypothesis

A receipt verifier should not rely on the same local authority that issued the receipt. A separate witness identity and injected key can test the minimum separation contract: distinct issuer and witness identities, receipt-content binding, and fail-closed signature verification.

## Experiment

`LocalReceiptWitness` signs a canonical digest of an `ExternalExecutionReceipt`. Verification rejects self-witnessing, receipt mutation, issuer mismatch, witness identity mismatch, and signatures produced by a different injected key.

## Decision

`ADAPT` for synthetic boundary testing only. The witness is still local, caller-labeled, and injected; it is not an independent external system, protected organizational identity, public-key trust root, durable witness log, or evidence that an external action occurred.

## Gate impact

No production gate changes. Consequential recovery, external evidence, networked MCP, and real-world action replay remain blocked. Human approval and no-handler-replay invariants remain required.
