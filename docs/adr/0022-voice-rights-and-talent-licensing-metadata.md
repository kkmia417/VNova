# ADR-022: Voice Rights And Talent Licensing Metadata

Status: Proposed

Priority: P2

Date: 2026-07-17

Sources: `AGENTS.md`, `vnova-review-handoff.md`, `docs/architecture/privacy-retention-model.md`, ADR-008, ADR-016, ADR-017, ADR-021

This ADR is non-binding while its status is `Proposed`. It defines a technical control model, not a legal conclusion. Only authorized human legal, talent, and rights owners may determine whether evidence is sufficient and a proposed use is permitted.

## Context

A technically available voice, voice model, recording, or provider profile is not necessarily authorized for every broadcast. Permission may differ by talent, territory, platform, account, time period, language, live versus recorded use, commercial context, archive or replay, promotional clips, editing, voice conversion, model training, and other derivative uses.

Storing a free-text note such as "licensed" on a provider configuration cannot support deterministic authorization, expiry, revocation, incident response, or audit. Provider availability and provider terms are also not substitutes for talent consent or a reviewed rights grant.

Rights must therefore be executable system constraints. VNova must fail closed when the intended use cannot be proven to fit a current, human-verified grant.

## Decision

`VoiceProfileDefinition` and `VoiceRightsGrantVersion` are first-class immutable, versioned domain
objects. Their current activation, suspension, expiry, supersession, and revocation are held in a
separate authoritative `VoiceRightsState` with a monotonic rights epoch. Technical synthesis
configuration is separated from normalized rights metadata, mutable lifecycle state, and
restricted evidence.

Every synthesis, playback, replay, export, archive publication, promotional use, or derivative operation requires a concrete `VoiceUseAuthorization`. Authorization is evaluated against a human-verified, versioned rights grant and bound to the exact intended use.

No voice profile is active merely because a provider exposes it. Missing, unknown, ambiguous, expired, suspended, conflicting, or revoked rights state denies use.

The proposed sole mint boundary for `VoiceUseAuthorization` is `packages/safety`. This capability
is distinct from `ApprovedResponse` and `SurfaceAuthorization`: it cannot approve content or a
presentation, and neither content nor presentation approval can manufacture or widen voice
rights. The normalized-rights administrative domain verifies evidence and controls rights state;
the runtime mint evaluator receives only reviewed grant/state IDs, normalized constraints, epoch,
and verification provenance, not raw contracts or identity evidence.

OD-024 must explicitly accept or replace this ownership. A replacement may use another equally
protected sole rights-authorization boundary, but the console, provider, TTS adapter, renderer,
and stage host cannot mint it.

The initial trust chain is:

```text
restricted consent / license evidence
  -> human-verified VoiceRightsGrantVersion
  -> authoritative VoiceRightsState + epoch
  -> immutable VoiceProfileDefinition version
  -> requested DistributionAndUseContext
  -> VoiceRightsDecision(decision = allowed)
  -> VoiceUseAuthorization
  -> voice SurfaceDecision + SurfaceAuthorization
  -> identifier-only synthesis request bound to ApprovedResponse
  -> immutable voice artifact
  -> signed SpeechTask
  -> stage-host content/rights/surface/version/expiry check
  -> playback
```

Content approval, voice rights authorization, and voice surface authorization are independent
mandatory gates composed as defined by ADR-021. A safe response without valid voice rights and an
exact final-presentation authorization is not speakable, and valid rights never approve unsafe
content or a different rendering.

## Rights Data Model

The names below define responsibilities, not an authorized database migration. Any schema requires a linked migration ADR and human review.

### VoiceProfile Definition

An immutable profile-definition version binds:

- stable profile identity and version;
- talent or voice identity reference;
- provider-neutral technical voice identity;
- persona or production binding where applicable;
- language and locale capabilities;
- one or more reviewed rights-grant version references;
- creation and review provenance.

Provider-specific synthesis settings stay inside the provider gateway or its protected configuration. Provider SDK objects and credentials never enter this domain model.

### VoiceRightsGrant Version

