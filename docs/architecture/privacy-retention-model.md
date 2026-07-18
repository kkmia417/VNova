# Privacy And Retention Model

Status: Accepted ADR-017 structural baseline with Proposed elaboration; durations, legal
classifications, and deletion SLOs remain OPEN

Governing decision:
[ADR-017](../adr/0017-data-retention-privacy-and-pii.md)

Proposed review companions:
[ADR-024](../adr/0024-versioned-configuration-and-scoped-activation.md) and the
[domain record lifecycle catalog](domain-record-lifecycle-catalog.md). The P0 corrective proposal
[ADR-026](../adr/0026-opaque-audit-references-for-deletable-personal-data.md) would forbid
content-derived viewer message/memory hashes in ordinary audit if accepted. These proposals do
not change ADR-017 or authorize a schema before protected acceptance.

Only the constraints established by Accepted ADR-017 and `AGENTS.md` are binding through this
document. In particular, viewer memory and audit evidence remain separate in tables, content, and
access roles. `ApprovedContentSnapshot`, configuration/lifecycle elaborations inherited from
Proposed ADR-024, semantic-copy/archive handling, and the detailed validation workflows below are
Proposed until their own governing ADR, Open Decision, migration, and protected human review are
complete. If an elaboration conflicts with ADR-017, ADR-017 controls. Nothing in this document
silently revises ADR-017 or authorizes a schema, storage layout, role, retention value, or runtime
behavior.

VNova minimizes data while preserving the evidence needed to operate and investigate a live
broadcast. Viewer memory and audit evidence are separate domains: they never share tables, raw
content, or access roles.

## Data Domains

| Domain                       | Content posture                                                                                         | Access posture                                                  |
| ---------------------------- | ------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| Viewer input                 | Minimum platform identity snapshot and time-limited moderated message content                           | Runtime/moderation roles; no provider or OAuth secrets          |
| Typed viewer memory          | Enumerated low-risk slots with source provenance; no free-text instruction or authority claim           | Purpose-limited memory roles; separate from audit               |
| Restricted generation        | Raw candidates and full prompts; short, explicit retention; redacted in ordinary console views          | Privileged reveal only with logged reason                       |
| Approval and policy evidence | Decision IDs, hashes, categories, versions, actor, timing, and outcome                                  | Safety/audit roles; no viewer-memory content                    |
| Approved-content snapshot    | Exact immutable content owned by the approval boundary, independently available/held/deleted            | Restricted content-resolution roles; not ordinary audit/archive |
| Broadcast archive            | Approved public output and aligned session/turn IDs, subject to archive, talent, and rights policy      | Production/archive roles                                        |
| Voice and rights evidence    | Restricted consent/license records and voice data referenced by IDs/hashes in ordinary operational data | Separate legal/talent/privacy roles under Proposed ADR-022      |
| Derived cache                | Embeddings and indexes rebuildable from named source records                                            | Same or narrower purpose than the source; never authoritative   |
| Stage-host offline journal   | Bounded operational IDs, sequences, outcomes, and health metadata                                       | Local protected buffer until acknowledged ingest                |
| Secrets and credentials      | Managed only in the approved secret boundary                                                            | Never in logs, prompts, events, artifacts, or memory            |

The final legal classification of voice, identity, consent, platform, and recording data is a
human privacy/legal decision. The table is a technical separation model, not a legal conclusion.
Approval metadata, the restricted approved-content snapshot, rendered media, playout observation,
and public archive remain different records with independent access, retention, deletion, and
use eligibility. Archive or media is never an authoritative source for rehydrating or minting an
`ApprovedResponse` and never substitutes for the canonical `ApprovedContentSnapshot`. Audio,
captions, or another semantic copy that discloses equivalent linguistic content remains
separately inventoried and governed by its own retention, deletion, hold, rights, and publication
basis.

## Collection And Purpose

Every stored field has an owner, data class, declared purpose, source, permitted consumers,
retention policy ID, deletion behavior, and export/logging rule. An unknown classification or
purpose prevents production persistence.

Operational events and authorized trace/log evidence may contain approved stable references,
privacy-safe integrity references, versions, timings, and outcomes. Metric labels use bounded
dimensions and never per-record identities. Alerts carry only the minimized fields in their
versioned signal data contract. None becomes a second copy of viewer messages, memory values,
prompts, raw candidates, consent evidence, contracts, credentials, or synthesized media.

Opaque IDs and digests can remain linkable. A raw or low-entropy hash is not automatically a
privacy-safe reference. Pending ADR-026 review, no implementation may treat a content-derived
viewer message/memory hash as privacy-safe foundation evidence. The proposed safe direction is a
cryptographically random, content-independent opaque record ID; any privileged resolver remains
a separately reviewed data, key, access, retention, and deletion domain.

Provider requests disclose only data required for that reviewed capability and profile. Vendor,
region, processing, model-training, logging, and deletion terms require protected privacy review
before activation.

## Viewer Memory

