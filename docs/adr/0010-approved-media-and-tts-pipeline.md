# ADR-010: Approved Media And TTS Pipeline

Status: Proposed

Date: 2026-07-17

Sources: `AGENTS.md`, `vnova-review-handoff.md`, ADR-007, ADR-008, ADR-016, ADR-017, ADR-018

This ADR is non-binding while its status is `Proposed`. It authorizes no live TTS provider,
voice, object-store, or broadcast adapter.

## Context

Approval of text is not sufficient by itself to make an audio artifact safe to play. The
system must preserve approval identity, content integrity, expiry, voice authorization, and
provenance across synthesis, object storage, dispatch, download, and local playout.

Passing raw generated text into a generic TTS helper would erase the most important safety
boundary. Retrying synthesis with a different provider, accepting partial output, or
reusing an old artifact could also detach media from the safety decision that authorized
it.

## Decision

VNova uses an identifier-only approved-media pipeline. Public TTS and media interfaces take
`approved_response_id` as the sole content authority; they never accept candidate text,
generated text, SSML, captions, or an unrestricted text field.

For initial production behavior, synthesis begins only after the complete response has
passed the safety gate. Sentence-chunked safety and TTS remain outside this ADR and require
the separate decision described by ADR-018.

The approved speech path is:

```text
approved_response_id
  -> trusted content/rights/session resolution and expiry check
  -> deterministic normalization, sanitization, and pronunciation rendering
  -> terminal SurfaceDecision + exact voice SurfaceAuthorization
  -> immutable synthesis attempt
  -> bounded TTS provider call
  -> immutable audio/timing artifact plus digest
  -> committed media authorization
  -> signed identifier-only SpeechTask
  -> stage-host verification and pre-playback expiry check
```

Failure at any step produces no playable speech task.

### Trusted Resolution

Only the reviewed TTS gateway may resolve an approved response into linguistic content for
synthesis. Resolution revalidates:

- persisted candidate metadata, the approving `SafetyDecision`, the safety-owned
  `ApprovedResponse` record, and its immutable approved-content snapshot/reference;
- selected-candidate and stream-session identity;
- policy/provenance required by ADR-008;
- terminal voice-rights decision, `VoiceUseAuthorization`, current rights epoch, and exact
  voice-profile/use-context binding under ADR-022;
- current emergency/session epoch and cancellation state where applicable;
- authoritative `not_after`, which may be shortened but never extended.

The resolved text exists only inside the trusted approved-media/TTS gateway boundary. No provider
or object-store call occurs until final rendering and voice-surface authorization complete. Text
is not copied into public commands, events, queue records, `SpeechTask`, URLs, ordinary logs, or
stage-host storage. If the approved-content snapshot is unavailable or disagrees with its
decision/candidate digest and provenance, the gateway cannot reconstruct it from candidate audit,
logs, provider history, media, or archive artifacts and creates no synthesis attempt.

### Synthesis Request And Attempts

The public synthesis-orchestration command contains the approved response identifier as its sole
content authority and reviewed non-content metadata such as voice-use-authorization, request, and
session identities. It cannot supply a voice surface authorization that has not yet been computed
for the final rendering. Voice and provider/model profiles are resolved from immutable, approved
session/policy configuration rather than arbitrary caller-supplied strings. Text-shaped escape
fields are forbidden.

After the trusted gateway creates the exact final rendering, `packages/safety` returns the
terminal surface decision and authorization. Only then may the private provider invocation use the
resolved linguistic input, the surface-authorization ID, and its exact digest. This private call is
inside the provider gateway and is not an exported raw-text TTS/media interface.

Each primary, retry, or fallback provider call creates an immutable synthesis attempt only after
its exact final rendering is surface-authorized. The attempt records provider-neutral outcome,
timing, configuration, content/rights/surface authorization IDs, rendering digest, and usage/cost
evidence. A retry or fallback repeats resolution, rendering, and authorization for the actual
provider configuration; it does not reuse a stale authorization snapshot.

Provider SDKs remain inside TTS provider adapters under ADR-007. Every provider and object
storage call has an explicit timeout bounded by the remaining approval deadline.

### Text And Markup Handling

Approved linguistic content is treated as text, not executable provider markup.

- Viewer- or model-originated markup, control characters, SSML, phoneme tags, URLs, and provider
  directives are rejected or transformed only by a deterministic, versioned policy before surface
  authorization.
- Provider markup, when required, is constructed internally and deterministically only from the
  final authorized linguistic rendering and policy-owned structured controls.
- A provider fallback cannot translate, summarize, rewrite, decorate, or add words.
- Pronunciation handling and spoken usernames use reviewed structured data and the
  broadcast-surface policy; they cannot append unapproved text.
- Sanitizer, normalization, pronunciation-map, structured-control, and provider-renderer versions
  plus the digest of the exact synthesized linguistic input are retained as restricted
  provenance.

