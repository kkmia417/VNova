# Voice-Rights Revocation And Suspension Runbook

Status: Proposed rehearsal-only operational procedure; readiness state: `Drafted`;
non-authorizing and not legal advice

Governing sources:

- [ADR-010: approved media and TTS pipeline](../adr/0010-approved-media-and-tts-pipeline.md)
- [ADR-011: stage-host wire protocol and clock synchronization](../adr/0011-stage-host-wire-protocol-and-clock-synchronization.md)
- [ADR-015: layered emergency stop](../adr/0015-layered-emergency-stop.md)
- [ADR-017: data retention, privacy, and PII](../adr/0017-data-retention-privacy-and-pii.md)
- [ADR-019: authentication, authorization, and operator roles](../adr/0019-authentication-authorization-and-operator-roles.md)
- [ADR-020: mode transition and degradation matrix](../adr/0020-mode-transition-and-degradation-matrix.md)
- [ADR-021: broadcast surface inventory and overlay policy](../adr/0021-broadcast-surface-inventory-and-overlay-policy.md)
- [ADR-022: voice rights and talent licensing metadata](../adr/0022-voice-rights-and-talent-licensing-metadata.md)
- [VNova threat model](../security/threat-model.md)

The action names in this runbook describe required semantics, not executable commands, API names,
role grants, legal determinations, or production defaults. The concrete rights protocol, stop
scope, authorization roles, SLOs, retention, and evidence process remain subject to protected
human review.

## Purpose And Entry Conditions

Use this runbook when a current or planned voice use may no longer be authorized, including:

- an authorized legal, talent, or rights owner communicates a suspension or revocation;
- a grant expires, is superseded, disputed, or is found to exclude the current destination,
  territory, purpose, language, commercial context, archive, clip, export, or derivative use;
- consent, contract, identity, signature, reviewer, custody, or evidence integrity is uncertain;
- a voice profile, provider mapping, rights policy, or authoritative rights-state record is
  missing, conflicting, stale, corrupted, or suspected compromised;
- a generated artifact or queued task may be bound to an invalid grant, profile, context, or
  rights epoch;
- a provider or platform change creates an unreviewed use outside the previously evaluated
  context.

Technical responders do not decide whether a legal right exists or whether evidence is
sufficient. Uncertainty denies new use while the accountable human rights authority decides the
legal state. A credible urgent safety or rights report may justify a precautionary technical
suspension without converting that suspension into a legal conclusion.

## Required Human Functions

The incident must assign accountable humans for these functions using ADR-019-approved identities
and capabilities:

| Function                      | Responsibility                                                                                            |
| ----------------------------- | --------------------------------------------------------------------------------------------------------- |
| Incident coordination         | Owns scope, timeline, handoffs, decision log, and exit criteria                                           |
| Legal/talent rights authority | Determines suspension/revocation meaning, affected grant/use, external obligations, and recovery evidence |
| Safety/broadcast operations   | Applies the safest required output containment and confirms audience-facing effects                       |
| Rights-system owner           | Serializes the authoritative state/epoch transition and dependent invalidation                            |
| Stage-host owner              | Confirms queue, active playout, adapter, offline, epoch, and local-stop state                             |
| Security owner                | Investigates evidence, identity, policy, signing, or system compromise                                    |
| Privacy/evidence custodian    | Preserves purpose-limited evidence and applies retention, hold, deletion, and disclosure rules            |
| Communications owner          | Coordinates approved talent, partner, platform, audience, or regulatory communication                     |

One person may perform multiple functions only if the accepted separation-of-duty policy permits
it. An ordinary broadcaster or operator cannot widen, reinterpret, reactivate, or replace a
rights grant.

## Safety Principles

- No current, exact, human-verified rights state means no affected voice synthesis, playback,
  replay, export, publication, or derivative operation.
- Contain the narrowest scope only when identity, dependency mapping, and renderer isolation are
  authoritative. Ambiguous scope expands toward safety.
- A safe-content approval does not supply voice rights, and valid voice rights do not approve
  content or presentation.
- Revocation, suspension, restored connectivity, or evidence repair never revives an existing
  authorization, task, artifact, archive permission, or export automatically.
- Stop wins every race. If unauthorized active or queued audience output cannot be proven stopped,
  use the accepted emergency-stop scope.
