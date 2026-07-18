# ADR-020: Mode Transition And Degradation Matrix

Status: Proposed

Priority: P1

Date: 2026-07-17

Sources: `AGENTS.md`, `vnova-review-handoff.md`, ADR-003, ADR-008, ADR-015, ADR-017,
ADR-019, ADR-023, ADR-024, ADR-025

This ADR is non-binding while its status is `Proposed`. No autonomous mode may be enabled
until the capability matrix, health preconditions, operator-presence contract, and
production evidence are accepted.

## Context

Progressive autonomy is safe only when mode has precise operational meaning. A UI label such
as "Mode 2" cannot decide whether a viewer trigger may generate, whether a machine verdict
may approve, whether an operator must be present, whether memory may be written, or what a
provider or safety failure does.

Mode is also not the session lifecycle, emergency latch, rig connection, or candidate state.
Those axes change independently. Combining them in one enum creates unsafe recovery and
ambiguous audit behavior.

## Decision

VNova will initially define Modes 0, 1, and 2 only. Any higher numeric mode is invalid until a
later ADR defines its capabilities, threat model, degradation behavior, and evidence.

The `StreamSession` stores two mode values:

- `requested_mode`: the operator-approved autonomy ceiling.
- `effective_mode`: the computed session ceiling after session-wide health, policy,
  presence, release, and degradation constraints.

The session value is computed, never directly assigned by an operator:

```text
effective_mode = min(
  requested_mode,
  session-wide health ceiling,
  operator-presence ceiling,
  active policy ceiling,
  environment/release enablement ceiling,
  upward-recovery-hold ceiling
)
```

For each unit of work, a further value is computed:

```text
work_effective_mode = min(
  effective_mode,
  segment/content-category ceiling,
  trigger and broadcast-surface ceiling
)
```

Unknown or unverifiable ceilings fail toward the lower mode. The emergency latch remains an
independent dominant axis: when engaged or resume-pending, no mode authorizes output.

## Initial Capability Matrix

| Capability                                             | Mode 0: safe hold                                                                      | Mode 1: supervised                                              | Mode 2: guarded autonomy                                                                                       |
| ------------------------------------------------------ | -------------------------------------------------------------------------------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Scheduled/viewer/idle model generation                 | Not admitted autonomously                                                              | Allowed for enabled categories                                  | Allowed for enabled low-risk categories                                                                        |
| Automated terminal approval                            | Never                                                                                  | Never; a human completes the terminal `SafetyDecision`          | Allowed only when every safety layer returns an approving, determinate verdict and policy permits the category |
| Operator review                                        | May review operator-originated or already queued eligible work; no autonomous dispatch | Required before generated speech                                | Required for borderline, exceptional, or capped categories                                                     |
| Dispatch without a per-item operator terminal decision | Never                                                                                  | Never                                                           | Allowed for eligible, unexpired, fully approved low-risk work                                                  |
| Operator-originated/manual speech                      | Same common safety lineage; explicit operator decision required                        | Same common safety lineage; explicit operator decision required | Same common safety lineage; never bypasses safety or audit                                                     |
| Separately approved canned fallback                    | Policy-authorized, identifier-only path only                                           | Policy-authorized, identifier-only path only                    | Policy-authorized, identifier-only path only                                                                   |
| Viewer-memory write                                    | Operator-approved typed slots only                                                     | Operator-approved typed slots only                              | Automatic write only for policy-defined low-risk typed slots; all others require operator approval             |
| Tool use                                               | Prohibited                                                                             | Prohibited                                                      | Prohibited                                                                                                     |
| Qualifying operator presence                           | Required for human actions; not a basis for autonomous output                          | Required to complete approvals                                  | Continuously required for autonomous eligibility                                                               |

Mode 0 is not emergency stop. It blocks autonomous generation and speech but may allow a
separately authorized human to submit and complete operator-originated work through the same
`SafetyDecision -> ApprovedResponse -> identifier-only media` chain. ADR-015's engaged latch
blocks even that path.

