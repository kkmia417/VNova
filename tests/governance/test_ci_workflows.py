import json
from pathlib import Path

from tooling.ci.check_workflows import (
    REQUIRED_ROOT_SCRIPTS,
    find_violations,
    verify_root_entrypoints,
)

VALID_WORKFLOW = """\
name: CI
on:
  push:
    branches:
      - main
  pull_request:
  merge_group:
  workflow_dispatch:
permissions:
  contents: read
jobs:
  quality:
    name: quality (${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    timeout-minutes: 5
    strategy:
      fail-fast: false
      matrix:
        os:
          - ubuntu-24.04
          - windows-2025
    steps:
      - name: Test
        timeout-minutes: 1
        run: corepack pnpm run verify
  package-artifacts:
    name: package-artifacts (${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    timeout-minutes: 5
    strategy:
      fail-fast: false
      matrix:
        os:
          - ubuntu-24.04
          - windows-2025
    steps:
      - name: Verify artifacts
        timeout-minutes: 1
        run: corepack pnpm run artifacts:verify
  security:
    name: security
    runs-on: ubuntu-24.04
    timeout-minutes: 5
    permissions:
      contents: read
      security-events: write
    steps:
      - name: Check out history
        timeout-minutes: 1
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd
        with:
          fetch-depth: 0
          persist-credentials: false
      - name: Scan secrets
        timeout-minutes: 1
        uses: gitleaks/gitleaks-action@e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e
        env:
          GITHUB_TOKEN: ${{ github.token }}
          GITLEAKS_ENABLE_COMMENTS: "false"
          GITLEAKS_ENABLE_UPLOAD_ARTIFACT: "false"
          GITLEAKS_VERSION: 8.28.0
      - name: Review dependencies
        if: ${{ github.event_name == 'pull_request' }}
        timeout-minutes: 1
        uses: actions/dependency-review-action@a1d282b36b6f3519aa1f3fc636f609c47dddb294
        with:
          fail-on-severity: moderate
      - name: Initialize CodeQL
        timeout-minutes: 1
        uses: github/codeql-action/init@7188fc363630916deb702c7fdcf4e481b751f97a
        with:
          languages: javascript-typescript,python
          queries: security-extended
      - name: Analyze source
        timeout-minutes: 1
        uses: github/codeql-action/analyze@7188fc363630916deb702c7fdcf4e481b751f97a
  ci-required:
    name: ci-required
    if: ${{ always() }}
    needs:
      - quality
      - package-artifacts
      - security
    runs-on: ubuntu-24.04
    timeout-minutes: 5
    permissions: {}
    steps:
      - name: Require quality
        if: ${{ needs.quality.result != 'success' }}
        timeout-minutes: 1
        run: exit 1
      - name: Require artifacts
        if: ${{ needs.package-artifacts.result != 'success' }}
        timeout-minutes: 1
        run: exit 1
      - name: Require security
        if: ${{ needs.security.result != 'success' }}
        timeout-minutes: 1
        run: exit 1
"""


def _verify_temporary_repository(
    tmp_path: Path,
    workflow: str,
    *,
    local_action: str | None = None,
) -> list[str]:
    (tmp_path / "package.json").write_text(
        json.dumps({"private": True, "scripts": REQUIRED_ROOT_SCRIPTS}),
        encoding="utf-8",
    )
    workflow_root = tmp_path / ".github" / "workflows"
    workflow_root.mkdir(parents=True)
    (workflow_root / "ci.yml").write_text(workflow, encoding="utf-8")
    action_root = tmp_path / ".github" / "actions"
    if local_action is not None:
        wrapper_root = action_root / "wrapper"
        wrapper_root.mkdir(parents=True)
        (wrapper_root / "action.yml").write_text(local_action, encoding="utf-8")
    return [violation.message for violation in find_violations(workflow_root, action_root)]


def test_github_actions_workflows_follow_repository_governance() -> None:
    assert find_violations() == []


def test_root_verify_entrypoint_cannot_drop_a_quality_gate(tmp_path: Path) -> None:
    scripts = dict(REQUIRED_ROOT_SCRIPTS)
    scripts["verify"] = "corepack pnpm run test"
    package_path = tmp_path / "package.json"
    package_path.write_text(
        json.dumps({"private": True, "scripts": scripts}),
        encoding="utf-8",
    )

    messages = [violation.message for violation in verify_root_entrypoints(package_path)]

    assert "Root script 'verify' must equal the governed foundation entrypoint" in messages


