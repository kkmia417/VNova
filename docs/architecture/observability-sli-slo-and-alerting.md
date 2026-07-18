# Observability, SLI/SLO, And Alerting Model

Status: Proposed architecture reference; no telemetry backend, numeric objective, alert threshold,
route, retention, or production authority

Governing sources:

- [`AGENTS.md`](../../AGENTS.md)
- [`vnova-review-handoff.md`](../../vnova-review-handoff.md), especially section 9
- [ADR-003: stream-session, segment, and turn lifecycle](../adr/0003-stream-session-segment-and-turn-lifecycle.md)
- [ADR-004: PostgreSQL outbox and Redis Streams](../adr/0004-postgresql-outbox-and-redis-streams.md)
- [ADR-007: provider gateway and fallback isolation](../adr/0007-provider-gateway-and-fallback-isolation.md)
- [ADR-011: stage-host protocol and clock synchronization](../adr/0011-stage-host-wire-protocol-and-clock-synchronization.md)
- [ADR-015: layered emergency stop](../adr/0015-layered-emergency-stop.md)
- [ADR-017: data retention, privacy, and PII](../adr/0017-data-retention-privacy-and-pii.md)
- [ADR-018: latency budget and streaming strategy](../adr/0018-latency-budget-and-streaming-strategy.md)
- [ADR-020: mode transition and degradation matrix](../adr/0020-mode-transition-and-degradation-matrix.md)
- [ADR-023: event subject, scope, correlation, and ordering lanes](../adr/0023-event-subject-scope-correlation-and-ordering.md)
- [ADR-024: versioned configuration and scoped activation](../adr/0024-versioned-configuration-and-scoped-activation.md)
- [ADR-025: session actor ownership, command ingress, and fencing](../adr/0025-session-actor-ownership-command-ingress-and-fencing.md)
- [VNova threat model](../security/threat-model.md), especially TM-13, TM-16, and TM-19

This model defines signal authority, clock evidence, SLI structure, alert ownership, and telemetry
privacy before implementation. It does not select OpenTelemetry infrastructure, storage,
exporters, dashboards, paging products, contacts, thresholds, error budgets, or retention values.

## Objectives

Observability must let an authorized responder answer, without copying restricted content:

1. What did the system believe, decide, authorize, dispatch, present, stop, and recover?
2. Which exact session, recovery/ownership composite fence, process incarnation, command receipt,
   normal-work admission epoch/closure cut, trigger occurrence/current claim, effect
   intent/attempt/observation/disposition, recovery cut, turn, candidate, decision, artifact,
   task, rig, and version produced the outcome?
3. Which source clock and uncertainty support the timeline?
4. Which safety, rights, privacy, authorization, provider, capacity, and renderer controls were
   healthy or unknown at each boundary?
5. Did the relevant alert reach an accountable owner, and was the runbook executed?
6. Can the same evidence be reproduced from authoritative state after Redis, telemetry, or
   dashboard loss?

The answer to the last question must be yes for domain authority. Telemetry improves diagnosis; it
does not grant permission or replace PostgreSQL state, audit, outbox, or stage-host safety
evidence.

## Evidence And Signal Authority

| Signal class                 | Purpose                                                                                                                                        | Authority                                                      | Sampling/loss posture                                                                                                       |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Domain state                 | Current aggregate, ownership, normal-work admission/closure, command, timer, effect, decision, authorization, deletion, rights, and mode state | PostgreSQL under the owning ADR                                | Never inferred from telemetry; state mutation follows its transaction, generation, and concurrency contract                 |
| Audit record                 | Minimized durable evidence of actor, input identity/digest, decision, policy, transition, and outcome                                          | PostgreSQL or separately approved immutable audit boundary     | Required records are not sampled; loss blocks actions that require durable audit, except immediate safe-direction actuation |
| Domain event/outbox          | Committed notification plus transition-manifest/expected-delivery evidence of an authoritative fact                                            | PostgreSQL outbox/manifest; event payload is not primary state | Complete contract identity is durable; Redis delivery may duplicate/disappear and completeness is rebuilt from PostgreSQL   |
| Stage-host local journal     | Bounded local task/control/playout/watchdog/e-stop evidence during partition                                                                   | Authenticated local record reconciled with cloud authority     | Gaps stay explicit; it cannot manufacture cloud approval or a human decision                                                |
| Operational log              | Structured diagnostic observation                                                                                                              | Non-authoritative                                              | May be sampled/dropped only under an accepted policy; prohibited content is rejected before export                          |
| Metric                       | Aggregated behavior, health, rate, age, resource, and SLI observation                                                                          | Non-authoritative derived signal                               | Aggregation cannot erase failed/unknown outcomes or be used to infer authorization                                          |
| Trace                        | Causal diagnostic view across one operation/turn                                                                                               | Non-authoritative derived signal                               | Sampling never removes required domain/audit evidence; restricted attributes are forbidden                                  |
| Alert                        | Derived assertion that a reviewed condition needs action                                                                                       | Non-authoritative operational control input                    | Delivery and acknowledgement are themselves monitored; alert clearance does not prove recovery                              |
| Restricted forensic evidence | Content or deep technical evidence needed for an approved incident purpose                                                                     | Separately controlled evidence store                           | No ordinary export/sampling; access, retention, hold, deletion, and disclosure follow source classification                 |

