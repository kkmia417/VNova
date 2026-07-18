# Foundation Stage A Governance Bootstrap Review Handoff

Status: Proposed review-only handoff; no candidate, approval, authority, or gate closure

Date: 2026-07-18

Handoff ID: `VNOVA-FOUNDATION-STAGE-A-HANDOFF-v1`

This handoff defines the smallest review subject that can establish VNova's repository-governance
authority before the executable foundation scaffold is reviewed. It is a path-selection and
evidence worksheet, not a pull request, external inventory/overlay, disposition, vote, or
amendment.

It does not:

- modify `AGENTS.md`;
- ratify OD-040 or close any other Open Decision;
- name an eligible reviewer or approve the current CODEOWNERS proposal;
- accept an ADR;
- authorize the current executable scaffold;
- create an immutable candidate or external inventory/overlay;
- configure GitHub Rulesets or required checks; or
- authorize feature, runtime, provider, schema, migration, prompt, policy, infrastructure, or
  stage-host implementation.

Only eligible humans acting through the protected process in the
[foundation authority and bootstrap proposal](foundation-authority-and-bootstrap-proposal.md)
may turn a later immutable candidate into effective evidence.

## Governing Sources

- [`AGENTS.md`](../../AGENTS.md)
- [`vnova-review-handoff.md`](../../vnova-review-handoff.md)
- [Foundation authority and bootstrap proposal](foundation-authority-and-bootstrap-proposal.md)
- [Open Decision Register](../architecture/open-decisions.md)
- [Open Decision Disposition Register](open-decision-dispositions.md)
- [CI quality gates and repository rules](ci-quality-gates.md)

If this handoff conflicts with one of those sources, the higher-authority source governs and this
handoff must be revised before a candidate is frozen.

## Historical Context — Expired

The initial observations were rechecked at `2026-07-18T05:00:44.168Z` and supplemented by
read-only repository orientation through `2026-07-18T06:18Z`. The documentation worktree changed
afterward. The combined snapshot is therefore expired even where the later read observed the same
facts. It is historical orientation only, not current or candidate-bound evidence. Every row must
be recollected and durably retained from the isolated Stage A candidate and the live repository
immediately before review.

| Observation                   | Source scope                     | Observed fact                                                                                                    | Evidence status                                             |
| ----------------------------- | -------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Repository                    | Connected GitHub repository read | `kkmia417/VNova`; public; default branch `main`                                                                  | Live read was not retained as an immutable artifact         |
| Local branch and `HEAD`       | Local checkout                   | `main`; `b553fc4a4f8e50631f71e6c540337191f95366a8`                                                               | Reproducible locally; not a Stage A candidate               |
| Local `origin/main` ref       | Local tracking ref               | Same SHA as local `HEAD`                                                                                         | Not independently sufficient as live-remote evidence        |
| Latest connected commit       | Connected GitHub commit read     | Same SHA as local `HEAD`                                                                                         | Live read was not retained as an immutable artifact         |
| Repository/account topology   | Connected GitHub repository read | Personal repository owned by `kkmia417`; owner access reported as admin; no organization membership was returned | Point-in-time query only; not reviewer-eligibility evidence |
| Remote branches               | Connected GitHub branch search   | Only `main` was returned                                                                                         | Point-in-time query only                                    |
| Open pull requests            | Connected GitHub PR search       | None returned                                                                                                    | Point-in-time query only                                    |
| PR workflow runs at base      | Connected GitHub Actions read    | None returned                                                                                                    | Point-in-time query only                                    |
| Candidate commit and PR       | Local checkout plus GitHub read  | Missing; the foundation work remains modified/untracked                                                          | Cannot support review or disposition                        |
| Effective base CODEOWNERS     | Base Git tree                    | Missing from `HEAD`; a single-owner proposal exists only in the mutable tree                                     | Cannot protect its own bootstrap PR                         |
| Collaborator/access inventory | Connected GitHub capability      | `not_collected`; the available read did not enumerate repository collaborators                                   | Must not be interpreted as “no collaborator”                |
| Ruleset and negative control  | Repository evidence set          | `not_collected`; no durable export, URL, attestation, or blocked-control PR is recorded                          | Must not be interpreted as “no Ruleset”                     |
| Local GitHub CLI credential   | Local `gh auth status`           | The stored `kkmia417` token was reported invalid                                                                 | Local tooling limitation only; not a repository fact        |

The current mixed worktree must not be staged wholesale. Stage A is prepared in a fresh clone or
separate Git worktree rooted at the reviewed base, using only the change-set allowlist below. A
new branch in this dirty shared checkout is not isolation.

## Stage A Objective

This handoff can construct only the governance-bootstrap candidate for a human-selected
**OD-018 Retire** outcome. It does not select that outcome. If protected humans select
**Restore**, this handoff is invalid: first recover and authenticate the source, then replace this
handoff with a new exact allowlist that atomically includes the recovered source, ADR-001,
overview, every affected boundary projection, and required tests.

