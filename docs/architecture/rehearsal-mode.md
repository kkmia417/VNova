# Rehearsal Mode

Status: Proposed normative test architecture; non-authorizing; implementation pending

Rehearsal mode executes the same contracts, state machines, safety gate, approved media path, signed dispatch, and stage-host queue used by production. Only external adapters are replaced.

Its core lifecycle, safety, privacy, expiry, and topology constraints come from Proposed ADR-003,
ADR-008, and ADR-018 plus Accepted ADR-016 and ADR-017. Enabled scenarios additionally depend on
the Proposed feature decisions in ADR-004, ADR-007, ADR-010, ADR-011, ADR-015, ADR-019 through
ADR-022, ADR-024, and ADR-025, with ADR-023 treated as the foundation event companion. Rehearsal
requirements do not authorize those capabilities; they define the evidence each accepted
capability must later produce.

## Required Test Doubles

- Fake OBS implementing the production adapter contract.
- Fake VTube Studio implementing the production adapter contract.
- Virtual audio sink reporting start, stop, level, underrun, and rendered digest.
- Deterministic per-host clocks with configurable offset, drift, uncertainty, sample age, and
  round-trip delay while preserving raw UTC and local-monotonic observations.
- Controllable transport for latency, duplication, reordering, corruption, disconnect, and reconnect.
- Mock provider gateways with scripted timeout, partial failure, fallback, and cancellation behavior.
- Fake identity provider, authorization policy, operator-presence clock, and restricted-data store.
- Deterministic configuration resolver with immutable roots/versions, atomic activation sets,
  typed scopes, current epochs, restrictive latches, exact snapshots, and stale-cache controls.
- Closed fake renderers for every enabled caption, overlay, alert, scene-text, username, and avatar surface.
- Fake rights/evidence service with grant expiry, conflict, suspension, revocation, and partition controls.
- PostgreSQL/Redis fault harness proving recovery from PostgreSQL without transport history.
- Deterministic actor harness with two runtime process incarnations, PostgreSQL-authoritative
  recovery/ownership composite fences, shared ownership-row conflict/post-lock clock,
  controllable transaction-response loss, submission-generation command receipts/outcomes,
  append-only authorization observations, monotonic normal-work admission/source CAS and closure
  drain, four-record ordinary-effect crash cuts, distinct four-role active-draining/recovering
  recovery-probe lineages, canonical timer materialization/current claims,
  committed-prefix recovery cuts/invalidation revisions, sealed rig cursors, restrictive
  dispatcher, and recovery-only takeover.
- Synthetic privacy inventory, provider/local-copy, backup/restore, tombstone, hold, deletion,
  quarantine, and independent-absence-verifier harness.
- Fake source/build/provenance/release/update/target chain supporting artifact substitution,
  compromised authority, promotion hold, rollback, and trusted rebuild.
- Multi-boundary recovery harness supporting stale recovery points, writer/actor split brain,
  independently retained recovery generation/high-water, lost command/effect/timer/restriction
  tails, dependency loss, failover, failed recovery, and failback.
- Controllable telemetry/alert pipeline with collector/exporter/store/route loss, stale or
  contradictory signals, bounded buffers, prohibited attributes, delivery acknowledgement, and
  dashboard query versions.
- Capacity, quota, billing, and cost harness with bounded queues/resources, protected reserves,
  skewed tenants/sessions, delayed reconciliation, hard/soft limits, retry/fallback amplification,
  and measured backlog drain.
- Workload/fault driver that executes immutable load, stress, spike, soak, chaos, abort, recovery,
  and cleanup manifests without test-only production bypasses.

## Required Scenarios

- Complete approved turn from trigger through simulated playback and audit reconstruction.
- Concurrent acquire/renew/revoke/lease-expiry/takeover and protected commit, process pause, lock
  wait, post-lock clock, and database partition, proving one active composite fence,
  stale-transaction rejection, and safe-direction restriction.
- Command response loss before/after durable receipt and domain commit, duplicate/conflicting
  idempotency with same-protected-scope/key/same-digest reuse versus
  same-protected-scope/key/different-digest conflict, refreshed
  authorization observation dedupe/commit-response loss/saturation, append-versus-execution
  lineage-revision CAS and deterministic precedence, fresh database-time deadline boundaries,
  stale submission recovery generation, lookup/execution authorization expiry, universal command
  expiry, successor execution, and queryable terminal outcome.
