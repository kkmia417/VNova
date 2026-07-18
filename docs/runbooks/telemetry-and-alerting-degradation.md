# Telemetry And Alerting Degradation

Status: Proposed operational runbook; readiness state: `Drafted`; no implementation, alert,
incident, or production authority

Governing sources:

- [`AGENTS.md`](../../AGENTS.md)
- [Observability, SLI/SLO, and alerting model](../architecture/observability-sli-slo-and-alerting.md)
- [Capacity, backpressure, and cost governance](../architecture/capacity-backpressure-and-cost-governance.md)
- [Privacy and retention model](../architecture/privacy-retention-model.md)
- [ADR-004: PostgreSQL outbox and Redis Streams](../adr/0004-postgresql-outbox-and-redis-streams.md)
- [ADR-011: stage-host protocol and clock synchronization](../adr/0011-stage-host-wire-protocol-and-clock-synchronization.md)
- [ADR-015: layered emergency stop](../adr/0015-layered-emergency-stop.md)
- [ADR-017: data retention, privacy, and PII](../adr/0017-data-retention-privacy-and-pii.md)
- [ADR-019: authentication, authorization, and operator roles](../adr/0019-authentication-authorization-and-operator-roles.md)
- [ADR-020: mode transition and degradation matrix](../adr/0020-mode-transition-and-degradation-matrix.md)
- [Threat model TM-13 and TM-16](../security/threat-model.md)
- [Operational runbook contract](README.md)

This runbook defines containment and recovery semantics, not executable commands, telemetry
products, endpoints, credentials, contacts, thresholds, routes, mode values, or retention
defaults. Those require deployment-specific protected review.

## Purpose And Entry Conditions

Use this runbook when VNova cannot prove that operational signals and alerts are current,
complete, correctly classified, and delivered to their accountable owners, including:

- logs, metrics, traces, profiles, dashboards, collectors, exporters, stores, queries, or alert
  evaluators are missing, delayed, rejected, duplicated, corrupted, saturated, or unavailable;
- alert delivery, acknowledgement, escalation, or secondary routing is delayed, failing,
  suppressed, misconfigured, or unverifiable;
- dashboards, PostgreSQL state, audit/outbox, Redis, provider, rig, OBS/audio, or local journal
  observations disagree;
- clock offset, uncertainty, sample age, source boot, or derived timeline makes signal ordering
  unreliable;
- instrumentation or auto-instrumentation may be dropping outcomes, changing application
  behavior, consuming safety/control capacity, or leaking restricted data;
- a required alert did not fire, fired with the wrong scope, cleared without recovery, or reached
  an unauthorized destination;
- a monitoring blind spot overlaps a live capability whose safe operation depends on current
  rig, safety, rights, identity, operator-presence, clock, capacity, or output evidence.

A stale or absent signal is `unknown`, not healthy. A dashboard color, process-up check, or empty
alert list is never sufficient entry or exit evidence.

## Non-Negotiable Invariants

- Local e-stop, audio cut, queue flush, watchdog, and safe local presentation do not depend on the
  telemetry or alerting path.
- Cloud e-stop, generation freeze, mode decrease, cancellation, rights/access/deletion
  invalidation, and fail-closed actuation are not delayed to preserve metrics or traces.
- Missing current evidence for a required safety, rights, authorization, operator-presence, rig,
  clock, or output condition applies the restrictive posture defined by the accepted capability
  profile.
- PostgreSQL remains authoritative for cloud state/audit/outbox. Redis, logs, metrics, traces,
  dashboards, alert state, and local journals cannot reconstruct permission.
- Required domain/audit evidence is not sampled. Telemetry loss does not make a domain transition
  successful, durable, or absent.
- Every exporter, store, route, synthetic probe, identity, and other external operation has an
  explicit timeout, outer deadline, bounded retry/cancellation, and classified late/unknown
  outcome.
- Telemetry retry, buffering, profiling, and diagnostics cannot starve safety, operator control,
  heartbeat, authoritative persistence, or current playout.
