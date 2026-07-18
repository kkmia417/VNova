# Domain Record Lifecycle Catalog

Status: Proposed architecture reference; no schema, migration, storage, retention, role,
configuration, content, event, runtime, or production authority

Governing sources:

- [`AGENTS.md`](../../AGENTS.md)
- [Domain information model](domain-information-model.md)
- [Scope and subject identity model](scope-and-subject-identity-model.md)
- [ADR-002: contract source and code generation](../adr/0002-contract-source-and-code-generation.md)
- [ADR-003: stream-session, segment, and turn lifecycle](../adr/0003-stream-session-segment-and-turn-lifecycle.md)
- [ADR-004: PostgreSQL outbox and Redis Streams](../adr/0004-postgresql-outbox-and-redis-streams.md)
- [ADR-008: safety gate enforcement](../adr/0008-safety-gate-enforcement.md)
- [ADR-010: approved media and TTS pipeline](../adr/0010-approved-media-and-tts-pipeline.md)
- [ADR-017: data retention, privacy, and PII](../adr/0017-data-retention-privacy-and-pii.md)
- [ADR-019: authentication, authorization, and operator roles](../adr/0019-authentication-authorization-and-operator-roles.md)
- [ADR-021: broadcast surfaces and overlay policy](../adr/0021-broadcast-surface-inventory-and-overlay-policy.md)
- [ADR-022: voice rights and talent licensing metadata](../adr/0022-voice-rights-and-talent-licensing-metadata.md)
- [ADR-023: event subject, scope, correlation, and ordering lanes](../adr/0023-event-subject-scope-correlation-and-ordering.md)
- [ADR-024: versioned configuration and scoped activation](../adr/0024-versioned-configuration-and-scoped-activation.md)

This catalog is the review inventory required before physical data design. It names conceptual
records and invariants, not tables, columns, object buckets, indexes, foreign keys, schemas,
serialized enums, retention durations, database products beyond accepted architecture, or
access-role assignments. Any realization requires accepted upstream decisions, a valid OD-034
disposition for the exact scope, and a linked migration ADR.

## Catalog Purpose

A single `status` field cannot safely represent whether:

- a decision is semantically terminal;
- restricted content is present, held, redacted, deleted, or corrupt;
- a legal hold prevents physical erasure;
- a definition is eligible for new use;
- an artifact may be replayed or published;
- an outbox event was delivered.

Those facts have different authorities, transitions, and retention. Combining them allows a
delivery retry to reopen a decision, an archive flag to imply safety approval, a legal hold to
make content usable, or a restored backup to reactivate deleted data.

This catalog therefore separates record families, content, evidence, authorization, observation,
and delivery state.

## Mandatory Orthogonal State Axes

Every physical design must declare which axes apply and store them under separate authorities.
Names below are conceptual vocabularies, not authorized enums.

| Axis                                 | Purpose                                                       | Example states or outcomes                                                             | Non-substitution rule                                                                   |
| ------------------------------------ | ------------------------------------------------------------- | -------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Semantic lifecycle                   | Domain meaning and terminality                                | draft, admitted, running, completed, failed, cancelled, expired, decided, revoked      | Delivery, deletion, and publication state cannot reopen a terminal domain decision      |
| Content availability                 | Whether protected bytes can be resolved                       | available, held, redacted, deleted/tombstoned, quarantined, corrupt/missing            | Metadata existence does not prove content exists or may be used                         |
| Retention and legal disposition      | Preservation/erasure obligation                               | policy-active, deletion-due, hold-active, deletion-confirmed, correction-required      | Hold preserves evidence; it does not grant retrieval, synthesis, or publication         |
| Activation/use/retrieval eligibility | Whether new work may select the record                        | eligible, suspended, expired, withdrawn, revoked, incompatible, blocked                | Eligibility does not mint content, rights, surface, or operator authorization           |
| Publication/distribution disposition | Whether a reviewed artifact may reach an audience/destination | private, review-pending, authorized, published, withdrawn, takedown-pending, retracted | Live playout or stored media does not imply archive, clip, replay, or export permission |
| Outbox/delivery processing           | Transport attempt and consumer progress                       | pending, claimed, attempted, acknowledged, retryable, poisoned, replayed               | Delivery state is separate from the immutable domain event and source transaction       |

No axis may use a generic unknown state that permits work. Unknown, missing, conflicted, or
unverifiable state is restrictive for new use.

## Required Record Profile

Before a conceptual row below becomes a schema, its migration ADR and field inventory must state:

1. authoritative owner and sole writer;
2. stable root, version, record, environment, and typed scope identities;
3. authoritative versus derived, content versus metadata, and decision versus observation;
4. immutable and mutable fields with the concurrency/epoch authority for each;
5. creation preconditions and atomic transaction companions;
6. every legal semantic transition, terminal state, and no-reopen rule;
7. activation, retrieval, replay, fallback, export, and publication eligibility;
8. supersession, rollback, revocation, expiry, and stale-epoch behavior;
9. field-level classification and prohibited content;
10. read, write, review, authorize, delete, hold, restore, and disclose capabilities;
11. retention policy reference, legal-hold precedence, erasure/tombstone behavior, and backups;
12. derived-data cascade, quarantine, cache invalidation, and reconstruction authority;
13. minimized audit and outbox evidence;
14. restore and incident-reconstruction source of truth;
15. uniqueness, cardinality, referential, digest, idempotency, and transaction constraints;
16. governing accepted ADRs and closure-capable Open Decision dispositions.

A migration that cannot trace every field and transition to this profile is incomplete.

## Cross-Cutting Cardinality And Lineage

The conceptual minimum relationships are:

```text
StreamSession
  1 -> 0..N SegmentVersion usages
  1 -> 0..N Turn

Turn
  1 -> 0..N GenerationAttempt over its lifetime

GenerationAttempt
  N -> 1 Turn
  1 -> 0..1 CandidateResponse

CandidateResponse
  1 -> 0..1 terminal SafetyDecision

SafetyDecision(decision = approved) + selected same-turn CandidateResponse
  1 -> 0..1 ApprovedResponseRecord

ApprovedResponseRecord
  1 -> exactly 1 restricted ApprovedContentSnapshot
  1 -> 0..N independent rights/surface/synthesis/dispatch/use decisions
```

A turn may terminate before generation admission and therefore own no attempt. Every attempt
belongs to exactly one turn. An attempt that times out, fails, is cancelled, returns
malformed/partial output, or never completes creates no candidate. A retry, rewrite, fallback, or
second complete output creates a new attempt and candidate. A candidate has at most one terminal
safety decision. Only a literal approved decision for the selected same-turn candidate can back
one approval. Every minted approval creates exactly one restricted approved-content snapshot in
the same safety transaction; an orphan snapshot is forbidden.

Approval metadata, restricted approved content, rendered media, actual playout observation, and
public archive/publication records are separate. No downstream record is an authoritative source
for rehydrating, widening, or minting an upstream authorization.

## Identity And Configuration Records

