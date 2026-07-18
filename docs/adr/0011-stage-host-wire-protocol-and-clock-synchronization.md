# ADR-011: Stage-Host Wire Protocol And Clock Synchronization

Status: Proposed

Date: 2026-07-17

Sources: `AGENTS.md`, `vnova-review-handoff.md`, ADR-002, ADR-008, ADR-010, ADR-016,
ADR-018, ADR-023, ADR-025

This ADR is non-binding while its status is `Proposed`. It selects no stage-host language,
cryptographic algorithm, credential system, network threshold, or numeric clock tolerance.

## Context

`stage-host` is a required local safety boundary and the sole consumer of `SpeechTask`.
Ordinary WebSocket delivery does not by itself provide durable acknowledgement, replay
protection, session ownership, application ordering, safe reconnect, or trustworthy
cross-host time.

The rig can disconnect, sleep, reboot, experience wall-clock adjustment, receive duplicated
frames, or reconnect after the runtime has changed session ownership. The protocol must
prevent stale, substituted, replayed, wrong-session, or expired work from reaching OBS while
preserving a local e-stop that works without cloud connectivity.

## Decision

`session-runtime` and `stage-host` communicate through one authenticated, version-negotiated
WebSocket application protocol. Redis is not exposed to the rig and is not part of the wire
contract.

Transport authentication and per-`SpeechTask` authorization are independent controls:

- the connection authenticates and authorizes a rig identity;
- the session binding authorizes one active rig for one stream-session epoch;
- every speech task carries a separately signed, session-bound, time-bounded,
  integrity-bound, replay-resistant authorization under ADR-008.

The stage host has verification authority but never receives the runtime's task-signing
authority.

### Connection And Session Binding

The handshake exchanges and validates:

- protocol versions and supported contract capabilities;
- rig identity and runtime identity;
- connection identity;
- requested and accepted `stream_session_id`;
- session epoch and current emergency-latch state;
- task-verification key identifiers and accepted rotation metadata;
- stage-host boot identity and local event cursor;
- queue/replay reconciliation summary;
- clock-synchronization capability and initial measurement evidence.

Only one rig binding is authoritative for a stream session and epoch. Takeover, reconnect,
or actor ownership transfer must be explicit, audited, and reconciled against PostgreSQL state
under ADR-025. An old connection cannot remain authorized after a new epoch or binding
supersedes it. If prior dispatch or playout is ambiguous or cannot be disproved, the successor
advances the session authorization epoch and reconciles the exact rig before becoming active.

Protocol negotiation fails closed. An endpoint does not silently downgrade to an
unsupported or semantically incompatible contract.

### Message Classes

The protocol separates:

- handshake, authentication, capability, and session-binding messages;
- runtime-to-stage commands, including identifier-only `SpeechTask` and reviewed
  rig-control commands;
- stage-to-runtime acknowledgements, queue/playback outcomes, adapter health, heartbeat,
  e-stop state, clock samples, and offline observation batches;
- resynchronization and protocol-error messages.

Every application message has a stable message identity, protocol/schema version, session
and epoch binding where applicable, correlation identity, and bounded payload. Unknown
fields and unsupported message variants are rejected according to the accepted contract
compatibility policy.

`SpeechTask` remains a closed identifier/integrity/timing contract and contains no raw text,
SSML, unrestricted object, provider payload, or media bytes. Media is retrieved separately
through the scoped authorization governed by ADR-010.

ADR-021 and ADR-022 propose additional content/rights/surface authorization bindings and a
rights-invalidation command. They are not part of the current ADR-008 allowlist. Adding them
requires those ADRs to be accepted, OD-021 to be closed, ADR-008 and the protected contracts to be
amended, and generated cross-language invalid fixtures to pass. This protocol ADR cannot infer or
accept unknown authorization fields.

Safety-control handling cannot be blocked behind ordinary media work. The local hard e-stop
uses the direct local path required by ADR-016 and does not depend on this connection. Cloud
freeze, queue flush, and resume reconciliation require ADR-015 before implementation.

### Restrictive Control And Mode Convergence

