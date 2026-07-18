# Offline Observation And Domain-Event Reconciliation

Status: Proposed operational runbook; implementation and production use pending

Readiness state: `Drafted` only; no rehearsal, target validation, or production authorization

Date: 2026-07-17

Sources: `AGENTS.md`, `vnova-review-handoff.md`, ADR-003, ADR-004, ADR-007, ADR-008,
ADR-011, ADR-015, ADR-016, ADR-017, ADR-018, ADR-019, ADR-020,
ADR-023, `docs/architecture/rehearsal-mode.md`,
`docs/architecture/privacy-retention-model.md`

This document describes an intended reconciliation workflow. It does not authorize a replay,
runtime command, endpoint, schema, migration, Redis layout, local journal, timeout, retry,
retention value, or production operation while its governing ADRs and OD-027 remain unresolved.

## Purpose And Scope

Use this runbook after one or more of these conditions:

- `stage-host` disconnected and buffered local observations;
- the runtime or rig restarted with queue or acknowledgement ambiguity;
- a domain-event causal-position conflict/missing relevant fact, non-event protocol sequence gap,
  duplicate, conflicting identity, or clock discontinuity appeared;
- Redis Streams was unavailable, reset, expired, flushed, or accumulated backlog;
- an outbox publisher or consumer failed before its acknowledgement boundary;
- offline-buffer capacity, durability, integrity, or shipping became uncertain;
- PostgreSQL, outbox, runtime, Redis, and stage-host observations do not agree.

The workflow reconciles two bounded mechanisms without turning either into a new system of record:

1. PostgreSQL outbox delivery through Redis Streams to cloud consumers;
2. stage-host's crash-consistent local queue and minimized offline observation journal through the
   authenticated runtime protocol.

PostgreSQL remains authoritative for cloud session, turn, decision, approval, command, audit, and
outbox state. Redis is an at-least-once transport. The local journal is safety evidence and a
bounded offline buffer, not authority to approve, dispatch, raise mode, resume, or rewrite cloud
history.

## Non-Negotiable Invariants

- Recovery and incident reconstruction start from PostgreSQL, never Redis retention, consumer
  offsets, WebSocket buffers, or in-memory queues.
- Redis stream IDs, consumer offsets, publisher cursors, and dead-letter entries are operational
  metadata only.
- Replayed or retried outbox delivery preserves the original canonical `event_id`, complete
  event-contract identity, typed primary scope, aggregate subject, aggregate version/event index,
  transition count/manifest identity, content, occurrence time, and payload-schema identity.
- Delivery is at least once. Duplicate identity plus identical canonical content is idempotent;
  duplicate identity plus different content is an integrity incident.
- Domain-event publishers preserve `(aggregate_version, event_index)` inside each
  catalog-declared subject lane; cross-lane ordering is not implied. A version gap alone is not
  loss when an aggregate mutation emitted no event or catalog filtering explains it. Every
  committed aggregate version has a PostgreSQL manifest, including a zero-count manifest, and
  every ordered consumer reconciles its authorized transition-manifest/expected-delivery
  high-water. A missing tail, whole manifest version, required subset member, zero/empty
  attestation, or conflicting manifest freezes the projection; Redis silence never proves
  completeness.
- The non-event speech/avatar task/control protocol has a separate ADR-011/OD-021
  session/epoch/sequence contract. A protocol gap pauses that lane; no component guesses,
  silently skips, or derives it from EventEnvelope or Redis.
- A consumer validates trusted envelope framing, immutable event-contract profile,
  operation-specific catalog lifecycle evidence, producer, historical classification plus current
  restrictive protection overlay identities/epochs/partition high-waters, scope, subject,
  ordering/completeness manifest, complete envelope, and payload before effects. Its durable side
  effect, processed-event marker, observed protection evidence, and completeness progress commit
  atomically where it owns persistent state. Later irreversible handling revalidates current
  protection at its immediate boundary.
- Stage-host is the sole consumer of `SpeechTask`; Redis is never exposed to the rig.
- Reconciliation cannot manufacture safety authority. Retry, rewrite, or provider-fallback
  content still enters the same complete safety gate, and media remains identifier-only.
- Emergency latch, newer restrictive epoch, expiry, and explicit cancellation dominate queue and
  replay state.
