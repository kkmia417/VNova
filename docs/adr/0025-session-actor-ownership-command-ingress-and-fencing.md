# ADR-025: Session Actor Ownership, Command Ingress, And Fencing

Status: Proposed

Priority: P0

Date: 2026-07-17

Sources: `AGENTS.md`, `vnova-review-handoff.md`, ADR-003, ADR-004, ADR-007, ADR-008,
ADR-011, ADR-015, ADR-019, ADR-020, ADR-023, ADR-024

This ADR is non-binding while its status is `Proposed`. It authorizes no runtime worker,
database schema or migration, command endpoint, serialized contract, provider call, timer,
signing path, or stage-host behavior. Every protected implementation remains subject to the
Runtime Implementation Gate and its own human review.

## Context

ADR-003 requires one logical actor per `StreamSession` and optimistic concurrency for aggregate
mutations. Those rules are necessary but insufficient. Optimistic concurrency can reject a
second database commit while still allowing a paused or partitioned actor to:

- start a provider, media, signing, dispatch, or other external effect after it has lost
  authority;
- accept or lose an operator command while `control-api` times out or crashes;
- apply a late provider result after another actor has taken over;
- fire an in-memory timer twice, skip it permanently, or replay an unbounded backlog after
  restart;
- sign or dispatch old work while a replacement actor believes it is the sole owner; or
- report success when the durable outcome is actually unknown.

Process identity, Redis routing, a WebSocket connection, a heartbeat, and an aggregate version
do not prove current actor ownership. A lease without a fencing generation also cannot
distinguish work started by an expired owner from work started by its successor. Conversely,
one generic epoch cannot safely stand for aggregate ordering, actor ownership, stage-host
authorization, operator presence, or disaster-recovery authority.

The ownership, command, external-effect, timer, and takeover model must therefore be closed
before session-runtime persistence or workers are implemented.

## Decision

PostgreSQL is the sole cloud authority for current `StreamSession` actor ownership inside one
protected disaster-recovery generation. Each session has one durable ownership record with an
`ownership_generation` that increases monotonically within that recovery generation. The
effective actor fence is the exact pair `(recovery_generation, ownership_generation)`;
neither component is optional and neither substitutes for the other. Ordinary session mutation,
approval progression, external-effect start, result application, signing, and dispatch require
an unexpired, `active`, exact-composite-fence ownership proof.

The current `recovery_generation` must be established by an independently retained,
non-rollback authority or rebased above a separately trusted high-water before any restored
database can serve. Numeric ownership generations may repeat after point-in-time restore, so
they are never compared across recovery generations. OD-029 retains the concrete authority and
mechanism; until it is accepted and enforceable at every protected boundary, disaster recovery
cannot authorize serving.

`control-api` remains stateless. An authenticated command is accepted only after the
session-runtime command-ingress boundary durably records its immutable intent and receipt in
PostgreSQL. Delivery from ingress to the current actor is at least once; durable idempotency and
terminal outcomes make redelivery safe. A transport timeout means the caller's observation is
`unknown`, never implicit success or failure.

Session-owned external effects use durable intent-before-effect, composite-fence-bound attempts,
explicit timeout and deadline, current-owner revalidation, and late-result fencing. Durable
timer occurrences and claims replace process-memory timer authority. Every new owner first
enters a recovery-only phase and cannot resume ordinary work until reconciliation succeeds.

The only ownership exception is a narrowly scoped safe-direction operation accepted by
ADR-004, ADR-015, and ADR-020. An authenticated or trusted boundary may freeze, stop, lower,
cancel, or deny locally when ownership or PostgreSQL is uncertain. It may not approve, resume,
raise, dispatch, claim durable success, or otherwise widen authority.

## Authoritative Ownership Record

The conceptual `SessionOwnership` record is keyed by exact environment and stream-session
identity. Its physical schema remains blocked, but any implementation must preserve at least:

- a stable ownership-record identity and revision;
- the exact current protected `recovery_generation`;
- the current `ownership_generation`;
- one closed ownership phase;
- the authenticated runtime process-incarnation identity when occupied;
- a database-authoritative lease expiry;
- the last transition identity, cause, and minimized audit provenance; and
- the recovery or relinquishment disposition needed to explain a takeover.

A runtime process-incarnation identity is newly issued for each process start and cannot be a
hostname, pod name, reusable deployment label, or human identity. It establishes who is asking,
not whether that process currently owns a session.

### Closed Ownership Phases

| Phase        | Meaning                                                                                                                                | Ordinary mutation or external-effect authority |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| `vacant`     | No process owns the session. A prior owner may still require takeover reconciliation.                                                  | None                                           |
| `recovering` | One exact process/composite actor fence holds the lease only to inspect, reconcile, expire, and restrict state.                        | None                                           |
| `active`     | Recovery gates passed and the exact process/composite actor fence holds an unexpired lease.                                            | Allowed only with all other current checks     |
| `closed`     | The session is terminal and can never acquire another owner or reopen admission; future broadcast uses a new `StreamSession` identity. | None                                           |

`uncertain` is an effective safety posture, not another durable phase. A process that cannot
prove the exact current phase, owner, composite actor fence, and lease is not an owner even if its last
cached row said `active`.

### Closed Ownership Transitions

| Operation               | Preconditions                                                                                                                                                                                                                                                                                                                                                                                            | Result                                                                                                                                                                         |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Initial acquire         | Exact session is `vacant`, admission is not `closed`, and expected recovery generation/ownership revision match                                                                                                                                                                                                                                                                                          | Increment ownership generation, bind process incarnation and lease, enter `recovering`; `draining` can only recover/final-close                                                |
| Renew                   | Exact process, composite actor fence, revision, nonexpired lease, and `recovering` or `active` phase match                                                                                                                                                                                                                                                                                               | Extend the lease without changing ownership generation                                                                                                                         |
| Activate after recovery | Exact process/composite actor fence is `recovering`; admission is `open`; every recovery gate is durable and current                                                                                                                                                                                                                                                                                     | Enter `active` without changing ownership generation                                                                                                                           |
| Graceful relinquish     | Exact process/composite actor fence and revision match                                                                                                                                                                                                                                                                                                                                                   | Increment ownership generation, clear owner/lease, enter `vacant`, record whether external work is fully reconciled                                                            |
| Administrative revoke   | Protected revocation authority, exact recovery generation, expected ownership revision, and current phase match                                                                                                                                                                                                                                                                                          | Increment ownership generation and clear owner/lease; preserve `closed`, otherwise enter/preserve `vacant`; atomically install the required restrictive recovery/dispatch hold |
| Expired-owner takeover  | Stored owner lease is expired according to PostgreSQL time and expected composite actor fence/revision match                                                                                                                                                                                                                                                                                             | Increment ownership generation, bind the new process and lease, enter `recovering`; never inherit the old actor's active phase                                                 |
| Close                   | Session is `Ending` with a resolved terminal target; exact `draining` admission epoch/prefix has every accepted item terminal or safely classified; every admitted `RecoveryProbe*` lineage is terminal/non-widening; every bound source ambiguity is resolved, permanently safe-quarantined, or accountably disposed; no audience ambiguity remains; exact current composite actor fence/revision match | Atomically commit the resolved session terminality, admission `closed`, ownership generation increment, owner/lease clear, and ownership `closed`                              |

Every operation uses the same PostgreSQL ownership-row linearization point required below.
`ownership_generation` never decreases or repeats within one `recovery_generation`; the exact
composite pair must never repeat. Backup restore, failover, and failback establish a new
protected recovery generation before ownership is acquired. A failed, timed-out, or ambiguous
transition grants no ownership. Reacquiring from a new process incarnation is a takeover, even
when the deployment name is unchanged.

Administrative revoke is phase-preserving for a terminal session: `closed` can never transition
back to `vacant`, `recovering`, or `active`. The revoke may still supersede stale ownership and
advance restrictive audience authority because terminality must not disable safe-direction
containment.

Lease expiry itself does not mutate business state. It makes the cached owner ineligible.
While the expired owner remains recorded, another process can become owner only through the
expired-owner takeover transaction. A `vacant` record instead uses acquire/reacquire.

## Lease And Clock Semantics

A fresh PostgreSQL clock reading obtained after the ownership-row conflict primitive is acquired
under the accepted clock profile decides acquire, renew, expiry, and takeover eligibility.
Transaction-start timestamps, Redis timestamps, application wall clocks, orchestration health,
and heartbeats are observations only. A long transaction or lock wait cannot reuse a time
sample taken before it became the serialization winner.

The actor may map a successful database lease proof to a deliberately earlier local monotonic
deadline for in-process cancellation and scheduling. It never maps it to a later deadline.
Clock regression, excessive uncertainty, stale sampling, lease-renewal timeout, database
unavailability, or inability to map the proof conservatively moves the actor to effective safe
hold.

