# ADR-024: Versioned Configuration And Scoped Activation

Status: Proposed

Priority: P0

Date: 2026-07-17

Sources: `AGENTS.md`, `vnova-review-handoff.md`, ADR-002, ADR-003, ADR-004, ADR-007,
ADR-008, ADR-016, ADR-017, ADR-019, ADR-020, ADR-021, ADR-022, ADR-023, ADR-025,
`docs/architecture/domain-information-model.md`

This ADR is non-binding while its status is `Proposed`. It supplies no prompt, persona, policy,
provider, model, voice, surface, scheduler, environment, secret, role, threshold, or retention
value. It authorizes no schema, migration, contract, event, configuration activation, runtime
implementation, or production use.

OD-034 covers more than configuration. Accepting this ADR alone cannot close OD-034 or authorize
restricted generation data, approved-content storage, memory, knowledge, archive, publication,
retention, deletion, or terminal lifecycle implementation. A valid protected disposition must
name the exact accepted scope and keep every uncovered capability explicitly OPEN and disabled.

## Context

VNova behavior depends on related persona, prompt, policy, scheduler, provider, model, voice,
surface, and other definitions. Treating those values as mutable rows, selecting `"latest"`, or
updating them independently can make one turn use a combination that no reviewer approved.
Using a mutable label or provider alias as identity also makes incident reconstruction and
rollback unreliable.

Configuration is not permission. An active provider profile cannot approve generated content;
an active voice cannot manufacture talent rights; an active surface cannot authorize final
presentation. Operational provider health is also not a new configuration version.

The system therefore needs immutable definitions, a separately authorized and scoped activation
decision, a deterministic resolution snapshot, and explicit restrictive overrides. It also
needs concurrency, rollback, cache, in-flight work, and database-failure rules before any
configuration schema can be designed.

## Decision

VNova separates these governed concepts:

1. a stable **definition root** that names one semantic configuration family member;
2. a non-selectable **definition draft** with explicit authoring revisions;
3. an immutable **definition version** containing one canonical configuration value;
4. separate, monotonic **definition-version and activation-set eligibility state**;
5. an immutable **activation-set version** containing one reviewed, compatible collection of
   exact definition versions;
6. authoritative **scoped activation state and transitions** that select or explicitly
   deactivate an activation set with a monotonic epoch;
7. an immutable, non-effective **activation schedule** for any future intent;
8. an immutable **resolved configuration snapshot** pinned to the work that used it.

Restrictive capability state, rights state, emergency-stop state, session ownership, and provider
health remain separate authorities. Their epochs are recorded together where needed but are
never collapsed into one generic configuration epoch.

### Definition Root And Version

A definition root has a stable, opaque, VNova-owned identity and a closed definition family.
A `DefinitionDraft` is a non-selectable authoring workspace. Draft edits use an explicit draft
revision and compare-and-swap or equivalent concurrency control; they never mutate a published
version. Publishing a draft revision creates a new `DefinitionVersion` with a new immutable
identity and canonical digest. Review evidence binds that exact version identity and digest, not
a mutable draft, filename, branch, or label.

Each definition version is immutable from creation and binds:

- root and version identity;
- canonical digest and canonicalization profile;
- source draft revision, author, and creation provenance;
- compatibility declarations;
- data classification and access-policy reference;
- secret, credential, restricted-content, rights, retention, and policy references where
  applicable.

No edit is permitted before or after eligibility under the same version identity. Corrections
create a new draft revision and then a new immutable version.

`DefinitionVersionEligibility` is a separate authoritative current-state record keyed by the
exact version. Every eligibility transition has its own immutable identity, expected and
resulting strictly increasing `eligibility_epoch`, state, actor/workload, protected review
evidence, reason, effective/expiry time where allowed, audit, event-manifest, and outbox evidence.
Withdrawal, deprecation, expiry, revocation, deletion, supersession, or incompatibility changes
this state; it never rewrites the version or earlier evidence.

Names, display labels, slugs, filenames, provider aliases, vendor model names, and the word
`latest` are never durable selection keys. Credentials and raw restricted content are never
embedded in an ordinary definition. A protected reference does not turn a secret or content
record into configuration metadata.

