# Operational Readiness Review Packet

Status: Proposed review packet; no live-operation authorization

This packet turns drafted runbooks and the threat model into an evidence-controlled readiness
gate. It does not accept an ADR, close an OPEN decision, certify a target, or authorize autonomous
or supervised live broadcast.

## Scope

Use this packet after the relevant architecture and feature ADRs are accepted and before a
production capability is enabled. It is cumulative with:

- the [architecture foundation review](architecture-foundation-review.md);
- the [feature architecture review](feature-architecture-review.md);
- protected code, contract, safety, provider, adapter, and CI review;
- release-readiness approval for the exact deployment.

The current repository has only Proposed procedures. No tabletop, target validation, on-call
activation, legal review, penetration test, or production authorization is claimed.

## Required Decisions

Protected reviewers must decide:

1. the incident-severity and command model, accountable roster, escalation route, handoff rules,
   communications ownership, and exercise cadence under OD-027;
2. the adversary model, validation depth, independent assessor scope, residual-risk owner, review
   triggers, and evidence freshness under OD-028;
3. observed service-latency SLOs under OD-001 and the independent deadline/timeout/clock profile
   under OD-035;
4. jurisdiction, data-role, notification, preservation, and communications obligations with
   accountable privacy/legal counsel;
5. which runbook version is authorized for each named capability and deployment.
6. the disaster recovery sites/failure domains, independently retained recovery generation/
   high-water, composite writer/actor/audience fencing, zero-loss or lost-tail disposition,
   restored epoch/signing/binding supersession, dependency order, RTO/RPO, continuity, and
   failover/failback authority under OD-029;
7. the personal-data breach assessment, notification decision, evidence, coordination, and
   communications profile under OD-030;
8. the software supply-chain, trusted build/release, provenance, signing/update, promotion,
   disable, rollback, and compromise profile under OD-031;
9. the deletion target, tombstone/hold, restore quarantine, provider/local copy, independent
   verification, and completion profile under OD-032.
10. the signal-authority/SLI, telemetry privacy/export, alert ownership/routes, dashboard, and
    monitoring-loss posture under OD-036;
11. the resource/queue bounds, protected reserves, admission/fairness/shedding, and recovery
    profile under OD-037;
12. the provider quota, cost/billing, warning/denial/override, and reconciliation profile under
    OD-038; and
13. the load/stress/spike/soak/chaos target, blast radius, abort, statistics, recovery, evidence,
    and finding-disposition profile under OD-039; any residual-risk acceptance remains exclusively
    governed by OD-028.

No recommendation in this packet supplies those human decisions.

## Evidence States

| State                   | Required evidence                                                                                                                   | Authority conveyed                          |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| `Drafted`               | Complete Proposed procedure, valid internal links, invariant and OPEN checks                                                        | None                                        |
| `Rehearsed`             | Scenario, participants/roles, controlled environment, sanitized timeline, observed outcomes, findings, remediation owners           | None for production                         |
| `Target-validated`      | Versioned deployment steps, target/hardware identity, alert and control evidence, negative cases, recovery and reconciliation proof | Technical evidence only                     |
| `Production-authorized` | Accepted upstream decisions, resolved blocking findings, named accountable approvals, validity scope and expiry/review trigger      | Only the recorded capability and deployment |

Evidence is monotonic only while its assumptions remain true. A material change can invalidate a
later state even when the document version itself is unchanged.

## Current Readiness Matrix

