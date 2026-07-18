# Disaster Recovery And Broadcast Continuity

Status: Proposed operational runbook; readiness state: `Drafted`; no implementation, failover,
production recovery, or live-operation authority

Governing sources:

- [`AGENTS.md`](../../AGENTS.md)
- [ADR-003: stream-session, segment, and turn lifecycle](../adr/0003-stream-session-segment-and-turn-lifecycle.md)
- [ADR-004: PostgreSQL outbox and Redis Streams](../adr/0004-postgresql-outbox-and-redis-streams.md)
- [ADR-007: provider gateway and fallback isolation](../adr/0007-provider-gateway-and-fallback-isolation.md)
- [ADR-008: safety gate enforcement](../adr/0008-safety-gate-enforcement.md)
- [ADR-010: approved media and TTS pipeline](../adr/0010-approved-media-and-tts-pipeline.md)
- [ADR-011: stage-host wire protocol and clock synchronization](../adr/0011-stage-host-wire-protocol-and-clock-synchronization.md)
- [ADR-015: layered emergency stop](../adr/0015-layered-emergency-stop.md)
- [ADR-016: stage-host and cloud/local topology](../adr/0016-stage-host-and-cloud-local-topology.md)
- [ADR-017: data retention, privacy, and PII](../adr/0017-data-retention-privacy-and-pii.md)
- [ADR-018: latency budget and streaming strategy](../adr/0018-latency-budget-and-streaming-strategy.md)
- [ADR-019: authentication, authorization, and operator roles](../adr/0019-authentication-authorization-and-operator-roles.md)
- [ADR-020: mode transition and degradation matrix](../adr/0020-mode-transition-and-degradation-matrix.md)
- [ADR-021: broadcast surface inventory and overlay policy](../adr/0021-broadcast-surface-inventory-and-overlay-policy.md)
- [ADR-022: voice rights and talent licensing metadata](../adr/0022-voice-rights-and-talent-licensing-metadata.md)
- [ADR-025: session actor ownership, command ingress, and fencing](../adr/0025-session-actor-ownership-command-ingress-and-fencing.md)
- [Privacy and retention model](../architecture/privacy-retention-model.md)
- [Stage-host model](../architecture/stage-host.md)
- [Operational readiness review](../governance/operational-readiness-review.md)

This runbook defines recovery semantics and evidence, not infrastructure. It supplies no cloud
region, database topology, backup product, recovery site, RTO, RPO, command, endpoint, credential,
key profile, failover threshold, or communications destination. Those are protected human
decisions and target-specific Phase 9 evidence.

## Purpose And Scope

Use this runbook when loss, corruption, compromise, or prolonged unavailability affects multiple
VNova boundaries or makes normal component-specific recovery unsafe, including:

- PostgreSQL or its recoverable history;
- object, restricted-generation, viewer-memory, audit, rights-evidence, or backup storage;
- `control-api`, `session-runtime`, actor ownership, outbox, or the internal transport;
- workload identity, signing authority, secrets, operator identity, or authorization policy;
- a cloud failure domain, network path, provider set, or production release;
- one or more streaming PCs, local journals, adapters, or venue connectivity;
- the consistency between restored cloud state and a rig that may still hold old work;
- deletion tombstones, legal/incident holds, rights revocations, or restrictive epochs after
  restore.

Component runbooks remain applicable. This workflow coordinates their ordering:

- [Emergency stop and deliberate resume](emergency-stop-and-resume.md)
- [Rig disconnect and watchdog](rig-disconnect-and-watchdog.md)
- [Safety fail-closed](safety-fail-closed.md)
- [Provider degradation and outage](provider-degradation-and-outage.md)
- [Offline observation and domain-event reconciliation](offline-event-reconciliation.md)
- [Privacy deletion and restore reconciliation](privacy-deletion-and-restore-reconciliation.md)
- [Personal-data breach response](personal-data-breach-response.md)
- [Operator identity compromise](operator-identity-compromise.md)
- [Software supply-chain and release compromise](software-supply-chain-and-release-compromise.md)

Continuity means maintaining a provably safe audience state and accountable control. It does not
mean keeping autonomous speech available through every disaster.

## Recovery Invariants