Under that condition, Stage A may establish only:

1. the one-time OD-040 disposition authority and record lifecycle;
2. the human-selected OD-018 retirement wording required by the companion `AGENTS.md` and system
   overview edits;
3. the human-selected OD-019 authoritative gate amendment and responsibility-boundary edits;
4. effective base-branch CODEOWNERS and a non-executable pull-request review template; and
5. the review packets and repository-rule documentation needed to explain those changes.

OD-040 must be validly ratified before another Open Decision can become effective. The OD-018 and
OD-019 external records may reference the same immutable candidate only with the explicit
effective order `OD-040 → OD-018 → OD-019`, separate record identities, and distinct human
decisions. Stage A changes no ADR status and does not decide the remaining foundation or feature
Open Decisions.

## Exact Stage A Change-Set Allowlist

This is an allowed diff/status/mode set, not the complete candidate-tree inventory. Every changed
path in the Stage A candidate must appear exactly once below with the required status. `M` means
the base and candidate both contain a regular `100644` blob; `A` means only the candidate contains
a regular `100644` blob. `D`, `R`, `C`, `T`, unmerged states, mode-only changes, non-blob entries,
and any other status invalidate Stage A. The external machine inventory still enumerates every
regular-file leaf in the complete candidate Git tree, including unchanged base files.

| Candidate path                                                   | Required status | Required Stage A operation                                                                                                                 | Why it is in scope                                                                                           | Human disposition |
| ---------------------------------------------------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ | ----------------- |
| `AGENTS.md`                                                      | `M`             | Apply exactly the protected gate, contract-source, and OD-018 retirement amendment                                                         | Resolves the authoritative pre-gate scope conflict; a review-table value alone is insufficient               |                   |
| `.github/CODEOWNERS`                                             | `A`             | Add human-approved individual GitHub accounts with accepted collaborator/write access, ownership of itself, and a distinct non-author path | Establishes ownership only after merge to the base branch; the current single-owner proposal is insufficient |                   |
| `.github/pull_request_template.md`                               | `A`             | Add the non-executable protected-path, evidence, decision, and risk checklist                                                              | Makes later review expectations visible without running candidate code                                       |                   |
| `docs/architecture/open-decisions.md`                            | `A`             | Add the OD-040/018/019 authority definitions and retain all unresolved scope as blocked                                                    | Defines the decisions whose final attestations remain external to the candidate                              |                   |
| `docs/architecture/review-gap-analysis.md`                       | `M`             | Apply only the narrow authority, retired-taxonomy, and gate-state projection required by the selected amendment                            | Keeps the documented gate state consistent; do not stage unrelated mutable-worktree edits wholesale          |                   |
| `docs/architecture/system-overview.md`                           | `M`             | Replace unresolved five-plane wording with only the human-selected explicit named-boundary baseline                                        | Makes the Retire outcome atomic across the authoritative gate and existing base overview                     |                   |
| `docs/governance/open-decision-dispositions.md`                  | `A`             | Add the lifecycle, evidence separation, blank templates, and blank append-only summary                                                     | Defines how an external decision becomes effective without letting an agent self-authorize                   |                   |
| `docs/governance/foundation-authority-and-bootstrap-proposal.md` | `A`             | Add the exact proposed amendment, staged ceremony, artifact contract, and evidence matrix                                                  | Supplies the non-self-authorizing redline and bootstrap procedure                                            |                   |
| `docs/governance/foundation-stage-a-review-handoff.md`           | `A`             | Add this path-exact handoff                                                                                                                | Prevents the mixed worktree from being mistaken for a Stage A candidate                                      |                   |
| `docs/governance/ci-quality-gates.md`                            | `A`             | Add only non-executable required-check, protected-path, and repository-rule design                                                         | Defines later enforcement without including the workflow or toolchain in Stage A                             |                   |

## Base-Anchored Source Blueprint

Stage A must be assembled from the Git objects below, not by copying the broad current worktree.
The immutable candidate inventory supersedes these preparation facts once a candidate exists.

| Base fact                 | Required value                             |
| ------------------------- | ------------------------------------------ |
| Repository                | `github.com/kkmia417/VNova`                |
| Base commit               | `b553fc4a4f8e50631f71e6c540337191f95366a8` |
| Git object format         | `sha1`                                     |
| Complete base-tree leaves | `41`, all regular `100644` blobs           |
| `AGENTS.md` base blob     | `e2d33c4cab3640e843f69f2cf33ea38f4e32dae4` |
| Gap-analysis base blob    | `3b97cad0692082d1e072003ea6c623137460e14e` |
| System-overview base blob | `569df03c9ee537e4bb1261dc3607de6e6043a3cf` |

The three blob identities above are the only required `M` sources. The following seven required
`A` paths are absent from the base tree:

