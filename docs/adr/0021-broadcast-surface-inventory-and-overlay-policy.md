# ADR-021: Broadcast Surface Inventory And Overlay Policy

Status: Proposed

Priority: P1

Date: 2026-07-17

Sources: `AGENTS.md`, `vnova-review-handoff.md`, `docs/architecture/broadcast-surface-model.md`, ADR-008, ADR-016, ADR-017

This ADR is non-binding while its status is `Proposed`. No broadcast-surface implementation is authorized until this ADR is accepted or replaced through protected human review.

## Context

VNova is a broadcast control system. Harm can reach the audience through voice, visible text, sounds, graphics, scene changes, or avatar behavior even when generated speech is safe. Treating voice as the only moderated output would leave direct paths from untrusted platform data, operator input, templates, or adapters to the broadcast.

Display names and usernames are especially dangerous because their written form, normalized form, and spoken pronunciation can differ. Approval of a viewer message does not make its author's name safe to display or speak.

Platform chat widgets and browser sources commonly render platform data outside the application's moderation, expiry, audit, and emergency controls. That path cannot satisfy VNova's fail-closed requirements.

## Decision

Every audience-visible, audience-audible, or audience-perceivable action controlled by VNova is a **broadcast surface**. Every broadcast surface is registered, moderated, authorized for a concrete presentation, bounded by expiry and session context, observable, and independently disableable.

The initial surface inventory is:

| Surface                            | Required authorization and provenance                                                                                                                                                                                           |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Voice                              | Independent unexpired content approval, voice-use authorization, and final-presentation surface authorization; TTS/media receive reviewed IDs, with `approved_response_id` as the sole content authority, never generated text. |
| Captions                           | A surface authorization bound to an approved response or approved media timeline and to the exact caption transformation.                                                                                                       |
| Chat overlay                       | A VNova-owned, moderated, delayed presentation item, if a human elects to implement the overlay at all.                                                                                                                         |
| Alerts                             | A reviewed template version plus separately screened and escaped dynamic fields.                                                                                                                                                |
| Scene and graphic text             | A reviewed template or approved content reference plus constrained, screened dynamic fields.                                                                                                                                    |
| Spoken usernames and display names | A separately normalized, screened, pronunciation-safe rendering bound to the speech context.                                                                                                                                    |
| Avatar and scene actions           | A policy-authorized action from a closed vocabulary, with session and expiry binding.                                                                                                                                           |

Pre-recorded or generated sound, image, and video playback is not implicitly authorized by this list. It remains disabled until a protected ADR amendment defines its identifier-only approval and rights model consistently with `AGENTS.md` and ADR-008.

A versioned broadcast-surface registry maps every output adapter, renderer, OBS source, and VTube Studio action family to one of the accepted surface kinds. An unregistered surface, renderer, adapter, template, or action is disabled. Adding a new surface is a protected architecture change, not a configuration shortcut.

The production OBS scene collection is part of this inventory. Every enabled source is classified
as a VNova-managed surface, a reviewed static/non-interactive source, or an explicitly governed
external source. Unknown sources, platform chat/browser widgets, and sources capable of
unreviewed remote content fail the live-readiness preflight even when VNova did not create them.

## Surface Authorization

`packages/safety` is the sole package permitted to mint a `SurfaceAuthorization`. This is an additional capability and does not replace, recreate, or weaken `ApprovedResponse`.

`SurfaceAuthorization` follows the same defense-in-depth ownership model proposed for
`ApprovedResponse`:

- A terminal persisted `SurfaceDecision(decision = authorized)` records the exact normalized
  presentation, final-context moderation evidence, policy version, source provenance, surface,
  destination, timing, and decision actor.
- The authorization has a private constructor and private mint capability under
  `packages/safety`; other packages receive only a frozen nominal view in-process.
- Process, queue, database, event, API, wire, and renderer boundaries carry its reviewed
  identifier and validated DTO, never a rehydratable capability or arbitrary presentation
  payload.
- Rehydration is safety-owned and revalidates the decision chain, payload digest, session/epoch,
  destination, policy version, emergency state, and expiry.
- The eventual database uses a unique/composite constraint or equivalent to prove that an
  authorization references the literal authorized terminal decision for the same presentation.
  A plain provenance reference is insufficient.
- The decision, authorization, audit, and required outbox evidence commit atomically. Any schema
  requires a linked migration ADR.
- Python/TypeScript protected-symbol checks, nominal typing, import boundaries, CODEOWNERS, and
  database tests reject construction, assertion, cloning, proxying, conflicting identity reuse,
  and non-safety mint calls.

