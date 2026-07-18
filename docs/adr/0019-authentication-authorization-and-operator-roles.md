# ADR-019: Authentication, Authorization, And Operator Roles

Status: Proposed

Priority: P1

Date: 2026-07-17

Sources: `AGENTS.md`, `vnova-review-handoff.md`, ADR-003, ADR-008, ADR-015, ADR-016,
ADR-017, ADR-025

This ADR is non-binding while its status is `Proposed`. It does not select an identity
vendor, create production role assignments, or authorize operator-console implementation.

## Context

The operator console can approve speech, submit manual speech, reveal restricted generation
data, change autonomy, activate policy, stop a broadcast, and resume after an emergency.
Those are safety and security decisions. Hiding or disabling a button in the UI is not an
authorization boundary.

The console is internal-only behind SSO and VPN, but network location alone is not identity,
and authentication alone does not establish permission over a particular environment,
talent, rig, or `StreamSession`. VNova also has workload and rig principals that must not
inherit human privileges or manufacture operator provenance.

## Decision

VNova will use centralized workforce authentication for humans and deny-by-default,
capability-based authorization enforced on every server-side command and restricted read.
Named roles are administrative bundles of capabilities; role names and bundle composition
are deliberately not architecture constants.

Authorization decisions bind:

```text
principal
  x authenticated session
  x semantic capability
  x resource scope
  x environment
  x command/read context
  x active authorization-policy version
  -> allow or deny
```

An allow decision for one action never implies a broader role, a different resource, or
future authorization. The operator console may present the evaluated permissions for
usability, but `control-api` and the owning domain boundary enforce them.

## Principal Types

VNova distinguishes at least:

- **Human operator principals**, authenticated through workforce SSO and identified by an
  immutable provider subject mapped to an internal `operator_id`.
- **Cloud workload principals**, assigned to `control-api`, `session-runtime`, and narrowly
  scoped background jobs.
- **Rig principals**, one per enrolled stage-host installation or device identity, bound to
  permitted environments and rig records.
- **Local safety inputs**, such as the physical e-stop hotkey, recorded as trusted local
  device provenance rather than a human principal.

Service accounts, rig identities, and local safety inputs cannot be recorded as
`decided_by = operator_id`. Human decisions retain the human operator identity even when a
workload transports the command.

Shared human accounts are prohibited. Email address and display name are mutable profile
attributes, not authorization identity.

## Human Authentication

The operator console is reachable only through the approved private-access boundary and
workforce SSO. Exact VPN/access technology and SSO vendor remain OPEN.

The authentication profile must provide:

- a stable issuer and immutable subject;
- audience-bound, signed, time-bounded assertions;
- account disablement and group/assignment lifecycle;
- multi-factor authentication appropriate to privileged broadcast control;
- authentication time and method evidence for step-up decisions;
- issuer-key rotation and revocation behavior;
- an internal `operator_id` that survives display-name or email changes.

The browser never stores provider credentials, long-lived refresh secrets, service
credentials, or stage-host keys. Access assertions are protected against script access and
cross-site request forgery according to the selected console architecture. Exact session,
refresh, idle, and step-up lifetimes remain OPEN and must not be embedded as unreviewed
defaults.

`control-api` validates issuer, audience, signature, expiry, not-before, subject, and required
authentication context. It must not make every command synchronously dependent on a live
identity-provider request. Already issued assertions may be validated with trusted,
rotation-aware key material until their accepted expiry; outages never extend validity.

## Workload And Rig Authentication

Cloud-to-cloud calls use distinct workload identities and mutually authenticated transport.
A workload receives only the capabilities required for its fixed responsibility boundary.
Provider API credentials are not workload identity and remain inside provider gateways.

`stage-host` uses an enrolled rig identity on the authenticated runtime link. Rig identity is
bound to an environment, rig record, allowed stream-session binding, and protocol epoch. It
can report local state and consume authorized `SpeechTask` work as permitted by ADR-016; it
cannot call human approval, mode-increase, policy-activation, restricted-data, or identity
administration operations.

Exact workload credential technology and the stage-host cryptographic profile remain OPEN
under their owning deployment and protocol decisions.

## Authorization Model

Capabilities are semantic permissions evaluated over a resource scope. Initial capability
classes are:

| Capability class                                         | Resource scope                          | Required behavior                                                                                                                     |
| -------------------------------------------------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Observe live operational state                           | environment, talent, session, or rig    | Excludes restricted candidate/prompt content unless separately allowed.                                                               |
| Review a candidate                                       | session and candidate                   | Completes the same `SafetyDecision` flow as automated review and records `operator_id`.                                               |
| Submit manual speech                                     | session and talent                      | Submission is not approval and still enters the common safety lineage.                                                                |
| Lower requested mode                                     | session                                 | No confirmation or health precondition may block a safe-direction change.                                                             |
| Request a higher mode or confirm effective-mode recovery | session and target mode                 | Requires confirmation, current preconditions, and ADR-020 enforcement; the operator never assigns computed `effective_mode` directly. |
| Engage emergency stop                                    | session/rig scope accepted by ADR-015   | One click, idempotent, no confirmation, no reason requirement.                                                                        |
| Resume from emergency stop                               | stopped session and rig binding         | Separate authority; requires confirmation, non-empty reason, and reconciliation.                                                      |
| Reveal restricted generation data                        | specific restricted record and purpose  | Default redaction; reveal requires a logged reason and time-bounded access.                                                           |
| Activate policy or prompt version                        | environment/talent/session policy scope | Versioned activation, confirmation, and protected review evidence.                                                                    |
| Manage operator access                                   | organization/environment scope          | Cannot silently modify immutable audit history or self-approve prohibited grants.                                                     |
| Read or export audit evidence                            | explicitly granted audit scope          | Separate from viewer-memory access; export is itself audited.                                                                         |

These rows define required separation of semantic authority, not final API permission strings
or concrete role names. One deployment may bundle capabilities only through a human-reviewed,
versioned authorization policy.

All resource checks are object-level. Possession of a valid identifier does not authorize
access. Environment boundaries, especially rehearsal versus production, are explicit; a
rehearsal grant does not imply production authority.

## Dangerous-Action Rules

| Action                   | Authentication and authorization                                     | Confirmation                     | Reason                                            | Concurrency behavior                                 |
| ------------------------ | -------------------------------------------------------------------- | -------------------------------- | ------------------------------------------------- | ---------------------------------------------------- |
| E-stop                   | Current authorized cloud principal, or trusted local safety input    | Never                            | Not required                                      | Stale version cannot block stop; idempotent          |
| Emergency resume         | Human principal with distinct resume authority and required presence | Required                         | Required                                          | State-bound challenge; stop wins races               |
| Mode decrease            | Human or reviewed system principal with scoped authority             | Never                            | Policy-dependent audit note only                  | Stale version cannot block safe decrease             |
| Mode increase            | Human principal with increase authority and required presence        | Required                         | Audited rationale                                 | Preconditions and aggregate version must still match |
| Candidate decision       | Human review authority over the candidate/session                    | Explicit decision                | Required for policy-defined exceptional decisions | Exactly one terminal decision                        |
| Manual speech submission | Manual-submission authority                                          | Explicit submit action           | Provenance required                               | Does not imply approval                              |
| Restricted-data reveal   | Privileged reveal authority                                          | Explicit purpose acknowledgement | Required                                          | Narrow, time-bounded record access                   |
| Policy/prompt activation | Protected activation authority                                       | Required                         | Required                                          | Version and review evidence must match               |

Confirmation is an intentional command semantic validated by the server. It is not inferred
from button placement. Emergency stop and mode decrease both forbid confirmation because
they move the system in the safe direction. E-stop additionally forbids a reason requirement
and must remain a one-click action.

The same operator submitting and approving manual speech, approving their own policy change,
or granting their own access may require separation of duties. Exact rules remain OPEN and
must be decided before those production capabilities are enabled.

## Command Authorization Envelope

Every operator command carries or is transformed into immutable authorization provenance:

- command and idempotency identities;
- protected submission recovery generation or equivalent receipt-authority token;
- authenticated `operator_id` and session identity;
- command type and a digest of canonical semantic intent;
- target environment and object scope;
- authorization policy version and evaluated capability;
- authentication time/method evidence needed by the action;
- issuance and expiry timestamps;
- expected aggregate version where applicable;
- confirmation/challenge identity and reason where required.

The semantic digest binds target, parameters, expected versions, deadline, and required
confirmation/reason semantics. It excludes bearer tokens, authentication session IDs, token
expiry, transport identity, and the particular authorization evaluation. Those volatile values
remain separately referenced as immutable original provenance, while execution and every
receipt/status lookup perform current authorization.

