"""Enforce VNova's security and operability rules for GitHub Actions."""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn, cast

import yaml  # type: ignore[import-untyped]

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPOSITORY_ROOT / ".github" / "workflows"
LOCAL_ACTION_ROOT = REPOSITORY_ROOT / ".github" / "actions"
ROOT_PACKAGE_PATH = REPOSITORY_ROOT / "package.json"

ACTION_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_./-]+@[0-9a-f]{40}$")
DOCKER_PATTERN = re.compile(r"^docker://[^\s@]+@sha256:[0-9a-f]{64}$")
FOUNDATION_WORKFLOW_NAME = "ci.yml"
REQUIRED_FOUNDATION_EVENTS = frozenset({"merge_group", "pull_request", "push", "workflow_dispatch"})
REQUIRED_FOUNDATION_RUNNERS = frozenset({"ubuntu-24.04", "windows-2025"})
REQUIRED_FOUNDATION_DEPENDENCIES = frozenset({"package-artifacts", "quality", "security"})
REQUIRED_FOUNDATION_COMMANDS = {
    "package-artifacts": "corepack pnpm run artifacts:verify",
    "quality": "corepack pnpm run verify",
}
REQUIRED_ROOT_SCRIPTS = {
    "artifacts:verify": "uv run --locked --python 3.13 python -m tooling.artifacts.verify",
    "ci:check": "uv run --locked --python 3.13 python -m tooling.ci.check_workflows",
    "contracts:check": (
        "uv run --locked --python 3.13 python -m tooling.contracts.generate --check"
    ),
    "format:check": (
        "prettier --check README.md AGENTS.md docs .github package.json pnpm-workspace.yaml "
        "tsconfig.base.json eslint.config.mjs prettier.config.mjs "
        "dependency-cruiser.config.mjs packages specs tests "
        "tooling/architecture/check_typescript_boundaries.mjs && "
        "uv run --locked --python 3.13 ruff format --check ."
    ),
    "lint": (
        "eslint . && node tooling/architecture/check_typescript_boundaries.mjs && "
        "uv run --locked --python 3.13 python -m tooling.architecture.check_boundaries && "
        "depcruise packages/contracts/typescript/src --config dependency-cruiser.config.mjs && "
        "uv run --locked --python 3.13 ruff check . && "
        "uv run --locked --python 3.13 lint-imports && corepack pnpm run ci:check"
    ),
    "test": (
        "corepack pnpm --recursive --if-present run test && "
        "uv run --locked --python 3.13 python -m pytest"
    ),
    "typecheck": (
        "corepack pnpm --recursive --if-present run typecheck && "
        "uv run --locked --python 3.13 mypy tooling tests "
        "packages/contracts/python/src packages/safety/src"
    ),
    "verify": (
        "corepack pnpm run contracts:check && corepack pnpm run format:check && "
        "corepack pnpm run lint && corepack pnpm run typecheck && corepack pnpm run test"
    ),
}
REQUIRED_SECURITY_ACTIONS = frozenset(
    {
        "actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd",
        "actions/dependency-review-action@a1d282b36b6f3519aa1f3fc636f609c47dddb294",
        "github/codeql-action/analyze@7188fc363630916deb702c7fdcf4e481b751f97a",
        "github/codeql-action/init@7188fc363630916deb702c7fdcf4e481b751f97a",
        "gitleaks/gitleaks-action@e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e",
    }
)


class UniqueKeyLoader(yaml.BaseLoader):  # type: ignore[misc]
    """Load scalars as strings and reject duplicate mapping keys."""


def _construct_unique_mapping(loader: Any, node: Any, deep: bool = False) -> dict[object, object]:
    mapping: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


@dataclass(frozen=True)
class WorkflowViolation:
    path: Path
    line: int
    message: str

    def render(self) -> str:
        relative = self.path.relative_to(REPOSITORY_ROOT)
        return f"{relative}:{self.line}: {self.message}"


def _yaml_mapping(value: object) -> dict[str, Any] | None:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        return None
    return cast(dict[str, Any], value)


def _yaml_sequence(value: object) -> list[Any] | None:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return None