- Silence, a neutral scene, or a separately content-, rights-, and surface-authorized fallback is
  preferable to uncertain voice use.
- Do not delete, edit, or disclose suspected evidence merely to complete containment. Quarantine
  and preserve it under the accountable legal/privacy decision.

## Scope Decision

Record the scope decision and its evidence before narrowing containment. Lack of evidence is not
evidence of narrow scope.

| Observed condition                                                                         | Minimum containment posture                                                                                                         |
| ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| One authoritative grant/profile and complete dependency index are known                    | Disable that grant/profile and every dependent pending use                                                                          |
| One use context is invalid but other contexts are independently proven                     | Disable the invalid destination/purpose/context; preserve the broader restriction until isolation is confirmed                      |
| Evidence record, grant mapping, policy version, or dependent-profile index is uncertain    | Suspend every profile/use that depends or may depend on it                                                                          |
| Authoritative rights store, policy, reviewer identity, or state/epoch integrity is suspect | Disable voice use for the affected environment or larger authoritative domain                                                       |
| Potentially unauthorized voice is actively playing or queued                               | Interrupt and flush under the accepted ADR-015/022 scope; if effect cannot be proved, engage emergency stop                         |
| Rig is disconnected or its rights epoch cannot be verified                                 | Treat affected local work as ineligible; use watchdog/local stop and offline policy rather than assuming cloud invalidation arrived |
| Published archive, clip, export, or promotion may be unauthorized                          | Block further access/publication where VNova controls it and escalate takedown/preservation decisions to the rights authority       |

The incident coordinator may broaden technical containment immediately. Narrowing containment,
resuming a profile, or declaring an artifact eligible requires current authoritative evidence and
the accountable rights decision.

## Immediate Containment

Perform these semantic actions in order where possible. A later failure does not undo an earlier
restrictive effect.

1. **Open a restricted incident record.** Assign a stable incident identity, record the report
   source, server receipt time, affected environment, known grant/profile/context IDs, and the
   accountable incident and rights authorities. Do not copy contracts, consent files, identity
   documents, tokens, candidate text, or unrestricted media into the ordinary record.
2. **Prevent new affected use.** Apply a deny/suspension at the earliest trusted rights admission
   boundary so no new `VoiceRightsDecision(allowed)` or `VoiceUseAuthorization` can be created.
   If the authoritative scope cannot be resolved, disable the broader voice domain.
3. **Apply authoritative state when authorized.** The rights-system owner serializes the
   human-authorized `suspended` or `revoked` transition against the current state, advances the
   rights epoch, and atomically records audit and invalidation/outbox evidence. A responder does
   not rewrite an immutable grant or invent a revocation on behalf of the legal/talent authority.
4. **Stop pipeline progression.** Cancel affected synthesis, fallback, cache reuse, media
   authorization, dispatch, replay, export, clip, archive publication, and derivative operations.
   Late success is diagnostic only and cannot restore eligibility.
5. **Quarantine artifacts and caches.** Mark affected artifacts non-dispatchable and prevent
   lookup/rebuild from treating them as reusable authority. Preserve identifiers, object versions,
   and integrity evidence; do not destroy material while hold, dispute, or legal treatment is
   unresolved.
6. **Invalidate local eligibility.** After the protected ADR-011/022 protocol exists, send the
   authenticated, idempotent, replay-resistant rights invalidation and require `stage-host` to
   persist the newer epoch, reject old-epoch work, and evict affected queued tasks before
   acknowledgement. Until that protocol is accepted, production voice is not authorized and no
   ad hoc queue message is a substitute.
7. **Converge active output.** Apply the human-approved interruption policy to affected active
   playout. If a disconnected, compromised, or uncertain rig cannot prove the voice surface is
   silent and its queue is ineligible, invoke the layered emergency stop. Stop requires no
   confirmation or reason; do not delay it for evidence collection.
8. **Degrade safely.** Set the affected work/surface ceiling to Mode 0. Lower the session mode or
   freeze the session when isolation is not proven, the rights system is compromised, or unsafe
   output may continue. Restoration never raises the mode automatically.
9. **Protect administrative state.** Freeze rights-policy activation, grant widening,
   evidence replacement, and profile reactivation within the affected scope until security and
   rights owners establish trustworthy control.
10. **Notify accountable owners.** Escalate immediately through the approved security, legal,
    talent, privacy, broadcast, and platform channels appropriate to the scope. External notice,
    takedown, retraction, or regulatory action is a human legal/communications decision.