- A `playing_or_in_doubt` queue entry is never replayed automatically after restart.
- Missing, corrupt, rolled-back, or conflicting local replay/journal state marks the rig unsafe
  and blocks new autonomous task acceptance; local safety controls remain available.
- Every database, Redis, authenticated-link, object-download, identity, and other external
  operation has an explicit timeout. Retries are bounded, observable, and cannot extend content
  authorization.
- Ordinary outbox, Redis, WebSocket, stage-host journal, log, trace, alert, ticket, and incident
  evidence contains no raw candidate text, full prompt, viewer-memory content, credential, secret,
  provider payload, or unrestricted media.

## Trigger And Containment Matrix

| Observed condition                                           | Immediate restriction                                                                                                     | Reconciliation source                                                      |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| PostgreSQL unavailable or authoritative state unreadable     | Hold the strongest known local/cloud restrictive state; no resume, mode increase, new replay, or claim of durable success | Wait for PostgreSQL recovery and validate authoritative rows               |
| Redis unavailable, empty, expired, or flushed                | Leave committed outbox records pending; do not infer domain loss or reconstruct from transport                            | PostgreSQL outbox                                                          |
| Publisher crash after possible publish                       | Expect possible duplicate; create no replacement identity                                                                 | Original PostgreSQL outbox row                                             |
| Consumer crash before acknowledgement                        | Expect redelivery; preserve idempotency and atomic side-effect marker                                                     | Consumer authoritative store plus PostgreSQL event identity                |
| Domain-event causal conflict or missing required predecessor | Freeze only the dependent projection/lane; do not infer loss from a valid filtered version gap                            | PostgreSQL aggregate/event/outbox plus consumer profile/inbox              |
| Stage-host protocol sequence gap or conflicting duplicate    | Pause later speech/avatar work and enter protocol resynchronization                                                       | PostgreSQL command/state plus stage-host durable queue evidence            |
| Stage-host disconnect or unknown binding/epoch               | Stop new dispatch; use local watchdog mute/neutral scene policy                                                           | PostgreSQL session/epoch plus authenticated reconnect evidence             |
| Local queue/journal corruption, rollback, or exhaustion      | Mark rig unsafe and block new autonomous acceptance; keep local hard stop available                                       | Preserved local evidence plus PostgreSQL; do not manufacture missing state |
| Clock mapping stale, discontinuous, or too uncertain         | Reject time-bounded task acceptance/playback until resynchronized                                                         | Original timestamps plus new four-timestamp evidence                       |
| E-stop or restrictive epoch disagreement                     | E-stop and the newer restrictive epoch win; evict old-epoch queued work                                                   | Reconciled PostgreSQL state plus durable local latch/epoch evidence        |
| Task expired, cancelled, flushed, or `playing_or_in_doubt`   | Never revive or automatically replay                                                                                      | Terminal evidence; any future work requires new authorization context      |

If broadcast output is unsafe or cannot be observed independently, use the local hard stop and the
safety fail-closed runbook rather than waiting for transport reconciliation.

## Response Roles

These labels follow the common runbook contract and do not grant production authority:

| Role                | Duties during this workflow                                                                                                                        |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Incident commander  | Own scope, assignments, phase transitions, unresolved conflicts, and closure evidence                                                              |
| Safety lead         | Keep fail-closed restrictions in force and verify that no replay or recovery widens authority                                                      |
| Stage operator      | Observe and control local output, preserve the rig, verify latch/queue/epoch state, and use the local stop when needed                             |
| Service owner       | Diagnose PostgreSQL, outbox, EventBus, consumer, runtime, or stage-host behavior within the assigned boundary                                      |
| Security lead       | Own conflicting identities, signature/replay anomalies, credential concerns, and suspected tampering                                               |
| Privacy/legal lead  | Decide handling when offline or transport evidence may contain personal/restricted data or when preservation duties conflict with normal retention |
| Communications lead | Use approved resilient channels for internal, talent, platform, or external communication                                                          |
| Recorder            | Maintain the minimized timeline, reconciliation manifest, decisions, evidence locations, and unresolved findings                                   |

OD-027 must map these labels to accountable people, coverage, capabilities, escalation paths, and
separation-of-duty requirements before live use.

## Immediate Containment

Perform containment before attempting replay or queue repair.

1. **Confirm local broadcast state.** The stage operator independently checks audio, enabled
   surfaces, fallback scene, local emergency latch, watchdog, and adapter state. A cloud heartbeat
   or WebSocket status is not sufficient.