A normalized, immutable grant version records the machine-evaluable scope approved by an authorized human reviewer:

- grant ID, version, and rights-holder/talent references;
- restricted evidence-record IDs and integrity hashes;
- rights basis and agreement/consent version references;
- human verifier identity, role, verification time, and review state;
- effective start and end, or an explicitly reviewed no-stated-end representation;
- allowed and excluded territories;
- allowed and excluded platforms, channels, accounts, and distribution modes;
- allowed use purposes and commercial contexts;
- live, rehearsal, archive, replay, clip, export, and promotional permissions as separate capabilities;
- languages or locales where the reviewed grant distinguishes them;
- derivative-use capabilities and prohibitions;
- consent restrictions, conditions, attribution obligations, and other normalized constraints;
- governing policy and normalization-taxonomy versions.

A free-text contract summary is not executable permission. If a material term cannot be normalized safely, it remains a restrictive condition requiring human review for every affected use.

### VoiceRights State And Epoch

One authoritative PostgreSQL state record per governed profile/grant family names the currently
eligible definition/grant versions, lifecycle state, state reason, effective time, and monotonic
rights epoch. Lifecycle state includes at least inactive, active, suspended, expired, superseded,
and revoked.

- Definition and grant versions never mutate when state changes.
- Activation, suspension, expiry, supersession, and revocation use compare-and-swap or equivalent
  aggregate serialization against the current epoch.
- The new state, epoch, audit evidence, invalidation/outbox record, and affected-profile index
  commit atomically.
- Every authorization and artifact records the epoch it evaluated.
- A stale epoch cannot become current through cache refresh, retry, replica lag, reconnect,
  restoration, or message reordering.
- Conflicting or missing current-state records deny use.

PostgreSQL is authoritative. Redis, provider metadata, cached policy snapshots, signed tasks, and
stage-host local state can only hold bounded verification snapshots and invalidation evidence.

### VoiceRights Decision

Every requested use creates a terminal, immutable
`VoiceRightsDecision(decision = allowed | denied | indeterminate)` bound to the profile definition,
grant version, current rights epoch, complete distribution/use-context digest, normalized policy
version, human-verification provenance, and decision reason.

Only the literal `allowed` outcome for the same bindings can back a `VoiceUseAuthorization`. A
missing, denied, indeterminate, conflicting, or stale decision cannot mint authorization.

### Restricted Evidence

Consent forms, contracts, identity evidence, correspondence, signatures, and legal interpretations are restricted records. Ordinary operational tables and audit logs store only evidence IDs, integrity hashes, versions, review outcomes, and authorized actor metadata.

The restricted evidence store has separate access roles and purpose-limited access. Exact evidence retention, deletion, legal-hold, residency, and disclosure rules remain human legal and privacy decisions under ADR-017.

### DistributionAndUseContext

Every requested use supplies an immutable context that resolves at least:

- stream session, production, talent, and voice-profile version;
- intended platform, destination account/channel, and simulcast set;
- intended territory classification;
- live, rehearsal, replay, archive, export, clip, promotional, sponsor, or other reviewed purpose;
- language/locale and audience context where material;
- requested transformations or derivative operations;
- planned start, end, and maximum artifact lifetime;
- applicable policy version and requesting actor or system provenance.

There is no implicit worldwide territory, all-platform permission, perpetual term, commercial permission, or derivative permission. Human legal review must define how internet broadcasts, geofencing, global availability, platform retransmission, and unknown viewer locations map to normalized territory constraints.

### VoiceUseAuthorization

An immutable authorization binds:

- authorization ID;
- `approved_response_id` for synthesized speech;
- voice-profile and rights-grant versions;
- distribution-and-use-context ID and digest;
- stream-session ID and session epoch;
- permitted operation and destination set;
- policy and human-review provenance;
- issued-at, `not_before`, and `not_after`;
- rights-state or revocation epoch;
- any artifact reuse or transformation restrictions.

The authorization expires no later than the earliest source approval, rights grant, session, or intended-use deadline. Retry, provider fallback, artifact caching, reconnect, queueing, archive, or replay never extends it.

