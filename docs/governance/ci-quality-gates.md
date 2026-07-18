# CI Quality Gates And Repository Rules

Status: Proposed non-executable Stage A CI and repository-rule design; Stage B executable
evidence, remote execution, human review, and repository rules pending

This document supplies the pre-implementation CI and repository-rule design. No workflow,
toolchain, package, schema, test, or executable enforcement file is part of the Stage A candidate.
A separate Stage B candidate may contain the quarantined executable baseline; it must be reviewed
on its exact SHA under effective repository controls before any result becomes authority.

## Current Quarantined Stage B Evidence

The current mutable Stage B scaffold implements a narrow, non-authorizing subset of this plan:

- `tooling/ci/check_workflows.py` rejects duplicate YAML keys, writable permissions,
  `pull_request_target`, unpinned external actions, persisted checkout credentials, missing
  timeouts, `continue-on-error`, and an aggregate check that does not fail closed;
- the canonical `ci.yml` contract additionally requires exactly the `push`, `pull_request`,
  `merge_group`, and `workflow_dispatch` triggers, an unfiltered `main` push, exact
  Ubuntu 24.04/Windows 2025 matrices driven by `matrix.os`, fail-fast disabled, the exact quality
  and artifact entrypoints running unconditionally under default run semantics, and a
  least-privilege `ci-required` job depending on quality, artifacts, and security;
- the `security` job pins Gitleaks v3, Dependency Review v5, and CodeQL v4 by immutable commit,
  disables Gitleaks comments/artifact upload, fixes the scanner version, runs dependency review on
  pull requests, and analyzes Python plus JavaScript/TypeScript with the extended security query
  suite;
- mutation tests remove or weaken each of those structural requirements; and
- the CI self-check pins the root `verify`, artifact, contract, format, lint, typecheck, test, and
  self-check script wiring; the root lint entrypoint invokes both architecture guards and the CI
  self-check directly rather than relying only on a pytest discovery side effect.

This is local technical evidence only. The governance semantic gate, protected-path
classification, remote security execution, remote quality/artifact matrices, negative-control
PR, Ruleset, and protected human acceptance remain absent. In particular, the local structural
self-check cannot prove that GitHub-hosted secret scanning, dependency review, or CodeQL executed
successfully on the immutable candidate, and it is not a foundation-closure decision.

## Stable Required Check

GitHub will expose one stable aggregate check named `ci-required`. It runs with `if: always()` semantics and fails unless every required child gate succeeds.

Planned child gates:

1. `governance`: unique ADR filename/header ID and index parity; ADR-versus-OD prefix
   disambiguation; foundation-versus-feature packet membership; authoritative/proposed gate text
   synchronization; protected-path classification; CODEOWNERS coverage; required report fields;
   OPEN-register/index range parity; unique append-only disposition records and valid state
   transitions; exact-subject ADR/disposition SHA reconciliation; OD-040 genesis invariants;
   machine-inventory tree completeness/digest checks; pre-decision-overlay binding checks; and
   external disposition-receipt/effectiveness-witness reconciliation without self-reference.
2. `schema-contracts`: Draft 2020-12 validity, unique `$id`, local `$ref` closure, event catalog
   consistency, and fixture validation. After ADR-023 acceptance and separately authorized v2
   work, this also validates trusted envelope-version framing, complete immutable event-contract
   identities, catalog-fixed subject/scope/ordering/completeness/classification/producer profiles,
   kind-specific identities, aggregate-version/event-index plus exactly one transition manifest
   with `N >= 0` for every committed aggregate version, authorized zero/empty/subset
   expected-delivery high-water invariants, closed typed protection-overlay targets, monotonic
   overlay epochs/partition high-waters, rollback/same-epoch-conflict rejection,
   effect-boundary validation, immutable profile-versus-catalog-lifecycle separation, the
   emission/delivery/recovery-replay/incident-decode status matrix, profile-only
   evolution/historical replay, and event-versus-non-event separation.
