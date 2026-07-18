"""Shared runtime behavior for generated VNova contract models."""

from __future__ import annotations

import math
import re
import warnings
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Self, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationInfo,
    field_serializer,
    field_validator,
    model_validator,
)

type JsonPrimitive = None | bool | int | float | str
type FrozenJsonValue = (
    JsonPrimitive | tuple["FrozenJsonValue", ...] | Mapping[str, "FrozenJsonValue"]
)
type FrozenJsonObject = Mapping[str, FrozenJsonValue]

MAX_PORTABLE_JSON_NUMBER = 9_007_199_254_740_991
MAX_CONTAINER_DEPTH = 64
MAX_JSON_NODES = 10_000
MAX_UTF8_STRING_BYTES = 1_048_576
CANONICAL_UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
CANONICAL_TIMESTAMP_PATTERN = re.compile(
    r"^(?!0000)[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])"
    r"T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    r"(?:\.(?!000000)[0-9]{6})?Z$"
)
_NOT_JSON_SCALAR = object()
_ASCII_MAX = 0x7F
_TWO_BYTE_UTF8_MAX = 0x7FF
_BMP_MAX = 0xFFFF
_SURROGATE_MIN = 0xD800
_SURROGATE_MAX = 0xDFFF


@dataclass
class _JsonProfileState:
    active_containers: set[int] = field(default_factory=set)
    nodes: int = 0
    utf8_string_bytes: int = 0


def _record_string(value: str, state: _JsonProfileState) -> str:
    remaining = MAX_UTF8_STRING_BYTES - state.utf8_string_bytes
    if len(value) > remaining:
        raise ValueError("Contract strings exceed the UTF-8 byte budget")
    for character in value:
        code_point = ord(character)
        if _SURROGATE_MIN <= code_point <= _SURROGATE_MAX:
            raise ValueError("Contract strings must contain only Unicode scalar values")
        width = (
            1
            if code_point <= _ASCII_MAX
            else 2
            if code_point <= _TWO_BYTE_UTF8_MAX
            else 3
            if code_point <= _BMP_MAX
            else 4
        )
        state.utf8_string_bytes += width
        if state.utf8_string_bytes > MAX_UTF8_STRING_BYTES:
            raise ValueError("Contract strings exceed the UTF-8 byte budget")
    return value


def _canonical_json_scalar(
    value: object,
    state: _JsonProfileState,
    subject: str,
) -> JsonPrimitive | object:
    if value is None or type(value) is bool:
        return value
    if type(value) is int:
        if abs(value) > MAX_PORTABLE_JSON_NUMBER:
            raise ValueError(f"{subject} numbers must use the portable IEEE-754 range")
        return value
    if type(value) is float:
        if not math.isfinite(value) or abs(value) > MAX_PORTABLE_JSON_NUMBER:
            raise ValueError(f"{subject} numbers must use the portable IEEE-754 range")
        return 0.0 if value == 0.0 else value
    if type(value) is str:
        return _record_string(value, state)
    return _NOT_JSON_SCALAR


def _snapshot_contract_json(
    value: object,
    state: _JsonProfileState | None = None,
    depth: int = 1,
) -> object:
    """Detach exact JSON builtins and enforce the cross-runtime resource profile."""

    state = state or _JsonProfileState()
    state.nodes += 1
    if state.nodes > MAX_JSON_NODES:
        raise ValueError("Contract input exceeds the JSON node budget")

    scalar = _canonical_json_scalar(value, state, "Contract")
    if scalar is not _NOT_JSON_SCALAR:
        return scalar
    if type(value) not in {dict, list}:
        raise ValueError("Contract input must contain exact built-in JSON values")
    if depth > MAX_CONTAINER_DEPTH:
        raise ValueError("Contract input exceeds the container-depth budget")

    identity = id(value)
    if identity in state.active_containers:
        raise ValueError("Contract input cannot contain cycles")
    state.active_containers.add(identity)
    try:
        if type(value) is list:
            if list.__len__(value) > MAX_JSON_NODES - state.nodes:
                raise ValueError("Contract input exceeds the JSON node budget")
            return [
                _snapshot_contract_json(child, state, depth + 1) for child in list.__iter__(value)
            ]

        snapshot: dict[str, object] = {}
        object_value = cast(dict[object, object], value)
        for key, child in dict.items(object_value):
            if type(key) is not str:
                raise ValueError("Contract object keys must be exact strings")
            canonical_key = _record_string(key, state)
            snapshot[canonical_key] = _snapshot_contract_json(child, state, depth + 1)
        return snapshot
    finally:
        state.active_containers.remove(identity)


