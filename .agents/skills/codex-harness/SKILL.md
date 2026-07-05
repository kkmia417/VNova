---
name: codex-harness
description: Design, generate, audit, validate, and evolve reusable Codex project harnesses. Use when asked to build a Harness-like system for Codex, create project-specific skills or skill teams, define orchestration patterns, scaffold repository-local skills, review an existing harness, synchronize skills with project workflows, or improve a harness based on repeated Codex misses.
---

# Codex Harness

Build a project harness: a versioned system of Codex skills, references, scripts, assets, validation checks, and project pointers that turns a repository or domain into repeatable Codex workflows.

This is the Codex-oriented counterpart to a team-architecture factory. Codex does not use Claude's `.claude/agents` format, so express durable roles as skills, orchestrator skills, prompt protocols, deterministic scripts, and optional sub-agent delegation when the current Codex runtime explicitly supports and authorizes it.

## Workflow

### Phase 0: Current-State Audit

Start by inspecting what already exists.

- List existing `skills/`, `.codex/`, `.claude/`, contributor docs, scripts, tests, CI, package manifests, and generated artifacts.
- Identify project languages, frameworks, package managers, command runners, and deployment surfaces.
- Check for existing agent or skill concepts before creating new ones.
- Preserve user edits and local conventions.
- Write a short audit note before changing files: current structure, missing pieces, risks, and proposed scope.

If the project already has a harness, classify the request as `create`, `extend`, `audit`, `repair`, or `evolve`.

### Phase 1: Domain Analysis

Define what work the harness should make repeatable.

- Collect concrete user tasks and failure modes.
- Identify fragile boundaries: API contracts, frontend/backend joins, release gates, external systems, credentials, regulatory rules, or brand rules.
- Separate stable procedural knowledge from fast-changing project facts.
- Map each repeated workflow to a skill, reference, script, or template.
- Avoid roles that are merely job titles; each role must own a distinct input/output contract.

Use this output shape:

```markdown
## Domain Analysis

- Primary workflows:
- Stable rules:
- Volatile project facts:
- Required tools or commands:
- Validation gates:
- Candidate skills:
```

### Phase 2: Team Architecture

Choose the smallest architecture that covers the work.

- `single-skill`: one skill drives the workflow.
- `pipeline`: ordered stages with handoff artifacts.
- `fan-out-fan-in`: independent checks or research streams followed by synthesis.
- `expert-pool`: multiple specialist skills selected by task.
- `producer-reviewer`: one workflow produces output and another reviews it.
- `supervisor`: a top-level orchestrator routes to narrower skills.
- `hierarchical-delegation`: a supervisor routes to sub-orchestrators for large domains.

Read `references/agent-design-patterns.md` before designing multi-skill harnesses.

### Phase 3: Skill and Role Definitions

Create skills for durable behavior and use role specs for orchestration.

For every proposed skill:

- Check for an existing skill with overlapping triggers.
- Name it in lowercase hyphen-case.
- Put trigger conditions in the `description` frontmatter.
- Keep the body procedural and concise.
- Put long rules in `references/`.
- Put deterministic repeated actions in `scripts/`.
- Add `agents/openai.yaml` metadata.

For every proposed role:

- Define mission, inputs, outputs, tools, validation, and failure handling.
- Decide whether it should become a skill, a section of an orchestrator skill, a prompt template, or a script.
- Do not create a separate skill if a section in an existing skill would be clearer.

Read `references/skill-writing-guide.md` before writing or materially changing skills.

### Phase 4: Orchestration

Create an orchestrator only when coordination adds value.

An orchestrator skill should:

- Classify the user's request.
- Select the relevant skill or workflow.
- Define workspace artifacts and file naming.
- Preserve context between phases.
- Specify handoff contracts.
- Run validation before final synthesis.
- Explain recovery steps when a phase fails.

Use `_workspace/` only for temporary intermediate artifacts. If a user asks for persistent docs or code, write them to the project paths requested or implied by the repo.

Read `references/orchestrator-template.md` for Codex-ready templates.

### Phase 5: Integration

Make the harness discoverable and maintainable.

- Keep repository-local skills under `skills/`.
- Add a root README pointer.
- Add optional install instructions for copying selected skills into `$CODEX_HOME/skills` or `~/.codex/skills`.
- Keep machine-local paths out of shared scripts unless they are examples.
- Store templates in `assets/` only when Codex should copy them into outputs.
- Do not add plugin metadata unless the user explicitly wants a Codex plugin package.

Read `references/project-integration.md` before changing repository layout.

### Phase 6: Validation and Testing

Validate structure, triggers, and real use.

Run:

```bash
python skills/codex-harness/scripts/validate_codex_harness.py .
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
python "$CODEX_HOME/skills/.system/skill-creator/scripts/quick_validate.py" skills/codex-harness
```

For every generated skill, also run the Codex quick validator on that skill directory.

For high-risk or large harnesses:

- Write trigger test prompts.
- Compare with-skill and baseline behavior.
- Add assertions for required outputs.
- Add a QA/reviewer skill or workflow.

Read `references/skill-testing-guide.md`, `references/evaluation-prompts.md`, and `references/qa-agent-guide.md` when validation needs more than structural checks.

### Phase 7: Evolution

Treat the harness as operational code.

Update it when:

- Codex repeatedly asks for the same missing context.
- Users correct the same assumption more than once.
- A workflow gains new validation gates.
- Project architecture changes.
- A skill trigger is too broad, too narrow, or collides with another skill.

Evolution loop:

1. Capture the failure or friction.
2. Decide whether the fix belongs in `SKILL.md`, `references/`, `scripts/`, `assets/`, README, or project code.
3. Make the smallest durable change.
4. Validate structure and one realistic scenario.
5. Record only stable project knowledge in memories or docs.

## Deliverables Checklist

A full Codex harness should include:

- Main harness skill: `skills/codex-harness/SKILL.md`
- UI metadata: `skills/codex-harness/agents/openai.yaml`
- Design references:
  - `references/agent-design-patterns.md`
  - `references/orchestrator-template.md`
  - `references/skill-writing-guide.md`
  - `references/skill-testing-guide.md`
  - `references/evaluation-prompts.md`
  - `references/qa-agent-guide.md`
  - `references/team-examples.md`
  - `references/project-integration.md`
- Scripts:
  - `scripts/scaffold_codex_skill.py`
  - `scripts/validate_codex_harness.py`
- Root README pointer and validation commands.

## Output Style

When building a harness for a user, return:

- Audit summary.
- Architecture chosen and why.
- Files created or changed.
- Validation commands run.
- Remaining gaps or recommended next workflows.

Keep explanations concrete. Do not claim the harness is complete until structure validation and at least one realistic usage path have been checked.