def _load_yaml(path: Path) -> tuple[dict[str, Any] | None, list[WorkflowViolation]]:
    try:
        document = yaml.load(
            path.read_text(encoding="utf-8"),
            Loader=UniqueKeyLoader,  # noqa: S506 - BaseLoader cannot construct objects.
        )
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        return None, [WorkflowViolation(path, 1, f"Cannot parse YAML: {error}")]
    mapping = _yaml_mapping(document)
    if mapping is None:
        return None, [WorkflowViolation(path, 1, "YAML document root must be a mapping")]
    return mapping, []


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate key {key!r}")
        value[key] = item
    return value


def verify_root_entrypoints(path: Path = ROOT_PACKAGE_PATH) -> list[WorkflowViolation]:
    """Keep the workflow's stable commands connected to the complete local gates."""

    try:
        package = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_json_keys,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        return [WorkflowViolation(path, 1, f"Cannot parse root package.json: {error}")]
    if not isinstance(package, dict) or not isinstance(package.get("scripts"), dict):
        return [WorkflowViolation(path, 1, "Root package.json requires a scripts mapping")]
    scripts = package["scripts"]
    violations: list[WorkflowViolation] = []
    for script_name, expected in REQUIRED_ROOT_SCRIPTS.items():
        if scripts.get(script_name) != expected:
            violations.append(
                WorkflowViolation(
                    path,
                    1,
                    f"Root script {script_name!r} must equal the governed foundation entrypoint",
                )
            )
    return violations


def _event_names(value: object) -> set[str]:
    if isinstance(value, str):
        return {value}
    mapping = _yaml_mapping(value)
    if mapping is not None:
        return set(mapping)
    sequence = _yaml_sequence(value)
    if sequence is not None and all(isinstance(item, str) for item in sequence):
        return set(sequence)
    return set()


def _verify_action_reference(
    path: Path, reference: str, repository_root: Path
) -> list[WorkflowViolation]:
    if reference.startswith("./"):
        resolved = (repository_root / reference).resolve()
        try:
            resolved.relative_to(repository_root)
        except ValueError:
            return [WorkflowViolation(path, 1, f"Local action escapes repository: {reference}")]
        action_files = [resolved / "action.yml", resolved / "action.yaml"]
        if not any(action_file.is_file() for action_file in action_files):
            return [WorkflowViolation(path, 1, f"Local action does not exist: {reference}")]
        return []
    if ACTION_PATTERN.fullmatch(reference) or DOCKER_PATTERN.fullmatch(reference):
        return []
    return [
        WorkflowViolation(
            path,
            1,
            "External actions must use an immutable 40-character commit SHA or container digest",
        )
    ]


def _verify_steps(
    path: Path,
    steps_value: object,
    repository_root: Path,
    *,
    require_timeout: bool,
) -> list[WorkflowViolation]:
    steps = _yaml_sequence(steps_value)
    if steps is None:
        return [WorkflowViolation(path, 1, "Job or composite action steps must be a sequence")]
    violations: list[WorkflowViolation] = []
    for index, step_value in enumerate(steps, start=1):
        step = _yaml_mapping(step_value)
        if step is None:
            violations.append(WorkflowViolation(path, 1, f"Step {index} must be a mapping"))
            continue
        if "uses" not in step and "run" not in step:
            violations.append(
                WorkflowViolation(path, 1, f"Step {index} requires exactly one of uses or run")
            )
            continue
        if "uses" in step and "run" in step:
            violations.append(
                WorkflowViolation(path, 1, f"Step {index} cannot define both uses and run")
            )
        if "continue-on-error" in step:
            violations.append(WorkflowViolation(path, 1, f"Step {index} cannot continue on error"))
        timeout = step.get("timeout-minutes")
        if require_timeout and (
            not isinstance(timeout, str) or not timeout.isdigit() or int(timeout) < 1
        ):
            violations.append(
                WorkflowViolation(path, 1, f"Step {index} requires positive timeout-minutes")
            )
        reference = step.get("uses")
        if isinstance(reference, str):
            violations.extend(_verify_action_reference(path, reference, repository_root))
            if reference.lower().startswith("actions/checkout@"):
                with_values = _yaml_mapping(step.get("with")) or {}
                if with_values.get("persist-credentials") != "false":
                    violations.append(
                        WorkflowViolation(
                            path,
                            1,
                            "actions/checkout must set persist-credentials: false",
                        )
                    )
    return violations