2. **Apply the strongest restriction.** If local output, epoch, queue integrity, or authoritative
   state is uncertain, stop dispatch, deny new autonomous admission, lower the applicable mode
   ceiling, and use the local hard stop when current output may be unsafe.
3. **Freeze affected causal/protocol lanes.** Freeze a domain projection when its required
   predecessor cannot be proven; pause speech/avatar work across a non-event protocol sequence
   gap, conflicting identity, unknown epoch, or uncertain queue transaction. Do not infer one
   lane's order from the other.
4. **Preserve local state.** Keep the original stage-host queue/journal, boot identity, cursor,
   digests, timestamps, monotonic offsets, latch, epoch, and adapter outcomes intact. Do not
   manually edit queue records, fabricate acknowledgements, or replay uncertain work.
5. **Preserve cloud state.** Keep PostgreSQL aggregate, command, audit, outbox, publisher-attempt,
   and consumer-marker evidence. Do not rewrite outbox records or create replacement event
   identities.
6. **Treat Redis as disposable transport.** Stop relying on current stream contents or offsets for
   history. Do not copy Redis data into PostgreSQL as reconstructed domain truth.
7. **Bound automated activity.** Pause or constrain publishers, consumers, reconnects, downloads,
   and resends through the approved restrictive control when they could amplify duplicates or
   obscure evidence. Do not introduce unreviewed retry or concurrency values.
8. **Open a minimized incident record.** Record affected IDs, time interval, session/rig/epoch,
   suspected boundary, and restrictive state without copying restricted content.

If containment persistence fails, hold the process-local state as `uncommitted_restrictive`, retry
the authoritative state/audit/outbox transaction with bounded operations, and prohibit recovery
until durable reconciliation succeeds.

## Read-Only Diagnosis

The diagnosis phase does not publish/replay an event, acknowledge a message, mutate a queue,
advance a cursor, clear a latch, restore a profile, raise mode, or resume playback.

### Establish The Authoritative Cloud View

From PostgreSQL, collect by identifier:

- current `StreamSession` lifecycle, requested/effective mode, degradation causes, emergency
  state, aggregate version, authorization epoch, rig binding, and operator presence;
- affected turn, candidate, safety decision, approval, media authorization, task/command,
  deadline, cancellation, and expiry lineage;
- distinct immutable domain-event and one-to-one outbox identities, complete event-contract
  profile, emission catalog state/epoch/transition evidence, trusted envelope framing,
  payload-schema identity/digest, environment and typed primary scope, aggregate subject,
  aggregate version/event index, transition count/manifest identity, session/turn correlation,
  occurrence time, canonical digest, historical classification, and publish-attempt state;
- every aggregate-version transition manifest including zero-count manifests, each authorized
  consumer's exact expected subset/zero-or-empty attestation/high-water, processed-event markers,
  durable side-effect references, and observed protection evidence where PostgreSQL is the
  consumer's authoritative store;
- current applicable protection-overlay identities/states/epochs/digests and authoritative
  protection-partition high-waters;
- idempotency records, audit metadata, restrictive transitions, and unresolved recovery holds.

Missing or contradictory authoritative evidence is a blocker. Redis contents cannot fill the
gap.

### Establish The Transport View

Inspect Redis and publisher/consumer telemetry only to answer operational questions:

- which committed outbox identities may have been attempted, delivered, duplicated, delayed, or
  left pending;
- which consumer groups report lag or unacknowledged transport work;
- whether a poison/unsupported event blocked progress;
- whether Redis loss, retention, or reset explains a delivery gap;
- whether each external operation used an explicit timeout and bounded retry.

A stream entry is not proof that its domain state committed, and absence from Redis is not proof
that the domain event never existed.

### Establish The Stage-Host View

Using preserved read-only local evidence, collect:

- enrolled rig, connection, stage-host boot, stream-session, and accepted epoch identities;
- emergency latch, watchdog, adapter, audio, clock, offline-buffer, and local durability state;
- last durably accepted message/task, sequence, canonical digest, replay identity, expiry, queue
  status, and acknowledgement stage;
- every `accepted`, `playing_or_in_doubt`, completed, interrupted, rejected, flushed, expired, or
  unknown record in the affected lane;
- offline observation cursor, stable observation identities, boot-local sequence, original UTC timestamp,
  monotonic offset evidence, schema version, classification, and canonical digest;
