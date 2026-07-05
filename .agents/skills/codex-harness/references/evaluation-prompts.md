# Harness Evaluation Prompts

Use these prompts to compare baseline Codex behavior with behavior when the repository harness is available.

Keep the test prompt separate from the grading assertions. The model under test should receive only the prompt and normal repository context, not the expected files, checks, or scoring criteria.

## Evaluation Protocol

For each scenario:

1. Run the prompt once without explicitly invoking a harness skill.
2. Run the same prompt with the relevant skill available or explicitly named.
3. Grade both runs against the assertions after the run finishes.
4. Record observable evidence: files changed, commands run, validation output, and final response claims.
5. Treat missing evidence as a failed assertion, even if the final response sounds plausible.

Do not write prompts that reveal required implementation details. The prompt should describe the user's goal, while assertions should describe the expected durable behavior.

## Scenario: Harness Creation

Prompt:

```text
Build a reusable Codex harness for this repository. It should help future Codex sessions perform the repository's most repeated workflows consistently.
```

Assertions:

- Inspects the existing repository structure before proposing new files.
- Identifies repeated workflows and maps each to a skill, reference, script, or template.
- Creates or updates repository-local skill files under `skills/` only when they have distinct trigger conditions.
- Adds `SKILL.md` and `agents/openai.yaml` for every new skill.
- Runs the repository harness validator or clearly reports why it could not run.
- Final response lists files changed and validation commands run.
- Does not create plugin packaging unless distribution outside repository-local skills is requested.

## Scenario: Harness Review

Prompt:

```text
Audit the current Codex harness and improve the most important gap you find.
```

Assertions:

- Reads the current harness skill, references, scripts, and README pointers before editing.
- Classifies the work as an audit or evolution task.
- Names the most important gap with evidence from existing files.
- Makes a scoped change that addresses that gap.
- Preserves existing skill names, descriptions, and references unless a concrete conflict is found.
- Runs structural validation after the change.
- Final response separates changes made from remaining risks or follow-up work.

## Scenario: Feature Delivery

Prompt:

```text
Use this repository's feature delivery workflow to implement a small, bounded feature requested in the project docs.
```

Assertions:

- Locates the feature request in project documentation instead of inventing a feature.
- Audits relevant files before editing.
- Produces a concise plan before making non-trivial changes.
- Keeps edits scoped to the requested feature and its validation path.
- Runs targeted tests, validators, or build commands that match the repository.
- Reports any tests that could not be run and why.
- Does not add unrelated architecture, dependencies, or documentation.

## Scenario: Integration QA

Prompt:

```text
Review the current changes for integration mismatches before release.
```

Assertions:

- Scopes the changed files before reviewing integration risk.
- Checks cross-boundary contracts such as command documentation, scripts, skill references, and README pointers.
- Reports findings with exact file references and observable evidence.
- Distinguishes confirmed mismatches from residual risk.
- Recommends targeted validation commands for the affected boundaries.
- Does not report generic quality opinions without a concrete integration path.

## Result Record

Use this shape for tracked evaluation notes:

```json
{
  "scenario": "harness-creation",
  "run": "baseline|with-skill",
  "prompt": "short prompt identifier",
  "score": 0,
  "max_score": 7,
  "passed_assertions": [],
  "failed_assertions": [],
  "evidence": [],
  "recommended_harness_changes": []
}
```
