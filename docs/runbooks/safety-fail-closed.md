# Safety Fail-Closed Response

Status: Proposed operational runbook; implementation and production use pending

Readiness state: `Drafted` only; no rehearsal, target validation, or production authorization

Date: 2026-07-17

Sources: `AGENTS.md`, `vnova-review-handoff.md`, ADR-003, ADR-004, ADR-007, ADR-008,
ADR-010, ADR-011, ADR-015, ADR-016, ADR-017, ADR-018, ADR-019, ADR-020, ADR-025,
`docs/architecture/rehearsal-mode.md`, `docs/architecture/privacy-retention-model.md`

This document describes an intended incident workflow. It does not authorize runtime code,
policy defaults, provider configuration, schema changes, commands, endpoints, or production
operation while its governing ADRs and OD-027/OD-028 remain unresolved.

## Purpose And Scope

Use this runbook when VNova cannot prove a complete, current safety verdict or cannot prove that
an approved item remains authorized through media and playback. Its purpose is to preserve the
invariant:

> No safety verdict means no autonomous speech or broadcast presentation.

The workflow covers generation-output safety, input and broadcast-surface moderation, approval
lineage, policy availability, mode degradation, dispatch invalidation, and stage-host convergence.
It does not replace the local hard e-stop. If unsafe or unverifiable output is already playing, or
containment cannot be proved, the authorized operator uses the local hard-stop path immediately.

## Non-Negotiable Invariants

- Only `packages/safety` may mint `ApprovedResponse`.
- A missing, unavailable, timed-out, malformed, stale, or indeterminate safety result grants no
  authority.
- Primary, retry, rewrite, and provider-fallback candidates enter the same complete safety
  pipeline.
- Provider fallback paths pass through the same safety gate as primary paths.
- Public TTS and media interfaces accept `approved_response_id`, never raw generated text.
- Every external operation, including incident probes and recovery validation calls, has an
  explicit timeout bounded by the enclosing incident operation deadline.
- Candidate, approval, media, task, and playback deadlines are never extended during recovery.
- PostgreSQL is authoritative for durable session, turn, decision, approval, audit, and outbox
  state. Redis is transport only.
- Ordinary recovery may admit new session work only under the exact `open`
  `SessionNormalWorkAdmission` epoch. `draining` and `closed` are permanent reopen prohibitions;
  a lost admission/close tail becomes `draining(lost_tail_quarantine)`, never restored autonomy.
  No ordinary Turn, candidate, approval, media, task, effect, signing, or dispatch path may bypass
  that gate; only bounded evidence—including the separately typed, finite, non-widening
  `RecoveryProbe*` exception—restrictive action, and terminal non-advancing disposition remain
  available after it closes.
- A restrictive action may take effect before PostgreSQL recovers, but uncertainty can never
  approve, dispatch, resume, raise mode, or widen authority.
- Stage-host remains the sole `SpeechTask` consumer and independently checks authorization,
  integrity, epoch, replay identity, and expiry before playback.
- Ordinary logs, alerts, tickets, and incident chat contain no raw candidate text, full prompt,
  viewer-memory content, credentials, provider payloads, or identity-provider tokens.

## Trigger Conditions

Start this runbook when any of the following is observed or cannot be disproved:

| Trigger class             | Examples of qualifying evidence                                                                                                   | Immediate safety interpretation                     |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| Safety-layer availability | Required deterministic, model-based, or policy layer is unavailable, times out, is cancelled, or returns malformed/partial output | Verdict is indeterminate; fail closed               |
| Provider independence     | Generator and required model-based judge are the same or an unverifiable failure domain                                           | Required independent verdict is absent; fail closed |
| Policy integrity          | Active safety, authorization, surface, prompt, or capability version is missing, invalid, unknown, or cannot be loaded            | No current authorization; fail closed               |
| Approval lineage          | Candidate, terminal approving decision, selected pointer, approval, or expiry binding is missing or contradictory                 | Approval cannot be minted or consumed               |
| Surface authorization     | Final normalized/rendered/pronounced presentation digest differs from the moderated digest, or moderation is unavailable          | Affected surface presents nothing                   |
| Dispatch integrity        | Signature, audience, session, epoch, replay, media digest, or expiry check fails                                                  | Reject the task and treat the path as unsafe        |
| Recovery uncertainty      | PostgreSQL state is unavailable or conflicts with runtime, outbox, Redis, or stage-host state                                     | Hold the most restrictive known state               |
| Unexpected output         | Unapproved, stale, substituted, or otherwise unverifiable content appears to be playing or visible                                | Engage the appropriate immediate stop path          |

