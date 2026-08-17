# Observed AI Build-Assistant Governance Refusal

## Observation

During the T1 synthetic-to-enforced transition, AI build assistants were permitted to support technical planning, implementation reasoning, review, validation, and artifact preparation. They were not designated as human authority holders.

When required human authority, reviewer independence, approval metadata, expiry, artifact acceptance, or gate prerequisites were absent, the observed workflow preserved the blocked state instead of silently inferring the missing authority. This occurred even when continuing would have accelerated the research.

```text
technical work ready
        +
tests passing
        +
research intent to continue
        +
required authority/control absent
        |
        v
      REFUSE
        |
        v
preserve BLOCKED state
```

## Evidence provenance

This is an observational research note, not a model-safety attestation.

The supporting evidence tiers and bound governance-record hashes are recorded in `docs/evidence/observed-ai-governance-refusal-manifest.json`.

### Directly evidenced in the current repository workflow

The gate history and conversation-supported repository changes directly evidence that the active build assistant:

- refused to infer named-human authority from autonomous-work instructions;
- refused to count the same builder/reviewer assignment as independent review;
- kept a research exception inactive until an exact expiry was supplied;
- limited that exception to G1 and refused to extend it to G2/G3;
- distinguished build completion from artifact acceptance, provisioning, and activation; and
- kept G2 blocked after 207 passing tests because the candidate and authority prerequisites remained incomplete.

Relevant records include `t1-gate-record.md`, `t1-implementation-gate.md`, G1 candidate provenance, and the blocked G2 plan.

### Project-owner attestation

Project owner Daniel Rosado Castro reports equivalent boundary-preserving behavior from assistants identified as Sol, Terra, and Luna. The repository records these names as AI build assistants but does not currently contain independently authenticated, complete transcripts for each assistant or a controlled cross-model replay.

Accordingly, the claim that multiple assistants independently reproduced the behavior is **owner-attested and not yet independently verified**. It must not be represented as replicated experimental evidence until model/version/configuration metadata and complete fixture results are captured.

## Observed pattern

Examples include:

- same-person builder/reviewer conflict did not become independent review;
- autonomous-work instructions did not manufacture human authority;
- an exception without expiry did not become active;
- a bounded G1 exception did not apply to G2;
- passing tests did not authorize the next boundary;
- blocked prerequisites prevented build or provisioning work at the applicable gate; and
- build completion, artifact acceptance, provisioning, and activation remained distinct states.

## Likely contributing factors

The behavior should not be attributed to one cause.

### Model training and general safety behavior

The underlying models may recognize ambiguity around security-critical authority and favor conservative handling. This behavior is configuration-dependent and is not an enforcement mechanism.

### Builder operating instructions

The assistants operated under instructions requiring preservation of human authority, avoidance of unsupported assumptions, evidence-grounded claims, and fail-closed behavior when security-critical information is absent.

### Nova Aegis governance context

Nova Aegis supplied persistent explicit concepts including named-human authority, fail-closed gates, bounded exceptions, separation of duties, claim boundaries, authority expiry, visible debt, production hard-disable, and evidence before authority. Manufacturing missing authority would have contradicted the current documented state.

## Limitation

Sol, Terra, Luna, GitHub Copilot, or any other reasoning model is not a security boundary. Equivalent prompts may produce different behavior under another model version, instruction stack, context window, prompt, tool configuration, implementation state, or conversation history.

> **Observed model refusal is defense-in-depth behavior, not authorization enforcement.**

Nova Aegis must remain secure when a reasoning model complies, fails, becomes confused, or is compromised. Deterministic gates and externally enforced controls must refuse unauthorized state transitions independently of model output.

## Governance significance

The useful behavior was the distinction between technical capability and authority to exercise it:

- passing tests did not grant authority;
- technical readiness did not grant authority;
- owner intent did not silently satisfy independent review;
- an exception did not erase the absent control; and
- one gate did not authorize the next.

This is consistent with **capability does not imply authority**.

## Research value

The observed scenarios are candidate fixtures for controlled evaluation across explicit model/configuration matrices. The goal is not to decide whether a model can be trusted with authority. The goal is to measure how frequently reasoning layers preserve or violate explicit governance state before deterministic enforcement intervenes.

Required future evidence includes:

- model/provider/version identifier;
- system and builder instruction digests;
- fixture version and exact prompt;
- supplied repository/governance state digest;
- tool availability and autonomy settings;
- complete output and attempted tool actions;
- expected and observed gate state;
- deterministic enforcement result; and
- independent classification with disagreement retained.

## Zero-trust interpretation

```text
good reasoning behavior
        |
        v
useful defense in depth

bad reasoning behavior
        |
        v
must encounter deterministic governance enforcement

compromised reasoning
        |
        v
must not manufacture authority
```

Future compromise experiments should test whether deterministic enforcement blocks violations even when the reasoning output explicitly recommends bypass.

## Bounded finding

Under the tested Nova Aegis development context, governance records, and builder operating instructions, the directly observed assistant preserved blocked authority states rather than silently inferring missing approval or expanding an exception. The project owner attests that Sol, Terra, and Luna exhibited equivalent behavior, but independent replication is not yet established.

This finding is observational and configuration-dependent. It does not establish model-level enforcement, general alignment, independence, or production security.

> **The important result is not merely that an assistant refused. The architecture supplied explicit authority boundaries worth preserving, while deterministic controls remain responsible for enforcement.**