- Begin-close racing command receipt/authorization refresh/claim/execution, viewer/platform/
  director/content-scheduler input promotion, timer materialization/claim/firing, direct Turn
  admission, ordinary effect intent/send/advancing application, and every ordinary candidate/
  selection/approval/media/task/signing/dispatch progression; prove one fixed committed prefix,
  no-lineage `session_closed`, raw-input non-promotion, frozen recurring cursors, bounded
  evidence-only late observations, bounded terminal non-advancing drain, atomic
  `ended`/`cancelled`/`failed` final close, no post-begin-close-cut ordinary growth, and
  safe-direction stop availability.
- Ordinary external-effect crash at intent, send-authorization, first possible byte, response,
  response-observation, and application commit for idempotent/queryable/non-idempotent providers;
  possibly-sent work is not blindly replayed and stale/late results do not advance.
- Recovery-probe crash at intent, send authorization, first possible byte, response observation,
  and disposition under both exact active+draining-prefix and
  recovering+recovery-attempt/source-ambiguity bindings; wrong binding, ordinary-lineage
  relabeling, zero-attempt terminalization, originating-fence provenance/current same-source
  successor terminalization without resend, idempotency collision,
  count/byte/rate/age/concurrency exhaustion, deadline extension, widening application,
  negative/timeout/contradictory terminal-unknown evidence versus separately resolved/
  permanently safe-quarantined/accountably disposed source ambiguity, replay authorization, and
  final close with a nonterminal probe or unresolved bound source ambiguity all fail closed.
- Concurrent canonical timer materialization, cursor response loss, duplicate/reordered wake-up,
  stale-owner takeover, recovering-owner no-create/no-cursor-advance, claim expiry/reclaim/late
  firing, missed window, clock uncertainty, one turn admission, one terminal firing disposition,
  bounded materialization/catch-up, and backlog exhaustion.
- Recovery cut with preallocated-ID late commit/commit reorder, immutable cut-time source/
  schedule-cursor snapshots, continuous harmless post-cut ingress advancing only the excluded
  operational cursor without activation starvation, every recovery-attempt-bound probe write
  plus restrictive/ambiguity evidence advancing invalidation after each frontier, activation
  rejection for a nonterminal probe or enabled-scope unresolved source ambiguity, sealed-rig
  invalidation, and activation CAS rejection.
- Administrative revoke racing signing/dispatch, actor-independent restrictive-control delivery,
  priority-lane loss/retry, exact rig acknowledgement, and truthful unknown audience convergence.
- PITR with repeated local generations and lost admission/close-cut/command/effect/timer/
  restriction tail, proving a restored `open` admission atomically becomes coherent
  `Ending`/`draining(lost_tail_quarantine)` with a proven or explicitly unresolved target, a
  restored `draining(normal_closure)` gains a monotonic lost-tail overlay without changing its
  historical cause, a restored atomic `closed` session stays closed/ownerless, and no reopen,
  reacceptance, Turn admission, replay, rematerialization, unresolved-target final close, or
  audience enablement follows from absence.
- Candidate expiry at every boundary, including immediately before playback.
- Safety timeout with zero autonomous speech and mode degradation.
- Provider fallback returning through the same safety gate.
- Signed-task tamper, replay, wrong-session, expired-key, and media-digest rejection.
- Cloud-link loss followed by watchdog mute and BRB scene.
- Local hard e-stop while cloud and operator console are unreachable.
- Offline observation buffering, reconnect, deduplicated ingest, raw clock evidence, derived
  cross-host timeline, and conservative deadline mapping under stale/uncertain samples.
- Audio underrun and silence-threshold detection.
- Outbox commit crash points, duplicate delivery, poison input, Redis loss, and PostgreSQL-only reconstruction.
- Typed event subject/scope substitution, cross-environment denial, multiple events per aggregate
  version, mutation without an event, filtered empty/subset routing, missing event tail, whole
  transition loss, conflicting manifest/count, stale expected-delivery high-water,
  causal-position collision, cross-lane reorder, trusted envelope-version downgrade conflict,
  profile-only event-contract evolution/historical replay, restrictive reclassification, stale
  projection freeze, and PostgreSQL reconciliation.
- Draft/published-version separation; concurrent scoped initialize/activate/replace/deactivate/
  rollback; partial-bundle abort; deactivation fallback/widening; conflicting/incomparable scope;
  stale activation/eligibility epoch/cache; definition/set withdrawal during work;
  family-specific in-flight disposition; forward rollback; scheduled-intent cancellation,
  supersession, stale due-time revalidation and clock uncertainty; emergency disable during
  database loss; and deliberate re-enable.
- Turn/attempt snapshot pinning across retry, provider fallback, reconnect, replica lag, current
  activation change, restore, definition withdrawal, and content deletion.
- PostgreSQL/outbox outage during cloud freeze or mode decrease, proving immediate restrictive
  actuation and no resume before durable reconciliation.
