# Foundation Authority And Repository Bootstrap Proposal

Status: Proposed human-decision aid; does not amend `AGENTS.md`, accept an ADR, authorize the
current scaffold, create a review subject, configure GitHub, or close any gate

Date: 2026-07-18

Governing sources:

- [`AGENTS.md`](../../AGENTS.md)
- [`vnova-review-handoff.md`](../../vnova-review-handoff.md)
- [Stage A governance bootstrap review handoff](foundation-stage-a-review-handoff.md)
- [CI quality gates and repository rules](ci-quality-gates.md)
- [Open decision register](../architecture/open-decisions.md)
- [Open decision disposition register](open-decision-dispositions.md)
- [Architecture gap analysis](../architecture/review-gap-analysis.md)

This proposal makes the unresolved foundation authority and first-review ceremony explicit. It is
not self-authorizing. Only protected humans with repository and architecture authority may apply
the proposed `AGENTS.md` amendment, accept ADRs, select OPEN outcomes, configure repository rules,
or approve a merge.

## Historical Verified Snapshot — Expired

The initial point-in-time observations were rechecked at `2026-07-18T05:00:44.168Z` and
supplemented by read-only repository orientation through `2026-07-18T06:18Z`. Source scope is
explicit because a local tracking ref, connected GitHub read, mutable worktree fact, and durable
candidate-bound artifact are not interchangeable. The documentation worktree changed afterward,
so the combined snapshot is historical. None of these rows is a current immutable review
artifact; Stage A must recollect and durably retain them from its isolated candidate.

| Item                                                | Source scope                    | Observed state                                                                                        | Acquisition / evidence status                                                     |
| --------------------------------------------------- | ------------------------------- | ----------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Local branch and base                               | Local Git checkout              | `main` at `b553fc4a4f8e50631f71e6c540337191f95366a8`                                                  | `git rev-parse HEAD`, `git branch --show-current`; repository projection only     |
| Local tracked remote base                           | Local Git tracking ref          | `origin/main` at the same SHA                                                                         | `git rev-parse origin/main`; not independently sufficient as live-remote evidence |
| Connected GitHub repository                         | Connected GitHub live read      | `kkmia417/VNova`, public, default branch `main`; latest commit is the same SHA                        | Repository/commit query response not retained as an immutable artifact            |
| Repository/account topology                         | Connected GitHub live read      | Personal repository; `kkmia417` has admin access; no organization membership was returned             | Point-in-time orientation, not reviewer-eligibility evidence                      |
| Remote branch search                                | Connected GitHub live read      | Only `main` was returned                                                                              | Point-in-time query; must be recollected for the candidate                        |
| Open pull requests                                  | Connected GitHub live read      | None returned                                                                                         | PR search response not retained as an immutable artifact                          |
| Pull-request workflow runs for base SHA             | Connected GitHub live read      | None returned                                                                                         | Commit workflow-run response not retained as an immutable artifact                |
| Candidate commit SHA / PR URL                       | Local checkout plus GitHub read | Missing; foundation work is modified/untracked                                                        | Mutable state cannot support review or disposition                                |
| Effective CODEOWNERS on base                        | Base Git tree                   | Missing; `.github/CODEOWNERS` exists only in the mutable worktree                                     | `git ls-tree`/worktree presence check; cannot protect its own bootstrap PR        |
| Collaborator/access inventory                       | Connected GitHub capability     | `not_collected`; the available connector did not enumerate collaborators                              | Must not be interpreted as “no collaborator”                                      |
| Recorded Ruleset export/URL and negative-control PR | Repository evidence set         | `not_collected`; no durable evidence is recorded                                                      | Must not be interpreted as “no Ruleset”                                           |
| Local GitHub CLI credential                         | Local `gh auth status`          | The stored `kkmia417` token was reported invalid                                                      | Local tooling limitation only; not a repository-state claim                       |
| Original architecture source                        | Local/base source inventory     | Missing                                                                                               | OD-008 remains OPEN                                                               |
| Handoff source                                      | Local/base file bytes           | `vnova-review-handoff.md`, SHA-256 `bac20743f9fd589e7ae5fcc9d7218f5fcbcc9272973f250462e14fb08ba5d851` | `Get-FileHash`; digest is reproducible but does not decide provenance             |
| Authoritative agent policy                          | Local/base file bytes           | `AGENTS.md`, SHA-256 `118b99159d2e90c6a12bd9555706ffe79a5698c54118b4414af259f5a30a24fa`               | `Get-FileHash`; the unamended policy remains authoritative                        |

