## Outcome

Describe the user or operational outcome, not only the files changed.

## Review profile

- [ ] Stage A governance bootstrap
- [ ] Stage A external-decision projection
- [ ] Stage B quarantined foundation scaffold
- [ ] Later feature, operations, or release change

Profile/handoff ID:

Protected paths touched:

Required human authorities:

## Scope

- Files created:
- Files updated:
- ADRs added or changed:
- Explicitly excluded paths/capabilities:

## Immutable subject — machine facts

Record facts or `missing` / `not_collected` with a reason. Do not infer eligibility, approval,
sufficiency, or decision outcomes. Stage A values must identify the exact
`VNOVA-FOUNDATION-STAGE-A-HANDOFF-v1` subject.

| Fact                                            | Value / evidence ID |
| ----------------------------------------------- | ------------------- |
| Repository and target branch                    |                     |
| Base commit SHA                                 |                     |
| Candidate commit SHA                            |                     |
| Final PR head SHA                               |                     |
| Diff identity / patch digest                    |                     |
| Exact path/status/mode allowlist result         |                     |
| Candidate-tree inventory URI and payload digest |                     |
| Inventory provenance receipt ID/digest          |                     |
| Pre-decision overlay URI and payload digest     |                     |
| Overlay freeze receipt ID/digest                |                     |
| Frozen review-package manifest ID/digest        |                     |
| PR URL and approval-bound head SHA              |                     |
| Required-check run IDs and conclusions          |                     |
| Temporary rule or Ruleset export ID/digest      |                     |
| GitHub account and repository-permission facts  |                     |
| Non-author approval event ID/time/head SHA      |                     |
| Stale-review dismissal event/rule facts         |                     |
| Merge event and merged SHA, when applicable     |                     |
| Post-merge CODEOWNERS parse/access evidence     |                     |
| External disposition receipt IDs/digests        |                     |
| Effectiveness-witness ID/digest                 |                     |

### Stage A machine-verifiable source assertions

Machines may mark these boxes only when the corresponding immutable evidence ID is recorded
above. They do not establish owner/reviewer eligibility or review sufficiency.

- [ ] The diff contains exactly the handoff's allowlisted paths, statuses, and `100644` modes.
- [ ] No workflow, toolchain, package, schema, test, runtime, provider, prompt, policy, migration,
      adapter, infrastructure, secret, generated artifact, or other excluded path changes.
- [ ] Every local Markdown link in a changed document resolves within the candidate tree.
- [ ] `AGENTS.md`, the system overview, and the gap analysis match the base-anchored source
      blueprint; broad mutable-worktree versions were not copied.
- [ ] Every applicable last-matching CODEOWNERS rule contains a distinct account token;
      repository API evidence shows accepted collaborator/write access, the account differs from
      the PR author, and `.github/CODEOWNERS` owns itself.
- [ ] Repository disposition summaries and all candidate-contained human decision cells are blank.
- [ ] The candidate contains no claim that an OD, ADR, gate, approval, or merge is already
      effective.

## Protected human evidence and decisions

Agents must leave this section blank. Each accountable human records a decision only after the
exact candidate, prerequisite receipts, and reviewer-access facts are frozen. References point
to separate protected records; this pull-request body is not itself the disposition authority.

| Human-owned field                                      | Outcome / identity / protected record |
| ------------------------------------------------------ | ------------------------------------- |
| Pre-decision overlay semantic assessment               |                                       |
| Owner mapping and reviewer eligibility/quorum judgment |                                       |
| Non-author approval sufficiency                        |                                       |
| OD-040 genesis outcome                                 |                                       |
| OD-018 Retire outcome                                  |                                       |
| OD-019 amendment outcome                               |                                       |
| Effective order `OD-040 → OD-018 → OD-019`             |                                       |
| Validation sufficiency and freshness                   |                                       |
| Security, privacy, and residual-risk decision          |                                       |
| Merge authorization / retained disabled scope          |                                       |
| Effectiveness-witness sufficiency, after merge         |                                       |

## Architecture and safety review

- [ ] I read `AGENTS.md` and the active ADRs for this exact change.
- [ ] `CandidateResponse` and `ApprovedResponse` remain separate.
- [ ] Only `packages/safety` can mint `ApprovedResponse`.
- [ ] No raw generated text crosses a TTS or media interface.
- [ ] Every new external call has an explicit timeout.
- [ ] Provider fallback still passes through the same safety gate.
- [ ] No schema migration is present, or every migration links an Accepted ADR.
- [ ] Viewer memory and audit data remain separated.
- [ ] Protected paths and required human authorities are identified above.

Not-applicable checks and reasons:

## Validation evidence

List the exact command, execution environment, result, final-subject SHA, run/evidence ID, and
freshness time. Do not mark an unexecuted gate as passed.

| Command / remote check | Environment | Result | SHA and evidence ID |
| ---------------------- | ----------- | ------ | ------------------- |
|                        |             |        |                     |

## Invalidation and freshness

- [ ] Any base, candidate, PR-head, diff, inventory, overlay, manifest, required signature, rule,
      access, or source change creates new evidence and invalidates every dependent approval.
- [ ] Any source change after approval requires stale-review dismissal and fresh approval for the
      final head.
- [ ] Missing or `not_collected` evidence remains missing; it is never converted to passed,
      accepted, decided, or closed.
- [ ] An administrator bypass is not ordinary acceptance evidence.

## Decisions and risk

- Assumptions made:
- OPEN decisions:
- Known residual risks:
- Deviations from ADRs, `AGENTS.md`, or `vnova-review-handoff.md`:
- Repository-structure mismatches discovered:
