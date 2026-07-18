# Operator Identity Compromise Runbook

Status: Proposed rehearsal-only operational procedure; readiness state: `Drafted`;
non-authorizing and not a substitute for the deployment's identity-provider or security incident
process

Governing sources:

- [ADR-008: safety gate enforcement](../adr/0008-safety-gate-enforcement.md)
- [ADR-011: stage-host wire protocol and clock synchronization](../adr/0011-stage-host-wire-protocol-and-clock-synchronization.md)
- [ADR-015: layered emergency stop](../adr/0015-layered-emergency-stop.md)
- [ADR-017: data retention, privacy, and PII](../adr/0017-data-retention-privacy-and-pii.md)
- [ADR-019: authentication, authorization, and operator roles](../adr/0019-authentication-authorization-and-operator-roles.md)
- [ADR-020: mode transition and degradation matrix](../adr/0020-mode-transition-and-degradation-matrix.md)
- [ADR-021: broadcast surface inventory and overlay policy](../adr/0021-broadcast-surface-inventory-and-overlay-policy.md)
- [ADR-022: voice rights and talent licensing metadata](../adr/0022-voice-rights-and-talent-licensing-metadata.md)
- [VNova threat model](../security/threat-model.md)

The actions below describe required containment and recovery semantics. They do not define
identity-provider commands, token formats, session lifetimes, concrete role names, communication
destinations, or numeric response targets. Those values and procedures remain protected human
decisions under OD-022, OD-027, and OD-028.

## Purpose And Entry Conditions

Use this runbook when the integrity of a human operator identity or its authorization evidence is
suspect, including:

- a stolen workstation, browser profile, session cookie, refresh credential, authenticator, or
  recovery factor;
- phishing, session fixation, CSRF, malicious extension, credential replay, impossible travel, or
  an identity-provider alert;
- an unexpected login, state subscription, candidate decision, manual speech submission, mode
  change, emergency resume, restricted-data reveal, policy activation, rights change, role grant,
  export, or break-glass use;
- shared-account use, incorrect subject mapping, disabled-account activity, stale role or scope,
  or a presence lease that survives revocation;
- suspected compromise of an identity administrator, authorization policy, group assignment,
  privileged-access workflow, or operator-to-internal-ID mapping;
- a workload, rig, or local safety identity being misrepresented as a human operator.

A credible report is enough to begin restrictive containment. Responders do not wait for proof
before preventing new privileged actions. Uncertainty is treated as compromised authority for the
affected scope, but stop and safe mode-decrease paths remain available through independently
valid authority and the local physical stop.

## Required Human Functions

Assign these functions through the approved incident process:

| Function              | Responsibility                                                                          |
| --------------------- | --------------------------------------------------------------------------------------- |
| Incident commander    | Owns scope, handoffs, timeline, decisions, and exit evidence                            |
| Security lead         | Owns identity/session containment, forensic scope, credential and endpoint assessment   |
| IAM owner             | Applies identity-provider, assignment, session, authenticator, and policy controls      |
| Safety lead           | Determines output containment and validates safety-gate consequences                    |
| Session-runtime owner | Reconciles commands, decisions, epochs, mode, and in-flight work                        |
| Stage operator        | Confirms local output, queue, rig binding, and physical hard-stop state                 |
| Privacy/legal lead    | Decides notification, evidence, employee/privacy, retention, and disclosure obligations |
| Communications lead   | Coordinates approved internal, talent, platform, partner, or public communication       |
| Recorder              | Maintains the sanitized incident timeline and unresolved-action register                |

One person may fill multiple functions only where the accepted separation-of-duty policy permits.
The affected operator does not approve their own restored access, emergency resume, mode increase,
or exceptional content unless an explicitly accepted policy allows it.

## Safety Principles

- UI visibility, VPN location, an open WebSocket, a remembered browser, or possession of an object
  ID is never authorization.
- Human, workload, rig, and local-safety identities are distinct. One cannot be converted into
  another to preserve availability.
