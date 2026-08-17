# T1 Gate Record

## Current decision

`BLOCK_IMPLEMENTATION`

This record is the current T1 authority state. Descriptive plans and completed technical tasks do not override it.

## G1 candidate build

| Required field | Value |
|---|---|
| Service owner | Daniel Rosado Castro; role/contact/expiry pending |
| Lifecycle/key owner | Daniel Rosado Castro; role/contact/expiry pending |
| Audit/replay owner | Daniel Rosado Castro; role/contact/expiry pending |
| Recovery/rollback owner | Daniel Rosado Castro; role/contact/expiry pending |
| Candidate builder | `UNASSIGNED`; GPT 5.6, Sol, Luna, and Terra proposed as build assistants only |
| Independent artifact reviewer | `UNASSIGNED` |
| G1 approver | `UNASSIGNED` |
| Source commit | `UNASSIGNED` |
| Build/toolchain record | `UNASSIGNED` |
| Dependency lock/SBOM digest | `UNASSIGNED` |
| Candidate package digest | `UNASSIGNED` |
| Focused test evidence digest | `UNASSIGNED` |
| G1 approval expiry | `UNASSIGNED` |
| G1 decision | `BLOCKED` |

## G2 disabled provisioning

| Required field | Value |
|---|---|
| Installation change ID | `UNASSIGNED` |
| Target host identity/OS build | `UNASSIGNED` |
| Deployment specification digest | `UNASSIGNED` |
| Approved candidate package digest | `UNASSIGNED` |
| Exact host-change plan digest | `UNASSIGNED` |
| Key-creation parameter digest | `UNASSIGNED` |
| Dry-run rollback evidence digest | `UNASSIGNED` |
| Threat-model review digest | `UNASSIGNED` |
| Primary G2 approver | `UNASSIGNED` |
| Independent G2 approver | `UNASSIGNED` |
| G2 approval expiry | `UNASSIGNED` |
| G2 decision | `BLOCKED` |

## G3 pilot activation

| Required field | Value |
|---|---|
| Observed service SID/ACL evidence digest | `UNASSIGNED` |
| Observed public-key fingerprint | `UNASSIGNED` |
| Private-key non-export evidence digest | `UNASSIGNED` |
| Signer manifest digest | `UNASSIGNED` |
| Audit/replay health evidence digest | `UNASSIGNED` |
| No-network evidence digest | `UNASSIGNED` |
| Disabled-pilot rollback evidence digest | `UNASSIGNED` |
| Full regression evidence digest | `UNASSIGNED` |
| Post-provision evidence bundle digest | `UNASSIGNED` |
| Primary G3 approver | `UNASSIGNED` |
| Independent G3 approver | `UNASSIGNED` |
| G3 approval expiry | `UNASSIGNED` |
| G3 decision | `BLOCKED` |

## Refusal rule

Any `UNASSIGNED`, stale, expired, revoked, ambiguous, conflicting, or digest-mismatched required field keeps the relevant gate blocked. No software component may populate human identity, approval, or risk-acceptance fields on behalf of a person.

## Assignment note - 2026-08-16

Daniel Rosado Castro explicitly accepted the four operational ownership categories above. Organizational role, escalation contact, effective/expiry dates, and replacement procedure were not supplied and remain required.

GPT 5.6, Sol, Luna, and Terra were nominated for candidate-building work. They are recorded only as software build assistants. A named human accountable builder must review and accept their output and provenance; software cannot hold G1 authority, accountability, approval, or risk acceptance.