| Record family                                         | Authority and identity/scope                                                                                                          | Mutability and semantic lifecycle                                                                                                    | Data, access, retention, and use rule                                                                                   | Governing gates                             |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| `Environment`                                         | Repository/operations-governed root; one stable VNova ID                                                                              | Immutable identity; attributes change through audited versions; retirement never reuses ID                                           | Contains references, not secrets; cross-environment transfer is explicit; retention/access OPEN                         | ADR-019/024; OD-022/034                     |
| `Talent`                                              | Protected talent/rights domain; stable environment-contained ID                                                                       | Corrections/versioned relationships; merge/split/deactivation protected                                                              | Identity and evidence restricted; character/voice/provider records do not establish talent identity or consent          | ADR-017/019/022; OD-024/034                 |
| `Character`                                           | Protected product/talent domain; stable ID distinct from talent/persona version                                                       | Versioned relationships; retirement does not rewrite historical sessions                                                             | Labels and persona content separated; no inferred talent, voice, rights, or viewer relationship                         | ADR-017/019/024; OD-022/034                 |
| `Viewer` and `PlatformIdentity`                       | Purpose-specific privacy boundary; internal ID plus qualified external mappings                                                       | Link/merge/split/correction/deletion workflows separate; no automatic cross-platform merge                                           | Highly linkable/restricted; audit stores opaque refs only; exact legal basis, access, and retention OPEN                | ADR-017; OD-009/026/034                     |
| Operator principal and presence binding               | Identity/presence authority; stable principal plus exact environment/session lease generation                                         | Principal lifecycle and current presence/lease are separate; expiry/revocation restrictive                                           | No IdP token in domain/event/audit; presence is not broad authorization; workload/rig/human identities non-convertible  | ADR-019/020; OD-022/034/035                 |
| Rig enrollment, boot, connection, and session binding | Stage-host trust/control boundary; distinct stable rig, key enrollment, boot, connection, and versioned session-binding IDs           | Enrollment/revocation, boot incarnation, connection terminality, and session binding have separate state/epochs                      | Hostname/IP/label is not identity; connection is not trust; local/cloud evidence minimized and reconciled               | ADR-011/015/016/017; OD-005/010/011/015/034 |
| Definition root                                       | Protected configuration boundary; stable family-typed ID                                                                              | Identity immutable; retirement/supersession separate                                                                                 | No raw secret/content in ordinary metadata; not selectable without eligible exact version                               | ADR-024; OD-034                             |
| `DefinitionDraft` and draft revision                  | Non-selectable authoring boundary under one definition root; stable draft ID plus CAS revision                                        | Editing/abandon/publish explicit; publish creates a new version; draft never becomes the version                                     | Protected content and authoring access are family-specific; review/activation never binds a mutable draft               | ADR-017/019/024; OD-022/034                 |
| `DefinitionVersion`                                   | Same family owner; immutable version ID/digest/source-draft revision/creation provenance                                              | Semantic content immutable from creation; every correction creates another version                                                   | Persona/prompt/policy/provider/voice/surface content has family-specific protected access and retention                 | ADR-007/017/021/022/024; OD-023/024/034     |
| `DefinitionVersionEligibility`                        | Protected review/lifecycle authority; one current state and monotonic epoch per exact version                                         | Immutable transitions; under-review/eligible/deprecated/withdrawn/expired/superseded profile; never edits version                    | Review binds exact ID/digest; restrictive state invalidates use under family rules; minimized evidence only             | ADR-004/017/019/024; OD-022/034/035         |
| `ActivationSetVersion`                                | Protected configuration bundle boundary; stable root plus immutable bundle version/digest/member digests                              | Immutable from creation; eligibility/supersession separate; no partial activation                                                    | Exact IDs/digests only; no `latest`, wildcard, secret, raw prompt, or provider response                                 | ADR-024; OD-034                             |
| `ActivationSetEligibility`                            | Protected bundle review/lifecycle authority; one current state and monotonic epoch per exact set                                      | Immutable transitions; member eligibility never edits set; restrictive change propagates under family rules                          | Review binds exact set/member digests; unknown or stale epoch denies use                                                | ADR-004/017/019/024; OD-022/034/035         |
| `ActivationBinding` and current state                 | Sole activation authority; environment + typed target + family; inactive/active state and monotonic activation epoch                  | Closed initialize/activate/replace/deactivate/rollback transitions; stale epoch rejected; row/history never silently deleted         | Active names exact eligible set; inactive/missing behavior family-explicit; fallback widening needs protected review    | ADR-019/023/024; OD-022/033/034             |
| `ActivationTransition`                                | Activation transaction; immutable transition ID tied to binding and previous/result state/epoch                                       | Append-only evidence; deactivation advances epoch; rollback is a new forward transition                                              | Minimized actor/reason/review/outbox refs; no definition or content body                                                | ADR-004/023/024; OD-033/034                 |
| `ActivationSchedule` and schedule state               | Immutable non-effective intent plus separate monotonic state/epoch; exact target/operation and expected activation/eligibility epochs | Closed scheduled/cancelled/expired/superseded/executed/failed transitions; due activation and executed disposition commit atomically | Active-producing operations require one exact set; initialize/deactivate prohibit one; stale prerequisite fails closed  | ADR-004/019/023/024; OD-022/033/034/035     |
| `ResolvedConfigurationSnapshot`                       | Deterministic resolver; immutable snapshot ID/digest for exact work scope                                                             | Created once; never edited; pins activation and eligibility epochs, while current restrictive state can invalidate further use       | Exact versions/epochs only; restricted content stays in its store; snapshot is not authority against later restriction  | ADR-003/008/017/024; OD-034/035             |
| Capability restriction/emergency state                | Accepted safety/e-stop/restriction authority; typed target and independent monotonic epoch                                            | Restrictive transition immediate; no automatic reset; re-enable is new reviewed epoch                                                | Deny dominates activation; minimized evidence; process-local `uncommitted_restrictive` requires durable reconciliation  | ADR-004/008/015/020/024; OD-013/015/034     |
| Provider health/circuit/quota observation             | Provider gateway/operations owner; provider/profile/failure-domain scope                                                              | Ephemeral observations and durable transition evidence separate; never edits definition                                              | No credentials/raw provider payload; may restrict eligibility, never widen fallback                                     | ADR-007/017/024; OD-007/034/036/037/038     |
| Budget ledger, reservation, and cost/quota decision   | Accountable budget/admission boundary; exact environment/resource/provider/currency-or-usage-unit scope                               | Ledger entries append; current balance/reservation derived under one authority; warnings/denials/overrides are separate decisions    | Estimates and provider billing observations never become authority silently; no personal/content data in cost telemetry | ADR-004/007/019/024; OD-022/034/037/038     |

No generic definition table may erase family-specific classification, review, compatibility, or
composition rules. Shared physical infrastructure, if later approved, does not imply shared
content access or one lifecycle.

## Session, Generation, And Safety Records

Every session-owned authority- or domain-advancing creation/progression in this section inherits
ADR-025's exact active composite actor fence, shared ownership-row conflict, post-conflict lease
check, exact open normal-work admission/source conflict, aggregate/version preconditions, and
fixed lock order. Once admission is non-open, only bounded evidence, restrictive action, and
terminal non-advancing disposition may commit through the exact draining-prefix rules. Late
observations or restricted content may be retained under their specific evidence rules, but a
stale/recovering owner cannot use them to advance a turn, mint approval, synthesize, sign, or
dispatch. The `packages/safety`-only mint rule remains independently mandatory.

