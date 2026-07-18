from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, assert_type, cast
from uuid import UUID

import pytest
import vnova_contracts.validation as contract_validation
from pydantic import ValidationError
from vnova_contracts import (
    EventEnvelopeValidationError,
    FrozenJsonObject,
    FrozenJsonValue,
    PublishableEventValidationError,
    VNovaEventEnvelopeV1,
    assert_valid_event_envelope,
    assert_valid_publishable_event,
    is_valid_event_envelope,
    is_valid_publishable_event,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_ROOT = REPOSITORY_ROOT / "tests" / "contracts" / "fixtures" / "envelope"
MAX_CONTAINER_DEPTH = 64
MAX_JSON_NODES = 10_000
MAX_UTF8_STRING_BYTES = 1_048_576
ENVELOPE_BASE_CONTAINER_DEPTH = 2


def _typing_probe_frozen_payload(model: VNovaEventEnvelopeV1) -> None:
    assert_type(model.payload, FrozenJsonObject)
    assert_type(model.payload["nested"], FrozenJsonValue)


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_rejected_by_public_and_direct_validation(value: dict[str, Any]) -> None:
    assert not is_valid_event_envelope(value)
    with pytest.raises(EventEnvelopeValidationError):
        assert_valid_event_envelope(value)
    with pytest.raises(ValidationError):
        VNovaEventEnvelopeV1.model_validate(value)


def _assert_accepted_by_public_and_direct_validation(value: dict[str, Any]) -> None:
    assert is_valid_event_envelope(value)
    assert_valid_event_envelope(value)
    VNovaEventEnvelopeV1.model_validate(value)


def _nested_arrays(depth: int) -> Any:
    value: Any = "leaf"
    for _ in range(depth):
        value = [value]
    return value


def _envelope_with_container_depth(depth: int) -> dict[str, Any]:
    assert depth >= ENVELOPE_BASE_CONTAINER_DEPTH
    value = cast(dict[str, Any], _load(FIXTURE_ROOT / "valid" / "minimal.json"))
    value["payload"] = {"nested": _nested_arrays(depth - ENVELOPE_BASE_CONTAINER_DEPTH)}
    return value


def _json_node_count(value: Any) -> int:
    if type(value) is list:
        return 1 + sum(_json_node_count(child) for child in value)
    if type(value) is dict:
        return 1 + sum(_json_node_count(child) for child in value.values())
    return 1


def _envelope_with_json_node_count(nodes: int) -> dict[str, Any]:
    value = cast(dict[str, Any], _load(FIXTURE_ROOT / "valid" / "minimal.json"))
    payload: dict[str, Any] = {"values": []}
    value["payload"] = payload
    fixed_nodes = _json_node_count(value)
    payload["values"] = list(range(nodes - fixed_nodes))
    assert _json_node_count(value) == nodes
    return value


def _utf8_string_and_key_bytes(value: Any) -> int:
    if type(value) is str:
        return len(value.encode("utf-8"))
    if type(value) is list:
        return sum(_utf8_string_and_key_bytes(child) for child in value)
    if type(value) is dict:
        return sum(
            len(key.encode("utf-8")) + _utf8_string_and_key_bytes(child)
            for key, child in value.items()
        )
    return 0


def _envelope_with_utf8_string_bytes(string_bytes: int) -> dict[str, Any]:
    value = cast(dict[str, Any], _load(FIXTURE_ROOT / "valid" / "minimal.json"))
    payload = {"text": ""}
    value["payload"] = payload
    fixed_bytes = _utf8_string_and_key_bytes(value)
    payload["text"] = "a" * (string_bytes - fixed_bytes)
    assert _utf8_string_and_key_bytes(value) == string_bytes
    return value


@pytest.mark.parametrize("fixture_path", sorted((FIXTURE_ROOT / "valid").glob("*.json")))
def test_valid_fixtures_are_accepted(fixture_path: Path) -> None:
    value = _load(fixture_path)
    model = assert_valid_event_envelope(value)
    assert model.event_id is not None
    assert is_valid_event_envelope(value)
    round_trip = json.loads(model.model_dump_json())
    assert is_valid_event_envelope(round_trip)
    assert assert_valid_event_envelope(round_trip) == model


@pytest.mark.parametrize("fixture_path", sorted((FIXTURE_ROOT / "invalid").glob("*.json")))
def test_invalid_fixtures_are_rejected(fixture_path: Path) -> None:
    value = _load(fixture_path)
    assert not is_valid_event_envelope(value)
    with pytest.raises(EventEnvelopeValidationError) as captured:
        assert_valid_event_envelope(value)
    assert captured.value.code == "invalid_event_envelope"


@pytest.mark.parametrize("fixture_path", sorted((FIXTURE_ROOT / "valid").glob("*.json")))
def test_envelope_validity_does_not_grant_publishable_event_authority(
    fixture_path: Path,
) -> None:
    value = _load(fixture_path)

    assert is_valid_event_envelope(value)
    assert not is_valid_publishable_event(value)
    with pytest.raises(PublishableEventValidationError) as captured:
        assert_valid_publishable_event(value)
    assert captured.value.code == "invalid_publishable_event"


def test_publishable_event_validation_normalizes_invalid_envelope_errors() -> None:
    value = _load(FIXTURE_ROOT / "invalid" / "missing-event-id.json")

    assert not is_valid_publishable_event(value)
    with pytest.raises(PublishableEventValidationError) as captured:
        assert_valid_publishable_event(value)
    assert captured.value.code == "invalid_publishable_event"
    assert isinstance(captured.value.__cause__, EventEnvelopeValidationError)


@pytest.mark.parametrize(
    "schema_version",
    [0, -1, 1.5, True, 9_007_199_254_740_992],
)
def test_active_event_registry_rejects_nonportable_schema_versions(
    schema_version: object,
) -> None:
    event = {
        "schema": "payloads/mode.schema.json",
        "schema_version": schema_version,
        "type": "ModeChanged",
    }

    with pytest.raises(RuntimeError, match="identity is malformed"):
        contract_validation._active_event_record(event)


@pytest.mark.parametrize("schema_id", [None, ""])
def test_active_event_registry_requires_nonempty_payload_schema_ids(
    schema_id: str | None,
) -> None:
    document = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
    }
    if schema_id is not None:
        document["$id"] = schema_id
    schema = {
        "document": document,
        "path": "payloads/mode.schema.json",
        "source_sha256": "0" * 64,
    }

    with pytest.raises(RuntimeError, match="non-empty \\$id"):
        contract_validation._payload_schema_record(schema)


