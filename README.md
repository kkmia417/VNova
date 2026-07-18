# VNova

VNova is a production-grade runtime for LLM-driven VTubers and AI talent. It is a real-time broadcast control system with AI components, not a chatbot attached to an avatar.

The initial production release is not a throwaway MVP. Capabilities may be deliberately deferred to keep the safety boundary auditable, but every capability that is enabled must meet the production bar for safety, operability, privacy, testing, and recovery.

## Safety In One Sentence

Generated text is unsafe by default. Only `packages/safety` may mint an `ApprovedResponse`, and TTS or media code receives an `approved_response_id`, never raw generated text.

## Deployed Surfaces

- `control-api`: stateless administration, configuration, policy, authentication, and authorization API.
- `session-runtime`: one logical actor per `StreamSession`; owns broadcast orchestration and the approved dispatch path.
- `stage-host`: required local agent and sole `SpeechTask` consumer; owns OBS, VTube Studio, playout, watchdog, and local hard e-stop behavior.
- `operator console`: internal operator surface behind SSO and VPN controls.

## Current State

The repository is in its architecture-foundation phase. Feature implementation is intentionally blocked until the [Runtime Implementation Gate](AGENTS.md#runtime-implementation-gate) is satisfied and reviewed.

The immediate review sequence starts with the Retire-only
[Stage A governance bootstrap handoff](docs/governance/foundation-stage-a-review-handoff.md) and
its [authority proposal](docs/governance/foundation-authority-and-bootstrap-proposal.md). The
broader architecture foundation packet is a Stage B input and must not be copied into the Stage A
candidate.

Start with:

- [Stage A governance bootstrap handoff](docs/governance/foundation-stage-a-review-handoff.md)
- [Foundation authority and bootstrap proposal](docs/governance/foundation-authority-and-bootstrap-proposal.md)
- [Architecture document index](docs/architecture/README.md)
- [System overview](docs/architecture/system-overview.md)
- [Domain and information model](docs/architecture/domain-information-model.md)
- [Scope and subject identity model](docs/architecture/scope-and-subject-identity-model.md)
- [Domain record lifecycle catalog](docs/architecture/domain-record-lifecycle-catalog.md)
- [Session runtime execution model](docs/architecture/session-runtime-execution-model.md)
- [Architecture gap analysis](docs/architecture/review-gap-analysis.md)
- [Production quality attributes](docs/architecture/production-quality-attributes.md)
- [Observability, SLI/SLO, and alerting model](docs/architecture/observability-sli-slo-and-alerting.md)
- [Capacity, backpressure, and cost governance](docs/architecture/capacity-backpressure-and-cost-governance.md)
- [Implementation roadmap](docs/architecture/implementation-roadmap.md)
- [Open decision register](docs/architecture/open-decisions.md)
- [Open decision disposition register](docs/governance/open-decision-dispositions.md)
- [Stage B architecture foundation review packet](docs/governance/architecture-foundation-review.md)
- [Feature architecture review packet](docs/governance/feature-architecture-review.md)
- [Security threat model](docs/security/threat-model.md)
- [Operational runbook index](docs/runbooks/README.md)
- [Operational readiness review packet](docs/governance/operational-readiness-review.md)
- [Load, soak, and chaos acceptance](docs/governance/load-soak-chaos-acceptance.md)
- [Toolchain baseline](docs/architecture/toolchain.md)
- [Architecture decision records](docs/adr/README.md)
- [CI and repository rules plan](docs/governance/ci-quality-gates.md)

## Repository Shape

```text
apps/                  deployable surfaces (created after the implementation gate)
packages/contracts/    generated contract libraries and contract tooling boundary
packages/safety/       exclusive ApprovedResponse minting boundary
specs/events/          canonical, hand-authored event JSON Schemas and catalogs
tests/red-team/        safety regression corpus
docs/                  architecture, ADRs, governance, security, and runbooks
```

The architecture/contract scaffold is not a runnable broadcast product. Its supported local
verification commands are documented in the [toolchain baseline](docs/architecture/toolchain.md).
Recorded local passes are technical evidence only; the scaffold remains quarantined until the
authoritative gate amendment, immutable protected review, remote CI, Ruleset, and non-author human
approval are complete.

## Governance

Read [AGENTS.md](AGENTS.md) before changing the repository. Protected paths require human review,
and a requested change that conflicts with `AGENTS.md` or any ADR requires an ADR proposal rather
than an improvised exception.
