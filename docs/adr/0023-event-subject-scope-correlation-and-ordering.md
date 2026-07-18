# ADR-023: Event Subject, Scope, Correlation, And Ordering Lanes

Status: Proposed

Priority: P0

Date: 2026-07-17

Sources: `AGENTS.md`, `vnova-review-handoff.md`, ADR-002, ADR-003, ADR-004, ADR-008,
ADR-017, ADR-019, ADR-025, `specs/events/event-envelope.v1.schema.json`,
`specs/events/event-catalog.v1.json`

This ADR is non-binding while its status is `Proposed`. It changes no event schema, generated
contract, producer, consumer, persistence model, or runtime behavior. OD-033 and the protected
human review process must accept this ADR or a replacement before any dependent event is
activated.

## Context

The provisional v1 event envelope requires `stream_session_id`. That shape works for facts whose
authoritative aggregate is a stream session, but the provisional catalog also names policy,
prompt, memory, rig, budget, and safety-availability facts that can exist outside a session.
Inventing a session ID would corrupt identity and recovery. Making the field casually nullable
would leave subject, authorization, ordering, and privacy semantics undefined.

An event must identify the state transition it reports, the ordering lane that serializes that
aggregate, and the lineage that explains why the transition occurred. These are different
concerns:

- the **subject** owns the authoritative state transition;
- the **scope** identifies the environment and catalog-selected primary resource used for
  routing and authorization filtering;
- an **activation target or business scope** says where a rule or definition applies;
- **session and turn correlation** relates work to a broadcast;
- **causation** names the command, event, or trigger that directly caused the fact;
- a **destination** says where a committed event is delivered;
- an **authenticated principal and authorization decision** permit the producer action.

Conflating any of these with a nullable session identifier creates ambiguous replay,
cross-tenant or cross-talent substitution risk, and unrecoverable ordering behavior.

## Decision

After human acceptance, VNova will replace the provisional envelope with one typed v2 event
envelope for all domain events. It will not mutate v1 in place and will not create separate,
semantically divergent envelopes for session, control, and data events.

The envelope describes only an immutable fact committed with authoritative PostgreSQL state. It
is not used for commands, receipts, execution/timer claims, effect attempts, acknowledgements,
heartbeats, `SpeechTask`, restrictive-control messages, or reconciliation requests. Those
non-event records/contracts remain governed by ADR-011, ADR-025, and OD-021 and cannot derive
their trust, sequence, recovery/ownership composite fence, or authority from a domain event.

Every domain event has exactly one authoritative aggregate subject and exactly one ordering lane
derived from that subject. It also has one mandatory typed primary scope; that scope is a
validated claim, not authority. There are no subjectless or scopeless domain events and no
implicit global lane. Session and turn identifiers remain optional correlation conveniences;
they are never a substitute for the subject.

The conceptual v2 envelope contains:

| Field                     | Requirement | Meaning                                                                                                    |
| ------------------------- | ----------- | ---------------------------------------------------------------------------------------------------------- |
| `envelope_version`        | Required    | Major envelope semantics; literal v2 for this model                                                        |
| `event_id`                | Required    | Immutable, globally unique VNova event identity                                                            |
| `type`                    | Required    | Registered domain-event type                                                                               |
| `event_contract_version`  | Required    | Immutable version of this type's complete payload/catalog contract, independent of envelope version        |
| `scope.environment_id`    | Required    | VNova environment containment and authorization partition; not an implicit organization or tenant          |
| `scope.resource.kind`     | Required    | Closed, event-catalog-selected primary resource kind used before payload exposure                          |
| `scope.resource.identity` | Required    | Closed, kind-specific identity object for the exact primary resource                                       |
| `subject.kind`            | Required    | Closed, catalog-governed aggregate kind                                                                    |
| `subject.identity`        | Required    | Closed, kind-specific, stable VNova-owned identity object for that aggregate                               |
| `aggregate_version`       | Required    | Optimistic-concurrency version of subject state after the committed transition                             |
| `event_index`             | Required    | Deterministic contiguous ordinal among events emitted for that subject transition                          |
| `transition_event_count`  | Required    | Exact number of events emitted for this subject transition; strictly positive and greater than event index |
| `transition_manifest_id`  | Required    | Opaque identity of the authoritative PostgreSQL completeness manifest committed with this transition       |
| `correlation_id`          | Required    | Opaque internal identity for the end-to-end operation or workflow lineage                                  |
| `causation`               | Conditional | Typed command, event, or trigger identity when a direct cause exists; absent only for a reviewed root fact |
| `stream_session_id`       | Optional    | Broadcast correlation; required when `turn_id` is present                                                  |
| `turn_id`                 | Optional    | Turn correlation; must belong to `stream_session_id`                                                       |
| `occurred_at`             | Required    | UTC source-clock observation; evidence only, never authoritative ordering                                  |
| `payload`                 | Required    | Exact payload schema selected by the immutable complete event-contract identity                            |

