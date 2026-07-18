# Capacity, Backpressure, And Cost Governance

Status: Proposed architecture reference; no capacity, quota, cost, queue, retry, deployment, or
production default

Governing sources:

- [`AGENTS.md`](../../AGENTS.md)
- [`vnova-review-handoff.md`](../../vnova-review-handoff.md)
- [ADR-003: stream-session, segment, and turn lifecycle](../adr/0003-stream-session-segment-and-turn-lifecycle.md)
- [ADR-004: PostgreSQL outbox and Redis Streams](../adr/0004-postgresql-outbox-and-redis-streams.md)
- [ADR-007: provider gateway and fallback isolation](../adr/0007-provider-gateway-and-fallback-isolation.md)
- [ADR-010: approved media and TTS pipeline](../adr/0010-approved-media-and-tts-pipeline.md)
- [ADR-011: stage-host protocol and clock synchronization](../adr/0011-stage-host-wire-protocol-and-clock-synchronization.md)
- [ADR-018: latency budget and streaming strategy](../adr/0018-latency-budget-and-streaming-strategy.md)
- [ADR-019: authentication, authorization, and operator roles](../adr/0019-authentication-authorization-and-operator-roles.md)
- [ADR-020: mode transition and degradation matrix](../adr/0020-mode-transition-and-degradation-matrix.md)
- [ADR-023: event subject, scope, correlation, and ordering lanes](../adr/0023-event-subject-scope-correlation-and-ordering.md)
- [ADR-024: versioned configuration and scoped activation](../adr/0024-versioned-configuration-and-scoped-activation.md)
- [ADR-025: session actor ownership, command ingress, and fencing](../adr/0025-session-actor-ownership-command-ingress-and-fencing.md)
- [Threat model TM-16](../security/threat-model.md#tm-16-resource-exhaustion-and-dependency-failure)
- [Threat model TM-19](../security/threat-model.md#tm-19-session-actor-split-brain-command-ambiguity-or-timer-replay)

This document defines how VNova must bound and prioritize work before implementation. It does not
select queue sizes, concurrency, traffic rates, hardware, provider quotas, currency budgets,
warning/limit percentages, retry counts, time windows, or deployment topology.

## Governing Invariants

1. E-stop, watchdog, safe-direction mode changes, safety decisions, operator control, current
   playout, heartbeat, and required durable evidence cannot be starved by speculative generation,
   telemetry, replay, indexing, or background work.
2. No queue, buffer, retry policy, SDK, exporter, provider, cache, or local journal is unbounded.
3. Admission considers the complete remaining path, including safety, media, dispatch, rig, and
   evidence capacity; accepting work into the first stage is not sufficient.
4. Retry, fallback, rewrite, reconnect, and replay consume the same deadline, capacity, quota, and
   cost budgets. They never create new budget silently.
5. Overload sheds or expires work before weakening safety, extending freshness, dropping stop, or
   accepting raw/unapproved output.
6. PostgreSQL is authoritative. Redis, queue depth, provider quota, cost estimates, dashboards, and
   local buffers cannot reconstruct permission or completed durable state.
7. Unknown capacity, quota, billing, clock, queue, or acknowledgement state is restrictive.
8. Recovery drains and reconciles under explicit holds; a cleared graph or returned quota never
   raises mode or resumes work automatically.
9. Actor lease renewal, durable command ingress, ordinary effect intent/attempt, separately typed
   recovery-probe lineage, timer claim, and takeover recovery have bounded protected capacity.
   Saturation cannot silently drop a receipt, extend a lease/deadline, blind-replay an effect,
   leave a probe nonterminal or its bound source ambiguity undisposed at close, or make a timer
   occurrence disappear.

## Resource And Queue Inventory

Every production path maintains a versioned inventory entry for each bounded resource:

| Field              | Required meaning                                                                                                                               |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Identity and owner | Stable resource/queue ID, component, capability, environment, accountable owner                                                                |
| Work unit          | Items, bytes, tokens, duration, connections, requests, artifacts, storage, cost units, or another reviewed measure                             |
| Scope              | Global, environment, talent/session, provider/profile, rig, surface, or data-class boundary; organization/tenancy only after OD-034 defines it |
| Capacity bounds    | Soft warning, hard admission bound, reserved capacity, and separately bounded retry/recovery capacity                                          |
| Age/deadline       | Maximum permitted age and relationship to the authoritative outer deadline/TTL                                                                 |
| Admission          | Preconditions, downstream reservation, fairness, idempotency, and rejection/expiry behavior                                                    |
| Backpressure       | Upstream signal, propagation delay, stale-signal behavior, and work already in flight                                                          |
| Overflow           | Exact drop/reject/expire/quarantine/fail-closed action and evidence; never implicit eviction                                                   |
| Durability         | Volatile, PostgreSQL-backed, object-backed, or local durable behavior plus crash/restart semantics                                             |
| Privacy            | Data class, prohibited content, retention, deletion/hold, access, and spill/export behavior                                                    |
| Observability      | Depth/bytes/oldest-age, rates, saturation, latency, outcome, drops, uncertainty, and alert/runbook                                             |
| Recovery           | Drain order/rate, poison handling, reconciliation, mode hold, and exit evidence                                                                |

The inventory covers at least:

- platform ingest and moderation;
- per-session ownership-row acquire/renew/revoke/takeover transactions, submission-generation
  command inbox/receipt/authorization-observation-lineage/claim/execution/outcome, ordinary
  effect intent/send-authorized attempt/response observation/application disposition,
  recovery-probe intent/attempt/response/disposition with dual-binding and count/byte/rate/age/
  concurrency bounds, canonical timer materialization/current claim/firing, normal-input/Turn
  admission source CAS, every ordinary
  candidate/selection/approval/media/task/signing/dispatch progression, begin-close
  committed-prefix/cursor freeze, bounded evidence/non-advancing drain/final close, recovery
  cut/barrier/lost-tail quarantine, restrictive-control priority dispatcher, and scheduler;
- prompt/memory/knowledge retrieval and assembly;
- generation, retry, fallback, rewrite, and provider adapter concurrency;
- deterministic, model-based, policy, and operator safety evaluation;
- operator review queues and presence-dependent work;
- TTS, surface authorization, immutable media commit, object transfer, and dispatch;
- PostgreSQL connections/transactions/storage, audit/domain-event/outbox backlog;
- Redis publication/streams/consumer groups and consumer inbox/poison handling;
- runtime-to-rig connection, stage-host acceptance/playback queues, audio buffer, adapter work,
  and offline journal;
- logs, traces, metrics, alert delivery, evidence manifests, and restricted forensic storage;
- deletion/restore, indexing/embedding, archive/export, backup, release, and recovery work.

No capability is production-authorized while an enabled queue or bounded external resource is
missing from the inventory.

## Priority And Isolation Classes

Priority is implemented through isolation, reservation, admission, and preemption rules, not only
an integer on one shared queue.

| Class                     | Examples                                                                                                                                  | Required posture                                                                                                  |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Local independent safety  | Physical/local e-stop, audio cut, queue flush, watchdog neutral state                                                                     | Must work without cloud, identity provider, telemetry, Redis, provider, or ordinary runtime capacity              |
| Cloud restrictive control | E-stop propagation, generation freeze, mode decrease, rights/access/deletion invalidation, cancellation                                   | Dedicated capacity and safe-direction concurrency semantics; stale aggregate version cannot block the restriction |
| Safety/control continuity | Safety evaluation for admitted work, operator command handling, heartbeat/clock health, current rig reconciliation, required audit/outbox | Reserved from speculative work; unknown durability blocks recovery/upward actions but not immediate restriction   |
| Current committed output  | Already authorized, current-epoch, unexpired artifact transfer/playout and explicit interruption                                          | Bounded and preemptible by safety; never displaced by filler merely to improve throughput                         |
| Normal broadcast work     | Eligible viewer/operator/scheduled turns, reviewed media preparation                                                                      | Fair, deadline-aware admission within accepted mode and downstream reservation                                    |
| Speculative/background    | Idle filler, prefetch, cache warming, reindexing, embedding, analytics, export, replay, telemetry enrichment                              | First to shed or pause; cannot consume safety/control reserves or make stale data authoritative                   |

Resume, mode increase, policy activation, privileged reveal, access grant, and publication are not
safe-direction actions. They retain their full authorization, confirmation, audit, freshness, and
capacity gates even during recovery.

If strict isolation cannot be proven for a shared pool, reservations assume the least favorable
contention and overload lowers the affected capability's mode ceiling.

## End-To-End Admission Reservation

A turn is admitted only if the scheduler can prove, under the accepted conservative model:

- its trigger, classification, policy, mode, category cap, and outer deadline permit work;
- per-session and global actor/scheduler capacity exists;
- an eligible generation path has bounded attempt, quota, cost, and cancellation capacity;
- the required independent safety path has reserved or protected capacity for the expected
  candidate outcome;
- operator-review capacity is available when policy requires it, or expiry behavior is acceptable;
- media, object storage, surface/rights authorization, dispatch, and exact rig can accept the
  expected work before expiry;
- authoritative persistence, audit/outbox, and idempotency capacity can record the transitions;
- failure can still terminate, cancel, expire, or fail closed without relying on the exhausted
  resource.

Generation must not consume scarce provider budget and then discover that all independent safety
classifier capacity was assigned to speculative work. A deployment either reserves the complete
required downstream safety capacity before admission or proves an isolated fail-closed reserve
that cannot be consumed by generation. It never speaks because safety capacity was unavailable.

Reservation is not preauthorization. Actual state, content, safety, rights, surface, expiry,
integrity, and rig checks still occur at every boundary. Unused reservations expire and release
without creating work or extending deadlines.

## Queue Contract

Every queue defines:

- accepted item identity, immutable canonical digest/reference, scope, priority class, admission
  time, deadline, epoch, and idempotency key;
- maximum items, bytes, oldest age, and per-scope share;
- ordering lane and whether order is strict, causal, best effort, or irrelevant;
- durable acceptance point and acknowledgement stages;
- duplicate, conflicting duplicate, poison, cancellation, expiry, interrupt, retry, restart, and
  in-doubt behavior;
- dequeue authorization and immediate revalidation requirements;
- overflow behavior that records an explicit normalized outcome.

Silent drop, silent overwrite, queue-tail replacement, unbounded `latest wins`, implicit SDK
queueing, and retry with a new identity are prohibited unless a capability-specific accepted ADR
defines an equivalent auditable semantic.

The non-event session command/receipt/outcome and speech/avatar command/task paths use their
accepted ADR-025/ADR-011/OD-021 identities and fencing rules. A full mailbox or lost wake-up
cannot erase a durable receipt; an expired execution claim does not complete a command or timer.
Domain-event publication separately preserves ADR-023 aggregate-version/event-index
order and transition-manifest/expected-delivery completeness inside each catalog-declared subject
lane while permitting cross-lane concurrency/reordering. Safety restrictions can preempt or
invalidate queued work; unrelated telemetry never blocks
either protected path.

## Backpressure Propagation

Backpressure travels toward admission:

```text
stage-host / renderer / audio
  -> dispatch and artifact transfer
  -> media / TTS / surface-rights authorization
  -> safety and operator review
  -> generation
  -> scheduler
  -> ingest admission
```

Each boundary communicates a provider-neutral state such as available, warning, saturated,
draining, failed, quarantined, or unknown plus freshness and scope. A stale signal is `unknown`,
not available.

- Downstream saturation stops new upstream work before queues exceed their hard bound.
- In-flight work may complete only when its deadline, authorization, and reserved downstream path
  remain valid.
- Backpressure cannot delay e-stop, mode decrease, cancellation, rights/deletion invalidation, or
  local watchdog actuation.
- A provider or rig reconnect starts reconciliation and bounded probing; it does not immediately
  advertise full capacity.
- Backlog drain uses an explicit recovery rate and preserves current/live work and control
  reserves.

## Fairness And Isolation

Capacity is partitioned deliberately across:

- environment and production/rehearsal;
- talent/character/session;
- trigger class and segment category;
- provider capability/profile/failure domain;
- rig and audience-facing surface;
- normal, incident, deletion, recovery, and background workloads.

One viewer flood, session, provider, rig, export, restore, reindex, or telemetry path cannot
consume every global worker, database connection, file descriptor, buffer, or quota. Fairness
must not override safety priority or category-specific autonomy caps.

Exact scheduling algorithms and shares remain OPEN. Tests must prove the accepted policy under
adversarial skew, not only uniform traffic.

## Provider Quota, Circuit, And Cost Ledger

Provider usage and cost are governed by an authoritative VNova ledger, not a provider dashboard
alone.

The ledger records minimized provider-neutral evidence for:

- capability, profile/model, session/scope, attempt, request, and billing-correlation identities;
- reserved, estimated, reported, reconciled, disputed, and unknown usage/cost states;
- token/audio/image/time/request units and currency/version where applicable;
- quota pool, rate/concurrency state, circuit state, retries/fallbacks, and late provider reports;
- warning, hard denial, exception/override authority, expiry, and reconciliation outcomes.

Warning and hard enforcement are different states:

- a warning emits operational evidence and may restrict new low-priority admission;
- a hard limit denies new affected work and follows the accepted ADR-020 degradation path;
- delayed billing or unknown usage keeps a conservative reserve or denies affected work;
- an operator cannot convert budget exhaustion into a safety bypass or use an unrelated provider
  without the reviewed fallback/profile path.

`CostBudgetWarning` remains a required but inactive event-catalog entry. No producer, complete
event-contract profile, threshold, or automatic action is authorized until event scope/subject,
completeness, classification/protection, cost semantics, and the human cost/quota decision are
accepted.

## Storage, Transport, And Local Capacity

### PostgreSQL And Outbox

- Reserve capacity for restrictive state, audit/outbox, idempotency, deletion/revocation, and
  recovery evidence ahead of speculative data.
- Connection and transaction saturation cannot cause a successful domain mutation to be reported
  without its required durable evidence.
- Hot-aggregate version serialization, multiple event indexes and manifest/expected-delivery rows
  per transition, activation/eligibility-state compare-and-swap, current epochs, scheduler, and
  resolver/snapshot persistence have measured contention, bounded retries, and dedicated
  restrictive-operation reserve. An independent gapless event counter is not introduced as a
  second authority.
- Outbox age/bytes/rows, poison state, publisher attempts, and storage growth have explicit bounds
  and recovery action.
- Retention/compaction never deletes the only authoritative or legally required record.

### Redis And Consumers

- Redis is replaceable transport; stream size, lag, pending entries, consumer retries, poison
  handling, and dead-letter data are bounded.
- Shedding Redis data cannot be reported as domain completion, and Redis restoration cannot
  authorize replay.
- Consumers reserve capacity for idempotent reconciliation and do not acknowledge before their
  required durable side effect.

### Object And Restricted Storage

- Upload/download, staging, integrity verification, incomplete multipart state, orphan cleanup,
  cache, and retention work are bounded.
- Storage pressure cannot silently convert an immutable artifact into an alias, overwrite, or
  lower-integrity representation.
- Restricted, rights, memory, audit, and public archive capacity remain separately classified and
  cannot spill into ordinary logs or temporary directories.

### Stage-Host Queue And Journal

- Queue, audio buffer, artifact cache, adapter calls, offline journal, evidence shipping, and disk
  use have target-specific bounds.
- Journal exhaustion, corruption, rollback, or unprovable durable acceptance blocks new autonomous
  playback while preserving the local hard stop.
- `playing_or_in_doubt` work never auto-replays; reconnect reconciles task/epoch/queue state with
  PostgreSQL.

## Runtime And Event-Loop Protection

CPU-heavy generation support, media transformation, archive work, scans, compression, and
cryptography that can block control latency do not execute unbounded on the `session-runtime`
async event loop. Every worker pool/process has bounded admission, cancellation, shutdown, and
resource isolation.

Ownership renewal, safe-direction control, durable command receipt/claim/execution,
current-generation revalidation, bounded command-authorization observation append/selection/
lineage-revision CAS, timer materialization/claim/deadline processing, ordinary effect
intent/send/advancing application, and every other ordinary pipeline progression use protected
resources. Normal-input/Turn admission, begin-close, bounded late-evidence capture, distinctly
typed/source-bound recovery-probe intent/attempt/response/non-widening disposition, terminal
non-advancing drain, and atomic final-close also have protected bounded transaction capacity.
Long provider
calls and recovery scans cannot block the event loop until a lease silently expires, strand a
closing prefix, arbitrarily select an older authorization observation, or make the actor appear
current from stale health.

Append-only command authorization evidence is itself bounded. OD-037 sets per-command and
per-principal/trusted-source count, byte, append-rate, age, and contention limits plus a protected
execution-reauthorization reserve. An observation append is admitted only for a nonterminal
command before its hard deadline and through the exact `open` normal-work admission epoch/source
CAS. At a hard bound, the service preserves existing lineage, rejects the new append with a
durable machine-readable overload/ineligibility result after current disclosure authorization,
leaves the command pending-but-ineligible or lets its deadline expire, and never substitutes
transient credentials, drops an earlier observation, reopens a terminal command, or bypasses
current authorization. During `draining`/`closed`, or after terminality/effective expiry, the
request may perform only disclosure-authorized lookup plus the separately bounded access-audit
path; it appends no authorization observation.

Garbage collection, memory pressure, file descriptors, threads/tasks, connection pools, DNS,
secret/identity lookups, and telemetry exporters belong in the resource inventory. A healthy
provider does not prove the local gateway has capacity.

## Overload And Degradation

The accepted profile maps each resource state to exactly one restrictive response:

| Resource condition                                      | Minimum semantic response                                                                                                                 |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Soft warning with trustworthy headroom                  | Restrict/pause lower-priority admission; preserve reserves; alert and measure                                                             |
| Hard bound reached                                      | Reject or expire new affected work with explicit outcome; no queue growth past the bound                                                  |
| Safety/control reserve threatened                       | Stop speculative/normal admission; lower effective mode or enter fail-closed posture                                                      |
| Authoritative persistence uncertain                     | Apply immediate in-process/local restriction; block resume, mode increase, and new durable-success claims until reconciliation            |
| Actor ownership/command/effect/timer capacity uncertain | Stop ordinary session progression; preserve safe-direction reserve; retain durable pending/unknown state; enter bounded recovery hold     |
| Recovery-probe reserve or bound uncertain/exhausted     | Admit no new probe; keep the source ambiguity and final-close blocker explicit; never reuse ordinary effect capacity or infer absence     |
| Command authorization-observation bound reached         | Reject the append durably; preserve lineage and execution reserve; keep command ineligible or expire it; never use transient/old evidence |
| Provider quota/cost unknown or exhausted                | Deny affected provider attempts; use only a separately eligible bounded fallback through the same safety gate                             |
| Rig/playout capacity unknown                            | Stop dispatch/admission for that rig; watchdog/local state governs output                                                                 |
| Local journal/storage unsafe                            | Block new autonomous acceptance/playback; preserve e-stop and bounded evidence                                                            |
| Telemetry capacity exhausted                            | Drop only policy-authorized diagnostic priority classes; preserve domain/audit and safety/control capacity; invoke observability runbook  |

Mode changes never replace the resource-specific containment. A lower mode can reduce admission,
but the saturated queue, provider, storage, or rig still requires explicit recovery.

## Recovery And Backlog Drain

Recovery is deliberate:

1. Keep the affected scope restricted and fence stale writer/actor/consumer recovery-generation
   pairs through their authoritative mechanisms.
2. Reconstruct only history inside proven-complete PostgreSQL/WAL/manifest horizons: composite
   ownership, command receipts/authorization observations/outcomes, four-record ordinary-effect
   classifications, distinct four-role recovery-probe bindings/terminality, normal-work
   admission/closure prefix, canonical timer/claim/cursor state, work, cancellations, expiries,
   restrictions, and idempotency, plus bounded sealed stage-host evidence.
3. Mark any unclosed PITR/RPO tail `lost_tail_unknown`; do not infer absent commands/effect
   attempts/timer slots/restrictions, reaccept/replay/rematerialize them, or enable the affected
   audience scope. Atomically make restored `open` coherent
   `Ending`/`draining(lost_tail_quarantine)` with a proven or explicitly unresolved target;
   strengthen restored `draining(normal_closure)` with the monotonic lost-tail overlay; keep a
   restored atomic `closed` session closed/ownerless; and block final close while its target or
   tail disposition is unresolved.
4. Quarantine poison, conflicting, stale, old-epoch, deleted, revoked, or unverifiable work.
5. Restore control/safety and restrictive-dispatcher priority reserves before accepting normal
   work.
6. Cross the source-serialized activation barrier using immutable cut-time
   frontiers/schedule-cursor snapshots and invalidation revisions; harmless pending ingress may
   advance only an excluded operational cursor and cannot starve activation. Then drain only
   eligible post-cut commands, occurrences, ordinary effects, and work under the exact active
   composite actor fence at an approved bounded rate while measuring downstream headroom.
   Recovery probes remain on their separate closed path and must terminalize non-wideningly;
   terminal `unknown` preserves the source ambiguity until resolved, permanently
   safe-quarantined, or accountably disposed.
7. Revalidate deadlines and all authorization at each handoff; expired backlog is terminated, not
   renewed.
8. Demonstrate stable headroom, empty/known poison state, reconciled cost/quota, current rig
   state, and alert delivery.
9. Require the normal human-gated recovery/mode path; never auto-restore a higher mode.

Redis backlog or provider pending work is not replay authority. Disaster recovery, deletion,
rights, identity, and supply-chain holds remain cumulative.

## Acceptance Evidence

Before production authorization:

- the complete resource/queue inventory is reviewed and versioned for the exact deployment;
- load, stress, spike, soak, chaos, and recovery scenarios use a declared workload and acceptance
  contract;
- tests cover saturation at every queue and external dependency, including simultaneous and
  correlated failures;
- safety/control reserves remain available under maximum accepted normal load and adversarial
  overload;
- full-pipeline admission prevents generation from consuming safety capacity;
- property tests prove bounded queues, deadline non-extension, idempotency, terminal outcomes,
  fairness constraints, and no unsafe priority inversion;
- actor lease/renew/takeover; command receipt/authorization-observation append/deduplication,
  lineage-revision CAS, selection, claim, execution, and successful/widening outcome; ordinary
  effect intent/send/application; recovery-probe intent/attempt/response/disposition under both
  phase/source bindings; timer materialization/claim/firing; and recovery-scan saturation tests
  prove protected
  safe-direction/execution-reauthorization capacity, visible pending/unknown outcomes, durable
  append-bound rejection, probe count/byte/rate/age/concurrency enforcement, no stale/recovering-
  owner ordinary progression, zero-attempt probe terminalization, current same-source successor
  terminalization without old-intent resend, no probe widening/absence inference, truthful
  terminal-unknown evidence, no nonterminal probe or unresolved bound source ambiguity at close,
  no blind replay, and no lost occurrence;
- every command receipt/auth-refresh/claim/execution/widening-outcome, viewer/platform/director/
  content-scheduler input, timer materialization/claim/firing, Turn, ordinary effect intent/send/
  application, and candidate/selection/approval/media/task/signing/dispatch progression versus
  begin-close; bounded late-evidence/terminal non-advancing drain; fixed-prefix and
  schedule-cursor freeze; final-close/revoke/relinquish/takeover race; and PITR-lost-close
  saturation test proves bounded closure without post-begin-close-cut ordinary work or
  reopening, coherent restored-open/draining/closed axes, monotonic lost-tail overlay, and
  unresolved-target final-close blocking;
- activation-churn tests distinguish immutable cut-time frontiers/cursors from the excluded
  operational cursor, prove continuous harmless post-cut ingress cannot starve activation, and
  prove ambiguity/restriction plus every recovery-attempt-bound probe write advances
  invalidation; activation rejects a nonterminal probe or enabled-scope unresolved source
  ambiguity;
- PostgreSQL/outbox, Redis, object, provider, rig, journal, and telemetry recovery preserve their
  authority boundaries;
- billing lag, quota disagreement, cost warning/limit, circuit, retry/fallback, and unknown-state
  tests invoke the accepted restrictive response;
- ordinary telemetry and spill paths pass prohibited-content, cardinality, capacity, and privacy
  checks;
- the [resource exhaustion and backpressure runbook](../runbooks/resource-exhaustion-and-backpressure.md)
  is rehearsed and target-validated;
- the exact target passes the
  [load, soak, and chaos acceptance](../governance/load-soak-chaos-acceptance.md) review and
  operational-readiness gate.

## OPEN Decisions

Human review must decide:

- OD-037 every resource/queue bound, command authorization-observation per-command/principal
  count/byte/append-rate/age/contention bound and protected execution reserve; command
  receipt/auth-refresh/lineage/claim/execution/widening-outcome, ordinary effect
  intent/send/application, recovery-probe intent/attempt/response/disposition
  count/byte/rate/age/concurrency, timer materialization/claim/firing/cursor/poll/scan/retry,
  every viewer/platform/director/
  content-scheduler input and Turn/candidate/selection/approval/media/task/signing/dispatch
  progression, begin-close, bounded late-evidence/terminal non-advancing prefix drain, and
  final-close bound/reserve; admission estimate, fairness/share, recovery, overload/degradation
  mapping, and provider/database/Redis/object/runtime/rig/audio/journal/telemetry/worker capacity;
- OD-038 cost units, currencies, attribution, billing reconciliation, warning/limit, override,
  dispute, fallback/retry composition, and provider quota policy;
- OD-039 load/stress/spike/soak/chaos workload, target, duration, blast radius, abort, pass/fail,
  evidence, and authorization profiles;
- retry/fallback/rewrite/circuit behavior and how those budgets compose end to end;
- the exact ADR-020 degradation/mode ceiling for each warning, saturation, unknown, and recovery
  state;
- any capability-specific value retained OPEN by the selected OD-037/038/039 disposition.
