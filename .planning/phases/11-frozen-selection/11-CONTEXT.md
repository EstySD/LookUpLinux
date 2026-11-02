# Phase 11 — Frozen-scene word selection

Gathered: 2026-11-02. Agent decisions under `gsd next --auto`; no human acceptance.

## Boundary
CAPT-08, TRIG-05 and TRIG-06: choose words from one retained scene, preserve available hover text, prevent pointer movements from reaching the underlying application, and restore control after Esc/close/repeated invocation/error, including real fullscreen.

## Automatic decisions
- Reuse the Phase 9 captured frame/cursor contract and Phase 10 popup preferences; avoid a new capture provider or second lookup pipeline unless research proves necessary.
- Select one word at a time from the retained scene; repeated selections may use that same scene. Do not add multi-word gestures or persistence of screenshots.
- Preserve CAPT-02: a fresh valid PRIMARY selection keeps its existing lookup precedence and normal popup. On the OCR path, the existing hotkey opens the retained layer and automatically looks up the initial pointed word, preserving the one-hotkey result. Clicking another word selects it from the same retained frame and ignores clipboard selection; no extra shortcut or entry mode is added.
- Preserve actual source hover text visible at invocation. Do not claim that displaying an image freezes the source application or enables new source hover interactions.
- The selection layer must intercept pointer input across its covered source area. Define and prove keyboard cancellation and cleanup before choosing implementation.
- Keep an explicit close action and Esc. Reinvocation replaces or dismisses the active layer safely; errors must release layer/input ownership. Preserve normal popup/card/history behavior.
- Esc, explicit close, error and configured timeout terminate the complete selection session, including popup, and release input. Focus movement between the owned popup and layer stays within the session; external focus ends it.
- Use only the documented owned clone, protect existing profiles, and restore its initial powered-off state. Never control or enter the original VM or bypass clone identity/disk/network isolation checks.

## Mandatory research gate
ROADMAP requires actual proof of KDE Wayland capture/input/hover behavior before approving implementation. A retained screenshot alone does not prove source application freezing or input isolation. Research must distinguish the requested observable scene/hover/input behavior from application execution state and report a blocker if it cannot be established.

Initial preflight rejected operation while original `arch-kde` was running. Denis explicitly authorized separate VM instances for concurrent agents. On 2026-11-02, the clone was verified to have an independent base VDI, distinct MAC and SSH port, and no shared folders. The preflight now checks disk/network isolation instead of requiring the original to be powered off. Concurrent operation is authorized; do not touch the original VM. The mandatory live research gate remains pending until the owned-clone probe succeeds.

## Required context
Read docs/lookupper/architecture.md, linux-requirements.md and evidence.md; existing observations do not prove untested Linux behavior. Keep Danila/human confirmation separate from agent evidence.