- `.github/CODEOWNERS`;
- `.github/pull_request_template.md`;
- `docs/architecture/open-decisions.md`;
- `docs/governance/open-decision-dispositions.md`;
- `docs/governance/foundation-authority-and-bootstrap-proposal.md`;
- `docs/governance/foundation-stage-a-review-handoff.md`; and
- `docs/governance/ci-quality-gates.md`.

No other path may differ from the base. In particular,
`docs/governance/architecture-foundation-review.md` is a Stage B review-packet input, not a
Stage A source. Its current form links to architecture and governance material that is absent
from the base-plus-allowlist tree, so adding it would violate candidate dependency closure.

Local checkout settings such as `core.autocrlf`, filesystem bytes, and an excluded mutable
`.gitattributes` file cannot define candidate identity. The final committed Git blob bytes and
modes do.

### Exact `AGENTS.md` Transform

Starting from the identified base blob, make only these three edits:

1. Replace the two base bullets for `packages/contracts` and `specs/events` with exactly:

   ```markdown
   - `packages/contracts`: generated/distributed shared contract libraries plus deterministic
     contract generation, validation, and compatibility tooling; it is not the hand-authored event
     schema source.
   - `specs/events`: sole hand-authored source for versioned event JSON Schemas and event catalogs,
     including envelope and payload schemas.
   ```

2. Replace
   `The five planes are package/module boundaries, not five deployed services.` with exactly
   `Conceptual responsibility boundaries are package/module boundaries, not additional deployed services.`
3. Replace the complete base `## Runtime Implementation Gate` section with the exact contents of
   the unique `markdown` fence between
   `VNOVA-STAGE-A-AGENTS-RUNTIME-REPLACEMENT-BEGIN` and
   `VNOVA-STAGE-A-AGENTS-RUNTIME-REPLACEMENT-END` in
   `docs/governance/foundation-authority-and-bootstrap-proposal.md`. The fence and HTML marker
   lines are not copied. After LF normalization for comparison, the candidate section and fenced
   contents must be byte-equal, including the heading, list order, punctuation, and final
   newline.

All other bytes from the base `AGENTS.md` blob remain unchanged. If the proposal fence changes,
the derived `AGENTS.md`, candidate SHA, inventory, overlay, and every dependent review artifact
must be regenerated.

### Exact System-Overview Transform

Starting from the identified base blob, make one replacement only:

```diff
-The five planes are package/module boundaries, not five deployed services.
+Conceptual responsibility boundaries are package/module boundaries, not additional deployed services.
```

Every other byte remains identical to the base system-overview blob. None of the broader current
worktree overview is part of Stage A.

### Exact Gap-Analysis Transform

Starting from the identified base blob, make only the following edits.

Immediately after the base scope note ending `Items marked OPEN remain pending human decision.`,
insert the following paragraph with exactly one blank line before and after it:

```markdown
The preparation inventories below are retained from the base as historical requirements, not as a
current absence report. At the reviewed base, the overview, this gap analysis, the architecture
stubs, ADR-016, ADR-017, and ADR-018 already exist. ADR-016 and ADR-017 are Accepted; ADR-018 has
`Status: Draft, with OPEN numeric decisions`. Their presence does not satisfy the amended Runtime
Implementation Gate, and Stage A changes no ADR status.
```

In byte-boundary terms, replace
`decision.\n\n## Baseline Inferred From The Review` with
`decision.\n\n<the paragraph above>\n\n## Baseline Inferred From The Review`; the existing boundary
blank line is consumed, not retained in addition.

Replace the historical gap bullet:

```diff
-- The five planes could be misread as five deployed services.
+- The unnamed historical responsibility taxonomy could be misread as a deployed-service topology.
```

Replace binding item 13:

```diff
-13. Treat the five planes as package/module boundaries, not five deployed services.
+13. Retire the unnamed historical taxonomy. Conceptual responsibility boundaries are
+    package/module boundaries, not additional deployed services; only the explicit named
+    surfaces and packages govern implementation.
```

Each continuation line in the replacement begins with exactly four ASCII space bytes (`0x20`).

Replace the base `packages/contracts` bullet and add the canonical authored-source bullet:

```diff
-- `packages/contracts`: JSON Schema source for event envelopes and event payloads.
+- `packages/contracts`: generated/distributed shared contract libraries plus deterministic
+  contract generation, validation, and compatibility tooling; it is not the hand-authored event
+  schema source.
+- `specs/events`: sole hand-authored source for versioned event JSON Schemas and event catalogs,
+  including envelope and payload schemas.
```

Immediately below `## Unresolved OPEN Decisions`, insert the following paragraph with exactly one
blank line after the heading and exactly one blank line before existing item 1:

```markdown
The seven entries below preserve the handoff's OPEN feature questions; they are not exhaustive
repository decision authority. The [Open Decision Register](open-decisions.md) and the protected
external lifecycle defined by the
[Open Decision Disposition Register](../governance/open-decision-dispositions.md) govern decision
state. This section cannot decide, waive, or close an item.
```

