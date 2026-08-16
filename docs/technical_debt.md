# Nova Aegis Technical Debt Ledger

## Purpose

This ledger records implementation debt, discovered defects, broken behavior, temporary decisions, and architectural questions. It prevents temporary MVP choices from becoming invisible permanent constraints.

Every phase must update this document before it is considered complete.

## Phase Record

Each phase record must answer:

- What changed?
- What broke or was discovered?
- What is the root cause?
- What fix was applied or proposed?
- Why was that fix chosen?
- What risk remains?
- Is refactoring required?
- Which threat, invariant, or architecture section is related?
- Which tests were added?
- Which tests are still missing?

## Status Values

- **Open:** known debt or defect remains.
- **In progress:** an owned fix is being implemented.
- **Mitigated:** risk is reduced, but the underlying debt remains.
- **Resolved:** the cause is fixed and validated.
- **Accepted:** consciously retained with rationale, owner, and review date.
- **Blocked:** cannot be resolved until a named dependency or decision is available.

## Severity Values

- **Critical:** threatens confidentiality, authorization, governance, or a security invariant.
- **High:** can cause unsafe behavior, material data exposure, incorrect assurance, or architectural boundary failure.
- **Medium:** meaningful defect or maintainability risk without immediate critical impact.
- **Low:** localized cleanup or minor usability/clarity issue.

## Current Phase Records

### TD-T1 - Protected signing pilot lacks configured enforcement boundary

- **Transition:** T1
- **Status:** Planning approved; implementation blocked
- **Severity:** High
- **What changed:** Selected a bounded Windows protected-signing pilot and defined its signer, IPC, lifecycle, refusal, recovery, rollback, and assurance contracts.
- **What broke or was discovered:** TPM readiness is unavailable or not exposed on this host, so hardware-backed custody cannot be claimed for the initial pilot.
- **Root cause:** No configured signer service identity, protected key, IPC ACL, lifecycle authority, audit target, or recovery process currently exists.
- **Fix applied or proposed:** Use a distinct Windows service identity with a non-exportable Microsoft Software KSP key and ACL-restricted authenticated named-pipe interface; require a separate gate for hardware backing.
- **Why this fix:** It can replace direct runtime key possession under testable local OS controls without adding network or consequential authority.
- **Remaining risk:** Local administrator/service compromise, software-provider compromise, shared-host failure, audit/lifecycle tampering, and absence of hardware protection remain unresolved.
- **Refactor required:** Yes before implementation and again before hardware-backed or production claims.
- **Related controls:** `docs/transitions/t1-protected-signing-plan.md`, AUD100-004, TD-104, INV-TRAJ-001, INV-FAIL-001 through INV-FAIL-003.
- **Tests added:** None; T1 remains planning-only.
- **Tests still missing:** All protected key, caller-token, named-pipe, lifecycle, replay, rotation, restart, failure, rollback, and substitute-key adversarial tests.
- **Owner:** Nova Aegis
- **Review date:** Before T1 implementation and mandatory pre-T2 audit.

### TD-104 - Protected deployment controls require a concrete platform

- **Phase:** 104
- **Status:** Blocked pending platform and operational decisions
- **Severity:** High
- **What changed:** Mapped an offline-first architecture for protected custody, independent retention and witness authority, durable coordination, permit enforcement, signed deployment, and rollback.
- **What broke or was discovered:** Process-local simulations cannot enforce trust against their own host, caller, alternate execution paths, shared keys, or shared storage failure domain.
- **Root cause:** No concrete deployment platform, protected key facility, immutable retention system, trusted clock, external fencing target, or operational owner has been selected.
- **Fix applied or proposed:** Follow `docs/research/phase-104-protected-deployment-architecture.md` after human selection and threat modeling of the target platform.
- **Why this fix:** Protected controls must be enforced outside model and worker processes; naming local metadata differently would not reduce the risk.
- **Remaining risk:** AUD100-004 and every Phase 99 deployment blocker remain unresolved.
- **Refactor required:** Yes before any Phase 104 platform implementation or real integration.
- **Related controls:** AUD100-004 through AUD100-008, TD-099, TD-100, Phases 101-103.
- **Tests added:** None; Phase 104 is architecture-only.
- **Tests still missing:** All platform custody, retention, concurrency, trusted-time, fencing, gateway-bypass, deployment, rollback, and recovery tests.
- **Owner:** Nova Aegis
- **Review date:** Before platform selection and at Phase 105 audit.

### TD-103 - Budget permits do not enforce alternate execution paths

- **Phase:** 103
- **Status:** Mitigated inside the synthetic coordinator; external enforcement blocked
- **Severity:** High
- **What changed:** Added signed pre-operation budget debits, exact exhaustion, duplicate-operation refusal, usage verification, and terminal consumed-unit accounting.
- **What broke or was discovered:** Phase 98 budget values were copied into receipts but did not constrain any operation or record consumption.
- **Root cause:** The coordinator had ownership and terminal-state controls but no pre-operation metering boundary.
- **Fix applied or proposed:** Require `authorize_consumption` before each synthetic operation and return a signed permit only after debit.
- **Why this fix:** Pre-operation debit makes exhaustion deterministic and prevents worker self-reporting from defining accepted usage.
- **Remaining risk:** Callers can bypass the coordinator unless every real worker/tool endpoint enforces permits; keys and time remain local.
- **Refactor required:** Yes before real workers or tools.
- **Related controls:** AUD100-003, `docs/research/phase-103-enforced-synthetic-budgets.md`.
- **Tests added:** Six focused budget enforcement tests.
- **Tests still missing:** Execution-gateway bypass, durable atomic debit, concurrent consumption, protected keys, trusted time, and real cost metering.
- **Owner:** Nova Aegis
- **Review date:** Phase 105 audit or before any execution integration.

### TD-102 - Witness-owned replay still shares a local failure domain

- **Phase:** 102
- **Status:** Mitigated for caller-constructed records; independent authority blocked
- **Severity:** High
- **What changed:** Removed raw-record attestation and required witness-owned anchored retrieval by evidence ID with checkpoint binding.
- **What broke or was discovered:** A witness could previously sign any caller-constructed record without proving that it existed in authenticated persistent evidence.
- **Root cause:** The Phase 97 attestation API accepted record objects across the witness boundary.
- **Fix applied or proposed:** Accept only evidence IDs and require witness and arbiter verification through `AnchoredSQLiteSyntheticEvidenceStore`.
- **Why this fix:** It moves evidence retrieval and chain verification into the witness path and cryptographically binds the current checkpoint.
- **Remaining risk:** Evaluator, witnesses, keys, anchors, and storage remain controlled by one process and caller.
- **Refactor required:** Yes before independent-evidence claims.
- **Related controls:** AUD100-002, `docs/research/phase-102-witness-owned-verification.md`.
- **Tests added:** Added missing-evidence and corrupted anchored-replay refusal to the witness suite.
- **Tests still missing:** Separate process identity, non-exportable witness keys, independent storage credentials, revocation, and compromise recovery.
- **Owner:** Nova Aegis
- **Review date:** Phase 105 audit or before witness deployment.

### TD-101 - Local anchors are not immutable external retention

- **Phase:** 101
- **Status:** Mitigated when separately retained; protected retention blocked
- **Severity:** High
- **What changed:** Added signed chained checkpoints that detect evidence tail/full deletion, anchor rollback, missing anchors, and tampering when the anchor database survives.
- **What broke or was discovered:** The Phase 96 self-contained chain accepted shortened or empty histories after tail or full deletion.
- **Root cause:** Expected event count and terminal digest existed only inside the evidence database being verified.
- **Fix applied or proposed:** Persist a separately signed checkpoint chain and require exact anchor agreement before replay or append.
- **Why this fix:** An independently surviving expected count and terminal digest make tested truncation and rollback observable without weakening offline operation.
- **Remaining risk:** An attacker deleting or rolling back both local databases can erase the expected state; local keys and backups are not protected.
- **Refactor required:** Yes before complete-history or immutable-retention claims.
- **Related controls:** AUD100-001, AUD100-007, `docs/research/phase-101-evidence-anchoring.md`.
- **Tests added:** Six focused anchor and strict canonical JSON tests.
- **Tests still missing:** Independent WORM retention, protected checkpoint keys, cross-device restore, concurrent writers, and dual-store power loss.
- **Owner:** Nova Aegis
- **Review date:** Phase 105 audit or before retained-evidence integration.

### TD-100 - Phase 100 retains confirmed evidence, witness, and budget gaps

- **Phase:** 100
- **Status:** Accepted for bounded synthetic remediation; pre-production blocked
- **Severity:** High
- **What changed:** Audited Phases 95-99, ran the 183-test regression, reviewed invariants and threat boundaries, and issued an explicit gate decision.
- **What broke or was discovered:** Tail/full evidence deletion can evade chain replay, witnesses can sign caller-constructed unverified records, and workload budgets are metadata rather than enforced limits.
- **Root cause:** Local chain state lacks an external anchor, witness attestation does not own evidence retrieval, and the coordinator does not execute or meter work.
- **Fix applied or proposed:** Track AUD100-001 through AUD100-003 as named blockers; require anchored evidence, witness-owned replay, and metered execution before stronger claims.
- **Why this fix:** It prevents passing synthetic tests and local metadata from being misrepresented as completeness, independence, budget enforcement, or readiness.
- **Remaining risk:** All Phase 99 deployment blockers remain unresolved, including custody, retention, identity, trusted time, concurrency, fencing, transport, data governance, recovery, and consequential-action controls.
- **Refactor required:** Yes before any real integration or pre-production boundary.
- **Related controls:** `docs/audits/phase-100-audit.md`, `docs/research/phase-99-pre-production-boundary-review.md`, AUD100-001 through AUD100-008, INV-FAIL-002, INV-AUD-001 through INV-AUD-003, INV-HUMAN-001 through INV-HUMAN-003.
- **Tests added:** No implementation tests in the audit; the complete 183-test suite passed.
- **Tests still missing:** Tail/full deletion detection, forged pre-attestation evidence refusal, strict canonical JSON, authenticated witness history, concurrency, durable leases, trusted time, enforced budgets, protected custody, and deployment controls.
- **Owner:** Nova Aegis
- **Review date:** Phase 105 audit or before any boundary expansion.
- **Remediation status:** AUD100-001 through AUD100-003 are mitigated in bounded local APIs by Phases 101-103. Their protected retention, independent authority, and external execution-enforcement variants remain open under TD-101 through TD-104.

### TD-099 - Pre-production boundary remains blocked

- **Phase:** 99
- **Status:** Blocked
- **Severity:** High
- **What changed:** Defined typed review outcomes, an exact integration interface contract, threat-model delta, human approval binding, rollback/refusal plan, and deployment blocker checklist.
- **What broke or was discovered:** No concrete deployment target, protected evidence, independent authority, trusted coordination, exact approval, or completed deployment control exists.
- **Root cause:** Phases 96-98 are local synthetic experiments rather than an enforceable integration control plane.
- **Fix applied or proposed:** Return `BLOCKED`, preserve default deny, and require every checklist item to be independently verified before reconsideration.
- **Why this fix:** Review artifacts must not silently become credentials, authority, readiness evidence, or deployment permission.
- **Remaining risk:** Every listed deployment blocker remains unresolved.
- **Refactor required:** Yes before any pre-production integration.
- **Related controls:** `docs/research/phase-99-pre-production-boundary-review.md`, AUD95-001 through AUD95-005, TD-096 through TD-098, INV-AUTH-001 through INV-AUTH-003, INV-HUMAN-001 through INV-HUMAN-003.
- **Tests added:** None; Phase 99 is review-only.
- **Tests still missing:** All enforceable deployment, rollback, identity, custody, retention, network, data, worker, and consequential-action controls.
- **Owner:** Nova Aegis
- **Review date:** Phase 100 audit and before any integration request.

### TD-098 - Local workload leases are not distributed authority

- **Phase:** 98
- **Status:** Mitigated for bounded local coordination; distributed reliability remains blocked
- **Severity:** High
- **What changed:** Added deterministic attempt ordering, bounded active leases, worker ownership, fencing tokens, explicit lease expiry, terminal crash/timeout receipts, and replay refusal.
- **What broke or was discovered:** Fixed-budget evaluation cases lacked a dedicated ownership lifecycle and could not distinguish explicit terminal expiry from implicit retry or requeue behavior.
- **Root cause:** Phase 94 measured attempts but did not coordinate local worker ownership or terminal lease state.
- **Fix applied or proposed:** Add `SyntheticWorkloadCoordinator` with one-claim attempt semantics and immutable terminal receipts.
- **Why this fix:** It makes local scheduling and ownership deterministic without adding networking, automatic recovery, or consequential execution.
- **Remaining risk:** State is process-local; time is caller-supplied; fencing is not enforced externally; process loss, concurrent mutation, distributed ownership, and failover are unproven.
- **Refactor required:** Yes before real workers, distributed coordination, trusted scheduling, or production recovery.
- **Related controls:** `docs/research/phase-98-bounded-workload-coordination.md`, AUD95-001 through AUD95-005, TD-093, TD-094, TD-096, TD-097, INV-FAIL-002, INV-AUD-001 through INV-AUD-003.
- **Tests added:** Six focused tests for deterministic scheduling, parallelism bounds, ownership/fencing, terminal receipts, crash/timeout separation, expiry, no replay/requeue, and invalid configuration.
- **Tests still missing:** Durable coordination, real concurrency, trusted time, external fencing enforcement, process crash recovery, distributed ordering, and deployment enforcement.
- **Owner:** Nova Aegis
- **Review date:** Phase 100 mandatory audit or before any real worker integration.

### TD-097 - Synthetic witness separation is not compromise independence

- **Phase:** 97
- **Status:** Mitigated for distinct local witness verification; independent external evidence remains blocked
- **Severity:** High
- **What changed:** Added exact evidence attestations, distinct evaluator/witness identity checks, witness-only keys, separate SQLite attestation persistence, and verified quorum decisions.
- **What broke or was discovered:** Phase 96 authenticated evaluator evidence but did not provide a distinct verification path or quorum capable of refusing self-attestation and evidence substitution.
- **Root cause:** Evidence authentication and evidence witnessing were owned by one local evaluator boundary.
- **Fix applied or proposed:** Add local synthetic evidence witnesses, a separate attestation store, and a distinct-witness arbiter.
- **Why this fix:** It tests identity, key, storage, binding, and quorum separation without introducing networking, external identity, or production authority.
- **Remaining risk:** The same process and caller can control evaluator and witnesses, choose storage paths, access all local keys, and mutate both databases; compromise independence is not established.
- **Refactor required:** Yes before independent evidence, organizational witness authority, distributed quorum, or production use.
- **Related controls:** `docs/research/phase-97-independent-synthetic-witness.md`, AUD95-001 through AUD95-005, TD-096, INV-FAIL-002, INV-AUD-001 through INV-AUD-003.
- **Tests added:** Six focused tests for restart persistence, self-witness refusal, exact binding, signature tampering, quorum, duplicate/unknown/insufficient witnesses, conflicts, and missing attestations.
- **Tests still missing:** Protected witness identities and keys, immutable independent storage, process isolation, distributed quorum, revocation, and deployment enforcement.
- **Owner:** Nova Aegis
- **Review date:** Phase 100 audit or before any Phase 98 scope reopening.

### TD-096 - Authenticated evidence remains locally mutable

- **Phase:** 96
- **Status:** Mitigated for authenticated local replay; protected retention remains blocked
- **Severity:** High
- **What changed:** Added a SQLite evidence chain for synthetic transcripts and failure receipts with canonical payloads, sequence continuity, prior-event digests, HMAC authentication, and full replay verification.
- **What broke or was discovered:** Existing synthetic outcome and failure records lacked a shared authenticated persistence boundary and could not prove complete restart replay or explicit corruption refusal.
- **Root cause:** Phase 92-94 evidence was process-local or stored without a dedicated authenticated event chain.
- **Fix applied or proposed:** Add `SQLiteSyntheticEvidenceStore` using injected local keys and fail-closed full-history verification before replay or append.
- **Why this fix:** It detects tested local mutation, deletion, malformed rows, unknown keys, and chain gaps without adding network access or production authority.
- **Remaining risk:** Direct database access can destroy evidence; local HMAC keys are not protected custody; SQLite and backups are not immutable retention; hardware power-loss and distributed ordering are unproven.
- **Refactor required:** Yes before protected evidence, independent witness authority, distributed use, or production recovery.
- **Related controls:** `docs/research/phase-96-protected-synthetic-evidence.md`, AUD95-001 through AUD95-005, TD-092 through TD-095, INV-FAIL-002, INV-AUD-001 through INV-AUD-003.
- **Tests added:** Six focused tests for restart replay, payload tampering, missing rows, unknown historical keys, corrupt-chain append refusal, duplicate/invalid evidence, and partial rows.
- **Tests still missing:** Hardware power-loss, protected key custody, immutable backups, concurrent writers, independent witnessing, distributed ordering, and deployment enforcement.
- **Owner:** Nova Aegis
- **Review date:** Phase 100 audit or before any Phase 97 scope reopening.

### TD-095 - Phase 95 retains high production blockers and freezes further work

