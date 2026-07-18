# ADR-003: Stream Session, Segment, And Turn Lifecycle

Status: Proposed

Date: 2026-07-17

Sources: `AGENTS.md`, `vnova-review-handoff.md`, ADR-023, ADR-024, ADR-025

## Context

VNova operates a continuous broadcast. A chatbot-shaped request/response record cannot represent scheduled segments, idle material, operator interventions, competing candidates, expiry, interruption, recovery, or the independent state of the local rig.

The domain model must establish a stable lifecycle before persistence, runtime workers, event payloads, or migrations are implemented. It must also avoid accidental event sourcing: authoritative state lives in PostgreSQL rows, while outbox events notify consumers and support reconstruction.

## Decision

`StreamSession` is the aggregate and serialization boundary for one live or rehearsal broadcast.
`session-runtime` owns one logical actor per `StreamSession`; all normal commands that mutate the
aggregate are serialized by the exact active PostgreSQL-authoritative
`(recovery_generation, ownership_generation)` composite actor fence defined by ADR-025 and
committed through the shared ownership-row conflict plus optimistic concurrency protection. A
process, route, heartbeat, read predicate, or correct aggregate version alone is not ownership.

The aggregate contains or references:

- one optional versioned `StreamPlan`;
- an ordered set of `Segment` records;
- zero or more `Turn` records;
- orthogonal session control state for lifecycle, requested/effective operating mode, emergency latch, and rig connectivity;
- the exact immutable `ResolvedConfigurationSnapshot` proposed by ADR-024, containing policy,
  prompt, persona, scheduler, version/set identities, activation and eligibility epochs, and
  other lineage needed to explain decisions without defeating current restrictive state.

Operating modes and emergency-stop semantics remain separate decisions in ADR-020 and ADR-015. A mode is not a session lifecycle state, and an e-stop is not a safety verdict.

## Stream Plan And Segment

`StreamPlan` describes intended broadcast structure without making future work executable by itself. A `Segment` is a versioned planned or ad-hoc unit such as opening, free talk, game play, sponsor read, intermission, or closing.

Each segment records its category, ordering identity, planned time window, interruption policy, autonomy ceiling, and provenance. Exact scheduling priorities and category rules remain OPEN. Sponsor or legally constrained material cannot receive an autonomy level above its approved category cap.

## Turn And Trigger

A `Turn` is one schedulable unit of broadcast work derived from one trigger. It is not one
provider attempt: one turn may own many immutable generation attempts and candidates before it
terminates. The trigger is a tagged value with these initial variants:

- `viewer_message`;
- `operator`;
- `scheduled_segment`;
- `idle_filler`;
- `system`.

Trigger-specific payloads are versioned contracts. Viewer input and spoken usernames cross input moderation before becoming eligible. A trigger never embeds secrets, provider credentials, or unrestricted memory/audit content.

Every turn records an authoritative `not_after` derived from the trigger policy version. Retry, rewrite, fallback, approval, synthesis, reconnect, or queueing may shorten that deadline but never extend it.

Scheduled and delayed triggers also follow ADR-025's canonical nominal-occurrence key,
materialization-cursor CAS, composite-fence/current-claim token, single-admission, and terminal
firing-disposition model. Process-memory timers and Redis delay are wake-up aids only. A missed
occurrence never creates an unbounded materialization or catch-up burst.

## Candidate And Approval Lineage

One `Turn` owns `0..N` `GenerationAttempt` records and `0..N` `CandidateResponse` records. A turn
may reject, cancel, or expire before generation admission; every attempt and candidate that does
exist belongs to exactly one turn.

- Every policy-level provider call, retry, fallback, or rewrite starts a new immutable
  `GenerationAttempt` with provider-neutral request provenance, deadline, timeout, and terminal
  outcome. It owns one ADR-025 `EffectIntent`; reviewed transport replay under the same semantic
  request/idempotency identity creates another send-authorized `EffectAttempt`, not another
  candidate-producing domain attempt.
- A successful attempt produces exactly one immutable candidate. A timeout, cancellation, or provider failure produces no candidate and cannot enter safety evaluation.
- Every candidate references the successful attempt that produced it.
- A terminal `rewrite_requested` decision carries `rewritten_from_candidate_id` equal to the
  source candidate it judged. The new attempt references that decision, and a successful child
  candidate carries the same `rewritten_from_candidate_id`; lineage cannot contain cycles or
  conflicting parent references.