In byte-boundary terms, replace
`## Unresolved OPEN Decisions\n\n1. Latency budget numbers.` with
`## Unresolved OPEN Decisions\n\n<the paragraph above>\n\n1. Latency budget numbers.`; the
existing boundary blank line is consumed, not retained in addition.

Replace everything from `## Implementation Blockers` through the end of the base blob with the
following bytes and one final LF:

```markdown
## Runtime Implementation Gate

`AGENTS.md` is the sole repository-local authority for the Runtime Implementation Gate. This gap
analysis, a review-table value, file presence, a local test pass, a pull-request merge, or an
administrator bypass cannot waive or close it.

The Retire-only Stage A candidate is limited to the exact paths, statuses, and modes in the
[Stage A governance bootstrap handoff](../governance/foundation-stage-a-review-handoff.md).
Candidate text does not select an outcome. Only separate protected external dispositions and the
effectiveness witness, ordered `OD-040 → OD-018 → OD-019`, can make the corresponding governance
amendment effective.

An effective Stage A establishes only the governance amendment. It changes no ADR status, accepts
no executable scaffold, and authorizes no runtime behavior. CODEOWNERS effectiveness still
requires post-merge parse and access verification. After the separate protected decision
projection and that ownership verification, Stage B may review the quarantined foundation
scaffold under effective base-branch controls.

The complete post-Stage-A requirement set is the amended `Runtime Implementation Gate` in
`AGENTS.md`; this summary cannot narrow it. File or directory presence is never acceptance.
Runtime implementation remains prohibited until every applicable condition has exact immutable
evidence and a protected foundation gate-closure record names only the next authorized increment.
Feature-specific ADRs and Open Decisions remain cumulative for that increment.
```

Every other byte remains identical to the base gap-analysis blob. Its older descriptions are
historical scope that Stage A intentionally does not broaden; later protected review may update
them separately.

### Derived `M` Target Identities

Applying the exact transforms above to the named base blobs with UTF-8/LF bytes and one final
newline produces:

| Candidate path                             | Bytes | Expected Git blob                          | Raw SHA-256                                                        |
| ------------------------------------------ | ----: | ------------------------------------------ | ------------------------------------------------------------------ |
| `AGENTS.md`                                |  9030 | `ec5370b50ebee30a7482962fa484850b43e0864a` | `650f58507d92a15867a6b5097cc062f2f9e8ba907a01bf9dc65e240da6695412` |
| `docs/architecture/system-overview.md`     |  4097 | `af57ab056cc16186fa5cc0139b1ebabde7f21ff4` | `843d12fd407eefdf841bf58b99c1c9a399b21bc760f3647f05d7ba536cde28ed` |
| `docs/architecture/review-gap-analysis.md` |  9936 | `5bf29ca08e004058a3380ab63503990e29c78790` | `d9aa8b679bd9d6c960f0678ef359abd56be5733ee6ff2ac1376cd90489ebcd5e` |

These are reproducible preparation assertions, not a candidate SHA, external inventory, review
receipt, or human disposition. Any source-fence or transform change requires recalculation before
freeze.

### Added-Source And Dependency-Closure Rules

The six non-CODEOWNERS additions are frozen from their protected human-reviewed Stage A versions
with all human outcome, identity, sufficiency, date, signature, and authority cells blank.
`CODEOWNERS` is the sole source whose final owner tokens cannot be prepared by an agent:

- a human repository administrator must nominate a distinct eligible non-author account;
- that account must accept collaborator access and machine evidence must show required write
  access before freeze;
- every applicable last-matching protected rule must name a satisfiable eligible owner path,
  because a later specific rule does not inherit owners from `*`; and
- the mutable one-owner proposal must not be copied into the candidate as if it passed.

Organization-team owner tokens are inapplicable to this personal repository. If repository
ownership or identity is deliberately changed to an organization, this handoff, repository
identity, access evidence, allowlist assumptions, and every dependent artifact must be
regenerated before review.

Before freeze, an external link verifier must evaluate every local Markdown link in each changed
document against the candidate Git tree. Every target must be present in the base or exact
allowlist, with fragment checks where supported. HTTP(S) references are external evidence links
and are not candidate-tree dependencies. A missing target, an excluded target, or an
unreviewed broad packet invalidates the candidate.

Effective OD-040, OD-018, and OD-019 disposition records are deliberately absent from this
allowlist. They require the frozen candidate SHA and external evidence digests and therefore
cannot be complete inside the candidate they decide. Protected reviewers may revise an exact
path or required status before freeze, but must then update this allowlist and every reference
before regenerating the inventory and pre-decision overlay. Wildcards, directory-only entries,
or an unlisted decision attachment are not permitted.

## Required Stage A Semantic Assertions

