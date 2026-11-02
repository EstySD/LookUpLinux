# Phase 11 — Frozen selection research

Researched: 2026-11-02. Status: BLOCKED at mandatory live research gate. Confidence: HIGH for inspected code/contracts; feasibility unproven.

## User Constraints

The complete locked decisions are in `11-CONTEXT.md`. Preserve the Phase 9 frame/cursor contract and Phase 10 preferences. Select individual words repeatedly from one retained scene; no persistent screenshots or new gestures. Preserve hover text visible at invocation without claiming a screenshot freezes source execution. Intercept pointer input; Esc, close, reinvocation and errors must restore control, including real fullscreen. Use only the protected owned clone; never enter/control the original VM or bypass its guard. [VERIFIED: 11-CONTEXT.md]

## Phase Requirements

| Requirement | Required proof |
|---|---|
| CAPT-08 | Multiple selections use one retained frame, despite source animation. |
| TRIG-05 | Captured hover text remains selectable; actual pointer movements are absent from source input logs while layer is active. |
| TRIG-06 | Esc/close/reinvoke/error restore real application input, including fullscreen. |

These remain pending; static API documentation cannot establish them. [VERIFIED: REQUIREMENTS.md, ROADMAP Phase 11 research gate]

## Summary

Probe a native Qt selection surface first, retaining the existing compositor-produced image and OCR geometry. Do not approve implementation until actual KWin input/stacking/hover behavior passes the probe below. A client surface displaying an old frame is distinct from pausing the source application; none of the inspected code proves source execution is suspended. [VERIFIED: native/kwin-capture/capture.cpp snapshot and InputEventSpy paths; 11-CONTEXT.md]

## Architectural Responsibility Map

| Capability | Primary owner | Secondary owner |
|---|---|---|
| Key-time frame/cursor | Existing native KWin capture | Python capture consumer |
| Retained scene selection | Native Qt layer, subject to probe | Existing OCR coordinate selection |
| Actual input delivery and fullscreen stacking | KWin/Wayland compositor | Client surface input region |
| Lookup/cards/preferences | Existing Python pipeline | Phase 10 popup |

These boundaries follow inspected code and protocol responsibilities; Qt layer sufficiency remains an experimental hypothesis. [VERIFIED: capture.cpp; lookup/gui.py; lookup/ocr.py; official Wayland protocol]

## Standard Stack and Architecture Patterns

Reuse Python/PyQt6, current KWin plugin and existing OCR `select_word`/transform structures. No new package/version recommendation or installation is justified before the gate. Current plugin observes input via `InputEventSpy` and snapshots an output; observing pointer events is not evidence of filtering their delivery. [VERIFIED: native/kwin-capture/capture.cpp; lookup/ocr.py]

