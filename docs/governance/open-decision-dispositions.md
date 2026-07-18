# Open Decision Disposition Register

Status: Proposed; no OPEN decision is closed by this document

This register defines the durable evidence required to move an item in the
[Open Decision Register](../architecture/open-decisions.md) out of `OPEN`. It prevents an ADR
status label, meeting note, blank approval table, or agent recommendation from silently becoming
production authority.

The lifecycle and eligible authority remain subject to OD-040 and protected human review. Until
the one-time genesis review below records otherwise, every item OD-001 through OD-040 remains
OPEN.

## One-Time OD-040 Genesis Ratification

OD-040 cannot rely on a lifecycle that has not yet been adopted. Its first disposition therefore
uses a one-time genesis authority derived only from the existing repository administrator's
authority to protect the repository, the accountable human architecture owner's design authority,
and the binding `AGENTS.md` requirement for human review of governance/protected changes.

The genesis record is valid only when all of the following hold:

- one external protected package manifest binds the exact OD-040 text, this complete lifecycle,
  the authoritative gate amendment, base SHA, reviewed-subject SHA, external machine-inventory
  digest, pre-decision semantic-overlay digest, pull-request head/diff, and review evidence;
- an eligible repository administrator and accountable architecture owner explicitly ratify,
  revise, or reject it;
- at least one eligible human who is neither the candidate author nor acting solely as an agent
  independently reviews and approves the final exact SHA;
- a temporary administrator-enforced pull-request/approval rule protects the bootstrap change,
  because candidate CODEOWNERS is not yet effective on the base branch;
- the human record states that its authority is this one-time genesis rule, not an assumed prior
  OD-040 disposition;
- any source change after review dismisses/stales the approval and requires review again; and
- the final result is recorded first as an external protected disposition attestation; a later
  separately reviewed repository projection links it from the summary table.

If the genesis review is deferred, inconclusive, rejected without an accepted replacement, lacks
eligible non-author review, or cannot bind to an immutable candidate, OD-040 and every other OPEN
item remain OPEN. After a valid `DECIDED` genesis record exists, this exception is exhausted and
all later decisions, including any OD-040 supersession, use the normal lifecycle.

The bootstrap candidate may carry blank templates and a blank summary, but no effective
disposition that recursively requires its own candidate SHA. Its external effective-order records
must apply OD-040 genesis first, OD-018 second, and OD-019 third. Every disposition has its own
record and eligible owners and independently satisfies the newly ratified lifecycle. A single
omnibus approval or same timestamp does not collapse those decisions.

## Authority Rules

- Codex and other agents may prepare alternatives, evidence, and blank records. They never supply
  a human identity, vote, outcome, date, signature, or approval.
- The accountable roles named by the decision register must be represented by eligible humans.
  Repository rules and CODEOWNERS may require additional independent, non-author review.
- The disposition binds to one immutable repository candidate and the exact reviewed artifacts.
  A later source change invalidates affected evidence and requires a new review.
- A selection is effective only when its accepted ADRs, policies, contracts, disabled scope, and
  this register describe the same outcome.
- `Deferred` and `Inconclusive` keep the item OPEN and its blocked scope disabled.
- A superseding decision never rewrites history. It appends a new record, links the prior record,
  and names the replacement authority.

## Field Ownership And Evidence Separation

A disposition joins two sources without merging their authority:

1. **Machine evidence** records observable facts such as repository/base/candidate SHA, complete
   external inventory URI/digest, pre-decision-overlay receipt, frozen package-manifest receipt,
   PR/head SHA, check/run IDs, Ruleset export, validation output, approval/merge events,
   effectiveness-witness state/time, and projection commit. A machine may report
   `not_collected`, `missing`, `not_applicable`, or a measured result. It never chooses an
   effective decision state.
2. **Pre-decision human semantics** records classification, executable behavior, governing
   authority, impact, validation references, required revisions, and proposed disabled scope. It
   contains no final disposition, approval evidence, reviewer-eligibility judgment, decision
   time, or risk acceptance.
3. **Human disposition** records outcome, normative decision statement, rejected/deferred
   alternatives, accepted authority, retained OPEN scope, reviewer eligibility, risk judgment,
   supersession/invalidation policy, and enabled/disabled capability in a separate protected
   attestation.

Hybrid fields retain both producers. For example, GitHub may timestamp an approval, but the
accountable human supplies the decision; a collector may assign a record ID only after humans
approve the identifier convention and may not use that assignment to imply `DECIDED`.

Every machine evidence object names its source scope, collection time, collector/tool identity,
candidate binding, and immutable evidence ID or explicitly says that no durable artifact exists.
Every human disposition references the machine evidence and pre-decision-overlay IDs and
separately decides whether they are sufficient and fresh. The disposition cannot be embedded in
the overlay whose digest it approves. A combined view may join the records but must not erase
producer, provenance, effective order, or authority.

## Allowed States

