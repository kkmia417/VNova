# ADR-008: Safety Gate Enforcement

Status: Proposed

Date: 2026-07-17

Sources: `AGENTS.md`, `vnova-review-handoff.md`, ADR-003, ADR-025

## Context

A convention that says "run safety before speech" is not an enforcement mechanism. VNova must make the unsafe path difficult at the language boundary, invalid at the database boundary, detectable in CI, and unverifiable work unplayable at the stage host.

Python cannot provide a security boundary against arbitrary malicious repository code. The design therefore uses independent, testable layers so that an accidental bypass cannot become broadcast speech.

## Decision

`CandidateResponse` and `ApprovedResponse` remain distinct types. A candidate is unsafe by default. Only the factory owned by `packages/safety` may construct an `ApprovedResponse`.

Approval is enforced as one trust chain:

```text
CandidateResponse
  -> SafetyDecision(decision = approved)
  -> ApprovedResponse
  -> approved_response_id resolution inside the TTS gateway
  -> immutable media artifact
  -> signed SpeechTask
  -> stage-host verification
  -> immediate pre-playback expiry check
```

Failure at any link produces no autonomous speech.

## Language And Package Boundary

- The concrete `ApprovedResponse` constructor and mint capability live in a private module under `packages/safety` and are not exported.
- Other packages receive an immutable public view/type and identifiers; they cannot import the private mint module.
- The TypeScript public view is nominal, not merely structural: it carries a `readonly` property keyed by a non-exported `unique symbol` owned by `packages/safety`. Exporting that brand, publishing an unbranded `ApprovedResponse`, or recreating the brand outside the package fails CI.
- `ApprovedResponse` is a non-serializable in-process capability. JSON, worker, process, queue, and network boundaries carry reviewed IDs or validated DTOs instead; rehydration is safety-owned and must revalidate the persisted approval chain and expiry.
- The safety factory freezes each capability at runtime and retains a private authenticity record. Consumers may read it, pass the same instance, or store it read-only, but may not clone, proxy, transform, ambiently declare, or expose a new producer of approval capabilities.
- The factory requires a persisted approving `SafetyDecision`, the exact candidate explicitly
  selected by `selected_candidate_id` on the same `Turn`, policy version, approval provenance,
  and authoritative `not_after` value. An approved but unselected candidate, a candidate selected
  by another turn, or a selection changed concurrently is not mintable.
- Import-linter enforces package dependencies.
- Repository Python AST and TypeScript compiler-AST checks reject direct construction, subtype/assertion and type-predicate bypasses, ambient capabilities, structural or `any` values flowing into direct or nested approval sinks, non-safety producer functions/calls, clone/proxy transformations, and private mint imports outside `packages/safety` because import graphs cannot enforce symbol-level behavior by themselves.
- Strict TypeScript compilation independently proves that structurally similar values cannot satisfy the private brand. The AST guard remains a separate defense against explicit escape hatches and provenance-erasing transformations.
- Static type tests prove that TTS, media, and dispatch interfaces accept `approved_response_id` and cannot be called with candidate text.
- CODEOWNERS and repository rules require human review for the safety package and the checks that protect it.

## Safety Evaluation Semantics

- A candidate has no more than one terminal `SafetyDecision`; once its evaluation completes with
  a determinate `approved`, `rejected`, or `rewrite_requested` outcome, exactly one terminal
  decision is persisted.
- Routing a candidate to operator review is a nonterminal evaluation status with provenance, not a `SafetyDecision` outcome.
- A terminal `rewrite_requested` decision carries `rewritten_from_candidate_id` equal to the
  source candidate. It starts a new immutable `GenerationAttempt` referencing that decision. Only
  a successful generation attempt creates a child `CandidateResponse` with the same
  `rewritten_from_candidate_id`; that child then enters the full evaluation pipeline.
