# Nova Aegis Problem Statement

**Working principle:** Private by location. Grounded by evidence. Governed by design.

**Working North Star:**

> An organization should be able to use capable AI with sensitive internal knowledge without requiring that knowledge to leave its own computing environment, while preserving evidence provenance, bounded authority, auditability, and meaningful human oversight.

## 1. What Problem Exists?

Organizations increasingly need AI assistance over internal technical, operational, and policy knowledge. The organizations most likely to need this capability include:

- regulated environments;
- privacy-sensitive organizations;
- intellectual-property-sensitive organizations; and
- critical or operationally sensitive environments.

These organizations hold information that may be necessary for effective decision support but inappropriate to send to an external service during normal operation. The central data-boundary concern is therefore:

> Sensitive organizational data should not require external cloud processing during normal operation.

The problem is not only where a model runs. A local model can still produce unsupported claims, expose information to unauthorized users, invoke tools outside its authority, or make actions difficult to reconstruct after the fact. Nova Aegis addresses the combined problem of **private, evidence-grounded, bounded, and auditable AI assistance** for sensitive organizational work.

### Local-first definition

For Nova Aegis, **local-first** means that the normal operating path is designed to function within the organization-controlled computing environment. Sensitive documents, user requests, retrieved evidence, model inputs and outputs, policy decisions, and tool results remain on the workstation or authorized intranet unless an explicitly approved future design says otherwise. Internet access is not assumed and should be disabled during normal operation.

### Initial deployment boundary

The initial system is limited to:

- a single workstation or edge node;
- local storage;
- local inference;
- local or intranet-only tools; and
- no routine Internet dependency.

This boundary is intentional. It makes data flow inspectable, supports offline operation, and permits the MVP to be evaluated without introducing enterprise-scale distribution or cloud trust assumptions.

## 2. Why Current Approaches Are Insufficient

### Cloud-hosted AI services

Cloud services can provide capable models and convenient integrations, but their normal data path may require sensitive requests, documents, prompts, telemetry, or tool results to cross an organizational boundary. Contractual, configuration, or provider assurances do not by themselves provide the local operational boundary required by this use case.

### Local LLMs without controls

Running an LLM locally improves location control but does not establish trust. A standalone model does not inherently provide:

- reliable retrieval from authorized private knowledge;
- source provenance for its claims;
- a distinction between evidence and interpretation;
- handling for missing or conflicting information;
- policy enforcement before sensitive tool use;
- explicit human-review gates; or
- a complete audit trail.

Local execution alone does not make AI trustworthy.

### General-purpose autonomous agents

An unconstrained agent can combine retrieval, reasoning, memory, and tool execution in ways that make authority difficult to bound and decisions difficult to review. Nova Aegis requires explicit separation of responsibilities and does not treat model intent as authorization.

## 3. What Nova Aegis Intends to Provide

Nova Aegis intends to provide a local-first, human-on-the-loop decision-support system for sensitive organizational knowledge. It is designed around four cooperating components with strict authority boundaries.

### Desired behavior

A user should be able to ask an operational question in natural language. The system should:

1. identify the authorized knowledge and tools relevant to the request;
2. retrieve private evidence while preserving source identity and location;
3. give a reasoning component the task and evidence, clearly separated from generated interpretation;
4. evaluate support, authorization, policy compliance, and uncertainty;
5. return an answer with supporting evidence, provenance, assurance status, and warnings; and
6. request human approval before an action that requires it.

Retrieved evidence is not treated as automatically true. Model-generated interpretation is not presented as source evidence. The response contract must preserve that distinction.

### Evidence outcomes

- **Sufficient:** Evidence is relevant, authorized, and adequately supports the proposed answer. The system may return a `PASS`, subject to policy and action requirements.
- **Missing:** Required evidence is unavailable or retrieval confidence is inadequate. The system must avoid inventing an answer and return `REVIEW` or an explicit refusal.
- **Conflicting:** Relevant sources disagree or contain unresolved versions. The system must identify the conflict, lower assurance, and return `REVIEW` unless a governing source resolves it.
- **Outside authorized scope:** The requested information or action is not permitted for the current identity, domain, or policy context. The system must not disclose the information or execute the action and should return `FAIL` where a policy violation is established.

### Assurance statuses

- **PASS:** The response is sufficiently supported, within authorized scope, and permitted by applicable policy. A PASS does not imply that the model is infallible.
- **REVIEW:** Human assessment is required because evidence is incomplete, conflicting, ambiguous, low-confidence, or because the requested action exceeds the system's approval boundary.
- **FAIL:** The request or proposed action is prohibited, unauthorized, materially unsupported, or otherwise violates a hard policy constraint. The system must block the prohibited action.

