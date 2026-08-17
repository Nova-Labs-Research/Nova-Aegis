# T1 Implementation Gate

## Objective

Close T1 operational and authority prerequisites without allowing technical readiness, roadmap progression, tests, commits, or local signatures to manufacture authority.

**Current result:** `BLOCK_IMPLEMENTATION`.

No account, service, pipe ACL, key, credential, signing authority, or signer activation is authorized by this document.

## Gate model

T1 uses three distinct gates because a non-exportable key fingerprint and observed host configuration do not exist before provisioning.

| Gate | Permitted result | Explicitly prohibited |
|---|---|---|
| G1 - Candidate build | Build and package an uninstalled candidate; calculate digest and provenance | Host changes, service registration, key creation, signer activation |
| G2 - Disabled provisioning | Apply the exact approved host change and create the non-exportable pilot key while signing remains disabled | Accepting signing requests or trusting the new identity |
| G3 - Pilot activation | Enable the single allowlisted signing purpose after post-provision evidence is independently approved | Production use, additional purposes, consequential authority |

Each gate requires a new exact approval. Approval at one gate does not imply approval at the next.

## 1. Operational ownership

Assign named human individuals, not software identities or generic team labels, for:

- T1 service ownership;
- lifecycle and key-management ownership;
- audit and replay-state ownership; and
- recovery and rollback ownership.

For each owner, record name, organizational role, approved contact/escalation route, responsibility, effective date, expiry/review date, and replacement procedure. Software components may verify an authority record but may not assign, impersonate, replace, or infer an owner.

At least two distinct humans must participate in key creation, rotation, revocation, trust-root replacement, G2 approval, and G3 approval. The candidate builder must not be the sole artifact reviewer or sole installation approver.

An independent artifact reviewer must be distinct from the builder and must not have contributed to candidate construction. Personal or family relationships must be disclosed as potential conflicts, but independence is evaluated against construction participation, decision coercion, evidence access, and freedom to return `REJECT` or `REVIEW_REQUIRED`. Assignment does not equal completed review.

For a single-human research laboratory, the project owner may document a G1-only research exception when independent review is unavailable. The record must state that independence is not established, prohibit separation-of-duty claims, accept residual risk explicitly, bind the exception to one non-production candidate scope and environment, and set an exact expiry. Such an exception cannot apply to G2, G3, key lifecycle changes, production, or consequential authority.

**Gate:** Any unresolved, expired, conflicted, self-assigned, or unreviewable ownership produces `BLOCK_IMPLEMENTATION`.

## 2. Approval authority

Record named humans authorized to approve:

- G1 candidate artifact acceptance;
- G2 installation and service registration;
- virtual service identity and ACL configuration;
- Software KSP key creation parameters;
- G3 public fingerprint and signer activation;
- rotation, retirement, revocation, and trust-root replacement; and
- recovery, rollback, key destruction, and uninstall.

Each approval record must bind:

- gate and change ID;
- exact scope and explicit non-goals;
- candidate artifact digest and build provenance;
- deployment specification version/digest;
- host identity and OS build;
- service, pipe, provider, key name/version, purpose, and environment;
- threat-model and invariant versions;
- rollback procedure and rehearsal evidence;
- unresolved findings and accepted residual risk;
- approver identity, decision time, expiry, and revocation state; and
- for G3, observed public fingerprint and post-provision evidence bundle digest.

Approval cannot be inferred from roadmap state, issue assignment, test success, commit history, implementation readiness, prior gate approval, or access to administrator privileges.

## 3. Candidate artifact freeze

G1 defines the exact signer candidate without installing it:

- source commit and clean-tree status;
- deterministic build command and toolchain versions;
- dependency lock and software bill of materials;
- compiler/runtime target;
- packaged file list and per-file SHA-256 digests;
- top-level package SHA-256 digest;
- static analysis, dependency review, and focused test results; and
- independent reviewer decision.

The candidate package must contain no keys, credentials, host-specific secrets, mutable state, or production configuration. A source, dependency, toolchain, compiler option, generated file, or package-content change creates a new candidate and invalidates the prior digest approval unless an exact supersession record says otherwise.

Installation must calculate the package digest again and refuse mismatch before any host mutation.

**Gate:** No independently reviewed exact artifact digest means G2 remains blocked.

## 4. Exact installation change

Before G2, enumerate every host mutation in execution order, including:

- signer and runtime Windows service registration using virtual service accounts;
- service SID type, privileges, startup/recovery behavior, and executable path;
- protected binary, config, state, export, and audit paths and exact ACLs;
- Event Log source/channel registration and retention settings;
- named-pipe name, framing, limits, local-only behavior, and exact DACL;
- Microsoft Software KSP provider, machine key name, algorithm, usage, export policy, and key ACL;
- manifest, lifecycle/replay schema, migration state, and initial disabled purpose;
- firewall/network verification proving no listener or new egress path;
- expected service state and signer readiness state after each step; and
- every step requiring elevation.