This table is a semantic contract proposal, not a serialized JSON Schema. Exact UUID profile,
timestamp profile, property names, extension rules, numeric limits, and canonicalization remain
under ADR-002, OD-017, OD-033, and OD-035. OD-021 governs only the separate non-event wire
contracts.

The full immutable catalog identity is
`(envelope_version, type, event_contract_version)`. The catalog entry pins the exact payload
schema identity/digest plus subject, scope, ordering/completeness, classification, authorization,
retention, compatibility, and recovery profiles. A change to any of those semantics creates a
new `event_contract_version` even when the payload's serialized shape is unchanged. Historical
outbox, inbox, replay, and incident evidence preserves the original complete identity and never
resolves it through a mutable "current" profile.

### Subject Invariants

- The subject is the aggregate whose committed state transition makes the event true.
- Subject kind and its kind-specific identity object are inseparable. An untyped generic ID or
  an identity inferred from the payload is invalid.
- The subject belongs to exactly `scope.environment_id`. Cross-environment subject,
  correlation, cause, or target references are invalid unless a separately reviewed transfer
  workflow explicitly models both sides without changing either identity.
- The event catalog declares the allowed subject kind or closed set of kinds for every complete
  `(envelope_version, type, event_contract_version)` identity. A producer cannot choose an
  arbitrary kind.
- If `subject.kind` is `stream_session`, its typed identity equals `stream_session_id`.
- If a future accepted aggregate model and catalog permit `subject.kind = turn`, its typed
  identity equals `turn_id`, and the corresponding `stream_session_id` is present. Current
  ADR-003 keeps turns inside the stream-session aggregate, so correlation does not make a turn an
  aggregate root.
- Other subjects may carry session and turn correlation only when the referenced records exist
  and the producer is authorized to associate them.
- An environment-wide fact uses a real environment aggregate subject. It does not use a magic,
  empty, wildcard, or fabricated session identity.
- A policy, prompt, or provider activation event is subject to the activation aggregate whose
  state changed. Its target scope is separately and explicitly represented.
- A memory event is subject to the memory record or reviewed memory aggregate. Raw viewer
  platform identity is not an event subject.
- Mutable names, display names, slugs, usernames, channel names, provider aliases, and external
  unqualified IDs are never subject identities.

The subject identifies a fact; it grants no permission. Producers still require authenticated
workload identity, exact current aggregate and actor ownership under ADR-025 where applicable,
command authorization, current configuration, and applicable policy checks under ADR-019.

### Scope Invariants

- The event catalog fixes the exact scope resource kind or closed set of kinds for every complete
  `(envelope_version, type, event_contract_version)` identity. Producers cannot downgrade
  classification or select a more convenient resource.
- Scope is available for environment partitioning, routing, and authorization filtering before
  a consumer is permitted to expose or decode the payload.
- The scope resource is the primary protected resource for this event contract. It may equal the
  subject, such as a session event, or differ, such as an activation binding whose target is a
  character.
- Additional business targets use event-specific typed payload references. A generic list of
  optional scope IDs is forbidden.
- Scope is a producer claim validated against authenticated identity, aggregate relationships,
  and consumer authorization. It is never an access grant.
- Subject/scope values are not duplicated in payloads. An unavoidable event-specific reference
  has an explicit equality constraint.
- Every currently proposed event is environment bound. A future organization, tenant,
  cross-environment, or global fact requires a new protected scope profile; null, wildcard,
  sentinel, or fabricated environment/resource identities are invalid.

