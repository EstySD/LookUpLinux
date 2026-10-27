---
phase: 06-words-cards
reviewed: 2026-10-27
depth: standard
files_reviewed: 11
files_reviewed_list:
  - lookup/learning.py
  - lookup/learning_gui.py
  - lookup/store.py
  - lookup/gui.py
  - lookup/app.py
  - tests/test_learning.py
  - tests/test_learning_gui.py
  - tests/test_app_gui.py
  - tests/test_app.py
  - tests/test_migrations.py
  - tests/test_core_imports.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 6: Code Review Report

Independent standard review found no concrete BLOCKER or WARNING in the submitted learning core, native widgets, migration and popup integration. This is a code-review result, not phase acceptance or proof of the pending native/Anki import checks.

## Reviewed Boundaries

- Popup creation copies the displayed result and event context/span synchronously. It does not re-query mutable history; closed, loading, sentence-only and superseded views reject creation. Existing cards are immutable under duplicate additions and later enrichment.
- History queries bind search values and allowlist sort columns; numeric count sorting occurs in SQL. History deletion does not cascade into cards. GUI learning operations use a separate GUI-owned SQLite connection with bounded lock waiting.
- Scheduler preview and application share one transition function. Grading uses the loaded version and due-time predicate in a compare-and-set update; duplicate/stale answers cannot overwrite a newer schedule. Reveal gating prevents a second queued click from grading the next card.
- Export materializes one card snapshot, uses three CSV columns or two escaped Anki fields with supported directives, and writes through a sibling temporary file plus atomic replacement. Failure cleanup preserves an existing destination. No provider HTML is rendered.
- V4 is additive and retains history/contextual cache data. Learning windows close independently of the tray owner and release their GUI connection on application quit. The current no-due copy correctly avoids implying that an Again card cannot become due later today.

## Validation Evidence

Executed against the reviewed working tree:

`python -m unittest tests.test_learning tests.test_learning_gui tests.test_app_gui tests.test_migrations`

**77 tests passed, 2 skipped** for host-only POSIX file-mode checks. The assertions inspect immutable snapshots, scheduler transitions/staleness, exact CSV/TSV contents, export rollback, native widget reveal/error behavior and popup lifecycle. Passing tests were used to check the inspected contracts, not as a substitute for source review.

Actual native VM acceptance and isolated Anki import remain the separate execution harness's responsibility. Phase 5.1's public-provider HTTP 429 limitation does not affect these offline learning operations.

No production files were modified and no commit was created by this review.