The base commit contains the handoff, `AGENTS.md`, Accepted ADR-016/017, ADR-018 with
`Status: Draft, with OPEN numeric decisions`, and a small architecture set. It does not contain
the current root toolchain, `.github` governance, contract/safety/spec scaffolds, tests, tooling,
new ADR proposals, or review packets.

Local tests and artifact hashes currently describe a mutable worktree, not an immutable GitHub
review subject. They cannot be attached retroactively to the base SHA.

## Authority Mismatch

The literal Runtime Implementation Gate in `AGENTS.md` requires the listed artifacts to exist but
does not require:

- acceptance of foundation ADR-001, ADR-002, ADR-008, or the ADR-023 event-model companion;
- acceptance of ADR-018's structural invariants;
- resolution of the missing source/five-plane/gate-authority decisions;
- exact-commit protected review;
- remote `ci-required` evidence;
- effective CODEOWNERS and a Ruleset;
- a non-author or independent reviewer;
- a recorded gate-closure decision naming the next allowed increment.

Those stronger controls currently exist only in Proposed documents. Proposed documents cannot
silently strengthen or replace `AGENTS.md`.

The pre-gate allowlist also permits only docs/ADRs/governance/repository stubs, while the required
scaffold includes executable contract generation, validation, packaging, boundary analyzers,
tests, lockfiles, and CI. Calling that work only a "skeleton" understates what a human would review.

OD-019 therefore cannot close through a generic review-table acknowledgement. The authoritative
text must be amended, or the executable scaffold must remain unapproved/quarantined.

## Exact `AGENTS.md` Amendment Proposal

The following is proposed replacement text for the entire current
`## Runtime Implementation Gate` section. It is deliberately not applied by this change.

<!-- VNOVA-STAGE-A-AGENTS-RUNTIME-REPLACEMENT-BEGIN -->

```markdown
## Runtime Implementation Gate

Before feature or runtime code starts, protected human review must record that:

- ADR-016 and ADR-017 remain Accepted.
- ADR-001, ADR-002, ADR-008, ADR-023, and ADR-018's structural invariants are Accepted or
  replaced by named Accepted ADRs. Numeric values and other explicitly OPEN behavior may remain
  disabled.
- OD-040's disposition lifecycle is ratified through its one-time protected genesis rule.
- Open Decisions OD-008, OD-017, OD-018, OD-019, OD-020, OD-021, and OD-033 have valid
  `DECIDED`, closure-capable dispositions. `Deferred`, `Inconclusive`, `OPEN`, `INVALIDATED`,
  missing, or `Rejected` without an Accepted replacement keeps the foundation blocked. ADR-002
  cannot be accepted while OD-017, OD-021, or OD-033 remains OPEN or otherwise lacks such a
  disposition. ADR-023 cannot be accepted while OD-017 or OD-033 remains OPEN or otherwise lacks
  such a disposition. ADR-002 and ADR-023 must describe one compatible event-contract model for
  the same immutable reviewed subject.
- Every later Open Decision whose registered `Blocks` scope includes a foundation artifact,
  acceptance of a foundation ADR, or foundation gate closure also has a valid `DECIDED`,
  closure-capable disposition; the named list above is the current snapshot, not a bypass for a
  newly added blocker.
- Every outcome is recorded against the exact immutable review subject in the accepted Open
  Decision Disposition Register; a review-table value alone is not authority.
- The system overview and gap-analysis baseline are approved.
- The exact foundation review subject is identified by repository, base SHA, candidate SHA,
  complete external machine inventory, pre-decision semantic overlay, frozen review-package
  manifest, pull request, final external disposition attestations, and effectiveness witness.
- The safety boundary scaffold, contract/schema source and generated distributions, event
  schema/catalog scaffold, boundary enforcement, deterministic generators, fixtures, packaging,
  artifact verification, tests, lockfiles, and CI are accepted for the exact candidate SHA.
- The final candidate SHA passes the required local and remote Linux/Windows gates.
- The default branch enforces the stable `ci-required` check, pull-request review, effective
  CODEOWNERS, stale-review dismissal, and protected-file ownership through a recorded Ruleset.
- At least one eligible non-author human reviewer can satisfy the protected review policy.
- A foundation gate-closure record names only the next implementation increment authorized.

Before that closure record, Codex may edit only:

- documentation, ADR proposals, governance records, review packets, repository-governance
  stubs, CODEOWNERS proposals, and CI TODO/design notes; and
- after the effective OD-019 disposition has been projected through protected review and the
  Stage A post-merge ownership evidence is complete, narrowly scoped review-only foundation
  enforcement evidence prospectively authorized by that disposition: `packages/contracts`, the
  non-runtime `packages/safety` mint-boundary placeholder, `specs/events`, root workspace/package
  manifests and repository text-normalization, version-manager, package-manager, formatter,
  linter, type-check, test, and boundary configuration, deterministic
  generation/validation/packaging tooling,
  boundary checks, fixtures/tests, lockfiles, and the CI workflow needed to evaluate those
  artifacts.

The review-only foundation evidence:

- does not implement a runtime capability, provider, prompt/persona, policy default, database
  schema or migration, worker, API/frontend, stage-host command/watchdog, OBS/VTube Studio
  adapter, infrastructure, secret, or production configuration;
- remains quarantined and non-authoritative until the exact-subject foundation review closes;
- must not be merged, published, deployed, imported by runtime code, or described as Accepted
  merely because local tests pass; and
- retains every protected human-review requirement in this document.

All feature/runtime work remains prohibited until the closure record exists. Closing the
foundation gate authorizes only the named next increment; every feature-specific ADR, OPEN
decision, migration ADR, protected-path review, threat-model validation, target-validation, and
operational-readiness gate remains cumulative.
```