- **Phase:** 95
- **Status:** Accepted; roadmap frozen pending human review
- **Severity:** High
- **What changed:** Audited Phases 90-94 and confirmed the synthetic boundary, outcome, failure, and scaling controls remain bounded and offline-first.
- **What broke or was discovered:** Local transcripts, receipts, confidence intervals, and process state do not establish protected custody, independent evidence, real containment, crash-safe durability, or deployment enforcement.
- **Root cause:** The project remains a process-local synthetic proof with caller-controlled evidence and no protected integration control plane.
- **Fix applied or proposed:** Retain production hard-disable, record the blockers, and freeze Phase 96-100 implementation until deliberate human review.
- **Why this fix:** It prevents roadmap momentum or local metadata from being misrepresented as readiness or authority.
- **Remaining risk:** Local compromise, process loss, fabricated evidence, host escape, distributed disagreement, and consequential integration risk remain unresolved.
- **Refactor required:** Yes before any real integration, distributed recovery, independent evidence, or consequential action.
- **Related controls:** `docs/audits/phase-95-audit.md`, `docs/research/phase-96-100-roadmap.md`, TD-090 through TD-094, INV-FAIL-002, INV-AUD-001 through INV-AUD-003.
- **Tests added:** Phase 94 added four focused tests; Phase 95 added no implementation.
- **Tests still missing:** Protected evidence, independent witness authority, coordinated workload safety, deployment enforcement, and all production controls.
- **Owner:** Nova Aegis
- **Review date:** Phase 100 audit or earlier boundary/security event.

### TD-094 - Synthetic scaling evaluation is measurement-only

- **Phase:** 94
- **Status:** Mitigated for deterministic synthetic accounting; capability generalization remains blocked
- **Severity:** High
- **What changed:** Added complete fixed-budget/parallelism/seed matrix validation, outcome classification, cost accounting, attempt accounting, and Wilson confidence intervals.
- **What broke or was discovered:** Repeated-attempt summaries can conflate valid success, false success, disengagement, self-destruction, execution failure, and invalid transcripts without an explicit classification contract.
- **Root cause:** No deterministic matrix and outcome aggregation contract connected the Phase 92 reviewer and Phase 93 failure receipts.
- **Fix applied or proposed:** Add `SyntheticScalingEvaluator` and immutable evaluation case/report models.
- **Why this fix:** It makes bounded synthetic measurements reproducible and prevents incomplete or ambiguous matrices from producing reports.
- **Remaining risk:** No real parallel workload, process persistence, statistical independence, crash-safe storage, or generalized capability evidence is established.
- **Refactor required:** Yes before live evaluation, distributed workers, or production reliability claims.
- **Related controls:** `docs/research/phase-94-scaling-evaluation.md`, TD-091 through TD-093, INV-FAIL-002, INV-AUD-001 through INV-AUD-003.
- **Tests added:** Four focused tests for matrix accounting, outcome separation, incomplete matrices, and ambiguous case state.
- **Tests still missing:** Real workload scheduling, durable reports, independent samples, and protected evidence.
- **Owner:** Nova Aegis
- **Review date:** Phase 100 mandatory audit or before any boundary expansion.

### TD-093 - Synthetic failure receipts are local and non-recovering

- **Phase:** 93
- **Status:** Mitigated for synthetic failure accounting; recovery assurance remains blocked
- **Severity:** High
- **What changed:** Added a bounded-timeout failure ledger with a fixed failure taxonomy, one terminal receipt per attempt, teardown state, and explicit replay refusal.
- **What broke or was discovered:** The boundary model could become unavailable after a destructive failure, but no local contract recorded crash, hang, corruption, self-invalidation, or unavailable state without implying repair or retry.
- **Root cause:** Failure lifecycle and no-replay semantics were not represented as a dedicated synthetic receipt contract.
- **Fix applied or proposed:** Add `SyntheticFailureLedger` and immutable `SyntheticFailureReceipt` records.
- **Why this fix:** It makes destructive failures observable and terminal while preserving the offline, synthetic-only boundary.
- **Remaining risk:** The ledger is process-local and caller-controlled; it does not enforce timeouts for arbitrary code, survive process loss, coordinate recovery, or prove production reliability.
- **Refactor required:** Yes before consequential recovery, protected persistence, or real execution boundaries.
- **Related controls:** `docs/research/phase-93-failure-semantics.md`, TD-091, TD-092, INV-FAIL-002, INV-AUD-001 through INV-AUD-003.
- **Tests added:** Eight focused tests for the failure taxonomy, timeout bounds, unavailable/invalid state, teardown verification, duplicate terminal receipts, immutable exposure, and replay refusal.
- **Tests still missing:** Protected durable failure storage, real timeout enforcement, crash-safe append semantics, recovery coordination, and deployment-boundary enforcement.
- **Owner:** Nova Aegis
- **Review date:** Phase 95 mandatory audit or before any boundary expansion.

### TD-092 - Synthetic success requires independent boundary evidence

- **Phase:** 92
- **Status:** Mitigated for local synthetic outcome review; generalized evaluation remains blocked
- **Severity:** High
- **What changed:** Added an immutable transcript reviewer that accepts exactly one matching boundary-originated goal signal.
- **What broke or was discovered:** A boolean success report alone cannot distinguish an actual boundary signal from subject self-attestation, fixture leakage, evaluator shortcuts, alternate paths, or malformed event order.
- **Root cause:** Outcome validity was not represented as an independent event-level contract.
- **Fix applied or proposed:** Add `SyntheticOutcomeReviewer` with exact goal matching, source restrictions, shortcut detection, and fail-closed transcript validation.
- **Why this fix:** It makes the Phase 92 success criterion deterministic and auditable without trusting the subject or evaluator to declare success.
- **Remaining risk:** Events are still process-local and caller-supplied; this does not prove independence, prevent a compromised host from fabricating events, or generalize to real agents or sandboxes.
- **Refactor required:** Yes before live semantic evaluation, real containment, or capability claims.
- **Related controls:** `docs/research/phase-92-outcome-validity.md`, TD-091, INV-FAIL-002, INV-AUD-001 through INV-AUD-003.
- **Tests added:** Five focused tests for exact success, self-report refusal, fixture/evaluator shortcut refusal, wrong/missing/duplicate signals, and ambiguous sequence refusal.
- **Tests still missing:** Durable append-only transcript storage, independent witness verification, crash semantics, repeated-attempt accounting, and real deployment-boundary enforcement.
- **Owner:** Nova Aegis
- **Review date:** Phase 95 mandatory audit or before any boundary expansion.

### TD-091 - Synthetic boundary is a contract simulator

- **Phase:** 91
- **Status:** Mitigated for benign local boundary testing; real containment remains blocked
- **Severity:** High
- **What changed:** Added an explicit synthetic boundary manifest, narrow benign capability execution, host/filesystem/network/production denial, and observable teardown.
- **What broke or was discovered:** The existing preflight decided continuation but did not model the subject boundary or expose a capability inventory and teardown state.
- **Root cause:** No local evaluation contract existed for the inner synthetic subject boundary.
- **Fix applied or proposed:** Add `SyntheticNestedBoundary` as a process-local contract simulator with fail-closed manifest validation.
- **Why this fix:** It enables Phase 92 outcome-validity testing without introducing shell access, real filesystem access, network access, or consequential actions.
- **Remaining risk:** This is not OS-level isolation and cannot detect container, VM, kernel, host, or deployment escape. Local code can bypass the simulator if treated as enforcement.
- **Refactor required:** Yes before any real containment or agent execution evaluation.
- **Related controls:** `docs/research/phase-91-nested-synthetic-boundary.md`, AUD90-001 through AUD90-004, INV-FAIL-002, INV-AUD-001 through INV-AUD-003.
- **Tests added:** Five focused tests for capability allowlisting, denied requests, teardown, unavailable state, and unsafe manifests.
- **Tests still missing:** Real nested isolation, host non-access proof, crash handling, shortcut detection, transcript classification, and deployment enforcement.
- **Owner:** Nova Aegis
- **Review date:** Phase 95 mandatory audit or before any boundary expansion.

### TD-090 - Phase 90 mandatory audit findings

- **Phase:** 90
- **Status:** Accepted for synthetic-only research; production blockers remain
- **Severity:** High
- **What changed:** Audited Phase 85 and reviewed the bounded Phase 86-89 roadmap for durable key replay, lifecycle integrity, two-person rotation, and deployment-boundary enforcement.
- **What broke or was discovered:** No Critical synthetic defect was found. Phases 86-89 are planning entries only; they do not yet provide implementation evidence or reduce the protected authority, custody, retention, distributed ordering, or deployment blockers.
- **Root cause:** The current system remains local, injected, and process-controlled, with no protected deployment control plane.
- **Fix applied or proposed:** Approve the roadmap as synthetic research only; implement each phase separately with adversarial tests and retain production hard-disable.
- **Why this fix:** It prevents roadmap intent or local integrity metadata from being misrepresented as authorization or readiness.
- **Remaining risk:** Local compromise, filesystem loss or tampering, stale lifecycle state, caller-controlled authority, distributed disagreement, and deployment bypass remain possible.
- **Refactor required:** Yes before real integrations, consequential recovery, independent evidence, distributed policy, or networked MCP.
- **Related controls:** `docs/audits/phase-90-audit.md`, `docs/research/phase-86-89-roadmap.md`, AUD90-001 through AUD90-005, INV-FAIL-002, INV-HUMAN-001 through INV-HUMAN-003, INV-AUD-001 through INV-AUD-003.
- **Tests added:** No implementation tests; audit revalidated the 143-test suite and current synthetic controls.
- **Tests still missing:** All implementation evidence specified for Phases 86-89, plus protected identity/custody, immutable retention, crash/failover, distributed ordering, and deployment enforcement.
- **Owner:** Nova Aegis
- **Review date:** Phase 95 mandatory audit or before any boundary expansion.

### TD-085 - Phase 85 mandatory audit findings

- **Phase:** 85
- **Status:** Accepted for synthetic-only research; production blockers remain
- **Severity:** High
- **What changed:** Audited Phases 80-84, including synthetic policy authority, identity lifecycle, durable identity replay, and policy-key rotation/retirement.
- **What broke or was discovered:** No Critical synthetic defect was found. Local identity, SQLite replay, and injected key lifecycle controls improve fail-closed behavior but do not establish protected authority, retention, custody, or deployment enforcement.
- **Root cause:** The implementation remains bounded to local SQLite events, caller-supplied synthetic lifecycle authority, injected process-local keys, and no protected deployment control plane.
- **Fix applied or proposed:** Continue synthetic-only research and retain High blockers for protected identity/custody, immutable retention, distributed ordering, authenticated rotation, and deployment enforcement.
- **Why this fix:** It preserves human authority and prevents local integrity signals from becoming production authorization or independent evidence.
- **Remaining risk:** Local compromise, filesystem loss or tampering, power-loss, split-brain ordering, stale rotation state, and deployment bypass remain possible.
- **Refactor required:** Yes before real integrations, consequential recovery, independent evidence, distributed policy, or networked MCP.
- **Related controls:** `docs/audits/phase-85-audit.md`, AUD85-001 through AUD85-005, INV-FAIL-002, INV-HUMAN-001 through INV-HUMAN-003, INV-AUD-001 through INV-AUD-003.
- **Tests added:** No implementation tests; audit revalidated the 143-test suite and focused Phase 83-84 controls.
- **Tests still missing:** Protected identity/custody, immutable retention, crash/failover, distributed ordering, authenticated rotation, rollback prevention, and deployment enforcement.
- **Owner:** Nova Aegis
- **Review date:** Phase 90 mandatory audit or before any boundary expansion.

### TD-084 - Synthetic policy keys remain locally controlled

- **Phase:** 84
- **Status:** Mitigated for synthetic rotation testing; protected key custody remains blocked
- **Severity:** High
- **What changed:** Added injected policy signing-key rotation, active-key successor signing, non-active-key retirement, and lifecycle-authority checks.
- **What broke or was discovered:** Without explicit lifecycle controls, old synthetic signing keys could remain trusted indefinitely and rotation authority was implicit.
- **Root cause:** The policy key provider was a minimal static test fixture without rotation or retirement semantics.
- **Fix applied or proposed:** Require the configured synthetic lifecycle authority for rotation and retirement; refuse verification after key retirement.
- **Why this fix:** It tests fail-closed key lifecycle behavior while keeping custody local and explicit.
- **Remaining risk:** Local key compromise, caller-controlled lifecycle authority, missing hardware protection, rotation propagation gaps, and deployment bypass remain possible.
- **Refactor required:** Yes before protected policy authority or production boundary enablement.
- **Related controls:** `docs/research/phase-84-synthetic-policy-key-lifecycle.md`, TD-081, AUD80-001, INV-FAIL-002, INV-AUD-001 through INV-AUD-003.
- **Tests added:** Successor signing, old-key retirement refusal, active-key retirement refusal, and invalid lifecycle authority tests.
- **Tests still missing:** Protected custody, rotation ceremony, distributed propagation, rollback prevention, and deployment enforcement.
- **Owner:** Nova Aegis
- **Review date:** Phase 85 mandatory audit or before any boundary expansion.

### TD-083 - Synthetic identity replay remains locally durable

- **Phase:** 83
- **Status:** Mitigated for SQLite replay testing; protected retention remains blocked
- **Severity:** High
- **What changed:** Added append-only SQLite identity registration and revocation events with restart replay and terminal revocation.
- **What broke or was discovered:** In-memory identity lifecycle state was lost on restart and could not demonstrate durable revocation.
- **Root cause:** Phase 82 used a process-local registry with no persistence boundary.
- **Fix applied or proposed:** Reconstruct identity state from append-only local SQLite events and reject re-registration after revocation.
- **Why this fix:** It exercises restart behavior and preserves fail-closed lifecycle semantics in the synthetic environment.
- **Remaining risk:** Local database loss or tampering, lack of immutable retention, split-brain ordering, stale replicas, and unprotected identity remain possible.
- **Refactor required:** Yes before protected retention, distributed identity, or organizational authority.
- **Related controls:** `docs/research/phase-83-durable-synthetic-identity-replay.md`, TD-082, AUD80-001, INV-FAIL-002, INV-AUD-001 through INV-AUD-003.
- **Tests added:** Same-database close/reopen replay and terminal revocation tests.
- **Tests still missing:** Crash consistency, corruption recovery, immutable storage, distributed ordering, and protected identity proof.
- **Owner:** Nova Aegis
- **Review date:** Phase 85 mandatory audit or before any boundary expansion.

### TD-082 - Synthetic identity registry remains unprotected

- **Phase:** 82
- **Status:** Mitigated for local identity lifecycle testing; protected identity remains blocked
- **Severity:** High
- **What changed:** Added an injected local identity registry with explicit registration, terminal revocation, and signer/approver validation for synthetic policy releases.
- **What broke or was discovered:** Phase 81 identity labels were not checked against any identity source; unknown labels could otherwise be presented as authority participants.
- **Root cause:** The synthetic authority had caller-supplied identity strings but no registry or lifecycle boundary.
- **Fix applied or proposed:** Require active registry membership during issue and verify, and reject re-registration after revocation.
- **Why this fix:** It makes the synthetic experiment deterministic and fail closed without promoting local metadata into protected identity.
- **Remaining risk:** Local registry compromise, missing protected identity, weak key custody, identity collision, stale replicas, and deployment bypass remain possible.
- **Refactor required:** Yes before production boundary enablement or organizational policy authority.
- **Related controls:** `docs/research/phase-82-synthetic-identity-lifecycle.md`, TD-081, AUD80-001, INV-FAIL-002, INV-HUMAN-001 through INV-HUMAN-003.
- **Tests added:** Active identity happy path, unknown signer, revoked approver, and re-registration rejection tests.
- **Tests still missing:** Protected identity proof, custody, rotation, distributed revocation propagation, and deployment enforcement.
- **Owner:** Nova Aegis
- **Review date:** Phase 85 mandatory audit or before any boundary expansion.

### TD-081 - Synthetic policy authority remains unprotected

- **Phase:** 81
- **Status:** Adapted for local approval-binding tests; protected policy authority remains blocked
- **Severity:** High
- **What changed:** Added signed synthetic policy releases binding boundary, decision, signer, approver, approval ID, and production-disabled state.
- **What broke or was discovered:** Self-approval, mismatched approvals, revoked approvals, unknown keys, tampering, and production state fail closed, but local identities and keys do not establish organizational authority.
- **Root cause:** The authority has no protected signer custody, approval control plane, organizational identity, or distributed policy consistency.
- **Fix applied or proposed:** Keep the authority synthetic and production-disabled; require protected policy authority and deployment enforcement before real enablement.
- **Why this fix:** It tests separation of duties without promoting caller-supplied metadata into authorization.
- **Remaining risk:** Local compromise, forged identity labels, approval loss, distributed disagreement, and deployment bypass remain possible.
- **Refactor required:** Yes before production boundary enablement.
- **Related controls:** `docs/research/phase-81-synthetic-policy-authority.md`, AUD80-001, AUD80-002, INV-FAIL-002, INV-HUMAN-001 through INV-HUMAN-003.
- **Tests added:** Distinct signer/approver, self-approval, mismatched approval, revocation, tampering, production, and missing-key tests.
- **Tests still missing:** Protected identity, approval custody, signer rotation, distributed policy agreement, and deployment enforcement.
- **Owner:** Nova Aegis
- **Review date:** Phase 85 mandatory audit or before any boundary expansion.

### TD-080 - Phase 80 mandatory audit findings

- **Phase:** 80
- **Status:** Accepted for synthetic-only research; production blockers remain
- **Severity:** High
- **What changed:** Audited Phases 75-79, including enforceable preflight, signed decisions, durable replay, revocation, and supersession.
- **What broke or was discovered:** No Critical synthetic defect was found. Local controls improve fail-closed behavior but do not establish protected policy authority, independent evidence, protected retention, distributed ordering, or deployment enforcement.
- **Root cause:** The implementation remains bounded to injected local keys, one SQLite event store, and process-local governance decisions.
- **Fix applied or proposed:** Continue synthetic-only research; retain High blockers for protected authority, external evidence, distributed durability, and networked deployment.
- **Why this fix:** It preserves human authority and prevents local integrity signals from becoming production authorization.
- **Remaining risk:** Local compromise, filesystem loss, power-loss, split-brain ordering, external conflict, and deployment bypass remain possible.
- **Refactor required:** Yes before real integrations, consequential recovery, distributed policy, independent evidence, or networked MCP.
- **Related controls:** `docs/audits/phase-80-audit.md`, AUD80-001 through AUD80-005, INV-FAIL-002, INV-HUMAN-001 through INV-HUMAN-003, INV-AUD-001 through INV-AUD-003.
- **Tests added:** Phase 76-79 focused enforcement, signing, replay, revocation, and supersession tests; full 133-test regression passed.
- **Tests still missing:** Protected policy authority, crash/failover, distributed ordering, immutable retention, independent evidence, network transport, and deployment enforcement.
- **Owner:** Nova Aegis
- **Review date:** Phase 85 mandatory audit or before any boundary expansion.

