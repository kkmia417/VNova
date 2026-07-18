# ADR-015: Layered Emergency Stop

Status: Proposed

Priority: P1

Date: 2026-07-17

Sources: `AGENTS.md`, `vnova-review-handoff.md`, ADR-003, ADR-008, ADR-016, ADR-025

This ADR is non-binding while its status is `Proposed`. E-stop implementation remains
prohibited until protected human review accepts this ADR or an explicit replacement.

## Context

VNova can continue producing or playing broadcast output while the cloud, operator console,
local rig, or the link between them is failing. A single cloud command cannot be the only
emergency control because the final audio and scene act occurs on the local streaming PC.
Conversely, cutting local audio alone is insufficient if the cloud continues generating,
synthesizing, and dispatching stale work that could play after reconnection.

Emergency stop is therefore a distributed safety protocol, not a UI button, a
`SafetyDecision`, a mode value, or a normal turn transition. Its stop path must favor
cessation over coordination, while its resume path must favor proof and reconciliation over
availability.

## Decision

VNova will implement two independently assertable stop layers:

1. **Local hard stop**, owned by `stage-host`, cuts the OBS audio source, flushes local
   playback, and rejects further playout under the invalidated authorization epoch. It is
   reachable through a direct local channel and a physical hotkey and does not depend on
   cloud connectivity.
2. **Cloud freeze**, owned by the `StreamSession` actor in `session-runtime`, halts new
   scheduling and generation, cancels or terminally drops in-flight work, blocks synthesis
   and dispatch, and invalidates authorization issued before the stop.

The effective emergency state is stopped when either layer is asserted, when the layers
cannot be reconciled, or while resume is pending. A stop assertion is monotonic until a
separate, confirmed resume protocol proves that every required layer is safe to clear.

The emergency latch is an orthogonal `StreamSession` control axis. It dominates requested
mode, effective mode, turn progress, queue progress, and ordinary optimistic-concurrency
success. It does not alter the meaning of a text-safety verdict and is not represented in the
`SafetyDecision` enum.

## Emergency State Model

The authoritative logical states are:

| State            | Meaning                                                                                                | Output permission                                                                                                            |
| ---------------- | ------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| `clear`          | No local or cloud assertion is known, epochs agree, and no resume is pending.                          | Determined by all other safety, mode, lifecycle, and rig checks.                                                             |
| `engaged`        | At least one stop layer is asserted, a partition leaves the state uncertain, or reconciliation failed. | No normal speech/media/avatar playout or autonomous pipeline progress; only ADR-015 safety-control effects remain permitted. |
| `resume_pending` | An authorized operator has initiated resume, but confirmation or reconciliation is incomplete.         | Same as `engaged`; this is never a partially resumed state.                                                                  |

Permitted transitions are:

- `clear -> engaged` on any valid local, cloud, operator, or policy-authorized automatic stop
  assertion.
- `engaged -> engaged` for duplicate or additional stop assertions.
- `engaged -> resume_pending` only after an authorized resume request with a non-empty
  reason and a successful preflight.
- `resume_pending -> engaged` on a new stop assertion, failed or stale precondition,
  timeout, partition, identity change, an unexpected or challenge-unbound epoch change, or
  explicit abort.
- `resume_pending -> clear` only after explicit confirmation and all cloud/local
  reconciliation checks succeed.

`clear -> resume_pending`, `clear -> clear` through a resume command, and any direct
`engaged -> clear` transition are invalid. A terminal turn or flushed task is never revived
by resume.

Local and cloud assertion provenance is retained separately even though the operator sees
one effective emergency state. Clearing one assertion never masks another active or unknown
assertion.

## Stop Command Semantics

The semantic command is `EngageEmergencyStop`. Final wire and API names remain contract work,
but every representation must preserve these rules:

- Stop is one click or one physical action.
- Stop is idempotent.
- Stop has no confirmation dialog, challenge, reason requirement, or optimistic-version
  rejection.
- A stale aggregate version is recorded for diagnostics but never prevents an otherwise
  authenticated and authorized stop from taking effect.
- A local hotkey or direct local command takes local effect before attempting cloud
  coordination.