| Artifact                                                                                                            | Current state | Primary dependencies                                                                  | Missing evidence                                                                                                                                    |
| ------------------------------------------------------------------------------------------------------------------- | ------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Emergency stop and deliberate resume](../runbooks/emergency-stop-and-resume.md)                                    | Drafted       | ADR-011/015/019/020/025; OD-010/011/014/015/021/022/027/035/037                       | Tabletop, cloud-loss, composite-fence/restrictive-control/barrier, and target-hardware stop/resume evidence, role and escalation approval           |
| [Rig disconnect and watchdog](../runbooks/rig-disconnect-and-watchdog.md)                                           | Drafted       | ADR-011/015/020/025; OD-010/011/013/014/015/027/035/036/037                           | Disconnect matrix, actor-takeover/epoch reconciliation, watchdog/clock/queue evidence, target ownership                                             |
| [Silence and audio underrun](../runbooks/silence-and-audio-underrun.md)                                             | Drafted       | ADR-010/011/020/021; OD-001/010/013/023/025/027/035/036/037                           | Alert definition, simulator and hardware playout evidence, surface verification                                                                     |
| [Safety fail-closed](../runbooks/safety-fail-closed.md)                                                             | Drafted       | ADR-003/007/008/020/025; OD-001/002/013/014/027/028/035/036/037                       | Fault injection, stale-owner/late-result rejection, zero-output proof, independent safety recovery evidence                                         |
| [Provider degradation and outage](../runbooks/provider-degradation-and-outage.md)                                   | Drafted       | ADR-007/010/020/025; OD-001/002/013/014/025/027/035/036/037/038                       | Correlated-failure and four-cut actor scenarios, possibly-sent/probe/fallback/safety evidence, provider-specific ownership                          |
| [Configuration activation, eligibility, and forward rollback](../runbooks/configuration-activation-and-rollback.md) | Drafted       | ADR-004/008/017/019/020/023/024; OD-022/027/028/034/035/036                           | Draft/version integrity, eligibility propagation, activation/deactivation/schedule/rollback races, cache reconciliation, and deliberate re-enable   |
| [Offline observation and domain-event reconciliation](../runbooks/offline-event-reconciliation.md)                  | Drafted       | ADR-004/011/015/017/023; OD-009/011/015/016/027/033                                   | Crash/power-loss matrix, event manifest/high-water completeness, durable replay, observation ingest, and data-minimization evidence                 |
| [Voice rights revocation](../runbooks/voice-rights-revocation.md)                                                   | Drafted       | ADR-010/011/022; OD-009/011/024/025/027/028                                           | Legal/talent approval, revocation propagation and cache/archive evidence                                                                            |
| [Operator identity compromise](../runbooks/operator-identity-compromise.md)                                         | Drafted       | ADR-011/015/019/020; OD-011/015/022/027/028                                           | IAM-specific revocation, command reconciliation, break-glass and independent security evidence                                                      |
| [Personal-data breach response](../runbooks/personal-data-breach-response.md)                                       | Drafted       | ADR-017/019/026; OD-009/022/027/028/030                                               | Jurisdiction/data-role review, target containment, evidence custody, notification and communications decisions                                      |
| [Privacy deletion and restore reconciliation](../runbooks/privacy-deletion-and-restore-reconciliation.md)           | Drafted       | ADR-004/017/026; OD-009/016/027/028/032                                               | Complete target inventory, opaque-reference/resolver and tombstone/hold policy, provider/backup evidence, canary absence verification               |
| [Software supply-chain and release compromise](../runbooks/software-supply-chain-and-release-compromise.md)         | Drafted       | Repository governance and enabled protected ADRs; OD-012/019/027/028/031              | Trusted build/release profile, provenance/signing, target inventory, rollback and independent validation                                            |
| [Disaster recovery and broadcast continuity](../runbooks/disaster-recovery-and-continuity.md)                       | Drafted       | ADR-004/011/015/016/017/020/025 plus enabled feature ADRs; OD-014/027-029/034/035/037 | Non-rollback/composite fences, closed activation, lost-tail disposition, RTO/RPO, backups, target failover/failback and continuity authorization    |
| [Telemetry and alerting degradation](../runbooks/telemetry-and-alerting-degradation.md)                             | Drafted       | ADR-018/020 plus enabled feature ADRs; OD-001/027/028/035/036                         | Signal/alert registry, target routes, loss/disagreement exercises, restrictive mode ceiling, delivery and recovery evidence                         |
| [Resource exhaustion and backpressure](../runbooks/resource-exhaustion-and-backpressure.md)                         | Drafted       | ADR-004/007/010/011/020/025 plus enabled feature ADRs; OD-014/027/028/035/037/038/039 | Target bounds/reserves, composite actor/command/effect/timer/control saturation, activation/lost-tail pressure, shedding and bounded drain evidence |
| [Load, soak, and chaos acceptance](load-soak-chaos-acceptance.md)                                                   | Drafted       | Exact subject ADRs; OD-001/027/028/035/036/037/038/039                                | Immutable subject/manifests, representative workload, blast radius, abort/cleanup, tail/leak/drain and independent review evidence                  |
| [Threat model](../security/threat-model.md)                                                                         | Drafted       | All enabled feature ADRs; OD-028                                                      | Accountable risk review, abuse-case tests, independent assessment, residual-risk decisions                                                          |