### TD-079 - Decision lifecycle remains locally ordered

- **Phase:** 79
- **Status:** Adapted for synthetic revocation and supersession testing; protected lifecycle authority remains blocked
- **Severity:** High
- **What changed:** Added append-only supersession events, terminal revocation checks, same-boundary successor validation, and current-successor replay.
- **What broke or was discovered:** Local ordering makes stale decisions and revoked successors fail closed, but it does not establish distributed ordering, protected revocation authority, or organizational policy approval.
- **Root cause:** The lifecycle is stored in one local SQLite database and depends on injected signing keys.
- **Fix applied or proposed:** Keep revocation terminal and supersession fail closed; require protected lifecycle authority and distributed consistency before real deployment.
- **Why this fix:** It prevents ambiguous local replay without treating event order as production governance.
- **Remaining risk:** Database loss, local compromise, split-brain ordering, and deployment bypass remain possible.
- **Refactor required:** Yes before production boundary enablement.
- **Related controls:** `docs/research/phase-79-decision-revocation-supersession.md`, AUD75-001, AUD75-003, INV-FAIL-002, INV-AUD-001 through INV-AUD-003.
- **Tests added:** Signed successor replay, stale-report rejection, identical-successor rejection, cross-boundary rejection, and revoked-predecessor rejection.
- **Tests still missing:** Protected revocation authority, distributed ordering, crash recovery, conflict arbitration, and deployment enforcement.
- **Owner:** Nova Aegis
- **Review date:** Phase 80 mandatory audit or before any boundary expansion.

### TD-078 - Durable signed boundary replay remains local

- **Phase:** 78
- **Status:** Adapted for local replay testing; protected policy retention remains blocked
- **Severity:** High
- **What changed:** Added append-only SQLite registration and revocation events for signed boundary decisions with exact report and key verification on replay.
- **What broke or was discovered:** Close/reopen replay and malformed-state refusal work locally, but SQLite does not establish protected retention, power-loss durability, distributed policy consistency, or production enforcement.
- **Root cause:** The store uses a local database and injected key provider without protected custody or a deployment control plane.
- **Fix applied or proposed:** Keep replay fail closed and retain production hard-disabled; require protected retention and distributed policy controls before real enablement.
- **Why this fix:** It extends auditability without presenting local persistence as authoritative governance.
- **Remaining risk:** Local compromise, filesystem loss, replay divergence, and deployment bypass remain possible.
- **Refactor required:** Yes before production boundary enablement.
- **Related controls:** `docs/research/phase-78-durable-signed-boundary-replay.md`, AUD75-001, AUD75-003, INV-FAIL-002, INV-AUD-001 through INV-AUD-003.
- **Tests added:** SQLite close/reopen replay, conflict, revocation, unknown-key, and malformed-event tests.
- **Tests still missing:** Protected retention, crash/power-loss recovery, distributed replay consistency, signed deployment enforcement, and policy conflict authority.
- **Owner:** Nova Aegis
- **Review date:** Phase 80 mandatory audit or before any boundary expansion.

### TD-077 - Signed boundary decisions remain synthetic

- **Phase:** 77
- **Status:** Adapted for local auditability; protected policy authority remains blocked
- **Severity:** High
- **What changed:** Added canonical HMAC-signed boundary decisions bound to exact preflight reports and production-disabled state.
- **What broke or was discovered:** Signing catches report mutation, unknown keys, and forged production state, but local injected keys do not establish protected policy authority or deployment enforcement.
- **Root cause:** The experiment has no protected signer, organizational approval chain, deployment control plane, or distributed policy consistency.
- **Fix applied or proposed:** Keep signed decisions synthetic and fail closed; require protected policy authority before release enforcement or production enablement.
- **Why this fix:** It improves reviewability without confusing tamper evidence with authorization.
- **Remaining risk:** A compromised local process can control the key provider or bypass the local verifier.
- **Refactor required:** Yes before production boundary enablement.
- **Related controls:** `docs/research/phase-77-signed-boundary-decisions.md`, AUD75-003, INV-FAIL-002, INV-AUD-001 through INV-AUD-003.
- **Tests added:** Exact report verification, mutation rejection, unknown-key rejection, production-state rejection, and missing-key tests.
- **Tests still missing:** Protected policy signer, approval chain, deployment enforcement, and distributed policy consistency.
- **Owner:** Nova Aegis
- **Review date:** Phase 80 mandatory audit or before any boundary expansion.

### TD-076 - Synthetic boundary gate is not protected policy authority

- **Phase:** 76
- **Status:** Adapted for local fail-closed enforcement; protected policy remains blocked
- **Severity:** High
- **What changed:** Added enforcement for synthetic boundary preflight decisions. Blocked reports and all production requests now raise instead of being silently accepted.
- **What broke or was discovered:** Local enforcement closes the caller-ignores-preflight path, but a process-local gate cannot enforce policy across deployments or establish protected authority.
- **Root cause:** The gate uses local metadata and has no protected policy signer, deployment control plane, or independently enforced release boundary.
- **Fix applied or proposed:** Keep production hard-disabled and require protected policy authority plus deployment integration before any real enablement.
- **Why this fix:** It strengthens fail-closed behavior without presenting a local governance helper as production authorization.
- **Remaining risk:** A compromised or bypassed deployment can ignore the local gate; identity, custody, transport, and distributed policy remain unresolved.
- **Refactor required:** Yes before production boundary enablement.
- **Related controls:** `docs/research/phase-76-enforceable-boundary-preflight.md`, AUD75-003, INV-FAIL-002, INV-HUMAN-001 through INV-HUMAN-003.
- **Tests added:** Blocked synthetic enforcement, valid synthetic continuation, production rejection, and invalid-mode tests.
- **Tests still missing:** Protected policy authority, deployment enforcement, signed release decisions, and distributed policy consistency.
- **Owner:** Nova Aegis
- **Review date:** Phase 80 mandatory audit or before any boundary expansion.

### TD-075 - Phase 75 mandatory audit findings

- **Phase:** 75
- **Status:** Accepted for synthetic-only research; production blockers remain
- **Severity:** High
- **What changed:** Audited witness separation, append-only local retention, synthetic quorum arbitration, and deterministic boundary preflight.
- **What broke or was discovered:** No Critical synthetic defect was found. Local retention, quorum, and preflight improve observability and failure behavior but do not create protected custody, independent evidence, or enforceable production policy.
- **Root cause:** The system remains intentionally bounded to injected local identities, SQLite, and advisory governance metadata.
- **Fix applied or proposed:** Continue synthetic-only research; retain blockers for protected identity, durable custody, external evidence, distributed recovery, and policy enforcement.
- **Why this fix:** It makes the limitations explicit without allowing local controls to become authority.
- **Remaining risk:** Local compromise, power-loss, failover, external conflict, and deployment-policy bypass remain possible.
- **Refactor required:** Yes before external evidence, consequential recovery, distributed deployment, or networked MCP.
- **Related controls:** `docs/audits/phase-75-audit.md`, AUD75-001 through AUD75-004, INV-FAIL-002, INV-HUMAN-001 through INV-HUMAN-003, INV-AUD-001 through INV-AUD-003, INV-MCP-001 through INV-MCP-004.
- **Tests added:** SQLite witness close/reopen replay/revocation, quorum arbitration, and boundary preflight tests; full 123-test regression passed.
- **Tests still missing:** Protected custody, power-loss/failover, independent witness deployment, public-key trust, external conflict authority, and enforced production policy.
- **Owner:** Nova Aegis
- **Review date:** Phase 80 mandatory audit or before any boundary expansion.

### TD-071 - Synthetic receipt witness remains non-independent

- **Phase:** 71
- **Status:** Adapted for local separation testing; independent evidence remains blocked
- **Severity:** High
- **What changed:** Added a separate local receipt witness that signs and verifies a canonical receipt digest.
- **What broke or was discovered:** Separating issuer and witness identities catches self-witnessing, tampering, and key mismatch, but caller-supplied labels and injected local keys do not establish actual independence.
- **Root cause:** The experiment has no protected organizational identity, public-key trust root, durable witness log, or external system boundary.
- **Fix applied or proposed:** Keep the witness contract fail-closed and synthetic; require protected identity, durable retention, revocation distribution, and independent deployment before using witness attestations as evidence.
- **Why this fix:** It tests the minimum separation invariant without turning a local second key into proof that an external action occurred.
- **Remaining risk:** A compromised local process can forge issuer and witness state, lose attestations, or present synthetic evidence as external fact.
- **Refactor required:** Yes before consequential recovery, external evidence, or networked MCP.
- **Related controls:** `docs/research/phase-71-independent-receipt-witness.md`, AUD70-001, INV-FAIL-002, INV-HUMAN-001 through INV-HUMAN-003, INV-MCP-001 through INV-MCP-004.
- **Tests added:** Separate witness success, self-witness rejection, receipt tampering rejection, and alternate-key rejection.
- **Tests still missing:** Protected identity, public-key trust, durable witness retention, revocation distribution, conflict arbitration, and deployment isolation.
- **Owner:** Nova Aegis
- **Review date:** Phase 75 mandatory audit or before any boundary expansion.

### TD-070 - Phase 70 mandatory audit findings

- **Phase:** 70
- **Status:** Accepted for synthetic-only research; production blockers remain
- **Severity:** High
- **What changed:** Audited Phases 65-69, including receipt lifecycle checks, synthetic transport binding, measurement-only profiling, and review-burden/fairness metrics.
- **What broke or was discovered:** No Critical synthetic defect was found. Local receipts, transport metadata, timing measurements, and routing metrics remain insufficient for independent evidence, secure network transport, optimization, or trusted reliability.
- **Root cause:** The current system intentionally stops at local deterministic contracts before protected authority, network deployment, representative runtime evidence, and independent witnesses.
- **Fix applied or proposed:** Continue synthetic-only experiments; retain blockers for consequential recovery, networked MCP, optimization, and reliability-driven routing.
- **Why this fix:** It preserves human authority and avoids converting descriptive local measurements into authority.
- **Remaining risk:** Cross-process receipt loss, transport attacks, misleading performance conclusions, and unfair or poisoned routing remain possible at real deployment boundaries.
- **Refactor required:** Yes before any corresponding production boundary.
- **Related controls:** `docs/audits/phase-70-audit.md`, AUD70-001 through AUD70-004, INV-FAIL-002, INV-HUMAN-001 through INV-HUMAN-003, INV-MCP-001 through INV-MCP-004.
- **Tests added:** Snapshot, transport-envelope, manifest-lifecycle, and focused boundary tests; full 114-test regression passed.
- **Tests still missing:** Independent receipt witnessing, network transport security, representative runtime quality/memory evidence, protected provenance, calibration, and fairness.
- **Owner:** Nova Aegis
- **Review date:** Before Phase 75 or any boundary expansion.

### TD-065 - Phase 65 mandatory audit findings

- **Phase:** 65
- **Status:** Accepted for synthetic-only research; production blockers remain
- **Severity:** High
- **What changed:** Audited manifest key lifecycle, historical snapshots, SQLite failure probes, and synthetic reliability attestation.
- **What broke or was discovered:** No Critical synthetic defect was found, but local key rotation, snapshots, SQLite state, and attestation metadata remain non-independent and deployment-specific.
- **Root cause:** The current boundary intentionally proves fail-closed local behavior before protected custody, archival authority, distributed durability, or independent witnesses exist.
- **Fix applied or proposed:** Continue synthetic-only experiments; retain blockers for protected authority, trusted retrieval, distributed recovery, and reliability adoption.
- **Why this fix:** It preserves bounded authority and prevents local integrity signals from becoming production claims.
- **Remaining risk:** Forged local lifecycle state, unavailable historical sources, physical durability failures, and poisoned reliability claims remain possible.
- **Refactor required:** Yes before any corresponding production boundary.
- **Related controls:** `docs/audits/phase-65-audit.md`, AUD65-001 through AUD65-004, INV-FAIL-002, INV-AUD-001 through INV-AUD-003.
- **Tests added:** Manifest lifecycle and snapshot rollback/digest failure tests.
- **Tests still missing:** Protected custody, immutable archival restoration, crash/failover evidence, independent attestation, calibration, and fairness.
- **Owner:** Nova Aegis
- **Review date:** Before Phase 70 or any boundary expansion.

### TD-060 - Phase 60 mandatory audit findings

- **Phase:** 60
- **Status:** Accepted for synthetic-only research; production blockers remain
- **Severity:** High
- **What changed:** Audited Phases 55-59, including corpus manifests, local concurrent replay, reliability provenance gating, and receipt conflict/revocation controls.
- **What broke or was discovered:** No Critical synthetic defect was found. Local integrity controls detect defined perturbations, but manifests, provenance claims, receipt state, SQLite coordination, and transport remain non-independent and synthetic.
- **Root cause:** The architecture proves bounded failure behavior before protected organizational authority, independent evidence, distributed coordination, or real transport are introduced.
- **Fix applied or proposed:** Continue only synthetic, hypothesis-driven research; retain High blockers for protected authority, distributed state, external evidence, and reliability adoption; retain Medium prerequisites for trusted retrieval, performance, and transport.
- **Why this fix:** It preserves human authority and fail-closed behavior while preventing local control evidence from becoming an unsafe production claim.
- **Remaining risk:** Treating local HMAC keys, manifests, observation provenance, receipts, SQLite state, or routing history as trusted could produce forged evidence, inconsistent recovery, unsafe routing, or unauthorized transport behavior.
- **Refactor required:** Yes before trusted corpus deployment, consequential recovery, reliability-driven routing, distributed deployment, or networked MCP.
- **Related controls:** `docs/audits/phase-60-audit.md`, INV-FAIL-002, INV-HUMAN-001 through INV-HUMAN-003, INV-AUD-001 through INV-AUD-003, INV-MCP-001 through INV-MCP-004, AUD60-001 through AUD60-007, TD-056 through TD-059.
- **Tests added:** Phase 56-59 focused failure and concurrency tests; full 109-test regression and focused audit validation.
- **Tests still missing:** Protected authority, distributed failover, independent receipt witnessing, authenticated scopes, historical restoration, reliability attestation/calibration/fairness, runtime prefill evidence, and networked transport.
- **Owner:** Nova Aegis
- **Review date:** Before any boundary expansion or the Phase 65 mandatory audit.

### TD-059 - Receipt and transport authority remains synthetic

- **Phase:** 59
- **Status:** Adapted for local conflict/revocation testing; independent witnessing remains open
- **Severity:** High
- **What changed:** Synthetic receipts now support explicit registration, duplicate-ID conflict rejection, and revocation while preserving task, tool, user, audience, parameter, result, signature, and expiry checks.
- **What broke or was discovered:** Local signature verification and gateway binding do not establish that an external system actually performed an action or that the receipt authority is independent.
- **Root cause:** Receipt keys and registry state remain process-local synthetic components, and MCP remains in-process rather than networked.
- **Fix applied or proposed:** Retain fail-closed receipt conflict/revocation checks and defer external authority, public-key trust, retention, and real transport until separately researched and audited.
- **Why this fix:** It closes identifiable local ambiguity without presenting synthetic receipts as external evidence.
- **Remaining risk:** Local compromise, forged registry state, revocation races, missing retention, conflicting external systems, and network transport threats remain.
- **Refactor required:** Yes before consequential recovery, independent external evidence, or networked MCP.
- **Related controls:** INV-FAIL-002, INV-HUMAN-001 through INV-HUMAN-003, INV-MCP-001 through INV-MCP-004, AUD55-003, AUD55-007.
- **Tests added:** Audience/parameter binding, revocation, duplicate-ID conflict, and focused gateway receipt recovery tests.
- **Tests still missing:** Independent witness, public-key trust, retention, revocation distribution, conflict arbitration, HTTP/OAuth/PKCE, SSRF, quotas, sessions, Apps, and Tasks.
- **Owner:** Nova Aegis
- **Review date:** Before networked MCP or the Phase 60 mandatory audit.

### TD-058 - Reliability provenance is caller-supplied

- **Phase:** 58
- **Status:** Adapted for synthetic poisoning detection; trusted reliability remains deferred
- **Severity:** High
- **What changed:** Reliability records now carry source, verification, and observation ID metadata; an opt-in provenance gate rejects unverified history and records rejected subjects.
- **What broke or was discovered:** A forged observation can poison an otherwise valid subject unless the entire subject history is provenance-gated.
- **Root cause:** Reliability history remains append-only caller-supplied operational metadata without an independent witness.
- **Fix applied or proposed:** Require every observation for a reliability-supported route to be verified and identified; otherwise retain baseline routing.
- **Why this fix:** Partial trust must not silently elevate a route or hide poisoning in an aggregate success rate.
- **Remaining risk:** Provenance claims can still be fabricated at the synthetic boundary; calibration, fairness, representative utility, review burden, and independent witnessing remain open.
- **Refactor required:** Yes before reliability-driven routing in production or consequential workflows.
- **Related controls:** INV-FAIL-002, INV-AUD-001 through INV-AUD-003, AUD55-004, TD-051.
- **Tests added:** Verified routing, unverified subject rejection, forged-observation poisoning fallback, and provenance decision metadata.
- **Tests still missing:** Protected witness, attestation, calibration, fairness, representative workload, and review-burden measurement.
- **Owner:** Nova Aegis
- **Review date:** Before reliability adoption or the Phase 60 mandatory audit.

