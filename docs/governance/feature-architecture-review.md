# Feature Architecture Review Packet

Status: Proposed artifacts awaiting protected human review

This packet is the decision surface for the feature-specific architecture gates that follow the
[architecture foundation review](architecture-foundation-review.md). It does not accept an ADR,
close an OPEN decision, authorize runtime implementation, or waive protected-file review.

## Review Boundary

The foundation gate and feature gates are cumulative:

1. The foundation gate must be closed first.
2. Every ADR required by a feature must be accepted or replaced before that feature starts.
3. OPEN parameters may remain unresolved only when the accepted ADR explicitly keeps the
   dependent behavior disabled.
4. Database work additionally requires a linked migration ADR.
5. Provider gateways, contracts, safety code, CI, stage-host safety behavior, and live adapters
   retain their protected human-review requirements after the architecture gate closes.
6. Accepted feature architecture still requires threat-model validation, rehearsed runbooks,
   target evidence, and a recorded
   [operational readiness decision](operational-readiness-review.md) before live use.

The ADRs below are handoff-derived proposals. The missing original architecture source and the
unresolved historical ADR-006 reference remain visible in the
[open decision register](../architecture/open-decisions.md); this packet does not reconstruct
unknown history.

## Dependency Order

```text
foundation review (ADR-001, ADR-002, ADR-008, ADR-018, ADR-023; accepted ADR-016/017 constraints)
  |
  +-- inherited ADR-023/OD-033 complete event identity/scope/order/completeness profile
  +-- ADR-024/025 + OD-034 versioned domain/coordination lifecycle schema profile
  |
  +-- ADR-003 session lifecycle
  |     +-- ADR-025 session actor ownership, command ingress, effects, timers, and takeover
  |     +-- ADR-004 durable event delivery
  |     +-- ADR-007 provider gateway
  |           +-- ADR-010 approved media pipeline
  |                 +-- ADR-011 stage-host protocol
  |                       +-- ADR-015 layered e-stop
  |
  +-- ADR-019 operator identity and authorization
  +-- ADR-020 mode transitions and degradation
  +-- ADR-021 broadcast surfaces
  +-- ADR-022 voice rights
  +-- ADR-026 opaque audit references before affected personal-data persistence
  |
  +-- OD-029 conditional disaster-recovery/continuity authority
  +-- OD-035, OD-036, OD-037, OD-038, OD-039 time/observability/capacity/cost/acceptance
```

The diagram communicates review order, not a package dependency graph. ADR-008's exclusive
approval boundary shapes every downstream speech or media path. ADR-010 also depends on the
accepted outcomes of ADR-007, ADR-021, and ADR-022 for each provider, surface, and voice capability
that is enabled.

## Decisions Requested

| Artifact                                                                      | Decision requested        | Acceptance focus                                                                                                                                                           | Status   |
| ----------------------------------------------------------------------------- | ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| [ADR-003](../adr/0003-stream-session-segment-and-turn-lifecycle.md)           | Accept, revise, or reject | Session/segment/turn lifecycle, terminal decisions, attempts, expiry, cancellation, recovery, scheduling                                                                   | Proposed |
| [ADR-004](../adr/0004-postgresql-outbox-and-redis-streams.md)                 | Accept, revise, or reject | PostgreSQL as system of record; transactional outbox; Redis as replaceable transport; replay and ordering                                                                  | Proposed |
| [ADR-007](../adr/0007-provider-gateway-and-fallback-isolation.md)             | Accept, revise, or reject | SDK isolation, explicit timeouts, failure taxonomy, independent safety provider, fallback through safety                                                                   | Proposed |
| [ADR-010](../adr/0010-approved-media-and-tts-pipeline.md)                     | Accept, revise, or reject | Identifier-only synthesis, immutable artifacts, expiry propagation, interruption, approved fallback                                                                        | Proposed |
| [ADR-011](../adr/0011-stage-host-wire-protocol-and-clock-synchronization.md)  | Accept, revise, or reject | Authenticated versioned protocol, signed tasks, replay defense, clock health, reconnect reconciliation                                                                     | Proposed |
| [ADR-015](../adr/0015-layered-emergency-stop.md)                              | Accept, revise, or reject | Local hard stop, cloud freeze, partition precedence, idempotency, audited deliberate resume                                                                                | Proposed |
| [ADR-019](../adr/0019-authentication-authorization-and-operator-roles.md)     | Accept, revise, or reject | SSO boundary, server-side authorization, least privilege, dangerous commands, break-glass controls                                                                         | Proposed |
| [ADR-020](../adr/0020-mode-transition-and-degradation-matrix.md)              | Accept, revise, or reject | Capability matrix, immediate downward transitions, gated upward transitions, automatic degradation                                                                         | Proposed |
| [ADR-021](../adr/0021-broadcast-surface-inventory-and-overlay-policy.md)      | Accept, revise, or reject | Closed renderer inventory, terminal authorization, composed voice gate, owned delayed overlay or no overlay                                                                | Proposed |
| [ADR-022](../adr/0022-voice-rights-and-talent-licensing-metadata.md)          | Accept, revise, or reject | Rights decision/mint, immutable grant plus state epoch, use constraints, revocation and evidence custody                                                                   | Proposed |
| [ADR-024](../adr/0024-versioned-configuration-and-scoped-activation.md)       | Accept, revise, or reject | Draft/immutable-version split, definition/set eligibility epochs, atomic sets, explicit inactive/active bindings, schedules, snapshots, rollback, restrictive change       | Proposed |
| [ADR-025](../adr/0025-session-actor-ownership-command-ingress-and-fencing.md) | Accept, revise, or reject | Composite actor/row-linearized fencing, recovery-bound commands, four-record effects, canonical timers, closed activation/lost-tail recovery, restrictive audience handoff | Proposed |
| [ADR-026](../adr/0026-opaque-audit-references-for-deletable-personal-data.md) | Accept, revise, or reject | Content-independent opaque audit references, resolver separation, deletion evidence, and prohibition of content-derived viewer-data digests                                | Proposed |

