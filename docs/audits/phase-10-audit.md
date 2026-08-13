# Nova Aegis Audit - Phase 10

## Scope

- **Phases reviewed:** Phases 6-9
- **Change range:** `6a2f942..c7f3e51`
- **Auditor:** GitHub Copilot
- **Date:** 2026-08-13
- **Operating profile:** Single-process synthetic workstation MVP with no real organizational data, no real MCP server, and no consequential external action.

This is the mandatory fifth-phase audit required after Phase 10. It reviews the adversarial evidence controls, STRIDE-AI/ATLAS mapping, durable audit boundary, identity boundary, policy integrity checks, source code, tests, and technical-debt records. It does not certify production authorization, enterprise identity, real MCP enforcement, or external audit immutability.

## Validation

Commands and results:

- `$env:PYTHONPATH='src'; pytest -q` -> **35 passed**.
- `python -m compileall -q src tests` -> **passed**.
- Editor diagnostics for `src`, `tests`, and `docs` -> **no errors**.
- `git diff --check` -> **passed**.
- Direct Phase 10 probes -> **passed** for issued identity, forged identity, policy mutation, and audit tampering.
- Repository state -> `main`, clean, synchronized with `origin/main` at `c7f3e51`.

The focused test suites cover 35 tests in total, including adversarial retrieval, Praetor authorization, SQLite audit integrity, identity credentials, expiry/revocation, and policy mutation.

## Findings

| ID | Severity | Area | Finding | Required action | Owner | Due date |
|---|---|---|---|---|---|---|
| AUD10-001 | Medium | Identity trust root | `IdentityAuthority` is a synthetic process-local issuer. Its secret, issued-token registry, and revocation registry are memory-local; legacy callers can still provide `user_id` and `role` without a credential. | Require authenticated Core-issued context and remove or isolate legacy caller-supplied authorization before multi-user deployment or real tools. | Nova Aegis | Before real MCP or multi-user phase |
| AUD10-002 | Medium | Policy integrity | Praetor detects in-process mutation through a startup fingerprint, but policy fingerprints are not persisted, externally anchored, versioned, or administered by a protected policy service. | Add signed/versioned policy storage and authorization to change policy before production use. | Nova Aegis | Before real policy administration |
| AUD10-003 | Medium | Audit trust boundary | SQLite persistence and hash chaining detect modification within the local database trust model, but storage is not encrypted, access-controlled, externally anchored, replicated, or independently monitored. | Add protected storage, key management, external anchoring or replication, retention, and audit-read authorization. | Nova Aegis | Before production audit storage |
| AUD10-004 | Medium | MCP enforcement | The tested execution route is synthetic application code. A real MCP Gateway or server-side rejection of calls without valid authorization context does not exist. | Implement gateway/server enforcement and response validation before connecting any real tool. | Nova Aegis | Before real MCP phase |
| AUD10-005 | Medium | Evidence verification | Conflict and lifecycle decisions are implemented, but provenance and claim metadata remain corpus-supplied and are not independently source/hash verified. | Add verified source objects, revision relationships, and provenance integrity checks before an authoritative corpus. | Nova Aegis | Before authoritative corpus phase |
| AUD10-006 | Low | ATLAS coverage | The STRIDE-AI and MITRE ATLAS mapping is a useful working crosswalk, but several mapped areas remain architecture-only because memory, real tools, model supply-chain verification, and network enforcement are absent. | Revalidate the living ATLAS mapping and add executable tests as each boundary is implemented. | Nova Aegis | Phase 15 audit |

### Finding interpretation

No finding is Critical or High for the evaluated synthetic profile because no real external action, real confidential corpus, or multi-user identity boundary is connected. AUD10-001 through AUD10-005 become High or release-blocking conditions if the system is deployed beyond that profile without their required controls.

The presence of a passing synthetic credential test must not be interpreted as enterprise authentication, and a local hash chain must not be interpreted as independent audit immutability.

## Confirmed Vulnerabilities

No Critical or High vulnerability was confirmed for the evaluated profile.

The following are confirmed architectural limitations and would be vulnerabilities if exposed as production security controls:

- caller-trusted legacy identity parameters;
- process-local credential issuance and revocation;
- unprotected policy administration;
- application-only rather than gateway-enforced tool authorization;
- local-only audit integrity; and
- caller-supplied evidence provenance.

No authorization bypass was demonstrated through the new credential or policy-integrity paths. Forged credentials, revoked credentials, expired credentials, and mutated policies were blocked.

## Confirmed Bugs

No unresolved correctness bug was found in Phases 6-9.

A Windows-specific audit probe harness initially held a SQLite connection open during temporary-directory cleanup. The application store was not changed because the repository tests correctly close their handles; the final reproducible probe used explicit connection cleanup and passed. This was test-harness handling, not a product defect.

## Invariant Coverage

### Passed or directly exercised

