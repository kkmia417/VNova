# Rehearsal Mode

Status: Stub

See ADR-016: `docs/adr/0016-stage-host-and-cloud-local-topology.md`.

Rehearsal mode runs the full VNova pipeline without live broadcast hardware by using:

- Fake OBS.
- Fake VTube Studio.
- Virtual audio sink.

Rehearsal mode is required for CI e2e coverage and for validating fail-closed behavior before live operation.
