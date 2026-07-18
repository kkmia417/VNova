# Toolchain Baseline

Status: Quarantined Stage B evidence; locally verified on Windows; exact-version remote CI and
protected acceptance pending

This executable baseline is absent from the Stage A candidate and is not active repository
enforcement. Local success proves only that the current mutable scaffold is internally
executable; it does not accept the scaffold, close an ADR or OD, or authorize runtime behavior.

## Selected Baseline

| Tool       | Baseline    | Reason                                                                                                                   |
| ---------- | ----------- | ------------------------------------------------------------------------------------------------------------------------ |
| Python     | 3.13.14     | Selected maintained Python 3.13 patch baseline; avoids changing the minor line during foundation review                  |
| Node.js    | 24.18.0 LTS | Selected Node 24 LTS patch baseline for the TypeScript workspace                                                         |
| uv         | 0.11.28 CI  | Selected cross-platform workspace/lockfile runner; local compatibility remains constrained to the pinned 0.11 minor line |
| pnpm       | 11.13.1     | Pinned workspace-aware package manager with strict lockfile behavior                                                     |
| TypeScript | 6.0.3       | Pinned version inside the supported peer range of the selected strict ESLint toolchain                                   |
| Hatchling  | 1.31.0      | Exact Python build backend installed from the workspace lock and reused without isolated re-resolution                   |

Version and behavior sources checked on 2026-07-18:

- [Python 3.13.14 release announcement](https://blog.python.org/2026/06/python-3146-31314/)
- [Node.js 24.18.0 LTS release](https://nodejs.org/en/blog/release/v24.18.0)
- [uv 0.11.28 release](https://github.com/astral-sh/uv/releases/tag/0.11.28)
- [pnpm 11.13.1 release](https://github.com/pnpm/pnpm/releases/tag/v11.13.1)
- [TypeScript 6.0.3 release](https://github.com/microsoft/TypeScript/releases/tag/v6.0.3)
- [Hatchling 1.31.0 package provenance](https://pypi.org/project/hatchling/1.31.0/)
- [uv workspace documentation](https://docs.astral.sh/uv/concepts/projects/workspaces/)
- [uv lock and sync documentation](https://docs.astral.sh/uv/concepts/projects/sync/)
- [pnpm workspace documentation](https://pnpm.io/workspaces)
- [pnpm CI lockfile behavior](https://pnpm.io/continuous-integration)

Minor lines are architecture baselines. Exact project dependencies and runtimes are captured in
`uv.lock`, `pnpm-lock.yaml`, `packageManager`, `.python-version`, and `.node-version`. The selected
remote-CI uv executable is pinned separately in `.github/workflows/ci.yml`; `pyproject.toml`
declares the compatible local uv minor range and does not claim to pin that executable.

## Observed Local Evidence

These are host facts, not the selected remote-CI baseline:

| Command                                          | Observed result |
| ------------------------------------------------ | --------------- |
| `uv run --locked --python 3.13 python --version` | `Python 3.13.5` |
| `node --version`                                 | `v24.11.0`      |
| `uv --version`                                   | `uv 0.11.15`    |
| `corepack pnpm --version`                        | `11.13.1`       |

## Workspace Rules

- One uv workspace and lockfile for Python packages.
- One pnpm workspace and lockfile for TypeScript packages.
- Workspace dependencies use explicit workspace references when introduced.
- CI uses locked/frozen installs and never updates lockfiles implicitly.
- Python builds run without build isolation only after the exact Hatchling version and its transitive dependencies have been installed from `uv.lock`.
- Generated contracts are reproduced twice and must be byte-identical.
- Schema, generated Python, and generated TypeScript validators run the same valid/invalid fixtures.
- Runtime packages never import their hand-authored specs directly; generated schema copies ship alongside a contract manifest carrying the source digest.
- The canonical CI self-check rejects root-entrypoint, trigger, matrix, required-command,
  aggregate-job, timeout, permission, security-control, run-semantics, and immutable-action-pin
  shrinkage before the wider test suite runs.

## Local Commands

The intended commands are:

```powershell
uv sync --all-packages --locked --no-install-workspace --no-build --python 3.13
uv sync --all-packages --locked --no-build-isolation --python 3.13
corepack pnpm install --frozen-lockfile
corepack pnpm run ci:check
corepack pnpm run verify
corepack pnpm run artifacts:verify
```

The full verification and package-build sequence passed locally on Windows with the observed
versions above. The quarantined Stage B workflow pins Python 3.13.14, Node 24.18.0, and uv 0.11.28
for Ubuntu 24.04 and Windows 2025. Until that exact workflow runs remotely on an immutable
candidate, exact-version and cross-platform validation remain pending rather than assumed.