def _needs_names(value: object) -> set[str]:
    if isinstance(value, str):
        return {value}
    sequence = _yaml_sequence(value) or []
    return {item for item in sequence if isinstance(item, str)}


def _normalized_if_expression(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    expression = re.sub(r"\s+", "", value)
    if expression.startswith("${{") and expression.endswith("}}"):
        expression = expression[3:-2]
    return expression


def _aggregate_asserts_dependencies(job: dict[str, Any]) -> bool:
    needs = _needs_names(job.get("needs"))
    if not needs:
        return False
    steps = _yaml_sequence(job.get("steps")) or []
    failed_guards: set[str] = set()
    for step_value in steps:
        step = _yaml_mapping(step_value) or {}
        condition = _normalized_if_expression(step.get("if"))
        command = step.get("run")
        if condition is None or not isinstance(command, str):
            continue
        if "shell" in step or "working-directory" in step:
            continue
        if command.strip() not in {"exit 1", "false"}:
            continue
        for dependency in needs:
            accepted_conditions = {
                f"needs.{dependency}.result!='success'",
                f'needs.{dependency}.result!="success"',
            }
            if condition in accepted_conditions:
                failed_guards.add(dependency)
    return failed_guards == needs


def _permissions_are_read_only(value: object, *, top_level: bool) -> bool:
    permissions = _yaml_mapping(value)
    if permissions is None:
        return False
    if top_level:
        return permissions == {"contents": "read"}
    return all(
        name == "contents" and level in {"none", "read"} for name, level in permissions.items()
    )


def _security_permissions_are_least_privilege(value: object) -> bool:
    return _yaml_mapping(value) == {
        "contents": "read",
        "security-events": "write",
    }


def _string_values(value: object) -> list[str] | None:
    if isinstance(value, str):
        return [value]
    sequence = _yaml_sequence(value)
    if sequence is None or not all(isinstance(item, str) for item in sequence):
        return None
    return cast(list[str], sequence)


def _normalized_command(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    return re.sub(r"\s+", " ", value).strip()


def _verify_foundation_matrix_job(
    path: Path,
    job_id: str,
    job: dict[str, Any],
) -> list[WorkflowViolation]:
    violations: list[WorkflowViolation] = []
    if "defaults" in job:
        violations.append(
            WorkflowViolation(
                path,
                1,
                f"Foundation job {job_id!r} cannot override run defaults",
            )
        )
    if "if" in job:
        violations.append(
            WorkflowViolation(path, 1, f"Foundation job {job_id!r} cannot use a job-level if")
        )
    if _normalized_if_expression(job.get("runs-on")) != "matrix.os":
        violations.append(
            WorkflowViolation(
                path,
                1,
                f"Foundation job {job_id!r} must run on matrix.os",
            )
        )

    strategy = _yaml_mapping(job.get("strategy"))
    matrix = _yaml_mapping(strategy.get("matrix")) if strategy is not None else None
    if strategy is None or strategy.get("fail-fast") != "false":
        violations.append(
            WorkflowViolation(
                path,
                1,
                f"Foundation job {job_id!r} must set strategy.fail-fast to false",
            )
        )
    if matrix is None or set(matrix) != {"os"}:
        violations.append(
            WorkflowViolation(
                path,
                1,
                f"Foundation job {job_id!r} matrix must contain only the os axis",
            )
        )
    else:
        runners = _string_values(matrix.get("os"))
        if (
            runners is None
            or len(runners) != len(set(runners))
            or set(runners) != REQUIRED_FOUNDATION_RUNNERS
        ):
            violations.append(
                WorkflowViolation(
                    path,
                    1,
                    f"Foundation job {job_id!r} must cover exactly ubuntu-24.04 and windows-2025",
                )
            )

    required_command = REQUIRED_FOUNDATION_COMMANDS[job_id]
    steps = _yaml_sequence(job.get("steps")) or []
    command_steps = [
        step
        for step_value in steps
        if (step := _yaml_mapping(step_value)) is not None
        if (command := _normalized_command(step.get("run"))) is not None
        if command == required_command
    ]
    if not command_steps:
        violations.append(
            WorkflowViolation(
                path,
                1,
                f"Foundation job {job_id!r} must execute exactly {required_command!r}",
            )
        )
    elif not any(
        "if" not in step and "shell" not in step and "working-directory" not in step
        for step in command_steps
    ):
        violations.append(
            WorkflowViolation(
                path,
                1,
                f"Foundation job {job_id!r} must execute {required_command!r} unconditionally "
                "with the default shell and working directory",
            )
        )
    return violations


def _verify_foundation_events(
    path: Path,
    document: dict[str, Any],
) -> list[WorkflowViolation]:
    violations: list[WorkflowViolation] = []
    event_mapping = _yaml_mapping(document.get("on"))
    events = _event_names(document.get("on"))
    if event_mapping is None or events != REQUIRED_FOUNDATION_EVENTS:
        violations.append(
            WorkflowViolation(
                path,
                1,
                "Foundation CI triggers must be exactly push, pull_request, merge_group, "
                "and workflow_dispatch",
            )
        )
    else:
        push = _yaml_mapping(event_mapping.get("push"))
        branches = _string_values(push.get("branches")) if push is not None else None
        if push is None or set(push) != {"branches"} or branches != ["main"]:
            violations.append(
                WorkflowViolation(
                    path,
                    1,
                    "Foundation CI push trigger must target only the main branch",
                )
            )
        for event_name, event_value in event_mapping.items():
            event_options = _yaml_mapping(event_value)
            if event_options is not None and {
                "paths",
                "paths-ignore",
            }.intersection(event_options):
                violations.append(
                    WorkflowViolation(
                        path,
                        1,
                        f"Foundation CI event {event_name!r} cannot use path filters",
                    )
                )
    return violations


def _verify_foundation_aggregate(
    path: Path,
    aggregate: dict[str, Any],
) -> list[WorkflowViolation]:
    violations: list[WorkflowViolation] = []
    if "defaults" in aggregate:
        violations.append(WorkflowViolation(path, 1, "ci-required cannot override run defaults"))
    if aggregate.get("name") != "ci-required":
        violations.append(
            WorkflowViolation(
                path,
                1,
                "Foundation aggregate job id and name must both be ci-required",
            )
        )
    if _needs_names(aggregate.get("needs")) != REQUIRED_FOUNDATION_DEPENDENCIES:
        violations.append(
            WorkflowViolation(
                path,
                1,
                "ci-required must depend exactly on quality, package-artifacts, and security",
            )
        )
    if aggregate.get("runs-on") != "ubuntu-24.04":
        violations.append(
            WorkflowViolation(
                path,
                1,
                "ci-required must use the stable ubuntu-24.04 runner",
            )
        )
    if _yaml_mapping(aggregate.get("permissions")) != {}:
        violations.append(
            WorkflowViolation(
                path,
                1,
                "ci-required permissions must be an explicit empty mapping",
            )
        )
    return violations


def _find_action_step(job: dict[str, Any], action: str) -> dict[str, Any] | None:
    for step_value in _yaml_sequence(job.get("steps")) or []:
        step = _yaml_mapping(step_value)
        if step is not None and step.get("uses") == action:
            return step
    return None


def _verify_dependency_review_step(
    path: Path,
    job: dict[str, Any],
) -> list[WorkflowViolation]:
    dependency_action = next(
        action for action in REQUIRED_SECURITY_ACTIONS if action.startswith("actions/dependency-")
    )
    dependency_step = _find_action_step(job, dependency_action)
    if dependency_step is None:
        return []

    violations: list[WorkflowViolation] = []
    dependency_condition = _normalized_if_expression(dependency_step.get("if"))
    dependency_inputs = _yaml_mapping(dependency_step.get("with")) or {}
    if dependency_condition not in {
        "github.event_name=='pull_request'",
        'github.event_name=="pull_request"',
    }:
        violations.append(
            WorkflowViolation(
                path,
                1,
                "Dependency review must run exactly for pull_request events",
            )
        )
    if dependency_inputs != {"fail-on-severity": "moderate"}:
        violations.append(
            WorkflowViolation(
                path,
                1,
                "Dependency review must fail on moderate-or-higher findings",
            )
        )
    return violations


def _verify_security_checkout_step(
    path: Path,
    job: dict[str, Any],
) -> list[WorkflowViolation]:
    checkout_action = next(
        action for action in REQUIRED_SECURITY_ACTIONS if action.startswith("actions/checkout@")
    )
    checkout_step = _find_action_step(job, checkout_action)
    if checkout_step is None:
        return []
    checkout_inputs = _yaml_mapping(checkout_step.get("with")) or {}
    if checkout_inputs == {
        "fetch-depth": "0",
        "persist-credentials": "false",
    }:
        return []
    return [
        WorkflowViolation(
            path,
            1,
            "Security checkout must fetch complete history without persisted credentials",
        )
    ]


def _verify_gitleaks_step(
    path: Path,
    job: dict[str, Any],
) -> list[WorkflowViolation]:
    gitleaks_action = next(
        action for action in REQUIRED_SECURITY_ACTIONS if action.startswith("gitleaks/")
    )
    gitleaks_step = _find_action_step(job, gitleaks_action)
    if gitleaks_step is None:
        return []
    environment = _yaml_mapping(gitleaks_step.get("env")) or {}
    expected_environment = {
        "GITHUB_TOKEN": "${{ github.token }}",
        "GITLEAKS_ENABLE_COMMENTS": "false",
        "GITLEAKS_ENABLE_UPLOAD_ARTIFACT": "false",
        "GITLEAKS_VERSION": "8.28.0",
    }
    if environment == expected_environment:
        return []
    return [
        WorkflowViolation(
            path,
            1,
            "Gitleaks must use the exact non-commenting, non-uploading, version-pinned environment",
        )
    ]


def _verify_codeql_init_step(
    path: Path,
    job: dict[str, Any],
) -> list[WorkflowViolation]:
    codeql_init_action = next(action for action in REQUIRED_SECURITY_ACTIONS if "/init@" in action)
    codeql_init_step = _find_action_step(job, codeql_init_action)
    if codeql_init_step is None:
        return []
    codeql_inputs = _yaml_mapping(codeql_init_step.get("with")) or {}
    if codeql_inputs == {
        "languages": "javascript-typescript,python",
        "queries": "security-extended",
    }:
        return []
    return [
        WorkflowViolation(
            path,
            1,
            "CodeQL must analyze Python and JavaScript/TypeScript with security-extended queries",
        )
    ]


def _verify_codeql_analyze_step(
    path: Path,
    job: dict[str, Any],
) -> list[WorkflowViolation]:
    codeql_analyze_action = next(
        action for action in REQUIRED_SECURITY_ACTIONS if "/analyze@" in action
    )
    codeql_analyze_step = _find_action_step(job, codeql_analyze_action)
    if codeql_analyze_step is None or "with" not in codeql_analyze_step:
        return []
    return [
        WorkflowViolation(
            path,
            1,
            "CodeQL analyze cannot override upload or analysis inputs",
        )
    ]


def _verify_security_action_conditions(
    path: Path,
    job: dict[str, Any],
) -> list[WorkflowViolation]:
    violations: list[WorkflowViolation] = []
    for action in REQUIRED_SECURITY_ACTIONS:
        if action.startswith("actions/dependency-review-action@"):
            continue
        step = _find_action_step(job, action)
        if step is not None and "if" in step:
            violations.append(
                WorkflowViolation(
                    path,
                    1,
                    f"Mandatory security action {action!r} must run unconditionally",
                )
            )
    return violations


def _verify_security_job(
    path: Path,
    job: dict[str, Any],
) -> list[WorkflowViolation]:
    violations: list[WorkflowViolation] = []
    if "defaults" in job:
        violations.append(
            WorkflowViolation(path, 1, "Foundation job 'security' cannot override run defaults")
        )
    if "if" in job:
        violations.append(
            WorkflowViolation(
                path,
                1,
                "Foundation job 'security' cannot use a job-level if",
            )
        )
    if job.get("runs-on") != "ubuntu-24.04":
        violations.append(
            WorkflowViolation(path, 1, "Foundation job 'security' must run on ubuntu-24.04")
        )
    if not _security_permissions_are_least_privilege(job.get("permissions")):
        violations.append(
            WorkflowViolation(
                path,
                1,
                "Foundation job 'security' must grant only contents: read and "
                "security-events: write",
            )
        )

    actions = {
        action
        for step_value in _yaml_sequence(job.get("steps")) or []
        if (step := _yaml_mapping(step_value)) is not None
        if isinstance(action := step.get("uses"), str)
    }
    missing_actions = REQUIRED_SECURITY_ACTIONS.difference(actions)
    if missing_actions:
        violations.append(
            WorkflowViolation(
                path,
                1,
                "Foundation security job is missing pinned controls: "
                + ", ".join(sorted(missing_actions)),
            )
        )
    violations.extend(
        [
            *_verify_dependency_review_step(path, job),
            *_verify_security_checkout_step(path, job),
            *_verify_gitleaks_step(path, job),
            *_verify_codeql_init_step(path, job),
            *_verify_codeql_analyze_step(path, job),
            *_verify_security_action_conditions(path, job),
        ]
    )
    return violations


def _verify_foundation_workflow(
    path: Path,
    document: dict[str, Any],
    jobs: dict[str, Any],
) -> list[WorkflowViolation]:
    """Protect the stable Stage B CI topology against silent gate shrinkage."""

    violations = _verify_foundation_events(path, document)
    if "defaults" in document:
        violations.append(
            WorkflowViolation(path, 1, "Foundation CI cannot override workflow run defaults")
        )
    missing_jobs = (
        set(REQUIRED_FOUNDATION_COMMANDS).union({"ci-required", "security"}).difference(jobs)
    )
    if missing_jobs:
        violations.append(
            WorkflowViolation(
                path,
                1,
                "Foundation CI is missing required jobs: " + ", ".join(sorted(missing_jobs)),
            )
        )

    for job_id in REQUIRED_FOUNDATION_COMMANDS:
        job = _yaml_mapping(jobs.get(job_id))
        if job is not None:
            violations.extend(_verify_foundation_matrix_job(path, job_id, job))

    security = _yaml_mapping(jobs.get("security"))
    if security is not None:
        violations.extend(_verify_security_job(path, security))

    aggregate = _yaml_mapping(jobs.get("ci-required"))
    if aggregate is not None:
        violations.extend(_verify_foundation_aggregate(path, aggregate))
    return violations


def verify_workflow(  # noqa: PLR0912 - policy branches stay explicit.
    path: Path,
    repository_root: Path = REPOSITORY_ROOT,
    *,
    require_foundation_contract: bool = False,
) -> tuple[list[WorkflowViolation], int]:
    document, violations = _load_yaml(path)
    if document is None:
        return violations, 0

    if "pull_request_target" in _event_names(document.get("on")):
        violations.append(
            WorkflowViolation(
                path,
                1,
                "pull_request_target is forbidden for repository build and test workflows",
            )
        )
    if not _permissions_are_read_only(document.get("permissions"), top_level=True):
        violations.append(
            WorkflowViolation(
                path,
                1,
                "Workflow top-level permissions must be exactly contents: read",
            )
        )

    jobs = _yaml_mapping(document.get("jobs"))
    if not jobs:
        violations.append(WorkflowViolation(path, 1, "Workflow defines no jobs"))
        return violations, 0

    aggregate_count = 0
    for job_id, job_value in jobs.items():
        job = _yaml_mapping(job_value)
        if job is None:
            violations.append(WorkflowViolation(path, 1, f"Job {job_id!r} must be a mapping"))
            continue
        if "continue-on-error" in job:
            violations.append(
                WorkflowViolation(path, 1, f"Job {job_id!r} cannot continue on error")
            )
        permissions_are_valid = (
            _security_permissions_are_least_privilege(job.get("permissions"))
            if require_foundation_contract and job_id == "security"
            else _permissions_are_read_only(job.get("permissions"), top_level=False)
        )
        if "permissions" in job and not permissions_are_valid:
            violations.append(
                WorkflowViolation(path, 1, f"Job {job_id!r} permissions are not read-only")
            )
        if "runs-on" in job:
            timeout = job.get("timeout-minutes")
            if not isinstance(timeout, str) or not timeout.isdigit() or int(timeout) < 1:
                violations.append(
                    WorkflowViolation(path, 1, f"Job {job_id!r} requires timeout-minutes")
                )
            violations.extend(
                _verify_steps(
                    path,
                    job.get("steps"),
                    repository_root,
                    require_timeout=True,
                )
            )
        elif isinstance(job.get("uses"), str):
            violations.extend(
                _verify_action_reference(path, cast(str, job["uses"]), repository_root)
            )
        else:
            violations.append(
                WorkflowViolation(path, 1, f"Job {job_id!r} requires runs-on or uses")
            )

        if job.get("name") == "ci-required":
            aggregate_count += 1
            if _normalized_if_expression(job.get("if")) != "always()":
                violations.append(
                    WorkflowViolation(path, 1, "ci-required must run with always() semantics")
                )
            if not _needs_names(job.get("needs")):
                violations.append(
                    WorkflowViolation(path, 1, "ci-required must aggregate dependent jobs")
                )
            if not _aggregate_asserts_dependencies(job):
                violations.append(
                    WorkflowViolation(
                        path,
                        1,
                        "ci-required must fail unless every dependency result is success",
                    )
                )
    if require_foundation_contract:
        violations.extend(_verify_foundation_workflow(path, document, jobs))
    return violations, aggregate_count


def verify_local_action(
    path: Path, repository_root: Path = REPOSITORY_ROOT
) -> list[WorkflowViolation]:
    document, violations = _load_yaml(path)
    if document is None:
        return violations
    runs = _yaml_mapping(document.get("runs"))
    if runs is None or runs.get("using") != "composite":
        return violations
    violations.extend(
        _verify_steps(path, runs.get("steps"), repository_root, require_timeout=False)
    )
    return violations


def find_violations(
    workflow_root: Path = WORKFLOW_ROOT,
    local_action_root: Path = LOCAL_ACTION_ROOT,
) -> list[WorkflowViolation]:
    workflow_paths = sorted([*workflow_root.glob("*.yml"), *workflow_root.glob("*.yaml")])
    if not workflow_paths:
        return [WorkflowViolation(workflow_root, 1, "No GitHub Actions workflows found")]

    repository_root = workflow_root.parent.parent.resolve()
    violations: list[WorkflowViolation] = []
    violations.extend(verify_root_entrypoints(repository_root / "package.json"))
    aggregate_count = 0
    for path in workflow_paths:
        workflow_violations, count = verify_workflow(
            path,
            repository_root,
            require_foundation_contract=path.name == FOUNDATION_WORKFLOW_NAME,
        )
        violations.extend(workflow_violations)
        aggregate_count += count
    if not (workflow_root / FOUNDATION_WORKFLOW_NAME).is_file():
        violations.append(
            WorkflowViolation(
                workflow_root,
                1,
                f"Required foundation workflow {FOUNDATION_WORKFLOW_NAME!r} is missing",
            )
        )
    if aggregate_count != 1:
        violations.append(
            WorkflowViolation(
                workflow_root,
                1,
                "Exactly one job across all workflows must be named ci-required; "
                f"found {aggregate_count}",
            )
        )

    if local_action_root.exists():
        action_paths = sorted(
            [*local_action_root.rglob("action.yml"), *local_action_root.rglob("action.yaml")]
        )
        for path in action_paths:
            violations.extend(verify_local_action(path, repository_root))
    return sorted(violations, key=lambda violation: (str(violation.path), violation.line))


def _fail(violations: list[WorkflowViolation]) -> NoReturn:
    for violation in violations:
        print(violation.render(), file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    violations = find_violations()
    if violations:
        _fail(violations)
    print("GitHub Actions governance checks passed")


if __name__ == "__main__":
    main()