An authorization is not portable to another response, voice version, profile, talent, platform, territory, account, session, purpose, derivative operation, or time window.

`VoiceUseAuthorization` uses ADR-008-grade mint enforcement:

- its constructor and mint capability are private to the accepted sole mint package;
- other packages receive a frozen nominal in-process view, while process/API/event/wire/storage
  boundaries carry only the reviewed authorization ID and DTO;
- rehydration revalidates the terminal rights decision, current state/epoch, exact use-context
  digest, profile/grant versions, `approved_response_id`, session, and expiry;
- a unique/composite database constraint or equivalent binds the authorization to the literal
  allowed decision and matching context/state epoch; a plain grant foreign key is insufficient;
- rights decision, authorization, audit, and required outbox evidence commit atomically;
- protected-symbol/import tests reject construction, assertion, cloning, proxying, serialization
  as a capability, conflicting identity reuse, and unauthorized mint calls;
- any schema requires a linked migration ADR and protected human review.

These controls authorize rights use only. The separate ADR-008 approval constraint and ADR-021
surface-decision constraint must also pass.

### Voice Artifact

Every synthesized artifact is immutable and binds:

- artifact ID and integrity digest;
- `approved_response_id`;
- voice-use-authorization ID;
- voice-profile and provider-profile versions;
- synthesis and creation provenance;
- generation time and expiry;
- allowed operation and reuse constraints.

Cached audio is not a perpetual entitlement. Reuse, replay, export, clipping, editing, or publication requires a fresh authorization for that use unless the original authorization explicitly and currently permits it. Revoked or indeterminate artifacts are quarantined from use while human legal and privacy owners decide required retention or deletion.

Non-synthesized recordings require the same rights evaluation, but this ADR does not create a content-approval or media-dispatch bypass for them. Their audience-facing playback remains disabled until ADR-021's protected media-surface amendment defines the required identifier-only content authorization.

## Territory, Platform, Time, And Purpose

Rights evaluation uses an explicit deny-by-uncertainty rule:

- Every intended destination must be within the reviewed platform, channel/account, distribution-mode, and territory scope.
- Simulcast and syndication are evaluated as a set; one unauthorized destination denies that multi-destination request or is removed through a new reviewed context.
- Start and end times are evaluated at authorization, before synthesis, before dispatch, on stage-host acceptance, and immediately before playback.
- The complete expected playout interval must fit within the authorized time scope; a task is not started when its expected completion would exceed that scope.
- A profile with a future grant does not authorize early use. An expired grant cannot authorize cached or queued output.
- Commercial, sponsor, ticketed, subscription, charitable, internal rehearsal, public live, archive, replay, clip, and promotional contexts are not assumed equivalent.
- Unknown or conflicting scope does not inherit the broadest grant; it requires human resolution.

Exact territory taxonomy, platform identifiers, context vocabulary, and conflict-resolution rules require legal, product, and rights-owner approval.

## Derivative Uses

Derivative permissions are represented as explicit, independently reviewable capabilities. The taxonomy must distinguish at least:

- creating, training, fine-tuning, adapting, or evaluating a voice model from talent material;
- real-time synthesis from an already authorized model;
- voice conversion or impersonation;
- pronunciation, timing, pitch, speed, emotion, and style transformations;
- editing, mixing, mastering, localization, and translation;
- combining the voice with another voice or media work;
- creating clips, compilations, archives, replays, promotional material, and exports;
- retaining source recordings, intermediate representations, embeddings, model checkpoints, and generated artifacts.

Permission for live synthesis does not imply permission to train or adapt a model, use source recordings, create a voice conversion, publish archives, make promotional clips, or perform any other derivative operation.

The final capability vocabulary and legal interpretation are OPEN. Until approved, an unrepresented derivative operation is denied.

## Consent And Human Authorization

- Consent or license evidence is ingested only through an authenticated, purpose-limited workflow.
- The system records who submitted, verified, approved, superseded, suspended, or revoked each grant and under which role.
- Evidence integrity uses immutable versioning, trusted capture/custody provenance, and an
  approved cryptographic integrity mechanism; corrections create a new version. A digest alone
  does not prove identity, consent, authority, or authentic capture.