Numeric error rates, durations, and alert thresholds are deliberately not defined here. A single
integrity contradiction or missing required verdict is sufficient to fail closed; health-based
incident aggregation thresholds remain human-approved policy.

## Response Roles

These common runbook labels are responsibilities, not authorization grants. Before production
enablement, OD-027 and ADR-019 must map each label to accountable people, deny-by-default
capabilities, resource scope, environment, coverage, and separation-of-duty policy.

| Role                | Duties during this workflow                                                                                                          |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Incident commander  | Establish scope and timeline, assign owners, keep restrictive state in force, control phase progression, and own exit-gate evidence  |
| Safety lead         | Verify fail-closed containment, approval lineage, common-gate recovery, and zero unauthorized output                                 |
| Stage operator      | Observe the local result, engage hard stop when required, verify latch/epoch/queue/playback/clock state, and preserve local evidence |
| Service owner       | Perform read-only runtime, safety, provider, policy, persistence, and transport diagnosis within the assigned boundary               |
| Security lead       | Own signature, replay, authorization, credential, provider-integrity, or adversarial concerns                                        |
| Privacy/legal lead  | Own restricted-data handling, preservation, notification, and legal/privacy decisions                                                |
| Communications lead | Coordinate only approved internal, talent, platform, and public communications                                                       |
| Recorder            | Maintain the sanitized timeline, decisions, evidence locations, and unresolved findings                                              |

No investigator gains candidate reveal, viewer-memory, audit export, mode increase, emergency
resume, or policy activation authority merely by participating in the incident.
Any mode increase or emergency resume still requires a human principal with the distinct ADR-019
capability; assignment to a response role does not supply it.

## Immediate Containment

Perform these actions in safety order. Do not wait for complete diagnosis.

1. **Confirm the broadcast result.** Use independent local observation to determine whether
   speech, captions, overlays, alerts, scene text, usernames, or avatar actions are currently
   reaching broadcast. Do not trust a single cloud status channel.
2. **Stop unsafe output locally when necessary.** If unsafe or unverifiable output is playing,
   presentation state is unknown, or remote containment cannot be proved, engage the authorized
   local hard stop. It must cut the OBS audio source and flush the local playback queue even while
   the cloud is unreachable.
3. **Activate cloud fail-closed restriction.** Stop new autonomous admission, generation
   progression, automated terminal approval, media resolution, and dispatch for the affected
   scope. Drop or invalidate in-flight work that depended on the missing evidence.
4. **Lower authorization immediately.** Apply ADR-020's required Mode 0 ceiling for a required
   safety-layer failure or an affected-work Mode 0 ceiling for isolated surface moderation
   failure. Advance the session authorization epoch where the accepted control contract requires
   it, and prevent old-epoch queued work from remaining eligible.
5. **Use only approved neutral coverage.** Silence, an approved fallback scene, or separately
   approved canned material may cover the incident. A generated candidate, provider fallback,
   platform raw chat, or operator-entered text is never an emergency bypass.
6. **Preserve restrictive state during persistence failure.** If PostgreSQL or the outbox is
   unavailable, mark the process-local state as `uncommitted_restrictive`, continue denying work,
   and retry the authoritative state, audit metadata, and outbox transition as one bounded
   operation. Do not claim durable success until PostgreSQL commits it.
7. **Alert the required humans.** Surface the affected sessions, surfaces, safety capability,
   effective mode, rig state, and evidence identifiers. Do not include restricted content in the
   alert.

If any containment action times out, its success is unknown. Retain or strengthen the restriction
and escalate; never assume a timeout means the action completed.

## Read-Only Diagnosis

Diagnosis must not mint an approval, complete a candidate decision, alter provider selection,
clear a degradation cause, replay an event, resume output, or raise mode.

### Establish Scope

- Identify affected environment, talent, stream sessions, segments, turns, candidates, surfaces,
  rigs, and provider capability profiles by opaque ID.
- Record the earliest observed anomaly and each source clock. Preserve original local timestamps
  and record any correction separately.
- Determine whether the issue is isolated to one work item, surface, provider capability, policy
  version, session, rig, or environment.
- Confirm current requested/effective mode, active degradation causes, emergency latch, session
  authorization epoch, exact protected recovery/ownership composite actor fence/phase/lease,
  ownership-row transition, normal-work admission status/epoch/closure prefix, recovery
  barrier/lost-tail disposition, sealed rig binding, and operator-presence state from
  authoritative sources.

### Inspect The Safety Chain

For each affected candidate or presentation, verify by identifiers and digests:

1. the generation attempt reached a complete, schema-valid terminal result before deadline;
2. the candidate belongs to that attempt and turn and was not expired or cancelled;
3. deterministic evaluation completed under the expected policy version;
4. model-based classification completed under an eligible independent provider profile;
5. the policy engine returned a determinate outcome for the category, severity, mode, and
   surface;
6. any operator action has an authorized `operator_id`, decision provenance, and exactly one
   terminal `SafetyDecision`;
7. an approving decision is the selected candidate's decision and backs no more than one
   `ApprovedResponse`;
8. surface authorization binds the exact final normalized/rendered/pronounced digest;
9. every downstream expiry is equal to or earlier than the candidate deadline;
10. media and `SpeechTask` integrity, session, epoch, replay, ordering, and time bindings agree.

An absent or contradictory link is a finding, not a prompt to reconstruct authority manually.

### Inspect Availability And Failure Evidence

- Review normalized attempt outcomes, explicit timeout/deadline evidence, cancellation, late
  results, malformed/partial output, quota state, and bounded retry/fallback lineage.
- Confirm that SDK-internal retries did not obscure network attempts or exceed the outer
  deadline.
- Confirm generator/judge vendor independence for the exact active and fallback profiles.
- Confirm that all successful generation fallback outputs became new candidates and entered the
  same safety pipeline.
- Inspect PostgreSQL aggregate, decision, approval, audit, and outbox evidence. Inspect Redis only
  for transport health, lag, and duplication; never use it to reconstruct truth.
- Inspect stage-host acceptance, queue, pre-playback, playback, epoch, replay, media-integrity,
  clock-uncertainty, and watchdog outcomes. A transport acknowledgement is not playback evidence.

## Data Minimization

Ordinary diagnosis uses IDs, canonical digests, classifications, policy/profile versions,
normalized reason codes, timing, usage counts, and outcomes. Raw candidates and full prompts
remain redacted by default. If content inspection is indispensable, use the separately authorized,
purpose-bound, time-bounded restricted-reveal workflow with a logged reason; do not paste revealed
content into this runbook's evidence packet.

## Recovery Procedure

Recovery is a new authorization decision, not reversal of fail-closed state.

1. **Select the restored path.** Identify the exact accepted safety, authorization, provider,
   prompt, surface, and capability versions intended for recovery. Do not substitute an
   unreviewed vendor, model, rule set, or default.
2. **Prove layer health independently.** Validate deterministic rules, independent model-based
   classification, policy evaluation, surface moderation, and identifier-only media behavior
   using approved, bounded probes or rehearsal fixtures. Every external probe has an explicit
   timeout and records a normalized result without raw content. These synthetic health checks are
   not session-bound `RecoveryProbe*` authority. If a call classifies a specific session effect,
   dispatch, rig, or lost-tail ambiguity, it must instead use the distinct four-role
   active+draining-prefix or recovering+recovery-attempt/source-bound lineage below.
3. **Prove failure behavior.** Re-run the relevant timeout, malformed-result, provider-correlation,
   and fallback-through-the-same-gate rehearsal cases. A healthy success probe alone is
   insufficient.
4. **Reconcile durable state.** Ensure every restrictive state, audit record, and outbox
   notification has committed in PostgreSQL. Resolve transport backlog from PostgreSQL under the
   offline reconciliation runbook; do not infer history from Redis.
5. **Discard incident-era work.** Expired, cancelled, old-epoch, failed-closed, indeterminate,
   partially evaluated, playing-or-in-doubt, or otherwise unverifiable work is not revived. New
   output starts with new attempts and current authorization context.
6. **Reconcile and seal the rig.** Establish the exact authenticated rig/boot binding, emergency
   state, authorization epoch, empty or fully reconciled queue/journal cursor, acceptable clock
   evidence, artifact integrity, and watchdog health while stage host remains in a sealed
   restrictive recovery hold. Persist its exact hold receipt; any later local fact invalidates
   the evidence.
7. **Prove current cloud recovery authority.** Freshly prove the exact active recovery/ownership
   composite fence through ADR-025's shared ownership-row linearization point. If ownership
   changed or remains `recovering`, complete the source-serialized activation barrier with
   unchanged immutable cut-time source/schedule-cursor snapshots and invalidation revisions plus
   the sealed rig receipt; harmless post-cut operational-cursor progress is excluded and cannot
   starve activation. Every recovery-attempt-bound probe write advances invalidation; activation
   requires all such probes terminal/non-widening and each enabled-scope source ambiguity
   resolved or explicitly capability-disabled. Prove every affected PITR/RPO tail, including the normal-work
   admission/close cut, complete or explicitly quarantined. A restored `open` admission with an
   unproven later tail becomes coherent `Ending`/`draining(lost_tail_quarantine)` under the new
   recovery generation with a proven or explicitly unresolved target. Restored
   `draining(normal_closure)` gains a monotonic lost-tail overlay, while restored atomic `closed`
   remains closed/ownerless. Only an exact still-`open` admission epoch may activate ordinary
   work; a draining successor may only safely classify its fixed prefix and may complete the
   atomic final close only after accountable tail/target resolution, every admitted probe
   terminal, and each bound source ambiguity resolved/permanently safe-quarantined/accountably
   disposed. A terminal probe may remain truthfully `unknown`; no recovered capability may depend
   on inferred absence.