An effective-mode decrease or other session-wide restriction advances the authoritative session
authorization epoch in `session-runtime`. After protected ADR-008/020 and contract review, a
priority authenticated control message communicates the new epoch and restrictive cause to
`stage-host`.

- The control message is signed or equivalently integrity protected, session/rig bound,
  idempotent, replay resistant, and ordered independently from ordinary media.
- Stage-host atomically persists the newer restrictive epoch and evicts every not-yet-playing task
  from an older epoch before acknowledging application. A stale, duplicate, delayed, or reordered
  control message can never restore an old epoch or raise autonomy.
- An authenticated stop assertion is never rejected solely because its observed session epoch is
  older; it still converges toward the local stop latch. Epoch ordering can reject stale widening
  or lowering of a newer restriction, not stop dominance.
- Work that remains eligible is freshly authorized and dispatched under the new epoch; an old task
  is never rewritten locally.
- A Mode 2 task's `not_after` is no later than the earliest candidate/approval deadline,
  qualifying operator-presence lease, and accepted health/control-link authorization horizon.
- On partition, no new higher-autonomy work is accepted; pre-playback expiry checks and the local
  disconnect watchdog bound how long an already queued authorization can remain usable.
- Any upward/recovery epoch binding follows the deliberate ADR-015/020 reconciliation and
  confirmation path; a restrictive control message cannot be repurposed as an increase.

ADR-025 administrative revoke atomically creates this restrictive intent while clearing actor
ownership. A closed `session-runtime` restrictive-control dispatcher therefore drains it without
active actor authority through a separately reserved priority lane, bounded claim/retry/timeout,
and exact acknowledgement. It validates the protected recovery generation, latest restrictive
epoch/cause, exact rig binding, and expiry and has no `SpeechTask`, resume, or mode-increase
authority.

The accepted protocol must make task acceptance downstream-verifiably ordered against
restrictive epoch application. A cloud database check before a later send is insufficient.
Stage-host acknowledgement seals the newer restriction and old-epoch queue eviction for its exact
boot/binding/journal cursor; until then audience convergence is unknown. Immediate audience
cessation remains the ADR-015 local e-stop guarantee, not a cloud-revoke claim.

The current closed `SpeechTask` boundary requires session epoch and expiry, but the priority
mode/epoch-control message is not yet authorized. Server-side dispatch evidence also binds the
current ADR-025 recovery/ownership composite actor fence through the shared ownership-row
linearization point. After PITR/failover, the audience path must validate the protected recovery
generation or a superseding rig binding/signing authority and session epoch above a trusted
high-water. Adding any such field to the wire is neither required nor authorized here.
ADR-020/025 acceptance, OD-021/029 resolution, protected ADR-008/contract amendment, numeric
convergence decisions, and target-hardware partition tests are prerequisites.

### Delivery, Ordering, And Acknowledgement

WebSocket frames are not treated as exactly-once commands. Application delivery is
at-least-once across retry and reconnect.

- Duplicate message/task identities with identical canonical content are handled
  idempotently and return the previously recorded outcome.
- Reuse of an identity with different content is rejected as an integrity incident.
- Speech/avatar work has strict FIFO per `stream_session_id` within the current epoch.
- Safety-control messages have priority and do not wait for the media lane.
- A sequence gap pauses acceptance of later ordered work and initiates resynchronization;
  the stage host does not guess, reorder, or skip silently.
- Receipt, validation/acceptance, playback start, and terminal playback outcome are distinct
  acknowledgements.
- A transport acknowledgement is not evidence that audio played.

### Crash-Consistent Local Queue

Stage-host acknowledges application-level acceptance only after one local atomic durable
transaction records:

- canonical task/message digest and immutable task identifiers;
- session/authorization epoch, ordered-lane sequence, token/replay identity, and expiry;
- artifact ID/digest and all accepted authorization references;
- queue position/status and the replay/idempotency marker.

Before asking the audio/OBS adapter to start, stage-host durably transitions the entry from
`accepted` to `playing_or_in_doubt`. It records a terminal completed/interrupted/rejected outcome
only after observing the corresponding local effect. The durability profile must ensure these
records survive the accepted power-loss and process-crash model before their acknowledgements are
emitted.