3. `codegen-drift`: deterministic Python/TypeScript regeneration followed by a clean-diff assertion.
4. `contract-parity`: shared valid and invalid fixtures evaluated by JSON Schema, Pydantic, and TypeScript validators.
5. `python-quality`: formatting, Ruff, mypy, tests, import-linter, and the Python AST `ApprovedResponse` guard.
6. `typescript-quality`: formatting, ESLint, tsc, tests, dependency-cruiser, nominal-brand enforcement, and the TypeScript compiler-AST `ApprovedResponse` provenance guard.
7. `package-artifacts`: clean release builds, exact archive-member allowlists, traversal/cache rejection, metadata and version parity, manifest/schema inclusion and hashes, and isolated offline import smoke tests.
8. `migration-governance`: linked accepted ADR, protected lifecycle-catalog row/field
   traceability, authority/content/evidence/state-axis/access/retention/deletion mapping, schema
   diff, downgrade/restore strategy, and protection against editing published migrations.
9. `safety-regression`: affected red-team corpus, fail-closed, expiry, rewrite-loop, fallback-through-gate, and raw-text boundary tests.
10. `integration`: affected API/client, schema/query, config/runtime, and rehearsal boundaries.
    For authorized ADR-008 surfaces this includes database/factory rejection of every
    non-approved, unselected, cross-turn, stale-selection, and concurrent selection-versus-mint
    chain plus immutable selection after mint.
    For authorized ADR-023 surfaces this includes atomic state/audit, zero-or-more distinct
    `DomainEventRecord` facts, exactly one per-version manifest and all expected-delivery
    attestations, exactly one distinct `OutboxRecord` per event, operation-specific catalog
    lifecycle behavior, typed overlay targets, epoch/high-water rollback and same-epoch conflict,
    concurrent new-overlay races, and immediate irreversible-effect revalidation. For authorized
    ADR-024 surfaces this includes draft/publish, activation race/atomic-bundle/scope,
    inactive/deactivate/fallback, activation/eligibility epoch, snapshot/withdrawal,
    operation-discriminated schedule targets, rollback/restrictive-change, and no-reopen
    scenarios. For authorized ADR-025 surfaces this includes shared ownership-row conflict/fixed
    lock order/post-conflict time across acquire/renew/revoke/lease-expiry/takeover and ordinary
    commits; stale-composite-fence/aggregate rejection; exact open normal-work admission/source
    CAS across command receipt/authorization-refresh/ordinary claim/execution/successful-or-
    widening outcome, input/director/scheduler, timer, Turn, ordinary
    effect-intent/send/advancing-application, and every ordinary
    candidate/selection/approval/media/task/signing/dispatch
    progression; begin-close committed prefix, draining-prefix CAS permitting only bounded
    evidence/restrictive/terminal non-advancing dispositions, bounded drain, atomic
    `ended`/`cancelled`/`failed` session/admission/ownership final close, no
    post-begin-close-cut ordinary creation or advancement, and PITR-lost-close non-open
    quarantine across restored `open`, `draining(normal_closure)`, and atomic `closed`, including
    coherent `Ending`, proven-or-conceptually-unresolved terminal target, monotonic lost-tail
    overlay, unresolved-target final-close rejection, and final-close rejection for any
    nonterminal recovery probe or bound source ambiguity that is not resolved, permanently
    safe-quarantined, or accountably disposed;
    distinct four-role recovery-probe lineages under both exact active+draining-prefix and
    recovering+recovery-attempt/source bindings, including intent/attempt/first-byte/response/
    disposition crash cuts, zero-attempt terminalization, wrong-binding rejection, stable
    idempotency, finite count/byte/rate/age/concurrency, no deadline extension, no ordinary
    application, originating-fence-as-provenance and current same-source successor
    terminalization without resend, negative/timeout/contradictory evidence producing truthful
    terminal unknown without resolving the source, and exactly one terminal non-widening
    disposition; source-serialized activation cuts, preallocated-ID late commits,
    immutable cut-time source/schedule-cursor snapshots, harmless post-cut ingress advancing only
    the excluded operational cursor without starving activation, every recovery-attempt-bound probe write
    advancing invalidation, activation rejection for a nonterminal probe or enabled-scope
    unresolved source ambiguity, ambiguity/restriction invalidation revisions, and sealed rig
    cursors; submission-generation command
    receipt/response-loss, same protected scope/key plus same digest returning the original
    lineage, same protected scope/key plus different semantic digest conflicting with no second
    lineage, append-only
    refreshed-authorization observation handoff/deduplication/commit-response loss with immutable
    prior lineage and no transient-credential reconstruction, every receipt-return disclosure
    check, execution observation/policy/revocation selection, append-versus-execution lineage-
    revision CAS, deterministic allow/deny/step-up/unavailable precedence with ambiguity
    fail-closed, retryable/nonretryable denial terminality, receipt/refresh/execution
    database-time deadline boundaries, terminal no-reopen, and universal expiry; effect
    intent/send-authorization/first-byte/response-observation/application crash cuts,
    possibly-sent behavior, concurrent multi-observation cardinality, one disposition per
    observation, and a new domain attempt/intent for every retry, rewrite, fallback, provider, or
    semantic change; downstream-verifiable restrictive epoch ordering and actor-independent
    restrictive dispatcher; canonical timer-key uniqueness, current-active ownership-row
    materialization fencing, recovering-owner no-create/no-cursor-advance, materialization
    commit-response loss/cursor CAS, current-claim-pointer acquisition/reclaim CAS, rejection of
    expired/superseded-claim firing, and atomic at-most-one Turn admission plus at-most-one
    terminal firing disposition per occurrence; PITR recovery-generation ABA/lost-tail
    quarantine; bounded catch-up; process pause, partition, clock uncertainty, stop dominance, and
    safe-direction-without-false-success scenarios.
