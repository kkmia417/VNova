# Personal-Data Breach Response Runbook

Status: Proposed rehearsal-only operational procedure; readiness state: `Drafted`;
non-authorizing and not legal advice

Governing sources:

- [`AGENTS.md`](../../AGENTS.md)
- [`vnova-review-handoff.md`](../../vnova-review-handoff.md)
- [ADR-017: data retention, privacy, and PII](../adr/0017-data-retention-privacy-and-pii.md)
- [ADR-026: opaque audit references for deletable personal data](../adr/0026-opaque-audit-references-for-deletable-personal-data.md)
- [ADR-019: authentication, authorization, and operator roles](../adr/0019-authentication-authorization-and-operator-roles.md)
- [Privacy and retention model](../architecture/privacy-retention-model.md)
- [VNova threat model](../security/threat-model.md), especially TM-12 and TM-13
- [Operational runbook index and common response contract](README.md)
- [Operational readiness review packet](../governance/operational-readiness-review.md)
- [Open decision register](../architecture/open-decisions.md)

This runbook uses "personal-data breach" as a conservative technical response label. It does not
decide whether information is legally personal information or personal data, whether a legally
reportable event occurred, which organization has a controller, processor, entrusting-party, or
entrusted-party role, or which jurisdiction applies.

The actions below describe required semantics, not executable commands, endpoints, contacts,
severity levels, numeric thresholds, reporting deadlines, notification wording, or legal
conclusions. Only the named privacy/legal decision owner may determine notification, reporting,
preservation, disclosure, and data-subject obligations using current law, regulator guidance,
contracts, and incident facts. Technical containment begins without waiting for that legal
determination.

## Purpose And Entry Conditions

Use this runbook when there is a credible suspicion that information about a person was accessed,
disclosed, acquired, altered, lost, destroyed, made unavailable, restored contrary to deletion,
or otherwise handled outside its approved purpose or authority. Entry conditions include:

- unexpected access, export, download, reveal, query, role use, support access, or administrator
  activity involving viewer, operator, talent, workforce, partner, or rights data;
- a misdirected message, attachment, report, object link, archive, screen share, overlay, caption,
  broadcast, notification, or bulk communication;
- public or cross-tenant access caused by configuration, authorization, identity mapping,
  storage, cache, index, replica, or isolation failure;
- secrets, OAuth tokens, session material, identity documents, contracts, raw prompts, candidate
  text, viewer memory, unrestricted messages, or rights evidence appearing in logs, traces,
  metrics, test artifacts, tickets, incident chat, or ordinary audit;
- unauthorized provider processing, logging, model-training use, regional transfer, retention, or
  onward disclosure, including a provider or subprocessor incident report;
- loss, theft, compromise, or uncertain custody of an operator endpoint, streaming PC, local
  journal, removable medium, backup, export, or other local copy;
- ransomware, malicious access, insider misuse, data scraping, credential compromise, or a
  third-party report of possible exposure;
- deletion that leaves an embedding, index, cache, object, provider copy, replica, offline buffer,
  backup, or restored copy available;
- viewer memory and audit data sharing a table, raw content, access role, export, or support
  workflow contrary to ADR-017;
- monitoring, integrity, or custody evidence that is incomplete enough that approved handling
  cannot be proved.

A credible report, control alert, or unexplained evidence gap is enough to start restrictive
containment. Responders must not wait for confirmed exfiltration or a legal classification.
Uncertainty broadens the provisional technical scope; it does not create a legal conclusion.

## Required Human Functions

Assign these functions through the approved incident process without delaying containment:

| Function                     | Responsibility                                                                                                                                                                  |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Incident commander           | Owns coordination, provisional scope, handoffs, decision requests, and exit evidence                                                                                            |
| Privacy/legal decision owner | Solely determines applicable data roles, jurisdictions, preservation and hold treatment, reporting and notification obligations, recipients, timing, and legal closure criteria |
| Security lead                | Contains adversarial access, identities, credentials, endpoints, persistence, and evidence tampering                                                                            |
| Data and service owners      | Map authoritative sources, data classes, purposes, consumers, copies, access paths, retention state, and remediation                                                            |
| Provider and partner owner   | Uses reviewed contractual channels to coordinate providers, subprocessors, platforms, and partners                                                                              |
| Stage operator               | Secures the streaming PC, local journal, media/cache state, active surfaces, and physical custody                                                                               |
| Safety lead                  | Prevents suspected personal data from progressing to autonomous speech or any broadcast surface                                                                                 |
| Evidence custodian           | Controls restricted collection, provenance, access, transfers, holds, retention, and authorized disposal                                                                        |
| Communications lead          | Drafts and delivers only privacy/legal-approved data-subject, regulator, partner, talent, workforce, or public communications                                                   |
| Recorder                     | Maintains a minimized timeline, fact/unknown register, decision log, copy manifest, and action ownership                                                                        |