The proposal to place this mint capability in `packages/safety` itself requires explicit protected
acceptance under OD-023. A replacement may define another equally protected sole mint boundary,
but it may not distribute mint authority among renderers, adapters, the console, or providers.

Each authorization is immutable and binds at least:

- authorization ID and surface kind;
- stream-session ID and session epoch;
- source provenance IDs, such as approved-response, approved-asset, template, or moderated-input IDs;
- a digest of the exact normalized presentation payload;
- renderer, template, pronunciation-map, and policy versions as applicable;
- automated or operator decision provenance;
- intended audience channel and platform context;
- `not_before` and `not_after`;
- a bounded presentation end or clear condition for persistent visible surfaces;
- any surface-specific constraints required to render without changing meaning.

Authorization is presentation-specific. Approval for one surface does not authorize another surface, and approval for one session, platform context, template version, payload digest, or time window cannot be reused outside that binding.

`not_after` is the last instant at which a presentation may start or restart. A visible item that starts validly may remain only until its separately authorized presentation end or clear condition. That condition does not permit a delayed start, replay, or resurrection after `not_after`.

An explicitly reviewed lossless rendering transformation may reuse source moderation evidence, but it still requires a surface authorization. A transformation that can change words, meaning, pronunciation, emphasis, markup, or audience interpretation re-enters the applicable moderation policy.

Dispatch and rendering contracts carry reviewed identifiers, authorization metadata, and constrained rendering fields. They do not carry raw candidate output or unmoderated platform payloads. Exact contracts require protected event-schema and package-contract review before implementation.

## Composed Voice Authorization

Voice requires three independent capabilities in this order:

```text
ApprovedResponse
  -> VoiceUseAuthorization
  -> final sanitized/pronunciation-safe linguistic rendering
  -> SurfaceDecision(decision = authorized)
  -> SurfaceAuthorization(surface = voice)
  -> synthesis attempt and immutable artifact
  -> signed SpeechTask
  -> stage-host acceptance and immediate pre-playback checks
```

- `ApprovedResponse` proves content safety; it grants neither voice rights nor a presentation.
- `VoiceUseAuthorization` proves that the selected voice and intended distribution/use context fit
  a current reviewed grant; it neither approves content nor a rendered surface.
- Voice `SurfaceAuthorization` proves that the exact final linguistic rendering, pronunciation,
  destination, session/epoch, policy versions, source content approval, and rights authorization
  are permitted for presentation; it grants neither broader rights nor different content.

The public approved-media/TTS orchestration boundary receives `approved_response_id` as its sole
linguistic content authority plus `voice_use_authorization_id` as non-content metadata. Inside the
trusted gateway, it deterministically computes the final rendering, obtains the bound
`surface_authorization_id`, and only then invokes the private provider adapter. It resolves and
revalidates all three chains and refuses the external call unless their bindings agree. Their
effective `not_after` is the earliest content, rights, surface, session, and intended-use deadline;
no downstream step extends it.

The surface decision/authorization must commit before an external TTS call. The immutable
synthesis attempt, artifact, media authorization, and dispatch record bind all three authorization
IDs and the exact linguistic-input and artifact digests. No transaction may mint one capability
by inferring the missing decisions of another.

The current ADR-008 `SpeechTask` allowlist does not yet admit these additional identifiers or a
generic surface command. ADR-011 acceptance, OD-021 resolution, protected ADR-008/contract
amendment, and generated cross-language fixtures are explicit prerequisites. Until then, this
composition authorizes no synthesis, task field, renderer command, or stage-host behavior.

## Surface-Specific Rules

### Voice

- Voice follows ADR-008's full `CandidateResponse` to `ApprovedResponse` trust chain.
- The voice surface authorization references the same unexpired `approved_response_id`.
- Synthesis retry, provider fallback, cache reuse, reconnect, and queueing do not extend the source deadline.
- SSML, provider markup, and pronunciation instructions are sanitized at the media boundary.
- Manual operator speech crosses the same safety and surface-authorization paths; the console has no direct speech path.

### Captions

- Captions derive only from an approved response or an approved media timeline.
- Raw candidate text, raw model tokens, partial unsafe generation, and raw platform messages never feed captions.
- Timing-only segmentation may be treated as lossless only when a reviewed transformer proves that it cannot alter content.
- Redaction, translation, summarization, spelling expansion, emoji narration, or other semantic transformation requires its own moderation decision and provenance.
- Caption start eligibility is no later than the source approval expiry. Once validly started, caption clear timing is bound to the approved media timeline; it cannot authorize a delayed start or replay. Expired or superseded captions are cleared, not left on screen.

