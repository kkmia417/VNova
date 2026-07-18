# Rig Disconnect And Watchdog

Status: Drafted / Proposed operational runbook; human review required; no implementation
or live use authorized

Governing decisions and references:

- [ADR-011](../adr/0011-stage-host-wire-protocol-and-clock-synchronization.md):
  Proposed link, queue, reconnect, and clock protocol
- [ADR-015](../adr/0015-layered-emergency-stop.md): Proposed stop and resume
  precedence
- [ADR-016](../adr/0016-stage-host-and-cloud-local-topology.md): Accepted local
  stage-host and watchdog authority
- [ADR-018](../adr/0018-latency-budget-and-streaming-strategy.md): Proposed
  timeout and freshness behavior
- [ADR-019](../adr/0019-authentication-authorization-and-operator-roles.md):
  Proposed operator authority and presence
- [ADR-020](../adr/0020-mode-transition-and-degradation-matrix.md): Proposed
  disconnect degradation
- [ADR-021](../adr/0021-broadcast-surface-inventory-and-overlay-policy.md):
  Proposed local surface behavior
- [ADR-025](../adr/0025-session-actor-ownership-command-ingress-and-fencing.md):
  Proposed cloud actor, signing/dispatch fence, and takeover reconciliation
- [Stage-host model](../architecture/stage-host.md)
- [Rehearsal mode](../architecture/rehearsal-mode.md)
- [Open decision register](../architecture/open-decisions.md)
- [Operational readiness review](../governance/operational-readiness-review.md)

This is a decision-ready operating specification, not an executable procedure. It chooses no
heartbeat interval, watchdog threshold, reconnect policy, endpoint, command, credential,
scene, alert route, or stage-host technology. Those values remain OPEN and protected. This
runbook may be used only as rehearsal and human-review input until accepted.

## Scope And Trigger

Use this runbook when any of the following is observed for a live or live-capable
`stage-host`:

- the authenticated cloud link closes, fails, or cannot complete its explicit timeout;
- expected heartbeat evidence is missing, stale, contradictory, or bound to the wrong rig,
  session, boot identity, or epoch;
- authentication, protocol negotiation, clock synchronization, or session binding fails;
- a connected rig reports its watchdog latch, unsafe adapter state, invalid local journal,
  or unprovable clock mapping;
- the runtime and rig disagree about queue progress, replay state, stop state, or the
  authoritative epoch;
- the runtime receives `RigDisconnected` or equivalent committed state; or
- the operator cannot prove that the displayed rig state is current.

Do not use reconnection as proof that the incident is resolved. Transfer immediately to the
[emergency stop and resume runbook](emergency-stop-and-resume.md) if output continues
unsafely, the local state cannot be bounded, or any stop assertion is made. Use the
[silence and underrun runbook](silence-and-audio-underrun.md) when the link is healthy but
the audio path alone is failing.

## Safety Objective

- `stage-host` retains local safety authority while the cloud is unreachable.
- The local monotonic watchdog auto-mutes and selects the reviewed safe fallback scene after
  the approved threshold; it does not depend on cloud, Redis, console, database, or
  wall-clock health.
- The runtime stops new dispatch and reduces the effective-mode ceiling to Mode 0 when the
  rig is disconnected, unbound, on the wrong epoch, or watchdog-unsafe.
- Missing or contradictory link, identity, clock, epoch, queue, or local-effect evidence
  fails closed to no new playback and the restrictive state.
- No unknown, expired, old-epoch, duplicated, replayed, reordered, or in-doubt work begins
  after a partition.
- Redis is never exposed to the rig and never becomes recovery authority.
- Recovery reconciles PostgreSQL authority with crash-consistent local evidence before any
  new playback.
- A returned network link never raises mode, clears an emergency latch, releases a watchdog
  latch, or revives queued work automatically.

## Roles And Authority

Concrete names and assignments remain OPEN.

