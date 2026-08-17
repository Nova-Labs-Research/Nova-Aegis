# T1 Deployment Specification

## Status and authority

**Specification complete; deployment not performed.**

This document fixes the T1 pilot defaults for review. It does not authorize account creation, service installation, key provisioning, ACL changes, Event Log registration, or protected signing. Those actions require an approved installation change and an elevated human operator.

## 1. Service identities and ownership

| Role | Windows identity | Purpose | Restrictions |
|---|---|---|---|
| Nova Aegis runtime | `NT SERVICE\NovaAegisRuntime` | Submit allowlisted anchor-signing requests | No private-key access; no signer state/audit write access; no service-control authority |
| Protected signer | `NT SERVICE\NovaAegisSigner` | Validate requests and invoke the protected CNG key | No interactive logon; no network requirement; no Nova Aegis policy/evidence mutation authority |
| Service control | Local `SYSTEM` and designated human administrators | Install, start, stop, and recover the service | Not accepted as application signing callers through the pipe |

Both application identities are Windows virtual service accounts. They require no managed password and receive service SIDs only after service installation. The signer and runtime must be separate services even if the runtime initially hosts only a benign test client.

**Accountable owner field:** `UNASSIGNED - human approval required before installation`.

## 2. Signer service and named-pipe boundary

### Service

- Service name: `NovaAegisSigner`
- Display name: `Nova Aegis T1 Protected Signer`
- Implementation target: minimal .NET Windows Worker Service
- Startup type during pilot: `Manual`
- Network dependency: none
- Recovery action: no automatic service restart during T1
- Executable directory: `C:\Program Files\Nova Aegis\Signer`
- Mutable state directory: `C:\ProgramData\NovaAegis\Signer`

The service binary must be version-pinned and hashed in the installation record. It must not load plugins, execute scripts, call models, access organizational data, or expose TCP/HTTP endpoints.

### Named pipe

- Pipe name: `NovaAegis.Signer.v1`
- Local path: `\\.\pipe\NovaAegis.Signer.v1`
- Remote clients: rejected
- Direction: duplex request/response
- Framing: unsigned 32-bit big-endian length followed by one UTF-8 JSON object
- Maximum request: 16 KiB
- Maximum response: 16 KiB
- Per-request deadline: 5 seconds
- Concurrent server instances: 4
- Automatic retry: prohibited

### Pipe DACL

Use a protected, non-inheriting DACL with only:

- `SYSTEM`: Full Control
- `NT SERVICE\NovaAegisSigner`: Full Control
- `NT SERVICE\NovaAegisRuntime`: Read/Write and Synchronize

`BUILTIN\Users`, `Everyone`, `ANONYMOUS LOGON`, and `NETWORK` receive no allow entry. Administrators control the service through the Service Control Manager, not by receiving application-call permission on the pipe.

The signer must impersonate each connected client long enough to inspect the operating-system token and require the exact `NovaAegisRuntime` service SID. Envelope `caller_id` is additional bound metadata, never authentication.

## 3. Cryptography and key lifecycle

### Pilot key profile

- Provider: `Microsoft Software Key Storage Provider`
- Algorithm: ECDSA P-256
- Hash: SHA-256
- Signature encoding: IEEE P1363 fixed-width `r || s`, base64url without padding
- Key name: `NovaAegis.T1.AnchorSigner.v1`
- Key scope: machine key owned for use by `NovaAegisSigner`
- Export policy: private-key export prohibited
- Usage: signing only
- Allowlisted purpose: `nova-aegis.evidence-anchor.v1`
- Environment: `t1-pilot-offline`
- Production use: prohibited

The runtime verifier pins provider, algorithm, signing identity `nova-aegis-t1-anchor-signer`, key version `v1`, and the exported public-key fingerprint. Caller-selected provider, key, algorithm, or purpose is refused.

### Canonical envelope

The service signs SHA-256 over UTF-8 strict canonical JSON containing:

- protocol `nova-aegis-protected-signer`;
- schema version `1`;
- purpose `nova-aegis.evidence-anchor.v1`;
- environment `t1-pilot-offline`;
- boundary ID;
- caller ID `nova-aegis-runtime`;
- request ID (UUIDv4);
- nonce (at least 128 random bits, base64url);
- issued-at and expires-at UTC timestamps;
- policy version;
- invariant version;
- payload digest (`sha256:<lowercase hex>`);
- signer identity;
- key version `v1`; and
- audit correlation ID (UUIDv4).

Strict canonical JSON rejects duplicate object keys, unsupported fields, non-finite numbers, non-UTF-8 input, and non-normalized schema values. Domain and purpose fields are part of the signed envelope.