### Chat Overlay

- Whether VNova implements a chat overlay or omits it remains a human product-and-safety decision under OD-006.
- A raw platform overlay is forbidden in either outcome.
- OBS browser sources, platform widgets, embedded chat pages, or third-party overlays that fetch and render platform chat outside VNova moderation are forbidden.
- If implemented, VNova owns ingestion, normalization, moderation, delay, authorization, rendering, removal, and audit correlation end to end.
- The message body, display name, badges, emotes, links, and their final combined rendering are treated as untrusted fields and checked under the overlay policy.
- Every item has a deliberate delay and an expiry. Delay never extends expiry.
- The renderer accepts only a closed schema, escapes active content, rejects unknown fields, and cannot execute viewer-provided markup, URLs, scripts, styles, or media.
- Rejection, moderation timeout, renderer uncertainty, stale authorization, or control-plane loss produces no new overlay item. Existing expired content is cleared to a neutral reviewed state.

### Alerts And Scene Text

- Templates are immutable, versioned, reviewed artifacts.
- Dynamic fields are normalized, screened, length-bounded, escaped, and authorized in the final rendered context.
- A reviewed template does not make viewer-provided values safe.
- Unknown placeholders, renderer extensions, active markup, control characters, bidirectional-control attacks, and layout-breaking values fail closed.
- Sponsor, legal, emergency, and other specially governed content obey their category-specific autonomy and authorization caps once those policies are human-approved.

### Spoken Usernames And Display Names

- A platform display name is untrusted input even when the associated message is approved.
- Screening occurs after Unicode normalization and again on the final pronunciation-safe rendering in its surrounding spoken context.
- Screening covers written and phonetic forms, control and bidirectional characters, homoglyphs, markup and SSML injection, deceptive spacing, and unsafe concatenation with surrounding words.
- Pronunciation dictionaries and substitutions are immutable and versioned; viewer text cannot inject pronunciation or provider markup.
- A name that cannot be rendered safely is omitted or replaced by a reviewed generic form. The system does not spell, transliterate, or guess its pronunciation as a bypass.
- Name approval is scoped to the normalized value, pronunciation version, policy version, language context, session, and expiry; it is not permanent viewer-memory authority.

### Avatar And Scene Actions

- Actions come from a versioned closed vocabulary with policy-defined parameters.
- Arbitrary expressions, script names, OBS commands, URLs, hotkeys, or adapter payloads cannot be supplied by a model or viewer.
- Actions may be authorized independently of speech, but remain bound to session epoch, expiry, provenance, and emergency state.
- Action fallback paths cross the same surface-authorization gate as primary paths.

## Renderer Trust Matrix

The initial-production proposal terminates every VNova-controlled broadcast surface at
`stage-host`, because it already owns the OBS and VTube Studio trust boundary. A cloud service,
operator browser, platform API, or third-party browser source may not render directly to the
audience.

| Surface                  | Initial renderer and owner                  | Identifier-only verification path                                                                | Local clear and offline behavior                                                             |
| ------------------------ | ------------------------------------------- | ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| Voice                    | stage-host playback/OBS adapter             | Signed `SpeechTask`; all composed authorization IDs and artifact digest after ADR-011 amendment  | E-stop cuts output and flushes; disconnect watchdog applies; no unknown/offline new work     |
| Captions                 | stage-host-owned OBS renderer               | Signed presentation command referencing authorization, approved source/timeline, renderer/digest | Clear at timeline/end/expiry; clear on uncertain state; no new disconnected cloud content    |
| Moderated chat overlay   | stage-host-owned VNova renderer, if enabled | Signed presentation command referencing exact authorized item and renderer version               | Local TTL/clear survives link loss; no raw platform fetch; watchdog/emergency scope reviewed |
| Alerts and scene text    | stage-host OBS adapter/renderer             | Signed presentation command referencing template/version, screened-field digest, authorization   | Bounded end/clear; unknown template or link state moves to neutral reviewed presentation     |
| Spoken username          | Composed into authorized voice path         | Voice chain binds normalized written/phonetic form and pronunciation-map version                 | Same cut, expiry, and reconnect rules as voice                                               |
| Avatar and scene actions | stage-host VTube Studio/OBS adapters        | Signed closed-vocabulary command referencing authorization, exact action, parameters, and expiry | Emergency/watchdog applies to accepted scope; expired or unknown actions are cleared/stopped |

