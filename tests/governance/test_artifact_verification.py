from __future__ import annotations

import base64
import hashlib
import json
import tomllib
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]

from tooling.artifacts import verify as artifact_verify
from tooling.artifacts.verify import (
    EXPECTED_CONTRACT_VERSION,
    ArtifactVerificationError,
    validate_archive_member_name,
    verify_declared_versions,
    verify_manifest_source_hash,
    verify_member_allowlist,
)
from tooling.ci.check_workflows import UniqueKeyLoader

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _synthetic_wheel_members(
    *,
    package_digest: str | None = None,
    package_size: str | None = None,
) -> tuple[dict[str, bytes], artifact_verify.PythonDistribution]:
    distribution = artifact_verify.PythonDistribution(
        project_name="test-package",
        import_name="test_package",
        project_root=Path("."),
        package_members=("test_package/__init__.py",),
        version="1.2.3",
    )
    package_path = "test_package/__init__.py"
    package_contents = b"VALUE = 1\n"
    metadata_path = f"{distribution.dist_info}/METADATA"
    wheel_path = f"{distribution.dist_info}/WHEEL"
    record_path = f"{distribution.dist_info}/RECORD"
    members = {
        package_path: package_contents,
        metadata_path: b"Name: test-package\nVersion: 1.2.3\n",
        wheel_path: b"Wheel-Version: 1.0\n",
    }

    rows: list[str] = []
    for name, contents in members.items():
        encoded_digest = base64.urlsafe_b64encode(hashlib.sha256(contents).digest()).rstrip(b"=")
        digest = f"sha256={encoded_digest.decode('ascii')}"
        size = str(len(contents))
        if name == package_path:
            digest = package_digest if package_digest is not None else digest
            size = package_size if package_size is not None else size
        rows.append(f"{name},{digest},{size}")
    rows.append(f"{record_path},,")
    members[record_path] = ("\n".join(rows) + "\n").encode()
    return members, distribution


@pytest.mark.parametrize(
    "member",
    [
        "../escape",
        "/absolute",
        "C:/windows",
        "package\\windows",
        "package//double",
        "package/./relative",
        "package/../escape",
    ],
)
def test_archive_member_paths_reject_traversal_and_nonportable_names(member: str) -> None:
    with pytest.raises(ArtifactVerificationError, match="Unsafe archive member path"):
        validate_archive_member_name(member)


@pytest.mark.parametrize(
    "member",
    [
        "package/__pycache__/module.pyc",
        "package/.pytest_cache/state",
        "package/build/tsconfig.tsbuildinfo",
        "package/node_modules/dependency/index.js",
        "package/cache.pyc",
    ],
)
def test_archive_member_paths_reject_cache_content(member: str) -> None:
    with pytest.raises(ArtifactVerificationError, match="forbidden"):
        validate_archive_member_name(member)


def test_archive_member_allowlist_is_exact() -> None:
    with pytest.raises(ArtifactVerificationError, match=r"unexpected=.*debug.log"):
        verify_member_allowlist(
            {"package/index.js", "package/debug.log"},
            {"package/index.js"},
            "test archive",
        )


def test_manifest_source_hash_accepts_v2_format() -> None:
    canonical_schema = b'{\r\n  "type": "object"  \r\n}\r\n'
    normalized_schema = b'{\n  "type": "object"\n}\n'
    manifest = json.dumps(
        {"manifest_version": 2, "source_sha256": hashlib.sha256(normalized_schema).hexdigest()}
    ).encode()

    verify_manifest_source_hash(manifest, canonical_schema, "test manifest")


def test_manifest_source_hash_rejects_wrong_digest() -> None:
    manifest = json.dumps({"source_sha256": "0" * 64}).encode()

    with pytest.raises(ArtifactVerificationError, match="does not match"):
        verify_manifest_source_hash(manifest, b"{}\n", "test manifest")


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_package_json_rejects_nonstandard_numeric_constants(constant: str) -> None:
    with pytest.raises(ArtifactVerificationError, match="Non-standard JSON numeric constant"):
        artifact_verify._load_json_bytes(
            f'{{"value": {constant}}}\n'.encode(),
            "test JSON",
        )