Mode 1 is the first live-operable mode: generation can run, but every candidate requires an
operator's terminal decision before `packages/safety` may mint approval. Absence of an
operator naturally yields no approval; queue TTL expiry discards the work.

Mode 2 permits automatic terminal approval only for work whose trigger, segment, surface,
policy category, and safety evidence all permit Mode 2. It does not authorize tool use,
unsafe memory writes, raw chat overlay, provider bypass, or raw-text TTS.

## Content-Category And Surface Caps

Every segment and policy-controlled content category has an explicit autonomy ceiling.
Missing or unknown category metadata has a Mode 0 ceiling.

Sponsor reads, contractual copy, legal/compliance statements, and materially equivalent
controlled content have a maximum ceiling of Mode 1: an operator must approve the exact
candidate that will be spoken or displayed. A policy cannot silently raise that ceiling.

Every broadcast surface is evaluated independently under its own cap and ADR-021 moderation
rules. Approval for voice does not imply approval for captions, overlay, alerts, scene text,
or spoken usernames unless an accepted contract explicitly binds those outputs.

The complete category taxonomy and caps beyond the mandatory controlled-content ceiling
remain OPEN. Policy activation cannot create a category whose ceiling exceeds the accepted
architecture matrix.

## Mode State And Transition Semantics

Mode state includes:

- requested and effective values;
- active degradation causes and their imposed ceilings;
- authorization-policy, safety-policy, prompt, and capability-matrix versions;
- operator-presence lease generation;
- session aggregate version and authorization epoch;
- identity and provenance of the last requested-mode change;
- an upward-recovery hold after every automatic degradation.

### Downward Transitions

A downward transition is instant and always allowed for an otherwise authenticated and
scoped operator or a reviewed automatic degradation rule.

- It has no confirmation dialog.
- Health, provider availability, queue state, and normal optimistic-version conflicts cannot
  block the safer value.
- A stale expected aggregate version is recorded but does not reject the decrease.
- The exact current session owner immediately commits the lower ceiling. Under ADR-025's
  safe-direction exception, any authenticated in-scope runtime boundary may first apply the
  strongest process-local lower ceiling when ownership or PostgreSQL is uncertain, stop
  admission under the old ceiling, and invalidate work whose authorization depended on the
  higher mode without claiming durable success.
- Failure to persist or publish the transition cannot justify continued higher autonomy; the
  runtime holds the lower mode and retries durable evidence.
- Multiple simultaneous degradation causes combine by taking the lowest ceiling.

"Instant" means the authorization ceiling changes before any later pipeline transition is
allowed. It does not by itself promise an audio hard cut. Work already playing follows its
accepted interruption policy unless the degradation cause also engages ADR-015. Queued or
in-flight work that depended on the previous higher mode is never grandfathered:

- a candidate whose evaluation is still nonterminal may enter `awaiting_operator` if it
  remains eligible and unexpired;
- a candidate with an existing terminal machine `SafetyDecision` is never reopened or given
  a second decision; its higher-mode approval, media authorization, and queued task are
  invalidated, and any renewed attempt must create new lineage under current policy;
- work already backed by the required per-item operator decision may continue only if every
  lower-mode, content-cap, expiry, epoch, and interruption check still permits it.

Every effective downward transition advances the session authorization epoch. A connected
stage host receives an authenticated epoch/ceiling update and evicts every not-yet-playing
task from the old epoch; work that remains valid must be freshly dispatched under the new
epoch. A lost update cannot leave Mode 2 tasks locally usable without bound:

- the signed authorization expiry for a Mode 2 `SpeechTask` is no later than the minimum of
  the candidate/approval deadline, qualifying operator-presence lease expiry, and the
  accepted runtime-health/control-link authorization horizon;
- stage-host validates signature, current epoch, and that shortened expiry immediately before
  playback using the conservative local-monotonic mapping bound to a named offset sample,
  uncertainty, sample age, and round-trip evidence under ADR-011; an unverifiable bound rejects
  playback;
