# Provider Degradation And Outage Response

Status: Proposed operational runbook; implementation and production use pending

Readiness state: `Drafted` only; no rehearsal, target validation, or production authorization

Date: 2026-07-17

Sources: `AGENTS.md`, `vnova-review-handoff.md`, ADR-003, ADR-004, ADR-007, ADR-008,
ADR-010, ADR-011, ADR-017, ADR-018, ADR-019, ADR-020, ADR-025,
`docs/architecture/rehearsal-mode.md`, `docs/architecture/privacy-retention-model.md`

This document describes an intended provider-incident workflow. It does not select or authorize a
vendor, model, endpoint, SDK, region, credential, timeout, retry, circuit-breaker, fallback, cost,
or mode policy while the governing ADRs and OD-027 remain unresolved.

## Purpose And Scope

Use this runbook when an external generation, model-based safety, input/broadcast-surface
moderation, TTS, or approved-media storage/transfer capability is degraded, unavailable, over
quota, slow, returning invalid results, or suspected of sharing a failure domain that policy
requires to be independent.

The runbook separates capability health from safety authority:

- a provider response is evidence from an attempt, never an approval;
- a generation provider can produce a candidate but cannot approve or dispatch it;
- a moderation or classifier provider can return a normalized classification but cannot mint a
  terminal authorization;
- a TTS provider can synthesize only through the identifier-only approved-media path;
- a provider recovery never raises mode or revives old work automatically.

If the incident includes unverifiable output already reaching broadcast, follow
`safety-fail-closed.md` and use the appropriate local stop path immediately.

## Non-Negotiable Invariants

- Provider SDK imports and provider-specific response types stay inside reviewed gateway adapters.
- Every external call has an explicit per-attempt timeout and an enclosing operation deadline; the
  shorter remaining bound wins.
- Automatic retries are disabled where possible or are bounded, observable, and represented in
  attempt evidence.
- A timeout, cancellation, transport error, provider rejection, incomplete stream, malformed
  response, or late result creates no usable content authority.
- Every primary call, retry, rewrite, fallback, moderation call, and synthesis call has a distinct
  immutable attempt identity.
- Every complete fallback-generated output becomes a new candidate and crosses the same full safety
  gate as a primary candidate.
- The active model-based safety judge is independent from the generator being judged under the
  accepted provider-profile policy.
- Safety and moderation unavailability is indeterminate and fails closed.
- TTS fallback accepts `approved_response_id` only, cannot change linguistic content, and
  revalidates approval, rights, surface, session, and expiry before the private provider call.
- Object storage is not approval or queue authority. A partial, mutable, unverified, corrupt, or
  uncommitted artifact is never dispatchable.
- PostgreSQL contains authoritative attempt, turn, decision, approval, mode, audit, and outbox
  evidence. Redis is transport only.
- Ordinary provider telemetry and incident evidence contain no full prompt, raw candidate,
  provider request/response body, viewer-memory content, secret, credential, bearer token, or
  synthesized media.

## Trigger Conditions

Begin the runbook for a single hard integrity/authorization failure or when the human-approved
health policy classifies observed provider evidence as degraded or down.

| Trigger class             | Examples                                                                                                   | Required interpretation                                                              |
| ------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Timeout or deadline       | Explicit attempt timeout, exhausted outer deadline, queueing that leaves no safe processing window         | Attempt did not produce authority                                                    |
| Transport/service failure | Connection failure, provider service error, unavailable region, cancelled request                          | Normalize and terminate the attempt                                                  |
| Invalid result            | Partial stream, malformed schema, missing required fields, provider refusal, late result                   | Discard as unusable; do not construct a candidate, classification, artifact, or task |
| Capacity or policy limit  | Rate/quota exhaustion, cost budget state, concurrency guard, circuit state                                 | Admit no call that exceeds the accepted bound                                        |
| Correlated safety risk    | Generator and judge resolve to the same or unverifiable vendor/failure domain                              | Required independent safety path is absent                                           |
| Credential/security issue | Authentication failure, unexpected identity, suspected credential exposure, unapproved key/profile version | Remove the affected profile from eligibility through the protected incident path     |
| Quality/semantic drift    | Provider-neutral conformance, language, safety, or rendering evidence fails accepted policy                | Treat the capability as ineligible for affected scope                                |
| Privacy/contract issue    | Region, retention, logging, training, residency, or legal terms no longer match the approved profile       | Stop disclosing data to that profile                                                 |