def test_root_lint_entrypoint_cannot_drop_python_boundary_guard(tmp_path: Path) -> None:
    scripts = dict(REQUIRED_ROOT_SCRIPTS)
    scripts["lint"] = scripts["lint"].replace(
        "uv run --locked --python 3.13 python -m tooling.architecture.check_boundaries && ",
        "",
    )
    package_path = tmp_path / "package.json"
    package_path.write_text(
        json.dumps({"private": True, "scripts": scripts}),
        encoding="utf-8",
    )

    messages = [violation.message for violation in verify_root_entrypoints(package_path)]

    assert "Root script 'lint' must equal the governed foundation entrypoint" in messages


def test_root_ci_self_check_cannot_be_disconnected(tmp_path: Path) -> None:
    scripts = dict(REQUIRED_ROOT_SCRIPTS)
    scripts["lint"] = scripts["lint"].replace(" && corepack pnpm run ci:check", "")
    package_path = tmp_path / "package.json"
    package_path.write_text(
        json.dumps({"private": True, "scripts": scripts}),
        encoding="utf-8",
    )

    messages = [violation.message for violation in verify_root_entrypoints(package_path)]

    assert "Root script 'lint' must equal the governed foundation entrypoint" in messages


def test_ci_required_job_is_mandatory(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.split("  ci-required:", maxsplit=1)[0]

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("Exactly one job" in message for message in messages)


def test_ci_required_must_assert_dependency_results(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        "        if: ${{ needs.quality.result != 'success' }}\n"
        "        timeout-minutes: 1\n"
        "        run: exit 1",
        "        timeout-minutes: 1\n        run: echo success",
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("fail unless every dependency" in message for message in messages)


def test_ci_required_guards_cannot_use_a_custom_shell(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        "        timeout-minutes: 1\n        run: exit 1",
        "        timeout-minutes: 1\n        shell: echo {0}\n        run: exit 1",
        1,
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("fail unless every dependency" in message for message in messages)


def test_ci_required_rejects_misleading_dependency_condition(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        "if: ${{ needs.quality.result != 'success' }}",
        "if: ${{ needs.quality.result != 'failure' && 'success' }}",
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("fail unless every dependency" in message for message in messages)


def test_pull_request_target_is_rejected_in_flow_style(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        "  pull_request:\n",
        "  pull_request_target:\n",
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("pull_request_target" in message for message in messages)


def test_workflow_steps_require_timeouts(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        "        timeout-minutes: 1\n        run: corepack pnpm run verify",
        "        run: corepack pnpm run verify",
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("Step 1 requires positive timeout" in message for message in messages)


def test_local_composite_action_dependencies_are_sha_pinned(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        "        run: corepack pnpm run verify",
        "        uses: ./.github/actions/wrapper",
    )
    local_action = """\
name: Wrapper
description: Test wrapper
runs:
  using: composite
  steps:
    - uses: actions/checkout@v6
"""

    messages = _verify_temporary_repository(
        tmp_path,
        workflow,
        local_action=local_action,
    )

    assert any("immutable 40-character" in message for message in messages)


def test_duplicate_yaml_keys_are_rejected(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        "permissions:\n  contents: read",
        "permissions:\n  contents: read\npermissions:\n  contents: read",
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("duplicate key" in message for message in messages)


def test_write_permissions_are_rejected(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace("contents: read", "contents: write", 1)

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("permissions must be exactly contents: read" in message for message in messages)


def test_continue_on_error_is_rejected(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        "        timeout-minutes: 1\n        run: corepack pnpm run verify",
        "        timeout-minutes: 1\n"
        "        continue-on-error: true\n"
        "        run: corepack pnpm run verify",
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("cannot continue on error" in message for message in messages)


def test_expression_continue_on_error_is_rejected(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        "        timeout-minutes: 1\n        run: corepack pnpm run verify",
        "        timeout-minutes: 1\n"
        "        continue-on-error: ${{ true }}\n"
        "        run: corepack pnpm run verify",
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("cannot continue on error" in message for message in messages)


def test_checkout_credentials_rule_is_case_insensitive(tmp_path: Path) -> None:
    checkout_reference = "Actions/Checkout@" + "a" * 40
    workflow = VALID_WORKFLOW.replace(
        "        run: corepack pnpm run verify",
        f"        uses: {checkout_reference}",
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("persist-credentials: false" in message for message in messages)


def test_foundation_ci_requires_complete_trigger_set(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace("  merge_group:\n", "")

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("triggers must be exactly" in message for message in messages)


def test_foundation_ci_rejects_path_filtered_pull_requests(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        "  pull_request:\n",
        "  pull_request:\n    paths:\n      - packages/**\n",
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("cannot use path filters" in message for message in messages)


def test_foundation_ci_requires_both_operating_systems(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace("          - windows-2025\n", "", 1)

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any(
        "must cover exactly ubuntu-24.04 and windows-2025" in message for message in messages
    )


def test_foundation_ci_matrix_must_drive_runner(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        "    runs-on: ${{ matrix.os }}",
        "    runs-on: ubuntu-24.04",
        1,
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("must run on matrix.os" in message for message in messages)


def test_foundation_ci_requires_quality_entrypoint(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        "        run: corepack pnpm run verify",
        "        run: corepack pnpm run test",
        1,
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("must execute exactly 'corepack pnpm run verify'" in message for message in messages)


def test_foundation_ci_requires_unconditional_quality_entrypoint(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        "        timeout-minutes: 1\n        run: corepack pnpm run verify",
        "        if: ${{ false }}\n"
        "        timeout-minutes: 1\n"
        "        run: corepack pnpm run verify",
        1,
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any(
        "must execute 'corepack pnpm run verify' unconditionally" in message for message in messages
    )


def test_foundation_ci_required_entrypoint_cannot_use_a_custom_shell(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        "        timeout-minutes: 1\n        run: corepack pnpm run verify",
        "        timeout-minutes: 1\n"
        "        shell: echo {0}\n"
        "        run: corepack pnpm run verify",
        1,
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("with the default shell and working directory" in message for message in messages)


def test_foundation_ci_cannot_override_workflow_run_defaults(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        "permissions:\n  contents: read",
        "permissions:\n  contents: read\ndefaults:\n  run:\n    shell: echo {0}",
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("cannot override workflow run defaults" in message for message in messages)


def test_foundation_ci_cannot_override_job_run_defaults(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        "    steps:\n      - name: Test",
        "    defaults:\n      run:\n        shell: echo {0}\n    steps:\n      - name: Test",
        1,
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("job 'quality' cannot override run defaults" in message for message in messages)


def test_ci_required_cannot_drop_foundation_dependency(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        "      - package-artifacts\n",
        "",
        1,
    ).replace(
        "      - name: Require artifacts\n"
        "        if: ${{ needs.package-artifacts.result != 'success' }}\n"
        "        timeout-minutes: 1\n"
        "        run: exit 1\n",
        "",
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any(
        "must depend exactly on quality, package-artifacts, and security" in message
        for message in messages
    )


def test_foundation_security_job_is_mandatory(tmp_path: Path) -> None:
    prefix, remainder = VALID_WORKFLOW.split("  security:", maxsplit=1)
    _, aggregate = remainder.split("  ci-required:", maxsplit=1)
    workflow = prefix + "  ci-required:" + aggregate

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("missing required jobs: security" in message for message in messages)


def test_foundation_security_controls_cannot_be_removed(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        "        uses: github/codeql-action/analyze@7188fc363630916deb702c7fdcf4e481b751f97a",
        "        run: echo skipped",
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("security job is missing pinned controls" in message for message in messages)


def test_foundation_security_permissions_are_exact(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        "      security-events: write\n",
        "      security-events: write\n      issues: write\n",
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("must grant only contents: read" in message for message in messages)


def test_foundation_gitleaks_version_is_pinned(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        "          GITLEAKS_VERSION: 8.28.0", "          GITLEAKS_VERSION: latest"
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("Gitleaks must use the exact" in message for message in messages)


def test_foundation_security_checkout_requires_complete_history(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace("          fetch-depth: 0", "          fetch-depth: 1")

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("fetch complete history" in message for message in messages)


def test_foundation_dependency_review_condition_is_exact(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        "if: ${{ github.event_name == 'pull_request' }}",
        "if: ${{ false }}",
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("exactly for pull_request events" in message for message in messages)


def test_foundation_dependency_review_severity_is_exact(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace("fail-on-severity: moderate", "fail-on-severity: critical")

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("fail on moderate-or-higher" in message for message in messages)


def test_foundation_codeql_languages_and_queries_are_exact(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        "          languages: javascript-typescript,python\n          queries: security-extended",
        "          languages: python\n          queries: default",
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("analyze Python and JavaScript/TypeScript" in message for message in messages)


def test_foundation_codeql_analyze_cannot_disable_upload(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        "        uses: github/codeql-action/analyze@7188fc363630916deb702c7fdcf4e481b751f97a",
        "        uses: github/codeql-action/analyze@7188fc363630916deb702c7fdcf4e481b751f97a\n"
        "        with:\n"
        "          upload: false",
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("cannot override upload or analysis inputs" in message for message in messages)


def test_foundation_mandatory_security_actions_cannot_be_conditionally_skipped(
    tmp_path: Path,
) -> None:
    workflow = VALID_WORKFLOW.replace(
        "      - name: Analyze source\n        timeout-minutes: 1",
        "      - name: Analyze source\n        if: ${{ false }}\n        timeout-minutes: 1",
    )

    messages = _verify_temporary_repository(tmp_path, workflow)

    assert any("must run unconditionally" in message for message in messages)