Path/status equality is necessary but not sufficient. Protected review and the pre-decision
overlay must also prove:

- `AGENTS.md` contains the exact human-selected gate and contract-source amendments and replaces
  the unnamed five-plane sentence with the Retire wording;
- the existing system overview no longer treats the absent five-plane taxonomy as unresolved and
  instead relies only on explicit named responsibilities and dependency directions;
- the gap analysis projects that same outcome without importing unrelated mutable-worktree edits;
- the OD register and disposition lifecycle define OD-040/018/019 while every repository summary
  outcome, identity, date, approval, and effective-authority cell remains blank;
- CODEOWNERS names human-approved individual GitHub accounts with accepted collaborator/write
  access, owns itself, and has a satisfiable non-author review path; the current one-owner mutable
  proposal does not satisfy this assertion;
- every local Markdown link in a changed Stage A document resolves to a path present in the
  candidate tree, and every linked path absent from the base is itself in the exact allowlist;
- no ADR status/text, workflow, toolchain, scaffold, runtime, provider, prompt, policy, migration,
  adapter, infrastructure, or production behavior changes; and
- every retained OPEN or feature-gated capability remains explicitly disabled.

A machine can verify text predicates, links, and path facts, but only eligible humans decide that
the wording, owners, sufficiency, risks, and retained scope are correct.

## Explicit Stage A Diff Exclusions

Any Stage A change matching this table invalidates the candidate. Do not delete or move those
paths from the shared worktree to simulate a split; construct Stage A in a fresh clone or
separate Git worktree rooted at the revalidated base.

| Excluded change set                                                                                                           | Reason                                                                                      |
| ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `.github/workflows/**` and `.github/actions/**`                                                                               | Executable CI belongs to Stage B after governance ownership is effective                    |
| `packages/**`, `specs/**`, `tests/**`, and `tooling/**`                                                                       | Contract, safety, schema, test, and enforcement evidence belongs to the quarantined Stage B |
| `.editorconfig`, `.gitattributes`, `.importlinter`, `.node-version`, `.npmrc`, `.prettierignore`, `.python-version`           | Root toolchain/configuration evidence is not part of Stage A                                |
| `dependency-cruiser.config.mjs`, `eslint.config.mjs`, `package.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml`                 | Executable JavaScript/TypeScript toolchain and lock state belongs to Stage B                |
| `prettier.config.mjs`, `pyproject.toml`, `tsconfig.base.json`, `uv.lock`                                                      | Executable formatter/type/test/package configuration and lock state belongs to Stage B      |
| `.gitignore`                                                                                                                  | The existing unrelated mutable change is not required for governance bootstrap              |
| `docs/adr/**`                                                                                                                 | Stage A changes no ADR status or decision text                                              |
| Any architecture, governance, security, runbook, or root document not listed in the exact allowlist                           | Prevents the broad mutable documentation set from entering the bootstrap accidentally       |
| `apps/**`, `deploy/**`, `infra/**`, migrations, provider gateways, prompts, personas, policies, secrets, or production config | Feature/runtime/production implementation remains forbidden                                 |
| Generated archives, build output, caches, virtual environments, logs, editor state, or temporary evidence                     | Ephemeral output is not source and must remain outside the candidate                        |

An excluded path may already exist unchanged in the base tree. The exclusion forbids a Stage A
diff; it does not rewrite the authority of unchanged base content.

## Non-Self-Referential Review Package

The protected review package has six separately attributable artifacts: a machine inventory, a
pre-decision semantic overlay, a frozen review-package manifest, final external disposition
attestations, an effectiveness witness, and a later repository projection. A joined user
interface may display them together but must preserve each producer, digest, authority, and
effective order.

### Machine Inventory

External read-only tooling generates the inventory from the immutable candidate Git tree. It
contains no approval state and must include:

- the exact `vnova.git-tree-inventory/v1` format and canonicalization rules below;
- repository identity, Git object format, base SHA, and candidate SHA;
- one entry for every candidate-tree regular-file leaf, sorted by exact Git path bytes;
- Git mode, blob object ID, raw-byte SHA-256, and byte length;
- the exact changed-path set relative to the base;
- a separate provenance envelope with acquisition tool identity/version and collection time; and
- the canonical-payload SHA-256 plus external storage/attestation identity.

Stage A v1 accepts only regular `100644` blobs. An executable, symlink, gitlink, tree-entry
inventory, or other mode requires a revised handoff and format review; it must not be silently
coerced into this format.

#### Canonical Inventory Payload v1

The canonical payload is RFC 8785 JSON Canonicalization Scheme output encoded as UTF-8 without a
BOM or trailing newline. Every scalar is a JSON string; there are no JSON numbers. Git path bytes
are represented as unpadded Base64url in `path_b64u` and are sorted by their decoded unsigned byte
sequence, not by the encoded text. Object IDs and digests use lowercase hexadecimal. Byte lengths
use canonical decimal strings (`0` or a non-zero digit followed by digits).