Audience-facing alert graphics or scene text are broadcast surfaces governed by ADR-021. They are
not the operational alerts described here, and an incident notification must never be routed to an
audience renderer by naming collision.

## Correlation Model

Every signal uses only applicable typed identities from the
[domain information model](domain-information-model.md). The minimum correlation vocabulary
includes:

- environment, deployment, release, capability, talent/character, session, segment, turn, trigger,
  attempt, candidate, decision, approval, and policy/prompt/persona/profile versions; an
  organization/tenancy identity may be added only if OD-034 defines its stable scope,
  authorization, and privacy-isolation semantics;
- command, idempotency, event complete-contract, typed event scope/subject, aggregate
  version/event index, transition manifest/consumer high-water, outbox, delivery attempt, trace,
  incident, deletion case, hold, definition/set eligibility, activation
  binding/transition/schedule/resolved snapshot, authorization, artifact, task, queue sequence,
  actor ownership record/generation/transition, normal-work admission epoch/closure cut,
  runtime process incarnation, command receipt/outcome, ordinary effect intent/attempt/
  observation/disposition, recovery-probe intent/attempt/observation/disposition/source binding,
  trigger occurrence/timer claim/firing disposition, rig, rig boot, connection, and independent
  activation/restrictive epochs;
- source component, software version, target identity, outcome category, failure category, and
  evidence classification.

Signals use typed attributes or unambiguous names; a generic `id`, `status`, `mode`, `version`,
`provider`, or `error` attribute is insufficient across boundaries.

High-cardinality identities are admitted only where the signal purpose requires them. Metrics use
bounded dimensions; per-record identities belong in logs/traces/audit references rather than
metric labels. Hashes remain linkable/sensitive and receive classification, access, retention, and
export review rather than being treated as anonymous.

## Clock And Timeline Evidence

VNova keeps four distinct time concepts:

1. **Raw UTC observation:** the source-reported wall-clock timestamp, retained unchanged.
2. **Local monotonic duration:** elapsed time measured on one process/boot, used for local
   deadlines and stage duration.
3. **Clock estimate:** the offset estimate, uncertainty bound, sample age, round-trip delay, source
   clock/boot identity, and estimation algorithm/version.
4. **Derived correlated timeline:** a diagnostic view calculated from subject-lane causal
   positions, raw observations, and a named clock estimate. It is never one authoritative global
   domain-event order.

Derived correction never overwrites raw timestamps. An apparent clock difference, offset estimate,
uncertainty, drift rate, and network delay are different measurements. A legacy or dashboard
metric named `clock_skew_ms` cannot be the sole deadline or evidence input; the implementation
must expose the unambiguous components above.

One trace follows a turn from its named trigger boundary through observed playback/terminal
outcome. Each span retains:

- raw start/end UTC observations;
- local monotonic duration where available;
- source component, process/boot, operation/attempt, and outcome;
- clock-sample identity and uncertainty for cross-host correlation;
- the applicable outer deadline and remaining-budget observation without extending it.

Deadline enforcement follows ADR-011 and the
[latency budget](latency-budget.md): a conservative local monotonic mapping and uncertainty bound
decide validity. A visually corrected trace cannot make expired or uncertain work valid.

## Prompt And Provider Observability

The per-turn prompt-assembly manifest is the ordinary incident artifact. It records versions,
source IDs, section counts, token/size counts, digests, and outcomes defined by the
[domain information model](domain-information-model.md), never prompt or memory values.

Provider attempts record:

- capability, provider-profile/model-config, gateway/normalizer, request/attempt, and failure-domain
  identities;