Human approval is required whenever policy designates an action as approval-gated, when an external or consequential state change is proposed, when evidence is insufficient or conflicting for a consequential decision, or when assurance components disagree in a way that cannot be resolved deterministically.

### Auditability

The system must preserve auditable records for:

- user requests and identity context;
- retrieval queries, filters, selected evidence, and provenance;
- model inputs, outputs, and model identity;
- policy evaluations and assurance decisions;
- MCP tool calls, arguments, results, and errors;
- human approvals, denials, and reviewer identity; and
- executed or blocked actions and their outcomes.

Audit records should be append-oriented, access-controlled, timestamped, and sufficient to reconstruct the decision path without treating an audit log as permission to disclose sensitive content broadly.

## 4. Component Responsibilities and Authority

### NIC: evidence and retrieval

NIC is responsible for indexing and retrieving authorized private knowledge, applying retrieval isolation, returning evidence with provenance, and reporting retrieval quality or gaps. NIC does not decide whether an action is allowed and does not execute tools.

### Cortex: reasoning and orchestration

Cortex is responsible for organizing the task, synthesizing retrieved evidence, generating a proposed response or action plan, and coordinating bounded capabilities. Cortex may interpret evidence but cannot grant itself permissions, override policy, or execute unrestricted actions.

### Praetor: governance and assurance

Praetor is responsible for evaluating evidence support, assurance status, policy constraints, provenance requirements, disagreement, and human-review gates. Praetor can block or escalate a proposed response or action; it does not silently rewrite evidence or act as an unrestricted executor.

### Nova Aegis Core: control plane

Nova Aegis Core is responsible for routing, identity, permissions, logging, model access, configuration, and service coordination. It enforces component boundaries and records the decisions needed to audit the system.

No individual component or agent has unrestricted authority. In particular:

- retrieval does not authorize disclosure;
- reasoning does not authorize execution;
- governance does not become a general-purpose operator; and
- the control plane does not bypass evidence or policy checks for convenience.

## 5. Local AI Boundary

Microsoft Foundry Local is the initial inference runtime for the workstation or edge-node MVP. It was selected because it performs inference on the local device, can operate without routine Internet connectivity after required artifacts are provisioned, and uses ONNX Runtime with hardware-aware execution across available CPU, GPU, or NPU resources. This supports the local data boundary without requiring Nova Aegis to distribute hardware-specific inference logic throughout the application.

Foundry Local also provides a practical initial integration point for organizations that already use Microsoft-oriented enterprise infrastructure. Its SDK support for Python, C#, JavaScript, and Rust, together with OpenAI-compatible request and response formats, supports a clean application boundary while keeping the initial implementation accessible across supported development environments.

These benefits describe the initial platform choice, not a permanent architectural dependency. Once provisioned, the runtime and required models must support operation with Internet access disabled. Any future migration or integration path, such as other local inference engines, dedicated internal inference servers, on-premises enterprise platforms, or approved cloud inference services, must be evaluated against Nova Aegis requirements and policy rather than assumed to be available.

Foundry Local may provide a future migration path toward larger Microsoft-based deployments, including Microsoft Foundry or Foundry Local on Azure Local, if requirements later expand to larger infrastructure, centralized management, Kubernetes-based deployment, or hybrid cloud/on-premises operation. Such growth is outside the MVP and must not introduce an implicit cloud dependency.

Nova Aegis must treat Foundry Local as an **Inference Provider**, not as the architecture itself. The inference interface must remain provider-abstract so that Foundry Local can later be replaced without redesigning NIC, Cortex, Praetor, MCP integrations, policy enforcement, provenance, or audit capabilities.

> **Foundry Local is the initial engine, not the ecosystem.**

The initial model requirements are:

- runs on the target workstation or edge node;
- supports the required context size and structured response contract;
- provides a documented model identity and version;
- can operate without routine network access; and
- is evaluated for the MVP's retrieval, reasoning, and assurance tasks rather than assumed capable by name alone.

Required model and dependency artifacts must be available locally and cached in a controlled manner. Model and dependency updates/imports must use a documented, reviewable procedure that includes provenance, integrity verification, compatibility checks, and approval before introduction into the offline environment.

Permitted network behavior is limited to explicitly configured local or intranet services. Internet access should be disabled during normal operation, with any future update or import workflow treated as a separate controlled procedure rather than an implicit runtime fallback.

