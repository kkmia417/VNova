"""Build and deeply verify VNova's Python and TypeScript package archives."""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from pathlib import Path, PurePosixPath
from typing import Any, NoReturn

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PYTHON_CONTRACTS_ROOT = REPOSITORY_ROOT / "packages" / "contracts" / "python"
PYTHON_SAFETY_ROOT = REPOSITORY_ROOT / "packages" / "safety"
TYPESCRIPT_CONTRACTS_ROOT = REPOSITORY_ROOT / "packages" / "contracts" / "typescript"
CANONICAL_SCHEMA_PATH = REPOSITORY_ROOT / "specs" / "events" / "event-envelope.v1.schema.json"
CANONICAL_CATALOG_PATH = REPOSITORY_ROOT / "specs" / "events" / "event-catalog.v1.json"
ROOT_GITIGNORE_PATH = REPOSITORY_ROOT / ".gitignore"
WORKSPACE_MANIFEST_PATH = REPOSITORY_ROOT / "packages" / "contracts" / "manifest.json"
PYTHON_MANIFEST_SOURCE_PATH = (
    PYTHON_CONTRACTS_ROOT / "src" / "vnova_contracts" / "contract-manifest.json"
)
TYPESCRIPT_MANIFEST_SOURCE_PATH = TYPESCRIPT_CONTRACTS_ROOT / "contract-manifest.json"
TYPESCRIPT_GENERATED_SOURCE_PATH = (
    TYPESCRIPT_CONTRACTS_ROOT / "src" / "generated" / "event-envelope.v1.ts"
)
PYTHON_ACTIVE_EVENT_REGISTRY_SOURCE_PATH = (
    PYTHON_CONTRACTS_ROOT / "src" / "vnova_contracts" / "registry" / "active-event-registry.v1.json"
)
TYPESCRIPT_ACTIVE_EVENT_REGISTRY_SOURCE_PATH = (
    TYPESCRIPT_CONTRACTS_ROOT / "src" / "generated" / "active-event-registry.v1.json"
)

EXPECTED_CONTRACT_VERSION = "0.1.0"
EXPECTED_NODE_ENGINE = ">=24.11.0 <25"
EXPECTED_SCHEMA_SOURCE = "specs/events/event-envelope.v1.schema.json"
EXPECTED_CATALOG_SOURCE = "specs/events/event-catalog.v1.json"
EXPECTED_MANIFEST_VERSION = 2
COMMAND_TIMEOUT_SECONDS = 300
MAX_ARCHIVE_BYTES = 50 * 1024 * 1024
MAX_MEMBER_BYTES = 10 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED_BYTES = 30 * 1024 * 1024
WHEEL_RECORD_COLUMNS = 3

DENIED_MEMBER_COMPONENTS = frozenset(
    {
        ".git",
        ".hg",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".svn",
        "__pycache__",
        "build",
        "coverage",
        "node_modules",
    }
)
DENIED_MEMBER_SUFFIXES = (".pyc", ".pyo", ".tsbuildinfo")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
WHEEL_RECORD_SHA256_PATTERN = re.compile(r"^sha256=[A-Za-z0-9_-]{43}$", re.ASCII)
PYTHON_MANIFEST_ARTIFACT_PATHS = frozenset(
    {
        "generated/event_envelope_v1.py",
        "registry/active-event-registry.v1.json",
        "schemas/event-envelope.v1.schema.json",
    }
)
TYPESCRIPT_MANIFEST_ARTIFACT_PATHS = frozenset(
    {
        "dist/generated/active-event-registry.v1.json",
        "dist/generated/event-envelope.v1.schema.json",
    }
)
WORKSPACE_MANIFEST_ARTIFACT_PATHS = frozenset(
    {
        "packages/contracts/python/src/vnova_contracts/generated/event_envelope_v1.py",
        ("packages/contracts/python/src/vnova_contracts/registry/active-event-registry.v1.json"),
        "packages/contracts/python/src/vnova_contracts/schemas/event-envelope.v1.schema.json",
        "packages/contracts/typescript/src/generated/active-event-registry.v1.json",
        "packages/contracts/typescript/src/generated/event-envelope.v1.schema.json",
        "packages/contracts/typescript/src/generated/event-envelope.v1.ts",
    }
)

CONTRACTS_PYTHON_MEMBERS = (
    "vnova_contracts/__init__.py",
    "vnova_contracts/_base.py",
    "vnova_contracts/contract-manifest.json",
    "vnova_contracts/py.typed",
    "vnova_contracts/validation.py",
    "vnova_contracts/generated/__init__.py",
    "vnova_contracts/generated/event_envelope_v1.py",
    "vnova_contracts/registry/__init__.py",
    "vnova_contracts/registry/active-event-registry.v1.json",
    "vnova_contracts/schemas/__init__.py",
    "vnova_contracts/schemas/event-envelope.v1.schema.json",
)
SAFETY_PYTHON_MEMBERS = (
    "vnova_safety/__init__.py",
    "vnova_safety/_mint.py",
    "vnova_safety/py.typed",
)
TYPESCRIPT_ARCHIVE_MEMBERS = frozenset(
    {
        "package/contract-manifest.json",
        "package/dist/generated/active-event-registry.v1.json",
        "package/dist/generated/event-envelope.v1.d.ts",
        "package/dist/generated/event-envelope.v1.js",
        "package/dist/generated/event-envelope.v1.schema.json",
        "package/dist/index.d.ts",
        "package/dist/index.js",
        "package/dist/types.d.ts",
        "package/dist/types.js",
        "package/dist/validation.d.ts",
        "package/dist/validation.js",
        "package/package.json",
    }
)