| Responsibility         | Required duty                                                                                                                                                          |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| First observer         | Declare the rig state unsafe when evidence is stale; do not assume a dashboard or reconnect attempt proves local safety.                                               |
| Local rig operator     | Observe actual local audio/scene state, preserve the watchdog latch, and assert local hard stop immediately if the watchdog does not contain the risk.                 |
| Incident commander     | Establish the affected rig/session/surface scope, choose safe-disconnected handoff versus recovery, and prevent uncoordinated playback enablement.                     |
| Stage-host owner       | Diagnose the link supervisor, verifier, queue, adapters, watchdog, clock, and local journal without bypassing their safety boundaries.                                 |
| Session-runtime owner  | Stop dispatch, apply restrictive mode/epoch state, prove the exact active recovery/ownership composite fence, and reconcile through the closed activation barrier.     |
| Network/security owner | Diagnose transport, authentication, enrollment, key, version, and replay incidents without weakening verification or extending credentials.                            |
| Broadcast operator     | Confirm the audience sees the reviewed safe local state and coordinate separately approved non-VNova programming when necessary.                                       |
| Evidence recorder      | Correlate rig, connection, heartbeat, queue, epoch, watchdog, adapter, and reconnect evidence without copying generated or restricted content.                         |
| Recovery authority     | A human with scoped authority who explicitly confirms the accepted recovery workflow and supplies a reason; separate mode-increase confirmation may still be required. |

The watchdog and machine principals may move the system only toward a safer state. They
cannot resume output or increase mode.

## Immediate Actions

### Local Stage-Host Actions

The local control path acts independently:

1. Use a local monotonic clock to evaluate cloud-link liveness against the human-approved
   threshold.
2. Reject new remote work once connection/session authority is no longer current.
3. When the threshold is exceeded, latch `WatchdogSafe`, cut or mute the configured OBS
   audio source, and select the reviewed safe fallback scene.
4. Permit no new playback while the watchdog latch is active.
5. Preserve queue, replay, session-epoch, adapter, clock, and journal evidence. Do not
   replay `playing_or_in_doubt` work.
6. Buffer sequenced local operational events for authenticated, idempotent upload after
   reconnect.
7. If the watchdog does not produce the accepted local effect, or any audience output is
   unsafe or uncertain, assert the local hard stop immediately without confirmation and
   transfer to the emergency-stop runbook.

The final policy for valid work already playing or queued before the watchdog threshold is
OPEN. Until it is accepted and measured, no production procedure may assume that such work
continues safely. Expiry, epoch, e-stop, rights, or approval failure always rejects it.

### Cloud Runtime Actions

The cloud side does not wait for the rig:

1. Mark the rig disconnected, unbound, or unsafe using authoritative session state.
2. Stop new dispatch to that rig.
3. Apply the ADR-020 restrictive ceiling: effective mode is at most Mode 0 for the affected
   session while no safe rig is bound.
4. Advance the authorization epoch for the effective downward transition and make old-epoch
   queued work ineligible.
5. Stop admission of work that depends on local presentation. Record late link, queue, or
   playback acknowledgements as evidence only.
6. Alert the operator through the accepted independent operational path.
7. Continue bounded reconnect attempts with explicit timeouts. Do not loosen
   authentication, version, signature, expiry, or session checks to recover availability.

If authoritative state cannot be persisted, hold the strongest available process-local
restrictive state and retry durability. Do not preserve higher autonomy because PostgreSQL
or outbox recording failed.

### Operator Actions

- Identify the affected environment, rig, session, current audience output, and all enabled
  broadcast surfaces.
- Verify the actual local mute/fallback effect through approved local observation when
  possible; a cloud status indicator is not sufficient evidence.
- Do not send test speech, raw text, manual adapter commands, or provider output to determine
  whether the path works.
- Do not expose Redis, bypass the authenticated WebSocket, extend an expired authorization,
  or re-enqueue a prior task.
- If output cannot remain safely contained, assert emergency stop immediately; do not wait
  for the watchdog threshold or diagnosis.

## Classification

Classify the incident by observed evidence. Multiple classes may apply.