- queue/journal corruption, rollback, capacity, fsync/atomicity, restart, sleep/resume, or
  wall-clock discontinuity evidence.

A receipt acknowledgement is not application acceptance, and acceptance is not evidence of
playback. Preserve those states separately.

### Compare Without Mutating

Build a reconciliation manifest keyed by stable identity and canonical digest:

| Comparison                                                    | Safe interpretation                                                           |
| ------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Same identity and same canonical digest                       | Duplicate; eligible for idempotent handling                                   |
| Same identity and different canonical digest                  | Integrity incident; do not choose one silently                                |
| PostgreSQL event exists, Redis delivery absent/unknown        | Pending transport work; PostgreSQL remains authoritative                      |
| Redis entry exists, PostgreSQL source event absent            | Unverifiable transport data; do not apply                                     |
| Stage-host accepted identity exists in runtime, states differ | Apply precedence and acknowledgement semantics; do not infer playback         |
| Stage-host identity absent in authoritative runtime           | Unknown/unverifiable work; never authorize from local presence alone          |
| Local event timestamp conflicts with cloud time               | Preserve original time and calculate a separate corrected/estimated value     |
| Session epoch differs                                         | Engaged latch or newer restrictive epoch dominates; old-epoch work is invalid |

Do not expose raw task content to compare records: `SpeechTask` is identifier/integrity/timing only,
and canonical digests plus reviewed fields are sufficient.

## Reconciliation Procedure

Proceed phase by phase. A failed gate returns to containment.

### Phase 1: Restore Authoritative Readability

1. Restore read access to the accepted PostgreSQL state through the deployment's approved
   procedure.
2. Validate aggregate, audit, outbox, idempotency, decision/approval, and restrictive-state
   consistency before permitting mutation.
3. If the database recovery point precedes known restrictive local evidence, retain the lower
   local/cloud state and escalate. Never use a potentially older database image to widen
   authority.
4. Do not declare PostgreSQL recovered solely because a connection succeeds; required
   constraints, transaction evidence, and state relationships must be coherent.

Exact database restoration and integrity commands are target-specific and remain outside this
Proposed runbook.

### Phase 2: Reconcile Session Safety State

1. Apply precedence in this order: engaged emergency latch or newer restrictive epoch; expiry or
   cancellation; verified current authorization; then sequence/queue progress.
2. Persist any previously `uncommitted_restrictive` transition, audit metadata, and all required
   outbox records in one PostgreSQL transaction before considering recovery.
3. Recompute the safe effective mode from current policy, health, presence, release, and recovery
   holds. Network or transport recovery never raises it.
4. Advance or retain the authorization epoch required by the accepted mode/stop decisions; never
   restore an older epoch.

### Phase 3: Establish A Fresh Rig Binding

1. Complete an authenticated, version-negotiated reconnect with explicit timeout.
2. Exchange the current emergency state, session epoch, rig and boot identities, queue summary,
   accepted/terminal task identities, offline cursor, verification-key metadata, and clock
   capability.
3. Reject an old or competing binding unless the accepted takeover procedure has reconciled it
   against PostgreSQL.
4. Fail closed on unsupported versions, unknown fields, authentication failure, contradictory
   epoch/latch state, or uncertain clock mapping.

Reconnect establishes a channel; it does not authorize old work or clear a stop.

### Phase 4: Reconcile The Local Queue

For each queue entry:

- **Old epoch, expired, cancelled, flushed, invalid signature/integrity, or unverifiable:** evict
  or retain as terminal evidence according to the approved local storage policy; never play.
- **`playing_or_in_doubt`:** cut/mute uncertain output, preserve the state, and never replay
  automatically.
- **Accepted but not started:** it remains eligible only if current signature, session/rig
  binding, epoch, sequence, every authorization reference, artifact digest, mode, interruption
  policy, clock evidence, and immediate expiry check pass. Otherwise reject it. No local rewrite
  or deadline extension is allowed.
- **Completed/interrupted/rejected terminal state:** reconcile the distinct terminal outcome
  idempotently; do not re-execute the task.
- **Sequence gap:** keep later ordered work paused until authoritative sequence reconciliation
  resolves the gap.
- **Conflicting identity/digest:** preserve both references as an integrity incident and block the
  lane.

Stage-host records queue decisions durably before acknowledgement according to the accepted
crash-consistency profile.

### Phase 5: Ingest Offline Stage-Host Observations