The top-level object has exactly:

- `format`: `vnova.git-tree-inventory/v1`;
- `repository`: exact ASCII `github.com/kkmia417/VNova`;
- `git_object_format`: `sha1` for this Stage A base; another format requires a revised handoff;
- `base_commit` and `candidate_commit`: full lowercase object IDs;
- `tree`: entries containing exactly `path_b64u`, `mode`, `blob_oid`, `raw_sha256`, and
  `byte_length`; and
- `changes`: entries containing exactly `path_b64u`, `status`, `base_mode`, `base_blob_oid`,
  `candidate_mode`, and `candidate_blob_oid`.

For `M`, both base and candidate fields are present and use mode `100644`. For `A`, both base
fields are the empty string. `tree` and `changes` are each sorted by decoded raw path bytes and
contain no duplicate path. Stage A rejects `D`, rename/copy detection, type changes, and every
other status, so no deletion or rename record is representable in v1. A future format that admits
them must define base-side path/object records explicitly and receive protected review.

The inventory digest is:

```text
SHA-256(ASCII("VNOVA-FOUNDATION-TREE-INVENTORY") || 0x00 || ASCII("v1") || 0x00 || canonical_payload_bytes)
```

The canonical payload excludes its own digest, collector identity, collection time, attestation,
and storage URI. A separate provenance envelope binds those facts to the payload digest and is
stored outside the candidate tree. This separation makes the payload deterministic without
discarding acquisition provenance.

### Pre-Decision Semantic Overlay

The protected pre-decision overlay references the exact candidate SHA and inventory digest, then
records for each changed path:

- documentation/proposal, governance stub, protected evidence, executable enforcement, or
  forbidden-runtime category;
- executable behavior;
- governing `AGENTS.md`/ADR/OD/owner authority;
- data and safety impact;
- validation evidence references;
- required-revision findings; and
- a retained-disabled-scope proposal.

It contains no final `Accept`/`Revise`/`Reject` disposition, approval event or sufficiency claim,
reviewer eligibility judgment, decision/effective time, risk acceptance, or final review evidence
ID. Those fields belong only to the outer disposition attestations. An overlay cannot cite the
approval that approves its own digest.

Its canonical payload uses RFC 8785 and unpadded Base64url path bytes as above. The top-level
object contains exactly `format` (`vnova.predecision-overlay/v1`), `candidate_commit`,
`inventory_digest`, and `entries`. Each entry contains exactly:

- `path_b64u`;
- `category`, exactly one of `documentation_proposal`, `governance_stub`,
  `protected_evidence`, `executable_enforcement`, or `forbidden_runtime`;
- `executable_behavior`;
- `governing_authority`;
- `data_safety_impact`;
- `validation_references`;
- `required_revisions`; and
- `disabled_scope_proposal`.

Every field except `path_b64u` and `category` is an array of Unicode NFC strings whose
human-approved order is preserved; duplicates are forbidden. `required_revisions` may be empty;
every other semantic array has at least one explicit value, using `none` only as a reviewed
semantic statement rather than an omitted field. `entries` covers every allowlisted changed path
exactly once and is sorted by decoded path bytes. There are no JSON numbers, booleans, or nulls.
Its digest is:

```text
SHA-256(ASCII("VNOVA-FOUNDATION-PREDECISION-OVERLAY") || 0x00 || ASCII("v1") || 0x00 || canonical_payload_bytes)
```

The protected system stores overlay authorship/freeze provenance in a separate receipt. Agents
may prepare a blank overlay and non-binding recommendations. Only eligible humans may finalize
its semantic assessment, and that act still does not decide an OD or approve the candidate.

### Frozen Review-Package Manifest

After the PR and non-author approval event are fixed, an external protected manifest binds:

- repository, base/candidate SHA, target branch, PR URL/head, and exact diff identity;
- machine-inventory payload and receipt digests;
- pre-decision-overlay payload and receipt digests;
- temporary-rule, validation, account/access, and approval-event evidence IDs/digests; and
- the manifest format/version and explicit absence of any final disposition/effective-state
  claim.

The manifest is frozen before final disposition signing. Its signed payload excludes its own
digest/URI and all later attestation/witness/projection IDs; an external immutable receipt
supplies the manifest ID, digest, signature/attestation identity, and URI. A changed prerequisite
creates a new manifest and invalidates dependent review.

### Final External Disposition Attestations

After the exact PR head, machine inventory, pre-decision overlay, temporary rule, validation
evidence, access facts, and non-author approval event exist, accountable humans create three
separate protected attestations outside the candidate tree:

1. OD-040 genesis, effective order `0`;
2. OD-018 Retire, effective order `1` and conditional on OD-040 effectiveness; and
3. OD-019 amendment, effective order `2` and conditional on OD-018 effectiveness.

