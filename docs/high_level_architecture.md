# Nova Aegis High-Level Architecture

## 1. Purpose

This document defines the initial high-level architecture for **Nova Aegis**, a local-first governed AI ecosystem intended for organizations that require AI capabilities while maintaining control over sensitive data, evidence, model execution, tools, and operational authority.

The architecture translates the Nova Aegis problem statement and design principles into independently bounded components.

The initial deployment target is a **single workstation or edge node** operating primarily with local or approved intranet resources.

Nova Aegis is not designed as a monolithic autonomous agent. It is a governed ecosystem in which knowledge retrieval, cognitive reasoning, memory, model inference, governance, authorization, tool execution, evidence provenance, and audit remain observable and separately controllable.

## 2. Architectural Model

Nova Aegis is organized around four primary logical domains:

1. **NIC - Evidence & Knowledge**
2. **Cortex - Cognitive Orchestration & Memory**
3. **Praetor - Governance, Assurance & Authorization**
4. **Nova Aegis Core - System Control Plane**

Microsoft Foundry Local provides the initial inference runtime. MCP provides a standardized interface for approved tools and capabilities.

Neither Foundry Local nor MCP defines the Nova Aegis architecture.

## 3. High-Level System Flow

```text
                  +---------------------+
                  |        User         |
                  |   / Enterprise UI   |
                  +----------+----------+
                             |
                             v
                  +---------------------+
                  |   Nova Aegis Core   |
                  | Identity / Routing  |
                  | Session / Audit     |
                  +----------+----------+
                             |
                             v
                  +---------------------+
                  |       Cortex        |
                  | Cognitive Planning  |
                  | Working Memory      |
                  | Orchestration       |
                  +------+--------+-----+
                         |        |
              Evidence   |        | Proposed Action
                         |        |
                         v        v
               +------------+   +---------------+
               |    NIC     |   |    Praetor    |
               | Knowledge  |   | Governance &  |
               | Graph      |   | Assurance     |
               +-----+------+   +-------+-------+
                     |                  |
                     | Evidence         | PASS / REVIEW / FAIL
                     |                  |
                     +---------+--------+
                               |
                               v
                      +-----------------+
                      |   MCP Gateway   |
                      | Authorized Tool |
                      |    Execution    |
                      +--------+--------+
                               |
                               v
                    Local / Intranet Systems
```

## 4. Nova Aegis Core

### Role

Nova Aegis Core is the control plane of the ecosystem. It coordinates system-level behavior without becoming the primary reasoning agent.

Core responsibilities include:

- identity;
- authentication;
- session management;
- component routing;
- service discovery;
- permission enforcement hooks;
- inference-provider access;
- MCP registration;
- configuration;
- audit event collection;
- system health; and
- controlled network access.

Nova Aegis Core should not independently decide whether an operational action is semantically appropriate. That responsibility belongs to the governed Cortex-to-Praetor path.

> **Core controls the environment. It does not replace governance.**

## 5. NIC - Evidence & Knowledge Agent

NIC is responsible for constructing, retrieving, and preserving relationships between authorized organizational evidence.

NIC should answer:

> **What evidence exists, where did it come from, and how is it related?**

NIC is not primarily responsible for determining what action should be taken. It provides Cortex and Praetor with structured, traceable evidence.

## 6. NIC Knowledge Architecture - Graph First

Nova Aegis adopts a:

> **Graph-first, vector-assisted knowledge architecture.**

Vector retrieval remains valuable but should not become the authoritative representation of organizational knowledge. Semantic similarity is useful for discovery.

Graph relationships provide:

- structure;
- provenance;
- authority;
- chronology;
- contradiction;
- dependency;
- multi-hop context;
- revision history; and
- policy relationships.

Text-bearing nodes may additionally contain embeddings for semantic discovery.

### Conceptual Knowledge Model

```text
Document
   |
   +-- CONTAINS ----------> Section
   |                          |
   |                          +-- ASSERTS ------> Claim
   |                                               |
   |                                               +-- SUPPORTED_BY -> Evidence
   |                                               +-- CONTRADICTS --> Claim
   |                                               +-- APPLIES_TO ---> Entity
   |                                               +-- GOVERNED_BY --> Policy
   |
   +-- SUPERSEDES --------> Document
   |
   +-- AUTHORIZED_BY -----> Authority
```

