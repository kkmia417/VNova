# Skill Testing and Iteration Guide

Use this reference when structural validation is not enough.

## Test Layers

### 1. Structure

Check:

- `SKILL.md` exists.
- frontmatter has `name` and `description`.
- `name` matches folder.
- `agents/openai.yaml` exists.
- referenced files exist.
- no TODO placeholders remain.

Run:

```bash
python skills/codex-harness/scripts/validate_codex_harness.py .
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
python "$CODEX_HOME/skills/.system/skill-creator/scripts/quick_validate.py" skills/<skill-name>
```

### 2. Trigger Coverage

Write prompts that should trigger the skill:

```markdown
## Positive Triggers

- "Build a Codex harness for this repo."
- "Audit the existing harness and improve it."
- "Create reusable Codex skills for release work."

## Negative Triggers

- "Explain this Python function."
- "Run the unit tests."
- "Summarize the README."
```

Revise `description` when positive prompts are ambiguous or negative prompts are too likely to trigger.

### 3. Scenario Dry Run

Use a realistic request and check whether the skill tells Codex:

- what files to inspect
- what references to load
- what artifacts to create
- what commands to run
- how to recover from failure
- how to report completion

### 4. With-Skill vs Baseline

For important skills, compare outcomes:

| Run | Prompt | Skill Available | Score | Notes |
|---|---|---|---|---|
| baseline | same task | no | | |
| harness | same task | yes | | |

Score against assertions, not vibes.

For harness-level evaluation scenarios, use `references/evaluation-prompts.md`.
Keep evaluation prompts separate from assertions so the model under test does not
receive the expected answer.

## Assertion Design

Good assertions are discriminating and observable:

- "Creates `agents/openai.yaml` with a `$skill-name` default prompt."
- "Runs the repository validation command."
- "Cites exact files changed."
- "Does not create unrelated docs."

Weak assertions:

- "Output is good."
- "Agent understands the task."
- "Looks professional."

## Grading Schema

```json
{
  "task": "string",
  "skill": "string",
  "score": 0,
  "max_score": 10,
  "passed_assertions": [],
  "failed_assertions": [],
  "missing_context": [],
  "recommended_skill_changes": []
}
```

## Iteration Loop

1. Run a scenario.
2. Record the miss.
3. Classify the fix:
   - trigger wording
   - workflow step
   - reference detail
   - script behavior
   - validation gate
4. Patch the smallest file.
5. Re-run structure validation.
6. Re-run one scenario that would have failed before.

## Workspace

Use `_workspace/evals/{skill-name}/` for optional evaluation notes when the user wants tracked evaluation artifacts. Otherwise, summarize results in the final response and avoid clutter.