| State         | Meaning                                                                 |
| ------------- | ----------------------------------------------------------------------- |
| `OPEN`        | No effective human disposition; all named blocked scope remains blocked |
| `DECIDED`     | A protected human disposition selected an outcome for an exact subject  |
| `SUPERSEDED`  | A later effective disposition replaced the prior outcome                |
| `INVALIDATED` | The evidence or reviewed subject changed; the item returns to OPEN      |

`Rejected` is an outcome, not a reason to erase the decision. Its disposition must say which
capability stays disabled or which replacement work is required.

The signed disposition payload records a selected outcome and intended lifecycle transition, not
a prematurely effective state. Until a valid effectiveness witness exists, the actual lifecycle
state remains `OPEN`. The external joined view derives `DECIDED`, `SUPERSEDED`, or `INVALIDATED`
from the immutable payload, predecessor relation, effectiveness/invalidation witnesses, and their
ordering; it never rewrites the signed payload.

## Required Disposition Record

Every disposition joined view uses this schema. It becomes effective only when every required
human field, external receipt, signature, and valid effectiveness witness is present:

| Field                                     | Requirement                                                                                                                                                                                                                                      |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Open Decision ID                          | Exact `OD-NNN` identifier                                                                                                                                                                                                                        |
| Previous effective record                 | Link or `none`; required for supersession                                                                                                                                                                                                        |
| Selected outcome and intended transition  | Explicit human choice and post-condition transition; never represented as already effective before its witness                                                                                                                                   |
| Effective lifecycle state                 | Externally derived from ordered effectiveness/invalidation witnesses; remains `OPEN` while the required witness is absent                                                                                                                        |
| Decision statement                        | Normative result and alternatives rejected/deferred                                                                                                                                                                                              |
| Blocked scope disposition                 | Exact capability enabled, still disabled, or replaced                                                                                                                                                                                            |
| Accepted authority                        | ADR/policy/contract versions and status after the decision                                                                                                                                                                                       |
| Retained OPEN items                       | Numeric/profile/sub-capability choices that remain disabled                                                                                                                                                                                      |
| Base and reviewed-subject commit SHA      | Exact immutable source state the humans decided                                                                                                                                                                                                  |
| External machine inventory and digest     | Every path/blob fact from the reviewed Git tree; generated outside that tree to avoid self-reference                                                                                                                                             |
| Pre-decision semantic overlay and digest  | Protected classification, behavior, authority, impact, revisions, and proposed disabled scope; no final disposition                                                                                                                              |
| Pull request/check/Ruleset facts          | Machine-observed URL/ID, final head SHA, checks, rule export, approval event, and stale-review behavior                                                                                                                                          |
| Frozen review-package manifest            | External ID/digest binding the candidate, inventory/overlay, PR/diff, rule, validation, access, and approval facts                                                                                                                               |
| Accountable human roles/identities        | Eligible decision makers and independent reviewer; never agent-populated                                                                                                                                                                         |
| Eligibility/quorum/sufficiency judgments  | Human judgments over machine account/access/approval facts                                                                                                                                                                                       |
| Decision order and effective condition    | Human-selected order and condition recorded in the signed payload                                                                                                                                                                                |
| Decision time                             | Human decision plus protected-system UTC timestamp                                                                                                                                                                                               |
| Witnessed condition/state/time            | Machine-observed result, derived lifecycle state, and UTC time from the valid effectiveness witness                                                                                                                                              |
| Validation facts and sufficiency          | Exact commands, targets, results, and evidence IDs plus a separate human sufficiency/freshness judgment                                                                                                                                          |
| Security/privacy/residual-risk note       | Required applicable reviews and named residual-risk authority                                                                                                                                                                                    |
| Supersession/invalidation triggers        | Conditions that force review or return the item to OPEN                                                                                                                                                                                          |
| Disposition attestation receipt           | External protected ID/digest/URI supplied outside the signed payload so the payload does not hash or locate itself                                                                                                                               |
| Repository projection status and evidence | `pending` is valid initially; a later protected mirror commit is recorded only by an external append-only witness                                                                                                                                |
| Effectiveness witness                     | External append-only payload binding repository/base/merged SHA, target branch, merge event/time, package manifest, every ordered receipt/digest and predecessor, condition result/time, and derived state; absent witness keeps the record OPEN |

## Full Disposition Artifact Template

Each disposition is a separately reviewable immutable artifact. Copy this template into a
human-reviewed record; do not replace blank human fields with agent-generated values.

The `reviewed-subject SHA` is the source commit whose behavior is decided. A signed disposition
payload cannot contain its own future Git commit SHA, its own receipt digest/URI, or an
inventory/overlay digest that recursively includes the disposition. Therefore:

- the complete machine inventory is a CI/review artifact generated from the Git tree of the
  reviewed-subject SHA and stored outside that tree with an immutable digest/attestation;
- the pre-decision semantic overlay separately references that SHA and inventory digest and
  contains no final decision/approval evidence;