- Safety, rights, integrity, privacy, and stop authority take precedence over availability and
  recovery time.
- `stage-host` can stop local output without cloud, database, identity-provider, or recovery-site
  availability.
- An engaged or uncertain emergency latch, newer restrictive epoch, revocation, deletion
  tombstone, legal/incident hold, expiry, or cancellation always wins over restored older state.
- PostgreSQL is the cloud system of record. Redis, object listings, browser state, provider
  records, WebSocket buffers, and local journals cannot reconstruct permission.
- Redis is restored as transport from committed PostgreSQL outbox state, never as historical
  authority.
- A recovery point is not automatically safe merely because it is internally readable. It stays
  quarantined until constraints, restrictive state, deletion, rights, identity, and audit
  reconciliation pass.
- No two sites, actors, databases, runtimes, or rigs may both believe they hold writable or
  dispatch authority for the same session. An independently retained non-rollback/rebased DR
  recovery generation and each PostgreSQL session ownership generation form the exact composite
  actor fence; neither substitutes for the other. Uncertain authority means safe hold.
- A new recovery generation fences old authority but does not prove a PITR/RPO tail complete.
  Absence of a normal-work admission/close cut, command, effect attempt, timer occurrence,
  dispatch, or restriction inside an unclosed interval is `lost_tail_unknown`, never evidence of
  nonoccurrence.
- `SessionNormalWorkAdmission` is monotonic per session. `draining(normal_closure)`,
  `draining(lost_tail_quarantine)`, and `closed` never return to `open`; recovery may only drain
  and safely classify the fixed accepted prefix or complete atomic final close. Every ordinary
  Turn/candidate/approval/media/task/effect/signing/dispatch progression uses that gate; bounded
  evidence and restrictive/terminal non-advancing writes remain available after it closes. A
  separately typed recovery probe is evidence only, requires exact active+draining-prefix or
  recovering+recovery-attempt/source binding, is finite/read-only-or-restrictive/non-widening,
  permits zero-attempt terminalization, and treats its originating fence as provenance so a
  current same-source successor can terminalize without resend. It must terminalize before close;
  its bound source ambiguity separately resolves, remains permanently safe-quarantined, or is
  accountably disposed.
- Old approvals, authorizations, artifacts, tasks, confirmation challenges, operator presence,
  epochs, queues, and provider results are not revived by restore, failover, failback, reconnect,
  cache rebuild, or clock reset.
- `playing_or_in_doubt` work never replays automatically.
- Every external recovery operation has an explicit timeout and bounded retry. A timeout is an
  unknown outcome and cannot be treated as successful recovery.
- Ordinary recovery evidence contains no raw prompts, candidates, viewer-memory values, secrets,
  credentials, rights documents, unrestricted media, or unnecessary personal data.

## Recovery Roles

These are response functions, not concrete IAM roles:

| Function                       | Required responsibility                                                                                                         |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| Recovery commander             | Owns incident scope, safe-hold state, recovery generation, dependency order, handoffs, go/no-go decisions, and closure evidence |
| Safety lead                    | Verifies no recovery action mints, dispatches, presents, resumes, or raises autonomy from uncertain authority                   |
| Data recovery lead             | Owns PostgreSQL, outbox, backups, constraints, recovery-point evidence, and single-writer fencing                               |
| Privacy/legal lead             | Owns deletion, hold, breach, notification, backup, provider-copy, and evidence-custody decisions                                |
| Security/identity lead         | Owns trusted administrative paths, workload/operator/rig identity, secrets, signing material, and compromise disposition        |
| Runtime owner                  | Restores actor ownership, policy/configuration identity, scheduling, admission, and dispatch in safe-disabled state             |
| Media/storage owner            | Reconciles immutable artifacts, object versions, digests, caches, restricted stores, and non-reusable content                   |
| Stage-host owner/operator      | Maintains local stop/watchdog state and reconciles exact rigs, queues, epochs, clocks, journals, and adapters                   |
| Provider/platform owner        | Restores only reviewed provider and ingestion profiles with bounded conformance checks                                          |
| Communications/continuity lead | Coordinates approved talent, venue, platform, internal, partner, and audience continuity messaging                              |
| Recorder                       | Maintains a minimized timeline, recovery manifest, approvals, blockers, and evidence locations                                  |

