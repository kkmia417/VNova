# VNova Threat Model

Status: Proposed security review artifact; readiness state: `Drafted`; no implementation,
production enablement, risk acceptance, legal conclusion, or incident authority is granted by this
document

Governing sources:

- [`AGENTS.md`](../../AGENTS.md)
- [`vnova-review-handoff.md`](../../vnova-review-handoff.md)
- [ADR-007: provider gateway and fallback isolation](../adr/0007-provider-gateway-and-fallback-isolation.md)
- [ADR-008: safety gate enforcement](../adr/0008-safety-gate-enforcement.md)
- [ADR-010: approved media and TTS pipeline](../adr/0010-approved-media-and-tts-pipeline.md)
- [ADR-011: stage-host wire protocol and clock synchronization](../adr/0011-stage-host-wire-protocol-and-clock-synchronization.md)
- [ADR-015: layered emergency stop](../adr/0015-layered-emergency-stop.md)
- [ADR-016: stage-host and cloud/local topology](../adr/0016-stage-host-and-cloud-local-topology.md)
- [ADR-017: data retention, privacy, and PII](../adr/0017-data-retention-privacy-and-pii.md)
- [ADR-026: opaque audit references for deletable personal data](../adr/0026-opaque-audit-references-for-deletable-personal-data.md)
- [ADR-019: authentication, authorization, and operator roles](../adr/0019-authentication-authorization-and-operator-roles.md)
- [ADR-020: mode transition and degradation matrix](../adr/0020-mode-transition-and-degradation-matrix.md)
- [ADR-021: broadcast surface inventory and overlay policy](../adr/0021-broadcast-surface-inventory-and-overlay-policy.md)
- [ADR-022: voice rights and talent licensing metadata](../adr/0022-voice-rights-and-talent-licensing-metadata.md)
- [ADR-023: event subject, scope, correlation, and ordering lanes](../adr/0023-event-subject-scope-correlation-and-ordering.md)
- [ADR-024: versioned configuration and scoped activation](../adr/0024-versioned-configuration-and-scoped-activation.md)
- [ADR-025: session actor ownership, command ingress, and fencing](../adr/0025-session-actor-ownership-command-ingress-and-fencing.md)

This model separates architectural requirements from accepted implementation evidence. Most
feature ADRs above remain `Proposed`; naming a control here does not authorize or prove that
control. Production risk acceptance remains a protected human decision.

## Scope And Security Objectives

The scope is one VNova production environment from platform input through cloud processing,
operator control, approved media creation, authenticated dispatch, local rendering, audit,
retention, and deletion. It includes rehearsal components because rehearsal must exercise the
same safety and authorization contracts as live operation.

The primary objectives, in priority order, are:

1. prevent unapproved, unauthorized, expired, substituted, or replayed content from reaching any
   broadcast surface;
2. preserve an independent local ability to stop audience output when cloud control is lost;
3. prevent compromised identities, providers, renderers, or transports from widening authority;
4. make rights, policy, content, surface, session, and artifact provenance independently
   verifiable;
5. protect secrets, restricted generation data, viewer data, voice data, and legal evidence;
6. reconstruct security and safety incidents without copying protected content into ordinary
   telemetry;
7. fail toward silence, a reviewed neutral state, a lower autonomy mode, or emergency stop when
   authority cannot be proved.

Availability and latency are subordinate to these objectives. This model does not claim that
VNova can remain available through every dependency or rig compromise.

## Protected Assets

| Asset                            | Required property                                                                          | Examples of compromise                                                        |
| -------------------------------- | ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------- |
| Audience output                  | Only exact, current, authorized presentations reach the audience                           | Unsafe speech, raw chat, substituted captions, malicious scene action         |
| Approval capabilities            | Sole mint ownership, immutable lineage, expiry, and non-serialization                      | Forged `ApprovedResponse`, `SurfaceAuthorization`, or `VoiceUseAuthorization` |
| Safety and authorization policy  | Version integrity, reviewed activation, deterministic evaluation                           | Downgraded policy, hidden allow rule, stale policy reuse                      |
| Operator and workload identity   | Strong authentication, least privilege, scoped provenance, revocation                      | Stolen operator session, forged workload, rig impersonation                   |
| Session and emergency state      | Ordered, durable, monotonic restrictive transitions                                        | Old epoch revival, stop bypass, automatic resume                              |
| Session actor and work authority | One composite fence, row-linearized commits, durable receipts/effects/timers/recovery cuts | Split brain, stale commit, lost/replayed work, unsafe recovery                |
| Recovery history completeness    | Restored authority never infers an unproven tail absent                                    | PITR reaccepts a lost command, replays an effect, or rematerializes a timer   |
| Media and presentation artifacts | Immutability, exact digest binding, authorized use context                                 | Audio replacement, renderer mutation, cache reuse outside grant               |
| Voice rights state and evidence  | Authentic custody, immutable versions, current epoch, restricted access                    | Fabricated consent, grant widening, suppressed revocation                     |
| Viewer and talent data           | Purpose limitation, separation, retention, verified deletion                               | Memory leakage, backup resurrection, unauthorized evidence access             |
| Secrets and signing material     | Confidentiality, scoped custody, rotation and revocation                                   | Provider-key leak, task-signing key theft, bearer token logging               |
| Audit and incident evidence      | Completeness, ordering, integrity, minimization, access control                            | Deleted stop evidence, injected event history, restricted-content leakage     |
| Availability of safety controls  | Bounded failure and independent stop path                                                  | Safety outage misread as approval, cloud loss disabling local stop            |