- Rewrite attempts are capped and tested.
- Manual approval, rejection, or rewrite request completes evaluation by recording the candidate's terminal `SafetyDecision` with `decided_by = operator_id`; it is not a parallel approval mechanism.
- Primary and fallback providers use the same gate.
- Missing, timed-out, unavailable, or indeterminate safety results terminate evaluation as `failed_closed` without a `SafetyDecision` and cannot mint an approval.
- Expiry or cancellation before evaluation completes may terminate work without a `SafetyDecision`; that candidate can never mint an approval.

## Database Enforcement

The eventual PostgreSQL schema must enforce the approval chain, not merely document it.

- `safety_decision` has a unique candidate relationship and records only terminal decision outcomes.
- `approved_response` has a unique foreign key to the corresponding safety decision.
- A composite key or equivalent database constraint binds the referenced decision ID to the literal approved outcome. A plain foreign key to an unconstrained decision row is insufficient.
- A composite constraint, protected constraint trigger, or equivalently proven database guard
  binds the approved decision to its candidate, that candidate to its owning `Turn`, and that
  turn's immutable `selected_candidate_id` to the exact same candidate. Approval cannot commit
  for an unselected candidate or a candidate from another turn.
- Once an approved-response row exists, the owning turn's selected candidate is immutable. A
  concurrent selection change and approval mint serialize so at most one exact same-turn
  selection can win; neither application ordering nor a prior read substitutes for the database
  guard.
- Approval minting and its audit/outbox records occur in one transaction. For session-owned
  progression, that transaction also participates in ADR-025's shared ownership-row conflict,
  takes the post-conflict lease check, and proves the exact current active
  `(recovery_generation, ownership_generation)` composite actor fence plus aggregate version; a
  stale actor cannot mint by presenting an otherwise valid candidate/decision chain.
- The database rejects an approved-response row backed by a `rejected`, `rewrite_requested`,
  missing, or unknown decision, an unselected candidate, a selected candidate owned by another
  turn, or a stale/concurrently changed selection. Operator-review queue state is not stored as a
  safety decision.
- A migration implementing these constraints requires its own linked ADR reference and human review.

## Durable Approved Content

The non-serializable in-process `ApprovedResponse` capability is distinct from its safety-owned
durable record.

- Minting persists an immutable approved-content snapshot or immutable restricted content
  reference in the same safety-owned approval transaction. It binds the exact linguistic content
  covered by the decision, canonical digest, source candidate/decision IDs, provenance, scope, and
  non-extended `not_after`.
- Candidate metadata and decision lineage remain available for revalidation even if retention
  policy later removes or redacts the raw candidate body. The approved snapshot cannot resolve to
  a different candidate value.
- Only `packages/safety` may create or authentically rehydrate the capability and durable record.
  Rehydration revalidates the same approving-decision, exact selected same-turn candidate,
  immutable selection, content, expiry, and current restriction chain; a row or ID alone is not
  sufficient.
  Public commands, events, TTS/media interfaces, queues, URLs, logs, traces, and `SpeechTask` carry
  the identifier and allowed integrity metadata, never the linguistic content.
- The trusted TTS/media gateway resolves the snapshot only after revalidating the complete
  persisted chain and current restrictive state.
- If the snapshot is deleted, expired, held unavailable, corrupt, or inconsistent, new synthesis,
  regeneration, replay, and export fail closed. A separately retained public broadcast artifact
  follows its own current archive, deletion, rights, and surface policy and cannot be accepted as
  the canonical source for rehydrating the missing approval record.

Exact storage, classification, retention, deletion, reveal, archive interaction, and physical
constraints require ADR-017 review plus the linked migration ADR. This Proposed ADR does not
silently revise Accepted retention policy.

## Expiry Propagation

The candidate's authoritative `not_after` is never extended by approval, synthesis, retry, reconnect, or queueing.

- `ApprovedResponse`, the media authorization record, `SpeechTask`, and its signed token carry the same or an earlier `not_after`.
- TTS resolution checks expiry before synthesis.
- Dispatch checks expiry before enqueue.
- `stage-host` checks expiry when accepting a task and again immediately before playback.
- Expired queued work is evicted, emits an auditable expiry event, and is never played.
- Wall-clock decisions use UTC timestamps; local scheduling may use a monotonic clock derived from the validated deadline and measured clock offset.