OD-027 must assign accountable people, resilient communication, coverage, handoff, and
separation-of-duty rules. A recovery commander coordinates authority but cannot waive a safety
gate, Accepted ADR, legal/rights decision, or target-validation requirement.

## Immediate Safe Hold

Act before determining recovery time:

1. **Protect audience output.** Observe each affected broadcast locally where possible. Engage the
   local hard stop immediately when output is unsafe or cannot be bounded. Stop has no
   confirmation or reason requirement.
2. **Freeze cloud progression.** Deny new autonomous admission, approval progression, synthesis,
   dispatch, surface presentation, rights use, export, and archive publication for affected
   scope. Hold the strongest available `uncommitted_restrictive` state when PostgreSQL is
   unavailable.
3. **Establish rig safety.** Disconnected rigs use their watchdog and reviewed neutral local
   state. Do not assume cloud failover reached them. Preserve local latches, epochs, queues,
   journals, boot identities, and adapter outcomes.
4. **Fence uncertain writers.** Prevent old and recovery environments from accepting concurrent
   authoritative writes or session ownership. Revoke or supersede each session through the
   protected ADR-025 composite recovery/ownership transition and shared ownership-row conflict; a
   route, stopped pod, heartbeat loss, or DR label is not a fence. If fencing cannot be proved,
   neither environment may resume normal work.
5. **Stop propagation of suspect state.** Pause deployments, restores, rebuilds, outbox
   publication, cache population, provider calls, exports, and destructive cleanup when they
   could widen corruption, disclosure, or ambiguity.
6. **Preserve minimum evidence.** Record affected environments, sessions, rigs, stores, recovery
   points, releases, identities, epochs, rights state, deletion/hold state, and first observations
   using identifiers and integrity evidence.
7. **Declare cross-functional response.** Assign the required functions and transfer any
   suspected identity, supply-chain, personal-data, rights, or active-output incident to its
   specialist workflow without releasing safe hold.

A separately approved venue or platform continuity plan may carry non-VNova programming.
Generated filler, old audio, raw chat, arbitrary OBS actions, or an unreviewed provider is never a
continuity shortcut.

## Damage And Recovery-Point Assessment

Before restore or failover, build a read-only impact manifest:

- affected failure domains, deployables, data stores, replicas, backups, providers, rigs, and
  audience surfaces;
- last independently proven healthy release, configuration, policy, schema, key/identity state,
  database point, object version, and local boot;
- last known durable restrictive transition, e-stop, mode epoch, rights epoch, deletion
  tombstone, hold, audit/outbox record, and stage-host acknowledgement;
- known or possible data loss, stale writes, split-brain writes, corrupted identities, missing
  objects, conflicting digests, provider copies, and local-only evidence;
- the earliest point at which integrity, confidentiality, availability, or authority became
  uncertain.

Select no recovery point until reviewers can explain how later restrictive, deletion, rights,
identity, and audit state will be preserved or reapplied. A nominally lower data-loss point may be
safer than a newer corrupt point, but this runbook chooses neither: the target RPO and
scenario-specific decision belong to accountable humans.

## Dependency-Ordered Recovery

Each phase has a gate. Failure returns the affected scope to safe hold.

### Phase 1: Establish Trusted Recovery Control

1. Prove an independently trusted administrative path, responder identity, authorization policy,
   recovery environment, and evidence channel.
2. Contain or replace suspect source, build, artifact, dependency, workload identity, signing,
   secret, update, and operator authority before it can control recovery.
3. Establish the unique recovery generation through an independently retained non-rollback
   authority or rebase above a trusted high-water; fence old writers, dispatchers, signing/
   binding authority, and administrative sessions. Each `StreamSession` separately requires a
   new PostgreSQL ownership generation in recovery-only phase, and every protected boundary uses
   the exact pair.
4. Preserve rollback capability and immutable evidence before any corrective mutation.

Do not rotate, revoke, or replace credentials blindly when doing so could destroy evidence,
strand the local stop path, or leave two active authorities. Use the separately approved
security/key procedure.

### Phase 2: Restore Authoritative Data In Quarantine

