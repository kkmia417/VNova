# Load, Soak, And Chaos Acceptance

Status: Proposed evidence contract; no workload, target, blast radius, numeric threshold, test
execution, or production authorization

Governing sources:

- [`AGENTS.md`](../../AGENTS.md)
- [Production quality attributes](../architecture/production-quality-attributes.md)
- [Latency budget](../architecture/latency-budget.md)
- [Capacity, backpressure, and cost governance](../architecture/capacity-backpressure-and-cost-governance.md)
- [Observability, SLI/SLO, and alerting](../architecture/observability-sli-slo-and-alerting.md)
- [Rehearsal mode](../architecture/rehearsal-mode.md)
- [ADR-019: authentication, authorization, and operator roles](../adr/0019-authentication-authorization-and-operator-roles.md)
- [ADR-023: event subject, scope, correlation, and ordering lanes](../adr/0023-event-subject-scope-correlation-and-ordering.md)
- [ADR-024: versioned configuration and scoped activation](../adr/0024-versioned-configuration-and-scoped-activation.md)
- [ADR-025: session actor ownership, command ingress, and fencing](../adr/0025-session-actor-ownership-command-ingress-and-fencing.md)
- [Threat model](../security/threat-model.md)
- [Operational readiness review](operational-readiness-review.md)

This packet prevents a single happy-path benchmark, average latency, or unbounded fault injection
from being called production evidence. It defines the metadata and invariant checks required
before protected humans approve a concrete performance or resilience test plan.

## Test Classes

| Class          | Purpose                                                                                      | Required distinction                                                                                           |
| -------------- | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Baseline       | Establish deterministic single-path and low-contention behavior                              | Not capacity evidence; validates instrumentation and expected lifecycle                                        |
| Load           | Exercise the reviewed expected workload and mix                                              | Proves steady operation only for the named profile and target                                                  |
| Stress         | Increase one or more resources toward and beyond the accepted bound                          | Proves controlled admission, shedding, fail-closed behavior, and recovery rather than maximum throughput alone |
| Spike          | Apply abrupt arrival, reconnect, or fan-out change                                           | Proves reserve isolation, queue bounds, no retry storm, and stable restriction                                 |
| Soak           | Sustain the accepted workload long enough to expose accumulation                             | Proves bounded memory/storage/task/connection growth, rotation, compaction, and operational stability          |
| Chaos          | Inject named dependency, process, network, clock, storage, identity, provider, or rig faults | Proves blast-radius controls, restrictive behavior, alert/runbook execution, and recovery                      |
| Recovery/drain | Start from a declared backlog, partition, restart, or failover state                         | Proves authoritative reconciliation, bounded drain, old-work rejection, and no automatic mode increase         |

Combining classes is permitted only when the manifest still identifies each hypothesis,
independent variable, expected restriction, and acceptance result. A test that changes workload,
software, target, and fault simultaneously without attribution is an experiment, not acceptance
evidence.

## Authority And Safety Boundary

Every execution requires a human-approved plan naming:

- accountable test commander and safety, SRE, security, privacy, data, provider, stage-host, and
  product roles as applicable;
- environment, target, rig, provider/test double, data classification, and audience isolation;
- exact commands and credentials through a protected target-specific procedure;
- permitted blast radius and systems explicitly out of scope;
- local/cloud stop paths independent from the fault injector and tested before the run;
- abort authority available without confirmation, including local rig control where applicable;
- evidence store, retention, incident escalation, cleanup, and restoration owner.

No test may use a live public audience, unrestricted personal data, production secrets, real rights
evidence, or unreviewed provider spend merely because the test is labeled rehearsal. Production
fault injection requires a separate deployment-scoped authorization and cannot be inferred from
this document.

## Immutable Test Subject

The plan binds:

- repository and base/candidate commit identities;
- release, artifact, provenance, complete event contract/framing/scope/subject/ordering/
  completeness/protection, definition draft/version/set eligibility, activation binding/
  transition/schedule/epochs/resolved snapshot, policy, prompt/persona, provider/model, surface,
  voice/rights, recovery/ownership fence, command/effect/timer/recovery-barrier profile,
  restrictive-control protocol, lifecycle catalog, schema, migration, and contract versions;
- deployment topology, region/failure domain, machine/runner, exact rig hardware/software,
  network, storage, database, Redis, object, identity, telemetry, and alert-route versions;