Virtual service identities arise from service registration; no password-bearing local user should be created for this pilot. G2 must leave the allowlisted purpose disabled until G3.

The change plan must define precondition, command or installer action, expected result, captured evidence, failure handling, and compensating rollback for each mutation. Partial failure remains blocked and must not continue opportunistically.

## 5. Rollback evidence

Before G2, capture a non-authoritative rehearsal against an isolated test identity and disposable paths. The rehearsal must prove ordering and evidence preservation, not protected custody.

Record:

- pre-change services, paths, ACLs, Event Log sources, CNG key names, network listeners, and relevant configuration;
- tested stop/disable and service-registration removal;
- virtual service SID and ACL cleanup behavior;
- disposable key retirement/destruction behavior;
- lifecycle, replay, audit, public-key, manifest, and approval evidence intentionally preserved;
- partial-failure rollback from each installation stage;
- post-rollback absence of service, pipe, private-key use permission, network listener, trusted fallback, and enabled purpose;
- residual state intentionally retained and its owner/retention rule; and
- complete regression result after rollback.

Rollback evidence must include timestamps, host/test identity, artifact digest, plan version, observed before/after state, failures, deviations, reviewer, and evidence-bundle digest. “Uninstall succeeded” is insufficient.

After G2, repeat rollback validation against the real disabled pilot before G3. G3 remains blocked until that evidence is reviewed.

## 6. Threat-model re-evaluation

Before each gate, confirm:

- Software KSP remains the observed provider and TPM-backed claims remain prohibited;
- service identity compromise and local administrator compromise assumptions are explicit;
- named-pipe token authentication, ACL bypass, impersonation, remote access, and downgrade are tested;
- the signer cannot become a generic oracle or accept caller-selected purpose/key/provider/algorithm;
- request ID, nonce, stale/future time, duplicate delivery, ambiguous disconnect, and replay are fail closed;
- key substitution, provider substitution, version confusion, rotation, retirement, and revocation are covered;
- lifecycle/replay corruption, rollback, deletion, and unavailability disable signing;
- mandatory audit deletion, rollback, saturation, write failure, and unavailability disable signing;
- signer failure creates no local-key fallback or automatic replay;
- Reasoning cannot access the pipe directly, use the private key, modify signer policy, or manufacture owner/approval records;
- candidate build and installer supply-chain threats are reviewed; and
- T1 introduces no real data, network transport, consequential tool, production identity, or consequential authority.

## 7. Gate decisions

### G1 - Candidate build authorization

Requires assigned owners/approvers, approved build scope, source baseline, toolchain, dependency policy, and review method. G1 permits only building and testing the uninstalled candidate.

### G2 - Disabled provisioning authorization

Requires all G1 evidence, approved exact artifact digest, exact installation change, key-creation parameters, host identity, dry-run rollback evidence, threat-model review, and two distinct human approvals. G2 may create the disabled pilot key and host boundary solely to produce observed evidence.

### G3 - Pilot signing activation

Requires G2 completion plus independently reviewed service SID/ACL evidence, non-export proof, public fingerprint, manifest digest, audit/replay-state health, no-network proof, real-disabled-pilot rollback evidence, full regression, and two distinct human approvals bound to the post-provision evidence bundle.

If any required value is absent, ambiguous, stale, expired, inconsistent, revoked, or unsupported by evidence, return `BLOCK_IMPLEMENTATION` or `BLOCK_ACTIVATION` as applicable.

## 8. Post-G3 experiment

Only after G3:

- enable the single purpose `nova-aegis.evidence-anchor.v1`;
- submit only canonical benign synthetic anchor digests;
- verify runtime non-possession and private-key export refusal;
- execute all signer, identity, lifecycle, replay, IPC, audit, failure, and rollback adversarial tests;
- run the complete regression suite;
- update threat model and debt; and
- perform the mandatory T1 audit before T2.

## Claim boundary

Successful T1 may establish only:

> Under the tested Windows service, Software KSP, IPC, identity, lifecycle, audit, replay, and operational configuration, Nova Aegis can request and verify one allowlisted purpose-bound signature without direct access to or export of the private key.

It does not establish hardware/TPM custody, organizational independence, truth of signed claims, proof of external action, general authorization, production readiness, consequential-action safety, or unrestricted compromise resistance.

## Exit criterion

T1 is complete only when the narrow custody/signing property survives its adversarial tests and mandatory audit. A running signer is not completion evidence.

**One boundary. One claim. Evidence before authority.**