The proposed draft lifecycle is `editing`, `abandoned`, or `published`. The proposed immutable
version eligibility vocabulary is `under_review`, `eligible`, `deprecated`, `withdrawn`,
`expired`, and `superseded`. Draft state is never activation eligibility. Exact names,
transition authority, terminality, and retention remain subject to OD-034 and the domain-record
lifecycle catalog.

### Activation Set Version

An activation-set version is an immutable, reviewed bundle of exact definition-version
identities that must change atomically for one configuration family or compatibility unit. It
binds:

- activation-set root and version identities;
- member definition root/version identities and canonical digests;
- its own canonical digest and canonicalization profile;
- declared family and target-scope profile;
- resolver and compatibility-profile versions;
- required safety, rights, surface, capability, and data-policy references;
- creation and authoring provenance.

The bundle boundary is not assumed to be the entire product. Human reviewers must choose which
definitions must be activated atomically. A bundle cannot contain a wildcard, floating range,
mutable alias, implicit default, or provider response. Partial application is invalid.

`ActivationSetEligibility` follows the same separate monotonic-state pattern as definition
eligibility, with its own immutable transitions and `eligibility_epoch`. It becomes eligible only
when protected review binds the exact set digest and every member identity/digest. A member
eligibility change does not mutate the set; current use eligibility is re-evaluated under the
accepted family policy and restrictive-precedence rules.

### Typed Scope And Composition

Every activation target has a required environment identity and exactly one closed,
family-approved resource scope. Candidate resource kinds include environment, talent,
character, stream session, provider capability, and broadcast surface. No organization,
tenant, wildcard, or arbitrary tag scope exists until a protected decision defines it.

Each configuration family declares:

- allowed target kinds;
- whether a broader baseline is required;
- which narrower overrides are allowed;
- one deterministic composition rule;
- conflict and missing-input behavior;
- whether the family may affect in-flight work;
- the protected roles/capabilities allowed to propose, approve, activate, restrict, and restore.

The proposed composition vocabulary is:

- **replace:** one exact activation set replaces the broader selection;
- **restrictive intersection:** all applicable sets apply and the most restrictive result wins;
- **reviewed overlay:** a closed, typed overlay order with field-level merge semantics fixed by
  the family contract.

There is no universal "most specific wins" rule. Time, insertion order, display label, map
iteration, database row order, or event arrival cannot break a tie. Multiple effective
activations at the same unique scope, incomparable scopes, an unauthorized override, conflicting
sets, missing required baseline, or unknown composition semantics fail closed for the affected
capability.

### Scoped Activation State And Transition

The authoritative current state for a reviewed activation binding is keyed conceptually by
environment, typed resource scope, and activation family. It contains a closed
`activation_state` of `inactive` or `active`, a strictly increasing `activation_epoch`, and an
exact activation-set version if and only if active. Absence of a binding row is not silently
equivalent to either state.

The closed transition operations are:

- `initialize`: create an explicitly inactive binding from no binding;
- `activate`: move an inactive binding to one exact eligible activation set;
- `replace`: move an active binding to a different exact eligible activation set;
- `deactivate`: move an active binding to explicit inactive state and remove the current
  selection without deleting history;
- `rollback`: move forward to an exact previously used `ActivationSetVersion` that is still
  currently eligible and compatible.

Every operation advances `activation_epoch` exactly once. A no-op or idempotent retry returns the
original outcome; it does not manufacture another epoch. Deactivation is never implemented by
deleting a binding or activation row.

Every change creates an immutable `ActivationTransition` that binds:

- transition and binding identities;
- environment and exact typed target;
- operation plus previous and next activation states;
- previous and next activation-set versions, each present exactly when its corresponding state
  is active;
- expected and resulting activation epochs;
- effective, expiry, and requested times as applicable;
- authenticated actor or workload, authorization decision, and separation-of-duties evidence;
- command identity, idempotency scope, reason category, and protected evidence references;
- compatibility and preflight result;
- whether the transition is restrictive, equivalent, or widening;
- superseded transition and rollback lineage.

The current state, new epoch, transition, minimized audit record, every required domain-event
record, transition manifest, and corresponding outbox records commit atomically in PostgreSQL
using compare-and-swap or equivalent aggregate serialization. A reused idempotency identity with
different canonical intent is rejected and audited. A stale expected epoch cannot overwrite a
newer decision.