The exact signed command schemas, protocol lanes, renderer process isolation, and interruption
scope are governed by ADR-011, ADR-015, OD-015, and OD-021. They cannot be improvised inside an
OBS scene, browser source, or adapter.

If a later capability needs a non-rig renderer, its ADR must name the deployable owner, trust
boundary, authenticated transport, sole verifier, local/audience clear mechanism, expiry behavior,
partition behavior, emergency scope, and incident evidence. It must provide safety at least
equivalent to the stage-host path.

## Data And Audit Requirements

The eventual data model separates source content, moderation evidence, surface authorization, rendering state, and audit metadata.

At minimum, the system records:

- surface kind, authorization ID, source IDs, content digest, and policy version;
- normalization and renderer versions;
- decision actor or automated evaluator identity;
- session, epoch, timing, display/removal outcome, and failure reason;
- the adapter and destination identity needed to reconstruct where the item could appear.

ADR-017 governs data classification and retention. Immutable audit records use identifiers, hashes, versions, outcomes, and actor metadata; they do not duplicate raw viewer messages, viewer-memory content, restricted candidates, or unnecessary display-name content. Exact content retention, deletion behavior, and incident holds remain human privacy and legal decisions.

An artifact/payload integrity digest and a privacy-preserving audit reference are different
controls. A plain hash of a low-entropy username, short caption, or template field can remain
linkable and is not automatically safe for ordinary logs. OD-023 must approve classification,
domain separation or keyed-reference strategy where needed, key custody, access, retention, and
deletion. A digest proves byte equality only within its trusted provenance; it does not prove that
moderation or evidence capture was legitimate.

## Authorization And Ownership

- `session-runtime` owns input moderation, safety invocation, surface-authorization requests, expiry, and approved dispatch for its `StreamSession`.
- `packages/safety` owns surface policy evaluation and the only mint capability for `SurfaceAuthorization`.
- `stage-host` is the only consumer of `SpeechTask` and owns final local playback plus OBS and VTube Studio adapters.
- The operator console may request or review a presentation but cannot directly write to an audience-facing renderer.
- Operators cannot widen an authorization, alter an authorized payload, extend expiry, or bypass moderation. Any changed presentation requires a new authorization.
- Roles for reviewing templates, policy versions, and exceptional content depend on ADR-019 and human approval.

## Enforcement

Enforcement is layered:

1. Package and contract boundaries reject raw candidate or raw platform content at dispatch and adapter interfaces.
2. Private mint ownership, nominal capability types, protected-symbol checks, and database
   constraints reject a missing, nonterminal, mismatched, forged, or non-safety surface decision.
3. The surface registry and production-scene preflight deny unregistered adapters, renderers, OBS
   sources, templates, and actions.
4. Safety verifies normalized content, final rendered context, provenance, policy version, session epoch, and deadline before minting authorization.
5. Dispatch rehydrates and revalidates the full authorization chain and expiry before enqueue.
6. After ADR-011/OD-021 contract approval, `stage-host` verifies the signed identifier-only
   command, every required authorization ID, session epoch, payload digest, and expiry at
   acceptance and immediately before presentation.
7. Renderers use closed schemas, contextual escaping, bounded resources, and no viewer-provided active content.
8. Repository checks inspect OBS and adapter configuration so a raw platform widget cannot be introduced silently.
9. Rehearsal mode exercises the same authorization, signed protocol, and renderer path as live mode.

All primary, retry, manual, pre-approved, and fallback paths pass through the same surface-specific authorization gate. A fallback may use only separately reviewed content and cannot expose the rejected source.

## Emergency And Failure Behavior

- No moderation verdict or no valid surface authorization means no presentation.
- A moderation timeout, unavailable safety dependency, unknown policy version, digest mismatch, invalid signature, stale session epoch, or expired authorization fails closed for that surface and emits an auditable failure.
- Local e-stop immediately cuts voice and the rig-controlled audience-facing actions within its accepted scope, flushes queued work, and prevents stale work from resuming.
- Cloud freeze stops new surface generation and dispatch. Partition handling follows ADR-016 and the future ADR-015.
- Every surface has an operator-visible disable control and a renderer-level clear or neutral-state operation.
- If a renderer cannot prove its current item began under a valid authorization and remains within its authorized presentation interval, it clears or hides the item.
- Disabling one failed surface need not halt independently safe surfaces unless policy or emergency state requires a broader stop.
- Recovery creates fresh authorization context; it never revives flushed, expired, superseded, or unknown work.