### TD-057 - Retrieval replay reproducibility remains local

- **Phase:** 57
- **Status:** Adapted for independent local-connection testing; distributed durability remains open
- **Severity:** Medium
- **What changed:** Eight concurrent independent SQLite connections reopened, verified, and replayed the same durable retrieval trace.
- **What broke or was discovered:** Local close/reopen consistency can be tested, but this does not establish multi-host coordination, crash recovery, or immutable replication.
- **Root cause:** The audit and trace stores are intentionally bounded to local SQLite.
- **Fix applied or proposed:** Keep concurrent-reader replay as a reproducible local experiment and retain distributed deployment as a refactor gate.
- **Why this fix:** It tests the nearest meaningful boundary without overstating local consistency as distributed durability.
- **Remaining risk:** Crash injection, corruption recovery, failover, split-brain, power-loss, and protected replication remain untested.
- **Refactor required:** Yes before distributed audit, workers, or production retrieval.
- **Related controls:** INV-FAIL-002, INV-AUD-001 through INV-AUD-003, TD-054, AUD55-002, AUD55-005.
- **Tests added:** Eight concurrent independent-connection retrieval replays.
- **Tests still missing:** Crash, corruption, failover, multi-host, and immutable-anchor tests.
- **Owner:** Nova Aegis
- **Review date:** Before distributed deployment or the Phase 60 mandatory audit.

### TD-056 - Corpus manifest authority remains synthetic

- **Phase:** 56
- **Status:** Adapted for local integrity and version experiments; protected custody remains open
- **Severity:** High
- **What changed:** Added canonical, versioned HMAC corpus manifests bound to source IDs and complete corpus digests, with rollback and unknown-key rejection.
- **What broke or was discovered:** A local digest and valid HMAC can detect drift but cannot establish that the signer, corpus, authority, or revision is organizationally trusted.
- **Root cause:** The experiment uses the existing process-local injected key-provider boundary.
- **Fix applied or proposed:** Keep manifest verification fail-closed and synthetic; require protected key custody, rotation, revocation, retention, and independent anchoring before trusted corpus deployment.
- **Why this fix:** It creates an auditable integrity contract without promoting test keys into production authority.
- **Remaining risk:** Forged local key providers, unanchored manifests, invalid evidence, stale revisions, and multi-node distribution remain possible.
- **Refactor required:** Yes before trusted external evidence or protected corpus custody.
- **Related controls:** INV-FAIL-002, INV-AUD-001 through INV-AUD-003, TD-053, AUD55-001, AUD55-005.
- **Tests added:** Canonical signing, round-trip verification, tampering, rollback, unknown-key, and corpus-drift rejection.
- **Tests still missing:** Protected signer, key rotation/revocation, immutable anchoring, historical snapshots, and distributed manifest consistency.
- **Owner:** Nova Aegis
- **Review date:** Before trusted retrieval or the Phase 60 mandatory audit.

### TD-055 - Phase 55 mandatory audit findings

- **Phase:** 55
- **Status:** Accepted for synthetic-only research; production blockers remain
- **Severity:** High
- **What changed:** Audited Phases 50-54, including reliability false-route evaluation, durable retrieval replay, corpus-bound trace digests, and verified SQLite trace access.
- **What broke or was discovered:** No Critical synthetic defect was found. Local digests detect corpus drift but do not establish protected corpus authority; fabricated reliability history can still cause false route changes; identity, independent receipts, distributed coordination, and networked MCP remain synthetic.
- **Root cause:** Local experiments prove bounded control behavior, not protected organizational authority, independent witnessing, or multi-host semantics.
- **Fix applied or proposed:** Continue synthetic-only work through focused experiments for protected corpus manifests, cross-process replay, reliability provenance/poisoning, and independent receipt/transport prerequisites.
- **Why this fix:** It extends evidence and failure coverage without allowing local metadata or research metrics to become production authority.
- **Remaining risk:** Treating local keys, digests, SQLite state, receipts, scopes, or reliability history as trusted could produce forged evidence, inconsistent recovery, unsafe routing, or unauthorized transport behavior.
- **Refactor required:** Yes before real integrations, consequential recovery, reliability-driven routing, trusted retrieval, distributed deployment, or networked MCP.
- **Related controls:** `docs/audits/phase-55-audit.md`, INV-FAIL-002, INV-HUMAN-001 through INV-HUMAN-003, INV-AUD-001 through INV-AUD-003, AUD55-001 through AUD55-007, TD-051 through TD-054.
- **Tests added:** Phase 53-54 retrieval integrity and verified-access tests; full 103-test regression and focused retrieval/reliability audit validation.
- **Tests still missing:** Protected authority, distributed failover, independent receipt witnessing, reliability provenance/poisoning, authenticated retrieval scopes, historical source restoration, and networked transport.
- **Owner:** Nova Aegis
- **Review date:** Before any boundary expansion or the Phase 60 mandatory audit.

### TD-054 - Verified replay access remains local

- **Phase:** 54
- **Status:** Adapted for reviewer-facing local replay; deployment trust remains open
- **Severity:** Medium
- **What changed:** SQLite audit logs now expose retrieval traces only after hash-chain verification; reopen and scope-mismatch replay tests were added.
- **What broke or was discovered:** Durable trace access was implicit through generic event enumeration and had no dedicated verified retrieval boundary.
- **Root cause:** Retrieval traces were stored as ordinary audit details without a purpose-specific accessor.
- **Fix applied or proposed:** Add `SQLiteAuditLog.retrieval_traces()` and keep retrieval replay computation-only.
- **Why this fix:** Reviewers can obtain the intended trace records after integrity verification without conflating retrieval replay with external action replay.
- **Remaining risk:** SQLite is process-local, the hash root is not independently anchored, and caller-supplied scopes are unauthenticated.
- **Refactor required:** Yes before distributed audit or trusted external retrieval deployment.
- **Related controls:** INV-FAIL-002, INV-AUD-001 through INV-AUD-003, TD-052, AUD50-005.
- **Tests added:** SQLite close/reopen access, verified trace extraction, and scope-alteration rejection.
- **Tests still missing:** Distributed failover, immutable anchoring, authenticated scopes, and historical corpus restoration.
- **Owner:** Nova Aegis
- **Review date:** Phase 55 mandatory audit or before distributed/trusted retrieval.

### TD-053 - Retrieval replay requires corpus identity binding

- **Phase:** 53
- **Status:** Adapted for local drift detection; independent corpus authority remains open
- **Severity:** Medium
- **What changed:** Retrieval traces now include canonical corpus and trace SHA-256 digests; replay rejects missing, invalid, or mismatched digests.
- **What broke or was discovered:** Same-ID source content changes could evade a trace comparison when ranking structure remained unchanged.
- **Root cause:** Phase 52 replay compared decision structure but did not bind the decision to the complete evidence corpus.
- **Fix applied or proposed:** Fingerprint the sorted `Evidence` corpus and canonical trace payload before replay.
- **Why this fix:** Replay detects corpus drift before accepting a durable selection, while remaining deterministic and dependency-free.
- **Remaining risk:** Local digests are not protected anchors, source truth is not established, and hierarchy/authority metadata remain caller-supplied.
- **Refactor required:** Yes before trusted external evidence or protected corpus custody.
- **Related controls:** INV-FAIL-002, INV-AUD-001 through INV-AUD-003, TD-052, TD-043.
- **Tests added:** Same-ID corpus mutation and trace-digest tampering rejection.
- **Tests still missing:** Signed corpus manifests, historical source snapshots, key rotation, and cross-node reproducibility.
- **Owner:** Nova Aegis
- **Review date:** Phase 55 mandatory audit or before trusted external retrieval.

### TD-052 - Durable retrieval replay remains local

- **Phase:** 52
- **Status:** Adapted for local auditability; independent trust remains open
- **Severity:** Medium
- **What changed:** Retrieval traces now serialize, deserialize, and replay against the supplied corpus; mismatches fail with `AuditIntegrityError`; SQLite audit events provide durable local storage.
- **What broke or was discovered:** Phase 43 traces were inspectable in memory but had no tested durable replay path.
- **Root cause:** Retrieval trace details were emitted as ordinary event data without a validated reconstruction contract.
- **Fix applied or proposed:** Add validated trace round-tripping and compare every retrieval stage during replay, while reusing the existing local audit hash chain.
- **Why this fix:** A reviewer can detect tampering or corpus drift rather than accepting a persisted selection without recomputation.
- **Remaining risk:** The audit chain is local, hierarchy and authority metadata are unauthenticated, unavailable historical sources cannot be recreated, and distributed replay is untested.
- **Refactor required:** Yes before trusted external retrieval or independently durable audit deployment.
- **Related controls:** INV-FAIL-002, INV-AUD-001 through INV-AUD-003, TD-043, TD-049, AUD50-005.
- **Tests added:** Durable SQLite round-trip replay, tampered trace rejection, corpus-change rejection, and integrity verification.
- **Tests still missing:** Immutable external anchoring, authenticated metadata, historical source snapshots, cross-process replay, and distributed recovery.
- **Owner:** Nova Aegis
- **Review date:** Before trusted external retrieval or the Phase 55 mandatory audit.

### TD-051 - Reliability evaluation exposes false route changes

- **Phase:** 51
- **Status:** Adoption deferred; synthetic evaluation expanded
- **Severity:** High
- **What changed:** Expanded replay metrics to distinguish genuine improvements from false reliability-driven route changes and added representative adversarial workload coverage.
- **What broke or was discovered:** Valid-looking fabricated history can improve a synthetic score while selecting the wrong subject; aggregate accuracy alone would hide this failure.
- **Root cause:** Reliability history is caller-supplied operational metadata without an independent witness or trust calibration.
- **Fix applied or proposed:** Count false route changes explicitly, preserve conservative fallbacks for missing/stale/tied history, and keep reliability isolated from factual and governance paths.
- **Why this fix:** A routing signal must be evaluated for harm as well as benefit before adoption.
- **Remaining risk:** Poisoning resistance, representative ground truth, calibration, fairness, review burden, and independent witnessing remain untested.
- **Refactor required:** Yes before reliability-driven routing in production or consequential workflows.
- **Related controls:** INV-FAIL-002, INV-AUD-001 through INV-AUD-003, AUD50-004, TD-047, TD-049.
- **Tests added:** Genuine improvement, false route change, stale fallback, tied fallback, invalid-history rejection, and metric accounting.
- **Tests still missing:** Broad adversarial workload, history provenance, poisoning defense, calibration, fairness, review burden, and durable independent records.
- **Owner:** Nova Aegis
- **Review date:** Before Phase 52 trusted trace work or the Phase 55 mandatory audit.

### TD-050 - Phase 50 mandatory audit findings

- **Phase:** 50
- **Status:** Accepted for synthetic-only research; production blockers remain
- **Severity:** High
- **What changed:** Audited Phases 45-49, including reliability routing experiments, fixed-workload comparison, profiling deferral, and experiment decision reconstruction.
- **What broke or was discovered:** No Critical synthetic defect was found, but synthetic reliability improvement does not establish trusted routing authority, and prefill remains unmeasured at the provider boundary.
- **Root cause:** Local experiments establish control shape and conservative failure behavior, not protected identity, independent evidence, distributed coordination, representative utility, or runtime performance truth.
- **Fix applied or proposed:** Continue synthetic-only research with explicit hypotheses and gates; retain refactor blockers for protected authority, distributed state, independent receipts, trusted retrieval metadata, reliability adoption, and SIFT optimization.
- **Why this fix:** It preserves evidence-grounded governance and prevents promising research results from becoming autonomous authority through convenience.
- **Remaining risk:** Treating local key, receipt, retrieval, reliability, or profiling records as production authority could permit forged evidence, incorrect routing, inconsistent state, or unsafe optimization.
- **Refactor required:** Yes before real integrations, consequential recovery, reliability-driven routing, or networked/distributed deployment.
- **Related controls:** INV-FAIL-002, INV-HUMAN-001 through INV-HUMAN-003, INV-AUD-001 through INV-AUD-003, AUD50-001 through AUD50-007, TD-049.
- **Tests added:** Mandatory audit validation plus full regression and focused reliability/profiling checks.
- **Tests still missing:** Protected identity/custody, distributed failover, independent receipts, authenticated retrieval replay, representative reliability evaluation, and runtime prefill instrumentation.
- **Owner:** Nova Aegis
- **Review date:** Before any corresponding boundary expansion or the next mandatory audit.

### TD-049 - Research decisions need explicit reconstruction metadata

- **Phase:** 49
- **Status:** Mitigated for synthetic experiment review; production authority remains blocked
- **Severity:** Medium
- **What changed:** Routing decisions now record complete candidates, eligible candidates, success rates, selection, baseline, fallback reason, and stable serialized output; replay results are serializable for audit records.
- **What broke or was discovered:** A selected route alone was insufficient to reconstruct whether other candidates lacked fresh valid history or were tied.
- **Root cause:** The experiment initially exposed outcomes without the full eligibility boundary used to produce them.
- **Fix applied or proposed:** Preserve candidate and eligibility sets as explicit decision metadata while keeping reliability outside evidence, assurance, approval, and execution.
- **Why this fix:** Reviewers can distinguish a reliability-supported route from a conservative baseline fallback without relying on unstored control flow.
- **Remaining risk:** Metadata is local and caller-supplied; serialization is not immutable anchoring, and poisoning, fairness, calibration, and independent witnessing remain open.
- **Refactor required:** Yes before reliability routing becomes production authority or consequential workflow input.
- **Related controls:** INV-FAIL-002, INV-AUD-001 through INV-AUD-003, TD-047, TD-048.
- **Tests added:** Candidate/eligibility reconstruction and decision/replay serialization assertions.
- **Tests still missing:** Immutable audit anchoring, representative workload evidence, poisoning resistance, fairness, calibration, and durable history.
- **Owner:** Nova Aegis
- **Review date:** Before any production routing adoption or the Phase 50 mandatory audit.

### TD-048 - Prefill bottleneck not established

- **Phase:** 48
- **Status:** Deferred pending explicit runtime instrumentation
- **Severity:** Medium
- **What changed:** Added a measurement-only pipeline profiler for retrieval, context assembly, prefill, and generation stages, including repeated-context labeling and prefill share.
- **What broke or was discovered:** The current inference provider exposes only whole-prompt inference, so prefill cannot be attributed independently or claimed as a bottleneck.
- **Root cause:** The provider abstraction intentionally hides model-runtime internals for replaceability and offline governance.
- **Fix applied or proposed:** Preserve the generic profiler and defer SIFT-like optimization until a local runtime supplies trustworthy prefill instrumentation and representative workloads.
- **Why this fix:** Optimization without a measured bottleneck could add memory pressure, stale-context risk, and evidence-integrity regressions without demonstrated benefit.
- **Remaining risk:** No local prefill, repeated-context frequency, RAM, or quality tradeoff has been measured against a real runtime.
- **Refactor required:** Yes before adding selective indexing, caching, or context reuse to production paths.
- **Related controls:** INV-FAIL-002, INV-AUD-001 through INV-AUD-003, TD-047.
- **Tests added:** Profiler stage order, sample counts, prefill-share accounting, repeated-context labeling, and invalid-repeat rejection.
- **Tests still missing:** Runtime-level prefill instrumentation, representative workload profiling, RAM/latency/quality comparison, and cache-integrity tests.
- **Owner:** Nova Aegis
- **Review date:** Before SIFT-like optimization or the Phase 50 mandatory audit.

### TD-047 - Reliability routing comparison remains under experiment

- **Phase:** 47
- **Status:** Adapted as a measurement tool; production adoption deferred
- **Severity:** High
- **What changed:** Added a deterministic fixed-workload replay evaluator comparing baseline routing with reliability-aware routing.
- **What broke or was discovered:** The controlled three-case workload improved synthetic accuracy from `2/3` to `3/3`, but two cases correctly retained baseline routing and the workload is too small for adoption claims.
- **Root cause:** Routing benefit and routing trust are separate properties; caller-supplied history can improve a selected case without establishing calibration, fairness, or resistance to fabricated history.
- **Fix applied or proposed:** Keep replay results inspectable, require unique workload IDs, preserve conservative fallback, and retain reliability outside factual and governance paths.
- **Why this fix:** It creates a reproducible comparison without allowing a promising metric to become autonomous authority.
- **Remaining risk:** The experiment does not measure broad utility, review burden, poisoning resistance, fairness, calibration, durable history, or independent witnessing.
- **Refactor required:** Yes before reliability-driven routing in production or consequential workflows.
- **Related controls:** INV-FAIL-002, INV-HUMAN-001 through INV-HUMAN-003, INV-AUD-001 through INV-AUD-003, TD-046.
- **Tests added:** Fixed workload accuracy comparison, fallback count, route-change count, and invalid workload rejection.
- **Tests still missing:** Representative workload replay, adversarial poisoning, fairness, calibration, review burden, and durable independent history.
- **Owner:** Nova Aegis
- **Review date:** Before reliability-routing adoption or the Phase 50 mandatory audit.

### TD-046 - Reliability-aware routing requires controlled evaluation