Before starting an external attempt, the actor must prove that the remaining conservative lease
horizon covers the complete attempt timeout, result-recording budget, and accepted uncertainty
margin. If it does not, the actor renews first or does not start the attempt. Exact durations,
renewal cadence, margins, and takeover holds belong to OD-035; no implementation may invent
defaults while they are OPEN.

## Ownership-Protected Commits

Every ownership transition and every ownership-protected commit must participate in one shared
linearization mechanism on the exact `SessionOwnership` row. It must either hold an incompatible
row lock through commit or perform an equivalent guarded write/CAS that necessarily conflicts
with renew, revoke, close, acquire, and takeover. A read predicate, cached lease proof,
aggregate-row update, advisory lock, or chosen isolation level alone is insufficient.

After winning that conflict, every operation takes a fresh database time sample and re-reads the
exact protected `recovery_generation`, ownership revision, and row. An ownership transition then
checks its operation-specific predicate from the closed transition table; vacant acquire,
recovering renew/activation, expired-owner takeover, revoke, and close do not falsely require an
already-active owner.

Every ordinary protected commit additionally requires:

1. the exact `SessionOwnership` process incarnation and `ownership_generation`;
2. `active` phase and an unexpired database lease; and
3. the exact open normal-work admission epoch for work that creates or advances normal session
   activity; and
4. the expected `StreamSession` aggregate version and all operation-specific authority.

The transaction commits the new aggregate state, command outcome, minimized audit evidence,
and any authorized event manifest/outbox records atomically. A correct aggregate version with a
stale composite actor fence is rejected. A current composite fence with a stale aggregate
version is also rejected. A transaction that waited behind revoke or takeover must observe the
new row and fail. Neither failure can be retried by changing only cached state.

The fixed lock order is protected recovery-generation guard, exact ownership row, session
aggregate row, then dependent work rows in a documented deterministic order. Implementations may
select exact SQL and isolation only if concurrency tests prove the required write conflict,
post-lock time check, deadlock behavior, and real-time ordering. External network calls never
hold this database transaction open.

Recovery-only transitions may expire or cancel stale work, persist restrictive evidence, and
record reconciliation. They cannot mint approval, start synthesis, sign, dispatch, resume,
increase mode, or make a timer produce new audience work until the ownership phase is `active`.

## Identity, Version, And Epoch Separation

| Value                                        | What it orders or invalidates                                                       | What it never proves                                                            |
| -------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Runtime process-incarnation identity         | Authenticated identity of one process lifetime                                      | Session ownership or ordering                                                   |
| Composite actor fence                        | Exact recovery site/campaign plus supersession of session actor ownership           | Aggregate state order, safe speech, or stage-host authorization                 |
| `ownership_generation`                       | Actor supersession within one exact recovery generation                             | Cross-recovery order, aggregate order, or rig authorization                     |
| `StreamSession` aggregate version            | Serialized committed business-state transitions                                     | Current actor, event count, or downstream playout authority                     |
| Normal-work admission status/epoch           | Monotonic open -> draining -> closed admission and its committed source cut         | Actor ownership, aggregate order, safety/authorization, or audience convergence |
| Session authorization epoch                  | Invalidates audience/widening work and prevents stale controls lowering restriction | Actor ownership, stop dominance, aggregate order, or safety approval            |
| Rig boot/connection/session-binding identity | Supersession and reconciliation of the local connection/binding                     | Cloud actor ownership or human authority                                        |
| Operator-presence lease generation           | Current qualifying human-presence evidence                                          | Actor ownership or permission for a different capability                        |
| Disaster-recovery generation                 | Supersession of a recovery site/campaign and its administrative authority           | A particular session actor lease or safe resumption                             |
| Attempt, command, trigger, and event IDs     | Identity and deduplication of one fact or operation                                 | A generic global order or authorization                                         |

No field may be named or interpreted as a generic `epoch` when its authority is one of these
specific concepts. Comparisons occur only within the declared identity and scope. An
authenticated stop assertion remains dominant even when it carries an older observed session
epoch; the epoch can prevent stale widening or a stale control from lowering restriction, but
can never invalidate stop authority.

## Durable Command Ingress

### Acceptance Boundary

The operator or trusted client sends an idempotent command to `control-api`. `control-api`
authenticates and authorizes it under ADR-019, canonicalizes the semantic intent under the
accepted contract, and forwards the exact human/trusted provenance using its workload identity.

The session-runtime ingress boundary validates framing, target, submission recovery generation/
receipt-authority token, source frontier, current normal-work admission status/epoch, provenance,
expiry, canonical digest, and idempotency scope, then atomically commits an immutable
`CommandIntent`, durable `CommandReceipt`, and initial append-only
`CommandAuthorizationObservation` in PostgreSQL before acknowledging acceptance. The receipt
transaction conflicts/CASes the same per-session admission/source row used to begin closure,
obtains fresh accepted database time after that conflict, and rejects when the immutable hard
deadline has passed. The receipt identifies the original intent and its current durable
disposition; the authorization observation preserves minimized evidence without credentials;
neither means the domain action succeeded.

`control-api` does not keep an authoritative retry queue or infer acceptance from a socket write.
If it receives no durable receipt, it reports an unknown outcome. Inside a proven-complete
current recovery horizon, the caller may resubmit the same generation/intent/key or query the
same receipt. Stale/unknown generation or lost-tail absence instead requires reconciliation. A
later synchronous terminal result is a convenience view of the durable outcome, not a second
authority.

### Idempotency And Canonical Intent

The protected idempotency-key scope binds at least:

- environment and stream-session identity;
- the command's protected submission `recovery_generation` or an equivalently non-rollback
  receipt-authority token;
- semantic command type;
- authenticated submitting principal or trusted source;
- the client idempotency key.

The canonical semantic-intent digest of target, parameters, confirmation/reason evidence where
applicable, expected versions, and command deadline is stored immutably on the first intent and
compared after lookup by that protected key scope. It is deliberately not part of the uniqueness
or lookup identity: otherwise reuse of one key for different semantics could create a second
command instead of conflicting.

Volatile bearer/session data, token expiry, transport identity, and the particular authorization
evaluation are excluded from the semantic digest. The receipt separately preserves minimized
references to the original authorization decision and provenance. Authorization evidence is a
separate append-only lineage under ADR-019: every observation binds the same command/principal/
semantic digest plus policy/revocation epoch, authentication context references, decision,
reason, evaluation time, and expiry, without storing reusable credentials. Execution revalidates
current authorization and binds the exact eligible observation plus expected per-command
authorization-lineage revision. Every append advances/CASes that revision; execution conflicts
on it so a concurrent append invalidates the attempt. OD-022 must select deterministic
allow/deny/step-up/unavailable precedence. Until then, a newer or incomparable competing
observation fails closed and execution cannot cherry-pick an older allow.

A retry by the same principal with refreshed credentials but the same semantic scope and digest
may append a new deduplicated authorization observation only while the command is nonterminal,
before its hard deadline, and under the exact open normal-work admission epoch through the same
admission/source CAS. That append obtains fresh accepted database time after the conflict and
rejects when the command or observation evidence is already expired. It returns the original
receipt and terminal outcome only after current receipt-disclosure authorization succeeds and
never overwrites earlier lineage. During
`draining`/`closed`, or after terminality/effective expiry, the retry can perform only
disclosure-authorized lookup plus separately bounded access audit; it appends no authorization
observation, while closure drain terminalizes any pre-close pending command. A different
principal occupies a different protected scope and must never learn another principal's receipt.
The same scope and key with a different semantic digest is a conflict, is audited, and cannot
change the original action. Canonicalization, authorization-evidence handoff, and serialized
fields remain OD-021 contract work.

Normal command framing binds the recovery generation observed at submission and preserves it
unchanged across forwarding and retry. A stale or unknown submission generation is
`reconciliation_required`, not a fresh command. Intentional issue after recovery requires the
current generation, a new idempotency key, current authentication/authorization, and every
command-specific confirmation. An authenticated stop assertion remains the safe-direction
exception.

Possession of an idempotency key or prior receipt is not read authority. Every path that returns
an existing receipt or outcome—including duplicate submission, synchronous completion, polling,
and direct lookup—performs current authentication plus object- and data-class disclosure
authorization independently from execution authorization, and denies or redacts the response
when that access was revoked.

### Actor Delivery And Completion

The durable command record is the inbox authority. A PostgreSQL wake-up, bounded poll, or
replaceable notification may alert the current actor, but Redis or in-memory routing cannot make
a command accepted or complete.

The active owner claims or selects pending work with the exact composite actor fence. Before
mutation it revalidates:

- current protected recovery/ownership composite fence, owner, phase, revision, and lease;
- exact open normal-work admission epoch/source-row conflict for an ordinary claim/execution;
- command deadline against fresh accepted database time obtained after the row conflicts;
- original authorization provenance plus an authoritative, current, unexpired append-only
  authorization observation bound to the same command/principal/digest and current policy/
  revocation epoch, selected by the accepted deterministic precedence at the exact expected
  authorization-lineage revision;
- expected aggregate and domain-specific epochs;
- emergency, mode, rights, configuration, safety, capacity, and other applicable restrictions;
  and
- command-specific confirmation, reason, and presence evidence.

A normal successful state transition, the exact selected authorization-observation reference,
and its terminal `CommandOutcome` commit atomically under the same current authorization epoch
and open admission/source CAS.
A role, policy, presence, revocation, or evidence-expiry change before that commit rejects the
execution attempt; an unavailable or indeterminate authorization boundary fails closed for that
attempt. An accepted retryable stale/expired/step-up/unavailable class leaves the command
`pending_but_ineligible_authorization` until a newer eligible observation arrives or the hard
deadline passes. Only a denial class explicitly accepted as nonretryable under ADR-019/OD-022 may
commit a terminal rejection. A refreshed observation survives process failure and can be
reconsidered, but never authorizes execution after its own expiry or a newer restrictive
authority. Once any terminal command outcome commits or effective expiry occurs, later retries
cannot append authorization observations or reopen execution.

A durable rejection or fail-closed outcome also records its machine-readable reason. A crash
after receipt but before execution leaves the command pending for the current or successor
owner. A crash after the atomic terminal transaction returns the same outcome on redelivery.

The caller-observed `unknown` result is never stored as a terminal command outcome: it means only
that the caller could not yet observe the durable receipt or result.

Every normal command has an immutable hard deadline. Once authoritative accepted time passes it,
the command is effectively expired and can never execute or widen authority, even before its
terminal row is written. A current owner commits exactly one terminal expired/failed-closed
disposition when authority becomes available; until then lookup reports
`pending_but_ineligible_expiry_uncommitted`, not ordinary executable pending. Deadline passage
cannot be reversed or extended. An independently authenticated stop assertion may still act
through the safe-direction path, while the expired normal-command lineage never becomes
successful.

After admission becomes non-open, an ordinary command cannot be claimed or execute. Closure
drain may select its fixed pre-close command only through a distinct non-advancing path that
commits expiry, cancellation, rejection, fail-closed, or quarantine evidence. It cannot turn a
pending command into a successful or widening domain transition.

## Session Closure And Normal-Work Admission

Session lifecycle terminality has a separate monotonic normal-work admission gate with an
`admission_epoch` and closed conceptual states `open`, `draining`, and `closed`. This gate is
PostgreSQL authority for accepting new normal command receipts, materializing/claiming timer
occurrences, promoting durable viewer/platform/director/content-scheduler input into eligible
work, admitting every normal turn, creating an ordinary external-effect intent, authorizing its
send, and applying an effect observation that advances domain or audience work; it is not actor
ownership, mode, or an audience fence. Separately typed bounded recovery-probe evidence follows
the non-widening exception below, never this ordinary gate.
The gate also covers every other ordinary creation or advancement in the session pipeline,
including Turn/attempt/candidate progression, selection, approval minting, media authorization,
task creation, signing, and dispatch. A non-open gate permits only bounded evidence capture,
restrictive action, and terminal/non-advancing expiry, cancellation, rejection, fail-closed, or
quarantine disposition.
`draining` carries a durable initial cause and reopen prohibition. Normal closure uses
`normal_closure`; recovery that supersedes a restored `open` state uses
`lost_tail_quarantine` under the new recovery generation. If recovery instead finds
`draining(normal_closure)` with an unproven later drain/final-close tail, it preserves that
historical initial cause and atomically adds a monotonic `lost_tail_quarantine` overlay,
affected interval, and stronger final-close preconditions. The effective state is
`draining(normal_closure + lost_tail_quarantine)`; neither the cause nor overlay clears or
returns to `open`. A restored `closed` state remains closed and may receive only separate
history-completeness/quarantine evidence and restrictive holds; it is never reacquired or
reopened.

Beginning session closure is an ownership-protected transaction that follows the fixed lock
order, transitions the nonterminal session lifecycle to `Ending` with its resolved requested
terminal target/cause, compare-and-swaps `open -> draining`, and fixes a committed-prefix cut
through every durable normal input/admission source, including command and timer source rows.
Every normal receipt, input-promotion, timer materialization/claim/firing, turn-admission,
effect-intent creation, effect-send-authorization, advancing effect-application transaction, and
every other ordinary Turn/candidate/approval/media/task/dispatch progression conflicts/CASes that
same admission/source authority:

- a transaction serialized before the cut is in the pre-close prefix and must reach one terminal
  non-executable or completed disposition before final close;
- a normal command serialized after `draining` or `closed` receives deterministic
  `session_closed` non-acceptance from the monotonic gate and creates no command intent, receipt,
  outcome, or authorization observation; only a separately bounded access/abuse audit may be
  recorded;
- timer materialization serialized after the cut creates no new occurrence identity; begin-close
  freezes each applicable schedule materialization cursor with one schedule-level closure
  disposition, and only occurrences already in the fixed prefix receive terminal dispositions;
- raw platform/input observations may continue only through their separately bounded evidence/
  moderation intake policy, but after the cut they cannot become eligible triggers, create a
  turn, or claim accepted session work; and
- no ordinary `EffectIntent` may be created after the cut; an ordinary effect attempt serialized
  afterward receives no send authorization, and a later response observation cannot advance
  domain or audience state. A bounded late `EffectResponseObservation` may still append as
  evidence for a pre-closure-cut send-authorized attempt; that attempt remains possibly sent
  until classified, and draining may append only fenced non-advancing
  expiry/cancellation/rejection/quarantine dispositions. The sole new external-interaction
  exception is the separately typed, bounded `RecoveryProbeIntent` lineage defined below, bound
  to a specific immutable closure-prefix item or pre-recovery-cut/lost-tail ambiguity and unable
  to widen state; and
- a caller timeout remains queryable/retryable against the same monotonic admission epoch and
  cannot turn a closed-session rejection into fresh acceptance.

While `draining`, the active actor or a recovery-only successor expires, cancels, fail-closes, or
reconciles the fixed pre-close input/command/occurrence/turn/effect prefix in bounded
transactions. Every turn-admission source and timer claim/firing rechecks the gate and cannot
admit a turn after draining begins. Ordinary effect intent creation, send authorization, and
advancing application also recheck the gate and remain blocked. Only a separately typed
fixed-prefix/lost-tail-bound recovery probe may perform a bounded read-only/restrictive external
interaction, and it may commit only a non-widening terminal disposition; closure never treats the
cut or a negative probe by itself as proof that a prior attempt was unsent.

Final close is one atomic ownership operation, not a two-step session/admission close followed by
owner cleanup. It takes the protected recovery-generation guard, ownership row, session
aggregate, and admission/source rows in the fixed order; compares the exact `draining` epoch and
fixed prefix; proves the `Ending` terminal target resolved, every pre-close
input/command/occurrence/turn/effect terminal or safely classified, every admitted recovery-probe
lineage terminal with a non-widening disposition, and no unresolved bound source ambiguity or
audience ambiguity; and commits that resolved session terminality, drain evidence,
`draining -> closed`, ownership-generation increment, owner/lease clear, and ownership `closed`
together.

For `lost_tail_quarantine`, the recovery transaction first records the trusted pre-loss
high-water, unproven interval, affected source set, restrictive holds, and reopen prohibition as
the visible conservative drain cut. In that same transaction, any restored nonterminal lifecycle
enters or remains `Ending`: a terminal target already proven inside the trusted pre-loss horizon
is preserved, while a missing or tail-ambiguous target is marked
`unresolved_lost_tail_target` rather than guessed. Final close additionally requires an
OD-029-authorized accountable disposition that resolves that target, exact rig/audience
reconciliation, and safe classification or permanent quarantine of every affected range. If
those proofs cannot be established, the session remains
`Ending`/`draining`/quarantined indefinitely; it never reopens or takes an illegal direct edge
from a live/preparing state to a terminal lifecycle merely to improve availability.

A crash before that transaction commits leaves `Ending`/`draining` durable; takeover can finish
restriction/terminalization and retry final close but cannot reopen admission. A crash after
commit observes every terminal/ownership fact together. Revoke or relinquish racing final close
uses the same ownership-row conflict: if it wins first, the session remains
`Ending`/`draining`/vacant and a successor may acquire only to recover and close; if final close
wins, later revoke preserves `closed` and no relinquish/reacquire is legal.