<!-- VNOVA-STAGE-A-AGENTS-RUNTIME-REPLACEMENT-END -->

Protected reviewers must revise this wording if it grants too much or too little scope. Applying
only a decision-table value while leaving the authoritative section unchanged does not resolve
OD-019 durably.

### Companion Responsibility-Boundary Amendments

The same protected governance change must reconcile two other authoritative `AGENTS.md` clauses;
replacing only the Runtime Implementation Gate leaves known contradictions.

Replace the contract-source bullets with:

```markdown
- `packages/contracts`: generated/distributed shared contract libraries plus deterministic
  contract generation, validation, and compatibility tooling; it is not the hand-authored event
  schema source.
- `specs/events`: sole hand-authored source for versioned event JSON Schemas and event catalogs,
  including envelope and payload schemas.
```

For the unresolved five-plane sentence, the OD-018 disposition selects exactly one atomic edit:

- **Restore:** replace it with the five human-approved names, ownership, responsibilities, and
  dependency directions from the recovered authoritative source, and reconcile ADR-001 and the
  overview in the same change; or
- **Retire:** replace it with
  `Conceptual responsibility boundaries are package/module boundaries, not additional deployed services.`
  and retain only the explicit named surfaces/packages in ADR-001 and the overview.

`Defer` means no amendment is applied and the foundation stays blocked. An agent must not fill in
missing plane names.

## External Review Artifact Contract

Before any review, generate a complete inventory from the immutable candidate Git tree and store
it outside that tree with an immutable digest/attestation. Human semantic assessment is a
separate pre-decision overlay referencing the exact candidate SHA and inventory digest. Final
human decisions are separate outer attestations referencing both digests. This separation
prevents a path/hash generator from silently becoming a decision maker and prevents an overlay
from recursively containing the approval that approves it.

### Machine Inventory

The external read-only collector records facts only:

| Required field                                 | Meaning                                                                            |
| ---------------------------------------------- | ---------------------------------------------------------------------------------- |
| Format/canonicalization version                | Exact deterministic byte format and ordering rules                                 |
| Repository, object format, base/candidate SHA  | Exact immutable Git subject and comparison base                                    |
| Path, Git mode/type, and blob object ID        | Exact candidate-tree member identity                                               |
| Raw-byte SHA-256 and byte length               | Tool-independent content digest and size                                           |
| Changed-path status                            | Exact add/modify/delete/rename relation to the base                                |
| Collector identity/version and collection time | Acquisition provenance; mutable time stays outside the canonical inventory digest  |
| External URI/attestation and inventory digest  | Durable evidence identity; the inventory cannot include its own digest recursively |

The inventory never emits `Accept`, `DECIDED`, gate closure, reviewer eligibility, risk
acceptance, or an enabled capability.

### Pre-Decision Semantic Overlay