One person may perform multiple functions only where the accepted separation-of-duty policy
allows it. A technical responder, incident commander, provider representative, or communications
lead cannot substitute for the privacy/legal decision owner. A person or team implicated in the
incident must not approve its own restored access, evidence disposition, notification decision,
or closure where independent review is required.

## Response Principles

- Protect potentially affected people and stop additional exposure before optimizing
  availability, diagnosis, or reputation.
- A safety approval, public-broadcast status, pseudonym, hash, encryption claim, provider
  assurance, or prior consent does not by itself declassify data or prove that handling is lawful.
- Contain the narrowest scope only when authoritative evidence proves both identity and isolation.
  Ambiguous sources, tenants, roles, time intervals, providers, or copies require broader
  containment.
- PostgreSQL remains the cloud system of record. Redis, a replica, browser state, a provider
  dashboard, an object-store listing, or a stage-host journal cannot establish the authoritative
  data or deletion state by itself.
- Viewer memory and ordinary audit remain separate in tables, raw content, and access roles during
  response. An incident does not authorize copying memory into audit, logs, tickets, or chat.
- Preserve the minimum evidence necessary for reconstruction and accountable decisions. Do not
  preserve an entire unrestricted dataset merely because a subset might be relevant.
- A digest supports byte-integrity comparison within trusted provenance; it does not prove
  consent, legal validity, non-identifiability, or safe disclosure.
- Pending ADR-026 review, a content-derived viewer message/memory digest in ordinary audit,
  telemetry, logs, events, receipts, tickets, or incident chat is itself a prohibited exposure,
  not a privacy-safe replacement for the source value.
- Provider, backup, replica, cache, or local-copy uncertainty remains an explicit partial state.
  Silence, timeout, or absence from one interface is not deletion or containment proof.
- Deletion, retention, incident hold, legal hold, correction, disclosure, and evidence disposal
  are privacy/legal decisions executed through approved controls. Responders do not silently
  override an existing deletion case or invent an indefinite hold.
- Restored availability, a fixed configuration, provider reassurance, or incident closure never
  automatically resumes broadcast, raises autonomy, clears an emergency stop, re-enables a data
  flow, or revives deleted content.

## Immediate Response To Credible Suspicion

Perform these semantic actions in order where dependencies allow. Independent containment actions
may run concurrently. Failure of a later action never reverses an earlier restriction.

1. **Stop active exposure.** Disable the affected collection, query, reveal, export, sharing,
   provider disclosure, model input, cache use, index use, download, publication, or public-access
   path at the earliest independently trusted boundary. If personal data may reach speech,
   captions, overlays, scenes, media, or another broadcast surface and isolation is not proved,
   stop affected dispatch and presentation, lower the effective mode, and use the
   [emergency-stop procedure](emergency-stop-and-resume.md) where required.
2. **Declare a restricted incident.** Assign a stable incident ID and record the report source,
   first observed and first received times with timezone and uncertainty, affected environment,
   provisional scope, current exposure state, and assigned functions. Do not put raw affected
   data, credentials, prompts, candidates, memory, contracts, or unrestricted media in the
   ordinary incident record.
3. **Escalate the decision request.** Notify the approved incident, security, privacy/legal, data,
   provider/partner, stage, safety, evidence, and communications functions for the provisional
   scope. Record unsuccessful or indeterminate escalation attempts. This runbook does not define
   destinations or response-time targets.
4. **Set the provisional boundary.** Treat every reachable tenant, environment, talent, viewer,
   workforce population, data class, provider, endpoint, replica, backup, export, and time
   interval as affected until authoritative evidence supports narrowing.
5. **Restrict authority.** Suspend suspect identities, sessions, roles, service credentials,
   signed links, exports, privileged reveals, support access, and administrative changes through
   independently trusted controls. If identity authority is suspect, also invoke the
   [operator identity compromise runbook](operator-identity-compromise.md).