- dataset/fixture manifest, deterministic seeds, virtual/real clock model, and workload-generator
  version;
- every fake/live adapter and the parity evidence that permits its use.

A source, configuration, topology, target, data, fault, or instrumentation change after approval
creates a new subject. Results from a different subject may inform review but do not silently
transfer acceptance.

## Workload Manifest

The workload is a versioned, reviewable artifact containing:

- hypothesis and capability/user outcome being evaluated;
- trigger mix, session count/distribution, segment/category mix, mode, surfaces, languages, and
  operator behavior;
- arrival model, bursts, concurrency, per-session fairness/skew, payload size classes, duration,
  warm-up, steady-state, cool-down, and drain phases;
- generation, safety, operator review, TTS/media, provider failure/fallback, artifact, dispatch,
  rig, and archive behavior;
- database/outbox, subject-lane distribution/hot aggregates, Redis, consumer, activation
  transition/resolution/cache, ownership-row contention, submission-generation command inbox,
  authorization-observation refresh/append/selection and bound rejection, four-record ordinary
  effects, distinct four-role active-draining/recovering recovery probes, canonical timer
  materialization/current claims, every normal input/Turn admission source, begin-close
  committed-prefix/frozen-cursor drain and atomic final close, recovery frontier/lost-tail
  quarantine, restrictive-control priority lane, object, local journal, telemetry, and evidence
  load;
- expected retries, expiries, cancellations, rejections, fail-closed outcomes, reconnects, and
  late results;
- cost/quota reservation and hard containment;
- source-data classifications and synthetic-data guarantees;
- exact numeric expectations only after their accountable OPEN decisions are closed.

Production acceptance uses representative tail, skew, failure, and background work rather than
only uniform average requests. Synthetic content must exercise equivalent schema, size,
classification, safety-category, renderer, and lifecycle behavior without embedding prohibited
data.

## Fault Manifest

Each fault specifies:

- target boundary and failure hypothesis;
- trigger, start, duration/termination, scope, and maximum blast radius;
- whether the fault is omission, delay, corruption, duplication, reorder, partition, crash,
  restart, clock error, ownership-row race, preallocated-ID late commit, recovery-frontier change,
  PITR/lost tail, restrictive-control loss, capacity exhaustion, stale authority, malicious
  substitution, or compromised identity;
- expected detection, alert, mode ceiling, local/cloud containment, queue/resource effect, and
  runbook entry;
- authoritative recovery source and explicit actions that must remain impossible;
- observation/evidence required to prove both injection and removal;
- abort conditions and cleanup.

Fault-injection tooling has no authority to mint approval, bypass authentication, alter protected
policy, disable local e-stop, or access unrestricted production data. A test-only bypass is not a
valid simulation of a production boundary.

## Execution Phases

1. **Preflight:** prove immutable subject, target isolation, stop paths, owners, telemetry/alert
   health, authoritative baseline, reserves, data controls, and rollback.
2. **Baseline:** run a known deterministic path and verify signal semantics before load/faults.
3. **Ramp:** enter the approved workload without skipping intermediate resource observations.
4. **Steady state:** hold the named profile and collect complete tail/outcome evidence.
5. **Fault or saturation:** inject only the approved condition and verify immediate restrictions.
6. **Recovery/drain:** remove the fault, reconcile authoritative state, drain eligible work under
   bounds, and reject stale/expired/in-doubt work.
7. **Exit:** prove target restoration or continued safe hold, artifact/evidence custody, cost
   reconciliation, cleanup, and invalidation of test credentials/data.
8. **Independent review:** compare evidence with the predeclared acceptance contract; do not tune
   the contract after seeing results.

Skipping a phase is recorded as missing evidence, not a pass.

## Immediate Abort Conditions

The test commander or any authorized local safety operator aborts immediately when:

- actual public or out-of-scope audience output could occur;
- local hard stop, cloud freeze, watchdog, or independent control is unavailable;
- unapproved raw, unsafe, expired, wrong-session, wrong-epoch, deleted, revoked, or unauthorized
  content reaches a broadcast/media boundary;
- personal/restricted data, secrets, credentials, rights evidence, or malicious payload enters an
  unauthorized signal, artifact, provider, support, or evidence path;
- writer/actor/rig authority becomes split or cannot be fenced;
- blast radius, spend, quota, data volume, target, duration, or fault differs materially from the
  approved manifest;