Command authorization evidence is append-only rather than an overwrite of the receipt or
semantic intent. Each immutable `CommandAuthorizationObservation` binds the command/intent,
principal or trusted source, semantic digest, environment/resource/capability, minimized
authentication-method/step-up/presence references, evaluator/workload identity, authorization
policy version and epoch, allow/deny result with reason, evaluation time, and non-extended
evidence expiry. It never stores a bearer token, session cookie, reusable credential, or raw
challenge response.

Initial acceptance conflicts/CASes the exact open normal-work admission epoch and command-source
row, obtains fresh accepted database time after that conflict, proves the immutable hard deadline,
and commits the first observation with the intent and receipt. A new key serialized after the
closure cut receives no-lineage `session_closed`; an authorized duplicate of a
pre-closure-cut receipt uses only the existing-record disclosure path and cannot create a second
lineage. A same-intent
retry with refreshed credentials may append a new deduplicated observation after fresh
authentication and authorization only while the command is nonterminal, before its hard
deadline, and under the same exact-open admission/source CAS. The append evaluates the immutable
hard deadline and evidence expiry against fresh accepted database time obtained after that
conflict. It never mutates the original intent, receipt, provenance, or prior evidence. A
draining/closed, terminal, or effectively expired command does not accept another authorization
observation; the retry may perform only currently authorized receipt disclosure using its
separate bounded access-decision audit.
Before domain mutation, the owning service obtains an authoritative current evaluation through
the accepted authorization boundary with an explicit timeout, durably records/selects the exact
observation, and binds its policy/revocation epoch and expiry into the protected commit. Every
append increments or CASes a per-command authorization-lineage revision. Execution conflicts on
that lineage, applies the deterministic selection/precedence rule accepted under OD-022, and
compares the exact expected revision in its final transaction; a concurrent observation append
invalidates the attempt. Until the rule decides ordering among concurrent allow, retryable deny,
step-up, and unavailable observations, an incomparable or newer competing result fails closed and
an older allow cannot be chosen opportunistically. A policy, role, presence, revocation, or
evidence-expiry change before commit rejects execution and requires another current evaluation.
No process-local token refresh or transient forwarding becomes recovery authority.

The console sends commands upward through REST POSTs with idempotency keys. WebSocket or SSE
is for state delivery and is never the sole command path. `control-api` authenticates and
authorizes the caller, then forwards a canonical command using its workload identity with the
original human provenance intact. Under ADR-025, the session-runtime ingress boundary verifies
submission recovery generation, command provenance, target scope, expiry, canonical digest, and
idempotency, then conflicts/CASes the exact open normal-work admission/source row, obtains fresh
accepted database time after that conflict, and persists an immutable command intent and durable
receipt before `control-api` can report acceptance. The same transaction persists the initial
immutable command-authorization observation or acceptance fails closed. A new key that loses to
begin-close returns no-lineage `session_closed`; a duplicate that finds a pre-close record can
only disclose that record under current object authorization. A stale/unknown recovery
generation or unclosed lost-tail receipt absence requires reconciliation rather than fresh
acceptance; stop remains the safe-direction exception.

The receipt is not domain success. Delivery to the exact active recovery/ownership composite
actor fence is at least once. Before mutation, that actor revalidates current authorization and
domain preconditions through ADR-025's protected commit, binding the exact current authorization
observation and policy/revocation epoch; state and terminal command outcome commit atomically.
Deadline passage makes pending work permanently ineligible. If `control-api`
or the console times out, the caller reports an unknown observation and queries or resubmits the
same idempotency identity. Possession of that identity is not read authority: every lookup
and every duplicate-submission path that returns an existing receipt/outcome reauthenticates and
reauthorizes the exact object/data class and may deny/redact after revocation. It never infers
success from a transport write or missing error.

Raw identity-provider tokens are not copied into domain events, general logs, Redis
messages, or stage-host traffic.

## Real-Time State Subscription Authorization

WebSocket or SSE state delivery is a protected read surface, not a trusted tunnel.

- The handshake authenticates the human session and authorizes every requested environment,
  talent, stream-session, rig, and data-class scope.
- The server filters each message by the connection's current authorized scope. A general
  live-state subscription never includes restricted candidate/prompt content, viewer memory,
  or audit data without the corresponding independent capability.
- A connection cannot outlive the authentication and authorization evidence that established
  it. Expiry, revocation, operator disablement, resource-scope loss, or incompatible
  authorization-policy change closes or safely narrows the subscription.
- Reauthentication or reconnect creates a new authorization decision; an old socket,
  cursor, resume token, or cached client state cannot extend authority.
- State connections carry no command authority. Every mutation still uses the authenticated,
  idempotent command path.

