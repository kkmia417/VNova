# Broadcast Surface Model

Status: Binding handoff safety baseline with Proposed implementation model; no surface
implementation authorized

Governing proposal:
[ADR-021](../adr/0021-broadcast-surface-inventory-and-overlay-policy.md)

Voice is not the only output that can harm a broadcast. Every value that reaches the audience is
a moderated broadcast surface with explicit ownership, provenance, expiry, and emergency-disable
behavior.

## Closed Surface Inventory

| Surface          | Source authority                                      | Minimum control                                                                                       |
| ---------------- | ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Voice            | `approved_response_id` plus voice/surface authority   | Full-response safety; rights; SSML/markup sanitization; signed expiring task; immediate replay checks |
| Captions         | Approved response or approved media timeline          | Authorized exact transformation; no raw candidate or raw chat; expiry and deterministic clear         |
| Chat overlay     | Moderated input plus exact final-render authorization | VNova-owned delayed renderer or absent; active content forbidden                                      |
| Alerts           | Immutable reviewed template plus screened fields      | Final-context moderation, escaping, bounds, expiry, and clear                                         |
| Scene text       | Approved content or immutable reviewed template       | Closed placeholders, screened dynamic fields, layout bounds, and expiry                               |
| Spoken usernames | Separately moderated name/pronunciation rendering     | Unicode and final-context checks, versioned pronunciation, safe omission fallback                     |
| Avatar actions   | Closed versioned policy vocabulary                    | Bounded parameters, session/epoch binding, expiry, emergency override                                 |

Sound, image, video, pre-recorded audio, or any new adapter output is disabled until a protected
ADR amendment defines its identifier-only content, rights, renderer, expiry, and emergency model.

## Authorization Shape

The Proposed ADR-021 model adds a presentation-specific `SurfaceAuthorization` without weakening
`ApprovedResponse`. It binds the exact normalized presentation digest, source IDs, session and
epoch, destination, renderer/template/policy versions, timing window, and clear condition.
Authorization for one surface or rendering is not reusable for another.

It must be backed by a terminal authorized `SurfaceDecision`, a sole protected private mint
boundary, ID-only serialization, and database constraints that reject a missing or mismatched
decision. For voice, the chain is explicitly composed:

```text
ApprovedResponse
  + VoiceUseAuthorization
  + voice SurfaceAuthorization
  -> immutable artifact
  -> signed SpeechTask
  -> stage-host
```

The three capabilities independently prove content safety, rights, and exact presentation. The
earliest expiry controls and none can infer or replace another.

```text
untrusted or approved source
  -> surface-specific normalization
  -> final-context moderation
  -> immutable surface authorization
  -> identifier-only dispatch
  -> renderer verifies authorization and expiry
  -> presentation outcome and clear
```

An absent registry entry, unknown renderer, changed payload digest, stale epoch, expired
authorization, failed moderation, or uncertain current renderer state produces no new output.

Raw platform chat must never be placed directly on the broadcast. A browser source or platform widget that bypasses VNova moderation is forbidden.

## Ownership And Emergency Control

- `session-runtime` owns input moderation, authorization requests, expiry, and approved dispatch.
- `packages/safety` is the Proposed sole mint boundary for surface authorization.
- `stage-host` owns final local voice, OBS, and VTube Studio presentation.
- The console can request or review output but never writes directly to a renderer.
- All surfaces have an operator-visible disable and renderer-level neutral/clear operation.
- Local e-stop overrides voice and the accepted rig-controlled surface scope.
- Cloud freeze halts new generation and dispatch.
- Recovery creates fresh authorization context; it does not revive expired or flushed output.

## Surface Registration Gate

Every adapter, OBS source, renderer, template family, and VTube Studio action family maps to one
versioned registered surface. An unregistered output is disabled. CI and rehearsal evidence must
prove that no raw platform widget, model payload, candidate text, arbitrary URL, script, markup, or
adapter command bypasses this registry.

The initial proposal renders every VNova-controlled surface through a stage-host-owned local
adapter/renderer. The production OBS scene collection itself is inventoried; unknown or remotely
mutable sources fail preflight. A non-rig renderer requires a later ADR with equivalent signed
verification, expiry, clear, partition, and emergency controls.

OD-006 decides whether a moderated overlay is implemented or omitted. Surface taxonomy, exact
moderation policies, delays, expiry, accessibility transformations, clear/disable SLOs, rights
rules, and retention remain human decisions tracked by ADR-021 and the
[open decision register](open-decisions.md).

No surface may enter production until ADR-021 is accepted and its surface-specific contract,
negative tests, fault injection, emergency behavior, observability, privacy, and protected review
evidence are complete.
