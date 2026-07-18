# Architecture Foundation Review Packet

Status: Proposed Stage B review design; excluded from the Stage A candidate; immutable candidate
and bootstrap prerequisites are still missing

This broad packet depends on architecture and governance sources outside the Stage A allowlist.
It may inform later review, but it must not be copied into the Retire-only Stage A candidate.

This packet is the decision surface for closing VNova's architecture-foundation gate. It does not
mark any proposal accepted. A human reviewer records `Accept`, `Revise`, or `Reject` for each
artifact and an explicit selected outcome/full disposition record for each Open Decision, then
names the approving role or person.

## Required Decisions

| Artifact                                                                             | Decision requested                                                                       | Acceptance focus                                                                                                                                                                                                | Current status |
| ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| [ADR-001](../adr/0001-monorepo-and-deployment-boundaries.md)                         | Accept, revise, or reject                                                                | Four deployed surfaces, package boundaries, ownership, and future extraction criteria                                                                                                                           | Proposed       |
| [ADR-002](../adr/0002-contract-source-and-code-generation.md)                        | Accept, revise, or reject                                                                | Canonical schema/generation, compatibility, typed event scope, non-event source, UUID, timestamp, Unicode, numeric, and JSON resource-profile semantics                                                         | Proposed       |
| [ADR-023](../adr/0023-event-subject-scope-correlation-and-ordering.md)               | Accept with ADR-002, revise, or reject and provide a compatible replacement              | One v2 envelope, immutable profile/separate catalog lifecycle, typed scope/subject, per-version zero/event manifest completeness, trusted framing, monotonic protection overlay/effect validation, and recovery | Proposed       |
| [ADR-008](../adr/0008-safety-gate-enforcement.md)                                    | Accept, revise, or reject                                                                | Exclusive approval minting, identifier-only media, fail-closed chain, expiry, and signed dispatch                                                                                                               | Proposed       |
| [ADR-018](../adr/0018-latency-budget-and-streaming-strategy.md)                      | Accept structural clauses, revise, or reject                                             | Full-response safety, non-extensible expiry, timeout/late-result behavior, raw/derived clock evidence, and independent SLO/deadline semantics; numeric profiles may remain OPEN                                 | Proposed       |
| [System overview](../architecture/system-overview.md)                                | Confirm or request revision                                                              | Responsibility, trust, data, and deployment boundaries                                                                                                                                                          | Draft          |
| [Gap analysis](../architecture/review-gap-analysis.md)                               | Accept handoff-derived baseline or require original source                               | Whether OD-008 is closed without the missing historical design                                                                                                                                                  | Pending        |
| [`AGENTS.md` runtime gate authority](foundation-authority-and-bootstrap-proposal.md) | Apply/revise the exact protected amendment, or reject and keep the scaffold blocked      | Resolve the conflict between the pre-gate edit allowlist and the executable foundation evidence; align the authoritative gate with exact-subject review requirements                                            | Pending        |
| [`VNOVA-FOUNDATION-STAGE-A-HANDOFF-v1`](foundation-stage-a-review-handoff.md)        | Confirm/revise the exact governance-bootstrap change set before freezing a candidate     | Retire-only Stage A path/status/mode allowlist, exclusions, non-recursive evidence layers, human-only fields, invalidation, and no runtime authority                                                            | Proposed       |
| [Open decision disposition lifecycle](open-decision-dispositions.md)                 | Ratify/revise OD-040 through its one-time genesis rule, or reject and keep every OD OPEN | Eligible authority/quorum, immutable reviewed subject, inventory/pre-decision-overlay/final-attestation separation, effective order, non-author review, supersession, and invalidation                          | Pending        |

## Current Scaffold Authority

`AGENTS.md` requires safety, contract, and event-schema skeletons before runtime work, but its
pre-gate edit allowlist does not authorize the executable foundation implementation that now
exists: contract validation/code generation/packaging, artifact verification, boundary analyzers,
tests, lockfiles, and CI in addition to package/schema placeholders. This packet cannot
self-authorize an exception to the repository's authoritative instructions.

Until a human records a decision, treat `packages/contracts`, `packages/safety`, `specs/events`,
root toolchain/lockfiles, tests, tooling, and the executable CI baseline as quarantined review
evidence: they do not activate a runtime capability, they must not be merged as compliant
foundation work without protected review, and they do not authorize feature implementation.
OD-019 tracks the required authoritative change. A decision-table acknowledgement alone cannot
permanently fix the literal allowlist; the
[authority and bootstrap proposal](foundation-authority-and-bootstrap-proposal.md) supplies exact
non-self-authorizing amendment text and the two-stage review ceremony.
The
[`VNOVA-FOUNDATION-STAGE-A-HANDOFF-v1`](foundation-stage-a-review-handoff.md)
selection ledger identifies the only permitted Stage A diff paths and explicitly excludes the
mixed executable worktree.

