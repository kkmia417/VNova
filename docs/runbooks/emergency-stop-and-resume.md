# Emergency Stop And Resume

Status: Drafted / Proposed operational runbook; human review required; no implementation
or live use authorized

Governing decisions and references:

- [ADR-011](../adr/0011-stage-host-wire-protocol-and-clock-synchronization.md):
  Proposed stage-host protocol and reconciliation
- [ADR-015](../adr/0015-layered-emergency-stop.md): Proposed layered emergency-stop
  semantics
- [ADR-016](../adr/0016-stage-host-and-cloud-local-topology.md): Accepted stage-host
  topology and local authority
- [ADR-019](../adr/0019-authentication-authorization-and-operator-roles.md):
  Proposed operator capabilities
- [ADR-020](../adr/0020-mode-transition-and-degradation-matrix.md): Proposed
  mode-degradation rules
- [ADR-021](../adr/0021-broadcast-surface-inventory-and-overlay-policy.md):
  Proposed broadcast-surface controls
- [ADR-025](../adr/0025-session-actor-ownership-command-ingress-and-fencing.md):
  Proposed composite actor fence, restrictive-control delivery, and closed recovery barrier
- [Stage-host model](../architecture/stage-host.md)
- [Rehearsal mode](../architecture/rehearsal-mode.md)
- [Open decision register](../architecture/open-decisions.md)
- [Operational readiness review](../governance/operational-readiness-review.md)

This document specifies the evidence and decisions a production procedure must contain. It
does not define executable commands, API endpoints, role assignments, timing values, physical
controls, OBS scenes, or policy defaults. Those remain protected human decisions. Until this
runbook and its governing Proposed ADRs are accepted, it is rehearsal-only review material.

## Scope

Use this runbook when stopping or resuming VNova-controlled broadcast output because:

- unsafe, unauthorized, unexpected, or indeterminate content may reach the audience;
- the operator cannot prove the current cloud, rig, queue, adapter, or broadcast-surface state;
- a safety, rights, authorization, policy, protocol, or artifact-integrity control has failed;
- normal degradation or surface isolation cannot bound the risk;
- a local or cloud emergency-stop assertion is already active; or
- emergency-stop propagation, reconciliation, or resume has failed.

This runbook covers the local hard stop at `stage-host`, the cloud freeze at
`session-runtime`, their reconciliation, and the only safe route back to normal output. A
disconnect-only event begins with the
[rig disconnect and watchdog runbook](rig-disconnect-and-watchdog.md). An audio-only event
begins with the [silence and underrun runbook](silence-and-audio-underrun.md). Either runbook
must transfer here immediately if an emergency assertion is made or state becomes
unverifiable.

## Safety Objective

Stop first and coordinate second:

- The local hard stop takes effect on the rig without waiting for cloud, identity-provider,
  database, audit, or console availability.
- The cloud freeze takes effect without waiting for rig acknowledgement.
- Stop is one action, idempotent, and has no confirmation or mandatory reason.
- Stop wins every race with generation, approval, synthesis, dispatch, queueing, playback,
  reconciliation, or resume.
- Missing safety, authorization, local-effect, or reconciliation evidence fails closed to
  `engaged` and zero normal audience output.
- Any active assertion, unknown peer state, epoch disagreement, or failed reconciliation
  means the effective emergency state is `engaged`.
- `resume_pending` permits no partial output.
- Resume is a separate human-authorized workflow requiring explicit confirmation and a
  non-empty reason.
- Resume creates a new authorization context. It never revives an old turn, approval,
  artifact authorization, `SpeechTask`, queue entry, surface item, or avatar action.

## Roles And Authority

Concrete role names and assignments remain OPEN under ADR-019. The accepted operating model
must assign the following responsibilities before a production session:

| Responsibility            | Required authority and duty                                                                                                                                                 |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| First observer            | Assert the nearest authorized stop path immediately; do not investigate first or wait for another stop layer.                                                               |
| Local rig safety operator | Use the direct local or physical stop path, observe actual local output state, and keep the local latch engaged while state is uncertain.                                   |
| Cloud stop operator       | Assert cloud freeze through the command path independent of console state streaming and report the target session and observed result.                                      |
| Incident commander        | Establish scope, assign owners, maintain the stop state, approve phase transitions, and prevent an uncoordinated resume.                                                    |
| Stage-host owner          | Diagnose local latch, queue, adapters, clock, journal, and rig identity without bypassing the safety controller.                                                            |
| Session-runtime owner     | Diagnose the cloud freeze, actor ownership, epochs, in-flight work, persistence, and dispatch state without admitting new work.                                             |
| Safety/security owner     | Evaluate content, authorization, signature, replay, identity, or policy failure and determine whether credentials, policies, or artifacts require revocation or quarantine. |
| Evidence recorder         | Preserve a correlated timeline using identifiers, versions, outcomes, and timestamps without copying restricted content into ordinary logs.                                 |
| Resume authority          | A human principal distinct in capability from stop authority; supplies a reason and explicitly confirms the state-bound resume workflow.                                    |

The same person may hold more than one responsibility only if the human-approved separation
of duties permits it. No automated principal, local hotkey, watchdog, recovered connection,
cleared alert, or returned operator presence may resume output.

## Immediate Stop Actions

Do not wait to identify the root cause.

1. Assert whichever stop layer is immediately reachable.
   - At the rig, invoke the approved direct local or physical stop input. `stage-host` must
     latch locally and begin its safety effects before attempting cloud coordination.
   - With cloud control available, invoke the authorized cloud stop command. The command
     path must not depend on the console WebSocket or SSE connection.
2. Do not present a confirmation, request a reason, wait for a fresh aggregate version, or
   postpone the assertion for audit availability.
3. If the other stop layer is independently reachable, assert or verify it after the first
   layer has taken effect. Failure to reach the other layer does not undo or delay the first.
4. Establish one effective incident state of `engaged`. Treat missing, contradictory, or
   stale state as an active assertion.
5. Observe and record, without treating observation as a stop precondition:
   - local latch state;
   - OBS audio cut or mute outcome;
   - active-sink stop outcome;
   - queue and avatar-action flush outcome;
   - safe fallback-scene outcome;
   - cloud freeze and session-epoch invalidation outcome;
   - cancellation or terminal fail-closed outcome for in-flight work; and
   - the state of every enabled audience-facing surface.
6. If any local output continues or cannot be observed reliably, keep the latch engaged and
   use only the separately reviewed venue/rig out-of-band safety procedure. Escalate
   immediately; do not improvise an OBS, audio-device, power, or platform command.
7. Assign an incident commander and evidence recorder. The emergency action remains valid
   even if assignment or durable evidence occurs later.

The required local effect order is latch, audio cut/mute, active-audio stop, queue/action
flush, old-epoch rejection, safe fallback when locally available, and durable local
evidence. Failure in a later effect never reverses an earlier effect. The required cloud
effect order is freeze, epoch invalidation, admission stop, provider cancellation or late
result rejection, in-flight terminalization, synthesis/dispatch rejection, local stop
delivery, and durable evidence or retry buffering.

## Stabilization And Scope

Before diagnosis, establish these invariants:

- No normal voice, caption, overlay, alert, scene text, spoken username, avatar action, or
  other VNova-controlled surface is authorized by the engaged latch.
- No primary, retry, rewrite, manual, canned, or provider-fallback path may bypass the
  emergency state or the normal safety and surface gates.
- The operator console does not control OBS, VTube Studio, the local queue, or stage-host
  adapters directly.
- Redis, a WebSocket buffer, or a stage-host cursor is not used as recovery authority.
- PostgreSQL remains the cloud system of record, but database unavailability cannot release
  the strongest available process-local freeze.
