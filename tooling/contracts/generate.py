"""Generate deterministic Python and TypeScript contracts from canonical schemas."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn
from urllib.parse import unquote, urldefrag

from tooling.contracts.verify import (
    CANONICAL_TIMESTAMP_PATTERN,
    CANONICAL_UUID_PATTERN,
    CATALOG_PATH,
    ENVELOPE_SCHEMA_PATH,
    EVENT_SPEC_ROOT,
    REPOSITORY_ROOT,
    load_json,
    verify_all,
)

COMMAND_TIMEOUT_SECONDS = 120
MANIFEST_VERSION = 2
PYTHON_PACKAGE_NAME = "vnova-contracts"
TYPESCRIPT_PACKAGE_NAME = "@vnova/contracts"

PYTHON_PACKAGE_ROOT = REPOSITORY_ROOT / "packages" / "contracts" / "python"
TYPESCRIPT_PACKAGE_ROOT = REPOSITORY_ROOT / "packages" / "contracts" / "typescript"
PYTHON_GENERATED_PATH = (
    PYTHON_PACKAGE_ROOT / "src" / "vnova_contracts" / "generated" / "event_envelope_v1.py"
)
PYTHON_SCHEMA_PATH = (
    PYTHON_PACKAGE_ROOT / "src" / "vnova_contracts" / "schemas" / "event-envelope.v1.schema.json"
)
TYPESCRIPT_GENERATED_PATH = TYPESCRIPT_PACKAGE_ROOT / "src" / "generated" / "event-envelope.v1.ts"
TYPESCRIPT_SCHEMA_PATH = TYPESCRIPT_GENERATED_PATH.with_suffix(".schema.json")
PYTHON_ACTIVE_EVENT_REGISTRY_PATH = (
    PYTHON_PACKAGE_ROOT / "src" / "vnova_contracts" / "registry" / "active-event-registry.v1.json"
)
TYPESCRIPT_ACTIVE_EVENT_REGISTRY_PATH = (
    TYPESCRIPT_PACKAGE_ROOT / "src" / "generated" / "active-event-registry.v1.json"
)
MANIFEST_PATH = REPOSITORY_ROOT / "packages" / "contracts" / "manifest.json"
PYTHON_DISTRIBUTION_MANIFEST_PATH = (
    REPOSITORY_ROOT
    / "packages"
    / "contracts"
    / "python"
    / "src"
    / "vnova_contracts"
    / "contract-manifest.json"
)
TYPESCRIPT_DISTRIBUTION_MANIFEST_PATH = TYPESCRIPT_PACKAGE_ROOT / "contract-manifest.json"
MANAGED_GENERATED_ROOTS: dict[Path, frozenset[Path]] = {
    PYTHON_GENERATED_PATH.parent: frozenset(
        {PYTHON_GENERATED_PATH, PYTHON_GENERATED_PATH.parent / "__init__.py"}
    ),
    PYTHON_SCHEMA_PATH.parent: frozenset(
        {PYTHON_SCHEMA_PATH, PYTHON_SCHEMA_PATH.parent / "__init__.py"}
    ),
    PYTHON_ACTIVE_EVENT_REGISTRY_PATH.parent: frozenset(
        {
            PYTHON_ACTIVE_EVENT_REGISTRY_PATH,
            PYTHON_ACTIVE_EVENT_REGISTRY_PATH.parent / "__init__.py",
        }
    ),
    TYPESCRIPT_GENERATED_PATH.parent: frozenset(
        {
            TYPESCRIPT_ACTIVE_EVENT_REGISTRY_PATH,
            TYPESCRIPT_GENERATED_PATH,
            TYPESCRIPT_SCHEMA_PATH,
        }
    ),
}
MANAGED_GENERATED_SUFFIXES = frozenset({".json", ".py", ".pyi", ".ts"})


class ContractGenerationError(RuntimeError):
    """Raised when deterministic contract generation fails."""


@dataclass(frozen=True)
class GeneratedArtifacts:
    python_model: bytes
    python_schema: bytes
    active_event_registry: bytes
    typescript_model: bytes
    typescript_schema: bytes
    workspace_manifest: bytes
    python_manifest: bytes
    typescript_manifest: bytes

    def as_paths(self) -> dict[Path, bytes]:
        return {
            PYTHON_GENERATED_PATH: self.python_model,
            PYTHON_SCHEMA_PATH: self.python_schema,
            PYTHON_ACTIVE_EVENT_REGISTRY_PATH: self.active_event_registry,
            TYPESCRIPT_GENERATED_PATH: self.typescript_model,
            TYPESCRIPT_SCHEMA_PATH: self.typescript_schema,
            TYPESCRIPT_ACTIVE_EVENT_REGISTRY_PATH: self.active_event_registry,
            MANIFEST_PATH: self.workspace_manifest,
            PYTHON_DISTRIBUTION_MANIFEST_PATH: self.python_manifest,
            TYPESCRIPT_DISTRIBUTION_MANIFEST_PATH: self.typescript_manifest,
        }


def _tool_path(name: str) -> str:
    executable_name = f"{name}.exe" if sys.platform == "win32" else name
    environment_candidate = Path(sys.executable).parent / executable_name
    if environment_candidate.is_file():
        return str(environment_candidate)
    workspace_executable = f"{name}.cmd" if sys.platform == "win32" else name
    workspace_candidate = REPOSITORY_ROOT / "node_modules" / ".bin" / workspace_executable
    if workspace_candidate.is_file():
        return str(workspace_candidate)
    tool = shutil.which(name)
    if tool is None:
        raise ContractGenerationError(f"Required executable not found: {name}")
    return tool


def _run(command: list[str]) -> str:
    try:
        completed = subprocess.run(
            command,
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        details = getattr(error, "stderr", None) or getattr(error, "stdout", None) or str(error)
        raise ContractGenerationError(
            f"External command failed: {' '.join(command)}\n{details}"
        ) from error
    return completed.stdout.strip()


def _normalize_text(path: Path) -> bytes:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    normalized = "\n".join(line.rstrip() for line in text.splitlines()).rstrip() + "\n"
    return normalized.encode("utf-8")


def _harden_python_model(contents: bytes) -> bytes:
    """Project generated payload typing onto VNova's immutable JSON public API."""

    text = contents.decode("utf-8")
    replacements = (
        ("from typing import Annotated, Any\n", "from typing import Annotated\n"),
        ("from collections.abc import Mapping\n", ""),
        (
            "from vnova_contracts._base import VNovaContractModel\n",
            "from vnova_contracts._base import FrozenJsonObject, VNovaContractModel\n",
        ),
        ("    payload: Mapping[str, Any]\n", "    payload: FrozenJsonObject\n"),
    )
    for original, replacement in replacements:
        if text.count(original) != 1:
            raise ContractGenerationError(
                f"Generated Python contract projection changed unexpectedly: {original.strip()}"
            )
        text = text.replace(original, replacement)
    return text.encode("utf-8")