- on link loss, no new authorization arrives and ADR-016's watchdog independently mutes and
  enters its safe fallback state;
- Mode 2 cannot be enabled until the maximum authorization horizon and watchdog behavior
  satisfy the accepted local convergence SLO on target hardware.

The existing signed task already binds session epoch and expiry under ADR-008. Final
mode-change control frames and any additional locally verifiable claim require ADR-011
contract review; no unreviewed mode or presence field may be added to `SpeechTask`.

### Upward Transitions

An upward transition is never automatic. It requires:

- an authenticated operator with scoped mode-increase authority;
- qualifying current operator presence;
- an explicit, server-validated confirmation bound to the target mode and preflight state;
- a current aggregate version and single-use idempotency/challenge identity;
- every target-mode precondition to pass at confirmation time;
- no unresolved degradation cause imposing a lower ceiling;
- accepted release/readiness evidence for the target environment;
- an auditable rationale and resulting state.

The operator may request a higher ceiling, but `effective_mode` does not rise until
confirmation commits. If any bound precondition changes between preflight and confirmation,
the increase is rejected. Clearing a fault or restoring operator presence only removes a
cause; it never clears the upward-recovery hold or raises mode by itself.

Mode increases proceed one level at a time in the initial proposal so each confirmation has
one capability delta. Whether production may allow a reviewed multi-level request remains
OPEN.

## Target-Mode Preconditions

All nonzero modes require:

- emergency latch `clear`;
- a valid session lifecycle state;
- authenticated current rig binding and accepted session epoch;
- healthy identifier-only approved-media and signed-dispatch path;
- active, accepted safety, authorization, prompt, persona, and content-policy versions;
- no unknown or expired safety decision for work being advanced;
- required observability, alert, and rollback/disable controls for the enabled capabilities.

Mode 1 additionally requires an operable manual review path for any generated work and an
operator authorized to complete decisions before production use.

Mode 2 additionally requires:

- current qualifying operator-presence leases that meet the human-approved required count
  and capability mix;
- deterministic and independent model-based safety layers healthy for every enabled
  category;
- generator and safety-judge provider independence as required by the safety architecture;
- passing red-team, fail-closed, fallback-through-gate, expiry, and rehearsal evidence for
  the exact policy/model versions;
- production telemetry and alerting for operator absence, safety health, provider health,
  queue age, rig health, and mode changes;
- an explicitly enabled category/surface allowlist whose caps permit Mode 2.

Numeric health windows, error thresholds, evidence freshness, and presence duration are
OPEN. They must be policy values approved before production rather than constants inferred
by implementation.

## Automatic Degradation Matrix

The initial fail-safe targets are:

| Trigger                                                                                      |              Immediate maximum effective mode | Additional behavior                                                                                                                                                                    |
| -------------------------------------------------------------------------------------------- | --------------------------------------------: | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Operator presence absent or uncertain while in Mode 2                                        |                                             1 | Stop new autonomous admission; route eligible pending work to operator review or expiry.                                                                                               |
| Primary generator hard failure with a healthy, policy-approved fallback                      |                                             1 | Fallback still re-enters the same safety gate; no automatic return to 2.                                                                                                               |
| No viable generator path                                                                     |                                             0 | Produce no candidate; use silence/fallback scene or separately approved canned behavior.                                                                                               |
| Safety result elevated to manual-review policy for the category                              |                           1 for affected work | No automatic terminal approval; queue with TTL.                                                                                                                                        |
| Required safety layer unavailable, timed out, indeterminate, or vendor-independence violated |                                             0 | Fail closed, emit `SafetyLayerUnavailable` and `FailClosedActivated`, and produce no autonomous speech.                                                                                |
| Required input/surface moderation unavailable for a trigger/surface                          |                           0 for affected work | Reject or hold that work; do not redirect it to an unmoderated surface.                                                                                                                |
| Stage host disconnected, unbound, wrong epoch, or watchdog-unsafe                            |                                             0 | Stop dispatch; local watchdog behavior follows ADR-016.                                                                                                                                |
| Speech-task signature, replay, artifact integrity, or expiry validation failure              |                                             0 | Reject task, alert, preserve evidence, and evaluate whether ADR-015 must engage.                                                                                                       |
| Active emergency latch or unresolved stop reconciliation                                     | No normal broadcast output regardless of mode | ADR-015 dominates; mode values authorize no normal speech/media/avatar output, while stop-owned audio cut, queue flush, alarm, and configured fallback-scene effects remain permitted. |
| Active policy/capability version missing, invalid, or unverifiable                           |                                             0 | Fail closed until a reviewed version is restored and an operator confirms any increase.                                                                                                |