- Restricted candidates, prompts, viewer-memory content, bearer tokens, and secrets are not
  copied into incident chat, ordinary logs, or screenshots.

Classify the incident scope as provisional until both layers reconcile. The accepted scope
policy must state whether the stop covers one session, one rig, all sessions on a rig, or a
broader environment. Until that policy is approved, operators must not infer that stopping
one displayed session has made every rig output safe.

## Diagnosis

Diagnosis occurs while `engaged`; it never weakens the latch.

### Local Layer

Determine and preserve evidence for:

- stage-host boot identity, rig identity, bound session, and local session epoch;
- local latch provenance and every duplicate stop assertion;
- the observed OBS audio-source state and actual output level;
- active sink and playback coordinator state, including `playing_or_in_doubt`;
- queued task/action identities, sequence, expiry, artifact digest, and flush outcome;
- OBS and VTube Studio adapter health and the fallback-scene result;
- direct local input and physical-control health;
- clock mapping validity, offset uncertainty, and any sleep, reboot, or clock step;
- offline journal durability, sequence range, capacity, corruption, or audit gaps; and
- any task rejected after the stop, without recording raw linguistic content.

An item in `playing_or_in_doubt` is not replayed. Missing, corrupt, conflicting, or rolled-back
local state keeps the rig unsafe.

### Cloud Layer

Determine and preserve evidence for:

- authoritative `StreamSession` ownership and lifecycle;
- cloud-freeze assertion provenance and durable or process-local state;
- old and current session authorization epochs;
- requested/effective mode and active degradation causes;
- scheduling, generation, safety, TTS, artifact, dispatch, and surface work present at the
  assertion boundary;
- cancellation attempts and late outcomes that were ignored;
- PostgreSQL, outbox, audit, and state-delivery health;
- rig-link identity, last heartbeat, acknowledgement, and clock evidence;
- authorization-policy, safety-policy, prompt, persona, model, voice-rights, and
  surface-registry versions; and
- any conflicting operator, workload, key, signature, replay, or idempotency evidence.

### Cross-Layer Reconciliation

Compare the local and cloud views by stable identifiers, not display labels:

| Condition                                                                           | Required interpretation                                                                                         |
| ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Either layer reports an assertion                                                   | `engaged`                                                                                                       |
| One layer is unreachable, stale, or unknown                                         | `engaged`                                                                                                       |
| Epochs, rig binding, queue outcomes, or stop provenance disagree                    | `engaged`; quarantine conflicting work and continue reconciliation                                              |
| Cloud is frozen but local output is not proven cut                                  | Critical unresolved local containment; escalate immediately                                                     |
| Local latch is engaged but cloud is not proven frozen                               | Keep local output stopped; freeze cloud before accepting any reconnect work                                     |
| Audit or journal evidence is not durable                                            | Stop remains effective; resume is prohibited                                                                    |
| Both layers agree they are stopped and every audience surface is safe               | Remain `engaged`; begin recovery planning only                                                                  |
| A valid new stop arrives during recovery or resume                                  | Invalidate recovery evidence and any resume challenge; return to the beginning of stabilization                 |
| A credential, signature, policy, artifact, or authorization compromise is suspected | Keep stopped; quarantine or revoke through the separately approved security process before any resume preflight |

## Recovery Preparation

Removing the technical cause is not permission to resume. Before entering a resume workflow:

1. Identify and document the root cause or, if not yet known, document the bounded failure
   domain and the controls that make continued operation safe. Unknown safety-critical
   causality blocks resume.
2. Complete any required credential, key, artifact, policy, voice-rights, or surface
   quarantine. A reconnect alone is not recovery.
3. Reconcile stage-host and runtime using authenticated peers and supported protocol
   versions.
4. Restore a valid clock mapping and current heartbeat evidence.
5. Prove all pre-stop and uncertain queue entries are flushed, terminal, expired, or
   otherwise ineligible. Nothing is reauthored or replayed locally.
