# Production Quality Attributes

Status: Proposed normative architecture target; non-authorizing until recorded foundation review

This document defines the quality bar requested for protected human review. It does not accept an
ADR, close an OPEN decision, or authorize implementation by describing a requirement.

VNova's first release is a production baseline, not a disposable MVP. Scope can be reduced; quality attributes cannot be waived silently.

## Priority Order

When requirements conflict, VNova optimizes in this order:

1. Human and broadcast safety.
2. Authorization, privacy, and audit integrity.
3. Correctness and deterministic recovery.
4. Availability with fail-closed degradation.
5. Latency and audience experience.
6. Cost efficiency.

Low latency never authorizes bypassing safety. Availability never authorizes unverifiable speech.

## Required Attributes

### Safety

- Unsafe and approved response types are structurally distinct.
- Every broadcast surface is moderated.
- Local hard e-stop works without cloud connectivity.
- All primary, retry, rewrite, and fallback paths pass through the same gate.

### Security

- Trust boundaries use authenticated, least-privilege identities.
- Secrets are managed externally and never enter logs or images.
- Speech tasks are signed, session-bound, time-bounded, integrity-bound, and replay-resistant.
- Operator actions are authorized server-side and audited.
- The [threat model](../security/threat-model.md) covers every enabled composed path, and an
  accountable human owns each accepted residual risk.
- Reviewed source, locked dependencies, deterministic generation, release artifacts, deployment,
  updates, and observed targets have one verifiable provenance chain.

### Reliability

- PostgreSQL is the recoverable system of record.
- State mutation and event publication use a transactional outbox.
- Redis Streams is replaceable transport, not recovery truth.
- One logical session actor is enforced by the exact protected recovery/PostgreSQL-ownership
  composite fence, shared ownership-row linearization, and recovery-only takeover/barrier.
  Process, heartbeat, aggregate version, session epoch, read predicate, and Redis lock do not
  substitute.
- One monotonic normal-work admission epoch gates every command, durable input, timer, Turn,
  candidate, selection, approval, media, task, ordinary effect, signing, and dispatch
  creation/advancement.
  Begin-close fixes a committed prefix, freezes recurring cursors, permits only bounded evidence/
  restrictive/terminal non-advancing writes, drains boundedly, and atomically closes
  session/admission/ownership without reopening. PITR-restored `open` becomes
  `Ending`/`draining(lost_tail_quarantine)`, restored `draining(normal_closure)` gains a monotonic
  lost-tail overlay, and restored atomic `closed` stays closed.
- Command acceptance binds submission recovery generation and requires a durable receipt;
  the protected idempotency-key scope returns the same digest's lineage and conflicts on a
  different digest; append-only authorization observations dedupe refresh, CAS a lineage
  revision, and use deterministic fail-closed precedence; outcomes are idempotent/queryable under
  current disclosure authorization, deadline expiry is final, and transport timeout/lost-tail
  absence remains unknown. Ordinary effects separate intent, send-authorization, response
  observation, and fenced application under the exact active/open source CAS.
- A session-bound recovery query uses a distinct, non-relabelable four-role `RecoveryProbe*`
  lineage under an exact active-plus-draining-prefix or recovering-plus-recovery-attempt/source
  binding. It is finite, read-only/restrictive, never widens or authorizes replay, permits
  zero-attempt terminalization and current-successor terminalization without resend. Every
  admitted probe is terminal before final close; a terminal `unknown` probe remains separate from
  the bound source ambiguity that closure must resolve, permanently safe-quarantine, or
  accountably dispose.
- Canonical trigger occurrence/materialization cursor and current claim token permit at most one
  turn admission and terminal firing disposition. Materialization requires the current active
  owner; a recovering owner cannot create occurrences or advance cursors, catch-up is bounded,
  and process-memory timers cannot hold authority.
- Recovery activation compares immutable cut-time source frontiers and schedule-cursor snapshots,
  not the separately advancing harmless post-cut operational cursor. Every
  recovery-attempt-bound probe write advances invalidation; activation requires all such probes
  terminal/non-widening and each enabled-scope source ambiguity resolved or explicitly
  capability-disabled.
- Administrative revoke installs a restrictive epoch/hold/control intent and remains audience
  unknown until exact stage-host acknowledgement; no active actor is needed to drain only that
  restrictive control.
- Domain-event consumers are idempotent and follow catalog-declared typed
  scope/subject/aggregate-version ordering; cross-lane reorder is explicit. The non-event
  stage-host speech/control path has an independent session-bound sequence/epoch contract.
- Disaster recovery and failback preserve one writer/actor authority, newer restrictive state,
  deletion tombstones, rights revocations, and old-work invalidation before availability.
- Every queue and resource has explicit item/byte/age bounds, and independent reserves protect
  e-stop, restrictive control, safety evaluation, heartbeat, and current playout.
- Admission reserves the required downstream safety capacity before speculative generation or
  fails closed; retry, fallback, and billing uncertainty cannot consume unbounded capacity.

### Operability

- Every external call has a timeout and documented failure behavior.
- Every live incident can be reconstructed from correlated runtime, operator, and stage-host records.
- Rehearsal mode supports deterministic clocks and fault injection.
- Raw UTC observations, local monotonic durations, clock-offset samples, uncertainty, age, and
  derived timelines remain distinct; a corrected view never rewrites source evidence or extends a
  deadline.
- Domain/audit evidence, telemetry, and alerts have explicit authority. Missing or stale
  monitoring is `unknown`, invokes a restrictive mode ceiling, and has its own runbook.
- Alerts and applicable [runbooks](../runbooks/README.md) are rehearsed, target-validated, and
  deployment-authorized before a failure mode can be enabled in production.

### Privacy

- Viewer memory and audit data have separate content, storage, and access roles.
- Data carries classification, retention, provenance, and deletion behavior.
- Derived caches are rebuildable and cascade from source-record deletion.
- Restores and rebuilds remain quarantined until tombstone/hold reconciliation and independent
  absence verification pass.
- Suspected personal-data exposure has an accountable containment, evidence, assessment,
  notification-decision, communications, and closure workflow.
- Metrics, traces, logs, profiles, dashboards, and alert payloads use versioned attribute
  allowlists, bounded cardinality/buffers, classification, retention, access, region, deletion,
  and export policy; sampling never replaces authoritative audit.

### Maintainability

- Contracts are generated from one canonical source and tested across languages.
- Architecture boundaries are enforced in CI, not left as review folklore.
- Provider SDKs and vendor behavior remain isolated behind gateways.
- Changes to irreversible boundaries require ADRs.
- Stable identities, immutable versions, scoped activation, lineage, terminal state, and
  supersession are explicit for configuration and durable domain records.
- Compatible configuration sets activate atomically with monotonic scoped epochs and exact
  resolved snapshots; restrictive state, health, rights, and publication authority remain
  independent.

## Definition Of Production-Ready

A capability is production-ready only when its contract, authorization, timeout behavior,
failure mode, observability, tests, threat-model validation, runbook, rollback or disable path,
and human review requirements are complete. Its
[operational readiness record](../governance/operational-readiness-review.md) must name the exact
capability and deployment. Representative load/stress/spike/soak/chaos/recovery evidence must
satisfy the [acceptance contract](../governance/load-soak-chaos-acceptance.md) without violating a
zero-tolerance safety, rights, privacy, authorization, or audit invariant. A demo that works on the
happy path does not meet this definition.
