# Phase 11 — Frozen-scene word selection

Gathered: 2026-11-02. Agent decisions under `gsd next --auto`; no human acceptance.

## Boundary
CAPT-08, TRIG-05 and TRIG-06: choose words from one retained scene, preserve available hover text, prevent pointer movements from reaching the underlying application, and restore control after Esc/close/repeated invocation/error, including real fullscreen.

## Automatic decisions
- Reuse the Phase 9 captured frame/cursor contract and Phase 10 popup preferences; avoid a new capture provider or second lookup pipeline unless research proves necessary.
- Select one word at a time from the retained scene; repeated selections may use that same scene. Do not add multi-word gestures or persistence of screenshots.
- Preserve actual source hover text visible at invocation. Do not claim that displaying an image freezes the source application or enables new source hover interactions.
- The selection layer must intercept pointer input across its covered source area. Define and prove keyboard cancellation and cleanup before choosing implementation.
- Keep an explicit close action and Esc. Reinvocation replaces or dismisses the active layer safely; errors must release layer/input ownership. Preserve normal popup/card/history behavior.
- Use only the documented owned clone, protect existing profiles, and restore its initial powered-off state. Never control or enter the original VM or bypass the identity/state guard.

## Mandatory research gate
ROADMAP requires actual proof of KDE Wayland capture/input/hover behavior before approving implementation. A retained screenshot alone does not prove source application freezing or input isolation. Research must distinguish the requested observable scene/hover/input behavior from application execution state and report a blocker if it cannot be established.

Current owned-clone preflight rejects operation: `Original VM must remain powered off`; original `arch-kde` is running. This is a genuine obstacle to mandatory real-environment evidence for this phase, unlike Phase 10's nonblocking compositor limitation. Perform useful source/documentation research, retain a concrete probe plan, and do not approve an unproven implementation.

## Required context
Read docs/lookupper/architecture.md, linux-requirements.md and evidence.md; existing observations do not prove untested Linux behavior. Keep Danila/human confirmation separate from agent evidence.