ADR-003 appears here because it is the feature lifecycle gate. ADR-025 closes the structural
meaning of its one-logical-actor, command, scheduler, external-effect, and ownership-transfer
assumptions; the two must be reviewed together. ADR-008 remains in the foundation
packet because its exclusive approval enforcement is itself a foundation prerequisite. They must
still be reviewed as one coherent upstream lifecycle/safety sequence. ADR-023 likewise remains in
the foundation packet because ADR-002 cannot be accepted without its event model; this packet
inherits that exact accepted subject and cannot select a different one. ADR-016 and ADR-017 are
already marked Accepted, but the OPEN parameters and protected implementation paths they govern
still require the named human decisions. ADR-026 is a narrow Proposed correction to ADR-017's
ordinary-audit hash language; affected persistence remains disabled until that relationship is
resolved through protected privacy/security review.

## Cross-Cutting OPEN Decisions

These are explicit decision rows, not implied consequences of accepting an ADR:

| Open Decision | Acceptance focus                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Dependent scope while OPEN                                                                             |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| OD-009        | Retention duration and deletion SLA by data class; legal/privacy basis; affected opaque-reference and any separately authorized resolver lifecycle                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Production persistence policy, affected migration, resolver, and deletion acceptance tests             |
| OD-014        | ADR-025 structural direction; admission/CAS over command receipt/auth-refresh/claim/execution/widening outcome, viewer/platform/director/content-scheduler promotion, timer materialization/claim/firing/cursor, direct Turn admission, ordinary effect intent/send/advancing application, and candidate/selection/approval/media/task/signing/dispatch; committed-prefix begin-close/cursor-freeze/bounded drain/coherent `Ending` and resolved-target atomic final close; restored-open/draining/closed recovery; trigger/retry/interruption/missed policy; recovery-probe allowlist/binding and terminal-unknown versus bound-source resolution/permanent-safe-quarantine/accountable-disposition policy for ordinary closure/actor takeover | All session actor, command, input/Turn admission, effect, scheduler, timer, closure, and recovery work |
| OD-021        | One hand-authored non-event schema source and deterministic generation for every consumer language; protected idempotency-key scope with digest excluded from lookup identity, same-protected-scope/key/same-digest original reuse, same-protected-scope/key/different-digest conflict/no second lineage, canonical command/receipt/outcome and no-lineage `session_closed`, refreshed-authorization evidence, and task/control/acknowledgement/reconciliation contracts                                                                                                                                                                                                                                                                        | All session and stage-host non-event protocols                                                         |
| OD-022        | Command principal/source capabilities, receipt/outcome disclosure, append-only authorization observations, deterministic concurrent allow/deny/step-up/unavailable precedence, retryable/nonretryable denial, current revocation/policy epoch, presence, and step-up                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | All realized operator/trusted-source command ingress and execution                                     |
| OD-029        | Independently retained recovery generation/high-water, composite writer/actor/audience fencing, zero-loss proof or lost admission/close-cut and other tail disposition, restored-open/draining/closed lifecycle/admission coherence, monotonic lost-tail overlay, accountable `unresolved_lost_tail_target` resolution, permanent non-reopen/atomic-final-close authority, and restored epoch/signing/binding supersession                                                                                                                                                                                                                                                                                                                      | Restore, failover/failback, multi-writer-site candidacy, and production continuity                     |
| OD-034        | Exact ADR-024/025 lifecycle rows: definitions/activation, ownership, `SessionNormalWorkAdmission`/closure drain, recovery barrier/history, commands/authorization-observation dedupe identity/lineage revision/selection CAS, four-record ordinary effects, distinct/discriminated four-role recovery probes, timers/claims, restrictive controls, content/memory/archive, access/retention, and terminality                                                                                                                                                                                                                                                                                                                                    | Phase 2 schema/migrations and dependent runtime/content/data capabilities                              |
| OD-035        | Independent freshness/TTL, external timeout, scheduler budget, and conservative clock profile                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Numeric deadline/timeout/clock behavior and expiry acceptance                                          |
| OD-036        | SLI/telemetry/alert/dashboard authority, privacy, ownership, loss posture, and evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Production observability, paging, and SLO enforcement                                                  |
| OD-037        | Queue/resource bounds, protected reserves, authorization-observation growth and command auth-lineage/claim/execution, ordinary effect intent/send/application, recovery-probe intent/attempt/response/disposition count/byte/rate/age/concurrency, all ordinary progression, bounded late-evidence/terminal non-advancing closure drain/cursor freeze/final close, fairness, shedding, and recovery                                                                                                                                                                                                                                                                                                                                             | Production backpressure, closure, autoscaling, and overload handling                                   |
| OD-038        | Provider quota, cost/billing ledger, warning/denial, override, and reconciliation                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Production quota/cost enforcement and budget event activation                                          |
| OD-039        | Representative load/soak/chaos subject, blast radius, abort, statistics, recovery, and evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Phase 9 performance/resilience acceptance                                                              |