Every family declares the result of an inactive or missing binding. It is either explicit denial
or a reviewed resolution to named broader binding kinds; there is no implicit default. Removing
a narrow selection can expose a broader baseline and therefore is not automatically restrictive.
The resolver compares the before/after effective result: any fallback that expands capability,
content, provider, surface, data access, or eligible work is a widening transition and requires
the full protected widening path. Unknown, incomparable, or unprovable fallback fails closed.

Under ADR-023, the stable activation-binding aggregate whose current state and epoch changed is
the proposed authoritative event subject for activation facts; the immutable
`ActivationTransition` identity is transition evidence in the payload. The target resource
scope is separate from subject, session and turn are correlation only, and raw configuration or
content is never placed in the event.

### Resolution And Work Pinning

The deterministic resolver produces an immutable `ResolvedConfigurationSnapshot` containing:

- environment and exact work/resource scope;
- every selected definition root/version identity and digest;
- activation-set and transition identities;
- activation epochs for every participating scope;
- current definition-version and activation-set eligibility epochs and transition identities for
  every selected input;
- resolver and compatibility-profile versions;
- applicable restrictive, rights, surface, session, and emergency epochs or references;
- resolution time, validity bound, and canonical snapshot digest;
- a result of `resolved` or a closed, non-sensitive failure reason.

A stream session, turn, attempt, safety evaluation, synthesis request, surface decision, task, or
other governed work records the exact snapshot identity required by its contract. A turn never
swaps definition versions mid-execution.

Retry, rewrite, provider fallback, reconnect, restore, queueing, or cache fill cannot silently
select a newer snapshot. A new attempt may use a new snapshot only when the accepted turn and
policy model explicitly permits it and records the lineage; safety and surface decisions then
evaluate the exact new inputs. A stale, missing, ambiguous, expired, withdrawn, revoked, deleted,
or incompatible input makes resolution fail closed.

Pinning preserves historical meaning; it is not a lease that defeats a later restriction.
Admission, safety minting, synthesis/content resolution, surface authorization, dispatch, and
immediate pre-playback checks revalidate the current eligibility epochs required by their
contracts. An epoch mismatch, unknown state, or restrictive eligibility transition holds,
cancels, expires, or re-resolves affected work under the accepted family policy and cannot widen
authority. Withdrawal, revocation, deletion, incompatibility, or other restrictive ineligibility
propagates immediately to every reachable enforcement point even when the activation binding's
epoch did not change.

### Precedence And Independent Authority

Configuration activation never mints or implies:

- `ApprovedResponse`;
- `VoiceUseAuthorization`;
- `SurfaceAuthorization`;
- operator or workload authorization;
- e-stop reset;
- publication, replay, archive, export, or derivative-use permission;
- data access, retention, deletion, or legal-hold authority.

The mandatory precedence is:

1. e-stop, emergency disable, deletion/hold prohibition, rights revocation, explicit
   suspension, expiry, incompatibility, and other accepted restrictive authorities deny use;
2. an exact current scoped activation may permit eligibility only within those restrictions;
3. a broader reviewed baseline applies only when the family explicitly permits inheritance.

An allow cannot override a deny from another mandatory authority. The current epoch of every
applicable authority is verified at its required enforcement points.

Provider availability, health, circuit, rate-limit, quota, latency, and cost state are
operational observations. They may make an active profile temporarily ineligible, but they do
not edit its definition, advance configuration epoch, widen fallback, or select an unreviewed
provider.

### Restrictive Change, Widening, And In-Flight Work

Transitions have directional safety semantics:

- A restrictive transition applies immediately at every reachable enforcement point. Pending
  affected work is held, cancelled, or revalidated according to an accepted family policy; it
  is never grandfathered merely because it cached an older allow.
- A widening transition requires protected review, authorization, successful preflight, and
  committed current state before it affects new work.
- Normal replacement starts new work with the new snapshot. Existing work follows one reviewed
  family disposition: finish with the exact still-eligible snapshot, hold for revalidation, or
  cancel.
