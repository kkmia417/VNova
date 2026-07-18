# ADR-004: PostgreSQL Outbox And Redis Streams

Status: Proposed

Date: 2026-07-17

Sources: `AGENTS.md`, `vnova-review-handoff.md`, ADR-002, ADR-003, ADR-017, ADR-023,
ADR-025

This ADR is non-binding while its status is `Proposed`. It authorizes no migration or
runtime event producer until it and the applicable schema ADR are accepted.

## Context

VNova needs low-latency notifications between runtime modules without making a transient
transport responsible for durable session state, safety evidence, or incident
reconstruction. A database commit followed by an unrelated publish can lose an event when
the process fails between those operations. Publishing first can expose a transition that
never committed.

Redis Streams is useful transport, but its retention, consumer offsets, and availability
cannot become recovery truth. PostgreSQL is already the authoritative store for session
state, turn state, safety decisions, audit metadata, and the domain event log. Viewer-memory
content must remain separate from both audit and transport payloads under ADR-017.

## Decision

PostgreSQL is the system of record. Redis Streams is an at-least-once notification transport
behind a thin internal `EventBus` port.

Every durable subject transition governed by ADR-023 lane completeness that advances an aggregate
version commits, in one PostgreSQL transaction:

1. the authoritative state mutation;
2. its required audit metadata;
3. zero or more distinct immutable `DomainEventRecord` facts;
4. exactly one immutable `EventTransitionManifest` for the new aggregate version, including a
   zero-count manifest when no event is emitted, and every authorized lane consumer's
   expected-delivery subset or explicit zero/empty attestation;
5. exactly one immutable `OutboxRecord` publication intent for each domain-event record.

The transaction is the publication boundary. No consumer may observe an outbox event as
committed unless the state it describes committed with it. An operation that requires one or
more events but cannot write every event/outbox pair does not commit its state transition. A
transition that emits no event still cannot commit without its zero-count manifest and required
expected-delivery attestations.

### Safety-Direction Actuation During Database Failure

The transaction rule governs durable domain transitions; it must not delay an immediate
restrictive safety effect. Cloud freeze, emergency stop, effective-mode decrease, cancellation,
and fail-closed admission denial first actuate the strongest available process-local restriction
even when PostgreSQL or the outbox is unavailable.

- The process-local restriction is explicitly `uncommitted_restrictive`, not authoritative
  durable success and not a published domain event.
- It may stop, mute, cancel, reject, invalidate local capabilities, or reduce autonomy. It may not
  approve, dispatch, resume, raise mode, widen authority, or claim a durable transition.
- The runtime retries persistence of the restrictive state, audit metadata, and all required
  outbox records as one transaction. It remains frozen while durability or peer reconciliation
  is uncertain.
- A process restart, actor takeover, or ownership transfer with unresolved restrictive evidence
  enters ADR-025 recovery hold and recovers to the accepted safe/frozen state; it never
  reconstructs permission from Redis or a cached ownership lease.
- Resume or any higher-autonomy action is prohibited until PostgreSQL is available, the
  authoritative transition and evidence commit, and required cloud/local reconciliation
  succeeds.
- Local hard e-stop remains stage-host-owned and independent of PostgreSQL; its offline evidence
  is reconciled later under ADR-015/016.

This is a narrow safety exception to commit-before-effect, not permission for a second system of
record. No notification may describe the restriction as durably committed until its PostgreSQL
transaction succeeds.

The outbox publisher reads committed records, publishes their canonical envelope to Redis
Streams, and records delivery attempts and acknowledgements in PostgreSQL. A crash after
Redis accepts a publish but before PostgreSQL records the acknowledgement can produce a
duplicate. Consumers therefore treat delivery as at least once and deduplicate by stable
event identity.

### Authoritative Records

- Current aggregate rows are authoritative for current state.
- ADR-025 ownership, durable command, effect-attempt, and timer-occurrence records are separate
  PostgreSQL authorities. A command receipt, claim, acknowledgement, or wake-up is not a domain
  event and Redis cannot make it accepted or current.
- Immutable candidate, decision, approval, audit, domain-event, manifest, and outbox lineage in
  PostgreSQL explains how that state was reached.
- The canonical event envelope follows ADR-002, accepted ADR-023 or its replacement, and the
  reviewed schemas/catalog in `specs/events`.
- The immutable `EventContractProfile` is separate from append-only
  `EventCatalogEligibility`. A domain-event record preserves the original `event_id`, complete
  immutable profile identity/digest, emission-time active state plus catalog epoch/transition
  evidence, typed environment/primary scope, aggregate subject, aggregate version/event index,
  transition count/manifest identity, `occurred_at`, payload schema identity/digest, and
  catalog-fixed historical data classification.
- `DomainEventRecord` and `OutboxRecord` are distinct logical records in an exact one-to-one
  relationship for each emitted event. The outbox references the event identity/digest and fixes
  immutable publication intent; claims, attempts, and acknowledgements are separate. Physical
  co-location requires a linked migration ADR proving that neither authority or lifecycle is
  collapsed.