Each outcome must be entered in the
[Open Decision Disposition Register](open-decision-dispositions.md) for the exact immutable
review subject. A blank row keeps the dependent scope disabled.

ADR-023 and OD-033 are inherited foundation evidence, not a second decision surface here. Every
feature using events must reference the same accepted ADR-002 and ADR-023 contract and OD-017 and
OD-033 dispositions. Missing, invalidated, or mismatched evidence blocks that feature and reopens
the foundation dependency; this packet cannot replace it with a local outcome.

## Cross-ADR Invariants

A reviewer should reject or revise any proposal that fails one of these checks:

- Only `packages/safety` can construct `ApprovedResponse`.
- Proposed surface and voice-use capabilities have one protected sole mint boundary each,
  terminal persisted decision lineage, private capability construction, ID-only serialization,
  and database rejection constraints; their final ownership remains an explicit Open Decision
  OD-023 and Open Decision OD-024 outcome.
- Voice synthesis requires mutually bound content approval, rights authorization, and exact
  voice-surface authorization. None substitutes for another, and the earliest deadline wins.
- TTS, media, dispatch, and stage-host boundaries never accept generated text.
- Missing, unavailable, expired, unverifiable, or replayed approval state produces no autonomous
  broadcast output.
- Primary, retry, rewrite, and fallback generation paths cross the same safety gate.
- Every external call has a finite explicit timeout and a classified failure result.
- One logical session actor means one exact active recovery/ownership composite fence. Every
  protected commit shares an ownership-row conflict/post-lock lease check with revoke/takeover;
  aggregate version, process, route, heartbeat, Redis lock, and session epoch cannot substitute.
- A normal command binds its submission recovery generation and is accepted only after a durable
  receipt and initial authorization observation; volatile auth provenance is outside the
  semantic digest, refreshed evidence appends without rewriting lineage, every receipt-return
  path and execution reauthorize, deadline expiry is universal, and unknown/lost-tail absence
  never becomes fresh acceptance.
- Session-owned ordinary effects persist intent, send-authorized attempt, response observation,
  and application disposition under active/open authority. Recovery probes use a distinct
  four-role lineage, bind exact active+draining-prefix or recovering+recovery-attempt/source
  ambiguity, stay finite/read-only-or-restrictive/non-widening, permit zero-attempt terminal
  disposition, and treat originating fence as provenance so a current same-source successor can
  terminalize without resend. Every probe terminalizes before close, while its source ambiguity
  separately resolves, remains permanently safe-quarantined, or is accountably disposed; a
  terminal `unknown` never becomes absence/replay authority.
