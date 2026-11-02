---
phase: 11-frozen-selection
plan: 01
subsystem: lookup-worker
tags: [retained-frame, request-generation, ocr, cancellation]
requires: [09-02, 10-01]
provides: [immutable retained scene events, same-frame selection queue, transient frame ownership]
affects: [11-02, 11-03]
tech-stack:
  added: []
  patterns: [stable scene identity with per-selection request generations, shared lookup and history path]
key-files:
  created: [.planning/phases/11-frozen-selection/11-01-SUMMARY.md]
  modified: [lookup/app.py, tests/test_app.py]
key-decisions:
  - Retain one bounded Capture and rerun existing recognition at each point rather than changing OCR or adding a cache.
  - A scene event supplies the immutable frame to the GUI once; ordinary result events carry only source geometry and selected-word box.
  - Fresh PRIMARY keeps ordinary lookup precedence and never creates a retained scene.
requirements-addressed: [CAPT-08, TRIG-05, TRIG-06]
requirements-completed: []
metrics:
  duration: not_aggregated
  tasks: 2
  files: 2
completed: 2026-11-02
---

# Phase 11 Plan 01: Retained-frame lookup worker

The worker retains one captured image, resolves subsequent points through the existing OCR/translation/history path, and invalidates scene ownership and stale work on cancellation or failure.

## Tasks and commits

| Task | Commit | Result |
|---|---|---|
| 1 RED | `6ee4fcd` | Scene API tests fail on absent enqueue/selection methods. |
| 1 GREEN | `10274a1` | Immutable scene contracts, bounded capture validation and same-frame selections; 26 app tests pass. |
| 2 RED | `ef52487` | Lifecycle tests fail on missing close and retained pixel references after dismiss/reload/stop/error. |
| 2 GREEN | `7df526c` | Stable-session cancellation, reference release, strict point/session checks and operational-error teardown; 38 app/hotkey tests pass. |

## Plan 02 integration contract

- `Scene(session_id, source)` is frozen; `source` is the original OCR `Frozen` with its immutable `Capture`, monitor, initial global logical point and available work area.
- `Engine.enqueue_scene(identity, snapshot=None)` uses existing `Source.freeze` once. OCR emits `Event(stage='scene', scene=Scene(...))` before `frozen`, `ready` and `context`; fresh PRIMARY emits only the existing ordinary stages.
- `Engine.select_scene(identity, session_id, point)` accepts a current request generation, exact integer session ID and finite in-monitor global logical coordinates. Call `begin()` for each selection. It returns a boolean; wrong/stale sessions and invalid points return false without queueing a lookup.
- A selected point replaces only `Frozen.point`; the exact original Capture is reused without another screenshot, cursor read or PRIMARY read. Each selection reuses existing `Source.resolve` and the sole translation/history/enrichment path.
- `Query.selection_box` and ready/context `Event.selection_box` carry the existing physical-image OCR box for the selected word. The GUI maps that box to its retained scene. Ordinary/default fields remain compatible.
- `Engine.close_scene(session_id=None)` drops the active scene and queued work and invalidates the request generation. A mismatched explicit session ID returns false without affecting a newer scene. An unspecified ID also cancels an initial queued scene before it has been published.
- Matching `dismiss`, reload, stop, failed resources and operational errors release engine frame ownership. `not_found` alone keeps the scene selectable. GUI callers must also release their received scene/image references on teardown; bounded in-flight OCR can retain its local source until it returns.
- Reused selections report capture time zero rather than counting the original capture duration again.

## Verification

Fresh final command: `python -m unittest tests.test_app tests.test_hotkey_capture -q` — **38 tests OK, zero skips, 1.225 s**. `git diff --check` reports no whitespace errors; only existing LF/CRLF conversion notices.

Regressions assert one freeze and exact image-object identity across points; automatic initial resolution; PRIMARY precedence; strict session IDs; NaN/infinite/huge/outside-monitor point rejection; bounded frame rejection; actual selection-box propagation; once-per-query history; stale ready/context suppression; weak-reference release after close/dismiss/reload/stop; queued raw snapshot release before resource initialization; and no-hit versus operational OCR error handling. Existing raw-capture and hotkey regressions remain intact.

## Deviations from Plan

None in scope or architecture. Capture timing is reset to zero on retained selections so measurements do not imply another capture. No OCR algorithm or cache, GUI, database, provider or VM changes were made.

## TDD Gate Compliance

Both tasks have failing-test commits before their corresponding feature commits. No known stubs or new undeclared security surfaces were found. Declared T-11-01/02/03 protections are covered by point/session validation, bounded transient ownership and existing current-generation persistence guards.

## Preservation and remaining acceptance

User changes in `lookup/ocr.py`, `tests/test_ocr_fallback.py`, `.omx/` and parent-owned planning state were not staged or reverted. Phase requirements remain pending overall: native surface/Owner integration is Plan 02; actual-product KDE/fullscreen/hover/input and complete cleanup acceptance is Plan 03. Worker tests do not claim either live compositor or human acceptance.

## Self-Check: PASSED

Both modified source/test files and this summary exist. Commits `6ee4fcd`, `10274a1`, `ef52487` and `7df526c` are present. Fresh final worker/hotkey verification passes. No tracked files were deleted by these commits.
