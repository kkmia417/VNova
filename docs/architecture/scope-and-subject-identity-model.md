# Scope And Subject Identity Model

Status: Proposed architecture reference; no schema, contract, migration, identity-linking,
authorization, event activation, or runtime authority

Governing sources:

- [`AGENTS.md`](../../AGENTS.md)
- [ADR-002: contract source and code generation](../adr/0002-contract-source-and-code-generation.md)
- [ADR-003: stream-session, segment, and turn lifecycle](../adr/0003-stream-session-segment-and-turn-lifecycle.md)
- [ADR-004: PostgreSQL outbox and Redis Streams](../adr/0004-postgresql-outbox-and-redis-streams.md)
- [ADR-008: safety gate enforcement](../adr/0008-safety-gate-enforcement.md)
- [ADR-016: stage-host and cloud/local topology](../adr/0016-stage-host-and-cloud-local-topology.md)
- [ADR-017: data retention, privacy, and PII](../adr/0017-data-retention-privacy-and-pii.md)
- [ADR-019: authentication, authorization, and operator roles](../adr/0019-authentication-authorization-and-operator-roles.md)
- [ADR-023: event subject, scope, correlation, and ordering lanes](../adr/0023-event-subject-scope-correlation-and-ordering.md)
- [ADR-024: versioned configuration and scoped activation](../adr/0024-versioned-configuration-and-scoped-activation.md)

This reference makes the identity distinctions required to review ADR-023 and ADR-024. It names
conceptual types, not tables, APIs, JSON fields, IAM roles, UUID encodings, tenant defaults, or
production identifiers. Proposed event mappings are review candidates only; every current event
catalog entry remains inactive.

## Why These Distinctions Matter

One object can participate in several relationships without those relationships being
interchangeable. For example, a policy activation can:

- be stored in a production environment;
- target a character;
- be changed by an authorized operator;
- affect a stream session;
- be caused by an administrative command;
- emit a notification delivered to several consumers.

The environment, target character, operator, stream session, command, and consumer are not six
aliases for the event subject. The subject is the one aggregate whose authoritative state
changed. Treating every relationship as a generic scope string creates confused-deputy,
cross-environment, replay, privacy, and ordering failures.

## Core Vocabulary

| Concept                 | Question it answers                                                 | Security and lifecycle rule                                                                   |
| ----------------------- | ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Stable identity         | Which enduring domain object is this?                               | VNova-owned, immutable, typed, never a mutable label                                          |
| Version identity        | Which immutable reviewed form was used?                             | Never inferred as `latest`; exact version and digest recorded                                 |
| Aggregate subject       | Which aggregate's committed transition makes this true?             | Exactly one per event; determines the ordering lane                                           |
| Environment containment | In which VNova environment does the object exist?                   | Required; cross-environment references need an explicit protected workflow                    |
| Event primary scope     | Which protected environment/resource may route or expose the event? | Catalog-fixed typed claim; validated before payload exposure, never an access grant           |
| Activation target scope | Where may a definition be eligible?                                 | Typed, family-specific, separately authorized, deterministic composition                      |
| Authorization resource  | What protected object and action is being permitted?                | Evaluated from authenticated principal and policy; never inferred from subject or target      |
| Correlation             | Which workflow, session, or turn is related?                        | Explanatory lineage only; does not own state or grant access                                  |
| Causation               | Which command, event, or trigger directly caused this?              | Typed immutable reference; not a transitive authorization chain                               |
| Destination             | Which consumer, platform, account, or surface receives?             | Delivery/use scope; does not change domain ownership or content approval                      |
| Data subject            | Which person or protected identity does data concern?               | Privacy concept; not automatically the aggregate subject, principal, talent, viewer, or owner |
| Authority               | Which component may make or record the decision?                    | Defined by package/service boundary and protected capability, not by possession of an ID      |

`Scope` without a qualifier is forbidden in binding design. A document or contract must say
environment containment, activation target, authorization resource, distribution destination,
privacy data subject, or another closed scope kind.

## Identity Principles

1. Every durable identity has one semantic type. APIs and generated contracts do not accept a
   generic string when cross-type substitution matters.
2. Every durable domain identity belongs to exactly one VNova environment. Environment is a
   deployment and authorization partition, not an assumed organization or customer tenant.
3. VNova-owned IDs are opaque, immutable, non-semantic, and never reused after deletion.
4. External IDs are qualified by issuer/namespace, platform or provider, account where needed,
   and environment. A raw external string is not globally unique.
