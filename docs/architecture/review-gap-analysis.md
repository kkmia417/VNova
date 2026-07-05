# VNova Review Gap Analysis

Status: Draft for architecture-governed implementation

Source: `vnova-review-handoff.md`

Note: the original VNova architecture design document referenced by the external review is not present in this repository. This gap analysis compares the handoff's description of the original direction against the accepted review decisions. Items marked OPEN remain pending human decision.

## Baseline Inferred From The Review

The original direction had the correct core safety model: `CandidateResponse` and `ApprovedResponse` are separate, and unsafe candidate text must pass a mandatory safety gate before speech.

The review identifies these original-design gaps:

- Local broadcast hardware topology was not modeled explicitly.
- The turn model was too chatbot-shaped for a continuous broadcast product.
- The safety gate lacked concrete enforcement mechanics.
- Latency budgets were not defined.
- Privacy, APPI posture, deletion, and retention were not defined.
- The five planes could be misread as five deployed services.
- Broadcast surfaces beyond voice were not fully inventoried.

## Acknowledged Binding Changes

1. Add required `stage-host` local agent.
2. Treat VNova as a broadcast runtime, not a chatbot.
3. Preserve `CandidateResponse` and `ApprovedResponse` as separate types.
4. Treat `CandidateResponse` as unsafe by default.
5. Make `packages/safety` the only package allowed to construct `ApprovedResponse`.
6. Require TTS and media boundaries to accept `approved_response_id`, never raw text.
7. Make `stage-host` the sole consumer of `SpeechTask`.
8. Require local hard e-stop to work when cloud is unreachable.
9. Fail closed when safety is unavailable.
10. Use Redis Streams as transport only.
11. Use PostgreSQL as the system of record.
12. Separate viewer memory and audit logs.
13. Treat the five planes as package/module boundaries, not five deployed services.
14. Define initial deployed surfaces as `control-api`, `session-runtime`, `stage-host`, and `operator console`.
15. Add rehearsal mode with fake OBS, fake VTube Studio, and virtual audio sink early enough to support CI and non-live testing.

## Concrete Changes By Area

### `docs/`

Required now:

- Add `docs/architecture/system-overview.md` with revised topology.
- Add `docs/architecture/review-gap-analysis.md`.
- Add short architecture stubs for stage-host, privacy retention, latency, broadcast surfaces, mode transitions, and rehearsal mode.

Required before runtime implementation:

- Add a broadcast surface model covering voice, captions, chat overlay, alerts, scene text, and spoken usernames.
- Add a mode transition and degradation model.
- Add a rehearsal mode test strategy.
- Add a runbook for live rig disconnect, silence, fail-closed activation, and e-stop.

### `docs/adr/`

Required P0 now:

- Add ADR-016: Stage host and cloud/local topology.
- Add ADR-017: Data retention, privacy, and PII.
- Add ADR-018: Latency budget and streaming strategy.

Required before affected feature work:

- ADR-019: AuthN/AuthZ and operator roles.
- ADR-020: Mode transition and degradation matrix.
- ADR-021: Broadcast surface inventory and chat overlay policy.
- ADR-022: Voice rights and talent licensing metadata.

Existing ADR references in the handoff, such as ADR-003, ADR-004, ADR-008, ADR-010, ADR-011, and ADR-015, are not present in this repository. They must be created or imported before they can govern implementation.

### `packages/`

No package code is created by this preparation step.

Required skeletons before runtime implementation starts:

- `packages/safety`: exclusive owner of `ApprovedResponse` construction.
- `packages/contracts`: JSON Schema source for event envelopes and event payloads.
- Provider gateway package/module boundaries for LLM and TTS SDK imports.
- Import-linter and dependency-cruiser rules enforcing the safety and provider boundaries.

### Domain Specs

Required changes:

- Model `Turn` to `CandidateResponse` as 1:N with a selected pointer.
- Add one `SafetyDecision` per candidate.
- Remove `EmergencyStop` from the `SafetyDecision` enum.
- Model e-stop as session-level operator/system state and audited event.
- Model manual approval as `SafetyDecision(decided_by: operator_id)`.
- Add `StreamPlan` and `Segment`.
- Make turn triggers polymorphic: `viewer_message`, `operator`, `scheduled_segment`, `idle_filler`, and `system`.
- Add typed `MemoryRecord` slots.
- Add `Operator`, `PromptVersion`, `PolicyVersion`, `ProviderProfile`, `ModelConfig`, `VoiceProfile`, `Recording`, and `SessionArchive`.
- Classify `CandidateResponse.raw_output` as restricted.
- Store full prompts only in a restricted table; ordinary events store prompt manifests.