- Ordinary incident and telemetry records contain no raw prompt, candidate, viewer message or
  memory, provider body, secret, credential, rights evidence, unrestricted personal data, or
  media.
- Restored telemetry or a cleared alert never resumes a broadcast, raises mode, clears e-stop,
  replays work, or closes an incident automatically.

## Required Response Functions

These are functions, not concrete IAM roles:

| Function                | Responsibility                                                                                                                                 |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Incident commander      | Owns affected scope, restrictive posture, handoffs, decision log, and exit authorization                                                       |
| Safety/operations lead  | Determines which capability cannot operate safely without the missing evidence and preserves stop/fail-closed behavior                         |
| Observability owner     | Diagnoses signal source, collection, export, storage, query, dashboard, alert evaluation, and delivery without treating that path as authority |
| Domain/data owner       | Verifies PostgreSQL state, audit/outbox, idempotency, retention, and evidence gaps                                                             |
| Stage-host/operator     | Observes actual local/audience output, preserves local stop/watchdog/journal state, and validates exact rig signals                            |
| Security/privacy owner  | Handles tampering, unauthorized routing, secret/restricted-data leakage, evidence custody, and access concerns                                 |
| Provider/platform owner | Verifies provider/platform signal and quota paths through approved profiles                                                                    |
| Recorder                | Maintains a minimized timeline, signal/alert coverage manifest, unknowns, decisions, and evidence locations                                    |

OD-027 and the observability/alerting decision must assign accountable people, resilient
communications, primary/secondary coverage, escalation, and separation of duties.

## Signal Criticality And Restrictive Posture

| Missing or contradictory evidence                                               | Immediate minimum posture                                                                                                                                            |
| ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Safety verdict/gate health or fail-closed actuation                             | Mint no approval and dispatch no autonomous work; invoke [safety fail-closed](safety-fail-closed.md)                                                                 |
| E-stop/local output/watchdog/queue or exact rig binding                         | Observe locally where safe, block new dispatch, use [emergency stop](emergency-stop-and-resume.md) or [rig disconnect](rig-disconnect-and-watchdog.md) as applicable |
| Required operator presence/authorization/revocation                             | Block mode increase, resume, privileged commands, and presence-dependent autonomy                                                                                    |
| Rights/surface expiry, revocation, final presentation, or current authorization | Stop/deny the affected voice or surface and invoke the relevant rights/surface workflow                                                                              |
| PostgreSQL/audit/outbox durability                                              | Apply immediate restrictive action locally/in process; block claims of durable success, replay, resume, or higher mode until reconciliation                          |
| Audience audio/surface observation                                              | Treat output state as unknown; block new affected presentation and use local independent observation/stop path                                                       |
| Provider capacity/quota/cost or fallback independence                           | Deny new affected attempts or use only an eligible bounded fallback through the same full gate                                                                       |
| Ordinary performance or diagnostic telemetry only                               | Keep the capability within its accepted minimum observability posture; restrict lower-priority work and repair without assuming broader safety impact                |
| Alert delivery/acknowledgement/escalation                                       | Use the approved independent incident channel; treat owner notification as unproven until acknowledged                                                               |
| Data classification/export/redaction                                            | Stop the affected export/collection, preserve minimized evidence, and invoke personal-data/security response if disclosure is plausible                              |

The exact mode ceiling is a protected human decision. The table never authorizes availability when
another ADR requires a stricter response.

## Immediate Containment

1. **Protect audience output.** Observe the exact live/local output through an independent path
   where safe. Engage local hard stop immediately when output is unsafe or cannot be bounded.
2. **Declare the blind spot.** Record the earliest plausible start, affected signals, capabilities,
   deployments, sessions, rigs, surfaces, providers, data classes, routes, and owners. Unknown
   start expands scope.
3. **Apply the restrictive capability posture.** Hold new work whose current preconditions cannot
   be proven. Stop and mode decrease have no confirmation requirement; resume and mode increase
   remain separately gated.
