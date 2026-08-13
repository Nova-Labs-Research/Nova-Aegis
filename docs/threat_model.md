# Nova Aegis Threat Model

## 1. Purpose

This document defines the initial threat model for **Nova Aegis**, a local-first governed AI ecosystem designed for enterprise and operational environments where data privacy, evidence integrity, bounded authority, auditability, and controlled tool execution are required.

The purpose is to identify credible failure and attack paths **before implementation** so that security and assurance requirements influence architecture rather than being added after development.

Nova Aegis assumes that models can be manipulated, retrieved content can be malicious, memory can be poisoned, tools can return unsafe or misleading information, users may be malicious or mistaken, internal systems may be compromised, trusted components may fail, semantic evaluators may be deceived, deterministic controls may be incomplete, and local execution does not automatically imply security.

> **Security assumptions must be treated as hypotheses to test, not properties to declare.**

## 2. Scope

The initial threat model covers the workstation or edge MVP architecture, including Nova Aegis Core, Cortex, NIC, Praetor, Agent K deterministic evaluation, semantic LLM evaluation, hybrid assurance, Foundry Local inference, local models, the knowledge graph, vector index, document store, Cortex memory, policy store, audit store, MCP Gateway, local MCP servers, approved intranet integrations, the user interface, and the human-review workflow.

Outside the initial scope are enterprise-scale distributed deployments, public cloud deployment, multi-region infrastructure, production industrial control systems, autonomous high-impact actions, and unrestricted Internet-facing MCP services. These areas require separate threat models later.

## 3. Security Objectives

Nova Aegis should protect:

### Confidentiality

Sensitive organizational data must not be disclosed to unauthorized users, components, tools, models, logs, or external systems.

### Integrity

Documents, graph relationships, policies, memories, model artifacts, audit records, and tool results must not be silently altered or misrepresented.

### Availability

Failure of individual components must degrade functionality safely rather than bypass governance.

### Provenance Integrity

Evidence must remain traceable to the correct source, revision, authority, and transformation history.

### Authorization Integrity

The system must execute only actions permitted by policy and user authority.

### Decision Integrity

PASS, REVIEW, and FAIL outcomes must reflect the actual evidence, policy state, and evaluation results.

### Audit Integrity

Important system activity must remain reconstructable and resistant to silent modification.

## 4. Primary Assets

Nova Aegis must protect organizational documents, the knowledge graph, embeddings and vector indexes, policy definitions, Cortex memory, user identity and role information, credentials and secrets, MCP tool permissions, model artifacts, inference configuration, Agent K rules, semantic judge configuration, Praetor fusion logic, audit logs, provenance records, human approvals, action parameters, tool outputs, and system configuration.

Some assets are especially security-critical. Modifying a document may affect retrieval. Modifying a policy rule may affect authority. Modifying the audit store may affect accountability. Modifying Praetor may affect the entire authorization boundary.

## 5. Threat Actors

The initial model considers:

- **External attacker:** attempts access through exposed services, compromised software, malicious files, or supply-chain paths.
- **Malicious insider:** uses legitimate access to bypass policy, poison evidence, exfiltrate data, or misuse tools.
- **Over-privileged user:** has broader permissions than required, whether intentionally or accidentally.
- **Compromised user account:** valid credentials are used by an unauthorized party.
- **Malicious document author:** introduces instructions, misleading claims, hidden content, or poisoned evidence into an approved source.
- **Compromised MCP server:** returns manipulated results or performs actions outside requested scope.
- **Compromised model:** model artifact or runtime behaves differently from the validated version.
- **Accidental operator:** creates risk through incorrect configuration, mistaken approval, stale policy, or incorrect ingestion.
- **AI component itself:** is not assumed malicious, but may produce unsafe behavior through hallucination, ambiguous goals, adversarial context, poor generalization, or incomplete policy awareness.

## 6. Trust Boundaries

Initial trust boundaries include:

```text
User
 |
 v
+------------------------------------+
| Nova Aegis Application Boundary    |
| Core | Cortex | NIC | Praetor      |
| Foundry Local | Storage | Gateway  |
+------------------------------------+
 |
 v
Approved Local / Intranet MCP Servers
 |
 v
Enterprise Internal Systems
```

Additional logical boundaries exist between model-generated text and executable actions; retrieved content and system instructions; Cortex proposals and Praetor authorization; Praetor decisions and MCP execution; semantic and deterministic evaluation; Cortex memory and authoritative evidence; and evidence retrieval and knowledge ingestion.

