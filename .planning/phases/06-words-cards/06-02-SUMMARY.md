---
phase: 06-words-cards
plan: 02
subsystem: gui
requires:
  - phase: 06-01
    provides: Independent card snapshots, scheduling and export core
provides:
  - Native Words and Review windows reachable from tray
  - Frozen displayed popup snapshots with exact occurrence metadata
  - GUI-owned SQLite connection and private retryable failures
key-files:
  created:
    - lookup/learning_gui.py
    - tests/test_learning_gui.py
  modified:
    - lookup/gui.py
    - lookup/app.py
    - tests/test_app_gui.py
    - tests/test_app.py
requirements-completed: [LIST-01, LIST-02, POP-04, LEARN-01, LEARN-02]
completed: 2026-10-27
---

# Phase 6 Plan 02: Native Learning Workflows

`lookup/learning_gui.py` implements reusable native Words/Review windows with plain text and caller-owned connection. Words provides numeric sorting, search, selected add/delete, clear independent-card deletion copy and CSV/Anki save dialogs. Review reveals the saved answer before enabling four rating buttons, uses core preview intervals and version-guarded grading, and presents an empty queue honestly.

`lookup/gui.py` enables Words/Review while leaving Settings to Phase 7. One lazy GUI connection has a short opening/busy deadline, stays separate from the engine worker and closes with owned windows at quit. Other open learning windows refresh after changes without resetting the emitting window's feedback.

The popup button copies the actually rendered result/context/source span at click. A newer history row is never consulted. Contextual meaning is preferred when displayed; dictionary fallback stays frozen if late meaning arrives after card creation. Known/duplicate cards are reported without changing the snapshot or schedule. Loading, error, sentence, untranslated, hidden and superseded results cannot add.

## Validation Results

- Focused application/native learning/core/privacy suite: **62 tests OK**, zero skips, 2.637s.
- Full host suite: **636 tests OK**, eight known Windows/environment/opt-in skips, 26.294s.
- Whitespace checks on changed sources/tests: exit 0.
- Real widget checks include count/search/header sorting, duplicate/deletion independence, reveal/interval/one-grade/restart, atomic export and canceled dialogs, retryable private DB errors, reusable windows/closed connection, and immutable popup snapshots across late enrichment and mutable history.
- Unit 03 owns actual native VM observation, all target-only checks and isolated Anki import. This summary does not claim those observations or human acceptance.

## Commits and Execution Adjustments

- Native window tests/implementation: 1f69adb, a2a9b2c.
- Application event metadata, tray/popup wiring and integration tests: 4afded7.
- App Event lacked the selected span needed by strict contextual-card validation. Added a defaulted span at the end of Event and propagated Query.span on ready/context events; existing positional calls remain compatible. The plan was updated to declare those files and tests.
- Existing V3 store assertions were explicitly preserved by the prior unit; its plan scope now records the required test_store caller adjustment.

## Limits

No new network dependency is introduced. The Phase 5.1 public-provider VM limit remains unchanged and does not affect local history/cards/review/export. Actual Anki import and native visual evidence remain Unit 03 checks.

## Self-Check: PASSED

All declared implementation/test files exist and scoped commits are present. Both planned tasks have focused and full-suite evidence.