4. **Protect control capacity.** Bound or pause profiling, verbose logging, trace export, replay,
   dashboard queries, backfill, and low-priority telemetry when they threaten safety/control,
   PostgreSQL, network, disk, or rig capacity.
5. **Preserve authoritative evidence.** Keep PostgreSQL state/audit/outbox, stage-host local
   journal, raw source timestamps, clock samples, alert configuration versions, and delivery
   evidence. Do not generate fake samples to fill a gap.
6. **Use an independent communication path.** Notify accountable owners without relying on the
   failed alert route as the only evidence. Record delivery and acknowledgement separately.
7. **Contain possible disclosure or tampering.** Disable affected export/access narrowly, preserve
   custody, and invoke the
   [personal-data breach response](personal-data-breach-response.md) or security workflow without
   waiting for final legal/adversarial classification.
8. **Freeze unsafe changes.** Pause telemetry schema, collector, exporter, query, dashboard, alert,
   deployment, and auto-remediation changes that could destroy evidence or widen ambiguity.

Containment actions themselves have explicit timeouts. Timeout or partial result remains unknown
and does not narrow the blind spot.

## Coverage Manifest

Create a versioned, content-free manifest for every affected signal/alert:

- signal/alert identity, version, purpose, class, owner, consumers, and required freshness;
- source boundary, authoritative source relationship, query/evaluator, collector/exporter/store,
  dashboard, and delivery route versions;
- environment, deployment, talent/session/rig/surface/provider/data scope;
- last independently proven source observation, accepted/exported/stored/query result, evaluation,
  notification, delivery, acknowledgement, and action;
- raw clock, process/boot, offset/uncertainty/sample identities;
- buffer/queue depth, oldest age, drops/rejections, retries, timeouts, and overflow;
- classification, attribute allowlist, sampling, retention, access, region, and export state;
- current outcome: healthy, degraded, blind, contradictory, contaminated, quarantined, or unknown;
- restrictive action, owner, evidence link, and next verification.

Do not declare coverage complete from configuration inventory alone. The manifest must include an
end-to-end accepted synthetic or real minimized observation for every required path.

## Diagnosis

### Trace Source To Owner

For each signal, verify in order:

1. the domain/local source actually emitted the expected observation;
2. instrumentation accepted the correct typed attributes without restricted content;
3. local buffer/collector accepted it and retained the expected source clock/sequence;
4. exporter attempted the correct destination with explicit timeout and bounded retry;
5. store/index/query accepted the expected schema/version and did not silently sample/drop it;
6. dashboard/SLI/alert evaluator used the reviewed query and freshness rule;
7. alert instance bound the correct scope, severity, runbook, and route;
8. primary/secondary destinations received and an authorized human acknowledged it;
9. the resulting action and authoritative recovery evidence were recorded.

A success at a later step cannot infer a missing earlier step. A synthetic alert injected directly
into the delivery tool does not prove source, collection, query, or evaluation.

### Compare Independent Authorities

Compare:

- PostgreSQL state, audit, outbox, and idempotency;
- Redis publication/consumer observations only as transport evidence;
- runtime process/actor/queue/provider observations;
- stage-host queue, journal, watchdog, adapter, audio, and actual OBS/surface output;
- identity/authorization, rights, deletion/hold, and configuration activation state;
- raw timestamps plus clock offset/uncertainty/sample age;
- telemetry store/query/dashboard/alert/delivery observations.

Contradiction stays visible. Never edit one source to match another before authoritative
reconciliation explains the difference.

### Common Failure Classes