1. Bind the batch to the authenticated rig, boot identity, stream session, epoch, cursor, schema
   versions, and bounded payload.
2. Validate every observation before side effects. Reject malformed, oversized, unknown-version,
   wrong-session, or unauthorized records into the human-approved terminal handling path.
3. Deduplicate by stable observation identity and canonical digest. Same ID/different digest is an
   integrity incident, not a duplicate.
4. Commit the accepted observation/evidence and processed marker durably before returning the
   application acknowledgement required by the protocol.
5. Preserve original local UTC and monotonic evidence. Store clock-corrected or estimated time as
   a separate derived field with the sample/uncertainty reference.
6. Advance the shipping cursor only after durable acceptance. A timeout produces an unknown
   outcome and is retried idempotently with the same identities.
7. Delete or compact the local copy only under the accepted acknowledgement, retention, privacy,
   and durability policy. This runbook supplies no retention duration.

An offline observation cannot retroactively authorize playback or overwrite authoritative
command/session state.

### Phase 6: Resume PostgreSQL-Backed Event Delivery

1. Identify committed pending outbox rows, transition manifests, authorized expected-delivery
   sets/high-water, and their catalog-declared subject-lane positions from PostgreSQL.
2. Publish each canonical envelope through the internal `EventBus` with its original identity and
   explicit timeout. Do not synthesize an event from Redis state or issue a new identity on retry.
3. Preserve `(aggregate_version, event_index)` within every catalog profile that requires ordered
   application while allowing unrelated subject lanes to progress independently. Verify every
   received transition count/manifest identity against PostgreSQL. Do not route the stage-host
   task/control sequence through this event path.
4. After Redis accepts a publish, persist publisher delivery evidence. If that persistence times
   out or fails, retry may duplicate the same event; it must not create new content or identity.
5. Consumers validate the complete profile, operation-specific catalog lifecycle evidence,
   envelope/payload, current restrictive protection overlay identities/epochs/partition
   high-waters, and exact authorized manifest subset or zero/empty attestation; then atomically
   commit durable side effects, processed-event markers, observed protection evidence, and
   completeness progress before Redis acknowledgement. A later irreversible effect revalidates
   current protection at its immediate boundary. Safety/authorization projections remain stale
   until every required manifest version through the authoritative high-water is proven.
6. Unsupported or poison events enter the accepted terminal handling/replay authorization path.
   Do not silently drop them, loop without bound, or treat a dead-letter stream as durable truth.

Redis may be repopulated from committed PostgreSQL outbox records only through the authorized
recovery procedure. A Redis restore is transport recovery, not historical restoration.

### Phase 7: Converge And Observe

1. Compare PostgreSQL pending/delivered state, consumer durable markers, Redis transport
   observations, and stage-host cursor/queue state again.
2. Confirm no unresolved required event predecessor, protocol sequence gap, conflicting digest,
   unknown epoch, missing restrictive transition, stale clock mapping, or
   `playing_or_in_doubt` item can produce playback.
3. Confirm backlog is reducing under approved bounds without starving safety and operator-control
   paths.
4. Validate newly authorized work end to end with new current authorization context; do not use
   an incident-era task as a recovery probe.
5. Keep the upward-recovery hold until all exit gates pass and an authorized human deliberately
   confirms any mode increase or emergency resume.

## Abort And Safe-Hold Conditions

Stop reconciliation and remain in the restrictive state when:

- PostgreSQL cannot prove coherent authoritative state;
- a restrictive local observation is newer than the recoverable cloud evidence;
- an event/task identity has conflicting canonical content;
- the queue/journal is corrupt, rolled back, or cannot prove its accepted durability;
- stage-host binding, epoch, latch, signature, artifact, sequence, or clock state is uncertain;
- a required envelope/event-contract version, manifest/high-water rule, restrictive overlay, or
  terminal poison-event path is unapproved;
- an operation repeatedly times out or retry would exceed the approved bound;
- evidence contains prohibited content or a privacy/security incident is suspected;
- recovery requires an invented command, threshold, role, vendor default, or bypass.

Safe hold may include Mode 0, stopped dispatch, local mute, approved neutral scene, blocked ordered
lane, or ineligible rig, depending on the already accepted controls. It never includes
unverifiable speech.

## Recovery Exit Gates