- **Phase:** 46
- **Status:** Experiment implemented; adoption deferred
- **Severity:** High
- **What changed:** Added a deterministic reliability-aware routing experiment with fresh-history selection and baseline fallback for missing, stale, tied, ambiguous, or invalid history.
- **What broke or was discovered:** Reliability can produce a routing signal, but caller-supplied operational history is not evidence and is not sufficient to establish routing quality or trustworthiness.
- **Root cause:** Reliability history describes messenger performance, not the truth of a message; uncertain history must not increase authority.
- **Fix applied or proposed:** Keep routing isolated from evidence and assurance, require fresh valid observations, reject invalid outcomes, and retain baseline routing unless one candidate is uniquely supported.
- **Why this fix:** It permits a falsifiable synthetic experiment without allowing reliability to alter claims, provenance, review, approval, or execution authority.
- **Remaining risk:** History is local and caller-supplied; poisoning resistance, calibration, fairness, and durable independent witnessing remain untested.
- **Refactor required:** Yes before reliability-driven routing in production or consequential workflows.
- **Related controls:** INV-FAIL-002, INV-HUMAN-001 through INV-HUMAN-003, INV-AUD-001 through INV-AUD-003, TD-044.
- **Tests added:** Fresh selection, missing/stale fallback, tie fallback, invalid-outcome rejection, and factual-assurance isolation.
- **Tests still missing:** Fixed-workload comparison, routing quality, review burden, poisoning resistance, calibration, fairness, and durable replay.
- **Owner:** Nova Aegis
- **Review date:** Before reliability-driven routing adoption or the next mandatory audit.

### TD-044 - Memory integrity and reliability remain synthetic

- **Phase:** 44
- **Status:** Mitigated for local fail-closed testing; production boundary remains
- **Severity:** High
- **What changed:** Added isolated append-only reliability history and formalized perturbation coverage for stale, poisoned, contradictory, unverified, and incorrectly scoped evidence.
- **What broke or was discovered:** Evidence-integrity degradation is covered by assurance tests, but reliability history has no independent witness and must not influence factual truth.
- **Root cause:** Operational performance history and factual evidence have different authority semantics and require separate stores and contracts.
- **Fix applied or proposed:** Keep `LocalReliabilityMemory` outside evidence, provenance, retrieval scoring, and Praetor assurance; retain fail-closed perturbation tests.
- **Why this fix:** Reliability of a messenger does not establish the truth of a message, and degraded evidence must increase review rather than trigger fallback.
- **Remaining risk:** Reliability records and integrity metadata remain caller-supplied, process-local, and unauthenticated; no routing benefit is established.
- **Refactor required:** Yes before reliability-driven routing, protected memory, or consequential retrieval.
- **Related controls:** INV-FAIL-002, INV-HUMAN-001 through INV-HUMAN-003, INV-AUD-001 through INV-AUD-003, TD-042, TD-043.
- **Tests added:** Reliability isolation and existing perturbation matrix coverage for stale, poisoned, contradictory, unverified, and scoped evidence.
- **Tests still missing:** Reliability poisoning, calibration, fairness, independent witnessing, durable replay, and a controlled routing-benefit experiment.
- **Owner:** Nova Aegis
- **Review date:** Before reliability-driven routing or the Phase 45 mandatory audit.

### TD-043 - Retrieval reconstruction and scope remain synthetic

- **Phase:** 43
- **Status:** Mitigated for deterministic local retrieval; broader evidence boundary remains open
- **Severity:** Medium
- **What changed:** Added optional evidence hierarchy metadata, authority and hierarchy pre-ranking filters, and an inspectable retrieval trace persisted in the retrieval audit event.
- **What broke or was discovered:** The prior retrieval event recorded selected source IDs but could not reconstruct candidate exclusion or ranking inputs.
- **Root cause:** Retrieval stages and ranking decisions were implicit inside the local retriever.
- **Fix applied or proposed:** Record query, scopes, candidate sets, filter stages, ranking scores, and selected identifiers; preserve the existing unscoped API.
- **Why this fix:** A reviewer can reconstruct the tested activation path without relying on model narration, while scope constraints reduce semantically similar cross-boundary candidates before ranking.
- **Remaining risk:** Hierarchy metadata and scopes are caller-supplied, durable retrieval-trace replay is not independently tested, and the experiment does not establish vector, graph, or memory quality.
- **Refactor required:** No immediate refactor for the synthetic experiment; required before trusted external hierarchy or consequential retrieval authority.
- **Related controls:** INV-FAIL-002, INV-AUD-001 through INV-AUD-003, TD-042.
- **Tests added:** Trace reconstruction, authority-before-hierarchy filtering, hierarchy-before-ranking exclusion, and semantic-neighbor adversarial coverage.
- **Tests still missing:** Durable trace replay, authenticated hierarchy metadata, broad-corpus ranking quality, and cross-process retrieval reproducibility.
- **Owner:** Nova Aegis
- **Review date:** Before trusted external retrieval, memory adoption, or the Phase 45 mandatory audit.

### TD-042 - Research integration remains an evidence gate

- **Phase:** 42
- **Status:** Accepted as a documentation-only research phase
- **Severity:** Medium
- **What changed:** Added a structured comparison of MOSS, directory-aware retrieval, Sigma-Mem, SIFT, and memory-integrity perturbations against the Phase 41 baseline.
- **What broke or was discovered:** Literature terminology must not be treated as an architecture gap until retrieval reconstructability, authority scoping, reliability separation, and measured performance are tested directly.
- **Root cause:** Research proposals describe possible capabilities, while Aegis requires observable evidence and governed authority boundaries.
- **Fix applied or proposed:** Require a falsifiable hypothesis, controlled experiment, acceptance criteria, and explicit decision before any Phase 43 implementation.
- **Why this fix:** It prevents paper-driven feature expansion and preserves the rule that remembered content is not evidence by default.
- **Remaining risk:** The current audit trail may not yet contain enough retrieval detail to reconstruct every activated-context decision; this is the first Phase 43 experiment candidate.
- **Refactor required:** No runtime refactor in Phase 42. Required before any adopted retrieval or memory behavior changes.
- **Related controls:** INV-FAIL-002, INV-AUD-001 through INV-AUD-003, AUD40-001 through AUD40-005, TD-041.
- **Tests added:** None; this phase defines experiments rather than runtime behavior.
- **Tests still missing:** Retrieval reconstruction, hierarchy/authority adversarial retrieval, reliability leakage, memory perturbation, and prefill profiling.
- **Owner:** Nova Aegis
- **Review date:** Before Phase 43 implementation and at the Phase 45 mandatory audit.

### TD-041 - Injectable synthetic journal key authority

- **Phase:** 41
- **Status:** Mitigated for synthetic provider isolation; production blocker remains
- **Severity:** High
- **What changed:** Journal key lookup, active-key selection, rotation, and retirement now use an injectable `JournalKeyProvider`; the local provider requires explicit synthetic authority and unknown keys fail closed.
- **What broke or was discovered:** Raw key material and lifecycle decisions were previously owned directly by `SQLiteRecoveryStore`, making the authority boundary implicit.
- **Root cause:** Synthetic persistence needed a replaceable control point before introducing protected key custody or organizational operators.
- **Fix applied or proposed:** Add a provider protocol and local compatibility implementation; preserve legacy constructor options while allowing tests and future integrations to inject a governed provider.
- **Why this fix:** Provider failures remain visible to the transaction boundary, and lifecycle authorization is explicit rather than inferred from store access.
- **Remaining risk:** The default provider is process-local, stores raw secrets, and uses a synthetic authority token. It is not a vault, HSM, rotation service, or independent trust authority.
- **Refactor required:** Yes before real integrations, multi-node deployment, or consequential recovery.
- **Related controls:** INV-FAIL-002, INV-HUMAN-001 through INV-HUMAN-003, INV-AUD-001 through INV-AUD-003, TD-040.
- **Tests added:** Authorized and unauthorized rotation/retirement, key overlap, unknown-key rejection, and provider-backed restart verification.
- **Tests still missing:** Protected custody, organizational identity, provider failover, external witnesses, and distributed lifecycle coordination.
- **Owner:** Nova Aegis
- **Review date:** Before consequential recovery or the next mandatory audit.

### TD-040 - Phase 40 mandatory audit findings

- **Phase:** 40
- **Status:** Accepted for synthetic MVP; blocking before real integrations
- **Severity:** High
- **What changed:** Audited Phases 36-39, including local unified recovery transactions, authenticated/versioned journal keys, key rotation and retirement, restart replay, and concurrent finalization.
- **What broke or was discovered:** No Critical defect was found in the synthetic profile. Protected human authority, protected key custody, distributed transactionality, and independent external evidence remain absent.
- **Root cause:** The implementation intentionally extends local fail-closed proofs before introducing organizational identity, distributed infrastructure, protected secrets, or consequential external systems.
- **Fix applied or proposed:** Continue synthetic-only work. Require protected approval and key services, authenticated workers, distributed transaction coordination, independent external receipts, and real MCP transport controls before integration.
- **Why this fix:** Local tests establish control shape and failure behavior but cannot establish trust across processes, hosts, operators, or external tools.
- **Remaining risk:** Treating the synthetic transaction, HMAC lifecycle, or receipt registry as production authority could permit forged recovery evidence, unauthorized operator action, or inconsistent distributed state.
- **Refactor required:** Yes before consequential recovery, real workers, multi-node deployment, or networked MCP.
- **Related controls:** `docs/audits/phase-40-audit.md`, AUD40-001 through AUD40-005, INV-FAIL-002, INV-HUMAN-001 through INV-HUMAN-003, INV-AUD-001 through INV-AUD-003.
- **Tests added:** Mandatory audit validation plus probes for atomic rollback, key overlap and retirement, wrong-key rejection, tamper rejection, concurrent finalization, single-use approval, and no handler replay.
- **Tests still missing:** Protected key custody, distributed failover, power-loss durability, external receipt witnesses, real transport, and organizational identity.
- **Owner:** Nova Aegis
- **Review date:** Before any corresponding real integration or the next mandatory audit.

### TD-039 - Local recovery durability and concurrency boundary

- **Phase:** 39
- **Status:** Mitigated for single-database synthetic recovery; production blocker remains
- **Severity:** High
- **What changed:** Added a concurrent finalizer probe against `SQLiteRecoveryStore`, proving SQLite transaction serialization permits exactly one approval/task commit and rejects the competing attempt.
- **What broke or was discovered:** The unified transaction boundary needed direct evidence under concurrent recovery attempts, not only sequential success and rollback tests.
- **Root cause:** Recovery authority is single-use and must remain single-use under contention; a wrapper-level test cannot establish that property.
- **Why this fix:** The losing attempt must observe consumed authority and must not mutate task state or create a second completed journal.
- **Remaining risk:** The result covers one local SQLite connection and process. It does not establish behavior under database failover, power loss, multi-host locking, or distributed coordination.
- **Refactor required:** Yes before multi-node or consequential recovery; no before the next synthetic phase.
- **Related controls:** INV-FAIL-002, INV-HUMAN-001 through INV-HUMAN-003, INV-AUD-001 through INV-AUD-003, AUD35-002.
- **Tests added:** Concurrent finalizer race, single-use approval assertion, task terminal-state assertion, and empty-pending-journal assertion.
- **Tests still missing:** Power-loss simulation, database failover, multi-process fault injection, and distributed transaction recovery.
- **Owner:** Nova Aegis
- **Review date:** Before consequential recovery or the next mandatory audit.

### TD-038 - Versioned synthetic journal key lifecycle

- **Phase:** 38
- **Status:** Mitigated for local synthetic key overlap; production blocker remains
- **Severity:** High
- **What changed:** Added persisted journal `key_id` values, trusted-key verification, active-key rotation, overlap during migration, and explicit old-key retirement. Unknown or retired keys block replay.
- **What broke or was discovered:** Phase 37 authenticated journals with an HMAC but had no versioned key identity or controlled rotation semantics.
- **Root cause:** Journal authentication metadata was bound to a single runtime secret rather than a lifecycle-managed key set.
- **Why this fix:** Rotation must preserve verification for existing records during overlap while ensuring retired or unknown keys fail closed.
- **Remaining risk:** Keys remain locally supplied and in-memory; there is no protected key vault, durable key lifecycle, rotation authorization, escrow, or external witness.
- **Refactor required:** Yes before protected audit deployment or consequential recovery; no before the next synthetic phase.
- **Related controls:** INV-FAIL-002, INV-AUD-001 through INV-AUD-003, AUD35-001, AUD35-004.
- **Tests added:** Key-version persistence, overlap verification, new-key signing, retired-key rejection, and active-key retirement rejection.
- **Tests still missing:** Protected key storage, authorized rotation, key destruction policy, restart key loading, and distributed trust convergence.
- **Owner:** Nova Aegis
- **Review date:** Before consequential recovery or the next mandatory audit.

### TD-037 - Authenticated recovery journal remains local

- **Phase:** 37
- **Status:** Mitigated for keyed synthetic replay; production blocker remains
- **Severity:** High
- **What changed:** `SQLiteRecoveryStore` can now authenticate journal payloads with an HMAC key and gateway startup verifies journals through the store boundary before replay.
- **What broke or was discovered:** Phase 36's deterministic digest detected accidental or one-column tampering but could be recomputed by a party able to rewrite the local database.
- **Root cause:** The local journal had integrity metadata without an authenticated witness or protected key authority.
- **Why this fix:** A wrong key or forged payload must block replay and preserve reduced authority rather than silently promote untrusted recovery state.
- **Remaining risk:** The HMAC key is still locally configured and has no protected lifecycle, rotation, external witness, or multi-node authority. Key loss is an availability event and key compromise permits local forgery.
- **Refactor required:** Yes before consequential recovery, protected audit deployment, or multi-node operation; no before the next synthetic phase.
- **Related controls:** INV-FAIL-002, INV-AUD-001 through INV-AUD-003, AUD35-001, AUD35-004.
- **Tests added:** Authenticated journal creation, wrong-key rejection, tamper rejection, startup replay blocking, and no-handler-replay coverage.
- **Tests still missing:** Key rotation, protected key storage, external anchoring, database failover, and distributed verification.
- **Owner:** Nova Aegis
- **Review date:** Before consequential recovery or the next mandatory audit.

### TD-036 - Unified recovery transaction remains local

- **Phase:** 36
- **Status:** Mitigated for single-database synthetic recovery; production blocker remains
- **Severity:** High
- **What changed:** Added `SQLiteRecoveryStore`, which co-locates task state, approvals, and recovery journals and provides one transaction for approval consumption, journal creation, task finalization, and journal completion.
- **What broke or was discovered:** Separate task and approval stores could commit recovery bookkeeping independently, leaving cross-store ambiguity after a process failure.
- **Root cause:** The gateway protocols allowed independently durable stores but had no shared transaction coordinator.
- **Why this fix:** A local SQLite transaction makes the synthetic commit boundary explicit and rolls back authority consumption when task finalization cannot commit.
- **Remaining risk:** The boundary is single-process and single-database. It is not a protected transaction authority, distributed coordinator, authenticated approval service, or independent external evidence witness.
- **Refactor required:** Yes before consequential recovery, multi-node deployment, or production human authority; no before the next synthetic phase.
- **Related controls:** INV-FAIL-002, INV-HUMAN-001 through INV-HUMAN-003, INV-AUD-001 through INV-AUD-003, AUD35-001 through AUD35-003.
- **Tests added:** Unified success, injected transaction rollback, single-use approval preservation, no handler replay, and existing restart/tamper coverage.
- **Tests still missing:** Database failover, distributed coordination, protected authority, transaction durability under power loss, and external witness anchoring.
- **Owner:** Nova Aegis
- **Review date:** Before consequential recovery or the next mandatory audit.

### TD-034 - Recovery journal integrity remains local

- **Phase:** 34
- **Status:** Mitigated for synthetic local replay; production blocker remains
- **Severity:** High
- **What changed:** Recovery journal entries now carry a deterministic digest over journal identity, task identity, target status, and canonical result. Startup verifies that digest before applying any replayed task bookkeeping and audits tampered entries as blocked.
- **What broke or was discovered:** Phase 33 trusted the payload returned by the local journal store. A database-level modification could otherwise promote forged reconciliation data into task state.
- **Root cause:** The journal had durable persistence but no payload-integrity check independent of the SQLite row contents.
- **Why this fix:** A mismatch must reduce authority and preserve `recovery_required`; it must never silently convert untrusted recovery data into a reconciled result.
- **Remaining risk:** The digest is not an independently protected witness or authenticated journal authority. An attacker able to rewrite both payload and digest can still forge local state, and task state remains in a separate store.
- **Refactor required:** Yes before consequential recovery, multi-node deployment, or production audit anchoring; no before synthetic Phase 35 audit work.
- **Related controls:** INV-FAIL-002, INV-AUD-001 through INV-AUD-003, AUD30-001, AUD30-005.
- **Tests added:** SQLite journal tamper injection, digest rejection, startup replay blocking, and no-handler-replay coverage.
- **Tests still missing:** Protected journal authority, external witness anchoring, key rotation, retention, and cross-store transactional coordination.
- **Owner:** Nova Aegis
- **Review date:** Before consequential recovery or the next mandatory audit.

### TD-033 - Recovery journal is local-store scoped

- **Phase:** 33
- **Status:** Mitigated for synthetic restart recovery; production blocker remains
- **Severity:** High
- **What changed:** Added a durable journal entry created atomically with SQLite approval consumption. Gateway startup replays pending task finalization bookkeeping without invoking an external handler, then marks the journal complete.
- **Remaining risk:** Task state and the journal still live in separate stores. A process or database failure can leave either side unavailable, and the journal has no protected external witness or distributed transaction coordinator.
- **Required before production:** Co-locate the recovery state under a protected transaction authority, bind the journal to independently verifiable receipt metadata, and add immutable audit anchoring and retention controls.
- **Tests added:** SQLite crash injection after journal creation, restart replay, idempotent single-use approval behavior, and no-handler-replay verification.
- **Owner:** Nova Aegis
- **Review date:** Before consequential recovery or the next mandatory audit.

### TD-032 - Fail-closed approval revocation and recovery commit ordering