## Review Checklist

- The system is treated as a real-time broadcast control system, not a chatbot/avatar integration.
- `stage-host` remains mandatory and is the sole `SpeechTask` consumer.
- `CandidateResponse` and `ApprovedResponse` remain separate; only `packages/safety` can mint approval.
- TTS, media, and dispatch boundaries accept identifiers rather than generated text.
- PostgreSQL is the system of record; Redis is transport and never the recovery source.
- Viewer memory and audit data remain structurally and access-control separated.
- Every fallback path crosses the same safety gate, and missing safety state fails closed.
- No OPEN number, provider, retention period, cryptographic profile, or deployment target is treated as an approved default.
- ADR-002's provisional JSON profile is explicitly reviewed: depth `64` with the root container at depth `1`, value-node count `10000`, combined UTF-8 key/string bytes `1048576`, Unicode scalar strings, and negative-zero normalization.
- ADR-002 cannot be accepted while the mandatory session envelope conflicts with required
  environment/talent/viewer-scoped events, while OD-017 leaves event compatibility/deprecation
  unresolved, or while OD-021 leaves non-event command contracts without one canonical source.
- ADR-023 cannot be accepted while OD-017 or OD-033 remains OPEN or lacks a valid closure-capable
  disposition. ADR-002 and ADR-023 describe one compatible event-contract model for the same
  immutable reviewed subject.
- OD-033 records the immutable event-contract profile and separate monotonic catalog lifecycle,
  catalog-fixed typed scope/subject, `(aggregate_version, event_index)` plus a manifest for every
  aggregate version and consumer high-water completeness, trusted envelope-version framing, and
  typed monotonic protection-overlay epoch/partition-high-water/effect-boundary outcome; producers
  never invent a session identity, infer a version from shape, or rely on an untyped optional
  scope.
- OD-040 is ratified first through its one-time genesis rule; every later OD outcome links a full
  disposition record for the exact immutable reviewed subject.
- Protected paths have named reviewers and the repository Ruleset will require `ci-required` before feature code merges.
- The exact candidate SHA and every path/blob fact are captured in the external machine
  inventory; the separately attributable pre-decision semantic overlay records behavior,
  authority, impact, required revisions, and proposed disabled scope; final disposition and
  effectiveness remain separate external records; no feature/runtime implementation is present.

## Evidence Available

The repository provides deterministic contract generation, shared Python/TypeScript fixtures, canonical scalar and resource-profile parity tests, strict type and lint gates, import and dependency boundaries, CI policy mutation tests, cross-platform workflow definitions, archive allowlists, archive integrity checks, and isolated package smoke tests.

Local evidence is produced by:

```powershell
corepack pnpm run verify
corepack pnpm run artifacts:verify
git status --short
```

Remote GitHub Actions evidence, an immutable candidate commit/PR, an effective base-branch
CODEOWNERS file, the branch Ruleset, and a deliberately failing negative-control PR remain
pending. A local pass is not a substitute for protected human review. The
[authority and bootstrap proposal](foundation-authority-and-bootstrap-proposal.md) records the
verified point-in-time repository state and required evidence matrix. The
[`VNOVA-FOUNDATION-STAGE-A-HANDOFF-v1`](foundation-stage-a-review-handoff.md)
separates its exact governance-only change set, external machine inventory, pre-decision semantic
overlay, final external attestations, and human-only decision fields.

## Machine Facts Index

This index reports observable facts and missing evidence. It is not an approval table. Tooling and
external systems may populate candidate-bound evidence IDs only after an immutable candidate
exists; they may report `not_collected` or `missing`, but never human eligibility, sufficiency,
`Accepted`, `DECIDED`, or gate closure.

