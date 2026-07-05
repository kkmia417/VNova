# Team Examples

Use these examples as patterns, not as files to copy verbatim.

## Example 1: Code Review Harness

Architecture: fan-out/fan-in + producer-reviewer.

Skills:

| Skill | Purpose |
|---|---|
| `repo-review-orchestrator` | route review requests and synthesize findings |
| `architecture-review` | inspect boundaries, ownership, and design regressions |
| `security-review` | inspect auth, secrets, injection, unsafe IO |
| `performance-review` | inspect hot paths, query patterns, bundle size |
| `qa-review` | verify tests, commands, and integration coherence |

Workflow:

1. Orchestrator scopes changed files.
2. Review branches inspect independent risk classes.
3. Fan-in deduplicates findings.
4. QA checks evidence and missing tests.
5. Final answer lists findings first.

## Example 2: Full-Stack Feature Harness

Architecture: pipeline with QA gate.

Skills:

| Skill | Purpose |
|---|---|
| `feature-planner` | define scope, data model, routes, tests |
| `frontend-builder` | implement UI consistent with project conventions |
| `backend-builder` | implement API, validation, persistence |
| `integration-qa` | compare API, frontend, routes, and docs |

Workflow:

1. Planner audits repo and writes implementation plan.
2. Backend and frontend changes are made in scoped files.
3. Integration QA compares contracts.
4. Tests and build run before final summary.

## Example 3: Research Harness

Architecture: fan-out/fan-in.

Skills:

| Skill | Purpose |
|---|---|
| `research-orchestrator` | define question, source classes, and synthesis criteria |
| `primary-source-research` | collect official docs, papers, filings, standards |
| `community-signal-research` | collect user reports and practical caveats |
| `synthesis-review` | compare claims and flag uncertainty |

Rules:

- Browse when facts may have changed.
- Prefer primary sources for technical claims.
- Keep quotes short.
- Separate evidence from inference.

## Example 4: Documentation Harness

Architecture: producer-reviewer.

Skills:

| Skill | Purpose |
|---|---|
| `docs-generator` | produce docs from code and existing conventions |
| `docs-accuracy-review` | verify commands, paths, examples, and links |

Workflow:

1. Generator reads code and existing docs.
2. Generator writes docs or patches.
3. Reviewer checks every command and path.
4. Final answer notes unverified examples.

## Example 5: Migration Harness

Architecture: supervisor + pipeline.

Skills:

| Skill | Purpose |
|---|---|
| `migration-supervisor` | classify migration type and route work |
| `impact-auditor` | map dependencies and affected modules |
| `migration-worker` | make scoped code changes |
| `compatibility-review` | check old/new behavior and rollback needs |

Workflow:

1. Supervisor identifies migration class.
2. Impact auditor produces file and API map.
3. Worker edits bounded scope.
4. Compatibility review checks old contracts.
5. Validation runs project commands and targeted checks.

## Example 6: Content Production Harness

Architecture: pipeline + expert pool.

Skills:

| Skill | Purpose |
|---|---|
| `content-strategist` | define audience, angle, and constraints |
| `content-drafter` | draft the artifact |
| `style-editor` | align voice and clarity |
| `fact-checker` | verify claims and sources |

Workflow:

1. Strategist defines brief.
2. Drafter creates versioned draft.
3. Style editor revises for audience.
4. Fact checker verifies claims.
5. Orchestrator returns final plus unresolved risks.

## Example Prompt Set

```text
Build a Codex harness for comprehensive code review in this repository.

Build a Codex harness for full-stack feature delivery. It should plan, implement,
cross-check frontend/backend contracts, and run the right validation commands.

Audit the existing Codex harness and evolve it based on repeated misses.

Create a documentation harness that generates API docs and verifies examples.
```