The affected autonomous capability may recover only when every applicable gate below passes. If a
blocker remains, active investigation may transition only to an explicitly disabled or safe-held
handoff with an accountable owner; the capability is not reconciled or recovered.

- PostgreSQL is readable, internally coherent, and authoritative for every affected aggregate,
  command, decision, approval, mode, epoch, audit, and outbox record;
- every previously local-only restrictive observation has been durably reconciled;
- every affected outbox identity required for safety or catalog-declared causal convergence is
  durably delivered; any other pending identity has an explicit non-enabling handling state and
  cannot conceal a missing relevant predecessor;
- consumer side effects and processed-event markers agree, with no conflicting event identity;
- Redis is functioning only as transport and no recovery claim relies on its retained history;
- stage-host has one authenticated current binding, current restrictive epoch/latch, valid clock
  evidence, and a crash-consistent reconciled queue;
- every old-epoch, expired, cancelled, flushed, invalid, unknown, and `playing_or_in_doubt` task is
  unable to play;
- the non-event ordered speech/avatar lane has no unresolved sequence gap or conflicting digest;
- every authorization-changing domain projection has reconciled its accepted subject-lane
  manifest/high-water, with complete required sets, filtered empty/subset attestations, and
  explicit zero-count manifests distinguishing aggregate mutations without events from missing
  tails or whole transitions;
- every affected event-handling path has reconciled current protection-overlay epochs and
  partition high-waters, rejected rollback/conflict, and revalidates irreversible effects at the
  immediate boundary;
- offline observations are validated, deduplicated, durably ingested, and cursor-reconciled while
  preserving original timestamps;
- ordinary observability and the incident packet pass prohibited-content scanning;
- deterministic reconciliation and relevant crash/partition tests pass for the exact versions;
- any mode increase or resume has separate current human authority, confirmation, required
  reason, durable audit, and target-mode preconditions.

Transport health alone is never an exit gate.

## Data Minimization

Permitted ordinary evidence includes:

- opaque event, complete event-contract, environment, typed scope/subject, aggregate
  version/event index, transition manifest/high-water, session, turn, task, rig, boot,
  connection, epoch, cursor, non-event sequence, trace, policy, schema, and artifact identifiers;
- canonical digests, integrity results, classifications, reason codes, versions, timings,
  timeouts, queue states, and acknowledgement stages;
- original local timestamps, separate correction/uncertainty metadata, and normalized health
  outcomes.

Do not copy:

- raw candidate, approved, prompt, viewer-message, username, or viewer-memory content;
- media bytes, SSML, provider bodies, platform raw chat, voice data, or rights evidence;
- credentials, signing material, access tokens, secrets, or unrestricted exception bodies;
- restricted records into Redis, the stage-host journal, general incident chat, screenshots, or
  ordinary audit.

The local journal and cloud event payloads are field-allowlisted and purpose-limited. A digest does
not automatically declassify personal or restricted data. Retention, deletion, incident hold, and
legal hold follow ADR-017 and the source data class.

## Evidence Packet

Record:

- incident, environment, typed event scope/subject, complete event-contract, aggregate
  version/event index, transition manifest/high-water, session, turn, event, command, task, rig,
  boot, connection, epoch, cursor, non-event sequence, schema, policy, trace, audit, and outbox
  identities;
- PostgreSQL recovery/read-consistency evidence and each authoritative state relationship checked;
- Redis outage/restore, publisher attempt, consumer delivery, duplicate, lag, poison, and
  acknowledgement observations;
- stage-host latch, watchdog, clock, queue, replay, adapter, offline-buffer, and actual playback
  outcomes;
- canonical digest comparisons and every duplicate/conflict disposition;
- original timestamps plus separately derived correction and uncertainty;
- explicit timeout/retry/cancellation outcomes for each external operation;
- containment, mode, recovery-hold, operator, confirmation, and resume decisions;
- rehearsal scenario, deterministic seed, virtual-time schedule, target/software versions, and
  artifact hashes;
- data classes accessed, evidence location/retention policy, unresolved gaps, owners, and review
  disposition.

Reference restricted source records by ID and digest only.

## Escalation

Escalate without weakening safe hold when:

- local and PostgreSQL restrictive state cannot be ordered confidently;
- accepted task identity, playback state, or durable acknowledgement may have been lost;
- the same identity has different canonical content or signature/replay tampering is suspected;
- PostgreSQL restoration cannot prove constraints or authoritative lineage;
- stage-host queue/journal corruption, rollback, power-loss behavior, or buffer exhaustion is
  detected;
