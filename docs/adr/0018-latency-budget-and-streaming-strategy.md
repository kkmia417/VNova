# ADR-018: Latency Budget And Streaming Strategy

Status: Proposed, with OPEN numeric decisions

Priority: P0

Date: 2026-07-05

Source: `vnova-review-handoff.md`

This ADR is non-binding while its status is `Proposed`. The behavior below becomes binding
only if a human accepts this ADR or an explicit replacement.

## Context

VNova needs a live-broadcast latency target so the runtime can make correct tradeoffs among generation, safety, TTS, delivery, playout, manual review, and candidate expiration.

The external review proposes starting numbers, but the numbers themselves remain OPEN pending human confirmation.

## Proposed Decision

If accepted, VNova's initial production release evaluates the full generated response before
TTS.

If accepted, the initial production release does not stream sentence chunks to TTS before
full-response safety evaluation.

Sentence-chunked streaming TTS remains a deferred future ADR unless a human explicitly chooses to spec it now.

## OPEN Decision: Latency Budget Numbers

The latency budget numbers are OPEN.

Review recommendation:

- Proposed starting target: p50 message-to-first-audio <= 7s.
- Proposed p95 target: <= 12s.

These values are recommendations, not final architecture, until confirmed by a human.

## Proposed Per-Stage Timing Requirements

These are proposed starting targets and remain OPEN until confirmed:

| Stage                                          | Proposed p50 Target |
| ---------------------------------------------- | ------------------: |
| Chat ingest and input moderation               |             <= 1.0s |
| Director, prompt assembly, generation          |             <= 2.5s |
| Safety evaluation                              |             <= 0.8s |
| TTS synthesis                                  |             <= 1.5s |
| Delivery to stage-host and local playout start |             <= 0.5s |

The p95 targets should be set by human decision alongside the overall p95 target.

Platform video delay gives some slack, but VNova should not rely on platform delay to mask internal instability.

## Candidate TTL

Every `CandidateResponse` must carry an expiration timestamp or equivalent TTL metadata.

Expired candidates:

- Emit `CandidateExpired`.
- Are discarded.
- Are never spoken.
- Are not eligible for manual approval after expiry.
- Must not be converted into `ApprovedResponse`.

The authoritative `not_after` must propagate without extension through `ApprovedResponse`, media authorization, `SpeechTask`, its signed token, stage-host queue acceptance, and the immediate pre-playback check. See ADR-008.

OPEN under OD-035: exact TTL duration and authorization horizon per trigger type.

Recommendation:

- Viewer-message candidates should use a short TTL.
- Scheduled-segment candidates may use a longer TTL if bound to a segment window.
- Manual speech submissions should have an explicit operator-visible expiry.

## Safety And TTS Ordering

Proposed initial-production behavior, non-binding until this ADR is accepted:

1. Generate full candidate.
2. Evaluate full candidate through deterministic rules, model-based classification, and policy engine.
3. Mint `ApprovedResponse` only inside `packages/safety`.
4. Dispatch only by `approved_response_id`.
5. Synthesize or play media only for approved work.

No raw `CandidateResponse` text may reach TTS or media interfaces.

## Sentence-Chunked Streaming TTS

OPEN: defer or spec now as ADR.

Review recommendation:

- Defer sentence-chunked streaming TTS.
- Create a future ADR before allowing per-chunk safety and partial synthesis.
- Do not implement chunked streaming in the initial production release.

If a human chooses to spec it now, the future ADR must define:

- Per-chunk safety semantics.
- Partial rollback behavior.
- SSML and markup sanitization per chunk.
- Playout cancellation behavior.
- Audit reconstruction for partial speech.

## Timeout Behavior

Every external call has an explicit timeout.

Timeout behavior:

- Input moderation timeout: fail closed for autonomous processing of that input.
- Generation timeout: produce no candidate and record provider failure.
- Safety timeout: fail closed, no autonomous speech, emit `SafetyLayerUnavailable` and `FailClosedActivated` as applicable.
- TTS timeout: do not play speech; record failure and use approved fallback behavior only if separately approved.
- Stage-host WebSocket timeout: mark rig degraded or disconnected; stage-host watchdog handles local mute and fallback scene.
- Operator command timeout: commands use REST POST with idempotency keys; under Proposed ADR-025,
  a timeout is an unknown observation resolved by durable receipt/outcome query or same-intent
  retry. E-stop must not depend on a healthy console WebSocket.

## Independent Time And Service Policies

The following controls are related but are not aliases and must be versioned, reviewed, and
observed independently:

- the safety/freshness absolute deadline, candidate TTL, and authorization horizon;
- each external-attempt timeout;
- actor lease/renew/takeover horizons, conservative uncertainty/result-recording margin, and the
  rule that a session-owned attempt cannot start unless its entire timeout fits the current lease
  proof under Proposed ADR-025;
- each scheduler stage budget and the turn's remaining-budget calculation;
- the measured service-latency SLI and its SLO;
- alert thresholds, burn-rate windows, and paging policy.

An SLO or error budget never authorizes an expired, unevaluated, partially evaluated, or otherwise
unsafe response. Changing an SLO, alert threshold, timeout, or scheduler estimate cannot lengthen
an already-issued safety deadline. A timeout must remain no later than the applicable outer
deadline even when the service SLO would permit a slower response.

OD-001 owns observed latency SLOs. OD-035 owns the freshness/deadline/clock and actor lease/effect
horizon profile. Numeric values
remain OPEN until their accountable human owners approve them; neither decision may be derived
implicitly from the other.

## Clock Evidence

Cross-host observations preserve, as separate evidence:

- the raw UTC timestamp observed by each host;
- the local monotonic timestamp or duration used for same-host ordering and elapsed time;
- the clock-offset estimate associated with a named synchronization sample;
- the offset uncertainty bound;
- the synchronization sample age;
- the measured round-trip delay; and
- an explicitly derived drift-rate estimate when one is available.

An offset estimate is not clock skew or drift. The ambiguous legacy label `clock_skew_ms` is not a
canonical deadline or ordering field; if retained temporarily for compatibility, it must be
marked legacy and mapped to a documented observation rather than guessed.

Cross-host corrected timelines are derived views only. They do not overwrite raw observations,
change durable event ordering, or decide whether speech is still authorized. Deadline enforcement
uses the conservative local-monotonic mapping and uncertainty rules in ADR-011. If the receiver
cannot prove that work remains valid within the uncertainty bound, it fails closed.

## Observability Requirements

Track per-turn timings from ingest to playback:

- `approval_queue_wait_ms`
- `safety_eval_latency_ms`
- `candidate_expired_count`
- `rig_ws_rtt_ms`
- clock-offset estimate, offset uncertainty, synchronization sample age, and round-trip delay
- `audio_buffer_underrun_count`
- raw per-host OpenTelemetry span observations plus a separately derived cross-host timeline

## Consequences

- Latency-sensitive implementation is blocked on human confirmation of numeric targets where product behavior depends on those targets.
- Safety is prioritized over low latency in the initial production release.
- Candidate expiration is a first-class safety and product behavior.