## Trust Boundaries

| Boundary                                               | Untrusted or less-trusted side                              | Required crossing                                                                                                                                      |
| ------------------------------------------------------ | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Platform to `session-runtime`                          | Viewer messages, names, badges, metadata, platform delivery | Normalized, bounded, deduplicated input; input moderation; no authority claims                                                                         |
| Operator browser to `control-api`                      | Browser state, identifiers, commands, network location      | Workforce authentication, server-side object authorization, idempotency, CSRF/session controls                                                         |
| `control-api` to `session-runtime`                     | Transported command and asserted human provenance           | Submission recovery generation, semantic intent/auth separation, durable receipt plus append-only authorization observations, authorized return/lookup |
| Runtime process to session authority                   | Cached actor/route/lease state                              | Protected recovery generation, shared ownership-row conflict, post-lock time, exact active generation/lease                                            |
| Domain code to provider gateway                        | Vendor-neutral request                                      | Intent/send authorization/response observation/application fence, timeout/deadline, redacted evidence                                                  |
| Generator to safety gate                               | Complete generated candidate                                | Immutable candidate lineage; all primary/fallback outputs use the same full gate                                                                       |
| Safety package boundary                                | All non-safety packages                                     | Private sole mint capabilities; nominal types; ID-only serialization; persistence constraints                                                          |
| Approved media gateway to TTS provider                 | Exact private final rendering                               | Current content, rights, and surface authorization; deterministic sanitization; bounded call                                                           |
| Cloud to object storage                                | Immutable artifact and metadata                             | Staged commit, object version, digest, scoped timed access, explicit timeout                                                                           |
| `session-runtime` to `stage-host`                      | Network and potentially duplicated/reordered frames         | Mutual identity, closed versioned schema, signed task, session/epoch/expiry/replay verification                                                        |
| `stage-host` to OBS/VTube Studio/audio                 | Locally verified presentation command                       | Closed adapter vocabulary, current authorization, local latch, immediate pre-presentation check                                                        |
| Operational tooling and personnel to restricted stores | Logs, traces, support and incident workflows                | IDs and privacy-preserving references only; purpose-limited privileged reveal                                                                          |
| Source data to cache/backup/restore                    | Derived or historical copy                                  | Source linkage, tombstone/delete reconciliation, no restoration of deleted authority or content                                                        |

Redis Streams is transport only and never a trust or recovery authority. PostgreSQL is the cloud
system of record, but database availability cannot be a prerequisite for local hard stop.
`stage-host` is the sole `SpeechTask` consumer; Redis, raw generated text, signing authority, and
direct database access never cross onto the rig.

## Adversaries And Failure Sources

The model considers:

- an external viewer attempting prompt, markup, name, layout, or resource-exhaustion attacks;
- a malicious or compromised operator, rights reviewer, administrator, support user, or browser;
- a stolen human session, workload identity, rig credential, provider credential, or signing key;
- a compromised or misconfigured provider, renderer, OBS source, plugin, dependency, or build;
- a provider outage or correlated generator/judge failure that returns partial, malformed, stale,
  or misleading results;
- a network attacker able to delay, duplicate, reorder, replay, truncate, or substitute traffic;
- a local attacker with access to the streaming PC, local queue, media cache, or adapter state;
- an insider altering rights evidence, policy, role assignment, audit records, retention state, or
  backups;
- accidental operator error, software defect, clock change, process crash, power loss, replica
  lag, restore error, or dependency exhaustion with security-equivalent consequences.

VNova does not treat the model, provider, platform, browser, Redis, object store, or a connected
rig as intrinsically honest. A fully compromised production host or signing authority remains a
residual risk requiring containment outside the application boundary.

## Misuse And Abuse Cases

### TM-01: Prompt Injection And Stored Instruction Replay

An attacker places instructions in a viewer message, display name, retrieved memory, or knowledge
record and attempts to move them into system authority or persist them for later replay.