| Evidence item                         | Producer/source                       | Current fact                                                        | Required durable evidence                                                            |
| ------------------------------------- | ------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Stage A change-set handoff            | Repository documentation              | `VNOVA-FOUNDATION-STAGE-A-HANDOFF-v1`; proposed and non-authorizing | Exact handoff ID and candidate-bound path/status/mode verification                   |
| Base and candidate SHA                | Git/review system                     | Base observed; candidate missing                                    | Exact immutable base/candidate pair and ancestry fact                                |
| Full candidate-tree machine inventory | External collector/attestation system | Contract specified; artifact missing                                | Every path/mode/blob/SHA-256/size, change records, URI, digest, and attestation      |
| Pre-decision overlay receipt          | Protected artifact system             | Blank structure specified; artifact missing                         | Candidate/inventory-bound URI, digest, authoring/freeze receipt                      |
| Frozen review-package manifest        | Protected artifact system             | Contract specified; artifact missing                                | Exact prerequisite IDs/digests, immutable receipt, and no outcome/self-reference     |
| Governance bootstrap PR               | GitHub                                | Missing                                                             | PR URL, final head SHA, review diff, approval/merge event IDs                        |
| Foundation scaffold PR                | GitHub                                | Missing                                                             | Separate Stage B PR after projection and effective Stage A ownership                 |
| Local validation                      | Exact candidate checkout              | Prior mutable-worktree runs are diagnostic only                     | Commands/results bound to the final candidate SHA                                    |
| Remote Linux/Windows `ci-required`    | GitHub Actions                        | No run for the current base/candidate                               | Successful run/job/check IDs on the final Stage B candidate                          |
| Ruleset                               | Repository administration/API         | No durable export or URL recorded                                   | Exact export/URL, scope, digest, required check, and effective state                 |
| Negative-control PR                   | GitHub plus Ruleset                   | Missing                                                             | Deliberately failing candidate proven unable to merge                                |
| Reviewer account/access/role facts    | Repository administration/API         | Not collected/proven                                                | Exact accounts, roles, access levels, source scope, collection time, and evidence ID |
| Base-branch CODEOWNERS parse/access   | GitHub/repository administration      | Missing on base; mutable proposal has one owner only                | Post-Stage-A parse, access, protected-pattern, and non-author-path facts             |
| Disposition/effectiveness receipts    | Protected attestation/witness systems | Missing                                                             | Three ordered receipt IDs/digests plus exact-merge witness state/times               |
| Decision-projection PR/merge          | GitHub plus append-only witness       | Missing                                                             | Protected projection review, exact commit/merge facts, and external witness          |

## Protected Human Evidence Requirements

These are human judgments or decisions, not machine-index rows. A tool may expose supporting
facts or artifact receipts but may not populate the outcome.

| Human evidence/decision                  | Accountable authority                           | Current state |
| ---------------------------------------- | ----------------------------------------------- | ------------- |
| Stage A Retire-only scope acceptance     | Architecture/repository authorities             |               |
| Pre-decision overlay semantic assessment | Eligible architecture/repository/domain humans  |               |
| Reviewer eligibility and quorum          | Repository administrator/governance authorities |               |
| Non-author approval sufficiency          | Protected review authority                      |               |
| OD-040, OD-018, and OD-019 outcomes      | Each OD's eligible accountable humans           |               |
| Effective order and condition            | Protected decision authorities                  |               |
| Effectiveness-witness sufficiency        | Protected decision authorities                  |               |
| Validation sufficiency/freshness         | Applicable accountable humans                   |               |
| Security/privacy/residual-risk decision  | Applicable eligible human authorities           |               |

## Gate Outcome

Runtime feature code remains blocked until:

1. Eligible humans ratify OD-040 through its one-time protected genesis rule and record the
   immutable disposition lifecycle.
2. A human resolves OD-019 by applying or revising the protected `AGENTS.md` amendment and its
   contract-source/five-plane companion edits; a
   review-table ruling without authoritative text change is insufficient.
3. ADR-001, ADR-002, ADR-008, ADR-023, and the structural scope of ADR-018 are accepted or
   replaced.
4. OD-008, OD-017, OD-018, OD-019, OD-020, OD-021, and OD-033 have valid `DECIDED`,
   closure-capable dispositions. `Deferred`, `Inconclusive`, `OPEN`, `INVALIDATED`, missing, or
   `Rejected` without an Accepted replacement keeps the foundation blocked. OD-017/021/033 must
   satisfy this before ADR-002 acceptance or contract activation. OD-017/033 must also satisfy
   this before ADR-023 acceptance, and ADR-002 and ADR-023 must remain one compatible reviewed
   model.
5. Any later Open Decision whose registered `Blocks` scope includes a foundation artifact,
   acceptance of a foundation ADR, or foundation gate closure also has a valid `DECIDED`,
   closure-capable disposition; the fixed list above is not a bypass for future blockers.
6. The system overview and gap-analysis baseline are approved, including explicit OD-008 source
   provenance and OD-018 restore/retire disposition.