- **Phase:** 32
- **Status:** Mitigated
- **Severity:** High
- **What changed:** Added durable approval revocation to in-memory and SQLite stores, serialized SQLite approval operations, and moved approval consumption before task finalization. A task-store commit failure now consumes authority and leaves the task in `recovery_required`.
- **What broke or was discovered:** Phase 31 updated the task to a reconciled state before consuming the approval. A consume failure could therefore leave a reusable approval after apparent reconciliation; concurrent SQLite approval operations also lacked a connection lock.
- **Root cause:** Approval consumption and task mutation span separate stores without a shared transaction coordinator.
- **Fix applied or proposed:** Treat conditional approval consumption as the fail-closed commit point, reject revoked approvals, and serialize local SQLite approval operations. Preserve unresolved task state when later finalization fails.
- **Why this fix:** Availability loss is safer than granting reusable recovery authority or claiming a reconciliation that was not durably committed.
- **Remaining risk:** Cross-store atomicity is not solved: a crash after approval consumption but before task finalization requires a new approval. There is no protected revocation authority, immutable revocation witness, or two-phase recovery journal.
- **Refactor required:** Yes before consequential recovery or multi-node production deployment; no before synthetic Phase 33 work.
- **Related controls:** AUD30-001, INV-HUMAN-001 through INV-HUMAN-003, INV-AUD-001 through INV-AUD-003, INV-FAIL-002, AUD20-002.
- **Tests added:** Durable revocation, concurrent approval consumption, and injected task-finalization failure proving approval is not reusable while recovery remains required.
- **Tests still missing:** Crash injection between store commits, recovery journal replay, protected revocation identity, immutable anchoring, and production transaction coordination.
- **Owner:** Nova Aegis
- **Review date:** Before consequential recovery or the next mandatory audit.

### TD-031 - Durable synthetic recovery approvals

- **Phase:** 31
- **Status:** Mitigated
- **Severity:** High
- **What changed:** Added injectable in-memory and SQLite approval stores. Recovery approvals survive gateway restart and are atomically consumed once after successful evidence verification and reconciliation.
- **What broke or was discovered:** Phase 29 stored approval authority in a gateway-process dictionary, so restart discarded approvals and separate gateway instances could not share the approval decision.
- **Root cause:** Dual approval was modeled as a signed value but not as durable state with a single-use lifecycle.
- **Fix applied or proposed:** Persist the complete task-bound approval record, expose it through an approval-store boundary, and use conditional SQLite consumption to prevent concurrent or replayed use.
- **Why this fix:** Restart and concurrency must not silently erase or multiply a human authorization decision. Single-use consumption narrows authority after successful reconciliation.
- **Remaining risk:** SQLite is local and not a protected approval authority. Reviewer identity is still synthetic, approvals have no revocation or immutable external witness, and task update plus approval consumption are not one cross-store transaction.
- **Refactor required:** Yes before consequential recovery, multi-node deployment, or production human authority; no before synthetic Phase 32 work.
- **Related controls:** AUD30-001, INV-HUMAN-001 through INV-HUMAN-003, INV-AUD-001 through INV-AUD-003, AUD20-002.
- **Tests added:** Approval survives gateway restart, replay after reconciliation is rejected, and concurrent durable consumption permits exactly one consumer.
- **Tests still missing:** Protected reviewer identity, revocation, approval conflict resolution, cross-store transaction failure injection, retention, and immutable audit anchoring.
- **Owner:** Nova Aegis
- **Review date:** Before consequential recovery or the next mandatory audit.

### TD-030 - Phase 30 mandatory audit findings

- **Phase:** 30
- **Status:** Accepted for synthetic MVP; blocking before real integrations
- **Severity:** High
- **What changed:** Audited Phases 26-29, including verifiable synthetic receipts, durable worker ownership, renewable leases, fencing, and dual-operator recovery approval.
- **What broke or was discovered:** No unresolved correctness defect was found in the synthetic profile. Protected approval state, worker identity, distributed lease authority, and independent external evidence remain local or synthetic.
- **Root cause:** The implementation intentionally proves fail-closed control contracts before introducing organizational identity, distributed infrastructure, protected human authority, or consequential external systems.
- **Fix applied or proposed:** Continue synthetic-only work. Require protected durable approval authority, authenticated workers, distributed fencing, independent external receipts, transactional/cancellable adapters, and actual MCP transport controls before integration.
- **Why this fix:** Local tests establish control shape but cannot establish trust across processes, hosts, operators, or external tools.
- **Remaining risk:** Treating synthetic contracts as production controls could permit unauthorized worker impersonation, non-durable approval, or misrepresented external recovery evidence.
- **Refactor required:** Yes before real workers, consequential recovery, networked MCP, or live external integrations.
- **Related controls:** `docs/audits/phase-30-audit.md`, AUD30-001 through AUD30-007, INV-AUD-001 through INV-AUD-003, INV-HUMAN-001 through INV-HUMAN-003, INV-MCP-001 through INV-MCP-004.
- **Tests added:** Mandatory audit validation and targeted probes for renewal, fencing, recovery approval, evidence binding, and no handler replay.
- **Tests still missing:** Protected production authority, distributed failure modes, external evidence witnesses, transactional tools, real transport, and broader integration controls.
- **Owner:** Nova Aegis
- **Review date:** Before any corresponding real integration or the next mandatory audit.

### TD-029 - Protected recovery authority and dual approval

- **Phase:** 29
- **Status:** Mitigated
- **Severity:** High
- **What changed:** Added a signed, task-bound recovery approval. A distinct operator with the recovery scope must approve the exact resolution, receipt ID, and result hash before the original task owner can reconcile. Approvals are single-use after successful receipt verification.
- **What broke or was discovered:** Phase 26 independently verified execution receipts but still allowed one owner-operator to complete recovery without a second human authorization decision.
- **Root cause:** Evidence integrity and authority separation were modeled as separate concerns; reconciliation had no dual-control boundary.
- **Fix applied or proposed:** Require independent operator approval, bind it cryptographically to the task and proposed outcome, reject owner self-approval and mismatches, and consume the approval only after all evidence checks pass.
- **Why this fix:** Recovery resolves ambiguous external effects and must require separated human authority rather than a single authenticated override.
- **Remaining risk:** Approval state is process-local and not durable; there is no organizational reviewer identity, quorum policy, protected approval store, revocation, expiration service, separation-of-duty administration, or immutable approval witness.
- **Refactor required:** Yes before consequential recovery or production deployment; no before synthetic Phase 30 audit work.
- **Related controls:** INV-HUMAN-001 through INV-HUMAN-003, INV-AUD-001 through INV-AUD-003, INV-ID-002, AUD20-002, AUD25-001.
- **Tests added:** Independent approver success, owner self-approval rejection, evidence/approval binding, and no handler replay after dual-controlled reconciliation.
- **Tests still missing:** Durable approval persistence, reviewer authentication, approval revocation, quorum/policy versioning, conflicting approvals, and protected audit anchoring.
- **Owner:** Nova Aegis
- **Review date:** Phase 30 audit or before real recovery integration.

### TD-028 - Renewable worker leases and fencing

- **Phase:** 28
- **Status:** Mitigated
- **Severity:** High
- **What changed:** Added lease renewal, monotonic fencing tokens, and ownership/fence checks to task completion. Gateway renewal emits an audit event; stale workers cannot renew or publish results after a newer claim.
- **What broke or was discovered:** Phase 27 claims expired safely but had no heartbeat path or fencing against an old worker continuing after lease loss.
- **Root cause:** Worker ownership was represented by a worker ID and deadline without generation semantics or renewal protocol.
- **Fix applied or proposed:** Increment a durable fence on each claim, require the current fence for renewal and completion, and reject expired or superseded generations.
- **Why this fix:** Lease expiry alone does not stop a delayed worker from attempting a late write; fencing turns stale execution into a denied operation.
- **Remaining risk:** No authenticated worker identity, automatic heartbeat supervisor, protected distributed store, clock strategy, queue fairness, or external fencing authority exists. A stale handler may still run physically, but its result is rejected and recovery is required.
- **Refactor required:** Yes before real workers or multi-node production deployment; no before the Phase 30 audit.
- **Related controls:** INV-FAIL-002, INV-HUMAN-001, INV-LOOP-001, INV-MCP-001 through INV-MCP-004, AUD20-002.
- **Tests added:** Gateway renewal, stale renewal rejection, monotonic fencing, stale completion rejection, and existing concurrent claim coverage.
- **Tests still missing:** Crash injection, renewal loss during external execution, database failover, worker authentication, and distributed lease contention.
- **Owner:** Nova Aegis
- **Review date:** Phase 30 audit or before real worker integration.

### TD-027 - Durable synthetic worker leases

- **Phase:** 27
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Added worker identity, atomic task claims, expiring leases, ownership-checked completion, and lease-expiry quarantine in both in-memory and SQLite task stores. `run_task` now requires an explicit worker ID.
- **What broke or was discovered:** Status-only `in_progress` state could not prove which worker owned a task, and separate gateway instances had no durable claim boundary.
- **Root cause:** Phase 22-23 modeled worker execution and restart recovery without persisted ownership or lease semantics.
- **Fix applied or proposed:** Claim pending tasks in the store with a worker ID and lease deadline. Reject competing claims and stale completion. Convert expired in-progress leases to `recovery_required` so uncertain external effects are not replayed.
- **Why this fix:** Worker concurrency must reduce authority on ambiguity; only an active owner may commit a terminal result.
- **Remaining risk:** No lease renewal, fencing token, heartbeat, distributed queue, protected lease authority, crash injection, or multi-node database deployment exists. A worker may continue running after lease loss, but its result is rejected and recovery is required.
- **Refactor required:** Yes before real workers, long-running tools, or multi-process production deployment; no before synthetic Phase 28 work.
- **Related controls:** High-level architecture Synthetic MCP Gateway Contract, INV-FAIL-002, INV-HUMAN-001, INV-LOOP-001, INV-MCP-001 through INV-MCP-004.
- **Tests added:** Shared SQLite claim race, competing worker rejection, expired lease quarantine, stale completion rejection, and existing worker lifecycle regression coverage.
- **Tests still missing:** Lease renewal and fencing, crash injection during handler execution, distributed contention under database failure, worker authentication, queue fairness, and production coordination.
- **Owner:** Nova Aegis
- **Review date:** Phase 30 audit or before real worker integration.

### TD-026 - Verifiable external recovery receipts

- **Phase:** 26
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Added `ExternalExecutionReceipt`, `ExternalReceiptVerifier`, and `LocalExternalReceiptRegistry`. Recovery reconciliation now requires a signed receipt bound to the task, tool, owner, gateway audience, canonical parameters, resolution, and result hash.
- **What broke or was discovered:** Phase 24 required a receipt ID but accepted caller-supplied receipt identity and result without independent verification.
- **Root cause:** Recovery evidence was modeled as metadata, not as a verifiable execution record.
- **Fix applied or proposed:** Introduce an injectable verifier boundary and fail closed when the verifier is absent, the receipt is unknown/expired/invalid, or task, parameters, result, or resolution do not match.
- **Why this fix:** Recovery authority must be anchored to evidence with integrity and operation binding, not an unstructured external ID.
- **Remaining risk:** The verifier is a local synthetic registry, not a real tool receipt service. No public-key trust, receipt persistence, revocation, witness anchoring, external query path, delegated reviewer, dual approval, or conflict handling exists.
- **Refactor required:** Yes before consequential recovery or real worker deployment; no before synthetic Phase 27 work.
- **Related controls:** AUD25-001, INV-HUMAN-001 through INV-HUMAN-003, INV-EVID-003, INV-EVID-004, INV-AUD-001 through INV-AUD-003.
- **Tests added:** Unknown receipt, blank receipt, result-hash mismatch, resolution mismatch, signed valid receipt, and no handler replay after reconciliation.
- **Tests still missing:** Receipt persistence/revocation, public-key verification, conflicting receipts, external receipt query failure, operator approval workflow, receipt tamper forensics, and real tool adapter integration.
- **Owner:** Nova Aegis
- **Review date:** Phase 30 audit or before real recovery integration.

### TD-025 - Phase 25 mandatory audit findings

- **Phase:** 25
- **Status:** Accepted for synthetic MVP; blocking before real integrations
- **Severity:** Medium
- **What changed:** Audited Phases 21-24 task admission, synthetic worker execution, durable local recovery, and scoped reconciliation.
- **What broke or was discovered:** No Critical or High defect was confirmed. Recovery receipt references and task-worker controls remain local/synthetic, and Foundry Local SDK availability does not constitute provider integration.
- **Root cause:** The architecture intentionally proves fail-closed local contracts before adding external systems, real workers, or live models.
- **Fix applied or proposed:** Continue synthetic-only work; require independently verifiable receipts, protected recovery authority, durable worker ownership, actual MCP transport controls, and prior integration prerequisites before scope expansion.
- **Why this fix:** Passing local task tests do not establish independent external execution evidence or production worker safety.
- **Remaining risk:** Real recovery could be misrepresented by unverified receipts; local SQLite cannot provide distributed worker coordination; networked MCP and live semantic/model paths remain unimplemented.
- **Refactor required:** Yes before real integrations; no before synthetic Phase 26.
- **Related controls:** `docs/audits/phase-25-audit.md`, INV-AUD-001 through INV-AUD-003, INV-HUMAN-001 through INV-HUMAN-003, INV-LOOP-001, INV-MCP-001 through INV-MCP-004.
- **Tests added:** Mandatory audit probes for cancellation, restart quarantine, scoped reconciliation, and no handler replay; 73-test regression baseline.
- **Tests still missing:** Independent receipt validation, dual approval, recovery policy/versioning, durable worker queue/leases, distributed task coordination, actual MCP transport/OAuth, live semantic isolation, and protected production stores.
- **Owner:** Nova Aegis
- **Review date:** Phase 30 audit or before any real integration.

### TD-024 - Scoped task recovery reconciliation

- **Phase:** 24
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Added explicit recovery reconciliation for `recovery_required` tasks. Resolution requires the original authenticated owner, operator role, `mcp:task:reconcile` scope, a valid terminal outcome, and a non-empty external receipt reference. Resolution stores evidence and does not replay the task handler.
- **What broke or was discovered:** Phase 23 safely quarantined interrupted work but left no controlled way to document an externally confirmed outcome, causing permanent unresolved state or unsafe manual bypass pressure.
- **Root cause:** Recovery handling had no distinct reconciliation authority, scope, or evidence contract.
- **Fix applied or proposed:** Add scoped owner-bound reconciliation for `completed` or `abandoned` outcomes and audit both blocked and successful attempts. Return stored reconciliation evidence rather than execute again.
- **Why this fix:** An interrupted action must be resolved by evidence and explicit authority, not by automatic retry or an unstructured override.
- **Remaining risk:** Receipt references are caller-supplied and not independently verified; no delegated reviewer, dual approval, policy version, signature, external tool query, retention rule, immutable resolution history, or conflict handling exists.
- **Refactor required:** Yes before consequential recovery or real worker deployment; no before the Phase 25 audit.
- **Related controls:** High-level architecture Section 17, INV-HUMAN-001 through INV-HUMAN-003, INV-AUD-001 through INV-AUD-003, INV-ID-002, AUD20-002.
- **Tests added:** Missing recovery scope, missing receipt, authorized reconciliation, durable reconciled state, reconciliation audit, and no handler replay.
- **Tests still missing:** Independent receipt verification, delegated/dual approval, recovery policy versioning, conflicting receipt handling, external receipt query, and immutable audit history.
- **Owner:** Nova Aegis
- **Review date:** Phase 25 audit or before real recovery integration.

### TD-023 - Durable local task recovery

- **Phase:** 23
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Added `SQLiteTaskStore` and injected task-store support into the MCP Gateway. Completed task results now survive gateway restart. A persisted `in_progress` task becomes `recovery_required` on store open and returns `REVIEW` without handler replay.
- **What broke or was discovered:** Phase 22 task state, replay protection, and terminal results were process-local; restart lost completed task results and could not distinguish interrupted work from a task that had never run.
- **Root cause:** The gateway lifecycle used in-memory dictionaries rather than durable task records.
- **Fix applied or proposed:** Persist task ID, owner, expiry, status, result, and update time in local SQLite. Quarantine interrupted work as `recovery_required` rather than retrying it automatically.
- **Why this fix:** After a crash, execution state is uncertain. Treating uncertainty as permission to replay can duplicate a consequential action.
- **Remaining risk:** SQLite is local-only and single-node. No worker lease/heartbeat, recovery authorization, independent external receipt, result verification, task payload persistence, durable credential/token state, encryption, access control, concurrency coordination, or distributed queue exists.
- **Refactor required:** Yes before real workers, real MCP Tasks, or multi-process deployment; no before synthetic Phase 24 work.
- **Related controls:** High-level architecture Section 17, AUD20-002, INV-AUD-001 through INV-AUD-003, INV-FAIL-002, INV-HUMAN-001, INV-LOOP-001.
- **Tests added:** Completed result survives restart without handler replay; interrupted `in_progress` task becomes `recovery_required` and requires `REVIEW`.
- **Tests still missing:** Worker lease expiry, crash injection during handler execution, authorized reconciliation, external receipt validation, database corruption, concurrent gateways, task payload persistence, and distributed queue semantics.
- **Owner:** Nova Aegis
- **Review date:** Phase 25 audit or before real worker integration.

### TD-022 - Synthetic asynchronous task state machine