1. Restore PostgreSQL through the approved target procedure into a non-serving, write-fenced
   recovery state.
2. Validate schema/migration identity, constraints, transaction consistency, aggregate versions,
   decision/approval lineage, audit/outbox coupling, idempotency, ownership transitions,
   normal-work admission status/epoch/closure cut, command receipts/authorization observations/
   outcomes, ordinary effect intents/send-authorized attempts/response observations/application
   dispositions, recovery-probe intent/attempt/response/disposition lineages and source bindings,
   canonical trigger occurrences/materialization cursors/current claims, firing dispositions,
   recovery barriers, and restrictive-control evidence.
3. Bind the recovery point to trusted WAL/quorum/backup/manifest high-waters. Prove zero loss for
   acknowledged authority records or identify the exact unproven interval/session/range and
   commit `lost_tail_unknown` quarantine/disposition. A restored event/outbox high-water alone is
   not this proof.
4. Compare the recovery point with preserved restrictive local/cloud observations. Apply the
   strongest valid restriction; an older database cannot overrule a causally newer stop, a
   superseding restrictive epoch, or a lower effective mode. Epoch ordering represents authority
   generation and supersession, not a safety ranking in which a numerically lower epoch is
   inherently more restrictive.
5. Reconcile deletion tombstones, incident/legal holds, rights revocations, access revocations,
   retention state, and backup-restoration manifests before data becomes application-readable.
6. Mark missing, contradictory, or unverifiable records as blockers. Do not invent a decision,
   event, acknowledgement, or terminal state.

In an unclosed lost tail, atomically supersede any restored `open` admission state with
`draining(lost_tail_quarantine)` under the new recovery generation. Record the trusted pre-loss
high-water, unproven interval, affected source set, restrictive holds, permanent reopen
prohibition, and coherent lifecycle `Ending`; preserve only a terminal target proven inside the
trusted horizon and otherwise bind conceptual `unresolved_lost_tail_target`. If the restore
already shows `draining(normal_closure)`, preserve its historical cause/fixed prefix and add the
monotonic lost-tail overlay and stronger close gate in the same transaction. If it shows the
atomic `closed` state, keep it closed/ownerless and record later unknown-tail/restrictive evidence
separately. Do not reaccept an absent old-generation command/idempotency key, replay an effect,
rematerialize/catch up a timer slot, admit a Turn, reopen that session, or enable
signing/dispatch. A deny-only independent ledger may prove prior existence but cannot reconstruct
PostgreSQL state or authorize execution.

PostgreSQL availability is not proof that the application may serve traffic.

### Phase 3: Reconcile Restricted And Object Data

1. Restore only the stores and object versions authorized by the recovery manifest.
2. Verify classification, tenant/talent/environment scope, source linkage, object version,
   canonical digest, encryption/custody state, retention, deletion, and hold disposition.
3. Quarantine any artifact, prompt, viewer memory, embedding, rights evidence, archive, export,
   cache entry, or provider copy whose authority or source is missing.
4. Treat missing or digest-conflicting media as non-playable. Never regenerate from raw content
   through an emergency path.
5. Complete the privacy deletion/restore workflow and independent absence checks before a
   restored or rebuilt index, cache, replica, or backup-derived record becomes available.

### Phase 4: Restore Cloud Control In Disabled Mode

1. Start only reviewed, provenance-verified release artifacts and immutable configuration
   versions under the new recovery generation.
2. Re-establish each exclusive `StreamSession` actor through ADR-025 acquire/takeover into
   `recovering` under the exact new composite actor fence; do not mark it active. Load the exact
   normal-work admission status/epoch. A `draining` session may be acquired only to finish its
   fixed prefix and atomic final close, and a `closed` session cannot be acquired. Keep ordinary
   admission, autonomous approval, media generation, dispatch, and audience surfaces disabled.
3. Reconcile every durable command, timer occurrence/claim, turn, ordinary external-effect
   intent/attempt/response-observation/application-disposition, distinct recovery-probe
   intent/attempt/response/disposition/source binding, signing/dispatch record, idempotency
   result, restrictive observation, lost-tail range, and possible playout before recovering
   requested/effective mode, emergency state, epochs,
   policy/prompt/persona/provider/voice/surface versions, and upward-recovery holds.