| Record family                                                                                                     | Authority and identity/cardinality                                                                                                                                                                                                                                                                                                        | Mutability and terminality                                                                                                                                                                                                                                                                                                                                                                           | Data, access, retention, and use rule                                                                                                                                                                                                                                                                                                                                                                                    | Governing gates                                         |
| ----------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------- |
| `StreamSession`                                                                                                   | Stable session ID and current aggregate revision/authorization epoch; operation-specific exact current fence: active for ordinary progression/begin-close, active or recovering for closure drain/final-close, and recovering for recovery-only quarantine; neither phase widens once admission is non-open                               | Explicit planned/active/degraded/ending axes; ended/cancelled/failed are terminal, never reopen, and commit only with admission/ownership in ADR-025 atomic final close                                                                                                                                                                                                                              | References exact config/rig/mode; no raw content in ordinary state; recovery from PostgreSQL                                                                                                                                                                                                                                                                                                                             | ADR-003/004/016/020/025; OD-012/013/014/034             |
| `SessionOwnership`                                                                                                | PostgreSQL authority; one environment/session record with exact protected recovery generation, process incarnation, and ownership generation                                                                                                                                                                                              | Closed vacant/recovering/active/closed phases; lease expiry removes authority; ownership generation is monotonic only within one recovery generation                                                                                                                                                                                                                                                 | No raw content/token; process identity is not permission; composite actor fence is separate from aggregate, session, rig, and presence epochs                                                                                                                                                                                                                                                                            | ADR-003/004/025; OD-014/029/034/035                     |
| `SessionOwnershipTransition`                                                                                      | Shared ownership-row linearization transaction; immutable cause, expected/result composite fence/revision, process, post-lock clock/lease proof, and recovery disposition                                                                                                                                                                 | Append-only acquire/renew/activate/relinquish/revoke/takeover/close evidence; failed/unknown transition grants no authority                                                                                                                                                                                                                                                                          | Minimized operational/security evidence; no command body, provider body, prompt, candidate, media, or secret                                                                                                                                                                                                                                                                                                             | ADR-004/017/019/025; OD-014/022/029/034/035             |
| `SessionRecoveryAttempt` and activation barrier                                                                   | Exact recovering composite actor fence; immutable cut-time inbox/timer frontiers and schedule-cursor snapshots, separate post-cut operational cursor, invalidation/source revisions including every recovery-attempt-bound recovery-probe write, classifications, and sealed stage-host receipt                                           | Attempt becomes activated, failed, or superseded; active CAS succeeds only when every bound immutable frontier/revision is unchanged, every recovery-attempt-bound probe is terminal/non-widening, and each enabled-scope source ambiguity is resolved or explicitly capability-disabled; harmless post-cut rows remain pending and may advance only the excluded operational cursor                 | Minimized IDs/revisions/cursors only; unknown or unsealed peers disable capability; no raw provider body, media, prompt, or rig journal                                                                                                                                                                                                                                                                                  | ADR-003/011/015/020/025; OD-014/021/029/034/035/037     |
| `SessionNormalWorkAdmission` and closure drain                                                                    | One PostgreSQL environment/session status/epoch and committed-prefix closure cut across every durable normal input/turn-admission source, shared by command/input/timer admission, all ordinary Turn/candidate/approval/media/task/dispatch progression, ordinary effect intent/send/advancing application, begin-close, drain, and close | Monotonic open -> draining -> closed; immutable initial cause is normal closure or lost-tail quarantine, and a restored normal-closure drain may gain a monotonic lost-tail overlay; neither draining nor closed reopens; pre-close/affected prefix terminalizes or stays quarantined before final close; no post-begin-close-cut ordinary work is created or advanced                               | Quarantine atomically keeps lifecycle at `Ending`, preserving only a proven target and otherwise binding conceptual `unresolved_lost_tail_target`; bounded observations and separately typed source-bound recovery probes may add only finite non-widening evidence and must terminalize before close; prior send-authorized effects remain possibly sent until safe classification; authenticated stop remains separate | ADR-003/004/015/020/025; OD-014/021/029/034/035/037     |
| `RecoveryHistoryCompleteness` and `LostTailDisposition`                                                           | Protected recovery authority; exact recovery generation/point, trusted WAL/manifest high-water proof, and affected admission/close-cut/session/command/effect/timer/restriction ranges                                                                                                                                                    | Append-only zero-loss-proven, unknown, quarantined, or accountable-human-disposed state; absence in an unknown range never becomes proof of nonoccurrence                                                                                                                                                                                                                                            | Deny-only independent ledger refs may contain minimized ID/digest/generation/high-water only; cannot prove absence, close PostgreSQL history, reconstruct facts, or authorize execution; access/retention separated                                                                                                                                                                                                      | ADR-004/017/025; OD-009/029/034                         |
| Restrictive-control intent, attempt, and acknowledgement                                                          | Administrative revoke/safe-direction transaction creates intent; closed `session-runtime` dispatcher drains without active actor under current recovery generation/latest restrictive epoch                                                                                                                                               | Intent/attempt/ack append; bounded claims/retries; duplicates/reorder only preserve/strengthen restriction; convergence unknown until exact rig ack                                                                                                                                                                                                                                                  | Identifier/cause/epoch/binding/expiry/outcome only; priority reserve; cannot carry speech, clear/resume/raise, mint approval, or claim audience success                                                                                                                                                                                                                                                                  | ADR-004/011/015/020/025; OD-010/011/015/021/034/035/037 |
| `CommandIntent`, `CommandReceipt`, and `CommandOutcome`                                                           | Session-runtime ingress accepts only under current protected recovery generation and exact open admission/source frontier; ordinary execution/outcome also requires exact active composite actor fence and open admission                                                                                                                 | Intent immutable; receipt durable before acceptance; retryable auth invalidation remains pending/ineligible; one terminal outcome commits with domain effect and never reopens; draining permits only fixed-prefix terminal non-advancing outcome; caller `unknown` is not terminal state                                                                                                            | Semantic digest excludes volatile credentials; original auth refs remain separate; current auth is rechecked; no cross-principal receipt disclosure                                                                                                                                                                                                                                                                      | ADR-003/004/019/025; OD-014/021/022/034/035/037         |
| `CommandAuthorizationObservation`                                                                                 | Authenticated control/API handoff or owning service authorization boundary; append-only evaluation bound to exact command/principal/semantic digest, policy/revocation epoch, open admission epoch, and per-command lineage revision                                                                                                      | Initial observation commits with receipt; refreshed observations share admission/source CAS and append/deduplicate only while open/nonterminal/pre-deadline; protected execution selects one exact eligible observation under deterministic precedence and CASes the expected lineage revision                                                                                                       | Minimized auth method/step-up/presence refs, capability/resource, evaluator, decision/reason, evaluated-at/expiry; no reusable credential; concurrent/newer/incomparable result invalidates execution; draining/closed/terminal/expired retry uses disclosure-only bounded audit                                                                                                                                         | ADR-004/017/019/025; OD-014/021/022/034/035/037         |
| Session schedule and `TriggerOccurrence`                                                                          | Materialization takes the ownership-row conflict and requires the exact active composite fence plus exact open normal-work admission/source frontier; recovering may only classify existing state; claim/firing/Turn admission require active/open; canonical schedule-version/scope/nominal-occurrence key                               | Intent/occurrence immutable; one unique row per pre-close canonical key; explicit due/expired/cancelled/skipped/admitted disposition; at most one admitted turn and terminal firing disposition; cursor freezes once drain begins                                                                                                                                                                    | Exact policy/config/deadline refs; bounded materialization cursor CAS; no recovering or non-open occurrence creation/cursor advance; activation schedules remain a different authority                                                                                                                                                                                                                                   | ADR-003/024/025; OD-014/029/034/035/037                 |
| `TimerClaim` and firing disposition                                                                               | Exact active composite actor fence plus exact open admission/source epoch for ordinary claim/reclaim/firing; one occurrence-owned current-claim pointer with bounded unique token/revision                                                                                                                                                | Claim/reclaim CASes expected occurrence/current-claim revisions; loser reads winner/disposition; expiry does not complete occurrence; firing requires current unexpired claim; after non-open no current claim forms and active/recovering drain may only write the fixed-prefix terminal non-admitted disposition; terminal disposition is unique                                                   | Database/accepted clock proof only; token uniqueness alone is insufficient; timer wheel/Redis are wake-up aids; no unbounded materialization or catch-up                                                                                                                                                                                                                                                                 | ADR-003/004/025; OD-014/029/034/035/037                 |
| `StreamPlanVersion` and `SegmentVersion`                                                                          | Planning domain; stable roots plus immutable versions; session records exact use                                                                                                                                                                                                                                                          | Version immutable from creation; authoring draft/review and runtime progress are separate                                                                                                                                                                                                                                                                                                            | Prompt/persona/media bodies remain in protected sources; historical use not rewritten                                                                                                                                                                                                                                                                                                                                    | ADR-003/017/024; OD-025/032/034                         |
| `Turn`                                                                                                            | Session actor under the exact composite actor fence and open normal-work admission epoch; one admitted work lineage per turn                                                                                                                                                                                                              | Monotonic admitted/running/terminal path; no post-drain admission; deadline, cancellation, expiry, and completion never reopen                                                                                                                                                                                                                                                                       | Stores exact snapshot/trigger/lineage refs; raw viewer input and prompt separated                                                                                                                                                                                                                                                                                                                                        | ADR-003/008/017/018/025; OD-012/014/025/029/034/035     |
| `EffectIntent`, `EffectAttempt`, `EffectResponseObservation`, and `EffectApplicationDisposition`                  | Ordinary intent creation, send authorization, and advancing application require the exact active composite fence plus exact open admission/source conflict and responsible gateway; one logical domain operation owns one intent, an intent owns send-authorized attempts, and each observation belongs to one attempt                    | Intent precedes send and records its originating fence as provenance, not continuing authority; attempt is authorization, not proof of send; bounded response observations are evidence; each has at most one terminal disposition and at most one observation per intent advances state                                                                                                             | Identifier/digest/config/deadline/outcome refs; restricted request/response stays protected; successor reuse requires closed recovery classification, later active/open state, and complete current-authority revalidation; no SDK object/raw body in ordinary records                                                                                                                                                   | ADR-003/007/008/010/017/025; OD-014/025/029/034/035/037 |
| `RecoveryProbeIntent`, `RecoveryProbeAttempt`, `RecoveryProbeResponseObservation`, and `RecoveryProbeDisposition` | Separately typed evidence lineage admitted only under exact active+draining closure-prefix binding or exact recovering+recovery-attempt/source-ambiguity binding; shared ownership-row conflict, fresh database time, allowlisted read-only/restrictive operation, stable idempotency identity, and finite capacity                       | Intent owns `0..N` bounded attempts and exactly one terminal disposition; each attempt precedes first possible byte and each received response is observed before an observation-derived disposition; zero-attempt and terminal-unknown are valid; originating fence is provenance, and a current same-source successor may terminalize without resend; every lineage is terminal before final close | Bound to original prefix/range/effect/dispatch/rig ambiguity and unextended deadline; final close separately requires that source resolved, permanently safe-quarantined, or accountably disposed; no ordinary creation/application, new normal lineage, proof of absence, replay authority, raw body, generation, synthesis, signing, dispatch, resume, or mode increase; physical discriminator remains OD-034         | ADR-003/007/011/015/017/025; OD-014/021/029/034/035/037 |
| `GenerationAttempt`                                                                                               | Session actor/provider gateway lineage under ADR-025 composite fencing/effect mapping; many per turn                                                                                                                                                                                                                                      | One logical provider operation; terminal success/failure/timeout/cancel/malformed; policy retry/fallback/rewrite is a new attempt                                                                                                                                                                                                                                                                    | Restricted request/response refs; timeout/deadline/provider/config versions; no SDK object                                                                                                                                                                                                                                                                                                                               | ADR-003/007/017/018/025; OD-007/014/025/029/034/035     |
| `CandidateResponse` metadata                                                                                      | Exact active composite-fenced session actor records complete candidate identity; zero or one per logical generation attempt                                                                                                                                                                                                               | Immutable once complete; expiry/cancel/use state cannot change body or create new candidate                                                                                                                                                                                                                                                                                                          | Contains IDs/digest/classification/provenance, not necessarily body; never directly speakable                                                                                                                                                                                                                                                                                                                            | ADR-003/008/017/025; OD-014/025/029/034                 |
| Restricted candidate body                                                                                         | Restricted generation-content boundary; candidate ID and immutable content digest                                                                                                                                                                                                                                                         | Immutable content; availability/hold/deletion separate from candidate semantic state                                                                                                                                                                                                                                                                                                                 | Strong access/minimization; absent/deleted/corrupt body cannot be approved, reconstructed from audit, or spoken                                                                                                                                                                                                                                                                                                          | ADR-008/017; OD-009/025/034                             |
| Safety-layer evaluation evidence                                                                                  | `packages/safety` and approved safety gateways; many evidence items per candidate                                                                                                                                                                                                                                                         | Immutable observation/result per layer/attempt; unavailable/malformed is evidence, not approval                                                                                                                                                                                                                                                                                                      | Restricted inputs/outputs separated from minimized scores/reasons; provider output never self-authorizes                                                                                                                                                                                                                                                                                                                 | ADR-007/008/017; OD-002/003/025/034                     |
| `SafetyDecision`                                                                                                  | `packages/safety`; approval progression additionally requires exact active composite actor fence; zero or one terminal decision per candidate                                                                                                                                                                                             | Immutable and terminal; only approved/rejected/rewrite_requested decisions; never reopened                                                                                                                                                                                                                                                                                                           | Binds exact candidate, policy, evidence, context, versions, deadline; stale/recovering observation cannot become approval                                                                                                                                                                                                                                                                                                | ADR-008/025; OD-002/003/014/025/029/034                 |
| Durable `ApprovedResponseRecord`                                                                                  | `packages/safety` sole mint boundary under an exact active composite-fenced approval transaction; exactly one approved decision and selected same-turn candidate                                                                                                                                                                          | Immutable, expiring, revocable/restrictable only through separately modeled state; no remint by rehydrate                                                                                                                                                                                                                                                                                            | Metadata/authority lineage only; TTS/media receive `approved_response_id`, never raw text; approval cannot be inferred                                                                                                                                                                                                                                                                                                   | ADR-008/010/017/025; OD-002/003/014/025/029/034         |
| Restricted `ApprovedContentSnapshot`                                                                              | Safety-owned restricted content boundary; one exact snapshot per approval                                                                                                                                                                                                                                                                 | Immutable bytes/digest; content-availability, hold, deletion, corruption, and expiry axes separate                                                                                                                                                                                                                                                                                                   | Independent access/retention from approval metadata and public archive; missing content fails closed for new use                                                                                                                                                                                                                                                                                                         | ADR-008/010/017; OD-009/025/034                         |
| Human review case/decision                                                                                        | Protected review workflow; operator principal and lineage; any approving completion uses the exact active composite-fenced safety transaction                                                                                                                                                                                             | Case workflow mutable through explicit transitions; final decision joins same safety lineage, no bypass                                                                                                                                                                                                                                                                                              | Restricted candidate context and minimized audit separated; reviewer role/separation OPEN                                                                                                                                                                                                                                                                                                                                | ADR-008/019/025; OD-003/014/022/025/029/034             |

