# Mode Transition Model

Status: Proposed reference model; no runtime behavior authorized

Governing proposals:
[ADR-020](../adr/0020-mode-transition-and-degradation-matrix.md) and
[ADR-025](../adr/0025-session-actor-ownership-command-ingress-and-fencing.md)

Mode transitions are operational safety behavior, not UI decoration. This document makes the
handoff-derived proposal reviewable without treating it as accepted architecture.

## Proposed Modes

| Mode | Proposed operating contract                                                                                                                                      |
| ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0    | Autonomous generation and dispatch are disabled. Only separately approved recovery assets and explicitly authorized manual workflows may reach a broadcast path. |
| 1    | The runtime may prepare candidates, but an authorized present operator must complete each candidate's terminal `SafetyDecision` before expiry and minting.       |
| 2    | Safety-approved work may dispatch without per-item approval only inside an accepted policy, content-category cap, and active operator-presence contract.         |

Mode numbers are ordered by autonomy. The exact names, detailed capability matrix, and whether a
future mode above 2 exists remain OPEN under OD-013.

## Requested, Effective, And Observed Mode

The runtime must keep these concepts separate:

- `requested_mode`: the last authorized operator request.
- `effective_mode`: the computed session-wide maximum currently permitted by every active
  session cap; it is never assigned directly by an operator.
- `upward_recovery_hold_cap`: the durable ceiling latched by an automatic degradation; recovery
  of the triggering fault cannot clear it.
- `work_effective_mode`: the lower value after applying a specific segment, category, trigger, and
  broadcast-surface cap.
- `observed_mode`: the last mode acknowledged by each safety-relevant participant.

The proposed calculation is:

```text
effective_mode = minimum(
  requested_mode,
  policy_cap,
  operator_presence_cap,
  safety_health_cap,
  provider_health_cap,
  rig_health_cap,
  environment_release_cap,
  upward_recovery_hold_cap
)

work_effective_mode = minimum(
  effective_mode,
  content_category_cap,
  trigger_surface_cap
)
```

An absent, unknown, stale, or contradictory cap is restrictive and must not increase autonomy.
An automatic degradation installs or lowers `upward_recovery_hold_cap` to the resulting effective
mode in the same serialized transition. The hold remains after a transient cap clears, so an old
higher `requested_mode` cannot silently restore autonomy.

## Transition Rules

### Downward

- Any authorized operator or safety controller may request a lower mode.
- An automatic degradation controller may lower the effective mode for its owned fault.
- The transition is immediate, idempotent, and does not require confirmation.
- Work that is no longer legal at the lower mode is cancelled or expired. Only a candidate whose
  evaluation is still nonterminal may move to an allowed operator-review state. A terminal
  machine decision is never reopened; any derived approval, media authorization, or task that
  depended on the higher mode is invalidated for further use.
- Every effective decrease advances the session authorization epoch. A connected stage host
  evicts not-yet-playing work from the old epoch; anything still eligible requires fresh dispatch.
- An automatic degradation durably installs or lowers the upward-recovery hold in the same
  transition. If PostgreSQL is unavailable, the process-local restrictive state remains
  `uncommitted_restrictive` and recovery is prohibited until the hold and evidence reconcile.
- A Mode 2 task expires no later than the earliest candidate/approval deadline, qualifying
  operator-presence lease, and accepted health/control-link horizon so a partition cannot preserve
  autonomous work without bound.
- Every participant acknowledges the new mode and epoch, but missing acknowledgement cannot delay
  the restrictive local action.
- Clearing a fault never raises the mode automatically.

### Upward

An upward transition requires all of the following:

1. An authorized operator requests a specific target mode.
2. Server-side authorization allows that operator and target.
3. Required health, operator presence, exact resolved-configuration snapshot and activation
   epochs, rig, and rehearsal evidence are current.
4. The content and session policy permit the target, and the exact normal-work admission epoch
   remains `open`.
5. The operator confirms the action and the system records the reason and evidence snapshot.
6. The current upward-recovery hold is explicitly reconciled and is cleared or raised atomically
   with this newly authorized transition; fault recovery alone never changes it.