def _sha256(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


def _manifest_bytes(value: dict[str, object]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _active_catalog_event(
    event: object,
    index: int,
) -> tuple[dict[str, object], Path] | None:
    if not isinstance(event, dict):
        raise ContractGenerationError(f"Catalog event {index} must be an object")
    if event.get("status") != "active":
        return None
    event_type = event.get("type")
    schema_version = event.get("schema_version")
    schema_reference = event.get("schema")
    if (
        not isinstance(event_type, str)
        or not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or not isinstance(schema_reference, str)
    ):
        raise ContractGenerationError(f"Invalid active catalog event at index {index}")
    schema_path = (EVENT_SPEC_ROOT / schema_reference).resolve()
    try:
        normalized_schema_reference = schema_path.relative_to(EVENT_SPEC_ROOT.resolve()).as_posix()
    except ValueError as error:
        raise ContractGenerationError(
            f"Active catalog schema escapes specs/events: {(event_type, schema_version)}"
        ) from error
    return (
        {
            "schema": normalized_schema_reference,
            "schema_version": schema_version,
            "type": event_type,
        },
        schema_path,
    )


def _active_event_sort_key(event: dict[str, object]) -> tuple[str, int]:
    event_type = event.get("type")
    schema_version = event.get("schema_version")
    if not isinstance(event_type, str) or not isinstance(schema_version, int):
        raise ContractGenerationError("Projected active-event identity is malformed")
    return event_type, schema_version


def _active_catalog_projection(
    catalog: object,
) -> tuple[int, list[dict[str, object]], set[Path]]:
    if not isinstance(catalog, dict):
        raise ContractGenerationError("Event catalog root must be an object")
    catalog_version = catalog.get("catalog_version")
    events = catalog.get("events")
    if catalog_version != 1 or not isinstance(events, list):
        raise ContractGenerationError("Unsupported event catalog structure")
    projected = [
        active_event
        for index, event in enumerate(events)
        if (active_event := _active_catalog_event(event, index)) is not None
    ]
    active_events = [event for event, _ in projected]
    active_events.sort(key=_active_event_sort_key)
    return catalog_version, active_events, {schema_path for _, schema_path in projected}


def _referenced_schema_paths(schema_path: Path) -> set[Path]:
    references: set[Path] = set()
    pending_values: list[object] = [load_json(schema_path)]
    while pending_values:
        value = pending_values.pop()
        if isinstance(value, list):
            pending_values.extend(value)
            continue
        if not isinstance(value, dict):
            continue
        pending_values.extend(value.values())
        reference = value.get("$ref")
        if not isinstance(reference, str):
            continue
        reference_path, _ = urldefrag(reference)
        if not reference_path:
            continue
        target_path = (schema_path.parent / unquote(reference_path)).resolve()
        try:
            target_path.relative_to(EVENT_SPEC_ROOT.resolve())
        except ValueError as error:
            raise ContractGenerationError(
                f"Active payload schema reference escapes specs/events: {reference}"
            ) from error
        references.add(target_path)
    return references


def _active_schema_closure(active_schema_paths: set[Path]) -> set[Path]:
    schema_paths: set[Path] = set()
    pending_schema_paths = sorted(active_schema_paths, reverse=True)
    while pending_schema_paths:
        schema_path = pending_schema_paths.pop()
        if schema_path in schema_paths:
            continue
        schema_paths.add(schema_path)
        for target_path in _referenced_schema_paths(schema_path):
            if target_path not in schema_paths:
                pending_schema_paths.append(target_path)
        pending_schema_paths.sort(reverse=True)
    return schema_paths


def _payload_schema_records(schema_paths: set[Path]) -> list[dict[str, object]]:
    return [
        {
            "document": load_json(schema_path),
            "path": schema_path.relative_to(EVENT_SPEC_ROOT.resolve()).as_posix(),
            "source_sha256": _sha256(_normalize_text(schema_path)),
        }
        for schema_path in sorted(schema_paths)
    ]


def _active_event_registry_bytes() -> bytes:
    """Project the governed catalog onto the runtime-authoritative active identity set."""

    catalog_version, active_events, active_schema_paths = _active_catalog_projection(
        load_json(CATALOG_PATH)
    )
    payload_schemas = _payload_schema_records(_active_schema_closure(active_schema_paths))
    catalog_source = _normalize_text(CATALOG_PATH)
    return _manifest_bytes(
        {
            "active_events": active_events,
            "catalog_source": str(CATALOG_PATH.relative_to(REPOSITORY_ROOT)).replace("\\", "/"),
            "catalog_source_sha256": _sha256(catalog_source),
            "catalog_version": catalog_version,
            "payload_schemas": payload_schemas,
            "registry_version": 1,
        }
    )


def _python_package_version() -> str:
    try:
        document = tomllib.loads(
            (PYTHON_PACKAGE_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        raise ContractGenerationError(f"Cannot read Python package metadata: {error}") from error
    project = document.get("project")
    name = project.get("name") if isinstance(project, dict) else None
    version = project.get("version") if isinstance(project, dict) else None
    if name != PYTHON_PACKAGE_NAME or not isinstance(version, str) or not version:
        raise ContractGenerationError("Unexpected Python contracts package identity")
    return version


def _typescript_package_metadata() -> tuple[str, str]:
    try:
        package = json.loads((TYPESCRIPT_PACKAGE_ROOT / "package.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ContractGenerationError(
            f"Cannot read TypeScript package metadata: {error}"
        ) from error
    if not isinstance(package, dict):
        raise ContractGenerationError("TypeScript package metadata must be an object")
    name = package.get("name")
    version = package.get("version")
    if name != TYPESCRIPT_PACKAGE_NAME or not isinstance(version, str) or not version:
        raise ContractGenerationError("Unexpected TypeScript contracts package identity")
    return name, version


def _write_python_generation_schema(temp_root: Path) -> Path:
    projection_root = temp_root / "python-projection"
    shutil.copytree(EVENT_SPEC_ROOT, projection_root)
    output = projection_root / ENVELOPE_SCHEMA_PATH.relative_to(EVENT_SPEC_ROOT)
    schema = load_json(output)
    if not isinstance(schema, dict):
        raise ContractGenerationError("Event envelope schema root must be an object")
    properties = schema.get("properties")
    occurred_at = properties.get("occurred_at") if isinstance(properties, dict) else None
    if (
        not isinstance(occurred_at, dict)
        or occurred_at.get("pattern") != CANONICAL_TIMESTAMP_PATTERN
    ):
        raise ContractGenerationError(
            "Python UTC projection expects the canonical occurred_at pattern"
        )
    occurred_at.pop("pattern")
    for field_name in ("event_id", "stream_session_id", "turn_id"):
        uuid_field = properties.get(field_name) if isinstance(properties, dict) else None
        if uuid_field is None:
            continue
        if not isinstance(uuid_field, dict) or uuid_field.get("pattern") != CANONICAL_UUID_PATTERN:
            raise ContractGenerationError(
                f"Python UUID projection expects the canonical {field_name} pattern"
            )
        uuid_field.pop("pattern")
    payload = properties.get("payload") if isinstance(properties, dict) else None
    expected_json_value_ref = {"$ref": "#/$defs/JsonValue"}
    if (
        not isinstance(payload, dict)
        or payload.get("additionalProperties") != expected_json_value_ref
        or "JsonValue" not in schema.get("$defs", {})
    ):
        raise ContractGenerationError("Python payload projection expects recursive JsonValue")
    payload["additionalProperties"] = True
    definitions = schema["$defs"]
    del definitions["JsonValue"]
    if not definitions:
        del schema["$defs"]
    output.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    return output


def _generate_once(temp_root: Path) -> GeneratedArtifacts:
    python_output = temp_root / "event_envelope_v1.py"
    typescript_output = temp_root / "event-envelope.v1.ts"
    python_input = _write_python_generation_schema(temp_root)

    datamodel_executable = _tool_path("datamodel-codegen")
    typescript_executable = _tool_path("json2ts")

    _run(
        [
            datamodel_executable,
            "--input",
            str(python_input),
            "--input-file-type",
            "jsonschema",
            "--output",
            str(python_output),
            "--output-model-type",
            "pydantic_v2.BaseModel",
            "--class-name",
            "VNovaEventEnvelopeV1",
            "--base-class",
            "vnova_contracts._base.VNovaContractModel",
            "--target-python-version",
            "3.13",
            "--schema-version",
            "2020-12",
            "--schema-version-mode",
            "strict",
            "--use-standard-collections",
            "--use-generic-container-types",
            "--use-union-operator",
            "--use-schema-description",
            "--use-field-description",
            "--use-annotated",
            "--disable-timestamp",
            "--enable-faux-immutability",
            "--no-allow-remote-refs",
            "--formatters",
            "ruff-check",
            "ruff-format",
        ]
    )

    _run(
        [
            typescript_executable,
            "--input",
            str(ENVELOPE_SCHEMA_PATH),
            "--output",
            str(typescript_output),
            "--bannerComment",
            "/* Generated from specs/events/event-envelope.v1.schema.json. Do not edit. */",
            "--unreachableDefinitions",
        ]
    )

    python_model = _harden_python_model(_normalize_text(python_output))
    typescript_model = _normalize_text(typescript_output)
    source_schema = _normalize_text(ENVELOPE_SCHEMA_PATH)
    active_event_registry = _active_event_registry_bytes()
    schema_digest = _sha256(source_schema)
    catalog_digest = _sha256(_normalize_text(CATALOG_PATH))
    schema_document = load_json(ENVELOPE_SCHEMA_PATH)
    schema_id = schema_document.get("$id") if isinstance(schema_document, dict) else None
    if not isinstance(schema_id, str) or not schema_id:
        raise ContractGenerationError("Canonical event envelope schema requires a non-empty $id")
    datamodel_version = _run([datamodel_executable, "--version"])
    root_package = json.loads((REPOSITORY_ROOT / "package.json").read_text(encoding="utf-8"))
    typescript_generator_version = root_package["devDependencies"]["json-schema-to-typescript"]
    generators = {
        "python": datamodel_version,
        "typescript": f"json-schema-to-typescript {typescript_generator_version}",
    }
    common_manifest: dict[str, object] = {
        "catalog_source": str(CATALOG_PATH.relative_to(REPOSITORY_ROOT)).replace("\\", "/"),
        "catalog_source_sha256": catalog_digest,
        "manifest_version": MANIFEST_VERSION,
        "source": "specs/events/event-envelope.v1.schema.json",
        "source_sha256": schema_digest,
        "schema_id": schema_id,
        "generators": generators,
    }
    workspace_manifest = {
        **common_manifest,
        "workspace_artifacts": [
            {
                "path": str(PYTHON_GENERATED_PATH.relative_to(REPOSITORY_ROOT)).replace("\\", "/"),
                "sha256": _sha256(python_model),
            },
            {
                "path": str(PYTHON_SCHEMA_PATH.relative_to(REPOSITORY_ROOT)).replace("\\", "/"),
                "sha256": _sha256(source_schema),
            },
            {
                "path": str(PYTHON_ACTIVE_EVENT_REGISTRY_PATH.relative_to(REPOSITORY_ROOT)).replace(
                    "\\", "/"
                ),
                "sha256": _sha256(active_event_registry),
            },
            {
                "path": str(TYPESCRIPT_GENERATED_PATH.relative_to(REPOSITORY_ROOT)).replace(
                    "\\", "/"
                ),
                "sha256": _sha256(typescript_model),
            },
            {
                "path": str(TYPESCRIPT_SCHEMA_PATH.relative_to(REPOSITORY_ROOT)).replace("\\", "/"),
                "sha256": _sha256(source_schema),
            },
            {
                "path": str(
                    TYPESCRIPT_ACTIVE_EVENT_REGISTRY_PATH.relative_to(REPOSITORY_ROOT)
                ).replace("\\", "/"),
                "sha256": _sha256(active_event_registry),
            },
        ],
    }
    python_manifest = {
        **common_manifest,
        "package": {
            "ecosystem": "python",
            "name": PYTHON_PACKAGE_NAME,
            "version": _python_package_version(),
        },
        "artifacts": [
            {
                "path": "generated/event_envelope_v1.py",
                "sha256": _sha256(python_model),
            },
            {
                "path": "schemas/event-envelope.v1.schema.json",
                "sha256": _sha256(source_schema),
            },
            {
                "path": "registry/active-event-registry.v1.json",
                "sha256": _sha256(active_event_registry),
            },
        ],
    }
    typescript_name, typescript_version = _typescript_package_metadata()
    typescript_manifest = {
        **common_manifest,
        "package": {
            "ecosystem": "npm",
            "name": typescript_name,
            "version": typescript_version,
        },
        "artifacts": [
            {
                "path": "dist/generated/event-envelope.v1.schema.json",
                "sha256": _sha256(source_schema),
            },
            {
                "path": "dist/generated/active-event-registry.v1.json",
                "sha256": _sha256(active_event_registry),
            },
        ],
        "generated_source_sha256": _sha256(typescript_model),
    }
    return GeneratedArtifacts(
        python_model=python_model,
        python_schema=source_schema,
        active_event_registry=active_event_registry,
        typescript_model=typescript_model,
        typescript_schema=source_schema,
        workspace_manifest=_manifest_bytes(workspace_manifest),
        python_manifest=_manifest_bytes(python_manifest),
        typescript_manifest=_manifest_bytes(typescript_manifest),
    )


def _generate_twice() -> GeneratedArtifacts:
    with tempfile.TemporaryDirectory(prefix="vnova-contracts-a-") as first_directory:
        first = _generate_once(Path(first_directory))
    with tempfile.TemporaryDirectory(prefix="vnova-contracts-b-") as second_directory:
        second = _generate_once(Path(second_directory))
    if first != second:
        raise ContractGenerationError("Generation is not byte-for-byte deterministic")
    return first


def _unexpected_generated_paths() -> list[Path]:
    unexpected: list[Path] = []
    for root, allowed_paths in MANAGED_GENERATED_ROOTS.items():
        if not root.exists():
            continue
        unexpected.extend(
            path
            for path in root.rglob("*")
            if path.is_file()
            and path.suffix in MANAGED_GENERATED_SUFFIXES
            and path not in allowed_paths
        )
    return sorted(unexpected)


def _write(artifacts: GeneratedArtifacts) -> None:
    for path in _unexpected_generated_paths():
        path.unlink()
    for path, content in artifacts.as_paths().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def _check(artifacts: GeneratedArtifacts) -> None:
    mismatches: list[str] = []
    for path, expected in artifacts.as_paths().items():
        if not path.is_file():
            mismatches.append(f"missing: {path.relative_to(REPOSITORY_ROOT)}")
        elif path.read_bytes() != expected:
            mismatches.append(f"stale: {path.relative_to(REPOSITORY_ROOT)}")
    mismatches.extend(
        f"unexpected: {path.relative_to(REPOSITORY_ROOT)}" for path in _unexpected_generated_paths()
    )
    if mismatches:
        formatted = "\n".join(f"- {mismatch}" for mismatch in mismatches)
        raise ContractGenerationError(f"Generated contract drift detected:\n{formatted}")


def _fail(error: Exception) -> NoReturn:
    print(f"Contract generation failed: {error}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if generated artifacts differ")
    arguments = parser.parse_args()
    try:
        verify_all()
        artifacts = _generate_twice()
        if arguments.check:
            _check(artifacts)
            print("Generated contracts are deterministic and current")
        else:
            _write(artifacts)
            print("Generated deterministic Python and TypeScript contracts")
    except (ContractGenerationError, OSError) as error:
        _fail(error)


if __name__ == "__main__":
    main()
