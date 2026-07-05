# AGENTS.md

This repository is the VNova production-grade LLM VTuber / AI talent broadcast runtime.

Treat VNova as a real-time broadcast control system with AI components, not as a chatbot connected to an avatar.

Codex must not implement feature code before architecture skeleton and governance are in place.

When a requested change conflicts with an ADR or this document: open an ADR proposal — do not improvise.

## Invariant Laws

1. Only `packages/safety` may construct `ApprovedResponse`.
2. TTS/media interfaces accept `approved_response_id` only — never raw text.
3. No LLM/TTS provider SDK import outside the provider gateways.
4. Every external call has an explicit timeout.
5. Provider fallback paths pass through the same safety gate as primary paths.
6. Fail closed: no safety verdict ⇒ no autonomous speech.
7. Schema migrations require a linked ADR reference.
8. Viewer memory and audit logs never share tables, content, or access roles.

## Repository Responsibility Boundaries

- `control-api`: stateless admin, config, policy, and auth API.
- `session-runtime`: one logical actor per `StreamSession`; owns chat collection, input moderation, director, content scheduler, persona/prompt/memory orchestration, provider gateway calls, safety gate invocation, and approved dispatch.
- `stage-host`: required local streaming PC agent; sole consumer of `SpeechTask`; owns playback queue, OBS adapter, VTube Studio adapter, local e-stop, watchdog, offline buffering, heartbeat, and clock-offset reporting.
- `operator console`: internal-only operator UI behind SSO/VPN.
- `packages/safety`: sole package allowed to mint `ApprovedResponse`.
- `packages/contracts`: source of shared event and API contracts.
- `specs/events`: JSON Schema source for versioned event envelopes and payloads.
- `tests/red-team`: regression fixtures for safety, prompt injection, username attacks, and SSML injection.

The five planes are package/module boundaries, not five deployed services.

The initial deployed surfaces are `control-api`, `session-runtime`, `stage-host`, and `operator console`.

## Forbidden Changes Without Prior ADR Or Human Approval

- Collapsing `CandidateResponse` and `ApprovedResponse`.
- Allowing TTS or media code to accept raw generated text.
- Constructing `ApprovedResponse` outside `packages/safety`.
- Importing LLM or TTS provider SDKs outside provider gateways.
- Exposing Redis directly to the rig.
- Treating Redis Streams as the system of record.
- Treating `stage-host` as optional.
- Letting any component other than `stage-host` consume `SpeechTask`.
- Weakening fail-closed behavior.
- Storing viewer memory content in audit logs.
- Adding database migrations without a linked ADR.
- Adding prompt templates, policy defaults, secrets, environment values, provider code, OBS adapter code, VTube Studio adapter code, runtime workers, or frontend implementation before architecture governance is complete.

## Required Pre-Commit Commands

For documentation-only governance changes before the toolchain exists:

- `git status --short`

Once the scaffold exists, agent-generated changes must run the applicable commands before reporting completion:

- Python type checks.
- TypeScript type checks.
- Import-linter contracts.
- Dependency-cruiser contracts.
- Contract schema validation and codegen round-trip tests.
- Affected unit and integration tests.
- Red-team regression subset for safety-relevant changes.
- Schema-diff gate for migrations, with linked ADR reference.

Do not claim a gate passed unless the command was actually run.

## Required Report Format For Agent Changes

Every agent completion report must include:

1. Files created.
2. Files updated.
3. ADRs added or changed.
4. Assumptions made.
5. OPEN decisions still requiring human decision.
6. Commands run.
7. Test, lint, and typecheck result, if applicable.
8. Deviations from the active ADRs, AGENTS.md, or `vnova-review-handoff.md`.
9. Repository-structure mismatches discovered during the work.

## Files Requiring Human Review

Human review is required for changes to:

- `AGENTS.md`
- ADRs
- `packages/safety`
- E-stop paths
- `packages/contracts`
- `specs/events`
- Database migrations
- Prompt and persona templates
- Policy defaults
- CI configuration
- Secrets and infrastructure configuration
- Provider gateway implementations
- OBS and VTube Studio adapters
- Stage-host command and watchdog behavior

## Runtime Implementation Gate

Before feature code starts, the repository must have:

- P0 ADR-016, ADR-017, and ADR-018.
- Updated system overview.
- Gap analysis.
- Safety and contract package skeletons.
- Event schema skeleton.
- CODEOWNERS or repository-equivalent review ownership.
- CI plan or configuration for import boundaries, contract tests, and protected-file review.

Until that gate is satisfied, Codex may only edit docs, ADRs, governance files, repository governance stubs, CODEOWNERS stubs, and CI TODO notes.
