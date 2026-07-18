"""Verify canonical JSON Schemas, the event catalog, and shared fixtures."""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, NoReturn, cast
from urllib.parse import unquote, urldefrag, urljoin, urlparse

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
EVENT_SPEC_ROOT = REPOSITORY_ROOT / "specs" / "events"
CATALOG_PATH = EVENT_SPEC_ROOT / "event-catalog.v1.json"
ENVELOPE_SCHEMA_PATH = EVENT_SPEC_ROOT / "event-envelope.v1.schema.json"
ENVELOPE_FIXTURE_ROOT = REPOSITORY_ROOT / "tests" / "contracts" / "fixtures" / "envelope"
EVENT_FIXTURE_ROOT = REPOSITORY_ROOT / "tests" / "contracts" / "fixtures" / "events"

EVENT_TYPE_PATTERN = re.compile(r"^[A-Z][A-Za-z0-9]+$")
ALLOWED_CATALOG_STATUSES = frozenset({"required", "active", "deprecated"})
DRAFT_2020_12_URI = "https://json-schema.org/draft/2020-12/schema"
SUPPORTED_ACTIVE_EVENT_IDENTITIES: frozenset[tuple[str, int]] = frozenset()
MIN_PORTABLE_JSON_NUMBER = -9_007_199_254_740_991
MAX_PORTABLE_JSON_NUMBER = 9_007_199_254_740_991
MAX_CONTAINER_DEPTH = 64
MAX_JSON_NODES = 10_000
MAX_UTF8_STRING_BYTES = 1_048_576
CANONICAL_UUID_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
CANONICAL_TIMESTAMP_PATTERN = (
    r"^(?!0000)[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])"
    r"T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    r"(?:\.(?!000000)[0-9]{6})?Z$"
)
EXPECTED_JSON_PROFILE: JsonObject = {
    "maxContainerDepth": MAX_CONTAINER_DEPTH,
    "maxNodes": MAX_JSON_NODES,
    "maxUtf8StringBytes": MAX_UTF8_STRING_BYTES,
    "normalizeNegativeZero": True,
    "requireUnicodeScalarStrings": True,
}
ASCII_MAX = 0x7F
TWO_BYTE_UTF8_MAX = 0x7FF
BMP_MAX = 0xFFFF
SURROGATE_MIN = 0xD800
SURROGATE_MAX = 0xDFFF

JsonObject = dict[str, Any]


class ContractVerificationError(RuntimeError):
    """Raised when a canonical contract invariant is violated."""


@dataclass
class _JsonProfileState:
    active_containers: set[int] = field(default_factory=set)
    nodes: int = 0
    utf8_string_bytes: int = 0


def _record_profile_string(value: str, state: _JsonProfileState) -> None:
    remaining = MAX_UTF8_STRING_BYTES - state.utf8_string_bytes
    if len(value) > remaining:
        raise ContractVerificationError("Contract strings exceed the UTF-8 byte budget")
    for character in value:
        code_point = ord(character)
        if SURROGATE_MIN <= code_point <= SURROGATE_MAX:
            raise ContractVerificationError(
                "Contract strings must contain only Unicode scalar values"
            )
        width = (
            1
            if code_point <= ASCII_MAX
            else 2
            if code_point <= TWO_BYTE_UTF8_MAX
            else 3
            if code_point <= BMP_MAX
            else 4
        )
        state.utf8_string_bytes += width
        if state.utf8_string_bytes > MAX_UTF8_STRING_BYTES:
            raise ContractVerificationError("Contract strings exceed the UTF-8 byte budget")