6. **Preserve before changing.** Capture the minimum volatile and durable metadata needed to
   explain the event, then record every containment change. Do not destroy suspect records,
   rotate away the only provenance, wipe a device, purge a provider account, or overwrite a
   backup before the evidence custodian and privacy/legal owner determine treatment.
7. **Contain providers and partners.** Stop new affected requests or transfers. Through approved
   contractual and security channels, request scoped containment, preservation, copy inventory,
   access history, onward-recipient information, region information, and a written outcome.
   Every external action has an explicit timeout; timeout leaves the item unresolved.
8. **Contain local and offline copies.** Secure affected streaming PCs, operator endpoints,
   removable media, downloaded exports, local journals, queues, caches, and offline buffers.
   Preserve physical custody and prevent reconnect, replay, rebuild, sync, or upload from widening
   exposure.
9. **Protect deletion state.** Record active deletion cases, tombstones, approved retention
   transitions, backup expiry, and holds. Disable affected restore, reindex, replay, or repopulation
   paths until they can reconcile that state before making data available.
10. **Maintain explicit unknowns.** Mark unverified access, people, fields, copies, providers,
    regions, and time intervals as unknown. Do not convert "no evidence yet" into "not affected."

If a containment control is unavailable, untrusted, or returns an indeterminate result, keep the
affected capability disabled and expand to the next independently enforceable boundary.

## Provisional Scope And Data-Role Assessment

The technical team prepares a fact package; the privacy/legal decision owner determines the legal
classification and organizational roles. Scope each dataset or processing relationship
separately rather than assuming one role for the whole incident.

Record at least:

- authoritative source IDs, data domains, field categories, declared purposes, owners, permitted
  consumers, access roles, retention policy IDs, deletion behavior, and export/logging rules;
- the earliest and latest plausible exposure, event times, server receipt times, timezone, clock
  uncertainty, and the evidence used to bound the interval;
- unique potentially affected people or records, the counting method, duplicate treatment,
  confidence, and unresolved population; not a threshold-derived legal conclusion;
- whether confidentiality, integrity, availability, purpose limitation, deletion state, or
  evidence custody may have been affected;
- actual accessibility and protection facts, including authentication, authorization, link scope,
  object policy, encryption state, key custody, redaction, tokenization, and whether controls were
  effective at the relevant time;
- every organization that determined a purpose, processed on another's instructions, entrusted or
  received data, supplied infrastructure, or received an onward transfer;
- relevant contracts, data-processing terms, provider profiles, regions, subprocessors,
  platforms, talent/rights relationships, and customer or partner incident clauses;
- data-subject location and processing/storage regions as facts for jurisdiction review;
- any potentially high-impact or specially regulated information for privacy/legal assessment,
  without assigning a legal category in the technical record;
- linked security, safety, rights, deletion, support, or continuity incidents.

Public broadcast content can remain identifying or rights-sensitive and may have been clipped,
mirrored, transcribed, or redistributed beyond VNova's control. Record what was actually exposed
and where; do not label it harmless merely because it reached a public surface.

### Copy And Recipient Manifest

Create a target manifest for every possible authoritative, derived, transferred, local, restored,
or human-created copy. Add a row even when existence is uncertain.