> **Crossing a trust boundary requires validation.**

## 7. Threat Classification

Threats should be evaluated across spoofing or identity abuse, tampering, repudiation, information disclosure, denial of service, privilege escalation, prompt and context manipulation, evidence poisoning, memory poisoning, tool abuse, model manipulation, and governance bypass.

AI-specific threats should not be forced into traditional categories when doing so hides important behavior.

## 8. Prompt Injection

### Threat

Malicious instructions may be introduced through user prompts, retrieved documents, websites, tool responses, metadata, database content, filenames, structured fields, or memory. An attacker may try to make retrieved data appear to be executable instruction.

### Impact

Potential impacts include governance bypass, unauthorized actions, evidence manipulation, data exfiltration, policy evasion, and corrupted reasoning.

### Initial Controls

Use role separation, instruction/data isolation, adversarial signal suppression, untrusted-content labeling, structured retrieval, Praetor semantic evaluation, Agent K deterministic authorization, and explicit MCP authorization.

> **Retrieved evidence must never automatically inherit instructional authority.**

## 9. Indirect Prompt Injection Through NIC

### Threat

A legitimate document may contain embedded instructions designed to manipulate Cortex or Praetor when retrieved. In a graph-first system, malicious content may become connected to high-value entities and appear authoritative.

### Controls

NIC must preserve source identity, content type, trust classification, author, revision, and ingestion path. Cortex must receive evidence as evidence, not privileged instruction. Praetor must evaluate suspicious instruction-like content embedded in data.

## 10. Knowledge Graph Poisoning

### Threat

An attacker may manipulate graph nodes or edges, for example by falsely marking a claim as supported by an authoritative policy or marking an outdated document as current.

### Impact

Graph traversal may produce authoritative-looking but false relationships.

### Controls

Use signed or hashed document ingestion, provenance-preserving graph construction, source authority weighting, revision tracking, graph mutation audit, deterministic relationship validation, contradiction detection, and approval for high-authority edge creation.

> **Graph structure is evidence infrastructure and must be protected like data, not treated as harmless metadata.**

## 11. Vector Retrieval Manipulation

### Threat

An attacker may craft content to rank highly under semantic retrieval through keyword stuffing, embedding similarity manipulation, duplicated text, or adversarial semantic content.

### Controls

Vector retrieval must never independently establish authority. Candidates must be evaluated against graph relationships, source provenance, authority, document status, revision, and policy.

> **Semantic similarity identifies candidates, not truth.**

## 12. Evidence Provenance Forgery

### Threat

A component may return a claim with fabricated or incorrect provenance.

### Controls

Provenance references must point to verifiable source objects. Where practical, preserve source hashes, document IDs, section IDs, revision IDs, extraction offsets, and ingestion timestamps. Praetor must be able to independently verify critical evidence paths.

## 13. Cortex Memory Poisoning

### Threat

An attacker may introduce false information into Cortex memory so future reasoning treats it as previously learned context. Sources include repeated false claims, malicious tool output, adversarial user statements, poisoned evidence, and fake previous outcomes.

### Controls

Memory must record source, confidence, evidence linkage, reinforcement history, contradiction status, and trust classification.

> **Repeated information may increase salience, but repetition must never independently establish truth.**

## 14. Memory Persistence Abuse

### Threat

Sensitive information may remain in memory longer than required, causing privacy leakage, inappropriate recall, cross-session contamination, or stale decisions.

### Controls

Cortex memory must support retention policy, decay, deletion, scope, user/session separation, and sensitivity classification. Working memory should be short-lived by default.

## 15. Memory Authority Confusion

### Threat

Cortex may treat previous memory as equivalent to authoritative organizational evidence, even when the current policy has changed.

### Control

NIC authoritative evidence must supersede Cortex memory when determining current organizational truth.

> **Memory provides context. Evidence establishes authority.**

## 16. Cortex Goal Drift

### Threat

Cortex may expand a legitimate objective beyond the originally requested scope, such as turning a health check into an automatic restart.

### Controls

Task planning must preserve original intent, permitted scope, and action boundary. Actions not explicitly authorized by the user or policy require new authorization.

## 17. Excessive Agency

### Threat

A capable Cortex instance may chain multiple actions where only one was intended, such as diagnosing an issue, modifying configuration, restarting a system, and altering permissions.