- Revocation uncertainty denies privileged mutations and restricted reads and makes operator
  presence absent or uncertain.
- A compromised operator decision is preserved as evidence; it is not rewritten or silently
  deleted. Downstream authority is invalidated and new work uses new lineage where required.
- Safe-direction actions already applied, including stop and mode decrease, are not reversed
  merely because their initiating identity later becomes suspect.
- E-stop remains one action without confirmation or a reason requirement. Identity investigation
  must not delay the local hard stop when audience output is unsafe or uncertain.
- Recovery of an account, identity provider, network, or audit system never raises mode, restores
  presence, resumes emergency state, or revives work automatically.

## Scope Decision

Start with every environment, talent, session, rig, data class, and time interval reachable by the
suspect principal, session, device, group, role, policy, or administrator. Narrow only after
authoritative evidence proves isolation.

| Observed condition                                                                | Minimum containment posture                                                                                                                  |
| --------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| One browser session is suspect and session identity is authoritative              | Revoke that session and all derived subscriptions, presence, challenges, and in-flight commands                                              |
| Human account or authenticator is suspect                                         | Disable/restrict the account and revoke all accepted sessions and presence leases for its VNova scope                                        |
| Role/group/authorization assignment is suspect                                    | Freeze affected privileged capabilities and review every principal receiving the assignment                                                  |
| Identity administrator, policy store, signing keys, or subject mapping is suspect | Deny privileged operations for the affected environment or broader identity domain                                                           |
| Compromised authority may have approved or dispatched output                      | Stop affected progression, invalidate epochs/authorizations, lower mode; engage emergency stop if current output cannot be proved safe       |
| Restricted content or rights evidence may have been accessed                      | Disable further reveal/export and invoke privacy/legal and rights-specific response                                                          |
| Break-glass credential is suspect                                                 | Disable the break-glass path if independently possible, alert protected owners, and treat its full documented scope as affected              |
| Workload or rig identity is suspect instead of a human                            | Isolate that credential class and invoke the applicable provider, protocol, rig, or signing incident process; never record it as an operator |

Scope is based on effective authority, not the account's advertised role name.

## Immediate Containment

Perform the following semantic actions. Independent safe actions may run concurrently, and failure
of a later step never rolls back a restrictive effect.

1. **Protect audience output.** If suspect commands may have caused unsafe or unauthorized output,
   stop affected new generation, approval, synthesis, dispatch, and presentation. Lower the
   effective mode immediately. If the affected work or rig state cannot be isolated and proved
   safe, engage cloud freeze and local hard stop; stop has no confirmation.
2. **Declare the incident.** Create a restricted incident identity and record the report source,
   server receipt time, suspected principal/session/device, environment, initial scope, and named
   response functions. Do not paste tokens, credentials, candidate text, viewer memory, rights
   evidence, or restricted media into the ordinary record.
3. **Revoke active human authority.** Through the independently trusted identity and VNova
   boundaries, disable or restrict the suspect account and revoke its browser sessions,
   authenticators or recovery factors as applicable, real-time subscriptions, command
   challenges, cached authorization evidence, and presence leases. Exact provider operations are
   deployment-specific and must be approved before production.
4. **Deny new privileged effects.** Block affected candidate decisions, manual speech, mode
   increase, emergency resume, restricted reveal/export, policy or prompt activation, access
   management, rights administration, and other privileged commands. Unknown authorization or
   policy state is denial, not a default role.
5. **Advance restrictive session state.** Presence loss caps Mode 2 at most to Mode 1. Lower to
   Mode 0 or engage freeze when suspect approvals, policy, rights, dispatch, or scope cannot be
   independently validated. Advance the session authorization epoch for an effective mode
   decrease and evict old-epoch queued work through the accepted protocol. A returned operator
   never restores the higher mode automatically.
6. **Invalidate pending command authority.** Reject uncommitted commands, confirmation challenges,
   resume challenges, idempotency continuations, and state-channel cursors derived from the
   suspect authentication context. Reusing an identity with different canonical content is an
   integrity incident.
