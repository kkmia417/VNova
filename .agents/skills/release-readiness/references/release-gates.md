# Release Gates

Use these checks when assessing pre-release readiness. Adapt them to the repository's actual stack and release process.

## Gate Severity

- `blocker`: release should not proceed without a fix or explicit user risk acceptance.
- `high`: likely to break a main workflow, deployment, migration, install, or rollback.
- `medium`: meaningful gap that can ship only with a clear caveat or follow-up owner.
- `low`: documentation, cleanup, or observability improvement that does not block shipping.

## Validation Gates

- Tests that cover changed behavior have passed or the missing test gap is called out.
- Lint, formatting, type checking, build, packaging, or install checks match the touched surfaces.
- Generated artifacts are current when the project relies on codegen, docs generation, lockfiles, or manifests.
- Manual verification steps are listed when automated validation cannot cover the change.

## Changelog and Versioning

- User-visible behavior changes appear in the changelog or release notes.
- Breaking changes, migrations, deprecations, and required operator actions are explicit.
- Version numbers, package metadata, tags, or release names are consistent where applicable.
- Examples and command snippets still match actual scripts and flags.

## Deployment Risk

- Config keys, environment variables, secrets, and feature flags are documented and read by runtime code.
- Database migrations are ordered, reversible where required, and compatible with rolling deploys when applicable.
- External service assumptions, rate limits, permissions, and network dependencies are named.
- Rollback instructions account for data shape, migrations, caches, queues, and client compatibility.

## Compatibility

- Public APIs, CLI flags, file formats, routes, and schemas remain compatible or are intentionally broken with migration guidance.
- Consumers are updated when producer contracts change.
- Error handling, empty states, and permission failures are represented.

## Readiness Decision

Use `ship` only when required gates pass and no blocker remains.

Use `hold` when a blocker remains, required validation is missing, release docs are materially wrong, or rollback is not credible for a high-risk change.

Use `ship with caveats` when remaining risks are understood, bounded, non-blocking, and visible in the final summary.
