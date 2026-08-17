# T1 - Protected Signing Identity and Key Custody Plan

## Gate decision

**Decision:** `APPROVE_PLANNING`; `BLOCK_IMPLEMENTATION` until the Windows service identity, local IPC ACL, key lifecycle authority, audit target, recovery procedure, and rollback procedure are configured and reviewed.

T1 introduces no production identity, organizational authority, external action, real data, worker, network transport, or consequential tool.

## Verified host capability

On 2026-08-16, read-only inspection found:

- Microsoft Software, Platform, Passport, and Smart Card key-storage providers are installed;
- Windows TPM CIM state is unavailable or not exposed on this host; and
- TPM-backed or hardware-backed custody therefore cannot be claimed or required for this pilot.

The initial pilot should use a non-exportable key in Microsoft Software Key Storage Provider under a distinct least-privilege Windows service identity. This establishes only OS-enforced separation from the Nova Aegis runtime under tested conditions. A later hardware-backed upgrade requires a ready TPM or approved hardware key provider and a separate migration audit.

## Synthetic assumption replaced

Current synthetic key providers place signing secrets in the Nova Aegis process. T1 replaces one instance of that assumption with a signer service whose private key is non-exportable and inaccessible to the Nova Aegis runtime identity.

## Component boundary

```text
Nova Aegis runtime identity
        |
        | ACL-restricted named pipe
        | canonical purpose-bound request
        v
Protected signer Windows service identity
        |
        | NCrypt/CNG non-exportable key handle
        v
Microsoft Software Key Storage Provider
```

The signer is not a generic cryptographic oracle. It signs only supported Nova Aegis envelope types after authenticating the local caller and validating the complete request.

## Signer request contract

Every signing request must contain:

- protocol and schema version;
- signing purpose from a fixed allowlist;
- environment and boundary ID;
- caller service identity;
- request ID and nonce;
- issued-at and expires-at values;
- policy and invariant version;
- canonical payload digest;
- required signing identity and key version; and
- audit correlation ID.

The canonical signed envelope must include every field above. Domain separation must bind a fixed Nova Aegis protocol name and signing purpose so a signature valid for one purpose cannot be reused for another.

Unsupported fields, non-finite JSON, duplicate keys, malformed encoding, stale or future requests, repeated request IDs, unknown callers, identity mismatch, key-version mismatch, revoked state, unavailable audit, or unavailable lifecycle state must produce typed refusal.

## Signer response contract

Success returns only:

- result `SIGNED`;
- signing identity;
- key version;
- signature algorithm;
- canonical envelope digest;
- signature;
- signer-observed timestamp; and
- audit correlation ID.

Failure returns one explicit code such as `CALLER_UNAUTHORIZED`, `PURPOSE_REFUSED`, `SCHEMA_INVALID`, `REQUEST_REPLAYED`, `REQUEST_EXPIRED`, `IDENTITY_MISMATCH`, `KEY_VERSION_MISMATCH`, `IDENTITY_REVOKED`, `AUDIT_UNAVAILABLE`, `LIFECYCLE_UNAVAILABLE`, or `SIGNER_UNAVAILABLE`.

The response never returns a private key, key blob, export handle, unrestricted signing primitive, or production authorization.

## Identity and key lifecycle

- The service identity owns key-use permission; the Nova Aegis runtime identity has none.
- Key creation sets non-exportable policy and fixed algorithm/size requirements.
- The verifier pins signing identity, provider, algorithm, and accepted key versions.
- Rotation introduces a successor version through an exactly bound two-person lifecycle decision.
- Retirement refuses new signing while preserving verification of retained evidence.
- Revocation fails closed immediately for new signing and marks historical verification state explicitly.
- Restart reloads the configured identity and key version; it never creates a replacement silently.
- Key loss produces `SIGNER_UNAVAILABLE`; no local fallback key is trusted.

## Local IPC contract

- Use Windows named pipes with an explicit security descriptor allowing only the Nova Aegis runtime service identity and designated administrators.
- The signer must obtain and validate the connected client process token; a caller-supplied identity string is insufficient.
- Reject remote named-pipe clients and network transport during T1.
- Apply bounded message sizes, strict framing, one canonical request per frame, deadlines, and connection limits.
- Do not retry signing automatically after disconnect or ambiguous response.
- Persist request ID and terminal outcome before returning success so duplicate delivery cannot create ambiguous state.

## Recovery and rollback

Rollback disables the signing purpose, revokes caller access to the pipe, preserves audit and public verification material, and returns the system to synthetic-only operation. It does not export the key or convert protected identity into a local fallback.

Recovery from service, key, lifecycle, or audit failure is refusal-first. Key restoration or trust-root replacement requires a new human-reviewed procedure and cannot silently replay queued requests.

## Required adversarial tests

- valid protected signature and independent verification;
- local substitute key refusal;
- private-key export refusal;
- malformed signature and payload mutation refusal;
- wrong caller token, identity, provider, algorithm, and key version refusal;
- revoked, retired, missing, and unavailable identity behavior;
- deterministic rotation and restart identity continuity;
- purpose substitution and cross-environment replay refusal;
- nonce/request-ID replay and incompatible-state refusal;
- stale, future, oversized, malformed, and duplicate-key requests;
- named-pipe ACL bypass, remote client, impersonation, downgrade, interruption, and duplicate delivery;
- unavailable signer, lifecycle store, and audit store fail closed; and
- rollback leaves no trusted local substitute path.

## Claim boundary

Passing T1 may establish only that the tested signing operation used a non-exportable key outside direct possession of the Nova Aegis runtime identity under the tested Windows service, CNG provider, ACL, lifecycle, and audit configuration.

It does not establish hardware-backed custody, administrator-compromise resistance, organizational independence, protected evidence retention, production authority, external-action truth, or consequential-action safety.

## Implementation prerequisites

- named Windows service identity and accountable owner;
- reviewed service binary and installation mechanism;
- explicit named-pipe security descriptor;
- selected CNG algorithm and provider configuration;
- key creation, rotation, revocation, retirement, backup, and loss procedures;
- protected lifecycle and replay-state storage design;
- signer audit destination and failure behavior;
- uninstall/rollback procedure; and
- dedicated pre-T2 audit criteria.

The concrete defaults and operational requirements are defined in:

- `docs/transitions/t1-deployment-specification.md`; and
- `docs/transitions/t1-operations-runbook.md`;
- `docs/transitions/t1-implementation-gate.md`; and
- `docs/transitions/t1-gate-record.md`.

The specification leaves accountable owners, approvers, change ID, reviewed binary digest, public-key fingerprint, and rollback evidence explicitly unassigned. T1 implementation remains blocked until those fields are assigned and reviewed.