An authenticated stop or stronger safe-direction assertion remains available through its
separate restrictive path after admission closes. Database uncertainty may stop work locally,
but cannot claim durable session closure or accepted terminal outcomes.

## Session-Owned External Effects

Every ordinary provider call, media operation, signing request, dispatch, and other session-owned
external effect uses four separate conceptual record families:

1. immutable `EffectIntent`, committed before the effect and bound to session, work lineage,
   command/trigger cause, originating composite actor fence, exact configuration/authorization epochs,
   idempotency identity, timeout, and outer deadline;
2. immutable `EffectAttempt`, one per send-authorized attempt, committed immediately before the
   first possible network byte and bound to the intent, current composite fence, attempt timeout,
   and stable downstream idempotency identity;
3. immutable `EffectResponseObservation`, one per response, query result, timeout, cancellation,
   or indeterminate transport observation, durably recorded before domain application and bound
   to its attempt; and
4. immutable `EffectApplicationDisposition` or owning domain transition, committed atomically
   only if the observation remains current and eligible, and explicitly recording applied,
   rejected, superseded, late, expired, or failed-closed disposition.

A recovery probe uses the same four durable roles but a logically distinct
`RecoveryProbeIntent`, `RecoveryProbeAttempt`, `RecoveryProbeResponseObservation`, and
`RecoveryProbeDisposition` lineage. A physical schema may use separate tables or a protected
purpose discriminator only after OD-034 review, but the uniqueness, lookup, admission, and
application predicates must make an ordinary effect impossible to reinterpret as a probe or vice
versa.

The following sequence is mandatory:

1. Persist intent without starting the effect.
2. Immediately before authorizing a possible send, revalidate the exact composite fence, lease
   horizon, deadlines, and every restrictive authority. An ordinary effect requires `active`
   phase plus exact-open admission/source and aggregate preconditions. A recovery probe requires
   either the exact active fence plus exact draining-prefix binding, or the exact recovering fence
   plus recovery-attempt binding, and cannot use an ordinary-effect path.
3. Commit the send-authorized attempt boundary and use the same downstream idempotency identity
   when supported.
4. Invoke through the responsible gateway with an explicit timeout and cancellation.
5. Durably record the normalized response observation before attempting any owning-domain
   transition. Restricted response bodies remain in their protected store.
6. Apply an ordinary observation only in an ownership-protected transaction that rechecks the
   current active composite fence, exact open admission/source epoch, aggregate version, intent
   eligibility, deadline, and restrictive state. A recovery-probe observation can commit only a
   non-widening recovery disposition under the exact current active-draining or recovering fence
   and a current closure-prefix/recovery-attempt binding to the same source ambiguity. The
   originating fence/binding is immutable provenance, not continuing authority; a successor may
   terminalize but never send/replay the old probe attempt.
7. Record a late, duplicate, superseded, or indeterminate application disposition as minimized
   evidence; never let it advance work.

`EffectAttempt` is authorization to cross the send boundary, not proof that a byte left the
process or that the provider accepted work. Once an attempt record commits, a crash is treated as
`possibly_sent` unless reviewed downstream idempotency, query, or fencing evidence proves a more
specific state. An intent is `definitely_not_send_authorized` only when it has no committed
send-authorized attempt inside a proven-complete authoritative horizon in the same recovery
generation. A received response that was not durably observed before a crash is also recovered
as possibly sent/unknown and is never reconstructed from process memory.

These fencing records do not replace domain-specific `GenerationAttempt`,
`SynthesisAttempt`, transfer, signing, or dispatch lineage. One admitted logical
domain-provider operation owns exactly one `EffectIntent`. Its originating fence records creation
provenance but grants no continuing authority: a successor may act on the same intent only after
closed recovery classification and complete current-authority revalidation. That intent may own `0..N`
send-authorized attempts only where reviewed downstream idempotency/query semantics permit
transport replay. A policy retry, rewrite, fallback, different provider, or changed request is a
new domain attempt and a new effect intent. Every response observation belongs to exactly one
send-authorized attempt and has at most one terminal application disposition. At most one
observation for an intent may produce an authority- or domain-advancing transition; all
duplicates and conflicting observations receive terminal non-advancing dispositions. The
domain-attempt terminal outcome and advancing application disposition commit together.

If an external system lacks idempotency or an outcome-query/fencing mechanism, a possibly-sent
attempt is not blindly repeated after takeover. The recovering owner waits for the bounded
attempt horizon, uses a recovery probe when a reviewed interface supports it, or terminates the
affected work fail-closed. A non-idempotent irreversible audience or authority-widening effect
without an end-to-end fence is prohibited.

ADR-004 outbox publication and independent consumer effects retain their own claim/inbox
fencing. This ADR does not turn the session actor into the owner of every event consumer.

## Signing, Dispatch, And Audience Fencing

Current actor ownership is necessary but does not replace the session authorization epoch used
by ADR-008, ADR-011, ADR-015, and ADR-020. Signing and dispatch boundaries must validate the
current composite actor fence server-side through the ownership-row linearization point and bind
the durable authorization/dispatch record to it. Caller-provided or previously cached ownership
proof is insufficient. The identifier-only stage-host contract continues to carry the accepted
session/authorization epoch; adding any serialized ownership or recovery field requires OD-021
and protected contract review.

A database check immediately before a later network send is not an end-to-end audience fence.
The accepted stage-host protocol must provide a downstream-verifiable ordering rule between
audience-task acceptance and restrictive session-epoch transitions. Until OD-021 and protected
ADR-008/011 review define and test that rule, a cloud administrative revoke guarantees removal
of cloud actor authority, not immediate audience cessation.

When protected administrative revoke cannot prove that no audience-bound work could have
escaped, its ownership transaction must also:

1. advance the session authorization epoch or establish an equivalently stronger reviewed
   downstream fence;
2. install a durable restrictive dispatch/recovery hold;
3. create the priority authenticated restrictive-control intent; and
4. mark exact-rig convergence unresolved.

These changes share the fixed ownership/session lock order and commit atomically with the
ownership revoke. Restrictive control is attempted immediately at every reachable runtime and
stage boundary; it is not deferred to a future successor. No component may claim audience
cessation or rig convergence until stage host durably acknowledges the newer restriction. A
disconnected or unsealed rig remains restricted/unknown, new dispatch and resume remain
prohibited, and existing exposure is bounded only by accepted task expiry, watchdog, and local
stop behavior. Immediate audience cessation requires the ADR-015 local hard-stop/e-stop path,
not cloud revoke alone.

Because revoke deliberately leaves no active actor, one closed restrictive-control dispatcher
inside the existing `session-runtime` responsibility boundary drains these durable intents
without requiring actor ownership. It is a safe-direction capability, not a second session
actor:

- PostgreSQL intent/outbox state is authority; a bounded claim, wake-up notification, or Redis
  delivery is coordination only;
- each attempt validates the current protected recovery generation, latest restrictive session
  epoch/cause, exact rig binding, expiry, and authenticated priority-control contract;
- it uses an independently reserved priority lane with explicit timeout, bounded retry, and
  durable acknowledgement/convergence evidence;
- duplicate, delayed, or reordered controls can only preserve or strengthen restriction; and
- it cannot mint approval, mutate normal session state, clear a latch, resume, raise mode,
  dispatch `SpeechTask`, or report audience convergence without exact stage-host acknowledgement.

If the dispatcher, database, identity, signing, transport, or rig is unavailable, reachable
local/process restrictions still apply but audience state remains unknown; watchdog and ADR-015
e-stop are the only stronger guarantees. OD-021/037 retain the exact control contract, claim,
reserve, retry, and capacity profile.

When a takeover follows any possibly sent signing, dispatch, restrictive-control, or playout
operation, the new owner must:

1. enter or preserve safe hold;
2. advance the session authorization epoch in a durable recovery transition;
3. invalidate old queued or signed work;
4. reconcile the exact rig boot, connection, binding, epoch, queue, journal, latch, and actual
   playout state; and
5. issue only fresh work after ownership becomes `active`.

The epoch advance is also required whenever absence of audience-bound ambiguity cannot be
proved. A clean pre-broadcast handoff may retain the session authorization epoch only when no
task or audience-widening control authority could have escaped and the accepted protocol can
prove that fact. A stale actor cannot obtain a valid signing or dispatch result merely by reading
the new epoch; the server-side composite-fence check still rejects it.

After point-in-time restore or site failover, a restored session epoch alone is not a
non-rollback fence. Before serving, the accepted recovery protocol must either make stage host
validate the protected `recovery_generation` or establish a superseding rig binding/signing
authority and session epoch above an independently retained trusted high-water. Otherwise old
signed work remains potentially valid and the audience surface stays disabled.