4. If signing, dispatch, restrictive-control, or playout ambiguity exists or cannot be disproved,
   advance the session authorization epoch or stronger binding fence, install/retain restrictive
   hold, drain priority control through the closed dispatcher, and require an exact sealed
   rig boot/binding/epoch/journal cursor. A stale owner result is evidence only.
5. Unknown or contradictory state recovers at Mode 0 or stronger stop. No service start raises
   mode.
6. Validate health, timeout, authorization, audit, and fail-closed paths without using live
   audience content.
7. For an `open` session, install the source-serialized recovery cut across command, durable
   input-promotion, timer, and Turn-admission sources; classify every pre-cut row, bind
   immutable cut-time source frontiers and timer-materialization-cursor snapshots, and keep
   post-cut normal rows pending. Each harmless post-cut write may advance only a separate
   operational cursor excluded from activation CAS; a changed pre-cut classification or new
   ambiguity/restriction advances the bound invalidation revision. For a `draining` session,
   preserve its immutable closure cut and terminalize or safely classify only that fixed prefix
   in bounded transactions; do not create new normal work. If a reviewed outcome query or rig
   reconciliation is indispensable, admit only the separately typed recovery-probe lineage under
   the exact active+draining-prefix or recovering+recovery-attempt/source binding, enforce its
   finite bounds/unextended deadline, and permit only one terminal non-widening disposition.
   Zero-attempt and terminal-unknown dispositions remain truthful; current same-source successor
   authority may terminalize an old-fence probe without resend. Resolve, permanently
   safe-quarantine, or accountably dispose the separately bound source ambiguity.
8. Enter active ownership only when the ownership-row-linearized activation CAS proves every
   immutable cut-time frontier/snapshot plus invalidation revision and exact `open` admission
   epoch unchanged, the rig remains sealed, and lost-tail/quarantine gates for the enabled scope
   are closed. Every recovery-attempt-bound probe write advances invalidation; every such probe
   must be terminal/non-widening and each enabled-scope source ambiguity resolved or explicitly
   capability-disabled. Continuous harmless post-cut operational-cursor progress alone must not
   reject or starve this CAS. A non-open session never enters ordinary active service.

### Phase 5: Rebuild Transport From PostgreSQL

1. Identify committed pending outbox rows and supported consumer versions from PostgreSQL.
2. Restore the internal transport as empty/replaceable infrastructure where possible.
3. Publish only canonical committed envelopes with original identities and ordering. Duplicate
   delivery remains idempotent; same identity/different content is an integrity incident.
4. Consumers commit durable effects and processed markers before transport acknowledgement.
5. Poison, unsupported, missing, or conflicting events remain blocked under the approved
   terminal handling path.

No Redis backup, stream offset, dead-letter stream, or consumer cursor becomes recovery truth.

### Phase 6: Reconcile Each Stage Host

1. Keep the local hard-stop/watchdog restriction active while establishing mutually authenticated
   current rig, boot, session, protocol, key, and recovery-generation binding.
2. Reconcile emergency state first, then the newest restrictive session/rights epochs, queue,
   replay state, local journal, clock mapping, adapters, and actual audio/surface state.
3. Evict old-generation, old-epoch, expired, cancelled, flushed, invalid, unknown, and
   `playing_or_in_doubt` work. Never infer permission from a local queue entry.
4. Upload minimized offline evidence idempotently without allowing it to overwrite authoritative
   cloud state.
5. Require exact target-rig validation for local stop, watchdog, audio, clock, queue, adapter, and
   recovery effects.

Reconnection is evidence of a channel, not permission to clear a latch or play.

### Phase 7: Restore External Capabilities Deliberately

1. Restore only protected, reviewed platform, identity, provider, object-transfer, OBS, and VTube
   Studio profiles whose integrity, region, privacy, rights, and timeout behavior are current.
2. Run provider-neutral conformance and negative tests with approved synthetic data. A vendor
   status page or successful call is not recovery evidence.
3. Confirm generator/judge independence and that primary, retry, rewrite, and fallback outputs use
   the same safety gate.
