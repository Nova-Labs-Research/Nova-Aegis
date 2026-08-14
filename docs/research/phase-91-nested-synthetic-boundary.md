# Nova Aegis Phase 91 - Nested Synthetic Boundary

## Hypothesis

A boundary evaluation needs an explicit capability manifest and observable teardown contract before outcome validity can be tested. A benign process-local inner boundary can model those contracts without claiming host or kernel isolation.

## Experiment

`SyntheticNestedBoundary` accepts a `SyntheticBoundaryManifest` containing a boundary ID and a narrow capability allowlist. The manifest rejects host, real-filesystem, network, and production access. The boundary permits only the benign `echo` operation for granted capabilities, rejects unavailable or ungranted requests, and exposes teardown state.

## Decision

`ADAPT` for synthetic contract testing only. This implementation does not create an OS sandbox, container, VM, kernel boundary, or protected deployment control. It cannot establish real containment or generalize to frontier-agent security. Phase 92 may build on the manifest and result contract for outcome-validity tests.