5. Display name, handle, slug, email, channel name, model alias, filename, and vendor label are
   mutable attributes, not keys or evidence of authority.
6. A stable root and an immutable version are different types. Historical work records the exact
   version; current eligibility is a separate state.
7. An aggregate subject is selected from the transaction that changed authoritative state, not
   from whichever identifier is convenient for routing.
8. Correlation can cross aggregate boundaries. Ordering cannot: each subject has its own lane.
9. Subject identity, target scope, and authorization decision are validated together but never
   collapsed.
10. Missing, ambiguous, unqualified, cross-environment, deleted, conflicted, or unauthorized
    identity fails closed for activation, autonomous speech, use, publication, and replay.

The exact UUID profile, canonical text form, timestamp profile, enum evolution, and external ID
normalization remain decisions under ADR-002 and the applicable Open Decisions.

## Conceptual Identity Families

### Environment, Talent, Character, And Viewer

| Type                        | Stable meaning                                                                           | Must not be confused with                                                        |
| --------------------------- | ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `Environment`               | VNova configuration, data, and authorization containment boundary                        | Organization, legal entity, cloud account, region, or deployment name            |
| `Talent`                    | Human performer/rights subject represented under reviewed governance                     | Character, voice model, operator account, provider profile, or display name      |
| `Character`                 | Performed AI-talent/persona identity                                                     | Talent, persona version, prompt version, channel, or model                       |
| `Viewer`                    | Optional VNova-internal person/pseudonymous identity under accepted privacy use          | Username, platform account, chat message author string, operator, or audit actor |
| `PlatformIdentity`          | Qualified external identity within a platform/account/issuer namespace                   | A universally resolved person or authorization principal                         |
| `ViewerInteractionIdentity` | Minimal session/platform-scoped identity used when durable viewer linkage is not allowed | Durable viewer memory identity or cross-platform person                          |

A talent may perform one or more characters, and a character may have reviewed relationships to
talent, voice, rights, persona, and production records. Those are explicit versioned
relationships. No relationship is inferred from names.

Cross-platform viewer linkage is disabled until privacy, consent, legal basis, access, deletion,
merge, and correction policy is accepted. Similar handles, platform-provided names, voice,
writing style, IP address, device evidence, or model inference cannot merge identities.

### Broadcast Execution

| Type                | Stable meaning                                             | Identity/lifecycle note                                                        |
| ------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `StreamSession`     | One logical rehearsal or live broadcast aggregate          | Owns session lifecycle; not a generic container for non-session facts          |
| `StreamPlan`        | Stable plan root                                           | Each reviewed plan form has a separate immutable version                       |
| `Segment`           | Stable planned or ad-hoc segment root                      | Version identity is separate from position or label                            |
| `Turn`              | One admitted response-work lineage within a session        | Retry/fallback creates attempts, not a new identity for the same admitted turn |
| `GenerationAttempt` | One exact provider/generation attempt                      | New provider call or complete retry gets a new attempt identity                |
| `CandidateResponse` | One complete candidate produced by one attempt             | Never reused for rewritten or fallback content                                 |
| `SafetyDecision`    | One terminal safety decision for a candidate               | Decision identity is not approval authority by itself                          |
| `ApprovedResponse`  | Safety-owned immutable approval capability/record identity | Construction remains exclusive to `packages/safety`                            |

Session and turn IDs are useful event correlation, but a policy activation, memory record, rig
connection, or budget ledger does not become session-owned merely because it affects a
broadcast.

### Rig, Connection, And Process Identity

| Type                | Stable meaning                                                   | Rule                                                                       |
| ------------------- | ---------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `Rig`               | Enrolled physical/logical stage-host installation                | Never inferred from hostname, IP address, or user label                    |
| `RigEnrollment`     | Reviewed trust and key enrollment lineage                        | Separate from current connection or session binding                        |
| `StageHostBoot`     | One process/host boot incarnation                                | New boot gets a new ID; counters from an old boot cannot silently continue |
| `RigConnection`     | One authenticated connection lifecycle                           | Connect and disconnect may share this subject; reconnect creates a new one |
| `SessionRigBinding` | Versioned binding between a stream session and eligible rig/boot | Session and rig remain independently identifiable                          |
| `Command`           | One authenticated semantic control intent                        | Idempotency scope and authorization resource are explicit                  |

Connection identity is not trust by itself. Enrollment, current key/epoch, boot incarnation,
session binding, command sequence, expiry, and authorization remain independently validated.