4. Confirm TTS/media remains identifier-only and every final surface, rights, artifact, dispatch,
   epoch, signature, replay, and expiry check is active.
5. Keep live ingestion and production output disabled until all recovery exit gates pass.

### Phase 8: Validate, Fail Back, And Resume

1. Run deterministic disaster, restore, deletion, safety, provider, stage-host, identity,
   supply-chain, and broadcast-surface scenarios against the exact recovery versions.
2. Reconstruct a minimized timeline only for proven-complete authority horizons from PostgreSQL
   plus bounded stage-host evidence, never from Redis history. Represent unclosed intervals
   explicitly as `lost_tail_unknown`; do not fabricate a complete timeline.
3. If failback is required, repeat fencing, quarantine, reconciliation, target validation, and
   deliberate authorization. Failback is another authority transfer, not a DNS or routing
   toggle.
4. A human with scoped authority may begin the applicable recovery/resume workflows only after
   all blockers close. E-stop resume requires confirmation and a non-empty reason.
5. Mode increase is separate, one accepted transition at a time, with current presence,
   preconditions, confirmation, rationale, durability, and no unresolved degradation.
6. Admit only newly created work under current policies, rights, epochs, recovery generation,
   deadlines, and the exact still-`open` normal-work admission epoch. A draining or closed session
   is completed or quarantined, never reopened. Observe every enabled surface during the approved
   validation interval.

## Safe Continuity States

The response may deliberately remain in one of these states:

| State                          | Required properties                                                                                                                 |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| Local safe hold                | Rig audio/output is stopped or in its reviewed neutral local state; cloud authority is not required                                 |
| Cloud frozen                   | New progression and dispatch are denied; strongest restrictive state is held and durability retried                                 |
| Production capability disabled | Healthy control/evidence paths may operate, but the affected provider, voice, surface, identity, or data domain remains unavailable |
| Venue/platform continuity      | A separately owned and approved non-VNova plan controls audience communication or programming                                       |
| Controlled supervised recovery | Only the explicitly authorized deployment/capability operates at the accepted conservative mode with current human control          |

No continuity state permits silent fallback to raw text, old media, direct Redis, direct adapter
control, stale rights, unverified identities, or higher autonomy.

## Abort Conditions

Stop recovery and maintain or strengthen safe hold when:

- composite writer/actor/session/audience fencing, independently retained recovery generation,
  or shared ownership-row ordering is uncertain;
- a command receipt, effect attempt/observation/application, timer materialization/claim/
  admission, recovery-probe binding/outcome/terminality, signing/dispatch, restrictive
  acknowledgement, prior actor fence, or lost tail cannot be classified without unsafe
  inference;
- the recovery point cannot preserve later stop, rights, deletion, identity, hold, or audit state;
- PostgreSQL constraints, lineage, outbox coupling, or ownership are inconsistent;
- source-to-artifact provenance, signing/update authority, or build integrity is suspect;
- restored data becomes readable before tombstone/hold/rights reconciliation;
- a required object, digest, task, queue, epoch, clock, journal, or rig binding conflicts;
- a dependency requires an unreviewed region, provider, schema, migration, key, policy, command, or
  bypass;
- recovery evidence leaks restricted content, personal data, credentials, or secrets;
- any operation repeatedly times out or its outcome cannot be bounded;
- live output, mode increase, or resume occurs without the separate current authorization.

## Recovery Exit Criteria

The affected capability or deployment is eligible for a protected authorization decision only
when:

- trusted recovery control and one independently protected authoritative recovery generation are
  established;
- every enabled session has one exact active composite actor fence after a source-serialized
  recovery barrier, with no stale owner/transaction, possibly-sent non-idempotent replay,
  duplicate canonical trigger admission, unsealed rig, or ambiguous old-epoch dispatch;
- every restored authority-record interval is proven complete or remains explicitly
  `lost_tail_unknown` and quarantined; no missing old command/effect/timer/restriction was inferred
  absent, reaccepted, replayed, or rematerialized;