Exact reconnect, cursor, and reauthentication protocols and numeric connection lifetimes
remain OPEN.

## Operator Presence State

Authentication and operator presence are different facts. A valid login or open console
socket does not indefinitely prove that a human is supervising a live session.

Presence is represented by a renewable, time-bounded, session-scoped lease derived from an
authenticated human action. The presence record binds operator identity, session,
environment, authentication context, issuance/expiry, and monotonic lease generation.
Passive WebSocket connectivity alone cannot renew it.

Semantic presence states are:

| State       | Meaning                                                                                           |
| ----------- | ------------------------------------------------------------------------------------------------- |
| `absent`    | Qualifying unexpired leases do not meet the human-approved count and capability requirements.     |
| `present`   | Current leases meet the human-approved required count and capability mix for the session.         |
| `uncertain` | Presence evidence is stale, contradictory, or cannot be verified; treated as absent for autonomy. |

Logout, revocation, lease expiry, incompatible role change, or loss of verifiable state
transitions the operator to absent/uncertain and emits `OperatorPresenceChanged`. ADR-020
immediately degrades modes that require presence. A returned operator never causes automatic
mode increase.

Exact lease duration, renewal gesture, number of required operators, and which capability
bundles qualify for each mode remain OPEN.

## Authentication And Authorization Failure Behavior

- **Identity provider unavailable:** new login and refresh fail closed. An already valid
  locally verifiable session may continue only to its accepted expiry. No outage extends a
  token or presence lease.
- **Authorization policy unavailable, unknown, or invalid:** mutation and restricted reads
  are denied. No implicit default role is applied.
- **Authorization evidence expires in flight:** the owning service rejects the command
  execution attempt before mutation. A retryable stale/expired/step-up condition keeps the
  command pending but ineligible until a new append-only `CommandAuthorizationObservation`
  arrives or the immutable command deadline passes; it retains the original semantic intent,
  receipt, and safe idempotency scope. Only a denial class explicitly accepted as nonretryable
  may terminally reject the command.
- **Policy version changes:** uncommitted commands are re-evaluated; a prior UI decision is
  not grandfathered.
- **Audit persistence unavailable:** e-stop and mode decrease still take their safe effect
  and buffer evidence. Resume, mode increase, restricted reveal, access management, and
  policy activation fail closed.
- **Console state channel unavailable:** commands use REST; loss of state streaming cannot
  make the client assume success.
- **Command-forwarding or response timeout:** the client-visible result is unknown. A durable
  receipt/outcome query or same-intent idempotent retry resolves it; a timeout is not a terminal
  rejection or success.
- **Cloud identity unavailable:** the physical/local hard-stop path remains operational.
- **Revocation uncertainty:** privileged mutations fail closed and operator presence is
  treated as absent.

Break-glass access, if approved, uses a separate, time-bounded, strongly authenticated,
alerting path with post-use review. It cannot bypass safety approval, identifier-only media,
e-stop dominance, audit separation, or stage-host verification.

## Audit Requirements

Allow and deny decisions for privileged actions are audited. Each record includes:

- immutable principal identity and, only for human principals, the internal `operator_id`;
- authenticated-session and authentication-context references;
- action/capability, target scope, and authorization-policy version;
- decision and machine-readable reason codes;
- command/idempotency/trace identities and canonical request digest;
- confirmation, human reason, and step-up evidence where required;
- previous and resulting domain state or immutable references to them;
- server receipt and decision timestamps;
- downstream acceptance, rejection, timeout, or reconciliation outcome.

Logs contain neither bearer tokens nor secrets. Restricted candidate/prompt content and
viewer-memory content are never copied into authorization or audit records. Restricted-data
reveals record the object ID, purpose, viewer, and outcome rather than duplicating the
revealed content. Viewer-memory and audit access capabilities remain separate as required by
ADR-017.

Operator command, identity-mapping, authorization-policy, role-assignment, and break-glass
changes are themselves audited. Audit retention and legal redaction follow ADR-017.

## Enforcement

- All protected HTTP routes and real-time handshakes/subscriptions authenticate before
  delivery or domain handling and authorize against the concrete object and data-class
  scope.
- Domain services recheck command provenance and business preconditions; route checks alone
  are insufficient.
- The operator console does not call Redis, stage-host adapters, provider gateways, or
  persistence directly.
- Workload and rig identities use independent credential classes and cannot be converted to
  operator identities.
- Authorization policy and role assignments are versioned, reviewable, and deployed through
  a protected path.
- Unknown capability, resource, principal, policy version, or authentication context is
  denied.