## 6. MCP and Tooling Boundary

MCP provides a structured interface between the system and local or intranet-only tools. The architecture must distinguish:

- **tool availability:** whether an MCP server and tool can be reached; and
- **tool authorization:** whether the current identity, request, evidence state, and policy permit its use.

Every tool must have least-privilege permissions covering its operations, data scope, target scope, and whether it is read-only or state-changing. Sensitive tool execution requires policy evaluation before invocation. State-changing or consequential tools may also require explicit human approval.

Each call must produce an audit record containing the requesting identity, tool and server identity, authorized scope, arguments or a protected representation of them, policy result, approval state, result, and error information.

If an MCP server is unavailable, the system must report the capability as unavailable and route to `REVIEW` or a safe read-only response where appropriate. It must not silently substitute an unauthorized tool or assume success. Unexpected, malformed, or policy-inconsistent tool data must be treated as untrusted, recorded, and blocked or escalated according to policy.

## 7. Initial MVP Use Case

The MVP will model a fictional technical organization and use a small private corpus made only from public or synthetic material. The corpus will include:

- technical procedures;
- internal-style policies;
- troubleshooting documentation;
- reference manuals; and
- intentionally conflicting or incomplete information for assurance testing.

A user will ask operational questions in natural language. NIC will retrieve supporting evidence. Cortex will reason over the task and evidence. Praetor will evaluate whether the proposed response is sufficiently supported and permitted. The result will contain:

- the answer or refusal;
- supporting evidence;
- provenance;
- assurance status (`PASS`, `REVIEW`, or `FAIL`); and
- relevant warnings or uncertainty.

The MVP must demonstrate:

- `REVIEW` when evidence is insufficient or conflicting;
- `FAIL` when a proposed action violates policy; and
- operation with Internet access disabled.

The MVP is a workstation experiment, not a claim that the design is production-ready for a regulated organization.

## 8. Success Criteria

The initial design and MVP are successful when:

- sensitive test data never leaves the workstation during normal operation;
- responses can be traced to the evidence used;
- unsupported claims can be detected or escalated;
- unauthorized tool actions can be blocked;
- human review can be explicitly requested;
- important events are auditable;
- the model runtime can be replaced without redesigning NIC, Cortex, or Praetor; and
- the MVP operates entirely on a workstation.

These criteria are necessary but do not by themselves constitute a security, compliance, or trust certification.

## 9. Explicit Non-Goals for the MVP

The MVP will not:

- build a general-purpose autonomous agent;
- attempt enterprise-scale multi-user serving;
- add cloud escalation;
- integrate real confidential organizational data;
- replace existing cybersecurity, IAM, or compliance platforms;
- claim that local execution alone makes AI trustworthy; or
- optimize for every possible model or hardware platform.

## 10. Conceptual Reference Sources

The following previous Nova Labs projects are design references only. They are not required dependencies, are not to be imported wholesale, and are not to be reproduced as-is. Nova Aegis will adopt a concept only when it solves a Nova Aegis problem and remains consistent with its own requirements and threat model.

- [PRAETOR_MCP](https://github.com/drosadocastro-bit/PRAETOR_MCP): governance, assurance, provenance, evidence validation, bounded behavior, policy enforcement, auditability, human-review gates, and MCP-oriented architecture.
- [nova_rag_public](https://github.com/drosadocastro-bit/nova_rag_public): local retrieval, evidence grounding, source traceability, offline operation, retrieval isolation, and hallucination mitigation.
- [Roswell-uap-cortex](https://github.com/drosadocastro-bit/Roswell-uap-cortex): domain-neutral ideas for orchestration, reasoning organization, memory, contextual synthesis, lessons learned, and coordination between specialized capabilities. UAP, Roswell, investigation-specific, domain-specific, dataset-specific, and subject-matter content is explicitly excluded.
- [PRAETOR_MCP_BICAMERAL](https://github.com/drosadocastrobit/PRAETOR_MCP_BICAMERA): complementary evaluation, deterministic and semantic checks, disagreement handling, and governed escalation. The repository name and architecture are not treated as an automatic design prescription.

Reference usage principles:

- extract concepts and lessons learned, not entire implementations;
- generalize domain-specific ideas before considering them;
- prefer clean interfaces over direct coupling to legacy code;
- document the origin of important adopted ideas when useful for traceability; and
- allow concepts to be rejected, simplified, or redesigned when they do not fit Nova Aegis requirements.

> Reuse what was learned, not necessarily what was built.