- Every candidate has at most one terminal `SafetyDecision`; exactly one exists only when
  evaluation completes with a determinate `approved`, `rejected`, or `rewrite_requested` outcome.
  Operator-review queueing remains a nonterminal evaluation status.
- A candidate may instead terminate as expired, cancelled, or failed-closed before evaluation completes; those outcomes create no `SafetyDecision` and can never mint approval.
- `selected_candidate_id` is optional until selection and may reference only a candidate owned by the same turn.
- Approval minting additionally requires the selected candidate's approving safety decision.
- One approving safety decision can back at most one `ApprovedResponse`.
- Candidate and approval deadlines preserve the authoritative non-extension rule.

Manual approval, rejection, or rewrite request completes evaluation by recording the candidate's terminal safety decision with operator provenance. It is not a parallel type or bypass.

## Handoff Reconciliation And Canonical Vocabulary

The binding handoff says each candidate has one `SafetyDecision`, while it also requires fail
closed when no safety verdict exists. Creating an artificial decision for a timeout,
unavailability, expiry, or cancellation would falsely turn missing authority into a verdict. This
ADR therefore makes the cardinality precise:

- `CandidateResponse : SafetyDecision` is `0..1`;
- it is exactly `1` only when evaluation reaches a determinate terminal decision;
- it remains `0` when work terminates as `expired`, `cancelled`, or `failed_closed`;
- a zero-decision terminal candidate is permanently ineligible for selection or approval.

The canonical terminal `SafetyDecision` outcomes are `approved`, `rejected`, and
`rewrite_requested`. Words such as blocked, denied, or rewrite in prose map to those canonical
outcomes and do not create additional enum values. Operator review is a nonterminal evaluation
state, not a decision outcome.

The rewrite relationship has three distinct records:

1. the source candidate's terminal `rewrite_requested` decision, carrying the source
   `rewritten_from_candidate_id`;
2. a new immutable attempt referencing that decision; and
3. only on successful generation, a child candidate referencing the same source candidate.

A failed rewrite attempt produces no child candidate and does not change the source decision. A
later permitted rewrite attempt is another immutable attempt under the same capped policy and
deadline. Exact serialized field names remain subject to the protected contract review, but the
three-record relationship and equality constraints are not optional.

## Lifecycle Semantics

The authoritative state model is defined in [session-turn-state-model.md](../architecture/session-turn-state-model.md). Its controlling rules are:

1. emergency latch dominates every mode and turn transition;
2. expiry and explicit cancellation dominate nonterminal work;
3. no safety verdict or an indeterminate verdict terminates the autonomous path fail-closed;
4. only an approved selected candidate can mint an `ApprovedResponse`;
5. only approved, unexpired, integrity-bound work can enter media and dispatch stages;
6. terminal states never transition back to active states;
7. resume creates new authorization context and never revives flushed or expired work.

## Commands, Idempotency, And Concurrency

Every externally initiated command carries a protected submission recovery generation/token,
idempotency key, principal/trusted-source identity where applicable, stream-session identity,
expected aggregate version, command deadline, and explicit timeout at the transport boundary.
ADR-025 separates semantic digest from volatile authorization provenance and durable receipt from
terminal domain outcome, with append-only current authorization observations.

- Repeating the same current-generation scope/key/semantic command returns the original outcome
  after current lookup authorization.
- Reusing a key with different content is rejected and audited.
- A stale/unknown submission generation or lost-tail receipt absence requires reconciliation; it
  is not accepted as a fresh normal command.
- `control-api` cannot report acceptance until session-runtime has durably recorded the command
  intent, receipt, and initial authorization observation; a transport timeout is an unknown
  observation and is recovered by receipt query or same-intent retry.
- Every normal command receipt/authorization refresh/claim/execution, input promotion, timer
  path, Turn admission, ordinary effect intent/send/advancing application, and other ordinary
  candidate/approval/media/task/dispatch progression validates the exact open normal-work
  admission epoch through the shared source-row CAS.
