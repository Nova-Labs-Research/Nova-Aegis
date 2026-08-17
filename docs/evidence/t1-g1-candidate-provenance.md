# T1 G1 Candidate Provenance

## Authority state

- Gate: G1 candidate build only
- Research exception: active through 2026-09-15
- Environment: single-human research laboratory
- Consequential authority: none
- G2/G3 applicability: none
- Installation/activation: blocked

## Source and toolchain

- Authorization baseline: `719ad0291c530df0d368412e1ce52a308a1dd725`
- Candidate source commit: `d5fc17b82ceb125a14d8552d54b9d604d59ebde3`
- OS: Windows 10.0.26200, `win-x64`
- .NET SDK: 10.0.102, commit `4452502459`
- MSBuild: 18.0.7+445250245
- Target: `net10.0-windows7.0`
- Build: deterministic Release, embedded debug information, warnings as errors
- NuGet package dependencies: none
- Installed workloads used: none

## Build commands

```powershell
dotnet build t1/signer/NovaAegis.ProtectedSigner/NovaAegis.ProtectedSigner.csproj --configuration Release --nologo
dotnet publish t1/signer/NovaAegis.ProtectedSigner/NovaAegis.ProtectedSigner.csproj --configuration Release --no-restore --output artifacts/t1-g1/publish --nologo
```

The package was created locally with `Compress-Archive`. Build outputs remain ignored under `artifacts/` and are not installation authority.

## Artifact hashes

Package: `NovaAegis.ProtectedSigner-g1.zip`

- Size: local evidence artifact
- SHA-256: `CC4B6AF816F5DDFE1909F05DF4B1AA2649D4095F147028F17B2B10E7138BC126`

Published files:

| File | Bytes | SHA-256 |
|---|---:|---|
| `NovaAegis.ProtectedSigner.deps.json` | 469 | `C0A581A51816D7A4A5F62AF8A3B9572D456441C4855B72B96BC15594742EA768` |
| `NovaAegis.ProtectedSigner.dll` | 40960 | `6F3E02E656239BDB771AA6A661D4C6A429F791351E12DE9E97E49F9AC98A45EA` |
| `NovaAegis.ProtectedSigner.exe` | 162816 | `CF1E3578D409D6CB12CDF8C342C45535ED559B4F9F350A801F5373B15716D86D` |
| `NovaAegis.ProtectedSigner.runtimeconfig.json` | 399 | `3E965CD7CFD553C2FF4E842D8D8019AAAE2DA0A21D92FF85A87573DD8D1B95C6` |

A second publish produced the same DLL SHA-256, confirming deterministic DLL output under this toolchain. The ZIP digest binds the exact local package but is not claimed reproducible because archive metadata may vary.

## Implemented candidate surface

- strict fixed-schema JSON parsing with duplicate/unknown-field refusal;
- exact protocol, purpose, environment, caller, signer identity, and key-version binding;
- bounded UTC request lifetime and strict payload digest/nonce validation;
- deterministic canonical envelope digest;
- existing-key-only CNG boundary using Microsoft Software KSP, ECDSA P-256, and fixed key name;
- no `CngKey.Create` path;
- no TCP/HTTP listener;
- default `BLOCK_IMPLEMENTATION` behavior; and
- non-authoritative candidate manifest.

## Known incomplete surface

This is not the exact G2 installation artifact and must not be accepted as one. It does not yet implement:

- Windows service hosting or service-SID startup validation;
- ACL-restricted named-pipe server;
- connected-client token authentication;
- request-ID and nonce replay persistence;
- lifecycle/revocation/rotation storage;
- mandatory Windows Event Log audit-before-success;
- ambiguity-safe query by request ID;
- manifest/public-fingerprint startup validation;
- actual signing route or activation mode; or
- install, migration, rollback, or uninstall mechanics.

These omissions keep the candidate incapable of signing and therefore safe for G1 protocol testing, but they block G1 artifact acceptance and all G2/G3 authority.

## Focused validation

`pytest -q tests/test_t1_signer_candidate.py` -> **11 passed**.

Covered: valid canonical envelope, purpose/environment/caller/identity/version substitution, unknown/missing/malformed/duplicate fields, expiry/lifetime, no activation mode, no key creation path, no network listener, and blocked candidate manifest.

Complete repository validation:

- `$env:PYTHONPATH='src'; pytest --tb=short -q` -> **207 passed**;
- `python -m compileall -q src tests` -> passed; and
- `git diff --check` -> passed.

## Decision

`G1_BUILD_COMPLETE`; `G1_ARTIFACT_ACCEPTANCE_BLOCKED_INCOMPLETE`; `G2_BLOCKED`; `G3_BLOCKED`.