## 7. NIC Retrieval Strategy

NIC should support multiple complementary retrieval methods.

### Graph Retrieval

Used for relationships, multi-hop queries, provenance, dependency chains, policy relationships, authority, contradiction, and revision lineage.

### Vector Retrieval

Used for semantic similarity, fuzzy natural-language queries, synonyms, and discovery of likely starting points.

### Lexical Retrieval

Used for exact terminology, identifiers, procedure numbers, equipment names, document references, and exact clauses.

### Retrieval Philosophy

> **Vector finds the neighborhood. Graph explains the neighborhood.**

NIC should be capable of assembling an **evidence subgraph** rather than simply returning a ranked list of chunks.

## 8. Evidence Subgraph

A NIC response to Cortex should ideally contain structured evidence such as:

```text
Requested Question
      |
      v
Relevant Claim
      |
      +-- supported_by -> Evidence A
      |                    |
      |                    +-- extracted_from -> Section 4.2
      |                                         |
      |                                         +-- belongs_to -> Procedure Rev 7
      |
      +-- governed_by -> Policy 12
      |
      +-- contradicts -> Claim B
                           |
                           +-- source -> Older Procedure Rev 5
```

This representation allows Cortex to reason over relationships while allowing Praetor to independently inspect evidence support.

## 9. Cortex - Cognitive Orchestration Agent

Cortex is responsible for determining:

> **What matters now, what has been learned, and what should the system do next?**

Cortex coordinates reasoning and task execution but does not hold unrestricted operational authority.

Its primary responsibilities include:

- interpreting user intent;
- decomposing tasks;
- coordinating NIC retrieval;
- selecting relevant tools;
- maintaining working context;
- maintaining cognitive memory;
- distinguishing signal from noise;
- proposing answers;
- proposing actions; and
- forwarding governed decisions to Praetor.

## 10. Cortex Cognitive Memory Model

Cortex should not attempt to store everything indefinitely. Its memory architecture should reflect a selective model of information processing.

### Working Memory

Short-lived, task-specific context required for the current task. It is limited, replaceable, and relevance-focused.

### Episodic Memory

Records meaningful events and outcomes, such as actions performed, failures, user decisions, important tool results, and resolved incidents.

### Semantic Memory

Represents consolidated knowledge learned across repeated observations. Semantic memory must retain traceability to supporting evidence where possible.

### Salience

Information may receive higher priority because of relevance, novelty, repeated occurrence, contradiction, operational consequence, uncertainty, unresolved state, or security significance.

### Reinforcement

Repeated and independently supported information may increase memory relevance. Reinforcement does not automatically establish truth.

### Decay

Low-value or unused memories may decrease in priority over time. Decay means **less cognitively active**, not necessarily **permanently deleted**.

### Deferred Memory

Information that is not relevant to the current task may remain available for later reactivation.

> **Cortex does not remember everything. It preserves what remains useful, unresolved, consequential, or repeatedly supported.**

## 11. Cortex and NIC Separation

NIC and Cortex must remain conceptually separate.

- **NIC** represents organizational knowledge and evidence.
- **Cortex** represents the system's current cognitive state.

NIC answers:

> What evidence exists?

Cortex answers:

> Which evidence matters for this task?

This separation reduces the risk that temporary model interpretation becomes indistinguishable from authoritative organizational knowledge.

## 12. Praetor - Governance, Assurance & Authorization

Praetor is the primary governance and assurance authority within Nova Aegis.

Praetor should answer:

> **Is this conclusion or proposed action sufficiently supported, permitted, and appropriate to release or execute?**

Praetor responsibilities include:

- evidence validation;
- provenance verification;
- policy enforcement;
- tool authorization;
- confidence boundaries;
- contradiction detection;
- high-risk detection;
- prompt-injection detection;
- output validation;
- disagreement handling;
- human-review escalation; and
- audit evidence generation.

## 13. Praetor Hybrid Assurance Architecture

Praetor should use complementary evaluation mechanisms rather than depending on a single evaluator.

### Agent K - Deterministic Governance Evaluator

Agent K is responsible for structured checks such as policy rules, provenance requirements, required evidence, authorization conditions, trace completeness, deterministic safety boundaries, tool permissions, schema validation, and reproducible controls.