Required controls are input normalization and bounds, data-slot isolation, no tool use, typed
viewer-memory slots, provenance, scoped retrieval, PII/instruction rejection, full-output safety,
and red-team fixtures. Memory uncertainty denies the write; safety uncertainty produces no
autonomous speech. Audit stores source IDs and outcomes, not the injected content.

### TM-02: Username, Unicode, And Final-Context Abuse

An attacker uses a display name, homoglyph, bidirectional control, unsafe concatenation, deceptive
spacing, or pronunciation ambiguity to create harmful visible or spoken output.

Written and phonetic forms are normalized and screened separately and again in the final rendered
context. Pronunciation maps are immutable and versioned. Unsafe or uncertain names are omitted or
replaced only by a separately reviewed generic form; spelling or transliteration is not a bypass.

### TM-03: SSML, Markup, And Provider-Control Injection

Viewer or model output includes SSML, phoneme tags, control characters, URLs, renderer markup, or
provider directives intended to alter speech or execute active content.

Public media interfaces remain identifier-only. A deterministic versioned sanitizer constructs
provider markup internally, and the exact final rendering receives a new surface authorization
before any bounded provider call. Unsupported or uncertain markup produces no artifact.

### TM-04: Correlated Provider Failure Or Safety Shopping

A generator and safety judge share a failure domain, a fallback bypasses safety, or repeated
providers are used to shop for an approving verdict.

Generator and model-based judge use independent vendors selected through human review. Every
complete primary, retry, rewrite, or fallback output creates immutable lineage and enters the same
gate. Technical failure can invoke an eligible fallback; a safety rejection cannot be converted
to a provider-shopping loop. Missing independence or determinate judgment fails closed.

### TM-05: Approval Or Authorization Forgery

Code constructs, asserts, clones, serializes, rehydrates, or persists a fake `ApprovedResponse`,
`SurfaceAuthorization`, or `VoiceUseAuthorization`.

Each capability requires a single protected private mint boundary, nominal in-process type,
ID-only process and wire representation, safety-owned rehydration, matching terminal decision,
and—where the capability is an `ApprovedResponse`—the exact candidate explicitly selected by the
same owning turn with immutable post-mint selection. Atomic audit/outbox commit and database
constraints serialize selection-versus-mint races. Static import/compiler-AST guards, mutation
tests, and database negative tests must prove unselected, cross-turn, stale-selection, and common
bypass attempts fail. A plain foreign key, digest, or provider result is insufficient authority.

### TM-06: SpeechTask Replay, Substitution, Or Clock Abuse

An attacker replays a valid task, replaces its artifact, changes session or rights context, uses an
old epoch, or exploits clock offset, uncertainty, drift, or stale synchronization evidence to play
expired work.

The stage host verifies a closed schema, authenticated rig/session binding, signature, audience,
unique replay identity, session and rights epochs after the protected protocol amendment, artifact
digest, order, and conservative time window. Acceptance and replay state are crash consistent;
`playing_or_in_doubt` is never replayed automatically. Uncertain clock mapping, sequence conflict,
state corruption, or stale epoch blocks playback.

### TM-07: Renderer Or Broadcast-Surface Bypass

A raw platform widget, browser source, arbitrary OBS command, model-selected action, or third-party
renderer reaches the audience outside VNova moderation.

Every audience-facing path belongs to a closed surface registry. The production OBS scene
collection is preflighted, unknown or remotely mutable sources fail readiness, and stage-host owns
the initial renderers. Commands use closed vocabularies and exact presentation authorization.
Unknown renderer state clears to a reviewed neutral state; no raw chat overlay is permitted.

### TM-08: Operator Identity Compromise

A stolen session, malicious extension, phishing event, shared account, role escalation, or abused
break-glass credential issues approvals, mode changes, data reveals, policy activations, or resume
commands.

Authentication, semantic capability, object scope, environment, current policy, confirmation, and
presence are independently checked server-side. Revocation or uncertainty closes/narrows
subscriptions, denies privileged mutations, treats presence as absent, and degrades autonomy.
Stop and safe mode decrease remain available through their accepted paths. Response follows the
[operator identity compromise runbook](../runbooks/operator-identity-compromise.md).

### TM-09: Authorization Scope Confusion

A valid principal uses an object identifier, rehearsal grant, UI state, service identity, or
stale policy decision to act on another talent, environment, session, rig, or data class.

Every command and subscription is object-authorized against the concrete scope. Workload, rig,
local safety, and human principals are non-convertible. State channels carry no mutation
authority. Unknown capability, scope, principal, policy version, or authentication context is
denied and audited.

### TM-10: Rights Or Evidence Tampering

An insider or compromised service alters a grant, widens a free-text restriction, replaces consent
evidence, suppresses suspension, or forges an integrity digest.

Rights evidence is restricted and purpose-limited. Immutable grant versions are separate from an
authoritative serialized rights state and monotonic epoch. Human verification, custody
provenance, normalized constraints, terminal rights decisions, atomic state/outbox evidence, and
independent access control are required. A digest proves byte equality only within trusted
provenance; it does not prove consent or legal validity.

### TM-11: Revocation Delay And Offline Voice Use

A voice right is suspended or revoked while synthesis, cache use, dispatch, queueing, or playback
is active, especially while the rig is disconnected.

New use fails closed, affected work and cache eligibility are cancelled, the authoritative rights
epoch advances, and a future accepted signed invalidation path removes old-epoch queued work.
Unknown scope uses the broader safe containment selected by accountable humans. Recovery never
revives old authorizations. Response follows the
[voice-rights revocation runbook](../runbooks/voice-rights-revocation.md).

No architecture can promise instant cloud-originated revocation on a disconnected rig. The
human-approved offline policy, task lifetime, watchdog, interruption scope, and convergence SLO
must close that exposure before voice production.

### TM-12: Privacy Deletion Failure Or Backup Resurrection

A deletion removes a primary row but leaves embeddings, caches, objects, provider copies, local
buffers, replicas, or backups; a later rebuild or restore makes the data available again.

Every derived record links to an authoritative source, deletion cases carry an explicit target
manifest, and completion requires independent absence verification across every in-scope
consumer. Tombstones and retention state are reconciled before restored data becomes available.
Partial, provider-uncertain, backup-pending, or hold-blocked cases remain incomplete rather than
reporting success. Response follows the
[privacy deletion and restore reconciliation runbook](../runbooks/privacy-deletion-and-restore-reconciliation.md).

### TM-13: Evidence Leakage Through Observability Or Support

Exceptions, traces, test artifacts, incident chat, or authorization logs copy tokens, prompts,
candidate text, viewer memory, contracts, identity documents, or generated media.

Ordinary evidence uses opaque IDs, protected references, versions, categories, timings, and
machine-readable outcomes. Redaction failure drops diagnostic content. Privileged reveal is
purpose-limited, time-bounded, and audited in the restricted system; exported evidence follows
separate authorization and retention. Suspected personal-data exposure follows the
[personal-data breach response runbook](../runbooks/personal-data-breach-response.md). Missing,
stale, contradictory, over-capacity, or undelivered operational signals are `unknown` rather than
healthy and follow the
[telemetry and alerting degradation runbook](../runbooks/telemetry-and-alerting-degradation.md).
The [observability model](../architecture/observability-sli-slo-and-alerting.md) governs signal
authority, attribute allowlists, buffering, sampling, retention, access, and export.

Pending ADR-026 review, a raw, normalized, truncated, salted, unsalted, keyed, or otherwise
content-derived viewer message/memory digest is prohibited from ordinary evidence. It remains
linkable and may permit dictionary recovery; it is not an opaque content-independent reference.

### TM-14: Event, Audit, Or Recovery Manipulation

An attacker duplicates, reorders, fabricates, drops, truncates a transition tail, suppresses an
entire transition, downgrades an envelope discriminator or historical classification,
cross-environment substitutes notifications, reinterprets an old event under a current profile,
or tries to make Redis, a WebSocket buffer, or a stage-host journal authoritative.

State mutation and outbox evidence commit together in PostgreSQL. Under Proposed ADR-023, the
complete immutable event-contract identity fixes typed primary scope, aggregate subject,
aggregate-version/event-index ordering, transition completeness, historical classification,
producer/consumer ownership, and payload profile before payload exposure. Trusted framing
selects the envelope parser; a PostgreSQL transition manifest and authorized
expected-delivery/high-water view covers every aggregate version, including zero-count
transitions, and detects filtered sets, missing tails, and whole-transition loss. Consumers are
idempotent, identity/profile/manifest reuse with conflicting content is an integrity incident,
and a safety-relevant incomplete projection cannot advance until PostgreSQL reconciliation proves
completeness. Current restrictive protection overlays use typed targets, monotonic epochs, and
authoritative partition high-waters; rollback or conflict fails closed, and irreversible effects
revalidate them at the immediate boundary without rewriting history. Commands, heartbeats, tasks,
acknowledgements, and restrictive control remain separate closed non-event contracts. Local
observation-journal gaps remain explicit. Redis loss cannot revive state or authorize work.

### TM-15: Rig Or Adapter Compromise

Malicious local software changes media, bypasses the verifier, re-enables a muted OBS source, or
drives an arbitrary VTube Studio/OBS action.

Task signing, artifact digests, minimal rig credentials, closed adapters, local latch persistence,
scene preflight, process boundaries, target-hardware tests, and independent physical stop reduce
the exposure. A rig that cannot prove queue, verifier, adapter, clock, or journal integrity is
unsafe and accepts no new autonomous playback. Full host compromise remains a residual risk.

