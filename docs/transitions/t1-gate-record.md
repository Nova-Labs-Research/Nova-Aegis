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
| Candidate builder | Daniel Rosado Castro |
| AI build assistants | GPT-5.6, Sol, Luna, Terra; no authority or risk acceptance |
| Artifact reviewer | Daniel Rosado Castro |
| Reviewer independence | `NOT ESTABLISHED`; same human as accountable builder |
| G1 approver | Daniel Rosado Castro |
| Owner metadata authority | Daniel Rosado Castro |
| Independent human review | `NOT ESTABLISHED` |
| Research exception | `APPROVED` by project owner; inactive pending exact expiry |
| Environment | Single-human research laboratory |
| Exception scope | T1 non-production G1 candidate pilot only |
| Consequential authority | `NONE` |
| Separation-of-duty claim | `PROHIBITED` |
| Residual risk | `ACCEPTED` by project owner for bounded experiment |
| Research exception expiry | `UNASSIGNED` |
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

Daniel Rosado Castro explicitly accepted accountable builder, artifact reviewer, G1 approver, and owner-metadata authority. GPT-5.6, Sol, Luna, and Terra are recorded only as software build assistants; they cannot hold G1 authority, accountability, approval, independence, or risk acceptance.

Reviewer independence is explicitly not established because Daniel Rosado Castro is both accountable builder and artifact reviewer. This disclosure is auditable but does not satisfy the independent-review requirement. G1 remains `BLOCKED` until a different named human independently reviews the exact candidate artifact, or a separately audited governance decision changes that requirement before any build authorization.

## Single-human research exception - 2026-08-16

Project owner Daniel Rosado Castro approved a bounded exception acknowledging that independent human review is not available in the single-human research laboratory. The exception applies only to building and testing an uninstalled T1 non-production G1 candidate. It grants no G2 provisioning, G3 activation, production use, protected-authority claim, consequential authority, or separation-of-duty claim.

The residual risk of self-review is explicitly accepted for that bounded experiment. AI build assistants may provide analysis but do not supply human independence. The exception terminates immediately on candidate digest change, scope expansion, environment change, authority change, T1 audit, or its exact expiry date, whichever occurs first.

The exact expiry date was not supplied. Under the gate's fail-closed expiry rule, this exception is recorded but inactive and does not yet authorize G1 candidate building.