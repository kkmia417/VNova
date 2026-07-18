# Security Document Index

Status: Proposed security review map; no production authorization

VNova security is a system property spanning model input, approval, persistence, operator
authority, provider gateways, media artifacts, rights, transport, and the local broadcast rig.
Security review must preserve the safety, privacy, and responsibility boundaries in `AGENTS.md`
and Accepted ADRs.

## Document Map

| Document                                                                                                    | Status                        | Purpose                                                                                                        |
| ----------------------------------------------------------------------------------------------------------- | ----------------------------- | -------------------------------------------------------------------------------------------------------------- |
| [VNova threat model](threat-model.md)                                                                       | Proposed                      | Assets, trust boundaries, adversaries, abuse paths, required controls, residual risks, and validation evidence |
| [Operational runbooks](../runbooks/README.md)                                                               | Drafted only                  | Fail-closed containment and deliberate recovery procedures                                                     |
| [Production quality attributes](../architecture/production-quality-attributes.md)                           | Normative architecture target | Security, safety, privacy, resilience, and release-quality obligations                                         |
| [Observability, SLI/SLO, and alerting](../architecture/observability-sli-slo-and-alerting.md)               | Proposed                      | Signal authority, telemetry privacy, clock evidence, monitoring-loss posture, and alert ownership              |
| [Capacity, backpressure, and cost governance](../architecture/capacity-backpressure-and-cost-governance.md) | Proposed                      | Bounded resources, protected reserves, admission/shedding, provider quota, cost, and recovery                  |
| [Load, soak, and chaos acceptance](../governance/load-soak-chaos-acceptance.md)                             | Proposed                      | Immutable workload/fault subject, blast radius, abort, zero-tolerance invariants, recovery, and evidence       |
| [Feature architecture review](../governance/feature-architecture-review.md)                                 | Proposed review packet        | Protected decisions for identity, providers, rights, media, surfaces, stage-host, and e-stop                   |

Red-team fixtures under `tests/red-team` are regression evidence for known classes; they are not a
complete threat model, penetration test, or production risk acceptance.

## Review Contract

Security review must:

- assess complete paths and composed authorizations, not isolated components;
- model malicious input, compromised identities, forged/replayed identifiers, stale state,
  provider correlation, control-plane loss, local compromise, and recovery abuse;
- keep primary and fallback routes under the same safety and authorization gates;
- validate negative and failure cases on the intended target;
- assign a named human owner to every accepted residual risk;
- treat unavailable, unverifiable, expired, or conflicting security state as restrictive;
- route any change to a binding invariant through a superseding ADR.

OD-028 must approve the adversary assumptions, residual-risk authority, independent validation
scope, and review triggers before production security acceptance.
Applicable production paths also require OD-029 through OD-032 for disaster recovery,
personal-data breach response, release integrity, and deletion/restore assurance. None of those
operational decisions can accept a violation of an `AGENTS.md` invariant or Accepted ADR.
Time/freshness, observability, capacity/backpressure, cost/quota, and load/soak/chaos validation
require OD-035 through OD-039 as applicable. OD-039 may classify test findings but only OD-028's
approved taxonomy and role may accept residual risk.

## Review Triggers

At minimum, reassess the threat model when a reviewer proposes or enables:

- a new provider, model, tool, input source, renderer, broadcast surface, or live adapter;
- a new operator capability, identity provider, trust relationship, or break-glass path;
- a contract, signature, key-custody, epoch, replay, or clock policy change;
- a new voice, rights grant type, media format, cache, archive, or distribution path;
- a data class, retention, deletion, backup, analytics, or cross-region change;
- higher autonomy, streaming synthesis, tool use, or offline operation;
- an incident, red-team finding, penetration-test result, or material dependency advisory.

Calendar cadence and evidence freshness remain OPEN under OD-028; they are not silently fixed by
this index.

## Informative Frameworks

The [threat model](threat-model.md) uses VNova-native assets and invariants. NIST AI 600-1 and
MITRE ATLAS provide external taxonomies for completeness checks, while NIST SP 800-61 Rev. 3
informs incident-response integration. These frameworks are informative and do not replace
deployment-specific security engineering or accountable risk acceptance.