| Copy or recipient class                                                      | Facts to establish                                                                                                             | Containment and terminal evidence                                                                                                         |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| PostgreSQL source and outbox                                                 | Records, versions, tenants, purposes, access history, deletion/tombstone and hold state                                        | Scoped access restriction; preserved transaction/outbox provenance; authoritative repaired or approved terminal state                     |
| Redis transport or cache                                                     | Keys/stream references, consumers, payload class, expiry, replay/repopulation path                                             | Use disabled and cache reconciled from PostgreSQL; Redis never accepted as scope, recovery, or deletion authority                         |
| Derived embeddings, indexes, and application caches                          | Source links, models/versions, rebuild paths, consumers, replicas                                                              | Rebuild/use disabled until source state is valid; source-linked purge or approved treatment plus independent verification                 |
| Object storage, archives, replicas, and signed links                         | Object/version IDs, policies, recipients, replication, access logs, link scope                                                 | Public/shared access closed; every version/replica/link has a recorded disposition and verification                                       |
| Backups, snapshots, and restore environments                                 | Coverage interval, locations, access, expiry, tombstones, deletion cases, restore path                                         | Governed retention/hold disposition; restore rehearsal proves reconciliation before availability; no false immediate-deletion claim       |
| LLM, moderation, TTS, media, analytics, or support provider                  | Request/profile IDs, fields disclosed, region, logging/training/retention terms, subprocessors, access and deletion capability | New transfer stopped; written provider containment, preservation, copy, onward-recipient, and terminal outcome or explicit uncertainty    |
| Platform, customer, processor, subprocessor, or other partner                | Data and purpose transferred, contract role, destinations, onward copies, local exports                                        | Approved coordination record and each recipient's containment/notification/terminal status                                                |
| `stage-host`, streaming PC, and local adapters                               | Journal, queue, cache, temporary files, diagnostics, playback/surface history, connectivity and physical custody               | Rig secured; affected work cannot replay or upload; local copy retained, quarantined, or deleted only under approved disposition          |
| Operator, reviewer, support, and workforce endpoints                         | Downloads, browser caches, screenshots, clipboard, recordings, removable media, forwarded messages                             | Endpoint and account contained; forensic or verified copy disposition under privacy/employment review                                     |
| Logs, traces, metrics, alerts, CI/test artifacts, tickets, and incident chat | Data fields, audiences, retention, exports, mirrors, search indexes, notification copies                                       | Further exposure restricted; evidence preserved before authorized remediation; every secondary copy tracked                               |
| Broadcast, archive, clip, transcript, overlay, and public platform           | Exact surface, session, artifact, audience, availability interval, platform IDs, mirrors                                       | Further VNova-controlled publication blocked; platform/takedown and communication decisions owned; uncontrollable redistribution explicit |

For each manifest row, record an owner, status, last verified time, verification method, evidence
reference, next action, dependency, and uncertainty. "Not found" must name the query scope and
evidence; "contained" and "deleted" require separate accepted proofs. Missing provider
confirmation, backup expiry, local-device custody, or independent absence verification keeps the
row open.

## Containment Confirmation

Containment is partial until authoritative evidence proves, for the provisional scope:

- the original disclosure, access, alteration, loss, destruction, restore, or unavailable-data
  path cannot continue;
- suspect human and workload authority, sessions, links, exports, privileged reveals, provider
  routes, and administrative persistence are disabled or independently trusted;
- affected broadcast surfaces are no longer presenting the data and cannot replay queued or
  cached work;
- every connected local target is reconciled and every disconnected or unverified target is in
  the accepted local safe state;
- providers, subprocessors, partners, platforms, endpoints, exports, caches, replicas, objects,
  backups, and restore paths appear in the copy manifest with confirmed or explicitly unresolved
  status;
- restored, replayed, reindexed, or repopulated data cannot bypass deletion cases or tombstones;
- viewer memory, audit, restricted generation, rights evidence, and secrets remain in their
  approved separate domains and roles;
- ordinary telemetry and incident channels contain only minimized evidence, with any secondary
  evidence leakage contained as part of the incident;
- an independently trusted path remains for security, privacy/legal, evidence, and safety
  response.

If any item cannot be proved, the corresponding restriction and manifest item remain active.
Technical containment does not answer whether reporting or notification is required.

## Evidence Custody And Minimization

Use an access-controlled restricted evidence system approved for the affected data class. The
ordinary incident record contains only what is necessary to coordinate response:

- incident, source-record, event, trace, request, session, principal, policy, role, object,
  provider-profile, artifact, task, rig, copy-manifest, deletion-case, and evidence-record IDs;
- reviewed privacy-preserving references, versions, reason categories, allow/deny outcomes,
  integrity outcomes, state transitions, region categories, and bounded counts;
- original and collection timestamps, timezone, clock uncertainty, collector identity, custody
  status, and decision references.

Ordinary evidence must not contain bearer tokens, signing keys, provider credentials, session
secrets, raw prompts, raw candidates, viewer-memory values, unrestricted viewer messages,
contracts, consent or identity documents, signatures, unrestricted synthesized media, or complete
affected datasets. A screenshot, spreadsheet, attachment, exported query result, crash dump, or
hash is not safe for an ordinary channel merely because it is convenient.

For each restricted evidence item, the evidence custodian records:

- a stable evidence ID, incident and purpose;
- original source and system, collection authority, collector identity, method/tool and version;
- original time, collection time, timezone, clock uncertainty, and acquisition sequence;
- original format, integrity digest where appropriate, classification, encryption/custody state,
  and protected location;
