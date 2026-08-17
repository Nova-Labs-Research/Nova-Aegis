# T1 G2 - Disabled Provisioning Plan

## Objective

Provision and validate the approved T1 Windows trust boundary in a disabled, non-authoritative state.

G2 may eventually materialize the approved Windows service identities, non-exportable Software KSP key, authenticated local named-pipe boundary, lifecycle/replay/audit persistence, and exact host configuration. G2 must never activate purpose-bound signing authority.

> **Provisioning infrastructure is not authorization to use it.**

## Current gate decision

**`BLOCK_G2`**

G2 is currently blocked for two independent reasons:

1. G1 artifact acceptance is `BLOCKED_INCOMPLETE`. The current protocol/core candidate lacks Windows service hosting, named-pipe token authentication, replay/lifecycle persistence, mandatory audit, disabled-state enforcement, and an activation-safe signing route.
2. The G1 single-human research exception has `G2/G3 applicability: NONE`. Required G2 approvers and authority evidence are unassigned.

This document is an acceptance plan only. It creates no service, identity, key, directory, ACL, Event Log source, database, pipe, or authority.

## Refinements to the provisioning model

### Candidate replacement before G2

The current G1 package cannot be provisioned under G2. A new candidate revision must implement the complete disabled host boundary, pass focused tests, receive a new source/package/SBOM/provenance evidence bundle, and supersede the current candidate explicitly. Prior digest approval never transfers to a new build.

### Key creation and activation separation

G2 may create a non-exportable pilot key only after exact key-creation parameters are approved. The signer purpose must remain disabled in a separately verified manifest before, during, and after key creation. Presence of the key, service, public fingerprint, or completed installation is never activation evidence.

### Rollback versus destruction

Rollback disables use, removes access, stops services, and preserves required evidence. Private-key destruction is a separate, potentially irreversible lifecycle action requiring its own exact approval. A rollback test should normally retain or revoke the disabled disposable key rather than silently destroy it.

### Host reboot scope

A host reboot is a separately approved disruptive test. G2 must first prove service-restart behavior. Reboot testing occurs only when a pre-change recovery point, operator availability, evidence capture, and rollback path are approved.

## Entry conditions

Before any host modification:

- G1 artifact acceptance is explicitly `ACCEPTED_FOR_G2` for the exact complete candidate;
- source baseline, package and file SHA-256 digests, SBOM, provenance, and focused tests match;
- the G1 exception remains in scope only for its historical G1 evidence and is not treated as G2 approval;
- all named-human G2 ownership and approval fields are assigned and unexpired;
- G2 approval binds the exact host, candidate, installation plan, key parameters, threat model, and rollback rehearsal;
- the pre-change host baseline and evidence-bundle format are defined;
- production hard-disable is verified; and
- G3 remains explicitly blocked.

Any absent, stale, expired, ambiguous, conflicting, revoked, or digest-mismatched prerequisite produces `BLOCK_G2`.

## 1. Host baseline evidence

Collect only T1-relevant evidence:

- Windows edition, build, machine identity reference, and boot time;
- existing `NovaAegisRuntime` and `NovaAegisSigner` service state;
- relevant service SIDs and local identities;
- intended binary/config/state/export paths and current existence;
- parent and target ACLs in SDDL plus resolved identities;
- named-pipe/service-name collisions;
- Microsoft Software KSP availability and observed provider properties;
- existing T1 key-name collision state without exposing private material;
- Event Log source/channel collision and retention state;
- relevant listeners/firewall state sufficient to prove no T1 network surface; and
- current repository, artifact, plan, threat-model, and gate digests.

TPM readiness remains unavailable/not exposed on the current host. Hardware-backed and TPM-backed claims remain prohibited.

## 2. Separate Windows service identities

- Register only the approved `NovaAegisRuntime` and `NovaAegisSigner` services using virtual service accounts.
- Enable service SID isolation and grant only required logon/service rights.
- Do not create password-bearing local users.
- Remove unnecessary privileges and verify neither identity is an administrator.
- Restrict signer binary/state/key access to the approved service SID and `SYSTEM` as specified.
- Verify Reasoning and interactive user contexts cannot authenticate as the signer through the application boundary.
- Record service configuration, effective token privileges, SIDs, and ACL evidence.

Separate service identities establish tested OS separation only, not organizational independence.

## 3. Software KSP key custody

- Create only `NovaAegis.T1.AnchorSigner.v1` in Microsoft Software Key Storage Provider.
- Use machine-scoped ECDSA P-256 signing-only configuration with private export prohibited.
- Grant private-key use only to `NT SERVICE\NovaAegisSigner` and required system administration paths.
- Record provider, key name/version, algorithm, usage, export policy, public key, and fingerprint.
- Verify runtime, Reasoning, interactive non-administrator, and unauthorized service identities cannot sign or open private material.
- Attempt every supported private export path and record refusal.
- Initialize lifecycle state as `PROVISIONED_DISABLED`; never `ACTIVE`.
- Preserve explicit version, retirement, revocation, and replacement state.

Do not claim hardware backing, TPM identity, independent organizational authority, production custody, or administrator-compromise resistance.

## 4. Authenticated named-pipe boundary

- Expose only `\\.\pipe\NovaAegis.Signer.v1` with the exact protected DACL.
- Reject remote clients and verify no TCP/HTTP listener exists.
- Impersonate the connected client and validate the exact runtime service SID; envelope identity is not authentication.
- Enforce 32-bit big-endian framing, one request per frame, 16 KiB bounds, deadlines, and connection limits.
- Reject malformed/partial/oversized frames, unsupported schema and fields, unknown purpose, environment/boundary mismatch, caller mismatch, key-version mismatch, and generic-signing requests.
- Record caller SID, request ID, correlation ID, result, and refusal code without sensitive payload duplication.