Qt exposes mouse/keyboard grab and release methods, but the generic QWidget documentation does not prove a particular Wayland global grab or fullscreen behavior. Treat grab success as something to measure, not a platform guarantee. [CITED: https://doc.qt.io/qt-6/qwidget.html#grabMouse]

Do not set `WindowTransparentForInput`: Qt explicitly defines it as passing input through. Visual translucency must not be confused with input transparency. Wayland surface input-region semantics are a separate contract from painted alpha. [CITED: https://doc.qt.io/qt-6/qt.html#WindowType-enum] [CITED: https://wayland.freedesktop.org/docs/html/apa.html#protocol-spec-wl_surface-request-set_input_region]

## Don't Hand-Roll / Common Pitfalls

- Reuse captured image/cursor transforms; recapturing after layer activation can select the overlay or a later scene. [VERIFIED: Phase 9 implementation and context contract]
- Do not use process suspension as an assumed substitute for hover retention or safe input isolation; that behavior has not been approved or tested. [VERIFIED: Phase 11 scope]
- A screenshot alone cannot prove absence of underlying motion events. Measure source event counters with real input. [VERIFIED: ROADMAP mandatory research gate]
- Preserve frozen pixels independently of a translucent tint: transparency over the live underlying application can expose motion. This is a probe acceptance condition, not proven implementation behavior. [VERIFIED: CAPT-08]
- Centralize layer cleanup across cancellation/error/reinvocation; a successful Esc test alone does not prove every exit path. [VERIFIED: TRIG-06]

## Environment Availability

Host native offscreen PyQt6 is available, but it cannot supply KDE compositor evidence. Owned-clone preflight was repeated during this research and still rejects operation with `Original VM must remain powered off`. No guest was entered, controlled or launched. The documented script pins clone UUID/network and requires original VM poweroff. [VERIFIED: tools/check_package_vm.ps1 and fresh preflight output]

## Mandatory Probe — Not an Approved Implementation Plan

1. Once the documented preflight passes, root may start only the owned clone and record initial profile/state. Establish cleanup and independent escape path before input experiments. [VERIFIED: project VM contract]
2. Use a source fixture with visible hover tooltip, moving frame counter and logged pointer/button/key events. Capture the tooltip and frame identity through the existing physical-hotkey path. Preserve logs and coordinates. [PROPOSED PROBE: requirements-derived]
3. Present a native input-taking selection surface containing the retained pixels; move/click across its source area and select at least two words. Assert identical frame identity, unchanged captured tooltip, correct transformed OCR words and zero new source pointer/button events. Separately record whether source execution continues; do not label a visual snapshot an application freeze. [PROPOSED PROBE: CAPT-08/TRIG-05]
4. Repeat at supported scale cases and over a real fullscreen application. Verify layer stacking, visible controls and that source input resumes after Esc, close, reinvocation, injected OCR failure and forced layer-process exit. Preserve actual source input logs rather than relying on the layer reporting receipt. [PROPOSED PROBE: TRIG-06]
5. Restore profile, stop owned clone to initial powered-off state, retain raw evidence and update this research gate. If behavior fails, investigate compositor-side filtering/overlay responsibility using version-matched KWin source; do not weaken acceptance. [PROPOSED PROBE: mandatory research gate]

## Validation Architecture

Existing unittest/PyQt6 infrastructure can later cover retained frame lifetime, transformations, generations and cleanup callbacks; focused commands are `python -m unittest tests.test_app_gui tests.test_app`. These do not replace the live probe. No executable Phase 11 plan or test infrastructure has been approved. [VERIFIED: existing tests; ROADMAP]

## Security Domain

Keep captured pixels transient, bounded and local; prevent stale frames crossing request identity. Input ownership cleanup is the main denial-of-service boundary. Existing peer/capture validation must remain in place; no new authentication/network/cryptography component is proposed. [VERIFIED: existing capture ownership checks; Phase 11 constraints]

## Project Constraints (from AGENTS.md)

No root AGENTS.md exists; session-provided directives require autonomous scoped work, preserving user edits and verifying claims. Original VM preservation remains mandatory. Research touched only this document, leaving OCR/OMX and product source intact. [VERIFIED: Test-Path AGENTS.md; task/session instructions]

## Open Questions / Gate Disposition

BLOCKED: Real KDE hover retention, input isolation and fullscreen cleanup are not established. The immediate obstacle is the original-VM-running guard, not demonstrated platform impossibility. Resume with the safe documented preflight and the probe above; no user design choice or generic approval is required. [VERIFIED: fresh preflight; absence of Phase 11 runtime evidence]

## Sources

- Inspected local CONTEXT, REQUIREMENTS/ROADMAP, capture.cpp, gui.py, ocr.py and VM guard.
- Existing Lookupper evidence records Q08 as partial and does not prove Linux freeze/input semantics. [VERIFIED: docs/lookupper/evidence.md]
- Official Qt QWidget/window flag docs and official Wayland protocol URLs cited above were retrieved during research; APIs are documentary evidence only.

No training-only platform impossibility claims or recommended new dependencies are asserted. [VERIFIED: scope of this research]
