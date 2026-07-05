---
name: repo-review
description: Review a repository, pull request, or changed file set for defects, regressions, architecture risks, security issues, performance concerns, missing tests, and release readiness. Use when asked for code review, PR review, repo audit, regression review, pre-merge review, or readiness assessment.
---

# Repo Review

Perform a code-review style inspection. Findings come first, ordered by severity, with exact file references and evidence.

## Workflow

1. Inspect current git state and identify changed files.
2. Read project instructions, validation commands, and relevant implementation files.
3. Classify risk areas: behavior, tests, security, performance, maintainability, docs, and integration boundaries.
4. Compare both sides of changed contracts such as API/client, config/docs, schema/query, and route/link.
5. Run targeted validation when feasible.
6. Return findings first. If there are no findings, say that clearly and list residual test gaps.

## Review Focus

- Behavioral regressions and edge cases.
- Broken assumptions across module boundaries.
- Missing or weak tests for changed behavior.
- Security-sensitive input handling, secrets, auth, file IO, and network calls.
- Performance issues in hot paths or repeated work.
- User-facing docs or commands that no longer match implementation.

Read `references/review-rubric.md` for severity, evidence, and output rules.

## Output

Use this shape:

```markdown
## Findings

- Severity: high
  File: path/to/file.ext:line
  Evidence:
  Impact:
  Fix:

## Open Questions

## Validation
```

Keep summaries short. Do not bury findings below implementation notes.