### Event Specs

Required changes:

- Define a versioned envelope with `event_id`, `type`, `schema_version`, `stream_session_id`, optional `turn_id`, `occurred_at`, and `payload`.
- Keep Redis Streams as transport only.
- Reconstruct state from PostgreSQL, not Redis retention.
- Partition strict FIFO speech/avatar path by `stream_session_id`.
- Add events: `ModeChanged`, `OperatorPresenceChanged`, `PolicyVersionActivated`, `PromptVersionActivated`, `MemoryWritten`, `MemoryDeleted`, `RigConnected`, `RigDisconnected`, `CandidateExpired`, `SafetyLayerUnavailable`, `FailClosedActivated`, `SilenceThresholdExceeded`, `CostBudgetWarning`, and `ManualSpeechSubmitted`.
- Add stage-host playback, heartbeat, clock-offset, watchdog, and offline-buffer replay events.

### Tests

Required tests before runtime implementation proceeds past skeletons:

- Codegen round-trip tests for contracts.
- Contract test proving no TTS/media path accepts raw text.
- Contract test proving construction of `ApprovedResponse` outside `packages/safety` fails boundary checks.
- Database constraint test proving `approved_response` requires an approved `safety_decision`.
- Fault injection test for safety timeout causing zero speech and mode degradation.
- Local e-stop test with cloud link severed.
- Red-team fixture corpus for prompt injection, username attacks, and SSML injection.
- Rewrite-loop cap test.
- Synthetic full incident timeline reconstruction.
- Rehearsal-mode e2e test using fake OBS, fake VTS, and virtual audio sink.

### Runbooks

Required runbooks before supervised live operation:

- Local hard e-stop and cloud freeze.
- Rig disconnected during live broadcast.
- Silence threshold exceeded during live broadcast.
- Safety layer unavailable and fail-closed activation.
- Provider outage and fallback-through-gate verification.
- Candidate expiration and approval queue age.
- Offline stage-host log replay after reconnect.
- Privacy deletion request and embedding cascade verification.

## Disagreements

None.

## Unresolved OPEN Decisions

1. Latency budget numbers.
2. Generator vs safety-judge vendor pairing.
3. Twitch-first vs YouTube-first ingestion.
4. Deployment target: ECS Fargate vs Fly.io vs other.
5. Stage-host implementation language: Python vs Node vs Go.
6. Chat overlay: build moderated overlay now or omit at launch.
7. Sentence-chunked streaming TTS: defer or spec now as ADR.

## Implementation Blockers

Runtime implementation must not start until these blockers are resolved or explicitly waived by a human:

- P0 ADRs 016, 017, and 018 exist and are reviewed.
- AGENTS.md governance exists.
- System overview reflects the accepted topology.
- Safety construction boundary is designed.
- Contract schema source location is defined.
- CODEOWNERS and CI enforcement strategy are created before code affecting protected areas is added.
- OPEN decisions that affect the next implementation step are resolved or explicitly marked as pending with a safe default that does not ship runtime behavior.

## Files That Must Be Created Before Runtime Implementation Starts

- `AGENTS.md`
- `docs/architecture/system-overview.md`
- `docs/architecture/review-gap-analysis.md`
- `docs/adr/0016-stage-host-and-cloud-local-topology.md`
- `docs/adr/0017-data-retention-privacy-and-pii.md`
- `docs/adr/0018-latency-budget-and-streaming-strategy.md`
- `docs/adr/0019-authn-authz-and-operator-roles.md`
- `docs/adr/0020-mode-transition-and-degradation-matrix.md`
- `docs/adr/0021-broadcast-surface-inventory-and-chat-overlay-policy.md`
- `docs/adr/0022-voice-rights-and-talent-licensing-metadata.md`
- `packages/contracts/` skeleton
- `packages/safety/` skeleton
- `specs/events/` JSON Schema skeleton
- `tests/red-team/` fixture skeleton
- `.github/CODEOWNERS` or repository-equivalent CODEOWNERS file
- CI configuration for import boundaries, contract tests, and schema-diff gates