### TM-16: Resource Exhaustion And Dependency Failure

Flooding, oversized payloads, moderation quota exhaustion, provider stalls, storage failure, or
offline-buffer exhaustion pressure the system to skip controls.

Inputs and schemas are bounded; every external call has an explicit timeout and outer deadline;
capacity is reserved for safety and operator-control paths; queue/retry/cost budgets are reviewed;
and overload degrades or stops affected capability. Exhaustion never authorizes raw, stale, or
unverified output. Resource and quota incidents follow the
[resource exhaustion and backpressure runbook](../runbooks/resource-exhaustion-and-backpressure.md)
and the [capacity model](../architecture/capacity-backpressure-and-cost-governance.md).
Multi-system loss, corruption, failover, or failback follows the
[disaster recovery and broadcast continuity runbook](../runbooks/disaster-recovery-and-continuity.md).

### TM-17: Supply-Chain, Build, And Update Compromise

A malicious or unintended dependency, generated artifact, CI change, package substitution,
provider SDK update, stage-host installer, live-adapter release, or update channel introduces a
bypass, leaks authority, or deploys code different from the reviewed source.

Required future controls include immutable lockfiles, deterministic generation and packaging,
dependency and artifact allowlists, source-to-artifact provenance, secret and dependency scanning,
protected CI/repository ownership, isolated artifact inspection, signed release/update metadata
under a human-approved profile, target identity/version reporting, staged rollout, and a tested
disable/rollback path. Protected packages, contracts, CI, provider gateways, stage-host commands,
and live adapters require accountable review. An unverifiable build, unexpected dependency,
provenance mismatch, failed artifact inspection, or unknown target version is not production
eligible and must not be promoted merely because functional tests pass. Response follows the
[software supply-chain and release compromise runbook](../runbooks/software-supply-chain-and-release-compromise.md).

### TM-18: Configuration Activation, Rollback, Or Cache Manipulation

An attacker or defect edits a reviewed identity through a mutable draft, activates only part of a
compatible set, selects a mutable `latest` alias, deletes/deactivates a narrow binding to expose a
broader fallback, exposes a scheduled set before due time, exploits ambiguous scope precedence,
replays a stale activation or eligibility epoch, rolls history backward, or uses
cache/restore/provider health to revive withdrawn or restrictive configuration.

Proposed ADR-024 separates non-selectable drafts, immutable definition/set versions, monotonic
eligibility state/epochs, explicit inactive/active bindings, closed forward transitions,
non-effective schedules, exact resolved snapshots, independent restrictive authorities, and
ephemeral health. State, transition, minimized audit, and outbox commit atomically; conflicts,
incomparable scopes, stale epochs, and unreviewed fallback fail closed. Restriction dominates
activation; protected enforcement points revalidate eligibility epochs; due schedules revalidate
before creating an ordinary transition; work pins exact snapshots; rollback is a new forward
epoch; and emergency disable remains a separate safe-direction latch that cannot re-enable before
durable reconciliation. Activation never mints content, voice-rights, surface, publication,
identity, or data-access authority.
Containment and forward-only recovery follow the
[configuration activation, eligibility, and forward rollback runbook](../runbooks/configuration-activation-and-rollback.md).

### TM-19: Session Actor Split Brain, Command Ambiguity, Or Timer Replay

A paused, partitioned, or compromised runtime continues after lease loss; a protected commit
reads ownership before concurrent revoke; two instances race; response loss is reported as
success; a successor repeats a possibly-sent provider call; concurrent evaluators create two
timer IDs or an expired claim fires after reclaim; recovery activates across a moving input set;
administrative revoke leaves old-epoch rig work usable; or PITR makes a lost command/effect/timer
tail look absent. Identity, optimistic concurrency, a local generation, and a restored database
alone do not fence these attacks.

