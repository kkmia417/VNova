# VNova Review Gap Analysis

Status: Updated architecture-foundation assessment

Source: [external architecture review handoff](../../vnova-review-handoff.md)

## Scope Limitation

The original VNova architecture document referenced by the external review is not present in this repository. This analysis therefore compares the handoff's description of the original direction with the binding review decisions and the current repository.

That limitation is explicit rather than silently waived. OD-008 requires either importing the original design or human acceptance of this handoff-derived baseline.

## Baseline Inferred From The Review

The original direction had the correct core safety instinct: `CandidateResponse` and `ApprovedResponse` were distinct and unsafe candidate text had to cross a mandatory gate before speech.

The review identified these gaps:

- Local broadcast hardware topology was not modeled explicitly.
- The turn model was too chatbot-shaped for continuous broadcast.
- The safety gate lacked enforceable mechanics.
- Latency and candidate-expiry budgets were undefined.
- Privacy, APPI posture, deletion, and retention were undefined.
- Five planes could be misread as five deployed services.
- Broadcast surfaces beyond voice were not inventoried.

## Binding Corrections Incorporated

1. A required local `stage-host` is the sole `SpeechTask` consumer.
2. Local hard e-stop works when cloud connectivity is absent.
3. `CandidateResponse` remains unsafe and structurally separate from `ApprovedResponse`.
4. Only `packages/safety` may mint an approval.
5. TTS/media public interfaces accept `approved_response_id`, never raw generated text.
6. Every primary, retry, rewrite, and fallback route crosses the same safety gate.
7. Safety unavailability fails closed.
8. Redis Streams is transport only; PostgreSQL is the system of record.
9. Viewer memory and audit data are separate in content, storage, and access role.
10. The handoff requires planes to be module boundaries rather than deployables, but the
    taxonomy remains unresolved under OD-018; only explicit named boundaries are enforceable.
11. Rehearsal mode uses fake OBS, fake VTube Studio, and a virtual audio sink.
12. Every broadcast surface, including spoken usernames, is moderated.

## Runtime Implementation Gate

The gate in `AGENTS.md` is distinct from later feature-specific ADR gates.

| Gate artifact                           | Current state                                                                                                                        | Remaining action                                                                                                  |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| ADR-016                                 | Present, Accepted                                                                                                                    | Human review of future protocol/e-stop details                                                                    |
| ADR-017                                 | Present, Accepted                                                                                                                    | Retention values and deletion SLA remain OPEN                                                                     |
| ADR-026 privacy correction proposal     | Present, Proposed                                                                                                                    | Protected privacy/security review before affected persistence; does not silently amend ADR-017                    |
| ADR-018                                 | Present, Proposed                                                                                                                    | Accept binding clauses; SLOs and freshness/clock values remain independently OPEN                                 |
| ADR-023 foundation companion            | Present, Proposed                                                                                                                    | Accept with ADR-002 or replace after OD-017/033 dispositions; synchronize the exact gate amendment                |
| Updated system overview                 | Present, Draft                                                                                                                       | Human architecture review                                                                                         |
| Gap analysis                            | Present                                                                                                                              | Resolve original-source limitation or accept it                                                                   |
| Protected safety-boundary evidence      | Quarantined non-runtime mint placeholder plus enforcement tests                                                                      | Candidate-bound inventory/pre-decision-overlay/final-attestation review before domain implementation              |
| Executable contract-foundation evidence | Quarantined envelope/full-event validators, active-only registry, deterministic Python/TS codegen/distribution, packaging, and tests | Resolve OD-019 and review every executable behavior before incremental payload work                               |
| Event schema/catalog evidence           | Quarantined envelope and required-event catalog; generated active set is empty and every full-event validation fails closed          | Resolve OD-017/033 and add governed payload schemas/fixtures incrementally                                        |
| Review ownership                        | Candidate `.github/CODEOWNERS` exists only in the worktree                                                                           | Land it on the base branch through the bootstrap ceremony; add an eligible non-author reviewer/team               |
| CI enforcement plan                     | Candidate cross-platform quality/artifact workflow, pinned security job, self-check, and stable aggregate exist only in the worktree | Freeze an immutable candidate, run remotely on its exact SHA, prove a negative control, and configure the Ruleset |

