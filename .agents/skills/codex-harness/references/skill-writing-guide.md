# Skill Writing Guide

Use this reference before creating or materially updating a Codex skill.

## Required Structure

```text
skills/<skill-name>/
  SKILL.md
  agents/openai.yaml
  references/
  scripts/
  assets/
```

Only create resource directories that are needed.

## SKILL.md Frontmatter

Use only:

```yaml
---
name: skill-name
description: Verb-rich description that explains what the skill does and when Codex should use it.
---
```

Rules:

- `name` must match the folder.
- Use lowercase hyphen-case.
- Put trigger conditions in `description`.
- Include task verbs, domain nouns, file types, and maintenance scenarios.
- Do not put trigger rules only in the body.

Good pattern:

```yaml
description: Generate, validate, and evolve API documentation for this repository. Use when asked to document endpoints, update examples, check request/response contracts, or repair stale API docs.
```

Weak pattern:

```yaml
description: Helps with API docs.
```

## Body Style

- Write for another Codex session.
- Prefer imperative steps.
- Keep the main body short.
- Link directly to references and state when to read them.
- Include validation commands.
- Include output expectations.
- Avoid project facts that belong in normal docs.

## Progressive Disclosure

Use this loading model:

1. Frontmatter tells Codex when to load the skill.
2. `SKILL.md` gives the core workflow.
3. `references/` carries optional depth.
4. `scripts/` performs deterministic work.
5. `assets/` stores copyable templates and media.

Do not hide required steps in references. The core workflow must be executable after reading `SKILL.md`.

## Resource Decisions

Use `references/` for:

- domain rules
- API schemas
- long examples
- grading rubrics
- architecture patterns

Use `scripts/` for:

- scaffolding
- validation
- parsing
- migrations
- repeatable generation

Use `assets/` for:

- templates
- boilerplate projects
- images or icons
- sample documents meant to be copied

## agents/openai.yaml

Minimum:

```yaml
interface:
  display_name: "Readable Name"
  short_description: "Short UI summary"
  default_prompt: "Use $skill-name to ..."
```

Rules:

- Quote strings.
- Keep `default_prompt` one sentence.
- Include the literal `$skill-name`.
- Do not add dependencies unless the skill really needs a tool.

## Output Contracts

For skills that create artifacts, specify:

```markdown
## Output

- Path:
- Format:
- Required sections:
- Validation:
- Done criteria:
```

For review skills, specify severity levels and evidence requirements.

## Reuse Boundary

Generalize only stable procedure. Keep project-specific facts where future maintainers expect them:

- code ownership in repo docs
- current endpoints in API docs
- commands in README or package scripts
- Codex-specific workflow in skills

## Do Not Include

- generic tutorials
- long README files inside skill folders
- stale examples copied from unrelated projects
- broad roles with no trigger
- scripts that duplicate existing project tooling
- hidden assumptions about global machine paths