After restart:

- `playing_or_in_doubt` is never replayed automatically, even if the adapter may not actually have
  started;
- stage-host first cuts/mutes uncertain output, restores restrictive latches and epoch state, and
  reconciles with the runtime;
- an accepted-but-not-started entry remains eligible only if every current signature, epoch,
  sequence, authorization, artifact, mode, and expiry check still passes;
- missing, corrupt, conflicting, or rolled-back queue/replay state marks the rig unsafe, blocks
  new autonomous playback, and requires reconciliation.

The local queue journal is safety evidence and bounded offline state, not a second cloud system of
record. The runtime persists authoritative command and session state in PostgreSQL. Neither
endpoint reconstructs authority from a WebSocket buffer or Redis offset. Exact local storage,
atomicity, flush/fsync, encryption, capacity, and corruption-recovery profile remains OPEN.

### Reconnect And Offline Observations

On reconnect, both sides exchange the current epoch, emergency state, accepted/terminal task
identities, queue summary, stage-host boot identity, and offline observation cursor.

Reconciliation applies this precedence:

1. engaged emergency latch or superseded session epoch;
2. expiry or explicit cancellation;
3. verified current authorization;
4. sequence and queue progress.

Previously flushed, cancelled, expired, unknown-epoch, or unverifiable work is never revived.
Conflicting state pauses the ordered lane and requires an authoritative runtime decision or
operator action.

Stage-host observations buffered offline retain a stable observation identity, local sequence,
stage-host boot identity, session/epoch binding, original local UTC timestamp, and monotonic
offset evidence. Shipping is resumable and deduplicated. Runtime ingest preserves the raw
timestamp and records any corrected/estimated time separately.

These are non-event wire observations. Earlier design notes used the historical word "events";
that term grants no ADR-023 semantics. Observations do not use the ADR-023 `EventEnvelope`,
aggregate version/event index, event catalog, or PostgreSQL outbox publisher. If ingest later
commits a domain event, the owning cloud aggregate creates that separate fact in its own
state/audit/outbox transaction; the local observation cannot acquire domain authority by being
wrapped.

### Clock Synchronization

The protocol performs repeated four-timestamp exchanges rather than assuming either host's
wall clock is exact. Each sample captures runtime send, stage-host receive, stage-host send,
and runtime receive instants. The runtime derives round-trip delay, offset estimate, and an
uncertainty bound; filtering and acceptance rules use multiple samples.

Both endpoints record:

- UTC wall time for signed claims and cross-system correlation;
- monotonic time for local durations, queue scheduling, timeout measurement, and watchdog
  operation;
- the clock sample/estimate used for each corrected trace span or deadline decision.

Monotonic values are never compared directly across hosts. A validated offset maps a signed
UTC authorization window to a conservative local monotonic deadline. Queue acceptance and
immediate pre-playback checks proceed only when the stage host can prove, within the current
uncertainty bound, that `not_before` has passed and `not_after` has not passed.

Sleep/resume, reboot, monotonic discontinuity, material wall-clock step, excessive
uncertainty, or stale synchronization invalidates the mapping and requires resynchronization.
Corrected telemetry never overwrites original local timestamps.

### Heartbeat And Health

Heartbeats report rig/session binding, boot identity, current epoch, queue state, emergency
latch, adapter health, playback/audio health, offline-buffer health, and clock
offset/uncertainty evidence.

Heartbeat and WebSocket health do not replace the stage-host disconnect watchdog. The
watchdog uses a local monotonic clock and applies ADR-016's auto-mute and fallback-scene
behavior even when the cloud is unreachable.

Every connection, object-download, authentication, and other external operation has an
explicit timeout. Reconnect and retransmission are bounded and observable.

## Enforcement

- All wire messages use closed, versioned schemas and generated contracts for every participating
  implementation language. Python/TypeScript parity is only the current toolchain baseline; the
  selected stage-host language must be added without a hand-maintained parallel schema. A
  protected decision must first establish the canonical authoring location for non-event
  WebSocket messages consistently with ADR-002.
