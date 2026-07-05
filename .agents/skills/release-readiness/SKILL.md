---
name: release-readiness
description: Run pre-release readiness checks, validation gates, changelog readiness, deployment risk review, and release decision summaries. Use when asked to prepare a release, review release readiness, check deployment risk, verify release notes, define release gates, or assess whether a repository change is ready to ship.
---

# Release Readiness

Assess whether a repository change, branch, build, or release candidate is ready to ship.

## Workflow

1. Identify the release scope: changed files, target version, deployment surface, user-facing behavior, and rollback path.
2. Inspect current git state, release notes, changelog entries, version metadata, migrations, config, and deployment docs that apply to the release.
3. Read `references/release-gates.md` before making a readiness decision.
4. Run or recommend the validation gates that match the touched surfaces.
5. Classify blocking risks separately from non-blocking follow-ups.
6. Return a clear ship, hold, or ship-with-caveats decision with evidence.

## Focus Areas

- Required tests, linters, build checks, and packaging checks.
- Changelog, release notes, version numbers, migration notes, and operator docs.
- Deployment risks: config changes, credentials, data migrations, feature flags, external services, and rollback.
- User-facing compatibility: API contracts, CLI flags, file formats, routes, docs, and deprecations.
- Monitoring and support readiness: known risks, alerts, dashboards, and incident response notes.

## Output

Use this shape:

```markdown
## Decision

Ship/Hold/Ship with caveats:
Reason:

## Blocking Issues

- Severity:
  Evidence:
  Impact:
  Required fix:

## Validation

## Changelog and Docs

## Deployment Risk

## Follow-ups
```

Keep the decision tied to observed evidence. Do not approve a release when required validation is missing unless the user explicitly accepts that risk.