Every external system action uses an explicit timeout. Timeout or indeterminate outcome remains
an unresolved containment item; it is not interpreted as success.

## Containment Confirmation

Do not declare the incident contained until evidence proves, for the authoritative affected
scope:

- no new voice-use authorization can be minted;
- current rights state and epoch are durable, or the environment remains held in a stronger local
  restriction while durability is unavailable;
- primary, fallback, and retry synthesis cannot progress;
- media authorization, cache reuse, dispatch, replay, export, and publication are denied;
- every connected stage host has acknowledged the new epoch and queue eviction through the
  accepted protocol;
- every disconnected or unverified stage host is in the accepted watchdog/local-stop safe state
  and cannot play affected work offline;
- active affected audio has stopped or emergency stop remains engaged;
- no old task, artifact, cache entry, replica, restored state, or reordered invalidation can
  become current;
- affected archives, clips, promotions, and exports are blocked or explicitly under an
  accountable legal handling plan;
- evidence and administrator access are restricted against further tampering;
- operator-visible status clearly identifies unresolved rigs, uses, artifacts, and evidence.

If any item is unknown, containment is partial and the corresponding broader restriction remains.

## Investigation And Evidence

Construct a timeline from authoritative and independently observed records:

- report, incident, grant, immutable grant version, rights-state and epoch transitions;
- profile, distribution/use context, rights decision, voice-use authorization, content approval,
  surface authorization, artifact, task, session, rig, archive/export, and trace IDs;
- authenticated actor and reviewer IDs, authorization-policy version, machine-readable reason,
  idempotency identity, state version, and decision outcome;
- synthesis, cache, dispatch, queue, playback, invalidation, interruption, stop, and fallback
  outcomes;
- provider profile and object version identifiers, integrity-check results, original local
  timestamps, and explicit clock-correction metadata;
- access, reveal, grant activation, policy change, role change, export, restore, and evidence
  custody events.

Ordinary evidence contains identifiers, reviewed privacy-preserving references, versions, hashes,
and outcomes only. It excludes raw agreements, consent and identity evidence, signatures, bearer
tokens, provider credentials, signing keys, prompts, candidate text, viewer memory, and
unrestricted audio. A plain hash of a name, clause, or signature may remain identifying; use only
the approved evidence-reference design.

Restricted material is accessed only through a purpose-limited, audited workflow. Preserve
original versions and chain of custody. Corrections create a new version; responders do not edit
history. Legal hold, deletion, disclosure, platform request, and talent communication are decided
by the accountable humans, not inferred from this runbook.

Investigation must determine at least:

- the earliest potentially unauthorized use and the complete dependent scope;
- whether the cause is legal scope, expiry, evidence integrity, reviewer compromise, policy
  mapping, provider mapping, state/epoch corruption, cache/replica lag, protocol delay, or operator
  error;
- whether content was synthesized, queued, played, archived, clipped, exported, promoted,
  transformed, or used for model work;
- whether an identity, evidence store, policy, build, provider, signing authority, rig, or
  privileged workstation remains compromised;
- whether any deletion, retention, provider, platform, contractual, talent, privacy, or
  notification obligation applies.

## Failure Variants

| Failure during response                                  | Required posture                                                                                                               |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| PostgreSQL or rights-state write unavailable             | Hold a process-local deny/freeze, cancel affected work, prohibit recovery, and retry durable reconciliation                    |
| Audit or outbox unavailable                              | Restrictive action proceeds and evidence buffers; no reactivation until required evidence is durable                           |
| Stage-host unreachable                                   | Cloud denies new work; local watchdog/stop applies; incident remains partially contained until local state is proved           |
| Invalidation rejected, delayed, duplicated, or reordered | Newer epoch remains authoritative; old state never wins; unresolved rig stays ineligible                                       |
| Rights/evidence administrators may be compromised        | Remove affected administrative authority through the approved IAM response, preserve evidence, and broaden voice disable scope |
| Provider or object store cannot confirm cancellation     | Mark use unresolved and artifacts non-eligible; do not treat timeout as deletion or cancellation proof                         |
| Scope or legal instruction conflicts                     | Maintain the most restrictive technically supportable state and escalate to named legal/talent authority                       |
| Active adapter effect is uncertain                       | Keep or engage local hard stop; do not attempt a normal resume                                                                 |