| Class                            | Evidence to seek                                                               | Safe interpretation                                                                                                 |
| -------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| Transport interruption           | Link close/timeout, network reachability, reconnect attempts                   | No current remote authority; local watchdog owns containment                                                        |
| Authentication/session failure   | Rig/runtime identity, credential/key status, session binding, protocol version | Establish no active binding; accept no task                                                                         |
| Heartbeat or state-channel fault | Link appears open but heartbeat/state evidence is stale or contradictory       | Treat as disconnected/unsafe; an open socket is not proof of liveness                                               |
| Clock uncertainty                | Stale samples, excessive uncertainty, wall-clock step, sleep/resume, reboot    | Reject deadline-sensitive work until a new conservative monotonic mapping is valid                                  |
| Epoch or queue divergence        | Session epoch, sequence, accepted/terminal identities, replay markers disagree | Pause the ordered lane; do not guess, skip, or replay                                                               |
| Watchdog or adapter failure      | Latch asserted but audio/scene effect absent, unknown, or contradictory        | Assert emergency stop and use only the separately approved out-of-band rig procedure                                |
| Local journal failure            | Capacity exhaustion, corruption, truncation, rollback, missing sequence range  | Block new autonomous playback; preserve the gap and reconcile rather than fabricating evidence                      |
| Security/integrity incident      | Wrong identity, signature/replay failure, conflicting task digest, key concern | Quarantine the binding and work; emergency-stop if audience risk exists; require security clearance before recovery |
| Cloud state failure              | Actor ownership, PostgreSQL, outbox, or epoch cannot be proved                 | Maintain Mode 0/process-local restriction; reconnect cannot authorize output                                        |

## Diagnosis

Diagnosis must not clear `WatchdogSafe` or re-enable dispatch.

### Link And Identity

Inspect:

- runtime and rig identities, environment, boot identity, connection identity, and expected
  session binding;
- negotiated protocol/schema versions and capability compatibility;
- authentication and authorization outcome, credential/key identifiers, and revocation
  state;
- connection-open/close evidence, explicit timeout outcomes, reconnect history, and
  duplicate bindings; and
- whether an old connection remained active after a takeover or epoch change.

Do not accept a silent protocol downgrade, an unknown field, a broadened rig scope, or a
second authoritative rig binding.

### Heartbeat, Clock, And Local Health

Inspect the last trustworthy heartbeat and local evidence for:

- session/epoch and emergency/watchdog latches;
- queue watermark, active task, accepted and terminal outcomes;
- OBS/VTube Studio adapter state, actual audio output level, and fallback scene;
- local monotonic watchdog observations;
- wall-clock, offset, uncertainty, sample freshness, sleep/reboot/clock-step evidence; and
- offline-journal range, durability, capacity, and acknowledgement cursor.

Corrected timestamps never replace raw local timestamps. Monotonic values from different
hosts are not directly compared.

### Cloud State

Inspect:

- authoritative protected recovery generation, actor ownership, and persisted lifecycle;
- exact composite actor fence/phase/lease, ownership-row transition, recovery cut/invalidation
  revisions, pending submission-generation commands, four-record effects, canonical timer/current
  claims, lost-tail disposition, and whether the actor is recovery-only;
- requested/effective mode, degradation cause, and upward-recovery hold;
- current and superseded authorization epochs;
- priority restrictive-control intent/attempt/exact-rig acknowledgement and sealed boot/binding/
  epoch/journal cursor;
- last dispatched task and every acknowledgement phase;
- in-flight approved-media and surface work that depended on the rig;
- PostgreSQL/outbox/audit health; and
- operator-visible state freshness and any misleading stale client cache.

WebSocket frames, Redis retention, and transport acknowledgements are not evidence that work
was accepted or played.

## Recovery And Reconciliation

Fault clearance begins reconciliation; it does not restore output.

1. Keep cloud dispatch disabled, stage host in a sealed restrictive recovery hold, and the local
   watchdog latch active.
2. Re-establish mutually authenticated transport and negotiate a supported protocol without
   downgrade.
3. Establish a reconciliation-only binding for the intended rig, session, boot identity, and
   current restrictive epoch while the sealed hold remains active. Resolve duplicate or
   superseded bindings before proceeding; this is not playback activation.
4. Restore clock synchronization and prove current authorization windows can be mapped
   conservatively to local monotonic deadlines.
5. Reconcile emergency state first. If either side reports an emergency assertion or cannot
   prove it clear, transfer to the emergency-stop runbook.
6. Exchange accepted/terminal task identities, sequence watermarks, queue summary, replay
   state, local boot identity, and journal cursor.