- Safety-, rights-, surface-, deletion-, and emergency-related uncertainty takes the
  restrictive disposition. No placeholder default may silently choose otherwise.

The exact disposition for each family remains OPEN. The system must not implement a generic
in-flight fallback.

### Rollback

Rollback is a new forward activation transition selecting an exact, previously used
`ActivationSetVersion` that is still currently eligible and compatible. A bare
`DefinitionVersion` is never a rollback target. Reusing an older definition requires selecting a
newly or previously reviewed activation-set version that contains that exact definition version
and passes every current member, bundle, compatibility, scope, and preflight check. The rollback
receives a new transition identity, epoch, audit, event manifest/outbox evidence, review evidence,
and snapshot.

Rollback never decrements an epoch, edits history, resurrects withdrawn/deleted/revoked content,
restores an old authorization, reopens terminal work, or changes the snapshot recorded on
completed work. A rollback that cannot pass current preflight fails closed.

### Emergency Disable And Database Failure

Emergency disable is a separate, typed, scoped restrictive latch. It is not implemented by
editing or deleting definitions and does not wait for an ordinary activation workflow.

An authorized safe-direction command takes immediate process-local effect even when PostgreSQL
cannot confirm the transition, following ADR-004's `uncommitted_restrictive` pattern. The
affected capability cannot resume until durable authoritative state, epoch, audit, event
manifest, and outbox evidence reconcile successfully. Re-enable requires a new epoch,
authenticated protected authority, explicit confirmation, fresh
compatibility/rights/surface/safety preflight, and no remaining restrictive state.

This ADR does not define e-stop scope or reset behavior; ADR-015 and its Open Decisions remain
the authority for that capability.

Integrity, stale-epoch, eligibility, schedule, cache, rollback, and database-failure incidents
follow the Proposed
[configuration activation, eligibility, and forward rollback runbook](../runbooks/configuration-activation-and-rollback.md);
that procedure grants no implementation or production authority.

### Scheduled Activation And Time

An `ActivationSchedule` is a separate immutable intent record. A distinct
`ActivationScheduleState` has a monotonic `schedule_epoch` and closed proposed states of
`scheduled`, `cancelled`, `expired`, `superseded`, `executed`, and `failed`; immutable state
transitions preserve actor/workload, reason, idempotency, and audit evidence. Creating or changing
schedule state never edits current activation state or advances its epoch. The immutable intent
binds an exact desired transition operation, target binding, expected activation epoch,
definition/set eligibility epochs, not-before and expiry constraints, command/idempotency
identity, actor and protected review evidence, reason, and preflight profile. The target-set field
is operation-discriminated: `activate`, `replace`, and `rollback` require one exact
`ActivationSetVersion`, while `initialize` and `deactivate` prohibit a target set. The ordinary
operation's source-state precondition and resulting inactive/active state remain authoritative;
no schedule may carry an irrelevant set or leave a set selected in inactive state.

At the due time, an authorized scheduler first compare-and-swaps the exact still-`scheduled`
state/epoch and revalidates the accepted authoritative clock, expected binding epoch, every
current eligibility epoch, actor/workload authority, compatibility, scope,
restrictive/widening classification, and complete preflight. Only then may it commit the ordinary
forward `ActivationTransition` and the schedule's `executed` transition atomically with current
binding state, audit, event manifest, and outbox evidence. A stale, conflicting, expired,
cancelled, superseded, failed, or uncertain schedule produces no activation and terminates or
remains held under its closed state machine; it never retargets itself, activates early, replaces
current state, or falls back to a different set.

Schedule cancellation and supersession are explicit idempotent terminal dispositions with audit
evidence. Reusing an idempotency identity with different schedule intent is an integrity error.
Expiry is restrictive. Clock uncertainty, backward steps, unavailable time authority, or stale
scheduler state cannot activate early, extend expiry, or restore a prior set.

Exact timestamp, UTC, monotonic clock, skew, lease, and scheduling behavior depends on OD-035.
Until it is decided, scheduled production activation remains disabled.

`ActivationSchedule` remains configuration-authority work, not a `StreamSession` trigger. It uses
its own scheduler/workload authorization and schedule epoch. ADR-025's actor ownership,
`TriggerOccurrence`, timer claim, and turn-admission semantics apply only when the scheduled fact
belongs to a session-runtime trigger; neither schedule type may impersonate or silently convert
into the other.