### Ordering And Concurrency

The lexicographic pair `(aggregate_version, event_index)` is the only cross-process event-order
authority for a `(scope.environment_id, subject.kind, subject.identity)` lane.
`occurred_at`, database commit timestamps, Redis stream IDs, consumer receipt time, and telemetry
timestamps cannot reorder facts.

- The subject's optimistic `aggregate_version` advances under PostgreSQL serialization or
  compare-and-swap. It commits in the same transaction as state, required audit evidence, exactly
  one transition manifest, authorized expected-delivery attestations, and zero-or-more
  event/outbox pairs.
- Multiple events for one subject transition receive unique, deterministic, contiguous
  zero-based `event_index` values `0..N-1`. Every envelope for that transition carries the same
  `transition_event_count = N` and `transition_manifest_id`; aborted transactions publish none of
  them.
- The same PostgreSQL transaction creates one immutable `EventTransitionManifest` for every
  committed aggregate version, not only an event-emitting transition. It contains the environment,
  subject lane, aggregate version, exact event count, and ordered event IDs, complete catalog
  identities, and canonical envelope/payload digests. `N = 0` is a valid manifest with empty event
  lists and no event/outbox pair.
- Each manifest derives the exact required subset for every authorized durable lane-consumer
  profile, including explicit zero-event and filtered-empty attestations. Manifest and
  expected-delivery evidence is minimized and access controlled; a consumer cannot use it to
  discover payloads or classifications it is not authorized to know.
- No independent event counter or global database sequence becomes a second aggregate
  authority.
- Redis transports committed events and may redeliver or deliver different lanes in any order.
  It does not allocate causal position or become recovery authority.
- The same `event_id` with the same canonical envelope and payload digest is a duplicate and is
  handled idempotently.
- Reuse of an `event_id` with different canonical content, or reuse of an
  `(scope.environment_id, subject.kind, subject.identity, aggregate_version, event_index)` position
  with a different event identity or digest, is an integrity incident and fails closed.
- A numeric version gap alone is not proof of lost delivery: an aggregate mutation may emit no
  event, and catalog routing may filter event types. Every ordered durable consumer therefore
  reconciles the gapless sequence of authorized PostgreSQL-backed transition-manifest versions
  and expected-delivery high-water through an internal bounded reconciliation port on startup,
  after a gap or timeout, and within its catalog-fixed maximum staleness. Redis receipt or silence
  is not completeness evidence.
- A complete-lane consumer verifies every position `0..transition_event_count-1` against the
  manifest. A filtered consumer verifies its exact authorized required subset. Every lane
  consumer advances across an intentional zero-event aggregate version only after receiving its
  explicit zero-count attestation. A missing tail, an entirely missed manifest version, a
  manifest/envelope mismatch, or an unknown high-water makes the projection stale; it never
  guesses or skips a required fact silently.
- A safety-, authorization-, rights-, deletion-, activation-, or other capability-expanding
  projection cannot advance or authorize work until completeness of every required manifest set
  through its authoritative high-water is proven. A received restrictive fact may take immediate
  safe-direction effect, but the projection remains stale/frozen until reconciliation completes.
- Consumers whose catalog profile permits reordering still use the causal position for
  idempotency and stale-write rejection.
- A late event from another subject lane is not a gap. Cross-subject coordination uses an
  explicit command/saga/projection contract and cannot infer a global total order.

Aggregate version, event index, event identity, and domain-specific epoch remain separate
concepts. An aggregate command may change state without an externally visible event, while one
committed transition may emit several events. Rights, activation, session, restriction, and
other domain epochs are named explicitly in their payload schemas; consumers never reinterpret
an event position as one generic safety epoch.

### Correlation And Causation

`correlation_id` groups one end-to-end operation without changing aggregate ownership. A new
external command or reviewed autonomous trigger starts a correlation identity; downstream work
preserves it. Retries preserve correlation but create new attempt and event identities.

`causation` identifies the direct input that caused the event:

- command cause: authenticated command identity and its idempotency scope;
- event cause: a prior immutable `event_id`;
- trigger cause: a registered scheduler, watchdog, provider, or system-trigger identity.