- A cloud command freezes the authoritative session immediately and attempts local hard-stop
  delivery through a channel independent of console state streaming.
- E-stop must not depend on the operator console WebSocket or SSE connection.

An externally initiated cloud command carries at least:

- command and idempotency identities;
- stream-session identity and, when known, bound rig identity;
- authenticated principal and authorization evidence;
- source (`operator_console`, trusted local control, watchdog, or system safety rule);
- observed aggregate version and session/rig epoch for audit, not as stop preconditions;
- client and server receipt timestamps.

The local physical path records a trusted rig-control identity and input provenance rather
than fabricating a human operator identity.

Repeating the same idempotency key and payload returns the first known outcome. Reusing the
key for different content is rejected and audited, but that rejection cannot clear or weaken
an already engaged latch. Distinct concurrent stop commands all converge on `engaged` and
remain separately auditable.

### Required Local Effects

`stage-host` performs the safety-critical local sequence without waiting for the cloud:

1. atomically assert its local stop latch;
2. cut or mute the configured OBS audio source;
3. stop current audio according to the hard-stop adapter contract;
4. flush pending playback and avatar actions that could resume speech;
5. latch the current session epoch as locally ineligible and reject its queued tasks; only the
   authoritative cloud reconciliation may bind a later epoch;
6. show the configured safe fallback scene when locally available;
7. durably buffer the stop record for post-reconnect shipping.

Failure of a later step never rolls back an earlier successful stop effect. If adapter state
cannot be proven safe, the local latch remains engaged and emits a local alarm.

### Required Cloud Effects

`session-runtime` performs the cloud sequence without waiting for rig acknowledgement:

1. assert the cloud freeze for the `StreamSession`;
2. invalidate the current dispatch/session epoch;
3. stop scheduling and generation admission;
4. cancel external provider calls where possible and ignore late success;
5. terminally cancel or fail-close every in-flight turn and invalidate every queued task;
6. reject synthesis, dispatch, retry, rewrite, and fallback progression;
7. attempt authenticated local stop delivery and retry it idempotently;
8. persist or buffer the audit and outbox evidence required for reconciliation.

Late provider, safety, TTS, queue, or playback acknowledgements are diagnostic only. They
cannot advance work under an invalid epoch.

Cloud stop is the ADR-025 safe-direction exception: any authenticated in-scope runtime boundary
may assert the strongest process-local freeze without waiting for current actor ownership or
PostgreSQL. It cannot claim a durable session transition or successful rig convergence until the
current owner and authoritative evidence reconcile. Every normal approval, signing, dispatch, or
resume path still requires ADR-025's exact active composite actor fence and shared
ownership-row linearization.

Administrative revoke can leave no active actor. Its durable priority restrictive-control intent
is therefore drained by ADR-025's closed `session-runtime` restrictive-control dispatcher, which
has stop/restriction delivery authority only and cannot resume, raise mode, mint approval, or
dispatch `SpeechTask`.

## Resume Command Semantics

Resume is deliberately asymmetric with stop. It requires an authenticated and authorized
operator, explicit confirmation, and a non-empty human reason. A local hotkey, watchdog,
service identity, recovered network connection, cleared alarm, or returned operator presence
cannot resume output automatically.

The resume protocol has two server-distinguishable intents:

1. `BeginEmergencyResume` validates authorization and current preconditions, records the
   reason, moves the logical state to `resume_pending`, and returns a single-use challenge
   bound to the operator, session, current aggregate version, stop assertions, and
   cloud/local epochs.
2. `ConfirmEmergencyResume` explicitly confirms that challenge. It re-evaluates every
   precondition, authorizes exactly one new epoch derived from the challenge, and clears the
   latch only after both cloud and local reconciliation commit.

The challenge-authorized epoch rotation is the sole expected epoch change during
`resume_pending`. Confirmation validates the old bound epochs before issuing the new one.
Any partial rotation, failed durable transition, missing peer acknowledgement, or different
epoch leaves or returns the logical state to `engaged`; it never exposes a partially clear
state.

The final API may encode these intents differently, but a client-provided boolean in a single
unverified request is not sufficient evidence of confirmation. Challenge lifetime and exact
step-up authentication policy remain OPEN.