Exact aggregation windows, error-rate thresholds, circuit thresholds, quota reserves, budgets, and
SLOs remain OPEN. Missing required integrity or safety evidence does not wait for a statistical
threshold.

## Response Roles

The labels below follow the common runbook contract and do not grant authority. OD-027 and ADR-019
must assign accountable people, capabilities, resource scopes, environment boundaries, coverage,
and separation of duties before live use.

| Role                | Duties during this workflow                                                                                                                                 |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Incident commander  | Own scope, restrictive state, assignments, phase transitions, communications handoff, and exit evidence                                                     |
| Safety lead         | Verify common-gate containment, independent judgment, zero unauthorized output, and safe recovery evidence                                                  |
| Stage operator      | Observe live effects, engage local stop when output is unsafe or uncertain, and confirm neutral coverage                                                    |
| Service owner       | Inspect normalized attempts, approved profiles, gateway behavior, deadlines, quotas, lineage, persistence, and dispatch denial within the assigned boundary |
| Security lead       | Own credential, identity, SDK/supply-chain, provider-integrity, and correlated-failure concerns                                                             |
| Privacy/legal lead  | Assess data disclosure, residency, provider logging/training/retention, restricted content, preservation, and notification                                  |
| Communications lead | Coordinate only approved internal, talent, provider, platform, and public communications                                                                    |
| Recorder            | Maintain the sanitized timeline, decisions, evidence locations, and unresolved findings                                                                     |

Provider support personnel and vendor consoles are external evidence sources, not VNova
authorization authorities.
Profile activation, mode increase, and emergency resume each require their distinct approved human
capability; response-role assignment supplies none of them.

## Capability-Specific Containment Matrix

| Affected capability               | Immediate admission rule                                                                           | Mode/degradation posture                                                                                    | Permitted fallback behavior                                                                                                           |
| --------------------------------- | -------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Primary generation                | Do not create a candidate from a failed, partial, malformed, cancelled, timed-out, or late attempt | At most Mode 1 when a healthy policy-approved fallback exists; Mode 0 when no viable generation path exists | New bounded attempt using an eligible profile; every complete output becomes a new candidate and enters the full gate                 |
| Model-based safety classification | Mint no approval and dispatch no autonomous output                                                 | Mode 0 for required affected scope; emit fail-closed evidence                                               | Only an eligible independent safety profile may make a new classification attempt; indeterminate or exhausted fallback remains closed |
| Input moderation                  | Do not admit the affected trigger                                                                  | Mode 0 for affected work; lower session mode if isolation cannot be proved                                  | A new eligible moderation attempt over the exact unchanged normalized context; never bypass or weaken input controls                  |
| Broadcast-surface moderation      | Present nothing on the affected surface and do not redirect content to an unmoderated surface      | Mode 0 for affected work/surface; lower session mode if isolation cannot be proved                          | A new eligible attempt over the exact unchanged final presentation digest and context                                                 |
| TTS synthesis                     | Produce no playable artifact and no `SpeechTask` from a failed attempt                             | Keep speech unavailable; apply accepted mode/degradation policy without widening another surface            | New attempt from `approved_response_id` only; unchanged linguistic content and full current authorization revalidation                |
| Approved-media storage/transfer   | Mark partial, mutable, unavailable, or digest-mismatched media non-dispatchable and issue no task  | Keep the affected media path unavailable; do not bypass it through a raw or unverifiable source             | Only a reviewed immutable storage/transfer path with the same content, rights, surface, session, digest, and expiry validation        |
| Multiple or unknown capabilities  | Deny every capability whose independence and current authorization cannot be proved                | Mode 0 or emergency containment according to observed broadcast risk                                        | None until each dependency and failure domain is understood                                                                           |

An automated or operator-generated fallback line is not a provider fallback. Canned speech requires
its separate approved, identifier-only, auditable path; otherwise use silence or an approved
fallback scene.

## Immediate Containment

1. **Identify the capability boundary.** Record the affected capability, provider-profile and
   model/configuration versions, environments, sessions, surfaces, and earliest normalized
   failure without copying request or response content.