## TTS And Media Boundary

- Public TTS and media interfaces accept `approved_response_id`, never raw generated text.
- The trusted gateway resolves approved text internally after revalidating the approval chain and expiry.
- Provider SDKs remain inside provider gateways and every provider call has an explicit timeout.
- Media artifacts are immutable and content-addressed or carry an integrity digest bound to the speech task.
- SSML and provider markup are sanitized at the media boundary even for approved text.

## Signed SpeechTask

The runtime signs every task with an asymmetric key. The stage host is provisioned with public
verification keys and does not receive signing authority. The signing/dispatch boundary verifies
the exact current active ADR-025 composite actor fence through the shared ownership-row
linearization point and records it server-side; process possession of workload or signing access
is not session ownership. Administrative revoke and disaster recovery additionally use
ADR-025's downstream-verifiable session-epoch/binding fence; a cached database check alone
cannot order a later send against revoke.

The signed claims bind at least:

- issuer, audience, key ID, issued-at, not-before, and expiry;
- unique token ID and speech-task ID;
- stream-session ID and session epoch;
- approved-response ID and safety-decision ID;
- media artifact ID and integrity digest;
- queue sequence or ordering identity.

Until ADR-011 accepts a broader wire contract, the repository boundary checker admits only a closed, flat `SpeechTask` object whose direct fields come from the reviewed identifier/integrity/timing allowlist and whose values are scalar strings or integers. Entity identifier fields use UUID format. `patternProperties`, property-shaping composition, unresolved references, nested data containers, and arbitrary field aliases fail closed. Extending that allowlist is a protected protocol change, not an implementation convenience.

The stage host rejects unknown keys, invalid signatures, wrong audiences, wrong sessions, expired tasks, artifact digest mismatches, and replayed token IDs. Verification-key rotation uses an explicit overlap window. E-stop increments or invalidates the session epoch so previously queued work cannot resume accidentally.

The concrete signature algorithm, key custody system, and rotation interval must be selected in the stage-host protocol security design before implementation.

## Fail-Closed Behavior

- No safety verdict means no autonomous speech.
- Safety unavailability emits `SafetyLayerUnavailable` and activates the documented degradation path.
- Pre-approved canned material may be used only through a separately approved and auditable path.
- Fallback scenes and silence are preferred to unverifiable speech.

## Required Verification

- Construction/import boundary test for `ApprovedResponse`.
- Python and TypeScript compiler-AST guard tests for forbidden construction, subtype, assertion, type predicate, ambient capability, structural/`any` flow, direct and nested containers, provenance-erasing producer/clone calls, and mint calls.
- Database/factory tests for every non-approved decision outcome, approved-but-unselected
  candidate, candidate selected by another turn, missing/mismatched `selected_candidate_id`,
  concurrent selection-versus-mint race, and attempted selection mutation after mint.
- State-machine tests proving operator-review queueing creates no terminal decision and that operator completion creates exactly one.
- Static contract tests proving raw text cannot call TTS/media interfaces.
- Safety timeout fault injection proving zero autonomous speech and mode degradation.
- Fallback-provider test proving re-entry through the same gate.
- Expiry tests at mint, synthesis, dispatch, queue acceptance, and immediate pre-playback stages.
- Stale composite-fence, ownership-row/revoke race, PITR/failover, and takeover tests proving an
  old actor cannot mint, sign, dispatch, or apply a late safety result, including restrictive
  epoch/binding rotation, sealed rig reconciliation, and lost-tail quarantine when dispatch is
  ambiguous.
- Signature, replay, session-binding, artifact-substitution, rotation, and
  offset/uncertainty/sample-staleness tests.
- Local e-stop test with the cloud link severed.

## Consequences

- Safety enforcement is deliberately redundant across code, storage, CI, cryptographic dispatch, and local playback.
- TTS gateways need privileged approved-content resolution but expose only identifier-based interfaces.
- Stage-host protocol implementation remains blocked until its cryptographic profile and e-stop SLO receive human review.
- Database implementation remains blocked until a linked schema ADR is accepted.
