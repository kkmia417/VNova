# Resource Exhaustion And Backpressure

Status: Proposed operational runbook; readiness state: `Drafted`; no implementation, scaling,
spend, command, or production authority

Governing sources:

- [`AGENTS.md`](../../AGENTS.md)
- [Capacity, backpressure, and cost governance](../architecture/capacity-backpressure-and-cost-governance.md)
- [Latency budget](../architecture/latency-budget.md)
- [Observability, SLI/SLO, and alerting](../architecture/observability-sli-slo-and-alerting.md)
- [ADR-003: stream-session, segment, and turn lifecycle](../adr/0003-stream-session-segment-and-turn-lifecycle.md)
- [ADR-004: PostgreSQL outbox and Redis Streams](../adr/0004-postgresql-outbox-and-redis-streams.md)
- [ADR-007: provider gateway and fallback isolation](../adr/0007-provider-gateway-and-fallback-isolation.md)
- [ADR-010: approved media and TTS pipeline](../adr/0010-approved-media-and-tts-pipeline.md)
- [ADR-011: stage-host protocol and clock synchronization](../adr/0011-stage-host-wire-protocol-and-clock-synchronization.md)
- [ADR-018: latency budget and streaming strategy](../adr/0018-latency-budget-and-streaming-strategy.md)
- [ADR-020: mode transition and degradation matrix](../adr/0020-mode-transition-and-degradation-matrix.md)
- [ADR-025: session actor ownership, command ingress, and fencing](../adr/0025-session-actor-ownership-command-ingress-and-fencing.md)
- [Threat model TM-16](../security/threat-model.md#tm-16-resource-exhaustion-and-dependency-failure)
- [Operational runbook contract](README.md)

This runbook defines containment and recovery semantics for overload. It does not define queue
sizes, scaling commands, provider quotas, currency limits, retry counts, thresholds, contacts,
deployment products, or target-specific actions.

## Purpose And Entry Conditions

Use this runbook when a resource is at warning, saturation, exhaustion, unknown, or unsafe
recovery state, including:

- ingest, actor, scheduler, generation, safety, operator-review, TTS/media, dispatch, stage-host,
  adapter, or playback queues exceed their approved depth, bytes, age, or deadline posture;
- CPU, event-loop latency, memory, tasks/threads, file descriptors, connections, network,
  database, Redis, object storage, local disk, audio buffer, or journal capacity is threatened;
- provider rate, concurrency, quota, circuit, usage, cost, or billing state is exhausted,
  contradictory, delayed, or unknown;
- outbox, consumer, poison/dead-letter, deletion, restore, evidence, archive, or telemetry backlog
  grows without bounded drain;
- retry, fallback, rewrite, reconnect, replay, cache fill, or recovery amplifies load;
- one viewer/session/provider/rig/background job causes unfair global starvation;
- safety, e-stop, operator control, heartbeat, current playout, or authoritative evidence reserve
  is consumed or cannot be proven;
- scaling, returned quota, or dependency recovery could release a stale backlog into active work.

Do not wait for process crash or complete exhaustion. A credible trend toward loss of
safety/control reserve is enough to enter restrictive containment.

## Non-Negotiable Invariants

- Local hard stop, watchdog, audio cut, and queue flush remain independent and available.
- E-stop, cloud freeze, mode decrease, cancellation, revocation, deletion invalidation, safety,
  heartbeat, operator control, current playout, and required durable evidence outrank speculative
  work.
- Every queue, buffer, external call, retry, fallback, worker, and journal is bounded.
- No overload extends a turn/candidate/approval/authorization/task deadline or permits partial
  safety, raw-text TTS, stale output, or an unreviewed fallback.
- Generation does not consume all independent safety capacity. If a determinate safety result
  cannot be obtained, no autonomous speech occurs.
- PostgreSQL is the recovery source. Redis backlog, provider pending work, telemetry, object
  listing, or local queue state cannot reconstruct permission.
- Overflow produces an explicit rejected, expired, cancelled, quarantined, or fail-closed outcome;
  no silent drop/overwrite is reported as success.
- Normal command receipt, durable input promotion, timer materialization/claim/firing, and Turn
  admission require the exact `open` `SessionNormalWorkAdmission` epoch. Once session closure
  enters `draining`, only its fixed accepted prefix may be terminalized or safely classified;
  capacity recovery never reopens admission or grows that prefix.
- `playing_or_in_doubt` work never auto-replays.
- A quota, cost, billing, capacity, acknowledgement, or scaling timeout is `unknown`, not success.
- Scaling, returned headroom, empty queues, or green dashboards never resume or raise mode
  automatically.

## Required Response Functions

| Function               | Responsibility                                                                                                 |
| ---------------------- | -------------------------------------------------------------------------------------------------------------- |
| Incident commander     | Owns affected scope, priority posture, load shedding, handoffs, recovery generation, and exit decision         |
| Safety/operations lead | Preserves stop/fail-closed controls and determines the restrictive capability/mode posture                     |
| Runtime owner          | Owns actor/scheduler/gateway/media/dispatch admission, queues, cancellation, and worker isolation              |
| Data/transport owner   | Owns PostgreSQL, outbox, Redis, consumers, poison handling, storage growth, and authoritative reconciliation   |
| Stage-host/operator    | Owns exact rig queue/audio/adapter/journal capacity, local stop, audience observation, and safe local recovery |
| Provider/cost owner    | Owns profile quota/circuit/usage/cost evidence and eligible fallback restrictions                              |
| Security/privacy owner | Handles adversarial flooding, resource abuse, data spill, evidence custody, and access concerns                |
| Observability owner    | Proves resource signal freshness, alert delivery, and monitoring capacity without starving control             |
| Recorder               | Maintains the minimized resource/backlog manifest, decisions, unknowns, and evidence references                |

No owner may increase capacity by bypassing a provider gateway, disabling a safety gate, exposing
Redis to the rig, weakening data separation, or changing an OPEN default during the incident.

## Immediate Containment

1. **Protect audience output.** Observe the exact local/audience output where safe. Engage local
   hard stop when output is unsafe or current control cannot be bounded.
2. **Protect independent reserves.** Stop or pause speculative/background work first: filler,
   prefetch, cache warming, reindexing, embedding, analytics, export, replay, verbose telemetry,
   and nonessential recovery.
3. **Restrict admission.** Deny new affected work before the hard bound. Apply per-session,
   provider, rig, category, and global fairness without sacrificing safety priority.
4. **Expire or cancel stale work.** Revalidate remaining deadline and authorization. Do not renew
   queued work or issue replacement identities to make backlog look current.
5. **Preserve safe-direction control.** Reserve cloud/local e-stop, freeze, mode decrease,
   cancellation, rights/access/deletion invalidation, heartbeat, current playout interruption,
   and required evidence capacity.
6. **Apply degradation.** Move affected capability to the accepted restrictive posture when
   safety/control reserve, downstream capacity, quota/cost, rig, or authority is uncertain.
7. **Contain amplification.** Bound retries/fallbacks/reconnects, disable implicit SDK retry,
   prevent synchronized recovery probes, and pause backlog drain.
8. **Protect authoritative persistence.** Do not let telemetry, export, cleanup, replay, or
   background reads consume connections/storage needed for restrictive state and audit/outbox.
9. **Record unknowns.** Capture affected resources, queues, scopes, releases, profiles, rigs,
   epochs, time range, soft/hard states, last trusted measurements, and actions without copying
   restricted content.
10. **Escalate abuse or disclosure.** Invoke security/privacy response when flooding, resource
    theft, credential misuse, malicious payload, data spill, or evidence tampering is plausible.

Every containment/scaling/provider/storage operation has explicit timeout, outer deadline,
bounded retry/cancellation, and late-result reconciliation. A partial result does not justify
more admission.

## Resource And Backlog Manifest

For every affected resource record:

- stable inventory identity, owner, component/capability, environment/session/provider/rig/surface
  scope, and software/configuration version;
- work unit, soft warning, hard bound, reserved safety/control capacity, current/peak/oldest state,
  and signal freshness;
- queue ordering, durable acceptance, acknowledgement, idempotency, deadline, epoch, and
  cancellation posture;
- normal-work admission status/epoch, closure cause, fixed committed-prefix cut, frozen schedule
  cursors, remaining drain work, and final-close blocker;
- admitted, in-flight, queued, playing, completed, rejected, expired, cancelled, failed-closed,
  poison, and in-doubt counts/bytes/ages;
- upstream/downstream backpressure and last trusted capacity advertisement;
- provider quota/circuit/usage/cost reservation, estimate, report, reconciliation, and unknown
  state;
- data classification, spill/overflow, retention, deletion/hold, and evidence risk;
- immediate restriction, shedding action, owner, timeout/result, and recovery prerequisite.

An unavailable metric or stale dashboard makes current capacity unknown. It never supplies zero
backlog or available headroom.

## Failure Matrix

| Boundary                                | Immediate posture                                                                                                                 | Authoritative recovery source                                 |
| --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| Ingest/moderation flood                 | Rate-limit/reject before session actor; preserve control and moderation capacity; never pass unscreened input                     | Platform cursor plus accepted normalized input/domain records |
| Actor/scheduler mailbox                 | Stop new normal/speculative admission; process restrictions/cancellation ahead of normal work; expire stale turns                 | PostgreSQL aggregate/idempotency/deadline state               |
| Generation provider                     | Deny new attempts when quota/cost/circuit unknown/exhausted; eligible fallback only through reviewed profile and same safety gate | Provider-neutral attempt and VNova quota/cost ledger          |
| Safety classifier/evaluation            | Reserve for admitted work; if unavailable or saturated, mint no approval and fail closed                                          | Safety decision/attempt lineage in PostgreSQL                 |
| Operator review                         | Admit only within approved queue/deadline policy; expire rather than auto-approve                                                 | Candidate/evaluation/deadline and operator decision state     |
| TTS/media/object                        | Stop new synthesis/dispatch, preserve current authorized interruption, reject incomplete/unverified artifact                      | Approval/rights/surface state plus immutable artifact record  |
| PostgreSQL/connections/storage          | Apply immediate restrictive state locally/in process; stop claims of durable success and new recoverable work                     | Restored coherent PostgreSQL plus recovery evidence           |
| Outbox/Redis/consumer/DLQ               | Keep state in PostgreSQL; pause unsafe consumers/backlog growth; never infer history from Redis                                   | PostgreSQL outbox/domain state and consumer durable markers   |
| Stage-host queue/audio/adapter          | Block new task acceptance/dispatch; preserve local e-stop/watchdog; evict expired/old-epoch work                                  | Local durable journal plus PostgreSQL reconciliation          |
| Stage-host disk/journal                 | Block new autonomous acceptance/playback if durability/evidence cannot be proven                                                  | Preserved local records plus cloud authoritative state        |
| Telemetry/exporter                      | Shed allowed diagnostics first; preserve domain/audit; invoke telemetry runbook                                                   | Source state/audit plus reviewed signal pipeline              |
| Delete/restore/index/archive/background | Pause background work and quarantine partial results; never outrank live safety/control                                           | Applicable source/tombstone/hold/restore manifest             |
| Global CPU/memory/network/event loop    | Stop low-priority producers; isolate/block CPU-heavy work; preserve control channel and current output safety                     | Process/target evidence plus PostgreSQL and rig state         |

The most restrictive applicable row wins. A resource-specific recovery never waives rights,
privacy, identity, safety, disaster, or supply-chain holds.

## Diagnosis

### Prove The Bottleneck And Amplification Path

Trace work from admission through:

```text
ingest
  -> actor / scheduler
  -> generation
  -> safety / operator review
  -> TTS / media / object
  -> dispatch / transfer
  -> stage-host queue / audio / renderer
  -> terminal state / audit / outbox / consumers
```

At each boundary compare arrival, admission, service, completion, rejection, expiry, cancellation,
retry/fallback, queue depth/bytes/age, resource saturation, and downstream capacity advertisement.
Identify whether the symptom is:

- legitimate load beyond the reviewed profile;
- one unfair scope or abusive input;
- downstream slowness without propagated backpressure;
- retry/reconnect/replay/cache stampede;
- poison/conflicting item blocking progress;
- leaked tasks/connections/files/storage;
- provider quota/cost/billing/circuit uncertainty;
- telemetry or background work consuming reserved resources;
- split writer/consumer/rig authority;
- stale or incorrect capacity instrumentation.

Do not raise limits until the causal path, data classification, safety reserve, and failure
semantics are understood.

### Inspect Deadline And Authorization Age

For every backlog class:

- compute remaining validity from authoritative source deadlines and conservative clock evidence;
- identify expiry/cancellation/revocation/deletion/hold/epoch changes after admission;
- reject work that cannot finish the full remaining path;
- never reset TTL because capacity returned, a provider changed, or an operator waited;
- preserve only minimized terminal evidence for expired/rejected work.

### Inspect Quota And Cost

Separate:

- local admission reservation;
- provider-reported remaining quota;
- confirmed usage/billing;
- estimated but not reconciled usage;
- delayed, disputed, or unknown usage;
- soft warning, hard denial, circuit-open, and administrative disable.

A provider dashboard, delayed bill, or successful probe cannot by itself widen VNova's accepted
budget state.

## Safe Load Shedding

Shedding order is capability-specific but follows these constraints:

- stop new background/speculative work first;
- reject before expensive work when the complete path lacks capacity;
- preserve already playing authorized output only while current safety/expiry/rights/surface and
  local control remain valid;
- never drop an e-stop, restriction, cancellation, deletion/right/access invalidation, required
  audit/outbox, or current rig safety event;
- never auto-approve operator-queue work;
- never discard poison/conflicting data silently; quarantine and expose bounded evidence;
- never route around a provider gateway, safety classifier, object integrity check, or stage-host
  verifier;
- record a stable normalized terminal outcome for every admitted work identity.

If the system cannot shed safely because queue ownership or item classification is unknown, stop
new affected autonomous work.

## Recovery And Drain

### Establish A Stable Restricted Baseline

1. Prove one writer/consumer/rig authority and exact recovery/ownership composite actor fence per
   scope through the shared ownership-row mechanism.
2. Restore safety/control and restrictive-dispatcher priority reserves plus the independent local
   stop path.
3. Reconcile PostgreSQL aggregates, submission-generation commands, four-record ordinary
   effects, distinct four-role recovery-probe lineages/source classifications, canonical
   timer/materialization/current claims, normal-work admission/closure prefix and frozen cursors,
   recovery frontiers/lost-tail disposition, decisions, approvals, restrictions, audit/outbox,
   deletion/hold, rights, and current epochs.
4. Reconcile stage-host task/queue/journal/audio/adapter state; mark
   `playing_or_in_doubt` terminally in-doubt without replay.
5. Reconcile quota/circuit/usage/cost and telemetry/alert health through bounded synthetic
   probes. These are not session-bound `RecoveryProbe*` authority. A call classifying a specific
   effect/dispatch/rig/lost-tail ambiguity must use the distinct lineage and binding below.
6. Quarantine poison, conflicting, partial, stale, expired, old-epoch, deleted, revoked, or
   unverifiable work.

### Drain Deliberately

1. Identify which cut governs the drain. Recovery activation may classify its fixed pre-cut
   frontier while leaving later normal rows pending. Session closure may process only the exact
   pre-close committed prefix and must create no later command lineage, eligible input,
   occurrence identity, cursor advance, claim, firing, Turn, ordinary effect intent/send/
   advancing application, or other ordinary candidate/approval/media/task/dispatch progression.
   Bounded late observations remain evidence-only, and prior send-authorized attempts remain
   possibly sent until safely classified. Redis/provider/local queues and PITR absence cannot
   manufacture either list or prove no earlier work. The sole session-bound external evidence
   exception is a distinct recovery-probe lineage under exact active+draining-prefix or
   recovering+recovery-attempt/source binding, with finite bounds, no widening, and one terminal
   disposition.
2. Set an approved bounded drain profile below proven downstream headroom while preserving
   safety/control/current work reserves.
3. Revalidate deadline, policy, approval, rights, surface, artifact, epoch, rig, and idempotency at
   every handoff.
4. Monitor queue items/bytes/age, tail latency, failures, retries, headroom, quota/cost, local
   output, and alert delivery.
5. Stop drain on renewed growth, uncertainty, poison, unfairness, reserve erosion, or unexpected
   output.
6. Expire rather than renew backlog that cannot complete.
7. Admit new normal work only for a session whose exact admission epoch remains `open` and only
   after the reviewed overlap/drain policy proves it cannot starve recovery or control. A
   `draining` or `closed` session never reopens; a recovery-only successor may only finish the
   fixed closure prefix and atomic final close. Lost-tail recovery first makes restored
   `open`/`draining(normal_closure)`/atomic-`closed` lifecycle and admission axes coherent,
   applies any monotonic quarantine overlay, and blocks close on unresolved tail/target evidence.
   Probe originating fence is provenance: a current same-source successor may zero-attempt or
   stale/unknown terminalize without resend. Close also requires every probe terminal and every
   bound source ambiguity resolved/permanently safe-quarantined/accountably disposed.

### Deliberate Capability Restoration

Returned capacity does not restore the previous mode. Run the normal recovery preflight, resolve
the initiating cause, prove target-specific negative cases, and obtain the required human
confirmation/reason for resume or mode increase. Create a new authorization context where the
governing ADR requires it.

## Exit Criteria

All are required:

- the resource/backlog manifest is complete and every unknown has a disposition;
- exact queues/resources are within the approved recovery/steady profile with trustworthy signal
  freshness and stable headroom;
- safety/control reserves remain isolated under current load;
- no unbounded or unexplained CPU, memory, task, connection, file, storage, queue, journal,
  telemetry, retry, or cost growth remains;
- PostgreSQL, outbox, consumers, object state, provider ledger, rig queue/journal, and terminal
  outcomes are reconciled;
- every expired, cancelled, poison, in-doubt, old-epoch, deleted, revoked, or unauthorized work
  item is rejected/quarantined and cannot replay;
- every non-open session has no post-begin-close-cut normal-work growth; every closed session has
  no accepted nonterminal prefix work, and any initial or overlaid `lost_tail_quarantine` session
  remains `Ending`/draining until its terminal target, accountable tail disposition, and exact
  rig/audience reconciliation permit atomic final close; every admitted recovery probe is
  terminal/non-widening and its bound source ambiguity is resolved/permanently
  safe-quarantined/accountably disposed, while terminal `unknown` evidence remains truthful;
- backpressure reaches admission and the same overload no longer grows hidden downstream work;
- quota/cost/billing/circuit state is reconciled or remains conservatively restricted;
- alerts, runbooks, local stop, and target-specific fault cases pass;
- any resume/mode increase is a separate human-authorized action with no revived old work.

Empty queues are not enough if work was silently lost, dropped without terminal evidence, moved to
another store, or drained through an unsafe path.

## Evidence And Audit

Retain only:

- incident, resource, inventory, deployment, release, session, rig, boot, provider/profile,
  queue, task, event, trace, command, quota/cost, and evidence-manifest IDs;
- reviewed limit/profile/configuration versions and privacy-safe integrity references;
- queue/resource warning, peak, hard-bound, overflow, shedding, timeout, retry, drain, and final
  outcomes;
- authoritative state/reconciliation references and explicit unknowns;
- stop, restriction, mode, alert, runbook, human decision, finding, owner, and follow-up.

Do not put raw prompts, candidates, viewer memory, provider bodies, secrets, credentials, rights
documents, unrestricted personal data, media, or poison payloads in ordinary incident evidence.

## Escalation

Escalate without widening capacity or availability when:

- e-stop, safety/control reserve, current playout interruption, heartbeat, or required evidence
  capacity is unavailable;
- overload may have produced unsafe, stale, unauthorized, unrecorded, or silently lost work;
- database, outbox, consumer, actor, or rig authority is split or unrecoverable;
- local disk/journal/queue corruption or exhaustion affects playback safety;
- quota/cost/billing is materially unknown or an unapproved spend/override occurred;
- flooding, credential abuse, malicious payload, supply-chain issue, or telemetry tampering is
  plausible;
- personal/restricted data may have spilled through logs, disk, provider, cache, evidence, or
  overflow paths;
- recovery would require unbounded replay, fabricated history, risk acceptance of an invariant,
  or bypass of target validation.

Exact severity, contacts, scaling authority, provider coordination, cost approval, and
communications remain human decisions.

## Required Rehearsal Scenarios

Before production authorization, exercise:

- flood/skew across viewers, sessions, trigger classes, providers, rigs, and surfaces;
- saturation of each actor/scheduler/generation/safety/operator/TTS/media/dispatch/rig queue at
  soft warning, hard bound, and unknown signal states;
- safety reserve contention after generation admission, proving zero speech without determinate
  safety;
- database connection/storage/outbox growth, Redis loss/lag/poison, consumer crash, and
  PostgreSQL-only reconstruction;
- provider rate/concurrency/quota/cost warning/limit/billing lag/circuit/fallback and recovery
  probe stampede;
- object transfer/storage/cache pressure, incomplete artifacts, and orphan cleanup;
- stage-host queue/audio/adapter/disk/journal exhaustion, power loss, reconnect, and in-doubt work;
- event-loop/CPU/memory/task/thread/file/connection leak plus telemetry exporter/cardinality load;
- retry/fallback/rewrite/reconnect/replay/cache-warm amplification and bounded cancellation;
- ownership-row renew/revoke/takeover contention, command/effect/timer/restrictive-control claim
  backlog, receipt response loss, immutable activation-frontier/schedule-cursor snapshots versus
  excluded harmless post-cut operational-cursor churn/no-starvation, recovery-attempt-bound
  probe-write plus ambiguity/restriction invalidation, nonterminal-probe/enabled-scope
  unresolved-source activation rejection, preallocated-ID commit reorder,
  begin-close admission/source races across command auth-lineage/claim/execution, every normal
  input/Turn/effect and candidate/approval/media/task/dispatch path, bounded late-evidence/
  terminal non-advancing fixed-prefix drain, cursor freeze, atomic final-close races, lost-tail
  restored-open/draining/closed lifecycle-admission coherence, monotonic quarantine overlay,
  unresolved-target blocking, distinct recovery-probe dual binding/zero-attempt/current-successor
  no-resend/finite-bound/terminal-unknown-source-axis/final-close behavior, recovery-scan
  pressure, and protected safe-direction capacity;
- background deletion/restore/index/archive/backup work contending with live control;
- backlog drain with new traffic, poison, expiry, revocation, deletion, old epoch, and renewed
  saturation;
- full load/stress/spike/soak/chaos evidence under the
  [acceptance packet](../governance/load-soak-chaos-acceptance.md).

## OPEN Decisions

Human approval is required for:

- OD-014 acceptance of ADR-025 structural ownership/recovery plus retry/fallback/rewrite,
  segment priority/interruption, trigger, scheduling, and catch-up policy;
- OD-027/028 incident command, exercise/validation, threat assumptions, finding severity, and
  residual-risk authority;
- OD-035 actor lease/effect horizon, timeout/deadline/recovery timing, and clock-validity profile;
- OD-036 resource/queue/alert signal definitions, telemetry posture, thresholds, routes, response
  objectives, and evidence freshness;
- OD-037 inventory ownership, work units, warning/hard bounds, protected reserves, priorities,
  fairness, admission, command auth-lineage/claim/execution, effect intent/send/application,
  timer claim/poll/scan/retry, all ordinary pipeline progression, shedding, overflow,
  begin-close and bounded late-evidence/terminal non-advancing fixed-prefix drain/cursor-freeze/
  final-close, recovery, and database/Redis/object/runtime/rig/audio/journal/telemetry
  capacity/storage/compaction/scaling profile;
- OD-038 provider quota/circuit/cost accounting, warning/limit, billing reconciliation, override,
  and fallback composition;
- OD-039 load/stress/spike/soak/chaos workload, duration, target, blast radius, abort, pass/fail,
  finding disposition, and production-execution eligibility; and
- target-specific commands, contacts, credentials, retention, and exact ADR-020 mode posture
  through the applicable protected deployment review.