6. Prove the audio source is safe, the active sink is stopped, adapters are in known state,
   and every persistent visible surface is cleared or in its reviewed neutral state.
7. Reconcile the local event journal with the cloud without fabricating a missing range.
   Record unresolved gaps and block resume when required evidence is missing.
8. Prove the cloud actor has the exact active recovery/ownership composite fence through the
   shared ownership-row mechanism; the source-serialized activation barrier and sealed rig cursor
   are current; freeze/restrictive-control acknowledgement is durable; and no late or lost-tail
   provider, safety, TTS, dispatch, or playback outcome can advance old work.
9. Verify current safety, authorization, policy, rights, approved-media, signed-dispatch,
   rig, observability, and operator-presence preconditions for the intended post-resume
   mode.
10. Select the proposed post-resume requested mode according to the accepted policy. Fault
    clearance never restores a prior higher mode automatically.

If any step fails, remain `engaged`, record the failed precondition, and escalate to its
owner.

## Resume Procedure

Resume is prohibited unless an accepted implementation provides the state-bound, auditable
workflow proposed by ADR-015.

1. A human with scoped resume authority initiates resume and supplies a non-empty reason.
2. The system re-evaluates all preparation criteria and enters `resume_pending`, which
   permits no normal output.
3. The system issues a single-use confirmation challenge bound to the human, session, rig,
   current aggregate version, every stop assertion, cloud/local epochs, and preflight
   evidence.
4. The human explicitly confirms that challenge through the approved
   submission-recovery-generation-bound command path.
5. Both cloud and stage-host authenticate each other, re-evaluate all current conditions,
   and commit exactly one new authorization epoch derived from the confirmed workflow.
6. Only after both layers reconcile the new epoch may the effective latch become `clear`.
7. Admit only newly created or freshly authorized work under the new epoch. Never restore a
   pre-stop queue or extend an old deadline.
8. Observe all enabled surfaces and health signals for the human-approved post-resume
   validation interval. Keep the mode at the accepted conservative ceiling unless a
   separate confirmed mode-increase workflow succeeds.

A stale challenge, changed principal, new stop, changed epoch, partition, timeout, missing
acknowledgement, failed durable transition, failed precondition, or ambiguous local effect
returns the session to `engaged`. It never produces a partially clear state.

## Exit Criteria

The incident may exit this runbook in one of two states.

### Safe-Stopped Handoff

All of the following are true:

- the effective emergency state remains `engaged`;
- local output is cut or a reviewed out-of-band containment owns the unresolved local risk;
- cloud work is frozen or the strongest available local process freeze is held;
- old tasks and audience-surface items cannot resume automatically;
- unresolved scope, evidence gaps, owners, and next review time are recorded; and
- a named incident commander retains authority over any later resume attempt.

### Controlled Resume

All of the following are true:

- every local and cloud stop assertion has been acknowledged and is eligible to clear;
- a scoped human supplied a reason and explicitly confirmed the current state-bound
  challenge;
- cloud and stage-host agree on a newly issued epoch and authenticated binding;
- local latch, queue, adapters, clock, journal, and audience surfaces satisfy the accepted
  preconditions;
- cloud ownership, persistence, safety, authorization, policy, rights, observability, and
  operator-presence evidence is current;
- no pre-stop or in-doubt work is eligible;
- the post-resume requested/effective mode is explicit and did not rise automatically; and
- the accepted observation period completed without a new stop, safety fault, stale output,
  or unreconciled audit evidence.

Technical fault clearance alone, a green dashboard, reconnection, or successful test sound
does not satisfy controlled resume.

## Evidence And Audit

Capture a correlated incident timeline with:

- incident, command, idempotency, session, rig, boot, epoch, trace, turn, task, artifact, and
  surface identifiers as applicable;
- human principal or trusted local-device provenance;
- old/new emergency state and assertion layer;
- authorization decision and policy versions;
- local and cloud receipt times, raw local times, monotonic durations, and clock-correction
  evidence;
