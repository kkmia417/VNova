# Configuration Activation, Eligibility, And Forward Rollback

Status: Proposed operational runbook; readiness state: `Drafted`; no implementation, command,
schema, configuration, rollback, or production authority

Governing sources:

- [`AGENTS.md`](../../AGENTS.md)
- [ADR-004: PostgreSQL outbox and Redis Streams](../adr/0004-postgresql-outbox-and-redis-streams.md)
- [ADR-008: safety gate enforcement](../adr/0008-safety-gate-enforcement.md)
- [ADR-017: data retention, privacy, and PII](../adr/0017-data-retention-privacy-and-pii.md)
- [ADR-019: authentication, authorization, and operator roles](../adr/0019-authentication-authorization-and-operator-roles.md)
- [ADR-020: mode transition and degradation matrix](../adr/0020-mode-transition-and-degradation-matrix.md)
- [ADR-023: event subject, scope, correlation, ordering, and completeness](../adr/0023-event-subject-scope-correlation-and-ordering.md)
- [ADR-024: versioned configuration and scoped activation](../adr/0024-versioned-configuration-and-scoped-activation.md)
- [Domain record lifecycle catalog](../architecture/domain-record-lifecycle-catalog.md)
- [Threat model TM-18](../security/threat-model.md#tm-18-configuration-activation-rollback-or-cache-manipulation)
- [Operational runbook contract](README.md)

This document defines fail-closed containment and forward-only recovery semantics. It does not
select configuration families, schemas, storage, commands, roles, thresholds, cache products,
clock values, retention, or deployment-specific procedures.

## Purpose And Entry Conditions

Enter this runbook when any configuration authority or dependent enforcement point is uncertain,
including:

- a published definition or activation-set identity appears to have changed content or digest;
- review evidence does not bind the exact immutable identity and digest;
- a partial activation bundle or state/audit/outbox mismatch is visible;
- the current binding state, selected set, or activation epoch disagrees across PostgreSQL,
  replicas, caches, runtime actors, or operator views;
- an inactive or deactivated narrow binding unexpectedly resolves to a broader or more permissive
  baseline;
- a stale activation or definition/set eligibility epoch remains usable;
- a withdrawn, expired, superseded, deleted, incompatible, or held input continues to affect work;
- a scheduled intent appears effective early, executes after cancellation/supersession, or runs
  without due-time revalidation;
- rollback decrements an epoch, edits history, or revives withdrawn content or authority;
- emergency disable took process-local effect while PostgreSQL was unavailable;
- unauthorized authoring, review, activation, scheduling, rollback, or re-enable is suspected;
- restored data or cache warmup could resurrect an obsolete selection.

A credible integrity or authority mismatch is enough to enter restrictive containment. Do not
wait for audience-visible output.

## Non-Negotiable Invariants

- A mutable `DefinitionDraft` is never selectable. Every published `DefinitionVersion` and
  `ActivationSetVersion` is immutable from creation.
- Review evidence binds one exact immutable identity and canonical digest.
- Definition-version eligibility, activation-set eligibility, and scoped activation are separate
  authorities with separate monotonic epochs.
- Binding state is explicitly `inactive` or `active`; absence or row deletion never implies a
  reviewed fallback.
- Initialize, activate, replace, deactivate, and rollback are serialized forward transitions.
  Deactivation and rollback advance the activation epoch.
- An `ActivationSchedule` is non-effective intent. Only a newly committed ordinary transition
  may change current state at due time.
- A pinned `ResolvedConfigurationSnapshot` preserves historical meaning but cannot defeat a later
  restrictive eligibility, rights, deletion, hold, e-stop, or emergency transition.
- PostgreSQL is authoritative. Redis, a cache, replica, operator screen, log, trace, provider
  response, or restored snapshot cannot establish current activation or eligibility.
- Emergency disable and safe-direction local restriction remain available during database or
  control-plane failure. `uncommitted_restrictive` never means durable success.
- Rollback is a new forward selection of a still-currently-eligible exact activation-set version.
  An older definition is usable only through a currently reviewed compatible set containing that
  exact version. No epoch, history, terminal decision, approval, right, or publication authority
  moves backward.
- Configuration activation never mints `ApprovedResponse`, rights/surface authorization, e-stop
  reset, data access, archive/publication permission, or operator authority.
- Recovery, green telemetry, an empty queue, cache convergence, or dependency health never
  re-enables capability or raises mode automatically.

## Required Response Functions

| Function                | Responsibility                                                                                                   |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Incident commander      | Owns scope, containment generation, handoff, evidence completeness, and exit decision                            |
| Safety/operations lead  | Chooses the strongest accepted restrictive output/mode posture and validates deliberate re-enable                |
| Configuration owner     | Owns roots, drafts, immutable versions/sets, eligibility evidence, resolver profile, and intended selection      |
| Runtime owner           | Holds affected admission/work, identifies snapshots and enforcement points, and prevents stale-cache use         |
| Data/transport owner    | Reconciles PostgreSQL state/transitions/audit/outbox/manifests, replicas, delivery, and cache invalidation       |
| Identity/security owner | Contains suspect principals, sessions, credentials, review/activation capability, tampering, and evidence access |
| Privacy/rights owner    | Owns restricted-content, deletion/hold, talent/rights, and reclassification precedence                           |
| Stage operator          | Verifies actual output and retains local stop/watchdog control when affected work may have reached the rig       |
| Recorder                | Maintains minimized identities, epochs, digests, unknowns, actions, approvals, and evidence references           |

No responder may repair an incident by editing an immutable record, selecting `latest`, deleting
a binding, bypassing protected review, reusing an old authorization, or treating a cache as
authority.

## Immediate Containment

1. **Protect audience output.** If affected work may have reached dispatch or playout, stop new
   dispatch and use the already-authorized local/cloud restrictive controls. Engage local hard
   stop when actual output or control is unsafe.
2. **Freeze affected capability.** Apply the narrowest provably sufficient emergency disable,
   admission hold, Mode ceiling, or broader safe hold. Unknown scope is contained broadly enough
   to prevent cross-scope leakage.
3. **Stop mutation and propagation.** Pause affected authoring publication, eligibility changes,
   activation, schedule execution, rollback, cache fill, replica promotion, restore, and backlog
   release. Do not block safe-direction restriction.
4. **Fence suspect authority.** Revoke or suspend compromised human/workload sessions and
   activation capabilities through the accepted identity procedure without destroying evidence.
5. **Hold dependent work.** Identify every session, turn, safety evaluation, synthesis/surface
   decision, media task, archive/export job, and restore/rebuild operation pinned to affected
   snapshots. Hold, cancel, expire, or revalidate under the accepted family policy; never
   grandfather a cached allow.
6. **Preserve exact evidence.** Record opaque root/draft/version/set/binding/transition/schedule/
   snapshot identities, canonical digests, activation and eligibility epochs, command/
   idempotency identities, actors, times, and authoritative references. Do not copy prompt,
   persona, policy, secret, generated/approved content, memory, contract, or identity evidence
   into ordinary incident records.
7. **Keep the recovery hold.** Fault clearance, database return, cache eviction, or a successful
   read is diagnostic progress only.

## Establish The Authoritative View

Read through the protected PostgreSQL authority with explicit timeouts and collect:

- exact definition root, source draft revision, immutable version identity/digest, and creation
  provenance;
- definition-version and activation-set current eligibility state, epoch, transition, protected
  review evidence reference, reason, expiry, and outbox/audit relationship;
- activation-set identity/digest, exact member identities/digests, compatibility and resolver
  profile;
- binding identity, explicit inactive/active state, selected set when active, activation epoch,
  and family-specific missing/inactive/fallback rule;
- complete initialize/activate/replace/deactivate/rollback transition history, expected/result
  epochs, direction classification, actor/workload authority, idempotency identity, and
  state/audit/outbox atomicity;
- pending and terminal schedules, immutable intent, current schedule state/epoch, exact desired
  operation and its operation-discriminated target set, expected activation/eligibility epochs,
  not-before/expiry, cancellation/supersession, and due-time execution result; verify that
  `activate`/`replace`/`rollback` have one exact set and `initialize`/`deactivate` have none;
- every affected resolved snapshot and its pinned versions, set/transition identities,
  activation/eligibility epochs, resolver profile, restrictions, validity, and digest;
- dependent work and current safety, mode, e-stop, rights, surface, deletion/hold, publication,
  and emergency epochs;
- event transition manifests, expected-delivery/high-water, consumer evidence, and cache/replica
  generations needed to prove propagation.

Missing, contradictory, unreadable, or partially committed evidence is a blocker. Do not fill a
gap from Redis, cache, telemetry, a provider dashboard, or operator memory.

## Classify The Failure

| Observation                                                                 | Required interpretation and containment                                                                                  |
| --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Same immutable identity has different content/digest                        | Integrity/security incident; quarantine every related set, snapshot, artifact, and dependent use                         |
| State/epoch changed without matching transition, audit, manifest, or outbox | Authoritative integrity or transaction failure; keep capability disabled and escalate data recovery                      |
| Cache/replica is stale while PostgreSQL is coherent                         | Keep stale generation fenced; invalidate/rebuild only from exact current state and epochs                                |
| Deactivation exposes broader behavior                                       | Treat as widening unless the accepted family proof says otherwise; require protected widening authorization              |
| Eligibility epoch changed but activation epoch did not                      | Expected independent restriction; invalidate/hold affected use and propagate the new eligibility state                   |
| Schedule is early, stale, cancelled, or superseded                          | It cannot transition current state; terminate/hold it and investigate scheduler/clock/authority                          |
| Rollback points to ineligible or incompatible history                       | Reject rollback; history remains evidence only                                                                           |
| Local emergency disable lacks durable PostgreSQL evidence                   | Maintain `uncommitted_restrictive`; retry bounded persistence and prohibit recovery until reconciliation                 |
| PostgreSQL and restored/cache state disagree                                | PostgreSQL plus newer accepted restrictions dominate; quarantine restored/cache state                                    |
| Unauthorized actor or forged review evidence                                | Security/identity incident; fence authority, preserve chain of custody, and expand scope based on verified relationships |

## Forward-Only Recovery

1. Repair availability and control paths without changing configuration semantics.
2. Verify immutable identity/digest closure from definitions through sets, eligibility,
   bindings, transitions, schedules, snapshots, and dependent records.
3. Reconcile any `uncommitted_restrictive` state into one durable authoritative transition,
   minimized audit, event manifest, and outbox transaction. If exact intent cannot be proved,
   retain the stronger restriction.
4. Decide the desired current state through the accepted protected authority. If change is
   needed, issue a new initialize/activate/replace/deactivate/rollback command with the current
   expected epoch; never patch or decrement existing state.
5. Treat rollback as current re-selection: revalidate the old set and every member's current
   eligibility epoch, compatibility, rights, surface, deletion/hold, emergency, and policy
   prerequisite.
6. Leave stale/cancelled/superseded schedules terminal. A replacement schedule receives a new
   identity. Due execution compare-and-swaps its current schedule epoch and commits the ordinary
   activation transition plus `executed` schedule disposition atomically.
7. Invalidate/fence affected cache and replica generations, then rebuild from the exact committed
   binding, eligibility, and resolver evidence. Cache convergence alone is not an exit gate.
8. Re-resolve new work. Existing work follows its accepted family disposition and revalidates
   current eligibility/restriction at every protected enforcement point.
9. Reconcile outbox manifests, required consumers, runtime actors, operator views, and affected
   rigs without treating transport receipt as authority.
10. Exercise the exact repaired path in deterministic rehearsal and on the required target before
    deliberate re-enable.

## Abort And Safe-Hold Conditions

Remain disabled or safe-held when:

- PostgreSQL cannot prove one coherent current binding and eligibility state;
- immutable digest, review evidence, actor authority, or transaction atomicity is uncertain;
- a broader fallback or widening classification cannot be proved;
- a restrictive transition or protection overlay may not have reached every enforcement point;
- required current rights, deletion/hold, surface, safety, mode, e-stop, or emergency state is
  missing;
- schedule time authority or due-time prerequisite is uncertain;
- stale snapshots, caches, replicas, tasks, media, archives, or restores can still be used;
- an external operation repeatedly times out or retry would exceed its accepted bound;
- recovery would require editing history, inventing a default, bypassing review, or reusing an
  expired/withdrawn authorization.

## Recovery Exit Gates

Recovery is eligible for human consideration only when:

- every affected immutable identity/digest and review reference is coherent;
- definition/set eligibility state and epochs are current and propagated;
- each binding has one explicit state, exact current epoch, and complete forward transition/
  audit/event-manifest/outbox evidence;
- every schedule is provably pending, terminal without effect, or executed through one ordinary
  transition;
- deactivation/fallback and restrictive/widening classification match the accepted family
  contract;
- every affected snapshot and dependent use is reconciled; stale or ineligible work cannot reach
  synthesis, surface authorization, dispatch, replay, export, or playout;
- current restrictive, safety, rights, deletion/hold, mode, e-stop, and emergency authorities are
  known and dominate configuration;
- caches, replicas, runtime actors, consumers, operator views, and rigs agree with PostgreSQL or
  remain fenced;
- monitoring and alert routes are current, and no evidence depends on Redis history;
- deterministic and target-specific negative tests pass for the exact versions;
- an authorized human reviews the evidence, records the reason/confirmation, and creates a new
  re-enable/activation epoch where required.

No gate permits automatic mode increase, e-stop reset, rights restoration, or replay of in-doubt
work.

## Evidence Packet

Record:

- incident, environment, typed target/family, root/draft revision/version/set/binding/transition/
  schedule/snapshot, activation/eligibility/restriction, command/idempotency, audit/event/
  manifest/outbox, consumer, cache/replica, release, session/turn/task, rig, and trace identities;
- canonical digests and the exact relationships checked, without restricted values;
- authoritative PostgreSQL read/transaction/restore evidence and every mismatch;
- requested, previous, effective, and resulting state/epoch plus restrictive/widening
  classification;
- explicit timeout, retry, cancellation, schedule, cache invalidation, and reconciliation
  outcomes;
- affected data classes, evidence access/retention/hold, and any security/privacy/rights scope;
- rehearsal/target identities, deterministic seed, injected fault, expected and actual outcome,
  artifact hashes, and negative-control result;
- containment, continued-safe-operation, forward transition, rollback, and deliberate re-enable
  decisions;
- unresolved gaps, severity, owner, disposition, reviewers, validity scope, and invalidation
  triggers.

## Required Rehearsal Scenarios

Before production authorization, exercise:

- mutable-draft publication race and proof that review binds one immutable version/digest;
- same identity/different digest, partial bundle, transaction abort, and state/audit/outbox/
  manifest mismatch;
- concurrent initialize/activate/replace/deactivate/rollback, duplicate intent, conflicting
  idempotency identity, stale expected epoch, and same-scope conflict;
- inactive/missing binding, explicit denial, allowed broader baseline, and deactivation that
  unexpectedly widens effective behavior;
- definition or set withdrawal/expiry/deletion during admission, safety, synthesis, dispatch,
  pre-playback, replay, export, and restore;
- stale eligibility epoch with unchanged activation epoch and stale activation epoch with
  otherwise eligible members;
- schedule cancellation, supersession, duplicate due delivery, early clock, backward step,
  uncertainty, stale prerequisite, invalid target-set presence/absence for the selected
  operation, and transaction failure;
- forward rollback to eligible and ineligible history, proving no epoch/history/authorization
  resurrection;
- database loss during emergency disable, process restart/takeover, bounded persistence retry,
  reconciliation, and deliberate re-enable;
- cache, replica, runtime, consumer, operator view, backup restore, and provider-health
  disagreement;
- unauthorized actor/review substitution, cross-environment/target identity substitution, and
  restricted-content leakage through audit/event/log/trace/incident evidence.

Each scenario proves fail-closed containment, immutable lineage, monotonic epochs, no partial
visibility, no automatic fallback/re-enable, bounded external calls, and zero unauthorized
output.

## OPEN Values And Decisions

Human approval is required for:

- OD-022 identity, authorization, confirmation, separation-of-duties, break-glass, and
  principal/workload capability policy;
- OD-027 incident roles, command/handoff/escalation paths, communications, coverage, evidence
  freshness, and runbook authorization;
- OD-028 security severity, investigation, containment, risk acceptance, and independent review;
- OD-034 exact draft/version/set/eligibility/binding/schedule/snapshot rows, family scopes,
  composition, inactive/fallback, direction, in-flight, access, retention, deletion/hold/restore,
  and terminality;
- OD-035 authoritative time, schedule, expiry, lease, skew, and uncertainty behavior;
- OD-036 signal/alert/dashboard authority, freshness, route failure, and restrictive fallback;
- exact database isolation/constraints, cache/replica design, invalidation fanout, retry bounds,
  recovery targets, target commands, owners, and evidence retention.

Until these are decided and target-validated, this runbook remains `Drafted` and no production
configuration capability is authorized.