## Durable Triggers And Timers

Process-memory timers are wake-up optimizations only. Session scheduling uses separate durable
conceptual records:

- immutable schedule/trigger intent with stable identity, exact session and policy provenance,
  due window, hard deadline, and catch-up disposition;
- one stable `TriggerOccurrence` identity for each due occurrence, uniquely keyed by exact
  environment/session/schedule version/scope plus its canonical nominal occurrence coordinate;
- a bounded `TimerClaim` with a unique claim token/revision tied to the exact current composite
  actor fence, plus one occurrence-owned current-claim token/revision pointer; and
- one durable firing disposition, optionally bound to the single admitted `Turn`.

The canonical occurrence coordinate is derived deterministically from the accepted schedule
calendar/time-zone semantics and nominal ordinal/window; it is not an allocated UUID, commit
timestamp, or scan-local counter. A database uniqueness invariant prevents two evaluators from
materializing different IDs for the same nominal slot. A per-schedule materialization cursor or
equivalent compare-and-swap advances only with the same committed occurrence set, so duplicate
evaluation and commit-response loss re-read the same rows without gaps. Every materialization
range/batch is bounded under OD-037. The materialization transaction takes the shared
ownership-row linearization point, revalidates the exact current `active` composite actor fence
and fresh accepted database time, then conflicts/CASes the current session normal-work
admission/source row and schedule cursor with the committed occurrence set. A `recovering` owner
may classify existing occurrence/cursor state through the closed recovery workflow but cannot
create normal occurrences or advance the cursor. After `draining` begins, no phase can create any
new occurrence identity or advance a recurring cursor. The one schedule-level closure
disposition, not one row per future nominal slot, proves materialization is frozen.

Due evaluation uses the accepted authoritative clock profile in a PostgreSQL transaction. Local
monotonic time may wake the actor early but cannot make an occurrence due or extend its deadline.
Claim acquisition takes the shared ownership-row linearization point, fresh database time, and
rechecks the exact open normal-work admission epoch before atomically compare-and-swapping the
expected occurrence revision plus expected current-claim revision into one new current
token/revision. A concurrent loser reads the winning current claim or terminal disposition;
unique token generation by itself is not sufficient.

Claim expiry never deletes or completes the occurrence. A successor may reclaim the same
occurrence identity only through the same CAS, which supersedes every older claim even inside the
same composite actor fence. The firing transaction again uses the shared ownership-row
linearization point and must compare the exact current unexpired claim token/revision plus
expected occurrence revision plus the still-open admission epoch. If closure started, firing
commits only a terminal non-admitted disposition. These uniqueness and compare-and-swap rules
permit at most one turn admission and one terminal firing disposition.

Timer firing reuses the same ownership, restriction, admission, capacity, and atomic-outcome
rules as an external command. Restart or takeover reconstructs due and pending occurrences from
PostgreSQL, not from a timer wheel, Redis delay, or wall-clock scan alone.

Every trigger family must declare a finite missed-occurrence policy. Until OD-014 accepts a
family-specific policy, the safe default is no autonomous catch-up: a missed occurrence expires
or requires explicit operator disposition. No restart may bunch an unbounded historical backlog
into the live broadcast. Numeric windows and clock uncertainty belong to OD-035; queue,
claim-count, and recovery-drain bounds belong to OD-037.

ADR-024 `ActivationSchedule` is a separate configuration-authority workflow. It never becomes a
session trigger or inherits actor ownership merely because both use time.

## Recovery Probes

Only a closed class of external recovery probes may classify prior work or establish a stronger
restriction without reopening ordinary admission. A probe may be admitted under either:

- the exact current `active` fence with admission `draining`, bound to one item in that immutable
  closure prefix; or
- the exact current `recovering` fence, bound to one durable recovery attempt and one pre-cut,
  lost-tail, provider, dispatch, or rig ambiguity in its classified source set.

The intent-creation transaction takes the shared ownership-row conflict and fresh accepted
database time. It proves the phase/admission/binding above, a reviewed allowlisted probe
operation, an unextended outer deadline, current restriction, and OD-037 capacity before
committing the distinct immutable `RecoveryProbeIntent`. Each probe:

- is read-only at the provider/peer or monotonic in the restrictive direction;
- has its own stable idempotency identity and four-role recovery-probe lineage, never an ordinary
  `EffectIntent` relabeled after creation;
- may own zero or more bounded attempts: each send-authorized `RecoveryProbeAttempt` commits
  immediately before the first possible byte, and each received result records a bounded
  `RecoveryProbeResponseObservation` before disposition;
- has an explicit timeout, finite attempt/count/byte/rate/age bound, and cannot extend the
  original work, closure, or recovery deadline;
- cannot apply an ordinary domain result, mint approval, generate/synthesize media, sign,
  dispatch, admit a turn, resume, increase mode, create a new normal lineage, or make a pending
  row eligible;
- commits exactly one terminal non-widening `RecoveryProbeDisposition`; an intent with no attempt
  may terminalize as expired, cancelled, superseded, or failed-closed-before-send;
- treats its originating composite fence and source binding as immutable provenance. After crash,
  lease expiry, or takeover, a successor holding the exact current active-draining or recovering
  fence and a current binding to the same source ambiguity may append bounded late evidence and
  CAS a terminal stale/unknown/quarantined disposition. It may not authorize another byte on the
  old intent; a further query needs a newly admitted, separately bounded probe intent; and
- treats timeout, contradictory evidence, or a non-authoritative negative result as unknown,
  never as proof of absence or permission to replay.

Probe-lineage terminality and the underlying source-ambiguity classification are separate axes.
A terminal probe disposition may truthfully remain `unknown`. The bound original
effect/dispatch/rig/lost-tail ambiguity has its own ownership-protected classification, which
must be resolved, permanently safe-quarantined, or accountably disposed before final close.
OD-014 owns ordinary closure/actor-takeover provider/effect/dispatch/rig classification policy;
OD-021 owns any serialized rig protocol; OD-029 owns only lost-tail/PITR/failover disposition.
An unknown probe never becomes known by relabeling, and final close never requires that
historical evidence to lie.

Reviewed provider outcome queries and stage-host state/hold reconciliation may be recovery
probes. Ordinary provider generation, synthesis, audience dispatch, and any irreversible
authority-widening operation are not. Restrictive control remains governed by the safe-direction
exception and never derives widening authority from a probe. A closed session has no actor and
admits no probe; later evidence uses only its separately governed history/restrictive paths.

## Takeover And Recovery

Every initial acquire, restart under a new process incarnation, lease-expiry takeover,
acquisition following forced revoke, disaster failover, and failback enters `recovering`. The
owner performs this order:

1. Prove the exact new composite actor fence and conservative lease horizon.
2. Load the authoritative `StreamSession`, aggregate version, lifecycle, mode, emergency,
   session authorization epoch, rig binding, configuration snapshot, rights, safety, deadlines,
   and capacity state.
3. Reconcile all durable command receipts/outcomes, trigger occurrences/claims, turns, ordinary
   effect intents/attempts/response observations/application dispositions, recovery-probe
   lineages, signing/dispatch records, outbox state, and idempotency records.
4. Apply every known or locally reported restrictive fact first. Missing or unresolved
   `uncommitted_restrictive` evidence keeps safe hold.
5. Classify each pending effect as definitely not send-authorized, possibly sent and
   idempotently queryable, possibly sent/unknown, durably observed but unapplied, superseded,
   expired, or terminal.
6. Expire, cancel, quarantine, or fail-close ineligible work without reopening any terminal
   state or extending a deadline.
7. Advance the session authorization epoch and reconcile stage host whenever audience-bound
   ambiguity exists or cannot be disproved.
8. Prove there is no stale owner, unresolved external effect, ambiguous playout, timer double
   admission, invalid authorization, or missing restrictive evidence.
9. Seal the exact stage-host reconciliation cursor/receipt while stage host remains in
   restrictive recovery hold.
10. Commit `recovering -> active` only through the closed activation barrier below.

Recovery also loads the exact normal-work admission status/epoch. A `draining` session cannot
activate ordinary work: recovery terminalizes the fixed pre-close prefix and completes session
closure. A `closed` session remains terminal and never reacquires or reopens admission.

While ownership remains `recovering`, no ordinary effect attempt or advancing application may
run. Classification calls use only the distinct bounded recovery-probe lineage. If admission is
still exact-open and activation later succeeds, the active owner may revalidate and attempt a
`definitely_not_send_authorized` ordinary effect using its original stable intent/idempotency
identity, or apply a durably observed result only if it remains current and safe. If admission is
non-open, ordinary attempts/applications stay prohibited and drain records only non-advancing
terminal dispositions. Possibly-sent non-idempotent work is never assumed failed and never
replayed automatically.