- Redis stream entry IDs, consumer-group offsets, in-memory queues, and publisher cursors
  are operational metadata only.
- Replay and incident reconstruction read PostgreSQL. They never infer missing truth from
  the current contents of Redis.

### Publication And Ordering

The publisher may process unrelated subject lanes concurrently. For domain events it preserves
the lexicographic `(aggregate_version, event_index)` causal position within every
catalog-declared `(scope.environment_id, subject.kind, subject.identity)` lane whose consumer
profile requires ordered application. Cross-lane ordering is not implied; every consumer also
handles duplicates, delay, and the reordering allowed by its declared profile.

The transition manifest and authorized per-consumer expected-delivery/high-water evidence
proposed by ADR-023 commit for every new aggregate version with state and zero-or-more event/outbox
pairs. A zero-count manifest is authoritative evidence that a transition intentionally emitted no
event. A publisher does not infer transition completeness from Redis. A consumer profile that
requires order cannot advance a dependent projection until every manifest version through its
high-water, including zero-event and filtered-empty attestations, is durable and complete.

The identifier-only speech/avatar task and control path is not a domain-event envelope. Its
session-bound command/task ordering remains governed by ADR-011 and OD-021. Neither the event
envelope nor Redis order may replace that wire protocol's accepted sequence, epoch, expiry,
signature, and acknowledgement rules.

An event is published with the same canonical identity on retry or authorized replay.
Replay authorization and execution are audited separately; replay does not rewrite the
original envelope, occurrence time, or domain history.

### Consumer Semantics

- Every consumer declares an identity, supported complete catalog-identity set, idempotency,
  completeness/high-water, timeout, and poison-message behavior.
- A consumer validates trusted envelope-version framing, immutable event-contract profile,
  operation-specific catalog lifecycle evidence, producer/classification, current restrictive
  protection overlay identities/epochs/partition high-waters, scope, subject,
  ordering/completeness profile and manifest, complete envelope, and selected payload schema
  before exposure or side effects.
- A durable side effect and its processed-event marker commit atomically in the consumer's
  authoritative store when that consumer owns persistent state, binding the exact observed
  protection epochs/high-waters. Inbox completion alone never authorizes a later irreversible
  route, replay, export, support reveal, deletion, or dead-letter effect; that boundary performs
  current PostgreSQL-backed revalidation or consumes an exact single-use authorization that any
  newer protection high-water invalidates.
- Reusing an `event_id` with different canonical content is an integrity violation, not a
  duplicate.
- Unsupported event-contract or envelope versions are rejected and surfaced; consumers do not
  silently discard unknown required semantics.
- Redis acknowledgement occurs only after the consumer's required side effects are durable
  or the event has entered an explicitly governed terminal handling path.

### Data Minimization

Outbox and Redis payloads carry only data required by their consumers.

- Restricted candidate output, full prompts, secrets, credentials, and viewer-memory
  content are not copied into ordinary events.
- Audit events reference internal IDs, policy/prompt versions, classifications, and hashes
  rather than viewer-memory content.
- Media bytes remain in governed object storage and are referenced by immutable identifiers
  and integrity metadata.
- Retention and replay permissions follow the event's data classification and ADR-017.

### EventBus Isolation

Application code depends on provider-neutral `EventBus` and outbox repository ports, never
on Redis client types. Redis credentials and topology remain inside the transport adapter.
Redis is never exposed to `stage-host`; the rig communicates with `session-runtime` through
the authenticated protocol governed by ADR-011 and ADR-016.

All database, Redis, and other external operations have explicit timeouts. Library-level
automatic retries must be bounded, observable, and subordinate to the outbox retry policy.

## Enforcement

- A linked, accepted migration ADR must define the outbox, inbox/idempotency, audit, indexes,
  constraints, and retention implementation before schema changes are added.
- Database integration tests prove that state, required audit, zero-or-more distinct event/outbox
  pairs, the per-version manifest, and every expected-delivery/zero-or-empty attestation commit or
  roll back together.
- Contract validation rejects unknown complete catalog identities, envelope-framing conflicts,
  catalog-lifecycle epoch conflicts, manifest/count conflicts, and malformed envelopes before
  publish and before consume.
- Import and dependency rules prevent application modules from importing Redis SDKs outside
  the transport adapter.
- Publisher tests cover concurrent subject lanes, complete transition manifests including
  zero-count versions, missing-tail/whole-transition recovery, duplicate publication, crash
  points, retries, and acknowledgement races.
- Consumer contract tests prove exact expected-set/high-water completion, idempotent duplicate
  handling, catalog operation-specific dispositions, protection-epoch/high-water rollback
  rejection and effect-boundary revalidation, and rejection of conflicting
  event/contract/manifest identity reuse.