A category-specific cause lowers `work_effective_mode` without unnecessarily lowering
unrelated work, provided the accepted policy engine can prove isolation. A session-wide
trust failure lowers the session `effective_mode`.

Exact provider health classification, safety escalation categories, rig thresholds, and
whether additional incidents degrade to 0 or 1 remain subject to protected human review.
Unknown fault classes default to Mode 0 until classified.

## Operator Absence

Mode 2 continuously requires qualifying unexpired presence leases that meet the
human-approved count and capability mix defined by ADR-019. Any shortfall caused by lease
expiry, revocation, incompatible permission change, or unverifiable presence:

1. effective mode immediately degrades to at most Mode 1;
2. new autonomous approval and dispatch stop;
3. eligible candidates with nonterminal evaluation may enter operator review with their
   original TTL; terminal machine-approved work is invalidated rather than reopened;
4. `OperatorPresenceChanged` and `ModeChanged` are emitted and alerted;
5. return of presence does not restore Mode 2 without a new confirmed upward transition.

Mode 1 can remain the effective ceiling while no operator is present, but no human approval
can occur and queued work expires. Whether prolonged Mode 1 absence must further degrade the
session to Mode 0, and after what duration, remains OPEN.

## Command Semantics And Concurrency

Mode commands follow ADR-003/025 submission-recovery-generation framing, semantic idempotency,
current lookup/execution authorization, durable receipt, universal expiry, and exact composite
actor/ownership-row serialization rules. A response timeout is unknown and is resolved by an
authorized receipt query or same-intent retry; stale/unknown-generation or lost-tail absence
requires reconciliation.

`LowerRequestedMode` carries an idempotency key, target session, target lower value,
principal, authorization evidence, observed version, and source/reason metadata. Duplicate
commands return the first result. Same-key/different-content reuse is rejected and audited,
but cannot restore the prior higher mode.

`BeginModeIncrease` evaluates preconditions and creates a short-lived, single-use challenge
bound to operator, session, source mode, target mode, aggregate version, policy versions,
presence generation, active health snapshot, and rationale.

`ConfirmModeIncrease` re-evaluates the bound facts and, only if all remain valid, atomically
updates the requested target and/or clears only the upward-recovery holds named by the
challenge. It never writes a chosen `effective_mode`; the actor recomputes that value from
the updated requested mode and every current session-wide ceiling. A concurrent degradation
or emergency stop wins, invalidates the challenge, and leaves the lower ceiling in effect.

Final command names and schemas remain contract work. A plain client-side toggle or boolean
does not satisfy confirmation.

## Authorization

Mode decrease and mode increase are distinct semantic capabilities under ADR-019.

- A human principal may lower mode only within its authorized environment and session scope,
  but a valid lower request needs no additional confirmation, healthy dependency, or
  optimistic-version match.
- A reviewed machine principal may only apply the downward ceilings assigned to its named
  fault rules. It cannot increase requested or effective mode.
- Mode increase is human-only, scoped to the target session and mode, and requires the
  confirmation, presence, and precondition evidence defined above.
- An operator may request a higher ceiling or confirm clearing a proved recovery hold but
  can never assign the computed `effective_mode` directly.
- Authority to observe mode, lower mode, raise mode, approve content, resume from e-stop, or
  activate policy is independently grantable. None implies another.