- **Phase:** 22
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Added explicit `submit_task` and `run_task` contracts over the local MCP task lifecycle. Handler failure now produces an audited terminal `failed` state; running tasks cannot be cancelled, preventing a cancellation/execution race from creating contradictory state.
- **What broke or was discovered:** The Phase 21 lifecycle had no explicit worker boundary, and handler exceptions could escape while the finalizer returned the task to `pending`.
- **Root cause:** The initial task contract modeled admission and cancellation but not worker execution ownership or terminal failure handling.
- **Fix applied or proposed:** Claim a pending task before handler execution, expose worker execution through `run_task`, mark handler exceptions `failed`, and allow cancellation only while pending.
- **Why this fix:** Asynchronous work needs explicit ownership and terminal states before it can be made durable or distributed. Retrying a failed/ambiguous task by default could duplicate a consequential action.
- **Remaining risk:** No actual asynchronous scheduler, durable queue, worker identity, lease heartbeat, restart recovery, timeout, cancellation signal for running work, task-result persistence, resource metering, distributed locking, or operator reconciliation exists.
- **Refactor required:** Yes before real workers, MCP Tasks, or long-running execution; no before synthetic Phase 23 work.
- **Related controls:** High-level architecture Section 17, AUD20-002, AUD20-005, INV-LOOP-001, INV-FAIL-002, INV-HUMAN-001.
- **Tests added:** Explicit worker run, handler failure to terminal state, task failure audit, and cancellation race rejection while running.
- **Tests still missing:** Durable restart recovery, worker lease expiry/reclaim, crash injection, running-task cancellation protocol, scheduler fairness, per-tool runtime budgets, result retention, and distributed concurrency.
- **Owner:** Nova Aegis
- **Review date:** Phase 25 audit or before real worker integration.

### TD-021 - Synthetic task quota and cancellation boundary

- **Phase:** 21
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Added a local MCP task lifecycle with `pending`, `in_progress`, `completed`, `cancelled`, and expiry handling. The gateway now enforces a per-user active-task quota and permits cancellation only before execution.
- **What broke or was discovered:** Signed task-state integrity and replay protection did not prevent an attacker from creating unbounded pending tasks or invoking a state that had been cancelled in the server-side lifecycle.
- **Root cause:** Phase 19 modeled task integrity but not task admission, lifecycle state, or resource limits.
- **Fix applied or proposed:** Track a local task record for each signed task, reject creation beyond the user quota, reject cancelled/non-active state before invocation, and record task creation/cancellation audit events.
- **Why this fix:** Stateless envelopes still need bounded server-side resource admission. A valid signature must not outlive cancellation authority.
- **Remaining risk:** The lifecycle is process-local and synchronous. No durable queue, distributed lease, task ownership transfer, timeout, running-task interruption, cancellation race handling, memory/CPU accounting, per-tool cost budget, or operator workflow exists.
- **Refactor required:** Yes before real MCP Tasks or long-running work; no before synthetic Phase 22 work.
- **Related controls:** High-level architecture Section 17, AUD20-002, AUD20-005, INV-LOOP-001, INV-HUMAN-001, MCP 2026 Tasks security considerations.
- **Tests added:** Per-user active-task quota exhaustion, pending-task cancellation, cancelled signed-state invocation rejection, and lifecycle audit events.
- **Tests still missing:** Durable restart recovery, distributed quota/lease behavior, cancellation during execution, timeout enforcement, quota bypass concurrency, resource metering, task-result retention, and real Tasks extension interoperability.
- **Owner:** Nova Aegis
- **Review date:** Phase 25 audit or before real MCP Tasks integration.

### TD-019 - Stateless MCP task and routing integrity

- **Phase:** 19
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Added signed, client-held synthetic `McpTaskState` envelopes bound to user, role, audience, tool, and canonical parameters. Added stateless gateway request validation for task-state integrity, exact `Mcp-Method`/`Mcp-Name` header-body consistency, untrusted `_meta` handling, and process-local replay protection that returns a stored result instead of re-executing a completed task.
- **What broke or was discovered:** Phase 18 lacked an executable control for the June 2026 stateless-era risks: client-held state tampering, gateway routing desynchronization, metadata-driven privilege confusion, and replay of a valid signed task state. The replay flaw was found during Phase 20 audit preparation and fixed before the gate.
- **Root cause:** The initial synthetic gateway modeled access-token authorization only, not stateless task continuation or gateway routing boundaries.
- **Fix applied or proposed:** Sign task state server-side, bind it to the current credential and operation, validate it on every request, return stored results for completed task IDs, reject header/body mismatch, and reject metadata that purports to establish identity or authorization.
- **Why this fix:** Client-held state and metadata are untrusted input. A gateway must not let either silently change identity, routing, or tool scope.
- **Remaining risk:** No real 2026-07-28 MCP transport, durable task state machine, task quotas/cancellation, distributed replay/revocation registry, Apps sandbox/XSS policy, HTTP header canonicalization, or proxy/server desync testing exists.
- **Refactor required:** Yes before real MCP 2026-07-28 integration; no before synthetic Phase 20 audit.
- **Related controls:** High-level architecture Section 17, AUD15-005, INV-MCP-001 through INV-MCP-004, INV-FAIL-003, June 25, 2026 MCP security analysis.
- **Tests added:** Valid signed stateless request, task-state operation tampering, header/body desynchronization, benign metadata, authorization metadata poisoning, and replay return without duplicate execution.
- **Tests still missing:** Stateful task lifecycle, cancellation, quotas, replay control, metadata namespace policy, Apps security, HTTP/proxy behavior, and real OAuth/transport integration.
- **Owner:** Nova Aegis
- **Review date:** Phase 20 audit or before real MCP integration.

### TD-018 - Synthetic MCP Gateway security boundary

- **Phase:** 18
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Added an in-process `McpGateway` contract with HTTPS resource identity, gateway-issued audience-bound tokens, backing-credential revalidation, per-tool scopes, role-limited discovery, exact request schemas, server-side Praetor checks, and structured allow/deny audit events. Phase 18 documentation was corrected to distinguish the older authorization guidance from the June 25, 2026 analysis of the 2026-07-28 revision.
- **What broke or was discovered:** Tool authorization had only an application-local path; there was no independently testable gateway layer to reject bypassed, wrong-audience, over-scoped, malformed, revoked-identity, or unregistered-tool requests.
- **Root cause:** MCP was previously an architecture boundary without an executable enforcement contract.
- **Fix applied or proposed:** Implement a synthetic server-owned gateway contract. Never accept token passthrough, require the exact gateway audience, and validate the backing credential for every request.
- **Why this fix:** It exercises the security shape required by MCP authorization guidance without introducing a networked service or claiming OAuth/HTTP conformance.
- **Remaining risk:** This is not a real MCP transport, OAuth 2.1 resource server, Protected Resource Metadata endpoint, PKCE flow, consent system, SSRF defense, stateless task-state integrity layer, `_meta` trust boundary, header/body consistency validator, Apps sandbox, task quota system, external server inventory, tool response validator, or real execution-receipt adapter.
- **Refactor required:** Yes before real MCP or multi-user deployment; no before continued synthetic gateway hardening.
- **Related controls:** High-level architecture Sections 15-17, AUD15-005, INV-MCP-001 through INV-MCP-004, INV-ID-001, INV-ID-002, MCP authorization/security guidance, and June 25, 2026 analysis of the 2026-07-28 revision.
- **Tests added:** Authorized scoped call, wrong audience, valid narrow-scope denial, schema rejection, revoked identity, role-limited discovery, unknown tool, and audit events.
- **Tests still missing:** HTTP authorization headers, OAuth 2.1/PKCE, Protected Resource Metadata, redirect/state validation, consent, token rotation/storage, SSRF, stateless task-state tampering, `_meta` poisoning, header/body desynchronization, Apps sandboxing/XSS, task quota abuse, tool response validation, real server compromise, and network isolation.
- **Owner:** Nova Aegis
- **Review date:** Phase 20 audit or before real MCP integration.

### TD-017 - Idempotent execution receipt and recovery boundary

- **Phase:** 17
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Added SQLite-backed idempotency-keyed execution receipts with `authorized` and `completed` states. Synthetic execution persists completion before reporting success, returns stored results without duplicate execution, and routes incomplete receipts to `REVIEW` with a recovery event.
- **What broke or was discovered:** Phase 14 preflight prevented execution without authorization audit, but a crash or completion-persistence failure after the tool call could still leave the operation ambiguous.
- **Root cause:** The audit event chain had no durable operation-level receipt tying authorization, execution identity, and completion result together.
- **Fix applied or proposed:** Persist a receipt before execution; reject reuse for a different operation; complete the receipt before success; never automatically replay an `authorized` but incomplete receipt.
- **Why this fix:** Ambiguous external state must reduce authority. Retrying blindly can duplicate a consequential action.
- **Remaining risk:** The receipt records Nova Aegis state, not independent external-tool state. No real MCP execution receipt, transactional adapter, reconciliation workflow, operator resolution, concurrency control, or crash-injection harness exists.
- **Refactor required:** Yes before real tools or consequential execution; no before synthetic Phase 18 work.
- **Related controls:** High-level architecture Section 21, AUD15-002, INV-AUD-001 through INV-AUD-003, INV-FAIL-002, INV-HUMAN-001, STRIDE-AI repudiation.
- **Tests added:** Duplicate completion returns stored result, pending receipt requires review, completion persistence failure, and idempotency-key operation mismatch.
- **Tests still missing:** Real tool receipt validation, crash recovery across process restart, reconciliation authorization, concurrent key contention, transactional MCP adapter, and durable operator workflow.
- **Owner:** Nova Aegis
- **Review date:** Phase 20 audit or before real tool integration.

### TD-016 - Phase 15 debt reconciliation

- **Phase:** 16
- **Status:** Mitigated
- **Severity:** Low
- **What changed:** Reconciled the active debt view after the Phase 15 audit. TD-014 is resolved for the synthetic flow; unresolved identity, gateway, evidence, audit-completion, semantic-evaluator, and Agent K scope items are consolidated in TD-015 and AUD15-002 through AUD15-006.
- **What broke or was discovered:** Several older entries retained review dates already reached by the Phase 15 audit, and Phase 11-12 historical remaining-risk text no longer reflected the implemented Agent K and response-path integration.
- **Root cause:** The ledger preserves phase history while implementation phases advanced faster than the original review-date wording.
- **Fix applied or proposed:** Keep historical records, but use TD-015 as the current security disposition and update stale Phase 11-12 implementation references below. Reassess all unresolved items at Phase 20 or before any real integration.
- **Why this fix:** A debt ledger must distinguish historical discovery context from active, actionable risk.
- **Remaining risk:** Duplicate historical entries can still require human interpretation; a future ledger normalization should add explicit `superseded by` metadata if the record volume grows.
- **Refactor required:** No before synthetic Phase 16 work; reassess at Phase 20 audit.
- **Related controls:** Phase 15 audit, Debt Rules 4-7.
- **Tests added:** Full 53-test regression suite remains passing.
- **Tests still missing:** No code test required; future ledger consistency checks could validate overdue review dates and supersession links.
- **Owner:** Nova Aegis
- **Review date:** Phase 20 audit.

### TD-015 - Phase 15 mandatory audit findings

- **Phase:** 15
- **Status:** Accepted for synthetic MVP; blocking before real integrations
- **Severity:** Medium
- **What changed:** Audited Phases 11-14, including hybrid assurance, Agent K traces, response fusion, and governed durable-audit integration.
- **What broke or was discovered:** Found a High audit-ordering weakness in Phase 14: execution could precede the completion audit append. It was fixed before the audit by requiring `tool_authorized` preflight recording.
- **Root cause:** Audit was initially post-execution observability, rather than a fail-closed authorization condition.
- **Fix applied or proposed:** Keep the repaired preflight gate; add crash recovery, transactional adapters, execution receipts, and completion reconciliation before consequential tools.
- **Why this fix:** An audit outage must reduce authority, not permit execution without an authorization record.
- **Remaining risk:** A crash after execution can still omit the completion record; semantic evaluation, Agent K, identity, evidence, MCP, and audit storage remain synthetic or local-only.
- **Refactor required:** Yes before real integrations; no before synthetic Phase 16.
- **Related controls:** `docs/audits/phase-15-audit.md`, INV-AUD-001 through INV-AUD-004, INV-GOV-002 through INV-GOV-004, INV-MCP-001, STRIDE-AI tampering and repudiation.
- **Tests added:** Mandatory audit probes plus durable audit preflight failure, Agent K trace, and hybrid response fusion suites.
- **Tests still missing:** Transactional tool adapters, crash recovery, real MCP enforcement, live evaluator isolation, source verification, protected audit storage, memory, network enforcement, and concurrency.
- **Owner:** Nova Aegis
- **Review date:** Phase 20 audit or before any real integration.

### TD-014 - Governed durable audit integration

- **Phase:** 14
- **Status:** Resolved for synthetic tool flow
- **Severity:** High
- **What changed:** Added end-to-end integration tests for `NovaAegisMVP` with `SQLiteAuditLog` and added a required `tool_authorized` audit preflight before synthetic execution.
- **What broke or was discovered:** The prior flow executed a synthetic tool before writing its `tool_executed` event. An audit failure at that point could leave an executed action without a completed execution record.
- **Root cause:** Audit was treated as post-execution observability instead of part of the authorization path.
- **Fix applied or proposed:** Record authorization intent before execution and return `FAIL` without executing when that append fails. Continue to write the execution result after successful action completion.
- **Why this fix:** It enforces INV-AUD-003: audit subsystem failure cannot increase authority or permit execution.
- **Remaining risk:** The preflight guarantees an authorization record but a process failure after execution can still prevent the completion/result event. Durable recovery, transactional tool adapters, external anchoring, and real MCP enforcement are not implemented.
- **Refactor required:** Yes before consequential tools or production audit guarantees; no before the Phase 15 audit.
- **Related controls:** High-level architecture Section 21, INV-AUD-001, INV-AUD-002, INV-AUD-003, INV-FAIL-002, STRIDE-AI repudiation.
- **Tests added:** Durable response/tool lifecycle, blocked tool audit, and preflight audit failure blocks execution.
- **Tests still missing:** Crash recovery between execution and completion record, concurrent audit/tool operations, transactional MCP adapters, real storage outage, and result verification.
- **Owner:** Nova Aegis
- **Review date:** Phase 15 audit and before consequential tool integration.

### TD-013 - Agent K deterministic evidence trace

- **Phase:** 13
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Extracted response evidence checks into first-class `AgentK`, which returns an immutable ordered rule trace and deterministic evaluator decision. Praetor defaults to Agent K and audits its stable rule reason.
- **What broke or was discovered:** Deterministic response rules were embedded in Praetor, so their source and evaluation order were not independently inspectable.
- **Root cause:** The documented Agent K boundary had not yet been represented as an executable component.
- **Fix applied or proposed:** Define fixed evidence rule identifiers and return the complete trace, with the first non-PASS rule controlling the deterministic outcome.
- **Why this fix:** Deterministic reproducibility is useful only when a human can inspect which rule produced the decision.
- **Remaining risk:** Agent K covers response evidence only. It does not yet trace tool authorization, policy versions, schemas, risk, delegation, rule signatures, rule persistence, rule conflicts, or administrative changes.
- **Refactor required:** Yes before policy-managed production governance; no before additional synthetic rule families.
- **Related controls:** High-level architecture Section 13, threat model Sections 19-21, INV-GOV-001 through INV-GOV-004, INV-EVID-003 through INV-EVID-006.
- **Tests added:** Ordered valid-evidence trace, first blocking provenance rule, conflicting-claim rule, and default Praetor delegation/audit reason.
- **Tests still missing:** Tool/policy rule traces, rule versioning, signed rule bundles, mutation testing, rule-conflict testing, and persistent rule audit.
- **Owner:** Nova Aegis
- **Review date:** Phase 15 audit or before policy-managed governance.

### TD-012 - Praetor response-path hybrid integration

- **Phase:** 12
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Integrated injected deterministic and semantic evaluators into `Praetor.evaluate_response_with_trace`. The response path now fuses both verdicts and audits evaluator statuses and reasons with the final assurance decision.
- **What broke or was discovered:** The Phase 11 fusion contract was standalone, so response assurance neither invoked both evaluators nor retained their separate verdicts in the audit trail.
- **Root cause:** The original Praetor response path performed deterministic evidence checks inline and returned a single untraceable decision.
- **Fix applied or proposed:** Route response assurance through labeled evaluator contracts and `HybridAssurance`. Convert evaluator exception or mislabeled output to `REVIEW` before fusion.
- **Why this fix:** A semantic evaluator must be independently observable and unable to convert uncertainty, failure, or injection into an approved response.
- **Remaining risk:** The semantic evaluator is a synthetic default; Agent K is now separately implemented for evidence rules, but no evaluator isolation, prompt construction, suppression layer, confidence calibration, or real model/provider lifecycle exists.
- **Refactor required:** Yes before live semantic evaluation or any claim of production hybrid assurance; no before continued synthetic governance work.
- **Related controls:** High-level architecture Section 13, threat model Sections 19-21, INV-GOV-001 through INV-GOV-004, INV-AUD-001, INV-AUD-002.
- **Tests added:** Response-path semantic concern, deterministic hard failure, semantic evaluator outage, evaluator-kind mismatch, and audit-verdict assertions.
- **Tests still missing:** Live semantic evaluator isolation, evaluator prompt injection, repeated-run behavior, evaluator model provenance, and tool-path hybrid fusion.
- **Owner:** Nova Aegis
- **Review date:** Phase 20 audit or before live semantic evaluator integration.

### TD-011 - Fixed hybrid assurance fusion contract