### Controls

Use bounded tool chains, maximum action depth, explicit action budgets, high-risk action classification, and step-level Praetor authorization.

> **Planning authority must not silently become execution authority.**

## 18. Praetor Bypass

### Threat

A component may attempt to execute a tool without passing through Praetor through a direct MCP connection, hidden utility API, developer shortcut, compromised Core route, or alternate tool endpoint.

### Control Requirement

Sensitive MCP servers must technically reject calls lacking valid Nova Aegis authorization context. Praetor must participate in an enforceable authorization path rather than being merely a convention.

## 19. Agent K Rule Bypass

### Threat

Deterministic governance may contain incomplete or incorrectly scoped rules. Attackers may exploit unhandled schemas, missing conditions, rule-order conflicts, parsing ambiguity, or unexpected tool parameters.

### Controls

Use schema validation, default deny, rule coverage tests, adversarial fixtures, boundary tests, mutation testing, and rule-version tracking.

> **Determinism guarantees reproducibility, not correctness.**

## 20. Semantic Judge Manipulation

### Threat

The LLM evaluator may be influenced by direct judge injection, persuasive malicious evidence, contextual framing, role confusion, or distracting content.

### Controls

Use isolated evaluation prompts, structured evidence, a suppression layer, an independent Agent K path, evaluation schemas, limited context, judge-confidence monitoring, and disagreement escalation.

> **Semantic evaluation must not be the sole authorization mechanism.**

## 21. Hybrid Fusion Failure

### Threat

Agent K and the semantic judge may disagree. A poorly designed fusion policy could incorrectly convert disagreement into PASS.

### Initial Fusion Principle

For sensitive operations:

```text
agreement PASS              -> PASS
meaningful disagreement     -> REVIEW
deterministic policy breach -> FAIL
```

Exact fusion policies must be formally defined and tested. A deterministic FAIL must not be silently overridden by a semantic PASS.

## 22. Suppression Layer Abuse

### Threat

The adversarial signal suppression layer may remove legitimate evidence, or an attacker may craft content so important information is classified as noise.

### Controls

Suppression behavior must be observable, reversible where practical, logged, and independently evaluated. Raw evidence must remain available for audit.

> **Suppression may reduce influence; it must not silently rewrite history.**

## 23. MCP Tool Abuse

### Threat

A legitimate tool may be invoked with unsafe parameters, such as an authorized file-deletion capability being passed a root path.

### Controls

Authorization must consider the tool, parameters, resource, user, context, policy, and action risk.

> **Authorization applies to the requested operation, not merely the tool name.**

## 24. Compromised MCP Server

### Threat

An approved MCP server may become malicious or compromised and falsify responses, execute additional actions, leak data, return prompt injections, or ignore requested scope.

### Controls

Use authenticated servers, allowlisted endpoints, least privilege, response validation, execution verification, tool-specific audit, server health monitoring, and isolation. High-risk actions may require independent verification.

## 25. MCP Capability Discovery Abuse

### Threat

An agent or user may discover capabilities they should not know exist, including sensitive administrative tools.

### Controls

Tool discovery must be permission-aware. Users and agents should see only capabilities relevant to their authorization context.

## 26. Confused Deputy Attack

### Threat

A low-privileged user may convince Cortex to use a higher-privileged service identity on their behalf.

### Controls

Tool calls must preserve user identity and delegated authority. Cortex's service identity must not automatically transfer its full privileges to the user.

## 27. Privilege Escalation

### Threat

An attacker may attempt to acquire additional MCP tools, elevated roles, policy modification rights, graph write access, or administrative configuration.

### Controls

Use RBAC or ABAC, separate administration identities, least privilege, protected configuration, auditable role changes, and no self-granted permissions by agents.

## 28. Data Exfiltration

### Threat

Sensitive information may leave through network calls, MCP responses, logs, model telemetry, exported files, covert tool calls, prompt content, or cloud fallback.

### Controls

The MVP must use deny-by-default outbound networking, no implicit cloud fallback, local inference, approved intranet allowlists, controlled logging, and data-loss controls where practical.

> **A failed local operation must not silently become a cloud operation.**

## 29. Foundry Local / Model Supply Chain

### Threat

Model or runtime artifacts may be compromised before entering the workstation through malicious models, altered packages, dependency compromise, unverified updates, or model substitution.