7. OD-020 either recovers historical ADR-006 or explicitly reserves/remaps the known dependency.
8. A complete external machine inventory generated from the immutable candidate Git tree,
   separately attributable pre-decision semantic overlay, frozen review-package manifest, final
   protected disposition attestations, and effectiveness witness bind every reviewed artifact
   without self-reference and prove feature/runtime implementation is absent.
9. CI has passed remotely on the final candidate SHA and `ci-required` is enforced by an exported
   repository Ruleset.
10. CODEOWNERS is effective on the base branch and at least one eligible non-author human can
    satisfy the agreed protected review policy.
11. A negative-control PR proves a failing required check cannot merge.
12. The Stage A external decisions have been mirrored through a separate protected projection PR;
    the projection does not claim its own SHA or replace the external authority.

Numeric latency targets, retention durations, provider selections, stage-host language, and cryptographic parameters may remain OPEN if the accepted ADR explicitly keeps their dependent implementation disabled.

Closing this foundation gate authorizes only the next increment whose own entry gates are
satisfied. It does not accept or waive ADR-003, ADR-004, ADR-007, ADR-010, ADR-011, ADR-015,
ADR-019, ADR-020, ADR-021, ADR-022, ADR-024, ADR-025, ADR-026, or any future migration ADR. The
[implementation roadmap](../architecture/implementation-roadmap.md) and
[feature-specific gate table](../architecture/review-gap-analysis.md#feature-specific-adr-gates)
remain binding for later capabilities.

Those feature ADRs now exist as non-binding review proposals. Their dependency order, cross-ADR
invariants, acceptance evidence, and decision rows are collected in the
[feature architecture review packet](feature-architecture-review.md). The historical ADR-006
reference remains unresolved under OD-020; the new proposals do not silently impersonate or
reconstruct it.

If ADR-002 is accepted, that decision also accepts or explicitly revises its canonical UUID/timestamp forms, Unicode and negative-zero rules, numeric-value parity semantics, and JSON resource ceilings. The same protected review must update the repository-responsibility wording in `AGENTS.md` to say explicitly that `specs/events` is the sole hand-authored event-schema and event-catalog source and `packages/contracts` is the generated distribution and tooling boundary. Until then, the checked-in contract scaffold and profile are provisional review-supporting evidence, not acceptance of the proposal.

## Human Decision Record

Every outcome, reviewer, date, sufficiency judgment, and authority cell below is human-owned.
Machine evidence belongs in the index above and is referenced here only after protected humans
judge it sufficient and fresh.

| Item                                           | Selected outcome / Accept / Revise / Reject | Reviewer | Date | Evidence or required follow-up                                                       |
| ---------------------------------------------- | ------------------------------------------- | -------- | ---- | ------------------------------------------------------------------------------------ |
| OD-040 genesis/disposition lifecycle           |                                             |          |      | External record, reviewed SHA, inventory, pre-decision overlay, non-author review    |
| `AGENTS.md` gate / OD-019                      |                                             |          |      |                                                                                      |
| OD-008 baseline provenance                     |                                             |          |      | Exact source/digest, limitations, and explicit revision record                       |
| OD-018 five-plane restore/retire               |                                             |          |      | Do not confuse with ADR-018 latency                                                  |
| ADR-001                                        |                                             |          |      |                                                                                      |
| ADR-002                                        |                                             |          |      |                                                                                      |
| ADR-023                                        |                                             |          |      | Same immutable event-model subject as ADR-002/OD-017/OD-033                          |
| OD-017 compatibility/deprecation               |                                             |          |      | Disposition record ID; ADR-002 remains blocked while OPEN                            |
| OD-021 non-event contract source               |                                             |          |      | Dependent protocols remain disabled                                                  |
| OD-033 event identity/scope/order/completeness |                                             |          |      | No invented session identity, structural version inference, or incomplete projection |
| ADR-008                                        |                                             |          |      |                                                                                      |
| ADR-018 structural scope                       |                                             |          |      |                                                                                      |
| OD-020 / historical ADR-006                    |                                             |          |      | Recover or explicitly reserve/remap known dependency                                 |
| System overview and gap analysis               |                                             |          |      |                                                                                      |
| Protected ownership policy                     |                                             |          |      | Named owners and approval rule                                                       |
| Mechanical evidence sufficiency/freshness      |                                             |          |      | Human judgment over the complete evidence index                                      |
| Overall foundation gate outcome                |                                             |          |      | Closed only after every required row is accepted and evidenced                       |
