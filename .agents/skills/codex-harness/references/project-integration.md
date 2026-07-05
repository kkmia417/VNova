# Project Integration

Use this reference when adding a Codex harness to a repository or installing it locally.

## Recommended Repository Layout

```text
.
  README.md
  skills/
    codex-harness/
      SKILL.md
      agents/openai.yaml
      references/
      scripts/
    <project-skill>/
      SKILL.md
      agents/openai.yaml
      references/
      scripts/
      assets/
```

Keep repository-local skills under `skills/` so they are versioned with the project.

## Direct Use

Use the repository copy directly during development:

```text
Use $codex-harness at ./skills/codex-harness to build a project harness.
```

For another skill:

```text
Use $<skill-name> at ./skills/<skill-name> to ...
```

## Local Install

Install a repository skill into the local Codex skill directory when it should be available across sessions:

```powershell
$name = "codex-harness"
$dest = Join-Path $env:USERPROFILE ".codex\skills\$name"
New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
Copy-Item -Recurse -Force ".\skills\$name" $dest
```

For teams, keep the repository copy authoritative. Treat global installs as local cache.

## Scaffolding a New Project Skill

```powershell
python .\skills\codex-harness\scripts\scaffold_codex_skill.py repo-review `
  --description "Review this repository for architecture, security, performance, tests, and integration risks. Use when asked for code review, PR review, regression review, or release readiness review." `
  --orchestrator `
  --resources references,scripts
```

Then edit the generated `SKILL.md`, add focused references, and validate.

## Validation

Run after any harness edit:

```powershell
python .\skills\codex-harness\scripts\validate_codex_harness.py .
$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
python (Join-Path $CodexHome "skills/.system/skill-creator/scripts/quick_validate.py") .\skills\codex-harness
```

Run `quick_validate.py` for every skill that changed.

## README Pointer

Add a short root README section:

```markdown
## Codex Harness

This repository includes Codex skills under `skills/`. Start with
`skills/codex-harness/SKILL.md` when creating, auditing, or evolving reusable
Codex workflows for this project.
```

## Maintenance Rules

- Keep task procedures in skills.
- Keep general project facts in normal repository docs.
- Keep long optional guidance in `references/`.
- Keep deterministic repeated actions in `scripts/`.
- Keep output templates in `assets/`.
- Validate before committing.
- Remove obsolete workflows instead of letting triggers collide.