class ArtifactVerificationError(RuntimeError):
    """Raised when a built archive violates the release contract."""


@dataclass(frozen=True)
class PythonDistribution:
    project_name: str
    import_name: str
    project_root: Path
    package_members: tuple[str, ...]
    version: str = EXPECTED_CONTRACT_VERSION

    @property
    def normalized_name(self) -> str:
        return self.project_name.replace("-", "_")

    @property
    def wheel_filename(self) -> str:
        return f"{self.normalized_name}-{self.version}-py3-none-any.whl"

    @property
    def sdist_filename(self) -> str:
        return f"{self.normalized_name}-{self.version}.tar.gz"

    @property
    def dist_info(self) -> str:
        return f"{self.normalized_name}-{self.version}.dist-info"

    @property
    def sdist_root(self) -> str:
        return f"{self.normalized_name}-{self.version}"


PYTHON_DISTRIBUTIONS = (
    PythonDistribution(
        project_name="vnova-contracts",
        import_name="vnova_contracts",
        project_root=PYTHON_CONTRACTS_ROOT,
        package_members=CONTRACTS_PYTHON_MEMBERS,
    ),
    PythonDistribution(
        project_name="vnova-safety",
        import_name="vnova_safety",
        project_root=PYTHON_SAFETY_ROOT,
        package_members=SAFETY_PYTHON_MEMBERS,
    ),
)


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ArtifactVerificationError(f"Duplicate JSON key in package artifact: {key}")
        result[key] = value
    return result


def _reject_nonstandard_json_constant(value: str) -> NoReturn:
    raise ArtifactVerificationError(f"Non-standard JSON numeric constant: {value}")


