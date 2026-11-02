---
phase: 11-frozen-selection
plan: 02
subsystem: native-selection-ui
tags: [qt, retained-scene, focus, input-ownership]
requires: [11-01]
provides: [native retained-scene surface, hotkey scene entry, shared popup and layer lifecycle]
affects: [11-03, 14]
tech-stack:
  added: []
  patterns: [opaque retained-image painting, owned-surface focus domain, idempotent scene teardown]
key-files:
  created: [lookup/selection_gui.py, tests/test_selection_gui.py]
  modified: [lookup/gui.py, tests/test_app_gui.py, lookup/platform.py, tests/test_platform.py]
key-decisions:
  - Keep the captured monitor coordinate origin fixed; overlay controls never shift the source image.
  - Treat the popup and selection surface as one focus domain, with a deferred null-focus check after initial owned focus.
  - Reuse the existing popup timer even when no-hit or pending selection hides the popup.
requirements-addressed: [CAPT-08, TRIG-05, TRIG-06]
requirements-completed: []
metrics:
  duration: not_aggregated
  tasks: 2
  files: 6
completed: 2026-11-02
---

# Phase 11 Plan 02: Native retained-scene selection and popup ownership

The OCR hotkey now displays the retained scene and initial result; later clicks reuse that scene through Engine, while popup and layer share cancellation, timeout, focus and transient-image cleanup.

## Tasks and commits

| Task | Commit | Result |
|---|---|---|
| 1 RED | `f147996` | Native surface tests fail on the missing selection module. |
| 1 GREEN | `0e0b7e0` | Lazy native layer with bounded image decoding, opaque retained painting, mapped selection box, controls and local input handling; 3 native tests pass. |
| 2 RED | `934334e` | Scene entry, selection and all-session cleanup tests fail on missing Owner integration. |
| 2 GREEN | `339bfe1` | Engine scene entry/reselection, shared lifecycle, focus domain and compatible PRIMARY/card/settings behavior; 103 scoped tests pass. |
| Review correction RED | `11b7fc5` | Reproduce active retained layer after asynchronous focus/placement failure, with and without a pending paint revision. |
| Review correction GREEN | `a760500` | End the scene and invalidate queued work before showing an ordinary placement error; fresh final verification below. |
| Native-probe correction RED | `54826f3`, `2f852a7` | Reproduce wrong same-process surface selection and acceptance of foreign-process window IDs. |
| Native-probe correction GREEN | `a3d0c50` | Require conjunctive KWin PID/title matching and strict PID ownership before window actions. |

## Integration contract

- `selection_gui.components()` returns `SelectionLayer(scene)` lazily. It keeps a decoded QImage and geometry, not the Scene/Capture bytes. PNG header dimensions are checked before decoding; invalid or oversized frames cannot create a blocking surface.
- `selected(global_logical_point)` drives `Engine.begin()` and `select_scene` without capture or PRIMARY reads. `set_selection(word, physical_image_box)` maps the actual OCR box into displayed monitor coordinates.
- The frame is painted over an opaque base, followed by the 20% palette tint. Pointer events stay local; clicks on instruction controls do not become source-word clicks. Esc and native close are reachable from controls.
- `Owner.scene_window` and `_scene_id` describe the current selection session. OCR hotkeys use `enqueue_scene`; PRIMARY events retain ordinary-popup behavior. Scene events arrive before frozen/ready; popup results and cards continue through existing binding paths.
- `_end_scene()` hides both surfaces, clears decoded pixels and queued presentation/focus work, closes the Engine scene and invalidates results. Esc, either close action, repeat hotkey, configured timeout, settings invalidation, external focus, shutdown and operational error all use this path.
- No-hit retains the layer with actionable status and a running inactivity timer. Ordinary useful offline/provider results remain available. Layer interactions reset the same existing timer even while the popup is hidden.
- Popup/layer focus transfers are internal. Native focus classification arms only after an owned surface receives focus, then waits 75 ms for transient Wayland null focus to settle; callbacks are session-bound. Actual compositor behavior and transient stacking remain the mandatory Plan 03 product gate.

