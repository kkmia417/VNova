# Silence And Audio Underrun

Status: Drafted / Proposed operational runbook; human review required; no implementation
or live use authorized

Governing decisions and references:

- [ADR-011](../adr/0011-stage-host-wire-protocol-and-clock-synchronization.md):
  Proposed queue, playout evidence, and clock protocol
- [ADR-015](../adr/0015-layered-emergency-stop.md): Proposed emergency
  containment and resume
- [ADR-016](../adr/0016-stage-host-and-cloud-local-topology.md): Accepted local
  playback and OBS audio-level ownership
- [ADR-018](../adr/0018-latency-budget-and-streaming-strategy.md): Proposed
  latency, timeout, freshness, and underrun telemetry
- [ADR-019](../adr/0019-authentication-authorization-and-operator-roles.md):
  Proposed operator authorization
- [ADR-020](../adr/0020-mode-transition-and-degradation-matrix.md): Proposed
  fail-safe degradation
- [ADR-021](../adr/0021-broadcast-surface-inventory-and-overlay-policy.md):
  Proposed surface isolation, clear, and fallback rules
- [Stage-host model](../architecture/stage-host.md)
- [Rehearsal mode](../architecture/rehearsal-mode.md)
- [Open decision register](../architecture/open-decisions.md)
- [Operational readiness review](../governance/operational-readiness-review.md)

This document proposes decision and evidence requirements. It does not select audio
thresholds, device/vendor controls, OBS source names, test signals, buffer sizes, retry
behavior, fallback assets, commands, or endpoints. It authorizes neither a live adapter
operation nor an automatic policy. All numeric and environment-specific choices require
human review and target-rig measurement.

## Scope And Trigger

Use this runbook when:

- OBS audio level remains below the accepted live-silence threshold during a window in which
  audio is expected;
- stage-host emits `SilenceThresholdExceeded`, records an audio-buffer underrun, or reports
  audio health as unknown;
- a `SpeechTask` is accepted or marked starting/playing but expected first audio or
  completion is not observed;
- audio begins and then gaps, truncates, repeats, distorts, or becomes
  `playing_or_in_doubt`;
- the virtual or live audio sink, playback coordinator, OBS adapter, source routing, or
  monitor disagrees about playout; or
- the operator cannot distinguish intentional silence from a failed or unsafe audio path.

Intentional silence with no audio work expected is not automatically an incident. The
monitor must correlate silence with session lifecycle, segment intent, local queue/playback
state, and the expected-audio window. Exact correlation and threshold policy remains OPEN.

Transfer to the [rig disconnect and watchdog runbook](rig-disconnect-and-watchdog.md) if
link, heartbeat, binding, epoch, or watchdog state is unsafe. Transfer immediately to the
[emergency stop and resume runbook](emergency-stop-and-resume.md) if output may be harmful,
uncontrolled, repeated, substituted, or otherwise unbounded, or if any emergency assertion
is made.

## Safety Objective

- Prevent partial, stale, repeated, corrupted, or unverified audio from reaching the
  audience.
- Preserve `stage-host` as the sole `SpeechTask` consumer and local playback authority.
- Diagnose from identifier-only task, artifact, queue, adapter, level, and timing evidence;
  never send raw generated text through a diagnostic path.
- Missing or contradictory approval, integrity, local-output, or monitoring evidence fails
  closed to no new voice output.
- Treat `playing_or_in_doubt` as non-replayable.
- Do not convert a TTS, artifact, buffer, device, OBS, or monitoring failure into an
  unmoderated fallback.
- A fallback is either a separately approved identifier-only canned asset or a reviewed
  neutral scene. Provider retry and fallback still use the same safety, rights, surface,
  expiry, and artifact-integrity gates.
- Isolate only the affected audio surface when the failure domain is proven. Unknown or
  broader trust failure moves the effective ceiling toward Mode 0 and may require emergency
  stop.
- Recovery never extends an approval deadline, restores an in-doubt task, or automatically
  raises mode.

## Roles And Authority

Concrete roles, capabilities, and assignments remain OPEN.

| Responsibility        | Required duty                                                                                                                                                  |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| First observer        | Declare the observed silence/underrun and identify whether audio was expected; do not fill silence with unapproved speech.                                     |
| Broadcast operator    | Observe audience output, disable or clear the affected surface through the approved control, and assert emergency stop immediately if output is unsafe.        |
| Incident commander    | Bound the affected session/rig/surface, choose voice isolation versus broader containment, and prevent speculative replay or premature recovery.               |
| Stage-host owner      | Diagnose local queue, artifact, sink, buffer, OBS adapter/source, output level, clock, and terminal outcome without bypassing the playback coordinator.        |
| Session-runtime owner | Stop or hold new audio dispatch as required, correlate cloud attempts, maintain expiry/epoch restrictions, and apply the accepted degradation policy.          |
| Safety/media owner    | Verify the identifier-only approval, rights, surface, sanitization, synthesis, immutable artifact, and fallback chains without exposing restricted content.    |
| Evidence recorder     | Preserve task/artifact/adapter/timing/level evidence and incident decisions without copying linguistic or viewer-memory content.                               |
| Recovery authority    | A scoped human who supplies a reason and explicitly confirms audio recovery; separate e-stop resume or mode-increase confirmation remains mandatory when used. |