Proposed ADR-025 makes the independently protected recovery generation plus PostgreSQL ownership
generation the composite actor fence. Every protected commit and ownership transition shares an
ownership-row write conflict, post-conflict database clock check, and fixed lock order.
Submission-generation-bound semantic command intent/receipt and initial authorization observation
are durable before acceptance. Refreshed evidence appends without rewriting lineage; every
receipt-return path and protected execution reauthorize against current policy/revocation epoch;
deadline expiry is final, and timeout remains unknown. Effects separate intent, send-authorized
attempt, response observation, and application disposition under the exact active/open source
CAS; attempt means possibly sent. Session-bound queries use a distinct, non-relabelable four-role
`RecoveryProbe*` lineage under exact active-plus-draining-prefix or
recovering-plus-recovery-attempt/source binding. Probes are finite and non-widening; a current
same-source successor may terminalize without resending, and terminal `unknown` evidence remains
separate from the bound source ambiguity that must be resolved, permanently safe-quarantined, or
accountably disposed before final close.
Canonical occurrence keys/materialization cursors plus current claim token/revision permit one
admission. Recovery uses immutable cut-time source and schedule-cursor snapshots, a separately
excluded harmless post-cut operational cursor, invalidation revisions, and a sealed rig cursor;
preallocated-ID late commits cannot hide. Every recovery-attempt-bound probe write invalidates
activation, which rejects any nonterminal probe or enabled-scope unresolved source ambiguity.
Revoke atomically installs restrictive epoch/hold/control intent drained by a non-widening
dispatcher, while audience convergence stays unknown until exact rig acknowledgement. PITR lost
tails are quarantined; absence cannot reaccept, replay, rematerialize, or authorize. Ownership
uncertainty permits only safe-direction restriction, and authenticated stop remains dominant
regardless of observed epoch.

## Control And Failure-Posture Matrix

| Uncertain or failed control                                                               | Mandatory posture                                                                                                                          |
| ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Input or final-surface moderation                                                         | Reject or hold the affected work; do not redirect it to an unmoderated surface                                                             |
| Safety verdict or independent judge                                                       | No approval, no autonomous speech, fail-closed event, Mode 0 ceiling for affected/session-wide trust failure                               |
| Content, rights, or surface authorization                                                 | No synthesis, dispatch, presentation, replay, export, or derivative use                                                                    |
| Operator identity, authorization, or revocation state                                     | Deny privileged mutations and restricted reads; presence becomes absent/uncertain                                                          |
| Effective mode or policy state                                                            | Compute the lowest provable ceiling; unknown state recovers at Mode 0                                                                      |
| Composite actor/lease, command, effect, timer, recovery frontier, or history completeness | Stop ordinary progression; retain authorized unknown/quarantine state; no reaccept/replay/catch-up; permit safe-direction restriction only |
| Definition, activation set, scoped epoch, or resolved snapshot                            | Hold/cancel affected new work; use no `latest` or inferred scope; reconcile authoritative state before resuming                            |
| Session epoch, signature, replay state, artifact digest, or clock validity                | Reject task and block playback                                                                                                             |
| Renderer registration or current state                                                    | No new presentation; clear/hide to the reviewed neutral state                                                                              |
| Audit durability                                                                          | Stop and safe mode decrease still act and buffer evidence; resume, mode increase, privileged reveal, and policy activation fail closed     |
| PostgreSQL during a restrictive transition                                                | Hold the strongest process-local restriction, retry durability, prohibit recovery/resume                                                   |
| Cloud link                                                                                | Stage-host watchdog converges locally; local hard stop remains available                                                                   |
| Restricted evidence integrity or rights state                                             | Suspend affected use; preserve and isolate evidence; no broadening by inference                                                            |
| Deletion propagation or restore reconciliation                                            | Case remains incomplete and data remains unavailable after restore until reconciled                                                        |
| Required operational signal or alert route                                                | State is unknown; apply the accepted restrictive mode ceiling and use the reviewed alternate containment path                              |
| Queue/resource reserve, provider quota, or cost authority                                 | Deny or shed affected new work by the accepted priority order; preserve safety/control reserves and never bypass the gate                  |

Containment should be scoped to the affected voice, surface, session, identity, or environment only
when that scope is authoritative and isolation is proved. Ambiguous scope expands toward safety.
Emergency stop remains dominant. Recovery, restored connectivity, returned presence, or cleared
health never causes an automatic increase, resume, or authorization revival.

## Incident Evidence Rules

Security evidence must support a correlated timeline without becoming another restricted-data
store. Ordinary incident records may contain:

- incident, command, event, trace, session, rig, principal, definition/version, activation
  set/transition/snapshot, policy, profile, authorization, task, artifact, and evidence-record
  IDs;
- non-reversible or privacy-reviewed references, object versions, integrity outcomes, sequence and
  epoch values, machine-readable reason codes, and timestamps with clock uncertainty;
- allow/deny outcomes, mode/emergency transitions, queue/renderer effects, provider-neutral health,
  and deletion/revocation status.

They must not contain bearer tokens, signing keys, provider credentials, raw prompts, raw
candidates, viewer-memory values, unrestricted viewer messages, contracts, consent documents,
identity documents, signatures, or unrestricted synthesized media. Investigators use a separate
purpose-limited restricted workflow when content access is necessary. Evidence preservation,
legal hold, deletion, and disclosure are human legal/privacy decisions; responders do not copy
material into a convenient channel to avoid those controls.

## Verification Mapping

The following is required future evidence, not a claim that the repository currently implements
or passes it.