`ApprovedResponseRecord` is not a serialized capability that other packages can clone. The
runtime representation remains protected by ADR-008. A database row, DTO, event, or identifier
alone cannot mint or prove an in-process approval capability.

If the approved-content snapshot is unavailable, deleted, held against use, corrupt, mismatched,
or expired, new synthesis, rendering, replay, export, or publication fails closed. A public
recording or archive cannot be accepted as the canonical source for rehydrating the snapshot or
approval.

Every session-owned domain attempt, including generation, model-based safety, synthesis,
transfer, signing, and dispatch, inherits ADR-025 composite actor fencing and the four-record
effect crash boundary even when its row below names a more specific owner. One admitted logical
operation maps to one `EffectIntent`; reviewed transport replay is a child `EffectAttempt`,
whereas policy retry/fallback/rewrite or semantic/provider change is a new domain attempt and
intent. No lifecycle row may be implemented as an exception to that mapping.

## Rights, Surface, Media, And Playout Records

| Record family                                     | Authority and identity/cardinality                                                                          | Mutability and terminality                                                                                                                    | Data, access, retention, and use rule                                                                                     | Governing gates                                             |
| ------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `VoiceProfileDefinition`                          | Protected voice/config owner; stable root plus immutable version                                            | Version immutable; technical eligibility separate from rights state                                                                           | Provider-neutral technical metadata/restricted refs; profile existence is not permission                                  | ADR-007/017/022/024; OD-024/034                             |
| `VoiceRightsGrantVersion`                         | Human legal/talent rights domain; immutable normalized grant version                                        | Corrections create version; grant eligibility/state separate                                                                                  | Raw contracts/identity/consent evidence in restricted store; audit/events use IDs/digests only                            | ADR-017/019/022; OD-024/034                                 |
| `VoiceRightsState`                                | Rights authority; one current state/epoch per governed binding                                              | Activation/suspension/expiry/revocation serialized and monotonic; no stale resurrection                                                       | PostgreSQL authority; caches/tasks only bounded snapshots; hold does not authorize use                                    | ADR-004/017/022; OD-024/034                                 |
| `VoiceRightsDecision` and `VoiceUseAuthorization` | Proposed protected rights evaluator/mint boundary; decision per exact use context                           | Decision terminal; authorization immutable and bounded; retry/replay needs exact valid binding                                                | Separate from content and surface approval; no raw legal evidence; missing/current-epoch mismatch denies                  | ADR-008/017/021/022; OD-023/024/025/034                     |
| `SurfaceDecision` and `SurfaceAuthorization`      | Proposed protected surface-policy evaluator/mint boundary; exact final rendering/destination                | Decision terminal; authorization immutable, expiring, exact-context bound                                                                     | Separate from content and rights; normalization/final context fixed; authorization cannot be reused for another rendering | ADR-008/010/017/021; OD-023/025/034                         |
| `FinalRendering`                                  | Protected rendering boundary; immutable exact linguistic/presentation representation                        | New normalization, SSML, subtitle, translation, or layout creates a new identity                                                              | Restricted content separate from metadata; changing rendering requires new surface evaluation                             | ADR-008/010/017/021; OD-023/025/034                         |
| `SynthesisAttempt`                                | TTS provider gateway under ADR-025 composite fencing/effect mapping; one logical identifier-only invocation | Terminal attempt; policy retry/fallback is new attempt; reviewed transport replay is a child `EffectAttempt`; cannot extend upstream deadline | Receives `approved_response_id` plus approved metadata/authorization IDs only; provider request/response restricted       | ADR-007/008/010/017/018/022/025; OD-007/014/024/025/029/035 |
| Immutable media artifact                          | Approved media boundary; immutable artifact ID/digest and complete authorization/version lineage            | Bytes never mutate; availability/quarantine/expiry/deletion separate; transformations create new artifact                                     | Technical existence is not replay/export/publication permission; storage/access/retention family-specific                 | ADR-010/017/021/022; OD-023/024/025/032/034                 |
| Media/use authorization                           | Protected reviewed decision for non-text media/use where accepted                                           | Immutable, exact artifact/context/destination/time bound; missing or stale denies                                                             | Cannot bypass `ApprovedResponse` for generated speech or manufacture voice/surface rights                                 | ADR-008/010/021/022; OD-023/024/025                         |
| `SpeechTask` dispatch record                      | `session-runtime` approved dispatch; stage host is sole task consumer                                       | Immutable signed task intent; delivery/acceptance/playback outcomes separate; expiry terminal                                                 | Identifier-only, no raw text; binds approval/artifact/rights/surface/session/epoch/deadline per accepted contracts        | ADR-008/010/011/016/021/022; OD-010/011/021/023/024         |
| Stage-host queue/journal entry                    | Bound `stage-host`; local append-only intent/outcome evidence                                               | Queue state monotonic; reboot/reconnect/reconciliation explicit; no cloud state invention                                                     | Encrypted/restricted local data; cannot approve or rewrite task; retention and upload policy OPEN                         | ADR-011/015/016/017; OD-010/011/015/034                     |
| `PlayoutObservation`                              | Stage host records observed start/stop/interrupt/failure; cloud reconciles                                  | Immutable observation/correction lineage; late evidence does not rewrite authorization                                                        | Proves observed behavior, not permission; no raw speech text; clock uncertainty preserved                                 | ADR-004/011/015/016/017; OD-010/011/015/032/035             |

Actual playout, authorized playout, successful synthesis, and audience publication are distinct
facts. A recording of unauthorized output is incident evidence, not a retroactive approval.

## Input, Prompt, Memory, Knowledge, And Archive Records