- The exact current active composite actor fence serializes normal command execution. Every
  authorization append advances/CASes its per-command lineage revision, and execution rejects a
  concurrent change or older/incomparable allow under ADR-019/025.
- PostgreSQL optimistic concurrency plus ADR-025's shared ownership-row conflict, post-conflict
  lease check, and fixed lock order prevent split-brain commits; any one alone is insufficient.
- Deadline passage makes a command permanently ineligible before its one terminal
  expired/failed-closed disposition is writable.
- State mutation, audit metadata, and outbox notification commit atomically when their governing ADR allows persistence.
- Approval progression and session-owned external effects use ADR-025 intent-before-effect,
  remaining-lease-budget, idempotency, current-owner revalidation, and late-result fencing.

Session closure first atomically transitions the nonterminal lifecycle to `Ending` with a
resolved requested terminal target/cause, moves the monotonic admission gate `open -> draining`,
and cuts a committed prefix across every normal input/Turn source. New normal commands are
deterministically not accepted, recurring timer cursors freeze without future occurrence rows,
raw observations cannot become eligible work, and no ordinary
Turn/candidate/approval/media/task/effect/signing/dispatch path advances. The actor or recovery
successor terminalizes or safely classifies the fixed prefix in bounded transactions. `Ended`,
`Cancelled`, and `Failed` are terminal targets, not direct pre-drain edges: one final-close
transaction requires the target resolved, every separately typed source-bound recovery-probe
lineage terminal/non-widening, and every bound source ambiguity resolved, permanently
safe-quarantined, or accountably disposed; it atomically commits that session terminal value,
drain evidence, admission `closed`, ownership-generation advance, owner/lease clear, and ownership
`closed`. A terminal probe may remain truthfully `unknown`; the finite read-only/restrictive probe
exception adds evidence only, and no intermediate state can reopen or strand accepted pending
work.

## Recovery

After actor restart, ownership transfer, or process failure, every new process generation first
enters ADR-025's recovery-only phase. It restores authoritative rows, durable commands, canonical
trigger occurrences/claims, effect intents/attempts/response observations/application
dispositions, distinct recovery-probe lineages, normal-work admission/closure-drain state,
dispatch ambiguity, and pending work from PostgreSQL. It activates only through a
source-serialized recovery cut with immutable cut-time
frontier/cursor snapshots, unchanged invalidation revisions, exact open admission epoch, every
recovery-attempt-bound probe terminal/non-widening, each enabled-scope source ambiguity resolved
or explicitly capability-disabled, and sealed stage-host receipt. Every such probe write plus
ambiguity/restriction advances invalidation. Harmless post-cut ingress may advance only a
separate operational cursor excluded from activation CAS.
Redis retention, consumer offsets, process-memory timers, or cached lease state never define
recoverability.

Recovery re-evaluates deadlines, emergency latch, effective mode, rig epoch, and idempotency records before work resumes. Work whose safety, approval, epoch, or expiry cannot be proven is terminated fail-closed.

If prior signing, dispatch, restrictive-control, or playout state is or may be ambiguous,
recovery advances the session authorization epoch and reconciles the exact stage host before the
new actor becomes active. Ownership generation and session authorization epoch remain separate.

After PITR/nonzero or unknown RPO, absence of an admission-close cut, command, effect, timer, or
restriction inside an unclosed tail is not evidence of nonoccurrence. A restored `open` admission
state atomically becomes `draining(lost_tail_quarantine)` while its nonterminal lifecycle enters
`Ending`; a target proven inside the trusted recovery horizon is preserved, otherwise the
conceptual `unresolved_lost_tail_target` blocks final close pending OD-029/034 disposition. A
restored `draining(normal_closure)` preserves its cause/fixed prefix and receives a monotonic
lost-tail overlay with the same stronger close gate. A restored atomic `closed` state remains
closed and ownerless. The affected scope never gains same-session reopen, normal command
reacceptance, effect replay, timer rematerialization/catch-up, Turn admission, or audience
enablement; the gates permit only accountable disposition and atomic final close.

## Events Are Notifications

Turn and session rows are authoritative state-machine records. Under Proposed ADR-023, an event
for their session-owned transition uses the stream-session aggregate subject, catalog-fixed
primary session scope, and the committed session aggregate version plus deterministic event
index. Turn, attempt, and candidate identities remain typed lineage/correlation unless a future
accepted aggregate model gives them independent ownership.