def test_active_event_registry_rejects_duplicate_payload_schema_ids() -> None:
    schema_id = "urn:vnova:test:duplicate"
    raw_schemas: list[object] = [
        {
            "document": {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": schema_id,
                "type": "object",
            },
            "path": path,
            "source_sha256": "0" * 64,
        }
        for path in ("payloads/first.schema.json", "payloads/second.schema.json")
    ]
    documents, resources = contract_validation._payload_schema_resources(raw_schemas)

    with pytest.raises(RuntimeError, match="\\$id is duplicated"):
        contract_validation._payload_schema_registry(documents, resources)


@pytest.mark.parametrize("fixture_path", sorted((FIXTURE_ROOT / "invalid").glob("*.json")))
def test_generated_model_directly_rejects_every_invalid_fixture(fixture_path: Path) -> None:
    value = _load(fixture_path)

    with pytest.raises(ValidationError):
        VNovaEventEnvelopeV1.model_validate(value)


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("event_id", UUID("018f47df-7c09-7b1a-83b5-57f0d6e15f3f")),
        ("stream_session_id", UUID("018f47df-7c09-7b1a-83b5-57f0d6e15f40")),
        ("stream_session_id", "018F47DF-7C09-7B1A-83B5-57F0D6E15F40"),
        ("turn_id", UUID("018f47df-7c09-7b1a-83b5-57f0d6e15f42")),
        ("turn_id", "urn:uuid:018f47df-7c09-7b1a-83b5-57f0d6e15f42"),
        ("turn_id", None),
        ("schema_version", True),
        ("schema_version", 1.0),
        ("type", b"ModeChanged"),
        ("occurred_at", 0),
    ],
)
def test_exact_json_scalar_types_are_enforced_by_all_python_entry_points(
    field_name: str,
    invalid_value: object,
) -> None:
    value = _load(FIXTURE_ROOT / "valid" / "minimal.json")
    value[field_name] = invalid_value

    _assert_rejected_by_public_and_direct_validation(value)


