# ADR-017: Data Retention, Privacy, And PII

Status: Accepted

Priority: P0

Date: 2026-07-05

Source: `vnova-review-handoff.md`

## Context

VNova processes live viewer messages, platform identifiers, operator commands, generated candidates, safety decisions, audio artifacts, logs, and memory. The system must preserve auditability without turning long-lived memory into a privacy or prompt-injection risk.

APPI-aware privacy posture is required. This ADR blocks schema design.

## Decision

VNova will use explicit data classification, retention rules, and deletion behavior. Viewer memory and audit logs are separate domains with separate tables, content, access roles, and retention rules.

## Data Classification

| Class | Examples | Handling |
|---|---|---|
| Public broadcast data | final spoken content, visible captions, broadcast scene text | May be archived with session records according to archive policy. |
| Viewer identity snapshot | platform ID, display name at time of interaction | Store minimum required fields. Do not store OAuth tokens in logs. |
| Viewer message content | chat messages, moderated input | Retain according to message retention policy. Use for provenance where needed. |
| Viewer memory | typed slots such as nickname, favorite topic, milestones | Separate from audit logs. Delete on request. No free-text memory blobs. |
| Restricted generation data | raw `CandidateResponse` output, full prompts | Restricted access. Redacted by default in console. Reveal requires privileged role and logged reason. |
| Safety/audit data | safety decisions, event IDs, hashes, operator IDs, policy versions | Immutable audit retention. Must not contain viewer-memory content. |
| Derived cache | embeddings, indexes, generated lookup artifacts | Rebuildable from source records. Delete by source-record FK cascade. |
| Secrets and credentials | provider keys, OAuth tokens, signing keys | Never store in logs. Managed secrets only. |

## Retention Matrix

Exact durations are policy values and must be set by human-approved retention policy before production launch.

| Data Class | Default Posture | Deletion Behavior | Audit Compatibility |
|---|---|---|---|
| Viewer messages | Time-limited operational retention | Delete or anonymize according to request and legal requirements | Audit rows reference message IDs or hashes, not content. |
| Viewer memory | Retain until deleted, expired, or superseded | Delete source record and cascade derived embeddings | Audit logs retain deletion event without memory content. |
| Candidate responses | Restricted, time-limited retention | Delete or redact per retention policy | Audit retains candidate ID, safety decision, hashes, and metadata. |
| Approved responses | Retain with broadcast/session archive policy | Retain if part of archive unless policy requires redaction | Audit references approved response ID and safety decision. |
| Full prompts | Restricted table only, short retention unless incident hold applies | Delete per restricted-data retention policy | Ordinary logs keep prompt manifest only. |
| Prompt manifests | Operational/audit retention | Keep template version, memory IDs, token counts | Does not contain full prompt text. |
| Safety decisions | Audit retention | Immutable except legally required redaction/anonymization | Contains no viewer-memory content. |
| Embeddings | Derived cache | Cascade delete through source-record FK | Rebuildable; not audit source. |
| Stage-host local logs | Buffered until shipped, then retained per event class | Delete local copy after confirmed ingest and retention window | Shipped events use IDs and metadata. |

## APPI-Aware Privacy Posture

- Collect only data necessary for live operation, safety, audit, and viewer memory.
- Separate personal data from immutable audit evidence where possible.
- Prefer internal IDs and hashes in audit logs.
- Avoid storing PII beyond platform ID and display-name snapshot.
- Never store payment data.
- Never store secrets or platform OAuth tokens in logs.
- Provide viewer- and operator-initiated deletion paths.
- Provide a verification job that proves absence after deletion.
- Treat prompt/persona data and restricted generation data as sensitive operational records.

## Viewer Memory And Audit Separation

- Viewer memory and audit logs never share tables.
- Viewer memory and audit logs never share raw content.
- Viewer memory and audit logs never share access roles.
- Audit logs may reference memory IDs, hashes, policy versions, prompt versions, and deletion events.
- Audit logs must not embed memory content.

## Typed Viewer Memory Slots

Viewer memory is structured as typed slots. Examples:

- `nickname`
- `favorite_topic`
- `milestone`
- `preference`
- `prior_interaction_summary_id`

Forbidden viewer memory content:

- Free-text blobs.
- Authority claims.
- Self-referential instructions.
- Hidden prompt text.
- Viewer-provided instructions that attempt to affect system behavior.

Writes happen only through a post-turn extraction pipeline. Every memory record carries provenance such as `source_message_id` and `turn_id`.

Mode requirements:

- Mode 1 and below: viewer memory writes require operator approval.
- Mode 2: auto-write is limited to low-risk structured slots.
- Higher-autonomy writes require a later ADR and red-team coverage.

## Deletion Behavior

- Viewer-initiated deletion must remove viewer memory source records.
- Operator-initiated deletion must be audited.
- Deletion cascades to embeddings through source-record foreign keys.
- Ordinary logs reference memory IDs, not content.
- Deletion verification proves absence from source records and derived caches.
- Audit records retain that deletion occurred without retaining deleted memory content.

## Embedding Cascade Behavior

- Embeddings are derived cache.
- Every embedding row must reference a source record by foreign key.
- Deleting a source record cascades to derived embeddings.
- Embedding rows include `embedding_model` and `version`.
- Re-embedding after model changes is lazy and rebuildable.
- pgvector is used for Knowledge Base only in MVP; viewer and character memory use scoped key lookup.

## PII Scrubbing Before Memory Writes

- PII scrubbing occurs before memory extraction writes.
- Scrubbing includes control-character stripping, normalization, platform-token removal, and detector-based PII checks.
- Memory writes that contain unresolved PII risk go to manual review or are discarded.

## Restricted Generation Data

- Raw `CandidateResponse` outputs are restricted.
- Full prompts are restricted.
- Raw candidates are redacted by default in the operator console.
- Reveal of raw candidates or full prompts requires privileged role and logged reason.
- Ordinary logs store prompt manifests: template version, memory IDs, token counts, provider profile, and policy version.

## Consequences

- Schema work is blocked until memory, audit, and restricted-data storage are separated.
- Privacy deletion can coexist with immutable audit because audit logs do not store viewer-memory content.
- Memory cannot be modeled as free-form chatbot history.