- explicit timeout, outer deadline, start/end/cancellation/late-result outcome;
- normalized error/failure category rather than unrestricted exception bodies;
- request/response digests and schema/validation outcome without raw content;
- usage, quota, circuit, retry/fallback, and cost-accounting evidence under the approved profile;
- redaction/scrubbing/export outcome.

SDK logs and auto-instrumentation are denied by default until their attribute/body behavior passes
the same telemetry allowlist and prohibited-content tests. A redaction failure drops diagnostic
content and emits minimized failure evidence; it does not export the original value.

## Required Signal Semantics

Metric names below originate in the binding handoff or existing ADRs. Exact units, temporality,
aggregation, dimensions, collection intervals, thresholds, and retention require human review.

| Signal                                                           | Source boundary                                    | Required interpretation                                                                                                                                                                                                                                                                                                                                                                                                |
| ---------------------------------------------------------------- | -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `approval_queue_wait_ms`                                         | Authoritative operator-review queue transitions    | Time from queue admission to terminal decision/expiry; expired and cancelled outcomes remain visible                                                                                                                                                                                                                                                                                                                   |
| `candidate_expired_count`                                        | Authoritative candidate/turn transition            | Classified expiries by boundary and trigger; never inferred only from queue disappearance                                                                                                                                                                                                                                                                                                                              |
| Actor ownership phase, lease proof, and takeover                 | Authoritative ownership transitions and rejections | Recovery/ownership components, row-conflict/post-lock time, phase, lease, revoke/takeover, stale-composite rejection, and recovery-hold age stay distinct                                                                                                                                                                                                                                                              |
| Normal-work admission, closure prefix, and drain                 | Authoritative session admission/closure records    | Open/draining initial cause plus monotonic lost-tail overlay/closed, lifecycle `Ending`, resolved versus conceptual unresolved target, admission epoch, fixed closure cut, frozen cursors, remaining prefix, final-close blockers, post-closure-cut rejection, and quarantine stay distinct                                                                                                                            |
| Command receipt/auth-lineage/outcome age and unknown observation | Durable command ingress/authorization/outcome      | Submission generation, protected key/digest conflict, receipt vs success, authorization-lineage revision/selection ambiguity, lookup denial, pending/effective expiry, response loss, lost-tail unknown, and terminal outcome stay distinct                                                                                                                                                                            |
| Effect ambiguity and stale/late-result disposition               | Durable four-record ordinary-effect lineage        | No attempt in proven horizon, send-authorized/possibly-sent, response observed, application rejection, late/stale, and lost-tail unknown are not collapsed                                                                                                                                                                                                                                                             |
| Recovery-probe binding, bounds, and terminality                  | Distinct four-role recovery-probe lineage          | Active+draining-prefix versus recovering+recovery-attempt/source binding, zero-attempt terminality, originating fence provenance/current-successor terminalization without resend, intent/attempt/response/disposition, count/byte/rate/age/concurrency rejection, terminal unknown negative/timeout/contradiction, and separately bound source classification/final-close blocker stay distinct from ordinary effects |
| Trigger occurrence, claim, due lag, and disposition              | Durable scheduler/timer records                    | Canonical slot/materialization cursor, claim token/reclaim, one admission, missed/skipped, bounded materialization/catch-up, and backlog age remain distinct                                                                                                                                                                                                                                                           |
| Recovery activation and history completeness                     | Recovery cuts/barriers and DR evidence             | Immutable cut-time source/schedule-cursor snapshots, separate excluded post-cut operational cursor, recovery-attempt-bound probe-write/restrictive invalidation revision, terminal-probe/enabled-source-resolution gate, sealed rig state, zero-loss proof, lost-tail scope, quarantine, and human disposition are explicit                                                                                            |
| Restrictive-control convergence                                  | Durable intent/attempt/exact-rig acknowledgement   | Pending claim, retry, epoch/binding, downstream acknowledgement, unknown audience convergence, and local e-stop outcome are distinct                                                                                                                                                                                                                                                                                   |
| `safety_eval_latency_ms`                                         | Safety evaluation lineage                          | Complete deterministic/model/policy evaluation duration by terminal/indeterminate outcome                                                                                                                                                                                                                                                                                                                              |
| Event-bus consumer lag                                           | Outbox publisher and each consumer                 | Transport delay/backlog relative to PostgreSQL source; never domain-data loss or recovery authority                                                                                                                                                                                                                                                                                                                    |
| `rig_ws_rtt_ms`                                                  | Authenticated runtime/rig clock sampling           | Round-trip observation, not one-way latency or clock offset                                                                                                                                                                                                                                                                                                                                                            |
| Clock offset/uncertainty/sample-age signals                      | Clock estimator                                    | Separate components bound to rig boot/connection/sample; `clock_skew_ms` may be a derived display only                                                                                                                                                                                                                                                                                                                 |
| `audio_buffer_underrun_count`                                    | Virtual/live audio sink and stage-host             | Observed local-playout underrun with bounded environment/rig-class/output-outcome metric dimensions; exact session/rig identity stays in trace/local evidence                                                                                                                                                                                                                                                          |
| OBS audio level and `silent_duration_seconds`                    | Independent OBS/source monitor                     | Audience-output evidence independent of TTS/task success; silence alarm does not by itself identify cause                                                                                                                                                                                                                                                                                                              |
| `operator_presence` and presence age                             | Authorization/presence boundary                    | Current scoped presence evidence and freshness, not browser connectivity alone                                                                                                                                                                                                                                                                                                                                         |
| Moderation/provider quota and health                             | Provider gateway                                   | Reviewed capability/profile pool state, uncertainty, reserve, and normalized denial/failure                                                                                                                                                                                                                                                                                                                            |
| Chat-ingest gap                                                  | Platform collector plus expected cursor/poll state | Missing/stale input collection even when process/network appears healthy                                                                                                                                                                                                                                                                                                                                               |
| Cost warning/limit state                                         | Authoritative budget ledger                        | Warning, hard denial, billing lag, and unknown usage are distinct; event activation requires a governed payload                                                                                                                                                                                                                                                                                                        |
| Fail-closed and safety-layer health                              | Safety/domain transitions                          | Every activation, scope, cause, mode ceiling, and recovery hold; no verdict means no speech                                                                                                                                                                                                                                                                                                                            |
| E-stop, watchdog, queue, playback, and surface outcome           | Cloud plus exact stage-host/renderer               | Command, local actuation, acknowledgement, observed output, and reconciliation remain distinct                                                                                                                                                                                                                                                                                                                         |
| Telemetry/alert pipeline health                                  | Each collector/exporter/store/route                | Last accepted signal, queue age/capacity, drop/error state, route test, delivery, acknowledgement, and blind-spot scope                                                                                                                                                                                                                                                                                                |

