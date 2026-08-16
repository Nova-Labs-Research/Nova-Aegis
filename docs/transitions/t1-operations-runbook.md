# T1 Protected Signer Operations Runbook

## Safety status

This is a dry-run operational procedure. Commands that create accounts, services, keys, ACLs, Event Log sources, or protected directories are intentionally omitted until the deployment specification is approved and an elevated human change is scheduled.

## Pre-install review

1. Assign every approval field in the deployment specification.
2. Review the signer binary source, dependencies, build provenance, and digest.
3. Confirm the host remains offline and no network listener is introduced.
4. Confirm `NovaAegisRuntime` and `NovaAegisSigner` service names and target paths do not conflict.
5. Review exact service SID, file DACL, key DACL, and named-pipe DACL output before applying it.
6. Approve the CNG provider, ECDSA profile, key name, purpose, environment, and public fingerprint procedure.
7. Verify Event Log ownership, retention, capacity, access, export, and failure behavior.
8. Approve key loss, revocation, rollback, uninstall, and incident contacts.

## Installation evidence to capture

- change ID and two approver identities;
- OS build and signer service binary digest;
- service configuration and service SIDs;
- protected directory and file ACLs;
- named-pipe ACL and local-only behavior;
- CNG provider, key name, algorithm, export policy, usage, and key ACL;
- public key and SHA-256 fingerprint;
- signer manifest digest;
- Event Log source/channel configuration;
- initial empty replay state; and
- proof that the Nova Aegis runtime cannot open or export the private key.

Do not capture private key material, secrets, complete sensitive payloads, or reusable administrator credentials.

## Startup checklist

1. Validate manifest schema and exact environment.
2. Validate service identity and binary digest.
3. Open the configured CNG key by exact provider/name/version.
4. Validate algorithm, usage, non-export policy, public fingerprint, and lifecycle state.
5. Open and integrity-check replay state.
6. Validate mandatory Event Log write and read-back metadata.
7. Create the named pipe with the reviewed protected DACL.
8. Enter ready state only after every check succeeds.

Any failed check keeps the service unavailable and emits an auditable refusal when possible.

## Pilot test sequence

1. Submit one canonical benign evidence-anchor digest through the runtime service identity.
2. Verify the signature with the pinned public identity outside the signer process.
3. Confirm request, terminal result, and audit correlation state agree.
4. Repeat every adversarial test in the T1 plan.
5. Restart signer and runtime services and verify identity/fingerprint continuity.
6. Exercise revocation and retirement in a disposable pilot identity.
7. Exercise audit loss, replay-state loss, pipe interruption, duplicate delivery, and signer unavailability.
8. Exercise full rollback to protected-signing refusal.
9. Run the complete Nova Aegis regression suite.
10. Perform the mandatory T1 audit before any T2 work.

## Incident response

On suspected key, signer, manifest, replay-state, audit, or service-account compromise:

1. Stop signing and preserve host/audit state.
2. Revoke the affected identity through the approved lifecycle path.
3. Disable runtime access to the pipe.
4. Do not retry unknown requests or trust unsigned reconstruction.
5. Export public verification and audit evidence to approved offline retention.
6. Determine affected request IDs, purposes, key versions, and time interval.
7. Require a separate trust-root replacement review before restoration.

## Recovery decision

Recovery may restore the same key only when custody, identity, state, and audit integrity remain verified. Otherwise create a new version under two-person approval and explicitly supersede the old trust root. Missing evidence produces refusal, not optimistic recovery.

## Exit criteria

T1 is not complete until:

- every required adversarial test passes;
- runtime private-key possession/export attempts fail;
- restart, rotation, revocation, audit loss, state loss, and rollback are exercised;
- full regression passes;
- assurance claims match the tested Software KSP boundary; and
- a dedicated audit approves or blocks progression to T2.