# ADR-002: Contract Source And Code Generation

Status: Proposed

Date: 2026-07-17

Sources: `AGENTS.md`, `vnova-review-handoff.md`, ADR-023

## Context

VNova has Python and TypeScript consumers across cloud and local boundaries. The repository previously described both `packages/contracts` and `specs/events` as the event-contract source, which leaves validation, generation, and ownership ambiguous.

Contract drift is a safety and operability risk. A stage host that interprets a wire-contract
message differently from the runtime can play stale or unauthorized media, and a console
generated from stale API definitions can send invalid commands.

## Decision

`specs/events` is the sole hand-authored source of truth for versioned event JSON Schemas and
event catalogs, including envelope and payload schemas.

`packages/contracts` is the distribution and tooling boundary. It will contain generated Python and TypeScript contract libraries, validators, and deterministic generation tooling. Generated files are never edited by hand.

HTTP API contracts originate from FastAPI's OpenAPI document when `control-api` exists. A normalized OpenAPI artifact and its generated TypeScript client will be checked for drift through `packages/contracts`; neither generated artifact becomes a second authoring source.

## Event Contract Rules

- JSON Schema Draft 2020-12 is required.
- Schemas use repository-local references so validation and generation require no network access.
- The current provisional base envelope requires `event_id`, `type`, `schema_version`,
  `stream_session_id`, `occurred_at`, and `payload`; `turn_id` is optional. This exact subject
  shape is not accepted architecture until OD-033 is decided.
- In provisional v1, `schema_version` is a positive integer scoped to an event type.
- Proposed ADR-023 replaces that v1 field in v2 with `event_contract_version`, a positive integer
  scoped to an event type that versions the complete immutable payload/catalog profile.
- Envelope UUIDs use only the lowercase, hyphenated 8-4-4-4-12 representation. URN prefixes, braces, uppercase hex digits, and non-hyphenated variants are rejected even when a UUID library could parse them.
- Event timestamps are calendar-valid UTC RFC 3339 date-times with uppercase `T` and `Z`, a year from `0001` through `9999`, and seconds from `00` through `59`. They contain either no fractional component or exactly six fractional digits whose value is not all zero.
- JSON numbers stay within the inclusive IEEE-754 portable range so Python and TypeScript preserve the same numeric value; larger integers or precision-sensitive decimals use schema-defined strings. Cross-runtime parity means JSON numeric-value equality, not identical numeric lexemes, so equivalent spellings such as `1` and `1.0` do not constitute drift.
- Provisional v1 payload validation is selected by `(type, schema_version)` inside an explicitly
  v1-bound trusted context. Under Proposed ADR-023, v2 validation is selected by
  `(envelope_version, type, event_contract_version)`, whose immutable catalog entry pins the
  exact payload schema identity/digest and every subject, scope, completeness, classification,
  authorization, compatibility, and recovery semantic.
- Authored object schemas default to `additionalProperties: false` unless an extension point is explicitly documented.
- Every active, publishable event type/version has valid and invalid fixtures shared by JSON Schema, Python, and TypeScript validators. `required` catalog entries are non-publishable backlog and do not claim a payload contract.
- Event evolution follows explicit compatibility rules. A consumer must reject unsupported versions rather than silently dropping unknown required semantics.

## Event Subject And Scope Blocker

The required catalog includes environment-, talent-, character-, or viewer-scoped policy, prompt,
and memory facts that may occur without an active `StreamSession`. The current provisional
envelope requires `stream_session_id` for every event, so it cannot represent all required facts
without fabricating a session identity.

ADR-023 now proposes one v2 domain-event envelope with a catalog-fixed typed primary scope, one
authoritative aggregate subject, `(aggregate_version, event_index)` ordering, a PostgreSQL-backed
transition-completeness manifest/high-water contract, correlation/causation, authorization
filtering, compatibility, and privacy rules. A simple nullable session field without that
reviewed model is not a resolution. Until OD-033 has a valid human disposition accepting ADR-023
or a compatible replacement:

