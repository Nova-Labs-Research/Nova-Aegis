# Nova Aegis Five-Phase Audit Policy

## Purpose

Nova Aegis performs a full audit after every fifth completed phase. The audit checks whether the implementation still preserves the problem statement, architecture, threat model, security invariants, and controlled authority boundaries.

The audit is a release gate, not a retrospective formality.

## Cadence

- Phase 1-4: complete the phase record and focused validation.
- Phase 5: complete the phase record, then run the full audit before starting Phase 6.
- Repeat at Phases 10, 15, 20, and every fifth phase thereafter.
- A serious security event, invariant failure, architecture boundary change, model/runtime replacement, or new high-impact tool may trigger an out-of-cycle audit.

## Audit Inputs

The auditor reviews:

- problem statement and design principles;
- high-level architecture and canonical flow;
- threat model;
- security invariants;
- technical debt ledger;
- source code and configuration;
- tests and coverage evidence;
- dependencies and model/runtime artifacts;
- audit records and failure behavior; and
- changes since the previous audit.

## Audit Questions

### Security and Vulnerability Review

- Can sensitive actions bypass Praetor or the MCP Gateway?
- Can retrieved content become trusted instruction?
- Can memory override current authoritative evidence?
- Can local failure trigger cloud or Internet fallback?
- Can identity or delegated authority be lost across components?
- Can malformed input, tool output, or debug paths bypass controls?
- Can logs expose unnecessary sensitive data or be silently modified?
- Have prompt injection, data leakage, denial of service, and supply-chain risks been tested?

### Correctness and Bug Review

- Do focused tests cover changed behavior and failure modes?
- Do invariant tests pass for the evaluated operating profile?
- Are PASS, REVIEW, and FAIL outcomes consistent with actual evidence and policy?
- Are contradictions and missing evidence visible rather than silently collapsed?
- Are failures deterministic, observable, and audited?

### Architecture Review

- Do components still have distinct responsibilities?
- Has any component gained authority through convenience or coupling?
- Is the inference provider still replaceable?
- Are storage, identity, policy, tool, and audit boundaries explicit?
- Is the current design more complex than the demonstrated requirement requires?
- Is a refactor needed before additional features are added?

### Technical Debt Review

- Which items are Critical or High severity?
- Which accepted items have exceeded their review date?
- Which workarounds are now permanent architecture?
- Which deferred tests are required before the next phase?
- Does any debt contradict a security invariant?

## Required Audit Outputs

Each audit produces `docs/audits/phase-XX-audit.md` containing:

- audit scope and phase range;
- commit or change range reviewed;
- environment and test commands used;
- findings ordered by severity;
- confirmed vulnerabilities;
- confirmed bugs;
- technical debt changes;
- architecture/refactor assessment;
- invariant and threat-model coverage;
- accepted risks with owner and review date;
- required remediation items; and
- final gate decision.

## Severity and Gate Decisions

- **Critical:** active security invariant violation, authorization bypass, material data leakage, or fail-open governance. Gate: **PAUSE**. Fix and re-audit.
- **High:** serious vulnerability, unsafe behavior, incorrect assurance, or boundary failure. Gate: **REFACTOR** or **PAUSE**, with explicit remediation before affected work continues.
- **Medium:** meaningful bug or debt with a bounded workaround. Gate: **CONTINUE** only with an owner, due date, and added test plan.
- **Low:** localized cleanup or documentation issue. Gate: **CONTINUE**, record in the ledger.

The final audit decision is one of:

- **CONTINUE:** no blocking findings; next phase may begin.
- **REFACTOR:** architecture or implementation must be corrected before dependent work continues.
- **PAUSE:** critical uncertainty or vulnerability prevents safe continuation.

No fifth phase is complete until the audit is documented and all Critical findings are resolved or formally blocked by an explicit human decision.

## Audit Evidence Standard

A claim that a control works must include observable evidence, such as a passing automated test, a reproducible command result, an inspectable audit record, or a documented review of the relevant code path. Architecture claims alone are insufficient.

## Audit Record Template

```markdown
# Nova Aegis Audit - Phase XX

## Scope
- Phases reviewed:
- Change range:
- Auditor:
- Date:

## Validation
- Commands:
- Results:
- Environment:

## Findings
| ID | Severity | Area | Finding | Required action | Owner | Due date |
|---|---|---|---|---|---|---|

## Invariant Coverage
- Passed:
- Failed:
- Not tested:

## Threat Coverage
- Tested:
- Not tested:
- New threats:

## Technical Debt Decision
- Added:
- Resolved:
- Accepted:
- Escalated:

## Architecture Decision
- Continue, refactor, or pause:
- Rationale:

## Final Gate
- Decision:
- Human approval required:
- Follow-up audit:
```