### Definitions, Versions, And Activation

| Type                            | Stable meaning                                                       | Rule                                                                                                          |
| ------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `DefinitionRoot`                | One semantic persona/prompt/policy/provider/model/etc. family member | Stable across immutable versions                                                                              |
| `DefinitionDraft`               | One non-selectable authoring workspace                               | Explicit CAS revision; publishing creates a new version identity                                              |
| `DefinitionVersion`             | One immutable canonical form                                         | Exact digest/provenance from creation; review binds this identity, never a mutable alias                      |
| `DefinitionVersionEligibility`  | Current reviewed use state for one exact version                     | Separate monotonic eligibility epoch and immutable transitions                                                |
| `ActivationSetRoot`             | One compatible activation-bundle lineage                             | Bundle granularity is human reviewed                                                                          |
| `ActivationSetVersion`          | One immutable exact version bundle                                   | No wildcard, range, `latest`, or partial application                                                          |
| `ActivationSetEligibility`      | Current reviewed use state for one exact set                         | Separate monotonic eligibility epoch and immutable transitions                                                |
| `ActivationBinding`             | Stable aggregate for one typed target/family                         | Explicit inactive/active state, exact set only when active, and monotonic activation epoch                    |
| `ActivationTransition`          | Immutable evidence of one forward binding change                     | Closed initialize/activate/replace/deactivate/rollback operation; not a replacement for the stable event lane |
| `ActivationSchedule`            | Immutable non-effective future intent                                | Separate monotonic schedule state; due execution and ordinary activation transition commit atomically         |
| `ResolvedConfigurationSnapshot` | Immutable exact resolution used by work                              | Records versions, activation and eligibility epochs, resolver version, restrictions, and digest               |

The activation binding is the event subject when its current state changes. The target
environment/talent/character/session/surface/provider resource is a separate typed target.

### Rights, Surfaces, Media, Memory, And Operations

These identity families stay distinct even when one operation references all of them:

- `VoiceProfileDefinition`, `VoiceRightsGrantVersion`, `VoiceRightsState`,
  `VoiceRightsDecision`, and `VoiceUseAuthorization`;
- `SurfaceDefinitionVersion`, `SurfaceDecision`, `SurfaceAuthorization`, final rendering, and
  immutable media artifact;
- typed viewer memory, character memory, session context, knowledge source, derived chunk,
  embedding, and retrieval-index generation;
- `BudgetLedger`, quota decision, admission decision, and cost observation;
- capability restriction/emergency latch, safety dependency state, provider-health state, and
  alert/incident identity;
- audit record, domain event, outbox record, delivery attempt, inbox consumption, and stage-host
  local journal record.

Technical availability is not eligibility, and eligibility is not authorization. An artifact,
memory index, event, audit record, cache, provider observation, or playout observation cannot
manufacture the decision that originally allowed use.

## Containment And Relationship Rules

Conceptual containment is explicit:

```text
Environment
  +-- Talent <-> Character (reviewed versioned relationship)
  +-- Viewer <-> qualified PlatformIdentity (privacy-governed relationship)
  +-- StreamSession -> Segment/Turn -> Attempt -> Candidate -> Decision
  +-- Rig -> Boot/Connection; SessionRigBinding relates Rig to StreamSession
  +-- DefinitionRoot -> DefinitionVersion
  +-- ActivationBinding -> ActivationSetVersion -> DefinitionVersion[]
  +-- Rights/Surface/Memory/Budget/Operational aggregates
```

The tree is explanatory, not a database cascade. In particular:

- a session ending does not delete its talent, character, rig, definitions, or viewer;
- deleting source content does not delete minimized operational evidence when policy requires a
  tombstone, but evidence cannot recreate the content;
- a character relationship does not grant talent rights or voice use;
- an activation target does not transfer ownership of the activated definition;
- an event correlation does not change containment;
- a distribution destination is not an environment or authorization resource.

Relationships with safety, rights, privacy, or historical consequences are themselves stable,
versioned, reviewed records. A mutable many-to-many join without provenance, effective time,
reason, and lifecycle is insufficient.

## Typed Activation Target Model

Every activation target is conceptually:

```text
ActivationTarget {
  environment_id
  resource = exactly one allowed typed resource reference
}
```

The environment is mandatory. The resource kind is selected from the closed list for the
definition family. Candidate targets are:

- the environment baseline;
- one talent;
- one character;
- one stream session;
- one registered broadcast surface;
- one reviewed provider capability or failure domain.