8. **Activate the exact binding separately.** After the cloud barrier, perform the authenticated
   stage-host binding activation for the exact accepted epoch and sealed receipt. Reconcile its
   durable acknowledgement before any audience task; an unknown/unsealed rig remains disabled.
9. **Clear only proved causes.** Removing a fault may remove its degradation cause, but it does
   not automatically raise `effective_mode`.
10. **Request deliberate recovery.** Any upward mode transition follows ADR-020: current qualified
    human presence, scoped authority, fresh preflight, confirmation, rationale, audit persistence,
    and all target-mode preconditions. Emergency resume, if applicable, follows its separate
    confirmation and reconciliation path.
11. **Observe new work.** Validate the first newly authorized work through candidate, complete
    safety, approval, media, signed task, stage-host acceptance, and actual playback evidence.
    Re-enter containment on any mismatch.

## Recovery Exit Gates

The incident may leave active containment only when all applicable gates are evidenced:

- Before the affected autonomous capability is recovered, its trigger and scope are understood,
  the failed control is remediated, and the relevant negative case passes. If the cause remains
  unknown, the incident may transition only to an explicitly disabled or safe-stopped handoff;
  the affected capability is not considered recovered or eligible for autonomous output.
- All required safety layers and their independent failure domains are healthy for the enabled
  scope.
- The active policy/profile/configuration identities match protected reviewed versions.
- PostgreSQL contains coherent restrictive, audit, decision, approval, mode, epoch, and outbox
  state; no recovery claim depends on Redis retention.
- the exact active composite actor fence, shared ownership-row/post-lock lease proof, and any
  required closed recovery activation barrier are freshly evidenced;
- the exact normal-work admission status/epoch is current; ordinary recovery is `open`, while any
  draining/closed session has accepted no post-begin-close-cut normal work and is being completed
  or kept quarantined without reopening; any lost-tail overlay/target ambiguity remains visible
  and blocks final close; every session-bound recovery probe uses a distinct four-role lineage,
  exact dual binding, finite bounds, zero-attempt/current-successor terminalization without
  resend, and no widening, while any unresolved bound source ambiguity remains a blocker;
- every affected recovery tail is zero-loss proven or explicitly `lost_tail_unknown` and
  quarantined, with no recovered capability authorized by absence;
- No incident-era candidate, approval, media authorization, or task has been revived or had its
  deadline extended.
- Stage-host is authenticated, on the current epoch, locally safe, clock-valid, queue-reconciled,
  and able to reject stale/tampered work; its sealed hold receipt is bound to the cloud recovery
  evidence and the exact binding-activation acknowledgement is durable.
- Required timeout and fallback-through-gate rehearsal evidence passes for the exact recovery
  configuration.
- Alerts and operator views agree with authoritative state without exposing restricted content.
- Any mode increase or emergency resume has fresh human authorization, confirmation, reason where
  required, and durable audit evidence.
- The incident commander and required safety, stage, privacy/legal, or security reviewers have
  recorded their disposition.

If a gate cannot be proved, remain in the lower mode or stopped state.

## Evidence Packet

Record:

- incident, environment, session, turn, candidate, decision, approval, media, task, rig,
  connection, epoch, policy, profile, and trace identifiers;
- original and corrected timestamps, clock samples, uncertainty, and evidence source;
- normalized trigger/reason codes and affected safety layer or surface;
- requested/effective modes, degradation causes, emergency state, and every containment outcome;
- explicit timeout, cancellation, retry, fallback, and late-result outcomes;
- PostgreSQL transaction/outbox identities and Redis transport observations;
- stage-host queue, replay, integrity, watchdog, and actual playback outcomes;
- human principals, evaluated capabilities, confirmations, reasons, and decision timestamps;
- rehearsal scenario manifest, configuration versions, deterministic seed, and artifact hashes;
- unresolved questions, accepted residual risk, follow-up owner, and review decision.