- Data-classification tests prevent restricted prompt, candidate, credential, and
  viewer-memory fields from entering ordinary event payloads.
- CI reconstruction tests build a synthetic incident timeline exclusively from PostgreSQL state,
  audit, event, manifest, expected-delivery, catalog lifecycle, protection-overlay, and outbox
  evidence.

## Failure Behavior

- If PostgreSQL is unavailable or the outbox write fails, the corresponding durable
  transition does not commit. Restrictive safety actuation follows the exception above and
  prevents continued higher-autonomy work while persistence is retried.
- If Redis is unavailable or times out, committed outbox records remain pending in
  PostgreSQL, backlog metrics and alerts fire, and recovery retries from PostgreSQL.
- If the publisher crashes after a successful publish, retry may duplicate delivery; it
  must not invent a new event identity.
- If a consumer crashes before acknowledgement, delivery repeats and its idempotency guard
  prevents duplicate durable effects.
- A malformed, unsupported, or policy-forbidden event is not applied. It enters the
  human-approved poison-event path with enough non-sensitive evidence to diagnose it.
- Loss, flush, or expiration of Redis data does not delete authoritative state or prevent
  reconstruction. Redis is repopulated only through an authorized PostgreSQL-backed
  recovery procedure.
- Unbounded retries, silent drops, and treating a dead-letter stream as authoritative
  storage are forbidden.
- Backlog or consumer lag can trigger the degradation behavior defined by ADR-020; it never
  authorizes bypassing safety or speaking unverifiable work.

## Consequences

- The system accepts duplicate notifications in exchange for atomic durable transitions and
  recoverability.
- Consumers require explicit idempotency and compatibility design.
- PostgreSQL write load and outbox retention require capacity planning and operational
  monitoring.
- Redis can be replaced without changing domain state or recovery semantics.
- Moving to another transport requires an ADR when there are at least three independent
  consumer services, cross-region delivery is required, or measured retention/throughput
  needs exceed the PostgreSQL-plus-Redis design.
- No event producer or migration is authorized until ADR-002, ADR-023 or a compatible
  replacement, this ADR, OD-017, OD-033, and the applicable schema ADR are accepted/decided for
  the exact scope.

## OPEN Decisions

- OD-016: publisher retry/backoff, claim/lease behavior, poison-event handling, replay
  authorization and window, event classifications, and operational retention.
- OD-017: event compatibility, catalog activation, deprecation, rollback, and removal rules.
- OD-033: accepted complete event-contract/framing, scope/subject,
  aggregate-version/event-index ordering and manifest/high-water completeness,
  producer/consumer authorization, historical classification/current restrictive protection,
  and recovery profile under ADR-023 or a replacement.
- The PostgreSQL schema, transaction isolation, indexes, partitioning, and archival strategy;
  these require a linked migration ADR.
- OD-037: PostgreSQL/outbox/Redis resource bounds, protected reserves, deployment topology,
  stream/consumer-group layout, capacity, backlog/lag/storage thresholds, admission/shedding,
  drain/recovery, and exact ADR-020 degradation targets. None may make Redis the system of record.
- OD-036: outbox/transport SLI, telemetry, alert, monitoring-loss posture, and evidence freshness.
- OD-035: database/Redis/external-operation timeouts, claim/lease timing, and recovery-hold timing;
  none may extend an authoritative work deadline.
- The privacy/legal retention values and deletion behavior for each event class under
  OD-009 and ADR-017.

## Acceptance Evidence

Human acceptance requires a review packet containing:

- transaction-fault tests at every state/audit/event/manifest/expected-delivery/outbox commit
  boundary, including an aggregate version with no emitted event;
- PostgreSQL/outbox outage tests proving cloud freeze, e-stop propagation, fail-closed admission,
  and effective-mode decrease actuate immediately, never enable a capability, survive
  restart/takeover as restrictive uncertainty, fence stale recovery/ownership composite actors
  through the shared ownership-row conflict, and prohibit resume until durable reconciliation;
- publisher crash/restart tests showing no committed event is lost and duplicates retain
  their identity;
- catalog-declared subject-lane tests under concurrent publication, including aggregate
  version/event index, zero-count manifest versions, and allowed cross-lane reordering;
- separate stage-host command/task ordering tests under the accepted ADR-011/OD-021 protocol;
- consumer duplicate, delayed, reordered, unsupported-version, catalog-lifecycle,
  protection-epoch/high-water rollback, effect-boundary revalidation, and poison-event tests;
- a Redis-loss exercise that restores service from PostgreSQL without treating Redis
  retention as history;
- an incident-reconstruction test using only PostgreSQL evidence;
- payload data-classification fixtures proving viewer memory, secrets, full prompts, and raw
  restricted candidates are absent;
- the proposed migration ADR, retention/replay decisions, observability, runbook, and
  rollback or disable procedure;
- passing contract, import-boundary, type, integration, and protected-file review gates.