The authoritative gate is not yet closable: the current `AGENTS.md` pre-gate allowlist does not
authorize the complete executable scaffold now present in the worktree, and neither CODEOWNERS nor
CI is active on the base branch. OD-019 and the
[foundation authority/bootstrap proposal](../governance/foundation-authority-and-bootstrap-proposal.md)
and
[`VNOVA-FOUNDATION-STAGE-A-HANDOFF-v1`](../governance/foundation-stage-a-review-handoff.md)
define an exact non-self-authorizing amendment, governance-only path/status/mode allowlist,
external machine inventory, pre-decision semantic overlay, frozen review-package manifest, final
external attestations/effectiveness witness, immutable candidate, decision projection, and staged
protected review.
Feature code remains blocked. Provisional Stage B JSON-profile limits are implemented only as
quarantined contract evidence; production numeric and policy profiles remain unapproved while
their decisions are OPEN.

## Source-Of-Truth Resolution

The current repository skeleton applies the following working split, and proposed ADR-002 asks human review to make it binding:

- `specs/events` is the sole hand-authored event JSON Schema and event-catalog source.
- `packages/contracts` owns deterministic generators, validators, and generated Python/TypeScript libraries.
- FastAPI OpenAPI becomes the HTTP authoring source once the API exists; normalized and generated artifacts are checked for drift.

## Safety Enforcement Design

Proposed ADR-008 specifies independent layers for human review:

- private mint implementation and capability;
- import-linter plus Python AST and TypeScript compiler-AST symbol enforcement;
- identifier-only TTS/media type contracts;
- PostgreSQL approval-chain constraint;
- authoritative `not_after` propagation;
- signed, session-bound, artifact-bound, replay-resistant `SpeechTask`;
- stage-host acceptance and immediate pre-playback checks;
- CODEOWNERS, fail-closed fault injection, and red-team tests.

No runtime safety engine or database schema has been added. The current `packages/safety` code is a non-runtime boundary scaffold used to prove exclusive mint ownership.

## Remaining Domain Design

Before safety-critical persistence work:

- Review the [domain and information model](domain-information-model.md), Proposed ADR-024, and
  the [domain record lifecycle catalog](domain-record-lifecycle-catalog.md). Close OD-034 only
  for exact catalog rows whose draft/immutable-version boundaries, definition/set eligibility
  epochs, atomic explicit activation/deactivation/schedule semantics, content/evidence
  separation, memory/knowledge, archive/publication, access, retention, deletion/hold/restore,
  and terminal lifecycles are accepted; uncovered scope remains disabled.
- Review proposed ADR-003 and its broadcast session, segment, and turn lifecycle model.
- Review proposed ADR-025 and the
  [session runtime execution model](session-runtime-execution-model.md). One logical actor must
  mean an exact protected recovery/PostgreSQL-ownership composite fence, shared ownership-row
  linearization, monotonic normal-work admission and atomic closure across every input/Turn
  source, submission-generation-bound command receipts and append-only authorization
  observations, four-record ordinary-effect crash boundaries, a distinct four-role bounded
  `RecoveryProbe*` lineage, canonical timer/current-claim fencing, a source-serialized recovery
  barrier with immutable cut-time frontier/schedule-cursor snapshots and a separately excluded
  operational cursor, and sealed stage-host reconciliation—not a process route, heartbeat, Redis
  lock, read predicate, or aggregate version alone. Every recovery-attempt-bound probe write must
  invalidate the activation candidate; activation and final close must independently prove probe
  terminality and the required disposition of each bound source ambiguity.
- Accept or refine its directional cardinality model: a turn owns `0..N` attempts and candidates,
  every existing attempt/candidate belongs to exactly one turn, and selection, terminal-decision,
  and rewrite lineage remain explicit.
- Accept or refine its separation of e-stop session state/events from text-safety verdicts.
- Resolve approved-content availability after raw candidate expiry/deletion, including
  classification, retention, archive interaction, and fail-closed resolution.