No audio device, provider, watchdog, or monitor may authorize resume or mode increase.

## Immediate Actions

1. Establish whether audio is currently expected using committed segment/turn/task state and
   local queue/playback evidence. Do not infer intent from silence alone.
2. If unexpected, harmful, repeated, substituted, or uncontrolled audio is present, assert
   emergency stop immediately without confirmation and transfer to the emergency-stop
   runbook.
3. For confirmed unexplained silence or underrun during expected playout:
   - stop admitting new audio work to the affected local path;
   - keep safety-control, emergency-stop, heartbeat, and current-state reporting available;
   - mark the affected playout outcome interrupted, failed, or in doubt according to
     observed evidence rather than claiming completion;
   - prevent automatic retry or replay of the current task; and
   - move the voice surface to the reviewed mute/neutral state.
4. If the failure is proven isolated to voice, other independently safe surfaces may
   continue only under their own current surface authorizations. Do not infer caption,
   overlay, scene, alert, or avatar safety from voice isolation.
5. If adapter, task, artifact, epoch, signature, clock, monitoring, or failure scope is
   unknown, apply the accepted Mode 0 ceiling and stop new dispatch. Unknown fault classes
   do not default to continued output.
6. Do not submit generated filler, manual raw text, a provider console test, an arbitrary
   sound, or a previous artifact. A separately approved canned asset may be used only when
   its current identifier-only authorization, rights, surface, expiry, and local integrity
   checks pass. Otherwise use silence or the reviewed neutral scene.
7. Record the first observation, expected-audio evidence, affected identifiers, actual local
   effect, and containment decision.

Exact criteria for automatically isolating voice, terminalizing a task, cutting active
audio, selecting a neutral scene, or escalating to e-stop remain protected policy decisions.
Until accepted, a human incident commander chooses the safe direction; no implementation may
invent a default.

## Classification

| Observed state                                                   | Provisional interpretation                           | Required containment                                                                                            |
| ---------------------------------------------------------------- | ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| No task expected; level is quiet                                 | Intentional or scheduled silence                     | Continue monitoring; record no incident unless another health signal is unsafe                                  |
| Task queued but not started; deadline remains valid              | Queue/backpressure or admission delay                | Hold new audio admission; inspect remaining deadline; never reset TTL                                           |
| Task marked starting/playing but no OBS level                    | Artifact, sink, route, adapter, or observation fault | Mute/disable affected voice path; mark in doubt; no automatic replay                                            |
| Audio begins then underruns, gaps, or truncates                  | Buffer/device/scheduler or artifact-delivery failure | Stop affected playout safely; no continuation from guessed offset; preserve local outcome                       |
| Audio repeats or an in-doubt task starts again                   | Replay/idempotency or crash-consistency incident     | Emergency stop; quarantine rig/task evidence; escalate safety/security                                          |
| Local sink reports audio but OBS reports silence                 | Routing/source/mixer or OBS-observation fault        | Disable voice surface; verify actual audience path through approved observation                                 |
| OBS reports level but no expected task is active                 | Unauthorized/substituted source or stale state       | Emergency stop; inventory OBS source and adapter provenance                                                     |
| Monitor health itself is unknown or contradictory                | Detection blind spot                                 | Treat audio state as unknown; isolate voice or stop according to accepted scope; do not declare recovery        |
| Link/heartbeat/epoch/watchdog is also unsafe                     | Rig-disconnect incident                              | Apply disconnect runbook; emergency stop if local containment is not proven                                     |
| Approval, rights, surface authorization, digest, or expiry fails | Authorization/integrity incident                     | Reject/stop the task; no fallback from rejected content; evaluate emergency stop and security/rights escalation |

## Diagnosis

Keep the affected voice path contained while collecting evidence.

### Expected-Audio And Task Lineage

Verify:

- session, segment, turn, approval, rights authorization, surface authorization, synthesis
  attempt, artifact, media authorization, task, rig, epoch, and queue identities;
- candidate/approval/task `not_after` and immediate pre-playback validity;
- the exact immutable artifact digest and local verification outcome;
- task signature, session/rig binding, replay identity, ordered sequence, and
  acknowledgement phase; and
- whether cancellation, mode decrease, emergency state, rights invalidation, or surface
  disable made the task ineligible.