- this ADR cannot be accepted;
- no producer may invent `stream_session_id`;
- no affected catalog entry may become active; and
- schemas, generated distributions, fixtures, and consumers remain provisional review evidence.

OD-017 must separately define compatibility, catalog state transitions, deprecation, rollback,
and removal before this ADR can be accepted or an event activated. ADR-002 and ADR-023 must be
accepted against the same immutable reviewed subject and describe one compatible model.

## Non-Event Contract Blocker

Stage-host tasks, restrictive controls, acknowledgements, heartbeat/clock samples, reconnect, and
reconciliation are not domain events. OD-021 must select one language-neutral hand-authored source
and deterministic generation/validation for Python, TypeScript, and the selected stage-host
language, with no parallel handwritten DTOs. This ADR cannot be accepted while OD-021 remains
OPEN; all dependent protocols remain disabled.

## Canonical JSON Runtime Profile

The envelope schema declares an `x-vnova-json-profile` annotation for constraints that JSON Schema does not enforce portably. Contract tooling and the generated Python and TypeScript runtime validators enforce this profile before returning a trusted value:

- every object key and string value must be a Unicode scalar-value sequence; unpaired UTF-16 surrogates are rejected;
- negative zero is normalized to positive zero;
- container depth is at most `64`, counting a root object or array as depth `1`;
- a document contains at most `10000` JSON value nodes, including its root and container values; object keys do not add nodes;
- the combined UTF-8 encoding size of all object keys and string values is at most `1048576` bytes.

The ceilings are inclusive. Exceeding any ceiling rejects the whole document rather than partially accepting or truncating it. The profile values and their counting semantics are **Proposed** production contract decisions: they require the same protected human review as ADR-002 and must not be treated as approved defaults before this ADR is accepted.

## Deterministic Generation

The contract gate will:

1. Validate schema syntax, unique `$id` values, and local `$ref` closure.
2. Validate all fixtures against their declared type and version.
3. Generate Python and TypeScript contracts from a clean tree.
4. Run each language's type checker and contract tests.
5. Validate every accepted fixture after canonical serialize-and-parse round trips in both runtimes, comparing normalized JSON structures with numeric-value equality.
6. Generate a second time and require byte-for-byte stable output.
7. Require `git diff --exit-code` after generation.

Tool versions will be pinned in lockfiles. Generation metadata may record the source schema digest and generator version, but must not include nondeterministic timestamps.

## Ownership And Enforcement

- `specs/events`, `packages/contracts`, generator configuration, and contract fixtures require human review.
- CI will expose stable required checks for schema validation, codegen drift, and cross-language fixture parity.
- Changes that remove or rename fields require an explicit compatibility assessment and an ADR when they alter a public or safety-relevant semantic.

## Consequences

- There is one schema authoring location and no generated-source ambiguity.
- Runtime packages depend on generated contract libraries rather than parsing ad hoc dictionaries.
- Runtime validation supplements JSON Schema for the canonical JSON profile; using a schema validator alone is not sufficient to establish a trusted contract value.
- Contract tooling must exist before event producers or consumers are implemented.
- OpenAPI generation cannot be completed until the API scaffold exists, but its ownership and drift direction are fixed now.
- ADR-002 acceptance is blocked by OD-017, OD-021, and OD-033; ADR-023 is a Proposed companion,
  and draft schemas/code generation cannot close those human decisions.

## OPEN Decisions

- OD-017: event compatibility, catalog activation/deprecation, rollback, and removal.
- OD-021: canonical non-event contract source and deterministic multi-language generation.
- OD-033: acceptance or replacement of ADR-023's typed event scope/subject,
  aggregate-version/event-index ordering and completeness, correlation, authorization,
  compatibility, and privacy.
- Canonical JSON profile values and any future resource-limit change require protected ADR-002
  review; no value becomes a production default merely because the scaffold enforces it.