The current synthetic Agent K implementation evaluates response evidence through ordered immutable rules for evidence presence, authority classification, currency, provenance verification, and unresolved claim conflicts. Each evaluation returns an inspectable rule trace with stable identifiers (`AK-EVID-001`, `AK-PROV-001`, `AK-REV-001`, `AK-PROV-002`, and `AK-CLAIM-001`). Praetor records the resulting deterministic reason with the fused assurance audit event.

This is an evidence-assurance subset, not a complete production rule engine. Tool authorization, policy versioning, schema validation, risk classification, rule distribution, and rule-change approval remain separate controls or future Agent K rule families.

### Semantic LLM Judge

The semantic evaluator is responsible for context-sensitive evaluation such as semantic inconsistency, misleading interpretation, subtle contradiction, hidden intent, context-dependent risk, disguised prompt injection, semantic manipulation, and claims that technically pass rules but misrepresent evidence.

### Hybrid Fusion

Hybrid fusion combines deterministic and semantic evaluation. Possible states include **PASS**, **REVIEW**, and **FAIL**.

Disagreement should not be silently converted into approval.

The current synthetic `HybridAssurance` contract uses fixed, non-averaging fusion rules:

```text
deterministic FAIL             -> FAIL
deterministic PASS + semantic PASS -> PASS
every other combination        -> REVIEW
```

This makes a deterministic hard-boundary failure terminal, while a semantic failure or review prevents PASS without independently authorizing an action. The contract is unit-tested against semantic misrepresentation, structural-tag omission, hard safety boundary, and evaluator-injection fixtures.

The current Praetor response path injects both evaluators, fuses their independent verdicts, and records both statuses and reasons with the fused audit event. Evaluator exception, unavailable evaluation, or evaluator-kind mismatch becomes `REVIEW`; it cannot silently retain or create `PASS`. The default semantic evaluator is a synthetic stub and must be replaced only through an isolated, audited provider boundary.

The rule was informed by the locally provided August 2026 *Hybrid AI Evaluation and Governance Study* (`SHA-256: 932ABDBC32A10E76BE755251BD308ABBE4F2D07CBFE4C3AF5159F310D6AA96A1`). That report is research input, not an authority source or production validation: it records unresolved semantic-judge configuration metadata and a source-table discrepancy.

> **Complementary evaluators are intended to expose different failure modes, not to create an illusion of certainty.**

## 14. Intermediate Suppression / Isolation Layer

Before semantic evaluation, Praetor may apply an intermediate filtering and isolation stage inspired by previous experimental work.

This stage may identify or suppress:

- irrelevant instruction fragments;
- suspicious retrieved content;
- tool-output manipulation;
- prompt-injection patterns;
- semantic noise;
- malformed structured data;
- context contamination; and
- untrusted instructions embedded inside evidence.

This concept may be referred to internally as an **Adversarial Signal Suppression Layer**.

Its purpose is not to remove legitimate evidence. Its purpose is to prevent untrusted or irrelevant signals from gaining unnecessary influence over downstream semantic evaluation.

## 15. MCP Tool Governance

MCP provides Nova Aegis with a standardized method for exposing enterprise capabilities. MCP does not grant authority.

A tool being available does not mean Cortex or the underlying model is authorized to execute it.

### Governed Tool Flow

```text
Cortex
   |
   | proposes action
   v
Praetor
   |
   +-- Agent K deterministic checks
   |
   +-- semantic evaluation
   |
   +-- policy evaluation
   |
   +-- authorization decision
           |
           +-- PASS -----> MCP Gateway
           |
           +-- REVIEW ---> Human Approval
           |
           +-- FAIL -----> Block + Audit
```

## 16. Tool Execution Lifecycle

Sensitive tool execution should follow:

> **Proposal -> Evidence -> Policy Evaluation -> Authorization -> Execution -> Verification -> Audit**

Tool results should return through Nova Aegis Core rather than being implicitly trusted. Tool output may itself require validation, provenance, schema checks, security filtering, and additional Praetor evaluation.

## 17. MCP Gateway

The initial architecture should include a logical MCP Gateway or broker.

Its responsibilities may include:

- registered MCP server inventory;
- tool capability discovery;
- connection management;
- identity;
- authorization tokens;
- least-privilege enforcement;
- request validation;
- response validation;
- audit correlation IDs;
- timeout handling; and
- server health.

The MCP Gateway should not override Praetor authorization decisions.

### Synthetic MCP Gateway Contract

The current MVP includes a synthetic, in-process `McpGateway` for boundary testing. It is not an MCP HTTP server or OAuth implementation. It binds a gateway-issued access token to the canonical HTTPS resource URI, validates the audience and backing identity on every request, requires a registered least-privilege tool scope, validates exact request parameters, invokes Praetor server-side, limits discovery by role, and records allow/deny events.

This implements a subset of MCP authorization guidance: access tokens are audience-bound to the MCP resource server, token passthrough is prohibited, every HTTP request requires authorization in a real HTTP deployment, and scope semantics are minimized. The current security baseline must also track the June 25, 2026 security analysis of the 2026-07-28 revision: stateless client-held task state, unsigned `_meta` fields, gateway header/body desynchronization, interactive Apps, and long-running Tasks are untrusted or separately governed surfaces. Full Protected Resource Metadata, OAuth 2.1/PKCE, HTTP transport, redirect handling, consent, SSRF controls, stateless task-state integrity, metadata/header consistency, Apps sandboxing, task quotas, session handling, and real server response validation remain unimplemented.

The synthetic gateway now signs a client-held task-state envelope bound to the authenticated user, gateway audience, requested tool, and canonical parameters. It validates that envelope on every stateless request, requires `Mcp-Method` and `Mcp-Name` to exactly match the body routing fields, rejects `_meta` fields that attempt to supply identity, audience, or scope, and returns the stored result rather than replaying a completed task. The replay registry is process-local; durable distributed task state remains future work. This is a local contract test, not implementation of the 2026-07-28 transport or Tasks extension.

The local task contract also enforces a per-user active-task budget and supports cancellation while a task is pending. A cancelled state is rejected before tool execution, even if its signature is still valid. This is not a long-running task runtime: it has no durable queue, distributed lease, cancellation of already-running work, timeout enforcement, or resource accounting beyond local task admission.

For synthetic worker testing, `submit_task` creates a `pending` state and `run_task` claims it for execution. The local state machine is `pending -> in_progress -> completed | failed`, with `pending -> cancelled | expired` as terminal alternatives. Handler errors become audited `failed` tasks rather than returning them to `pending`; cancellation of an in-progress task is rejected to avoid contradictory state.

The task store can now be backed by local SQLite. Completed task results remain available after gateway restart. On startup, any persisted `in_progress` task becomes `recovery_required`; Nova Aegis returns `REVIEW` and does not automatically replay the handler. Recovery requires a future authorized reconciliation workflow with an independent execution receipt.

## 18. Initial MCP Capability Categories

Initial workstation experiments may expose a small number of controlled local capabilities.

### Knowledge MCP

- query local documents;
- fetch source metadata;
- retrieve graph nodes; and
- retrieve relationships.

### System MCP

- inspect approved local system status;
- read approved configuration; and
- return health information.

### Audit MCP

- query audit records; and
- retrieve decision traces.

### Test Operations MCP

Provides safe synthetic operations for demonstrating PASS, REVIEW, FAIL, and human approval.

No high-impact enterprise tool should be introduced in the initial MVP.

## 19. Local Inference Layer

Microsoft Foundry Local is the initial inference runtime for Nova Aegis. It may provide models used by Cortex, NIC semantic processing, Praetor semantic evaluation, structured extraction, summarization, and classification.

The architecture should expose an internal abstraction similar to:

```text
InferenceProvider
    |
    +-- FoundryLocalProvider
    |
    +-- FutureLocalProvider
    |
    +-- FutureInternalServerProvider
    |
    +-- FutureApprovedCloudProvider
```

No higher-level component should require Foundry Local-specific logic where avoidable.

> **Foundry Local is the initial engine, not the ecosystem.**

## 20. Model Separation

Nova Aegis should not assume every function uses the same model. Different tasks may eventually use different models.

```text
Cortex
   +-- reasoning model

NIC
   +-- embedding model
   +-- extraction model

Praetor
   +-- semantic judge model
```

Model assignment should remain configurable.

