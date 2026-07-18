# VNova Contracts Package Boundary

Status: Phase 1 contract foundation implemented; protected human review required

This protected path contains deterministic contract tooling plus generated Python and TypeScript libraries for the event envelope.

The canonical hand-authored event source is `specs/events`. Generated files under this package will never be edited manually. HTTP client artifacts will be generated from the normalized FastAPI OpenAPI document after `control-api` exists.

Implemented capabilities:

- Draft 2020-12 schema validation with offline `$ref` resolution;
- deterministic Python and TypeScript generation;
- shared valid/invalid fixtures;
- cross-language parity tests;
- a deterministic `active-event-registry.v1.json` projection generated from the canonical catalog
  and embedded identically in both distributions;
- separate envelope and publishable-event validation APIs, with publishable validation requiring
  both an active `(type, schema_version)` identity and the exact payload validator selected by that
  identity;
- canonical lowercase, hyphenated UUIDs and canonical UTC timestamps with uppercase `T`/`Z`, no leap seconds, and either no fraction or a nonzero six-digit fractional value;
- detached, deeply immutable runtime values: Python exposes `FrozenJsonObject`/`FrozenJsonValue`, while TypeScript assertions return a frozen clone rather than narrowing the mutable source object;
- one-shot snapshots of untrusted inputs before schema/model validation, plus a shared portable IEEE-754 number range and JSON numeric-value comparison semantics to prevent Python/TypeScript round-trip divergence;
- rejection of unpaired Unicode surrogates, normalization of negative zero to positive zero, and matching depth, node-count, and UTF-8 string budgets in contract tooling and both runtimes;
- manifest v2 provenance for both the envelope schema and event catalog:
  repository-relative workspace artifacts and package-relative Python/npm artifacts with SHA-256
  digests;
- codegen drift detection;
- rejection and cleanup of unexpected stale generated artifacts.

TypeScript validation clones untrusted input through property descriptors before AJV sees it. Frozen object records intentionally use a null prototype to avoid inherited-property hazards; consumers must use `Object.hasOwn(value, key)` rather than calling `value.hasOwnProperty(...)`. `isValidEventEnvelope` returns only a boolean because it does not replace or freeze the caller's original value; `assertValidEventEnvelope` is the API that returns the trusted immutable clone.

Envelope validation is transport-only:

- Python: `is_valid_event_envelope` / `assert_valid_event_envelope`;
- TypeScript: `isValidEventEnvelope` / `assertValidEventEnvelope`.

Publishing or consuming requires the full contract boundary:

- Python: `is_valid_publishable_event` / `assert_valid_publishable_event`;
- TypeScript: `isValidPublishableEvent` / `assertValidPublishableEvent`.

The assertion APIs normalize every full-validation rejection to
`PublishableEventValidationError` with code `invalid_publishable_event`; predicates return only
`false`. The validator first accepts the immutable transport envelope, then requires the generated
active identity and its exact generated payload-schema validator. A missing catalog verdict,
missing validator, malformed registry, or payload mismatch therefore fails closed. The current
catalog has no `active` entries, so every full-event input is rejected even when its envelope is
valid. This registry is quarantined Stage B evidence and does not activate any event contract.

Each embedded payload schema record carries `source_sha256`, the digest of its normalized canonical
source file. It is provenance, not a runtime self-signature: the runtime validates registry shape,
portable identity bounds, unique non-empty schema IDs, reference closure, and exact validator
selection, while package/archive verification checks the SHA-256 digest of the complete generated
registry against each manifest. A consumer that bypasses the verified build/install path also
bypasses that artifact-integrity gate; package-manager integrity and the release artifact verifier
remain required controls.

The proposed canonical JSON profile caps container depth at `64` (a root object or array is depth `1`), JSON value nodes at `10000`, and the combined UTF-8 size of all object keys and string values at `1048576` bytes. Node counting includes the root and container values but not object keys. All limits are inclusive; an over-budget value is rejected without truncation. String keys and values must contain Unicode scalar values only. Cross-language parity compares JSON numbers by numeric value, while trusted outputs normalize negative zero to positive zero.

These profile semantics and ceilings are protected ADR-002 decisions. The implementation is provisional architecture-foundation evidence and does not make them approved production defaults; human acceptance of ADR-002 is still required.

Still required before the broader contract platform is complete:

- documented compatibility and deprecation behavior;
- reviewed payload schemas and fixtures before catalog entries become `active`;
- normalized OpenAPI generation and drift checks after `control-api` exists.

No catalog entry may become `active` until OD-017 is closed with an accepted
compatibility/deprecation policy and generated Python/TypeScript payload parity is implemented
and reviewed.

All changes require human review under `CODEOWNERS`.