Do not inspect or copy raw generated text to diagnose the path. Use identifiers, digests,
versions, decision outcomes, and restricted tools approved for accountable owners.

### Local Playback Chain

Determine where observed behavior diverges:

```text
durably accepted task
  -> verified local artifact
  -> playing_or_in_doubt transition
  -> playback coordinator
  -> audio buffer and sink
  -> OBS configured audio source
  -> observed OBS output level
  -> terminal local outcome
```

For each boundary, record start, success/failure/in-doubt outcome, monotonic duration,
timeout, and correlation identity. Inspect:

- queue order, backlog, active entry, replay marker, and restart history;
- artifact presence, digest, supported media format, and local read outcome;
- buffer fill/underrun state and any resource starvation evidence;
- selected local sink and its health;
- OBS adapter state, registered source identity, mute/routing state, and observed level;
- whether an unknown, external, or remotely mutable OBS source exists;
- clock-offset/uncertainty and deadline mapping;
- stage-host process/boot identity and adapter version; and
- local journal capacity and the event sequence around the failure.

Do not restart, reroute, unmute, alter buffer values, or switch devices on the live path
unless that action is part of an accepted, reversible recovery profile.

### Cloud And Provider Chain

Verify:

- TTS attempt timeout, cancellation, retry/fallback, and immutable artifact-commit outcome;
- that every provider attempt used the private gateway and the same approval, rights, and
  surface gates;
- object/media transfer timeout and digest result;
- dispatch and each application acknowledgement, distinguishing receipt, acceptance,
  playback start, and terminal playback;
- requested/effective mode and any automatic degradation;
- queue wait, end-to-end deadline, and whether late completion was correctly rejected; and
- whether dashboards or state subscriptions were stale.

A TTS success or transport acknowledgement is not evidence that valid audio reached OBS.

### Monitoring Integrity

Confirm that the monitored OBS source is the registered live source, the measurement is
current, and silence detection has not lost its own input. Compare independent accepted
observations without treating one metric as absolute truth. A broken monitor does not
authorize continued blind playback.

## Recovery

1. Keep voice disabled or muted and keep new audio dispatch held.
2. Correct the identified fault only through the approved adapter, configuration, release,
   or infrastructure change process. Do not improvise production commands or unreviewed
   defaults.
3. Ensure the failed or in-doubt task is terminal and cannot replay. Flush or invalidate
   related queued work when required by the accepted interruption policy.
4. Reconcile stage-host boot identity, session/epoch, queue/replay state, artifact state,
   clock mapping, and cloud acknowledgements.
5. Prove the registered OBS audio source, sink, adapter, level observation, and local journal
   are in known state.
6. Validate the full local audio path with the separately approved non-linguistic or
   pre-approved identifier-only test artifact, routed through a non-audience rehearsal or
   protected preflight path. The test asset, routing, level, and success criteria remain
   OPEN. Never use raw generated text as a test.
7. Verify the safety, rights, surface, approved-media, signature, expiry, and artifact
   controls are current for any later production task.
8. Verify the silence and underrun monitors can distinguish expected silence from expected
   audio and are reporting current data.
9. A scoped human supplies a reason and explicitly confirms audio-path recovery. This does
   not resume an emergency latch or increase mode.
10. Admit a newly authorized, unexpired task under the current epoch and observe the entire
    path through its terminal local outcome during the accepted validation interval.
11. Remove only the degradation cause proven clear. Do not raise effective mode
    automatically.

If emergency stop was engaged, use its separate confirmation, reason, reconciliation, and
new-epoch resume workflow before step 10. If watchdog state was engaged, complete the
disconnect recovery criteria first.

## Exit Criteria

### Safely Isolated Voice

The incident may be handed off while voice remains unavailable only when:

- the voice source is muted/disabled or the accepted neutral audience state is observed;
- no affected, old, expired, or in-doubt task can start;
- other continuing surfaces have independent current authorization and are not affected by
  the fault;
- cloud dispatch to the failed path is held;
- the effective mode/fault state reflects the unresolved risk;
- owners, evidence gaps, and the next review point are recorded; and
- no fallback speech or media bypass is active.

### Controlled Audio Recovery

All of the following are required:

- the failure domain and corrective action are identified and reviewed;
- queue, replay, artifact, epoch, clock, sink, adapter, OBS source, output-level, and monitor
  state are known and consistent;
- the affected task is terminal and no in-doubt work is replayable;
- non-audience preflight proves the approved audio chain and monitoring;
- a scoped human supplied a reason and explicitly confirmed recovery;
- emergency-stop and watchdog recovery completed separately when applicable;
- any production validation task is newly authorized, unexpired, integrity-verified, and
  completes with the expected local evidence;
- the accepted no-underrun, expected-level, and observation windows complete; and
- mode did not rise automatically.

A cleared alarm, reset counter, TTS success, audible local monitor, or single green metric
does not by itself prove controlled recovery.