`Drafted` means only that the Proposed artifact exists and is available for review. The state must
be downgraded if link, consistency, or protected-review checks fail.

The dependency column is a compact navigation aid, not a complete gate list. The governing-source
and OPEN-decision sections inside each artifact are cumulative and authoritative for this packet;
the production checklist additionally requires every applicable repository, architecture,
feature, migration, legal/rights, security, and target gate. A reviewer cannot infer that an
omitted dependency is waived. Exact dependency metadata and a future drift check remain required
before operational authorization.

## Minimum Scenario Families

The exercise plan must include, as applicable:

- unsafe or adversarial input through primary, retry, rewrite, fallback, username, and overlay
  paths;
- missing, slow, contradictory, compromised, or correlated provider verdicts;
- approval, rights, surface, artifact, task, signature, epoch, clock, and replay failures;
- PostgreSQL, Redis, control API, session runtime, network, and streaming-PC partitions;
- complete event-contract/framing and subject/scope/classification substitution,
  aggregate-lane reorder/filter/missing-tail/whole-transition/manifest conflict,
  stale-high-water projection reconciliation, restrictive protection overlay, and non-event
  protocol separation;
- draft/version digest substitution, configuration activation/deactivation races, partial
  bundles, fallback widening, scope conflicts, stale activation/eligibility epochs/caches,
  withdrawal during work, schedule cancellation/due-time uncertainty, restrictive in-flight
  changes, forward rollback, emergency DB-outage latch, snapshot pinning, and deliberate
  re-enable;
- stage-host process crash, machine restart, queue ambiguity, local e-stop, and reconnect;
- silence, underrun, wrong surface, stale media, revoked voice, and artifact substitution;
- stolen operator session, privilege misuse, break-glass misuse, and delayed revocation;
- privacy deletion, derived-cache cleanup, backup restore, and incident-evidence separation;
- suspected personal-data breach, scope expansion, provider/processor coordination, evidence
  custody, and human notification decisions;
- dependency/artifact/build/signing/update compromise, promotion halt, target quarantine, trusted
  rebuild, disable, and rollback;
- multi-system/region loss, stale recovery point, split brain, failover/failback, and safe
  broadcast continuity;
- telemetry collector/exporter/store/route loss, stale/missing/contradictory signals, alert
  delivery failure, dashboard disagreement, prohibited attributes, bounded-buffer exhaustion,
  restrictive mode ceiling, and route revalidation;
- global/session/provider/database/Redis/object/runtime/rig/audio/journal/worker quota or capacity
  exhaustion, skewed load, protected-reserve pressure, deterministic shedding, cost/billing
  uncertainty, bounded retry/fallback, and backlog drain;
- representative load, stress, spike, soak, chaos, abort, rollback, cleanup, and recovery under
  an immutable workload/fault manifest;
- failed rollback, shift handoff, and communications failure.

Exercises must prove containment as well as recovery. A successful stop with an unsafe resume path
is not a passing result.

## Evidence Record

For each exercise or target validation, record:

- repository commit and document/contract/policy versions;
- target identity and relevant hardware/software versions;
- immutable workload/fault manifest, scenario, assumptions, arrival/mix/skew, injected faults,
  blast radius, abort/cleanup authority, and expected restrictive outcome;
- assigned roles and separation-of-duties exceptions;
- sanitized timestamps, identifiers, decisions, and observed state transitions;
- pass/fail criteria and actual result;
- complete event contract/framing/scope/subject/ordering/completeness/protection,
  definition/eligibility/activation/schedule/snapshot/lifecycle,
  SLI/query/alert/clock/resource/quota/cost profile versions, raw evidence location, statistical
  method, tail/headroom/leak/backlog-drain/recovery result, and monitoring-route delivery result;
