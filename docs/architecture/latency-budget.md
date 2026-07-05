# Latency Budget

Status: Stub

See ADR-018: `docs/adr/0018-latency-budget-and-streaming-strategy.md`.

Latency numbers remain OPEN. The review recommendation is p50 message-to-first-audio <= 5-7s and p95 <= 10-12s.

VNova v1 evaluates the full response before TTS. Candidate expiration is required.
