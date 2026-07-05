# Stage Host

Status: Stub

See ADR-016: `docs/adr/0016-stage-host-and-cloud-local-topology.md`.

`stage-host` is the required local streaming PC agent. It is the sole consumer of `SpeechTask`, owns local playback, drives OBS and VTube Studio, enforces local hard e-stop, buffers offline logs, and reports heartbeat and clock offset.

OPEN: implementation language remains pending human decision.