This is not a universal hierarchy. A policy family may use restrictive intersection while a
persona family may permit one reviewed replacement. A provider profile may be selectable only
for a capability and environment, not directly by a viewer or arbitrary tag. Exact rules come
from ADR-024 and the family's protected contract.

An activation target is not:

- an authorization principal;
- an event subject unless the target aggregate itself changed;
- a destination platform/account;
- a privacy data subject;
- an implicit tenant or organization;
- a wildcard or textual expression.

## Event Subject Selection Procedure

For each complete `(envelope_version, type, event_contract_version)` catalog identity, reviewers
follow this procedure:

1. Identify the PostgreSQL transaction and the authoritative aggregate state transition that
   makes the fact true.
2. Name the stable aggregate root, not a version, label, correlation object, destination, or
   convenient parent.
3. Confirm that exactly one subject exists. A command changing multiple aggregates emits one
   event per aggregate or uses an explicitly designed coordination protocol.
4. Confirm the subject belongs to the envelope environment and that every cross-reference has a
   reviewed relationship.
5. Fix the permitted subject kind in the event catalog; producers cannot choose it dynamically
   except from a closed event-specific union.
6. Select the catalog-fixed primary scope resource, verify its environment and relationship to
   the subject, and make it available for routing/authorization filtering before payload
   exposure.
7. Record the committed subject aggregate version, deterministic event indexes, exact transition
   count, immutable completeness manifest, authorized expected-delivery sets, and outbox evidence
   in the same transaction as state and required minimized audit.
8. Add workflow, session, turn, and direct-cause references only as correlation/causation.
9. Validate authenticated producer authority independently of every identity in the envelope.
10. Apply the event-specific data classification, minimization, retention, consumer, replay, and
    recovery profile.

An event with an unknown subject, invented session, conflicting environment, arbitrary subject
kind, or impossible lineage is not published.

## Provisional Catalog Mapping

The table below is a review aid for the 14 inactive entries in
`specs/events/event-catalog.v1.json`. It does not update that catalog or activate a producer.
Exact event names, subject kinds, payloads, and versioning may change under ADR-002 and ADR-023.

| Provisional event          | Candidate authoritative subject                                          | Candidate primary scope resource           | Target/correlation distinction                                                                      | Required review before activation                                                                                                |
| -------------------------- | ------------------------------------------------------------------------ | ------------------------------------------ | --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `ModeChanged`              | `StreamSession`                                                          | Same `StreamSession`                       | Mode is a session state axis; session ID equals subject ID                                          | ADR-003/020 state transition, actor/cause, session epoch, invalid transitions                                                    |
| `OperatorPresenceChanged`  | `OperatorPresenceBinding` or session-owned presence axis                 | Affected `StreamSession`                   | Operator is principal; session is scope/correlation if presence is not session-owned                | ADR-019 ownership, lease/presence semantics, privacy, failover; choose exactly one aggregate model                               |
| `PolicyVersionActivated`   | `ActivationBinding`                                                      | Exact typed activation target              | Policy version is payload evidence; session/turn only correlation                                   | Rename/split for initialize/activate/replace/deactivate/rollback; eligibility, composition, epoch, authorization, classification |
| `PromptVersionActivated`   | `ActivationBinding`                                                      | Exact typed activation target              | Prompt version is payload evidence; no prompt content                                               | Rename/split for all closed binding operations; prompt review, eligibility, epoch, classification                                |
| `MemoryWritten`            | typed `MemoryRecord`                                                     | Protected viewer/character memory resource | Viewer/character/source are protected relationships, not raw subject strings                        | ADR-017/OD-026 purpose, provenance, legal basis, retention, access, extraction policy                                            |
| `MemoryDeleted`            | typed `MemoryRecord`                                                     | Same protected memory resource             | Deletion case/tombstone is evidence; no deleted content in payload                                  | Hold/delete precedence, derived-data cascade, tombstone minimization, no reconstruction                                          |
| `RigConnected`             | UNRESOLVED: `RigConnection`, `Rig`, or `SessionRigBinding`               | Enrolled `Rig` or exact binding            | Durable connection fact must be distinguished from heartbeat/transport observation                  | ADR-011 enrollment, boot/sequence, expiry, binding owner; choose one aggregate or split types                                    |
| `RigDisconnected`          | Same selected aggregate as matching connect fact                         | Same enrolled `Rig` or binding             | Timeout observation versus authoritative disconnect must be explicit; reconnect has new incarnation | Duplicate/late disconnect, watchdog, recovery, connection terminality                                                            |
| `CandidateExpired`         | `StreamSession`                                                          | Same `StreamSession`                       | Candidate is session-owned entity/payload ref; turn/attempt are lineage; expiry cannot reopen       | ADR-003/008 aggregate revision, terminality, clock, cleanup versus evidence retention                                            |
| `SafetyLayerUnavailable`   | UNRESOLVED: safety-capability state or split session/capability types    | Exact affected capability/resource         | A provider/instance health observation is not automatically a durable domain transition             | ADR-008 fail-closed trigger, correlated failure, owner, evidence, recovery; split differing semantics                            |
| `FailClosedActivated`      | UNRESOLVED: typed `CapabilityRestriction` or split target-specific types | Exact restriction target                   | Environment and session restriction semantics must not share an ambiguous event type                | Restrictive epoch, DB-failure actuation, no automatic reset, composition with e-stop/modes                                       |
| `SilenceThresholdExceeded` | `StreamSession` only if a durable session transition                     | Same `StreamSession`                       | A pure threshold observation/alert belongs in telemetry, not the domain-event catalog               | OD-001/035/036 threshold, clock, state owner, evidence quality, degradation behavior                                             |
| `CostBudgetWarning`        | `BudgetLedger` only if a durable budget transition                       | Exact governed budget resource             | A pure warning/alert belongs in observability; it is not admission or spending authority            | OD-037/038 ledger owner, reservation/finalization, currency/usage authority, alert dedupe                                        |
| `ManualSpeechSubmitted`    | `StreamSession` after an accepted command                                | Same target `StreamSession`                | Command is non-event; operator is principal; restricted text is stored separately by ID             | ADR-008 same safety gate, authorization, idempotency, content privacy, surface/rights                                            |

