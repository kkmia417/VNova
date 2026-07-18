# Production Implementation Roadmap

Status: Active planning sequence; non-authorizing

This roadmap orders work only. A phase heading, exit criterion, or completed earlier phase grants
no authority that `AGENTS.md`, an ADR, an OPEN decision, protected review, or a migration gate
withholds.

This roadmap delivers VNova in reviewable vertical increments. Each increment is production-quality within its enabled scope; "later" means disabled or absent, never silently incomplete.

The feature-specific ADR gates in the [gap analysis](review-gap-analysis.md#feature-specific-adr-gates) govern every phase even when a phase repeats only its nearest entry gates. Closing the architecture-foundation gate does not authorize a later capability whose own ADR remains Proposed or absent.

Reviewers use the
[architecture foundation packet](../governance/architecture-foundation-review.md) first and the
[feature architecture packet](../governance/feature-architecture-review.md) for the later
capability decisions. The feature ADRs are now present as review-ready proposals; none is accepted
merely because it has been drafted.

## Current Gate State

| Gate set                    | Current state                                                                                                                                 | Effect                                                                                                                            |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Foundation authority        | OD-019, protected human review, remote CI, Ruleset, and independent ownership remain pending                                                  | Runtime implementation remains blocked                                                                                            |
| Accepted topology/privacy   | ADR-016 and ADR-017 are Accepted; ADR-026 proposes a narrow audit-reference correction; numeric, security, and retention parameters stay OPEN | They constrain review but do not independently authorize a feature or affected persistence                                        |
| Foundation proposals        | ADR-001, ADR-002, ADR-008, ADR-018, and ADR-023 await one compatible protected review                                                         | Current scaffold and event model remain quarantined review evidence                                                               |
| Session execution proposals | ADR-003 and ADR-025 await compatible review; OD-014/035/037 remain pending                                                                    | Session actors, durable command ingress, effect fencing, timers, scheduler, and lifecycle persistence remain blocked              |
| Feature proposals           | ADR-004, 007, 010, 011, 015, 019 through 022, and 024 await review                                                                            | Their named production capabilities remain blocked                                                                                |
| Domain/operations proposals | Identity/lifecycle, activation, observability, capacity/cost, and load/soak/chaos models are Proposed; OD-033 through OD-039 remain pending   | No schema realization, event activation, config activation, production telemetry, capacity/cost policy, or resilience pass exists |
| Operational/security design | Threat model and runbooks are Proposed and Drafted only; OD-027 through OD-032 and OD-036 through OD-039 remain pending                       | No live-operation, recovery, privacy, release-integrity, performance/resilience, or production security authorization exists      |
| Historical decision record  | Original architecture source and ADR-006 are absent                                                                                           | OD-008 and OD-020 require restoration, acceptance, or explicit retirement/remap                                                   |
| Decision authority          | OD-040 and the disposition register are Proposed; no effective rows exist                                                                     | No OPEN decision may be treated as closed                                                                                         |

## Phase 0: Architecture Foundation And Governance

Exit criteria:

- Runtime Implementation Gate in `AGENTS.md` is satisfied.
- Canonical contract source and generation direction are unambiguous.
- ADR-002 and ADR-023 define one accepted complete event-contract identity, typed
  scope/subject, ordering/completeness, trusted version framing, compatibility, privacy
  protection, and recovery model for the same immutable review subject.
- Safety minting and identifier-only media boundaries have an accepted enforcement ADR.
- CODEOWNERS and a repository-rules/CI plan exist.
- OPEN decisions have owners, recommendations, and explicit blocking scope.
- OD-040's one-time genesis is validly ratified, and every foundation-blocking OD has a complete
  disposition for the same immutable reviewed subject.
- The authoritative gate amendment, exact external machine inventory, pre-decision semantic
  overlay, frozen review-package manifest, final protected disposition/effectiveness records,
  immutable review subject, base-branch ownership bootstrap and decision projection, remote
  CI/negative-control evidence, and non-author approval are accepted under OD-019.

No feature code is allowed in this phase.

## Phase 1: Reproducible Monorepo And Contract Toolchain

Exit criteria:

- Pinned Python and TypeScript toolchains with lockfiles.
- Deterministic JSON Schema validation and Python/TypeScript code generation.
- Shared valid/invalid contract fixtures pass in both languages.
- Import-linter, dependency-cruiser, Python AST, and TypeScript compiler-AST protected-symbol checks run locally and in CI.
- Stable required-check aggregation is documented and implemented.

## Phase 2: Safety-Critical Domain And Persistence

Entry gates: accepted ADR-002, ADR-003, ADR-004, ADR-008, ADR-017, ADR-019, ADR-023, ADR-024,
ADR-025, and ADR-026 for persistence that stores or references deletable viewer data; an inherited
still-valid OD-033 disposition for the exact event profiles; a separate
OD-034 disposition naming the exact realized lifecycle-catalog rows and referencing that
inherited dependency; OD-014 acceptance of the structural ownership/scheduling profile; an
applicable OD-022 disposition for every operator or trusted-source command family realized;
protected review of the
[domain record lifecycle catalog](domain-record-lifecycle-catalog.md); and a linked migration
ADR.

Exit criteria:

- Stable roots, non-selectable drafts, immutable definition/set versions, monotonic eligibility
  states/epochs, explicit inactive/active scoped activation state/epochs, non-effective schedules,
  resolved snapshots, PostgreSQL-authoritative session ownership/transitions and monotonic
  normal-work admission/closure-drain cuts, durable command intents/receipts/outcomes and
  append-only authorization observations, canonical trigger
  occurrences/materialization cursors/current claims/firing dispositions, effect
  intents/send-authorized attempts/response observations/application dispositions, recovery
  cuts/barriers/history-completeness dispositions, restrictive-control delivery evidence, turns,
  candidates, safety decisions, durable
  approval/approved-content snapshots, and audit models exist.
- The recovery/ownership composite actor fence, shared ownership-row conflict, fresh post-conflict
  database time, fixed lock order, and aggregate version jointly protect every normal session
  transaction; no read predicate, receipt, heartbeat, process identity, or Redis record
  substitutes for authority.
- PostgreSQL constraints make invalid approval chains unrepresentable.
- Transactional outbox and replayable domain event log are tested.
- Viewer/character memory, knowledge, restricted generation/approved content, archive, telemetry,
  and audit storage/roles are structurally separated according to accepted scope.
- Complete event-contract identities, typed scope/subjects,
  `(aggregate_version, event_index)` lanes, transition-manifest/expected-delivery high-water,
  trusted envelope-version framing, correlation/causation, authorization, restrictive protection
  overlays, and compatibility follow accepted ADR-023/OD-033.
- Semantic terminality, content availability, retention/hold, use eligibility, publication, and
  delivery are independent axes; archive/media cannot rehydrate or mint approval or substitute
  for the canonical approved-content snapshot.

## Phase 3: Provider-Neutral Runtime Core

Entry gates: ADR-003, ADR-019, ADR-024, and ADR-025 accepted for the exact
runtime/configuration/command scope; OD-014 accepted for trigger, scheduling, effect, and
takeover policy; an applicable OD-022 disposition for every command principal/source and
authorization behavior realized; and the applicable OD-034/035/037 profiles decided. Live
provider SDKs, credentials, and cost/quota enforcement remain disabled pending ADR-007, OD-038,
and protected-path review.

Exit criteria:

- One logical actor per stream session, proven by exact recovery/ownership composite fence,
  closed vacant/recovering/active/closed phases, bounded lease, shared ownership-row
  linearization, and recovery-only takeover.
- Durable submission-generation-bound command receipt/outcome, universal expiry, deterministic
  state machine, protected idempotency-key scope with immutable semantic-digest conflict,
  append-only initial/refreshed authorization observations, current policy/revocation-epoch
  selection with deterministic precedence and authorization-lineage revision CAS, current
  receipt/outcome disclosure authorization, retryable-ineligible versus nonretryable-terminal
  denial, monotonic normal-work admission and bounded pre-close drain across every command
  claim/execution/widening-outcome, viewer/platform/director/content-scheduler input, timer/Turn,
  ordinary effect-intent/send/advance, and
  candidate/selection/approval/media/task/signing/dispatch progression; distinct four-role
  recovery probes under active+draining-prefix or recovering+recovery-attempt/source binding,
  with zero-attempt terminality, originating-fence provenance/current-successor close without
  resend, finite bounds, terminal-unknown/source-classification separation, and no widening;
  atomic `ended`/`cancelled`/`failed` session/admission/ownership final close with no earlier
  lifecycle terminal row, no nonterminal probe, and every bound source ambiguity resolved/
  permanently safe-quarantined/accountably disposed; canonical active-owner-only timer materialization,
  recovering-owner no-create/no-cursor-advance, at most one Turn and terminal firing disposition
  per occurrence, current-claim fencing, closed recovery activation barrier with immutable
  cut-time frontiers/schedule-cursor snapshots, excluded post-cut operational cursor, probe-write
  invalidation, and terminal-probe/enabled-source-resolution gate; content scheduler,
  non-extensible candidate deadline, protected reserves, admission, and backpressure.
- Mock gateways cover intent-before-effect, send-authorization/first-byte,
  response-observation/application, remaining-lease budget, distinct four-role bounded recovery
  probes, timeout, retry/fallback, cancellation, possibly-sent, late result, takeover, and
  correlated failure.
- Process pause, partition, database-response loss, stale composite actor, immutable
  source-frontier/cut-time-cursor versus excluded operational-cursor activation/no-starvation
  races, ambiguity/restriction invalidation, command
  receipt/refreshed-authorization/claim/execution/widening-outcome,
  every viewer/platform/director/content-scheduler input, timer materialization/claim/firing,
  Turn, ordinary effect intent/send/application, and
  candidate/selection/approval/media/task/signing/dispatch progression versus begin-close;
  authorization observation append/selection/disclosure/denial crash cuts; recovery-probe
  intent/attempt/first-byte/response/disposition crash cuts, zero-attempt and stale-fence
  successor terminalization/no-resend, dual-binding/bounds/non-widening/source-axis tests,
  probe-write-versus-activation races, final-close/revoke/relinquish/takeover races for every
  terminal target; PITR-lost
  close cuts across restored `open`, `draining(normal_closure)`, and atomic `closed`, including
  lifecycle/admission coherence, monotonic lost-tail overlay, and unresolved-target final-close
  rejection; duplicate command/timer; and every effect crash boundary prove no split-brain
  progression, post-begin-close-cut ordinary creation/advancement, credential-lineage overwrite,
  early lifecycle terminality, or terminal command/session reopen while bounded evidence and
  terminal non-advancing drain remain available.
- No live provider credential is required for the full lifecycle test.

## Phase 4: Safety Gate And Supervised Production Mode

Entry gates: ADR-008, ADR-020, and the applicable ADR-024 configuration/policy scope accepted.
Any persistence changes also require the applicable migration ADR.

Exit criteria:

- Deterministic rules, independent model classification gateway, and policy engine are layered in order.
- Fail-closed and rewrite-loop behavior pass fault injection and red-team regressions.
- Mode 0/1 transition and operator approval paths are fully audited.

## Phase 5: Approved Media Pipeline And Rehearsal Rig

Entry gates: ADR-007, ADR-008, ADR-010, ADR-011, ADR-018, ADR-021, ADR-022, and applicable
ADR-024 configuration families plus ADR-025 signing/dispatch fencing accepted;
OD-021 decided for the non-event `SpeechTask`/control contract; an applicable migration ADR
accepted before persistence work; implementation-required cryptographic parameters approved; and
the applicable OD-034/035 content-resolution, retention, expiry, and clock profiles decided.

Exit criteria:

- Identifier-only TTS/media flow, artifact integrity, and signed `SpeechTask` contract.
- Server-side signing/dispatch rejects stale composite actor fences through the shared
  ownership-row conflict. Administrative revoke atomically creates restrictive epoch/hold/
  priority-control intent, and ambiguous takeover uses sealed rig reconciliation before
  activation.
- Fake OBS, fake VTube Studio, virtual audio sink, deterministic clock, and fault controls.
- Expiry is enforced immediately before playback.
- Rehearsal e2e reconstructs the complete incident timeline.

## Phase 6: Stage Host Safety Runtime

Entry gates: ADR-011, ADR-015, and ADR-020 accepted; OD-021 decided for the stage-host non-event
protocol; OD-035/037 decided for clock/deadline/watchdog timing and local queue/journal resource
bounds; stage-host language, protocol security profile, e-stop SLO, and watchdog policy approved
by a human. Production signal/alert behavior remains disabled until OD-036 is decided and
target-validated.

Exit criteria:

- Local queue, authenticated cloud link, signature/replay checks, offline log buffer, raw
  clock/offset/uncertainty evidence, and conservative local-monotonic deadline enforcement.
- Local hard e-stop and disconnect watchdog pass tests with cloud loss.
- Live adapters remain disabled until separate protected-path review and simulator parity pass.

## Phase 7: Live Platform Ingestion

Entry gate: platform choice approved.

Exit criteria:

- Input normalization, moderation, deduplication, rate limiting, backpressure, gap detection, and username screening.
- Flood and injection tests pass without starving safety or operator control paths.

## Phase 8: Operator Console And Authorization

Entry gates: ADR-019, ADR-020, and ADR-015 accepted. Manual-speech behavior also requires the relevant safety and broadcast-surface decisions.

Exit criteria:

- Internal-only console, server-side authorization, approval SLA, mode controls, manual speech, and layered e-stop controls.
- Dangerous commands are idempotent and audited; stop has no confirmation and resume requires confirmation plus reason.
- Every accepted session command has a durable receipt and one queryable terminal outcome;
  response loss remains unknown until same-intent reconciliation.

## Phase 9: Production Integrations And Live Readiness

Entry gates: ADR-007 accepted for live providers; ADR-011, ADR-015, ADR-021, and ADR-022
accepted where their corresponding live surfaces are enabled; protected adapter and gateway
reviews complete; OD-027 and OD-028 plus applicable OD-029 through OD-039 approved for the target.

Exit criteria:

- Human-reviewed provider gateways and OBS/VTube Studio adapters.
- The exact immutable target passes the
  [load, stress, spike, soak, chaos, and recovery acceptance contract](../governance/load-soak-chaos-acceptance.md),
  plus security, privacy-deletion, backup/restore, and disaster-recovery exercises.
- Versioned SLI/telemetry/alert contracts, alert-route delivery, monitoring-loss response,
  protected reserves, admission/shedding, cost/quota controls, backlog drain, and deployment
  rollback are rehearsed and target-validated.
- Applicable runbooks progress from `Drafted` through `Rehearsed` and `Target-validated`, with
  sanitized evidence in the operational readiness packet.
- Personal-data breach, privacy deletion/restore, supply-chain/release compromise, and disaster
  recovery/continuity exercises pass for every capability and data path that depends on them.
- Actor split-brain, lease expiry, ownership-row/revoke ordering, command-response loss,
  possibly-sent effect, timer materialization/current-claim races, recovery activation-frontier
  change, restrictive-dispatcher loss, stage-host dispatch ambiguity, PITR lost-tail, failover,
  and failback exercises pass with one current authority and no automatic stale replay.
- Telemetry/alerting degradation and resource exhaustion/backpressure runbooks pass containment,
  evidence, deliberate recovery, and exit criteria for the exact target.
- A protected operational-readiness decision and release-readiness review authorize the exact
  supervised capability and deployment.

## Phase 10: Progressive Autonomy

Higher autonomy is enabled by evidence, not schedule. Each upward mode requires explicit
preconditions, operator-presence enforcement, red-team coverage, production telemetry, and a
reversible rollout. The repository-wide threat model does not authorize tool use; tool use remains
out of scope until a dedicated threat model and ADR are approved.