Success-only metrics are insufficient. Each SLI accounts explicitly for timeout, cancellation,
rejection, expiry, indeterminate, fail-closed, missing evidence, and late completion.

## SLI Definition Contract

Each SLI has a versioned definition containing:

- user/operational outcome and safety relevance;
- exact population, inclusion/exclusion rules, trigger/capability/mode/surface classes, and source
  boundaries;
- numerator, denominator, unit, aggregation/percentile, time window, low-traffic treatment, and
  missing/late-data policy;
- authoritative source records and derived query version;
- clock model and uncertainty treatment;
- data classification, attributes, retention, access, region, and export policy;
- validation method, synthetic canary, dashboard/alert consumers, owner, and invalidation triggers.

A dashboard query is not the definition. The same versioned SLI semantics must be used in
rehearsal, target validation, and production, with environment clearly separated.

### Safety Deadlines Are Not Error Budgets

The following decisions are separate even when a review considers them together:

- absolute safety/freshness deadline and candidate/authorization TTL;
- per-external-attempt timeout and cancellation bound;
- scheduler stage budget and admission estimate;
- observed latency SLI/SLO;
- alert threshold, burn policy, and response objective.

An SLO change, error-budget allowance, degraded-service declaration, or low-traffic exception can
never extend an individual turn, approval, authorization, task, rights, or surface deadline.
Safety, rights, privacy, authorization, and fail-closed invariants have no error budget.

## Alert Contract And Registry

Every production alert has a versioned registry entry:

| Field                | Requirement                                                                                                     |
| -------------------- | --------------------------------------------------------------------------------------------------------------- |
| Identity and purpose | Stable alert ID, capability/failure class, user/safety impact, and why action is required                       |
| Source and condition | Exact SLI/signal/query versions, freshness requirement, evaluation window, and missing-data behavior            |
| Scope                | Environment, deployment, talent/session/rig/surface/provider/data boundary and aggregation rules                |
| Severity and posture | Human-approved severity plus required mode ceiling, hold, or immediate local/cloud action                       |
| Ownership            | Primary and secondary accountable functions, coverage, handoff, and escalation                                  |
| Delivery             | Approved routes, route health, deduplication/grouping, repeat, acknowledgement, and delivery evidence           |
| Suppression          | Narrow maintenance/test context, authorized actor, reason, expiry, audit, and automatic restoration prohibition |
| Runbook              | Exact version and entry/exit link; no alert is production-authorized without an actionable runbook              |
| Recovery             | Authoritative exit checks and deliberate clearance; disappearance of the signal is not recovery proof           |
| Evidence             | Alert instances, notifications, acknowledgement, actions, findings, and retained minimized references           |