- every restored normal-work admission/close cut is proven complete, or the session is durably
  `Ending` plus `draining(lost_tail_quarantine)` or
  `draining(normal_closure + lost_tail_quarantine)` with its affected prefix, holds, resolved or
  explicitly unresolved terminal target, and reopen prohibition; any unresolved target blocks
  final close, every admitted recovery-probe lineage is terminal/non-widening, every bound source
  ambiguity is resolved/permanently safe-quarantined/accountably disposed, final close is atomic,
  and no non-open session has accepted new normal work; a terminal probe may remain truthfully
  `unknown`;
- the selected recovery point and every known later restrictive fact have accountable,
  independently reviewed disposition;
- PostgreSQL, required restricted/object stores, outbox, consumers, and transport are coherent
  under their proper authority roles;
- deletion/tombstone, retention, backup, hold, rights, identity, and provider-copy reconciliation
  is complete or the affected data/capability remains unavailable;
- no restored cache, replica, index, object, artifact, task, queue, session, challenge, presence
  lease, or epoch can revive deleted, revoked, expired, stopped, or in-doubt state;
- every production rig has current authenticated binding, exact-target validation, safe local
  state, reconciled queue/journal/clock, and no old work;
- safety, authorization, provider, media, surface, privacy, security, audit, alert, rollback, and
  fail-closed negative evidence passes for the exact release/configuration;
- RTO/RPO outcomes, actual data loss, unresolved gaps, residual risks, and follow-up owners are
  recorded without implying an unapproved target;
- all blocking findings are closed; residual-risk treatment follows OD-028 and cannot waive an
  invariant, ADR, legal/rights authority, required gate, or target evidence;
- an accountable deployment-scoped operational and release-readiness decision is recorded.

If these criteria cannot be proved, remain safely stopped, frozen, or disabled.

## Evidence And Data Handling

Record:

- incident, recovery generation, environment, deployment, release, build, artifact, configuration,
  migration, policy, key/identity, database recovery point, backup, object, provider, session, rig,
  boot, epoch, task, event, outbox, trace, and evidence-manifest identifiers;
- raw observation times, source clocks, correction/uncertainty, outage boundaries, fencing,
  ownership, timeout, retry, and acknowledgement outcomes;
- integrity/constraint/provenance results, data classifications, tombstone/hold/rights state,
  queue/journal/adapter effects, and safe-hold transitions;
- every recovery/failback phase gate, human decision, confirmation, reason, blocker, rollback,
  target validation, and authorization scope.

Ordinary evidence uses identifiers, versions, classifications, machine-readable results, and
privacy-reviewed references. It does not contain raw prompts, candidates, viewer-memory content,
personal-data samples, rights/identity documents, credentials, signing material, provider bodies,
media bytes, or unrestricted backups. A digest does not automatically declassify data.

## Escalation

Escalate without weakening safe hold when:

- people or audience safety, personal-data exposure, rights misuse, identity/key compromise, or
  supply-chain tampering is suspected;
- no independently trusted administrative, evidence, or local-stop path remains;
- a recovery point, backup, replica, provider copy, or local journal is missing or untrusted;
- multiple failure domains, regions, rigs, talents, or environments may be affected;
- split brain, stale authority, deleted-data resurrection, or unapproved output may have
  occurred;
- target RTO/RPO, retention, notification, rights, platform, partner, or contractual decisions
  require accountable human action.

Exact incident severity, contacts, recovery-site activation, notification, platform/talent/public
communications, and external coordination remain OPEN.

## Required Rehearsal Scenarios

Before production authorization, exercise:

- complete loss and point-in-time corruption of PostgreSQL, including a recovery point older than
  a normal-work admission/close cut, stop, mode decrease, rights revocation, access revocation,
  deletion, and hold;
- split-brain database/runtime/session ownership and failed fencing;
- command acceptance with submission-generation response loss, lookup revocation, and crash at
  every receipt/state boundary; process pause/row-lock wait/post-lock clock beyond lease; forced
  revoke during every effect send-authorization/first-byte/response-observation/application cut;
  possibly-sent non-idempotent work; canonical timer materialization/current-claim races;
  immutable recovery-frontier/cursor snapshots; harmless post-cut operational-cursor progress
  without activation starvation; ambiguity/restriction invalidation; restrictive-dispatcher
  loss; and timer missed/catch-up recovery;
