---
name: docs-maintenance
description: Generate, maintain, verify, and repair repository documentation including README files, API docs, command references, examples, and usage guides. Use when asked to write docs, update stale docs, check examples against implementation, verify documented commands, or separate documentation generation from accuracy review.
---

# Docs Maintenance

Maintain repository documentation as a production artifact. Separate drafting from accuracy review so generated prose does not hide stale commands, examples, paths, APIs, or behavior.

## Workflow

1. Classify the request as generation, update, repair, or accuracy review.
2. Inspect current docs, implementation, public interfaces, scripts, and examples that the docs mention.
3. Draft or update documentation from source artifacts, not memory.
4. Run a separate accuracy pass against commands, paths, options, examples, API shapes, and linked files.
5. Execute documented commands or examples when practical. Mark anything unverified with a concrete reason.
6. Update nearby docs consistently when the same workflow appears in multiple places.
7. Summarize changed files, validation run, verified examples, and residual risk.

Read `references/verification-rules.md` before verifying commands, examples, API docs, or generated documentation.

## Documentation Types

- README and quickstart docs.
- API, CLI, configuration, and command references.
- Usage examples, tutorials, and troubleshooting notes.
- Skill, harness, or workflow documentation.

## Constraints

- Do not invent behavior, flags, paths, return shapes, or installation steps.
- Prefer implementation, tests, package scripts, and existing docs as source of truth.
- Keep generated docs concise and task-oriented.
- Preserve deliberate project terminology and style.
- Treat docs-only changes as code changes when commands or examples can break users.

## Output

Return:

- files changed
- sources checked
- commands or examples verified
- documentation accuracy risks that remain