The protected pre-decision overlay records meaning and proposed scope:

| Required field          | Meaning                                                                                                                                   |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Inventory binding       | Exact candidate SHA, inventory URI, and inventory digest                                                                                  |
| Category                | Documentation/proposal, governance stub, executable enforcement tooling, protected contract/safety evidence, or forbidden runtime feature |
| Executable behavior     | What the file can validate, generate, build, package, import, run, or publish                                                             |
| Governing authority     | `AGENTS.md`, ADR/OD, protected owner, and review requirement                                                                              |
| Data/safety impact      | Contracts, mint boundary, event semantics, packaging, CI, migration, prompt/policy, provider, rig, or none                                |
| Validation references   | Exact local/remote job, fixture, mutation test, package check, expected result, and evidence ID                                           |
| Required revisions      | Semantic findings that must change before a final decision                                                                                |
| Disabled-scope proposal | Capability proposed to remain prohibited even if the reviewed source is accepted                                                          |

The overlay contains no final disposition, approval event/sufficiency, reviewer eligibility
judgment, decision/effective time, risk acceptance, or final review evidence ID. Agents may
prepare a blank overlay and non-binding classification recommendation. Only eligible humans
finalize its semantic assessment, but that act does not approve the candidate or close an OD.

At minimum the pre-decision semantic overlay categorizes:

1. root documentation and architecture/ADR/governance/security/runbook proposals;
2. root toolchain configuration, lockfiles, formatter/linter/type/test configuration;
3. `.github` workflow, CODEOWNERS, and pull-request template;
4. `specs/events` canonical envelope/catalog source;
5. generated/distributed `packages/contracts` libraries, manifests, packaging, and validators;
6. `packages/safety` non-runtime mint-boundary placeholder;
7. contract, architecture, CI, artifact, documentation, and red-team test evidence;
8. deterministic contract/artifact/boundary/CI/documentation tooling;
9. feature/runtime/provider/adapter/migration/prompt/policy/infra/secret implementation, which must
   be empty before gate closure.

A directory label is not sufficient. The machine inventory lists every path from the immutable
candidate commit; the pre-decision overlay covers every changed or protected path required by the
review; and package evidence proves that archives contain only the reviewed allowlist. Any
repository mirror of an external artifact is a later protected projection and cannot
retroactively change the reviewed subject.

### Frozen Review-Package Manifest

After the exact PR head and approval event exist, an external protected manifest binds the
repository/base/candidate, inventory/overlay receipts, PR head/diff, temporary rule, validation,
account/access, and approval-event evidence. It contains no outcome or effective-state claim and
excludes its own receipt/digest/URI and all later disposition/witness/projection identities. A
changed prerequisite requires a new manifest and dependent review.

### Final Protected Disposition Attestation

Each final OD or gate decision is a separate signed/protected record outside the candidate and
pre-decision overlay. It binds the frozen review-package-manifest digest, candidate SHA,
inventory/overlay digests, PR head/diff, validation and repository-rule evidence, accountable
humans, independent-review judgment, explicit outcome, retained disabled scope, risk/sufficiency
decisions, invalidation rules, and effective condition/order. The signed payload excludes its own
digest/URI and any later projection SHA; the protected system supplies those in an immutable
receipt.

For Stage A the required order is `OD-040 → OD-018 → OD-019`. The exact merge is captured by a
separate append-only effectiveness witness that binds the package-manifest digest, every ordered
disposition receipt/digest and predecessor, repository/base/candidate/target branch, merge
event/time, condition result/time, and derived lifecycle state. A later protected repository
projection mirrors the external records but does not create their initial authority.

Stage A additionally uses the exact changed-path allowlist and worksheets in
[`VNOVA-FOUNDATION-STAGE-A-HANDOFF-v1`](foundation-stage-a-review-handoff.md). That handoff is not
the inventory, overlay, candidate, or disposition.

## Two-Stage Bootstrap Ceremony

GitHub uses the `CODEOWNERS` file from the pull request's base branch for review requests. A
CODEOWNERS file introduced by a PR therefore cannot protect that same first PR. GitHub also does
not let an author approve their own pull request, and a required status check must first have a
recent successful run in the repository before it can be selected and must pass on the latest
reviewed SHA.