def validate_json_profile(
    value: object,
    state: _JsonProfileState | None = None,
    depth: int = 1,
) -> None:
    """Validate the deterministic JSON resource profile shared by both runtimes."""

    state = state or _JsonProfileState()
    state.nodes += 1
    if state.nodes > MAX_JSON_NODES:
        raise ContractVerificationError("Contract value exceeds the JSON node budget")
    if value is None or type(value) in {bool, int, float}:
        return
    if type(value) is str:
        _record_profile_string(value, state)
        return
    if type(value) not in {dict, list}:
        raise ContractVerificationError("Contract value is not exact built-in JSON")
    if depth > MAX_CONTAINER_DEPTH:
        raise ContractVerificationError("Contract value exceeds the container-depth budget")

    identity = id(value)
    if identity in state.active_containers:
        raise ContractVerificationError("Contract value contains a cycle")
    state.active_containers.add(identity)
    try:
        if type(value) is list:
            if list.__len__(value) > MAX_JSON_NODES - state.nodes:
                raise ContractVerificationError("Contract value exceeds the JSON node budget")
            for child in list.__iter__(value):
                validate_json_profile(child, state, depth + 1)
            return
        object_value = cast(dict[object, object], value)
        for key, child in dict.items(object_value):
            if type(key) is not str:
                raise ContractVerificationError("Contract object key is not an exact string")
            _record_profile_string(key, state)
            validate_json_profile(child, state, depth + 1)
    finally:
        state.active_containers.remove(identity)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> JsonObject:
    result: JsonObject = {}
    for key, value in pairs:
        if key in result:
            raise ContractVerificationError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite_constant(value: str) -> NoReturn:
    raise ContractVerificationError(f"Non-standard JSON numeric constant: {value}")


def load_json(path: Path) -> Any:
    """Load UTF-8 JSON while rejecting duplicate object keys."""

    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonfinite_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ContractVerificationError(f"Cannot read JSON {path}: {error}") from error


