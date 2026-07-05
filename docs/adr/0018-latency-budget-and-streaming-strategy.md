# ADR-018: Latency Budget And Streaming Strategy

Status: Draft, with OPEN numeric decisions

Priority: P0

Date: 2026-07-05

Source: `vnova-review-handoff.md`

## Context

VNova needs a live-broadcast latency target so the runtime can make correct tradeoffs among generation, safety, TTS, delivery, playout, manual review, and candidate expiration.

The external review proposes starting numbers, but the numbers themselves remain OPEN pending human confirmation.

## Decision

VNova v1 evaluates the full generated response before TTS.

VNova v1 does not stream sentence chunks to TTS before full-response safety evaluation.

Sentence-chunked streaming TTS remains a deferred future ADR unless a human explicitly chooses to spec it now.

## OPEN Decision: Latency Budget Numbers

The latency budget numbers are OPEN.

Review recommendation:

- Proposed starting target: p50 message-to-first-audio <= 5-7s.
- Proposed p95 target: <= 10-12s.

These values are recommendations, not final architecture, until confirmed by a human.

## Proposed Per-Stage Timing Requirements

These are proposed starting targets and remain OPEN until confirmed:

| Stage | Proposed p50 Target |
|---|---:|
| Chat ingest and input moderation | <= 1.0s |
| Director, prompt assembly, generation | <= 2.5s |
| Safety evaluation | <= 0.8s |
| TTS synthesis | <= 1.5s |
| Delivery to stage-host and local playout start | <= 0.5s |

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

OPEN: exact TTL duration per trigger type.

Recommendation:

- Viewer-message candidates should use a short TTL.
- Scheduled-segment candidates may use a longer TTL if bound to a segment window.
- Manual speech submissions should have an explicit operator-visible expiry.

## Safety And TTS Ordering

Binding v1 behavior:

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
- Do not implement chunked streaming in v1.

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
- Operator command timeout: commands use REST POST with idempotency keys; e-stop must not depend on a healthy console WebSocket.

## Observability Requirements

Track per-turn timings from ingest to playback:

- `approval_queue_wait_ms`
- `safety_eval_latency_ms`
- `candidate_expired_count`
- `rig_ws_rtt_ms`
- `clock_skew_ms`
- `audio_buffer_underrun_count`
- Per-stage OpenTelemetry spans corrected using stage-host clock-offset reporting

## Consequences

- Latency-sensitive implementation is blocked on human confirmation of numeric targets where product behavior depends on those targets.
- Safety is prioritized over low latency in v1.
- Candidate expiration is a first-class safety and product behavior.