Numeric thresholds, severity labels, contacts, routes, and response objectives remain OPEN.
Silencing cannot suppress local e-stop, fail-closed actuation, or authoritative recording. A
suppression that hides a production safety condition without an equivalent approved control is
forbidden.

Day-one alert families include rig disconnect during live operation, audience-output silence,
safety-layer/fail-closed activation, e-stop, provider hard failure, cost warning/limit, required
operator absence, dead-letter/backlog growth, approval-queue age, chat-ingest gap, clock
uncertainty, nonterminal/over-bound recovery probe or unresolved bound source ambiguity blocking
activation/final close, and telemetry/alert-pipeline blind spots. A terminal probe whose evidence
is `unknown` remains visible but is not itself mislabeled as an unresolved lineage.

## Dashboard Contract

Dashboards are read models and never command or recovery authority. Required views include:

- **live session operations:** lifecycle, requested/effective mode, emergency latch, rig binding,
  exact recovery/ownership composite fence/phase/lease freshness, immutable activation
  frontiers/cut-time cursor snapshots versus the excluded operational cursor, invalidation
  revision/sealed rig, normal-work admission epoch/initial closure cause/quarantine overlay/
  fixed-prefix drain/resolved-or-unresolved target/final-close blockers,
  lost-tail/restrictive-control convergence, pending/expired/unknown commands and ordinary
  effects, recovery-probe origin/current-successor binding/bounds/terminality/terminal-unknown
  evidence versus bound-source blocker, canonical due/missed triggers/current claims/frozen
  closure cursors, clock health,
  latency/deadline posture, queues, last turns, and surface/playout outcomes;
- **safety and authorization:** decisions by category/outcome, indeterminate/fail-closed scope,
  approval/operator queue, expiry, rights/surface denial, revocation, and evidence gaps;
- **provider and cost:** profile/capability health, latency/outcome, quota/circuit state,
  generator/judge independence, usage/cost ledger, warning/limit/unknown state;
- **transport and storage:** PostgreSQL/outbox health, Redis/consumer lag, poison/DLQ, object
  integrity/transfer, local-journal range/capacity/shipping;
- **observability health:** collector/exporter health, dropped/rejected signal counts, alert route
  tests, freshness, coverage gaps, and prohibited-content scan state.

Every view displays its source freshness, query/SLI version, environment, and incomplete/unknown
state. Green presentation cannot override an authoritative restriction.

## Telemetry Data Contract

Every log, metric, trace, profile, alert, dashboard dataset, and exporter path has:

- owner, purpose, signal class, authoritative source relationship, and consumers;
- field/attribute allowlist and classification;
- cardinality/volume budget, sampling/aggregation policy, and loss semantics;
- retention, deletion, legal/incident hold, access role, region/residency, and export policy;
- buffer capacity, overflow/drop priority, explicit exporter timeout, bounded retry/cancellation,
  and late-result behavior;
- prohibited-content and secret scanning, canary tests, and schema/version evolution;
- failure posture proving telemetry cannot starve e-stop, safety, operator control, heartbeat,
  authoritative persistence, or current playout.

Ordinary telemetry must not contain raw prompts, candidates, viewer messages or memory, full
provider bodies, voice/rights evidence, secrets, credentials, unrestricted media, identity
documents, or incident samples. Restricted diagnostics use a separate approved evidence workflow.

## Failure Behavior

- Missing/stale signal, exporter timeout, buffer overflow, query failure, alert delivery failure,
  dashboard disagreement, or unknown route health is an observability incident, not evidence of
  system health.
- Local and cloud safety actions continue without a telemetry backend. Actions requiring durable
  audit still follow their fail-closed rules.
- Required operator presence, rig health, safety health, rights state, or clock validity cannot be
  inferred from silence; unknown evidence lowers the applicable mode ceiling or holds the
  capability.
