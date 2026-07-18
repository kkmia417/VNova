# ADR-001: Monorepo And Deployment Boundaries

Status: Proposed

Date: 2026-07-17

Sources: `AGENTS.md`, `vnova-review-handoff.md`

## Context

VNova combines cloud control, long-lived per-session orchestration, a local Windows broadcast agent, and an internal operator console. Treating every conceptual plane as a separately deployed service would add failure modes and operational burden without improving the initial safety boundary.

The repository must still make responsibility and dependency direction explicit so that an in-process shortcut cannot bypass approval, provider, data, or local-rig boundaries.

## Decision

VNova is a polyglot monorepo with four initial deployed surfaces:

- `apps/control-api`
- `apps/session-runtime`
- `apps/stage-host`
- `apps/operator-console`

The historical handoff refers to five conceptual planes, but their names and dependency
directions are not present in the repository. This ADR cannot be accepted until OD-018
either restores that taxonomy or retires the term in favor of the explicit responsibility
and dependency boundaries below. No implementation authority may be inferred from an
unnamed plane. Cloud runtime modules may be separated later only through a superseding ADR
with measured operational triggers.

Shared protected boundaries live under:

- `packages/contracts`: generated cross-language contracts and deterministic tooling;
- `packages/safety`: exclusive approval-minting boundary;
- `specs/events`: canonical hand-authored event schemas and event catalogs;
- `tests/red-team`: safety regression corpus.

Provider gateways remain owned by the surface that executes them and are isolated as explicit gateway modules. Provider SDKs cannot become general shared dependencies.

## Dependency Direction

- Deployable surfaces may depend on public generated contracts.
- The runtime may invoke the public safety boundary; safety does not depend on runtime orchestration.
- TTS/media modules receive approved identifiers and cannot depend on candidate-generation modules.
- The operator console depends on generated API/event clients, never backend implementation modules.
- The stage host depends on local adapters and generated wire contracts; it never depends on Redis or cloud persistence code.
- Test helpers cannot become production dependencies.
- Cross-language sharing occurs through schemas and generated artifacts, not duplicated handwritten models.

These rules will be enforced by import-linter, dependency-cruiser, Python AST and TypeScript compiler-AST checks for protected symbols, contract parity tests, and CODEOWNERS.

## Deployment Consequences

- `control-api` is stateless.
- `session-runtime` is long-lived and owns one logical actor per `StreamSession`.
- `stage-host` is required on the streaming PC and is the sole `SpeechTask` consumer.
- `operator-console` is internal-only and deployed separately behind SSO/VPN.
- PostgreSQL is the system of record; Redis Streams is transport only.

The cloud deployment target and stage-host implementation language remain OPEN and are tracked separately because they do not change these boundaries.

## Quality Consequences

- Root tooling must support reproducible Python and TypeScript workspaces without forcing a single runtime language.
- Each deployable has an explicit health model, configuration contract, and release artifact.
- Shared packages must remain small and contract-oriented; dumping general utilities into a common package is forbidden.
- A new deployable or a plane-to-service split requires an ADR with load, isolation, ownership, and failure-domain evidence.