Recovery activation cannot rely on a final scan followed by an unguarded phase update. One
durable recovery attempt installs a commit-time recovery cut through session/source frontier rows
shared by every durable normal input-promotion/turn-admission source, including command-receipt
and timer-materialization commits. Each source must provide either a source-serialized gapless
committed-prefix manifest or an equivalent commit-time pre-cut/post-cut partition. A database
sequence maximum, allocated ID, timestamp maximum, or nonlocking scan is not a frontier:
reservation before the cut does not make a row pre-cut if its transaction commits after the cut.

The cut fixes every normal input/admission frontier plus command-inbox and timer-materialization
frontiers, including immutable cut-time schedule-cursor values, and a monotonic
recovery-invalidation revision. A later operational cursor is a separate field and is not an
activation-CAS input. Normal input, command, or occurrence work committed after the cut is
durably tagged `post_cut_pending`, cannot be promoted/claimed/admitted during recovery, and is
considered only after activation under its original deadline/missed policy.
Every write that changes classification of pre-cut work, or adds restrictive/ambiguity-bearing
effect, dispatch/playout, authorization, stage-host, or other recovery evidence, advances the
invalidation revision in the same transaction. Every recovery-probe
intent/attempt/response/disposition write bound to this recovery attempt also advances it,
including a successor's terminalization of an old-fence lineage. This prevents continuous
harmless ingress from starving activation without hiding late facts. The activation candidate
durably binds:

- the exact composite actor fence and ownership revision;
- the exact normal-work admission status/epoch and any pre-close drain prefix;
- the expected recovery-input revision and source high-waters;
- every completed classification/disposition, every recovery-attempt-bound recovery-probe lineage as
  terminal/non-widening, and each bound source ambiguity as resolved for the enabled scope or
  held behind an explicit capability disable;
- the sealed stage-host boot/binding/epoch/journal cursor and restrictive-hold receipt; and
- the exact configuration, authorization, safety, rights, clock, and capacity evidence used.

The `recovering -> active` transaction takes the shared ownership-row linearization point and
compares all immutable cut-time frontiers plus bound authority/invalidation revisions and
high-waters; it deliberately excludes the later post-cut operational cursor. Any new
ambiguity-bearing or restrictive evidence invalidates the activation CAS. An unknown or unsealed
peer keeps its capability disabled.
Only an `open` admission gate can activate ordinary work; `draining` follows the bounded closure
path and `closed` remains terminal.
Stage host may leave its sealed recovery hold only through a later authenticated activation/
binding step for the exact accepted epoch; a late local observation invalidates or refuses that
step. Exact physical revisions and protocol fields remain OD-021/034 work, but an open-ended scan
without this barrier is prohibited.

Disaster-recovery generation and site fencing under OD-029 are part of every composite actor
fence in this procedure; they do not replace session ownership. A new recovery site must
establish its non-rollback recovery authority and each session's new ownership generation before
any protected boundary can serve.

### Lost-Tail Recovery

A new recovery generation prevents old authority from becoming current; it does not prove that a
point-in-time restore contains the latest normal-work admission/close cut, command,
effect-attempt, timer, dispatch, or restrictive records. `definitely_not_send_authorized` is valid
only inside a proven-complete authoritative write horizon in the same recovery generation.
Absence of a row after PITR or any nonzero/unknown RPO is not evidence that the operation never
committed or never reached an external boundary.

Recovery identifies the exact unproven interval and affected sessions from trusted WAL/backup/
manifest high-waters and marks it `lost_tail_unknown`. Only trusted zero-loss quorum/WAL/commit
attestation accepted under OD-029 can prove the authoritative PostgreSQL tail complete. Without
that proof:

- an absent or ambiguous old-generation command receipt/idempotency key is not accepted again as
  a new command; normal reissue requires explicit post-reconciliation human disposition and a
  new current-generation intent;
- a restored `open` normal-work admission state whose later epoch/close cut may be in the lost
  tail is atomically superseded under the new recovery generation by
  `draining(lost_tail_quarantine)`, a visible conservative cut/affected interval, restrictive
  holds, and reopen prohibition; the same transaction moves any restored nonterminal session
  lifecycle to `Ending`, preserves only a terminal target proven inside the trusted horizon, and
  otherwise records `unresolved_lost_tail_target`; it cannot accept commands,
  materialize/claim timers, admit turns, or reopen the same session;
- a restored `draining(normal_closure)` whose later drain/final-close tail is unproven preserves
  its historical cause and fixed prefix, adds the monotonic lost-tail overlay/affected interval/
  holds under the new generation, and cannot final-close until OD-029 resolves the unknown tail
  and any ambiguous terminal target; and
- a restored atomic `closed` state remains terminal and ownerless; recovery records any later
  unknown interval and restrictive evidence separately but cannot acquire, reopen, or reconstruct
  missing success from it;
- an effect whose intent/attempt may be in the lost tail is never classified
  `definitely_not_send_authorized`;
  and is not replayed automatically;
- timer slots in the lost interval are not rematerialized or caught up autonomously;
- signing, dispatch, task, and playout scope remains disabled until the exact rig is reconciled;
  and
- newer stops, rights restrictions, deletion, holds, and other restrictive evidence are
  reapplied from independently preserved sources before any activation.

An authenticated stop may always be reasserted through the safe-direction path. Any affected
normal capability stays quarantined when the lost-tail scope cannot be bounded. OD-029 owns the
accepted completeness authority, RPO, high-water custody, and human recovery disposition.

An independently retained non-rollback deny-only ledger may prove only that an
identity/digest/generation/high-water existed, narrow the affected scope, and require
deny/quarantine. It cannot prove that an unlisted operation was absent, close an authoritative
PostgreSQL history interval, reconstruct a command receipt/outcome, effect observation, domain
fact, or success, authorize execution, or become a second system of record. It contains no raw
command/provider/content data or viewer-memory content and cannot share viewer-memory/audit
access roles. OD-017/029/034 own its minimum data, access, retention, and restore proof.

## Safe-Direction Exception

An authorized emergency stop, mode decrease, cancellation, fail-closed admission denial, rights
restriction, or equivalent accepted restrictive action does not wait for normal ownership when
doing so would make the system less safe.

During ownership or PostgreSQL uncertainty:

- every reachable runtime boundary may assert `uncommitted_restrictive`, cancel local work, and
  stop new progression;
- stage host may apply its trusted local stop and watchdog behavior;
- evidence is buffered or retried through the accepted restricted path; and
- every later owner must reconcile the strongest valid restriction before activation.

The boundary cannot report a durable aggregate transition, accepted command completion,
successful rig convergence, resume, or mode increase until authoritative state and peer
evidence are reconciled. This exception cannot mint approval, start generation/synthesis,
dispatch, clear a latch, or make a restrictive state less severe. A boundary that cannot be
reached remains unknown; the effective session stays restricted or stopped and no global
success is claimed. An authenticated stop assertion is applied in the restrictive direction
regardless of its observed session epoch.

## Failure Posture