- Contract fixtures reject raw text, unknown fields, nested arbitrary payloads, invalid
  identifiers, unsupported versions, and invalid timing/order representations.
- Stage-host admission follows one ordered verifier: schema, connection/session binding,
  signature/claims, replay identity, artifact integrity metadata, sequence, and expiry.
- Queue admission, replay marker, sequence movement, task digest, and accepted status commit
  atomically before acceptance acknowledgement; `playing_or_in_doubt` commits before adapter
  start.
- Restrictive epoch controls use a priority verifier and atomically persist the newer epoch plus
  old-epoch queue eviction before acknowledgement.
- Task-signing authority is absent from stage-host artifacts and credentials.
- Replay and idempotency state survives reconnect and the required local restart scenarios.
- Deterministic rehearsal transport injects duplication, loss, delay, reordering, corruption,
  disconnect, reconnect, clock offset/drift/uncertainty/sample staleness, wall-clock steps, and
  sleep/resume.
- Live OBS/VTube Studio adapters, stage-host commands, watchdog, and e-stop behavior remain
  protected by human review.

## Failure Behavior

- Authentication, authorization, version negotiation, session binding, or handshake failure
  establishes no active rig and accepts no task.
- Malformed, oversized, unknown-version, unsigned, invalid-signature, wrong-audience,
  wrong-session/epoch, expired, not-yet-valid, digest-mismatched, or replayed tasks are
  rejected and never queued.
- An ordered-lane gap or conflicting duplicate pauses later media work and requests
  resynchronization; it never guesses an order.
- Media download timeout, authorization failure, or digest mismatch produces no playback.
- If clock freshness or uncertainty cannot prove that authorization is currently valid,
  task acceptance/playback fails closed until synchronization recovers.
- Connection loss invokes the local disconnect/watchdog policy. Redis or cloud unavailability
  cannot disable local mute, fallback-scene control, or hard e-stop.
- Offline-buffer exhaustion or loss of required audit durability marks the rig degraded and
  blocks new autonomous task acceptance; local safety actions remain available.
- A process/power failure after acceptance cannot lose the replay marker or cause automatic replay.
  A recovered `playing_or_in_doubt` entry is muted/stopped and reconciled, never resumed.
- During a partition, an old Mode 2 task becomes ineligible at its presence/health/control-link
  bounded expiry, and watchdog policy supplies the independent local safe-state bound.
- Reconnect does not resume a partial task or revive flushed work without a new valid
  authorization context.
- No failure path substitutes raw text, unsigned media, a stale cached task, or provider
  fallback output.

## Consequences

- The protocol carries more application state than a best-effort WebSocket, but reconnect
  and incident reconstruction become deterministic.
- Strict ordering is limited to the per-session speech/avatar lane; unrelated telemetry can
  progress independently.
- Conservative clock uncertainty can reject otherwise valid work, which is preferable to
  stale speech.
- Local durable state is required for replay defense, queue recovery, and offline evidence,
  but PostgreSQL remains the cloud system of record.
- Crash consistency deliberately prefers an in-doubt item being dropped over possibly playing the
  same speech twice.
- The stage-host language, cryptographic profile, timing values, and wire schema source must
  be approved before implementation.
- Live stage-host work remains blocked until this ADR, ADR-010, ADR-015, ADR-020, and the
  applicable OPEN security and timing decisions are accepted.

## OPEN Decisions

- OD-005: stage-host implementation language and distribution/update model.
- OD-011: connection authentication, task signature algorithm, key custody/provisioning,
  rotation overlap, revocation, and replay-record lifetime.
- OD-010 and OD-015: e-stop/watchdog SLOs, stop scope, resume authority, partition
  precedence, and reconciliation behavior.
- OD-017: protocol compatibility, deprecation, downgrade, rollback, and removal policy.
- OD-021: canonical schema authoring location and generation workflow for non-event WebSocket
  messages under ADR-002 and the selected stage-host language.
- OD-035: heartbeat/clock-sampling, staleness, offset/uncertainty, sample age, drift,
  retransmission/reconnect, deadline-mapping, authorization-horizon, and watchdog timing values.