| Record family                            | Authority and identity/cardinality                                                                   | Mutability and terminality                                                                | Data, access, retention, and use rule                                                                                 | Governing gates                     |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| Viewer/operator input metadata           | Session/input boundary; immutable input ID, source/provenance/classification refs                    | Observation immutable; moderation/admission/deletion outcomes separate                    | No raw message in ordinary event/audit/telemetry; username attacks treated as untrusted content                       | ADR-003/008/017/019; OD-025/026/034 |
| Restricted input body                    | Restricted input-content store; exact input ID/digest                                                | Immutable source bytes; content availability/retention/hold/delete separate               | Purpose-limited access; cannot become durable memory without separate extraction and policy                           | ADR-008/017; OD-009/025/026/034     |
| `PromptAssemblyManifest`                 | Session orchestration records exact ordered inputs/versions/digests                                  | Immutable per attempt; new assembly is new manifest                                       | IDs/digests and transformation provenance; does not contain ordinary audit copy of full prompt                        | ADR-007/008/017/024; OD-025/026/034 |
| Restricted assembled prompt              | Restricted generation-content boundary; manifest/attempt binding                                     | Immutable bytes; availability/hold/deletion/corruption separate                           | Provider gateway receives only under approved purpose/timeout; never logged, emitted, or copied into config           | ADR-007/008/017; OD-009/025/026/034 |
| Typed `ViewerMemory`                     | Viewer-memory boundary; VNova viewer/interaction identity, purpose, source, extractor/policy version | Explicit propose/review/active/superseded/deleted lifecycle; no silent mutation           | Never shares table/content/access role with audit; consent/legal basis, retention, correction, deletion OPEN          | ADR-017; OD-009/026/034             |
| Typed `CharacterMemory`                  | Character-memory boundary; character and source scope                                                | Versioned facts/summaries; conflict/supersession/deletion explicit                        | Cannot absorb viewer identity/content without approved purpose; separate access and retention                         | ADR-017; OD-009/026/034             |
| Ephemeral `SessionContext`               | Session actor; session/turn scope                                                                    | Bounded session lifetime; expiry terminal; durable promotion requires new reviewed record | Not durable viewer memory by accident; fail closed when required provenance unavailable                               | ADR-003/017; OD-009/026/034         |
| `KnowledgeSource` and version            | Curated knowledge owner; stable source plus immutable version/provenance/rights/classification       | Eligibility, expiry, withdrawal, deletion, correction separate                            | Source content protected; retrieval rights and publication rights independent                                         | ADR-017/019; OD-026/032/034         |
| Derived chunk/embedding/index generation | Retrieval subsystem; source/version/model/scrubber/index-build lineage                               | Rebuildable and non-authoritative; generation immutable; current index pointer separate   | Source deletion cascades; hold/revocation quarantines; cannot restore source, memory, consent, or authority           | ADR-007/017; OD-026/034             |
| Recording asset                          | Media/archive evidence boundary; immutable bytes/digest/source/session/playout lineage               | Availability, rights, retention, quarantine, deletion separate                            | Recording does not imply approved content or archive/publication rights; restricted access until reviewed             | ADR-017/021/022; OD-023/024/032/034 |
| `SessionArchive` index                   | Archive domain; immutable references to curated evidence/artifacts                                   | Archive composition is versioned; current/publication status separate                     | Never stores or reconstructs viewer memory/audit content together; source authorization remains traceable             | ADR-017/021/022; OD-023/024/032/034 |
| Publication/use disposition              | Authorized publication/rights/surface workflow; exact artifact/destination/purpose/time              | Terminal decision or explicit superseding/takedown/retraction transition                  | Live allow does not imply archive/replay/clip/export; public artifact cannot mint safety/rights/surface authorization | ADR-019/021/022; OD-023/024/032/034 |

Memory is typed and purpose-specific. Every durable memory record retains source provenance,
scrubber/extractor version, governing policy version, confidence/evidence semantics, and
classification. A model-generated summary is derived evidence, not an unqualified fact.

Knowledge embeddings and indexes are rebuildable acceleration structures. Source deletion,
revocation, correction, or hold changes retrieval eligibility immediately and drives a
reviewed cascade/quarantine workflow. Backup restoration or stale index replay cannot re-enable
them.

## Operational, Audit, Event, And Workflow Records

| Record family                                | Authority and identity/cardinality                                                                                                                             | Mutability and terminality                                                                                                                                                           | Data, access, retention, and use rule                                                                                                | Governing gates                             |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------- |
| `AuditRecord`                                | Owning domain transaction plus protected audit boundary; immutable fact ID                                                                                     | Append-only; correction/redaction/anonymization uses linked disposition, never silent rewrite                                                                                        | Minimized IDs/digests/versions/actor/action/outcome; no viewer-memory, prompt, candidate, approved text, secret, or contract         | ADR-004/017/019; OD-009/022/034             |
| `EventContractProfile`                       | Contract authority; immutable complete `(envelope_version, type, event_contract_version)` identity/profile/digest                                              | Immutable from creation; semantic change creates another profile                                                                                                                     | Payload, subject/scope, completeness, classification, producer/consumer, retention, and recovery semantics stay historical           | ADR-002/004/017/023; OD-017/033/034         |
| `EventCatalogEligibility`                    | Contract lifecycle authority; one current state and monotonic catalog epoch per exact event-contract profile                                                   | Append-only transitions; active/deprecated/retired/withdrawn history never edits the profile                                                                                         | Emission binds exact active-state evidence; delivery, recovery replay, and incident decode use distinct current dispositions         | ADR-002/004/017/019/023; OD-017/022/033     |
| `DomainEventRecord`                          | Owning aggregate transaction; immutable event ID and complete profile plus emission eligibility evidence, typed scope/subject, causal position, manifest ID    | Immutable semantic fact; delivery and replay attempts separate                                                                                                                       | Minimized catalog-approved payload; PostgreSQL recovery authority; event is notification, not authorization                          | ADR-002/004/017/023; OD-017/033/034         |
| `EventTransitionManifest`                    | Owning aggregate transaction; one immutable manifest for every committed subject aggregate version, including exact zero-count attestations                    | Commits with state, zero-or-more events, expected-delivery evidence, audit, and outbox; never inferred from Redis                                                                    | Exact ordered event identities/digests/count; authorized views expose required subset or explicit zero/empty attestation             | ADR-002/004/017/023; OD-017/033/034         |
| `OutboxRecord`                               | Same transaction as one emitted event; distinct immutable publication intent referencing exact event identity/digest                                           | Exactly one per event; claim/attempt/ack never rewrites the event or publication intent                                                                                              | PostgreSQL authority; retention/classification explicit; Redis copy is transport only                                                | ADR-004/023; OD-017/033/034/037             |
| Outbox claim/lease                           | Publisher coordination; one bounded claim attempt                                                                                                              | Mutable/expiring coordination or append-only attempts; lease expiry never means domain rollback                                                                                      | No payload authority; clock/owner generation/fencing required; restoration cannot make stale claimant current                        | ADR-004; OD-035/037                         |
| Delivery attempt                             | Publisher; one destination attempt ID per event/replay lineage                                                                                                 | Append-only outcome; retries are new attempts; external timeout explicit                                                                                                             | Carries minimized transport evidence; does not change occurrence time or event identity                                              | ADR-004/007/017; OD-017/035/036/037         |
| Consumer expected-delivery/high-water record | Authorized durable lane-consumer profile plus every manifest version, required subset, and subject-lane progress                                               | Required set fixed by committed manifest/profile; progress monotonic only after durable completeness                                                                                 | Explicit zero-event and filtered-empty attestations reveal no unauthorized event metadata; missing whole transition stays stale      | ADR-002/004/017/023; OD-017/033/034         |
| Inbox consumption record                     | Consumer authoritative store; consumer/event/complete-contract/manifest/effect and observed protection-epoch/high-water binding                                | Exact duplicate idempotent; conflicting digest, lane position, or regressed protection evidence is an integrity incident                                                             | Commits with durable side effect; later irreversible handling requires current protection revalidation                               | ADR-002/004/017/019/023; OD-017/033         |
| `EventProtectionOverlay` aggregate           | Protected privacy/security/legal authority; stable environment-contained ID, typed immutable target profile, monotonic protection epoch/partition high-water   | CAS forward transitions; ordinary change tightens, protected release is explicit; never deletes or rewrites event/profile/digest                                                     | Effective union governs access/routing/replay/retention/hold/deletion/export/reveal/dead-letter; stale/unknown/conflict fails closed | ADR-017/019/023; OD-009/017/022/033/034     |
| `EventHandlingAuthorization`                 | Protected event-protection authority; exact event/digest, operation, purpose/destination, overlay epochs/high-waters, workload, and expiry                     | Immutable, short-lived, and single-use; retry is new authorization; reuse/expiry/newer high-water invalidates                                                                        | Carries no payload/content authority; direct current revalidation remains an alternative at the irreversible effect boundary         | ADR-004/017/019/023; OD-009/017/022/033     |
| Idempotency record                           | Owning command/effect/trigger boundary; protected principal/action/environment/resource/stable-key scope; command digest is not its uniqueness/lookup identity | Digest is stored and compared after scoped-key lookup; same intent returns prior outcome, conflicting reuse creates no second lineage; retention covers retry/replay/recovery window | Stores digest and minimized refs, not secret/raw command content; never authorizes a different action                                | ADR-004/019/025; OD-014/017/021/022/034/035 |
| Stage-host journal                           | Local stage-host authority for received command/task and observed outcome                                                                                      | Append-only/fenced by boot, connection, session, command sequence; reconciliation explicit                                                                                           | No raw generated text; protected local retention/access; cloud cannot treat absence as proof of non-playout                          | ADR-011/015/016/017; OD-010/011/015/034     |
| Incident and evidence manifest               | Incident-response owner; stable incident/evidence refs and chain-of-custody metadata                                                                           | Findings/corrections append; closure/reopen follows incident policy, not domain-record mutation                                                                                      | Restricted evidence remains in source stores; manifest has hashes/refs/access logs, not copied content                               | ADR-017/019; OD-022/027/032/034             |
| Deletion/correction/hold case                | Privacy/legal/data owner; exact subject/source/policy/request/authority scope                                                                                  | Explicit requested/validated/executing/confirmed/denied/held transitions; terminal outcomes linked                                                                                   | Separate from content record; hold blocks erasure but not use restrictions; evidence access purpose-limited                          | ADR-017/019; OD-009/022/026/034             |
| Tombstone                                    | Source domain under accepted privacy policy; minimum stable identity and disposition refs                                                                      | Immutable/minimized; cannot reactivate source; correction is linked new evidence                                                                                                     | Contains no deleted content or reversible low-entropy digest; retention and disclosure OPEN                                          | ADR-017; OD-009/026/034                     |
| Restore/reconstruction case                  | Protected recovery authority; exact backup/source/scope/epoch/review evidence                                                                                  | Append-only workflow; successful technical restore does not restore eligibility                                                                                                      | Revalidates deletion, hold, revocation, rights, activation, epochs, and derived-data quarantine before any use                       | ADR-004/017/019/024; OD-009/022/034         |