7. Every safety-relevant participant acknowledges the new mode epoch before capabilities expand.

If a precondition changes during the transition, the increase fails closed.

## Proposed Automatic Caps

| Condition                                  | Maximum effective mode | Required immediate action                                                                                  |
| ------------------------------------------ | ---------------------- | ---------------------------------------------------------------------------------------------------------- |
| Safety verdict unavailable or inconsistent | 0                      | Stop autonomous dispatch, expire affected work, emit fail-closed events, alert                             |
| Safety escalation requiring human judgment | 0 or 1 by policy       | Queue only still-valid work that policy permits for manual review; otherwise discard                       |
| Generator or moderation provider degraded  | 1                      | Disable autonomous provider fallback until the fallback completes the same safety path                     |
| Required operator presence absent or stale | 1                      | Disable Mode 2 dispatch and alert                                                                          |
| Rig state, clock, or link unsafe           | 0                      | Stop new dispatch; stage-host applies its local watchdog and playback policy                               |
| Content-category cap below session mode    | Category cap           | Apply the lower cap to that item without raising or lowering unrelated work                                |
| Emergency stop active                      | No output              | E-stop overrides every mode; use the separate resume reconciliation in ADR-015 before normal mode handling |

Exact fault thresholds, debounce windows, presence lease, and the policy mapping from a safety
category to Mode 0 or Mode 1 remain OPEN. No implementation may encode the examples as production
defaults before review.

## Content-Category Caps

Every dispatchable content category has an explicit maximum mode. An absent category entry denies
autonomous dispatch. The handoff specifically proposes sponsor reads never exceed Mode 1; legal,
talent, safety, and product owners must approve the final matrix.

Caps apply independently to speech, captions, overlays, alerts, scene text, avatar actions, and
spoken usernames. A lower cap on one surface cannot be bypassed by rendering equivalent content
on another surface.

## Ordering And Concurrency

Mode-changing commands carry a protected submission recovery generation/token, session
identifier, idempotency key, expected mode epoch, target, principal/trusted source, reason, and
issued-at time. Session-runtime durably records semantic intent and receipt before acceptance,
under the exact `open` normal-work admission epoch/source CAS, then ADR-025's shared ownership-row
conflict and exact active composite actor fence serialize normal execution with other session
safety commands. A stale expected/recovery generation is rejected or requires reconciliation; a
duplicate identical semantic intent returns the original outcome after current lookup
authorization; a normal request serialized after begin-close makes admission non-open receives
the no-lineage `session_closed` response; a response timeout remains unknown. Downward
safe-direction actuation may apply without current ownership or open normal admission but cannot
claim durable success.

The durable transition record and Proposed `ModeChanged` event distinguish requested and
effective mode, trigger, previous and new epochs, exact configuration snapshot/activation
lineage, active caps, operator identity when applicable, and participant acknowledgements.
Under ADR-023 the event uses the stream-session aggregate subject and committed aggregate
version/event index. PostgreSQL is the recovery source; the current inactive event name and
schema grant no producer authority.

## Verification Contract

Before any mode is enabled:

- every capability has positive and negative tests at every mode;
- property tests prove that adding a restriction cannot increase effective autonomy;
- injected provider, safety, presence, rig, and clock faults degrade as specified;
- restoration never causes an automatic upward transition;
- clearing a transient fault while its upward-recovery hold remains cannot raise effective mode;
- queued and in-flight work cannot cross a newly lowered cap;
- restart and duplicate-command tests reconstruct the same effective mode from PostgreSQL;
- lost-response, stale-owner, lease-expiry/revoke/takeover, and recovery-only tests prove a
  downward restriction remains available while an upward change cannot bypass ADR-025;
- begin-close races prove no upward or ordinary mode command is accepted under a non-open
  admission epoch, while the separate authenticated safe-direction path remains restrictive-only;
- rehearsal tests cover each output surface and e-stop precedence;
- authorization tests cover each upward and downward command role.

The accountable product, safety, and operations owners must close OD-013 before accepting the
capability matrix or enabling autonomy.