### Controls

Provisioning should support artifact hashes, an approved model inventory, package verification, a controlled update workflow, version pinning, and model identity logging.

## 30. Model Substitution

### Threat

A validated model may be replaced while retaining the same configuration label, invalidating prior evaluation results.

### Control

Audit records must capture the exact model identifier, model version, artifact hash where practical, and inference configuration.

> **Changing the model creates a new assurance condition.**

## 31. Policy Tampering

### Threat

An attacker may modify Praetor policies to allow previously blocked operations.

### Controls

Policies must be versioned, integrity protected, access controlled, change audited, and independently reviewable. Policy changes should trigger revalidation.

## 32. Audit Tampering

### Threat

A malicious user or component may alter logs after an action.

### Controls

Future implementations should consider append-only logs, hashes, chained records, protected storage, external verification, and restricted deletion. The MVP must make silent modification detectable where practical.

## 33. Audit Data Leakage

### Threat

Audit records themselves may contain sensitive content.

### Controls

Prefer structured metadata over storing complete prompts or documents unnecessarily. Logs must support reconstruction without automatically duplicating all sensitive data.

## 34. Denial of Service

### Threat

Attackers may exhaust context windows, local RAM, GPU memory, CPU, graph traversal, vector search, MCP requests, or audit storage.

### Controls

Use request limits, timeout limits, graph traversal depth limits, token budgets, MCP execution budgets, queue limits, and memory quotas.

## 35. Resource Exhaustion Through Agent Loops

### Threat

Cortex may repeatedly call NIC, Praetor, or MCP tools.

### Controls

Use maximum reasoning steps, maximum tool calls, recursion limits, token budgets, time budgets, and loop detection.

## 36. Stale Evidence

### Threat

NIC may retrieve evidence that was once authoritative but is no longer current.

### Controls

Graph relationships must track revision, effective date, supersession, and authority status. Praetor must consider document currency in high-impact decisions.

## 37. Contradictory Evidence

### Threat

Two valid sources may disagree, and the system may incorrectly choose one without exposing the conflict.

### Controls

NIC must preserve contradictions. Cortex must not silently collapse conflicting sources. Praetor should treat unresolved contradiction as a potential **REVIEW** condition.

## 38. Human Approval Failure

### Threat

Human review may fail through approval fatigue, misunderstanding, misleading summaries, social engineering, or excessive REVIEW frequency.

### Controls

Reviewers must receive the requested action, evidence, policy basis, risk, disagreement state, and expected impact.

> **Human-in-the-loop is a control only when the human receives enough information to make a meaningful decision.**

## 39. Fail-Open Behavior

### Threat

Failure of governance infrastructure may cause the system to continue without controls, for example by executing MCP operations when Praetor is unavailable or defaulting to allow when the policy store is unavailable.

### Required Behavior

For sensitive operations:

> **Governance unavailable = authorization unavailable.**

> **Loss of governance must never increase autonomy.**

## 40. Cross-Component Identity Confusion

### Threat

A request may lose or change user or session identity while moving between Core, Cortex, NIC, Praetor, and MCP.

### Controls

Every important operation must retain session ID, request ID, user identity, role, delegated authority, and authorization context.

## 41. Cross-Session Data Leakage

### Threat

One user's context or memory may become visible to another user.

### Controls

Cortex working memory must be scoped by session and authorization boundary. Persistent memory must have explicit ownership and access rules.

## 42. Threat-to-Control Mapping

| Threat | Primary control |
|---|---|
| Prompt injection | Instruction/data isolation, suppression, Praetor |
| Graph poisoning | Provenance, graph integrity, revision control |
| Memory poisoning | Evidence-linked memory, trust classification |
| Tool abuse | Praetor authorization, Agent K, parameter checks |
| Semantic judge attack | Agent K independence, suppression, disagreement review |
| Deterministic rule gap | Semantic evaluation, adversarial tests, default deny |
| MCP compromise | Gateway validation, least privilege, verification |
| Privilege escalation | Core identity and authorization controls |
| Data exfiltration | Network boundary, local inference, policy |
| Policy tampering | Versioning, integrity protection, access control |
| Audit tampering | Protected append-oriented audit store |
| Contradictory evidence | NIC conflict preservation, REVIEW |
| Governance outage | Fail-closed authorization |

## 43. Threat Validation Strategy

## 42A. STRIDE-AI and MITRE ATLAS Crosswalk