The exact cause kind and ID profile is catalog governed. A consumer must not follow causation as
an authorization chain, and a producer cannot cite an event it was not allowed to observe.
Cycles, self-causation, impossible lineage, or mismatched session/turn correlation are rejected
or quarantined as integrity failures.

### Event-Contract Profile And Catalog Lifecycle

`EventContractProfile` is the immutable complete profile selected by
`(envelope_version, type, event_contract_version)`. Catalog lifecycle eligibility is a separate
authoritative aggregate with a stable identity, closed state, strictly increasing
`catalog_epoch`, immutable transition identity, expected/current epoch, actor/workload,
authorization/review evidence, reason, and effective time. A lifecycle transition never edits the
profile or historical events. Reuse of an epoch with different state/evidence, epoch regression,
or a current-state/history mismatch is an integrity incident.

Every operation interprets lifecycle evidence explicitly:

- New event emission requires the exact profile to be currently `active` at the aggregate commit,
  plus separately current producer/capability authority for the environment, and records the
  catalog state, epoch, and transition identity as immutable emission evidence.
- Ordinary delivery/retry validates the immutable profile, emission evidence, exact retained
  delivery obligation, and current restrictive handling state. Deprecation or retirement cannot
  reinterpret the event. Retirement preflight must prove required ordinary outbox delivery is
  complete; contradictory pending delivery freezes the lane.
- Recovery replay requires a separate current replay decision, retained original profile/schema,
  consumer support, retention eligibility, and current protection overlay. Neither historical
  `active` nor current `deprecated`/`retired` status alone permits or forbids replay.
- Incident decoding may use a retained profile or catalog tombstone for read-only evidence
  interpretation. It grants no producer, consumer, replay, or business-effect authority.

A consumer must not require current `active` status to understand retained historical evidence,
and must not treat emission-time `active` evidence as current authorization for delivery, replay,
export, or another effect.

### Privacy And Data Classification

The envelope is operational metadata and remains linkable even when it carries opaque IDs.

- It contains no raw viewer input, generated text, approved text, memory content, prompt
  content, persona content, policy content, credentials, contracts, identity evidence, or
  provider request/response content.
- External identities are represented through protected, qualified reference records; they are
  not copied into subject or correlation fields.
- The catalog fixes data classification, allowed producers/consumers, retention class, and
  redaction profile for each `(envelope_version, type, event_contract_version)` identity; a
  producer cannot supply or downgrade those values dynamically. The payload schema enforces the
  permitted data shape.
- The immutable emitted classification/profile is historical evidence and a minimum protection,
  not a permanent ceiling. An effective, independently authorized `EventProtectionOverlay` state
  for restrictive reclassification, incident, deletion, or legal hold makes access, routing,
  replay, retention/hold/deletion, export, support reveal, or dead-letter handling for existing
  events no less restrictive than that historical floor. It never rewrites the envelope, catalog
  identity, digest, or historical profile.
- Each overlay is an environment-contained aggregate with a stable identity, immutable typed
  target profile, current restrictive state, and strictly increasing `protection_epoch`.
  Permitted targets are an exact event identity, immutable event set, exact catalog identity
  within a typed subject/scope, or named evidence scope; null, mutable query, implicit wildcard,
  or cross-environment targeting is invalid. Every transition uses compare-and-swap, records the
  previous/result state and epoch, actor/workload, authorization/legal basis, reason, effective
  time, and immutable transition identity.
- Each event-contract profile fixes the closed protection partitions that apply. Every overlay
  transition atomically advances the authoritative PostgreSQL `protection_high_water` for each
  affected partition. A protected lookup returns the complete applicable overlay set, exact
  epochs/digests, and partition high-waters without exposing unauthorized event metadata.
  Consumers retain their greatest observed values; an epoch/high-water regression, same-epoch
  digest conflict, incomplete partition set, or stale/unknown/unavailable authority freezes
  handling and fails closed.
- Effective handling is the deterministic restrictive union of the immutable historical profile
  and every applicable current overlay. Ordinary overlay transitions only tighten. A relaxation
  or release requires a separately authorized protected decision and a new forward overlay
  transition/epoch after current legal, privacy, security, hold, deletion, and retention
  revalidation; absence, expiry, deletion, cache eviction, restore, or fault clearance never
  widens by inference.