- authoritative state, required audit/evidence, clock validity, or test instrumentation becomes
  too uncertain to evaluate safety;
- safety/control reserve, stop responsiveness, or current playout isolation cannot be proven;
- the approved abort or rollback path fails.

Abort is idempotent, has no confirmation or reason precondition, and moves every affected target
to the safest available state. Investigation and recovery occur after containment.

## Acceptance Contract

### Zero-Tolerance Invariants

No error budget, percentile, sample, or residual-risk decision can excuse:

- construction of `ApprovedResponse` outside `packages/safety`;
- mint/rehydration of `ApprovedResponse` for an unselected candidate, a candidate owned by another
  turn, or a stale/concurrently changed selection, or mutation of selection after mint;
- raw generated text crossing a public TTS/media/dispatch boundary;
- safety/fallback bypass or autonomous speech without a determinate verdict;
- playback after expiry, cancellation, invalid epoch, invalid signature, rights/surface denial, or
  emergency stop;
- Redis/local/telemetry state replacing PostgreSQL authority;
- an ordinary session mutation, approval progression, effect start/application, signing, or
  dispatch committing under a stale composite actor fence, expired lease, non-`active` ownership
  phase (including an exact current `recovering` fence), or ownership-row linearization bypass;
- a `closed` session reopening, or administrative revoke reducing terminal/restrictive state;
- an expired normal command mutating domain state, one command intent producing multiple domain
  transitions, or an idempotent retry disclosing a receipt/outcome without current disclosure
  authorization;
- an ordinary command claim/execution/successful outcome committing under a non-open admission
  epoch, or receipt/authorization-observation/execution passing its deadline because of process
  clock skew or lock-wait time;
- an authorization observation appended after command terminality/deadline, beyond its accepted
  count/byte/rate bound, or used after expiry/newer revocation epoch; or observation overload
  consuming the protected execution-reauthorization reserve;
- command execution surviving a concurrent authorization-lineage revision change, selecting an
  older allow over a newer/incomparable allow/deny/step-up/unavailable observation, or applying an
  ambiguity without the accepted deterministic fail-closed precedence;
- any normal command lineage, eligible input, timer occurrence/claim, or Turn created/admitted
  after the session admission gate becomes non-open; any ordinary effect intent/send
  authorization/advancing application or other ordinary
  candidate/selection/approval/media/task/signing/dispatch progression committing after that
  cut; any recurring cursor advancing after drain; any final close with accepted nonterminal or
  unsafely classified pre-close work, a nonterminal recovery probe, a bound source ambiguity not
  resolved/permanently safe-quarantined/accountably disposed, or an unresolved target; or
  PITR-lost closure restoring admission to open;
- a recovery probe sharing/relabeling an ordinary effect lineage, lacking exact
  active+draining-prefix or recovering+recovery-attempt/source binding, exceeding its finite
  attempt/count/byte/rate/age/concurrency or deadline, lacking a zero-attempt terminal path,
  requiring the stale originating fence to terminalize, resending an old-fence intent,
  applying/widening ordinary state, treating terminal `unknown` as source resolution, or treating
  negative/timeout/contradictory evidence as absence or replay authority;
- one effect intent producing more than one authority/domain-advancing observation, one
  observation receiving more than one application disposition, or a policy retry/fallback/
  provider/semantic change reusing the old domain attempt/intent;
- a stale or superseded timer claim firing, one canonical occurrence admitting more than one
  turn, one occurrence receiving more than one terminal firing disposition, or pre-cut/
  post-cut-pending normal work being claimed during recovery;
- PITR/lost-tail absence being treated as nonoccurrence, command reacceptance, effect replay,
  timer rematerialization/catch-up, or audience-enable authority;
- an unsealed or wrong boot/binding/epoch rig accepting audience work, or any boundary claiming
  audience convergence without exact stage-host acknowledgement;
- an event contract/framing/scope/subject/classification mismatch, conflicting causal position or
  manifest, missing transition tail, or incomplete authorization-changing projection widening
  authority;
- mutable reviewed identity, partial/mixed activation, implicit deactivation fallback, early/stale
  schedule, stale activation/eligibility epoch or cache widening eligibility, backward rollback,
  inferred `latest`, or configuration activation minting another authority;
- viewer-memory content entering audit or another prohibited data boundary;
- loss of independent local e-stop;
- unbounded resource growth or automatic replay of `playing_or_in_doubt` work.