An outbox row is not a mutable delivery job containing the latest attempt. The immutable domain
event/publication intent, transient claim or lease, each delivery attempt, consumer inbox
record, poison disposition, and authorized replay are separate records. This separation
preserves original evidence and permits bounded cleanup without rewriting domain history.

`DomainEventRecord` and `OutboxRecord` are distinct logical records with separate identities and
lifecycles, in an exact one-to-one relationship for every emitted event. A future linked migration
ADR may prove that one physical row safely implements both roles, but it must preserve the
independent event fact, publication intent, constraints, access, retention, reconstruction, and
attempt history. Physical co-location cannot collapse the logical authorities.

## Transaction Profiles

The following atomicity profiles are conceptual minimums. Physical isolation and constraints
require a migration ADR.

### Aggregate Transition

One PostgreSQL transaction commits:

- authoritative aggregate state and revision/epoch;
- every required immutable transition record and zero or more distinct domain-event records with
  typed scope/subject, aggregate version/event index, complete event-contract profile, and exact
  emission eligibility evidence;
- exactly one immutable transition manifest for the new aggregate version, including when its
  event count is zero, plus every authorized lane consumer's expected-delivery subset or explicit
  zero/empty attestation;
- required minimized audit evidence;
- one immutable outbox record for each emitted event.

If the manifest, required expected-delivery evidence, any required event, its corresponding
outbox record, or required audit record cannot be written, the transition does not commit. A
zero-event transition has no event or outbox record, but its zero-count manifest and authorized
attestations remain mandatory completeness evidence.
ADR-004's explicit safe-direction database-failure exception may restrict process-local behavior,
but it cannot claim durable completion or permit recovery before reconciliation.

### Session Ownership

One ownership transition transaction:

- validates the independently protected recovery generation and takes the shared incompatible
  conflict on the exact environment/session ownership row;
- after winning the conflict, takes a fresh PostgreSQL clock sample, re-reads the row/revision,
  and applies the operation-specific acquire, renew, activate, expiry/takeover, revoke,
  relinquish, or close predicate;
- validates authenticated runtime process incarnation and protected revoke/close authority where
  applicable;
- increments `ownership_generation` for acquire, relinquish, revoke, takeover, or close and never
  for ordinary renew/activation;
- records the resulting vacant/recovering/active/closed phase, exact owner/lease when applicable,
  immutable transition evidence, and minimized audit; and
- grants ordinary authority only after a distinct recovery-complete transition reaches `active`.

The `close` transition from the exact current active or recovering fence additionally proves the
session lifecycle is `Ending` with a resolved terminal target, the exact `draining` admission
epoch/fixed normal input/command/timer prefix is fully terminal, and no accepted nonterminal work
or unresolved audience ambiguity remains. Every admitted recovery-probe lineage must already
have a terminal non-widening disposition, while each separately bound source ambiguity is
resolved, permanently safe-quarantined, or accountably disposed. A terminal probe may remain
truthfully `unknown`. The same transaction commits that resolved session terminality, admission
`closed`, ownership-generation increment, owner/lease clear, and ownership `closed`; it cannot
abandon pending accepted work or create an intermediate terminal-session/active-owner gap.

A timed-out transaction is unknown and grants no cached authority. An aggregate mutation that
does not use the same ownership-row conflict and validate the exact active composite fence,
post-conflict unexpired lease, aggregate version, and deterministic lock order cannot commit.
Transaction-start time, a read predicate, aggregate-row update, or isolation level alone is not
the fence.

Administrative revoke with possible escaped audience work uses the ownership/session lock order
to atomically increment ownership generation, clear the owner, preserve a `closed` phase or
otherwise enter/preserve `vacant`, rotate the restrictive session fence/epoch, install
dispatch/recovery hold, create priority-control intent, and mark exact-rig convergence
unresolved. Cloud revoke does not claim audience cessation before stage-host acknowledgement.

The closed restrictive-control dispatcher claims that intent without active actor authority,
revalidates current recovery generation/latest restrictive epoch/exact rig binding/expiry, and
records each bounded priority-lane attempt and acknowledgement. Its transaction cannot mutate
ordinary session state or reduce restriction. Redis/notification loss leaves the PostgreSQL
intent pending; missing exact-rig acknowledgement leaves convergence unknown.

### Session Closure And Normal-Work Admission

One begin-close transaction takes the ownership/session/source lock order, transitions the
nonterminal lifecycle to `Ending` with its resolved requested terminal target/cause,
compare-and-swaps the normal-work admission gate `open -> draining`, advances its epoch, and fixes
the committed-prefix cut across every durable normal input/turn-admission source, including
command receipt and timer materialization. All normal input-promotion/turn-admission, ordinary
effect-intent/send/advancing-application, and ordinary
Turn/attempt/candidate/selection/approval/media/task/signing/dispatch progression transactions
share the same row conflict:

- a receipt/occurrence serialized before the cut belongs to the bounded pre-close drain;
- a normal command serialized afterward receives deterministic non-acceptance and creates no
  command lineage;
- timer materialization after the cut creates no occurrence; applicable cursors freeze with one
  schedule-level closure disposition rather than per-future-slot rows;
- raw input may append only under separately bounded intake/evidence policy and cannot be
  promoted into an eligible trigger or turn; and
- no post-begin-close-cut ordinary effect receives send authority or advances domain/audience
  state; a prior send-authorized attempt remains possibly sent until safely classified, bounded
  late response observations may append as evidence, and drain may commit only non-advancing
  expiry/cancellation/rejection/quarantine evidence;
- the separately typed, finite `RecoveryProbe*` exception may send only under its exact
  active-plus-draining-prefix or recovering-plus-recovery-attempt/source binding; it is
  read-only/restrictive, cannot widen or replay ordinary work, and terminates independently from
  the bound source ambiguity;
- no unlisted ordinary pipeline stage may advance after the cut; bounded observation evidence,
  restrictive action, and terminal/non-advancing disposition are the only permitted writes; and
- safe-direction stop remains a separate restrictive path.

The active actor or recovery-only successor terminalizes the fixed prefix in bounded
transactions. Every input promotion, turn admission, timer claim/firing, ordinary effect intent/
send/advancing application, and other ordinary pipeline progression checks the exact open
admission epoch and cannot advance normal work after drain begins. Final close takes the recovery
guard,
ownership, session, and admission/source rows in fixed order; compares the exact draining epoch/
prefix; proves the lifecycle is `Ending` with a resolved terminal target, every pre-close input,
command, occurrence, turn, and effect is terminal/safely classified, and no audience ambiguity
remains; proves every admitted recovery-probe lineage terminal/non-widening and every bound source
ambiguity resolved, permanently safe-quarantined, or accountably disposed; and atomically commits
that resolved session terminality, drain evidence, admission `closed`, ownership-generation
increment, owner/lease clear, and ownership `closed`.

A crash before commit leaves `Ending`/`draining`; a successor may acquire only to recover/close.
A crash after commit sees all terminal facts. Revoke/relinquish versus final close serializes on
the ownership row: a prior revoke/relinquish leaves `Ending`/`draining`/vacant for successor
close, while a winning final close makes later relinquish/reacquire illegal and revoke
phase-preserving.

### Recovery Activation

One recovery attempt installs a commit-time cut through source-frontier rows shared by every
durable normal input-promotion/turn-admission source, including command receipt and
timer-materialization commits. A source uses a gapless committed-prefix manifest or equivalent
commit-time pre-cut/post-cut partition; allocated IDs, sequence/timestamp maxima, and nonlocking
scans are not frontiers. Post-cut normal rows remain pending and unclaimable/unpromotable.

The activation transaction takes the shared ownership-row conflict and compare-and-swaps:

- exact composite actor fence and ownership revision;
- exact normal-work admission status/epoch and any pre-close drain prefix;
- immutable cut-time committed source frontiers and timer materialization-cursor snapshots,
  excluding any later post-cut operational cursor;
- recovery invalidation/source revisions, including every recovery-attempt-bound recovery-probe
  intent/attempt/observation/disposition write and a successor's terminalization of an
  old-originating-fence lineage;
- completed classifications, every recovery-attempt-bound probe terminal/non-widening, and each bound
  source ambiguity resolved for the enabled scope or held behind an explicit capability disable;
- exact configuration/safety/rights/authorization/clock/capacity evidence; and
- authenticated sealed stage-host boot/binding/epoch/journal cursor and restrictive-hold receipt.

Any changed pre-cut classification, new restrictive/ambiguity-bearing fact, or recovery-attempt-bound
recovery-probe write invalidates activation. A transaction that reserved an ID before the cut but
commits afterward is source-serialized into the post-cut partition or invalidates the attempt.
Harmless post-cut ingress may advance only its separate operational cursor; that cursor is not
compared by the activation CAS and cannot starve activation.
Ordinary activation requires admission `open`; `draining` recovery finishes terminalization and
closure, while `closed` remains terminal.

### Recovery History Completeness

