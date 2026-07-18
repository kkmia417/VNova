# Privacy Deletion And Restore Reconciliation

Status: Proposed operational runbook; implementation and production use pending

Readiness state: `Drafted` only; no rehearsal, target validation, legal approval, or production
authorization

Date: 2026-07-17

Governing sources:

- [`AGENTS.md`](../../AGENTS.md)
- [`vnova-review-handoff.md`](../../vnova-review-handoff.md)
- [ADR-017: data retention, privacy, and PII](../adr/0017-data-retention-privacy-and-pii.md)
- [ADR-026: opaque audit references for deletable personal data](../adr/0026-opaque-audit-references-for-deletable-personal-data.md)
- [Privacy and retention model](../architecture/privacy-retention-model.md)
- [Threat model, including TM-12](../security/threat-model.md)
- [Disaster recovery and broadcast continuity](disaster-recovery-and-continuity.md)
- [Offline observation and domain-event reconciliation](offline-event-reconciliation.md)
- [Operational runbook contract](README.md)

This is a proposed review artifact. It does not determine whether a person has a legal right to
deletion, select deletion or anonymization, authorize access, release a hold, define a retention
period or SLO, select a storage mechanism, create a schema or migration, or provide executable
commands. Those decisions require the accountable human authorities and accepted protected
artifacts named below.

## Purpose And Scope

Use this runbook for:

- an authenticated viewer- or operator-initiated deletion, correction, or approved anonymization
  case;
- policy-driven retention expiry;
- failed or uncertain propagation to a source, derivative, provider, replica, backup, or local
  buffer;
- suspected resurrection through cache fill, reindexing, embedding generation, offline ingest,
  replica recovery, backup restore, or data rebuild;
- any restore or rebuild that could contain data deleted after its recovery point.

The runbook prevents the TM-12 failure mode: deleting a primary row while leaving a usable copy or
allowing an older copy to reappear. It governs privacy availability, not broadcast approval.
Safety, rights, identity, and emergency controls continue to apply independently.

## Non-Negotiable Invariants

- Viewer memory and audit evidence never share tables, raw content, or access roles.
- Every deletion case is authenticated, authorized, idempotent, durable, and bound to a versioned
  target manifest before completion can be evaluated.
- Every derived record has an authoritative source relationship. A broken or unknown relationship
  blocks derived use and rebuild; it never proves that deletion succeeded.
- A durable deletion/tombstone barrier takes precedence over older writes, cache entries,
  embeddings, replicas, offline observations, replayed domain events, backup contents, and
  rebuild input.
- A restored or rebuilt dataset is quarantined before any runtime, operator, provider, index,
  renderer, or ordinary read path can access it. Readability is an explicit post-reconciliation
  decision.
- PostgreSQL is the system of record for durable operational deletion-case and source state.
  Redis is transport/cache only and is never deletion or recovery authority.
- Backup, replica, provider, or local-buffer unavailability is unknown state, not proof of
  absence.
- Every external deletion, provider, storage, replica, restore, verification, or local-buffer
  operation has an explicit timeout. A timeout leaves that target unresolved; retries are bounded
  and idempotent.
- Legal or incident preservation does not silently cancel a request, authorize normal use, or
  permit a false completion claim. Held data remains purpose-restricted and unavailable outside
  the approved hold workflow.
- No case is reported complete while any in-scope target is missing, unknown, failed, provider
  uncertain, awaiting approved backup expiry, blocked by hold, awaiting restore verification, or
  independently unverified.
- Ordinary logs, events, metrics, traces, alerts, tickets, manifests, and incident chat contain
  opaque IDs and minimized outcomes, never viewer-memory values, raw viewer input, prompts,
  candidate text, credentials, provider payloads, voice data, rights evidence, or deleted content.
- Pending ADR-026 review, none of those ordinary surfaces retains a raw, normalized, truncated,
  salted, unsalted, or keyed content-derived viewer message/memory digest as a substitute.

## Trigger Conditions

Begin or reopen this workflow when:

| Trigger                                                                                                           | Required initial interpretation                                                                                                            |
| ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Authenticated deletion, correction, or anonymization request                                                      | Scope and legal/policy authority are not yet proved; quarantine affected use while the case is evaluated where approved policy requires it |
| Retention policy reaches its approved terminal action                                                             | Create or resume the durable case; do not rely on a background job's success counter                                                       |
| Derived/source linkage is missing or contradictory                                                                | Block the derivative and every rebuild that could consume it                                                                               |
| Provider, replica, cache, index, embedding, object, backup, or local buffer does not confirm its required outcome | Case remains partial or blocked                                                                                                            |
| A restore or rebuild is proposed                                                                                  | Candidate data remains quarantined until current tombstones and retention state are reconciled                                             |
| Restored or rebuilt data becomes readable before reconciliation                                                   | Treat as a privacy/security incident and remove the affected path from readability                                                         |
| Canary or case-specific verification finds a residual or resurrected copy                                         | Reopen or fail the case, expand the target manifest, and quarantine affected paths                                                         |
| A legal or incident hold overlaps the target                                                                      | Pause only the human-approved held action/scope; do not mark deletion complete                                                             |
| An older write, event, replica, or backup conflicts with a newer tombstone                                        | The newer authoritative restrictive state wins; preserve the conflict as evidence                                                          |

Exact intake channels, response times, automatic quarantine rules, and escalation severity remain
OPEN.

## Response Roles

These common runbook labels describe responsibilities, not IAM grants or legal authority:

| Role                | Duties during this workflow                                                                                                       |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Incident commander  | Coordinates scope, assignments, handoffs, and closure evidence without deciding legal entitlement or overriding privacy controls  |
| Safety lead         | Verifies that quarantined, deleted, or uncertain data cannot enter memory retrieval, generation, media, or broadcast output       |
| Stage operator      | Protects and reconciles affected stage-host local buffers without copying their content into general evidence                     |
| Service owner       | Maps and remediates the assigned source, cache, embedding, index, object, provider, replica, backup, restore, or rebuild boundary |
| Security lead       | Owns suspected tampering, unauthorized readability, identity abuse, manifest corruption, or deliberate resurrection               |
| Privacy/legal lead  | Determines request authority, data class, action, hold conflict, jurisdiction, notification, and acceptable terminal evidence     |
| Communications lead | Uses approved channels for requester, talent, provider, platform, regulator, and internal communications                          |
| Recorder            | Maintains the minimized case timeline, target-manifest versions, decisions, evidence locations, and unresolved outcomes           |

OD-027 must map these labels to accountable people, coverage, capabilities, escalation paths, and
separation-of-duty requirements. Assignment to a response role does not grant restricted-data
reveal, hold placement/release, deletion approval, legal judgment, audit export, or production
readability authority.

## Immediate Containment

1. **Open or resume one durable case.** Bind the request, requester verification reference,
   authority decision, scope, policy/legal basis, idempotency identity, and current target-manifest
   version without copying target content.
2. **Quarantine affected use.** Prevent uncertain target data from memory retrieval, prompt
   assembly, provider disclosure, indexing, cache repopulation, export, broadcast, or ordinary
   read access. Quarantine is reversible containment; it is not proof of deletion.
3. **Quarantine every restore candidate.** A restored database, replica, object set, index,
   backup extraction, or local-buffer replay remains outside ordinary readability before its
   first record is served or used.
4. **Pause resurrection mechanisms.** Hold affected rebuild, re-embedding, reindexing, cache
   warming, replica promotion, provider resubmission, backup publication, offline-observation
   materialization, and domain-event replay until the current tombstone state is available.
5. **Preserve minimal evidence.** Retain content-independent case/source/derived IDs, versions,
   locations, causal positions, hold references, outcomes, and only separately governed
   non-personal artifact-integrity digests. Do not preserve target content or its content-derived
   verifier in an ordinary log to compensate for deletion.
6. **Apply the stricter scope when isolation is uncertain.** Scoped quarantine is allowed only
   when source relationships and access isolation are authoritative. Ambiguity expands
   quarantine; it never narrows the manifest by assumption.
7. **Escalate unauthorized readability.** If deleted or quarantined data was served, retrieved,
   disclosed to a provider, or otherwise made available, invoke the
   [personal-data breach response](personal-data-breach-response.md) through the approved
   privacy/security incident path while keeping this reconciliation active.

A containment call that times out has unknown outcome. Keep the affected path quarantined and
record the unresolved target.

## Target Manifest

The case owns a versioned target manifest. Each revision is immutable; discovery of another copy
creates a new revision and invalidates any prior completion decision until the new revision is
resolved.

Each target entry records only minimized metadata:

- stable case, target, source, and derived-record identifiers;
- data class, declared purpose, owning boundary, region/environment, and retention-policy version;
- authoritative source type and provenance relationship;
- dependency edges to embeddings, indexes, caches, objects, replicas, provider copies, backups,
  exports, and stage-host/offline buffers;
- requested and approved privacy action, such as deletion, correction, or approved anonymization,
  plus a separate hold or backup-terminal disposition where applicable;
- current quarantine/readability state;
- tombstone/deletion causal identity and the authoritative state against which it was evaluated;
- responsible service owner and required privacy/legal or security review;
- explicit timeout, bounded-attempt outcomes, provider acknowledgements, and unresolved
  uncertainty;
- restore/rebuild paths that could rematerialize the target;
- independent verification method, verifier identity/role reference, result, and evidence
  location.

The manifest contains no target values, raw messages, memory values, prompts, candidate text,
media, provider bodies, credentials, or legal evidence. It is purpose-limited and access
controlled; an opaque ID or digest can remain linkable and follows the source data classification.

### Completeness Rules

- A manifest is complete only against the approved data inventory and consumer registry for the
  exact policy/version scope.
- Unknown classification, purpose, owner, deletion behavior, consumer, provider behavior, or
  restore path is an unresolved target.
- A successful source deletion does not remove its derivative entries from the manifest.
- A component's aggregate success count is not evidence that the named target reached its
  required state.
- Discovery coverage and absence verification are separate. Failure to discover a path does not
  make it absent.

## Source-To-Derived Linkage

Each derivative is usable only while it can prove a current, permitted authoritative source:

| Boundary                              | Required linkage and restrictive behavior                                                                                                                                              |
| ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Typed viewer memory/source records    | Source record and provenance remain authoritative; deletion or approved anonymization starts from the named source                                                                     |
| Embeddings                            | Each row has a source-record foreign key and model/version; source deletion cascades to the embedding, and the tombstone prevents rebuild                                              |
| Search indexes and materialized views | Indexed identity maps back to a current source and tombstone state; an orphan or stale generation is removed from service                                                              |
| Caches, including Redis               | Cache identity maps to source/version and cannot outlive a current tombstone; cache loss or flush is not deletion evidence                                                             |
| Objects and media artifacts           | Object version and lifecycle entry map to the governed source/use; object-store presence grants no privacy, safety, rights, or retention authority                                     |
| Replicas and read models              | Replica position and source identity are known; a lagging or recovered replica remains unreadable until current tombstones apply                                                       |
| External providers                    | Provider-copy purpose/profile and request identity map to the source/case; a provider acknowledgement is evaluated under the approved contractual and technical evidence policy        |
| Backups and snapshots                 | Recovery point, included sources, tombstone horizon, and restore paths are known; immutable backup retention remains an explicit unresolved target until its approved terminal outcome |
| Stage-host and offline buffers        | Rig/boot/cursor identity and event/source references are known; reconnect applies current tombstones before an offline record can materialize data                                     |

A missing edge blocks the derivative and expands investigation. It must not be repaired by copying
the deleted value into the manifest or audit log.

## Tombstone Ordering

A tombstone is a durable, content-free restriction that prevents older or restored data from
becoming usable. Its exact schema and storage design remain OPEN, but every implementation must
preserve these semantics:

1. The authenticated case, reviewed scope, target-manifest revision, and hold decision become
   durable before a terminal deletion claim.
2. The authoritative tombstone/restriction commits before the source deletion/anonymization
   attempt and before any derivative, restored record, offline observation, or replayed domain
   event can be made readable.
3. Ordering is based on an authoritative causal version or equivalent serialized state, not on
   whichever wall-clock timestamp is largest.
4. A duplicate tombstone with the same identity and canonical content is idempotent. Reuse of an
   identity with different content is an integrity incident.
5. An older source write, cache fill, index job, embedding task, replica state, provider result,
   offline observation, replayed domain event, or backup restore cannot override a newer
   tombstone.
6. Redis delivery, in-memory state, consumer offset, or job completion is not proof that the
   tombstone committed. Durable recovery starts from PostgreSQL and the accepted current
   deletion-control state.
7. If tombstone continuity across a restore point cannot be proved, the restored scope remains
   quarantined.

Tombstone retention and compaction must preserve every accepted backup, replica, provider,
offline, rebuild, and legal-hold horizon. Exact values and mechanisms require OD-009 and a
protected schema/migration decision.