- Concrete role names and capability bundles remain OPEN; the operator console cannot infer
  authority from a role label or button state.

An unauthorized caller is rejected and audited. "Downward transitions are always allowed"
means no operational precondition may block a valid scoped authority; it does not grant
anonymous or cross-scope callers permission to mutate a session. ADR-015's direct local stop
remains available independently of mode authorization.

## Recovery And Failure Behavior

- After actor restart or ownership transfer, PostgreSQL state is authoritative; Redis is not
  a recovery source. The new ADR-025 composite-fenced owner remains recovery-only, restores the
  lowest proven ceiling, and cannot increase or resume until the source-serialized activation
  barrier, commands, four-record effects, canonical timers, restrictions, lost-tail disposition,
  and sealed rig state reconcile.
- Missing or contradictory requested/effective mode, degradation, policy, presence, or epoch
  state recovers at Mode 0.
- An unresolved previous degradation restores its lower ceiling and upward-recovery hold.
- Late success from a provider, safety layer, operator, TTS gateway, or stage host cannot
  advance work authorized by a superseded mode/epoch.
- Audit or outbox failure never preserves higher autonomy. Safe downward state is held and
  durability is retried.
- Upward transitions fail closed when authorization, preconditions, audit persistence, or
  confirmation evidence is unavailable.
- Network or state-channel recovery never raises mode.

## Audit And Observability

Every requested or effective mode change records:

- command, idempotency, trace, session, and actor identities;
- initiating human/system principal and authorization-policy version;
- old/new requested mode and old/new effective mode;
- degradation cause set and computed ceilings;
- exact resolved-configuration snapshot, activation and definition/set eligibility
  transitions/epochs, and the policy, prompt, persona, model, and capability-matrix versions it
  selected;
- operator-presence lease generation without identity-provider tokens;
- precondition snapshot, confirmation identity, rationale, and rejection codes;
- affected turn/task identities and their cancellation/review/expiry outcomes;
- session/rig epoch and timestamps.

Required notifications include `ModeChanged`, `OperatorPresenceChanged`,
`SafetyLayerUnavailable`, and `FailClosedActivated` where applicable. Notifications describe
committed state and contain no restricted candidate text, viewer-memory content, secrets, or
credentials.

Those names remain inactive catalog proposals. `ModeChanged` is proposed as a stream-session
subject event under ADR-023. Operator-presence ownership is unresolved, and the safety/fail-closed
names must be split or assigned one durable session/capability aggregate and scope before
activation; a pure alert or health observation is telemetry, not a domain event. Commands and
restrictive controls remain separate OD-021 contracts.

Metrics and alerts cover time in each effective mode, attempted/rejected increases,
degradation count by cause, upward-recovery-hold age, operator-presence state, pending review
age, and any work rejected after a lower ceiling. Numeric alert SLOs remain OPEN.

## Enforcement

- The session actor is the sole writer of requested/effective mode state for its
  `StreamSession`.
- The policy engine computes session and per-work ceilings from versioned inputs.
- Versioned inputs resolve through the exact ADR-024 draft/version/eligibility/activation/snapshot
  model; mode cannot select `latest`, resolve an ambiguous scope or implicit deactivation
  fallback, or make stale activation/eligibility current.
- Input admission, scheduling, generation, safety decision completion, approval minting,
  media resolution, dispatch, stage-host queue acceptance, and immediate pre-playback each
  reject work whose mode/epoch authorization is no longer sufficient.
- `packages/safety` remains the only approval minter in every mode.
- Public TTS/media boundaries remain identifier-only in every mode.
- Primary, retry, rewrite, and fallback paths cross the same gate in every mode.
- Tool use remains unavailable in every initial mode.
- Mode commands are authorized server-side under ADR-019; UI visibility is not enforcement.
- Mode policy, transition code, event contracts, protected tests, and production defaults
  require human review.

No schema, policy default, runtime worker, console behavior, or migration is authorized by
this proposal.

