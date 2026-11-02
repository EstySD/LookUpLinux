---
phase: 10-compact-popup
reviewed: 2026-11-02
depth: standard
files_reviewed: 6
files_reviewed_list:
  - lookup/config.py
  - lookup/settings_gui.py
  - lookup/gui.py
  - tests/test_config.py
  - tests/test_settings_gui.py
  - tests/test_app_gui.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 10: Code Review Report

Reviewed implementation through `5dab98f` and rechecked the caption correction in `0e6758e` plus compact heading correction in `2cb628a`, scoped to the six Phase 10 source/test files. Pre-existing OCR and OMX changes are excluded. No source edits or duplicate suite execution were performed. No outstanding blockers or warnings remain in this review scope.

## Resolved findings

### WR-01 — WARNING, RESOLVED: Long dictionary names clip the disclosure action

**File:** `lookup/gui.py:316`, `lookup/gui.py:323`

**Issue:** The fixed-width popup gives each disclosure button about 408 logical pixels, but its single-line caption contains the entire unbounded dictionary name. `QSizePolicy.Ignored` prevents the button from widening the popup but does not wrap or elide its text. Native centered text is clipped when the caption is wider than the control, so a sufficiently long dictionary name can hide the actionable `Показать полную статью` / `Свернуть статью` portion and the visible change of state. Long dictionary filenames and metadata are valid inputs. The full accessible name helps assistive technology but does not repair the sighted interaction.

**Evidence:** A focused host Qt metrics probe with the same caption prefix and a 210-character dictionary name measured 2820 pixels of caption text for a 408-pixel button. QPushButton has no automatic text-elide mode. Existing dictionary headings use wrapping plain-text widgets, so the new disclosure introduces this particular clipping path.

**Fix:** Keep the action prefix visible and elide only the dictionary-name portion to the available button/font width, while retaining the complete caption in the accessible name and tooltip. Alternatively use a wrapping native disclosure label. Recompute the visible caption when the popup width changes. Add a narrow native Qt regression for a long dictionary name and expansion/collapse.

**Resolution rechecked:** `Popup.article_caption()` now preserves the action prefix, uses `fontMetrics().elidedText()` for the dictionary name within the popup width budget, and retains the full caption in the accessible name and tooltip. `size_for()` refreshes captions after selecting the available width, and toggling refreshes the action/state. Dynamic disclosure bookkeeping is cleared with each result. The added regression checks the long-name width, intact action prefix, complete accessible/tooltip caption, and Return-key expansion. The correction addresses WR-01 without changing result, settings, or card data.

**Final heading follow-up:** `2cb628a` also bounds each visible summary dictionary name to 80 characters including its ellipsis, so long metadata cannot occupy an arbitrary number of lines before meanings. The full name remains in the heading tooltip and accessible name. The existing long-name regression now checks this visible bound and tooltip. The guard for an absent heading preserves the existing total display-budget behavior. No new issue was identified in the final delta.

## Reviewed boundaries

Strict boolean loading/saving, atomic merge and existing acknowledgement/rollback paths were traced. Summaries precede detail creation; the existing text/block budget remains applied to full text; rendering stays plain text. Per-result immutable preferences guard late updates, and card/history payload paths are unchanged. No additional security or data-loss finding was identified in this scope.

Live KDE placement/focus acceptance remains unverified because the original-VM ownership guard blocks target execution. This is an acceptance limit, not evidence of a source defect. Missing original photo/article reproduction remains separately documented.

_Reviewer: independent gsd-code-reviewer._