2. **Deny unsafe progression.** Apply the capability row above before completing diagnosis.
   Cancel in-flight ordinary attempts where cancellation is safe, but treat any later result as
   discarded evidence. Preserve ADR-025 ordinary effect intent/send-authorized attempt/response
   observation/application disposition and composite actor-fence lineage; a possibly-sent
   non-idempotent attempt is not replayed by a successor.
3. **Apply the safe mode ceiling.** Use ADR-020's degradation rule. A required safety-layer
   failure goes to Mode 0; a primary-generation hard failure with a healthy reviewed fallback
   goes to at most Mode 1; no viable generation path goes to Mode 0.
4. **Protect the common gate.** Verify that fallback selection cannot return an approved type,
   skip deterministic/model/policy evaluation, call media directly, or reuse a prior terminal
   decision.
5. **Protect safety capacity.** Stop nonessential provider attempts when they threaten the
   resources reserved for safety, operator control, and incident evidence. Do not increase
   concurrency or retry volume using an unreviewed value.
6. **Quarantine suspect profiles.** If identity, credential, privacy, configuration, or semantic
   integrity is in doubt, make the profile ineligible through the authorized protected path.
   Do not edit an activated profile in place or silently substitute a vendor/model.
7. **Preserve authoritative evidence.** Commit the restrictive mode/fault state, normalized
   attempt outcomes, audit metadata, and outbox notification to PostgreSQL. During PostgreSQL
   failure, retain `uncommitted_restrictive` behavior and prohibit recovery or mode increase.
8. **Use neutral coverage only.** Keep affected speech/surfaces silent or in their separately
   approved neutral state. If unsafe output may already be playing, use the safety fail-closed
   and local hard-stop workflow.

An external call whose containment result times out is not assumed successful. Maintain the
restriction and escalate.

## Read-Only Diagnosis

Diagnosis does not activate a profile, reset a circuit, change a timeout, retry production work,
mint an approval, replay an attempt, clear a mode hold, or raise autonomy.

### Scope And Timeline

- Correlate environment, session, turn, attempt, candidate, provider profile, model/configuration,
  capability, policy, surface, trace, and outbox identities.
- Compare first failure, last known success, cancellation, late-result, session-bound
  `RecoveryProbe*` lineage times, and independently collected synthetic health-probe times using
  original per-host timestamps/monotonic durations plus a separately derived timeline with named
  offset/uncertainty samples where needed.
- Determine whether the issue is one provider profile, one capability, a shared dependency,
  region, credential class, quota pool, configuration version, or independent vendor failure
  domain.
- Verify current requested/effective mode, degradation causes, emergency state, session epoch,
  operator presence, and rig health.

### Attempt And Deadline Evidence

For each sampled attempt, inspect:

- capability, purpose, immutable profile/model/configuration identity, gateway/normalization
  version, and attempt identity;
- explicit attempt timeout, enclosing deadline, queue time, start/finish/cancellation time, and
  whether the remaining turn deadline could still support the complete pipeline;
- ordinary effect intent, protected recovery/ownership composite fence, exact-open admission/
  source CAS at intent, send authorization, and advancing application, post-conflict lease
  horizon at send authorization, provider idempotency/query support, and whether no attempt is
  proven in the same-recovery complete horizon or work is possibly sent/lost-tail unknown;
- send-authorized attempt, normalized response observation/reason/schema/partial status, and
  separate applied/non-advancing/late application disposition;
- each network retry exposed by the adapter and any SDK retry configuration;
- fallback eligibility, cost/retry budget evidence, selection reason, and distinct fallback
  attempt identity;
- usage/cost metadata and quota/circuit evidence that does not reveal content or credentials.

Never infer a successful candidate from token counts, provider billing, a transport success, or a
partial stream.

### Safety And Fallback Evidence

- For generation, verify that every complete primary or fallback output created exactly one
  immutable candidate and entered the same deterministic, independent-model, and policy gate.
- Verify that a safety rejection did not trigger provider shopping and that a rewrite created new
  lineage.
- For model-based classification, verify the judge is independent of the exact generator profile,
  including every fallback combination.
- For input/surface moderation, verify a complete classification binds the exact unchanged
  normalization, final presentation digest, destination, language context, and policy version.
- For TTS, verify public invocation used only `approved_response_id`, the fallback did not alter
  linguistic content, and approval/rights/surface/session/expiry were revalidated.