Before a restored session can classify an absent admission/close transition, command, effect,
timer, or restriction, recovery commits one completeness/disposition record binding recovery
generation, recovery point, trusted WAL/manifest high-waters, affected ranges, and the evidence
proving zero loss or unknown tail. An unknown tail atomically installs quarantine/deny scope; a
restored `open` admission state becomes non-open and cannot admit command/timer/turn work or
reopen that session. Specifically, the new recovery generation atomically installs
`draining(lost_tail_quarantine)`, the trusted pre-loss high-water/unproven interval/affected
source set, restrictive holds, permanent reopen prohibition, and a coherent `Ending` lifecycle.
It preserves a terminal target only when proven inside the trusted horizon; otherwise it binds
the conceptual `unresolved_lost_tail_target` marker.

A restored `draining(normal_closure)` state keeps its historical initial cause and fixed prefix
but atomically gains the monotonic lost-tail overlay/interval/holds and the same stronger
final-close gate. A restored atomic `closed` state remains terminal and ownerless while later
unknown-tail/restrictive evidence is recorded separately. Final close requires an
OD-029-authorized disposition that resolves any target ambiguity, exact rig/audience
reconciliation, and safe classification or permanent quarantine of every affected range;
otherwise it remains `Ending`/`draining`. Recovery never creates a missing domain fact. A
minimized independent ledger can strengthen denial by proving prior existence, but cannot prove
absence, close PostgreSQL history, recreate a receipt/outcome/observation, or authorize
execution. Human disposition is append-only, scoped, and cannot relabel unknown history as
definitely absent without accepted proof.

### Command Receipt And Execution

Command acceptance first conflicts/CASes the exact open normal-work admission/source row and
uses fresh accepted database time after that conflict to prove the immutable hard deadline before
it commits canonical intent, a durable receipt, and the initial append-only authorization
observation under one idempotency scope. A
same-scope/different-digest request conflicts; a same-intent retry may append a deduplicated
refreshed authorization observation only through the same exact open admission/source CAS and
fresh post-conflict database-time deadline/evidence check, and return the original record only
after current receipt-disclosure authorization. The protected lookup scope includes submission
recovery generation, environment/session, principal/trusted source, semantic command type, and
key—but not the semantic digest or parameters. The digest is stored on the first intent and
compared only after that lookup; it also excludes volatile credential/transport-session
artifacts. Original authorization provenance and later observations remain separate and
immutable. A stale/unknown submission generation requires reconciliation, not fresh acceptance.
No domain mutation is required for receipt acceptance. Once admission is `draining` or `closed`,
the transaction cannot create nonterminal accepted work; a concurrent pre-closure-cut winner
belongs to the fixed drain prefix. Refreshed retries after that cut append no authorization
observation and can perform only disclosure-authorized lookup.

Normal execution later commits in one PostgreSQL transaction:

- shared ownership-row conflict plus exact current active composite actor fence and post-conflict
  lease check;
- exact open normal-work admission/source-row conflict plus fresh post-conflict database time;
- current command deadline, exact eligible authorization observation, current policy/revocation
  epoch, expected authorization-lineage revision, deterministic observation precedence,
  aggregate version, and domain preconditions;
- authoritative aggregate mutation, if successful;
- exactly one terminal command outcome;
- required minimized audit; and
- any authorized event manifest/outbox records.

A caller timeout is not a terminal outcome. ADR-004/015/020/025 safe-direction actuation may
restrict before receipt or aggregate durability, but it cannot claim accepted command completion.
Every path returning an existing receipt/outcome—including duplicate submission—independently
reauthenticates and reauthorizes object/data-class disclosure; key possession is not read
capability. Deadline passage makes the command permanently ineligible immediately, and a current
owner later records one expired/failed-closed terminal disposition. A refreshed credential
handoff that was not durably appended cannot be reconstructed from a transient request, while an
appended observation cannot survive its expiry or a newer restrictive authorization epoch.
Retryable authorization invalidation remains pending-but-ineligible until refreshed evidence or
deadline; only an OD-022-accepted nonretryable denial may terminally reject. Observations appended
after any terminal outcome or effective expiry are rejected; receipt disclosure is a separate
bounded audit decision and never reopens execution.
Every append advances/CASes the per-command authorization-lineage revision. Execution conflicts
on that lineage and rejects a changed revision; until OD-022 accepts exact precedence, a newer or
incomparable allow/deny/step-up/unavailable result fails closed rather than permitting selection
of an older allow.

Once admission is non-open, ordinary claim/execution and successful or widening command outcome
are forbidden. The closure-drain transaction may select only the fixed pre-close command and
commit a terminal non-advancing expiry/cancellation/rejection/fail-closed/quarantine disposition,
using fresh accepted database time; it cannot execute the semantic action.

### Direct Input Promotion And Turn Admission

Every normal non-timer input-promotion or turn-admission transaction—including viewer/platform
input, operator/director, and content-scheduler paths—takes the shared ownership-row conflict and
the exact source/admission-row CAS. It proves the active composite fence, fresh lease time, exact
open admission epoch, stable input/trigger identity, moderation/configuration/deadline/capacity
eligibility, and aggregate version before committing one turn admission. Under `draining`, the
active or recovery-only closure transaction instead CASes the exact fixed prefix/draining epoch
and may commit only a terminal non-advancing input expiry/cancellation/rejection/fail-closed/
quarantine disposition; it cannot promote input or create a Turn. Raw intake may continue only
under its separately bounded retention/moderation policy; after a recovery cut it cannot become
an eligible trigger or turn until activation permits it, and after a closure cut it never can.

### Session External Effect

Ordinary `EffectIntent` creation takes the shared ownership-row conflict and exact-open
admission/source epoch, then commits before any send. Immediately before the first possible
network byte, the actor repeats that conflict to prove the exact active composite fence,
post-conflict remaining lease horizon, deadline, eligibility, and stable idempotency identity,
then commits one send-authorized `EffectAttempt`. The attempt is not proof of transmission; from
that commit boundary a crash is `possibly_sent`.

Every received response, query result, timeout, cancellation, or indeterminate transport result
commits an immutable `EffectResponseObservation` before application. Ordinary application is a
separate transaction that takes the shared ownership-row conflict and revalidates the exact
active composite fence, exact-open admission/source epoch, aggregate version, deadline, and
restrictions before atomically committing one terminal `EffectApplicationDisposition` and any
advancing domain transition. Recovery probes use the
distinct four-role lineage: intent admission proves either exact active+draining immutable-prefix
binding or exact recovering+recovery-attempt/source-ambiguity binding, plus fresh database time,
allowlisted read-only/restrictive purpose, stable idempotency, unextended deadline, and finite
capacity. An intent may terminalize with zero attempts; otherwise each attempt precedes the first
possible byte and each received result is observed before it may inform the intent's exactly one
terminal non-widening disposition; late observations after terminality are bounded evidence-only.
Originating fence/binding is provenance: after crash/takeover, current
active-draining or recovering authority bound to the same source may terminalize
stale/unknown/quarantined without another send; a new query requires a new bounded intent. A
timeout, contradiction, or non-authoritative negative may leave terminal probe evidence unknown
and cannot create/apply ordinary work, prove absence, or authorize replay. Final close requires
every probe terminal plus the separate bound source ambiguity resolved, permanently
safe-quarantined, or accountably disposed.

One logical domain-provider attempt owns one intent. Reviewed transport replay may create
multiple send-authorized attempts under the same intent/idempotency identity; a policy retry,
rewrite, fallback, provider change, or semantic request change creates a new domain attempt and
intent. Each observation belongs to one attempt and has at most one terminal disposition; at
most one observation per intent advances domain/authority state. A stale-composite-fence, late,
expired, cancelled, superseded, or possibly-sent/unknown result records only non-advancing
evidence. A successor does not blindly repeat a non-idempotent unknown effect.

### Timer Occurrence And Turn Admission

One bounded materialization transaction derives the canonical occurrence key from exact
environment/session/schedule version/scope and nominal schedule coordinate, enforces uniqueness,
then takes the shared ownership-row linearization point, fresh accepted database time, and exact
active composite actor fence before it conflicts/CASes the exact open normal-work
admission/source row and advances the per-schedule materialization cursor with the same committed
set. Commit-response loss and duplicate evaluators re-read the same occurrence; sequence
allocation alone cannot prove completeness. A recovering owner may classify only existing
occurrence/cursor state and cannot create or advance normal schedule work.
Once admission is non-open, materialization creates no occurrence identity of any disposition and
does not advance the recurring cursor; one schedule-level closure disposition records the freeze
without unbounded per-future-slot rows.

One due-evaluation/claim transaction takes the shared ownership-row conflict, validates the
occurrence key/revision, expected current-claim revision, due window, fresh accepted database
time, exact active composite actor fence, and bounded claim eligibility, then atomically
compare-and-swaps the occurrence-owned current-claim pointer to a unique token/revision. A
concurrent loser reads the winning claim or terminal disposition. Claim expiry never marks the
occurrence complete; reclaim repeats the CAS and supersedes the prior pointer.

Claim and firing also require the exact open normal-work admission epoch. If closure begins, no
claim can become current and a prior claim can commit only a terminal non-admitted occurrence
disposition.

One firing transaction takes the shared ownership-row conflict and revalidates the composite
fence, fresh database time, exact current unexpired claim token/revision, occurrence revision,
deadline, restrictions, capacity, and trigger policy, then commits either:

- exactly one new `Turn` admission plus the occurrence's terminal admitted disposition; or
- an explicit terminal expired/skipped/cancelled/failed-closed disposition.