- Approve exact schemas, constraints, encryption, roles, retention, deletion, concurrency, and
  migration design through a linked schema ADR before any migration.

## Remaining Event Design

The envelope and required type catalog exist, but no catalog entry is active. Generated
Python/TypeScript publishable-event APIs therefore reject every input after envelope validation;
envelope-only success grants no producer or consumer authority. Each type needs a reviewed payload
schema plus valid/invalid fixtures before a producer or consumer may use it.

The current envelope requires `stream_session_id` for every fact, while required
policy/prompt-activation and memory operations may be environment-, talent-, character-, or
viewer-scoped without an active session. This is a P0 contract blocker, not a request to invent a
session ID or make one field casually nullable.

Proposed ADR-023 and the
[scope and subject identity model](scope-and-subject-identity-model.md) select one v2 domain-event
envelope with trusted version framing, a complete immutable event-contract identity,
catalog-fixed typed primary scope, one aggregate subject,
`(aggregate_version, event_index)` ordering, transaction manifest/authorized expected-delivery
high-water completeness, correlation/causation, restrictive protection overlays, and optional
session/turn correlation. Ambiguous current names must be assigned one durable aggregate meaning,
split, or removed from the domain-event catalog when they are only commands, alerts, telemetry,
heartbeats, or wire observations. OD-033 must accept that model or a replacement before ADR-002
acceptance or affected event activation.

Additional stage-host playback, approval-expiry, outbox, and delivery facts must be specified
with their owning aggregate. Heartbeat, command, acknowledgement, restrictive control,
reconciliation, command receipt/outcome, execution/timer claim, effect attempt, and `SpeechTask`
remain non-event ADR-011/025/OD-021 records or contracts unless a separate semantic fact receives
an accepted ADR-023 catalog profile. Domain-event
publishers preserve aggregate-version/event-index order in each catalog-declared subject lane;
ordered consumers also prove their exact manifest subset/high-water from PostgreSQL before
advancing dependent projections. The stage-host protocol has independent session-bound
sequence/epoch rules and neither implies a global FIFO.

No catalog entry may become `active` during the envelope-only scaffold. Activation requires
OD-017 and the applicable OD-033 scope decision to be closed through accepted
compatibility/deprecation rules plus generated Python and TypeScript payload validators using the
same fixtures.

## Feature-Specific ADR Gates

These do not block the quarantined Phase 1 contract/tooling review scaffold, but they block the
named capabilities. Drafting them does not close their gates. Use the
[feature architecture review packet](../governance/feature-architecture-review.md) to record
protected decisions.

| ADR                                                                           | Status   | Required before                                                                                                       |
| ----------------------------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------- |
| [ADR-003](../adr/0003-stream-session-segment-and-turn-lifecycle.md)           | Proposed | Session actor, scheduler, attempt/candidate lifecycle, and TTL implementation                                         |
| [ADR-004](../adr/0004-postgresql-outbox-and-redis-streams.md)                 | Proposed | PostgreSQL outbox and Redis Streams event bus                                                                         |
| [ADR-007](../adr/0007-provider-gateway-and-fallback-isolation.md)             | Proposed | Live LLM/TTS provider gateway implementation                                                                          |
| [ADR-010](../adr/0010-approved-media-and-tts-pipeline.md)                     | Proposed | Approved media/TTS pipeline                                                                                           |
| [ADR-011](../adr/0011-stage-host-wire-protocol-and-clock-synchronization.md)  | Proposed | Stage-host wire protocol and synchronization                                                                          |
| [ADR-015](../adr/0015-layered-emergency-stop.md)                              | Proposed | Layered e-stop implementation                                                                                         |
| [ADR-019](../adr/0019-authentication-authorization-and-operator-roles.md)     | Proposed | Authentication, authorization, and operator console                                                                   |
| [ADR-020](../adr/0020-mode-transition-and-degradation-matrix.md)              | Proposed | Mode transitions and autonomous degradation                                                                           |
| [ADR-021](../adr/0021-broadcast-surface-inventory-and-overlay-policy.md)      | Proposed | Broadcast surfaces and any chat overlay                                                                               |
| [ADR-022](../adr/0022-voice-rights-and-talent-licensing-metadata.md)          | Proposed | Voice profile, rights, and licensing metadata                                                                         |
| [ADR-024](../adr/0024-versioned-configuration-and-scoped-activation.md)       | Proposed | Draft/immutable versions, eligibility, explicit activation/deactivation, schedule, resolver, and configuration schema |
| [ADR-025](../adr/0025-session-actor-ownership-command-ingress-and-fencing.md) | Proposed | Session actor ownership, durable command ingress, external-effect fencing, timers, and takeover/recovery              |