- **Phase:** 11
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Added typed semantic and deterministic evaluation contracts plus `HybridAssurance`, a fixed fusion boundary that permits `PASS` only when both independent evaluators pass, returns `REVIEW` on disagreement or uncertainty, and preserves deterministic `FAIL` as terminal.
- **What broke or was discovered:** Praetor had one undifferentiated decision type, so it could not represent evaluator provenance or mechanically prevent unsafe disagreement fusion.
- **Root cause:** The hybrid architecture was documented but no executable fusion contract existed.
- **Fix applied or proposed:** Use evaluator-labeled immutable decisions and explicit fixed rules; reject mislabeled evaluator inputs. The local research PDF is hash-recorded as design input, not treated as authority.
- **Why this fix:** It makes the Phase 10 hybrid-fusion requirement testable without connecting a live semantic model or weakening deterministic governance.
- **Remaining risk:** No live semantic evaluator, evaluator isolation, suppression layer, confidence calibration, or production-integrated tool fusion exists. The report’s judge configuration metadata is incomplete and its findings are not independently reproduced here.
- **Refactor required:** Yes before real semantic evaluation or production governance; no before further synthetic hybrid testing.
- **Related controls:** High-level architecture Section 13, threat model Sections 19-21, INV-GOV-002, INV-GOV-003, INV-GOV-004, STRIDE-AI AI-specific manipulation.
- **Tests added:** Dual-PASS, semantic misrepresentation, structural-tag omission, hard safety boundary, evaluator injection, semantic review, and evaluator-label mismatch.
- **Tests still missing:** Live evaluator isolation, stochastic repeatability, semantic prompt injection, integrated response/tool fusion, confidence thresholds, and human-review workflow.
- **Owner:** Nova Aegis
- **Review date:** Phase 20 audit or before live semantic evaluator integration.

### TD-010 - Phase 10 mandatory audit findings

- **Phase:** 10
- **Status:** Accepted for synthetic MVP; blocking before real integrations
- **Severity:** Medium
- **What changed:** Audited Phases 6-9 across evidence assurance, STRIDE-AI/ATLAS coverage, durable audit, identity, policy integrity, source, tests, and invariant behavior.
- **What broke or was discovered:** No Critical or High issue was confirmed for the synthetic profile, but identity, policy, audit, MCP, and provenance controls remain process-local or application-only.
- **Root cause:** The implementation is still a deliberately bounded local proof and retains compatibility paths that are not trusted security roots.
- **Fix applied or proposed:** Continue synthetic-only work; block real data, real tools, and production inference until AUD10-001 through AUD10-005 are re-audited at their actual integration boundaries.
- **Why this fix:** It preserves momentum without treating passing unit tests as evidence of production security.
- **Remaining risk:** A deployment outside the evaluated profile would inherit unprotected identity, policy, audit, MCP, and provenance boundaries.
- **Refactor required:** Yes before real integrations; no before synthetic Phase 11.
- **Related controls:** `docs/audits/phase-10-audit.md`, INV-ID-001, INV-ID-002, INV-AUD-003, INV-MCP-001, INV-EVID-004, STRIDE-AI and MITRE ATLAS crosswalk.
- **Tests added:** Mandatory audit validation, direct identity/policy/audit probes, and the Phase 9 identity-policy suite.
- **Tests still missing:** Enterprise identity, protected policy administration, gateway enforcement, external audit anchoring, verified provenance, memory, graph, model supply chain, network isolation, and concurrency.
- **Owner:** Nova Aegis
- **Review date:** Phase 15 audit or before any real integration.

### TD-009 - Synthetic identity and policy integrity boundary

- **Phase:** 9
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Added `IdentityAuthority` and short-lived `IdentityCredential` contracts with issuer membership, signature, expiry, and revocation checks. Added Praetor policy fingerprints and fail-closed detection of post-load policy mutation.
- **What broke or was discovered:** Tool authorization previously accepted caller-supplied `user_id` and `role`, and mutable in-memory policies had no integrity signal.
- **Root cause:** The MVP modeled identity and policy as function inputs and convenience dictionaries rather than controlled security boundaries.
- **Fix applied or proposed:** Preserve legacy calls for synthetic compatibility, but provide an explicit credential path that resolves server-issued authorization context before Praetor evaluation. Refuse execution when policy integrity changes.
- **Why this fix:** It demonstrates the authority boundary and tests spoofing, revocation, expiry, confused-deputy resistance, and policy tampering without introducing an unverified external identity dependency.
- **Remaining risk:** The issuer secret is process-local; credentials are not externally authenticated; policy fingerprints are not externally anchored; legacy caller-supplied context remains available for the synthetic MVP; and no real MCP gateway enforces the contract.
- **Refactor required:** Yes before multi-user deployment, real MCP tools, or production authorization; no before the Phase 10 audit.
- **Related controls:** High-level architecture Section 21A, threat model identity spoofing, policy tampering, confused deputy, INV-ID-001, INV-ID-002, INV-AUTH-002, INV-AUTH-003.
- **Tests added:** Issued identity authorization, forged credential rejection, revocation, expiry, policy mutation, and direct fingerprint verification.
- **Tests still missing:** External identity integration, credential transport protection, key rotation, policy version persistence, delegated authority constraints, gateway-side enforcement, and concurrent revocation.
- **Owner:** Nova Aegis
- **Review date:** Phase 10 audit and before any real integration.

### TD-008 - Durable tamper-evident audit boundary

- **Phase:** 8
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Added `SQLiteAuditLog`, a dependency-free local durable audit store with event allowlisting, transactional persistence, deterministic JSON serialization, and a SHA-256 predecessor hash chain. Exported it through the public package API.
- **What broke or was discovered:** The prior audit implementation lost all events when the process ended and provided no integrity signal after database modification.
- **Root cause:** The initial vertical slice intentionally stored audit events only in memory.
- **Fix applied or proposed:** Preserve the existing audit interface while allowing `NovaAegisMVP` to receive a SQLite-backed store. Verify the chain before reads and before appends; refuse operations after integrity failure.
- **Why this fix:** It establishes a small local persistence boundary without introducing a service dependency, while making silent post-write changes detectable within the database trust model.
- **Remaining risk:** The SQLite file is not yet encrypted, access-controlled, externally anchored, independently replicated, or protected against a privileged database administrator. Recovery, retention, key management, and concurrent-writer behavior remain unimplemented.
- **Refactor required:** Yes before production, multi-user deployment, or claiming durable audit assurance; no before the next local storage slice.
- **Related controls:** High-level architecture Sections 21-22 and 26-27, INV-AUD-001 through INV-AUD-004, STRIDE-AI repudiation and tampering.
- **Tests added:** Persistence across reopen, hash-chain verification, tamper detection, append refusal after tampering, and unsupported event rejection.
- **Tests still missing:** Concurrent writers, crash recovery, retention/deletion policy, encrypted storage, external anchoring, authorization to read audit data, and sensitive-log minimization.
- **Owner:** Nova Aegis
- **Review date:** Phase 10 audit or before production audit storage.

### TD-007 - STRIDE-AI and MITRE ATLAS adversarial coverage

- **Phase:** 7
- **Status:** In progress
- **Severity:** Medium
- **What changed:** Added a STRIDE-AI working crosswalk and MITRE ATLAS technique-area mapping to the threat model. Added dedicated Praetor and NIC adversarial tests for mixed trust, duplicate unverified claims, unknown lifecycle state, unknown roles, and unknown tools.
- **What broke or was discovered:** The mapping exposes that real Cortex memory, MCP tool-result validation, authenticated identity, and model/artifact integrity controls are still absent. The MVP previously had no dedicated adversarial suite boundary for these components.
- **Root cause:** The implementation is still a local vertical slice; several architecture components remain contracts or named boundaries rather than executable services.
- **Fix applied or proposed:** Keep the crosswalk explicit about partial and unimplemented coverage. Require executable tests before marking an ATLAS technique covered.
- **Why this fix:** Threat-framework labels are useful only when tied to a concrete asset, boundary, control, and test result.
- **Remaining risk:** ATLAS coverage is incomplete and the live matrix may evolve. No production security or framework conformance claim is made.
- **Refactor required:** Yes before real MCP, memory, model supply-chain, or multi-user integration; no before continued synthetic testing.
- **Related controls:** Threat model Sections 42A-44, INV-EVID-003 through INV-EVID-006, INV-AUTH-001 through INV-AUTH-003, INV-MCP-001, INV-NET-001.
- **Tests added:** Dedicated NIC and Praetor adversarial suite; full suite remains pytest-discoverable.
- **Tests still missing:** Memory poisoning, tool-description poisoning, tool-result validation, authenticated identity spoofing, artifact substitution, exfiltration, resource exhaustion, and evaluator disagreement.
- **Owner:** Nova Aegis
- **Review date:** Phase 10 audit or before any real integration.

### TD-006 - Phase 6 adversarial evidence assurance

- **Phase:** 6
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Added explicit claim-group, claim, lifecycle-status, and provenance-verification metadata to evidence and citations. Praetor now returns `REVIEW` for unresolved conflicting claims, stale or superseded evidence, unclassified authority, and unverified provenance.
- **What broke or was discovered:** The earlier MVP treated any retrieved citation as sufficient for `PASS`, including instruction-like, stale, unverified, or contradictory material.
- **Root cause:** Retrieval presence was used as a proxy for evidence quality; conflict and lifecycle semantics were not represented in the evidence contract.
- **Fix applied or proposed:** Make evidence quality explicit and keep ambiguous evidence visible to the reviewer while withholding the proposed answer from `PASS`.
- **Why this fix:** It directly exercises INV-EVID-003 through INV-EVID-006 and preserves the rule that retrieval is evidence gathering, not truth establishment.
- **Remaining risk:** Claim metadata and verification flags are still supplied by the in-memory corpus; source objects, hashes, revision relationships, graph authority, and contradiction semantics are not independently validated.
- **Refactor required:** Yes before authoritative corpus or production deployment; no before the next synthetic phase.
- **Related controls:** INV-EVID-001, INV-EVID-003, INV-EVID-004, INV-EVID-005, INV-EVID-006, INV-FAIL-003.
- **Tests added:** Conflicting claims, stale evidence, unverified provenance, and unclassified instruction-like evidence all require `REVIEW`.
- **Tests still missing:** Source-object verification, hash and revision checks, supersession relationships, contradictory evidence across retrieval limits, and durable provenance storage.
- **Owner:** Nova Aegis
- **Review date:** Before Phase 10 audit or any real corpus integration.

### TD-005 - Phase 5 full audit findings

- **Phase:** 5
- **Status:** Accepted for synthetic MVP; blocking before real integrations
- **Severity:** Medium
- **What changed:** Audited Phases 1-4 against the architecture, threat model, security invariants, tests, and technical-debt ledger.
- **What broke or was discovered:** The synthetic slice has no authenticated identity, gateway-enforced MCP boundary, durable tamper-evident audit, independent provenance verification, verified model cache, or operating-system network enforcement.
- **Root cause:** The MVP intentionally uses in-memory state and injected metadata to test the control flow before introducing platform infrastructure.
- **Fix applied or proposed:** Preserve the synthetic-only boundary; require these controls before real data, consequential tools, or production inference. Detailed findings are in `docs/audits/phase-05-audit.md`.
- **Why this fix:** The current tests demonstrate bounded behavior in the evaluated profile, but application conventions are not sufficient security roots for real deployment.
- **Remaining risk:** The MVP is not production-ready and must not be connected to real organizational data or high-impact tools.
- **Refactor required:** Yes before real integrations; no before Phase 6 synthetic corpus work.
- **Related controls:** Phase 5 audit, INV-ID-001, INV-ID-002, INV-MCP-001, INV-EVID-003, INV-AUD-003, INV-NET-002.
- **Tests added:** Full 17-test suite, compilation, diagnostics, and direct invariant probes.
- **Tests still missing:** Authenticated identity, gateway rejection, durable audit integrity, source/artifact verification, network isolation, memory, graph, conflict, and human-review tests.

### TD-004 - Provider-abstract local inference boundary

- **Phase:** 4
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Added the provider-neutral inference lifecycle and a Foundry Local adapter boundary with explicit model manifests, offline provisioning, load, ready, infer, and unload states.
- **What broke or was discovered:** Foundry Local model acquisition and execution-provider provisioning can involve network-hosted catalog or platform services, which conflicts with Nova Aegis normal-operation offline requirements if left implicit.
- **Root cause:** The earlier architecture named Foundry Local as the initial runtime but had no executable lifecycle or provisioning enforcement.
- **Fix applied or proposed:** Require an explicit local `ModelManifest`, reject network-enabled provisioning, inject the actual runtime function behind the adapter, and fail when no local inference implementation is available.
- **Why this fix:** It preserves provider independence and makes offline provisioning a testable boundary instead of an assumption.
- **Remaining risk:** The adapter does not yet call the Foundry Local SDK, verify artifact hashes, manage a persistent cache, validate execution providers, or record model lifecycle events in the audit store.
- **Refactor required:** Yes before real model inference or production deployment; no before the synthetic corpus and governance tests.
- **Related controls:** INV-NET-001, INV-NET-002, INV-MODEL-001, INV-MODEL-002, INV-FAIL-002.
- **Tests added:** Offline provisioning rejection, lifecycle success, load-before-provision rejection, missing-runtime rejection, and manifest validation.
- **Tests still missing:** Real Foundry Local integration, artifact hash verification, cache integrity, provider compatibility, model audit events, and network isolation enforcement.

### TD-003 - Policy-driven tool authorization

- **Phase:** 3
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Added explicit `ToolPolicy` and `AuthorizationContext` contracts. Praetor now evaluates capability, role, target, and operation value before synthetic-tool execution.
- **What broke or was discovered:** The Phase 1/2 capability allowlist did not constrain parameters or identity context; an authorized tool name could otherwise be reused for an unintended target or operation.
- **Root cause:** Authorization was modeled as tool availability rather than authorization of the complete requested operation.
- **Fix applied or proposed:** Require a named policy and evaluate user role, target, and operation value after the capability check. Preserve fail-closed behavior when Praetor is unavailable.
- **Why this fix:** It directly enforces INV-AUTH-002, INV-AUTH-003, and the confused-deputy boundary without giving the model or tool self-granted authority.
- **Remaining risk:** Policies are in-memory and caller-provided; user identity is recorded but not authenticated; delegated authority, policy versioning, resource hierarchies, and real MCP enforcement remain absent.
- **Refactor required:** Yes before real tools, persistent policy administration, or multi-user deployment; no before the synthetic corpus phase.
- **Related controls:** INV-AUTH-001, INV-AUTH-002, INV-AUTH-003, INV-ID-002, INV-MCP-001.
- **Tests added:** Out-of-scope target, out-of-scope operation, denied role, custom policy scope, and audit authorization context.
- **Tests still missing:** Policy persistence and integrity, authenticated identity, delegation limits, policy conflict resolution, and real gateway-side enforcement.

### TD-002 - Structured evidence and audit contracts

- **Phase:** 2
- **Status:** Mitigated
- **Severity:** Medium
- **What changed:** Added structured response and provenance contracts, retrieval scores, typed audit events, request correlation IDs, input validation, and adversarial evidence tests.
- **What broke or was discovered:** Title-referenced documents were not discoverable because retrieval initially indexed document text only. The initial audit events also had no stable event taxonomy or correlation identifier.
- **Root cause:** The first vertical slice optimized for the shortest behavior path and left evidence metadata and event contracts implicit.
- **Fix applied or proposed:** Include document titles in lexical retrieval; add `Provenance`, `Response`, supported audit event types, event IDs, request IDs, and explicit validation for empty questions and tool parameters.
- **Why this fix:** Evidence must be discoverable and traceable, while audit records must be structurally recognizable across the request path.
- **Remaining risk:** Provenance is currently caller-supplied and in-memory; citations are not yet independently hash-verified, persisted, or conflict-aware.
- **Refactor required:** Yes before persistent or multi-user deployment; no before the next synthetic-corpus phase.
- **Related controls:** INV-EVID-001, INV-EVID-003, INV-EVID-004, INV-AUD-001, INV-FAIL-003.
- **Tests added:** Provenance and score assertions, audit event sequence, instruction-like evidence isolation, malformed tool parameters, and invalid-question rejection.
- **Tests still missing:** Source hashing, revision conflict handling, durable audit storage, schema serialization, and independent provenance verification.

### TD-001 - Dependency-free MVP infrastructure

- **Phase:** 1
- **Status:** Accepted for MVP
- **Severity:** Medium
- **What changed:** Added a dependency-free local retrieval, evidence citation, response assurance, audit, and synthetic-tool slice.
- **What broke or was discovered:** The MVP does not yet use a persistent document store, graph database, vector index, Foundry Local, or a real MCP transport.
- **Root cause:** The first vertical slice intentionally minimizes infrastructure so the authority boundary can be tested before platform integration.
- **Fix or next step:** Keep the provider, storage, and tool interfaces replaceable; introduce each dependency only behind a tested boundary.
- **Why this fix:** It validates governance behavior without prematurely coupling the architecture to runtime or storage choices.
- **Remaining risk:** In-memory state is not durable, multi-user safe, or production-ready.
- **Refactor required:** Yes before production or multi-session deployment; no before the next MVP behavior slice.
- **Related controls:** High-level architecture, INV-AUTH-001, INV-GOV-001, INV-NET-001.
- **Tests added:** Local evidence PASS, missing evidence REVIEW, unauthorized tool BLOCK, authorized tool execution, Praetor outage fail-closed.
- **Tests still missing:** Persistence isolation, concurrent sessions, real MCP boundary, model-provider contract, and network enforcement.

## Phase Entry Template

Copy this section for each completed phase.

### TD-XXX - Short title

- **Phase:**
- **Status:** Open | In progress | Mitigated | Resolved | Accepted | Blocked
- **Severity:** Critical | High | Medium | Low
- **What changed:**
- **What broke or was discovered:**
- **Root cause:**
- **Fix applied or proposed:**
- **Why this fix:**
- **Remaining risk:**
- **Refactor required:** Yes | No | Reassess at audit
- **Related controls:**
- **Tests added:**
- **Tests still missing:**
- **Owner:**
- **Review date:**

## Debt Rules

1. Critical debt cannot be silently accepted.
2. A security-invariant failure is tracked as a release blocker for the affected operating profile.
3. A workaround must include the reason it exists and the condition that permits its removal.
4. Debt discovered during a phase is recorded in the same phase, even when the fix is deferred.
5. Accepted debt receives an owner and review date.
6. Resolved debt requires an executable validation result.
7. The five-phase audit reviews every open, mitigated, accepted, and blocked item.
