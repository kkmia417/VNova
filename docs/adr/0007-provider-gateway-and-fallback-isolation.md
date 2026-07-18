# ADR-007: Provider Gateway And Fallback Isolation

Status: Proposed

Date: 2026-07-17

Sources: `AGENTS.md`, `vnova-review-handoff.md`, ADR-003, ADR-008, ADR-017, ADR-018,
ADR-024, ADR-025

This ADR is non-binding while its status is `Proposed`. It selects no vendor, model,
credential system, timeout value, or production fallback policy.

## Context

VNova depends on external generation, safety-classification, moderation, and speech
synthesis capabilities. Provider SDK types, implicit retries, streaming behavior, error
taxonomies, and request logging can otherwise leak into domain code and couple safety
behavior to one vendor.

Fallback is especially sensitive. A generation fallback that bypasses evaluation, a safety
classifier correlated with the generator, or a TTS fallback that accepts raw text can turn a
provider outage into unsafe speech. Every external call also consumes a finite turn deadline
and must have an explicit timeout.

## Decision

All LLM and TTS provider SDKs live only in named provider-adapter modules behind
capability-specific, provider-neutral gateway ports. Domain services, routes, workers,
`stage-host`, the operator console, and shared contracts do not import provider SDKs or
provider response types.

The initial gateway capabilities are separated by purpose:

- generation;
- model-based safety classification;
- input/broadcast-surface moderation where an external provider is used;
- TTS synthesis under ADR-010.

The gateways normalize requests, outcomes, usage, and errors. They do not decide safety
policy, mint `ApprovedResponse`, dispatch speech, or expose vendor objects to callers.

### Configuration And Identity

Every call references exact immutable `ProviderProfileDefinition` and `ModelConfigVersion`
identities through the pinned `ResolvedConfigurationSnapshot` proposed by ADR-024 rather than
embedding vendor names, model names, endpoints, credentials, or a mutable `latest` alias in
domain code.

The immutable definitions and resolved snapshot record enough provenance to reconstruct:

- capability and vendor identity;
- model/configuration version;
- gateway and normalization version;
- request/attempt identity;
- explicit timeout and outer deadline;
- usage and cost metadata available without storing secrets or unrestricted content.

Definition roots/versions, compatible activation-set versions, current scoped activation
state/epoch, and resolved work snapshots are separate records. Provider availability, circuit,
quota, latency, and cost health are operational state: they can restrict current eligibility but
cannot edit a definition, advance activation, widen a fallback graph, or silently select a new
snapshot. A retry/fallback remains pinned unless the accepted turn policy creates a new attempt
with a newly recorded snapshot and repeats all dependent evaluation.

Secrets are obtained through the approved secret boundary and are never stored in profiles,
events, prompts, logs, exceptions, or generated artifacts.

### Attempt Boundary

Every policy-level primary call, retry, fallback, and rewrite is a distinct immutable
`GenerationAttempt` or capability-equivalent domain attempt. Each logical domain attempt owns
one ADR-025 `EffectIntent`. A reviewed transport replay of the identical semantic request under
one downstream idempotency identity is a separate send-authorized `EffectAttempt` beneath that
intent; a changed request, provider, fallback, rewrite, or policy retry is a new domain attempt
and intent.

- A timeout, cancellation, transport error, provider rejection, or incomplete response
  produces no `CandidateResponse`.
- Only a complete, schema-valid generation outcome can be converted by domain code into a
  new immutable candidate.
- Partial streamed fragments remain inside the gateway and are never approval, media, or
  broadcast input.
- SDK-internal retries are disabled where possible. Any reviewed retry must expose each network
  send authorization as durable ADR-025 attempt evidence and cannot hide a send after the
  process has lost its composite actor fence.
- A call cannot extend the turn's authoritative deadline.

The gateway response is not a domain result until session runtime durably records an
`EffectResponseObservation` and a current active composite-fence transaction commits its
`EffectApplicationDisposition`. Crash after send authorization is possibly sent; crash after
response but before observation remains unknown. Recovery-only outcome queries use the closed
read-only/restrictive probe class and can never directly advance audience work.

Provider raw request/response content follows ADR-017 restricted-data handling. Ordinary
logs contain a prompt manifest, identifiers, hashes, token/usage counts, timings, and
normalized outcomes rather than full prompts or raw candidate content.

### Generation Fallback

Fallback eligibility is policy-controlled and is triggered only by a recorded technical
outcome that produced no complete candidate. Every complete generated output becomes an
immutable candidate and enters safety; it is not silently discarded so another provider can
be tried. A safety rejection does not shop the same content across providers. A
policy-authorized rewrite creates a new attempt and candidate lineage under ADR-003.

Every successful generation fallback produces a new candidate and enters the same complete
safety pipeline as a primary candidate. The gateway cannot return an approved type or call
media/TTS directly.

Fallback is attempted only while an eligible provider, retry budget, cost budget, and
unexpired turn deadline remain. Exhaustion produces a normalized terminal failure and the
mode/degradation behavior governed by ADR-020.

### Correlated-Failure Isolation