- For media storage/transfer, verify staged versus ready state, immutable object version, artifact
  digest, authorization, scoped transfer, cache identity, and expiry. A storage success or cached
  object does not substitute for a committed dispatch-eligibility record.
- Verify no failed capability created an `ApprovedResponse`, surface authorization, media
  artifact, or `SpeechTask`.

### Infrastructure And Provider Evidence

- Read PostgreSQL attempt, aggregate, decision, approval, audit, and outbox state as authoritative.
- Inspect Redis only for delivery lag, duplicate delivery, or transport health; it is not provider
  or domain history.
- Review approved provider health/status evidence and support-case metadata without treating a
  vendor status page as proof of VNova recovery.
- Use only approved provider-neutral synthetic health or conformance probes. Each automated probe
  has an explicit timeout, bounded data disclosure, distinct attempt identity, and no production
  candidate or session-recovery authority. It cannot classify a session-bound possibly-sent
  effect, resolve a source ambiguity, or authorize replay.
- Confirm secrets are referenced through the managed secret boundary and never appear in logs,
  exceptions, profiles, tickets, or evidence exports.

### Session-Bound Recovery-Probe Evidence

A provider health probe is not a session-bound outcome query. When closure or recovery must
classify a specific possibly-sent ordinary effect, only ADR-025's distinct
`RecoveryProbeIntent`, `RecoveryProbeAttempt`, `RecoveryProbeResponseObservation`, and
`RecoveryProbeDisposition` lineage may interact with the provider:

- intent admission requires either the exact active fence plus immutable draining-prefix item, or
  the exact recovering fence plus durable recovery-attempt/source-ambiguity binding;
- the allowlisted operation is read-only or restrictive, has a stable idempotency identity,
  explicit timeout and unextended deadline, and finite attempt/count/byte/rate/age/concurrency
  bounds;
- one intent owns zero or more bounded attempts and exactly one terminal non-widening
  disposition; expired, cancelled, superseded, or failed-closed-before-send terminalization with
  zero attempts is valid;
- the originating fence and source binding are immutable provenance, not continuing authority. A
  current active-draining or recovering successor bound to the same source may append bounded
  evidence and terminalize the old intent, but cannot resend it; another query requires a new
  separately admitted intent;
- timeout, contradiction, or non-authoritative negative evidence may terminalize the probe as
  `unknown`, but cannot prove absence or authorize replay. The underlying source ambiguity is a
  separate axis and must be resolved, permanently safe-quarantined, or accountably disposed
  before final close; and
- every recovery-attempt-bound probe write advances the recovery invalidation/source revision.
  Recovery activation requires every such probe terminal/non-widening and each enabled-scope
  source ambiguity resolved or held behind an explicit capability disable.

## Data Minimization During Diagnosis

Use:

- opaque internal IDs and canonical digests;
- provider/profile/model/configuration and policy versions;
- normalized provider-neutral error categories;
- timings, timeouts, attempt counts, token/usage counts, and cost units;
- boolean/schema/conformance outcomes;
- affected data classification, region, and purpose metadata.

Do not place raw prompts, candidates, viewer messages, viewer memory, provider bodies, moderation
payloads, full exception bodies, credentials, keys, OAuth tokens, voice data, synthesized media, or
rights documents in ordinary logs, dashboards, tickets, chat, screenshots, or the incident
packet. A redaction failure drops diagnostic content rather than exposing it. Any indispensable
restricted inspection uses the separately authorized reveal path and remains in the restricted
store.

## Recovery Procedure

1. **Choose an already reviewed configuration.** Recovery targets an immutable approved provider
   profile/model/configuration and fallback graph. Creating or materially changing a production
   profile requires its separate protected review.
2. **Resolve security/privacy uncertainty first.** Suspected credential or data-handling issues
   require the approved credential/privacy response and a new reviewed activation decision.
   Service availability alone does not clear them.
3. **Run provider-neutral conformance.** Exercise the adapter's schema, timeout, cancellation,
   late-result, malformed-output, redaction, usage normalization, and applicable immutable-media
   integrity cases outside live work. External calls are bounded by explicit timeout and disclose
   only approved test data.
4. **Exercise failure and fallback.** In rehearsal, repeat the incident fault and prove the
   expected safe degradation, independent safety classification, fallback-through-gate, deadline
   non-extension, and absence of tasks on failure.