### Lifecycle authority

- Creation: two named human reviewers approve the exact provider, key name, algorithm, service SID, environment, and public fingerprint.
- Rotation: create `vN+1`, publish and approve its fingerprint, enable it for new signing, then retire `vN`; never overwrite a key version.
- Retirement: blocks new signing but preserves public verification metadata.
- Revocation: immediately blocks signing and marks verification state revoked from an explicit effective time.
- Restart: requires the configured key version and fingerprint to match; missing or substituted keys produce refusal.
- Loss: no trusted local fallback and no silent regeneration. Recovery requires a new version and trust-root replacement review.
- Backup: no private-key backup in T1. Loss is handled as revocation and replacement because the Software KSP pilot is not a production continuity control.

## 4. Lifecycle, replay, and audit storage

### Filesystem layout

```text
C:\ProgramData\NovaAegis\Signer\
  config\signer-manifest.json
  state\signer-state.db
  export\public-identity.json
```

- `config` and `state`: `SYSTEM` and `NovaAegisSigner` Full Control; designated administrators Read; runtime no access.
- `export\public-identity.json`: runtime Read; signer and `SYSTEM` write; no other application identity access.
- All DACLs are protected and non-inheriting.

`signer-manifest.json` binds service version, environment, allowed purpose, signer identity, provider, algorithm, key version, public fingerprint, lifecycle state, policy version, invariant version, and audit target. Startup refuses mismatches.

`signer-state.db` uses SQLite WAL mode with full synchronous commits and stores request ID, nonce digest, envelope digest, observed caller SID, terminal result, key version, correlation ID, and signer-observed time. A request ID or nonce may receive only one terminal result. Database unavailability, corruption, migration mismatch, or write failure produces `LIFECYCLE_UNAVAILABLE` and no signature.

### Audit target

- Windows Event Log channel/source: `Nova Aegis Protected Signer`
- Events: startup validation, shutdown, accepted request, every refusal, duplicate request, lifecycle change, key-version mismatch, audit failure, and recovery action
- Sensitive payloads and private material: never logged
- Required fields: correlation ID, request ID, caller SID, purpose, environment, envelope digest, result code, signer identity, key version, service version, and observed UTC time

The service must write a mandatory audit event before returning `SIGNED`. If Event Log registration, write, or required field validation fails, the terminal result is `AUDIT_UNAVAILABLE`; no signature is returned. Audit failure never falls back to a local text log.

## 5. Recovery, rollback, and uninstall

### Failure behavior

| Failure | Required behavior |
|---|---|
| Signer unavailable | Runtime returns `SIGNER_UNAVAILABLE`; no local signing fallback |
| Pipe disconnect before terminal response | Outcome remains unknown; do not retry automatically; query by request ID after service recovery |
| Replay-state unavailable/corrupt | `LIFECYCLE_UNAVAILABLE`; signing disabled |
| Audit unavailable | `AUDIT_UNAVAILABLE`; no signature returned |
| Config/key/fingerprint mismatch | `IDENTITY_MISMATCH` or `KEY_VERSION_MISMATCH`; startup or signing refused |
| Revoked/retired key | New signing refused; historical verification follows recorded lifecycle state |
| Key loss | Service remains unavailable until separately approved replacement version exists |

### Rollback to synthetic-only operation

1. Disable the T1 signing purpose in the reviewed manifest.
2. Stop and disable `NovaAegisSigner`.
3. Remove runtime access from the named-pipe and public-identity paths.
4. Preserve Event Log records, replay state, manifest, public key, fingerprint, and lifecycle evidence.
5. Mark the pilot key retired or revoked according to incident context.
6. Configure Nova Aegis to refuse protected-signing requests; do not trust a synthetic replacement.
7. Run the regression suite and record the rollback audit decision.

### Uninstall

Uninstall is a separate approved operation. It removes service registration and binaries only after preserving required audit and public verification evidence. Private-key deletion requires explicit two-person approval and a recorded key-destruction event. Uninstall never exports the key or replays queued requests.

## Authority and gate records

The authoritative prerequisites and current decisions are maintained in:

- `docs/transitions/t1-implementation-gate.md`; and
- `docs/transitions/t1-gate-record.md`.

The key fingerprint is necessarily observed after G2 creates the non-exportable disabled pilot key. G2 approval binds the exact key-creation parameters; G3 approval binds the observed fingerprint and complete post-provision evidence bundle. The signer purpose remains disabled between those gates.

Implementation remains blocked while any approval field is unassigned.