def _walk_json(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _decode_json_pointer_token(token: str) -> str:
    if re.search(r"~(?:[^01]|$)", token):
        raise ContractVerificationError(f"Invalid JSON Pointer escape in token: {token}")
    return token.replace("~1", "/").replace("~0", "~")


def _fragment_exists(document: Any, fragment: str) -> bool:
    decoded = unquote(fragment)
    if not decoded:
        return True
    if decoded.startswith("/"):
        current = document
        for raw_token in decoded[1:].split("/"):
            token = _decode_json_pointer_token(raw_token)
            if isinstance(current, dict) and token in current:
                current = current[token]
            elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
                current = current[int(token)]
            else:
                return False
        return True
    return any(
        isinstance(node, dict)
        and (node.get("$anchor") == decoded or node.get("$dynamicAnchor") == decoded)
        for node in _walk_json(document)
    )


def _load_ref_target(
    schema_path: Path,
    root_schema: JsonObject,
    reference_path: str,
    reference: str,
) -> Any:
    if not reference_path:
        return root_schema
    parsed = urlparse(reference_path)
    if parsed.scheme or parsed.netloc or Path(reference_path).is_absolute():
        raise ContractVerificationError(
            f"Only repository-local relative $ref values are allowed: {schema_path}: {reference}"
        )
    resolved = (schema_path.parent / unquote(reference_path)).resolve()
    try:
        resolved.relative_to(EVENT_SPEC_ROOT.resolve())
    except ValueError as error:
        raise ContractVerificationError(
            f"$ref escapes specs/events: {schema_path}: {reference}"
        ) from error
    if not resolved.is_file():
        raise ContractVerificationError(f"Unresolved local $ref in {schema_path}: {reference}")
    if not resolved.name.endswith(".schema.json"):
        raise ContractVerificationError(
            f"$ref target is not a governed schema file: {schema_path}: {reference}"
        )
    target_document = load_json(resolved)
    if not isinstance(target_document, dict):
        raise ContractVerificationError(f"Referenced schema must be an object: {resolved}")
    if target_document.get("$schema") != DRAFT_2020_12_URI:
        raise ContractVerificationError(f"Referenced schema must declare Draft 2020-12: {resolved}")
    try:
        Draft202012Validator.check_schema(target_document)
    except Exception as error:
        raise ContractVerificationError(
            f"Invalid referenced Draft 2020-12 schema {resolved}: {error}"
        ) from error
    return target_document


def _verify_local_refs(schema_path: Path, schema: JsonObject) -> None:
    for node in _walk_json(schema):
        if not isinstance(node, dict):
            continue
        if "$dynamicRef" in node:
            raise ContractVerificationError(
                f"$dynamicRef is not supported in governed event schemas: {schema_path}"
            )
        if "$ref" not in node:
            continue
        reference = node["$ref"]
        if not isinstance(reference, str):
            raise ContractVerificationError(f"Non-string $ref in {schema_path}")
        reference_path, fragment = urldefrag(reference)
        target_document = _load_ref_target(
            schema_path,
            schema,
            reference_path,
            reference,
        )
        if not _fragment_exists(target_document, fragment):
            raise ContractVerificationError(
                f"Unresolved $ref fragment in {schema_path}: {reference}"
            )


def _validate_schema_document(schema_path: Path) -> JsonObject:
    if not schema_path.name.endswith(".schema.json"):
        raise ContractVerificationError(
            f"Governed schema path must end with .schema.json: {schema_path}"
        )
    schema = load_json(schema_path)
    if not isinstance(schema, dict):
        raise ContractVerificationError(f"Schema root must be an object: {schema_path}")
    if schema.get("$schema") != DRAFT_2020_12_URI:
        raise ContractVerificationError(
            f"Schema must explicitly declare Draft 2020-12: {schema_path}"
        )
    for index, node in enumerate(_walk_json(schema)):
        if index > 0 and isinstance(node, dict) and "$id" in node:
            raise ContractVerificationError(
                f"Nested $id values are forbidden in governed event schemas: {schema_path}"
            )
        if isinstance(node, dict) and node.get("type") == "object":
            closed = (
                node.get("additionalProperties") is False
                or node.get("unevaluatedProperties") is False
            )
            extension_reason = node.get("x-vnova-extension-point")
            if not closed and not (isinstance(extension_reason, str) and extension_reason.strip()):
                raise ContractVerificationError(
                    "Open object schema requires a documented x-vnova-extension-point: "
                    f"{schema_path}"
                )
        if isinstance(node, dict):
            declared_type = node.get("type")
            declared_types = (
                {declared_type}
                if isinstance(declared_type, str)
                else set(declared_type)
                if isinstance(declared_type, list)
                and all(isinstance(item, str) for item in declared_type)
                else set()
            )
            if declared_types.intersection({"integer", "number"}):
                minimum = node.get("minimum")
                maximum = node.get("maximum")
                has_portable_minimum = (
                    isinstance(minimum, int | float)
                    and not isinstance(minimum, bool)
                    and minimum >= MIN_PORTABLE_JSON_NUMBER
                )
                has_portable_maximum = (
                    isinstance(maximum, int | float)
                    and not isinstance(maximum, bool)
                    and maximum <= MAX_PORTABLE_JSON_NUMBER
                )
                if not has_portable_minimum or not has_portable_maximum:
                    raise ContractVerificationError(
                        "Numeric schema must declare inclusive portable minimum/maximum: "
                        f"{schema_path}"
                    )
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as error:
        raise ContractVerificationError(
            f"Invalid Draft 2020-12 schema {schema_path}: {error}"
        ) from error
    _verify_local_refs(schema_path, schema)
    return schema


def _verify_envelope_schema_profile(schema: JsonObject) -> None:
    if schema.get("x-vnova-json-profile") != EXPECTED_JSON_PROFILE:
        raise ContractVerificationError(
            "Event envelope x-vnova-json-profile does not match the supported runtime profile"
        )
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        raise ContractVerificationError("Event envelope requires object properties")
    for field_name in ("event_id", "stream_session_id", "turn_id"):
        field_schema = properties.get(field_name)
        if (
            not isinstance(field_schema, dict)
            or field_schema.get("pattern") != CANONICAL_UUID_PATTERN
        ):
            raise ContractVerificationError(
                f"Event envelope {field_name} must require the canonical UUID pattern"
            )
    occurred_at = properties.get("occurred_at")
    if (
        not isinstance(occurred_at, dict)
        or occurred_at.get("pattern") != CANONICAL_TIMESTAMP_PATTERN
    ):
        raise ContractVerificationError(
            "Event envelope occurred_at must require the canonical timestamp pattern"
        )


def _schema_registry() -> Registry[Any]:
    schema_paths = sorted(EVENT_SPEC_ROOT.rglob("*.schema.json"))
    documents = {
        schema_path.resolve(): _validate_schema_document(schema_path)
        for schema_path in schema_paths
    }
    resources = {
        schema_path: Resource.from_contents(document) for schema_path, document in documents.items()
    }
    registry: Registry[Any] = Registry()
    for target_path, target_resource in resources.items():
        target_document = documents[target_path]
        target_identifier = target_document["$id"]
        registry = registry.with_resource(target_identifier, target_resource)
        registry = registry.with_resource(target_path.as_uri(), target_resource)
    for source_path, source_document in documents.items():
        for node in _walk_json(source_document):
            if not isinstance(node, dict) or not isinstance(node.get("$ref"), str):
                continue
            reference_path, _ = urldefrag(node["$ref"])
            if not reference_path:
                continue
            target_path = (source_path.parent / unquote(reference_path)).resolve()
            target_resource = resources[target_path]
            for source_base in (source_document["$id"], source_path.as_uri()):
                registry = registry.with_resource(
                    urljoin(source_base, reference_path),
                    target_resource,
                )
    return registry


def verify_schemas() -> list[Path]:
    """Validate every authored schema and return its paths."""

    schema_paths = sorted(EVENT_SPEC_ROOT.rglob("*.schema.json"))
    if not schema_paths:
        raise ContractVerificationError("No event schemas found")

    identifiers: dict[str, Path] = {}
    for schema_path in schema_paths:
        schema = _validate_schema_document(schema_path)
        if schema_path.resolve() == ENVELOPE_SCHEMA_PATH.resolve():
            _verify_envelope_schema_profile(schema)
        identifier = schema.get("$id")
        if not isinstance(identifier, str) or not identifier:
            raise ContractVerificationError(f"Schema requires a non-empty $id: {schema_path}")
        if identifier in identifiers:
            raise ContractVerificationError(
                f"Duplicate schema $id {identifier}: {identifiers[identifier]} and {schema_path}"
            )
        identifiers[identifier] = schema_path
    return schema_paths


def _profiled_event_envelope(
    event_type: str,
    schema_version: int,
    payload: object,
) -> JsonObject:
    return {
        "event_id": "00000000-0000-4000-8000-000000000001",
        "type": event_type,
        "schema_version": schema_version,
        "stream_session_id": "00000000-0000-4000-8000-000000000002",
        "occurred_at": "2026-01-01T00:00:00Z",
        "payload": payload,
    }


def _verify_active_event_contract(event_type: str, schema_version: int, schema_path: Path) -> None:
    fixture_root = EVENT_FIXTURE_ROOT / event_type / f"v{schema_version}"
    valid_paths = sorted((fixture_root / "valid").glob("*.json"))
    invalid_paths = sorted((fixture_root / "invalid").glob("*.json"))
    if not valid_paths or not invalid_paths:
        raise ContractVerificationError(
            f"Active event requires valid and invalid fixtures: {(event_type, schema_version)}"
        )
    schema = _validate_schema_document(schema_path)
    validator = Draft202012Validator(
        schema,
        registry=_schema_registry(),
        format_checker=FormatChecker(),
    )
    for fixture_path in valid_paths:
        fixture = load_json(fixture_path)
        try:
            validate_json_profile(_profiled_event_envelope(event_type, schema_version, fixture))
        except ContractVerificationError as error:
            raise ContractVerificationError(
                f"Active-event valid fixture violates JSON profile: {fixture_path}: {error}"
            ) from error
        errors = sorted(
            validator.iter_errors(fixture),
            key=lambda error: list(error.path),
        )
        if errors:
            raise ContractVerificationError(
                f"Active-event valid fixture rejected: {fixture_path}: {errors[0].message}"
            )
    for fixture_path in invalid_paths:
        fixture = load_json(fixture_path)
        try:
            validate_json_profile(_profiled_event_envelope(event_type, schema_version, fixture))
        except ContractVerificationError:
            continue
        if validator.is_valid(fixture):
            raise ContractVerificationError(
                f"Active-event invalid fixture accepted: {fixture_path}"
            )


def _verify_catalog_event(event: Any, index: int, identities: set[tuple[str, int]]) -> None:
    if not isinstance(event, dict):
        raise ContractVerificationError(f"Catalog event {index} must be an object")
    required_keys = {"type", "schema_version", "status"}
    allowed_keys = required_keys | {"schema"}
    if not required_keys.issubset(event) or not set(event).issubset(allowed_keys):
        raise ContractVerificationError(f"Invalid keys for catalog event {index}: {sorted(event)}")
    event_type = event["type"]
    schema_version = event["schema_version"]
    status = event["status"]
    if not isinstance(event_type, str) or EVENT_TYPE_PATTERN.fullmatch(event_type) is None:
        raise ContractVerificationError(f"Invalid event type at catalog index {index}")
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or schema_version < 1
        or schema_version > MAX_PORTABLE_JSON_NUMBER
    ):
        raise ContractVerificationError(f"Invalid schema version for {event_type}")
    if status not in ALLOWED_CATALOG_STATUSES:
        raise ContractVerificationError(f"Invalid catalog status for {event_type}: {status}")
    identity = (event_type, schema_version)
    if identity in identities:
        raise ContractVerificationError(f"Duplicate catalog identity: {identity}")
    identities.add(identity)
    if status != "active":
        return
    schema_reference = event.get("schema")
    if not isinstance(schema_reference, str) or not schema_reference:
        raise ContractVerificationError(f"Active event lacks schema: {identity}")
    schema_path = (EVENT_SPEC_ROOT / schema_reference).resolve()
    try:
        schema_path.relative_to(EVENT_SPEC_ROOT.resolve())
    except ValueError as error:
        raise ContractVerificationError(
            f"Catalog schema escapes specs/events: {identity}"
        ) from error
    if not schema_path.is_file():
        raise ContractVerificationError(f"Active event schema does not exist: {schema_path}")
    _validate_schema_document(schema_path)
    if identity not in SUPPORTED_ACTIVE_EVENT_IDENTITIES:
        raise ContractVerificationError(
            f"Active event lacks generated Python/TypeScript payload parity support: {identity}"
        )
    _verify_active_event_contract(event_type, schema_version, schema_path)