5. **Validate current independence.** Confirm every generator route has an eligible independent
   judge route for all enabled categories. If not, autonomous generation remains closed.
6. **Reconcile authoritative state.** Ensure restrictive mode/fault state, all ordinary attempts,
   discarded late results, every admitted session-bound recovery probe and its separately owned
   source-ambiguity classification, audit metadata, and outbox records are committed in
   PostgreSQL. Reconcile transport separately from PostgreSQL; never reconstruct provider
   lineage from Redis.
7. **Discard old work.** Do not retry, approve, synthesize, dispatch, or replay an incident-era
   candidate, classification, artifact, or task merely because a provider recovered. A further
   read-only/restrictive outcome query needs a new bounded recovery-probe intent under current
   authority; new live work receives new ordinary attempts and current deadlines.
8. **Restore eligibility deliberately.** An authorized human or reviewed deployment process may
   activate the exact reviewed profile only after evidence passes. Profile eligibility does not
   clear an emergency latch, upward-recovery hold, or mode degradation by itself.
9. **Confirm any upward transition.** ADR-020 preconditions, qualified presence, fresh preflight,
   human confirmation, rationale, current aggregate version, and durable audit are required. No
   health probe or circuit recovery automatically restores Mode 2.
10. **Observe a bounded recovery sample.** Follow newly created work through attempt, complete
    candidate, full safety gate, approval, identifier-only media, signed task, stage-host
    admission, and actual playback. Any mismatch returns to containment.

## Recovery Exit Gates

Recovery is eligible only when:

- the affected capability and failure domain are identified or unresolved scope remains disabled;
- the exact provider/profile/model/configuration and gateway versions have protected approval;
- explicit timeout, cancellation, partial/malformed, late-result, and redaction conformance passes;
- the fallback graph respects cost/retry/deadline limits and generator/judge independence;
- fallback generation crosses the same complete safety gate and fallback TTS remains
  identifier-only with unchanged linguistic content;
- the approved-media path rejects partial, mutable, corrupt, uncommitted, unauthorized, or
  expired artifacts and proves the immutable artifact digest before dispatch;
- PostgreSQL contains coherent attempts, restrictive state, audit, and outbox evidence;
- every recovery-attempt-bound session probe is terminal/non-widening and every enabled-scope
  bound source ambiguity is resolved or held behind an explicit capability disable; any session
  final close additionally requires every admitted probe terminal and each bound source ambiguity
  resolved, permanently safe-quarantined, or accountably disposed;
- no recovery decision depends on Redis retention, provider billing, or a vendor status page;
- no incident-era content, approval, artifact, or task has been revived;
- ordinary observability and the evidence packet pass prohibited-content scanning;
- required privacy, security, safety, and configuration reviewers record disposition;
- any higher mode or emergency resume is separately confirmed and durably audited.

If any gate cannot be proved, leave the capability ineligible and retain the applicable lower
mode or neutral output.

## Evidence Packet

Record:

- incident, environment, session, turn, attempt, candidate, provider profile, model/configuration,
  policy, capability, surface, artifact, storage-object version, rig, epoch, trace, audit, and
  outbox identifiers;
- immutable profile/gateway/normalization versions and approved failure-domain classification;
- normalized error/recovery codes, explicit timeout/deadline, cancellation, retry, fallback,
  quota, circuit, usage, and cost evidence;
- session-bound recovery-probe intent/attempt/observation/disposition IDs, exact authority/source
  binding, finite-budget evidence, terminal result, and the separately owned source-ambiguity
  classification or capability disable;
- requested/effective mode, degradation causes, emergency state, and containment outcomes;
- candidate/safety/media/task lineage results by ID and digest;
- PostgreSQL commit/outbox state and Redis transport observations;
- conformance and rehearsal manifests, deterministic seed, adapter versions, and artifact hashes;
- provider support/status references as supporting, not authoritative, evidence;
- human configuration, privacy, security, safety, mode, and incident decisions;
- unresolved risk, disabled scope, follow-up owner, and review status.

The packet contains no provider body, prompt, raw candidate, viewer-memory value, secret,
credential, token, voice data, media bytes, or rights document.

## Escalation

Escalate while maintaining the restriction when:

- required safety-provider independence is absent or uncertain;
- provider behavior may have produced an approval, presentation, artifact, or task without the
  required lineage;
- a partial, replaced, corrupt, wrong-version, or digest-mismatched media object may be
  dispatchable or cached;
