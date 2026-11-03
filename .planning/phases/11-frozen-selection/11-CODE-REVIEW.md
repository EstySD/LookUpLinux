---
phase: 11-frozen-selection
reviewed: 2026-11-03T03:33:46Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - lookup/app.py
  - lookup/gui.py
  - lookup/selection_gui.py
  - lookup/platform.py
  - tests/test_app.py
  - tests/test_app_gui.py
  - tests/test_selection_gui.py
  - tests/test_platform.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
reviewed_through: a3d0c50
---

# Phase 11: Code Review Report

**Depth:** Standard, with cross-file tracing of worker ownership, Qt events and packaging consumers.
**Status:** No outstanding findings after independent source and targeted regression recheck. Native product acceptance remains separate.

## Scope

Reviewed the retained-scene worker and native layer/Owner changes since `ae9af73`, including the error-path correction in `a760500` and KWin search/ownership corrections in `a3d0c50`. The resumed review inspected the corrected selectors, action consumers and regressions introduced by `54826f3` and `2f852a7`. Existing user OCR/OMX edits were excluded. No source files were changed by the reviewer.

Traced initial capture and PRIMARY precedence, retained selections and request identities, shared history/enrichment, frame bounds and cleanup, image-header validation and opaque painting, logical/physical coordinate mapping, internal focus transitions, cancellation, timeout, reinvocation, settings invalidation and shutdown. Existing package staging recursively includes Python files under `lookup`, so the added native module is included without a separate package file-list update.

## Resolved BLOCKER

### CR-01: Placement failure left the retained input layer active

**Classification:** BLOCKER — resolved in `a760500`.

**File:** `lookup/gui.py:886` (`Owner.focus_done`).

**Issue:** With an active scene, failed popup focus/placement updated the popup to `placement_failed` but retained the visible input-taking layer and its image. The ordinary-popup fallback was insufficient for a scene session and violated operational-error teardown.

**Original reproduction:** Construct the existing GUI-test scene, present the frozen state, set `_paint_revision` to the active presentation revision, and call `focus_done((current_id, revision, None, 'focus_failed'))`. The layer remained visible and `scene_window` still owned it while the error appeared.

**Correction:** The scene-specific error path now ends the entire scene before creating a fresh ordinary error request and returns before stale focus/arming callbacks can continue. The regression covers both waiting-paint and initial/no-paint states, cleared waiting results/card binding and rejection of the old result.

**Independent recheck:** Repeated the same focused reproduction after `a760500`: layer visible `False`, scene still owned `False`, pixels released `True`, old generation current `False`. Inspected the additional no-paint regression and the shared teardown path.

## Resolved native-discovered BLOCKER findings

### CR-02: Popup placement selected and moved the retained layer

**Classification:** BLOCKER — resolved in `a3d0c50`.

**File:** `lookup/gui.py:878` (`Owner.start_focus`).

**Issue:** `kdotool search --pid PID --name TITLE` uses OR matching by default. With both layer and popup owned by the same process, the layer also satisfies the PID branch and can be returned first. The placement loop then moves the fullscreen input layer to the popup coordinates. Actual product testing observed the scene offset by the popup's displacement, breaking frame/pointer agreement and exposing an underlying input area. `11-product-layer-attempt2.png` retains the failed run; it is not acceptance evidence.

**Fix:** Require conjunction with `search --all --pid PID --name ^ESCAPED_TITLE$`, then act only on the selected popup UUID. Keep a regression with the same-PID layer and a foreign-PID window sharing the popup title.

**Correction and independent recheck:** The current query includes `--all`, the current PID and an anchored `re.escape(TITLE)` expression. The regression models the same-PID layer, foreign-PID same-title window and same-PID suffixed title; all three placement actions target only the exact owned popup. The reviewer reran this regression successfully on the corrected source.

### CR-03: Window ownership check accepted unrelated application windows

**Classification:** BLOCKER — resolved in `a3d0c50`.

**File:** `lookup/platform.py:267` (`owned_window`; consumed by `window_action`).

**Issue:** PID-only `search --pid PID` does not imply PID-only matching in kdotool. When no textual criterion is specified, its parser enables textual fields with an empty matching expression; default OR matching consequently includes unrelated windows. The membership check in `window_action` could therefore authorize moving/raising/activating a foreign UUID. The live query returned desktop/panel/source windows together with owned windows.

**Fix:** Use `search --all --pid PID` so the PID condition is mandatory. Assert that a foreign UUID is rejected before an action command is issued while an owned UUID remains usable.

**Correction and independent recheck:** `owned_window` now uses the conjunctive PID query. `window_action` still checks membership before issuing a command. The reviewer reran the regression that rejects a foreign UUID without any action invocation and then accepts an owned UUID. PID validation, bounded command output and UUID syntax checks remain in place.

**Primary-source confirmation for CR-02/CR-03:** The [upstream search parser](https://raw.githubusercontent.com/jinliu/kdotool/master/src/main.rs) defaults `match_all` to false, enables it with `--all`, and supplies default textual criteria when none were given. Its [search template](https://raw.githubusercontent.com/jinliu/kdotool/master/src/templates.rs) joins criteria with OR or AND accordingly. The native observations establish that these semantics affect the installed tool; documentation alone is not the runtime proof.

## Fresh reviewer checks

`python -m unittest tests.test_app_gui.GuiTests.test_scene_placement_failure_releases_layer_before_ordinary_error tests.test_app_gui.GuiTests.test_focus_moves_only_popup_when_scene_shares_process tests.test_platform.BoundaryTests.test_window_ownership_requires_pid_filter_conjunction -q`: 3 tests, OK, 0 skips, 0.161 s. `git diff --check` on the corrected production/test files exited 0. No full suite or VM operations were repeated by this reviewer.

## Acceptance boundary

All three recorded blockers are corrected and rechecked at source/regression level; no further proven correctness or security defect was found in this resumed review. Native stacking/focus timing, full-monitor geometry, input isolation, foreign-window rejection and fullscreen product behavior must still be rerun on the corrected revision. The failed native screenshots remain historical failures, not acceptance evidence. Earlier offscreen results and the feasibility probe do not replace integrated-product evidence. No human acceptance is claimed.

---

Reviewer: independent gsd-code-reviewer. Report not committed by the reviewer.