Viewer memory is a typed source record, not chat history. Each value carries viewer/character
scope, slot type, normalized value, source message/turn IDs, creation actor or extractor version,
policy version, confidence/review state, expiry where applicable, and supersession lineage.

- Mode 1 and below require operator approval for writes.
- Mode 2 may write only a human-approved low-risk slot allowlist.
- Retrieval is scoped to viewer and character, token-budgeted, and injected as untrusted delimited
  data.
- Prompt manifests record memory IDs, not values.
- Authority claims, self-referential instructions, hidden prompts, secrets, and unresolved PII are
  never memory values.

## Source And Derived Data

Every derived record references its authoritative source. Embeddings include model/version and are
rebuildable; source deletion cascades to them. Reindexing, cache repopulation, backup restoration,
offline-observation ingest, and domain-event replay must honor tombstones and cannot resurrect
deleted source content.

PostgreSQL is the system of record for durable operational state. Redis is transport/cache only.
Object storage holds governed immutable artifacts but does not decide approval, rights,
authorization, or retention.

## Retention Policy

Retention is versioned policy by data class and purpose. Exact durations remain OPEN under OD-009
and cannot appear as database defaults, fixture-derived production values, or undocumented vendor
settings.

An accepted policy defines at least:

- active retention, archive transition, deletion/anonymization, and backup-expiry periods;
- event/outbox, object, cache, search index, replica, stage-host buffer, and provider-copy behavior;
- incident hold and legal-hold authority, scope, review, and release;
- deletion and export request identity verification, authorization, and abuse protection;
- regional/residency requirements and cross-border provider constraints;
- evidence retained after deletion without retaining the deleted content;
- measurable deletion and verification SLOs.

## Deletion Workflow

```text
authenticated request
  -> scope and authority review
  -> durable deletion case and target manifest
  -> source deletion / approved anonymization
  -> derived-cache and artifact propagation
  -> provider and stage-host propagation where applicable
  -> independent absence verification
  -> minimized audit completion record
```

The deletion case is idempotent and records target IDs, policy/legal basis, requester and approver,
hold conflicts, component outcomes, retries, verification, and completion state without copying
the deleted values.

Deletion is not reported complete until every in-scope authoritative source and derived consumer
has confirmed the accepted terminal outcome. Missing components, backups awaiting approved expiry,
provider uncertainty, or a lawful hold remain explicit partial states rather than false success.

## Audit Compatibility

Immutable auditability and deletion coexist through separation:

- audit references deleted records by opaque ID, digest, version, decision, and timing;
- audit never embeds viewer-memory content;
- ordinary audit does not copy raw viewer input, prompt, candidate, rights evidence, or secrets;
- legally required correction or anonymization preserves a traceable operation without silently
  rewriting history;
- access to restricted content is itself audited with actor, purpose, case, and outcome.

## Failure Behavior

- Unknown classification, purpose, retention policy, access role, or deletion behavior blocks new
  production storage.
- A failed PII scrub denies or routes the memory write to the approved manual path.
- Deletion propagation failure retries with explicit timeouts and alerts; it does not mark the case
  complete.
- A broken source relationship blocks derived-cache use and rebuild.
- Provider or evidence-store timeout fails closed for the affected operation and does not expose
  a broader dataset.
- Missing, held-against-use, deleted, corrupt, mismatched, or expired approved content blocks new
  synthesis, replay, export, and publication; archive/media is not a recovery source.
- Backup restore, offline-observation ingest, and domain-event replay apply deletion/tombstone
  reconciliation before making restored data available.
- Audit unavailability blocks actions whose policy requires an audit record; it never causes
  memory content to be written into a fallback log.

## Acceptance Evidence

Before production persistence:

- a data inventory maps every field, event, log, metric, trace, artifact, cache, backup, provider,
  and stage-host record to class, purpose, owner, access role, retention, and deletion behavior;
- migration review proves physical and role separation between memory, audit, and restricted data;
- lifecycle/schema review separates semantic terminality, content availability, retention/hold,
  use eligibility, publication, and delivery state and traces every implemented catalog row;
- access-control tests cover every positive and negative role and privileged reveal reason;
- canary records prove deletion across source, embeddings, indexes, caches, objects, replicas,
  providers, offline buffers, and restore paths;
- ordinary observability is scanned for prohibited content and credentials;
- [privacy deletion and restore](../runbooks/privacy-deletion-and-restore-reconciliation.md),
  [personal-data breach](../runbooks/personal-data-breach-response.md), and
  [disaster recovery](../runbooks/disaster-recovery-and-continuity.md) procedures cover
  backup/restore, incident/legal hold, export, correction, and partial failure and are rehearsed;
- privacy/legal owners approve durations, SLOs, jurisdictions, provider handling, and evidence;
- applicable protected schemas and migrations cite an accepted ADR.

Official guidance from Japan's
[Personal Information Protection Commission](https://www.ppc.go.jp/personalinfo/legal/guidelines_tsusoku/)
is a review input. It does not replace VNova-specific legal advice or accountable human approval.
