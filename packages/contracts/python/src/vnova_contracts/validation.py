"""Runtime validation backed by the canonical generated schema copy."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import Any
from urllib.parse import unquote, urldefrag, urljoin

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
from pydantic import ValidationError as PydanticValidationError
from referencing import Registry, Resource

from vnova_contracts._base import _snapshot_contract_json
from vnova_contracts.generated.event_envelope_v1 import VNovaEventEnvelopeV1

_ACTIVE_EVENT_REGISTRY_NAME = "active-event-registry.v1.json"
_ACTIVE_EVENT_REGISTRY_KEYS = frozenset(
    {
        "active_events",
        "catalog_source",
        "catalog_source_sha256",
        "catalog_version",
        "payload_schemas",
        "registry_version",
    }
)
_ACTIVE_EVENT_KEYS = frozenset({"schema", "schema_version", "type"})
_PAYLOAD_SCHEMA_KEYS = frozenset({"document", "path", "source_sha256"})
_SHA256_HEX_LENGTH = 64
_MAX_PORTABLE_SCHEMA_VERSION = 9_007_199_254_740_991


class EventEnvelopeValidationError(ValueError):
    """Normalized public error for an invalid event envelope."""

    code = "invalid_event_envelope"

    def __init__(self) -> None:
        super().__init__("Value is not a valid VNova event envelope")


class PublishableEventValidationError(ValueError):
    """Normalized public error for an event that is not safe to publish or consume."""

    code = "invalid_publishable_event"

    def __init__(self) -> None:
        super().__init__("Value is not a publishable VNova event")


class _ActiveEventRegistryError(RuntimeError):
    """Raised when generated active-event authority cannot be loaded exactly."""


@dataclass(frozen=True)
class _ActiveEventRegistry:
    identities: frozenset[tuple[str, int]]
    validators: Mapping[tuple[str, int], Draft202012Validator]


@lru_cache(maxsize=1)
def _event_envelope_validator() -> Draft202012Validator:
    schema_resource = files("vnova_contracts.schemas").joinpath("event-envelope.v1.schema.json")
    schema = json.loads(schema_resource.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _walk_json(value: object) -> Iterable[object]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _safe_registry_path(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise _ActiveEventRegistryError("Generated registry contains an invalid schema path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise _ActiveEventRegistryError("Generated registry schema path is not package-relative")
    return path.as_posix()


def _is_sha256_digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == _SHA256_HEX_LENGTH
        and all(character in "0123456789abcdef" for character in value)
    )


def _registry_lists(raw_registry: object) -> tuple[list[object], list[object]]:
    if (
        not isinstance(raw_registry, dict)
        or set(raw_registry) != _ACTIVE_EVENT_REGISTRY_KEYS
        or raw_registry.get("registry_version") != 1
        or raw_registry.get("catalog_version") != 1
        or raw_registry.get("catalog_source") != "specs/events/event-catalog.v1.json"
    ):
        raise _ActiveEventRegistryError("Generated active-event registry has an invalid header")
    if not _is_sha256_digest(raw_registry.get("catalog_source_sha256")):
        raise _ActiveEventRegistryError("Generated registry has an invalid catalog digest")
    raw_payload_schemas = raw_registry.get("payload_schemas")
    raw_active_events = raw_registry.get("active_events")
    if not isinstance(raw_payload_schemas, list):
        raise _ActiveEventRegistryError("Generated registry payload_schemas must be a list")
    if not isinstance(raw_active_events, list):
        raise _ActiveEventRegistryError("Generated registry active_events must be a list")
    return raw_payload_schemas, raw_active_events


def _schema_identifier(document: Mapping[str, Any]) -> str:
    identifier = document.get("$id")
    if not isinstance(identifier, str) or not identifier:
        raise _ActiveEventRegistryError("Generated payload schema requires a non-empty $id")
    return identifier


def _payload_schema_record(
    raw_schema: object,
) -> tuple[str, dict[str, Any], Resource[Any]]:
    if not isinstance(raw_schema, dict) or set(raw_schema) != _PAYLOAD_SCHEMA_KEYS:
        raise _ActiveEventRegistryError("Generated registry contains an invalid payload schema")
    path = _safe_registry_path(raw_schema.get("path"))
    document = raw_schema.get("document")
    if not _is_sha256_digest(raw_schema.get("source_sha256")) or not isinstance(document, dict):
        raise _ActiveEventRegistryError("Generated registry payload schema is malformed")
    Draft202012Validator.check_schema(document)
    _schema_identifier(document)
    return path, document, Resource.from_contents(document)


def _payload_schema_resources(
    raw_payload_schemas: list[object],
) -> tuple[dict[str, dict[str, Any]], dict[str, Resource[Any]]]:
    documents: dict[str, dict[str, Any]] = {}
    resources: dict[str, Resource[Any]] = {}
    for raw_schema in raw_payload_schemas:
        path, document, resource = _payload_schema_record(raw_schema)
        if path in documents:
            raise _ActiveEventRegistryError("Generated registry payload schema path is duplicated")
        documents[path] = document
        resources[path] = resource
    return documents, resources


def _payload_schema_registry(
    schema_documents: Mapping[str, dict[str, Any]],
    schema_resources: Mapping[str, Resource[Any]],
) -> Registry[Any]:
    json_schema_registry: Registry[Any] = Registry()
    identifiers: set[str] = set()
    for path, resource in schema_resources.items():
        identifier = _schema_identifier(schema_documents[path])
        if identifier in identifiers:
            raise _ActiveEventRegistryError("Generated payload schema $id is duplicated")
        identifiers.add(identifier)
        json_schema_registry = json_schema_registry.with_resource(identifier, resource)
    for source_path, source_document in schema_documents.items():
        source_identifier = _schema_identifier(source_document)
        source_parent = PurePosixPath(source_path).parent
        for node in _walk_json(source_document):
            if not isinstance(node, dict) or not isinstance(node.get("$ref"), str):
                continue
            reference_path, _ = urldefrag(node["$ref"])
            if not reference_path:
                continue
            target_path = (source_parent / unquote(reference_path)).as_posix()
            target_resource = schema_resources.get(target_path)
            if target_resource is None:
                raise _ActiveEventRegistryError(
                    f"Generated registry lacks referenced payload schema: {target_path}"
                )
            json_schema_registry = json_schema_registry.with_resource(
                urljoin(source_identifier, reference_path),
                target_resource,
            )
    return json_schema_registry


def _active_event_record(raw_event: object) -> tuple[tuple[str, int], str]:
    if not isinstance(raw_event, dict) or set(raw_event) != _ACTIVE_EVENT_KEYS:
        raise _ActiveEventRegistryError("Generated registry contains an invalid active event")
    event_type = raw_event.get("type")
    schema_version = raw_event.get("schema_version")
    if (
        not isinstance(event_type, str)
        or not event_type
        or not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or schema_version < 1
        or schema_version > _MAX_PORTABLE_SCHEMA_VERSION
    ):
        raise _ActiveEventRegistryError("Generated active-event identity is malformed")
    return (event_type, schema_version), _safe_registry_path(raw_event.get("schema"))


def _active_event_validators(
    raw_active_events: list[object],
    schema_documents: Mapping[str, dict[str, Any]],
    json_schema_registry: Registry[Any],
) -> _ActiveEventRegistry:
    identities: set[tuple[str, int]] = set()
    validators: dict[tuple[str, int], Draft202012Validator] = {}
    for raw_event in raw_active_events:
        identity, schema_path = _active_event_record(raw_event)
        schema = schema_documents.get(schema_path)
        if identity in identities or schema is None:
            raise _ActiveEventRegistryError(
                "Generated active-event identity lacks one exact payload schema"
            )
        identities.add(identity)
        validators[identity] = Draft202012Validator(
            schema,
            registry=json_schema_registry,
            format_checker=FormatChecker(),
        )
    if set(validators) != identities:
        raise _ActiveEventRegistryError("Generated payload-validator registry is not exact")
    return _ActiveEventRegistry(
        identities=frozenset(identities),
        validators=MappingProxyType(validators),
    )


def _load_active_event_registry() -> _ActiveEventRegistry:
    registry_resource = files("vnova_contracts.registry").joinpath(_ACTIVE_EVENT_REGISTRY_NAME)
    raw_registry = json.loads(registry_resource.read_text(encoding="utf-8"))
    raw_payload_schemas, raw_active_events = _registry_lists(raw_registry)
    schema_documents, schema_resources = _payload_schema_resources(raw_payload_schemas)
    json_schema_registry = _payload_schema_registry(schema_documents, schema_resources)
    return _active_event_validators(
        raw_active_events,
        schema_documents,
        json_schema_registry,
    )


@lru_cache(maxsize=1)
def _active_event_registry() -> _ActiveEventRegistry:
    try:
        return _load_active_event_registry()
    except _ActiveEventRegistryError:
        raise
    except Exception as error:
        raise _ActiveEventRegistryError(
            "Generated active-event authority could not be loaded"
        ) from error


def assert_valid_event_envelope(value: object) -> VNovaEventEnvelopeV1:
    """Validate against JSON Schema and return the frozen generated model."""

    try:
        snapshot = _snapshot_contract_json(value)
        _event_envelope_validator().validate(snapshot)
        return VNovaEventEnvelopeV1.model_validate(snapshot)
    except (
        JsonSchemaValidationError,
        PydanticValidationError,
        RecursionError,
        TypeError,
        ValueError,
    ) as error:
        raise EventEnvelopeValidationError() from error


def is_valid_event_envelope(value: object) -> bool:
    """Return whether value satisfies both schema and generated model validation."""

    try:
        assert_valid_event_envelope(value)
    except EventEnvelopeValidationError:
        return False
    return True


def assert_valid_publishable_event(value: object) -> VNovaEventEnvelopeV1:
    """Return a frozen event only after envelope, activation, and payload validation."""

    try:
        envelope = assert_valid_event_envelope(value)
        identity = (envelope.type, envelope.schema_version)
        active_registry = _active_event_registry()
        if identity not in active_registry.identities:
            raise _ActiveEventRegistryError("Event identity is not active")
        payload_validator = active_registry.validators.get(identity)
        if payload_validator is None:
            raise _ActiveEventRegistryError("Active event lacks an exact payload validator")
        payload_validator.validate(envelope.model_dump(mode="json")["payload"])
        return envelope
    except (
        _ActiveEventRegistryError,
        EventEnvelopeValidationError,
        JsonSchemaValidationError,
        RecursionError,
        TypeError,
        ValueError,
    ) as error:
        raise PublishableEventValidationError() from error


def is_valid_publishable_event(value: object) -> bool:
    """Return whether value is fully valid under an active event contract."""

    try:
        assert_valid_publishable_event(value)
    except PublishableEventValidationError:
        return False
    return True


def _typing_probe(value: dict[str, Any]) -> VNovaEventEnvelopeV1:
    """Keep static analyzers checking the envelope validation return type."""

    return assert_valid_event_envelope(value)


def _publishable_typing_probe(value: dict[str, Any]) -> VNovaEventEnvelopeV1:
    """Keep static analyzers checking the full validation return type."""

    return assert_valid_publishable_event(value)