The pipe must expose no arbitrary hash/sign primitive and no lifecycle or activation mutation operation to the runtime caller.

## 5. Lifecycle, replay, and audit state

- Create the approved manifest, lifecycle/replay database, public-identity export, and Event Log source/channel.
- Apply protected non-inheriting ACLs and verify unauthorized read/write/delete behavior.
- Use transactional request-ID and nonce uniqueness with durable terminal outcomes before response.
- Validate schema, key version, public fingerprint, lifecycle state, service version, purpose, and environment at startup.
- Refuse on missing, malformed, corrupt, stale, rolled-back, conflicting, unavailable, or migration-mismatched required state.
- Verify duplicate request IDs and nonces remain refused after service restart.
- Record state/audit corruption, deletion, saturation, and write-failure behavior.

Local state is durable under tested conditions but not immutable or independently retained.

## 6. Disabled signing invariant

G2's central invariant is:

```text
G2_STATE = PROVISIONED_DISABLED
G3_ACTIVATION = BLOCKED
ACCEPTED_SIGNATURES = 0
```

- The manifest contains no active purpose authorization.
- Startup, service restart, host restart, key presence, artifact presence, successful installation, G1 evidence, and G2 approval cannot activate signing.
- Valid-looking requests receive `PURPOSE_DISABLED` before any private-key operation.
- Configuration mutation, stale approval, replaced manifest, lifecycle rollback, or missing G3 evidence causes refusal.
- The public verifier must not accept a T1 protected-signature claim because G3 has issued no accepted signing identity state.

The private key may exist, but the governed Nova Aegis interface must produce no accepted T1 signature during G2.

## 7. Adversarial test matrix

At minimum test:

- unauthorized, interactive, substituted, remote, and malformed named-pipe callers;
- service SID, binary, provider, key, version, purpose, environment, and boundary substitution;
- malformed, partial, duplicate-key, oversized, unsupported, stale, and future frames;
- direct private-key operation and every supported export attempt from unauthorized identities;
- request-ID/nonce replay before and after service restart;
- lifecycle, replay, manifest, public-identity, and audit corruption/deletion/rollback/unavailability;
- Event Log saturation/write refusal;
- missing required files/directories and ACL mutation;
- service restart and separately approved host restart;
- signing while disabled and activation through config, key presence, approval metadata, or artifact substitution;
- stale/expired G2 approval and artifact digest mismatch; and
- partial installation failure at each host-mutation step.

Every authority ambiguity fails closed.

## 8. Compromised-caller probe

Assume the runtime caller is malicious and verify it cannot:

- obtain/export private key material or invoke private operations outside the allowlisted protocol;
- impersonate the signer service or mutate its binary/config/state/audit/key ACLs;
- alter lifecycle authority or erase replay state to regain request validity;
- turn the pipe into a generic signing oracle;
- activate G3 or manufacture/modify human approval evidence; or
- produce an accepted T1 signature while disabled.

This is a bounded caller-compromise precursor, not a full Reasoning- or host-compromise experiment.

## 9. Recovery and rollback exercise

- Capture the exact pre-change baseline and evidence-bundle digest.
- Exercise rollback from every provisioning stage, including partial failure.
- Stop/disable services, remove runtime pipe/public-identity access, and restore documented host configuration.
- Preserve manifest, public key/fingerprint, lifecycle/replay/audit records, approvals, artifact evidence, and incident evidence as required.
- Treat key retirement/revocation/destruction as explicit lifecycle decisions; never silently delete the key.
- Verify post-rollback absence of active service/pipe access, trusted local fallback, network surface, and enabled purpose.
- Record intentionally retained service registration, files, logs, public identity, and disabled/revoked key state.
- Run the complete regression after rollback.

Rollback success requires before/after observations and reviewer acceptance, not an uninstall exit code.

## 10. Validation evidence

Record:

- focused G2 and complete Nova Aegis test results;
- .NET/Python compilation and repository integrity results;
- exact source, package, file, SBOM, provenance, plan, host-baseline, and post-provision hashes;
- effective service identities, privileges, ACLs, key properties, pipe behavior, state health, audit behavior, and network absence;
- every refusal result and unresolved finding; and
- rollback evidence and intentionally retained state.

Passing tests grant no authority.

## 11. Mandatory G2 audit

Before any G3 planning:

- verify each G2 claim against observed host evidence;
- review service isolation, Software KSP custody, IPC token authentication, state durability, audit-before-success, and disabled-state enforcement;
- identify remaining synthetic assumptions and new host attack surfaces;
- review compromised-caller and rollback evidence;
- update threat model, invariants, and debt; and
- explicitly decide only whether evidence permits G3 **planning**.

G2 completion never authorizes G3 activation.

## Claim boundary

Successful G2 may establish only:

> Under the tested Windows host configuration, the approved T1 service identities, non-exportable Software KSP pilot key, authenticated local IPC boundary, and lifecycle/replay/audit state can be provisioned while T1 signing authority remains disabled and inaccessible through the governed Nova Aegis interface.

It does not establish hardware/TPM custody, organizational independence, independent human separation, immutable retention, network security, production readiness, consequential safety, truth of future claims, safe activated signing, or G3 authorization.

## Exit criteria

G2 is complete only when the approved complete candidate is materially provisioned, host enforcement and disabled signing survive adversarial testing, rollback is exercised, evidence is recorded, complete regression passes, and the mandatory G2 audit accepts the bounded claim.

Until then:

```text
G2 = INCOMPLETE
G3 = BLOCKED
```

> **Materialize the boundary without materializing authority.**