## Test, Security, And Operational Gaps

Required before their corresponding production capability:

- event-specific complete contract profiles, payload schemas, transition manifests/high-water,
  trusted version framing, restrictive protection overlays, fixtures, and generated
  Python/TypeScript parity;
- approval-chain database rejection tests;
- raw-text TTS/media boundary tests;
- safety-timeout fault injection with zero speech;
- fallback-through-gate and rewrite-loop tests;
- expiry checks through immediate pre-playback;
- signed-task substitution, replay, rotation, clock-offset uncertainty/sample-staleness, and
  conservative deadline-mapping tests;
- ownership acquire/renew/revoke/expiry/takeover row-conflict races, post-lock clock checks, and
  stale-composite-fence rejection; normal-work admission/source-CAS races across command
  receipt/auth-refresh/claim/execution/successful-or-widening outcome, viewer/platform/director/
  content-scheduler input, timer materialization/claim/firing, Turn, ordinary effect
  intent/send/application, and candidate/selection/approval/media/task/signing/dispatch
  progression; committed-prefix
  begin-close, bounded evidence/terminal non-advancing drain, frozen cursors, atomic terminal-
  target final close, and lost-close non-reopen quarantine; submission-generation command
  receipt/response-loss/key-versus-digest idempotency, authorization-observation dedupe/lineage-
  revision CAS/precedence/database-time deadline, and lookup authorization; effect
  intent/send-authorization/first-byte/response-observation/application cuts and possibly-sent
  behavior; distinct `RecoveryProbeIntent`/`Attempt`/`ResponseObservation`/`Disposition` crash
  cuts under exact active-plus-draining-prefix or recovering-plus-recovery-attempt/source binding,
  including zero-attempt terminalization, successor terminalization without resend, finite
  bounds, terminal `unknown` versus separate source classification, and no widening/absence/
  replay authority; canonical timer key, active-only materialization, recovering-owner no-create,
  current-claim/reclaim CAS, and unique terminal firing disposition; immutable recovery cut-time
  source/schedule-cursor snapshots versus the excluded operational cursor, every
  recovery-attempt-bound probe write invalidating activation, activation blocking on a
  nonterminal probe or enabled-scope unresolved source ambiguity, and final-close blocking until
  every probe is terminal and every bound source ambiguity is resolved, permanently
  safe-quarantined, or accountably disposed; restrictive-dispatcher loss; and recovery-only
  takeover/PITR lost-tail with restrictive epoch/sealed-rig reconciliation;
- local e-stop and watchdog tests with cloud loss;
- deterministic rehearsal e2e with complete timeline reconstruction;
- privacy deletion and derived-cache absence verification;
- accountable threat-model review, abuse-case validation, independent security assessment, and
  residual-risk decisions;
- rehearsed and target-validated runbooks for rig loss, silence, fail-closed, provider outage,
  e-stop, offline reconciliation, voice-rights revocation, operator identity compromise,
  personal-data breach, privacy deletion/restore, software supply-chain/release compromise, and
  disaster recovery/continuity, telemetry/alerting degradation, and resource
  exhaustion/backpressure;
- versioned signal/alert contracts, telemetry prohibited-content and capacity tests, monitoring
  loss exercises, and target alert-delivery evidence;