7. **Reconcile suspect actions.** Enumerate every allow/deny decision and command in the exposure
   interval, including review, submit, stop, resume, lower, raise, reveal, activate, access change,
   rights change, archive/export, and subscription activity. Cancel or invalidate dependent
   in-flight work before detailed investigation.
8. **Preserve immutable decisions safely.** Do not reopen a terminal `SafetyDecision` or edit
   audit history. If suspect human approval backed an `ApprovedResponse`, invalidate its current
   dispatch/media/session authorization and create new candidate/decision lineage for any future
   attempt. A stop or safe decrease remains effective.
9. **Contain persistent access.** Freeze suspect role, group, policy, identity mapping,
   break-glass, API/session, and privileged-device changes. Remove persistence only through an
   independently authenticated owner and preserve before/after evidence.
10. **Escalate.** Notify the approved security, IAM, safety, operations, privacy/legal, talent,
    rights, and communications channels for the affected scope. Regulatory, employee, partner,
    talent, platform, or audience notification is an accountable human decision.

Every identity-provider, policy-store, session-store, audit-store, or remote-control operation has
an explicit timeout. A timeout or indeterminate response leaves the control unresolved and the
broader restriction in place.

## Containment Confirmation

Containment is not complete until authoritative evidence proves:

- the suspect principal cannot start or refresh a VNova session;
- every accepted browser session, real-time subscription, presence lease, step-up result,
  confirmation/resume challenge, and cached authorization derived from it is expired or revoked;
- suspect role, group, object-scope, policy, identity mapping, and break-glass persistence is
  removed or held disabled;
- the affected environment rejects privileged commands from stale tokens, sockets, cursors,
  duplicated requests, delayed messages, and replayed idempotency identities;
- all affected sessions are at the lowest provable mode, current authorization epoch, and required
  emergency state;
- stage hosts have evicted old-epoch work, or disconnected/unverified rigs are in their accepted
  local safe state;
- suspect approvals, manual speech, resumes, mode changes, policy activations, rights changes,
  reveals, exports, and access grants have been enumerated and their dependent effects contained;
- restricted data and rights evidence access are blocked from the suspect authority;
- audit, identity, command, and stage-host evidence are preserved without secrets or restricted
  content in ordinary records;
- an independently trusted administrative path remains for continued response.

If identity-provider, authorization, audit, runtime, rig, or local state cannot prove an item, the
incident remains partially contained and the corresponding restriction remains.

## Investigation And Evidence

Build a correlated timeline using:

- immutable operator ID, identity-provider issuer/subject reference, authenticated-session ID,
  device or managed-endpoint reference, and authentication method/time evidence;
- roles, groups, capability evaluations, object scopes, policy versions, assignment changes,
  step-up results, presence lease generations, and break-glass events;
- command, idempotency, challenge, aggregate, event, trace, session, rig, epoch, candidate,
  decision, approval, authorization, artifact, task, export, and reveal IDs;
- canonical request digests, allow/deny outcomes, reason codes, server receipt times, target-local
  observations, and clock-offset metadata;
- identity-provider, authorization-policy, console, control-api, session-runtime, PostgreSQL,
  stage-host, and restricted-access outcomes.

Ordinary logs and the incident timeline must not contain bearer tokens, session cookies, refresh
credentials, authenticator secrets, recovery codes, signing material, provider credentials, raw
prompts, raw candidates, viewer-memory values, rights evidence, or unrestricted media. Do not hash
a secret and place it in a general record as a substitute for proper custody.

Sensitive identity-provider or endpoint evidence uses the approved restricted forensic store,
purpose logging, access roles, retention, legal hold, and disclosure process. Collection must be
proportionate to the incident and applicable privacy/employment rules as determined by accountable
humans.

Determine at least:

- initial access vector and earliest/latest plausible exposure;
- every account, device, factor, session, grant, scope, environment, talent, and administrative
  boundary affected;