11. `security`: secret scanning, dependency review, static analysis, and pinned CI dependencies.
12. `operability-performance` (future): versioned SLI/alert contract checks, telemetry
    prohibited-content/cardinality/buffer tests, bounded queue/reserve assertions, and immutable
    cost/quota/billing-ledger and warning/denial/reconciliation fixtures, plus load/soak/chaos
    evidence validation for capabilities that exist. Session-runtime evidence also validates
    bounded command/ordinary-effect/recovery-probe/timer/restrictive-control claims, actor
    lease/takeover saturation,
    command-authorization observation append/count/rate/age bounds and protected execution
    reserve, recovery-probe count/byte/rate/age/concurrency bounds and non-widening reserve,
    normal-input/Turn closure-drain saturation and frozen timer cursors,
    immutable-activation-frontier churn versus excluded operational-cursor progress, recovery
    drain, restored-open/draining/closed lost-tail lifecycle/admission coherence,
    unresolved-target blocking, and stale-composite-fence/unknown-outcome alert contracts.

The planned Stage B workflow must run both code quality and `package-artifacts` as Linux and
Windows matrices. The artifact job must build Python wheels and sdists plus the TypeScript npm
archive twice from clean state and require identical SHA-256 digests by filename. It must admit
only declared members, reject traversal, links, caches, and duplicate entries, validate wheel
`RECORD` hashes, require Python/TypeScript contract version parity, check every manifest v2
schema/catalog provenance digest and package-relative artifact digest against the archive member it
names, and install one archive set into isolated offline smoke environments. The TypeScript
`prepack` lifecycle must always perform contract drift verification, a clean compile, a direct
canonical-envelope-schema byte copy, and a direct generated-active-registry byte copy before
packing, so an old `dist` directory cannot satisfy the gate.

The planned `ci-required` check must depend on the full `quality` matrix, `package-artifacts`, and
`security`, run even when any dependency fails or is cancelled, and reject every dependency
result other than `success`. The current quarantined aggregate implements those three
dependencies. The security job is structurally present but remains unobserved remote evidence
until it runs successfully on the immutable candidate. Gates that depend on future migrations,
provider code, runtime services, red-team corpora, deployment configuration, target telemetry,
or representative performance/resilience evidence remain planned and must be activated with
those surfaces. The future operability/performance gate is not part of the initial planned
`ci-required` dependency set and no pass is claimed.

The ADR/index/gate/disposition semantic checks and the ADR-023-, ADR-024-, and ADR-025-specific
schema/integration checks described above are planned design requirements unless and until their
implementation is present in the immutable candidate and observed in remote CI. Existing
formatting or link checks must not be reported as proof of those semantic controls.

The planned matrix uses the fixed `ubuntu-24.04` and `windows-2025` runner labels. Checkout, Node
setup, and uv setup actions must be pinned to immutable commit SHAs, with version comments
retained for reviewability. Reference material:

- [GitHub-hosted runner image labels](https://github.com/actions/runner-images)
- [actions/checkout releases](https://github.com/actions/checkout/releases)
- [actions/setup-node releases](https://github.com/actions/setup-node/releases)
- [astral-sh/setup-uv](https://github.com/astral-sh/setup-uv)
- [Gitleaks Action v3.0.0](https://github.com/gitleaks/gitleaks-action/releases/tag/v3.0.0)
- [Dependency Review Action v5.0.0](https://github.com/actions/dependency-review-action/releases/tag/v5.0.0)
- [CodeQL Action v4.37.1](https://github.com/github/codeql-action/releases/tag/v4.37.1)

Every planned job and every action or command step must have an explicit timeout. CI action
dependencies must be pinned to immutable commit SHAs. Workflows must use least-privilege
permissions and must not run untrusted PR code with secrets; `pull_request_target` is forbidden
for build or test execution.

## Protected-Path Classification

CI will detect changes to:

- governance and CI configuration;
- ADRs;
- safety and contract packages;
- event schemas and red-team fixtures;
- migrations;
- prompt, persona, and policy defaults;
- provider gateways;
- infrastructure, secrets configuration, and deployment definitions;
- stage-host command, adapter, watchdog, and e-stop behavior.

A future protected-path classification check will report required review categories. The
quarantined Stage B workflow now verifies its own action pinning, timeout, aggregate-check,
trigger, runner-matrix, and required-entrypoint invariants. That self-check cannot substitute for
successful remote security execution, GitHub repository rules, immutable evidence, or human
approval.

## Repository Ruleset

The default branch should require:

- pull requests rather than direct pushes;
- the `ci-required` check;
- code-owner review;
- dismissal of stale approvals after protected changes;
- resolution of review conversations;
- signed commits if the team can operate them reliably;
- blocked force pushes and branch deletion.

For safety-critical protected paths, use two independent approvals once the repository has enough maintainers. The current single-owner bootstrap cannot provide independent review and is recorded as OD-012.

CODEOWNERS is evaluated from the pull request's base branch and therefore cannot protect the PR
that first introduces it. Follow the two-stage ceremony in the
[foundation authority and bootstrap proposal](foundation-authority-and-bootstrap-proposal.md):
first land governance/ownership with an eligible non-author approval under an administrator-set
temporary rule, then review the executable foundation after CODEOWNERS is effective on `main`.

## Migration Gate

The gate must inspect migration content, not rely only on a PR label. Every new migration contains an `ADR: NNNN` reference to an accepted ADR. The gate verifies that the ADR exists and is accepted, generates a schema diff, and rejects modification of a migration already present on the default branch.

## Activation Sequence

1. Prepare OD-040's one-time genesis rule and the normal immutable disposition lifecycle for
   protected, non-author human review; do not claim ratification before its candidate and
   external evidence exist.
2. Prepare the OD-019 exact authoritative gate amendment and use
   [`VNOVA-FOUNDATION-STAGE-A-HANDOFF-v1`](foundation-stage-a-review-handoff.md) to freeze the
   Retire-only governance path/status/mode allowlist. A Restore choice requires a replacement
   handoff.
3. Freeze the governance candidate SHA first; then generate the external machine inventory and
   pre-decision semantic overlay, open the PR, and collect exact rule/validation/access/approval
   facts. A later source or overlay change invalidates dependent evidence.
4. Freeze the external review-package manifest over those prerequisite receipts. Create separate
   external OD-040, OD-018, and OD-019 attestations in that effective order, then land the exact
   governance candidate and record the merge, ordered receipts/predecessors, condition results,
   times, and derived states in an append-only effectiveness witness.
5. Verify CODEOWNERS/access on `main` and land the separate protected decision-projection PR.
6. Open the separate executable foundation PR; run every local-equivalent Linux/Windows job and
   `ci-required` on its exact final SHA.
7. Configure and export the GitHub Ruleset after the stable aggregate check has a successful run.
8. Record evidence that a deliberately failing fixture blocks a test pull request.
9. Dismiss stale approval after the last protected change, obtain the required non-author/code
   owner approval for the exact SHA, freeze the external review-package manifest, and create the
   separate pre-merge intended OD dispositions and ADR decisions required by the authority
   proposal.
10. Merge only the exact reviewed candidate through the protected rule; the executable scaffold
    remains quarantined if this merge or any post-merge condition is absent.
11. Append the effectiveness witness binding the merged SHA, merge event/time, ordered
    disposition receipts, ADR decisions, and condition results. Never create the witness before
    the merge it names.
12. Land the protected decision projection, then record the separate
    gate-closure/next-increment decision, or leave the gate blocked.

Until this sequence is complete, no document may claim that CI enforcement is active.