- OD-036: stage-host protocol/clock/queue/journal SLI, telemetry, alert, monitoring-loss posture,
  and evidence freshness.
- OD-037: local queue/journal/message/connection capacity, protected reserve, overflow/shedding,
  compaction, drain, and recovery bounds.
- ADR-025: composite cloud actor fence, shared ownership-row linearization, recovery-only
  takeover/barrier, restrictive dispatcher, server-side signing/dispatch fence, and
  audience-bound ambiguity handling.
- Ordered-lane sequence allocation, gap recovery, acknowledgement retention, replay window, and
  rig-binding takeover policy.
- Local queue/journal storage engine, atomicity and flush profile, power-loss model, encryption,
  corruption recovery, and `playing_or_in_doubt` incident handling; numeric capacity belongs to
  OD-037.
- Restrictive epoch-control schema, authorization horizon, Mode 2 local convergence SLO, and
  interaction with watchdog and accepted interruption policy.
- Offline-buffer durability, capacity, retention, encryption-at-rest, overflow, and shipping
  policy under ADR-017 and OD-009/OD-016.
- Media-transfer authorization and object-storage mechanism under ADR-010.
- Framing, encoding, compression, maximum message sizes, rate limits, and endpoint/network
  deployment.
- Whether any valid queued work may continue during the pre-watchdog disconnect interval;
  no choice may override expiry, epoch, e-stop, or approval verification.

## Acceptance Evidence

Human acceptance requires:

- generated-contract parity across every participating implementation language plus invalid
  fixtures for every handshake, command, acknowledgement, heartbeat, clock, replay, and
  offline-observation message;
- authentication, signature, key-rotation, revocation, replay, substitution, wrong-session,
  wrong-epoch, and protocol-downgrade tests for the selected security profile;
- deterministic duplicate, loss, delay, reorder, gap, conflicting-ID, disconnect, reconnect,
  takeover, restart, and offline-observation upload/reconciliation tests;
- cloud actor pause/lease-expiry/revoke/takeover/PITR tests proving stale composite fences cannot
  sign or dispatch and ambiguous audience-bound work forces restrictive epoch/binding rotation,
  priority-control acknowledgement, and exact sealed-rig reconciliation;
- a crash/power-loss matrix at every queue transaction, acceptance acknowledgement, artifact
  fetch, `playing_or_in_doubt` transition, adapter start, completion, terminal commit, and
  acknowledgement boundary proving no lost accepted task and no automatic duplicate playback;
- connected and partitioned Mode 2 tests proving epoch advancement, priority notification,
  old-epoch eviction, presence/health-bounded expiry, immediate pre-playback rejection, and
  watchdog convergence;
- clock-model tests preserving raw UTC/local-monotonic observations while varying offset,
  asymmetric round-trip delay, drift, stale sample age, uncertainty, wall-clock step,
  sleep/resume, reboot, and expiry immediately before playback;
- local e-stop and watchdog tests with runtime, Redis, and operator console unreachable;
- proof that no task, wire log, offline record, or stage-host API contains raw generated
  text;
- a complete rehearsal incident timeline retaining raw local timestamps, monotonic durations,
  synchronization sample IDs, offset/uncertainty/age/round-trip evidence, and a separately
  derived non-authoritative cross-host view;
- approved protocol-security, timing, offline durability, compatibility, runbook,
  rollback/disable, and protected human-review decisions;
- passing contract, type, boundary, integration, fault-injection, and red-team gates on all
  target platforms.

## Informative Security References

These sources inform the eventual protocol-security review; they do not select JWT, DPoP, a
signature algorithm, credential type, or authentication profile:

- [RFC 6455: The WebSocket Protocol](https://www.rfc-editor.org/info/rfc6455/)
- [RFC 8725: JSON Web Token Best Current Practices](https://www.rfc-editor.org/info/rfc8725/),
  if the approved profile uses JWT
- [RFC 9449: OAuth 2.0 Demonstrating Proof of Possession](https://www.rfc-editor.org/info/rfc9449/),
  if the approved profile uses OAuth-bound proof of possession