- whether an identity, endpoint, browser supply chain, authorization policy, role assignment,
  identity mapping, break-glass path, workload, rig, or signing key remains compromised;
- which commands were attempted, accepted, denied, duplicated, delayed, or replayed;
- whether unsafe content, rights misuse, privacy access, evidence tampering, or public broadcast
  occurred;
- whether a suspect actor changed controls intended to detect or contain the incident;
- whether external notification, password/session reset, device rebuild, key rotation, rights
  suspension, platform action, or talent communication is required.

## Command And Decision Reconciliation

Classify each suspect-interval action without rewriting history:

| Action                               | Reconciliation rule                                                                                                              |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| Emergency stop or safe mode decrease | Preserve the restrictive result; verify scope and provenance but never auto-undo it                                              |
| Emergency resume or mode increase    | Invalidate dependent higher-authority context; return to safe state and require a new independent confirmed workflow             |
| Candidate approval/rewrite/rejection | Preserve the terminal decision as evidence; invalidate affected downstream authorization; any renewed content uses new lineage   |
| Manual speech submission             | Treat submission as untrusted provenance; cancel pending work and require a fresh common safety path                             |
| Policy/prompt activation             | Disable suspect version and recover only to an independently reviewed known version; do not silently edit the activated artifact |
| Rights grant/state change            | Suspend affected voice use and invoke the [voice-rights revocation runbook](voice-rights-revocation.md)                          |
| Restricted reveal/export             | Revoke further access, preserve access metadata without copying content, and invoke privacy/legal review                         |
| Role/access/break-glass change       | Remove suspect persistence through independent authority and review every derived principal                                      |
| State subscription                   | Close it, invalidate cursors/resume authority, and prove no restricted data continued after revocation                           |

An operator identity is decision provenance, not content safety by itself. Invalidating the current
use of a suspect decision does not create a second terminal decision for the same candidate.

## Failure Variants

| Failure during response                     | Required posture                                                                                                                                             |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Identity provider unavailable               | New login/refresh fails closed; locally verifiable sessions continue only to accepted expiry unless independently revoked; no lifetime or presence extension |
| Authorization policy unavailable or suspect | Deny mutations and restricted reads; apply Mode 0/freeze where current output authority is uncertain                                                         |
| Audit persistence unavailable               | Stop and safe mode decrease proceed and buffer evidence; resume, mode increase, reveal, access change, and policy activation remain blocked                  |
| Console state channel unavailable           | Do not infer success; use the independent command and local-stop paths                                                                                       |
| Runtime or cloud identity unavailable       | Local physical hard stop remains available; do not convert a rig/local identity into operator authority                                                      |
| Stage host unreachable                      | Cloud freezes/lowers; watchdog and local operator establish safe state; no normal resume before reconciliation                                               |
| IAM administrator may be compromised        | Use the pre-approved independent administrative or break-glass authority; never let the suspect path approve itself                                          |
| Break-glass path also uncertain             | Disable privileged production operations, preserve local stop, and escalate to the highest approved independent authority                                    |
| Session revocation propagation is uncertain | Treat the principal as active for scope analysis but deny through a broader server-side restriction                                                          |
| Signing or workload keys may be exposed     | Invoke the protected key/workload incident process and broaden containment; do not rotate blindly without preserving verification and rollback safety        |

## Eradication And Recovery

Recovery requires independent proof; a password reset or returned identity-provider availability
is insufficient.

1. Remove the initial access and all persistent sessions, factors, devices, grants, policies,
   mappings, API credentials, or malicious software within the confirmed scope.
2. Restore the identity, authorization, and endpoint systems from trusted versions and validate
   issuer, subject mapping, key rotation/revocation, policy, and protected administrator paths.
3. Reconstruct and disposition every suspect command and dependent effect. Preserve immutable
   history; issue new lineage or authorization only where future work is still appropriate.