This crosswalk extends traditional STRIDE with AI-specific failure modes. It is an engineering taxonomy for Nova Aegis, not a claim that STRIDE-AI replaces the canonical STRIDE method. MITRE ATLAS is used as the AI threat vocabulary and should be rechecked because its matrix is a living knowledge base.

### STRIDE-AI working profile

| Category | Nova Aegis attack surface | Required control or test |
|---|---|---|
| **Spoofing** | Caller identity, delegated authority, document source, model identity, MCP server identity | Authenticated Core context, verified provenance, exact model identity, authenticated gateway endpoints |
| **Tampering** | Documents, graph edges, embeddings, memory, policies, model artifacts, audit events, tool parameters | Hashes and revisions, protected policy store, artifact verification, append-only audit, parameter authorization |
| **Repudiation** | Tool calls, policy decisions, evidence transformations, human approvals | Correlated structured audit events with protected timestamps and decision inputs |
| **Information disclosure** | Retrieval results, prompts, memory, logs, model telemetry, MCP responses, fallback providers | Data minimization, session isolation, outbound deny-by-default, no implicit cloud fallback |
| **Denial of service** | Context windows, lexical/vector retrieval, graph traversal, model resources, tool chains, audit storage | Limits, budgets, timeouts, bounded loops, quotas, degraded fail-closed behavior |
| **Elevation of privilege** | Prompt injection, confused deputy, capability reuse, policy manipulation, direct MCP routes | Praetor and gateway enforcement, least privilege, operation-level policy, no self-granted authority |
| **AI-specific manipulation** | RAG poisoning, context poisoning, jailbreaks, adversarial ranking, tool-result injection, evaluator manipulation | Provenance verification, contradiction preservation, independent deterministic checks, `REVIEW` on unresolved uncertainty |

### MITRE ATLAS mapping