Versioned outbox events describe committed transitions for consumers, audit correlation, and
timeline reconstruction. They are not an excuse to reconstruct primary state from Redis or to
duplicate restricted candidate, prompt, viewer-memory, or media content into the event stream.

## Required Verification

- State-transition table tests including every illegal edge.
- Property tests for terminal-state closure, deadline non-extension, attempt/candidate cardinality, lineage acyclicity, and same-turn selection.
- Concurrency tests for duplicate commands, conflicting versions, durable-receipt response loss,
  key-versus-semantic-digest conflict, authorization-observation dedupe/lineage CAS/precedence/
  deadline, actor pause/restart, lease expiry, ownership-row/revoke ordering, stale composite
  fence, PITR, ownership transfer, every command/input/timer/Turn/ordinary-effect/candidate/
  approval/media/task/dispatch progression versus begin-close, bounded evidence/terminal non-advancing
  pre-close drain, atomic `Ended`/`Cancelled`/`Failed` final close, restored
  `open`/`draining(normal_closure)`/atomic-`closed` lost-tail cases, lifecycle/admission-axis
  coherence, monotonic quarantine overlay, and unresolved-target blocking.
- Ordinary external-effect crash-boundary tests for intent-before-send, remaining lease horizon,
  send-authorization-before-byte, response-observation-before-application, possibly-sent
  outcomes, provider idempotency/query behavior, late results, signing/dispatch fencing, and
  recovery-only takeover, plus separately typed recovery probes under active-draining-prefix and
  recovering-attempt bindings with finite bounds, all four crash cuts, non-widening terminality,
  and negative evidence never proving absence/replay authority.
- Durable timer tests for canonical occurrence uniqueness, materialization-cursor races,
  current-active materialization fencing, recovering-owner no-create/no-cursor-advance,
  expired-claim/reclaim fencing, one turn admission, one terminal firing disposition, missed
  windows, clock uncertainty, takeover, bounded materialization/catch-up, cursor freeze, and no
  post-begin-close-cut occurrence/cursor/storage growth.
- One-turn/many-attempt/many-candidate tests covering provider failure, timeout, retry, fallback, rewrite, selection, rejection, and expiry.
- Fail-closed recovery tests with missing decisions, unknown epochs, stale candidates, and unavailable safety state.
- Snapshot-pinning tests across activation or eligibility change, retry, fallback, restrictive
  transition, restore, and definition/set withdrawal.
- Session-subject, complete event-contract/framing, aggregate-version/event-index,
  multiple-event, filtered expected subsets, missing-tail/whole-transition manifest/high-water,
  cross-lane reorder, restrictive protection overlay, and PostgreSQL reconciliation tests under
  accepted ADR-023.
- Reconstruction tests proving PostgreSQL state plus audit/outbox metadata explains the synthetic session timeline.

## Consequences

- Runtime and schema implementation remain blocked until this ADR and its dependencies are accepted.
- The model supports continuous programming, not only viewer-message replies.
- Multiple candidates and independent control-state axes increase schema detail but remove ambiguous recovery behavior.
- ADR-004, ADR-015, ADR-020, ADR-023, ADR-024, and ADR-025 may refine delivery, emergency, mode,
  event, configuration, ownership, command, effect, timer, and recovery behavior without
  collapsing those concerns into the turn state machine.

## Open Decisions

- ADR-025 acceptance or replacement for PostgreSQL-authoritative actor ownership, durable command
  ingress, effect fencing, durable timer occurrence, and recovery-only takeover: OD-014.
- Trigger taxonomy/eligibility, generation retry/fallback policy, rewrite limits, segment
  priority/interruption, and per-family catch-up policy: OD-014.
- Trigger-specific TTL, deadline, timeout, scheduler-budget, and clock values: OD-035.
- Numeric lease, takeover, timeout, deadline, and recovery-hold timing: OD-035.
- Command/effect/timer queue, claim, scan, retry, fairness, reserve, and recovery-drain bounds:
  OD-037.
- Exact mode capabilities and degradation targets: OD-013.
- E-stop scope, resume authority, and partition reconciliation: OD-015.