- A durable inbox/effect record binds the overlay identities, protection epochs, and partition
  high-waters it observed. Before an irreversible route, replay, export, support reveal, deletion,
  or dead-letter effect, the enforcement point either revalidates those values against
  PostgreSQL in the effect transaction or consumes an exact, single-use, short-lived
  `EventHandlingAuthorization` minted by the protected event-protection authority after that
  revalidation. The immutable authorization binds event identity/digest, one operation,
  purpose/destination, overlay set, epochs, high-waters, expiry, authorization decision, and
  workload. Any mismatch, reuse, expiry, or newer high-water invalidates it; retry requires a new
  authorization. Earlier inbox progress or a cached allow is never sufficient.
- Viewer-memory facts and audit records keep the table, content, and access-role separation
  required by `AGENTS.md` and ADR-017. Sharing an event ID or minimized reference does not permit
  joining or copying restricted content.
- Deletion, merge, split, and tombstone events retain only the minimum identity and evidence
  allowed by the accepted privacy policy. Replay cannot recreate deleted source content.

### Compatibility And Activation

The existing v1 envelope and catalog remain provisional, inactive evidence. This proposal does
not authorize editing them, generating v2, or emitting any listed event.

After acceptance:

1. ADR-002 must be accepted or superseded with exact compatibility and code-generation rules.
2. v2 receives a new schema identity; v1 is never silently reinterpreted.
3. Each catalog entry is reviewed for subject kind, scope profile, payload classification,
   producer, consumer, ordering behavior, retention, and recovery before activation.
4. Producers and consumers declare supported
   `(envelope_version, type, event_contract_version)` catalog identities.
5. Before version-specific parsing, an authenticated or schema-bound transport/storage
   discriminator selects one exact envelope version. The v2 serialized `envelope_version` must
   match that trusted framing. Legacy v1, which has no serialized discriminator, may be consumed
   only from an explicitly v1-bound trusted context or must be withdrawn; absence of a v2 field
   never implies v1. Unknown or conflicting discriminators fail closed.
6. Mixed-version transport never relies on structural guessing. An explicit, tested adapter may
   project a reviewed v1 fact into v2 only when subject, scope, complete event-contract profile,
   causal position, and transition completeness can be proven without invention.
7. Unknown envelope versions, unknown event types, unsupported event-contract versions, and
   invalid subject, scope, completeness, or catalog mappings are quarantined or rejected
   according to the accepted delivery policy.
8. Rollout, dual-read, deprecation, replay, and removal require the compatibility decision in
   OD-017 and protected contract review.

The proposed catalog lifecycle states for OD-017 review are `required`, `candidate`, `active`,
`deprecated`, and `retired`, plus terminal `withdrawn` for a never-activated candidate. They are
append-only eligibility states with the catalog epoch/transition evidence defined above, not
mutable fields of the immutable profile. An active complete event-contract profile is immutable;
a payload, subject, scope, completeness, ordering, classification, authorization, retention,
recovery, or serialized-shape change creates a new `event_contract_version`. Consumers deploy and
prove readiness before a producer activates a new version. Retirement retains a catalog
tombstone and requires outbox, replay-window, retention, required-consumer, incident-decoder, and
rollback evidence.

Envelope validation alone never yields a trusted event. The consumer must validate the immutable
complete profile, trusted framing discriminator, subject and scope profiles,
ordering/completeness manifest, producer ownership, operation-specific catalog lifecycle evidence,
effective restrictive protection overlay epochs/high-waters, payload schema, and payload before
exposure or side effects.

Catalog `active` means the contract is eligible for reviewed publication; it does not enable a
producer in every environment. The exact producer/capability activation, environment,
configuration snapshot where applicable, and authenticated authority must also be current. An
inactive capability cannot be enabled by sending a structurally valid event.

The current catalog marks no event active. Subject to repository/production evidence and human
review, the preferred migration is therefore to freeze and withdraw the unused v1 proposal and
activate only reviewed v2 entries, avoiding needless dual publication. This ADR does not assume
that evidence or authorize withdrawal.

