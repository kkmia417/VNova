# Review Rubric

Use this reference during repository, PR, or release-readiness reviews.

## Severity

- `critical`: security exposure, data loss, broken install, production outage risk.
- `high`: main workflow fails, contract mismatch, migration risk, missing required validation.
- `medium`: edge case failure, incomplete tests, confusing behavior, maintainability risk.
- `low`: clarity, naming, docs, or small cleanup.

## Evidence Rules

Every finding needs:

- exact file and line when available
- observed behavior or code path
- why it matters
- concrete fix direction

Avoid speculative findings without a plausible failure path.

## Review Passes

### Behavior

- Changed code still satisfies the user-visible contract.
- Error paths and empty states are handled.
- Backward compatibility is preserved or intentionally broken.

### Integration

- API responses match consumers.
- Config keys match readers.
- Docs and scripts match actual commands.
- Routes, links, and generated paths agree.

### Tests

- New behavior has targeted coverage.
- Existing tests still exercise changed contracts.
- Test assertions would fail on the suspected bug.

### Security

- Secrets are not logged or committed.
- Inputs are validated before dangerous use.
- File paths and shell commands avoid injection.
- Auth and permission checks remain in place.

### Performance

- Loops, queries, and renders do not introduce avoidable repeated work.
- Cache invalidation and batching are considered where relevant.

## No-Finding Response

If no issues are found:

- say no findings clearly
- list commands run
- list residual risk or untested surfaces
