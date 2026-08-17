# T1 Gate Record

## Current decision

`BLOCK_IMPLEMENTATION`

This record is the current T1 authority state. Descriptive plans and completed technical tasks do not override it.

## G1 candidate build

| Required field | Value |
|---|---|
| Service owner | Daniel Rosado Castro; Project Owner / Independent Researcher; repository governance escalation; expires 2026-09-15 |
| Lifecycle/key owner | Daniel Rosado Castro; Project Owner / Independent Researcher; repository governance escalation; expires 2026-09-15 |
| Audit/replay owner | Daniel Rosado Castro; Project Owner / Independent Researcher; repository governance escalation; expires 2026-09-15 |
| Recovery/rollback owner | Daniel Rosado Castro; Project Owner / Independent Researcher; repository governance escalation; expires 2026-09-15 |
| Candidate builder | Daniel Rosado Castro |
| AI build assistants | GPT-5.6, Sol, Luna, Terra; no authority or risk acceptance |
| Builder self-reviewer | Daniel Rosado Castro |
| Independent human reviewer | Hecmaris M. Rosado Gonzalez; assignment accepted, review evidence pending |
| Relationship to builder | Family member; disclosed |
| Independence scope | Independent from artifact construction; no construction contribution recorded |
| Technical authority claimed | `NONE` beyond defined artifact-review scope |
| Reviewer independence | `ASSIGNED_NOT_YET_EVIDENCED` |
| G1 approver | Daniel Rosado Castro |
| Owner metadata authority | Daniel Rosado Castro |
| Independent human review | `NOT ESTABLISHED` |
| Research exception | `ACTIVE`; approved by project owner |
| Environment | Single-human research laboratory |
| Exception scope | T1 non-production G1 candidate pilot only |
| Consequential authority | `NONE` |
| Separation-of-duty claim | `PROHIBITED` |
| Residual risk | `ACCEPTED` by project owner for bounded experiment |
| Research exception effective date | `2026-08-16` |
| Research exception expiry | `2026-09-15` |
| G2/G3 applicability | `NONE` |
| Source commit | `d5fc17b82ceb125a14d8552d54b9d604d59ebde3` |
| Build/toolchain record | `docs/evidence/t1-g1-candidate-provenance.md`; SHA-256 `CD3092CB08237AA1FF459CE46DFD9A90378416E67D31EAC8B6967FA9D7E546F8` |
| Dependency lock/SBOM digest | `76EA6EE3BD137F081B3405384DA00A885F7394A65C3D8381CCE9BB419E60BDD7` |
| Candidate package digest | `CC4B6AF816F5DDFE1909F05DF4B1AA2649D4095F147028F17B2B10E7138BC126` |
| Focused test evidence | 11 focused tests passed; 207 complete tests passed |
| G1 approval expiry | `2026-09-15` |
| G1 build authorization | `COMPLETED` for uninstalled non-production protocol/core candidate |
| G1 artifact acceptance | `BLOCKED_INCOMPLETE` |
| G1 decision | `BUILD_COMPLETE`; no installation authority |

## G2 disabled provisioning

Current dependency status: `BLOCK_G2`. The G1 protocol/core candidate is evidence-bound but `BLOCKED_INCOMPLETE` and is not an accepted G2 artifact. The G1 single-human exception has no G2 applicability.

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

Daniel Rosado Castro performed builder self-review, which does not establish independence. Hecmaris M. Rosado Gonzalez is now assigned as the independent human artifact reviewer. The family relationship to the builder is disclosed; familial relationship does not automatically invalidate artifact-review independence, but it is a conflict-of-interest consideration that must remain visible.

Independence is bounded to non-participation in artifact construction and review of the exact evidence-bound candidate. Hecmaris claims no lifecycle, installation, security-architecture, G2/G3, production, or consequential technical authority beyond the defined review scope. Assignment alone is not completed review evidence. G1 artifact acceptance remains `BLOCKED_INCOMPLETE` until a dated review record binds the source commit, package digest, SBOM/provenance digests, test evidence, known incomplete surface, decision, limitations, and reviewer acknowledgement.

## Single-human research exception - 2026-08-16

Project owner Daniel Rosado Castro approved a bounded exception acknowledging that independent human review is not available in the single-human research laboratory. The exception applies only to building and testing an uninstalled T1 non-production G1 candidate. It grants no G2 provisioning, G3 activation, production use, protected-authority claim, consequential authority, or separation-of-duty claim.

The residual risk of self-review is explicitly accepted for that bounded experiment. AI build assistants may provide analysis but do not supply human independence. The exception terminates immediately on candidate digest change, scope expansion, environment change, authority change, T1 audit, or its exact expiry date, whichever occurs first.

The project owner assigned expiry `2026-09-15`. The exception is active only from `2026-08-16` through that date and has no G2 or G3 applicability. It authorized building and testing one uninstalled non-production candidate. That build is complete and evidence-bound, but artifact acceptance is blocked because the candidate lacks required service, IPC, replay, lifecycle, audit, and activation controls.

If Daniel Rosado Castro becomes unavailable, all owner and exception authority expires immediately and work stops; no software or AI assistant may replace the owner.