def test_repeated_clean_builds_must_be_byte_identical(tmp_path: Path) -> None:
    first = tmp_path / "first.tgz"
    second = tmp_path / "second.tgz"
    first.write_bytes(b"first")
    second.write_bytes(b"second")

    with pytest.raises(ArtifactVerificationError, match="not reproducible"):
        artifact_verify._verify_reproducible_archives(
            {"package.tgz": first},
            {"package.tgz": second},
        )


def test_wheel_record_accepts_canonical_sha256_and_exact_size() -> None:
    members, distribution = _synthetic_wheel_members()

    artifact_verify._verify_wheel_record(members, distribution)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda digest: f"{digest}é",
        lambda digest: f"{digest}=",
        lambda digest: f"{digest[:-1]}+",
        lambda digest: digest[:-1],
        lambda _digest: "sha256=not-base64url",
    ],
    ids=["non-ascii-suffix", "padding", "invalid-alphabet", "short", "malformed"],
)
def test_wheel_record_rejects_noncanonical_sha256_digest(mutation: Any) -> None:
    baseline_members, _ = _synthetic_wheel_members()
    package_contents = baseline_members["test_package/__init__.py"]
    encoded_digest = base64.urlsafe_b64encode(hashlib.sha256(package_contents).digest()).rstrip(
        b"="
    )
    canonical_digest = f"sha256={encoded_digest.decode('ascii')}"
    members, distribution = _synthetic_wheel_members(package_digest=mutation(canonical_digest))

    with pytest.raises(ArtifactVerificationError, match="canonical unpadded SHA-256"):
        artifact_verify._verify_wheel_record(members, distribution)


@pytest.mark.parametrize("size", ["010", "+10", " 10", "10 ", "-1"])
def test_wheel_record_rejects_noncanonical_or_wrong_size(size: str) -> None:
    members, distribution = _synthetic_wheel_members(package_size=size)

    with pytest.raises(ArtifactVerificationError, match="size mismatch"):
        artifact_verify._verify_wheel_record(members, distribution)


def test_contract_package_versions_match_release_line() -> None:
    assert verify_declared_versions() == EXPECTED_CONTRACT_VERSION == "0.1.0"


@pytest.mark.parametrize(
    "relative_path",
    [
        "packages/contracts/python/pyproject.toml",
        "packages/safety/pyproject.toml",
    ],
)
def test_python_sdists_use_an_explicit_source_allowlist(relative_path: str) -> None:
    document = tomllib.loads((REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8"))

    assert document["tool"]["hatch"]["build"]["targets"]["sdist"] == {"only-include": ["src"]}


def test_typescript_prepack_gate_is_mandatory() -> None:
    package_root = REPOSITORY_ROOT / "packages" / "contracts" / "typescript"
    package = json.loads((package_root / "package.json").read_text(encoding="utf-8"))
    prepack_script = (package_root / "scripts" / "prepack.mjs").read_text(encoding="utf-8")

    assert package["scripts"]["prepack"] == "node scripts/prepack.mjs"
    assert package["engines"]["node"] == ">=24.11.0 <25"
    assert (package_root / "scripts" / "prepack.mjs").is_file()
    ordered_operations = [
        "tooling.contracts.generate",
        "scripts/clean-build.mjs",
        "typescriptCompiler,",
        "copyFile(canonicalSchema",
    ]
    positions = [prepack_script.index(operation) for operation in ordered_operations]
    assert positions == sorted(positions)


def test_foundation_jobs_are_aggregated_by_ci_required() -> None:
    workflow_path = REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml"
    workflow = yaml.load(
        workflow_path.read_text(encoding="utf-8"),
        Loader=UniqueKeyLoader,  # noqa: S506 - BaseLoader cannot construct Python objects.
    )
    assert isinstance(workflow, dict)
    jobs: dict[str, Any] = workflow["jobs"]

    assert "package-artifacts" in jobs
    assert jobs["package-artifacts"]["strategy"]["matrix"]["os"] == [
        "ubuntu-24.04",
        "windows-2025",
    ]
    needs = jobs["ci-required"]["needs"]
    assert set(needs) == {"quality", "package-artifacts", "security"}
    conditions = {step.get("if") for step in jobs["ci-required"]["steps"] if isinstance(step, dict)}
    assert "${{ needs.quality.result != 'success' }}" in conditions
    assert "${{ needs.package-artifacts.result != 'success' }}" in conditions
    assert "${{ needs.security.result != 'success' }}" in conditions
