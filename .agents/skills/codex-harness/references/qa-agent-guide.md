# QA and Reviewer Guide

Use this reference when a harness needs review, QA, or integration-coherence checks.

## What QA Should Catch

A good QA workflow catches boundary failures that simple static review misses:

- frontend type expects a field the API does not return
- route exists in navigation but not in router config
- generated docs reference stale command names
- a skill says to run a script that does not exist
- a migration changes data shape but not validation
- a README install step diverges from actual layout

## QA Principles

- Compare both sides of every boundary.
- Prefer contract checks over existence checks.
- Validate immediately after a module or artifact is complete.
- Require evidence: file paths, commands, observed output.
- Report risks in priority order.

## Cross-Boundary Checklist

### API and Frontend

- API response fields match frontend types.
- Error shapes are handled.
- Loading and empty states exist.
- Endpoint paths match client hooks.

### Routing and Links

- File routes match navigation links.
- Dynamic params are named consistently.
- Redirects and fallback routes are intentional.

### Skills and Scripts

- `SKILL.md` references existing files.
- Validation commands exist.
- `agents/openai.yaml` default prompt uses the correct `$skill-name`.
- Script arguments match README examples.
- Generated skill names are hyphen-case.

### Docs and Code

- README commands match actual scripts.
- Examples compile or are clearly illustrative.
- Config names match files in the repository.

## Reviewer Skill Template

```markdown
---
name: {domain}-qa
description: Review {domain} outputs for contract mismatches, missing validation, stale references, and integration risks. Use after implementation, scaffold generation, documentation updates, or harness evolution.
---

# {Domain} QA

Review completed work by comparing boundaries and validating claims.

## Workflow

1. Read the user request and changed files.
2. Identify producer outputs and consumers.
3. Compare both sides of each boundary.
4. Run or inspect validation commands.
5. Report findings first, ordered by severity.

## Findings Format

- Severity:
- File:
- Evidence:
- Impact:
- Fix:
```

## Severity

- `critical`: data loss, security issue, broken install, unusable generated harness
- `high`: main workflow fails, validation command invalid, key contract mismatch
- `medium`: confusing behavior, missing edge case, incomplete docs
- `low`: naming, clarity, maintainability

## Common False Confidence

Avoid accepting output because:

- files exist
- headings look complete
- tests pass without covering the changed boundary
- examples are plausible but not runnable
- the producer and reviewer share the same unchecked assumption