7. Apply reconciliation precedence: emergency assertion, superseded epoch, expiry or
   cancellation, current verified authorization, then ordered queue progress.
8. Reject or quarantine every flushed, expired, cancelled, unknown-epoch, digest-conflicting,
   replayed, or `playing_or_in_doubt` item. Never rewrite it locally.
9. When cloud actor takeover followed any possibly sent task/control/playout operation, advance
   the session authorization epoch and reconcile the exact local queue/journal before any new
   dispatch.
10. Upload offline evidence in bounded, explicitly timed, idempotent batches. Preserve and
    escalate missing or corrupt ranges.
11. Prove OBS, VTube Studio, audio output, fallback scene, local queue, watchdog, and
    operator-visible rig status are known and mutually consistent.
12. Persist the exact sealed stage-host boot/binding/epoch/journal cursor and restrictive-hold
    receipt in the cloud recovery evidence. Any later local observation, binding change, queue/
    journal advance, or restrictive fact invalidates that evidence.
13. If cloud ownership changed or is `recovering`, cross ADR-025's source-serialized activation
    barrier under the exact composite actor fence. If ownership did not change, revalidate the
    exact active composite fence, recovery-invalidation revision, restrictions, and sealed
    receipt before continuing.
14. Keep the session's upward-recovery hold. Returning health removes a fault cause but does
    not raise mode.
15. A scoped human explicitly confirms the accepted rig-recovery workflow and supplies a
    reason. The exact recovery challenge and whether it reuses emergency-resume semantics
    remain OPEN.
16. Perform the separate authenticated binding-activation step for the exact accepted session
    epoch and sealed receipt. Stage host remains sealed and accepts no audience task until its
    durable activation acknowledgement is reconciled.
17. Admit only new or freshly authorized work under the current reconciled epoch after every
    preceding gate remains current.

If an emergency latch was ever engaged, the human confirmation and binding activation additionally
require the full reason, new-epoch, and resume gates of the emergency-stop runbook. A
watchdog-only recovery cannot clear an emergency assertion.

## Exit Criteria

### Safe Disconnected State

The incident may be handed off without reconnecting only when:

- local audio is muted and the reviewed fallback scene or accepted out-of-band safe state
  is observed;
- `WatchdogSafe` or an emergency latch remains active;
- cloud dispatch is stopped and effective mode is no higher than Mode 0;
- queued or stale work cannot start automatically;
- the affected rig/session/surface scope, evidence gaps, and owners are recorded; and
- the next human review point is assigned.

### Controlled Recovery

All of the following are required:

- authenticated protocol and intended rig/session binding are current;
- no duplicate/superseded connection or unresolved security concern exists;
- cloud and rig agree on the restrictive state, current epoch, queue outcomes, and journal
  cursor;
- the exact sealed restrictive-hold receipt is durably bound to the current recovery evidence;
- any required cloud `recovering -> active` barrier completed under the current composite fence,
  or unchanged active ownership and recovery-invalidation inputs were freshly revalidated;
- the separate authenticated binding activation for that exact epoch/receipt is durably
  acknowledged, with no audience task accepted while the rig was sealed;
- clock offset/uncertainty, heartbeat, adapters, audio output, fallback scene, queue, and
  journal satisfy the accepted profile;
- no old, in-doubt, expired, cancelled, or unknown work is eligible;
- a scoped human supplied a reason and explicitly confirmed recovery;
- emergency-stop resume, when applicable, completed separately;
- effective mode did not rise automatically; and
- the human-approved stable-link and observation periods complete with no new disconnect,
  watchdog trip, audit gap, or stale-output attempt.

Reconnection, a fresh heartbeat, or an apparently healthy OBS display alone does not satisfy
controlled recovery.

## Evidence And Audit

Record:

- incident, rig, runtime, session, boot, connection, epoch, protocol, heartbeat, task,
  artifact, queue-sequence, journal-sequence, command, trace, and surface identifiers;
- raw local and cloud timestamps plus clock-offset/uncertainty evidence;
- link close, timeout, reconnect, negotiation, authentication, and binding outcomes;
- requested/effective mode and degradation causes;
- watchdog threshold profile version and trip observation, without claiming an unapproved
  numeric SLO;
