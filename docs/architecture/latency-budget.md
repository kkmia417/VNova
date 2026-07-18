# Latency Budget

Status: Proposed structural model; all production numbers remain OPEN

Governing proposal:
[ADR-018](../adr/0018-latency-budget-and-streaming-strategy.md)

Related execution proposal:
[ADR-025](../adr/0025-session-actor-ownership-command-ingress-and-fencing.md)

VNova measures latency as a safety and freshness budget, not merely a performance metric. The
initial-production proposal evaluates a complete response before TTS. Sentence-chunked TTS is
disabled unless a later accepted ADR defines its separate safety model.

## End-To-End Clock

The viewer-trigger path begins when VNova's ingestion boundary first receives a platform item and
ends when `stage-host` observes the first valid audio output. Scheduled and operator-triggered work
use their own named start events but the same downstream stage boundaries.

```text
ingest
  -> input moderation
  -> scheduling / prompt assembly
  -> generation
  -> full-response safety
  -> optional operator queue
  -> TTS and artifact commit
  -> signed dispatch
  -> stage-host admission
  -> first audio observed
```

The runtime records both wall-clock timestamps and monotonic durations. Cross-host spans retain the
raw local observations and an explicit clock-offset/uncertainty estimate; corrected time never
overwrites the source evidence.

## One Authoritative Freshness Deadline

Every turn carries an outer deadline derived from its trigger class and accepted policy. Each
external attempt has an explicit timeout no greater than its allocated stage budget or remaining
outer deadline, whichever is shorter.

For session-owned work, ADR-025 adds a third independent ceiling under the exact phase-appropriate
composite actor fence: conservative remaining lease horizon minus accepted uncertainty,
response-observation, and application-recording margins. If it cannot cover the complete attempt,
the actor renews first or does not start. Recovery probes use their own non-widening budget. Lease
renewal never extends the turn, candidate, approval, command, or trigger deadline.

Retries, provider fallback, rewrite, operator queueing, synthesis, media transfer, reconnect, and
local queueing consume the same remaining budget. They never reset or extend it. A late completion
is recorded as a terminal attempt result and cannot re-enter the active path.

## Freshness Chain

`CandidateResponse` has an authoritative `not_after`. The approval, media authorization, immutable
artifact, signed `SpeechTask`, stage-host queue entry, and immediate pre-playback check propagate a
deadline no later than that source value. A downstream component may shorten but never lengthen
the chain.

Expired work:

- cannot be approved, synthesized, dispatched, accepted, restarted, or replayed;
- emits a classified expiry outcome;
- is removed from manual-review and local playback queues;
- cannot become eligible after reconnect or clock recovery;
- may leave only the minimized audit evidence allowed by retention policy.

An uncertain clock is restrictive. If the stage host cannot prove validity within the measured
uncertainty bound, playback does not start.

## Independent Control Planes

The following values are recorded and governed independently:

| Control                                     | Purpose                                                                     | Decision owner |
| ------------------------------------------- | --------------------------------------------------------------------------- | -------------- |
| Safety/freshness deadline and candidate TTL | Maximum authorization horizon for this content                              | OD-035         |
| External-attempt timeout                    | Bound one dependency call                                                   | OD-035         |
| Composite actor lease/effect horizon        | Fence send authorization, observation, and application within current proof | OD-035         |
| Scheduler stage budget                      | Admission and remaining-time planning                                       | OD-035         |
| Observed latency SLI/SLO                    | Measure service behavior against a product reliability objective            | OD-001         |
| Alert and error-budget thresholds           | Detect and escalate sustained service degradation                           | OD-036         |

An SLO miss can consume an error budget; it cannot consume a safety invariant. Error-budget policy
never allows late approval or playback, incomplete safety evaluation, raw-text dispatch, or
deadline extension. Changing an SLO, alert threshold, timeout, or scheduling estimate cannot
change the authoritative deadline already attached to work.

## Budget Ledger

Exact p50, p95, and p99 service objectives are OPEN under OD-001. Timeout, scheduler-budget,
freshness, trigger-specific TTL, and clock-profile values are independently OPEN under OD-035.
The accepted policies must allocate and measure at least:

| Stage                          | Required measurement                                                        |
| ------------------------------ | --------------------------------------------------------------------------- |
| Ingest and input moderation    | platform receipt to normalized accepted/rejected input                      |
| Scheduling and prompt assembly | accepted trigger to immutable provider request                              |
| Generation                     | provider attempt start to complete schema-valid outcome                     |
| Safety                         | candidate creation through deterministic, model, and policy verdict         |
| Operator review                | queue entry to decision or expiry; reported separately from autonomous path |
| TTS and artifact commit        | approved resolution through immutable ready artifact                        |
| Dispatch and transfer          | signed task creation through stage-host artifact verification               |
| Local queue and playout        | task acceptance through observed first audio and completion                 |
| End to end                     | named trigger start through observed first audio                            |

Queue wait, retry/fallback time, cancellation cleanup, and clock uncertainty are visible rather
than hidden inside provider or network spans.

## Admission And Load Shedding

The scheduler estimates whether enough deadline remains before starting another expensive stage.
Work that cannot plausibly finish within the accepted budget is expired or rejected according to
policy; it is not allowed to consume safety or rig capacity indefinitely. Load shedding protects
e-stop, operator commands, safety evaluation, heartbeat, and current playout ahead of speculative
generation.

Backpressure, provider degradation, and budget exhaustion may lower effective autonomy under
ADR-020. They never permit partial safety, raw-text TTS, stale output, or a longer approval
deadline.

## Measurement Rules

- Percentiles are reported by trigger class, effective mode, provider profile, surface, and
  completion outcome; a combined average is not sufficient.
- Timeouts, blocks, expiries, cancellations, and fail-closed outcomes remain in reliability
  reporting rather than disappearing from successful-latency charts.
- Traces, restricted logs, and authoritative evidence may use approved stable attempt, turn,
  approval, artifact, task, and session references for correlation. Metric labels use only the
  versioned bounded dimensions in the observability data contract; per-record IDs are forbidden.
- Restricted prompt, candidate, viewer-memory, or rights evidence content is absent from ordinary
  telemetry.
- Platform video delay is not subtracted from VNova latency or used as a safety margin.
- SLO windows, low-traffic treatment, burn-rate alerts, and rehearsal/live separation require
  human SRE approval.

## Acceptance Evidence

Before numeric targets become production gates:

- the accountable product, safety, architecture, and SRE owners close OD-001;
- deterministic virtual-clock tests prove deadline non-extension across every retry and handoff;
- fault injection covers provider timeout, operator expiry, object-store delay, WebSocket
  reconnect, queue backlog, offset uncertainty/sample staleness, and late completion;
- actor lease-renewal timeout, insufficient attempt horizon, process pause, takeover, lost command
  response, and stale/late-result rejection are exercised independently from service SLOs;
- rehearsal and target-rig measurements use the same span definitions;
- dashboards show stage percentiles, queue wait, expiry rate, fail-closed rate, first-audio
  latency, and audio underruns;
- alerts and runbooks distinguish slow-but-valid work from unsafe or expired work;
- the approved values live in versioned policy/configuration, not embedded constants.

The handoff and ADR-018 contain starting recommendations for human review. They are not accepted
SLOs, TTLs, timeout defaults, scheduler budgets, alert thresholds, or clock-policy values.