- Ownership, normal-work admission/closure, command, effect, or timer state cannot be inferred
  from a healthy process, route, metric, trace, or empty queue. Unknown composite actor fence,
  admission epoch/close cut, send outcome, recovery frontier, or history completeness stops
  ordinary progression and enters ADR-025 recovery hold. Telemetry cannot reopen a draining or
  closed session.
- Telemetry retry is bounded and lower priority than safety/control. It never extends domain
  deadlines or causes unbounded memory/disk use.
- Recovery reconciles authoritative state first, then signal pipelines, alert delivery, and
  dashboards. No mode increase or incident closure occurs solely because graphs become green.

## Acceptance Evidence

Before production use of any capability:

- every required signal and alert has reviewed semantic/registry metadata and an accountable
  owner;
- shared fixtures prove telemetry allowlists, classification, redaction, cardinality bounds,
  timeout, overflow, sampling, and prohibited-content rejection;
- deterministic traces reconstruct complete successful, blocked, expired, failed-closed,
  interrupted, disconnected, and recovered paths without restricted content;
- event traces preserve complete contract/framing, catalog scope/subject/historical
  classification/current protection overlay, aggregate-version/event-index positions, and
  transition-manifest/high-water state; distinguish filtered empty/subset sets from missing tails
  or whole transitions; and never treat correlation or Redis order as authority;
- activation traces prove exact set/transition/epoch/snapshot lineage, restrictive precedence,
  forward rollback, stale-cache rejection, and no raw configuration/content leakage;
- session-execution traces prove composite-fence/ownership-row/post-lock-time transitions,
  exact normal-work admission/source-CAS ordering across command/auth-lineage, every input/
  timer/Turn/ordinary effect, and
  candidate/selection/approval/media/task/signing/dispatch progression;
  begin-close committed prefix, cursor freeze, bounded evidence/terminal non-advancing drain,
  atomic terminal-target final close, and no post-begin-close-cut ordinary growth;
  submission-generation
  command key/digest, receipt versus outcome/lookup authorization/expiry, authorization-
  observation dedupe/lineage CAS/precedence, ordinary effect intent/send-authorization/
  first-byte/response-observation/application crash boundaries, distinct recovery-probe
  four-role lineage under both exact bindings, zero-attempt and current-successor
  terminalization/no-resend, wrong-binding/ordinary-relabel rejection, finite
  count/byte/rate/age/concurrency, non-widening terminality, terminal-unknown negative/timeout/
  contradiction separated from source resolution, nonterminal-probe/unresolved-bound-source
  final-close rejection, canonical timer
  materialization/current-claim admission, restrictive-dispatcher convergence,
  immutable cut-time source/cursor snapshots, excluded harmless post-cut operational-cursor
  progress without activation starvation, recovery-attempt-bound probe-write plus
  ambiguity/restriction invalidation and activation rejection, PITR restored
  `open`/`draining(normal_closure)`/atomic-`closed` lifecycle-admission coherence, monotonic
  lost-tail overlay, unresolved-target final-close blocking, safe-direction exception, and
  recovery-only takeover without making telemetry authoritative;
- clock tests cover offset, uncertainty, sample age, RTT, asymmetric delay, drift, wall-clock
  steps, sleep/reboot, and derived-timeline non-authority;
- alert tests prove condition detection, missing-data behavior, delivery, acknowledgement,
  escalation, suppression expiry, runbook entry, and false-clear rejection;
- telemetry/alert pipeline loss and disagreement exercise the
  [telemetry and alerting degradation runbook](../runbooks/telemetry-and-alerting-degradation.md);
- load, soak, chaos, and recovery evidence proves observability remains bounded and cannot starve
  safety/control resources;
- privacy/security review approves each signal data contract and export path;
- the exact deployment advances through rehearsal, target validation, and the
  [operational readiness review](../governance/operational-readiness-review.md).

## OPEN Decisions

Human review must decide:

- OD-001 observed service-latency SLI populations, SLO windows/targets, and error-budget policy;
- OD-035 safety/freshness deadline, actor lease/renew/takeover/effect-margin, timeout,
  scheduler-budget, clock sample/freshness/uncertainty, drift, reconnect, and deadline-validity
  profiles without deriving them from SLOs;
- OD-036 the remaining SLI catalog; telemetry backend, collection, sampling, cardinality,
  retention, deletion, hold, access, residency, export, and cost policy; alert ownership,
  severity, routes, coverage, acknowledgement/escalation, suppression/maintenance, response
  objectives, and evidence freshness; dashboard/query governance; and the minimum observability
  posture/mode ceiling during monitoring loss.