- actual audio mute/level, fallback scene, adapter, queue, replay, and journal outcomes;
- rejected tasks and reason codes without generated text;
- offline upload range, deduplication acknowledgement, and unresolved evidence gaps;
- human recovery principal, reason, confirmation, preconditions, resulting epoch/mode, and
  observation outcome; and
- escalations and follow-up owners.

Do not store bearer tokens, keys, raw task text, prompts, candidate content, viewer-memory
content, or restricted rights evidence in ordinary logs. The stage-host journal is bounded
operational evidence, not a second system of record.

## Escalation

Escalate immediately when:

- watchdog mute or fallback does not occur or cannot be observed;
- any audience output remains unsafe or unexplained;
- the direct local stop path is required;
- two peers claim authoritative ownership or epochs/bindings cannot reconcile;
- a signature, digest, replay, credential, key, or protocol-downgrade incident is suspected;
- `playing_or_in_doubt` work replays or old work appears after reconnect;
- clock validity, queue durability, or journal integrity cannot be restored;
- cloud restriction cannot be held or persisted;
- evidence gaps prevent a safe recovery decision; or
- repeated disconnects exceed the human-approved operational tolerance.

Exact severity, on-call routing, network/vendor escalation, rig replacement, platform
communication, and venue fallback procedures remain OPEN.

## Rehearsal Acceptance

Before production acceptance, rehearsal must deterministically cover:

- link loss while idle, queued, fetching, starting, playing, stopping, and acknowledging;
- open socket with stale heartbeat and contradictory heartbeat/session evidence;
- watchdog mute and fallback with cloud, Redis, database, identity provider, and console
  unavailable;
- failure of the watchdog, OBS adapter, audio source, and fallback scene, proving transfer
  to local emergency stop;
- duplicate connections, takeover, wrong rig, wrong session, old epoch, protocol downgrade,
  authentication failure, and key revocation;
- task duplicate, loss, delay, reorder, sequence gap, conflicting digest, and replay;
- clock offset/drift/uncertainty, asymmetric delay, stale samples, wall-clock step, sleep/resume,
  and reboot;
- stage-host process/power loss at every queue transaction and adapter-start boundary;
- local journal exhaustion, corruption, truncation, duplicate upload, and missing range;
- PostgreSQL/Redis failures proving PostgreSQL authority and fail-safe cloud restriction;
- reconnect reconciliation that never revives flushed, expired, or in-doubt work;
- operator-confirmed recovery with reason and no automatic mode increase; and
- a reconstructable incident timeline with adapter outcomes and raw/corrected time evidence.

The target streaming PC must separately demonstrate the approved watchdog, mute,
fallback-scene, reconnect, clock, journal, and stable-recovery SLOs. Simulator evidence is not
live-adapter authorization.

## OPEN Decisions Requiring Human Review

- OD-027: incident classes and severity, accountable roster and coverage, command/handoff
  authority, resilient escalation and communications, exercise cadence, evidence
  freshness, runbook ownership, and deployment-specific authorization.
- Heartbeat, disconnect, watchdog, authentication, clock, reconnect, retransmission,
  stable-link, observation, and escalation thresholds.
- Whether any otherwise valid active or queued work may continue before the watchdog trip;
  nothing may override expiry, epoch, e-stop, rights, approval, or integrity checks.
- Exact watchdog action scope across voice, captions, overlays, alerts, scenes, avatar
  actions, multiple sessions, and multiple rigs.
- Fallback scene and any separately approved canned behavior; generated filler is not an
  implicit fallback.
- Rig-recovery authority, confirmation/challenge semantics, required reason, separation of
  duties, and post-recovery mode.
- Stage-host language, process model, deployment, update, rollback, and rig-replacement
  procedure.
- Transport authentication, signature, key custody, enrollment, rotation, revocation,
  replay-record lifetime, and protocol compatibility profile.
- Local queue/journal storage, atomicity, flush behavior, encryption, capacity, compaction,
  corruption recovery, and evidence retention.
- Network, identity, OBS, VTube Studio, audio, and venue escalation ownership.
- Final command/event schemas and API/transport paths. This runbook intentionally specifies
  no executable command or endpoint.