Resume requires at least:

- all known stop sources are acknowledged and eligible to clear;
- the cloud stop state is durable and the session actor has the exact current active ADR-025
  recovery/ownership composite fence after completing the closed activation barrier;
- the local audio source is safe, the playback queue is empty, and required adapters report
  known state;
- cloud and stage host authenticate each other and agree on the one newly issued session
  epoch authorized by the confirmed challenge;
- no pre-stop `SpeechTask`, token, media authorization, or queued action can be replayed;
- the rig binding, heartbeat, and clock state satisfy the accepted stage-host protocol;
- the safety gate, active policy, and any capability required by the post-resume mode are
  available;
- session lifecycle permits operation;
- operator presence and authorization satisfy ADR-019 and ADR-020;
- the non-empty reason and confirmation are durably auditable.

Resume creates a new authorization context. Work is admitted only as new or freshly
revalidated work under the new epoch. It never unflushes a queue, reopens a terminal turn, or
extends an expired candidate.

## Partition And Race Semantics

Stop wins every race.

- If the rig is reachable but the cloud is not, local hard stop takes effect and remains
  latched. Reconnection reports the assertion, and the cloud freezes before any new task is
  accepted.
- If the cloud is reachable but the rig is not, cloud freeze takes effect. The rig's
  disconnect watchdog provides the local safety action required by ADR-016, and stop delivery
  is retried after reconnection.
- If either side cannot prove the other's current assertion and epoch, effective state is
  `engaged`.
- A stop received during resume invalidates the resume challenge and returns to `engaged`.
- A stop concurrent with approval, synthesis, dispatch, queue acceptance, or playback
  completion has precedence; lower-priority success cannot authorize later work.
- Clock uncertainty never delays stop. Time uncertainty may block resume.

Neither side may unilaterally clear a stop assertion that originated on the other side.
Exact multi-rig, multi-session, and process-restart reconciliation scope remains an OPEN
decision under OD-015.

## Authentication And Authorization

Cloud stop commands require server-verified identity, the semantic `emergency.stop`
capability, and scope over the target session. This authorization is performed server-side;
rendering a button is not authorization.

The direct local control and physical hotkey are trusted rig safety inputs. They may assert
local stop without human SSO and must work while identity providers, VPN, cloud, and audit
services are unavailable. They cannot resume, raise mode, alter policy, or impersonate an
operator.

Resume requires a distinct `emergency.resume` capability and the confirmed workflow above.
Its grant is intentionally separable from stop authority. Concrete role names, role bundles,
step-up requirements, and separation-of-duty rules are defined or left OPEN by ADR-019.

Automated watchdog and fail-closed rules may assert stop or freeze only through reviewed
machine-principal capabilities. No automated principal can resume.

## Audit And Observability

Every stop attempt, local effect, cloud effect, propagation acknowledgement, resume request,
resume confirmation, rejection, timeout, reconciliation step, and final outcome is
correlated by command, session, rig, epoch, and trace identities.

Audit records include:

- principal or trusted device identity and source;
- authorization decision and policy version where applicable;
- idempotency key or non-reversible digest;
- old and new emergency state;
- asserted layer and stop provenance;
- aggregate, session, and rig epochs;
- timestamps from each participant plus measured clock-offset metadata;
- reason for resume, but no mandatory reason for stop;
- precondition snapshot and failure codes;
- queue-flush, audio-cut, fallback-scene, and cloud-freeze outcomes.

Audit records never include secrets, access tokens, raw prompts, viewer-memory content, or
generated candidate text. Stage-host records are buffered offline and shipped with local
sequence numbers. PostgreSQL remains the cloud system of record, but inability to write an
audit row does not postpone a stop action.

Required operational signals include stop activation, stop propagation lag, local audio-cut
result, flush result, unmatched local/cloud assertions, reconciliation age, resume attempt
outcomes, and any post-stop task rejection. Numeric alert and response SLOs remain OPEN.

## Failure Behavior

- **Cloud or network unavailable:** local hard stop still cuts output and buffers evidence.
- **Rig unavailable:** cloud freezes and cannot resume until the rig is reconciled or an
  accepted scope rule explicitly removes that rig from the session.