## Legal And Incident Hold Conflicts

Only the accountable privacy/legal authority may determine that a legal or incident hold changes
the requested action.

- A hold records its authority, scope, purpose, start/review state, affected manifest entries, and
  restricted evidence reference without copying held content into ordinary audit.
- A hold preserves only the approved scope. Unrelated targets may proceed only when separation is
  authoritative and privacy/legal approves the split.
- Held data is quarantined from ordinary use, provider disclosure, memory retrieval, rebuild, and
  broadcast unless the hold authority explicitly permits a purpose-limited access.
- A hold-blocked entry remains nonterminal for deletion. Requester communication must not say
  deleted, absent, or complete.
- Incident preservation cannot be created informally by copying target content into a ticket,
  chat, trace, or general-purpose evidence store.
- Hold release triggers a fresh policy, scope, tombstone, and target-manifest review. It does not
  restore ordinary readability or complete deletion automatically.
- Conflict, partial execution, release, correction, and every privileged access are durably
  audited with minimized references.

The legal basis, notification language, review cadence, preservation scope, and release authority
are human decisions and are not supplied by this runbook.

## Read-Only Diagnosis

Diagnosis does not delete, anonymize, place/release a hold, advance a tombstone, acknowledge a
provider, compact a backup, ingest an offline observation, replay a domain event, publish a
restore, or mark a case complete.

### Establish Case And Authority

- Verify case/idempotency identity, requester-verification reference, scope, environment, data
  class, purpose, policy version, requested action, and authorization decision.
- Confirm the current target-manifest revision and whether new discoveries invalidated earlier
  evidence.
- Identify active or conflicting legal/incident holds and the human authority responsible for
  each.
- Confirm viewer-memory, restricted-data, audit, and evidence roles remain physically and
  logically separated.

### Trace The Copy Graph

- Start from each authoritative source ID and traverse registered source-to-derived relationships.
- Compare the manifest to data inventory, provider profiles, cache/index definitions, replica
  topology, object lifecycle, backup catalog, restore/rebuild plans, and stage-host/offline
  consumers.
- Identify orphaned derivatives, unknown consumers, stale replicas, unacknowledged providers,
  backup generations, local buffers, and restore candidates.
- Treat inability to query a target, a timeout, permission failure, or missing inventory as
  unknown, not absence.

### Establish Ordering And Readability

- Confirm the authoritative tombstone/restriction and manifest revision are newer than or
  causally dominate every candidate source, derivative, replica, event, and recovery point.
- Confirm quarantine is enforced on every actual read/use path, not only indicated by a control
  plane flag.
- Check that rebuild, cache, indexing, provider, and offline-ingest jobs consult current source and
  tombstone state before materialization.
- Verify no restored copy has already entered memory retrieval, prompt assembly, provider
  processing, export, or broadcast.

All diagnosis uses IDs, classifications, versions, causal positions, digests, outcomes, and
restricted references. Inspecting target content requires a distinct, purpose-bound, time-bounded,
audited reveal authorization and never permits copying it into this case record.

## Deletion And Propagation Procedure

Proceed only through the approved privacy workflow. A failed step leaves the case active and the
affected scope quarantined.

### Phase 1: Validate Scope And Holds

1. Confirm requester identity/authority and the exact human-approved action.
2. Reconcile data class, purpose, jurisdiction, policy, and all hold conflicts.
3. Freeze the target-manifest revision used for this attempt and retain an explicit discovery
   coverage statement.
4. If authority, scope, action, or hold state is unknown, perform no irreversible action and keep
   affected use quarantined.

### Phase 2: Establish The Restrictive Barrier

1. Durably bind the case, manifest revision, source identities, approved action, and current hold
   decision.
2. Commit the content-free tombstone/restriction using the accepted authoritative ordering
   mechanism.
3. Confirm active writers, consumers, rebuilders, replicas, and offline-ingest paths cannot admit
   a causally older copy.
4. Do not infer success from Redis delivery, cache eviction, worker acknowledgement, or a
   scheduled job.

### Phase 3: Apply The Source Action

1. Delete or anonymize each source exactly as approved; do not widen anonymization or retain a
   convenience copy.
2. Preserve only content-independent opaque audit references consistent with the pending ADR-026
   correction; do not encode ADR-017's unqualified viewer-data hash allowance while review is
   unresolved.