### Privacy, Restricted Content, And Evidence

- Prompt/persona content, policy content, secrets, credentials, provider payloads, raw generated
  content, approved content, viewer memory, identity evidence, contracts, and legal evidence do
  not enter ordinary activation, event, audit, log, metric, or trace records.
- Activation and audit evidence use opaque IDs, approved digests, versions, classifications,
  outcomes, actors, and reason categories.
- A digest of low-entropy or identifying content remains linkable and is not automatically safe
  for ordinary metadata. Keyed or opaque references and access domains require privacy review.
- Viewer memory and audit retain separate tables, content, and access roles.
- Definitions, activation state, restricted content, approved-content snapshots, memory,
  artifacts, and public archives may require independent retention, hold, deletion, and access
  policies.

This ADR selects no storage location, retention duration, role, keying mechanism, or
classification default.

## Schema And Implementation Gate

No configuration, activation, snapshot, lifecycle, or event schema or migration is authorized
until:

- the Runtime Implementation Gate is validly closed for the named increment;
- ADR-002, ADR-003, ADR-004, ADR-008, ADR-017, ADR-023, this ADR, and every applicable
  feature-specific ADR are Accepted or replaced;
- an inherited, still-valid OD-033 disposition identifies the accepted ADR-023 event model, and a
  separate OD-034 disposition identifies the exact lifecycle-catalog rows and ADR-024 scope being
  implemented; each disposition is bound to its own immutable reviewed subject under OD-040 and
  the latter explicitly references the former dependency;
- applicable identity/role, surface, rights, media, retention, memory, archive, and clock
  decisions are closed for the exact scope being implemented;
- the domain-record lifecycle catalog is protected-reviewed with field-level classification,
  access, retention, deletion, hold, restore, lineage, and authority profiles;
- a linked migration ADR defines tables or objects, constraints, transactions, indexes,
  row-level access, encryption, backups, restore, rollback, and catalog traceability;
- exact implementation paths receive CODEOWNERS coverage and protected remote CI.

## Alternatives Considered

### Mutable Configuration Rows

Rejected. In-place edits destroy historical meaning, make rollback ambiguous, and allow completed
work to appear governed by values it never used.

### Select The Most Recent Version

Rejected. "Most recent" can change between reads, depends on clock or commit ordering, and does
not prove review, scope, compatibility, or authorization.

### Independently Activate Every Definition

Rejected as a universal model. It permits partial mixed configurations. Human review must define
the compatibility units that change atomically.

### One Global Configuration Bundle

Rejected. It creates an unnecessary serialization and blast-radius boundary and cannot express
reviewed talent, character, session, surface, or capability isolation.

### Universal Most-Specific-Wins Scope

Rejected. Configuration families have different composition and restriction semantics.
Ambiguous or incomparable scopes must not be resolved by inference.

### Roll Back The Epoch Or Restore A Database Snapshot

Rejected. Either can resurrect revoked decisions, make stale caches current, and rewrite audit
history. Recovery and rollback always move forward.

### Encode Emergency Disable As A Configuration Version

Rejected. A safe-direction action must remain available when ordinary authoring, review,
activation, cache, or database paths are degraded.

## Enforcement And Verification

Once implementation is separately authorized, it must include:

- nominal generated identities that prevent root, version, activation, snapshot, epoch, rights,
  surface, and session IDs from being substituted;
- protected command capabilities and separation-of-duties checks for proposal, review,
  activation, restriction, rollback, and re-enable;
- draft/version separation plus immutable-version and canonical-digest enforcement;
- unique current-binding, closed active/inactive state, expected activation/eligibility epochs,
  idempotency, eligibility, and atomic-bundle constraints;
- transaction tests proving state, epoch, audit, required event manifest, and every outbox record
  commit together;
- deterministic resolver fixtures for every family, allowed scope, override, composition,
  conflict, and missing-input case;
- cache and consumer checks that reject stale activation or eligibility epochs and never infer
  `latest`;
- import and dependency boundaries preventing providers, the operator console, stage host,
  Redis, or telemetry from becoming activation authority;