- **PostgreSQL unavailable:** cloud applies the strongest available process-local freeze and
  retries durable recording; autonomous work remains disabled and resume is prohibited.
- **Audit transport unavailable:** stop proceeds; evidence is written to the local durable
  buffer or cloud retry path. Resume fails closed until required evidence is durable.
- **OBS control uncertain:** stage-host remains latched, retries the safe adapter operation,
  and escalates locally; it never reports successful resume.
- **Identity or authorization unavailable:** new cloud commands fail closed. The direct local
  stop path remains available.
- **Duplicate, delayed, or reordered messages:** idempotency and epochs converge toward
  stopped; an old resume can never override a newer stop.
- **Process restart or actor takeover:** the new composite actor fence remains recovery-only and
  restores `engaged` unless durable source frontiers and sealed peer reconciliation prove
  `clear`; ambiguous prior dispatch forces session-epoch advancement and queue reconciliation.

## Enforcement

- `stage-host` is the only component allowed to perform local audio cut, queue flush, and
  playout resumption.
- Every cloud pipeline boundary checks the emergency latch and current session epoch before
  advancing work.
- Every normal cloud mutation, signing, and dispatch boundary also uses ADR-025's shared
  ownership-row conflict and checks the exact current active composite actor fence; stop assertion
  alone remains available without it.
- Every stage-host queue acceptance and immediate pre-playback check validates the current
  epoch and local latch.
- Stop and resume commands use dedicated server-side authorization policies and audited
  idempotency handling.
- The e-stop endpoint is a command POST path independent of console state streaming.
- Protected ownership covers e-stop command contracts, runtime guards, stage-host adapters,
  local hotkey handling, reconciliation, tests, and CI policy.
- Unknown state, missing acknowledgement, invalid authorization, stale challenge, or
  unverifiable epoch fails toward `engaged`.

## Acceptance Evidence

Acceptance of this ADR requires a review plan for all evidence below. Production enablement
requires the evidence itself:

- state-table and property tests proving stop dominance and absence of direct
  `engaged -> clear` transitions;
- idempotency, duplicate, reorder, stale-version, and concurrent stop/resume tests;
- target-hardware test proving local audio cut and queue flush with the cloud link severed;
- cloud-freeze tests proving zero new generation, synthesis, dispatch, or autonomous speech;
- partition tests in both directions, including reconnect and assertion reconciliation;
- process, database, audit transport, OBS adapter, and identity-provider fault injection;
- actor pause, lease expiry, forced revoke, stale-composite-fence, PITR, restrictive-dispatcher
  loss, command-response-loss, and takeover fault injection proving stop remains available while
  resume and stale-owner progression do not;
- signature, epoch, expiry, and replay tests proving pre-stop work cannot play after resume;
- authorization tests distinguishing stop from resume and rejecting client-side-only checks;
- rehearsal-mode end-to-end evidence with a reconstructable incident timeline;
- human-reviewed runbooks for stop, failed propagation, failed local cut, and resume.

No numeric latency claim passes until measured on the selected rig and accepted under OD-010.

## Consequences

- Stop remains available under cloud failure, while resume becomes intentionally conservative.
- Distributed assertion and epoch reconciliation add protocol complexity but prevent stale
  work from reappearing after a partition.
- Normal transactional command rules gain a narrowly scoped safety exception: stop effects
  happen before audit availability is guaranteed, and the system remains frozen until the
  evidence is reconciled.
- No e-stop runtime, adapter, schema, or event payload is authorized by this proposal.

## Open Decisions

- OD-010: numeric local hard-stop, propagation, watchdog, and recovery SLOs.
- OD-011: signed command/task algorithm, key custody, rotation, and replay profile.
- OD-015: stop scope across sessions and rigs, resume authority, partition reconciliation,
  post-resume mode, and whether resume requires two distinct human principals.
- Concrete operator role names, capability bundles, SSO vendor, and step-up mechanism:
  ADR-019.
- Resume challenge lifetime and operator-presence lease duration.
- Direct local channel and physical-hotkey integration details for the selected stage-host
  platform.
- Final command/event names, payload schemas, persistence constraints, and retention policy.