Each attestation binds the frozen review-package-manifest ID/digest, repository, base/candidate
SHA, PR/head, inventory digest, overlay digest, approval-event facts, accountable human
identities/roles, independent-review judgment, explicit outcome, normative statement, retained
disabled scope, validation sufficiency/freshness, applicable risk decision, invalidation rules,
and effective condition. Its frozen payload receives separately attributable accountable-human
and eligible non-author review signatures in the protected-system receipt. A single omnibus
approval or one signature over three undifferentiated outcomes is not three decisions.

The signed attestation payload records the selected outcome and intended transition but does not
claim that transition is already effective. It also does not contain its own digest, storage URI,
or later projection commit. The protected system's immutable receipt supplies the record ID,
digest, signature/attestation identity, and URI outside that payload. The Stage A source changes
are authorized for merge by the pre-existing genesis authorities. The actual lifecycle state
remains `OPEN` until an external append-only witness payload binds exactly:

- repository, base SHA, candidate/merged SHA, target branch, merge-event ID, and merge UTC time;
- the frozen review-package-manifest ID/digest;
- each OD ID and disposition receipt ID/digest;
- each predecessor receipt ID/digest or explicit `none`;
- effective order `0`, `1`, or `2`, effective-condition ID, observed condition result, and
  witnessed effective UTC time; and
- the derived lifecycle state for each record and any predecessor it supersedes.

The witness payload excludes its own digest/URI; an external immutable receipt supplies them.
Any source, overlay, manifest, attestation payload, or required signature change invalidates the
dependent approval/receipt and requires the affected review again.

### Later Repository Projection

After Stage A merges and CODEOWNERS/access are verified on `main`, a separate protected
projection PR may add only:

- `docs/governance/decisions/od-040-genesis.md`;
- `docs/governance/decisions/od-018-five-plane-taxonomy.md`;
- `docs/governance/decisions/od-019-runtime-gate-authority.md`; and
- the corresponding summary rows in `docs/governance/open-decision-dispositions.md`.

Those files mirror the external records and receipts; they are not the source of initial
effectiveness. The projection commit cannot contain its own SHA. An external append-only witness
records that SHA after merge. Stage B cannot start until this projection and its protected review
are complete.

## Machine-Fact Worksheet

Machine facts may be collected only after the candidate is immutable. A system may report a fact
or `missing`/`not_collected`; it may not infer human eligibility, sufficiency, or outcome.

| Evidence field                              | Machine producer/source                  | Final candidate value |
| ------------------------------------------- | ---------------------------------------- | --------------------- |
| Repository                                  | GitHub/review system                     |                       |
| Base commit SHA                             | Git                                      |                       |
| Candidate/reviewed-subject commit SHA       | Git                                      |                       |
| Exact path/status/mode allowlist result     | External inventory verifier              |                       |
| Full-tree inventory URI and payload digest  | External artifact/attestation system     |                       |
| Pre-decision overlay URI and payload digest | Protected artifact system                |                       |
| Frozen review-package manifest ID/digest    | Protected artifact system                |                       |
| Governance bootstrap PR URL/head SHA        | GitHub                                   |                       |
| Temporary rule export/URL and digest        | Repository administrator/repository API  |                       |
| Non-author approval event ID/time/head SHA  | Protected review system                  |                       |
| Reviewer account/access/role facts          | Repository administrator/repository API  |                       |
| Stale-review dismissal event facts          | GitHub/repository rule                   |                       |
| Merge event and exact merged SHA            | GitHub                                   |                       |
| Post-merge CODEOWNERS parse/access facts    | GitHub/repository API                    |                       |
| Disposition receipt IDs/digests             | Protected attestation system             |                       |
| Effectiveness witness ID/digest/order/times | External append-only witness             |                       |
| Projection PR/commit/merge facts            | GitHub plus external append-only witness |                       |

## Protected Human Evidence And Decisions

Every cell below is human-owned and remains blank in agent-authored copies.

| Human field                              | Accountable authority                               | Final decision |
| ---------------------------------------- | --------------------------------------------------- | -------------- |
| Pre-decision overlay semantic assessment | Eligible architecture/repository/domain humans      |                |
| Reviewer eligibility and quorum judgment | Repository administrator and governance authorities |                |
| Non-author approval sufficiency          | Protected review authority                          |                |
| OD-040 outcome and genesis authority     | Eligible repository/architecture/governance humans  |                |
| OD-018 Retire outcome                    | Eligible architecture/repository humans             |                |
| OD-019 amendment outcome                 | Eligible architecture/repository humans             |                |
| Validation sufficiency/freshness         | Applicable accountable humans                       |                |
| Security/privacy/residual-risk decision  | Applicable eligible human authorities               |                |
| Effective order and condition            | Protected decision authorities                      |                |
| Effectiveness-witness sufficiency        | Protected decision authorities                      |                |