No runtime implementation begins merely because this ADR is accepted. The literal Runtime
Implementation Gate, accepted upstream ADRs, valid Open Decision dispositions, protected human
review, contract generation, and the feature's own entry gates still apply.

## Alternatives Considered

### Keep A Session-Only Envelope

Rejected. Policy, prompt, memory, rig, budget, and environment facts do not necessarily belong to
a stream session. Fabricated or placeholder sessions corrupt identity, authorization, retention,
and recovery.

### Make `stream_session_id` Nullable Without A Subject

Rejected. Nullability would describe absence but not say which aggregate owns the fact, which
ordering lane applies, or which principal may produce it.

### Separate Session, Control, And Data Envelopes

Rejected as the default. Divergent envelope semantics would multiply code generation, routing,
signature, compatibility, replay, and observability logic and make cross-domain consumers guess
which guarantees apply. A future transport-specific wrapper may be proposed separately, but it
cannot replace the single domain-event semantic envelope.

### Use Time Or Redis Order

Rejected. Clocks can skew or step, networks reorder, Redis can redeliver, and multiple streams
have no authoritative global order. Those values remain delivery and diagnostic evidence only.

### Add An Independent Gapless Subject Event Counter

Rejected as the default. It duplicates the aggregate's concurrency authority, adds hot-aggregate
allocation and recovery work, and still cannot prove consumer loss when mutations emit no event
or catalog routing filters event types. The aggregate version plus deterministic event index
preserves causal order without pretending every numeric gap is missing delivery.

### Put Every Scope In One Generic List

Rejected. A bag of optional environment, talent, character, viewer, session, rig, and provider
IDs permits contradictory combinations and makes authorization dependent on inference. The
subject is singular and typed; other scopes are payload-specific, closed contracts.

## Enforcement And Verification

Once implementation is authorized, enforcement must include:

- schema fixtures and generated types for every supported language;
- a closed immutable `EventContractProfile` registry keyed by
  `(envelope_version, type, event_contract_version)` and mapping that exact identity to one
  payload-schema identity/digest, subject kinds, scope, ordering/completeness, classification,
  allowed producer/consumer profiles, retention, recovery, and immutable compatibility semantics;
- separate monotonic `EventCatalogEligibility`, supersession, and required consumer-readiness
  records with stable identities, current state/epoch, immutable transitions/review evidence, and
  explicit emission, ordinary-delivery, recovery-replay, and incident-decoding checks;
- producer APIs that derive subject, scope, aggregate version, event indexes, transition count,
  manifest, and expected-delivery sets from the owning aggregate transaction and reviewed
  relationships rather than accepting arbitrary caller strings;
- PostgreSQL constraints or equivalent transaction invariants that prevent duplicate lane
  positions, missing zero-count versions, incomplete/contradictory manifests, regressed
  catalog/protection epochs or high-waters, and conflicting event or contract identities;
- outbox checks proving aggregate state/version, audit evidence where required, causal position,
  per-version completeness manifest/expected-delivery attestations, every emitted event and its
  distinct one-to-one outbox row commit atomically;
- consumer inbox/idempotency/high-water records that distinguish exact duplicates from integrity
  conflicts and cannot mark a transition complete before its authorized expected set or
  zero/empty attestation is durable;
- authenticated/schema-bound envelope discriminators and parser dispatch that fail closed on
  downgrade, absence, mismatch, or unknown versions;
- import and dependency boundaries preventing Redis, telemetry, or provider adapters from
  becoming event authority;
- authorization tests proving subject identity cannot grant producer or consumer access;
- privacy tests proving envelope, manifest, audit, telemetry, and dead-letter paths never copy
  restricted content and that current restrictive protection-overlay epochs/partition
  high-waters dominate historical handling without rewriting event evidence;
- effect-boundary tests proving stale inbox progress, cache rollback, same-epoch digest conflict,
  new overlay creation, protected release, or expired/superseded single-use authorization cannot
  perform an irreversible event-handling effect;
- replay and recovery tooling that preserves the original immutable event and records delivery
  attempts separately.

## Acceptance Evidence

Human architecture, contract, runtime, data, safety, privacy, security, and operations reviewers
must approve:

- the one-envelope v2 direction and the distinction between subject, scope, correlation,
  causation, destination, and authorization;