| Threats         | Required evidence                                                                                                                                                                                                                                                                                                                               | Governing review                                                                    |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| TM-01 to TM-03  | Prompt, memory, username, Unicode, SSML, markup, final-context, and rewrite-loop red-team fixtures                                                                                                                                                                                                                                              | ADR-008, ADR-010, ADR-017, ADR-021                                                  |
| TM-04           | Provider independence validation; timeout, partial output, fallback-through-gate, and no-safety-shopping fault tests                                                                                                                                                                                                                            | ADR-007, ADR-008, ADR-020                                                           |
| TM-05           | Import/compiler-AST mutation tests; nominal-type tests; decision/authorization database negatives including unselected/cross-turn/stale-selection and selection-versus-mint races; immutable post-mint selection; rehydration and atomicity tests                                                                                               | ADR-008, ADR-021, ADR-022                                                           |
| TM-06           | Signature, key rotation/revocation, replay, wrong-session/epoch, digest substitution, crash, power-loss, and offset/uncertainty/sample-staleness tests                                                                                                                                                                                          | ADR-008, ADR-010, ADR-011; OD-035                                                   |
| TM-07           | Closed registry and OBS-scene preflight; active-content negatives; renderer clear/expiry/emergency rehearsal                                                                                                                                                                                                                                    | ADR-015, ADR-021                                                                    |
| TM-08 and TM-09 | Authentication threat tests; command/read capability matrix; object-scope, CSRF, session, revocation, presence, and break-glass exercises                                                                                                                                                                                                       | ADR-019, ADR-020                                                                    |
| TM-10 and TM-11 | Evidence-custody review; rights-state concurrency, epoch, revocation, partition, stale-task, cache, replay, export, and recovery tests                                                                                                                                                                                                          | ADR-010, ADR-011, ADR-015, ADR-022                                                  |
| TM-12           | Canary deletion across source, embeddings, indexes, objects, providers, replicas, local buffers, backups, opaque-reference/resolver paths, and restore paths plus independent absence proof                                                                                                                                                     | ADR-017, ADR-026                                                                    |
| TM-13           | Signal data-contract review; prohibited-content and content-derived viewer-digest/cardinality/buffer scans of metrics/logs/traces/profiles/alerts/artifacts; restricted-reveal authorization; collector/exporter/route loss and synthetic incident reconstruction                                                                               | ADR-017, ADR-019, ADR-021, ADR-022, ADR-026; OD-036                                 |
| TM-14           | Complete event contract/framing, typed scope/subject/producer, profile-only evolution, historical replay, restrictive overlay; aggregate-version/event-index plus manifest/high-water gaps; outbox crash; command/receipt/claim/reconciliation remain non-events unless separately modeled; event high-water is not PITR lost-tail proof        | ADR-002, ADR-004, ADR-011, ADR-017, ADR-023, ADR-025                                |
| TM-15           | Target-rig secure-build review; adapter contract negatives; verifier isolation; local stop with cloud/auth unavailable                                                                                                                                                                                                                          | ADR-011, ADR-015, ADR-016, ADR-021                                                  |
| TM-16           | Resource inventory/bounds/reserves; admission/fairness/shedding; quota/cost uncertainty; timeout/cancellation; queue/provider/storage/journal exhaustion; representative load/soak/chaos and backlog-drain evidence                                                                                                                             | ADR-004, ADR-007, ADR-010, ADR-011, ADR-020; OD-037/038/039                         |
| TM-17           | Lockfile/dependency review; deterministic codegen/package round trip; source-to-artifact provenance and allowlist verification; protected-CI mutation tests; stage-host/live-adapter signed release, staged update, disable, and rollback evidence                                                                                              | Repository governance, release-readiness review, ADR-002, ADR-007, ADR-011, ADR-016 |
| TM-18           | Draft/publish digest binding; immutable version/set and eligibility checks; initialize/activate/replace/deactivate/fallback/schedule race; stale activation/eligibility epoch; snapshot pinning/withdrawal; restrictive in-flight change; forward rollback; DB-outage disable/reconciliation                                                    | ADR-004, ADR-008, ADR-017, ADR-019, ADR-023, ADR-024                                |
| TM-19           | Composite-fence state machine; ownership-row/post-lock-time/revoke races; submission-generation receipt/lookup/expiry; four ordinary-effect crash cuts and distinct recovery probes; canonical timer/cursor/current-claim races; committed-cut/preallocated-ID activation; restrictive dispatcher/downstream ack; PITR ABA/lost-tail quarantine | ADR-003/004/007/008/011/015/019/020/025; OD-014/021/029/034/035/037                 |

The complete rehearsal suite must record immutable scenario and build provenance while referring
to restricted fixtures by privacy-reviewed references. Live adapter, identity, provider, rights,
and target-rig evidence remains a separate human gate; simulator success alone is insufficient.