Several rows deliberately record unresolved candidates because current sources do not settle
their authoritative owner or whether the name describes a durable domain transition rather than
telemetry, alert, command, or wire observation. The catalog cannot activate one until reviewers
select exactly one subject/scope profile or split the semantics into distinct event types.
Ambiguity is a blocker, not a union chosen at runtime.

ADR-024's explicit inactive state and closed binding operations make the two provisional
`*VersionActivated` names insufficient as generic activation facts: deactivation and forward
rollback cannot be truthfully encoded as “version activated” by convention. OD-033/034 review
must either choose a neutral binding-transition event contract or split operation-specific types
before either entry can become active.

## Ordering, Revision, And Transition Identity

Six values must not be overloaded:

- **aggregate version** controls authoritative subject-state concurrency and orders transitions
  within a subject lane;
- **event index** orders multiple events emitted by one aggregate transition;
- **transition event count/manifest identity** proves the complete emitted set and each authorized
  consumer's expected subset;
- **event contract version** selects one immutable payload/catalog/security profile for historical
  interpretation;
- **domain epoch** represents family-specific safety/current-state semantics;
- **transition identity** names one immutable state change.

They often advance together but are not interchangeable. One aggregate transition may emit
several indexed events. An internal state update may have no public event, so a numeric aggregate
version gap is not itself proof of lost delivery. A rights, configuration, restriction, or
session epoch has domain semantics that an event consumer cannot infer from a transport
position.

Every event carries the complete contract identity, aggregate version, event index, transition
count, and manifest identity proposed by ADR-023. Payload schemas carry the exact transition ID,
activation epoch, session epoch, rights epoch, or other domain-specific value when a consumer
needs it. Redis stream ID, delivery attempt, clock time, and event ID do not replace those values.

## Identity Lifecycle

### Creation And Qualification

- Creation requires an authenticated semantic command, environment, type, authority, and
  idempotency scope.
- Imported external identities retain issuer and source provenance. Import never turns a
  provider/platform key into a VNova-owned identity.
- A version, child, mapping, or activation cannot exist until every required parent/reference is
  current and eligible under the accepted policy.

### Rename And Attribute Correction

Labels and attributes may change through audited versioned operations. Stable IDs and historical
references do not. A correction never edits an event, decision, approval, or completed snapshot.

### Merge, Split, And Deduplication

Merge and split are explicit protected workflows, not primary-key rewrites:

- source identities remain traceable through minimized, access-controlled relationship
  evidence;
- historical events, decisions, authorizations, memories, and archives keep their original IDs;
- future resolution uses a new reviewed relationship/version;
- conflicting rights, consent, deletion, legal hold, access, or classification fails closed;
- cross-platform viewer merge remains disabled until a privacy-approved workflow exists.