- every access, reveal, copy, transformation, redaction, transfer, receipt, rejection, and
  authorized disclosure;
- retention policy, incident/legal-hold decision, review state, release criteria, and authorized
  disposal outcome.

Preserve original evidence and make analysis copies only when necessary. A transformation must
retain provenance to the original; a corrected interpretation creates a new record rather than
editing history. Restrict privileged reveal by purpose, role, incident, time, and logged reason.
Use independent corroboration where possible; provider assertions and application logs are not
automatically sufficient.

If the restricted evidence system is unavailable, do not redirect raw data to ordinary logs,
tickets, chat, personal storage, or unapproved removable media. Keep the affected processing
disabled, preserve only through the approved bounded contingency, and record the evidence gap.

An existing deletion request, routine retention action, or backup expiry must not be silently
cancelled. The privacy/legal owner decides whether a scoped incident or legal hold applies, and
the evidence custodian records the authority, affected records, review/release conditions, and
conflicts. A hold-blocked deletion remains an explicit incomplete case; evidence preservation does
not authorize retaining unrelated content.

## Investigation And Impact Fact Package

Maintain separate fields for **confirmed fact**, **unconfirmed report**, **reasoned inference**,
and **unknown**. Every material change in scope or confidence records its evidence and decision
owner. Do not remove earlier estimates from the timeline.

Determine at least:

- the initiating event, control failure, actor or failure source, earliest plausible access, and
  whether persistence or repeated exposure remains;
- whether data was viewed, queried, downloaded, copied, altered, destroyed, encrypted,
  transmitted, broadcast, indexed, trained on, logged, restored, or merely reachable, and the
  evidence for each conclusion;
- the exact fields and data domains involved, their declared purposes, source records, affected
  people, tenants, talents, sessions, and environments;
- effective authorization and access at the incident time, including human, workload, provider,
  support, local, break-glass, and inherited access;
- provider and partner processing, regions, subprocessors, retention, logging, model-training,
  support access, onward disclosure, and deletion behavior;
- every cloud, transport, object, derived, replica, backup, export, endpoint, local-rig,
  observability, support, and public copy;
- whether a prior deletion, correction, opt-out, restriction, consent/rights state, contract,
  retention transition, or hold was bypassed;
- whether evidence, access logs, timestamps, object versions, tombstones, alerts, or custody
  records were altered, missing, disabled, or unreliable;
- whether unsafe output, identity compromise, rights misuse, provider compromise, ransomware, or
  supply-chain compromise requires another runbook or a broader security incident;
- what actions may reduce harm to potentially affected people without causing additional
  disclosure.

The privacy/legal decision owner uses this fact package to assess applicable law, jurisdiction,
data roles, impact on people, regulator and contractual requirements, and communication options.
The technical team does not convert field names, record counts, encryption, malicious intent, or
provider location into a legal reporting conclusion.

## Provider, Partner, And Local-Copy Coordination

For every external provider, subprocessor, platform, customer, or partner in scope:

1. verify the intended organization and approved incident contact through a trusted source;
2. disclose only the minimum incident facts needed for that recipient's role;
3. request a stable external case ID and the times, systems, regions, data classes, actors,
   recipients, logs, containment actions, preservation state, copies, subprocessors, and
   uncertainty relevant to VNova;
4. require a written distinction between confirmed containment, pending investigation,
   contract-limited retention, backup expiry, deletion, and inability to verify;
5. record every outbound disclosure and inbound artifact in the copy manifest and evidence
   custody record;
6. apply explicit timeouts and escalation through the approved contract path; do not infer
   success from silence or a closed support ticket.

Do not send the complete affected dataset back to a provider to ask whether it has a copy. A
provider-side deletion request does not become complete until the accepted policy and contract
define the terminal outcome and VNova records the available independent verification.

For local devices and media, preserve physical custody, power/network state decisions, device and
storage identity, assigned custodian, transfers, and tamper evidence. Exact forensic acquisition,
isolation, rebuild, or disposal steps require target-specific security and privacy approval.
Reconnecting a rig or endpoint must not replay, sync, restore, or upload affected content before
copy-manifest and tombstone reconciliation.

## Notification And Communications Decision

Only the assigned privacy/legal decision owner determines whether, when, how, and to whom VNova or
another organization must report or notify. That decision must use the current incident facts,
applicable jurisdiction and organizational role, current regulator guidance, contracts, and
qualified advice. It records the decision owner, decision time, sources/version checked,
recipients considered, rationale, unknowns, required follow-up, and review trigger.