Use the
[`VNOVA-FOUNDATION-STAGE-A-HANDOFF-v1`](foundation-stage-a-review-handoff.md)
selection ledger to construct Stage A from a clean checkout. Do not stage the current mixed
worktree wholesale. That handoff is intentionally Retire-only: selecting OD-018 Restore requires
a replacement exact handoff containing the authenticated recovered source, ADR-001, overview,
affected boundary projections, and tests.

### Stage A: Human-Administered Governance Bootstrap

Create a narrowly scoped governance PR containing:

- the exact OD-040 genesis proposal, full-record template/lifecycle, and blank repository
  disposition summary;
- the human-approved `AGENTS.md` amendment;
- the exact OD register, disposition lifecycle, authority proposal, Stage A handoff, and
  non-executable CI/repository-rule design;
- CODEOWNERS with human-approved individual GitHub accounts having accepted collaborator/write
  access and ownership of `.github/CODEOWNERS` itself;
- the pull-request template and non-executable repository-rule documentation;
- no contract/safety/schema/toolchain/CI executable scaffold.

The broader mutable `docs/governance/architecture-foundation-review.md` packet is not in Stage A.
Its local links depend on Stage B architecture and governance material that is absent from the
base-plus-allowlist tree. It may be reviewed only with that dependency-closed Stage B subject.
Organization-team CODEOWNER tokens are inapplicable while this remains a personal repository; a
deliberate ownership/identity change requires a regenerated handoff and evidence set.

Before merge:

- configure a temporary repository rule requiring a pull request and at least one eligible
  non-author human approval through a path that does not depend on the not-yet-effective
  CODEOWNERS file;
- freeze the candidate first, then generate the complete machine inventory and pre-decision
  semantic overlay;
- record repository/base/candidate SHA, inventory/overlay receipts, PR/review URLs, account/access
  facts, and administrative-rule evidence;
- dismiss/reacquire approval after any source change;
- freeze the external review-package manifest over those prerequisite receipts;
- create separate protected external OD-040, OD-018, and OD-019 disposition attestations in that
  order; and
- merge only after the protected architecture/repository owners approve the authoritative
  amendment.

After merge, verify CODEOWNERS is parsed from `main`, every owner has required repository access,
protected patterns resolve as intended, and the author cannot satisfy their own approval. Then
land a separate protected projection PR for the three external records and the disposition
summary. Stage B waits for that projection.

### Stage B: Protected Foundation Scaffold

Stage B requires a separate dependency-closed handoff with an exact base SHA, path/status/mode
allowlist, exclusions, ADR status edits, generated-artifact closure, and protected decision
artifacts. The current mixed worktree and this broad proposal are not that handoff. Until a
protected human approves the exact Stage B handoff, no one may construct its candidate by staging
the worktree wholesale.

The Stage B decision set is explicit:

| Record class                    | Exact items                                          | Required treatment                                                                                                      |
| ------------------------------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Effective Stage A prerequisites | OD-040, OD-018, OD-019                               | Verify effective receipts, witness, projection, and ownership; do not decide them again                                 |
| Stage B OD dispositions         | OD-008, OD-017, OD-020, OD-021, OD-033               | One separate closure-capable intended disposition and receipt per OD for the same immutable subject                     |
| Foundation ADR decisions        | ADR-001, ADR-002, ADR-008, ADR-018, ADR-023          | One explicit clause-level decision per ADR; ADR-002 and ADR-023 form one atomic compatible review cohort                |
| Architecture baseline review    | System overview and review gap analysis              | Bind the exact reviewed bytes and retained OPEN/disabled scope                                                          |
| Repository evidence sufficiency | CI, artifacts, CODEOWNERS, Ruleset, negative control | Human sufficiency decision over exact external evidence IDs; machine observations do not decide sufficiency             |
| Foundation closure              | Gate outcome and one next implementation increment   | Separate protected record after every prerequisite is effective; it cannot be folded into one OD or generic attestation |

Use this order:

1. verify the Stage A decision projection, effectiveness witness, and post-merge ownership
   evidence;
2. construct only the separately approved exact Stage B handoff in an isolated clean checkout;
3. freeze the base and candidate SHAs, then generate the complete machine inventory and
   pre-decision semantic overlay;
4. run and record locked local verification and package-artifact results;
5. let the now-effective base-branch CODEOWNERS request protected reviewers;
6. run remote Linux/Windows jobs and `ci-required` on the final candidate SHA;
7. configure and export the Ruleset requiring `ci-required`, code-owner/non-author review,
   stale-review dismissal, conversation resolution, and blocked force push/deletion;