An unavailable fact is recorded as `not_collected`, `missing`, or `not_applicable` with a reason.
It is never converted to `passed`, `accepted`, or `closed`.

## Review And Freeze Sequence

1. Create a fresh clone or separate Git worktree at the revalidated base SHA. Before applying any
   change, require `git status --porcelain=v1 -uall` to return no output. Verify the intended PR
   base and repository identity; do not use a new branch in the mixed shared checkout.
2. Protected humans direct the exact OD-040 lifecycle proposal, OD-018 Retire wording, OD-019
   amendment, and eligible CODEOWNERS proposal. These source choices are not yet effective
   dispositions.
3. Apply only the exact allowlisted paths/statuses/modes. Leave the repository disposition
   summary and all human decision tables blank.
4. Commit the candidate, require the isolated worktree (including untracked files) to be clean,
   verify the reviewed base is its ancestor, and freeze the candidate SHA. Any later byte change
   creates a new candidate and restarts the evidence sequence.
5. Generate the full external machine inventory from that Git tree. Verify repository identity,
   ancestry, every regular-file leaf, and exact path/status/mode equality with the allowlist.
6. Finalize and digest the pre-decision semantic overlay bound to that candidate and inventory.
7. Open the governance PR and durably record its exact head/diff, temporary rule, validation,
   access/role facts, and external artifact receipts.
8. Obtain an eligible non-author approval event for that exact head and the available prerequisite
   evidence set. Source or overlay changes stale it.
9. Freeze the external review-package manifest over every prerequisite fact and artifact receipt.
10. Create and separately counter-review the three external protected disposition attestations in
    effective order `OD-040 → OD-018 → OD-019`. Merge only after their receipts/signatures and
    outcomes authorize the exact source and all temporary-rule requirements hold.
11. Record the exact merge and ordered lifecycle transitions in the external append-only
    effectiveness witness. Re-read CODEOWNERS
    from `main`, verify every owner has required access and protected paths resolve, then complete
    the separate decision-projection PR before Stage B.

PowerShell revision and isolation checks quote revision expressions explicitly:

```powershell
$stageABase = "<base-sha>"
$stageACandidate = "<candidate-sha>"
git rev-parse --verify "$stageABase^{commit}"
git rev-parse --verify "$stageACandidate^{commit}"
git merge-base --is-ancestor $stageABase $stageACandidate
git status --porcelain=v1 -uall
git diff --check "$stageABase..$stageACandidate"
```

A trusted collector invokes Git as argument vectors and consumes stdout as bytes, not decoded
PowerShell text:

```text
["git","diff","--raw","-z","--no-renames",base,candidate,"--"]
["git","diff","--name-status","-z","--no-renames",base,candidate,"--"]
["git","ls-tree","-r","--full-tree","-z",candidate]
["git","cat-file","--batch"]
```

Rename/copy detection is pinned off. The collector joins raw diff records with base/candidate
blob metadata and independently verifies the candidate tree; it must not parse quoted
human-readable path output. These primitives do not by themselves provide canonical JSON,
SHA-256 entries, semantic classification, attestation, human eligibility, or approval. The
collector must be reviewed and run outside the candidate until Stage B authorizes
repository-local inventory tooling.

## Invalidation Conditions

The Stage A evidence is invalid if:

- the base or candidate SHA changes;
- any candidate path is missing from the full inventory;
- the changed path, status, or mode differs from the exact allowlist;
- an excluded path changes;
- the inventory or pre-decision-overlay digest cannot be reproduced;
- the pre-decision overlay refers to another candidate or inventory;
- an overlay contains its own approval or final disposition evidence;
- the frozen review-package manifest omits or mismatches a prerequisite receipt;
- `AGENTS.md`, OD records, review packet, and CODEOWNERS describe different outcomes;
- the current single-owner CODEOWNERS proposal is used without an eligible non-author path;
- the PR head changes without refreshed evidence and approval;
- the OD-040, OD-018, and OD-019 external records are absent, combined, or effectively reordered;
- the temporary rule, reviewer access, or review evidence is absent or inapplicable;
- any human decision cell is populated by an agent; or
- Stage A is represented as accepting the executable scaffold or authorizing implementation.

## Exit And Next Increment

Stage A succeeds only when its immutable evidence and protected human records are complete and the
governance change is merged. Stage A success:

- establishes the authority and ownership needed to review Stage B;
- does not close the Runtime Implementation Gate;
- does not accept the executable contract/safety/schema/toolchain/CI scaffold;
- does not accept a feature ADR or Open Decision beyond the exact Stage A records; and
- does not authorize runtime implementation.

The next permitted increment is the separately protected decision-projection PR described above.
Only after that projection and post-merge ownership evidence are complete may a separate Stage B
foundation-scaffold candidate be reviewed under the now-effective base-branch CODEOWNERS and
repository rules. Runtime implementation remains blocked until the full foundation gate and
applicable feature gates close.