def _load_json_bytes(contents: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(
            contents.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_constant=_reject_nonstandard_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ArtifactVerificationError(f"Invalid UTF-8 JSON in {label}: {error}") from error
    if not isinstance(value, dict):
        raise ArtifactVerificationError(f"JSON root in {label} must be an object")
    return value


def _project_version(path: Path) -> str:
    try:
        document = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        raise ArtifactVerificationError(f"Cannot read package metadata {path}: {error}") from error
    project = document.get("project")
    version = project.get("version") if isinstance(project, Mapping) else None
    if not isinstance(version, str) or not version:
        raise ArtifactVerificationError(f"Package metadata has no project.version: {path}")
    return version


def verify_declared_versions() -> str:
    """Require the Python and TypeScript contract release lines to be identical."""

    python_version = _project_version(PYTHON_CONTRACTS_ROOT / "pyproject.toml")
    safety_version = _project_version(PYTHON_SAFETY_ROOT / "pyproject.toml")
    typescript_package = _load_json_bytes(
        (TYPESCRIPT_CONTRACTS_ROOT / "package.json").read_bytes(),
        "TypeScript contracts package.json",
    )
    typescript_version = typescript_package.get("version")
    if not isinstance(typescript_version, str):
        raise ArtifactVerificationError("TypeScript contracts package has no string version")
    typescript_engines = typescript_package.get("engines")
    node_engine = (
        typescript_engines.get("node") if isinstance(typescript_engines, Mapping) else None
    )
    if node_engine != EXPECTED_NODE_ENGINE:
        raise ArtifactVerificationError(
            f"TypeScript contracts package must require Node.js {EXPECTED_NODE_ENGINE}"
        )

    versions = {
        "Python contracts": python_version,
        "Python safety": safety_version,
        "TypeScript contracts": typescript_version,
    }
    unexpected = {
        name: version for name, version in versions.items() if version != EXPECTED_CONTRACT_VERSION
    }
    if unexpected:
        details = ", ".join(f"{name}={version}" for name, version in sorted(unexpected.items()))
        raise ArtifactVerificationError(
            f"Package versions must all be {EXPECTED_CONTRACT_VERSION}: {details}"
        )
    if python_version != typescript_version:
        raise ArtifactVerificationError(
            "Python and TypeScript contracts package versions must remain identical"
        )
    return python_version


def validate_archive_member_name(name: str) -> None:
    """Reject non-portable, traversing, hidden-cache, and generated-cache member paths."""

    if not name or "\x00" in name or "\\" in name:
        raise ArtifactVerificationError(f"Unsafe archive member path: {name!r}")
    raw_parts = name.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        raise ArtifactVerificationError(f"Unsafe archive member path: {name!r}")
    path = PurePosixPath(name)
    if path.is_absolute() or re.match(r"^[A-Za-z]:", name):
        raise ArtifactVerificationError(f"Unsafe archive member path: {name!r}")
    if any(part in DENIED_MEMBER_COMPONENTS for part in path.parts):
        raise ArtifactVerificationError(f"Cache or workspace content is forbidden: {name}")
    if name.endswith(DENIED_MEMBER_SUFFIXES):
        raise ArtifactVerificationError(f"Generated cache file is forbidden: {name}")


def verify_member_allowlist(
    actual: Iterable[str],
    expected: Iterable[str],
    label: str,
) -> None:
    """Require an exact archive member set."""

    actual_set = set(actual)
    expected_set = set(expected)
    unexpected = sorted(actual_set - expected_set)
    missing = sorted(expected_set - actual_set)
    if unexpected or missing:
        details: list[str] = []
        if unexpected:
            details.append(f"unexpected={unexpected}")
        if missing:
            details.append(f"missing={missing}")
        raise ArtifactVerificationError(f"{label} member allowlist mismatch: {'; '.join(details)}")


def _check_archive_file(path: Path) -> None:
    if not path.is_file():
        raise ArtifactVerificationError(f"Expected archive was not built: {path}")
    size = path.stat().st_size
    if size <= 0 or size > MAX_ARCHIVE_BYTES:
        raise ArtifactVerificationError(f"Archive size is outside the safe range: {path} ({size})")


def _store_member(
    members: dict[str, bytes],
    name: str,
    contents: bytes,
    total_uncompressed: int,
) -> int:
    validate_archive_member_name(name)
    if name in members:
        raise ArtifactVerificationError(f"Duplicate archive member: {name}")
    if len(contents) > MAX_MEMBER_BYTES:
        raise ArtifactVerificationError(f"Archive member is too large: {name}")
    next_total = total_uncompressed + len(contents)
    if next_total > MAX_TOTAL_UNCOMPRESSED_BYTES:
        raise ArtifactVerificationError("Archive exceeds the uncompressed-size safety limit")
    members[name] = contents
    return next_total


def _read_wheel(path: Path) -> dict[str, bytes]:
    _check_archive_file(path)
    members: dict[str, bytes] = {}
    total_uncompressed = 0
    try:
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    raise ArtifactVerificationError(
                        f"Directory entries are forbidden: {info.filename}"
                    )
                file_type = (info.external_attr >> 16) & 0o170000
                if file_type == stat.S_IFLNK:
                    raise ArtifactVerificationError(
                        f"Symbolic links are forbidden: {info.filename}"
                    )
                if info.flag_bits & 0x1:
                    raise ArtifactVerificationError(
                        f"Encrypted wheel members are forbidden: {info.filename}"
                    )
                if info.file_size > MAX_MEMBER_BYTES:
                    raise ArtifactVerificationError(f"Archive member is too large: {info.filename}")
                contents = archive.read(info)
                total_uncompressed = _store_member(
                    members,
                    info.filename,
                    contents,
                    total_uncompressed,
                )
    except (OSError, zipfile.BadZipFile) as error:
        raise ArtifactVerificationError(f"Cannot read wheel {path}: {error}") from error
    return members


def _read_tar_archive(path: Path) -> dict[str, bytes]:
    _check_archive_file(path)
    members: dict[str, bytes] = {}
    total_uncompressed = 0
    try:
        with tarfile.open(path, mode="r:gz") as archive:
            for info in archive.getmembers():
                if not info.isfile():
                    raise ArtifactVerificationError(
                        f"Only regular archive members are allowed: {info.name}"
                    )
                if info.size < 0 or info.size > MAX_MEMBER_BYTES:
                    raise ArtifactVerificationError(f"Archive member is too large: {info.name}")
                member_file = archive.extractfile(info)
                if member_file is None:
                    raise ArtifactVerificationError(f"Cannot read archive member: {info.name}")
                contents = member_file.read(MAX_MEMBER_BYTES + 1)
                if len(contents) != info.size:
                    raise ArtifactVerificationError(f"Archive member size mismatch: {info.name}")
                total_uncompressed = _store_member(
                    members,
                    info.name,
                    contents,
                    total_uncompressed,
                )
    except (OSError, tarfile.TarError) as error:
        raise ArtifactVerificationError(f"Cannot read tar archive {path}: {error}") from error
    return members


def _wheel_expected_members(distribution: PythonDistribution) -> frozenset[str]:
    return frozenset(
        {
            *distribution.package_members,
            f"{distribution.dist_info}/METADATA",
            f"{distribution.dist_info}/RECORD",
            f"{distribution.dist_info}/WHEEL",
        }
    )


def _sdist_expected_members(distribution: PythonDistribution) -> frozenset[str]:
    root = distribution.sdist_root
    return frozenset(
        {
            *(f"{root}/src/{member}" for member in distribution.package_members),
            f"{root}/.gitignore",
            f"{root}/PKG-INFO",
            f"{root}/pyproject.toml",
        }
    )


def _verify_python_metadata(
    metadata_bytes: bytes,
    distribution: PythonDistribution,
    label: str,
) -> None:
    message = BytesParser(policy=policy.default).parsebytes(metadata_bytes)
    if message["Name"] != distribution.project_name:
        raise ArtifactVerificationError(f"{label} project name mismatch: {message['Name']!r}")
    if message["Version"] != distribution.version:
        raise ArtifactVerificationError(f"{label} version mismatch: {message['Version']!r}")


def _verify_wheel_record(
    members: Mapping[str, bytes],
    distribution: PythonDistribution,
) -> None:
    record_path = f"{distribution.dist_info}/RECORD"
    try:
        rows = list(csv.reader(io.StringIO(members[record_path].decode("utf-8"), newline="")))
    except (KeyError, UnicodeDecodeError, csv.Error) as error:
        raise ArtifactVerificationError(
            f"Invalid wheel RECORD for {distribution.project_name}: {error}"
        ) from error

    records: dict[str, tuple[str, str]] = {}
    for row in rows:
        if len(row) != WHEEL_RECORD_COLUMNS:
            raise ArtifactVerificationError(
                f"Wheel RECORD row must have three columns: {distribution.project_name}"
            )
        name, digest, size = row
        validate_archive_member_name(name)
        if name in records:
            raise ArtifactVerificationError(f"Duplicate wheel RECORD entry: {name}")
        records[name] = (digest, size)
    verify_member_allowlist(records, members, f"{distribution.project_name} wheel RECORD")

    for name, contents in members.items():
        digest, size = records[name]
        if name == record_path:
            if digest or size:
                raise ArtifactVerificationError("Wheel RECORD must not hash itself")
            continue
        if WHEEL_RECORD_SHA256_PATTERN.fullmatch(digest) is None:
            raise ArtifactVerificationError(
                f"Wheel RECORD must use canonical unpadded SHA-256: {name}"
            )
        expected_digest = (
            base64.urlsafe_b64encode(hashlib.sha256(contents).digest()).rstrip(b"=").decode("ascii")
        )
        if digest.removeprefix("sha256=") != expected_digest:
            raise ArtifactVerificationError(f"Wheel RECORD digest mismatch: {name}")
        if size != str(len(contents)):
            raise ArtifactVerificationError(f"Wheel RECORD size mismatch: {name}")


def _verify_python_source_bytes(
    wheel_members: Mapping[str, bytes],
    sdist_members: Mapping[str, bytes],
    distribution: PythonDistribution,
) -> None:
    for member in distribution.package_members:
        source = (distribution.project_root / "src" / Path(member)).read_bytes()
        if wheel_members[member] != source:
            raise ArtifactVerificationError(f"Wheel member differs from source: {member}")
        sdist_member = f"{distribution.sdist_root}/src/{member}"
        if sdist_members[sdist_member] != source:
            raise ArtifactVerificationError(f"Sdist member differs from source: {sdist_member}")

    pyproject_member = f"{distribution.sdist_root}/pyproject.toml"
    if (
        sdist_members[pyproject_member]
        != (distribution.project_root / "pyproject.toml").read_bytes()
    ):
        raise ArtifactVerificationError(
            f"Sdist pyproject.toml differs from source: {distribution.project_name}"
        )
    gitignore_member = f"{distribution.sdist_root}/.gitignore"
    if sdist_members[gitignore_member] != ROOT_GITIGNORE_PATH.read_bytes():
        raise ArtifactVerificationError(
            f"Sdist .gitignore differs from repository source: {distribution.project_name}"
        )


def _normalized_schema_bytes(contents: bytes) -> bytes:
    try:
        text = contents.decode("utf-8").replace("\r\n", "\n")
    except UnicodeDecodeError as error:
        raise ArtifactVerificationError("Canonical schema must be UTF-8") from error
    normalized = "\n".join(line.rstrip() for line in text.splitlines()).rstrip() + "\n"
    return normalized.encode("utf-8")


def verify_manifest_source_hash(
    manifest_bytes: bytes,
    canonical_schema_bytes: bytes,
    label: str,
) -> None:
    """Verify a manifest's normalized canonical-source digest."""

    manifest = _load_json_bytes(manifest_bytes, label)
    source_digest = manifest.get("source_sha256")
    if not isinstance(source_digest, str) or SHA256_PATTERN.fullmatch(source_digest) is None:
        raise ArtifactVerificationError(f"{label} requires a lowercase source_sha256 digest")
    expected_digest = hashlib.sha256(_normalized_schema_bytes(canonical_schema_bytes)).hexdigest()
    if source_digest != expected_digest:
        raise ArtifactVerificationError(
            f"{label} source_sha256 does not match the canonical event schema"
        )


def _verify_manifest_common(
    manifest: Mapping[str, Any],
    canonical_schema_bytes: bytes,
    canonical_catalog_bytes: bytes,
    label: str,
) -> None:
    if manifest.get("manifest_version") != EXPECTED_MANIFEST_VERSION:
        raise ArtifactVerificationError(
            f"{label} must use manifest_version {EXPECTED_MANIFEST_VERSION}"
        )
    if manifest.get("source") != EXPECTED_SCHEMA_SOURCE:
        raise ArtifactVerificationError(f"{label} canonical source path mismatch")
    source_digest = manifest.get("source_sha256")
    expected_source_digest = hashlib.sha256(
        _normalized_schema_bytes(canonical_schema_bytes)
    ).hexdigest()
    if source_digest != expected_source_digest:
        raise ArtifactVerificationError(f"{label} canonical source digest mismatch")
    if manifest.get("catalog_source") != EXPECTED_CATALOG_SOURCE:
        raise ArtifactVerificationError(f"{label} canonical catalog path mismatch")
    catalog_digest = manifest.get("catalog_source_sha256")
    expected_catalog_digest = hashlib.sha256(
        _normalized_schema_bytes(canonical_catalog_bytes)
    ).hexdigest()
    if catalog_digest != expected_catalog_digest:
        raise ArtifactVerificationError(f"{label} canonical catalog digest mismatch")

    canonical_schema = _load_json_bytes(canonical_schema_bytes, "canonical event schema")
    schema_id = canonical_schema.get("$id")
    if not isinstance(schema_id, str) or manifest.get("schema_id") != schema_id:
        raise ArtifactVerificationError(f"{label} canonical schema_id mismatch")

    generators = manifest.get("generators")
    if not isinstance(generators, Mapping) or set(generators) != {"python", "typescript"}:
        raise ArtifactVerificationError(f"{label} generator provenance is incomplete")
    if not all(isinstance(value, str) and value for value in generators.values()):
        raise ArtifactVerificationError(f"{label} generator versions must be non-empty strings")


def _manifest_artifact_digests(
    manifest: Mapping[str, Any],
    field: str,
    expected_paths: frozenset[str],
    label: str,
) -> dict[str, str]:
    raw_artifacts = manifest.get(field)
    if not isinstance(raw_artifacts, list) or not raw_artifacts:
        raise ArtifactVerificationError(f"{label} requires a non-empty {field} list")

    digests: dict[str, str] = {}
    for index, raw_artifact in enumerate(raw_artifacts):
        if not isinstance(raw_artifact, Mapping) or set(raw_artifact) != {"path", "sha256"}:
            raise ArtifactVerificationError(
                f"{label} {field} entry {index} must contain only path and sha256"
            )
        path = raw_artifact.get("path")
        digest = raw_artifact.get("sha256")
        if not isinstance(path, str):
            raise ArtifactVerificationError(f"{label} {field} entry {index} path must be a string")
        validate_archive_member_name(path)
        if path in digests:
            raise ArtifactVerificationError(f"{label} contains duplicate artifact path: {path}")
        if not isinstance(digest, str) or SHA256_PATTERN.fullmatch(digest) is None:
            raise ArtifactVerificationError(f"{label} artifact requires lowercase SHA-256: {path}")
        digests[path] = digest

    verify_member_allowlist(digests, expected_paths, f"{label} {field}")
    return digests


def _verify_distribution_manifest(
    manifest_bytes: bytes,
    archive_members: Mapping[str, bytes],
    manifest_member: str,
    *,
    ecosystem: str,
    package_name: str,
    package_version: str,
    expected_artifact_paths: frozenset[str],
    canonical_schema_bytes: bytes,
    canonical_catalog_bytes: bytes,
    generated_source_bytes: bytes | None,
    label: str,
) -> None:
    manifest = _load_json_bytes(manifest_bytes, label)
    _verify_manifest_common(
        manifest,
        canonical_schema_bytes,
        canonical_catalog_bytes,
        label,
    )
    expected_keys = {
        "artifacts",
        "catalog_source",
        "catalog_source_sha256",
        "generators",
        "manifest_version",
        "package",
        "schema_id",
        "source",
        "source_sha256",
    }
    if generated_source_bytes is not None:
        expected_keys.add("generated_source_sha256")
    if set(manifest) != expected_keys:
        raise ArtifactVerificationError(f"{label} top-level fields do not match manifest v2")

    expected_package = {
        "ecosystem": ecosystem,
        "name": package_name,
        "version": package_version,
    }
    if manifest.get("package") != expected_package:
        raise ArtifactVerificationError(f"{label} package identity mismatch")

    digests = _manifest_artifact_digests(
        manifest,
        "artifacts",
        expected_artifact_paths,
        label,
    )
    manifest_parent = PurePosixPath(manifest_member).parent
    for relative_path, expected_digest in digests.items():
        archive_path = str(manifest_parent / relative_path)
        contents = archive_members.get(archive_path)
        if contents is None:
            raise ArtifactVerificationError(
                f"{label} artifact is absent from the distribution: {relative_path}"
            )
        if hashlib.sha256(contents).hexdigest() != expected_digest:
            raise ArtifactVerificationError(f"{label} artifact digest mismatch: {relative_path}")

    if generated_source_bytes is not None:
        generated_source_digest = manifest.get("generated_source_sha256")
        if (
            not isinstance(generated_source_digest, str)
            or SHA256_PATTERN.fullmatch(generated_source_digest) is None
            or generated_source_digest != hashlib.sha256(generated_source_bytes).hexdigest()
        ):
            raise ArtifactVerificationError(
                f"{label} generated_source_sha256 does not match generated TypeScript"
            )


def _verify_workspace_manifest(
    canonical_schema_bytes: bytes,
    canonical_catalog_bytes: bytes,
) -> None:
    manifest = _load_json_bytes(WORKSPACE_MANIFEST_PATH.read_bytes(), "workspace manifest")
    label = "workspace manifest"
    _verify_manifest_common(
        manifest,
        canonical_schema_bytes,
        canonical_catalog_bytes,
        label,
    )
    expected_keys = {
        "catalog_source",
        "catalog_source_sha256",
        "generators",
        "manifest_version",
        "schema_id",
        "source",
        "source_sha256",
        "workspace_artifacts",
    }
    if set(manifest) != expected_keys:
        raise ArtifactVerificationError("Workspace manifest top-level fields do not match v2")
    digests = _manifest_artifact_digests(
        manifest,
        "workspace_artifacts",
        WORKSPACE_MANIFEST_ARTIFACT_PATHS,
        label,
    )
    for relative_path, expected_digest in digests.items():
        artifact_path = (REPOSITORY_ROOT / Path(relative_path)).resolve()
        try:
            artifact_path.relative_to(REPOSITORY_ROOT.resolve())
        except ValueError as error:
            raise ArtifactVerificationError(
                f"Workspace manifest artifact escapes repository: {relative_path}"
            ) from error
        if not artifact_path.is_file():
            raise ArtifactVerificationError(
                f"Workspace manifest artifact is missing: {relative_path}"
            )
        if hashlib.sha256(artifact_path.read_bytes()).hexdigest() != expected_digest:
            raise ArtifactVerificationError(
                f"Workspace manifest artifact digest mismatch: {relative_path}"
            )


def _verify_python_distribution(
    output_root: Path,
    distribution: PythonDistribution,
) -> tuple[Path, Path, dict[str, bytes], dict[str, bytes]]:
    wheel_path = output_root / distribution.wheel_filename
    sdist_path = output_root / distribution.sdist_filename
    wheel_members = _read_wheel(wheel_path)
    sdist_members = _read_tar_archive(sdist_path)

    verify_member_allowlist(
        wheel_members,
        _wheel_expected_members(distribution),
        distribution.wheel_filename,
    )
    verify_member_allowlist(
        sdist_members,
        _sdist_expected_members(distribution),
        distribution.sdist_filename,
    )
    _verify_wheel_record(wheel_members, distribution)
    _verify_python_source_bytes(wheel_members, sdist_members, distribution)
    _verify_python_metadata(
        wheel_members[f"{distribution.dist_info}/METADATA"],
        distribution,
        distribution.wheel_filename,
    )
    _verify_python_metadata(
        sdist_members[f"{distribution.sdist_root}/PKG-INFO"],
        distribution,
        distribution.sdist_filename,
    )
    return wheel_path, sdist_path, wheel_members, sdist_members


def _verify_contract_payloads(
    python_wheel: Mapping[str, bytes],
    python_sdist: Mapping[str, bytes],
    typescript_archive: Mapping[str, bytes],
) -> None:
    canonical_schema = CANONICAL_SCHEMA_PATH.read_bytes()
    canonical_catalog = CANONICAL_CATALOG_PATH.read_bytes()
    python_manifest_source = PYTHON_MANIFEST_SOURCE_PATH.read_bytes()
    typescript_manifest_source = TYPESCRIPT_MANIFEST_SOURCE_PATH.read_bytes()
    active_event_registry_source = PYTHON_ACTIVE_EVENT_REGISTRY_SOURCE_PATH.read_bytes()
    if TYPESCRIPT_ACTIVE_EVENT_REGISTRY_SOURCE_PATH.read_bytes() != active_event_registry_source:
        raise ArtifactVerificationError("Python and TypeScript active-event registries differ")

    payloads = {
        "Python wheel active-event registry": python_wheel[
            "vnova_contracts/registry/active-event-registry.v1.json"
        ],
        "Python sdist active-event registry": python_sdist[
            f"vnova_contracts-{EXPECTED_CONTRACT_VERSION}/src/"
            "vnova_contracts/registry/active-event-registry.v1.json"
        ],
        "TypeScript archive active-event registry": typescript_archive[
            "package/dist/generated/active-event-registry.v1.json"
        ],
    }
    for label, registry_bytes in payloads.items():
        if registry_bytes != active_event_registry_source:
            raise ArtifactVerificationError(f"{label} is not a byte copy of the generated registry")

    schema_payloads = {
        "Python wheel schema": python_wheel[
            "vnova_contracts/schemas/event-envelope.v1.schema.json"
        ],
        "Python sdist schema": python_sdist[
            f"vnova_contracts-{EXPECTED_CONTRACT_VERSION}/src/"
            "vnova_contracts/schemas/event-envelope.v1.schema.json"
        ],
        "TypeScript archive schema": typescript_archive[
            "package/dist/generated/event-envelope.v1.schema.json"
        ],
    }
    for label, schema_bytes in schema_payloads.items():
        if schema_bytes != canonical_schema:
            raise ArtifactVerificationError(f"{label} is not a byte copy of the canonical schema")

    python_wheel_manifest_member = "vnova_contracts/contract-manifest.json"
    python_wheel_manifest = python_wheel[python_wheel_manifest_member]
    if python_wheel_manifest != python_manifest_source:
        raise ArtifactVerificationError("Python wheel manifest differs from its generated source")
    _verify_distribution_manifest(
        python_wheel_manifest,
        python_wheel,
        python_wheel_manifest_member,
        ecosystem="python",
        package_name="vnova-contracts",
        package_version=EXPECTED_CONTRACT_VERSION,
        expected_artifact_paths=PYTHON_MANIFEST_ARTIFACT_PATHS,
        canonical_schema_bytes=canonical_schema,
        canonical_catalog_bytes=canonical_catalog,
        generated_source_bytes=None,
        label="Python wheel manifest",
    )

    python_sdist_manifest_member = (
        f"vnova_contracts-{EXPECTED_CONTRACT_VERSION}/src/vnova_contracts/contract-manifest.json"
    )
    python_sdist_manifest = python_sdist[python_sdist_manifest_member]
    if python_sdist_manifest != python_manifest_source:
        raise ArtifactVerificationError("Python sdist manifest differs from its generated source")
    _verify_distribution_manifest(
        python_sdist_manifest,
        python_sdist,
        python_sdist_manifest_member,
        ecosystem="python",
        package_name="vnova-contracts",
        package_version=EXPECTED_CONTRACT_VERSION,
        expected_artifact_paths=PYTHON_MANIFEST_ARTIFACT_PATHS,
        canonical_schema_bytes=canonical_schema,
        canonical_catalog_bytes=canonical_catalog,
        generated_source_bytes=None,
        label="Python sdist manifest",
    )

    typescript_manifest_member = "package/contract-manifest.json"
    typescript_manifest = typescript_archive[typescript_manifest_member]
    if typescript_manifest != typescript_manifest_source:
        raise ArtifactVerificationError(
            "TypeScript archive manifest differs from its generated source"
        )
    _verify_distribution_manifest(
        typescript_manifest,
        typescript_archive,
        typescript_manifest_member,
        ecosystem="npm",
        package_name="@vnova/contracts",
        package_version=EXPECTED_CONTRACT_VERSION,
        expected_artifact_paths=TYPESCRIPT_MANIFEST_ARTIFACT_PATHS,
        canonical_schema_bytes=canonical_schema,
        canonical_catalog_bytes=canonical_catalog,
        generated_source_bytes=TYPESCRIPT_GENERATED_SOURCE_PATH.read_bytes(),
        label="TypeScript archive manifest",
    )
    _verify_workspace_manifest(canonical_schema, canonical_catalog)


def _resolve_executable(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise ArtifactVerificationError(f"Required executable not found: {name}")
    return executable


def _run(
    command: list[str],
    *,
    cwd: Path,
    timeout: int = COMMAND_TIMEOUT_SECONDS,
    environment: Mapping[str, str] | None = None,
) -> str:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            env=dict(environment) if environment is not None else None,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        details = getattr(error, "stderr", None) or getattr(error, "stdout", None) or str(error)
        raise ArtifactVerificationError(
            f"External command failed: {' '.join(command)}\n{details}"
        ) from error
    return completed.stdout.strip()


def _require_exact_output_files(output_root: Path, expected_names: set[str], label: str) -> None:
    actual_names = {path.name for path in output_root.iterdir() if path.is_file()}
    verify_member_allowlist(actual_names, expected_names, label)


def _build_archives(work_root: Path) -> tuple[Path, Path]:
    python_output = work_root / "python"
    npm_output = work_root / "npm"
    python_output.mkdir()
    npm_output.mkdir()

    _run(
        [
            _resolve_executable("uv"),
            "build",
            "--all-packages",
            "--no-build-isolation",
            "--clear",
            "--python",
            "3.13",
            "--out-dir",
            str(python_output),
        ],
        cwd=REPOSITORY_ROOT,
    )
    _require_exact_output_files(
        python_output,
        {".gitignore"}
        | {
            archive_name
            for distribution in PYTHON_DISTRIBUTIONS
            for archive_name in (distribution.wheel_filename, distribution.sdist_filename)
        },
        "Python build output",
    )
    if (python_output / ".gitignore").read_bytes() != b"*":
        raise ArtifactVerificationError("uv build output .gitignore has unexpected contents")

    stale_probe = TYPESCRIPT_CONTRACTS_ROOT / "dist" / ".vnova-stale-artifact-probe"
    stale_probe.parent.mkdir(parents=True, exist_ok=True)
    if stale_probe.exists():
        raise ArtifactVerificationError(f"Refusing to overwrite stale probe path: {stale_probe}")
    stale_probe.write_text("prepack must remove this file\n", encoding="utf-8")
    try:
        _run(
            [
                _resolve_executable("corepack"),
                "pnpm",
                "--dir",
                str(TYPESCRIPT_CONTRACTS_ROOT),
                "pack",
                "--pack-destination",
                str(npm_output),
            ],
            cwd=REPOSITORY_ROOT,
        )
    except ArtifactVerificationError:
        stale_probe.unlink(missing_ok=True)
        raise
    if stale_probe.exists():
        stale_probe.unlink()
        raise ArtifactVerificationError("TypeScript prepack did not clean the stale dist probe")
    npm_archive = npm_output / f"vnova-contracts-{EXPECTED_CONTRACT_VERSION}.tgz"
    _require_exact_output_files(npm_output, {npm_archive.name}, "pnpm pack output")
    return python_output, npm_archive


def _clean_smoke_environment() -> dict[str, str]:
    environment = dict(os.environ)
    for name in ("NODE_PATH", "PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        environment.pop(name, None)
    environment["CI"] = "true"
    environment["COREPACK_ENABLE_DOWNLOAD_PROMPT"] = "0"
    return environment


def _venv_python(venv_root: Path) -> Path:
    if os.name == "nt":
        return venv_root / "Scripts" / "python.exe"
    return venv_root / "bin" / "python"


def _smoke_python_wheels(
    smoke_root: Path,
    wheel_paths: Mapping[str, Path],
    expected_source_digest: str,
) -> None:
    venv_root = smoke_root / "python-venv"
    environment = _clean_smoke_environment()
    uv = _resolve_executable("uv")
    _run(
        [uv, "venv", "--no-project", "--python", "3.13", str(venv_root)],
        cwd=smoke_root,
        environment=environment,
    )
    python = _venv_python(venv_root)
    _run(
        [
            uv,
            "pip",
            "install",
            "--offline",
            "--python",
            str(python),
            str(wheel_paths["vnova-contracts"]),
            str(wheel_paths["vnova-safety"]),
        ],
        cwd=smoke_root,
        environment=environment,
    )
    smoke_program = (
        "import importlib.metadata as m, json\n"
        "from importlib.resources import files\n"
        "import vnova_contracts, vnova_safety\n"
        f"assert m.version('vnova-contracts') == {EXPECTED_CONTRACT_VERSION!r}\n"
        f"assert m.version('vnova-safety') == {EXPECTED_CONTRACT_VERSION!r}\n"
        "manifest = json.loads(files('vnova_contracts').joinpath("
        "'contract-manifest.json').read_text(encoding='utf-8'))\n"
        f"assert manifest['source_sha256'] == {expected_source_digest!r}\n"
        "assert files('vnova_contracts.schemas').joinpath("
        "'event-envelope.v1.schema.json').is_file()\n"
        "assert files('vnova_contracts.registry').joinpath("
        "'active-event-registry.v1.json').is_file()\n"
        "assert callable(vnova_contracts.assert_valid_publishable_event)\n"
        "assert callable(vnova_contracts.is_valid_publishable_event)\n"
    )
    _run(
        [str(python), "-I", "-c", smoke_program],
        cwd=smoke_root,
        environment=environment,
    )


def _smoke_typescript_archive(
    smoke_root: Path,
    npm_archive: Path,
    expected_source_digest: str,
) -> None:
    node_root = smoke_root / "node"
    node_root.mkdir()
    root_package = _load_json_bytes(
        (REPOSITORY_ROOT / "package.json").read_bytes(),
        "root package.json",
    )
    package_manager = root_package.get("packageManager")
    if not isinstance(package_manager, str):
        raise ArtifactVerificationError("Root package.json requires packageManager")
    archive_reference = f"file:{npm_archive.resolve().as_posix()}"
    smoke_package = {
        "name": "vnova-artifact-smoke",
        "version": "0.0.0",
        "private": True,
        "type": "module",
        "packageManager": package_manager,
        "dependencies": {"@vnova/contracts": archive_reference},
    }
    (node_root / "package.json").write_text(
        json.dumps(smoke_package, indent=2) + "\n",
        encoding="utf-8",
    )
    environment = _clean_smoke_environment()
    corepack = _resolve_executable("corepack")
    _run(
        [
            corepack,
            "pnpm",
            "install",
            "--offline",
            "--ignore-scripts",
            "--no-frozen-lockfile",
        ],
        cwd=node_root,
        environment=environment,
    )
    smoke_program = (
        "const contracts = await import('@vnova/contracts');"
        "if (typeof contracts.assertValidEventEnvelope !== 'function') "
        "throw new Error('missing API');"
        "if (typeof contracts.assertValidPublishableEvent !== 'function') "
        "throw new Error('missing publishable-event API');"
        "if (typeof contracts.isValidPublishableEvent !== 'function') "
        "throw new Error('missing publishable-event predicate');"
        "const value = await import('@vnova/contracts/contract-manifest.json',"
        " { with: { type: 'json' } });"
        f"if (value.default.source_sha256 !== {json.dumps(expected_source_digest)}) "
        "throw new Error('manifest digest mismatch');"
    )
    _run(
        [_resolve_executable("node"), "--input-type=module", "--eval", smoke_program],
        cwd=node_root,
        environment=environment,
    )


def _archive_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as artifact:
        while chunk := artifact.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _built_archive_paths(python_output: Path, npm_archive: Path) -> dict[str, Path]:
    paths = {
        archive_path.name: archive_path
        for distribution in PYTHON_DISTRIBUTIONS
        for archive_path in (
            python_output / distribution.wheel_filename,
            python_output / distribution.sdist_filename,
        )
    }
    if npm_archive.name in paths:
        raise ArtifactVerificationError(f"Duplicate built archive filename: {npm_archive.name}")
    paths[npm_archive.name] = npm_archive
    return paths


def _verify_reproducible_archives(
    first_archives: Mapping[str, Path],
    second_archives: Mapping[str, Path],
) -> None:
    verify_member_allowlist(
        first_archives,
        second_archives,
        "Repeated clean-build archive names",
    )
    for filename, first_path in first_archives.items():
        first_digest = _archive_sha256(first_path)
        second_digest = _archive_sha256(second_archives[filename])
        if first_digest != second_digest:
            raise ArtifactVerificationError(
                f"Clean package builds are not reproducible: {filename} "
                f"({first_digest} != {second_digest})"
            )


def verify_built_artifacts() -> list[tuple[str, str]]:
    """Build twice, inspect, and smoke-test every current package archive."""

    verify_declared_versions()
    canonical_schema = CANONICAL_SCHEMA_PATH.read_bytes()
    expected_source_digest = hashlib.sha256(_normalized_schema_bytes(canonical_schema)).hexdigest()

    with tempfile.TemporaryDirectory(prefix="vnova-package-artifacts-") as directory:
        work_root = Path(directory)
        first_build_root = work_root / "build-a"
        second_build_root = work_root / "build-b"
        first_build_root.mkdir()
        second_build_root.mkdir()
        python_output, npm_archive = _build_archives(first_build_root)
        second_python_output, second_npm_archive = _build_archives(second_build_root)
        _verify_reproducible_archives(
            _built_archive_paths(python_output, npm_archive),
            _built_archive_paths(second_python_output, second_npm_archive),
        )
        verified_paths: list[Path] = []
        python_wheels: dict[str, Path] = {}
        contracts_wheel_members: dict[str, bytes] | None = None
        contracts_sdist_members: dict[str, bytes] | None = None

        for distribution in PYTHON_DISTRIBUTIONS:
            wheel, sdist, wheel_members, sdist_members = _verify_python_distribution(
                python_output,
                distribution,
            )
            verified_paths.extend((wheel, sdist))
            python_wheels[distribution.project_name] = wheel
            if distribution.project_name == "vnova-contracts":
                contracts_wheel_members = wheel_members
                contracts_sdist_members = sdist_members

        if contracts_wheel_members is None or contracts_sdist_members is None:
            raise ArtifactVerificationError("Python contracts archive was not verified")

        npm_members = _read_tar_archive(npm_archive)
        verify_member_allowlist(
            npm_members,
            TYPESCRIPT_ARCHIVE_MEMBERS,
            npm_archive.name,
        )
        npm_package = _load_json_bytes(npm_members["package/package.json"], npm_archive.name)
        if npm_package.get("name") != "@vnova/contracts":
            raise ArtifactVerificationError("npm archive package name mismatch")
        if npm_package.get("version") != EXPECTED_CONTRACT_VERSION:
            raise ArtifactVerificationError("npm archive package version mismatch")
        npm_engines = npm_package.get("engines")
        archived_node_engine = npm_engines.get("node") if isinstance(npm_engines, Mapping) else None
        if archived_node_engine != EXPECTED_NODE_ENGINE:
            raise ArtifactVerificationError("npm archive Node.js engine requirement mismatch")
        _verify_contract_payloads(
            contracts_wheel_members,
            contracts_sdist_members,
            npm_members,
        )
        verified_paths.append(npm_archive)

        smoke_root = work_root / "smoke"
        smoke_root.mkdir()
        _smoke_python_wheels(smoke_root, python_wheels, expected_source_digest)
        _smoke_typescript_archive(smoke_root, npm_archive, expected_source_digest)

        return [(path.name, _archive_sha256(path)) for path in verified_paths]


def _fail(error: Exception) -> NoReturn:
    print(f"Package artifact verification failed: {error}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    try:
        digests = verify_built_artifacts()
    except (ArtifactVerificationError, OSError) as error:
        _fail(error)
    print("Package artifact verification passed:")
    for filename, digest in digests:
        print(f"- {filename}: sha256:{digest}")


if __name__ == "__main__":
    main()
