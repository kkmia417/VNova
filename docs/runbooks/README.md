# Operational Runbook Index

Status: Proposed operational design; not production authority

These runbooks define the minimum safe shape of incident response for VNova. They are review
artifacts, not executable procedures and not evidence that a capability is ready for live use.
Every enabled production capability needs target-specific commands, owners, communication paths,
approved thresholds, rehearsals, and protected human authorization before its runbook can become
operational.

## Safety Authority

When instructions disagree, responders apply this order:

1. `AGENTS.md`, Accepted ADRs, and the invariant that missing safety authority produces no
   autonomous output.
2. A local `stage-host` hard stop, restrictive epoch, rights revocation, or other already-valid
   safety control.
3. The approved incident command and recovery policy for the affected deployment.
4. This Proposed runbook family.
5. Provider or platform guidance.

An incident commander can coordinate response but cannot waive a safety verdict, extend an
expired authorization, re-enable revoked rights, bypass an e-stop, or turn an unavailable
dependency into implicit approval. Stop and containment paths must remain available during
control-plane, persistence, identity, and provider failures.

## Common Response Contract

Every runbook specializes the following fail-closed sequence:

1. **Protect:** stop or suppress the affected autonomous output when safety, identity, rights,
   integrity, freshness, or delivery state is uncertain.
2. **Declare:** open an incident record using the approved deployment process; name the
   accountable response roles without delaying containment.
3. **Bound:** identify affected sessions, surfaces, voices, epochs, artifacts, principals, and
   time interval from authoritative identifiers.
4. **Preserve:** retain the minimum evidence needed for reconstruction and legal or security
   review without copying restricted content into general audit or chat channels.
5. **Diagnose:** distinguish symptom from cause using durable state, authenticated telemetry, and
   target-local evidence. Redis is never the recovery source.
6. **Recover restrictively:** restore observability and control first; do not automatically replay
   in-doubt work, raise autonomy, revive expired work, or clear a local stop.
7. **Verify:** prove the exit criteria on the affected target and reconcile PostgreSQL, transport,
   and stage-host state.
8. **Resume deliberately:** use the authorized role, confirmation, reason, and post-recovery mode.
   The emergency-stop action itself never waits for confirmation.
9. **Learn:** preserve a sanitized timeline, identify control and runbook gaps, and route any
   invariant change through an ADR.

If an exact command, endpoint, role assignment, threshold, communication destination, or legal
classification is absent, it is OPEN. Responders must not infer one from examples in this
repository.

## Response Roles

The runbooks use role labels rather than named people:

- **Incident commander:** owns coordination, scope, handoffs, and closure evidence.
- **Safety lead:** owns autonomous-output containment and verifies safety-gate recovery.
- **Stage operator:** has physical or authenticated control of the streaming PC and local stop.
- **Service owner:** diagnoses and restores the affected VNova boundary.
- **Security lead:** owns suspected identity, integrity, credential, or adversarial compromise.
- **Privacy/legal lead:** determines notification, preservation, and data-subject obligations.
- **Communications lead:** coordinates approved internal, talent, platform, and public messaging.
- **Recorder:** maintains a sanitized event timeline and decision log.

One trained person may fill multiple roles only where the accepted separation-of-duties policy
allows it. OD-027 must assign accountable roles, escalation paths, and coverage before live
operation.

## Runbook Catalog

| Incident class                                                                   | Runbook                                                                                                 | Primary containment boundary                                                              |
| -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Emergency stop or unsafe output                                                  | [Emergency stop and deliberate resume](emergency-stop-and-resume.md)                                    | Local playback plus cloud dispatch                                                        |
| Rig link, heartbeat, or watchdog failure                                         | [Rig disconnect and watchdog](rig-disconnect-and-watchdog.md)                                           | `stage-host`                                                                              |
| Silence, audio underrun, or playout failure                                      | [Silence and audio underrun](silence-and-audio-underrun.md)                                             | Local playback and session output                                                         |
| Missing or unhealthy safety verdict                                              | [Safety fail-closed](safety-fail-closed.md)                                                             | Safety gate and approved dispatch                                                         |
| LLM, moderation, TTS, or media dependency failure                                | [Provider degradation and outage](provider-degradation-and-outage.md)                                   | Provider gateway and mode control                                                         |
| Configuration integrity, activation, eligibility, schedule, or rollback mismatch | [Configuration activation, eligibility, and forward rollback](configuration-activation-and-rollback.md) | Configuration authority, dependent work, caches, and deliberate re-enable                 |
| Transport gap or disconnected local observation buffer                           | [Offline observation and domain-event reconciliation](offline-event-reconciliation.md)                  | PostgreSQL recovery and stage-host reconciliation                                         |
| Voice-use authorization invalidation                                             | [Voice rights revocation](voice-rights-revocation.md)                                                   | Rights state, synthesis, cache, and playout                                               |
| Stolen or suspect operator authority                                             | [Operator identity compromise](operator-identity-compromise.md)                                         | Identity, sessions, privileged commands, and epochs                                       |
| Suspected personal-data exposure, loss, or unauthorized access                   | [Personal-data breach response](personal-data-breach-response.md)                                       | Data access, propagation, evidence custody, and accountable notification decision         |
| Deletion, rebuild, backup, or restore inconsistency                              | [Privacy deletion and restore reconciliation](privacy-deletion-and-restore-reconciliation.md)           | Source/derived data, tombstones, holds, copies, and completion evidence                   |
| Dependency, build, artifact, signing, or update compromise                       | [Software supply-chain and release compromise](software-supply-chain-and-release-compromise.md)         | Promotion, artifacts, release authority, targets, rollback, and trusted rebuild           |
| Multi-system loss, corruption, failover, or failback                             | [Disaster recovery and broadcast continuity](disaster-recovery-and-continuity.md)                       | Safe hold, authoritative recovery order, fencing, rigs, and deliberate resume             |
| Telemetry loss, stale signals, alert-delivery failure, or dashboard disagreement | [Telemetry and alerting degradation](telemetry-and-alerting-degradation.md)                             | Operational signal/alert trust, restrictive mode ceiling, routes, and deliberate recovery |
| Queue, quota, storage, runtime, transport, or rig capacity exhaustion            | [Resource exhaustion and backpressure](resource-exhaustion-and-backpressure.md)                         | Protected reserves, admission/shedding, backpressure, and bounded backlog recovery        |

