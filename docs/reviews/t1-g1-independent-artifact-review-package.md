# T1 G1 Independent Artifact Review Package

## Purpose

This package supports the bounded G1 artifact-review process for Nova Aegis. The reviewer is asked to review one candidate they did not construct.

This is not a security certification, installation approval, provisioning approval, production approval, or authority grant.

## 1. Reviewer

- **Reviewer:** Hecmaris M. Rosado Gonzalez
- **Relationship to accountable builder:** Family member; disclosed
- **Participation in artifact construction:** None recorded
- **Independence claim:** Independent from construction of this candidate only
- **Organizational independence:** Not established
- **Broader technical authority:** None claimed
- **Freedom of decision:** Reviewer may return `ACCEPT`, `REJECT`, or `NEEDS_CLARIFICATION`

The relationship disclosure remains part of the review evidence. Review assignment alone does not establish completed review.

## 2. Exact candidate

- **Project:** Nova Aegis
- **Transition:** T1 - Protected Identity and Key Custody
- **Gate:** G1 - Candidate Artifact Review
- **Candidate type:** Uninstalled, non-authoritative protocol/core candidate
- **Source baseline:** `d5fc17b82ceb125a14d8552d54b9d604d59ebde3`
- **Evidence commit:** `767567b78e556a4679a5f30cb8ab0900ac817928`
- **Candidate/package name:** `NovaAegis.ProtectedSigner-g1.zip`
- **Package SHA-256:** `CC4B6AF816F5DDFE1909F05DF4B1AA2649D4095F147028F17B2B10E7138BC126`
- **Recorded validation:** 11 focused tests and 207 complete tests passed

The package binary is retained locally under ignored `artifacts/` storage and is not installation authority. The reviewer must compare any package supplied for review against the complete SHA-256 above.

## 3. Evidence set

| Evidence | Path | SHA-256 |
|---|---|---|
| Candidate file-hash manifest | `docs/evidence/t1-g1-candidate-file-manifest.json` | `6E40B0AC1AA6DC1EB3BD3F579E1DC8854092E31A158A0998FA7A364BA1A9EC5C` |
| SBOM | `docs/evidence/t1-g1-sbom.json` | `76EA6EE3BD137F081B3405384DA00A885F7394A65C3D8381CCE9BB419E60BDD7` |
| Provenance | `docs/evidence/t1-g1-candidate-provenance.md` | `CD3092CB08237AA1FF459CE46DFD9A90378416E67D31EAC8B6967FA9D7E546F8` |
| Gate record | `docs/transitions/t1-gate-record.md` | `AA08C37403CBFD4A5192019653C66A522EF6FF69980785A880D1DAF72AE90C80` |
| G2 blocked plan | `docs/transitions/t1-g2-disabled-provisioning-plan.md` | `C9E227683216279FCDCB77E79ED362B6929F46E0FD8CF75498B4BCC01B634308` |

Published candidate files and hashes are listed in the machine-readable candidate manifest and provenance record. The reviewer should return `NEEDS_CLARIFICATION` if candidate identity or any evidence reference is unavailable, inconsistent, or mismatched.

## 4. Requested review

Please verify that:

- the candidate is unambiguously identified by complete package SHA-256;
- source baseline and evidence commit are recorded;
- the candidate file manifest, SBOM, and provenance are present;
- validation evidence records 11 focused and 207 complete passing tests;
- known limitations and blocked capabilities remain visible;
- no material claims exceed the evidence;
- nothing approves installation, provisioning, production, signing, G2, or G3;
- you did not participate in candidate construction; and
- your decision applies only to this exact package and evidence set.

You are not required to reproduce the build or cryptographic calculations unless you separately agree to do so. If you do not independently verify a technical property, do not attest that you did.

## 5. Known incomplete surface

The candidate does not implement or establish:

- Windows service hosting or service-SID startup validation;
- authenticated/ACL-restricted named-pipe enforcement;
- operational Software KSP key custody;
- request-ID and nonce replay persistence;
- lifecycle, revocation, or rotation persistence;
- mandatory Windows Event Log audit-before-success;
- manifest/public-fingerprint startup validation;
- ambiguity-safe query by request ID;
- an actual signing route or activation mode;
- installation, migration, rollback, or uninstall mechanics;
- hardware-backed or TPM-backed custody;
- organizational independence;
- production readiness;
- consequential authority; or
- G2/G3 authorization.

These limitations are expected for this protocol/core candidate. They also mean that review acceptance cannot make this artifact G2-eligible. A superseding complete candidate and new evidence/review are required before G2.

## 6. What this review does not approve

An `ACCEPT` decision does not authorize:

- installation or Windows service creation;
- service-identity or ACL provisioning;
- key creation or Software KSP provisioning;
- named-pipe activation;
- signing or purpose activation;
- G2 execution or G3 planning/activation;
- production use; or
- consequential tools/actions.

This review records a bounded opinion on whether the exact candidate package and evidence are sufficiently identified and limitations sufficiently disclosed. It does not override the authoritative gate record.

## 7. Reviewer decision

Select exactly one decision and complete the attestation.

### `ACCEPT`

I reviewed the exact package/evidence identified above. I confirm that I did not participate in constructing the candidate and that the materials identify the candidate and disclose the stated limitations. My acceptance applies only to this exact package SHA-256 and does not make the incomplete artifact G2-eligible.

### `REJECT`

I do not accept the candidate based on the materials presented. I will record a reason below.

### `NEEDS_CLARIFICATION`

I cannot decide because evidence is missing, unclear, inconsistent, or requires explanation. I will record the question or concern below.

## 8. Reviewer attestation - reviewer completes

- **Reviewer:** Hecmaris M. Rosado Gonzalez
- **Decision:** `[ACCEPT / REJECT / NEEDS_CLARIFICATION]`
- **Review date (UTC, YYYY-MM-DD):** `[REVIEWER ENTERS]`
- **Candidate package SHA-256:** `[REVIEWER COPIES COMPLETE HASH]`
- **Candidate file-manifest SHA-256:** `[REVIEWER COPIES COMPLETE HASH]`
- **SBOM SHA-256:** `[REVIEWER COPIES COMPLETE HASH]`
- **Provenance SHA-256:** `[REVIEWER COPIES COMPLETE HASH]`
- **Construction participation:** `[NONE / DESCRIBE]`
- **Materials actually reviewed:** `[REVIEWER LISTS]`
- **Technical checks independently reproduced, if any:** `[NONE / DESCRIBE]`
- **Reason, question, concern, or optional comments:** `[REVIEWER ENTERS]`

By completing this attestation, the reviewer acknowledges:

- the review is limited to the exact candidate and listed materials;
- Nova Aegis is not certified secure;
- installation, G2, G3, production, and consequential authority are not approved;
- organizational independence and broader technical authority are not claimed;
- the reviewer may reject or request clarification;
- no decision may be inferred beyond the stated scope; and
- any material candidate/evidence change requires a new review.

## 9. Governance handling

After completion:

1. preserve the original reviewer decision without reinterpretation;
2. hash the completed review record and bind it to the exact package/evidence hashes;
3. verify candidate and evidence identity again;
4. record missing/reproduced technical checks accurately;
5. re-evaluate all G1 requirements independently of the reviewer decision;
6. do not infer artifact completeness, G2 eligibility, installation, or activation;
7. require a new review for any material candidate/evidence change; and
8. retain `BLOCKED` on `NEEDS_CLARIFICATION`, mismatch, missing evidence, or reviewer construction participation.

> **The reviewer records a bounded artifact-review decision, not authority to deploy it.**