3. Record a per-target outcome and authoritative version. A bulk result without target identity is
   insufficient.
4. A timeout, transaction uncertainty, or late result remains unresolved and is retried
   idempotently under the approved bound.

### Phase 4: Propagate Across Derived And External Targets

For every manifest entry:

- invalidate and remove embeddings, indexes, materialized views, and caches through their source
  relationship;
- make objects/artifacts non-readable and apply their approved deletion, anonymization, or
  retention action;
- reconcile replicas and read models against the current tombstone before they serve reads;
- issue the minimum approved provider deletion/correction request with an explicit timeout and
  retain only the minimized acknowledgement evidence;
- reconcile stage-host and offline buffers under the offline-observation/domain-event runbook
  before ingest, compaction, or local deletion;
- mark backups/snapshots with the current tombstone requirement and their accepted terminal
  policy; do not report them absent while awaiting approved expiry or destruction;
- update the manifest with each distinct terminal, partial, blocked, failed, timed-out, or unknown
  outcome.

Do not weaken a target's action because another target lacks an API or is difficult to inspect.
Uncertainty remains visible.

### Phase 5: Independently Verify

1. Use a verifier independent of the deletion executor and its success report.
2. Exercise every in-scope direct, derived, replica, provider, restore, rebuild, and local-buffer
   read/materialization path permitted by the approved verification plan.
3. Verify source absence or approved anonymization, derivative nonexistence/non-readability,
   current tombstone enforcement, and quarantine of unresolved held copies.
4. Treat timeout, permission failure, stale replica, unavailable provider, or incomplete coverage
   as a failed or inconclusive verification, not a pass.
5. Bind results to the exact manifest, policy, schema, provider, backup, and software versions.

## Restore And Rebuild Reconciliation

No restored or rebuilt data becomes readable merely because restore integrity checks or ordinary
application tests pass.

### Prove One Current Write Lineage

1. Before trusting a deletion, retention, or hold authority, prove that one current PostgreSQL
   write lineage owns the affected scope and that every former writer is fenced under the
   disaster-recovery workflow.
2. Identify and preserve every branch created by failover, restore, split brain, delayed
   replication, or offline administration. Reconcile every deletion case, target-manifest
   revision, tombstone, hold, hold release, and terminal outcome from those branches into the
   current lineage before release.
3. Treat an unfenced writer, an undiscovered branch, conflicting causal history, or an
   unverifiable manifest horizon as an unknown outcome. Keep candidate data quarantined and
   invoke the disaster-recovery workflow; selecting one branch as `trusted` is not sufficient.
4. Bind the single-writer, fencing, branch-inventory, and reconciliation evidence to the recovery
   generation and candidate restore identity without copying personal content into evidence.

### Quarantine Before Readability

1. Place the entire candidate restore/rebuild output behind a boundary that ordinary runtime,
   operator, provider, cache, index, export, and broadcast paths cannot read.
2. Record the candidate recovery point, included source/derived domains, schema/policy versions,
   backup/snapshot identities, and known tombstone horizon without copying content.
3. Load the accepted current deletion, retention, anonymization, and hold state from a trusted
   authority that is not silently regressed to the candidate restore point.
4. If current tombstone continuity or authority is unavailable, keep the candidate quarantined.

### Reconcile Before Materialization

1. Compare every restored source and derivative to the current target manifests and tombstones.
2. Apply all tombstones and approved anonymization actions that causally follow the restore point.
3. Remove or quarantine orphaned derivatives and unknown classifications before rebuilding any
   cache, embedding, index, object view, or replica.
4. Rebuild only from current, permitted authoritative sources. A deleted backup copy, stale
   replica, provider export, offline buffer, or derived record cannot become rebuild input.
5. Reconcile offline observations and replayed domain events before they materialize state;
   neither a stale observation nor a stale event can recreate a deleted source or derivative.
6. Preserve audit/history separation: restoration must not copy viewer-memory content into audit
   or grant audit roles access to restored memory.

### Verify Before Release

1. Run case-specific absence checks for every deletion whose tombstone follows the recovery point.
2. Run the approved independent canary suite across restored sources and all derivative/rebuild
   paths.
3. Prove actual read/use paths deny or omit quarantined, deleted, held, orphaned, and unknown data.
4. Re-run verification after cache fill, reindex, embedding generation, replica catch-up, provider
   synchronization, and offline-buffer reconciliation.