The [security threat model](../security/threat-model.md) identifies adversarial conditions that
may invoke more than one runbook.

## Readiness Lifecycle

Each runbook moves independently through these evidence states:

| State                   | Meaning                                                                                                                                                                                                                                                                             |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Drafted`               | The Proposed procedure exists, links resolve, and architecture invariants are explicit.                                                                                                                                                                                             |
| `Rehearsed`             | A controlled tabletop or deterministic rehearsal completed with a sanitized timeline and recorded findings.                                                                                                                                                                         |
| `Target-validated`      | Target-specific controls, commands, alerts, ownership, and exit checks passed on the required target. Representative hardware may support only controls proven target-independent; it cannot establish an e-stop, watchdog, audio, clock, adapter, or other target-dependent claim. |
| `Production-authorized` | Accountable protected reviewers accepted the evidence and deployment-specific runbook version for the named capability.                                                                                                                                                             |

States never advance from document age, merge status, or a generic test pass. A material topology,
provider, renderer, rights, identity, safety, or legal change invalidates affected evidence and
returns the runbook to the appropriate earlier state.

Current state for every catalog entry is `Drafted` only. The
[operational readiness review packet](../governance/operational-readiness-review.md) records
evidence and human decisions.

## Evidence Handling

Incident records should use opaque IDs, classifications, hashes, verdict categories, policy
versions, timestamps, and bounded state transitions. They must not become a second store for:

- raw candidate or prompt text;
- viewer-memory content or embeddings;
- unrestricted chat or username content;
- synthesized voice content unless separately authorized;
- authentication tokens, signing material, provider credentials, or recovery secrets;
- rights evidence whose custody policy does not permit the incident audience.

Evidence access, retention, deletion, and legal hold follow the source data class. A digest does
not automatically declassify personal, restricted, or rights-sensitive data.

## Activation Gate

Before a catalog entry can be marked `Production-authorized`, reviewers must confirm:

- its governing ADRs and OPEN parameters are accepted for the enabled scope;
- the exact alert source, incident intake, role roster, and escalation route exist;
- target-specific steps are versioned and accessible during control-plane loss;
- required local controls work without the cloud where the architecture requires it;
- deterministic rehearsal and target validation cover both containment and recovery;
- e-stop, watchdog, audio, clock, adapter, queue, and local recovery claims identify and pass on
  the exact production rig/configuration they authorize;
- telemetry and evidence are sufficient to reconstruct the path without violating data
  separation;
- rollback or continued-safe-operation behavior is explicit;
- security, privacy/legal, talent, and communications reviewers participate where relevant;
- the applicable privacy-breach, deletion/restore, release-integrity, and disaster-recovery
  profiles under OD-029 through OD-032 are decided for capabilities that depend on them.
- the applicable freshness/deadline/clock, observability/alerting, capacity/backpressure,
  cost/quota, and load/soak/chaos profiles under OD-035 through OD-039 are decided and evidenced
  for the named target.

## Informative References

These sources inform the review method; they do not override VNova policy or constitute legal
advice:

- [NIST SP 800-61 Rev. 3, Incident Response Recommendations and Considerations for Cybersecurity Risk Management](https://csrc.nist.gov/pubs/sp/800/61/r3/final)
- [NIST AI 600-1, Generative Artificial Intelligence Profile](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence)
- [MITRE ATLAS](https://atlas.mitre.org/)
- [Japan Personal Information Protection Commission: response resources for personal-data leakage](https://www.ppc.go.jp/personalinfo/legal/leakAction/)