- a frozen external review-package manifest binds the inventory/overlay receipts, exact PR/diff,
  rule, validation, access, and approval-event facts without containing later dispositions;
- the human disposition is a protected review or signed evidence object that names that SHA and
  external inventory/overlay plus the frozen package-manifest digest;
- the protected system supplies the disposition receipt ID/digest/URI outside the signed payload;
- a future effective condition is not silently backdated: an external append-only witness records
  the exact observed effective time;
- a later repository commit may mirror/index the disposition, but its commit ID is recorded in
  the external evidence or a subsequent append-only record, not inside itself; and
- the mirror commit receives its own protected review and cannot change the selected outcome.

| Field                                  | Producer / authority                                         | Value |
| -------------------------------------- | ------------------------------------------------------------ | ----- |
| Record ID                              | Protected-system preallocation under a human-approved scheme |       |
| Open Decision ID                       | Register fact; human confirms the decided subject            |       |
| Previous effective record              | Machine lookup; human confirms supersession relation         |       |
| Selected outcome                       | Accountable human decision only                              |       |
| Intended lifecycle transition          | Accountable human decision only                              |       |
| Effective lifecycle state              | Derived external witness/invalidation evidence               |       |
| Decision statement                     | Accountable human decision only                              |       |
| Alternatives rejected/deferred         | Accountable human decision only                              |       |
| Blocked scope disposition              | Accountable human decision only                              |       |
| Accepted authority                     | Accountable human decision reconciled with protected source  |       |
| Retained OPEN items                    | Accountable human decision only                              |       |
| Base commit SHA                        | Git/review-system machine evidence                           |       |
| Reviewed-subject commit SHA            | Git/review-system machine evidence                           |       |
| External machine inventory link/digest | External collector/attestation evidence                      |       |
| Pre-decision overlay link/digest       | Protected artifact-system evidence                           |       |
| Frozen review-package manifest         | Protected artifact-system ID/digest                          |       |
| Pull request/head/check facts          | GitHub/review-system machine evidence                        |       |
| Required-check and Ruleset facts       | GitHub/repository-administration machine evidence            |       |
| Approval event ID/time/head SHA        | Protected review-system machine fact                         |       |
| Accountable human roles/identities     | Eligible humans only                                         |       |
| Independent non-author reviewer        | Eligible human plus repository-access evidence               |       |
| Eligibility/quorum judgment            | Accountable human decision only                              |       |
| Decision order and effective condition | Accountable human decision only                              |       |
| Decision time                          | Human decision plus protected-system timestamp               |       |
| Effectiveness witness ID/digest        | External append-only witness receipt                         |       |
| Witnessed effective time               | External append-only effectiveness evidence                  |       |
| Validation fact references             | Machine evidence with exact commands/targets/results         |       |
| Validation sufficiency/freshness       | Accountable human decision only                              |       |
| Security/privacy review                | Applicable eligible human authorities                        |       |
| Residual-risk authority/decision       | Applicable eligible human authority only                     |       |
| Supersession triggers                  | Accountable human decision only                              |       |
| Invalidation triggers                  | Accountable human decision only                              |       |
| Disabled scope after decision          | Accountable human decision only                              |       |
| Disposition attestation receipt        | Protected-system wrapper; excluded from signed payload       |       |
| Repository projection status           | `pending` initially or external projection witness afterward |       |

The external receipt and effectiveness witness establish the record; a repository summary row is
a later protected projection. A blank or stale summary never creates authority, and a pending
projection does not invalidate an otherwise complete external decision. VNova nevertheless
requires the projection before Stage B may rely on a Stage A decision.

## Current Dispositions

There are no effective dispositions yet. After an external record becomes effective, a separate
protected projection must add its summary row before Stage B reliance. Agents must leave all
human-owned cells blank and cannot infer a row from a PR merge.

| Record ID | OD ID | State | Outcome | Full artifact and digest | Reviewed-subject SHA | Projection commit | Human decision evidence | Effective authority |
| --------- | ----- | ----- | ------- | ------------------------ | -------------------- | ----------------- | ----------------------- | ------------------- |
|           |       |       |         |                          |                      |                   |                         |                     |

## Reconciliation Check

Before relying on a disposition, reviewers verify:

1. the OD exists and its accountable roles and blocked scope still match;
2. the reviewed subject, external machine inventory, pre-decision semantic overlay, disposition
   attestation receipt, and effectiveness witness are immutable, non-self-referential, mutually
   bound, and checks ran on that exact SHA;
3. the human identities are eligible, required independent review is present, and the author did
   not self-approve;
4. every affected ADR, architecture document, contract state, policy activation, and disabled
   capability matches the selected outcome;
5. retained OPEN items are still fail-closed or unavailable;
6. no later disposition supersedes or invalidates the record; and
7. the release and operational-readiness evidence is still fresh for the named target.

Any failed check keeps the item OPEN. The discrepancy is recorded; implementation does not guess
the intended outcome.