5. Release only the explicitly verified scope through the approved human authorization. Unknown
   scope remains quarantined and cannot be risk-accepted into readability by convenience. The
   single-writer, fencing, branch-reconciliation, and recovery-generation evidence above must
   still be current at release.

## Canary And Independent Absence Verification

Canaries are synthetic, non-personal records designed to prove control coverage. They do not
replace case-specific verification.

The rehearsal/validation plan must:

- create a canary source with known source-to-derived relationships across every enabled source,
  embedding, index, cache, object, replica, provider test boundary, backup, and local-buffer path;
- bind the canary to a target manifest and tombstone without using a real viewer or talent record;
- execute deletion, cache/rebuild activity, an older restore, replica recovery, provider
  reconciliation, and offline ingest;
- use a verifier that is organizationally and technically independent from the deletion executor
  and does not trust its reported success;
- query actual read/use paths as well as storage/control metadata;
- inject at least one residual or resurrected copy and prove verification fails;
- treat an unavailable path as unknown rather than absent;
- remove the canary and its derivatives under the same governed process;
- retain only IDs, versions, digests, coverage, outcomes, and evidence references.

An absence check proves only the named scope, versions, query paths, and point in time. Human
review determines evidence freshness and whether provider or backup evidence is independently
sufficient.

## Completion And Exit Gates

The case may be marked complete only when every applicable gate passes:

- requester authority, data class, action, policy, jurisdiction, and hold disposition are
  approved and durable;
- the final target-manifest revision covers every registered source, derivative, provider,
  replica, backup, restore/rebuild path, and local buffer in scope;
- the authoritative source reached its approved action and every derived source relationship is
  resolved;
- the current tombstone causally dominates older writes, events, replicas, offline buffers,
  backups, and rebuild inputs;
- every external call has a known accepted terminal outcome under the approved evidence policy;
- no target is failed, timed out, unknown, provider uncertain, backup pending, restore pending,
  hold blocked, partially propagated, orphaned, or awaiting verification;
- independent case-specific verification proves the required absence, anonymization, or
  quarantine outcome through actual read/use paths;
- the independent canary suite passes for the exact enabled topology and versions;
- any restore or rebuild remains quarantined until all post-restore cache, embedding, index,
  replica, provider, and local-buffer checks pass;
- ordinary logs, audit, manifests, evidence, and communications contain no deleted/restricted
  values and preserve viewer-memory/audit separation;
- the minimized completion audit binds the case, final manifest, policy, tombstone, verification,
  human decisions, and evidence references.

If any gate is unresolved, the case remains partial, blocked, or active. A workflow may hand off
an explicitly quarantined target with an accountable owner, but that is not deletion completion,
absence proof, restore reconciliation, or permission to make data readable.

## Evidence Packet

Record:

- case, request, requester-verification, authorization, policy, manifest, target, source,
  derivative, provider-attempt, backup/snapshot, restore/rebuild, rig/boot/cursor, verifier,
  audit, and trace identifiers;
- data class, purpose, environment/region, approved action, source relationship, causal version,
  tombstone identity, and quarantine/readability outcome;
- hold authority/scope reference, conflict and release decisions, and purpose-limited access
  outcomes;
- explicit timeout, bounded retry, provider acknowledgement, replica position, backup terminal
  policy, local-buffer, and restore results;
- discovery coverage, independent verifier identity/role, query-path coverage, canary manifest,
  expected result, actual result, and artifact hashes;
- partial/blocked/unknown outcomes, owners, next review, requester communication state, and final
  human disposition.

The packet contains no target values, raw messages, viewer-memory values, prompts, candidates,
embeddings, provider bodies, media, credentials, identity documents, rights evidence, or held
content. Evidence access, retention, deletion, and hold follow the source classification.

## Escalation

Escalate while keeping affected data quarantined when:

- deleted or quarantined data becomes readable, retrievable, disclosed, rebuilt, or broadcast;
- the target manifest, tombstone, source relationship, deletion evidence, or verifier may be
  altered or forged;
- requester identity/authority, data classification, jurisdiction, action, or hold authority is
  disputed;
- a provider, replica, backup, restore, local buffer, or unknown consumer cannot prove the
  required state;
- a source was removed before its dependencies were discoverable or a derivative became orphaned;
- current tombstone continuity cannot be established across a restore;
- viewer-memory content enters audit, logs, tickets, traces, support channels, or a hold created
  outside the approved restricted store;
- completion, requester communication, or restore release was asserted despite a partial,
  blocked, provider-uncertain, or unverified target.

Use OD-027's approved incident command, privacy/legal, security, communications, and handoff
routes. If exposure or unauthorized readability is suspected, invoke the
[personal-data breach response](personal-data-breach-response.md) without waiting for a legal
classification. Exact notification duties, severity, regulator/provider contact, requester
language, and response timing are human decisions.

## Required Rehearsal Scenarios

Before production authorization, exercise:

- source deletion with residual embeddings, indexes, caches, objects, provider copies, replicas,
  backups, and stage-host/offline records;
- process, transaction, network, and external-call failure before and after case, manifest,
  tombstone, source action, derivative action, acknowledgement, and verification boundaries;
- duplicate identical and conflicting tombstones plus older writes/events arriving after the
  tombstone;
- broken source-to-derived linkage, unknown consumer, orphan embedding, stale index, and cache
  repopulation after deletion;
- replica lag, replica promotion, and an older replica becoming readable;
- provider timeout, indeterminate acknowledgement, late success, unavailable deletion interface,
  and provider-copy rediscovery;
- immutable backup awaiting approved expiry, backup deletion failure, and a restore older than the
  tombstone;
- restore with current tombstone state unavailable, proving quarantine remains;
- reindexing, re-embedding, cache warming, materialized-view rebuild, and object restoration from
  stale inputs;
- stage-host disconnect, deletion while offline, reconnect, tombstone-first ingest, and local
  buffer uncertainty;
- Redis loss or stale transport delivery, proving PostgreSQL/tombstone authority and no
  resurrection;
- legal hold before deletion, hold discovered mid-propagation, partial-scope hold, conflicting
  incident hold, hold release, and purpose-limited held access;
- viewer-memory deletion while audit retains only content-free case/deletion references;
- canary deletion followed by injected residual copies across each target class, proving the
  independent verifier rejects false success;
- verifier timeout, permission failure, stale read path, incomplete coverage, and deletion-worker
  false completion report;
- prohibited-content scanning of manifests, logs, traces, alerts, tickets, evidence, and requester
  communication;
- repeated idempotent execution and complete reconstruction of the minimized deletion/restore
  timeline.

Every scenario asserts quarantine-before-readability, no resurrection, explicit partial/blocked
state, and no false completion.

## OPEN Values And Decisions

Human approval is required for:

- OD-009 retention, deletion/anonymization, backup terminal behavior, restore, hold, verification,
  evidence, and measurable SLO policy by data class and jurisdiction;
- OD-032 privacy deletion/restore assurance profile, including target-manifest completeness,
  tombstone continuity, quarantine release, external-copy evidence, independent verification, and
  false-completion prevention;
- OD-027 incident command, role coverage, privacy/security/legal escalation, communications,
  exercise cadence, evidence freshness, and runbook authorization;
- OD-028 independent validation scope, adversary assumptions, review triggers, and residual-risk
  authority; no risk acceptance may waive a deletion or quarantine gate;
- requester identity verification, authorization, abuse protection, correction, export, and
  appeal workflows;
- legal/incident hold authority, scope, custody, access, review/release, notification, and
  conflict policy;
- target-manifest schema, consumer inventory, discovery mechanism, source/derived identity, and
  completeness evidence;
- tombstone schema, causal ordering, durability, retention, compaction, propagation, and continuity
  across backup/restore;
- concrete behavior for PostgreSQL, caches, Redis, embeddings, indexes, objects, replicas,
  providers, backups, exports, and stage-host/local buffers;
- provider deletion APIs, contracts, regions, acknowledgement sufficiency, late-result handling,
  and verification evidence;
- backup/snapshot topology, immutability, encryption, expiry/destruction evidence, recovery
  points, and quarantine boundary;
- independent verifier ownership, credentials, query paths, canary design, evidence freshness, and
  separation of duties;
- exact timeouts, retry/backoff, alert thresholds, deletion/restore SLOs, contacts, commands,
  endpoints, and production storage mechanisms;
- protected schema/migration ADRs and review ownership before persistence implementation.

No example, fixture, library, provider, database, cache, backup, operating-system, or deployment
default may become a production value without protected human approval.