Any occurrence fails the run and invokes incident response.

### Performance And Reliability Evidence

The approved plan defines pass/fail rules for:

- end-to-end and per-stage tail latency by trigger, mode, provider/profile, surface, and outcome;
- admission, queue depth/bytes/oldest age, expiry, rejection, cancellation, fail-closed, and
  shedding rates;
- command authorization-observation count/bytes/append rate/oldest age, bound rejections,
  same-protected-scope/key/same-digest reuse and
  same-protected-scope/key/different-digest conflict counts, refresh dedupe/commit-response-loss
  outcomes, lineage-revision CAS contention, current-selection latency, and protected
  reauthorization-reserve saturation;
- command receipt/auth-refresh/claim/execution/widening-outcome, viewer/platform/director/
  content-scheduler input, timer materialization/claim/firing, Turn, ordinary effect
  intent/send/application, and candidate/selection/approval/media/task/signing/dispatch
  admission-CAS contention; recovery-probe intent/attempt/response/disposition
  count/bytes/rate/age/concurrency, binding rejection, zero-attempt terminalization, stale-fence
  successor terminalization-without-resend, terminal/non-widening/terminal-unknown rates, bound
  source-ambiguity age/disposition, and activation-invalidation contention; pre-close prefix
  size/age/drain rate; bounded late-evidence/non-advancing disposition rate; frozen-schedule
  count; close latency/abort/retry; and zero post-begin-close-cut ordinary-work growth;
- throughput and fairness without safety/control priority inversion;
- provider/quota/cost, database/outbox, Redis/consumer, object, rig, journal, and telemetry
  saturation;
- subject-lane contention and ordered publication, aggregate-version/event-index and
  manifest/high-water completeness conflicts, activation/eligibility-state CAS contention,
  scheduler due-time validation, resolver/cache freshness, and restrictive-change convergence;
- errors, unknown/late results, retry/fallback amplification, circuit behavior, and correlated
  failure;
- CPU, memory, task/thread, connection, file-descriptor, storage, cache, journal, and exporter
  growth;
- backlog drain time/rate, poison handling, stale-work rejection, and stable post-recovery
  headroom;
- alert detection/delivery/acknowledgement, runbook action, dashboard freshness, and evidence
  completeness.

Means alone cannot establish a tail or failure-boundary claim. Missing/late telemetry cannot be
dropped from the denominator to create a pass.

### Soak Stability

The plan predefines how to detect:

- monotonic or unexplained growth after warm-up;
- periodic spikes from rotation, compaction, key refresh, garbage collection, backup, retention,
  journal shipping, and cache expiry;
- resource leaks across session, provider, rig, reconnect, or deployment lifecycle;
- accumulating outbox/consumer/poison/deletion/evidence work;
- clock/sample drift, alert-route decay, credentials nearing expiry, and quota/billing lag;
- degradation that remains hidden by successful averages.

A test duration is accepted only by accountable humans based on the slowest relevant lifecycle;
this document does not invent one.

### Recovery Evidence

Passing recovery requires:

- one authoritative writer and exact recovery/ownership composite actor fence, plus sealed
  session/rig binding;
- proof that a `recovering` owner performed only closed read/classification, separately typed
  source-bound recovery-probe, restrictive, or terminal non-advancing work and created no
  occurrence/cursor advance or other ordinary progression;
- exact database constraint/property counts proving one terminal command transition, at most one
  advancing application per effect intent, at most one disposition per observation, one
  canonical occurrence/turn admission, at most one terminal firing disposition per occurrence,
  current timer-claim firing only, each recovery-probe lineage having exactly one terminal
  non-widening disposition (including valid zero-attempt or terminal-unknown cases), every bound
  source ambiguity resolved/permanently safe-quarantined/accountably disposed before close, and
  zero recovery claims of post-cut-pending normal work;
- exact admission-epoch/source-CAS evidence proving every command receipt/auth-refresh/claim/
  execution/widening-outcome, viewer/platform/director/content-scheduler input, timer
  materialization/claim/firing, Turn, ordinary effect intent/send/application, and
  candidate/selection/approval/media/task/signing/dispatch path is covered; every pre-close
  prefix row terminalizes
  or is safely classified; bounded late evidence and terminal non-advancing drain remain
  available; each `ended`/`cancelled`/`failed` target closes atomically across session/admission/
  ownership with no earlier terminal lifecycle row; post-begin-close-cut ordinary advancement
  remains zero; restored `open`, `draining(normal_closure)`, and atomic `closed` PITR cases retain
  coherent lifecycle/admission axes; lost-tail overlay is monotonic; and unresolved target blocks
  final close;
- reconciled PostgreSQL, ownership-row transitions, submission-generation idempotency,
  four-record ordinary effects, distinct four-role recovery-probe bindings/lineages, canonical
  timer/materialization/current claims, source-serialized activation
  revisions including every recovery-attempt-bound probe write and old-fence successor terminalization,
  immutable cut-time frontiers/schedule-cursor snapshots, excluded post-cut operational-cursor
  progress, activation rejection for nonterminal probes or enabled-scope unresolved source
  ambiguity, restrictive-control acknowledgement, event/outbox projections, definition
  eligibility, activation snapshots, restrictions, deletion/hold, rights, identity, artifact,
  queue, and journal state;
- under sustained harmless post-cut ingress, the operational cursor may progress while the
  immutable activation snapshot does not change and an otherwise valid activation completes
  without starvation; ambiguity or restriction alone advances invalidation and rejects the CAS;
- every PITR/RPO tail is proven complete or explicitly quarantined; absence never drives
  command reacceptance, effect replay, timer rematerialization, or audience enablement;
- no automatic revival of old approval/task/epoch/provider results;
- bounded drain with normal and safety/control reserves preserved;
- current target health plus alert delivery and authoritative exit checks;
- deliberate authorization for any resume or mode increase.

A returned dependency, empty queue, green dashboard, or average latency recovery is insufficient.

## Evidence Record

Each run produces:

- subject, workload, fault, target, role, command-procedure, and acceptance-contract versions;
- raw and derived signal locations with classifications and integrity evidence;
- start/end/phase/fault observations with clock source and uncertainty;
- every admission, shed, timeout, abort, restriction, mode, alert, runbook, recovery, and human
  decision outcome;
- resource/cost/quota baseline, peaks/tails, steady state, drain, and final reconciliation;
- deviations, missing evidence, invalid samples, findings, severity, owners, and remediation;
- exact pass/fail result for each predeclared criterion;
- reviewer identities/roles, review date, validity scope, and invalidation triggers.

The record contains no raw prompts, candidates, viewer memory, unrestricted personal data,
secrets, credentials, rights documents, malicious executable content, or unrestricted media.
Restricted evidence remains in its approved store and is referenced by controlled IDs.

## Review Outcome

| Item                             | Pass / Fail / Inconclusive | Reviewer and role | Evidence | Follow-up or invalidation trigger |
| -------------------------------- | -------------------------- | ----------------- | -------- | --------------------------------- |
| Immutable subject and target     |                            |                   |          |                                   |
| Workload representativeness      |                            |                   |          |                                   |
| Zero-tolerance invariants        |                            |                   |          |                                   |
| Capacity/reserve/backpressure    |                            |                   |          |                                   |
| Latency and reliability          |                            |                   |          |                                   |
| Soak stability                   |                            |                   |          |                                   |
| Chaos containment                |                            |                   |          |                                   |
| Alert/runbook execution          |                            |                   |          |                                   |
| Recovery and drain               |                            |                   |          |                                   |
| Privacy/security/cost guardrails |                            |                   |          |                                   |
| Overall named capability/target  |                            |                   |          |                                   |

`Inconclusive` is not a pass. A passing row provides technical evidence only; production authority
still requires the upstream ADRs, OPEN decisions, protected review, exact target validation,
operational readiness, and release decision.

## OPEN Decisions

Human approval is required for:

- OD-039 workload classes, arrival/mix/skew, target topology, duration,
  warm-up/steady/drain phases, representativeness, chaos targets, blast radius, production
  eligibility, fault duration, abort/rollback/cleanup authority, fixtures/providers/rigs,
  telemetry/evidence/retention/access, independent review, statistical methods, finding
  severity/disposition, evidence freshness, and invalidation policy; any residual-risk acceptance
  uses only the OD-028 taxonomy and authorized role;
- OD-001/035/036/037/038 capacity, headroom, queue, resource, latency, deadline, telemetry, error,
  leak, backlog, recovery, cost, and quota thresholds used by a test; and
- every capability-specific ADR and OPEN decision governing the selected test subject.
