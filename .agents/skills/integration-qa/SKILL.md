---
name: integration-qa
description: Verify cross-boundary coherence after repository changes. Use when asked to QA an implementation, check frontend/backend integration, verify docs against scripts, compare APIs and consumers, review generated harness files, or find mismatches between changed artifacts.
---

# Integration QA

Check whether changed artifacts agree across boundaries. This skill is a reviewer, not a producer.

## Workflow

1. Identify producers and consumers in the changed surface.
2. Read both sides of each boundary.
3. Compare names, types, paths, commands, states, and error shapes.
4. Run targeted validation when feasible.
5. Report findings first with evidence and fixes.
6. If no findings are found, state residual risk and unverified surfaces.

Read `references/boundary-checks.md` for common boundary patterns.

## Boundaries

- API response to frontend hook or client.
- Route file to navigation link.
- Config file to runtime loader.
- Script arguments to README command.
- Skill `SKILL.md` references to actual files.
- `agents/openai.yaml` prompt to skill name.
- Database schema to query or model code.

## Output

```markdown
## Findings

- Severity:
  Boundary:
  Evidence:
  Impact:
  Fix:

## Validation

## Residual Risk
```