- data classes accessed and evidence location/retention policy;
- unresolved findings, severity assigned by the approved model, owner, and disposition;
- rollback or continued-safe-operation decision;
- reviewers, validity scope, and invalidation triggers.

Do not paste restricted candidate text, viewer memory, credentials, signing material, or
rights-sensitive evidence into this record.

## Operational Authorization Checklist

A protected reviewer may consider `Production-authorized` only when:

- all applicable architecture and feature gates are accepted;
- OD-027 and OD-028, plus applicable OD-029 through OD-039, are decided for the target;
- target-specific commands and contacts are available through the approved resilient channel;
- monitoring detects the conditions the runbook claims to handle;
- the operational signal and alert pipeline's own freshness, delivery, disagreement,
  bounded-failure, and restrictive fallback behavior are target-validated;
- stop, restrictive transition, reconciliation, and deliberate resume paths passed;
- exact event-contract/framing/profile/manifest/high-water/protection overlay, activation and
  eligibility epochs/snapshot/schedule, content/evidence lifecycle, and authoritative recovery
  paths passed without relying on Redis, cache, archive, or mutable current configuration;
- exercises cover both common and adversarial failures without bypassing safety;
- security/privacy/legal/talent reviews are complete for the affected data and rights;
- all blocking findings are closed. Only non-blocking residual risk within the OD-028-approved
  taxonomy may be accepted by the role authorized for that risk class;
- risk acceptance never satisfies or waives an `AGENTS.md` invariant, Accepted ADR, unresolved
  required feature/migration gate, missing legal or rights authority, required evidence,
  target-specific validation, or protected-review requirement;
- remote CI, repository protection, deployment rollback, and release review evidence identify the
  exact commit;
- the exact target passes the applicable load/soak/chaos acceptance rows with zero safety,
  authorization, rights, privacy, audit, freshness, or e-stop invariant violations;
- the authorization names its capability, deployment, effective period or review trigger, and
  rollback owner.

## Decision Record

| Item                                                | Drafted / Rehearsed / Target-validated / Production-authorized | Reviewer and role | Date | Evidence scope, retained OPEN items, expiry, or follow-up |
| --------------------------------------------------- | -------------------------------------------------------------- | ----------------- | ---- | --------------------------------------------------------- |
| Emergency stop and deliberate resume                | Drafted                                                        |                   |      |                                                           |
| Rig disconnect and watchdog                         | Drafted                                                        |                   |      |                                                           |
| Silence and audio underrun                          | Drafted                                                        |                   |      |                                                           |
| Safety fail-closed                                  | Drafted                                                        |                   |      |                                                           |
| Provider degradation and outage                     | Drafted                                                        |                   |      |                                                           |
| Configuration activation and forward rollback       | Drafted                                                        |                   |      |                                                           |
| Offline observation and domain-event reconciliation | Drafted                                                        |                   |      |                                                           |
| Voice rights revocation                             | Drafted                                                        |                   |      |                                                           |
| Operator identity compromise                        | Drafted                                                        |                   |      |                                                           |
| Personal-data breach response                       | Drafted                                                        |                   |      |                                                           |
| Privacy deletion and restore reconciliation         | Drafted                                                        |                   |      |                                                           |
| Software supply-chain and release compromise        | Drafted                                                        |                   |      |                                                           |
| Disaster recovery and broadcast continuity          | Drafted                                                        |                   |      |                                                           |
| Telemetry and alerting degradation                  | Drafted                                                        |                   |      |                                                           |
| Resource exhaustion and backpressure                | Drafted                                                        |                   |      |                                                           |
| Load, soak, and chaos acceptance                    | Drafted                                                        |                   |      |                                                           |
| Threat model                                        | Drafted                                                        |                   |      |                                                           |
| Overall operational readiness                       | Drafted                                                        |                   |      | Name only the capability and deployment authorized        |

Approval must never be inferred from a pull-request merge, elapsed time, an unreviewed rehearsal,
or silence.