## Acceptance Evidence

Acceptance of this ADR requires human review of the capability and degradation matrices.
Production enablement requires:

- exhaustive state-transition tests for requested/effective mode, degradation causes,
  presence, emergency latch, lifecycle, rig state, and recovery hold;
- property tests proving downward monotonicity, stop precedence, minimum-ceiling
  computation, no automatic upward transition, and no work grandfathering;
- authorization and confirmation tests for lower versus higher transitions;
- operator-presence expiry, revocation, uncertainty, and return tests;
- fault injection for every degradation row, including safety timeout with zero autonomous
  speech and provider fallback through the same gate;
- queued/in-flight/playing work tests across mode changes and emergency-stop races;
- connected and partitioned stage-host tests proving epoch rotation, old-queue eviction,
  presence/health-bounded task expiry, immediate pre-playback rejection, watchdog fallback,
  and absence of stale Mode 2 playout;
- category/surface-cap tests proving unknown content fails to Mode 0 and sponsor/controlled
  content never exceeds Mode 1;
- Mode 0 manual/canned-path tests proving common safety lineage and e-stop dominance;
- Mode 1 end-to-end rehearsal proving every generated candidate needs an operator terminal
  decision;
- Mode 2 rehearsal and red-team evidence proving only allowlisted low-risk work can
  auto-approve and operator absence immediately degrades;
- restart/recovery and incident-timeline reconstruction from PostgreSQL plus audit/outbox
  evidence;
- stale-owner, lease-expiry, forced-revoke, lost-command-response, and takeover tests proving
  downward action remains available, upward action remains fenced, and ambiguous dispatch forces
  current session-epoch/rig reconciliation;
- runbooks for every production-enabled degradation cause and rejected mode increase.

No response-time, presence, health, or degradation SLO passes until its numeric target is
approved and measured in the target environment.

## Consequences

- Autonomy becomes a reviewable capability contract rather than a UI preference.
- Safe decreases remain available during partial failure, while recovery requires a fresh
  human decision.
- Mode 2 carries substantial evidence, presence, and observability prerequisites; schedule
  pressure cannot waive them.
- Per-category ceilings reduce unnecessary session-wide shutdowns only when isolation can be
  proven.
- Session-runtime, operator-console, policy-default, and autonomy implementation remain
  blocked until this ADR and its OPEN decisions are accepted.

## Open Decisions

- OD-013: final mode names, complete capability matrix, complete fault-to-target matrix,
  category taxonomy/caps, and default requested/effective mode.
- Concrete role names and capability bundles for lower, increase, review, and presence:
  ADR-019.
- OD-035: numeric operator-presence authorization horizon, health/freshness windows, timeout,
  clock, and recovery-hold timing.
- OD-036: health SLI definitions, monitoring posture, alert thresholds/routes/response
  objectives, dashboards, and evidence freshness.
- OD-037/038: capacity/quota/cost warning, saturation, unknown-state, degradation target,
  protected reserve, drain, and recovery policy.
- OD-033 and ADR-023: exact `ModeChanged`, operator-presence, safety-layer, and fail-closed event
  contract/type split, subject/scope, ordering/completeness, classification/protection, producer,
  and compatibility profile.
- OD-034 and ADR-024: exact configuration families, draft/version and eligibility state,
  activation/deactivation/schedule scope/composition/epochs, snapshot, restrictive change,
  in-flight disposition, and forward rollback behavior.
- Whether upward changes may skip a level and whether any increase requires two-person
  approval.
- Whether prolonged operator absence in Mode 1 forces Mode 0.
- Exact interruption behavior for already playing work and segment priority under OD-014.
- ADR-025/OD-014: composite actor/ownership-row fencing, recovery-bound durable mode-command
  ingress, safe-direction/restrictive-control delivery, four-record effects, and closed
  recovery-only takeover/activation.
- Post-emergency requested/effective mode and resume reconciliation under OD-015.
- Mode-change command/event schemas, persistence constraints, and deployment rollback
  protocol.
