import hashlib
import json
from pathlib import Path

import pytest
from pytest import MonkeyPatch

from tooling.contracts import generate
from tooling.contracts import verify as contract_verify
from tooling.contracts.verify import ContractVerificationError, verify_all


def test_canonical_contracts_and_fixtures_verify() -> None:
    verify_all()


def test_active_event_registry_is_a_deterministic_catalog_projection(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    event_root = tmp_path / "specs" / "events"
    payload_root = event_root / "payloads"
    payload_root.mkdir(parents=True)
    catalog_path = event_root / "event-catalog.v1.json"
    catalog_path.write_text(
        json.dumps(
            {
                "catalog_version": 1,
                "description": "test",
                "events": [
                    {
                        "type": "ZuluEvent",
                        "schema_version": 2,
                        "status": "active",
                        "schema": "payloads/zulu.schema.json",
                    },
                    {
                        "type": "RequiredEvent",
                        "schema_version": 1,
                        "status": "required",
                    },
                    {
                        "type": "AlphaEvent",
                        "schema_version": 1,
                        "status": "active",
                        "schema": "payloads/alpha.schema.json",
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (payload_root / "alpha.schema.json").write_text(
        json.dumps(
            {
                "$schema": contract_verify.DRAFT_2020_12_URI,
                "$id": "https://schemas.vnova.test/alpha.schema.json",
                "type": "object",
                "properties": {"shared": {"$ref": "./shared.schema.json"}},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (payload_root / "shared.schema.json").write_text(
        json.dumps(
            {
                "$schema": contract_verify.DRAFT_2020_12_URI,
                "$id": "https://schemas.vnova.test/shared.schema.json",
                "type": "string",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (payload_root / "zulu.schema.json").write_text(
        json.dumps(
            {
                "$schema": contract_verify.DRAFT_2020_12_URI,
                "$id": "https://schemas.vnova.test/zulu.schema.json",
                "type": "object",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(generate, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(generate, "EVENT_SPEC_ROOT", event_root)
    monkeypatch.setattr(generate, "CATALOG_PATH", catalog_path)

    first = generate._active_event_registry_bytes()
    second = generate._active_event_registry_bytes()
    registry = json.loads(first)

    assert first == second
    assert registry["active_events"] == [
        {
            "schema": "payloads/alpha.schema.json",
            "schema_version": 1,
            "type": "AlphaEvent",
        },
        {
            "schema": "payloads/zulu.schema.json",
            "schema_version": 2,
            "type": "ZuluEvent",
        },
    ]
    assert [schema["path"] for schema in registry["payload_schemas"]] == [
        "payloads/alpha.schema.json",
        "payloads/shared.schema.json",
        "payloads/zulu.schema.json",
    ]
    assert registry["catalog_source"] == "specs/events/event-catalog.v1.json"


def test_generated_active_event_registry_is_empty_and_identical_across_distributions() -> None:
    python_registry = generate.PYTHON_ACTIVE_EVENT_REGISTRY_PATH.read_bytes()
    typescript_registry = generate.TYPESCRIPT_ACTIVE_EVENT_REGISTRY_PATH.read_bytes()
    registry = json.loads(python_registry)

    assert python_registry == typescript_registry
    assert registry["active_events"] == []
    assert registry["payload_schemas"] == []
    assert registry["catalog_source"] == "specs/events/event-catalog.v1.json"
    assert (
        registry["catalog_source_sha256"]
        == hashlib.sha256(generate._normalize_text(contract_verify.CATALOG_PATH)).hexdigest()
    )


def test_generated_python_payload_uses_the_public_frozen_json_type() -> None:
    generated = generate.PYTHON_GENERATED_PATH.read_text(encoding="utf-8")

    assert "payload: FrozenJsonObject" in generated
    assert "payload: Mapping[str, Any]" not in generated
    assert "from vnova_contracts._base import FrozenJsonObject" in generated


def test_contract_drift_detects_unexpected_generated_files(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    expected_path = tmp_path / "expected.py"
    unexpected_path = tmp_path / "stale.py"
    expected_path.write_text("expected\n", encoding="utf-8")
    unexpected_path.write_text("stale\n", encoding="utf-8")
    monkeypatch.setattr(
        generate,
        "MANAGED_GENERATED_ROOTS",
        {tmp_path: frozenset({expected_path})},
    )

    assert generate._unexpected_generated_paths() == [unexpected_path]


def test_duplicate_json_keys_are_rejected(tmp_path: Path) -> None:
    document = tmp_path / "duplicate.json"
    document.write_text('{"value": 1, "value": 2}\n', encoding="utf-8")

    with pytest.raises(ContractVerificationError, match="Duplicate JSON key"):
        contract_verify.load_json(document)


def test_nonstandard_json_numeric_constants_are_rejected(tmp_path: Path) -> None:
    document = tmp_path / "nan.json"
    document.write_text('{"value": NaN}\n', encoding="utf-8")

    with pytest.raises(ContractVerificationError, match="Non-standard JSON numeric constant"):
        contract_verify.load_json(document)


def test_missing_and_remote_schema_references_are_rejected(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr(contract_verify, "EVENT_SPEC_ROOT", tmp_path)
    schema_path = tmp_path / "root.schema.json"
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:test:root",
        "$defs": {"present": {"type": "string"}},
        "allOf": [{"$ref": "#/$defs/missing"}],
    }

    with pytest.raises(ContractVerificationError, match=r"Unresolved.*fragment"):
        contract_verify._verify_local_refs(schema_path, schema)

    schema["allOf"] = [{"$ref": "https://example.com/remote.schema.json"}]
    with pytest.raises(ContractVerificationError, match="repository-local"):
        contract_verify._verify_local_refs(schema_path, schema)

    catalog_path = tmp_path / "event-catalog.v1.json"
    catalog_path.write_text('{"events": []}\n', encoding="utf-8")
    schema["allOf"] = [{"$ref": "event-catalog.v1.json#/events"}]
    with pytest.raises(ContractVerificationError, match="not a governed schema"):
        contract_verify._verify_local_refs(schema_path, schema)


def test_duplicate_schema_identifiers_are_rejected(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr(contract_verify, "EVENT_SPEC_ROOT", tmp_path)
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:test:duplicate",
        "type": "object",
        "additionalProperties": False,
    }
    for name in ("one", "two"):
        (tmp_path / f"{name}.schema.json").write_text(
            json.dumps(schema),
            encoding="utf-8",
        )

    with pytest.raises(ContractVerificationError, match="Duplicate schema \\$id"):
        contract_verify.verify_schemas()


def test_schema_must_explicitly_declare_draft_2020_12(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr(contract_verify, "EVENT_SPEC_ROOT", tmp_path)
    (tmp_path / "old.schema.json").write_text(
        json.dumps(
            {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "$id": "urn:test:old",
                "type": "object",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ContractVerificationError, match="explicitly declare Draft 2020-12"):
        contract_verify.verify_schemas()


def test_open_object_schema_requires_documented_extension_point(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr(contract_verify, "EVENT_SPEC_ROOT", tmp_path)
    schema_path = tmp_path / "open.schema.json"
    schema_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "urn:test:open",
                "type": "object",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ContractVerificationError, match="x-vnova-extension-point"):
        contract_verify.verify_schemas()

    schema_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "urn:test:open",
                "type": "object",
                "x-vnova-extension-point": "Explicit test extension point.",
            }
        ),
        encoding="utf-8",
    )

    assert contract_verify.verify_schemas() == [schema_path]


def test_numeric_schema_requires_portable_inclusive_bounds(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr(contract_verify, "EVENT_SPEC_ROOT", tmp_path)
    schema_path = tmp_path / "integer.schema.json"
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:test:integer",
        "type": "integer",
        "minimum": 1,
    }
    schema_path.write_text(json.dumps(schema), encoding="utf-8")

    with pytest.raises(ContractVerificationError, match="inclusive portable minimum/maximum"):
        contract_verify.verify_schemas()

    schema["maximum"] = contract_verify.MAX_PORTABLE_JSON_NUMBER
    schema_path.write_text(json.dumps(schema), encoding="utf-8")

    assert contract_verify.verify_schemas() == [schema_path]


def test_json_profile_container_depth_limit_is_inclusive_from_root() -> None:
    at_limit: object = []
    for _ in range(contract_verify.MAX_CONTAINER_DEPTH - 1):
        at_limit = [at_limit]

    contract_verify.validate_json_profile(at_limit)

    over_limit = [at_limit]
    with pytest.raises(ContractVerificationError, match="container-depth budget"):
        contract_verify.validate_json_profile(over_limit)


def test_json_profile_node_limit_is_inclusive() -> None:
    contract_verify.validate_json_profile([None] * (contract_verify.MAX_JSON_NODES - 1))

    with pytest.raises(ContractVerificationError, match="JSON node budget"):
        contract_verify.validate_json_profile([None] * contract_verify.MAX_JSON_NODES)


def test_json_profile_utf8_budget_is_inclusive_and_counts_keys() -> None:
    contract_verify.validate_json_profile("a" * contract_verify.MAX_UTF8_STRING_BYTES)
    contract_verify.validate_json_profile({"é": "a" * (contract_verify.MAX_UTF8_STRING_BYTES - 2)})

    with pytest.raises(ContractVerificationError, match="UTF-8 byte budget"):
        contract_verify.validate_json_profile(
            {"é": "a" * (contract_verify.MAX_UTF8_STRING_BYTES - 1)}
        )


@pytest.mark.parametrize("value", [{"bad": "\ud800"}, {"\ud800": "bad"}])
def test_json_profile_rejects_unpaired_surrogates(value: object) -> None:
    with pytest.raises(ContractVerificationError, match="Unicode scalar"):
        contract_verify.validate_json_profile(value)


def test_catalog_schema_version_must_be_portable() -> None:
    event = {
        "type": "ModeChanged",
        "schema_version": contract_verify.MAX_PORTABLE_JSON_NUMBER + 1,
        "status": "required",
    }

    with pytest.raises(ContractVerificationError, match="Invalid schema version"):
        contract_verify._verify_catalog_event(event, 0, set())


def test_dynamic_ref_and_nested_schema_ids_are_rejected(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr(contract_verify, "EVENT_SPEC_ROOT", tmp_path)
    dynamic_ref_path = tmp_path / "dynamic.schema.json"
    dynamic_ref_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "urn:test:dynamic",
                "$dynamicRef": "#node",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ContractVerificationError, match="dynamicRef is not supported"):
        contract_verify.verify_schemas()

    dynamic_ref_path.unlink()
    (tmp_path / "nested.schema.json").write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "urn:test:nested",
                "$defs": {"nested": {"$id": "nested", "type": "string"}},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ContractVerificationError, match="Nested \\$id values are forbidden"):
        contract_verify.verify_schemas()


def test_active_catalog_schema_must_be_governed_before_parity_check(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr(contract_verify, "EVENT_SPEC_ROOT", tmp_path)
    arbitrary_path = tmp_path / "mode.json"
    arbitrary_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "urn:test:mode",
                "type": "object",
                "additionalProperties": False,
            }
        ),
        encoding="utf-8",
    )
    event = {
        "type": "ModeChanged",
        "schema_version": 1,
        "status": "active",
        "schema": "mode.json",
    }

    with pytest.raises(ContractVerificationError, match=r"must end with \.schema\.json"):
        contract_verify._verify_catalog_event(event, 0, set())


def test_active_event_fails_closed_without_payload_parity(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr(contract_verify, "EVENT_SPEC_ROOT", tmp_path)
    schema_path = tmp_path / "mode.schema.json"
    schema_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "urn:test:mode",
                "type": "object",
                "additionalProperties": False,
            }
        ),
        encoding="utf-8",
    )
    event = {
        "type": "ModeChanged",
        "schema_version": 1,
        "status": "active",
        "schema": "mode.schema.json",
    }

    with pytest.raises(ContractVerificationError, match="payload parity support"):
        contract_verify._verify_catalog_event(event, 0, set())


def test_active_event_requires_both_fixture_sets(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    fixture_root = tmp_path / "fixtures"
    valid_root = fixture_root / "ModeChanged" / "v1" / "valid"
    valid_root.mkdir(parents=True)
    (valid_root / "minimal.json").write_text("{}\n", encoding="utf-8")
    schema_path = tmp_path / "mode.schema.json"
    schema_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "urn:test:mode",
                "type": "object",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(contract_verify, "EVENT_FIXTURE_ROOT", fixture_root)

    with pytest.raises(ContractVerificationError, match="valid and invalid fixtures"):
        contract_verify._verify_active_event_contract("ModeChanged", 1, schema_path)


def test_active_event_fixtures_resolve_repository_local_refs(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    schema_root = tmp_path / "specs"
    fixture_root = tmp_path / "fixtures"
    valid_root = fixture_root / "ModeChanged" / "v1" / "valid"
    invalid_root = fixture_root / "ModeChanged" / "v1" / "invalid"
    valid_root.mkdir(parents=True)
    invalid_root.mkdir(parents=True)
    common_path = schema_root / "common.schema.json"
    mode_path = schema_root / "mode.schema.json"
    schema_root.mkdir()
    common_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "https://schemas.vnova.test/common.schema.json",
                "type": "string",
            }
        ),
        encoding="utf-8",
    )
    mode_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "urn:test:mode",
                "type": "object",
                "additionalProperties": False,
                "required": ["mode"],
                "properties": {"mode": {"$ref": "./common.schema.json"}},
            }
        ),
        encoding="utf-8",
    )
    (valid_root / "valid.json").write_text('{"mode": "supervised"}\n', encoding="utf-8")
    (invalid_root / "invalid.json").write_text('{"mode": 1}\n', encoding="utf-8")
    monkeypatch.setattr(contract_verify, "EVENT_SPEC_ROOT", schema_root)
    monkeypatch.setattr(contract_verify, "EVENT_FIXTURE_ROOT", fixture_root)

    contract_verify._verify_active_event_contract("ModeChanged", 1, mode_path)


def test_active_event_fixture_profile_accounts_for_envelope_overhead(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    schema_root = tmp_path / "specs"
    fixture_root = tmp_path / "fixtures"
    valid_root = fixture_root / "ModeChanged" / "v1" / "valid"
    invalid_root = fixture_root / "ModeChanged" / "v1" / "invalid"
    schema_root.mkdir()
    valid_root.mkdir(parents=True)
    invalid_root.mkdir(parents=True)
    mode_path = schema_root / "mode.schema.json"
    mode_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "urn:test:mode",
                "type": "object",
                "x-vnova-extension-point": "Adversarial recursive payload fixture.",
                "additionalProperties": True,
            }
        ),
        encoding="utf-8",
    )
    payload: object = {}
    for _ in range(contract_verify.MAX_CONTAINER_DEPTH - 1):
        payload = {"nested": payload}
    (valid_root / "standalone-limit.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    (invalid_root / "wrong-root.json").write_text("[]\n", encoding="utf-8")
    monkeypatch.setattr(contract_verify, "EVENT_SPEC_ROOT", schema_root)
    monkeypatch.setattr(contract_verify, "EVENT_FIXTURE_ROOT", fixture_root)

    with pytest.raises(ContractVerificationError, match="valid fixture violates JSON profile"):
        contract_verify._verify_active_event_contract("ModeChanged", 1, mode_path)


def test_python_generation_projection_preserves_local_ref_tree(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    schema_root = tmp_path / "specs"
    schema_root.mkdir()
    envelope_path = schema_root / "event-envelope.v1.schema.json"
    common_path = schema_root / "common.schema.json"
    common_path.write_text('{"const": "kept"}\n', encoding="utf-8")
    envelope_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "https://schemas.vnova.test/event-envelope.v1.schema.json",
                "$defs": {
                    "JsonValue": {"type": "string"},
                    "Shared": {"type": "string"},
                },
                "properties": {
                    "occurred_at": {
                        "type": "string",
                        "format": "date-time",
                        "pattern": contract_verify.CANONICAL_TIMESTAMP_PATTERN,
                    },
                    "shared": {"$ref": "common.schema.json"},
                    "local_shared": {"$ref": "#/$defs/Shared"},
                    "payload": {
                        "type": "object",
                        "additionalProperties": {"$ref": "#/$defs/JsonValue"},
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(generate, "EVENT_SPEC_ROOT", schema_root)
    monkeypatch.setattr(generate, "ENVELOPE_SCHEMA_PATH", envelope_path)

    projection = generate._write_python_generation_schema(tmp_path / "output")

    projected_schema = contract_verify.load_json(projection)
    occurred_at = projected_schema["properties"]["occurred_at"]
    assert "pattern" not in occurred_at
    assert projected_schema["properties"]["payload"]["additionalProperties"] is True
    assert projected_schema["$defs"] == {"Shared": {"type": "string"}}
    assert (projection.parent / "common.schema.json").read_text(encoding="utf-8") == (
        common_path.read_text(encoding="utf-8")
    )


def test_generated_manifests_are_distribution_specific_v2() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    workspace_manifest = json.loads(
        (repository_root / "packages" / "contracts" / "manifest.json").read_text(encoding="utf-8")
    )
    python_manifest_path = (
        repository_root
        / "packages"
        / "contracts"
        / "python"
        / "src"
        / "vnova_contracts"
        / "contract-manifest.json"
    )
    typescript_manifest_path = (
        repository_root / "packages" / "contracts" / "typescript" / "contract-manifest.json"
    )
    python_manifest = json.loads(python_manifest_path.read_text(encoding="utf-8"))
    typescript_manifest = json.loads(typescript_manifest_path.read_text(encoding="utf-8"))
    canonical_schema = (
        repository_root / "specs" / "events" / "event-envelope.v1.schema.json"
    ).read_bytes()
    canonical_catalog = generate._normalize_text(
        repository_root / "specs" / "events" / "event-catalog.v1.json"
    )

    for manifest in (workspace_manifest, python_manifest, typescript_manifest):
        assert manifest["manifest_version"] == generate.MANIFEST_VERSION
        assert manifest["source"] == "specs/events/event-envelope.v1.schema.json"
        assert manifest["schema_id"] == "urn:vnova:event-envelope:1"
        assert manifest["catalog_source"] == "specs/events/event-catalog.v1.json"
        assert manifest["catalog_source_sha256"] == hashlib.sha256(canonical_catalog).hexdigest()
        assert set(manifest["generators"]) == {"python", "typescript"}

    workspace_artifacts = {
        artifact["path"]: artifact["sha256"]
        for artifact in workspace_manifest["workspace_artifacts"]
    }
    assert set(workspace_artifacts) == {
        "packages/contracts/python/src/vnova_contracts/generated/event_envelope_v1.py",
        ("packages/contracts/python/src/vnova_contracts/registry/active-event-registry.v1.json"),
        "packages/contracts/python/src/vnova_contracts/schemas/event-envelope.v1.schema.json",
        ("packages/contracts/typescript/src/generated/active-event-registry.v1.json"),
        "packages/contracts/typescript/src/generated/event-envelope.v1.schema.json",
        "packages/contracts/typescript/src/generated/event-envelope.v1.ts",
    }
    for relative_path, digest in workspace_artifacts.items():
        assert hashlib.sha256((repository_root / relative_path).read_bytes()).hexdigest() == digest

    assert python_manifest["package"] == {
        "ecosystem": "python",
        "name": "vnova-contracts",
        "version": "0.1.0",
    }
    python_artifacts = {
        artifact["path"]: artifact["sha256"] for artifact in python_manifest["artifacts"]
    }
    assert set(python_artifacts) == {
        "generated/event_envelope_v1.py",
        "registry/active-event-registry.v1.json",
        "schemas/event-envelope.v1.schema.json",
    }
    for relative_path, digest in python_artifacts.items():
        assert (
            hashlib.sha256((python_manifest_path.parent / relative_path).read_bytes()).hexdigest()
            == digest
        )

    assert typescript_manifest["package"] == {
        "ecosystem": "npm",
        "name": "@vnova/contracts",
        "version": "0.1.0",
    }
    assert {
        artifact["path"]: artifact["sha256"] for artifact in typescript_manifest["artifacts"]
    } == {
        "dist/generated/active-event-registry.v1.json": hashlib.sha256(
            generate.PYTHON_ACTIVE_EVENT_REGISTRY_PATH.read_bytes()
        ).hexdigest(),
        "dist/generated/event-envelope.v1.schema.json": hashlib.sha256(
            canonical_schema
        ).hexdigest(),
    }
    generated_typescript = (
        repository_root
        / "packages"
        / "contracts"
        / "typescript"
        / "src"
        / "generated"
        / "event-envelope.v1.ts"
    ).read_bytes()
    assert (
        typescript_manifest["generated_source_sha256"]
        == hashlib.sha256(generated_typescript).hexdigest()
    )
    assert python_manifest != typescript_manifest