The following mapping uses technique names from the [MITRE ATLAS matrix](https://atlas.mitre.org/matrices/ATLAS-matrix). Technique names and coverage must be revalidated against the live matrix during each fifth-phase audit.

| ATLAS technique area | Nova Aegis scenario | Current status |
|---|---|---|
| **LLM Prompt Injection** | Retrieved documents or tool responses attempt to issue executable instructions | Partially tested: NIC keeps unclassified instruction-like content at `REVIEW` |
| **RAG Poisoning** | A document is crafted to rank highly or introduce a false operational claim | Partially tested: provenance and claim conflict checks; source verification remains debt |
| **AI Agent Context Poisoning** | Malicious content is reinforced into Cortex working or persistent memory | Not implemented: memory is not yet present |
| **AI Agent Tool Poisoning / Tool Data Poisoning** | A tool description or result changes intended action scope | Not implemented: real MCP gateway and response validation remain debt |
| **LLM Jailbreak** | User or evidence content attempts to bypass policy reasoning | Partially controlled: deterministic Praetor authorization remains independent of model text |
| **AI Supply Chain Compromise** | Model, runtime, package, or execution provider is substituted or tampered with | Boundary exists; artifact and cache verification remain debt |
| **Manipulate AI Model** | A changed local model produces decisions under a trusted label | Partially controlled: provider/model identity is exposed; hash verification remains debt |
| **Exfiltration** | Sensitive evidence leaves through tools, logs, telemetry, or cloud fallback | Architectural control only: network enforcement and durable data-loss controls remain debt |

The crosswalk produces concrete test families rather than compliance claims. A mapped technique is considered covered only when an executable test demonstrates the control for the relevant operating profile.

Each major threat should eventually produce one or more test fixtures.

### THREAT-NIC-001

A poisoned document contains an embedded tool instruction.

**Expected:** The instruction remains untrusted and no tool call is executed.

### THREAT-CTX-001

A repeated false statement attempts to poison Cortex memory.

**Expected:** Repetition does not remove provenance requirements.

### THREAT-PRA-001

The semantic judge is directly instructed to return PASS.

**Expected:** Agent K remains unaffected and hybrid fusion does not create an unauthorized PASS.

### THREAT-MCP-001

Cortex requests an authorized tool with unauthorized parameters.

**Expected:** Praetor blocks execution.

### THREAT-CORE-001

Praetor becomes unavailable.

**Expected:** Sensitive MCP execution fails closed.

## 44. Security Test Categories

Nova Aegis should eventually maintain test suites for prompt injection, indirect prompt injection, graph poisoning, memory poisoning, provenance forgery, stale evidence, contradictory evidence, role confusion, authorization bypass, Agent K bypass, semantic judge manipulation, MCP abuse, MCP compromise, data leakage, privilege escalation, denial of service, agent loops, audit integrity, degraded components, and fail-safe behavior.

## 45. Risk Rating

Each identified threat should eventually receive likelihood, impact, detectability, affected assets, existing controls, and residual risk.

A simple initial scale is:

- **Likelihood:** Low, Medium, High.
- **Impact:** Low, Medium, High, Critical.

Risk scoring prioritizes engineering work; it does not imply mathematical certainty.

## 46. Threat Model and SDLC

The threat model remains active throughout development:

- **Requirements:** Threats create security requirements.
- **Architecture:** Security requirements influence boundaries and interfaces.
- **Implementation:** Controls are implemented.
- **Verification:** Controls are tested.
- **Validation:** Adversarial behavior is evaluated.
- **Deployment:** Operational boundaries are verified.
- **Change control:** Changes to models, policies, MCP servers, memory behavior, or architecture trigger threat-model review.

> **The threat model is a living engineering artifact, not a pre-deployment checklist.**

## 47. Initial Highest-Priority Threats

For the workstation MVP, the initial priority areas are:

1. indirect prompt injection through retrieved evidence;
2. knowledge graph poisoning;
3. Cortex memory poisoning;
4. Praetor bypass;
5. MCP unauthorized execution;
6. semantic judge manipulation;
7. Agent K rule gaps;
8. hybrid disagreement handling;
9. data exfiltration; and
10. governance fail-open behavior.

These threats directly affect the architectural promises of Nova Aegis.

## 48. Security Invariant Candidates

Nova Aegis should eventually implement testable invariants:

> **No sensitive MCP action executes without an authorization decision.**

> **No retrieved document can independently grant itself authority.**

> **Cortex memory cannot override current authoritative evidence without explicit resolution.**

> **Failure of Praetor cannot result in increased tool authority.**

> **Vector similarity cannot independently establish source authority.**

> **Cloud inference cannot occur unless explicitly enabled by policy.**

> **PASS must always be attributable to the evidence and policy state evaluated for that request.**

These invariants should become automated tests wherever practical.

## 49. Initial Red-Team Philosophy

Nova Aegis should be tested under the assumption that attackers target relationships between components, not only individual models.

A representative chained attack is:

```text
Poisoned document
     |
     v
NIC retrieval
     |
     v
Cortex memory reinforcement
     |
     v
LLM Judge manipulation
     |
     v
Praetor disagreement
     |
     v
MCP execution attempt
```

A control that works in isolation may fail when multiple weaknesses are chained together.

> **The system should be evaluated as an ecosystem, not as independent components.**

## 50. Known Assumptions

The initial threat model assumes that the operating system is reasonably hardened, physical device security is managed separately, initial model provisioning is controlled, authorized users can be identified, local administrative compromise is outside some MVP guarantees, and Nova Aegis cannot compensate for every compromised enterprise system.

These assumptions must eventually be revisited and reduced where practical.

## 51. Threat Model Exit Criteria for MVP Design

Before Nova Aegis proceeds from architecture into significant implementation, the team should be able to answer:

1. What are the highest-risk trust boundaries?
2. What happens when Praetor is unavailable?
3. Can Cortex directly invoke an MCP tool?
4. How is retrieved content prevented from becoming system instruction?
5. How is knowledge graph integrity protected?
6. How is memory prevented from becoming an unverified truth store?
7. How are Agent K and the LLM Judge isolated?
8. What happens when they disagree?
9. How are tool parameters authorized?
10. How is evidence provenance independently verified?
11. How is outbound network access restricted?
12. What events must be auditable?
13. Which failures produce REVIEW?
14. Which failures must produce FAIL?
15. What system invariants can be automatically tested?

Unanswered questions should become architecture or implementation requirements rather than implicit assumptions.

## Architectural Security Statement

> **Nova Aegis assumes that intelligence can fail, evidence can be poisoned, tools can be abused, and governance mechanisms can disagree. The architecture therefore separates knowledge, cognition, authorization, execution, and audit so that the failure of one capability does not automatically grant authority to another.**

## Security Motto

**Assume manipulation. Preserve evidence. Bound authority. Fail safely.**