4. Re-enroll or restore the human operator through the approved workforce process with independent
   identity proof, authenticators, least-privilege assignments, object scope, and separation of
   duty. A prior session, cursor, challenge, or presence lease is never reused.
5. Confirm restricted-data, viewer-memory, audit, and rights access remain physically and
   logically separated and that no unauthorized exports or secondary copies persist.
6. Reconcile PostgreSQL state, outbox effects, runtime ownership, session epoch, stage-host queue,
   emergency latch, rig binding, clock, and renderer state. Redis or browser cache is never the
   recovery source.
7. Run the applicable deterministic identity, authorization, mode, emergency, rights, and
   broadcast-surface rehearsals against the exact recovered policy and target.
8. Obtain independent security, IAM, safety, operations, privacy/legal, and affected talent/rights
   review before re-enabling privileged capabilities.
9. Establish a fresh operator presence lease only through a qualifying authenticated human
   action. If mode was lowered, any increase is separately confirmed with current preconditions
   and rationale.
10. If emergency stop was engaged, use the ADR-015 deliberate resume flow with confirmation,
    non-empty reason, and cloud/local reconciliation. Identity recovery never clears the latch.

## Exit Criteria

The incident may leave active response only when:

- the initial access and persistence are removed and independently validated;
- every affected identity, session, factor, device, grant, policy, scope, break-glass path,
  workload, rig, and signing authority has a recorded trusted or disabled disposition;
- every suspect command and derived content, rights, surface, media, mode, emergency, access, and
  data effect has a terminal disposition;
- no stale session, socket, cursor, challenge, idempotency continuation, presence lease, or
  authorization can regain authority;
- all affected sessions and rigs are reconciled to current epochs and safe local state;
- required privacy, legal, employment, talent, platform, partner, and communications actions are
  complete or assigned through an approved tracked process;
- sanitized audit and restricted forensic evidence are complete, access-controlled, and governed
  by approved retention, deletion, and hold decisions;
- restored access, deliberate resume, and any upward mode transition have independent approval
  and target evidence, or the affected capabilities remain disabled;
- corrective actions, control gaps, residual risks, and runbook changes have accountable owners.

Incident closure never supplies risk acceptance, restores a role, resumes a broadcast, raises a
mode, or reauthorizes a decision by itself.

## Required Rehearsal Tests

Before privileged production operation, rehearse at least:

- stolen browser session, refresh credential, device, authenticator, and malicious-extension
  scenarios;
- session fixation, CSRF, command replay, idempotency conflict, stale challenge, old WebSocket/SSE
  cursor, and delayed revocation;
- account disable, role/group removal, object-scope loss, policy change, and presence expiry while
  Mode 2 work is generated, approved, dispatched, queued, and immediately pre-playback;
- unauthorized candidate decision, manual speech, emergency resume, mode increase, policy
  activation, rights change, restricted reveal/export, access grant, and break-glass use;
- compromised identity administrator, authorization-policy store, subject mapping, endpoint, and
  break-glass path;
- identity-provider, authorization, audit, PostgreSQL, runtime, network, console, and stage-host
  outage during containment;
- physical hard stop with cloud, SSO, VPN, database, and console unavailable;
- reconciliation proving suspect terminal decisions are preserved but cannot continue to media or
  playback and any retry uses new lineage;
- duplicate, reordered, and late commands after revocation with no privilege or stale-task
  revival;
- recovery proving a fresh authentication session and presence lease do not automatically resume
  emergency state or raise mode;
- a complete synthetic incident timeline without tokens, credentials, candidate text, viewer
  memory, rights evidence, or unrestricted media in the ordinary report.

Concrete IAM/provider steps, response and revocation SLOs, role roster, coverage, exercise cadence,
independent assessor, evidence freshness, and residual-risk authority remain OPEN under OD-022,
OD-027, and OD-028. The current `Drafted` state and missing evidence are tracked in the
[operational readiness review packet](../governance/operational-readiness-review.md); document
completion does not constitute rehearsal, target validation, or production authorization.