The evidence packet references restricted records by ID and digest. It contains no raw candidate,
full prompt, viewer-memory value, secret, credential, bearer token, provider payload, synthesized
media, or rights evidence.

## Escalation

Escalate without weakening containment when:

- output may have reached broadcast without a provable approval or surface authorization;
- local stop, mute, queue flush, or rig state cannot be confirmed;
- the same identity has conflicting canonical content, a signature/replay check fails, or
  authorization evidence may be forged;
- restricted content, personal data, secrets, credentials, or provider payloads may have leaked;
- PostgreSQL evidence is missing, corrupt, or contradictory;
- generator/judge independence cannot be established;
- the provider or safety failure spans multiple sessions or environments;
- recovery would require an unreviewed provider, policy, schema, command, threshold, or bypass.

Route privacy, security, talent/rights, provider, and legal escalation through their
human-approved channels. Exact contacts, paging routes, severity labels, response targets, and
regulatory notification decisions remain OPEN and must not be inferred by implementation.

## Required Rehearsal Scenarios

Before production use, exercise this runbook with deterministic time and the production-equivalent
contracts:

- each safety layer times out, fails, returns malformed output, and becomes indeterminate;
- actor pause, lease expiry, revoke, and takeover during safety evaluation or approval minting,
  proving stale composite fences, ownership-row races, PITR lost tails, and late observations
  create no approval or dispatch;
- generator and judge profiles become correlated or unverifiable;
- primary generation fails, fallback succeeds, and the new candidate crosses the same full gate;
- generation succeeds but safety fallback is unavailable, producing zero autonomous speech;
- policy or capability version disappears or changes during evaluation;
- PostgreSQL/outbox fails during fail-closed activation, proving immediate restrictive actuation
  and no resume before durable reconciliation;
- Redis is empty or unavailable while reconstruction succeeds only from PostgreSQL;
- a surface's rendered or pronounced digest changes after moderation;
- a safety failure occurs with old-epoch work queued at a connected and partitioned stage-host;
- a task reaches immediate pre-playback with expired, wrong-epoch, replayed, or substituted
  authorization;
- local hard stop succeeds while runtime, Redis, provider, identity, and console paths are
  unreachable;
- operator presence expires and a return does not automatically restore Mode 2;
- ordinary logs, alerts, traces, and the final incident packet are scanned for prohibited content;
- the proven-complete incident horizon is reconstructed from PostgreSQL plus minimized
  stage-host evidence, while every unproven PITR/RPO gap remains explicitly
  `lost_tail_unknown` rather than a fabricated complete timeline.
- PITR loses a session admission/close cut, proving restored `open` becomes coherent
  `Ending`/`draining(lost_tail_quarantine)`, restored `draining(normal_closure)` gains the
  monotonic overlay, restored atomic `closed` remains closed/ownerless, no case admits
  command/input/timer/Turn work, and unresolved tail/target or rig/audience disposition blocks
  final close.
- Session-bound recovery-probe intent/attempt/first-byte/response/disposition crash cuts under
  both exact bindings, including zero-attempt and current-successor terminalization without
  resend, finite-bound rejection, terminal-unknown evidence versus separately classified source
  ambiguity, activation invalidation, no widening/absence/replay authority, and close rejection
  for a nonterminal probe or unresolved bound source.

Each scenario must assert zero unauthorized speech or presentation, the expected lower-mode or
stopped state, durable evidence, and absence of prohibited content.

## OPEN Values And Decisions

Human approval is required for:

- concrete incident role mappings, separation of duties, escalation contacts, and severity model;
- OD-027 operational command, coverage, communications, exercise, evidence-freshness, and runbook
  authorization decisions;
- OD-028 adversary assumptions, independent validation, and residual-risk authority;
- exact timeouts, outer deadlines, health windows, retries, alert thresholds, and response SLOs;
- generator/judge vendor pairing and the definition of an independent failure domain;
- provider profiles, models, regions, residency, privacy terms, synthetic-health probe design,
  and session-bound recovery-probe allowlist/binding/bounds/source-disposition design;
- safety/category policy, rewrite cap, manual-review TTL, candidate TTL, and surface rules;
- stage-host protocol security, authorization horizon, clock tolerance, watchdog, and e-stop SLO;
- restricted-data reveal and evidence-retention policy;
- mode recovery, operator-presence, confirmation, and emergency-resume requirements;
- OD-014/029/034/037 normal-work admission/closure drain, lost admission/close-tail quarantine,
  physical record, and bounded drain/final-close decisions;
- schema/migration design and the canonical non-event command/wire contracts.

No placeholder, fixture value, vendor SDK default, or library default may become a production value
without the required protected human decision.