- `INV-EVID-003`: evidence citations preserve source, revision, authority, lifecycle, and verification fields.
- `INV-EVID-004`: unverified provenance cannot produce `PASS`.
- `INV-EVID-005`: conflicting claims produce `REVIEW`.
- `INV-EVID-006`: non-current evidence produces `REVIEW`.
- `INV-AUTH-001`: unauthorized tool capability is blocked.
- `INV-AUTH-002`: role, target, and operation policy checks are enforced.
- `INV-AUTH-003`: out-of-scope target and operation are blocked.
- `INV-ID-001`: forged identity credential is rejected.
- `INV-ID-002`: revoked and expired identity credentials are rejected.
- `INV-GOV-001`: Praetor outage prevents governed tool execution.
- `INV-MCP-001`: the synthetic application route requires Praetor.
- `INV-AUD-001`: successful and blocked events are recorded.
- `INV-AUD-002`: durable audit events survive reopen.
- `INV-AUD-003`: tampering with durable audit details is detected.
- `INV-FAIL-003`: invalid questions, parameters, credentials, and policy state do not execute actions.
- `INV-NET-001` and `INV-NET-002`: offline provider boundary tests remain passing from Phase 4.

### Not implemented or not fully testable

- authenticated enterprise identity, key rotation, transport protection, and delegated authority;
- real MCP Gateway/server enforcement and tool-result validation;
- independently verified source objects, hashes, and supersession relationships;
- Cortex memory persistence, poisoning, retention, and cross-session isolation;
- graph/vector authority separation beyond the lexical synthetic retriever;
- externally anchored, encrypted, access-controlled, and replicated audit storage;
- operating-system network enforcement and data-loss prevention;
- real Foundry Local SDK integration and artifact verification;
- semantic judge, Agent K, hybrid fusion, human approval, and bounded agent-loop controls; and
- resource exhaustion, concurrency, crash recovery, and recovery-point testing.

## Threat Coverage

### Tested or partially exercised

- LLM prompt injection and indirect evidence instruction;
- RAG poisoning and mixed-trust retrieval;
- false corroboration from duplicate unverified claims;
- stale, draft, and superseded evidence handling;
- identity spoofing, revocation, and expiry;
- policy tampering and unknown policy/tool denial;
- Praetor outage and fail-closed behavior;
- durable audit tampering and reserved-field forgery;
- STRIDE-AI tampering, repudiation, elevation-of-privilege, and decision-integrity scenarios; and
- ATLAS technique areas related to prompt injection, RAG poisoning, agent context/tool poisoning, supply chain, and model manipulation at the synthetic boundary.

### Not tested or not implemented

- memory poisoning and cross-session leakage;
- graph poisoning and vector-ranking manipulation against real indexes;
- compromised MCP server responses or tool-description poisoning;
- external identity provider compromise and credential transport attacks;
- model artifact substitution and execution-provider compromise;
- exfiltration through actual network or tool paths;
- denial of service, bounded loops, concurrency, and storage recovery; and
- semantic evaluator manipulation or human approval failure.

### New threats and assumptions

Phase 9 introduces a process-local identity secret and token registry. Compromise of the process or its memory invalidates this synthetic trust root. This is accepted only because the evaluated profile is single-process and synthetic; it must not be promoted to a production identity claim.

## Technical Debt Decision

### Added or updated

- AUD10-001 through AUD10-006 are recorded in this audit.
- TD-009 remains mitigated but is explicitly blocked before real authorization or multi-user deployment.
- TD-008 remains mitigated but is explicitly blocked before production audit storage.
- TD-007 remains in progress because framework mappings without executable boundary tests are not considered coverage.

### Resolved for evaluated profile

- Phase 6 unresolved evidence conditions now downgrade to `REVIEW`.
- Phase 8 audit events persist and detect local tampering.
- Phase 9 forged, expired, revoked, and policy-mutated authorization paths fail closed.

### Accepted

The synthetic-only boundary, in-memory legacy compatibility path, process-local identity authority, local SQLite audit file, and caller-supplied evidence metadata are accepted for continued synthetic development only. Owner: Nova Aegis. Review: Phase 15 or before any real integration.

### Escalated

Connecting real organizational data, real MCP tools, or production inference before AUD10-001 through AUD10-005 are re-audited with their required controls is a release-blocking architecture violation.

## Architecture Decision

**Decision:** `CONTINUE` for synthetic Phase 11 work; `REFACTOR` required before real integrations.

The architecture remains decomposed into retrieval/evidence, Praetor assurance, identity context, policy evaluation, synthetic execution, provider boundary, and audit storage. The new identity and policy checks strengthen the authority path without merging responsibilities.

No Critical or High finding requires an immediate pause for the current profile. The next implementation phases must not add real tools or confidential data until the medium findings are converted into protected boundaries and tested at their actual integration points.

## Final Gate

- **Decision:** `CONTINUE` for synthetic-only Phase 11 work.
- **Human approval required:** Yes for any scope expansion to real organizational data, consequential tools, external identity, external network access, or production inference.
- **Follow-up audit:** Phase 15, or earlier for a real integration, model/runtime replacement, serious security event, or invariant failure.
- **Blocking conditions:** Before real integrations, resolve or explicitly re-audit AUD10-001 through AUD10-005.

> **Audit conclusion:** Phases 6-9 materially improved evidence assurance, adversarial coverage, durable audit detection, and synthetic identity/policy integrity. The system remains a governed local proof, not a production authorization platform. Continue narrowly under the synthetic boundary.
