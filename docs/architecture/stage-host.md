# Stage Host

Status: Accepted topology with Proposed protocol and e-stop details; no implementation authorized

Governing decisions:

- [ADR-016](../adr/0016-stage-host-and-cloud-local-topology.md): accepted cloud/local
  topology
- [ADR-011](../adr/0011-stage-host-wire-protocol-and-clock-synchronization.md):
  proposed wire protocol and clock model
- [ADR-015](../adr/0015-layered-emergency-stop.md): proposed layered emergency stop
- [ADR-020](../adr/0020-mode-transition-and-degradation-matrix.md): proposed mode
  degradation
- [ADR-023](../adr/0023-event-subject-scope-correlation-and-ordering.md): proposed
  domain-event boundary; stage-host task/control/journal messages remain non-event contracts
- [ADR-025](../adr/0025-session-actor-ownership-command-ingress-and-fencing.md): proposed cloud
  composite actor/signing/dispatch fence, restrictive-control delivery, and sealed takeover
  reconciliation

`stage-host` is the required local streaming-PC agent. It is the sole consumer of `SpeechTask`,
owns local playback, drives OBS and VTube Studio, enforces local hard e-stop, buffers offline
observations, and reports heartbeat and clock state.

## Trust Boundary

```text
cloud session-runtime                   local streaming PC
---------------------                  --------------------
approved dispatch -- authenticated --> stage-host
status/observations <-- authenticated -- stage-host
                                         |
                                         +-- playback queue
                                         +-- OBS adapter
                                         +-- VTube Studio adapter
                                         +-- local hard e-stop
                                         +-- disconnect watchdog
                                         +-- durable offline observation journal
```

Redis, provider credentials, raw generated text, safety mint capability, and direct database
access do not cross onto the rig. The console does not drive OBS, VTube Studio, or the playback
queue directly.

## Local Components

| Component                   | Sole responsibility                                                                                              |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Link supervisor             | Authenticated protocol session, version negotiation, heartbeat, reconnect backoff, and session binding           |
| Command verifier            | Schema, signature, expiry, session, epoch, artifact-integrity, idempotency, ordering, and replay checks          |
| Playback coordinator        | Accepted-task queue, immediate pre-playback validation, interruption, completion, and local sequence reporting   |
| OBS adapter                 | Audio-source cut/mute, approved scene control, fallback scene, and measured output level                         |
| VTube Studio adapter        | Approved avatar actions, expressions, and viseme/timing delivery                                                 |
| Safety controller           | Local e-stop latch, watchdog, safe-state convergence, and resume precondition checks                             |
| Offline observation journal | Bounded local persistence of sequenced operational observations until acknowledged by the cloud                  |
| Clock monitor               | Monotonic scheduling, wall-clock comparison, offset/uncertainty reporting, and unsafe-skew rejection             |
| Rehearsal adapter bundle    | Fake OBS, fake VTube Studio, virtual audio sink, deterministic clock, and injectable link/adapter/clock failures |

The implementation may place these responsibilities in one process, but dependency boundaries
must keep adapter failure, network input, and offline observation upload/reconciliation from
bypassing command verification or the safety controller.

## Command Admission

A `SpeechTask` is admitted only when all required checks pass:

1. The protocol envelope and payload version are supported.
2. The authenticated peer, rig identity, stream session, and session epoch match.
3. The task signature and key identifier satisfy the approved cryptographic profile.
4. The `approved_response_id` and immutable media artifact binding are present.
5. No raw generated text or executable markup is present.
6. The approval and task have not expired under the measured clock uncertainty.
7. The task is not duplicated, replayed, superseded, or outside its allowed sequence window.
8. The local e-stop, watchdog, effective mode, and adapter health permit queueing.

The same expiry, e-stop, mode, and artifact checks run again immediately before playback. A
rejected task produces a classified local observation record but no broadcast output.

ADR-021/022 propose additional surface and voice-rights authorization bindings plus a
rights-invalidation command. They remain outside ADR-008's current closed task allowlist until
ADR-011, OD-021, the protected contracts, and ADR-015 interruption scope are accepted together.
Unknown fields or ad hoc invalidation messages fail closed; this reference model does not widen
the wire protocol.

## Local State Model

Safety-relevant state is explicit and persisted where restart recovery requires it:

```text
DisconnectedSafe
  -> Connecting
  -> Reconciling
  -> Ready
  -> Playing

any state -> Stopped       local e-stop
any connected state -> WatchdogSafe
Playing -> Ready           completion or safe interruption
Stopped/WatchdogSafe -> Reconciling -> Ready
```

`Stopped` and `WatchdogSafe` are restrictive latches, not transient UI indicators. A process
restart, cloud reconnect, or adapter recovery must not clear them implicitly. Reconciliation uses
the newest session epoch and the strictest known stop state; ambiguous state remains safe. Cloud
recovery/ownership composite actor fence is not a local playback claim unless an accepted
OD-021/029 contract explicitly carries its recovery component. When revoke/takeover leaves any
possible task/control/playout ambiguity, ADR-025 advances the session authorization epoch or
stronger binding fence, evicts old work, and reconciles this exact rig under a sealed recovery
hold before new dispatch. Administrative-revoke control may arrive from ADR-025's closed
restrictive dispatcher without an active actor; it can only preserve or strengthen restriction.