- Grant scope cannot be widened by a broadcaster, ordinary operator, model, provider response, or configuration change.
- Technical operators may select only among uses already authorized for the current context.
- Activation, scope expansion, exceptional use, and revocation require roles defined by ADR-019 and approved by legal/talent governance.
- Consent evidence is never inferred from silence, prior broadcasts, provider availability, or an unrelated talent agreement.

This ADR does not prescribe a signature method, legal capacity test, contract interpretation, or jurisdiction-specific consent standard.

## Authorization Enforcement

Rights checks occur at every point where the use can change:

1. **Profile activation:** incomplete or unverified rights metadata prevents activation.
2. **Production preflight:** every planned platform, territory, purpose, language, and anticipated derivative use must resolve to an allowed context.
3. **Voice selection:** the selected profile version must be valid for the current talent, persona, session, and intended use.
4. **Before synthesis:** the public gateway receives `approved_response_id` as its sole content
   authority plus voice-profile, context, and voice-use-authorization IDs as non-content metadata.
   It resolves content internally, computes the exact final rendering, obtains the bound voice
   surface authorization, and only then invokes the private provider adapter. Callers never supply
   raw generated text or a pre-rendering surface authorization.
5. **Provider retry or fallback:** the system re-evaluates the actual replacement profile,
   provider context, destination, rights grant/state, and exact final surface rendering. Fallback
   cannot inherit rights or surface authorization from a different voice or rendering.
6. **Artifact creation and cache lookup:** stored and reused artifacts remain bound to content,
   rights, and surface authorization IDs, integrity digest, purpose, destination, and earliest
   expiry.
7. **Before dispatch:** current rights state, revocation epoch, session epoch, and expiry are revalidated.
8. **Stage-host acceptance and immediate pre-playback:** after the protected ADR-011/OD-021
   protocol amendment, the signed task binds content, rights, and surface authorization IDs,
   voice-profile version, rights epoch, artifact digest, session epoch, and earliest expiry.
9. **Archive, replay, clip, export, promotion, or transformation:** each new use is evaluated independently before access or publication.

Provider gateways enforce provider-specific restrictions in addition to, never instead of, VNova's normalized grant. All external calls have explicit timeouts. Primary and fallback providers remain subject to ADR-008's same safety gate.

Package boundaries, reviewed contracts, repository checks, database constraints, signed tasks, and rehearsal tests must make omission of rights authorization detectable. Exact persistence constraints require a linked schema ADR.

The current ADR-008 `SpeechTask` allowlist does not admit the proposed rights/surface identifiers
or a rights-invalidation command. ADR-011 acceptance, OD-021 resolution, protected
ADR-008/contract changes, ADR-015 interruption-scope acceptance, and generated contracts for every
participating implementation language are prerequisites. This ADR alone changes no task, queue,
or stage-host command.

## Revocation And Suspension

Revocation and suspension are first-class state transitions, not mutable notes.

When a revocation or suspension becomes effective:

- the new authoritative `VoiceRightsState` and epoch, audit evidence, outbox/invalidation record,
  and affected-profile index commit atomically in PostgreSQL;
- no new voice-use authorization may be minted from the affected grant or profile;
- pending synthesis and dispatch are cancelled;
- relevant queued tasks and cached artifacts become ineligible for use;
- after the accepted ADR-011 protocol exists, `session-runtime` sends an authenticated,
  idempotent, replay-resistant invalidation carrying the new rights epoch and affected
  authorization/profile IDs;
- after ADR-015/OD-015 accepts the scope, `stage-host` applies the approved interrupt/flush behavior
  to affected active and queued work and refuses older rights epochs;
- operator workflows show the affected sessions, destinations, artifacts, and unresolved incident state;
- the transition and resulting cancellations are audited with IDs and hashes, not restricted evidence content.

Rights-state recovery never resurrects old authorizations or artifacts automatically. Resumption requires a new verified grant/profile version and fresh use authorizations.