- E-stop, safety, contracts, policy defaults, identity configuration, and authorization
  enforcement remain CODEOWNERS-protected and human-reviewed.
- Tests enumerate every command/capability combination; adding a command without an explicit
  authorization classification fails CI.

Database row-level security may provide an additional layer for restricted domains, but it
cannot replace application command authorization. Any schema implementation requires a
linked migration ADR.

## Acceptance Evidence

Acceptance of this ADR requires review of the proposed capability and principal model.
Production enablement requires:

- an authentication threat model covering token theft, fixation, CSRF, key rotation,
  revocation, replay, and identity-provider outage;
- a complete command/read-to-capability matrix with deny-by-default tests;
- object-scope and cross-environment tests preventing identifier-based privilege escalation;
- tests proving UI state cannot bypass server-side authorization;
- real-time handshake, per-message filtering, expiry, revocation, policy-change, reconnect,
  cursor, and restricted-subscription tests;
- tests separating submit, review, stop, resume, lower, raise, reveal, activate, and
  access-management authority;
- operator-presence lease tests for expiry, revocation, role changes, reconnect, duplicate
  consoles, local clock changes, conservative offset/uncertainty mapping, and stale samples;
- idempotency and replay tests over authenticated command envelopes;
- durable-receipt and terminal-outcome tests covering response loss, duplicate forwarding,
  stale/unknown submission recovery generation, wrong/stale composite actor fence, lost-tail
  receipt absence, takeover, lookup/execution authorization expiry/revocation, and
  same-key/different-semantic-intent conflict under ADR-025;
- command-authorization-observation tests proving initial observation/intent/receipt atomicity;
  refreshed append deduplication across crash, duplicate delivery, and commit-response loss;
  immutable prior lineage and no transient credential reconstruction; exact-open admission and
  fresh database-time deadline/terminal append rejection; current observation plus
  policy/revocation-epoch selection; append-versus-execution revision CAS; deterministic
  allow/deny/step-up/unavailable precedence with ambiguity fail-closed; retryable-ineligible
  versus nonretryable-terminal denial; terminal no-reopen; and current receipt disclosure on
  every duplicate, synchronous, polling, and direct-lookup path;
- fault injection for SSO, key discovery, policy store, audit store, and console state-channel
  failure;
- proof that e-stop remains one-click/no-confirmation and local hard stop survives total
  cloud/authentication loss;
- proof that resume and upward mode changes require confirmation and current preconditions;
- audit reconstruction of a synthetic session without tokens, restricted content, or
  viewer-memory leakage;
- runbooks for account compromise, emergency revocation, IdP outage, lost operator presence,
  and break-glass use.

No authentication availability, revocation, or operator-response SLO is claimed until the
numeric target is approved and measured.

## Consequences

- Operator authority becomes explicit, least-privilege, scoped, and reconstructable.
- Role naming can evolve with the organization without changing domain safety semantics.
- Privileged operations depend on server and domain checks rather than console behavior.
- Identity, authorization, presence, and audit implementation complexity is accepted because
  these controls govern live broadcast safety.
- Operator-console and production identity implementation remain blocked until this proposal
  and its OPEN decisions are reviewed.

## Open Decisions

- OD-022: the complete production identity, authorization, presence, separation-of-duty,
  break-glass, and revocation profile.
- Concrete SSO and private-access vendors and supported federation protocol.
- Concrete role names, capability bundles, assignment owners, and environment/talent/session
  scope hierarchy.
- MFA profile, step-up rules, browser session design, token/idle/refresh lifetime, revocation
  propagation, and numeric authentication availability SLOs.
- Operator-presence lease duration, renewal action, qualifying authority, and required
  operator count.
- Separation of duties for manual speech, policy activation, access grants, emergency
  resume, and mode increase.
- Break-glass eligibility, custody, duration, alerting, and retrospective review.
- Workload identity mechanism and stage-host enrollment/revocation design.
- ADR-025 command receipt/outcome, actor ownership, and recovery semantics; exact serialization,
  canonicalization, and API framing remain OD-021 work.
- Whether restricted-data reveal uses just-in-time grants, dual approval, or another
  privileged-access workflow.

## Informative Identity References

These sources inform the human security review without selecting an identity provider, federation
protocol, authenticator assurance level, browser-session design, or token format:

- [RFC 9700: Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/info/rfc9700/)
- [NIST SP 800-63-4: Digital Identity Guidelines](https://www.nist.gov/publications/nist-sp-800-63-4-digital-identity-guidelines)