- Process-memory timers are wake-up aids only. Canonical nominal-slot uniqueness,
  materialization-cursor CAS, current claim token/revision, one turn admission, hard deadlines,
  and bounded materialization/catch-up are durable.
- Every new owner begins recovery-only and crosses a source-serialized activation barrier with a
  sealed rig cursor. Every recovery-attempt-bound probe write advances invalidation; activation
  requires all such probes terminal and each enabled-scope source ambiguity resolved or
  explicitly capability-disabled. Administrative revoke creates restrictive
  epoch/hold/control intent drained without an active actor; audience convergence remains unknown
  until exact acknowledgement.
- `stage-host` remains required, is the sole `SpeechTask` consumer, and can stop local output
  without cloud connectivity.
- Proposed rights/surface fields and invalidation commands do not widen ADR-008's current closed
  `SpeechTask` allowlist until ADR-011, OD-021, and protected contract amendments are accepted.
- PostgreSQL remains the recovery source; Redis retention is never relied on for reconstruction.
- Event producers use ADR-023's accepted immutable event-contract profile, separate current
  catalog-lifecycle evidence, trusted envelope framing, catalog-fixed typed primary
  scope/aggregate subject, `(aggregate_version, event_index)` lane, and a transition manifest for
  every aggregate version including zero-count attestations. They never invent a
  `stream_session_id`, infer a version from shape, advance an incomplete safety/authorization
  projection, treat a command/heartbeat/`SpeechTask` as a domain event, or turn identity into an
  untyped nullable field.
- Non-selectable drafts, immutable behavior/set versions, separate eligibility state/epochs,
  explicit inactive/active scoped activation state/epoch, non-effective schedules, resolved work
  snapshots, independent restrictive authorities, and ephemeral provider health are distinct.
  No family selects `latest`, silently deletes/deactivates a binding, or uses a universal implicit
  most-specific-wins rule.
- Durable approval resolution uses the safety-owned approved-content snapshot/reference and
  candidate/decision lineage; missing content cannot be reconstructed from audit, provider,
  media, or archive storage.
- Safety/freshness deadlines, external timeouts, scheduler budgets, observed SLOs, and alert
  thresholds are independent; error budgets never permit an invariant violation.
- Bounded queues and protected reserves preserve e-stop, restrictive control, safety, heartbeat,
  and current playout. Generation does not consume unreserved downstream safety capacity.
- Downward safety transitions and stop actions are available during partial failure.
- Viewer memory, restricted generation content, rights records, and audit records keep their
  declared data classifications and access boundaries.
- Pending ADR-026 review, ordinary audit, telemetry, logs, traces, metrics, events, idempotency
  keys, and deletion receipts do not treat a content-derived viewer message or memory digest as a
  privacy-safe replacement for deletable content.
- No provider, duration, threshold, role assignment, cryptographic algorithm, legal conclusion,
  or SLO recommendation becomes a production default without its accountable human decision.

## Required Acceptance Evidence

Architecture approval defines what must be built; it is not implementation evidence. Before a
corresponding production capability is enabled, reviewers must have:

- generated contract parity and compatibility fixtures for every activated event or command;
- complete event-contract/profile-only evolution with separate catalog lifecycle, trusted version
  framing, typed subject/scope, per-version zero/event transition manifest/high-water,
  missing-tail/whole-transition, non-session facts, authorization, monotonic protection-overlay
  epoch/partition-high-water and effect-boundary validation, and privacy fixtures for the accepted
  OD-033 model;
- draft/publish and review-digest binding; definition/set eligibility; atomic bundle; closed
  initialize/activate/replace/deactivate/rollback; scope/fallback composition; stale activation
  or eligibility epoch; schedule due-time revalidation; restrictive transition/in-flight work;
  emergency DB-outage; snapshot pinning; and reconstruction evidence for every enabled ADR-024
  family;
- protected review of every realized
  [domain-record lifecycle](../architecture/domain-record-lifecycle-catalog.md) row, including
  orthogonal semantic/content/retention/use/publication/delivery state and no-reopen tests;