- minimized audit/event/telemetry schemas and restricted-content leakage tests;
- reconstruction tooling that can explain an exact completed snapshot without using mutable
  current configuration.

## Acceptance Evidence

Human architecture, product, safety, privacy, security, data, operations, talent/rights, and
configuration owners must approve:

- definition families, draft/version and eligibility-state boundaries, lifecycle vocabulary,
  compatibility units, and activation-set granularity;
- the typed scope lattice, allowed family overrides, composition rules, tie behavior, and
  environment partition;
- transition authority, closed initialize/activate/replace/deactivate/rollback semantics,
  separation of duties, idempotency, activation/eligibility epochs, schedule intent, expiry,
  emergency-disable, and re-enable semantics;
- each family's restrictive/widening classification and in-flight-work disposition;
- the independent safety, rights, surface, deletion, publication, and emergency precedence;
- classification, access, retention, hold, deletion, restore, and evidence rules;
- exact schema, migration, ownership, and remote protected-CI plan.

Executable evidence must then include:

- concurrent activation, stale expected activation/eligibility epoch, duplicate,
  conflicting-idempotency, and same-scope uniqueness tests;
- draft-edit/publish races and proof that review evidence can bind only one immutable
  version/digest;
- initialize, activate, replace, deactivate, and forward-rollback transition tests, including
  inactive/missing binding, explicit-deny, allowed-baseline, and deactivation-causes-widening
  cases;
- partial-bundle failure and transaction-abort tests proving no mixed activation becomes
  visible;
- deterministic resolution across allowed baselines, overrides, intersections, overlays,
  conflicts, and incomparable scopes;
- snapshot pinning across retry, fallback, reconnect, cache eviction, replica lag, restore,
  current-version change, definition withdrawal, and activation-set eligibility change;
- restrictive transition, widening review, every family in-flight disposition, expiry,
  withdrawal, revocation, deletion, and incompatibility tests;
- forward rollback tests proving epochs and history never move backward and old work or
  authorizations do not resurrect;
- emergency-disable tests during database, Redis, identity-provider, console, and network
  failure, followed by deliberate reconciliation and re-enable;
- provider-health/fallback tests proving operational state cannot edit configuration or widen
  eligibility;
- scheduled-intent tests for cancellation, supersession, duplicate delivery, stale binding or
  eligibility epoch, operation-discriminated target-set presence/absence, due-time revalidation,
  transaction failure, and clock uncertainty under the accepted OD-035 profile;
- access-control, minimized audit, event, log, metric, trace, and restricted-content leakage
  tests;
- incident reconstruction using only exact immutable versions, transitions, snapshots, and
  authoritative evidence.

## Consequences

- Completed work remains reproducible against exact reviewed configuration.
- Related definitions can change atomically without a universal product-wide lock.
- Scope, precedence, rollback, and restrictive behavior become explicit and fail closed.
- Configuration cannot be mistaken for content, rights, surface, publication, or operator
  authority.
- Additional version, activation, snapshot, epoch, and review records increase storage,
  transaction, tooling, and operational complexity.
- No configuration value, schema, migration, activation, runtime feature, or production
  capability is authorized by this Proposed ADR.

## OPEN Decisions

- OD-034 must accept or replace the stable root/version/set/activation/snapshot model and name
  every retained OPEN or disabled domain capability.
- Human reviewers must choose definition families, activation-set granularity, lifecycle states,
  scope lattice, override eligibility, composition rules, and in-flight dispositions.
- ADR-019 and OD-022 must define human/workload roles, capabilities, authentication,
  confirmation, and separation of duties for each transition.
- ADR-020 and OD-013 must define mode and degradation effects without using mode as
  authorization.
- ADR-021, ADR-022, and Open Decisions OD-023, OD-024, and OD-025 must define surface, voice
  rights, media, and asset policy before those families are activated.
- OD-009, OD-026, OD-032, and the lifecycle catalog must define retention, memory/knowledge,
  archive/publication, deletion, hold, and restoration profiles.
- OD-035 must define scheduling, clock uncertainty, expiry, and deadline behavior.
- Exact schema, transaction isolation, partitions, indexes, cache design, resolver placement,
  configuration service ownership, and migration/recovery mechanics remain future protected
  decisions.
