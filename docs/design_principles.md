# Nova Aegis Design Principles

## 1. Purpose

Nova Aegis is a local-first governed AI ecosystem designed for organizations that need useful AI capabilities while maintaining control over sensitive data, evidence, tools, and operational authority.

These principles define the architectural rules that guide implementation decisions across Nova Aegis. They are independent of any specific model, inference runtime, user interface, or enterprise integration.

## 2. Local-First by Default

Nova Aegis should perform normal AI processing within the organization's approved computing boundary. Local or intranet resources should be preferred over externally hosted services whenever they can satisfy the task. Internet or cloud access must never be an implicit requirement for normal operation.

External processing, if supported in future versions, must be explicitly enabled, policy controlled, auditable, limited to authorized data, and disabled by default.

> **Data should remain where the organization expects it to remain.**

## 3. Private by Location, Not by Assumption

Running an AI system locally does not automatically make it secure, trustworthy, or private. Nova Aegis must explicitly control:

- network access;
- model access;
- local storage;
- credentials and secrets;
- tool permissions;
- retrieval sources;
- logging;
- exported data; and
- software and model updates.

Privacy should result from enforceable system boundaries rather than assumptions about model behavior.

## 4. Evidence Before Assertion

When Nova Aegis is expected to answer from organizational knowledge, claims should be grounded in available authorized evidence whenever practical. NIC or equivalent retrieval capabilities should identify and preserve the evidence used to support a response.

The system should distinguish between:

- retrieved evidence;
- deterministic facts;
- model interpretation;
- inference;
- uncertainty; and
- unsupported statements.

When sufficient evidence is unavailable, the system should not manufacture certainty.

> **No evidence should not silently become confident evidence.**

## 5. Preserve Provenance

Important information should retain traceability to its origin. Where applicable, Nova Aegis should record:

- source identifier;
- document or system of origin;
- retrieval timestamp;
- relevant section or evidence location;
- transformation history;
- component responsible for retrieval; and
- model or process that generated subsequent interpretation.

Provenance should survive movement between NIC, Cortex, Praetor, and external tools.

## 6. Bounded Authority

AI capability and operational authority are separate concepts. A model may be capable of proposing an action without having permission to execute that action.

Nova Aegis must explicitly define what each component is permitted to read, retrieve, reason about, recommend, modify, execute, and approve. No model or agent should receive unrestricted authority simply because it can reason about the requested task.

> **Capability does not imply authorization.**

## 7. Least Privilege

Every agent, tool, MCP server, service, user, and integration should receive only the permissions required for its defined responsibility. Permissions should be explicit, minimal, revocable, scoped, and auditable.

Access should not automatically propagate between components. For example, Cortex being able to request an operation does not mean Cortex should directly possess the credentials required to perform it.

## 8. Separation of Responsibilities

Nova Aegis should avoid concentrating retrieval, reasoning, governance, authorization, and execution inside a single model or agent.

Initial conceptual responsibilities are:

### NIC: Evidence and Retrieval

NIC is responsible for locating, organizing, and returning authorized evidence.

### Cortex: Reasoning and Orchestration

Cortex is responsible for interpreting the task, coordinating capabilities, maintaining relevant context, and proposing a path toward resolution.

### Praetor: Governance and Assurance

Praetor is responsible for evaluating evidence support, policy compliance, operational boundaries, contradictions, uncertainty, and escalation requirements.

### Nova Aegis Core: Control Plane

Nova Aegis Core is responsible for identity, routing, permissions, policy enforcement hooks, model access, service coordination, and system-level audit functions.

These responsibilities may evolve, but separation of authority should remain a core architectural property.

## 9. Independent Governance

The component producing a recommendation should not be solely responsible for determining whether its own recommendation is acceptable. Where practical, Nova Aegis should maintain independent or complementary evaluation paths for:

- evidence support;
- policy compliance;
- output validation;
- tool authorization; and
- high-risk decisions.

Semantic evaluation and deterministic controls may be combined when their failure modes are complementary. Disagreement should be observable rather than silently resolved.

## 10. Human Review Is a Valid Outcome

Nova Aegis should not treat human escalation as system failure. When evidence is insufficient, conflicting, unusual, outside policy, or operationally sensitive, the correct behavior may be **REVIEW** rather than forcing approval or rejection.

Initial high-level assurance states may include:

- **PASS**;
- **REVIEW**; and
- **FAIL**.

The meaning and authority associated with these states must be explicitly defined.

> **Knowing when not to decide is part of reliable behavior.**

## 11. Explicit Tool Authorization

Tool availability and tool authorization must remain separate. An MCP server or internal integration being technically accessible does not automatically authorize every agent to invoke every capability.

Sensitive tool calls should follow this pattern:

**Proposal -> Policy Evaluation -> Authorization -> Execution -> Verification -> Audit**

Higher-risk actions may additionally require human approval.

## 12. MCP Is an Interface, Not a Trust Boundary

MCP provides a standardized mechanism for exposing tools and capabilities. Nova Aegis must not assume that an MCP-compatible server or tool is trustworthy simply because it implements the protocol.

MCP integrations should still be subject to:

- identity;
- authorization;
- input validation;
- output validation;
- least privilege;
- logging;
- network restrictions; and
- failure handling.

## 13. Fail Safely

Unexpected conditions should move the system toward reduced authority rather than increased autonomy. Examples include:

- unavailable evidence;
- malformed tool responses;
- failed policy checks;
- unavailable MCP services;
- model errors;
- ambiguous authorization;
- contradictory evidence; and
- unexpected network conditions.

Nova Aegis should prefer:

**degrade -> restrict -> REVIEW**

over:

**guess -> continue -> execute**