## Evidence And Audit

Record:

- incident, session, rig, boot, epoch, segment, turn, approval, rights, surface, synthesis,
  artifact, media authorization, task, queue, adapter, source, and trace identifiers;
- policy, provider profile, voice profile, renderer, adapter, and monitor configuration
  versions;
- expected-audio window provenance and actual OBS level/underrun observations;
- raw local time, monotonic durations, cloud time, and clock-correction evidence;
- task acceptance, artifact verification, `playing_or_in_doubt`, adapter start, first-audio,
  interruption, and terminal outcomes;
- mute/disable, neutral-scene, dispatch hold, degradation, emergency, and fallback decisions;
- timeout, retry/fallback, late completion, and rejected replay evidence;
- correction/preflight reference, human recovery principal, reason, confirmation, and
  post-recovery observation; and
- evidence gaps, escalations, and follow-up owners.

Ordinary evidence contains identifiers, versions, classified outcomes, levels, timings, and
digests. It does not duplicate raw prompts, generated candidate text, viewer-memory content,
secrets, tokens, or unnecessary audio/content. Recordings and snapshots are restricted
evidence governed by the human-approved retention and incident-hold policy.

## Escalation

Escalate immediately when:

- unexpected or unauthorized audio reaches or may reach the audience;
- audio repeats, a task replays, or `playing_or_in_doubt` work restarts;
- the local mute/disable effect or actual OBS source cannot be proven;
- an unregistered, external, or remotely mutable source may be producing audio;
- artifact digest, signature, approval, rights, surface authorization, expiry, or epoch
  validation fails;
- the monitor is blind and independent observation cannot bound the risk;
- underruns recur beyond the human-approved tolerance or affect multiple surfaces/rigs;
- the fault requires an unreviewed adapter, device, OBS, provider, policy, or configuration
  change; or
- required evidence is missing, contradictory, corrupt, or cannot become durable.

Security, rights, privacy, platform-policy, and audience-impact concerns also transfer to
their separately approved processes. Exact severity, contacts, paging, vendor escalation,
and public communication remain OPEN.

## Rehearsal Acceptance

Before production acceptance, deterministic rehearsal must cover:

- intentional silence with no false incident and expected speech with threshold detection;
- missing artifact, digest mismatch, unsupported media, object-transfer timeout, and late
  artifact completion;
- queue delay, expiry immediately before playback, and no deadline extension on retry;
- sink failure, empty/partial buffer, underrun, resource starvation, wrong route, muted OBS
  source, and monitor failure;
- local sink/OBS level disagreement and unknown external-source audio;
- audio gap, truncation, corruption, repetition, and `playing_or_in_doubt` restart;
- stage-host process/power loss at acceptance, artifact fetch, adapter start, and terminal
  commit;
- TTS timeout and provider fallback through the same full safety and authorization chain;
- link loss, watchdog trip, mode decrease, emergency stop, and their races with underrun;
- voice-only isolation while independently authorized non-audio surfaces continue;
- broad unknown failure causing Mode 0 or emergency containment;
- separately approved fallback success and fallback failure with no raw/unapproved
  substitution;
- confirmed recovery with reason, no old-task replay, and no automatic mode increase; and
- a reconstructable timeline from synthesis through observed local output without
  restricted-content leakage.

Fake and live adapters must pass the same behavioral contract suite. The target rig must
separately prove approved level thresholds, expected-audio windows, underrun detection,
mute/disable, preflight, and stable-recovery SLOs.

## OPEN Decisions Requiring Human Review

- OD-027: incident classes and severity, accountable roster and coverage, command/handoff
  authority, resilient escalation and communications, exercise cadence, evidence
  freshness, runbook ownership, and deployment-specific authorization.
- Silence level, duration, expected-audio, first-audio, underrun, recurrence, observation,
  and escalation thresholds by environment and content class.
- Audio buffer, format, device, sink, OBS source, routing, monitoring, and resource-health
  profiles.
- Exact voice-isolation versus Mode 0 versus emergency-stop decision matrix.
- Interruption, terminalization, queue flush, preemption, crossfade, retry, and
  resume-from-offset policy. In-doubt work may never replay automatically.
- Approved neutral scene, canned fallback assets, diagnostic test artifact, preflight
  routing, and success criteria.
- Recovery authority, confirmation/challenge semantics, required reason, separation of
  duties, and post-recovery mode.
- Whether and how captions or avatar timing continue when voice is isolated.
- Monitor independence, OBS-level collection, metric retention, recordings/snapshots,
  privacy classification, and incident-hold policy.
- Provider, object storage, network, audio device, OBS, venue, safety, rights, and
  communications escalation ownership.
- Final event schemas, adapter controls, API/transport paths, and executable commands. This
  runbook intentionally defines none.