def verify_catalog() -> int:
    """Validate the architectural event catalog."""

    catalog = load_json(CATALOG_PATH)
    if not isinstance(catalog, dict):
        raise ContractVerificationError("Event catalog root must be an object")
    expected_top_level = {"catalog_version", "description", "events"}
    if set(catalog) != expected_top_level:
        raise ContractVerificationError(
            f"Event catalog keys must be {sorted(expected_top_level)}, got {sorted(catalog)}"
        )
    if catalog["catalog_version"] != 1:
        raise ContractVerificationError("Only event catalog version 1 is supported")
    events = catalog["events"]
    if not isinstance(events, list) or not events:
        raise ContractVerificationError("Event catalog requires a non-empty events list")

    identities: set[tuple[str, int]] = set()
    for index, event in enumerate(events):
        _verify_catalog_event(event, index, identities)
    return len(events)


def verify_envelope_fixtures() -> tuple[int, int]:
    """Validate shared positive and negative envelope fixtures."""

    schema = load_json(ENVELOPE_SCHEMA_PATH)
    validator = Draft202012Validator(
        schema,
        registry=_schema_registry(),
        format_checker=FormatChecker(),
    )
    valid_paths = sorted((ENVELOPE_FIXTURE_ROOT / "valid").glob("*.json"))
    invalid_paths = sorted((ENVELOPE_FIXTURE_ROOT / "invalid").glob("*.json"))
    if not valid_paths or not invalid_paths:
        raise ContractVerificationError("Envelope fixtures require valid and invalid examples")

    for fixture_path in valid_paths:
        fixture = load_json(fixture_path)
        try:
            validate_json_profile(fixture)
        except ContractVerificationError as error:
            raise ContractVerificationError(
                f"Valid fixture violates JSON profile: {fixture_path}: {error}"
            ) from error
        errors = sorted(
            validator.iter_errors(fixture),
            key=lambda error: list(error.path),
        )
        if errors:
            raise ContractVerificationError(
                f"Valid fixture rejected: {fixture_path}: {errors[0].message}"
            )
    for fixture_path in invalid_paths:
        fixture = load_json(fixture_path)
        try:
            validate_json_profile(fixture)
        except ContractVerificationError:
            continue
        if validator.is_valid(fixture):
            raise ContractVerificationError(f"Invalid fixture accepted: {fixture_path}")
    return len(valid_paths), len(invalid_paths)


def verify_all() -> None:
    schema_paths = verify_schemas()
    event_count = verify_catalog()
    valid_count, invalid_count = verify_envelope_fixtures()
    print(
        "Contract verification passed: "
        f"{len(schema_paths)} schemas, {event_count} catalog entries, "
        f"{valid_count} valid fixtures, {invalid_count} invalid fixtures"
    )


def _fail(error: Exception) -> NoReturn:
    print(f"Contract verification failed: {error}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    try:
        verify_all()
    except ContractVerificationError as error:
        _fail(error)


if __name__ == "__main__":
    main()
