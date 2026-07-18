# ADR-026: Opaque Audit References For Deletable Personal Data

Status: Proposed

Priority: P0

Date: 2026-07-18

Sources:

- `AGENTS.md`
- ADR-017
- `docs/architecture/privacy-retention-model.md`

Acceptance prerequisites:

- Protected privacy, security, data, and architecture-owner review.
- A closure-capable disposition for OD-009 covering the affected retention classes.
- Legal/privacy review of the target deployment's deletion and audit obligations.

Atomic review cohort:

- ADR-017's viewer-memory/audit separation clauses.
- The privacy and retention model's audit-reference rules.
- The exact data inventory and access-role design for any first persistence migration.

Implementation gates:

- No persistence schema, migration, audit serializer, deletion workflow, or resolver may implement
  this proposal before acceptance and a linked migration ADR.

## Context

ADR-017 correctly separates viewer memory and audit logs by table, content, access role, and
retention. It also permits audit rows to reference message or memory hashes. Low-entropy personal
values such as nicknames, favorite topics, or short messages can be recovered by hashing a small
dictionary and comparing results. Salting does not solve that problem when the salt is stored with
the immutable audit record, and a long-lived keyed digest remains personal-data linkage while its
resolver key exists.

An ordinary audit record therefore cannot treat a digest as privacy-safe merely because it is not
the original string. The audit trail needs stable evidence of what operation occurred without
becoming a durable semantic copy of deletable personal content.

## Decision

If accepted, this ADR supersedes only ADR-017 language that permits an unqualified hash of viewer
messages or viewer-memory values in ordinary audit. All other ADR-017 separation, minimization,
retention, deletion, and access-control requirements remain binding.

For deletable viewer messages, viewer memory, and equivalent low-entropy personal content:

- ordinary audit references use a cryptographically random, content-independent record ID created
  before or atomically with the source record;
- audit, source, and deletion-case records may share that opaque ID only through separately
  authorized roles; ordinary audit readers receive no content resolver;
- raw, normalized, truncated, salted, or unsalted content hashes are forbidden in audit,
  telemetry, logs, traces, metrics, events, idempotency keys, and deletion receipts;
- a keyed or domain-separated content digest is also forbidden as an ordinary audit reference;
- integrity digests remain permitted only for non-personal immutable artifacts whose exact bytes
  are intentionally retained under their own accepted policy, never as a substitute for deleted
  viewer content;
- deletion evidence records the opaque target ID, deletion-case ID, policy/legal basis, component
  outcomes, and verification result without preserving a content-derived verifier;
- a privileged linkage service, if a later accepted ADR requires one, uses a separate data store,
  key/access domain, purpose, retention limit, access audit, and crypto-erasure behavior. It is not
  an audit-table column or a default join path;
- unknown reference provenance, data class, or resolver authority fails closed and blocks the
  write.

This decision does not choose retention durations, legal bases, pseudonymization keys, or resolver
availability. Those remain protected human decisions and cannot be encoded as defaults.

## Enforcement And Verification

Before any affected persistence is accepted:

- the data inventory classifies every identifier and digest by source, derivation, entropy,
  purpose, resolver, reader role, retention, deletion, backup, and export behavior;
- schema and serializer tests reject content-derived viewer message/memory hash fields, including
  aliases and generic metadata maps;
- role tests prove audit readers cannot resolve opaque IDs to viewer-memory content;
- deletion canaries prove source, cache, index, backup-reconciliation, and resolver removal without
  relying on a retained content digest;
- observability and export scanners reject prohibited content and content-derived references;
- migration review links an accepted ADR and proves memory, audit, resolver, and restricted-content
  storage remain physically and logically separated.

## Failure Behavior

- Missing classification or provenance denies the audit/source write rather than hashing content
  as a fallback.
- Audit unavailability blocks an operation whose policy requires audit; it never widens logging.
- Resolver uncertainty does not make content available and does not report deletion complete.
- Restore and replay apply deletion tombstones before any opaque-ID resolver becomes available.

## Consequences

- Dictionary recovery from immutable low-entropy audit hashes is removed from the ordinary design.
- Incident correlation uses stable opaque operation/record IDs and explicit authorized evidence
  paths instead of semantic fingerprints.
- Some forensic comparisons become deliberately unavailable after deletion or crypto-erasure.
- Schema realization remains blocked until this proposal, its OPEN policy values, and a linked
  migration ADR receive protected human approval.

## OPEN Decisions

- Exact retention and deletion SLA by affected class: OD-009.
- Whether any target deployment needs a privileged linkage service at all.
- Key custody, rotation, crypto-erasure, and disaster-recovery rules if such a service is approved.
- Jurisdiction-specific legal basis and evidence obligations.