Canonical escaping may proceed only when a reviewed transformer proves that it preserves the
authorized spoken linguistic sequence and meaning. Any transformation that can change words,
pronunciation, emphasis, meaning, or audience interpretation creates a new candidate and returns
through the complete safety gate.

### Final Rendering And Surface Authorization

The gateway computes one immutable `FinalVoiceRendering` before any external TTS call. It binds
the exact linguistic sequence, pronunciation decisions, language, sanitizer/normalizer versions,
structured synthesis controls, selected voice/provider renderer versions, and canonical digest.

The gateway submits that closed rendering plus the existing content and rights authorization IDs
to `packages/safety`. A terminal voice `SurfaceDecision(decision = authorized)` and
`SurfaceAuthorization` must bind the exact rendering digest and every version above.

- A denied, indeterminate, timed-out, mismatched, or unpersisted surface decision produces no
  provider attempt.
- Surface decision/authorization, audit, and outbox evidence commit before the external call.
- The authorization expires at the earliest content, rights, surface, session, and use-context
  deadline.
- A provider retry, fallback, voice/profile change, pronunciation change, sanitizer change, or
  renderer-version change recomputes the final rendering and obtains a fresh surface
  authorization.
- The exact private provider input is deterministically derived from the authorized rendering. A
  digest mismatch or non-deterministic derivation is an integrity failure.

### Artifact Commit

A successful attempt produces immutable audio and, where supported, immutable timing,
viseme, or caption-alignment artifacts.

- Bytes are staged before an artifact is marked ready.
- The system computes and records an integrity digest over the exact immutable bytes.
- The committed artifact record binds the approved response, safety decision, synthesis
  attempt, voice-rights decision/authorization/epoch, voice surface decision/authorization,
  voice/profile versions, sanitizer version, media format metadata, storage object version,
  digest, creation provenance, and non-extended earliest `not_after`.
- A partial, mutable, unverified, or uncommitted object is never dispatchable.
- Deduplication or cache reuse is permitted only when the complete reviewed synthesis
  identity matches and the current approval, rights, session, and expiry checks still pass.
- Object storage is a media store, not the authority for approval or queue state.

Captions derive only from the approved response or its approved media timeline. Raw
candidates and raw platform chat cannot become caption or overlay content.

### Media Authorization And Dispatch

Media readiness and its immutable dispatch-eligibility record commit before dispatch. The record
binds the ready artifact to the exact content approval, current rights decision/authorization
epoch, surface decision/authorization, session/emergency epoch, rendering and artifact digests,
and earliest expiry. It is not a new content or rights approval and cannot infer a missing gate.

Cache reuse, media-authorization rehydration, dispatch, retry, and every `SpeechTask` issuance or
reissuance atomically revalidate:

- the complete persisted candidate, safety decision, and approved-response chain;
- the current voice-rights state/epoch and matching allowed rights decision/authorization;
- the matching authorized voice-surface decision, final-rendering digest, renderer versions, and
  authorization;
- current session/emergency/authorization epochs, cancellation, effective mode, and intended
  destination/use context;
- artifact readiness, immutable storage version, artifact digest, and non-extended earliest
  expiry.

Any mismatch, suspension, revocation, invalidation, cancellation, uncertainty, or expiry makes the
artifact non-dispatchable. The runtime creates and signs a `SpeechTask` only after this validation
succeeds against one consistent database snapshot or equivalently serialized aggregate state.

The task carries identifiers, artifact integrity, ordering, timing, session epoch, and
signed authorization under ADR-008 and ADR-011. It contains no raw text or media bytes.
`stage-host` is the sole `SpeechTask` consumer under ADR-016.

The current ADR-008 `SpeechTask` allowlist does not yet include the proposed rights and surface
authorization identifiers. ADR-011 acceptance, OD-021 resolution, and protected ADR-008/contract
amendment are prerequisites; this ADR does not widen the current task schema.

The stage host downloads through a scoped, time-bounded authorization, validates the digest,
checks task authorization and expiry at acceptance, and checks expiry again immediately
before playback.

### Fallback And Pre-Approved Material

TTS fallback preserves the same approved linguistic content and repeats all approval,
rights, sanitizer, timeout, and artifact checks. A failed or partial primary artifact cannot
be concatenated with fallback output.

Fallback scenes, silence, and pre-approved canned audio are separate, versioned broadcast
paths. They require explicit provenance, expiry/enablement rules, and audit; they are not a
way to pass arbitrary text around this pipeline.

## Enforcement

- Public Python and TypeScript TTS/media contracts expose identifiers and reviewed
  structured controls only. Boundary checks reject raw-text, candidate, SSML, generic
  payload, and text-alias fields.
- Static type tests prove a caller cannot pass `CandidateResponse` or a string where
  `approved_response_id` is required.