- persistence constraints and replay/reconstruction tests for durable workflow state;
- ownership state-machine/property and PostgreSQL race tests for acquire, renew, revoke,
  row-conflict ordering, post-lock time, expiry, takeover, activation cuts, relinquish, stale
  composite fence, PITR, process pause, database timeout, and clock uncertainty;
- normal-work admission/source-CAS tests covering every command/input/director/scheduler/timer/
  Turn/ordinary-effect-intent/send/advancing-application path and every ordinary candidate/
  selection/approval/media/task/signing/dispatch progression, begin-close committed prefix,
  no-lineage
  `session_closed`, raw-input non-promotion, recurring-cursor freeze, bounded evidence-only late
  observations, prior-attempt possibly-sent classification, bounded drain, atomic
  `ended`/`cancelled`/`failed` session/admission/ownership final close with no earlier terminal
  lifecycle row, revoke/relinquish/takeover races, no post-begin-close-cut ordinary growth, and
  PITR restored-`open`/`draining(normal_closure)`/atomic-`closed` lifecycle/admission coherence,
  monotonic lost-tail overlay, and unresolved-target final-close blocking;
- command receipt/outcome tests for submission generation, semantic digest versus append-only
  auth provenance, refreshed-observation deduplication and crash handoff, duplicate/conflicting
  idempotency, response loss, receipt-return disclosure and execution revocation/expiry,
  current-observation/policy/revocation selection, append-versus-execution authorization-lineage
  revision CAS, deterministic allow/deny/step-up/unavailable precedence and ambiguity
  fail-closed, retryable-versus-nonretryable denial terminality, fresh database-time receipt/
  refresh/execution deadline boundaries, ordinary execution versus begin-close, terminal
  no-reopen, universal expiry, lost-tail absence, every crash boundary, and successor processing;
- ordinary effect intent/send-authorization/first-byte/response-observation/application tests
  for lease horizon, provider idempotency/query support, possibly-sent non-idempotent work,
  forced revoke, late result, signing/dispatch fence, recovery classification, concurrent
  multi-attempt/observation cardinality, one disposition per observation, and new intent on
  retry/rewrite/fallback/provider/semantic change;
- recovery-probe intent/attempt/first-byte/response/disposition tests under both exact
  active+draining-prefix and recovering+recovery-attempt/source bindings, including wrong binding,
  zero-attempt terminalization, crash/takeover current-successor terminalization without old-
  intent resend, finite count/byte/rate/age/concurrency, idempotency, no deadline extension, no
  ordinary application, negative/timeout/contradictory evidence remaining terminal-unknown
  without resolving the source, one terminal non-widening disposition per probe, and final-close
  rejection for a nonterminal probe or unresolved bound source ambiguity;
- timer canonical occurrence/materialization/current-claim/firing tests for duplicate wake-up,
  current-active ownership fencing, recovering-owner no-create, cursor/commit-response races,
  occurrence/current-claim-pointer acquisition/reclaim CAS, same-actor concurrent poll, expired
  claim after reclaim, one turn admission, one terminal firing disposition, missed window,
  takeover, clock uncertainty, bounded catch-up, and resource exhaustion;
- recovery barrier tests for source commit reordering/preallocated IDs, immutable cut-time
  frontier/schedule-cursor snapshots, harmless post-cut operational-cursor progress without
  activation starvation, every recovery-attempt-bound probe write invalidating the candidate,
  nonterminal probe/enabled-scope unresolved-source-ambiguity activation rejection,
  ambiguity/restriction invalidation, sealed rig cursor, restrictive-dispatcher loss, and PITR
  lost-tail quarantine;
- PostgreSQL/outbox outage tests proving restrictive safety actuation happens immediately while
  resume and higher-autonomy work remain blocked until durable reconciliation;
- construction, decision-lineage, exact selected-same-turn candidate, immutable post-mint
  selection, database, and composed-chain tests for every content, rights, surface, media, and
  dispatch authorization;
- import-boundary and protected-symbol tests for provider and safety ownership;
- fail-closed tests covering timeout, fallback, expiry, signature failure, replay, and partition;
- exact final voice rendering before surface authorization, with any provider/sanitizer/
  pronunciation change requiring a fresh decision and authorization;
- target-hardware evidence for local e-stop, watchdog, raw clock/offset/uncertainty/sample-age
  handling, queue flush, and recovery;
- a stage-host crash/power-loss matrix proving atomic acceptance/replay state, no lost accepted
  acknowledgement, no automatic in-doubt replay, restrictive epoch convergence, and old-epoch
  queue eviction;