## 21. Audit Architecture

Important events should produce structured audit records. Each request should receive a correlation identifier that propagates across components.

For sensitive tool execution, audit recording is part of the authorization boundary. The current synthetic flow records a `tool_authorized` event before execution and refuses the action if that preflight record cannot be written. A later `tool_executed` event records the result. This ordering ensures an audit outage cannot make execution more permissive.

SQLite-backed synthetic execution also persists an idempotency-keyed receipt before the tool is called and completes that receipt before reporting success. A completed receipt returns the stored result without replaying the tool. An authorized receipt without completion is an ambiguous recovery state: Nova Aegis returns `REVIEW`, records `tool_recovery_required`, and does not automatically retry the operation.

Example fields include:

```text
session_id
request_id
user_id
timestamp
component
event_type
model_id
source_ids
policy_id
tool_name
decision
confidence
human_review
result
```

Sensitive content should not automatically be duplicated into logs. The audit system should prioritize reconstructability while respecting organizational data-handling policy.

The current workstation implementation provides a local SQLite audit boundary with an append-only sequence and SHA-256 predecessor hash chain. This detects post-write modification when the database is reopened or appended to, but it is not yet an externally anchored, access-controlled, encrypted, or independently replicated audit service. Those controls are required before production or multi-user deployment.

## 21A. Identity and Policy Boundary

Core must establish authorization context; callers must not be trusted to self-assign identity or role. The current synthetic boundary provides an `IdentityAuthority` that issues short-lived signed credentials and validates issuer membership, expiry, revocation, and signature before a tool decision. Praetor fingerprints its loaded tool policies and rejects authorization when the policy set has changed since initialization.

This is a local contract demonstration, not enterprise authentication. The authority secret is process-local, credentials are not yet backed by an external identity provider, and policy fingerprints are not externally anchored. Those controls remain prerequisites for multi-user or real-tool deployment.

## 22. Trust Boundaries

Initial trust boundaries should include:

```text
+--------------------------------------------+
|        Nova Aegis Workstation Boundary    |
|                                            |
|  UI                                        |
|  Core                                      |
|  Cortex                                    |
|  NIC                                       |
|  Praetor                                   |
|  Foundry Local                             |
|  Local Knowledge Graph                     |
|  Vector Index                              |
|  Audit Store                               |
|  Local MCP Servers                         |
|                                            |
+--------------------------------------------+
                  |
                  | explicitly approved
                  v
         Enterprise Intranet Boundary
                  |
                  v
         Approved Internal Systems
```

Internet access should not be required during normal operation.

## 23. Primary End-to-End Query Flow

For a knowledge request:

1. The user submits a query.
2. Nova Aegis Core authenticates the user, creates a request ID, and establishes permissions.
3. Cortex interprets intent and determines required evidence.
4. NIC performs semantic discovery, graph traversal, provenance resolution, and evidence-subgraph construction.
5. Cortex evaluates relevant evidence, updates working context, and constructs a proposed response.
6. Praetor verifies evidence support, evaluates policy, runs deterministic checks, runs semantic evaluation, and assigns PASS, REVIEW, or FAIL.
7. Core returns an approved response, routes REVIEW when required, or blocks FAIL.
8. Audit records important events and decisions.

## 24. Primary Tool-Calling Flow

For an operational action:

1. The user requests an action.
2. Cortex interprets the request.
3. NIC retrieves relevant evidence, procedure, policy, and authority requirements.
4. Cortex proposes the action, parameters, and rationale.
5. Praetor evaluates authorization, evidence, policy, risk, semantic intent, and Agent K deterministic conditions.
6. The decision is applied:
   - **PASS:** MCP Gateway executes the approved operation.
   - **REVIEW:** human authorization is required.
   - **FAIL:** the operation is blocked.
7. The MCP result returns.
8. The result is validated.
9. The audit record is completed.

## 25. Fail-Safe Behavior

When an unexpected condition occurs, Nova Aegis should reduce authority.

```text
NIC unavailable
      |
      v
No evidence
      |
      v
REVIEW / insufficient evidence
```

```text
Praetor unavailable
      |
      v
No authorization
      |
      v
Sensitive tool execution blocked
```

```text
MCP response malformed
      |
      v
Execution result untrusted
      |
      v
REVIEW / failure
```