No distributed system can promise that a cloud-originated revocation is instant on a disconnected rig. Signed task lifetime, local rights snapshots, disconnect watchdog behavior, offline playback policy, revocation convergence SLO, and the treatment of a revocation whose legal effective time precedes receipt require explicit human legal, safety, and operations decisions. If a grant requires zero offline revocation exposure, that profile must not be playable while disconnected.

Until those protocol and interruption decisions are accepted, production voice use is disabled;
an implementation cannot approximate invalidation with an unsigned queue message or ad hoc adapter
call.

## Failure Behavior

- Missing, unavailable, unverifiable, conflicting, expired, suspended, or revoked rights state means no synthesis and no playback.
- A rights-policy timeout fails closed. It does not fall back to provider defaults or a previous grant version.
- A profile or provider fallback is allowed only when separately authorized for the exact use.
- During a live incident, VNova halts the affected voice surface, cancels affected work, alerts the operator, and follows the accepted mode-degradation policy.
- Silence, a reviewed non-voice continuation, or a separately rights-authorized fallback may be used; unsafe or unauthorized speech is never used to preserve continuity.
- An artifact with unknown authorization, digest mismatch, stale rights epoch, or uncertain provenance is quarantined and cannot be replayed, exported, or published.
- Evidence-system or policy-version uncertainty blocks new voice use while preserving restricted evidence according to human-approved legal and privacy procedure.

## Privacy, Security, And Retention

Voice recordings, biometric-like voice data, talent identity records, consent evidence, contracts, model artifacts, provider data, and generated audio may require different classifications and controls. ADR-017 supplies the separation and minimization baseline but does not decide their legal classification.

- Secrets, signing keys, provider credentials, raw contracts, signatures, and identity documents never enter ordinary logs.
- Audit records contain IDs, hashes, versions, decisions, actor identity, timing, destination, and purpose needed to prove authorization.
- Restricted evidence and operational audit use separate content and access roles.
- Access to restricted evidence requires a logged purpose and an authorized role.
- Generated artifacts and source recordings are not retained merely because storage is convenient.
- Deletion, preservation, legal hold, residency, data-subject rights, and post-revocation artifact treatment require human legal and privacy policy.

No retention duration or deletion SLA is selected by this ADR.

Integrity digests, privacy-preserving audit references, and legal evidence are not interchangeable.
A plain hash of a name, short clause, signature image, or low-entropy identifier can remain
linkable; a digest alone does not establish chain of custody or legal validity. OD-024 must approve
the evidence-custody workflow, classification, domain separation or keyed-reference approach where
needed, key access, retention, deletion, and disclosure. Concrete cryptography remains a security
review decision.

## OPEN Decisions Requiring Human And Legal Review

- OD-024: approve the accountable legal/talent governance, executable rights taxonomy,
  evidence workflow, provider mapping, revocation/offline convergence, and data policy.
- Confirm or replace the proposed sole mint boundary, terminal `VoiceRightsDecision`, private
  capability enforcement, and its composition with `ApprovedResponse` and voice
  `SurfaceAuthorization`.
- Approve the immutable definition/grant versus authoritative current-state/epoch model, atomic
  transition/outbox constraints, and concurrent revocation semantics.
- Applicable jurisdictions and the legal interpretation of consent, license, publicity, performer, copyright, neighboring, biometric/privacy, and contract rights.
- Who may submit, verify, approve, suspend, revoke, and audit a grant; role design depends on ADR-019.
- The normalized rights taxonomy and how free-text contractual restrictions map to executable deny/allow constraints.
- Territory semantics for worldwide internet distribution, unknown viewer location, geofencing, retransmission, and platform CDN behavior.
- Platform, destination-account, simulcast, commercial-purpose, sponsor, archive, replay, clip, export, promotional, rehearsal, language, and localization vocabularies.
- The derivative-use capability vocabulary and which operations each real grant permits.
- Consent capture, identity/signatory verification, evidence integrity, renewal, supersession, and dispute workflows.
- Revocation legal effect, convergence SLO, task lifetime, offline/disconnected behavior, cache invalidation, and incident escalation.
- Whether and when rights revocation requires deletion, quarantine, preservation, takedown, retraction, or legal hold for source and generated artifacts.
- Retention, residency, access, deletion, disclosure, and audit requirements for restricted evidence and voice data.
- Provider-specific contract mapping, regional availability, data processing, model-training restrictions, and fallback eligibility; no vendor is selected here.
- Exact metadata/event/API schemas and persistence constraints; migrations require a separate linked ADR.
- Rights-policy ownership, review cadence, and production acceptance signatories.

