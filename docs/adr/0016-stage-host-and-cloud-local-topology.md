# ADR-016: Stage Host And Cloud/Local Topology

Status: Accepted

Priority: P0

Date: 2026-07-05

Source: `vnova-review-handoff.md`

## Context

VNova is a real-time broadcast runtime. OBS, VTube Studio, and audio playout run on a local streaming PC. They must not be treated as cloud services or optional peripherals.

The cloud runtime can generate, evaluate, and dispatch approved work, but the final broadcast act happens on the rig. Local failure modes must be handled locally because the cloud link may be unavailable during the most important incident: emergency stop.

## Decision

VNova will include a required local agent named `stage-host`.

`stage-host` is the local streaming PC agent responsible for:

- Maintaining an authenticated WebSocket connection to `session-runtime`.
- Being the sole consumer of `SpeechTask`.
- Maintaining the local playback queue.
- Driving the OBS adapter.
- Driving the VTube Studio adapter.
- Running a disconnect watchdog.
- Enforcing the local hard e-stop.
- Buffering logs while offline and shipping them after reconnect.
- Reporting heartbeats and measured clock offset to `session-runtime`.
- Supporting rehearsal mode with fake OBS, fake VTube Studio, and a virtual audio sink.

## Binding Requirements

### Cloud/Local Boundary

- `session-runtime` dispatches only approved speech and avatar work.
- `stage-host` receives `SpeechTask`s over an authenticated WebSocket.
- Redis is never exposed to the rig.
- `stage-host` verifies a signed approval token on every `SpeechTask`.
- `stage-host` rejects any speech task that lacks an `approved_response_id`.
- `stage-host` rejects any speech task whose approval token is invalid, expired, or not bound to the expected stream session.

### Sole SpeechTask Consumer

- No cloud worker, console, media layer, or provider gateway may consume `SpeechTask` directly.
- The only path from approved speech to broadcast playout is `session-runtime` dispatch to `stage-host`.
- TTS/media interfaces must accept `approved_response_id`; they must not accept raw text.

### Local Playback Queue

- `stage-host` owns playout ordering on the rig.
- The queue supports enqueue, play, interrupt, flush, and mark-complete operations.
- Queue state is reported back to `session-runtime`.
- Queue events are buffered offline when the cloud link is unavailable.

### OBS Adapter

- `stage-host` owns local OBS control.
- OBS control includes audio source cut/mute, fallback scene control, and scene/action dispatch required by approved broadcast tasks.
- OBS audio level is the source of silence monitoring for live playout.

### VTube Studio Adapter

- `stage-host` owns local VTube Studio control.
- VTS control includes avatar actions, expressions, and viseme/timing delivery required by approved tasks.
- `AvatarAction` may exist without `speech_task_id`.

### Disconnect Watchdog

- `stage-host` detects cloud-link loss.
- On disconnect beyond the configured watchdog threshold, `stage-host` auto-mutes and switches to a fallback BRB scene.
- The watchdog threshold value is configuration, not an embedded constant.
- Watchdog trips are audited after reconnect.

### Local Hard E-Stop

- Local hard e-stop cuts the OBS audio source and flushes the local playback queue.
- Local hard e-stop must work when the cloud is unreachable.
- Local hard e-stop must be reachable through a direct local channel and a physical hotkey.
- Local hard e-stop is idempotent.
- Local hard e-stop has no confirmation dialog.
- Resume requires confirmation and a reason.
- E-stop activation and resume are audited.

### Offline Log Buffering

- `stage-host` buffers local events while disconnected.
- Buffered events retain local timestamps and sequence numbers.
- After reconnect, `stage-host` ships buffered events to `session-runtime`.
- `session-runtime` corrects or annotates stage-host spans using reported clock offset.

### Heartbeat And Clock Offset

- `stage-host` reports heartbeat state to `session-runtime`.
- Heartbeats include rig identity, stream session binding, queue state, e-stop state, adapter health, and measured clock offset.
- `session-runtime` exposes rig status to operator workflows and observability.

### Rehearsal Mode

- Rehearsal mode runs the full pipeline without live OBS, live VTube Studio, or live broadcast output.
- Rehearsal mode uses fake OBS, fake VTube Studio, and a virtual audio sink.
- Rehearsal mode is required for CI e2e coverage and safety behavior testing.

## Consequences

- Media Plane implementation is blocked until this topology is honored.
- `stage-host` is required and is not optional.
- Broadcast safety no longer depends only on cloud availability.
- CI must include a rig simulator before live adapter behavior is trusted.

## Human Review Required

- Stage-host implementation language remains OPEN.
- E-stop latency budget must be confirmed in the latency ADR or a later e-stop ADR.
- Adapter implementation details require human review before production use.