Exact disable latency, overlay delay, expiry windows, and incident escalation thresholds are policy and SLO decisions and are not set by this ADR.

## Observability

Each surface exposes correlated events or equivalent telemetry for authorization requested, approved, denied, expired, dispatched, presented, removed, cleared, and failed. Metrics distinguish policy rejection, timeout, stale content, renderer rejection, signature failure, and emergency removal.

Telemetry includes IDs, hashes, versions, timings, and destinations needed for reconstruction without copying restricted content into ordinary logs. Rehearsal recordings and rendered snapshots are restricted evidence whose retention requires human-approved policy.

## OPEN Decisions Requiring Human Review

- OD-006: omit the chat overlay or implement a VNova-owned moderated overlay.
- OD-023: approve the closed registry and each surface's moderation, transformation, expiry,
  disable, accessibility, observability, and retention policy.
- Confirm the sole mint package, terminal `SurfaceDecision` model, `ApprovedResponse` /
  `VoiceUseAuthorization` / `SurfaceAuthorization` composition, atomic persistence constraints,
  and private-capability enforcement before accepting the authorization design.
- Accept the per-surface renderer location, protocol/verifier, offline behavior, full OBS-source
  inventory, and ADR-015 emergency/interruption scope.
- Surface-specific moderation policies, categories, thresholds, normalization rules, and operator-review requirements.
- Overlay delay, item lifetime, queue size, flood behavior, and neutral-state presentation.
- Caption transformation policy, accessibility requirements, language handling, and whether any translation path is authorized.
- Username/display-name normalization, pronunciation policy, generic fallback wording, language coverage, and adversarial lexicon ownership.
- Alert, scene-text, action, and template ownership plus category-specific autonomy caps.
- Exact surface expiry, clear, disable, and incident-response SLOs.
- Retention and deletion rules for rendered content, screenshots, rehearsal captures, and moderation evidence under ADR-017.
- Authentication and authorization roles under ADR-019.
- The identifier-only authorization model for future sound, image, and video surfaces.
- Exact event and API contracts; any schema or migration requires its own protected review and linked ADR.

No moderation vendor, policy default, numeric threshold, or retention duration is selected by this ADR.

## Acceptance Evidence

This ADR may be accepted as an architecture decision before implementation, but a surface may not enter production until its evidence set includes:

- a reviewed, versioned inventory proving every audience-facing adapter, renderer, OBS source, and action maps to an accepted surface;
- construction/import/compiler-AST and database tests proving a surface authorization cannot be
  forged, serialized as a capability, or backed by a missing, non-authorized, mismatched, or
  nonterminal surface decision;
- composed voice-chain tests proving content approval, rights authorization, and voice surface
  authorization are all present, mutually bound, atomically traceable, and constrained by the
  earliest expiry;
- contract and static-boundary tests proving raw candidate text and raw platform payloads cannot reach TTS, dispatch, stage-host, or renderer interfaces;
- configuration tests rejecting platform chat widgets and browser sources that bypass VNova;
- valid/invalid contract fixtures for every enabled surface and authorization binding;
- primary, retry, manual, and fallback tests proving identical moderation enforcement;
- expiry, payload-substitution, session-epoch, replay, disconnect, recovery, and immediate pre-presentation checks;
- red-team coverage for usernames, display names, Unicode controls, homoglyphs, markup/SSML, emotes, links, template injection, unsafe concatenation, and layout/resource exhaustion;
- renderer security tests for closed schemas, escaping, unknown fields, and active-content rejection;
- fault injection proving safety or renderer uncertainty produces no new audience output and clears stale content;
- local e-stop and cloud-freeze rehearsal evidence for every enabled surface;
- target renderer and OBS-scene preflight evidence proving every enabled source has the accepted
  owner, verifier, clear path, partition behavior, and emergency scope;
- telemetry reconstruction proving what was authorized, shown, removed, and why without leaking restricted content;
- protected review by safety, product, operations, privacy, and affected stage-host/adapter owners.

## Consequences

- Broadcast safety becomes an end-to-end property of every audience-facing path, not only speech.
- Raw platform chat can never be used as an expedient overlay.
- New surfaces require explicit inventory, contracts, moderation, expiry, observability, emergency behavior, and review before activation.
- Surface-specific authorization adds latency and operational complexity but makes renderer and adapter bypasses detectable and testable.
- Chat overlay, future media surfaces, and their policy defaults remain disabled until their OPEN decisions and acceptance evidence are closed.
