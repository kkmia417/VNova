# Agent and Skill Design Patterns

Use this reference when a harness needs more than one workflow, role, or skill.

## Codex Execution Modes

Codex harnesses should describe reusable behavior in files, not rely on invisible runtime state.

### Single-Session Mode

Use one Codex session and one skill when:

- The task is linear.
- The user needs implementation, not parallel research.
- The validation commands are local and deterministic.
- The workflow can fit in one `SKILL.md` plus optional references.

### Script-Assisted Mode

Use scripts when a repeated step must be deterministic:

- validate skill structure
- scaffold files
- parse manifests
- compare generated artifacts
- run project checks

Scripts should be standard-library-only unless the project already depends on a package.

### Sub-Agent Delegation Mode

Use sub-agent delegation only when the active Codex runtime provides sub-agent tools and the user has explicitly asked for delegation, parallel agents, or agent-team work. Otherwise, encode the role as a skill or prompt protocol.

Good uses:

- parallel audits with disjoint scopes
- independent reviewer passes
- worker agents editing non-overlapping file sets
- validation while the main agent implements separate files

Do not delegate just to imitate an agent team. Delegation has coordination cost.

### External Automation Mode

Use external CLIs, CI, or scripts when the harness should run outside the current Codex session.

Good uses:

- repository-wide validation
- release checks
- code generation
- schema extraction

## Architecture Patterns

### 1. Single Skill

Use for a compact repeated workflow with one owner.

Structure:

```text
SKILL.md -> references as needed -> scripts as needed
```

Risk: the skill can become a junk drawer. Split when sections gain different triggers or validation.

### 2. Pipeline

Use when stages must run in order.

Typical stages:

1. Audit.
2. Plan.
3. Implement.
4. Validate.
5. Summarize.

Require each stage to produce a handoff artifact or explicit state summary.

### 3. Fan-Out/Fan-In

Use when independent branches can run in parallel and then need synthesis.

Examples:

- architecture, security, performance, and style review
- multiple source research
- package-by-package monorepo impact analysis

Require every branch to provide evidence. The synthesis step must resolve conflicts.

### 4. Expert Pool

Use when the user may ask for one of several specialties.

Examples:

- frontend skill
- backend API skill
- database skill
- release skill
- QA skill

Avoid a supervisor until users regularly ask broad tasks that require routing.

### 5. Producer-Reviewer

Use when quality depends on critique.

Examples:

- implementation + code review
- documentation draft + accuracy review
- prompt generation + adversarial test

The reviewer must have permission to reject output or request changes.

### 6. Supervisor

Use when a top-level skill should classify requests and choose workflows.

The supervisor owns:

- request classification
- skill selection
- context gathering
- handoff format
- final synthesis

The supervisor should not duplicate the detailed instructions of child skills.

### 7. Hierarchical Delegation

Use only for large domains where a supervisor routes to sub-orchestrators.

Good for:

- large monorepos
- regulated document systems
- full product launch factories

Document ownership boundaries clearly. Deep hierarchy becomes stale quickly.

## Role Specification Template

Use this shape before deciding whether a role deserves its own skill:

```markdown
## Role: {name}

- Mission:
- Inputs:
- Outputs:
- Required tools:
- References to read:
- Validation:
- Failure handling:
- Should be implemented as: skill | orchestrator section | script | prompt template
```

## Skill vs Role

Create a skill when:

- Users invoke the workflow directly.
- The workflow has stable trigger phrases.
- It needs reusable references or scripts.
- It can be validated independently.

Keep a role inside an orchestrator when:

- It is never invoked alone.
- It only describes a phase of a larger flow.
- It shares all references and validation with the parent skill.

Use a script when:

- The behavior is mechanical.
- Failure should be deterministic.
- A human-readable prompt would be less reliable than code.

## Split Criteria

Split roles when at least two of these are true:

- different input artifacts
- different output artifacts
- different validation commands
- different failure modes
- different trigger phrases
- different domain references
- different cadence of change

Keep roles together when they only differ by label.

## Handoff Protocol

Every multi-role workflow needs a handoff contract:

```markdown
## Handoff

- Producer:
- Consumer:
- Artifact path:
- Required fields:
- Done criteria:
- Validation command:
- Escalation condition:
```

Use `_workspace/` for temporary handoffs and project paths for durable outputs.
