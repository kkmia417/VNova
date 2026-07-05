---
name: feature-delivery
description: Plan, implement, validate, and summarize repository feature work across code, tests, docs, and integration boundaries. Use when asked to build a feature, make a product change, implement a workflow, update behavior end to end, or continue feature work with validation.
---

# Feature Delivery

Deliver a bounded feature end to end while preserving the repository's existing architecture and validation flow.

## Workflow

1. Audit the request, current git state, and relevant project conventions.
2. Identify affected modules, data contracts, tests, and docs.
3. Produce a short implementation plan when the change spans multiple files or behaviors.
4. Implement the smallest coherent change.
5. Add or update focused tests when the risk justifies it.
6. Run validation commands that match the touched surfaces.
7. Use `$integration-qa` when frontend/backend, docs/scripts, config/runtime, or schema/query boundaries changed.
8. Summarize files changed, validation results, and remaining risk.

Read `references/delivery-workflow.md` for planning and validation details.

## Constraints

- Prefer existing project patterns over new abstractions.
- Keep unrelated refactors out of scope.
- Preserve user edits in the worktree.
- Make validation failures explicit if they cannot be fixed in scope.

## Output

Return:

- what changed
- validation run
- user-facing behavior impact
- follow-up work if the feature exposed a separate issue