- multiple capabilities, regions, sessions, or environments are affected;
- a credential, identity, signature, replay, supply-chain, or SDK-integrity issue is suspected;
- provider data handling may violate the approved purpose, region, retention, logging, training,
  or legal profile;
- provider diagnostics or ordinary observability may contain restricted data or secrets;
- PostgreSQL provider-attempt or audit evidence is missing or contradictory;
- recovery requires a new vendor/model, altered content, new timeout/retry/circuit value, or
  unreviewed policy;
- no neutral broadcast state can be maintained.

Exact escalation channels, severity labels, vendor contacts, response targets, and notification
duties remain human-approved OPEN decisions.

## Required Rehearsal Scenarios

Before any production provider profile is enabled, exercise:

- generation timeout, cancellation, transport failure, provider error, partial stream, malformed
  output, and late result, each producing no candidate;
- actor pause, lease expiry, revoke, or takeover before ordinary effect intent, send
  authorization, first byte, response, response-observation, and application commit, including
  exact-open admission/source-CAS rejection, possibly-sent non-idempotent work,
  ownership-row/revoke ordering, stale-composite-fence rejection, and PITR lost-tail quarantine;
- session-bound recovery-probe intent/attempt/first-byte/response/disposition cuts under both
  exact bindings, including wrong binding, zero-attempt terminalization, current-successor
  terminalization without old-intent resend, finite bounds, terminal `unknown` without source
  resolution, probe-write activation invalidation, enabled-scope capability disable, and no
  widening/absence/replay authority;
- primary generation failure followed by an eligible fallback, with a distinct attempt/candidate
  and the same full safety gate;
- fallback exhaustion, cost/retry/deadline exhaustion, and no viable generation path;
- safety-provider timeout, malformed/indeterminate result, fallback exhaustion, and
  generator/judge correlation, each producing zero autonomous speech;
- input and surface moderation timeout, digest/context mismatch, provider disagreement, and
  fallback exhaustion, each producing no presentation;
- TTS primary/fallback timeout, cancellation, altered-content attempt, rights/surface expiry, and
  late artifact, each producing no unauthorized `SpeechTask`;
- object upload/download timeout, partial upload, mutable replacement, corruption, orphan,
  unauthorized transfer, stale cache, and artifact-commit race, each producing no playback;
- quota, circuit, credential, secret-boundary, region, and privacy-profile failures;
- SDK-hidden retry detection and outer-deadline non-extension;
- PostgreSQL/outbox loss during degradation, proving immediate restriction and no upward recovery
  before durability;
- Redis loss during an incident, proving reconstruction from PostgreSQL only;
- provider recovery while old candidates, approvals, media, or tasks are expired or on an old
  epoch, proving no revival;
- operator-presence return and provider recovery without automatic Mode 2 restoration;
- redaction failure and scanning of logs, alerts, traces, provider support artifacts, and the
  incident packet;
- full incident reconstruction with normalized evidence and no restricted content.

Fake and live adapters must pass the same provider-neutral conformance suite. A live success test
does not replace deterministic failure injection.

## OPEN Values And Decisions

Human approval is required for:

- provider/vendor/model/profile selection, region, residency, processing, logging, training,
  retention, and contractual terms;
- OD-027 operational command, role/coverage, escalation, communications, exercise,
  evidence-freshness, and runbook-authorization decisions;
- generator/judge vendor pairing and independent-failure-domain criteria;
- timeouts, outer deadlines, retry/fallback caps, backoff, concurrency, queue, and cancellation
  policy;
- circuit-breaker, synthetic-health, quota, cost warning/limit, typed session recovery-probe, and
  alert thresholds;
- OD-025 immutable storage, object integrity/version, scoped transfer, cache/deduplication,
  codec/timing, interruption, and artifact-lifecycle profile;
- capability-specific degradation targets beyond the accepted ADR-020 matrix;
- credential custody, rotation, revocation, provider-profile activation, rollback, and disable
  workflow;
- exact conformance fixtures, live validation scope, canary/readiness evidence, and observation
  window;
- incident role assignments, escalation contacts, severity model, and operational SLOs;
- evidence retention, restricted-reveal, privacy, security, and legal response policy.

No SDK, library, vendor, deployment, example, fixture, or dashboard default may become a production
value without the required human decision.