- immutable event-contract profiles, separate monotonic catalog lifecycle authority, and
  operation-specific emission, delivery, replay, and incident-decoding dispositions;
- the subject-kind registry and per-event mapping for every catalog entry proposed for
  activation;
- the per-event scope profile and aggregate-version/event-index/completeness-manifest transaction,
  retention, projection, high-water, and recovery design;
- typed protection-overlay targets, monotonic protection epochs/partition high-waters, protected
  release, and exact immediate effect-boundary authorization/revalidation;
- exact v1-to-v2 compatibility, deprecation, and unsupported-version behavior;
- the UUID, timestamp, canonicalization, signature/integrity, and payload-extension profiles;
- the data classification, retention, and access policy for envelope metadata and each payload.

Executable evidence must then include:

- positive and negative Python, TypeScript, and applicable stage-host contract fixtures;
- subject-kind, catalog scope, subject/scope/environment relationship, subject/session equality,
  turn/session membership, and scope-conflict tests;
- concurrent producer tests proving aggregate version and event indexes are deterministic and
  atomically bound to the committed transition, with one manifest for every aggregate version;
- abort, retry, duplicate, event-ID collision, causal-position collision, missing middle/tail,
  whole-transition loss, zero-event transition, missing zero-count attestation, conflicting
  count/manifest, filtered-empty/subset routing, stale high-water, replay, restore, and
  projection-rebuild tests;
- proof that safety/authorization projections cannot advance on an incomplete expected set and
  that restrictive facts can apply immediately without declaring the projection complete;
- multi-lane tests proving consumers do not infer a global order;
- outbox atomicity and Redis redelivery/reordering/partition tests;
- unauthorized producer/consumer, forged subject, cross-environment, cross-talent, and
  cross-viewer substitution tests;
- privacy, restrictive-reclassification, deletion, tombstone, hold, dead-letter, log, trace, and
  telemetry leakage/precedence tests, including monotonic overlay epoch/high-water, cache rollback,
  concurrent new restriction, protected release, and immediate effect-boundary revalidation;
- compatibility tests for every allowed and denied complete catalog identity, including
  immutable-profile/catalog-lifecycle separation, operation-specific status behavior,
  profile-only evolution, historical replay under its original profile, trusted framing,
  downgrade, and conflicting-discriminator cases;
- capacity evidence that aggregate serialization and ordered publication meet reviewed
  hot-aggregate load and recovery targets without weakening ordering.

## Consequences

- Session and non-session facts share one explicit semantic envelope.
- Aggregate ownership, replay order, and recovery become deterministic without a global FIFO.
- Session and turn lineage remains available without inventing session identity.
- Strong typed subjects, scopes, and catalog mappings increase schema-review and producer
  discipline.
- Aggregate-version ordering avoids a second event counter but requires authoritative transition
  manifests and expected-delivery high-water reconciliation to distinguish loss from a valid
  filtered/version gap.
- v1 cannot be activated as-is for the affected catalog; a reviewed v2 and compatibility plan
  are required.
- No event schema, catalog entry, producer, consumer, or runtime behavior is authorized by this
  Proposed ADR.

## OPEN Decisions

- OD-033 must accept this ADR or a replacement and name the approved subject kinds, per-event
  scope and ordering profiles, compatibility profile, and privacy classification.
- OD-017 and ADR-002 must define complete event-contract evolution, schema/code generation,
  compatibility, deprecation, retention, and deletion treatment.
- OD-021 governs the separate command/receipt/outcome/task/control/acknowledgement/reconciliation
  wire contracts. ADR-025 governs their durable actor-side semantics. Neither authorizes or
  versions domain events.
- OD-014 and ADR-025 must decide whether any ownership, command-outcome, effect, or timer semantic
  fact warrants a domain-event profile; coordination records and delivery observations remain
  non-events.
- OD-035 must define UTC, monotonic-time, deadline, and clock-uncertainty profiles without making
  timestamps ordering authority.
- OD-034 must define the stable aggregate/version/activation identities referenced by future
  event subjects and scopes.
- Exact event signatures or integrity protection, dead-letter/quarantine retention, hot-lane
  capacity limits, and projection-rebuild authority remain human-reviewed design inputs.
