# Documentation Verification Rules

Use this reference when generating, updating, or reviewing repository documentation.

## Generation vs Accuracy Review

Generation creates or rewrites documentation for a target reader. Accuracy review verifies whether the documentation matches the repository.

Keep the two passes distinct:

1. Draft from current source artifacts.
2. Review the draft against implementation, scripts, tests, and existing docs.
3. Fix mismatches found during review.
4. Report anything that remains unverified.

Do not use polished wording as evidence that a claim is true.

## Source Priority

Prefer sources in this order:

1. Executed command output or passing validation.
2. Source code, schemas, route definitions, scripts, package manifests, and tests.
3. Existing checked-in documentation.
4. User-provided requirements.

When sources conflict, flag the mismatch and prefer implementation only for describing current behavior. Do not silently rewrite product intent.

## Command Verification

For documented commands:

- Check that referenced files and scripts exist.
- Check command syntax on the repository's target shell when possible.
- Run commands that are safe, local, and reasonably fast.
- Avoid commands that publish, deploy, delete data, rotate secrets, or mutate external services unless the user explicitly asks.
- If a command cannot be run, verify its components statically and state why execution was skipped.

For command docs, capture:

- working directory
- shell or platform assumptions
- required environment variables
- expected success signal
- known non-fatal warnings

## Example Verification

For code or usage examples:

- Confirm imported modules, function names, options, paths, and output fields exist.
- Prefer examples that can be copied without hidden setup.
- Keep placeholders visibly placeholder-like, such as `<TOKEN>` or `<project-id>`.
- Avoid sample output that implies exact timestamps, IDs, or generated values unless it is actually deterministic.
- If an example is conceptual, label it as conceptual instead of executable.

## API and CLI Documentation

For APIs:

- Compare documented request parameters, response fields, status codes, and error shapes against code or tests.
- Include authentication, pagination, rate limits, and idempotency only when confirmed.
- Mark unstable or inferred behavior as such.

For CLIs:

- Compare command names, flags, defaults, required arguments, exit behavior, and output formats against parser definitions or help output.
- Prefer generated `--help` output as evidence when available.

## Done Criteria

Documentation maintenance is complete when:

- changed docs match current implementation or explicitly document intended future behavior
- referenced files, links, scripts, and commands have been checked
- examples are either verified or clearly marked conceptual/unverified
- validation results and residual risks are included in the final response