| Failure or race                                        | Required posture                                                                                                                              |
| ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Lease renewal or ownership query times out             | Outcome unknown; stop ordinary progression/effects and re-read authority before continuing                                                    |
| PostgreSQL unavailable                                 | No acquire, renew, normal mutation, command acceptance, timer firing, or widening effect; safe-direction actuation only                       |
| Old process resumes after pause or partition           | Cached ownership is invalid until exact composite fence/lease is revalidated; late work cannot commit or dispatch                             |
| Two processes race to acquire or take over             | One ownership-row transaction can succeed; only its winner enters `recovering`; loser has no authority                                        |
| Protected commit waits behind revoke/takeover          | It re-reads the changed ownership row under the shared conflict and rejects; an earlier read cannot authorize commit                          |
| `control-api` times out after forwarding               | Caller sees unknown and retries/queries with the same idempotency identity                                                                    |
| Crash before command-receipt commit                    | No acceptance was established; retry may create the first durable receipt                                                                     |
| Crash after receipt but before execution               | Pending command is recovered and processed at least once under one terminal idempotent outcome                                                |
| Command receipt races session closure                  | Shared admission/source CAS puts it in the fixed pre-close prefix or returns no-lineage `session_closed`; no post-begin-close pending lineage |
| Crash while closure is draining                        | Admission remains non-open; takeover terminalizes the fixed prefix and may close, but cannot reopen normal work                               |
| Crash around an aggregate transition                   | State, command outcome, audit, manifest, and outbox are all committed or none are                                                             |
| Crash after effect intent but before attempt           | Only a proven-complete same-recovery horizon proves no send authorization; then a successor may revalidate and allocate the first attempt     |
| Crash after attempt commit, before/during send         | Treat as possibly sent; use reviewed idempotency/query/fence or fail closed, never infer no send                                              |
| Response received, observation not durably recorded    | Recover as possibly sent/unknown; process memory or transport logs cannot recreate success                                                    |
| Observation committed, before application              | Revalidate and apply once if still eligible, otherwise commit non-advancing disposition                                                       |
| Crash or revoke after possible send                    | Treat as possibly sent; use provider idempotency/query or fail closed, never blind replay                                                     |
| Provider/media/safety result arrives after takeover    | Record minimized late evidence; stale composite fence cannot apply, approve, synthesize, or dispatch                                          |
| Signing/dispatch/playout state is ambiguous            | Advance session authorization epoch, invalidate old work, reconcile rig, remain in recovery hold                                              |
| Administrative revoke with possible escaped work       | Atomically rotate restrictive fence/hold and priority-control intent; cloud authority ends, audience convergence unknown                      |
| Recovery input changes before activation               | Recovery revision/high-water comparison fails; reconcile the new fact before another activation attempt                                       |
| PITR restores a previously used ownership number       | New protected recovery generation makes the composite fence distinct; no serving on restored number alone                                     |
| PITR/RPO may omit admission close/command/effect/timer | Mark the bounded tail unknown; force admission non-open and do not infer absence, reopen, reaccept, replay, or rematerialize                  |
| Timer claim expires or fires twice                     | Same occurrence is reclaimed; uniqueness/CAS allows at most one admitted turn and terminal disposition                                        |
| Clock state is stale, regressed, or contradictory      | Do not extend lease/deadline or fire autonomously; hold until the accepted clock profile is proven                                            |
| Safe-direction persistence is unavailable              | Apply the strongest local/process restriction, never claim durable success, and block recovery pending reconciliation                         |

## Audit, Events, And Data Handling

Ownership transitions, normal-work admission transitions/cuts, command intents/receipts/
authorization observations/outcomes, effect intents/send-authorized attempts/response
observations/application dispositions, timer occurrences/claims, recovery barriers, and recovery
classifications are PostgreSQL-authoritative records. Ordinary audit and telemetry contain only
minimized identities, generations, versions, digests, timestamps, deadlines, reason codes, and
outcome classifications. They never copy prompts, candidates, approved text, provider bodies,
media bytes, secrets, identity tokens, viewer-memory content, or unrestricted stage-host
journals.

These records are not automatically domain events. If an accepted event catalog later exposes a
domain fact, ADR-023 determines its aggregate subject, scope, ordering, completeness, protection,
and lifecycle. Commands, receipts, claims, acknowledgements, heartbeats, `SpeechTask`, and
reconciliation requests remain non-event contracts unless a reviewed semantic fact is modeled
separately. No producer may invent an event type or use event delivery as ownership authority.

## Enforcement And Verification

Implementation must provide:

- one ownership repository API that makes protected recovery generation, ownership-row
  linearization, post-conflict database time, phase, generation, owner, lease, and revision
  checks inseparable from acquire/renew/takeover/activate/relinquish/revoke/close;
- transaction helpers that require the exact composite actor fence, ownership-row write conflict,
  fixed lock order, and aggregate version for every ordinary session mutation;
- one monotonic normal-work admission repository/API whose receipt, timer materialization/claim/
  firing, durable input promotion, every normal Turn/attempt/candidate/approval/media/task/
  dispatch progression, effect-intent creation/send authorization/advancing application,
  begin-close, drain, and final-close transactions share the exact admission/source-row conflict
  and cannot reopen `draining` or `closed`;
- no direct provider, media, signing, dispatch, or timer execution path that bypasses durable
  intent and current-owner checks;
- command-ingress APIs that acknowledge only durable receipts, append refreshed authorization
  observations without mutating semantic lineage, and expose disclosure-authorized durable
  outcome lookup;
- one closed restrictive-control dispatcher API that cannot obtain ordinary actor/mutation,
  approval, resume, mode-increase, or `SpeechTask` authority;
- compile-time/dependency boundaries preventing `control-api`, Redis consumers, provider
  adapters, and stage host from impersonating the session actor;
- explicit timeout and cancellation on every database, transport, provider, signing, and
  reconciliation call;
- bounded queues, polls, claims, retries, and recovery scans under OD-037;
- metrics and alerts that distinguish no owner, recovering owner, lease uncertainty, stale
  composite-fence rejection, unknown/expired/reconciliation-required command, effect
  observation/application ambiguity, timer materialization/claim lag, activation invalidation,
  restrictive-control convergence, lost-tail quarantine, and recovery hold without making
  telemetry authoritative; and
- protected ownership/review of ownership, command, timer, signing, dispatch, e-stop, contracts,
  and migration changes.

Required tests include:

- model/property tests for the closed ownership state machine, within-recovery monotonic
  ownership generation, and nonrepeating composite fence;
- PostgreSQL concurrency tests for acquire, renew, expiry, revoke, takeover, aggregate commit,
  post-lock lease time, fixed lock order, write-conflict linearization, and stale composite-fence
  rejection;
- process pause, clock step, partition, database outage, lease-renewal timeout, and dual-writer
  fault injection;
- command canonicalization, conflicting idempotency reuse, duplicate delivery, lost response,
  submission-generation mismatch, lost-tail receipt absence, cross-principal isolation,
  refreshed credential retry/observation deduplication, crash before/after refreshed-observation
  commit, receipt-return disclosure authorization, universal expiry, execution-observation
  selection, concurrent append-versus-execution lineage-revision CAS, deterministic precedence
  and older/incomparable-allow rejection, retryable-versus-nonretryable denial classification,
  policy/revocation/observation-expiry race, receipt/refresh/execution/terminalization at the exact
  database-time deadline boundary, retry-versus-begin-close admission CAS, terminal no-reopen,
  process-clock skew rejection, and every crash boundary;
- command-receipt versus begin-close concurrency, pre-close committed-prefix drain,
  post-begin-close-cut deterministic non-acceptance with no command-lineage append,
  crash/takeover during drain, ordinary claim/execution/successful outcome versus begin-close in
  every ordering, non-open terminal-only drain, no pending accepted normal command after close,
  and safe-direction stop-after-close tests;
- direct viewer/platform/director/content-scheduler input promotion and turn admission versus
  begin-close concurrency, proving post-begin-close-cut raw observations cannot become eligible
  work and no normal turn is admitted under a non-open epoch;
- ordinary `EffectIntent` creation, attempt send authorization, and advancing effect application
  versus begin-close in every ordering, proving post-begin-close-cut ordinary intents/sends/
  advancing applications are rejected, bounded late response observations remain evidence-only,
  prior send-authorized attempts stay possibly sent until safely classified, and draining
  commits only non-advancing dispositions;
- every ordinary Turn/attempt/candidate/selection/approval-mint/media/task/signing/dispatch
  progression versus begin-close, proving no path advances after the cut while bounded
  observation evidence, restrictive action, and terminal/non-advancing disposition remain
  available;
- provider/media/signing/dispatch intent-before-effect, remaining-lease-budget, timeout,
  cancellation, attempt-before-send crash, response-before-observation crash,
  observation-before-application crash, possibly-sent, idempotent query, late result, and stale
  composite-fence tests, plus concurrent `N` attempts/observations proving at most one advancing
  disposition per intent, at most one disposition per observation, and a new domain
  attempt/intent for every retry/rewrite/fallback/provider/semantic change;
- recovery-probe tests across exact active-draining-prefix and recovering-attempt bindings,
  proving ordinary intent/send/application remains blocked when admission is non-open; probe
  intent/attempt/response/disposition crash cuts and idempotency; finite count/byte/rate/age
  bounds; zero-attempt expired/cancelled/superseded/failed-closed terminalization; wrong-prefix/
  wrong-recovery-attempt rejection; crash/takeover successor terminalization under a new current
  fence without old-intent send/replay; no deadline extension; no widening application; terminal
  unknown probe evidence versus separately resolved/safe-quarantined/accountably disposed source
  ambiguity; and negative/timeout/contradictory evidence never proving absence or permitting
  replay;
- takeover tests proving recovery-only behavior, restrictive-evidence precedence, deadline
  non-extension, recovery-probe confinement, source-serialized recovery cuts, preallocated-ID
  late commit/commit reordering, immutable cut-time frontier/cursor snapshots, harmless
  post-recovery-cut ingress advancing only the excluded operational cursor without starving
  activation, every recovery-attempt-bound probe write advancing invalidation, activation rejection for
  any nonterminal probe or enabled-scope unresolved source ambiguity, ambiguity/restriction advancing the
  invalidation revision, no terminal-state reopen, stage-host sealed-cursor/epoch rotation,
  old-queue eviction, and no automatic in-doubt replay;