| Failure class                         | Evidence                                                                         | Required response                                                                                              |
| ------------------------------------- | -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Source instrumentation absent/wrong   | Domain transition exists but expected minimized observation does not             | Preserve domain truth, block dependent observability claim, fix and replay only from a governed durable source |
| Collector/exporter/store outage       | Queued/dropped/timeout/unknown export or stale query                             | Bound retries/buffers, protect control resources, keep blind-spot posture                                      |
| Schema/query/dashboard drift          | Signal exists but is rejected, misclassified, or displayed incorrectly           | Quarantine affected view/alert; review exact versions and fixtures                                             |
| Sampling/cardinality loss             | Required outcomes/identities disappear or metric series explode                  | Keep audit authoritative, stop unsafe sampling/export, apply accepted dimension/budget policy                  |
| Alert evaluator/delivery failure      | Condition exists without valid notification/acknowledgement                      | Use independent incident path; test full route after repair                                                    |
| Suppression/maintenance error         | Alert hidden, overbroad, stale, or restored incorrectly                          | Remove only through authorized audited action; suppression expiry never clears incident                        |
| Clock/timeline disagreement           | Raw observations cannot be ordered inside uncertainty                            | Treat causal order/validity as unknown; do not use corrected dashboard time as authority                       |
| Telemetry-induced resource exhaustion | CPU/memory/disk/network/DB/rig control latency affected                          | Shed diagnostic work first and invoke resource-exhaustion runbook                                              |
| Restricted data/secret leakage        | Prohibited field reaches ordinary telemetry/support/destination                  | Stop propagation, preserve minimized custody evidence, invoke breach/security response                         |
| Compromise/tampering                  | Config, query, signal, alert, route, or evidence controlled by suspect principal | Quarantine trust boundary and invoke identity/supply-chain response                                            |

## Recovery

### Restore Source And Collection In Isolation

1. Restore or rebuild the minimum signal path from reviewed source, schema, configuration, query,
   and release identities.
2. Validate attribute allowlists, redaction, classification, timeout, buffer/overflow, sampling,
   cardinality, access, retention, and export before reconnecting production sources.
3. Use synthetic non-personal canaries and deterministic fixtures. Do not use raw incident content
   as a probe.
4. Keep backfill/replay bounded and lower priority than live safety/control. Re-export only from an
   approved durable source; never reconstruct domain facts from logs or dashboards.
5. Preserve every original gap and unknown. Generated replacement telemetry is labeled synthetic
   and cannot pretend the historical observation occurred.

### Revalidate Alerts End To End

For every affected alert:

1. produce the reviewed source condition or synthetic equivalent at the true source boundary;
2. prove collection, storage, query, evaluation, scope, freshness, and missing-data behavior;
3. prove primary and secondary delivery, acknowledgement, escalation, and runbook access;
4. exercise delivery timeout, route outage, suppression expiry, duplicate/grouping, and false
   clear;
5. verify no audience-facing surface, unauthorized party, or prohibited data receives the alert;
6. bind results to exact target, release, configuration, query, route, owner, and evidence version.

### Reconcile And Deliberately Restore Capability

1. Reconcile authoritative PostgreSQL and stage-host state independently of recovered telemetry.
2. Account for every missing interval, affected decision, alert, operator handoff, provider
   attempt, task, output, deletion/right/access change, and incident action.
3. Resolve or retain explicit unknowns; do not close gaps by inference.
4. Prove current signal freshness and alert delivery for the exact capability/target.
5. Re-run relevant fail-closed, e-stop, rig, silence, provider, rights, privacy, and capacity
   scenarios.
6. Only the normal protected human recovery path may lift the observability hold, resume, or raise
   mode. Old queued work remains invalid unless independently current and authorized.

## Exit Criteria

All are required for the named scope:

- authoritative domain/local state is coherent and no recovery conclusion relies on telemetry as
  truth;
- the coverage manifest accounts for every required signal, gap, contradiction, alert, route, and
  owner;
- source-to-owner signal/alert canaries pass on the exact target;
- clock raw observations, offset, uncertainty, sample age, and derived timeline are valid and
  separately represented;
- buffers, retries, sampling, cardinality, export, and resource use stay inside the approved
  profile without starving safety/control;
- prohibited-content/security/privacy scans pass and any disclosure/tampering incident has its
  own disposition;