## Verification

Fresh final scoped command after review/native-probe corrections: `python -m unittest tests.test_selection_gui tests.test_app_gui tests.test_settings_gui tests.test_app tests.test_hotkey_capture tests.test_platform -q` — **118 tests OK, zero skips, 7.176 s**.

Fresh font-backed command loads the installed Segoe UI font only in the test process and runs selection/GUI/settings/platform suites — **80 tests OK, zero skips, 5.885 s**. Product fonts remain system-owned. Expected libpng diagnostics come from deliberately malformed-frame rejection cases.

Coverage includes negative monitor origins and 100%/125%/200% coordinate mapping; opaque pixels; actual OCR box mapping; native keyboard close; status/close bounds; repeated selection and stale-result suppression; fresh PRIMARY; unchanged card binding; all session exit routes; no-hit timer and interaction reset; duplicate hotkey coalescing; initial focus arming and internal/external focus classification; malformed image rejection; and pending capture cancellation. Existing Phase 9/10 and worker regressions continue to pass.

`git diff --check` found no whitespace errors; only existing LF/CRLF conversion notices. No VM commands were run by this executor, and host offscreen checks do not claim native KDE acceptance.

## Deviations from Plan

- **[Rule 1 — Bug]** Instruction-label mouse events can propagate to their parent. The layer now excludes the whole toolbar from word selection, with a regression, so controls cannot accidentally select text underneath them.
- **[Rule 1 — Bug]** Initial Wayland activation and transfers between owned surfaces can temporarily have null focus. Focus classification is armed after actual owned focus and deferred briefly instead of tearing down a newly shown layer; final real-compositor verification remains required.
- **[Rule 1 — Bug]** Independent review reproduced a placement/focus callback that displayed an error while retaining the input-taking scene. This callback now calls shared scene teardown before creating a fresh ordinary error result. Regressions verify image release, cancellation of queued readiness/context and rejection of stale results in both paint-wait and initial-focus paths.
- **[Rules 1/2 — Bug and missing ownership enforcement]** The native product probe found that the existing kdotool search selected and moved the retained layer as though it were the popup. Upstream `step_search` defaults to OR matching; the parent approved extending this correction to the existing platform ownership guard. Popup lookup now requires `--all`, the current PID and an anchored escaped title; ownership lookup requires `--all --pid`. Regressions reject the layer, same-title foreign PID, suffixed title and foreign window IDs before any action. Native verification must restage both corrected modules. Upstream API source: https://raw.githubusercontent.com/jinliu/kdotool/master/src/main.rs.
- The Context7 CLI lookup did not return and was stopped. Official Qt QWidget/QGuiApplication documentation was retrieved directly for native surface and focus APIs; no new dependency was introduced.

## TDD Gate Compliance

Both implementation tasks have RED commits before GREEN commits. Follow-up integration regressions preserve the original card contract by supplying a valid translation before expecting a displayed card pair.

## Preservation and remaining acceptance

User modifications in `lookup/ocr.py`, `tests/test_ocr_fallback.py`, `.omx/`, and parent-owned planning state were not staged or reverted. Engine/OCR/provider/database behavior was not modified in this plan; the parent-authorized platform change strengthens the existing KWin ownership boundary. No known feature-blocking stubs or new undeclared security surfaces remain.

Plan 03 must prove the actual product's initial activation, popup/layer stacking and focus transfers, key-time hover capture, repeated same-frame OCR selection, absence of underlying application input, and release after every exit/error path over real KDE/fullscreen. The feasibility probe is not substituted for that acceptance; no human acceptance is claimed.

## Self-Check: PASSED

All four initially declared source/test files, the two parent-authorized platform files and this summary exist. RED/GREEN commits `f147996`, `0e0b7e0`, `934334e`, `339bfe1`, `11b7fc5`, `a760500`, `54826f3`, `2f852a7`, `a3d0c50` are present; fresh scoped and font-backed verification pass. No tracked file was deleted. Shared workflow state and final requirement acceptance remain owned by the parent orchestrator.