The model-based safety classifier uses a different vendor from the generator being judged.
The ADR-024 activation-set preflight validates this separation using exact provider definition
versions, compatibility profiles, and fallback combinations.

If no eligible independent safety-classification route is available, the result is
indeterminate and the autonomous path fails closed. A generation provider's own moderation
signal may be retained as evidence but cannot replace the independent safety layer.

Credentials, rate-limit pools, health state, circuit breakers, and fallback selection are
isolated by capability and provider profile so one provider failure cannot silently disable
both generation and judgment.

### Input And Surface Moderation

An external input or broadcast-surface moderation call is an immutable `ModerationAttempt`, not a
policy decision and never an authorization mint.

- The request binds its moderation purpose, normalized source/final-presentation digest,
  surface/destination and language context, policy/profile versions, attempt identity, explicit
  timeout, and outer deadline.
- The gateway returns a schema-valid provider-neutral classification with provenance, or a
  normalized `indeterminate`/technical failure. It cannot return `SurfaceAuthorization` or an
  implicit allow.
- Only a complete classification for the exact unchanged digest/context may enter the safety
  policy engine and terminal `SurfaceDecision` path under ADR-021.
- A retry or moderation-provider fallback is a new attempt over the same exact context. Any
  normalization, rendering, pronunciation, template, destination, or policy change requires a new
  digest and new moderation.
- Timeout, cancellation, malformed/partial output, quota failure, unavailable fallback, or
  disagreement that policy cannot resolve yields no authorized terminal surface decision and no
  presentation.
- Generation-provider moderation and platform moderation signals may be retained as evidence but
  cannot silently replace the reviewed independent surface/input moderation path.

All moderation provider logging, data transfer, regional processing, retention, and model-training
terms require the same privacy/profile review as other providers.

### TTS Fallback

The public TTS orchestration gateway accepts `approved_response_id` as its sole content authority,
never candidate or generated text. A reviewed voice-use-authorization ID is caller-supplied
non-content metadata; the exact surface authorization is obtained internally only after the
gateway computes the final rendering under ADR-010/021/022. Each primary or fallback synthesis
attempt revalidates the complete content, rights, surface, session, and non-extended
earliest-expiry chain before the private provider call.

A TTS fallback may change only reviewed synthesis configuration. It cannot rewrite,
translate, summarize, decorate, or otherwise change approved linguistic content. Any content
change requires a new candidate and full safety evaluation.

### Timeouts, Cancellation, And Concurrency

Every external call has both an explicit per-attempt timeout and an enclosing operation
deadline. The shorter remaining bound wins.

Cancellation is propagated to the adapter, but a late provider result is still recorded and
discarded rather than revived. Concurrency, queueing, retry, and circuit-breaker policies
must preserve capacity for safety and operator-control paths.

For ordinary session-owned calls, ADR-025 additionally requires `EffectIntent` creation and send
authorization under the exact current active composite actor fence plus exact-open
admission/source conflict, a conservative remaining lease horizon covering the entire attempt, a
send-authorized attempt before the first possible byte, durable response observation, and the
same active/open conflict before advancing application. Provider idempotency/outcome query is
used only under reviewed semantics. A possibly-sent non-idempotent attempt is not blindly
replayed by a successor.

A session-bound outcome query during closure/recovery is not an ordinary provider effect or a
generic health probe. It uses ADR-025's distinct four-role `RecoveryProbe*` lineage under exact
active+draining-prefix or recovering+recovery-attempt/source binding, with finite
attempt/count/byte/rate/age/concurrency, an unextended deadline, no widening, and exactly one
terminal disposition. Zero-attempt terminalization is valid; the originating fence is provenance,
so current same-source successor authority may terminalize without resending the old intent.
Terminal `unknown` evidence never resolves the separately bound source ambiguity, proves absence,
or authorizes replay. Every recovery-attempt-bound probe write invalidates the activation
candidate.

## Enforcement

- Import-linter, dependency-cruiser, Python AST, and TypeScript compiler-AST checks restrict
  LLM/TTS SDK imports and provider-specific types to reviewed adapter modules.
- Dependency manifests and CI policy tests maintain an explicit SDK-to-adapter allowlist;
  transitive convenience imports do not create an exception.
- Gateway conformance suites run the same timeout, cancellation, error-normalization,
  telemetry, and redaction cases against mocks and every live adapter.
- Configuration validation rejects generator/classifier vendor correlation and invalid fallback
  graphs, partial activation sets, stale activation/eligibility epochs, and ambiguous scopes
  before activation.
- Static and runtime contract tests prove generation gateways cannot return
  `ApprovedResponse` and public TTS/media interfaces cannot accept raw text.
- Attempt-lineage tests prove every retry, fallback, and rewrite has a distinct identity and
  that every complete generated candidate enters safety exactly once.
- Provider gateways, secrets/configuration, and production profile activation require human
  review.
- Snapshot-pinning tests prove health changes, definition/set withdrawal, cache refresh, retry,
  fallback, replica lag, rollback, and restore cannot select an unreviewed definition or make
  stale activation/eligibility current.