## Queue And Interruption

- Queue order is strict per `stream_session_id`; unrelated telemetry does not share that FIFO.
- Queue operations are idempotent and identified independently from transport delivery.
- Acceptance acknowledgement follows an atomic durable commit of the canonical task digest,
  replay marker, sequence, authorization epoch, queue state, artifact binding, and expiry.
- `playing_or_in_doubt` is durably recorded before adapter start; restart never automatically
  replays that state and first converges to muted/reconciled safety.
- A queue entry references approved immutable artifacts; it never caches generated text.
- Interruptibility is explicit per approved task and content category.
- E-stop and watchdog actions override non-interruptible media.
- A flush records which queued and active entries were prevented from playing.
- Completion means locally observed playout completion, not command receipt.
- Cloud cancellation that arrives after local completion is reconciled as an audited late command.
- An effective-mode decrease advances the authorization epoch through a protected priority control;
  stage-host atomically persists the newer epoch and evicts old-epoch queued work before
  acknowledgement. Mode 2 task expiry is additionally bounded by operator-presence and accepted
  health/control-link horizons.

Exact priority, preemption, crossfade, and resume-from-offset policy remains OPEN and must be
accepted before the relevant behavior is enabled.

## Connectivity And Watchdog

The authenticated link carries commands down and state/events up. Operator stop has an independent
cloud command path and does not depend on console state streaming. The stage-host watchdog uses a
local monotonic clock and moves the rig to the accepted safe scene and audio state when cloud
liveness exceeds the approved threshold.

Heartbeat payloads expose rig/session binding, protocol and software version, queue watermark,
current task, e-stop/watchdog latch, adapter health, offline-buffer watermark, clock offset and
uncertainty, and last accepted command sequence. Thresholds and heartbeat intervals are
configuration validated against an accepted operational profile, never embedded assumptions.

## Offline Observations And Reconciliation

The local journal is bounded, integrity protected, crash recoverable, and contains operational
metadata rather than generated or approved response text. Each observation has rig identity,
session epoch, local sequence, monotonic observation time, wall-clock observation time, data
classification, and a stable idempotency key.

These offline observations are not ADR-023 domain-event envelopes. Their schema, sequence,
authentication, acknowledgement, and generation for the selected stage-host language remain
governed by ADR-011 and OD-021. Cloud ingestion may commit a separate domain fact only through
its owning aggregate transaction; it never wraps the local message and inherits authority
automatically.

After reconnect:

1. Both peers authenticate and negotiate a supported protocol.
2. Stage-host reports its restrictive state, sequence watermarks, clock estimate, and buffer range.
3. The runtime reports the authoritative session epoch and acknowledgements.
4. Stage host enters a sealed restrictive recovery hold and returns its exact boot/binding/epoch/
   journal cursor; stop state and epoch reconcile before any dispatch.
5. Buffered observations upload in bounded batches with explicit timeouts and acknowledgements.
6. Already acknowledged observations are skipped idempotently.
7. Missing, corrupt, or truncated ranges raise an audit gap; they are not fabricated.
8. New playback is enabled only by an authenticated activation/binding step for the exact accepted
   epoch after the cloud activation barrier succeeds.

PostgreSQL remains the cloud recovery source. The stage-host buffer is evidence from a disconnected
rig, not a parallel system of record. After PITR, neither restored PostgreSQL absence nor a local
journal gap proves no task played; `lost_tail_unknown` keeps the affected audience scope disabled.

## Local Hard Stop

The direct local stop path must remain functional with the cloud, console, database, network, or
main stage-host control loop unavailable to the greatest extent allowed by the approved design.
It cuts the OBS audio source, stops the active local sink, flushes queued media, prevents new
admission, and records the latch locally.

Stop is one action, idempotent, and has no confirmation. Resume is a separate authorized operation
with confirmation, reason, healthy adapters, reconciled cloud state, and an explicitly selected
post-resume mode. Target-hardware latency and independence evidence are required before live use.

## Rehearsal Equivalence

The simulator implements the same public stage-host contracts and state machine as live adapters.
Tests control monotonic time, wall-clock offset/drift/uncertainty, link loss, duplicate and
reordered frames, signature and artifact failure, OBS/VTube Studio failure, audio underrun,
process restart, journal
truncation, stop, and deliberate resume. Simulator-only success cannot authorize live adapters;
target-rig parity and protected human review are separate gates.

## OPEN Decisions

- Stage-host implementation language: OD-005.
- Local e-stop and watchdog SLOs: OD-010.
- Cryptographic, key-custody, and rotation profile: OD-011.
- Stop scope and resume reconciliation: OD-015.
- Queue interruption and reconnect thresholds require accountable stage-host, safety, security,
  and operations approval before implementation.

No stage-host command, watchdog, OBS adapter, or VTube Studio adapter implementation is authorized
by this reference model.