## Recovery And Re-Enablement

Recovery is a new authorization path, never reversal of history.

1. The accountable legal/talent authority documents the permitted future use and affected scope.
2. Security proves that compromised identities, policy, evidence custody, state, builds, providers,
   rigs, and signing material are contained or replaced as applicable.
3. A human-verified immutable grant/profile version and authoritative current state are created or
   selected through the protected workflow. The state advances to a new epoch; an old revoked or
   suspended authorization is not reactivated.
4. The complete destination, territory, purpose, language, commercial, archive, replay, export,
   promotional, and derivative context is evaluated again. Unknown scope denies use.
5. A fresh `VoiceRightsDecision`, `VoiceUseAuthorization`, exact voice
   `SurfaceAuthorization`, synthesis attempt, artifact authorization, and signed task are required.
   Existing tasks and artifacts do not inherit recovery.
6. Every affected rig reconciles current state, queue emptiness, epochs, clock, adapter health,
   and stop/watchdog state. No flushed, expired, unknown, or old-epoch work returns.
7. The relevant rehearsal scenarios pass against the exact policy, profile, protocol, and
   configuration proposed for re-enable.
8. Product, safety, operations, security, privacy, legal/talent, and stage-host owners sign the
   protected re-enable evidence required by the accepted governance model.
9. If emergency stop was engaged, use the separate confirmed resume flow with a non-empty human
   reason and complete cloud/local reconciliation. If mode was lowered, any increase is a separate
   confirmed transition; recovery never raises it automatically.

## Exit Criteria

The incident can leave active response only when:

- containment confirmation is complete for every affected and potentially affected scope;
- authoritative legal/talent disposition and future-use decision are recorded;
- all known unauthorized or indeterminate operations have a terminal technical and human-owned
  disposition;
- every rig, artifact, archive, clip, export, provider copy, cache, replica, backup, and evidence
  record is either reconciled or explicitly tracked under an approved follow-up owner;
- required security, privacy, contractual, platform, talent, audience, or regulatory actions are
  complete or owned with an approved deadline outside this document;
- audit and restricted evidence are complete, minimized, access-controlled, and retained or
  deleted according to approved policy;
- re-enable criteria are independently reviewed, or the affected voice remains disabled;
- corrective actions have owners and verification evidence; no OPEN item is disguised as
  incident closure.

Closing the incident record does not itself reactivate a profile, clear emergency stop, raise
mode, delete evidence, or authorize future use.

## Required Rehearsal Tests

Before any production voice use, rehearse at least:

- revocation before synthesis, during provider call, after artifact commit, before dispatch, while
  queued, immediately before playback, and during active playback;
- suspension and revocation racing with provider fallback, cache reuse, task reissue, reconnect,
  replay, export, clip, archive, and derivative-use requests;
- concurrent state updates proving the monotonic rights epoch cannot roll back through stale
  writer, replica, cache, restore, or reordered invalidation;
- connected, disconnected, sleeping, rebooting, wrong-epoch, compromised, and clock-uncertain rig
  behavior;
- local hard stop with runtime, identity provider, database, and operator console unavailable;
- evidence-store corruption, reviewer-identity compromise, incomplete dependency index, and
  conflicting legal scope;
- provider/object-store timeout and indeterminate cancellation with no reuse or false completion;
- quarantine, legal hold, deletion request, backup restore, and provider-copy reconciliation
  without evidence leakage;
- recovery proving that old authorizations and artifacts never revive and that new use traverses
  all content, rights, surface, artifact, dispatch, and immediate pre-playback checks;
- reconstruction of the complete incident timeline using identifiers and restricted references
  without secrets, raw contracts, viewer memory, candidate text, or unrestricted media in the
  ordinary report.

Numeric response, propagation, offline exposure, watchdog, and takedown targets are not defined
here. OD-027 must establish the incident command, roster, escalation, resilient communication,
exercise cadence, and runbook authorization process. OD-028 must establish adversary assumptions,
independent validation, evidence freshness, residual-risk classification, and the authority
allowed to accept remaining exposure. The current `Drafted` state and missing evidence are
tracked in the
[operational readiness review packet](../governance/operational-readiness-review.md); this
procedure cannot become `Rehearsed`, `Target-validated`, or `Production-authorized` by document
merge or elapsed time.