def test_generated_model_directly_accepts_canonical_microseconds_and_unicode() -> None:
    timestamp_value = _load(FIXTURE_ROOT / "valid" / "microsecond-time.json")
    timestamp_model = VNovaEventEnvelopeV1.model_validate(timestamp_value)
    unicode_value = _load(FIXTURE_ROOT / "valid" / "emoji.json")
    unicode_model = VNovaEventEnvelopeV1.model_validate(unicode_value)

    assert json.loads(timestamp_model.model_dump_json())["occurred_at"] == (
        "2026-07-17T00:00:00.010000Z"
    )
    assert unicode_model.payload["emoji"] == "😀"


def test_negative_zero_is_normalized_by_public_and_direct_validation() -> None:
    value = _load(FIXTURE_ROOT / "valid" / "negative-zero.json")
    public_model = assert_valid_event_envelope(value)
    direct_model = VNovaEventEnvelopeV1.model_validate(value)

    for model in (public_model, direct_model):
        normalized = cast(float, model.payload["negative_zero"])
        assert normalized == 0.0
        assert math.copysign(1.0, normalized) == 1.0


def test_contract_profile_container_depth_budget_is_inclusive() -> None:
    _assert_accepted_by_public_and_direct_validation(
        _envelope_with_container_depth(MAX_CONTAINER_DEPTH)
    )
    _assert_rejected_by_public_and_direct_validation(
        _envelope_with_container_depth(MAX_CONTAINER_DEPTH + 1)
    )


def test_contract_profile_json_node_budget_is_inclusive() -> None:
    _assert_accepted_by_public_and_direct_validation(_envelope_with_json_node_count(MAX_JSON_NODES))
    _assert_rejected_by_public_and_direct_validation(
        _envelope_with_json_node_count(MAX_JSON_NODES + 1)
    )


def test_contract_profile_utf8_string_budget_is_inclusive() -> None:
    _assert_accepted_by_public_and_direct_validation(
        _envelope_with_utf8_string_bytes(MAX_UTF8_STRING_BYTES)
    )
    _assert_rejected_by_public_and_direct_validation(
        _envelope_with_utf8_string_bytes(MAX_UTF8_STRING_BYTES + 1)
    )