- recovery-probe intent/attempt/first-byte/response/disposition crash cuts under exact
  active+draining-prefix and recovering+recovery-attempt/source bindings; wrong binding,
  ordinary-effect relabeling, zero-attempt terminalization, current same-source successor
  terminalization without old-intent resend, finite-bound/deadline exhaustion,
  negative/timeout/contradictory terminal-unknown evidence separated from source resolution, no
  widening/absence/replay authority, and final-close rejection for a nonterminal probe or
  unresolved bound source ambiguity;
- PITR/nonzero-RPO loss of an admission/close cut or acknowledged command/effect/timer/restriction
  records, repeated local generations/epochs, deny-only ledger disagreement, and proof that a
  restored `open` state enters coherent `Ending`/`draining(lost_tail_quarantine)`, a restored
  `draining(normal_closure)` gains the monotonic quarantine overlay, a restored atomic `closed`
  state stays closed, unresolved target blocks final close, and unknown tails never reopen,
  reaccept, replay, rematerialize, admit a Turn, or enable audience output;
- object/restricted-store loss, digest conflict, missing artifact, cache/index rebuild, and
  provider-copy uncertainty;
- Redis loss and rebuild exclusively from PostgreSQL outbox state;
- cloud failure while one or more rigs are connected, disconnected, playing, queued, rebooting,
  clock-uncertain, or `playing_or_in_doubt`;
- identity, secret, signing, build, update channel, and administrative-path compromise during
  failover;
- provider, platform, object-transfer, and control-link outage with bounded timeouts and no unsafe
  fallback;
- backup restore that would resurrect deleted, held, revoked, expired, or restricted data,
  proving quarantine and independent absence verification;
- local stop and neutral continuity with all cloud, identity, database, and provider paths
  unavailable;
- failover recovery, failed recovery rollback, and failback, each proving one authority,
  current epochs, no old work, and no automatic mode increase/resume;
- complete reconstruction for proven authority horizons, with every lost/unknown interval
  explicit, without Redis history or prohibited evidence content.

Simulator and tabletop evidence can establish `Rehearsed` only. Exact production infrastructure
and rig exercises are required for `Target-validated`.

## OPEN Decisions

Human approval is required for:

- OD-027 incident/recovery command, roster, coverage, handoffs, resilient communications,
  exercise cadence, evidence freshness, and runbook authorization;
- OD-028 adversary assumptions, independent validation, residual-risk taxonomy, and acceptance
  authority;
- OD-029 recovery failure domains/sites, data-class and capability RTO/RPO, backup/restore
  custody, independently retained recovery generation/high-water, composite writer/actor/audience
  fencing, authoritative zero-loss completeness proof, deny-only ledger evidence that can prove
  existence/bound quarantine but never absence or reconstructed authority, lost normal-work
  admission/close-cut and other tail disposition, restored epoch/signing/binding supersession,
  dependency order, failover/failback authority, continuity states, and target authorization;
- OD-014/035/037 session ownership/scheduling/recovery policy, typed recovery-probe
  allowlist/binding, lease/timeout/clock values, and command/ordinary-effect/recovery-probe/timer
  queue/claim/recovery-drain bounds;
- applicable OD-030, OD-031, and OD-032 decisions for personal-data breach response, trusted
  supply-chain/release recovery, and deletion/restore assurance;
- recovery regions/sites, single-writer/fencing mechanism, dependency order implementation,
  activation and failback authority;
- data-class and capability-specific RTO, RPO, maximum tolerable outage, recovery-point selection,
  validation, and observation targets;
- PostgreSQL/object/restricted-store backup, replication, encryption, custody, integrity,
  restoration, quarantine, and destructive-cleanup procedures;
- tombstone, retention, deletion, legal/incident hold, rights, provider-copy, archive, and
  independent absence-verification policy;
- identity, secret, signing, key rotation/revocation, build provenance, release, update, and
  rollback profiles;
- stage-host replacement/enrollment, local storage, queue/journal recovery, adapter/OBS/VTube
  Studio continuity, venue fallback, and target evidence;
- target-specific commands, endpoints, infrastructure providers, contacts, alerts, severity,
  external notification, and communications.

No example, fixture, cloud product, library, backup default, provider, or operating-system
behavior becomes a production value through this document.