Reclaim supersedes an old token even under the same actor fence. Duplicate wake-ups and successor
claims return the same disposition. Materialization/catch-up ranges are bounded under OD-037. No
restart creates an unbounded catch-up set or silently turns an ADR-024 activation schedule into a
session trigger.

### Safety Approval

One protected safety transaction or equivalently constrained workflow binds:

- terminal literal approving `SafetyDecision`;
- selected same-turn `CandidateResponse`;
- safety-owned `ApprovedResponseRecord`;
- exact restricted `ApprovedContentSnapshot` and canonical digest;
- required minimized audit/outbox evidence.

Only `packages/safety` can construct the approval capability. A partially committed approval,
content snapshot without matching decision, or metadata without resolvable exact content is not
speakable.

### Definition Or Activation-Set Eligibility

One eligibility transition commits:

- exact immutable definition/set identity and digest;
- expected current eligibility state/epoch;
- new state and strictly increasing eligibility epoch;
- immutable transition and protected review/authority evidence;
- affected-use restriction/invalidation intent where required;
- minimized audit, event manifest, and outbox evidence.

The immutable version or set is not edited. A restrictive transition takes safe-direction effect
at reachable enforcement points and dependent work cannot rely on a snapshot carrying the stale
eligibility epoch.

### Activation

One activation transaction commits:

- expected/current binding state, selected set, and activation epoch check;
- exact closed operation and next inactive/active state, with an exact eligible set only when
  active;
- current definition/set eligibility epochs used by preflight;
- new monotonic activation epoch/current binding state;
- immutable transition and protected review/authorization refs;
- minimized audit, event manifest, and outbox evidence.

Consumers never observe a partial bundle or row-deletion deactivation. Rollback uses the same
profile with a new forward epoch. At scheduled execution, the exact still-scheduled state/epoch,
ordinary activation transition, resulting binding state, and `executed` schedule-state
transition commit atomically; stale or terminal schedules create no activation.

### Memory Write Or Delete

The purpose-specific memory transaction binds:

- source/provenance and policy/extractor/scrubber versions;
- typed memory metadata and restricted content operation;
- retention/access/deletion disposition;
- minimized audit/outbox references without copying content;
- derived-index invalidation or quarantine intent.

Audit and viewer memory remain separate tables, content, and access roles even when committed
under one higher-level workflow.

### Delivery And Consumer Effect

Publisher claim, each external attempt, acknowledgement, and replay evidence are recorded
separately. A consumer with a durable side effect commits that effect, its inbox/idempotency
marker, and manifest expected-set/high-water progress atomically in the consumer's authoritative
store. Redis acknowledgement follows durable effect or an explicitly governed terminal poison
path; it never proves transition completeness.

## Terminality And No-Reopen Rules

- An expired, cancelled, failed, superseded, rejected, indeterminate, revoked, deleted, or
  completed domain outcome never becomes active again by editing the same record.
- Retry creates a new attempt; rollback creates a new activation transition; renewed rights
  create new reviewed state/authorization; corrected content creates a new version.
- Cache refresh, replica catch-up, Redis replay, provider fallback, reconnect, process restart,
  backup restore, clock step, or operator UI state cannot decrease an epoch or clear a terminal
  restriction.
- A terminal decision may be superseded only through a separately named, human-approved appeal
  or correction model that preserves the original record. No such model is selected here.
- Deletion and legal hold operate on content/retention axes; neither rewrites a historical safety
  verdict. Content unavailability still prevents new use.
- Publication withdrawal or takedown does not erase original authorization/evidence; prior
  publication does not authorize republishing.

## Retention, Hold, Deletion, And Restore

No duration is selected by this catalog.

1. Every record and content object has a named retention class and authority.
2. Metadata, restricted content, audit evidence, event history, derived data, media, and public
   archive may have different policies.
3. Legal hold or incident preservation blocks physical deletion where law/policy requires, but
   it does not make content eligible for generation, retrieval, synthesis, replay, or
   publication.
4. Deletion records a case and disposition; silent row removal is insufficient for protected
   data.
5. Derived caches, embeddings, indexes, provider copies where controllable, local stage-host
   data, backups, and replicas have explicit convergence evidence.
6. A restored backup remains quarantined until current tombstones, holds, revocations,
   activations, epochs, rights, and policy are reapplied.
7. A tombstone retains only accepted minimum evidence and never a reversible raw or low-entropy
   digest.
8. Audit correction or legally required redaction is an append-only disposition with protected
   original handling; it is not an untracked rewrite.

## Schema Realization Gate

No catalog family may be implemented until:

- the Runtime Implementation Gate authorizes the exact increment;
- its governing ADRs are Accepted or replaced and every required Open Decision has a valid
  closure-capable disposition for the same immutable reviewed subject;
- OD-034 disposition identifies the exact catalog rows and state axes authorized, with
  uncovered rows explicitly OPEN and disabled;
- field-level classification, content/evidence separation, access capabilities, retention,
  deletion, hold, restoration, residency, encryption, backup, and provider-copy inventory is
  protected-reviewed;
- a linked migration ADR maps each conceptual record to physical ownership, constraints,
  transaction boundaries, RLS/access enforcement, indexes/partitions, encryption, backups,
  restore, rollback, and deletion convergence;
- CODEOWNERS covers the concrete implementation paths and remote protected CI is evidenced;
- contracts and events are generated only from accepted reviewed sources under ADR-002 and
  ADR-023.

Schema review must reject a table or document that combines viewer-memory content with audit,
stores raw generated text in TTS/media tasks, permits `ApprovedResponse` construction outside
`packages/safety`, treats Redis as history, or makes `stage-host` optional.

## Required Validation

Authorized implementation must provide:

- cardinality, unique-binding, immutable-version, digest, foreign-reference, exact decision, and
  no-reopen constraint tests;
- safety factory/database negatives for unselected, cross-turn, missing/stale selection,
  concurrent selection-versus-mint, and post-mint selection mutation;
- concurrency/property tests for turn attempts, safety decisions, approval minting, activation
  epochs, rights/revocation, deletion/hold, publication disposition, current timer-claim-pointer
  CAS, ordinary effect attempt/observation/application cardinality, and recovery-probe
  intent/attempt/observation/disposition cardinality; probe storage/discriminator
  non-relabeling; exact active+draining-prefix and recovering+recovery-attempt/source binding;
  every crash cut; zero-attempt terminalization; stale-fence successor terminalization without
  resend; finite count/byte/rate/age/concurrency; non-widening/absence/replay negatives; terminal
  unknown evidence separated from source classification; and final-close rejection until every
  probe is terminal and every bound source is resolved, permanently safe-quarantined, or
  accountably disposed;
- transaction-abort tests proving state/audit/outbox and approval/content evidence cannot
  partially commit;
- stale cache, replica, event, epoch, task, journal, and backup-restore tests;
- content-leakage tests across audit, event, log, metric, trace, dead-letter, exception, fixture,
  and support export paths;
- access and separation-of-duties tests for content, evidence, audit, memory, rights, activation,
  deletion, hold, restore, and publication;
- source-delete/hold/revocation cascades through chunks, embeddings, indexes, caches, providers,
  media, archive, local stage-host state, backups, and rehydration;
- proof that missing/held/deleted/corrupt approved content prevents synthesis/replay/export, that
  no authorized code or resolution path can use archive/media to rehydrate approval or substitute
  for the canonical snapshot, and that every in-scope semantic copy follows its own deletion,
  hold, rights, retention, and publication disposition;
- outbox duplicate, reorder, gap, poison, replay, claim-expiry, and consumer atomic-effect tests;
- incident reconstruction from exact versions, snapshots, decisions, epochs, events, and
  minimized evidence without mutable labels or current configuration;
- migration upgrade, rollback, restore, and schema-diff gates linked to the accepted migration
  ADR.

## OPEN Decisions

- OD-034 must accept or replace the record families, orthogonal axes, authority boundaries,
  cardinalities, and no-reopen rules for the exact implementation scope.
- OD-014 must accept ADR-025's structural ownership, command, effect, timer, restrictive-control,
  and recovery policy before those record families are realized.
- OD-021 must define the canonical non-event command/control/acknowledgement/reconciliation
  contracts and code-generation boundary.
- OD-029 must define non-rollback recovery generation/high-water, PITR/lost-tail completeness,
  deny-only ledger limits, restored fencing, and failover/failback authority before any restore
  or continuity scope is enabled.
- OD-035 and OD-037 must define every lease/deadline/clock and queue/claim/materialization/
  retry/recovery-drain bound represented by these records.
- OD-009 must define retention durations, deletion SLAs, holds, backups, residency, and evidence
  treatment by data class.
- OD-022 must define human/workload capabilities, separation of duties, emergency authority,
  access reviews, and restore/publication authority.
- Open Decisions OD-023, OD-024, and OD-025 must settle surface, voice-rights, media, restricted
  generation, and approved-content policy.
- OD-026 must settle viewer/character memory, identity linkage, provenance, extraction,
  retrieval, derived data, and deletion.
- OD-032 must settle archive, recording, replay, clip, export, publication, incident evidence,
  and takedown semantics.
- OD-033 must settle event subject/catalog mapping, compatibility, ordering, classification,
  replay, and retention.
- Exact schema names, database constraints, transaction isolation, storage topology, RLS,
  encryption/keying, indexes, partitions, archival tiers, tombstone content, and restore
  procedures require later protected decisions.