- all required alerts deliver, acknowledge, escalate, link the correct runbook, and reject false
  clear;
- missing historical evidence remains explicitly classified and accepted only by the authorized
  residual-risk owner where no invariant or required evidence is waived;
- current mode/resume state was decided deliberately and no old work was revived.

An empty alert list, recovered exporter, query success, green dashboard, or one delivered test
notification is not an exit criterion.

## Evidence And Audit

Retain only:

- incident, signal, alert, query, configuration, route, owner-function, deployment, session, rig,
  boot, event, trace, clock-sample, command, and evidence-manifest IDs;
- versions/digests of reviewed schemas, allowlists, queries, dashboards, alerts, routes, releases,
  and runbooks;
- raw timestamps, local monotonic durations, offset/uncertainty/sample references;
- queue/buffer/drop/timeout/retry/sampling/cardinality outcomes;
- alert evaluation, delivery, acknowledgement, escalation, suppression, action, and recovery
  outcomes;
- restrictive decisions, findings, owners, follow-up, and authorization references.

Restricted forensic data stays in its approved evidence store. Ordinary evidence never becomes a
shadow copy of source content.

## Escalation

Escalate without weakening the restrictive posture when:

- audience output, safety, e-stop, rig, clock, rights, identity, operator presence, or
  authoritative state cannot be observed adequately;
- a required alert did not reach an accountable owner or the independent incident path failed;
- blind-spot start, scope, or historical effect cannot be bounded;
- telemetry caused resource exhaustion, outage, control delay, or unsafe backpressure;
- restricted data, credentials, rights evidence, or incident content may have leaked;
- malicious modification, supply-chain compromise, identity misuse, or evidence tampering is
  plausible;
- restoration would require fabricated history, unreviewed backfill, or risk acceptance of a
  required safety/target gate.

Exact severity, contacts, routes, notification duties, and response objectives remain protected
human decisions.

## Required Rehearsal Scenarios

Before production authorization, exercise:

- source instrumentation missing, wrong schema/version, attribute rejection, and query/dashboard
  drift;
- collector/exporter/store outage, timeout, backpressure, buffer overflow, retry exhaustion, and
  late recovery;
- sampling of required evidence, metric cardinality explosion, trace loss, and telemetry-induced
  CPU/memory/disk/network pressure;
- alert evaluator failure, route failure, primary/secondary delivery, acknowledgement timeout,
  suppression expiry, duplication, grouping, escalation, and false clear;
- dashboard disagreement with PostgreSQL, Redis, provider, runtime, rig, OBS/audio, and local
  journal;
- clock offset/uncertainty/sample staleness, wall-clock step, sleep/reboot, asymmetric delay, and
  derived-timeline error;
- safety, rig, operator-presence, rights, capacity, and audience-output blind spots with the
  required restrictive posture;
- restricted data/secret canaries and prohibited-content rejection before export;
- synthetic backfill from a durable source while preserving the original evidence gap;
- full recovery, deliberate mode decision, and reconstruction without telemetry authority.

## OPEN Decisions

Human approval is required for:

- OD-027/028 incident command, exercise/validation, threat assumptions, finding severity, and
  residual-risk authority;
- OD-035 clock sampling, offset, uncertainty, freshness, drift, deadline validity, external
  timeout, and recovery timing;
- OD-036 signal/alert inventory, classifications, allowlists, owners, criticality, minimum
  operating posture, telemetry products/collectors/exporters/stores, queries, dashboards, routes,
  regions, sampling, cardinality, retention, access, deletion, hold, cost, alert
  severity/thresholds/coverage/delivery/acknowledgement/escalation/suppression/response objectives,
  target probes, and runbook authorization;
- OD-037 queue/buffer/retry/overflow/drop/backfill bounds and safety/control resource isolation;
  and
- target-specific commands, credentials, contacts, evidence retention, and recovery authorization
  through the applicable protected deployment review.
