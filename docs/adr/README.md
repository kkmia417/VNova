# Architecture Decision Records

ADRs capture decisions that are difficult to reverse, cross responsibility boundaries, or affect safety, privacy, contracts, data, deployment, and operations.

## Status Model

- `Proposed`: written for review; feature/runtime implementation and irreversible changes that depend on it remain blocked. Reversible, non-runtime review scaffolds explicitly permitted by repository governance may be built to prove enforceability, but they do not activate a capability or make the proposal binding.
- `Accepted`: approved and binding.
- `Superseded`: replaced by a named ADR; retained for history.
- `Rejected`: considered and intentionally not adopted.

An ADR may contain explicitly OPEN parameters while its invariant decision is accepted. Code must not embed an OPEN parameter as a production default.

Changing an ADR status does not close an Open Decision by implication. When an ADR acceptance
depends on an OD, the protected human outcome must also exist in the
[Open Decision Disposition Register](../governance/open-decision-dispositions.md) for the same
immutable reviewed subject, and the ADR status/wording, retained OPEN scope, disabled
capabilities, and disposition record must agree. A missing, invalidated, deferred, or
inconclusive disposition keeps the dependent ADR/capability blocked.

## Index

| ADR                                                                    | Decision                                              | Status                                      |
| ---------------------------------------------------------------------- | ----------------------------------------------------- | ------------------------------------------- |
| [ADR-001](0001-monorepo-and-deployment-boundaries.md)                  | Monorepo and deployment boundaries                    | Proposed; human review required             |
| [ADR-002](0002-contract-source-and-code-generation.md)                 | Contract source and code generation                   | Proposed; human review required             |
| [ADR-003](0003-stream-session-segment-and-turn-lifecycle.md)           | Session, segment, and turn lifecycle                  | Proposed; human review required             |
| [ADR-004](0004-postgresql-outbox-and-redis-streams.md)                 | PostgreSQL outbox and Redis Streams                   | Proposed; migration and human review needed |
| [ADR-007](0007-provider-gateway-and-fallback-isolation.md)             | Provider gateway and fallback isolation               | Proposed; provider choices OPEN             |
| [ADR-008](0008-safety-gate-enforcement.md)                             | Safety gate enforcement                               | Proposed; human review required             |
| [ADR-010](0010-approved-media-and-tts-pipeline.md)                     | Approved media and TTS pipeline                       | Proposed; media profile OPEN                |
| [ADR-011](0011-stage-host-wire-protocol-and-clock-synchronization.md)  | Stage-host protocol and clock synchronization         | Proposed; security and timing profile OPEN  |
| [ADR-015](0015-layered-emergency-stop.md)                              | Layered emergency stop                                | Proposed; SLO and reconciliation OPEN       |
| [ADR-016](0016-stage-host-and-cloud-local-topology.md)                 | Stage host and cloud/local topology                   | Accepted                                    |
| [ADR-017](0017-data-retention-privacy-and-pii.md)                      | Data retention, privacy, and PII                      | Accepted; retention durations OPEN          |
| [ADR-018](0018-latency-budget-and-streaming-strategy.md)               | Latency budget and streaming strategy                 | Proposed; numeric targets OPEN              |
| [ADR-019](0019-authentication-authorization-and-operator-roles.md)     | Authentication, authorization, operator roles         | Proposed; identity and role profile OPEN    |
| [ADR-020](0020-mode-transition-and-degradation-matrix.md)              | Mode transition and degradation matrix                | Proposed; capability matrix OPEN            |
| [ADR-021](0021-broadcast-surface-inventory-and-overlay-policy.md)      | Broadcast surfaces and overlay policy                 | Proposed; surface policies OPEN             |
| [ADR-022](0022-voice-rights-and-talent-licensing-metadata.md)          | Voice rights and talent licensing metadata            | Proposed; human legal review required       |
| [ADR-023](0023-event-subject-scope-correlation-and-ordering.md)        | Event contract, scope, order, and completeness        | Proposed; foundation review required        |
| [ADR-024](0024-versioned-configuration-and-scoped-activation.md)       | Immutable configuration, eligibility, and activation  | Proposed; domain/data review required       |
| [ADR-025](0025-session-actor-ownership-command-ingress-and-fencing.md) | Session actor ownership, command ingress, and fencing | Proposed; runtime/data review required      |
| [ADR-026](0026-opaque-audit-references-for-deletable-personal-data.md) | Opaque audit references for deletable personal data   | Proposed; privacy/security review required  |

The external handoff's implementation sequence also references ADR-006, but neither that ADR nor
enough authoritative topic metadata to reconstruct it exists in the repository. OD-020 requires a
human to restore its source or explicitly retire and remap that historical reference. No unknown
decision is invented from the number alone. See the
[open decision register](../architecture/open-decisions.md).

## Authoring Rules

Every ADR must include context, decision, enforcement or verification where applicable, consequences, status, and explicit OPEN decisions. Schema migrations must cite the accepted ADR that authorizes the schema change.

An ADR's `Sources` section records provenance and informative cross-references; it is not an
acceptance-prerequisite graph. Every new or substantively revised ADR must separately name its
`Acceptance prerequisites`, `Atomic review cohort`, and `Implementation gates`, using `None` when
the category is intentionally empty. Until older ADRs are migrated to those explicit fields, only
their normative decision text, OPEN-decision blockers, and protected governance matrices define
dependencies; reciprocal `Sources` references never create or satisfy an acceptance edge.

Changing an accepted ADR requires a new superseding ADR unless the edit is purely corrective and does not alter the decision.