## Residual Risks

- A fully compromised runtime, stage-host, operator endpoint, build pipeline, sole signing
  authority, or accepted safety package can subvert controls within its privilege.
- Human reviewers can make incorrect safety, authorization, rights, legal, policy, or incident
  decisions; separation of duty and review reduce but do not eliminate this risk.
- Safety models and deterministic rules can share semantic blind spots even when vendors differ.
- Unicode, language, pronunciation, cultural context, and multimodal audience interpretation
  create open-ended adversarial cases.
- A disconnected rig creates an unavoidable interval before a cloud-originated rights revocation,
  mode decrease, or freeze is observed; task expiry and watchdog can bound but not eliminate it.
- Emergency stop can prevent future or active local output but cannot retract content already
  broadcast, recorded, mirrored, clipped, or redistributed by platforms or viewers.
- Hashes and stable identifiers can remain linkable; an integrity digest is not automatically a
  privacy-safe reference or proof of legal authenticity.
- Provider, platform, identity, and storage services may retain or process data outside VNova's
  direct control according to their reviewed contracts and technical behavior.
- Backup deletion, legal holds, platform takedown, rights disputes, and cross-border obligations
  require accountable human/legal processes outside the runtime.
- Unknown vulnerabilities and supply-chain compromise remain possible even after the listed
  verification passes.

No residual risk is accepted by inclusion in this document.

## OPEN Human Decisions

Before production enablement, accountable owners must resolve at least:

- OD-012 independent repository ownership and protected review for safety-, contract-, CI-, and
  release-critical paths;
- OD-019 runtime-gate authority, accepted scaffold scope, remote CI, repository Ruleset, and merge
  authority before treating repository checks as production evidence;
- OD-002 provider independence and the privacy/security profile for every external provider;
- OD-009 retention, deletion, backup, restore, legal-hold, and verification policy;
- OD-010/011/015 numeric stop/watchdog targets, cryptographic profile, key custody, interruption
  scope, partition precedence, and resume authority;
- OD-021 the canonical submission-generation command/receipt/outcome and task/control/
  acknowledgement/reconciliation schema, downstream restrictive ordering, sealed rig cursor, and
  generated language coverage;
- OD-033 the complete event-contract/framing, scope/subject, ordering/completeness,
  catalog/classification/protection-overlay, authorization, compatibility, and recovery profile
  through accepted ADR-023 or a replacement;
- OD-034 the exact version/activation and ADR-025 ownership/recovery/command/effect/timer/control
  lifecycle rows, restricted content, memory/knowledge, archive/publication, access, retention,
  deletion/hold/restore, and terminal-state profile;
- OD-022 the SSO, browser-session, MFA/step-up, capability, presence, separation-of-duty,
  revocation, and break-glass profile;
- Open Decision OD-023 the complete surface registry, renderer trust matrix, emergency clear behavior, and
  privacy-safe audit-reference design;
- Open Decision OD-024 the legal/talent authority, evidence custody, rights taxonomy, revocation/offline policy,
  and post-revocation artifact treatment;
- Open Decision OD-025 the approved-media integrity, storage, transfer, cache, interruption, and lifecycle
  profile;
- OD-027 the incident command, severity, escalation, resilient communication, exercise cadence,
  runbook ownership, and deployment authorization profile;
- OD-028 the adversary/trust assumptions, independent validation and penetration-test scope,
  review triggers, evidence freshness, residual-risk taxonomy, and accountable risk-acceptance
  authority;
- OD-029 the disaster-recovery failure domains/sites, RTO/RPO, backup/restore custody,
  independently retained recovery generation/high-water, composite writer/actor/audience fence,
  zero-loss/lost-tail proof and disposition, restored epoch/signing/binding supersession,
  dependency order, failover/failback, continuity, and target-validation profile;
- OD-030 the personal-data breach assessment, evidence, notification decision, provider/
  processor coordination, communications, and closure profile;
- OD-031 the trusted build/release boundary, provenance, signing/update custody, promotion,
  disable, rollback, target identity, and supply-chain compromise profile;
- OD-032 the deletion manifest, source/derived linkage, tombstone/hold precedence, restore
  quarantine, provider/local/backup scope, independent verification, and completion profile;
- the exact production boundaries and evidence required to detect a compromised host, dependency,
  build artifact, signing key, rights store, or identity system.

This threat model must be revised when a trust boundary, deployable, broadcast surface, provider,
identity profile, rights use, persistence domain, cryptographic profile, or offline behavior
changes. Acceptance requires human security, safety, privacy, legal/talent, stage-host, platform,
and operations review. Its current `Drafted` state and missing evidence are tracked in the
[operational readiness review packet](../governance/operational-readiness-review.md); document
completion, merge, or generic test success cannot advance it to production security acceptance.