- representative load, stress, spike, soak, chaos, abort, recovery, backlog-drain, cost/quota, and
  protected-reserve evidence under the
  [load/soak/chaos acceptance contract](../governance/load-soak-chaos-acceptance.md).

The [threat model](../security/threat-model.md) and [runbook catalog](../runbooks/README.md) now
provide Proposed design artifacts for those gaps. Every runbook remains `Drafted`: exact commands,
alerts, contacts, thresholds, target evidence, exercises, and production authorization are still
absent. The [operational readiness packet](../governance/operational-readiness-review.md) prevents
document presence from being mistaken for operational readiness.

## Current Repository Mismatches

- The original architecture source is absent.
- The handoff's implementation sequence references ADR-006, but that ADR and enough authoritative
  topic metadata to reconstruct it are absent; OD-020 tracks restoration or explicit
  retirement/remapping.
- ADR-004, ADR-007, ADR-010, ADR-011, ADR-015, and ADR-019 through ADR-025 now exist only as
  Proposed review artifacts; none authorizes its dependent capability.
- ADR-018 numeric acceptance criteria are not approved.
- ADR-017 has no production retention durations.
- ADR-026 is a Proposed correction to ADR-017's unqualified allowance for viewer
  message/memory hashes in ordinary audit. Until protected review resolves it, no implementation
  may treat a content-derived viewer-data digest as a privacy-safe foundation primitive.
- Accepted ADR-017 still uses the legacy term `MVP` for its pgvector scope while the repository
  defines a production baseline rather than a disposable MVP. OD-026 requires protected human
  clarification of both terminology and the underlying vector-storage scope; this analysis does
  not edit the Accepted ADR silently.
- ADR-002 does not yet define a canonical authoring and code-generation source for non-event
  WebSocket/command contracts or a future non-Python/TypeScript stage-host language; OD-021 tracks
  that contract gap.
- The event envelope and required non-session catalog facts have incompatible subject/scope and
  completeness semantics. ADR-023's v2 complete-contract/framing/manifest/protection model is a
  Proposed resolution only; OD-033 still blocks ADR-002 and ADR-023 acceptance and affected event
  activation.
- The domain/lifecycle, configuration activation, observability, capacity/cost, and
  load/soak/chaos documents are Proposed review artifacts. OD-034 through OD-039 retain every
  realization and production gate.
- The previous one-logical-actor statement had no closed lease, fencing, normal-work
  admission/closure, command-ingress authorization handoff, external-effect, timer, takeover,
  activation-frontier, administrative-revoke delivery, or lost-tail model. ADR-025 is the
  Proposed structural resolution; OD-014/021/022/029/033-035/037, a linked migration ADR, and
  protected implementation review remain unresolved.
- CODEOWNERS exists only in the uncommitted candidate, is not on the base branch, and currently has
  only a bootstrap individual owner; it cannot yet provide independent review.
- The candidate CI workflow has not run remotely, no immutable candidate SHA/PR exists, and no
  GitHub Ruleset requires `ci-required` or has proven a failing negative control.
- No application runtime, database migration, provider integration, or production red-team corpus exists yet.
- The threat model has no accountable residual-risk acceptance or independent assessment, and no
  runbook has rehearsal, target-validation, or production-authorization evidence; OD-027 through
  OD-032 track the applicable human decisions.
- The historical five-plane taxonomy is unnamed and cannot be used as an enforceable boundary until OD-018 is closed.
- The pre-gate edit allowlist and scaffold prerequisites in `AGENTS.md` conflict; OD-019 requires
  the exact authoritative amendment and bootstrap ceremony before this scaffold can merge or
  runtime work can begin. A review-table ruling alone is insufficient.
- OD outcomes have no human entries yet. The
  [Proposed disposition register](../governance/open-decision-dispositions.md) and OD-040 require
  an immutable subject, eligible non-author review, selected outcome, retained OPEN scope, and
  reconciled authority before any item can be treated as closed.

## Open Decisions

All human-owned choices, recommendations, and blocking scopes are tracked as OD-001 through
OD-040 in the [open decision register](open-decisions.md). There are currently no effective
dispositions.
