# Event Specifications

Status: Canonical schema skeleton; proposed profile requires protected human review

This directory is the sole hand-authored source of truth for VNova event JSON Schemas and event
catalogs. `packages/contracts` will distribute generated validators and types.

## Layout

```text
specs/events/event-envelope.v1.schema.json     base transport envelope
specs/events/event-catalog.v1.json             required event type registry and delivery status
specs/events/payloads/                         governed event-specific payload schemas
packages/contracts/**/active-event-registry.v1.json
                                                generated active-only runtime projection
tests/contracts/fixtures/events/               shared valid and invalid payload examples
```

## Rules

- JSON Schema Draft 2020-12.
- Offline, repository-local `$ref` values only.
- One event type and positive integer schema version selects one payload schema.
- Envelope UUIDs use lowercase hex digits in the hyphenated 8-4-4-4-12 representation only.
- Timestamps are calendar-valid UTC RFC 3339 values with uppercase `T`/`Z`, year `0001`-`9999`, seconds `00`-`59`, and either no fraction or exactly six fractional digits whose value is not all zero.
- JSON numbers stay within the inclusive IEEE-754 portable range `[-9007199254740991, 9007199254740991]`; larger integers or precision-sensitive decimals use an event-specific string encoding. Python/TypeScript parity uses JSON numeric-value equality rather than requiring an identical numeric spelling.
- Strict objects unless a non-empty `x-vnova-extension-point` documents why open keys are required.
- A producer may publish only catalog entries whose status is `active` and whose payload schema and fixtures pass the contract gate.
- Entries marked `required` in the catalog are architectural backlog, not publishable contracts.
- Active payload fixtures live at `tests/contracts/fixtures/events/<EventType>/v<schema_version>/{valid,invalid}` and both sets must be non-empty.

## Canonical JSON Profile

`event-envelope.v1.schema.json` declares the proposed `x-vnova-json-profile`. Contract tooling and both runtime libraries enforce it because generic JSON Schema validators treat this extension as an annotation:

- object keys and string values contain Unicode scalar values only; unpaired surrogates are invalid;
- negative zero is normalized to positive zero;
- maximum container depth: `64` inclusive, counting a root object or array as depth `1`;
- maximum JSON value nodes: `10000`, counting the root and containers but not object keys;
- maximum combined UTF-8 size of all object keys and string values: `1048576` bytes.

All maxima are inclusive. The limits, normalization, and counting rules remain **Proposed** and require protected human review through ADR-002. They are implemented as provisional contract-foundation evidence, not as silently approved production defaults.

The current envelope intentionally allows an arbitrary object payload because event-specific
dispatch validation is generated from the catalog. The generator filters only `active` identities,
sorts them by `(type, schema_version)`, and embeds the transitive local schema dependency set needed
to construct the exact payload validators in each runtime distribution.

An envelope-only validation is never sufficient for publishing or consuming an event. Full
validation must first validate the envelope, then find the identity in the generated active
registry, and finally accept the payload with the validator selected by that exact identity.
Missing activation or validator parity fails closed. Because the canonical catalog currently has
no `active` entries, every full-event validation rejects; entries marked `required` remain backlog
only.