- Redis or consumer recovery would require fabricated history, silent loss, or unbounded replay;
- restricted/personal data, credentials, media, or rights evidence may have entered ordinary
  transport or incident records;
- multiple rigs, sessions, environments, or regions are affected;
- the accepted protocol, schema compatibility, replay authority, retention, or recovery policy
  cannot resolve the state.

Use OD-027's approved incident command, handoff, escalation, communications, and coverage model.
Security, privacy/legal, talent, and provider decisions remain with their accountable human
owners.

## Required Rehearsal Scenarios

Before production authorization, exercise this runbook deterministically:

- outbox crash before commit, after state commit attempt, after Redis publish, and before
  PostgreSQL delivery acknowledgement;
- consumer crash before/after side effect, processed marker, and Redis acknowledgement;
- identical duplicate, conflicting duplicate, delayed, cross-lane reordered, causal-position
  collision, mutation-without-event, filtered-empty/subset routing, missing middle/tail,
  whole-transition loss, conflicting transition count/manifest, stale high-water,
  missing-relevant-predecessor, unsupported/downgraded/conflicting envelope discriminator,
  profile-only event-contract evolution, historical replay, malformed, restrictive
  reclassification, wrong-scope, and poison events;
- Redis outage, flush, expiration, and complete loss followed by PostgreSQL-only reconstruction;
- PostgreSQL outage during cloud freeze or mode decrease, proving immediate restrictive effect and
  no resume before durable reconciliation;
- stage-host disconnect/reconnect with offline batches, duplicate ingest, cursor timeout, raw
  per-host clock evidence, and a separately derived cross-host timeline;
- runtime process crash, stage-host process crash, and power loss at every queue transaction,
  acceptance, `playing_or_in_doubt`, adapter start, completion, terminal commit, and
  acknowledgement boundary;
- stage-host journal corruption, rollback, capacity exhaustion, and loss of required audit
  durability;
- e-stop and newer restrictive epoch racing with queued work on connected and partitioned rigs;
- accepted-but-not-started, expired, cancelled, flushed, old-epoch, wrong-session,
  digest-mismatched, replayed, and `playing_or_in_doubt` tasks;
- wall-clock step, offset/drift, stale/uncertain samples, asymmetric delay, sleep/resume, reboot,
  and pre-playback expiry;
- restore from backup with deletion/tombstone reconciliation before restored data becomes
  available;
- ordinary event, Redis, journal, log, alert, trace, and evidence scanning for prohibited content;
- full incident-timeline reconstruction from PostgreSQL plus minimized stage-host evidence,
  explicitly excluding Redis as history.

Each scenario asserts restrictive behavior, stable identities, idempotency, required ordering,
durable evidence, no automatic in-doubt replay, and zero unauthorized output.

## OPEN Values And Decisions

Human approval is required for:

- OD-027 incident roles, coverage, command/handoff/escalation paths, resilient communications,
  exercise cadence, evidence freshness, and runbook authorization;
- outbox publisher claim/lease, timeout, retry/backoff, acknowledgement, replay authorization,
  poison-event, and retention policy;
- Redis topology, persistence, stream/group layout, capacity, lag/backlog thresholds, and
  recovery procedure;
- consumer identities, supported versions, idempotency stores, side-effect atomicity, poison
  handling, and operational retention;
- non-event WebSocket schema authority, compatibility, framing, authentication, signing, replay,
  takeover, and key-rotation profile;
- stage-host local journal storage, atomicity, flush/fsync, encryption, capacity, compaction,
  corruption recovery, power-loss model, and retention;
- heartbeat, reconnect, retransmission, clock sampling/freshness/uncertainty, watchdog, and
  authorization-horizon values;
- domain-event complete contract identity, aggregate-version/event-index publication,
  transition-manifest/expected-delivery high-water, restrictive protection overlay, and
  stale-projection reconciliation;
  separate non-event sequence allocation/gap recovery, acknowledgement retention, and queue
  interruption policy;
- privacy classifications, local/cloud evidence retention, deletion, backup/tombstone, incident
  hold, legal hold, and provider-copy handling;
- exact target-specific commands, endpoints, owners, alert routes, severity labels, SLOs, and
  production authorization evidence.

No fixture, deployment, database, Redis, operating-system, library, or vendor default may become a
production value without protected human approval.