def test_contract_profile_counts_object_keys_toward_the_total_string_budget() -> None:
    value = _load(FIXTURE_ROOT / "valid" / "minimal.json")
    value["payload"] = {"k" * (MAX_UTF8_STRING_BYTES // 2): "v" * (MAX_UTF8_STRING_BYTES // 2 + 1)}

    _assert_rejected_by_public_and_direct_validation(value)


def test_contract_profile_measures_strings_in_utf8_bytes() -> None:
    value = _load(FIXTURE_ROOT / "valid" / "minimal.json")
    value["payload"] = {"text": "😀" * (MAX_UTF8_STRING_BYTES // 4 + 1)}

    _assert_rejected_by_public_and_direct_validation(value)


def test_generated_model_rejects_non_utc_timestamp_strings() -> None:
    value = _load(FIXTURE_ROOT / "valid" / "minimal.json")
    value["occurred_at"] = "2026-07-17T10:00:00+09:00"

    with pytest.raises(ValidationError):
        VNovaEventEnvelopeV1.model_validate(value)


def test_generated_model_is_frozen_at_the_envelope_boundary() -> None:
    model = assert_valid_event_envelope(_load(FIXTURE_ROOT / "valid" / "minimal.json"))

    with pytest.raises(ValidationError):
        model.schema_version = 2


def test_payload_is_deeply_immutable_and_detached_from_input() -> None:
    value = _load(FIXTURE_ROOT / "valid" / "minimal.json")
    value["payload"] = {"nested": {"items": [{"name": "before"}]}}
    model = assert_valid_event_envelope(value)

    value["payload"]["nested"]["items"][0]["name"] = "after"
    nested = cast(Any, model.payload["nested"])
    items = cast(Any, nested["items"])

    assert items[0]["name"] == "before"
    with pytest.raises(TypeError):
        cast(Any, model.payload)["new"] = "value"
    with pytest.raises(TypeError):
        nested["new"] = "value"
    with pytest.raises(AttributeError):
        items.append("value")

    serialized = json.loads(model.model_dump_json())
    assert serialized["payload"] == {"nested": {"items": [{"name": "before"}]}}


def test_valid_model_serialization_round_trips_through_canonical_validation() -> None:
    model = assert_valid_event_envelope(_load(FIXTURE_ROOT / "valid" / "minimal.json"))

    serialized = json.loads(model.model_dump_json())

    assert "turn_id" not in serialized
    assert serialized["payload"] == {}
    assert is_valid_event_envelope(serialized)
    assert assert_valid_event_envelope(serialized) == model


def test_payload_null_is_preserved_while_absent_model_fields_are_omitted() -> None:
    value = _load(FIXTURE_ROOT / "valid" / "minimal.json")
    value["payload"] = {"nullable": None}
    model = assert_valid_event_envelope(value)

    serialized = json.loads(model.model_dump_json(exclude_none=False))

    assert "turn_id" not in serialized
    assert serialized["payload"] == {"nullable": None}


def test_payload_primitive_subclasses_are_rejected_as_non_json_runtime_types() -> None:
    class StringSubclass(str):
        pass

    class IntegerSubclass(int):
        pass

    class FloatSubclass(float):
        pass

    for invalid_value in (
        StringSubclass("value"),
        IntegerSubclass(3),
        FloatSubclass(1.5),
    ):
        value = _load(FIXTURE_ROOT / "valid" / "minimal.json")
        value["payload"] = {"invalid": invalid_value}

        _assert_rejected_by_public_and_direct_validation(value)


def test_direct_model_validation_enforces_portable_json_number_range() -> None:
    value = _load(FIXTURE_ROOT / "valid" / "minimal.json")
    value["payload"] = {"unsafe_integer": 9_007_199_254_740_992}

    with pytest.raises(ValidationError, match="portable IEEE-754 range"):
        VNovaEventEnvelopeV1.model_validate(value)


@pytest.mark.parametrize("invalid_value", [float("nan"), object()])
def test_payload_rejects_non_json_values(invalid_value: object) -> None:
    value = _load(FIXTURE_ROOT / "valid" / "minimal.json")
    value["payload"] = {"invalid": invalid_value}

    with pytest.raises(EventEnvelopeValidationError):
        assert_valid_event_envelope(value)


def test_copy_updates_are_revalidated_and_remain_deeply_immutable() -> None:
    model = assert_valid_event_envelope(_load(FIXTURE_ROOT / "valid" / "minimal.json"))
    copied = model.model_copy(update={"payload": {"items": [1, 2]}})

    with pytest.raises(TypeError):
        cast(Any, copied.payload)["new"] = "value"
    with pytest.raises(AttributeError):
        cast(Any, copied.payload["items"]).append(3)

    with pytest.raises(ValidationError):
        model.model_copy(update={"payload": {"invalid": object()}})


def test_unchecked_model_construction_is_disabled() -> None:
    with pytest.raises(TypeError, match="model_construct is disabled"):
        VNovaEventEnvelopeV1.model_construct()


def test_deprecated_copy_updates_are_revalidated() -> None:
    model = assert_valid_event_envelope(_load(FIXTURE_ROOT / "valid" / "minimal.json"))

    with pytest.warns(DeprecationWarning):
        copied = model.copy(update={"payload": {"items": [1, 2]}})
    with pytest.raises(TypeError):
        cast(Any, copied.payload)["new"] = "value"

    with pytest.warns(DeprecationWarning), pytest.raises(ValidationError):
        model.copy(update={"payload": {"invalid": object()}})


def test_payload_cycle_is_normalized_as_validation_failure() -> None:
    value = _load(FIXTURE_ROOT / "valid" / "minimal.json")
    cyclic: dict[str, Any] = {}
    cyclic["self"] = cyclic
    value["payload"] = cyclic

    with pytest.raises(EventEnvelopeValidationError):
        assert_valid_event_envelope(value)


def test_public_validation_rejects_mapping_subclasses_without_reading_them() -> None:
    class HostileMapping(dict[str, Any]):
        reads = 0

        def items(self) -> Any:
            type(self).reads += 1
            raise AssertionError("Untrusted mapping methods must not execute")

        def __getitem__(self, key: str) -> Any:
            type(self).reads += 1
            raise AssertionError("Untrusted mapping methods must not execute")

    value = HostileMapping(_load(FIXTURE_ROOT / "valid" / "minimal.json"))

    assert not is_valid_event_envelope(value)
    with pytest.raises(EventEnvelopeValidationError):
        assert_valid_event_envelope(value)
    assert HostileMapping.reads == 0