def _freeze_json(
    value: object,
    state: _JsonProfileState | None = None,
    depth: int = 1,
) -> FrozenJsonValue:
    """Freeze Pydantic-parsed JSON while preserving the canonical resource profile."""

    state = state or _JsonProfileState()
    state.nodes += 1
    if state.nodes > MAX_JSON_NODES:
        raise ValueError("Contract payload exceeds the JSON node budget")
    scalar = _canonical_json_scalar(value, state, "Contract payload")
    if scalar is not _NOT_JSON_SCALAR:
        return cast(JsonPrimitive, scalar)
    if not isinstance(value, Mapping | list | tuple):
        raise ValueError(f"Contract payload contains a non-JSON value: {type(value).__name__}")
    if depth > MAX_CONTAINER_DEPTH:
        raise ValueError("Contract payload exceeds the container-depth budget")

    identity = id(value)
    if identity in state.active_containers:
        raise ValueError("Contract payload cannot contain cycles")
    state.active_containers.add(identity)
    try:
        if isinstance(value, Mapping):
            frozen: dict[str, FrozenJsonValue] = {}
            for key, child in value.items():
                if type(key) is not str:
                    raise ValueError("Contract payload object keys must be strings")
                canonical_key = _record_string(key, state)
                frozen[canonical_key] = _freeze_json(child, state, depth + 1)
            return MappingProxyType(frozen)
        if len(value) > MAX_JSON_NODES - state.nodes:
            raise ValueError("Contract payload exceeds the JSON node budget")
        return tuple(_freeze_json(child, state, depth + 1) for child in value)
    finally:
        state.active_containers.remove(identity)


def _thaw_json(value: FrozenJsonValue) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw_json(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(child) for child in value]
    return value


class VNovaContractModel(BaseModel):
    """Deeply immutable contract model with canonical transport scalars."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="before")
    @classmethod
    def snapshot_json_input(cls, value: object) -> object:
        if isinstance(value, cls):
            return value
        if type(value) is not dict:
            raise ValueError("Contract model input must be an exact JSON object")
        return _snapshot_contract_json(value)

    @field_validator(
        "event_id",
        "stream_session_id",
        "turn_id",
        mode="before",
        check_fields=False,
    )
    @classmethod
    def require_canonical_uuid(cls, value: object, info: ValidationInfo) -> str:
        if type(value) is not str or CANONICAL_UUID_PATTERN.fullmatch(value) is None:
            raise ValueError(f"{info.field_name} must use the canonical lowercase UUID form")
        return value

    @field_validator("type", mode="before", check_fields=False)
    @classmethod
    def require_exact_event_type(cls, value: object) -> str:
        if type(value) is not str:
            raise ValueError("type must be an exact JSON string")
        return value

    @field_validator("schema_version", mode="before", check_fields=False)
    @classmethod
    def require_exact_schema_version(cls, value: object) -> int:
        if type(value) is not int:
            raise ValueError("schema_version must be an exact JSON integer")
        return value

    @field_validator("occurred_at", mode="before", check_fields=False)
    @classmethod
    def require_canonical_utc(cls, value: object) -> str:
        if type(value) is not str or CANONICAL_TIMESTAMP_PATTERN.fullmatch(value) is None:
            raise ValueError("occurred_at must use the canonical UTC timestamp form")
        return value

    @field_validator("payload", mode="before", check_fields=False)
    @classmethod
    def require_exact_payload_object(cls, value: object) -> dict[str, object]:
        if type(value) is not dict:
            raise ValueError("payload must be an exact JSON object")
        return value

    @model_validator(mode="after")
    def freeze_payload(self) -> Self:
        if "payload" in type(self).model_fields:
            payload = object.__getattribute__(self, "payload")
            object.__setattr__(self, "payload", _freeze_json(payload))
        return self

    @field_serializer("payload", check_fields=False)
    def serialize_payload(self, value: FrozenJsonValue) -> object:
        return _thaw_json(value)

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Serialize a schema-valid object by omitting absent optional model fields."""

        kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)

    def model_dump_json(self, **kwargs: Any) -> str:
        """Serialize canonical JSON that remains valid against the source schema."""

        kwargs["exclude_none"] = True
        return super().model_dump_json(**kwargs)

    def model_copy(
        self,
        *,
        update: Mapping[str, Any] | None = None,
        deep: bool = False,
    ) -> Self:
        """Return a fully revalidated copy; Pydantic's unchecked update path is forbidden."""

        del deep
        data = self.model_dump(mode="json")
        if update is not None:
            data.update(update)
        return type(self).model_validate(data)

    def copy(
        self,
        *,
        include: Any = None,
        exclude: Any = None,
        update: Mapping[str, Any] | None = None,
        deep: bool = False,
    ) -> Self:
        """Retain Pydantic's deprecated API without its unchecked update behavior."""

        warnings.warn("copy is deprecated; use model_copy", DeprecationWarning, stacklevel=2)
        del deep
        data = self.model_dump(mode="json", include=include, exclude=exclude)
        if update is not None:
            data.update(update)
        return type(self).model_validate(data)

    @classmethod
    def model_construct(cls, _fields_set: set[str] | None = None, **values: Any) -> Self:
        """Disable Pydantic's trusted-data constructor at the public contract boundary."""

        del _fields_set, values
        raise TypeError("model_construct is disabled for validated VNova contracts")