8. use a separate deliberately failing control PR/commit to prove merge is blocked, then close it
   without merging;
9. re-run the final exact SHA after the last change, obtain fresh protected approval, and freeze
   the external review-package manifest over every prerequisite receipt;
10. create separate protected pre-merge intended disposition attestations for OD-008, OD-017,
    OD-020, OD-021, and OD-033, plus the five explicit ADR decisions and architecture/evidence
    decisions above; never substitute one singular "foundation approved" record;
11. merge only the exact reviewed candidate through the protected rule. The executable scaffold
    remains quarantined and non-authoritative if the merge or any post-merge condition is absent;
12. append a post-merge effectiveness witness binding the merged SHA, merge event/time, ordered
    disposition receipts/predecessors, ADR decisions, condition results/times, and derived states;
    a witness cannot be created or declared effective before the merge it names;
13. land a separate protected projection PR for the external records and disposition summary,
    then create the distinct foundation gate-closure/next-increment record, or leave the gate
    blocked.

If no qualified second reviewer is available, the protected review requirement is unsatisfied.
Administrator bypass is an emergency repository capability, not ordinary foundation evidence.

Official GitHub references:

- [About code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [Approving a pull request with required reviews](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/approving-a-pull-request-with-required-reviews)
- [Troubleshooting required status checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks)

These references explain GitHub mechanics; VNova's stricter safety/governance requirements still
come from `AGENTS.md`, Accepted ADRs, and recorded human decisions.

## Foundation Decision Sequence

### 0. OD-040: One-Time Disposition Genesis

Before any other OD is treated as closed, the repository administrator, architecture owner, and
eligible non-author human reviewer ratify, revise, or reject OD-040 using the one-time genesis
rule in the [disposition register](open-decision-dispositions.md). The exact lifecycle, full
record schema, base/candidate SHA, inventory/pre-decision-overlay digests, governance PR,
temporary rule, and independent review are bound by one external protected package manifest.
They need not and cannot all be embedded recursively in the candidate Git tree.

If genesis is not validly ratified, every OD remains OPEN and later rows in this sequence are
recommendations only.

### 1. OD-008: Baseline Provenance

Protected architecture owners select exactly one:

| Choice                     | Required record                                                                                                       | Effect                                                                                             |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Recover original           | Source location, immutable digest, authority, and reconciliation findings                                             | Gap analysis is updated against the original plus handoff                                          |
| Designate current baseline | Exact handoff digest above, current overview/gap versions, known limitations/conflicts, and explicit human acceptance | The handoff-derived baseline becomes review authority without pretending the original was reviewed |
| Defer                      | Missing evidence and owner/follow-up                                                                                  | Foundation remains blocked                                                                         |

The record must note that the handoff described event schemas under `packages/contracts`, while
Proposed ADR-002 intentionally selects `specs/events` as the hand-authored schema/catalog source and
`packages/contracts` as generated distribution/tooling. Acceptance is an explicit revision, not
silent transcription.

### 2. Open Decision OD-018: Five-Plane Taxonomy

Do not confuse Open Decision OD-018 with ADR-018 latency.

| Choice  | Required record                                                                                                                                      | Effect                                                                  |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Restore | Authoritative source/digest, five names, owners, responsibilities, dependency directions, and reconciliation with ADR-001                            | Update `AGENTS.md`, ADR-001, overview, boundaries, and tests atomically |
| Retire  | Human decision that only named deployed surfaces/package boundaries govern; remove the unnamed five-plane phrase from active authoritative documents | ADR-001 may proceed on explicit named boundaries                        |
| Defer   | Missing source and follow-up                                                                                                                         | ADR-001 and foundation remain blocked                                   |

Given the absent source, retirement is the safer proposal; only the architecture owner may choose
it.

### 3. OD-019: Authoritative Gate

Select:

- apply/revise the exact amendment above and approve the quarantine categories; or
- reject the amendment/scaffold, record the required removal/rework, and keep runtime blocked.

A generic "scaffold acknowledged" outcome is insufficient.

### 4. ADR-001, ADR-002, ADR-008, ADR-018, And ADR-023

For each ADR, record:

- invariant clauses accepted;
- revisions required;
- exact OPEN items retained;
- dependent behavior kept disabled;
- required status text and follow-up ADR/OD;
- evidence reviewed and reviewer role/date.

ADR-018's structural decision separately covers full-response-before-synthesis, deadline
non-extension, candidate/task expiry, explicit timeout/late-result behavior, and clock/telemetry
semantics. Numeric latency/SLO/TTL values and sentence-chunked TTS may remain OPEN/disabled only
when recorded explicitly.

ADR-002 cannot be accepted until protected review resolves:

- Open Decision OD-017 for compatibility, catalog transitions, deprecation, rollback, and removal;
- Open Decision OD-021 for non-event command/task/acknowledgement schemas and code generation; and
- Open Decision OD-033 for the current mandatory `stream_session_id` envelope versus required
  environment/talent/viewer events, without inventing a session or merely making the field
  nullable without typed subject/scope and ordering semantics.

ADR-023 is the Proposed foundation companion that supplies that typed event model. It cannot be
accepted until Open Decisions OD-017 and OD-033 have valid closure-capable dispositions. ADR-002,
ADR-023, OD-017, and OD-033 must reference the same immutable reviewed subject and agree on the
v2 envelope and trusted version framing, immutable event-contract profile and separate monotonic
catalog lifecycle, catalog-fixed typed primary scope and aggregate subject,
`(aggregate_version, event_index)` plus a manifest for every aggregate version and
expected-delivery completeness, correlation/causation, compatibility, typed monotonic protection
overlay epochs/partition high-waters and immediate effect-boundary validation, producer/consumer
authorization, and disabled scope. If reviewers reject ADR-023, they must name an Accepted
compatible replacement; accepting ADR-002 with an unstated event model is invalid.

### 5. OD-020: Historical ADR-006

Select exactly one:

| Choice            | Required record                                                                                                                                                                                                                                                                                                                                                                                                 |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Recover           | Original ADR-006 source, digest, status, and reconciliation                                                                                                                                                                                                                                                                                                                                                     |
| Reserve and remap | Explicitly reserve number `006`; record that only the observable operator-console implementation dependency is known; map that scope to the named future acceptance gates ADR-003/008/015/019/020/021 plus rehearsal evidence without claiming to recover unknown content. Foundation closure may record this mapping now, but it does not accept those feature ADRs or enable operator-console/rehearsal scope |
| Defer             | Keep the provenance gap and affected scope blocked                                                                                                                                                                                                                                                                                                                                                              |

### 6. OD-021: Non-Event Contract Source

Decide the invariant alongside ADR-002 or add an explicit feature-gate disposition:

- one language-neutral hand-authored schema source;
- deterministic generated contracts/validators for Python, TypeScript, and the selected
  stage-host language;
- no parallel handwritten task/control DTOs;
- explicit compatibility, canonical serialization, authentication/signing, and activation gates.

Until decided, `SpeechTask`, restrictive epoch/mode commands, rights/deletion invalidation,
acknowledgements, heartbeat/clock, reconnect, and reconciliation protocols remain disabled.

## Evidence Matrix

| Requirement                           | Current evidence                                                                 | Source scope / freshness                                                            | Durable evidence required before human sufficiency decision                           |
| ------------------------------------- | -------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| OD-040 disposition genesis            | Proposed; no effective dispositions                                              | Mutable repository proposal; no immutable evidence ID                               | One-time protected genesis record with exact subject and eligible non-author review   |
| OD-019 / authoritative gate amendment | Contradicted by current unconditional text/allowlist                             | Base `AGENTS.md` plus mutable proposal; current at the snapshot time                | Protected amendment plus contract-source/five-plane companion edits merged and linked |
| ADR-001 + Open Decision OD-018        | Proposed; exclusive restore/retire choice absent                                 | Mutable repository proposals; no human record                                       | Named outcome plus consistent `AGENTS.md`/ADR/overview                                |
| ADR-002 and ADR-023 + OD-017/021/033  | Partial; compatibility, non-event source, and non-session event scope unresolved | Mutable repository proposals; no human records                                      | One compatible immutable accepted event subject plus source/contract plan             |
| ADR-008                               | Proposed; safety package is only a placeholder                                   | Mutable repository proposal/scaffold; no human record                               | Accepted invariant and explicit disabled implementation scope                         |
| ADR-018 structural scope              | Proposed; numeric values OPEN                                                    | Tracked mutable document; no human record                                           | Clause-level accepted invariants and retained OPEN values                             |
| System overview/gap + OD-008          | Present; source limitation remains                                               | Tracked mutable documents plus base handoff digest                                  | Exact source/baseline choice and reviewed versions                                    |
| OD-020 / ADR-006                      | Missing historical source                                                        | Local/base inventory; provenance evidence absent                                    | Recover or explicit reserve/remap outcome                                             |
| Stage A exact change-set handoff      | `VNOVA-FOUNDATION-STAGE-A-HANDOFF-v1`; proposed and non-authorizing              | Mutable repository projection; invalidated by any allowlist change                  | Human-confirmed allowlist bound to the immutable Stage A candidate                    |
| Inventory / pre-decision overlay      | Contracts specified; no candidate-bound external artifacts exist                 | Design only; no collector/overlay artifact, URI, digest, or attestation             | Every candidate path/digest and required semantic assessment recorded separately      |
| Frozen review-package manifest        | Contract specified; no candidate-bound external manifest/receipt exists          | Design only; no external ID, digest, URI, or attestation                            | Every prerequisite receipt bound without an outcome or self-reference                 |
| Final disposition/effectiveness       | No external OD attestation, approval binding, or effectiveness witness exists    | Human/protected-system evidence absent                                              | Separate ordered records plus exact-merge witness; never embedded recursively         |
| Immutable candidate SHA and PR        | Missing                                                                          | Local/GitHub read at snapshot time; mutable worktree remains                        | Candidate commit/PR frozen; later changes invalidate evidence                         |
| Effective CODEOWNERS                  | Missing on base branch                                                           | Base Git tree; mutable single-owner proposal is not effective                       | Parsed owners with access; protected patterns and non-author path proven              |
| Remote `ci-required`                  | No run for current base/candidate                                                | Connected GitHub point-in-time read; response not durably retained                  | Latest candidate SHA passes all required Linux/Windows jobs                           |
| Active Ruleset                        | No recorded export/URL                                                           | Not collected; no durable evidence ID                                               | Exact rule config exported/linked and applied to default branch                       |
| Negative-control PR                   | `not_collected`; no durable blocked-control evidence is recorded                 | The point-in-time open-PR search is not an all-state historical inventory           | Deliberately failing candidate demonstrably cannot merge                              |
| Overall gate closure                  | Not currently closable                                                           | Derived from missing machine facts and human dispositions; not an authority outcome | Every blocking row accepted/evidenced; exact next increment named                     |

## Human Decision Record

Agents leave every decision, reviewer, date, sufficiency, authority, and scope cell empty.
Machine-observed PR/check/Ruleset/inventory facts remain in the evidence matrix or an external
evidence object and are referenced here only after humans judge them sufficient and fresh.

| Item                                           | Selected outcome / Accept / Revise / Reject | Human reviewer and role | Date | Evidence/record link and retained disabled scope |
| ---------------------------------------------- | ------------------------------------------- | ----------------------- | ---- | ------------------------------------------------ |
| OD-040 one-time genesis/lifecycle              |                                             |                         |      |                                                  |
| OD-008 baseline provenance                     |                                             |                         |      |                                                  |
| Open Decision OD-018 taxonomy                  |                                             |                         |      |                                                  |
| OD-019 `AGENTS.md` amendment                   |                                             |                         |      |                                                  |
| ADR-001                                        |                                             |                         |      |                                                  |
| ADR-002                                        |                                             |                         |      |                                                  |
| ADR-023                                        |                                             |                         |      | Same immutable subject as ADR-002/OD-017/OD-033  |
| OD-017 event compatibility/deprecation         |                                             |                         |      |                                                  |
| OD-021 non-event contracts                     |                                             |                         |      |                                                  |
| OD-033 event identity/scope/order/completeness |                                             |                         |      |                                                  |
| ADR-008                                        |                                             |                         |      |                                                  |
| ADR-018 structural scope                       |                                             |                         |      |                                                  |
| OD-020 / ADR-006                               |                                             |                         |      |                                                  |
| Protected ownership/quorum                     |                                             |                         |      |                                                  |
| Mechanical evidence sufficiency/freshness      |                                             |                         |      | Human judgment over exact external evidence IDs  |
| Overall foundation gate and next increment     |                                             |                         |      |                                                  |

Silence, elapsed time, a local pass, an uncommitted worktree, a PR merge, or an administrator
bypass cannot populate this record.