The incident commander ensures the decision is requested and supplied with current facts but does
not make or suppress it. The communications lead prepares and sends only approved content. Exact
deadlines, thresholds, report recipients, forms, channels, named contacts, and legal tests are
OPEN and must be verified at incident time; examples or stale exercises are never production
defaults.

| Possible audience                                                                             | Decision and coordination boundary                                                                                                                                                      |
| --------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Potentially affected people or data subjects                                                  | Privacy/legal approves whether direct notification or another lawful measure applies, audience identity, content, channel, accessibility, support, and update plan                      |
| Japan Personal Information Protection Commission, another regulator, or a delegated authority | Privacy/legal confirms applicability, organizational role, current recipient, form, timing, content, and follow-up from current official sources                                        |
| Customer, controller, entrusting party, processor, subprocessor, provider, or platform        | Privacy/legal and contract owner determine role-specific notice, facts, preservation, cooperation, onward notification, and responsibility; technical teams do not infer the legal role |
| Talent, workforce, rights owner, insurer, law enforcement, or other partner                   | Accountable legal, security, rights, employment, contract, and communications owners determine necessity, authority, scope, and channel                                                 |
| Audience, press, or public                                                                    | Privacy/legal and communications owners decide whether and how to publish verified facts, protective guidance, and remediation without widening exposure or prejudicing response        |

Approved communications should:

- distinguish verified facts, current estimates, unknowns, and corrections;
- use consistent incident and version identifiers across recipients while tailoring disclosed data
  to each recipient's need and authority;
- avoid identifying one affected person to another, exposing recipient lists, embedding raw
  records, sending unsafe links, or disclosing exploitable security detail;
- explain available protective steps and an approved contact path where appropriate;
- be understandable and accessible to the intended recipient, with translation and support
  reviewed for the actual population;
- preserve every sent version, recipient class, dispatch outcome, correction, and follow-up as
  restricted evidence without copying the entire message into ordinary audit;
- never claim "no impact," "fully contained," "deleted everywhere," or "no notification required"
  beyond the evidence and accountable decision.

If a message is misdirected, exposes recipients, contains excessive data, or conflicts materially
with the approved facts, stop further delivery and treat it as a new or widened exposure.

## Failure Variants

| Failure during response                                                     | Required posture                                                                                                                                                                               |
| --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Authoritative source, inventory, or access logs unavailable                 | Keep the broader provisional scope and affected processing disabled; preserve the gap and use independent evidence without treating a cache as authority                                       |
| Provider, partner, or subprocessor does not respond or cannot verify copies | Mark the manifest item unresolved, stop new disclosure, escalate through the approved contractual path, and do not claim containment or deletion                                               |
| Audit or restricted evidence store unavailable                              | Restrictive action proceeds where independently safe; privileged reveal, restore, re-enable, and evidence-dependent closure remain blocked; raw evidence never moves to ordinary logs          |
| Stage host or endpoint unreachable                                          | Block cloud progression and sync; use the accepted local safety/custody path; incident remains partially contained until local state and copies are proved                                     |
| Identity or administrator compromise suspected                              | Deny affected access and invoke the operator identity or wider security response; the suspect authority cannot approve evidence, notification, recovery, or closure                            |
| Ransomware or destructive alteration suspected                              | Isolate affected processing, preserve evidence and known-good sources, treat exfiltration and availability as separate unknowns, and prohibit restore before tombstone/deletion reconciliation |
| Deletion request, routine expiry, or hold conflicts with preservation       | Do not delete or retain by convenience; privacy/legal records the scoped decision, affected cases, review/release conditions, and incomplete states                                            |
| Data role, jurisdiction, regulator, recipient, or contract is disputed      | Maintain protective technical containment and escalate to the privacy/legal decision owner; responders do not choose the most convenient interpretation                                        |
| Notification decision owner or approved channel unavailable                 | Use the pre-approved escalation and continuity path under OD-030; do not let technical staff invent a deadline, recipient, legal conclusion, or public statement                               |
| Communication itself causes exposure or misinformation                      | Stop further distribution, preserve the sent version and recipient facts, correct only through approved review, and widen the incident scope                                                   |
| Backup restore, reindex, replay, or cache rebuild starts prematurely        | Keep restored data unavailable, stop dependent consumers, reconcile source/deletion/hold state, and independently verify before any release                                                    |