No vendor, jurisdictional conclusion, license template, consent default, territory default, derivative permission, retention duration, or operational SLO is selected by this ADR.

## Acceptance Evidence

This ADR may be accepted as a technical control direction only after human legal, talent, privacy, safety, security, product, and operations reviewers confirm that its model is suitable. No voice may enter production until evidence includes:

- a human-approved normalized rights taxonomy and mapping procedure for the relevant real grant;
- a verified evidence chain linking talent/rights holder, grant version, voice-profile version, policy version, and authorized reviewer;
- protected-symbol/import/compiler-AST and database tests proving a voice-use authorization cannot
  be forged, serialized as a capability, or backed by a missing, non-allowed, mismatched,
  indeterminate, or stale rights decision;
- concurrency and recovery tests proving activation, suspension, expiry, supersession, and
  revocation atomically advance the authoritative epoch and cannot be rolled back by cache,
  replica, retry, restore, or reordered invalidation;
- positive and negative fixtures across territory, platform/account, time, purpose, language, simulcast, archive/replay, and each derivative capability;
- property and contract tests proving missing, unknown, conflicting, excluded, expired, suspended, and revoked scope always denies use;
- boundary tests proving synthesis cannot omit `approved_response_id` or voice-use authorization and cannot receive raw candidate text;
- composed-chain tests proving synthesis, artifact commit, dispatch, playback, replay, and export
  require mutually bound content, rights, and surface authorization with the earliest deadline;
- provider retry/fallback tests proving rights and safety are re-evaluated for the actual replacement;
- expiry and non-extension tests across approval, authorization, synthesis, cache, dispatch, queue, reconnect, playback, replay, and export;
- revocation tests that cancel synthesis, invalidate caches, flush queued tasks, reject stale rights epochs, and require fresh authorization after recovery;
- network-partition and offline-rig tests measured against the human-approved revocation and watchdog policy;
- artifact substitution, signature, replay, session-binding, context-binding, and profile-version tests;
- archive, clip, promotional, export, localization, editing, and model-training tests proving ungranted operations cannot execute;
- access-control, purpose logging, evidence redaction, audit reconstruction, retention, deletion, and legal-hold tests under approved policy;
- rehearsal evidence using the same rights, safety, signing, dispatch, and immediate pre-playback checks as live mode;
- a protected human sign-off record naming the legal/talent authority that approved the concrete voice use.

## Consequences

- Voice rights become an enforceable runtime prerequisite rather than descriptive profile metadata.
- Safety approval cannot be mistaken for talent or licensing authorization, and rights approval cannot bypass content safety.
- Territory, platform, time, purpose, derivative use, consent, and revocation constraints remain traceable through synthesis and playout.
- Cached audio, archives, clips, and provider fallback require explicit authorization instead of inheriting permission silently.
- The additional checks, restricted evidence store, versioning, and revocation protocol increase implementation and operational complexity.
- Voice-profile, synthesis, archive/replay, and derivative-use implementation remain blocked until human/legal OPEN decisions and the corresponding acceptance evidence are complete.

## Informative Legal And Privacy References

These official Japanese sources are review inputs only. They do not settle VNova's applicable
law, contractual rights, consent sufficiency, or data classification:

- [Personal Information Protection Commission: APPI guidelines](https://www.ppc.go.jp/personalinfo/legal/guidelines_tsusoku/)
- [Agency for Cultural Affairs: copyright, performer, portrait, and publicity-right FAQ](https://www.bunka.go.jp/seisaku/bunka_gyosei/kibankyoka/faq/index.html?s=09)
- [Agency for Cultural Affairs: AI and copyright resources](https://www.bunka.go.jp/seisaku/chosakuken/aiandcopyright.html)
