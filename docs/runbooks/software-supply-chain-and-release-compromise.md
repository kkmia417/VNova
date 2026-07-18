# Software Supply-Chain And Release Compromise

Status: Proposed rehearsal-only operational procedure; readiness state: `Drafted`;
non-authorizing

Governing sources:

- [`AGENTS.md`](../../AGENTS.md)
- [VNova threat model, TM-17](../security/threat-model.md#tm-17-supply-chain-build-and-update-compromise)
- [ADR-001: monorepo and deployment boundaries](../adr/0001-monorepo-and-deployment-boundaries.md)
- [ADR-002: contract source and code generation](../adr/0002-contract-source-and-code-generation.md)
- [ADR-007: provider gateway and fallback isolation](../adr/0007-provider-gateway-and-fallback-isolation.md)
- [ADR-008: safety gate enforcement](../adr/0008-safety-gate-enforcement.md)
- [ADR-011: stage-host wire protocol and clock synchronization](../adr/0011-stage-host-wire-protocol-and-clock-synchronization.md)
- [ADR-016: required local stage-host topology](../adr/0016-stage-host-and-cloud-local-topology.md)
- [CI quality gates and repository rules](../governance/ci-quality-gates.md)
- [Toolchain baseline](../architecture/toolchain.md)
- [Production quality attributes](../architecture/production-quality-attributes.md)
- [Production implementation roadmap](../architecture/implementation-roadmap.md)
- [Operational readiness review](../governance/operational-readiness-review.md)
- [Open decision register](../architecture/open-decisions.md)
- [Personal-data breach response](personal-data-breach-response.md)

This runbook defines required containment, investigation, recovery, and evidence semantics. It
does not select a registry, CI service, builder, signing algorithm, key custodian, provenance
format, scanner, updater, update channel, deployment system, incident command, or executable
command. It does not grant repository, signing, deployment, workload, stage-host, or release
authority. Exact procedures remain protected human decisions under OD-012, OD-019, OD-027,
OD-028, and OD-031.

The current repository contains a local Phase 1 CI and package-artifact evidence baseline. Remote
CI execution, repository Ruleset enforcement, independent ownership, production signing,
deployment provenance, and stage-host/update packaging do not yet exist as accepted evidence.
The current artifact verifier covers the package archives it explicitly knows; it is not evidence
for a future container image, stage-host installer, live adapter bundle, updater, or deployment.

## Purpose And Entry Conditions

Use this runbook when the source-to-target release chain is or may be untrustworthy, including:

- an unexpected source, dependency, lockfile, generated file, build input, package member, or
  artifact appears;
- a deterministic generator, clean build, archive allowlist, manifest digest, metadata, version,
  reproducibility, or isolated-install check fails;
- a repository branch, tag, protected path, approval, CODEOWNERS rule, required check, workflow,
  pinned CI dependency, permission, or audit trail is missing, changed, or bypassed;
- a maintainer, repository administrator, CI runner, build identity, release identity, signing
  authority, workload identity, registry credential, or update credential may be compromised;
- a dependency source, package registry, cache, mirror, build output, release store, update
  channel, installer, container, provider SDK, or live adapter may have been substituted;
- release metadata, provenance, signature, digest, source commit, builder identity, or target
  version conflicts or cannot be verified;
- a deployed workload, streaming PC, stage-host, OBS/VTube Studio adapter, updater, or other
  target reports an unexpected or unknown version;
- a security advisory, incident, or independent finding makes the reviewed dependency/build
  assumptions invalid; or
- functional tests pass but the reviewed source-to-artifact-to-target lineage is absent or
  contradictory.

A credible report or verification failure is sufficient to enter the runbook. Responders do not
wait for proof of malicious intent before halting promotion. A routine dependency outage without
integrity concern may use ordinary release operations, but uncertainty about integrity,
provenance, or authority remains a supply-chain incident.

## Safety And Release Objective

The immediate release decision is `HOLD` for the affected and potentially affected scope.

- No suspect source, dependency, generated output, package, installer, image, signature,
  release metadata, update, or cached copy is promoted, deployed, installed, restored, or
  reused.
- A green functional test does not compensate for failed provenance, ownership, artifact,
  generator, or repository evidence.
- Existing production output is restricted or stopped when the deployed target cannot prove a
  trusted version and the affected capability can reach a broadcast surface or safety control.
- Containment does not weaken the local hard e-stop, fail-closed behavior, identifier-only media
  boundary, or exclusive approval mint boundary.
- The incident scope starts at the earliest plausible compromised trust boundary and narrows only
  through independent evidence.
- Recovery uses a reviewed source checkpoint, recovered identities, clean trusted builders,
  deterministic regeneration, deep artifact verification, and target-specific validation.
- Rollback uses only independently proven trusted artifacts and compatible state. "Older" does
  not mean "trusted."
- Every call to a repository, CI system, dependency source, registry, signer, release service,
  deployment plane, updater, target, provider, or evidence service has an explicit operation
  timeout, an explicit outer deadline, and bounded retry/cancellation behavior.
- A timed-out, cancelled, disconnected, partial, or late external result is `unknown`; it cannot
  clear quarantine, narrow incident scope, prove containment, satisfy provenance, or release the
  `HOLD`. Reconciliation against current authoritative state is required before any late result
  is considered.
- Re-enablement is a deliberate, deployment-scoped human decision. Restored CI, a rotated key,
  a new build, or an updater reconnect never resumes promotion automatically.

## Protected Release Chain

The production authorization must eventually bind this complete chain:

```text
reviewed source identity
  -> protected change and independent approval evidence
  -> canonical specifications, generators, and locked dependency closure
  -> identified clean builder and immutable build recipe
  -> deterministic generated outputs and package artifacts
  -> deep artifact inspection and target-specific tests
  -> source-to-artifact provenance and release authorization
  -> approved signing and distribution/update metadata
  -> immutable registry or release object identity
  -> verified deployment/update transaction
  -> observed target identity, version, digest, and health
```

A valid element cannot infer a missing element. A signature proves only what the accepted
signature profile and key custody establish; it does not prove source review, safe behavior, legal
authority, or an uncompromised signer. A matching digest proves byte identity, not trustworthy
provenance. A tag, release name, package version, target label, dashboard status, or registry path
is not sufficient identity by itself.

## Required Human Functions

OD-027 must map these function labels to accountable people, coverage, capabilities, escalation,
and resilient communication. OD-012 and OD-028 must define independent review and risk authority.

| Function                           | Responsibility                                                                                                                                          |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Incident commander                 | Owns scope, phase transitions, handoffs, decision log, and the continued `HOLD` decision.                                                               |
| Security/supply-chain lead         | Owns the compromise hypothesis, credential/key exposure assessment, adversarial evidence, and quarantine boundaries.                                    |
| Repository administrator           | Protects repository access, refs, rules, approvals, integrations, and audit evidence without rewriting suspect history.                                 |
| Release owner                      | Stops promotion/deployment/update activity, inventories release candidates and targets, and owns rollback or disable coordination.                      |
| Build and provenance owner         | Reconstructs source, recipe, dependency, generator, builder, artifact, and attestation lineage using trusted infrastructure.                            |
| Package/dependency owner           | Assesses direct/transitive dependencies, locks, registries, mirrors, caches, advisories, and allowed source provenance.                                 |
| Protected-boundary owner           | Reviews effects on safety, contracts, CI, provider gateways, policies, migrations, stage-host commands, and live adapters within the person's scope.    |
| Stage-host/live-adapter owner      | Contains installer/update exposure, proves target version and adapter integrity, and preserves the independent local stop path.                         |
| Workload/deployment owner          | Contains cloud workload identities and deployment targets and proves the exact artifact running on each affected target.                                |
| Privacy/legal/communications owner | Determines preservation, disclosure, contractual, regulatory, talent, platform, and external communication duties.                                      |
| Evidence recorder                  | Maintains a sanitized timeline and artifact/target inventory without exposing credentials, signing material, restricted content, or malicious payload.  |
| Re-enable authority                | Performs the protected deployment-scoped decision after independent evidence review; cannot be the sole validator of the person's own compromised path. |

No potentially compromised principal, workflow, builder, signer, registry, updater, or target can
attest to its own recovery without independent corroboration. One person may fill multiple
functions only where the accepted separation-of-duties policy permits it.

## Immediate Containment

Contain first; do not begin by rebuilding or deleting evidence.

1. **Halt promotion.** Stop approvals, merges, tags, builds, publication, deployment, rollout,
   automatic update, and release-channel advancement for the affected scope using the approved
   controls. Prevent queued jobs from producing promotable evidence.
2. **Declare the incident through a trusted path.** Use the accepted resilient incident channel
   that is outside the suspected trust boundary. Do not use a compromised repository, CI log,
   release comment, or updater as the only coordination record.
3. **Preserve evidence.** Snapshot immutable references and access-controlled logs for source
   refs, approvals, workflows, builders, dependencies, generated outputs, artifacts, signatures,
   release metadata, registry objects, deployment transactions, update attempts, and targets.
   Preserve suspect bytes without executing, importing, rendering, installing, or republishing
   them.
4. **Quarantine artifacts and dependencies.** Make suspect release candidates, packages,
   installers, images, adapters, caches, mirrors, and dependency versions ineligible for
   promotion or reuse. Quarantine is an authorization state, not a filename suffix or mutable
   label.
5. **Contain authority.** Through separately approved security procedures, suspend or replace
   suspect repository, CI, builder, release, registry, signing, workload, deployment, and update
   credentials. Do not rotate away the only evidence before custody is established.
6. **Block target expansion.** Stop further deployment, automatic restart onto suspect artifacts,
   updater polling/application, cache warming, and replication from suspect sources.
7. **Protect current broadcasts.** If a running workload, stage-host, or live adapter may be
   compromised, hold new autonomous output, move the affected capability toward its accepted safe
   state, and use the relevant fail-closed, rig, or emergency runbook. Do not depend on the
   suspected updater or cloud path to preserve the local hard stop.
8. **Inventory the blast radius.** Begin with every source, build, artifact, credential, channel,
   and target that shares the earliest plausible compromised boundary.
9. **Record the `HOLD`.** Correlate the decision to the incident, release candidates, commits,
   artifacts, signing identities, update channels, deployments, targets, and time interval.

Deletion, force-push, tag replacement, cache purge, credential revocation, or target reimage can
destroy evidence or widen outage impact. Their exact ordering requires the approved
platform-specific response procedure; this runbook does not invent it.

## Quarantine Matrix

| Suspected boundary                  | Minimum quarantine posture                                                                                                                                          |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Source repository or maintainer     | Halt protected changes and releases; preserve refs and audit; distrust commits, tags, approvals, and automation after the earliest plausible compromise.            |
| CI workflow, runner, or integration | Treat its logs and success results as untrusted evidence; halt promotion from its outputs; contain its tokens and downstream credentials.                           |
| Dependency, registry, mirror, cache | Pin the affected resolution as ineligible; preserve lock and retrieval evidence; quarantine every artifact derived from the uncertain dependency closure.           |
| Generator or canonical source       | Quarantine generated outputs and downstream packages; compare from a trusted canonical source and reviewed generator rather than editing generated files manually.  |
| Artifact verifier or test tooling   | Treat artifacts previously cleared only by the suspect verifier as unverified; independently review and rebuild the verifier before trusting its result.            |
| Package, image, installer, adapter  | Quarantine the exact digest and every ambiguous alias or mutable reference; identify all promotions, downloads, caches, and targets that may contain it.            |
| Signing or release authority        | Halt signatures and publication; treat signatures in the exposure window as insufficient; preserve key IDs and signed metadata without disclosing private material. |
| Deployment/workload identity        | Block new mutations from the principal; inventory every environment and target it could alter; distrust self-reported version state without corroboration.          |
| Stage-host updater or channel       | Stop automatic updates and channel advancement; retain local stop capability; identify downloaded, staged, installed, and rollback candidates on every rig.         |
| Target host or live adapter         | Mark the target unsafe for affected output until actual binary/configuration identity and integrity are independently re-established.                               |

Quarantine never changes a rejected or unknown artifact into an approved fallback. If there is no
trusted artifact for continued operation, disable the affected capability or remain safely
stopped.

## Affected Scope And Target Inventory

Build the scope from independent records. Compromised-system telemetry may contribute evidence,
but it cannot be the sole source.

Include:

- source repositories, forks, branches, tags, commits, protected-path changes, approvals, bots,
  applications, and administrative changes;
- canonical schemas, generators, lockfiles, package manifests, build scripts, workflow files,
  reusable actions, runner images, and build dependencies;
- all clean and incremental builds after the last independently trusted checkpoint;
- archive digests, manifests, signatures, provenance records, package versions, mutable aliases,
  registry objects, mirrors, caches, and downloaded copies;
- environment, workload, service, task, container, machine, rig, stage-host boot, installer,
  updater, live-adapter, OBS scene/configuration, and reported version identities;
- credentials and authorities able to change source, build, release, distribution, deployment,
  target configuration, or evidence;
- downstream consumers, export/archive paths, offline installers, disaster-recovery material, and
  rollback candidates; and
- the earliest and latest plausible exposure times with the uncertainty retained.

Scope narrows only when evidence proves isolation. Shared signer, builder, dependency closure,
registry namespace, update channel, workload identity, or mutable alias expands scope. An unknown
target version or missing target is not assumed safe. A target that was offline during the
incident may still hold a downloaded or staged update and remains in scope until reconciled.

## Diagnosis

Diagnosis occurs while promotion remains halted.

### Repository And Change Authority

Verify independently:

- repository identity, default branch, relevant refs, commit ancestry, tag objects, and source
  content digests;
- protected-path changes, human approvals, approval invalidation, conversation resolution, and
  administrative events;
- CODEOWNERS coverage and whether the repository Ruleset actually required its review;
- maintainers, teams, bots, applications, deploy keys, tokens, workload identities, and
  permission changes;
- workflow triggers, permissions, secret exposure, runner selection, timeouts, action references,
  checkout credential persistence, and untrusted-code execution behavior; and
- whether the stable required check was remote, current, bound to the reviewed commit, and
  impossible for the suspect principal to satisfy alone.

The current bootstrap CODEOWNERS individual cannot provide independent review. A CODEOWNERS file
without an enforced Ruleset is not a control claim. Local checks and a mergeable pull request are
not proof that remote required checks ran on the exact promoted source.

### Dependency And Lock Integrity

Verify:

- direct and transitive resolution against the reviewed lockfile and package metadata;
- source registry or repository identity, immutable object/digest evidence where supported by the
  approved profile, and retrieval time;
- unexpected version, package name, owner, archive member, install script, binary, platform
  variant, or dependency graph changes;
- caches, mirrors, vendored copies, local build backends, package-manager/runtime versions, and
  network fallback behavior;
- advisory, malware, provenance, license, and maintenance evidence required by the approved
  dependency policy; and
- every artifact built from the affected dependency closure.

Preserve the original lock and retrieval evidence before any regeneration. A newly resolved lock,
successful install, or version downgrade is not proof that the prior or replacement dependency is
trusted.

### Canonical Source, Generator, And Build

Verify:

- canonical hand-authored source, generator source/version, generated-output manifest, lockfiles,
  build recipe, tool versions, and builder identity;
- that generated files were regenerated rather than manually altered;
- clean-state behavior, stale output removal, network isolation or approved dependency retrieval,
  environment inputs, locale/time effects, and hidden cache/workspace inputs;
- repeat-build byte identity under the accepted reproducibility profile; and
- any difference between reviewed source, generated source, packaged source, and deployed
  artifact.

For the current package scope, the repository artifact verifier is intended to build twice and
check exact archive-member allowlists, safe member paths, duplicate/link/cache rejection,
metadata and version parity, wheel `RECORD` digests/sizes, contract source and per-artifact
manifest digests, repeated archive SHA-256 identity, and isolated offline import smoke tests.
Review the verifier itself and its transitive build environment before treating a pass as trusted.
Its present scope does not cover future stage-host, live-adapter, container, infrastructure, or
updater artifacts.

### Artifact, Signing, And Distribution

Verify:

- artifact byte digest and immutable registry/release object identity;
- source commit, canonical input, dependency closure, generator, builder, build recipe, test set,
  verifier, and approval evidence bound by the accepted provenance profile;
- signature and release-metadata validity under the approved key, scope, time, rotation,
  revocation, and compromise policy;
- publication identity, destination, channel, mutable aliases, replication, mirrors, caches,
  downloads, and post-publication mutation;
- whether a compromised signer, publisher, registry, or update authority could substitute
  metadata or an artifact without another independent control detecting it; and
- every derivative package, image, installer, adapter bundle, export, and rollback artifact.

Do not treat a newly valid signature over suspect bytes as remediation. Exact signing algorithm,
attestation format, key custody, registry semantics, and evidence service remain OPEN.

### Deployment, Workload, And Target

Verify:

- deployment authorization, original human provenance, workload identity, immutable artifact
  reference, environment, timestamp, and result;
- actual target binary/package/image digest, configuration identity, software version, boot or
  process identity, and health;
- differences between deployment-controller state and target-local observation;
- restart, rollback, cache, sidecar/plugin, runtime download, and configuration paths that can
  change behavior after initial deployment;
- stage-host installer/updater identity, channel, staged/downloaded/installed versions, local
  cache, rollback slot, adapter/plugin versions, and OBS/VTube Studio integration state; and
- whether the target can still enforce local e-stop and fail-closed containment without relying
  on the suspected cloud/update path.

An observed expected version string is not enough. The accepted target profile must bind version,
digest, provenance, configuration, and deployment/update evidence.

## Root-Cause And Scope Decisions

Before recovery, the incident commander records:

- the earliest compromised or unprovable boundary;
- affected identities, source range, dependency closure, builds, artifacts, channels, and
  targets;
- whether malicious code executed and what credentials/data/authorities it could reach;
- which evidence is independent and which came only from a suspect system;
- the containment and credential/key recovery status;
- whether an accepted trusted source checkpoint and rollback artifact exist;
- residual unknowns and the safety posture they require; and
- privacy, legal, contractual, talent, platform, and external-notification decisions assigned to
  accountable humans.

Unknown root cause may permit a safe halted handoff but does not permit a trusted rebuild or
production re-enable unless the remaining uncertainty is outside the recovered chain and is
bounded by an OD-028-approved residual-risk decision. Risk acceptance cannot waive an
`AGENTS.md` invariant, Accepted ADR, required repository/feature gate, legal or rights authority,
provenance evidence, or target validation.

## Trusted Rebuild

Rebuild is a recovery operation, not ordinary CI retry.

### Entry Preconditions

- Promotion and affected updates remain halted.
- Suspect bytes and logs are preserved under controlled evidence custody.
- Repository, build, signing, release, deployment, and update identities needed for recovery are
  independently trusted or replaced.
- Repository Ruleset and protected ownership evidence is restored; OD-012 and OD-019 are closed
  for the scope whose evidence will be trusted.
- The source checkpoint or remediated source is independently reviewed, and no suspect mutable
  ref is used as authority.
- Canonical inputs, dependency locks, generators, build recipe, verifier, and expected artifact
  inventory are reviewed.
- Clean trusted builders are available outside the compromised boundary.
- The OD-031 release-integrity profile, including its required signing, provenance, distribution,
  update, and target-verification gates, is approved for this release scope and available.
- Rollback/disable and target-validation plans exist before anything is published.

### Rebuild Sequence

1. Materialize the exact reviewed source by immutable identity in an isolated clean workspace.
2. Reconstruct the approved dependency closure from reviewed locks and allowed sources. Reject any
   silent resolution, fallback, mutable substitution, or unexplained cache hit.
3. Regenerate all derived contracts and artifacts from canonical sources with the reviewed
   generator/toolchain. Reject drift, unexpected files, or manual generated-file differences.
4. Build the complete release set in clean builders under the accepted reproducibility profile.
   Repeated builds must produce the expected artifact set and byte identities.
5. Run the applicable type, lint, contract, boundary, safety, red-team, integration, package,
   install, security, compatibility, and target-specific gates against the exact source and
   artifacts.
6. Inspect each artifact independently. Apply exact member allowlists, traversal/link/duplicate
   rejection, metadata/version checks, manifest/provenance digests, executable-content policy,
   offline smoke installation where applicable, and malicious-content analysis required by the
   accepted profile.
7. Create source-to-artifact provenance and release metadata using recovered authority. Bind the
   immutable source, locks, generators, builders, tests, verifier, artifacts, review decision,
   and destination.
8. Publish only into the approved quarantine or candidate boundary. Do not place the rebuild
   directly into a production or automatic update channel.
9. Validate rollback/disable, deployment/update verification, telemetry, and target inventory in
   rehearsal and then on the required target.
10. Obtain independent security, repository, protected-boundary, release, and operational review
    of the complete chain.

A rebuild that uses the same unreviewed compromise domain as the suspect build is not trusted
merely because it is clean. Exact builder independence, reproducibility, and provenance evidence
requirements remain OPEN under OD-028 and OD-031.

## Rollback Or Disable

Rollback is allowed only when the candidate:

- has independently verified source-to-artifact provenance predating or outside the compromise;
- was built, signed, distributed, and retained under a still-trusted chain;
- is compatible with current data, contracts, configuration, policy, rights, and target state;
- cannot revive an expired authorization, deleted data, revoked right, vulnerable dependency, old
  session epoch, or unsafe policy;
- passes the required target-specific verification; and
- has an explicit rollback owner and observation plan.

Do not roll back by mutable tag, package name, channel label, local cache position, or version
number alone. Do not assume a pre-incident artifact is trusted when the compromised key, builder,
dependency, registry, or updater predates the observed incident.

If no trusted compatible rollback exists:

- keep promotion halted;
- disable the affected capability or target through the accepted safe control;
- maintain Mode 0, fail-closed output, local watchdog, local hard stop, or reviewed neutral scene
  as applicable;
- use only separately authorized unaffected capabilities whose isolation is proved; and
- wait for the trusted rebuild and target validation rather than accepting unknown provenance.

For stage-host and live adapters, a rollback or disable must preserve the direct local stop path.
It must not require the suspect updater to prove its own success, and it must not automatically
replay queued or in-doubt work after restart.

## Deliberate Re-Enable

Re-enable is separate from containment, credential rotation, rebuild, publication, rollback, and
target health.

All of the following are required:

- the compromise path and affected scope are sufficiently understood for the accepted risk
  taxonomy;
- every blocking finding is closed; only non-blocking residual risk may be accepted under
  OD-028, and never in place of a required gate or invariant;
- suspect repository, CI, builder, release, signing, registry, workload, deployment, and update
  authority is contained and recovered;
- OD-012 independent ownership and OD-019 remote CI/Ruleset/runtime-gate authority are resolved
  for the evidence being trusted;
- the OD-031 release-integrity profile is resolved for the capability and target scope, and every
  blocking gate in that profile passes;
- the remediated source, locks, generators, builders, verifier, artifacts, provenance, release
  metadata, signatures, destinations, and target identities form one independently reviewed
  chain;
- required remote checks and protected reviews passed on the exact source and artifact set;
- rollback or continued-safe disable behavior passed;
- every affected workload and rig is reconciled to a known artifact/configuration identity;
- stage-host installer/updater and live-adapter integrity, local stop independence, simulator
  parity, and target-rig behavior passed their protected reviews;
- alerts, target inventory, release telemetry, incident handoff, and rollback owner are active;
- the applicable runbook reaches `Target-validated` on the required targets; and
- a human with deployment-scoped re-enable authority explicitly confirms the candidate, target
  set, channel, rollout scope, observation criteria, and reason.

Re-enable proceeds through the human-approved staged rollout with explicit pause and rollback
points. Exact rings, target counts, observation periods, health thresholds, and channel promotion
rules are OPEN. Successful early targets do not authorize unreviewed later targets or channels.
Automatic updates and promotions remain disabled until their exact path is deliberately
re-authorized.

## Exit Criteria

### Safe Halted Handoff

The incident can leave active response while remaining on `HOLD` only when:

- affected promotion, deployment, and updates remain blocked;
- suspect artifacts, dependencies, credentials, channels, and targets are quarantined or safely
  contained;
- running affected capabilities are disabled or held in the accepted safe state;
- evidence custody, target inventory, unresolved scope, owners, and the next review point are
  recorded;
- local e-stop and other independent safety controls remain available; and
- no automated system can resume promotion, update, deployment, or output.

### Trusted Recovery

All of the following are required:

- the source-to-target chain has complete independently reviewed provenance;
- protected ownership, repository Ruleset, remote required checks, and exact-commit evidence are
  active;
- dependencies, generators, builders, verifier, artifacts, signing/release authority, registries,
  deployment identities, update channels, and targets pass the accepted checks;
- every affected target reports and independently proves the expected immutable
  artifact/configuration identity;
- rollback/disable and incident detection are tested;
- stage-host/live-adapter target evidence is complete where applicable;
- blocking findings are closed and any retained residual risk is authorized only within the
  OD-028-approved taxonomy;
- deliberate re-enable approval names the exact capability, artifacts, targets, channel, validity
  period or review trigger, reason, and rollback owner; and
- the accepted observation period completes without integrity, provenance, target, or safety
  contradiction.

The release remains `HOLD` when evidence is missing, stale, self-attested by a suspect boundary,
or inconsistent. There is no "ship with caveats" path for unknown artifact identity, missing
provenance, compromised signing/release authority, unresolved target scope, or a bypass of a
protected invariant.

## Evidence And Audit

Retain, with access and retention appropriate to the source class:

- incident, repository, commit, tree, ref, pull request, review, workflow, job, runner, builder,
  dependency, lock, generator, artifact, signature/key ID, provenance, release, registry,
  deployment, update, workload, target, rig, adapter, and trace identifiers;
- immutable source and artifact digests, manifest versions/digests, expected/actual archive
  members, verifier versions/results, and clean-build comparison outcomes;
- access, permission, repository-rule, workflow, credential/key, publication, channel, and target
  state transitions;
- promotion-halt, quarantine, revocation, rollback, disable, rebuild, review, re-enable, and
  rollback decisions with human provenance;
- raw event time, trusted observation time, source clock, and any uncertainty;
- evidence origin, custody, integrity, classification, retention, legal hold, and disclosure
  status; and
- unresolved gaps, affected target scope, owners, deadlines, and invalidation triggers.

Do not put credentials, private signing material, recovery secrets, malicious executable
payloads, raw candidate/prompt text, viewer-memory content, restricted rights evidence, or
unnecessary personal data into ordinary incident records. Store suspect bytes in the approved
restricted evidence system and refer to them by controlled identifiers. A public digest may still
be sensitive or linkable; follow the accepted evidence-classification policy.

## Escalation

Escalate immediately when:

- protected source, safety/contracts, CI, provider gateway, stage-host, policy, migration,
  infrastructure, secret, signing, or live-adapter integrity is uncertain;
- a suspect artifact was promoted, downloaded, installed, executed, or used by a production
  target;
- an affected target cannot be identified, reached, contained, or independently verified;
- a repository, signing, registry, workload, deployment, or update authority may be compromised;
- malicious code may have accessed credentials, signing material, personal data, rights evidence,
  provider data, or safety authority;
- a local stage-host stop, watchdog, verifier, adapter, or update boundary may be bypassed;
- rollback candidates share the suspect boundary or are incompatible;
- evidence is missing, mutable, contradictory, or controlled only by the suspected principal; or
- business pressure requests promotion without complete provenance or required validation.

Exact severity, on-call route, registry/vendor coordination, law-enforcement involvement,
contractual notice, platform/talent communication, and public communication remain accountable
human decisions. Suspected personal-data access or disclosure also invokes the
[personal-data breach response](personal-data-breach-response.md); technical containment does not
wait for legal classification. This document is not legal advice.

## Rehearsal Acceptance

This runbook cannot advance beyond `Drafted` until controlled exercises cover:

- malicious and accidental direct/transitive dependency substitution plus lockfile drift;
- compromised maintainer, repository administrator, bot, deploy key, and application authority;
- CODEOWNERS or Ruleset bypass, stale approval, forged required-check context, and direct push;
- workflow modification, unpinned or substituted CI dependency, excessive permission, secret
  exposure, compromised runner, poisoned cache, and untrusted pull-request execution;
- canonical source, generator, generated-output, build-script, build-backend, and toolchain
  substitution;
- stale generated output, archive path traversal, duplicate/link/cache member, unexpected file,
  metadata/version mismatch, wheel `RECORD` mismatch, manifest digest mismatch, irreproducible
  build, and isolated-install failure;
- verifier or security scanner compromise, including a false green result;
- package/registry substitution, mutable alias movement, mirror/cache poisoning, and
  post-publication artifact change;
- signing-key or release-identity compromise, forged/replayed metadata, and rotation/revocation
  uncertainty;
- workload/deployment identity compromise, wrong artifact deployment, target inventory gap, and
  misleading control-plane version state;
- stage-host installer, updater, update-channel, rollback slot, live-adapter, or OBS integration
  tamper;
- promotion halt while jobs, rollout, updates, restarts, or offline targets are in flight;
- blast-radius expansion from a shared builder, dependency, signer, channel, or mutable alias;
- trusted rebuild from reviewed source using recovered identities and clean builders;
- trusted rollback and the no-trusted-rollback path that disables the capability;
- deliberate target-scoped re-enable, staged rollout pause, rollback, and no automatic resume;
  and
- a complete sanitized timeline from first evidence through target reconciliation.

Exercises must include negative assertions: no suspect artifact reaches a new target; no old
authorization is revived; no compromised actor validates itself; no functional green result
overrides missing provenance; and no stage-host update can disable the independent local hard
stop. Target validation must use the exact production rig/configuration for installer, updater,
adapter, watchdog, audio, clock, queue, and local-stop claims.

## OPEN Decisions Requiring Human Review

- OD-012: independent repository ownership, protected-path approval count, reviewer separation,
  and repository-administration authority.
- OD-019: permitted scaffold scope, remote required checks, GitHub Ruleset, merge authority, and
  the point at which repository evidence becomes production-trusted.
- OD-027: incident command, severity, coverage, handoff/escalation, resilient communication,
  exercise cadence, runbook ownership, and deployment authorization.
- OD-028: adversary and trust assumptions, independent assessment, evidence freshness, residual
  risk taxonomy, and risk-acceptance authority.
- OD-031: software supply-chain and release-integrity profile, including the approved provenance,
  artifact, signing, distribution, update, target-verification, rollback, and re-enable gates.
- Trusted-source checkpoint, commit/tag authority, repository host, audit source, and ref-recovery
  procedure.
- Dependency allowlist/denylist, registry/mirror/cache trust, advisory response, provenance,
  malware/license review, emergency pin, and exception policy.
- Canonical build recipe, clean-builder trust and independence, reproducibility scope, allowed
  network/cache behavior, environment capture, and build-evidence lifetime.
- Artifact inventory and verifier coverage for packages, containers, installers, stage-host,
  live adapters, infrastructure bundles, policies, migrations, and updater payloads.
- Provenance/attestation format, storage, verification, source-to-artifact binding, and evidence
  custody.
- Signing algorithms, key custody, threshold/separation, builder versus release identities,
  rotation, revocation, compromise window, and re-signing rules.
- Registry and release-store immutability, mutable alias/channel policy, replication, cache purge,
  quarantine, takedown, and external coordination.
- Workload identity, deployment authorization, target inventory, artifact admission, target-local
  verification, restart, and disaster-recovery behavior.
- Stage-host installer/updater architecture, signed metadata, rollback/downgrade protection,
  offline update policy, local cache, channel ownership, live-adapter integrity, and local-stop
  independence.
- Promotion-halt, rollback/disable, trusted rebuild, rollout ring, observation, failure,
  rollback, and re-enable criteria by capability and target.
- Evidence classification, retention, legal hold, malicious-sample custody, disclosure, vendor,
  platform, talent, regulatory, and public-communication procedures.
- Exact registry, CI system, builder, scanner, signer, provenance service, updater, deployment
  platform, alert routes, and executable commands. None is selected by this Proposed runbook.