## 14. Auditability by Design

Auditability should not be added after the system is complete. Important events should produce structured records from the beginning.

Potential audit events include:

- user requests;
- retrieved evidence;
- model invocation;
- model identity and version;
- policy evaluation;
- assurance status;
- tool requests;
- authorization decisions;
- human approvals;
- executed actions;
- failures; and
- configuration changes.

Audit records should provide enough context to reconstruct what the system did without requiring unrestricted storage of sensitive content.

## 15. Model and Runtime Independence

Foundry Local is the initial Nova Aegis inference runtime. It must not become the definition of Nova Aegis.

The architecture should expose a provider abstraction allowing alternative inference runtimes to be introduced later without redesigning NIC, Cortex, Praetor, or governance logic.

Possible future inference environments may include:

- alternative local runtimes;
- internal inference servers;
- enterprise on-premises infrastructure; and
- approved cloud services.

> **Foundry Local is the initial engine, not the ecosystem.**

## 16. Models Are Replaceable Components

Nova Aegis should avoid embedding critical policy or security assumptions exclusively inside model prompts. Models may change because of performance, hardware requirements, licensing, security posture, organizational policy, vendor changes, or task specialization.

Switching models should not require redesigning the system's core governance or security boundaries.

## 17. Security Before Autonomy

Increasing agent autonomy should require stronger evidence that appropriate controls exist. Nova Aegis should initially favor retrieval, recommendation, analysis, and controlled tool proposals before expanding toward autonomous execution.

New autonomous capabilities should be introduced incrementally and evaluated under explicit threat models and test conditions.

## 18. Observable Behavior Over Trust Claims

Nova Aegis should not declare itself trustworthy, safe, secure, or reliable simply because particular architectural controls exist. Claims should be based on observable behavior under defined test conditions.

Testing should evaluate areas such as:

- evidence grounding;
- unauthorized actions;
- prompt injection;
- retrieval manipulation;
- conflicting evidence;
- tool misuse;
- data leakage;
- model failure;
- degraded services; and
- governance disagreement.

> **Trust should be supported by evidence, not branding.**

## 19. Reuse Lessons, Not Legacy Assumptions

Previous Nova Labs projects may provide useful architectural ideas, experimental findings, and lessons learned. Nova Aegis should not automatically inherit their implementations or assumptions.

Conceptual references include:

- [PRAETOR_MCP](https://github.com/drosadocastro-bit/PRAETOR_MCP);
- [nova_rag_public](https://github.com/drosadocastro-bit/nova_rag_public);
- [Roswell-uap-cortex](https://github.com/drosadocastro-bit/Roswell-uap-cortex); and
- [PRAETOR_MCP_BICAMERAL](https://github.com/drosadocastrobit/PRAETOR_MCP_BICAMERA).

Reusable concepts should be abstracted and evaluated against Nova Aegis requirements before adoption. Domain-specific material, particularly UAP, Roswell, dataset-specific, or investigation-specific content, must remain outside Nova Aegis.

> **Reuse what was learned, not necessarily what was built.**

## 20. Enterprise and Domain Neutrality

The core Nova Aegis platform should avoid assumptions tied to a single industry. Initial demonstrations may use technical or operational scenarios, but core capabilities should remain applicable across different enterprise environments.

Industry-specific behavior should eventually be implemented through policies, knowledge sources, tool integrations, configuration, and specialized modules rather than hard-coded into the platform core.

## 21. Secure-by-Default Networking

The initial workstation deployment should assume:

- no required outbound Internet access during normal operation;
- localhost or approved intranet communication only;
- explicit network allowlists;
- encrypted communications when services cross host boundaries; and
- authenticated access to enterprise resources.

Network access should be treated as a capability requiring justification.

## 22. Controlled Updates

Offline or restricted operation still requires controlled software and model maintenance. Future Nova Aegis update mechanisms should support verification of:

- model artifacts;
- application packages;
- dependencies;
- configuration;
- MCP servers; and
- policies.

Updates entering restricted environments should follow an explicit validation and approval process.

## 23. Configuration Over Hard-Coding

Enterprise requirements will differ between deployments. Where practical, Nova Aegis should represent operational boundaries through configuration rather than application rewrites.

Examples include:

- allowed tools;
- authorized data sources;
- confidence thresholds;
- human approval requirements;
- model selection;
- network access;
- retention periods; and
- assurance rules.

## 24. Minimal Initial Complexity

The MVP should implement only the capabilities required to validate the Nova Aegis problem statement. The first version should not attempt to solve:

- enterprise-scale concurrency;
- high availability;
- distributed model serving;
- every possible MCP integration;
- cloud escalation;
- autonomous enterprise operations; or
- every regulatory environment.

Complexity should be introduced only when supported by a demonstrated requirement.

> **Build the smallest system capable of testing the architecture honestly.**

## Core Nova Aegis Principles

Nova Aegis can be summarized by the following commitments:

- **Local-first by default.**
- **Private by enforceable boundary.**
- **Evidence before assertion.**
- **Provenance preserved.**
- **Capability does not imply authority.**
- **Least privilege everywhere.**
- **Governance independent from generation.**
- **Human review is a valid outcome.**
- **Tools require explicit authorization.**
- **Fail toward reduced authority.**
- **Auditability is architectural.**
- **Models and runtimes are replaceable.**
- **Security precedes autonomy.**
- **Trust claims require observable evidence.**
- **Reuse lessons, not legacy assumptions.**

## Working Design Statement

> **Nova Aegis is designed so that useful AI capability can operate inside an organization's controlled environment while evidence, authority, policy, and operational actions remain independently observable and governable.**

## Working Motto

**Private by location. Grounded by evidence. Governed by design.**