## Failure Behavior

- Timeout, cancellation, malformed output, SDK exception, transport failure, or provider
  failure yields a normalized terminal attempt outcome; incomplete content creates no
  candidate.
- A late result after cancellation, expiry, composite-fence change, or takeover is recorded
  without content in ordinary logs and cannot re-enter active processing.
- A generation fallback is never dispatched directly. If it succeeds, it starts at the
  candidate safety boundary.
- Safety-classifier timeout, unavailability, correlation violation, or indeterminate result
  yields no approval and no autonomous speech.
- Input/surface moderation timeout, indeterminate or malformed result, context/digest mismatch, or
  fallback exhaustion yields no authorized `SurfaceDecision` and no presentation.
- TTS timeout or failure yields no playable artifact and no `SpeechTask`. Fallback scenes,
  silence, or canned material require their separately approved paths.
- Retry or fallback exhaustion does not widen time, cost, or safety limits.
- Provider diagnostic payloads are redacted before logging; a redaction failure drops the
  diagnostic content rather than leaking it.
- Circuit-breaker and quota failures emit provider-neutral health evidence and invoke only
  the degradation path accepted in ADR-020.

## Consequences

- Adding a provider requires a small adapter, conformance evidence, profile review, and
  operational runbook rather than domain changes.
- Vendor-specific features are unavailable until represented safely in a provider-neutral
  contract.
- Independent generation and safety vendors increase integration and operational cost but
  reduce correlated failure.
- Hidden SDK retries and unbounded provider latency are not permitted.
- Full-response evaluation under proposed ADR-018 can still use internal generation
  streaming for collection, but no partial fragment becomes a candidate or reaches TTS.
- Live provider work remains blocked until this ADR and the applicable safety, privacy,
  latency, and protected-path reviews are accepted.

## OPEN Decisions

- OD-002: generator and safety-judge vendor pairing, including what constitutes an
  independent vendor/failure domain.
- OD-034 and ADR-024: provider/model definition identity, activation-set granularity, typed
  scopes, fallback compatibility, in-flight disposition, epoch, snapshot, rollback, and
  emergency restriction behavior.
- Provider, model, region, residency, privacy, and contractual selections for each
  capability.
- OD-014: retry/fallback eligibility, attempt caps, backoff, cancellation, and rewrite
  policy.
- OD-001: observed provider-stage and end-to-end service-latency SLOs only.
- OD-035 and ADR-018: per-capability timeout, outer deadline, scheduler-budget, and clock values.
- OD-037: provider concurrency/resource reserves, circuit thresholds, recovery probes,
  retry-amplification bounds, admission, and exact ADR-020 saturation/degradation targets.
- OD-038: quota reservation/uncertainty, cost accounting units, billing reconciliation,
  warning/hard-limit/override policy, and per-session/provider budgets.
- OD-036/039: provider telemetry/alert evidence and representative
  load/stress/spike/soak/chaos/recovery acceptance.
- Whether generation-provider streaming is enabled internally; sentence-chunked TTS remains
  governed separately by OD-007 and ADR-018.
- Production SDK versions, upgrade/canary policy, and the managed secret/custody
  implementation.

## Acceptance Evidence

Human acceptance requires a provider-neutral test kit and review evidence covering:

- import-boundary mutation tests for direct, re-exported, dynamic, and transitive SDK access;
- timeout, cancellation, late-result, partial-stream, malformed-output, quota, and provider
  error fault injection;
- actor pause/revoke/takeover tests at intent, send-authorization, first-byte, response,
  response-observation, and application-commit boundaries, including insufficient remaining
  lease horizon, exact-open admission/source rejection for ordinary intent/send/application,
  possibly-sent non-idempotent work, ownership-row race, and stale-composite-fence rejection;
- distinct recovery-probe intent/attempt/first-byte/response/disposition tests under both exact
  bindings, covering zero-attempt and current-successor terminalization without resend, wrong
  binding/ordinary relabeling, finite bounds, terminal-unknown versus separately resolved/
  permanently safe-quarantined/accountably disposed source ambiguity, activation invalidation,
  and no widening/absence/replay authority;
- primary failure followed by fallback, with a new attempt/candidate and the same complete
  safety gate;
- input/surface moderation primary/fallback tests binding the exact final context and digest, with
  timeout, indeterminate, disagreement, malformed output, and any rendering change producing no
  authorized surface decision;
- rejection proving that safety-provider failure or generator/classifier correlation
  produces zero autonomous speech;
- TTS fallback tests proving identifier-only invocation, approval revalidation, unchanged
  linguistic content, and no task on failure;
- lineage, idempotency, redaction, usage/cost, and deadline-non-extension assertions;
- draft/published-version and immutable definition/digest, atomic activation bundle, scope
  conflict, stale activation/eligibility epoch/cache, resolved-snapshot pinning, restrictive
  health, forward rollback, and reconstruction assertions;
- a vendor/profile decision record, privacy review, runbook, rollback/disable plan, and
  protected human approval for each production adapter;
- passing type, import-boundary, contract, affected integration, and red-team gates.
