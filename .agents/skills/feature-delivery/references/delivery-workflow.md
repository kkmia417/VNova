# Delivery Workflow

Use this reference for feature implementation tasks.

## Planning Heuristics

Write a plan before editing when:

- more than two modules are touched
- a data contract changes
- user-facing behavior changes
- tests or migrations are needed
- the implementation path is ambiguous

Skip a formal plan for narrow one-file fixes, but still inspect context first.

## Audit Checklist

- current git status
- relevant instructions
- existing tests and commands
- nearby implementation patterns
- public contracts and callers
- docs or examples that mention the behavior

## Implementation Order

1. Update shared contracts or types.
2. Update producers.
3. Update consumers.
4. Update tests.
5. Update docs or examples.
6. Run validation.

For UI work, verify responsive behavior and text fit when feasible.

## Validation Selection

- touched unit logic: run targeted tests
- changed type contracts: run type checker
- changed formatting-sensitive files: run formatter or lint
- changed frontend UI: run build and visual smoke checks when available
- changed scripts: run the script on a representative sample
- changed docs commands: execute or clearly mark as unverified

## Handoff to Integration QA

Use `$integration-qa` when a change crosses boundaries:

- API to client
- database schema to query code
- script behavior to README command
- route file to navigation link
- config file to runtime loader

Pass the changed files, expected behavior, and validation already run.