## Eradication, Recovery, And Re-Enablement

Recovery requires a new, independently reviewed path:

1. remove the initiating access, configuration, code, workflow, provider, identity, endpoint, or
   human-process cause and all persistence within the confirmed scope;
2. restore least-privilege access, tenant and role isolation, reviewed provider profiles, safe
   export/reveal paths, and data-domain separation from known, approved configurations;
3. reconcile PostgreSQL source records, outbox state, deletion cases, tombstones, holds, object
   versions, derived records, caches, replicas, backups, providers, partners, endpoints, and local
   rigs before making data available;
4. restore from a known-good backup only after proving that restoration cannot revive deleted,
   superseded, restricted, unauthorized, or incident-contained content;
5. obtain written terminal or explicitly unresolved outcomes for every provider, subprocessor,
   partner, platform, endpoint, export, and local copy in the manifest;
6. independently test absence, access denial, non-repopulation, and non-replay across every
   affected consumer; a source-row fix alone is insufficient;
7. scan ordinary logs, traces, alerts, test artifacts, tickets, and incident channels for
   prohibited evidence and remediate through the approved custody process;
8. validate that viewer memory and audit still use separate tables, content, access roles,
   retention, deletion, and export paths;
9. apply the privacy/legal-approved communication, data-subject support, regulator, contract,
   evidence, hold, and retention actions;
10. run deterministic rehearsal and target checks against the exact repaired configuration and
    record remaining uncertainty and residual risk;
11. obtain independent security, privacy/legal, data-owner, provider/partner, stage, safety, and
    communications review for the affected capability and deployment;
12. re-enable only the reviewed data paths and least-authority scope. Any broadcast resume, mode
    increase, emergency-stop clearance, provider activation, privileged reveal, restore release,
    or deletion completion remains a separate authorized action.

Recovery does not require destroying valid evidence or retaining unrelated affected data. The
privacy/legal and evidence owners decide the accepted balance through the approved, recorded
policy.

## Exit Criteria

The incident may leave active response only when:

- the initiating exposure and persistence are removed or the affected capability remains disabled
  under an approved containment owner;
- the scope fact package identifies every data class, purpose, person/record population,
  environment, time interval, organization, region, access path, and uncertainty material to the
  response;
- every cloud, provider, partner, platform, cache, replica, object, backup, export, endpoint,
  observability, support, public, and stage-host copy has a confirmed or explicitly unresolved
  manifest disposition and accountable follow-up;
- viewer memory, audit, restricted generation, rights evidence, and secrets are verified separate
  under ADR-017, including incident artifacts and support workflows;
- evidence is minimized, provenance-preserving, access-controlled, and governed by recorded
  retention, deletion, disclosure, and hold decisions;
- the privacy/legal decision owner has recorded the applicable data-role, jurisdiction,
  notification, regulator, partner, affected-person, preservation, and communication decisions;
- every required communication and support action is complete, or remains in a formally tracked
  legal/contractual process that does not permit incident closure to imply completion;
- remediation, independent verification, monitoring, rehearsal findings, and remaining risks
  have named owners and review triggers;
- restored data cannot bypass tombstones or incomplete deletion cases, and no provider, backup,
  or local uncertainty is represented as successful deletion;
- any production re-enable, broadcast resume, mode increase, or risk acceptance has separate
  protected authorization for the exact deployment.

Closing a technical incident record does not determine legal compliance, complete a regulator or
data-subject obligation, release evidence, end a hold, certify universal deletion, accept
residual risk, or authorize resumed processing.

## Required Rehearsal Tests

Use synthetic, non-production records and privacy-reviewed canaries. Rehearse at least:

- a misdirected export, email, support attachment, bulk recipient list, signed object link, and
  public storage configuration;
- raw viewer memory, prompt, candidate, contract, credential, or identity data appearing in
  ordinary audit, traces, crash dumps, tickets, CI artifacts, and incident chat;
- viewer memory and audit accidentally sharing a table, role, export, or support query, with
  separation restored without losing minimized decision evidence;
- unauthorized provider logging, model-training use, regional transfer, subprocessor access,
  retention, and a provider that cannot confirm deletion or containment;
- a stolen operator endpoint, streaming PC, local journal, removable medium, download, screenshot,
  clipboard, and disconnected rig that later reconnects;