- Operator authorization denial, presence expiry, confirmed mode increase, immediate mode decrease, and no automatic restoration.
- Concurrent stop/resume, process restart, stale challenge, partition reconciliation, and a new post-resume epoch.
- Actor takeover after possibly sent signing/dispatch/control/playout, forcing session
  authorization-epoch rotation, old-queue eviction, exact-rig reconciliation, and no new work
  while ownership is recovery-only.
- Stage-host power loss at acceptance, queue commit, artifact fetch, pre-playback, adapter start,
  completion, and terminal acknowledgement, with no lost accepted identity or automatic in-doubt
  replay.
- Voice-rights expiry or revocation before synthesis, dispatch, queue acceptance, playback, replay, and export.
- Every enabled surface's normalization, final-context moderation, expiry, neutral clear, fail-closed timeout, and emergency disable.
- Viewer-memory deletion through embeddings, caches, restore paths, and independent absence verification.
- Personal-data exposure through ordinary telemetry, provider/partner, public surface, endpoint,
  and local-copy paths, with a minimized copy manifest and human notification-decision handoff.
- Restore older than a deletion, hold, rights revocation, access revocation, stop, or restrictive
  epoch, proving quarantine and current-state precedence before readability.
- Dependency/build/artifact/signing/update compromise, promotion hold, target inventory, trusted
  rebuild or safe disable, rollback, and deliberate target-scoped re-enable.
- Multi-system recovery with PostgreSQL/object/identity/provider/rig loss, writer fencing,
  PostgreSQL-backed transport rebuild, stale-authority rejection, failback, and no automatic
  resume or mode increase.
- Telemetry collector/exporter/store/route loss, alert delivery failure, stale/disagreeing
  dashboards, restrictive mode ceiling, out-of-band containment, route revalidation, and
  deliberate recovery.
- Queue/worker/connection/storage/Redis/object/rig/journal/provider quota and cost saturation,
  proving protected reserves, fair admission, deterministic shedding, bounded retry/fallback,
  fail-closed safety capacity, backlog drain, and recovery hold.
- Representative load, stress, spike, soak, chaos, abort, rollback, and cleanup runs satisfying
  the [acceptance contract](../governance/load-soak-chaos-acceptance.md).

## Determinism And Evidence

Tests advance virtual time explicitly and do not depend on arbitrary sleeps. Each scenario
asserts emitted events, persisted state, activation/restriction epochs, exact configuration
snapshots, queue state, adapter calls, audio outcome, and operator-visible status. A synthetic
session must be reconstructable as subject-lane causal positions plus raw clock observations and
an explicitly derived incident timeline; the report never invents one authoritative global
event order.

Each evidence run records the commit, lockfiles, generated-contract digest, scenario manifest,
event catalog/profile versions, subject/scope mappings, policy/prompt/provider/voice/surface
versions, activation set/transition/epoch and resolved-snapshot IDs, deterministic seed,
actor process/recovery/ownership composite fence/transition, ownership-row ordering/post-lock
time, normal-work admission epoch/closure cause/fixed prefix/final-close disposition, command
submission generation/receipt/authorization observation/outcome, ordinary effect
intent/send-authorized attempt/response observation/application disposition, recovery-probe
intent/originating fence/attempt/response/terminal disposition plus current-successor/source
binding and source-ambiguity classification, trigger canonical key/materialization cursor/
current-claim token/disposition, recovery cut/revisions/sealed cursor/lost-tail disposition,
restrictive-control attempt/acknowledgement, virtual-time schedule, adapter versions, workload/
fault manifests,
queue/resource/alert/clock/lifecycle profile versions, expected outcomes, actual outcomes,
abort/cleanup state, and artifact hashes. Restricted content and rights evidence are referenced
by privacy-reviewed IDs rather than copied into the ordinary test report.

Runbook exercises map their declared symptoms, containment actions, recovery checks, and exit
criteria onto these deterministic scenarios. The evidence record additionally names response
roles, decision points, observed alerts, sanitized incident timestamps, findings, and remediation
owners. A passing simulator run can advance applicable evidence to `Rehearsed`; it cannot establish
target-hardware validation or production authorization. See the
[operational readiness review packet](../governance/operational-readiness-review.md).

## Adapter Parity

Fake and live adapters must pass a shared contract suite. Live OBS and VTube Studio adapters remain disabled until their human-reviewed implementation passes parity against the same behavioral tests used by the fakes.

The simulator cannot weaken validation, authentication, expiry, ordering, safety, rights, or
authorization semantics. Test-only bypasses are forbidden in production artifacts and the
artifact verifier must prove their absence. Target-hardware e-stop, timing, audio, adapter, and
network evidence remains a separate live-readiness gate.