- timer canonical occurrence/materialization-cursor uniqueness, commit-response loss,
  stale-owner materialization versus takeover, recovering-owner no-create/no-cursor-advance,
  claim-acquisition/reclaim CAS, same-actor concurrent poll, firing, at most one terminal firing
  disposition per occurrence, expired-claim-after-reclaim, missed window, takeover, clock
  uncertainty, bounded materialization/catch-up, admission, and resource-exhaustion tests,
  including frozen schedule cursors and no post-begin-close-cut/non-open occurrence,
  cursor, or storage growth;
- administrative-revoke/dispatch races and safe-direction tests proving immediate reachable
  restriction, actor-independent dispatcher drain/loss, priority reserve, stop dominance,
  truthful unknown audience convergence, no false durable-success claim, and phase-preserving
  revoke that can never reopen `closed`;
- PITR/failover tests proving old recovery, ownership, session-epoch, binding, signing, and
  dispatch authority cannot become current after rollback, plus lost admission-close/command/
  effect/timer/restrictive tails cannot be inferred absent, reopened, or replayed, including
  restored `open`, `draining(normal_closure)`, and atomic `closed` cases; exact
  lifecycle/admission-axis coherence; monotonic lost-tail overlay; unresolved-target blocking;
  and no final close without accountable disposition;
- reconstruction tests from PostgreSQL plus bounded stage-host evidence without Redis or
  process-memory authority, including non-open admission recovery and proof that closed sessions
  contain no accepted nonterminal command/occurrence.

The verification matrix must cut the process at every transaction/effect boundary, including
before and after receipt/initial authorization observation, refreshed-observation append/
deduplication, authorization-lineage revision CAS, ordinary command claim/execution/
terminalization, effect intent, send-authorized attempt, first possible send byte, external
response, response-observation commit, application commit, signing, dispatch, acknowledgement,
timer materialization/claim/firing disposition, direct input promotion, turn admission,
begin-close admission cut, each bounded drain disposition, schedule-cursor freeze, atomic final
close, ownership renewal, revoke, relinquish, takeover, recovery-input change, stage seal, and
activation. Final close must also race revoke/relinquish/takeover in every serialization order
for each terminal lifecycle target (`ended`, `cancelled`, and `failed`).

## Schema And Implementation Gate

No conceptual record or state in this ADR authorizes a table, migration, API schema, queue,
worker, timer library, provider integration, signing implementation, or deployment default.
Before implementation:

1. the Runtime Implementation Gate must be closed through the protected authority process;
2. ADR-003 and this ADR must be accepted or superseded for the exact scope;
3. ADR-019 must be accepted and OD-022 must decide the exact command principal/source,
   authorization-observation selection/precedence, disclosure, retryable/nonretryable denial,
   revocation, and step-up/presence behavior realized;
4. OD-014 must approve trigger/scheduling/recovery policy, while OD-035 and OD-037 approve
   numeric timing and resource bounds;
5. OD-021 must approve serialized non-event command/receipt/outcome and deterministic
   session-closed non-acceptance, refreshed-authorization evidence handoff, task/control,
   acknowledgement, binding-activation, and reconciliation sources;
6. OD-034 must name the exact lifecycle-catalog rows authorized for realization;
7. before enabling restore, failover, failback, or more than one candidate writer site, OD-029
   must approve and prove the independently retained recovery-generation/high-water authority
   and post-restore actor/audience fencing profile;
8. any database work must have a linked accepted migration ADR; and
9. protected owners must review contracts, safety, signing/dispatch, stage-host, e-stop, and
   provider changes as applicable.

## Alternatives Considered

### Aggregate Optimistic Concurrency Alone

Rejected. It prevents conflicting durable state commits but cannot fence an external effect
started by an old actor.

### Redis Lock Or Orchestrator Lease

Rejected as authority. Either may improve routing or scheduling, but Redis is replaceable
transport and orchestration health does not participate in the authoritative PostgreSQL
transaction.

### Exactly-Once Command Or External Delivery

Rejected. Network and process failures make exactly-once delivery claims misleading. At-least-once
delivery plus durable intent, idempotency, terminal outcome, and effect fencing is testable.

### One Epoch For Ownership, Session, Rig, And Recovery

Rejected. These values have different writers, scopes, invalidation effects, and recovery
semantics. Collapsing them creates false comparisons and privilege transfer.

### In-Memory Timers Reconstructed From Business Rows

Rejected as the durable model. A timer wheel may optimize wake-up, but canonical nominal
occurrence, materialization cursor, current claim token/revision, deadline, and firing disposition
are required to prove no duplicate or silent loss.

### Immediate Active Takeover

Rejected. A successor cannot safely progress before it classifies pending commands, effects,
timers, restrictive evidence, and possible stage-host playout.

## Consequences

- Session ownership and recovery become explicit, durable, fenced, and reconstructable.
- `control-api` remains stateless while accepted commands survive process failure and ambiguous
  responses have a truthful recovery path.
- Provider calls can still consume cost after a forced revoke, but their stale results cannot
  advance the broadcast; cloud revoke alone does not claim immediate audience cessation and
  non-idempotent ambiguity intentionally reduces availability.
- Recovery may flush queued work and advance the session authorization epoch more often, trading
  continuity for bounded audience safety.
- Durable receipts, four-record effect lineage, canonical timer materialization/claims, recovery
  barriers/history completeness, and restrictive-control evidence add schema and transaction
  complexity. That cost is accepted because one logical actor is otherwise only an aspiration.
- No runtime, contract, migration, or production behavior is authorized by this proposal.

## OPEN Decisions

- OD-014: trigger taxonomy and eligibility, segment priority/interruption, retry/rewrite/fallback
  caps, per-family missed-occurrence/catch-up policy, pre-close input/work drain and terminal
  disposition policy, typed recovery-probe allowlist/binding/non-widening policy, and terminal-
  unknown versus bound-source classification/quarantine/accountable-disposition policy for
  ordinary closure/actor takeover, plus protected acceptance of this structural
  ownership/recovery model.
- OD-035: lease duration, renewal cadence, database/local-clock uncertainty margin, takeover and
  recovery holds, command/trigger horizons, ordinary-provider and recovery-probe attempt budgets,
  and every other numeric deadline/timeout value.
- OD-037: command authorization-observation growth/execution reserve and auth-lineage/claim/
  execution, ordinary effect intent/send/application, recovery-probe intent/attempt/response/
  disposition count/byte/rate/age/concurrency, timer materialization/claim/firing/cursor,
  restrictive-control, every viewer/platform/director/content-scheduler input and Turn/candidate/
  selection/approval/media/task/signing/dispatch progression, begin-close, bounded late-evidence/
  terminal non-advancing drain, final-close, queue/poll/scan/retry/fairness/priority, and
  recovery-drain bounds.
- OD-021: canonical serialized source, protected idempotency-key scope, canonicalization/digest
  rules, same-protected-scope/key/same-digest original-record reuse,
  same-protected-scope/key/different-digest conflict with no second lineage, no-lineage
  `session_closed`, language generation, command receipt/outcome and
  refreshed-authorization-observation framing, downstream-verifiable
  task-versus-restrictive-control ordering, sealed recovery cursor, and stage-host
  task/control/acknowledgement/reconciliation contracts.
- OD-022: command principal/source capabilities, receipt/outcome disclosure, append-only
  authorization-observation semantics, deterministic concurrent selection/precedence,
  retryable versus nonretryable denial, revocation, presence, step-up, and separation of duties.
- OD-029: same-site PITR/restore and cross-site writer fencing, independently retained
  non-rollback recovery-generation or trusted high-water implementation, authoritative lost
  admission/close-cut and other tail completeness/ledger/quarantine/final-close disposition,
  restored-open/draining/closed lifecycle/admission coherence, monotonic lost-tail overlay,
  accountable `unresolved_lost_tail_target` resolution, restored
  session-epoch/signing/binding supersession, RTO/RPO, and failover/failback authority.
- OD-033: whether any ownership, command-outcome, effect, or timer semantic fact becomes a
  domain event and, if so, its exact subject/scope/catalog profile.
- OD-034: physical ownership/transition, normal-work admission/closure drain,
  recovery barrier/history completeness, command and authorization-observation dedupe identity/
  lineage-revision/selection-CAS, four-record ordinary effect, distinct/discriminated four-role
  recovery probe, timer/materialization/claim, restrictive-control, audit, access, and retention
  schemas.
- Concrete runtime placement, the exact PostgreSQL conflict primitive and isolation level that
  prove the decided ownership-row linearization property, workload identity, command API
  shape/status codes, notification mechanism, signing service, provider idempotency profile, and
  operational alert thresholds.