Automated similarity or model inference may propose a case for human review but cannot execute a
merge or widen access.

### Environment Transfer

An object is never silently re-parented to another environment. If transfer is allowed, a
protected workflow creates the destination identity or mapping, records both authorities and
minimized provenance, re-evaluates rights/access/retention, and does not rewrite source history.
Cross-environment event references remain invalid outside that explicit workflow.

### Deletion, Tombstone, And Reuse

Deletion affects content availability and future eligibility; it does not reuse identity or
rewrite immutable evidence. A minimized tombstone may retain type, opaque ID, deletion
disposition, policy/evidence reference, and non-sensitive integrity metadata only when accepted
retention and legal policy allow it.

Deleting source content:

- makes new use, synthesis, retrieval, replay, export, or publication fail closed when required
  evidence is unavailable;
- quarantines or rebuilds derived indexes and caches;
- never reconstructs content from events, audit, telemetry, media, or archives;
- does not erase a legal hold silently;
- does not turn a previously issued authorization into permission for a new use.

Exact erasure, anonymization, legal hold, restoration, appeal, and tombstone retention are OPEN.

## Authorization Checks

Possessing or citing an identity grants nothing. An operation validates:

- authenticated human/workload/rig principal and current credential/session;
- semantic capability and exact action;
- environment and typed authorization resource;
- aggregate ownership and expected revision/epoch;
- current definition/activation, safety, rights, surface, deletion/hold, and mode restrictions;
- idempotency identity and canonical command intent;
- applicable purpose, destination, time, and data classification;
- separation of duties and confirmation where required.

The resulting authorization decision has its own immutable identity and evidence. It cannot be
reconstructed from an event subject, a role label, a successful provider call, a UI control, or
an earlier authorization for a different operation.

## Privacy And Telemetry Rules

- Internal opaque IDs remain personal or linkable data when they can be joined to a person.
- Ordinary events, audit, logs, metrics, traces, dead-letter evidence, and alerts contain no raw
  viewer identity, username, prompt, memory, candidate, approved text, contract, credential, or
  provider payload.
- High-cardinality human/viewer/content IDs do not become metric labels.
- Trace and incident access does not imply access to restricted content stores.
- Viewer memory and audit never share tables, content, or access roles.
- Hashing low-entropy or identifying content is not anonymization. Privacy review selects
  opaque/keyed references and key/access domains where necessary.
- Subject deletion or merge does not cause telemetry to backfill or re-identify old records.

## Review And Validation Checklist

Before any identity or event schema is implemented, reviewers must be able to answer:

- What is the stable root, immutable version, authoritative aggregate, and sole writer?
- Which environment contains it, and can any valid relationship cross environments?
- What is the activation target, authorization resource, data subject, destination, correlation,
  and cause?
- Which values are identifiers versus mutable labels or external aliases?
- What orders concurrent transitions, and which domain epoch/revision is recorded?
- Which principal may create, change, merge, split, delete, restore, or observe it?
- Which content, metadata, classification, retention, hold, and deletion rules apply?
- What happens when identity, relationship, version, epoch, clock, or authorization is missing,
  stale, conflicted, deleted, or unavailable?
- Can audit, event, cache, provider data, media, archive, or telemetry recreate restricted
  content or authority?
- Which positive, substitution, cross-environment, race, replay, deletion, and privacy fixtures
  prove the rules?

The answer cannot be "use the session ID", "use latest", "most specific wins", "the UI already
checked", "Redis is ordered", or "the value is hashed".

## OPEN Decisions

- OD-033: exact event v2 subject kinds, per-event mappings, sequence, compatibility, privacy, and
  recovery profile.
- OD-034: stable/version identity vocabulary, activation target lattice, definition families,
  lifecycle, restricted-content, memory/knowledge, archive/publication, retention, deletion, and
  restoration profile.
- OD-017 and OD-021: contract compatibility, canonicalization, identifier/timestamp profiles,
  code generation, deprecation, and non-event wire contracts.
- ADR-019 and OD-022: human/workload/rig principal, role, capability, separation-of-duties, and
  identity lifecycle.
- OD-026: viewer/character memory identity, cross-platform linkage, consent/legal basis, derived
  data, and deletion.
- Exact external issuer namespaces, environment inventory, merge/split/transfer authority,
  tombstone content, and identity-retention values remain human decisions.