- audio-cut, active-stop, queue-flush, fallback-scene, cloud-freeze, cancellation, surface
  clear, and post-stop rejection outcomes;
- persistence, outbox, journal, reconnect, and acknowledgement status;
- every resume precondition, reason, confirmation identity, challenge outcome, new epoch,
  and post-resume mode; and
- owners, escalations, evidence gaps, and follow-up actions.

Stop proceeds if audit persistence is unavailable. Resume does not. Offline evidence is
shipped idempotently after reconnect. Do not place secrets, access tokens, raw prompts,
candidate text, viewer-memory content, or restricted rights evidence in ordinary audit
records.

## Escalation

Escalate immediately to the incident commander and accountable safety/stage-host owner when:

- local audio or another audience surface continues or cannot be proven safe;
- the direct local stop path, physical control, OBS adapter, or active sink does not produce
  its accepted effect;
- cloud freeze cannot be established or generation/dispatch continues;
- a rig, session, epoch, queue, or stop-state conflict persists;
- old or `playing_or_in_doubt` work appears eligible after restart or reconnect;
- authorization, signature, replay, key, policy, rights, or artifact compromise is
  suspected;
- required evidence is missing, corrupt, or cannot become durable; or
- a resume attempt partially commits, times out, or fails reconciliation.

Security compromise, personal-data exposure, rights violation, platform-policy breach, and
public audience impact also transfer to their separately approved incident and notification
processes. Exact contacts, paging routes, severity levels, regulatory decisions, and external
communications are OPEN and must be assigned before production.

## Rehearsal Acceptance

This runbook is not production-ready until deterministic rehearsal evidence covers:

- local hard stop with cloud, Redis, database, identity provider, and console unreachable;
- cloud freeze with the rig unreachable;
- stop during every pipeline and local playback boundary;
- duplicate, delayed, reordered, stale-version, and concurrent stop assertions;
- stop during resume, stale confirmation, changed principal, and changed epoch;
- local process restart, power loss, adapter failure, journal corruption, and audit-store
  failure;
- queue entries in accepted, starting, `playing_or_in_doubt`, completed, and terminal states;
- every enabled broadcast surface clearing or moving to its reviewed neutral state;
- authentication, signature, replay, and old-epoch rejection;
- reconciliation after both partition directions without reviving old work;
- a complete safe-stopped handoff and a separately complete confirmed resume; and
- one reconstructable timeline showing raw local observations and explicit clock
  corrections without restricted-content leakage.

Target-rig evidence must separately prove the accepted audio-cut, queue-flush, propagation,
surface-clear, and recovery SLOs. Simulator success does not authorize live adapters.

## OPEN Decisions Requiring Human Review

- OD-027: incident classes and severity, accountable roster and coverage, command/handoff
  authority, resilient escalation and communications, exercise cadence, evidence
  freshness, runbook ownership, and deployment-specific authorization.
- Numeric local hard-stop, propagation, watchdog, surface-clear, reconciliation, recovery,
  observation, and operator-response SLOs.
- Stop scope across sessions, rigs, environments, and concurrent broadcasts.
- Concrete stop/resume capabilities, role assignments, separation of duties, step-up
  authentication, confirmation challenge lifetime, and whether two humans are required.
- Direct local channel, physical control, out-of-band rig containment, and their independent
  failure tests.
- Exact local effect ordering where adapter constraints differ, active-audio interruption,
  avatar/surface interruption, and safe fallback scene.
- Post-resume requested/effective mode and the evidence needed to allow each mode.
- Protocol, signature, key custody, rotation, revocation, replay, and rig-enrollment profile.
- Persistence, offline journal, capacity, corruption recovery, audit retention, evidence
  access, and incident-hold policy.
- Severity, paging, on-call ownership, legal/privacy/rights escalation, and external
  communication procedures.
- Final command/event schemas and API paths. This runbook intentionally specifies no
  executable command or endpoint.