```text
Model unavailable
      |
      v
Degraded service
      |
      v
No automatic bypass of governance
```

> **Loss of governance must never increase autonomy.**

## 26. Initial Storage Layers

The workstation MVP may require separate stores for:

### Knowledge Graph

Relationships, entities, claims, documents, policies, and provenance.

### Vector Index

Semantic representations used for discovery.

### Document Store

Original approved organizational content.

### Cortex Memory Store

Working, episodic, semantic, salience, reinforcement, and decay metadata.

### Policy Store

Machine-readable governance rules.

### Audit Store

Structured operational and governance events.

The MVP implementation uses SQLite behind the `SQLiteAuditLog` interface. The store verifies its hash chain before reads and before accepting new events, and refuses to continue when integrity verification fails.

These should remain logically separated even if the MVP initially uses lightweight technologies.

## 27. Initial Security Posture

The first Nova Aegis workstation should assume:

- local inference;
- localhost or approved intranet communications;
- deny-by-default outbound network policy;
- authenticated users;
- least-privilege tool access;
- no autonomous high-impact operations;
- explicit MCP registration;
- controlled model provisioning;
- controlled policy changes; and
- tamper-aware audit records where practical.

## 28. Conceptual Heritage

Nova Aegis may draw architectural lessons from:

- [PRAETOR_MCP](https://github.com/drosadocastro-bit/PRAETOR_MCP);
- [nova_rag_public](https://github.com/drosadocastro-bit/nova_rag_public);
- [Roswell-uap-cortex](https://github.com/drosadocastro-bit/Roswell-uap-cortex); and
- [PRAETOR_MCP_BICAMERAL](https://github.com/drosadocastrobit/PRAETOR_MCP_BICAMERA).

These are conceptual references only. Nova Aegis should not directly reproduce these systems or inherit domain-specific assumptions. Specifically, Roswell/UAP-specific subject matter must remain outside the Nova Aegis architecture.

Reusable ideas should be generalized into domain-neutral enterprise capabilities.

> **Reuse what was learned, not necessarily what was built.**

## 29. Initial Component Summary

### NIC

**Question:** What evidence exists and how is it connected?

**Primary capabilities:** Graph knowledge, vector-assisted discovery, provenance, and evidence retrieval.

### Cortex

**Question:** What matters now, what have we learned, and what should we do with the evidence?

**Primary capabilities:** Reasoning, orchestration, selective memory, salience, and task planning.

### Praetor

**Question:** Is the conclusion or action justified, permitted, and safe to release or execute?

**Primary capabilities:** Governance, assurance, Agent K deterministic evaluation, semantic LLM evaluation, MCP authorization, and human escalation.

### Nova Aegis Core

**Question:** Who can access what, where do requests go, and how is system activity controlled and recorded?

**Primary capabilities:** Identity, routing, permissions, runtime access, system configuration, and audit coordination.

## 30. Architectural North Star

Nova Aegis should preserve the following separation:

> **NIC establishes evidence.**
>
> **Cortex establishes cognitive relevance and proposes reasoning.**
>
> **Praetor establishes justification and authority.**
>
> **Nova Aegis Core establishes system boundaries and execution control.**

No single model, agent, or tool should independently own all four responsibilities.

## 31. MVP Architecture Goal

The first Nova Aegis implementation should demonstrate that a single workstation can:

1. operate without routine Internet access;
2. ingest approved technical knowledge;
3. create a graph-first knowledge representation;
4. use vector retrieval for semantic discovery;
5. retrieve evidence with provenance;
6. maintain selective Cortex memory;
7. generate evidence-grounded responses;
8. evaluate those responses through Praetor;
9. combine deterministic Agent K-style controls with semantic LLM evaluation;
10. govern MCP tool requests;
11. produce PASS, REVIEW, and FAIL outcomes;
12. require human approval where appropriate;
13. block unauthorized operations; and
14. preserve an auditable decision trail.

Success should be evaluated through observable behavior rather than architectural claims.

## Working Architecture Statement

> **Nova Aegis separates knowledge, cognition, governance, and execution so that AI capability can increase without requiring equivalent increases in uncontrolled authority.**

## Working Motto

**Private by location. Grounded by evidence. Governed by design.**
