# Orchestrator Templates

Use this reference when creating a skill that coordinates other skills, roles, or scripts.

## Template A: Supervisor Skill

Use when the harness needs a single entry point.

```markdown
---
name: {domain}-orchestrator
description: Coordinate {domain} Codex workflows. Use when users ask to plan, execute, review, repair, or continue {domain} work across multiple skills, phases, or validation gates.
---

# {Domain} Orchestrator

Coordinate {domain} work by classifying the request, selecting the smallest workflow, preserving handoffs, validating results, and producing one final answer.

## Request Classes

| Class | Use When | Workflow |
|---|---|---|
| audit | User asks for state, risk, or readiness | Audit -> report |
| implement | User asks for code or artifact changes | Audit -> plan -> edit -> validate |
| review | User asks for critique | Inspect -> findings -> tests |
| evolve | User reports repeated misses | Diagnose -> update harness -> validate |

## Workflow

### Phase 0: Context

- Inspect existing files and user changes.
- Read only references needed for the request class.
- State assumptions before editing.

### Phase 1: Route

- Choose one workflow from the request class table.
- Name child skills or scripts to use.
- Define output paths.

### Phase 2: Execute

- Run phases in order.
- Write temporary handoffs to `_workspace/` only when needed.
- Keep durable outputs in project paths.

### Phase 3: Review

- Run validation commands.
- Check handoff artifacts for required fields.
- Resolve contradictions before final response.

### Phase 4: Close

- Summarize files changed.
- Summarize validation.
- List remaining gaps.
```

## Template B: Pipeline Skill

Use when stages must run sequentially.

```markdown
## Pipeline

### Stage 1: Audit

Input:

- User request
- Current repository state

Output:

- Scope
- Constraints
- Validation commands

Done when:

- A bounded edit set is identified.

### Stage 2: Implement

Input:

- Audit output
- Relevant references

Output:

- File changes

Done when:

- Changes are scoped and internally consistent.

### Stage 3: Validate

Input:

- File changes
- Project commands

Output:

- Command results
- Residual risk

Done when:

- Required commands have passed or failures are explained.
```

## Template C: Fan-Out/Fan-In

Use when independent streams are useful.

```markdown
## Fan-Out/Fan-In

### Branches

| Branch | Scope | Evidence Required | Output |
|---|---|---|---|
| {branch-a} | {scope} | file paths, commands, sources | `_workspace/{branch-a}.md` |
| {branch-b} | {scope} | file paths, commands, sources | `_workspace/{branch-b}.md` |

### Fan-In

- Read all branch outputs.
- Deduplicate findings.
- Resolve contradictions.
- Rank findings by impact.
- Produce final artifact.
```

If sub-agents are available and explicitly requested, branches may be delegated. Otherwise, execute branches sequentially and preserve the same output protocol.

## Template D: Producer-Reviewer

Use when the first pass is likely to miss quality issues.

```markdown
## Producer-Reviewer

### Producer

- Create the artifact.
- Record assumptions.
- Include validation instructions.

### Reviewer

- Read the user request, artifact, and assumptions.
- Check contract, edge cases, tests, and consistency.
- Return one of: accept, accept-with-notes, revise, reject.

### Revision

- Address reviewer findings.
- Re-run validation.
- Summarize what changed.
```

## Workspace Rules

- Use `_workspace/00_input/` for copied task input when needed.
- Use `_workspace/{phase}_{role}_{artifact}.md` for intermediate handoffs.
- Never rely on `_workspace/` for final persistent docs unless the user requested it.
- Clean up temporary artifacts when they would confuse future runs.

## Error Handling

For every orchestrator, define:

- missing input handling
- failed command handling
- partial artifact handling
- conflicting branch output handling
- user-interrupt handling

Use this table:

```markdown
| Failure | Detection | Recovery |
|---|---|---|
| Missing input | {check} | Ask or infer with stated assumption |
| Validation fail | command exit != 0 | Fix if in scope, otherwise report |
| Conflicting outputs | fan-in contradiction | cite evidence and choose conservative result |
```

## Description Keywords

The `description` should include:

- domain name
- primary trigger verbs
- workflow categories
- continuation terms such as continue, follow-up, repair, evolve
- validation or review terms if the orchestrator owns QA