- malicious operator access, compromised administrator, cross-tenant query, public overlay or
  caption, platform clip, and uncontrollable public redistribution;
- ransomware, destructive modification, missing logs, disputed exfiltration, and restore from a
  backup containing active tombstones or incomplete deletion cases;
- Redis loss or stale payload, cache repopulation, reindexing, replica lag, offline-observation
  ingest, domain-event replay, and object-version restoration without treating a derived system
  as authoritative;
- a complete copy manifest covering PostgreSQL, outbox, Redis, objects, providers, partners,
  caches, replicas, backups, endpoints, stage host, support systems, and public surfaces;
- evidence collection, restricted reveal, chain-of-custody transfer, evidence-store outage,
  scoped hold, deletion/hold conflict, authorized redaction, and disposal without secondary
  leakage;
- data-role, jurisdiction, regulator, contract, and notification ambiguity escalated to the
  privacy/legal owner without a technical legal conclusion;
- affected-person, regulator, customer/controller, provider/processor, partner, talent, workforce,
  and public communication drafting, approval, correction, accessibility, translation, and
  misdelivery response;
- a current-guidance verification drill that detects stale recipient, form, channel, threshold,
  or timing assumptions before any communication is authorized;
- recovery proving deleted content, old exports, cached records, provider copies, and local work
  do not revive, and that unknown copies remain visibly incomplete.

Each rehearsal records repository and runbook version, scenario, roles, synthetic data classes,
target identity, assumptions, injected failures, sanitized timeline, expected containment,
observed outcome, copy manifest, evidence custody, notification decision exercise, findings,
owners, and invalidation triggers. A tabletop or simulator cannot establish target-specific
endpoint, provider, stage-host, backup, communication, or legal readiness.

## OPEN Human Decisions And Readiness

The following remain unresolved and cannot be inferred from this document:

- OD-002: provider independence and each provider's privacy/security profile, regions, logging,
  model-training use, retention, subprocessors, evidence, containment, and deletion capability;
- OD-009: retention periods, deletion and verification SLOs, backup/restore behavior, incident and
  legal-hold authority, scope, review, release, and evidence retained after deletion;
- OD-022: SSO, session, capability, privileged-reveal, revocation, presence, separation-of-duty,
  and break-glass profiles;
- OD-027: incident classes and severity, command authority, roster and coverage, handoffs,
  escalation, resilient communications, exercises, evidence freshness, runbook ownership, and
  deployment authorization;
- OD-028: adversary and trust assumptions, independent assessment, review triggers, residual-risk
  taxonomy, and accountable risk-acceptance authority;
- [OD-030](../architecture/open-decisions.md): applicable jurisdictions and organizational data
  roles; incident assessment; evidence custody; notification and communication decision authority;
  target-specific deadlines, thresholds, forms, recipients, channels, and contacts;
  provider/processor and partner coordination; affected-person support; and closure evidence;
- the deployment-specific alert sources, containment commands, provider and local forensic
  procedures, evidence store, custody roster, contract inventory, current regulator resources,
  approved templates, translations, accessibility, support path, and independent verification
  evidence.

The current state is `Drafted` only. Advancing to `Rehearsed`, `Target-validated`, or
`Production-authorized` requires the evidence and protected human review defined by the
[operational readiness review packet](../governance/operational-readiness-review.md). A merge,
document age, completed tabletop, generic test, provider assurance, or legal-information link
does not advance readiness by itself.

## Informative Official References

At incident time, the privacy/legal decision owner must check the current versions and any
applicable sector or delegated-authority material. These references are review inputs, not VNova
policy, notification authorization, or legal advice:

- Japan Personal Information Protection Commission:
  [current personal-data leakage response and reporting resources](https://www.ppc.go.jp/personalinfo/legal/leakAction/)
- Japan Personal Information Protection Commission:
  [Guidelines on the Act on the Protection of Personal Information, General Rules](https://www.ppc.go.jp/personalinfo/legal/guidelines_tsusoku/)

Current PPC guidance describes internal escalation and prevention of further harm, fact and cause
investigation, scope identification, recurrence prevention, and privacy/legal assessment of
regulator reporting and notification to affected people. The official response page also warns
that the reporting destination can depend on delegated sector authority and should be verified
from current information before reporting. This runbook intentionally does not reproduce any
deadline, threshold, recipient, form, or legal test.