- Provider-SDK import rules confine TTS SDKs to reviewed adapters.
- Database constraints bind ready media authorization to a valid approved response,
  completed attempt, allowed current rights decision/authorization/epoch, authorized surface
  decision/authorization/rendering digest, immutable object version/digest, matching session/use
  context, and non-extended earliest expiry.
- The task signer accepts only the validated dispatch-eligibility record ID and rechecks its
  complete chain in the same serialized operation; it cannot sign directly from an artifact ID.
- Object-store integration tests prove that partial uploads and mutable replacement cannot
  become ready artifacts.
- Sanitizer fixtures include SSML injection, Unicode/control characters, spoken username
  attacks, and provider-specific markup.
- CODEOWNERS and repository rules require human review for contracts, safety, provider
  gateways, voice policy, and stage-host adapter behavior.

## Failure Behavior

- Missing, invalid, cancelled, mismatched, or expired content, rights, surface, media, session, or
  emergency authorization fails closed before synthesis and again before task signing.
- TTS timeout, provider failure, cancellation, malformed output, or incomplete stream
  creates no ready artifact and no `SpeechTask`.
- Sanitizer uncertainty or unsupported markup rejects the attempt; it never passes content
  through unchanged by default.
- Object upload, metadata commit, integrity, or authorization failure leaves the object
  non-dispatchable. Orphan cleanup cannot promote it.
- A late completion after cancellation or expiry is retained only as governed diagnostic
  evidence and cannot be authorized.
- Content/rights/surface authorization, rights/session epoch, artifact/rendering digest, signature,
  or expiry mismatch is rejected by `stage-host` after the protected protocol extension; playback
  does not start.
- Media fetch timeout or corruption produces no playback. The runtime may use only a
  separately approved fallback path.
- E-stop and watchdog actions interrupt/flush local playback under ADR-015/016; reconnect
  never revives flushed or expired artifacts.

## Consequences

- TTS gateways receive privileged, narrowly scoped access to approved content, while all
  callers and transport boundaries remain identifier-only.
- Artifact storage and metadata require transactional readiness semantics and integrity
  verification.
- Re-synthesis and fallback are auditable attempts rather than invisible provider behavior.
- Voice rights, media retention, format choices, and protocol security must be approved
  before production media work.
- The design prefers silence or a reviewed fallback to playing unverifiable or stale audio.
- Implementation remains blocked until ADR-007, ADR-008, this ADR, the structural scope of
  ADR-018, ADR-011, ADR-021, ADR-022, OD-021 where the task contract applies, and any required
  migration ADR are accepted.

## OPEN Decisions

- OD-025: immutable storage, media formats, integrity/version profile, scoped transfer,
  cache/deduplication, interruption, and artifact lifecycle.
- TTS provider/model profiles and fallback eligibility under ADR-007.
- Voice profile, consent, territory, purpose, expiration, revocation, and licensing metadata
  under ADR-022.
- Object-storage implementation, media containers/codecs, audio characteristics, timing and
  viseme representation, and artifact versioning.
- OD-014: synthesis attempt eligibility/caps and backoff semantics.
- OD-035: synthesis timeout, scheduler-budget/deadline allocation, candidate/approval TTL, and
  clock values. These are not derived from OD-001 service-latency SLOs.
- OD-037/038: TTS/media resource reservations, queue/cache/object bounds, provider quota, and
  cost/billing enforcement where applicable.
- OD-007: whether sentence-chunked TTS is ever specified; it is not authorized here.
- OD-009: audio, timing, restricted-input digest, orphan, and cache retention/deletion
  policy.
- Artifact deduplication identity, cache policy, scoped-download mechanism, and cleanup
  procedure.
- Caption and other broadcast-surface authorization/reuse semantics under ADR-021.
- Exact behavior when voice rights are revoked after synthesis but before or after
  broadcast/archive use.

## Acceptance Evidence

Human acceptance requires:

- compile/static-boundary tests proving all public TTS/media calls are identifier-only;
- database tests rejecting every broken approval, attempt, artifact, rights, session, and
  expiry chain;
- race tests suspending/revoking rights, invalidating surface authorization, changing emergency or
  session epoch, cancelling work, and expiring the earliest deadline between synthesis, cache
  lookup, media authorization, dispatch, task signing, reissue, queue acceptance, and playback;
- end-to-end sanitizer fixtures for raw markup, SSML injection, spoken usernames, control
  characters, and provider directives;
- primary/fallback tests proving identical approved linguistic content and a fresh
  authorization check for every attempt;
- object-store fault tests for partial upload, timeout, replacement, corruption, orphaning,
  and commit races;
- digest substitution, expired authorization, wrong-session/epoch, replay, and immediate
  pre-playback rejection tests in rehearsal mode;
- a complete synthetic turn reconstructed from approval through simulated audio outcome;
- approved voice-rights, retention, format, timeout, provider, protocol-security, runbook,
  disable/rollback, and protected-review decisions;
- passing contract, type, import-boundary, integration, red-team, and artifact-integrity
  gates.