- a per-surface renderer trust matrix and OBS-scene preflight proving every enabled source has an
  accepted owner, signed identifier-only verifier, expiry/clear path, partition behavior, and
  emergency scope;
- server-side authorization tests for every operator command and negative role case;
- deterministic rehearsal evidence for every enabled broadcast surface;
- privacy, deletion, access-log, voice-rights, and revocation evidence for the data involved;
- for affected personal-data persistence, opaque-reference role isolation, prohibited-digest
  serializer/schema tests, resolver absence or separately accepted lifecycle, and deletion
  canaries that do not retain a content-derived verifier;
- an accountable [threat-model](../security/threat-model.md) review covering the enabled composed
  path, with abuse-case tests and explicit residual-risk decisions;
- source-to-artifact-to-target provenance, trusted release/update, rollback/disable, and
  supply-chain compromise evidence for every deployed artifact;
- personal-data breach, deletion/restore, and disaster-recovery procedures and target exercises
  for every enabled data and deployment path;
- telemetry prohibited-content/capacity checks, alert-route delivery/acknowledgement, monitoring
  loss, and dashboard/query validation;
- representative load/stress/spike/soak/chaos/recovery evidence proving protected reserves,
  queue/resource limits, fairness, bounded retry/fallback, cost/quota behavior, abort, cleanup,
  and backlog drain under the accepted
  [acceptance contract](load-soak-chaos-acceptance.md);
- remote required-check and repository Ruleset evidence for the reviewed commit;
- applicable [runbooks](../runbooks/README.md), telemetry, alerts, rollback, named operational
  ownership, rehearsal, target-validation, and deployment-scoped authorization.

## Review Outcomes

For each ADR row, a protected reviewer records:

- `Accept`: the invariant decision is binding; every OPEN-dependent behavior stays disabled.
- `Revise`: the ADR remains Proposed and must identify the requested correction.
- `Reject`: the ADR remains non-authoritative and a replacement direction is recorded.

Acceptance must not be inferred from a pull-request merge, local test pass, elapsed time, or
silence. A later change to an accepted invariant requires a superseding ADR.

For each OD row, reviewers record the explicit selected outcome, alternatives
rejected/deferred, disabled scope, and full disposition-record ID under the OD-040 lifecycle. A
generic `Accept` does not decide a multi-option OPEN item.

## Decision Record

| Item                 | Selected outcome / Accept / Revise / Reject | Reviewer and role | Date | Evidence, OPEN items retained, or required follow-up   |
| -------------------- | ------------------------------------------- | ----------------- | ---- | ------------------------------------------------------ |
| ADR-003              |                                             |                   |      |                                                        |
| ADR-004              |                                             |                   |      |                                                        |
| ADR-007              |                                             |                   |      |                                                        |
| ADR-010              |                                             |                   |      |                                                        |
| ADR-011              |                                             |                   |      |                                                        |
| ADR-015              |                                             |                   |      |                                                        |
| ADR-019              |                                             |                   |      |                                                        |
| ADR-020              |                                             |                   |      |                                                        |
| ADR-021              |                                             |                   |      |                                                        |
| ADR-022              |                                             |                   |      |                                                        |
| ADR-024              |                                             |                   |      | OD-034 scope not explicitly accepted remains disabled  |
| ADR-025              |                                             |                   |      | Session execution remains disabled pending OD-014      |
| ADR-026              |                                             |                   |      | Affected persistence remains disabled pending OD-009   |
| OD-009               |                                             |                   |      | Retention/deletion policy remains disabled             |
| OD-014               |                                             |                   |      | Actor/scheduler/effect/recovery scope remains disabled |
| OD-021               |                                             |                   |      | Non-event protocols remain disabled                    |
| OD-022               |                                             |                   |      | Command authorization behavior remains disabled        |
| OD-029               |                                             |                   |      | Restore/failover/continuity scope remains disabled     |
| OD-034               |                                             |                   |      | Schema/migration scope remains blocked                 |
| OD-035               |                                             |                   |      | Numeric deadline/clock policy remains disabled         |
| OD-036               |                                             |                   |      | Production telemetry/paging remains disabled           |
| OD-037               |                                             |                   |      | Production admission/overload policy remains disabled  |
| OD-038               |                                             |                   |      | Cost/quota enforcement remains disabled                |
| OD-039               |                                             |                   |      | Phase 9 performance/resilience pass remains blocked    |
| Overall feature gate |                                             |                   |      | Name only the capability authorized by this outcome    |
