---
phase: 06-words-cards
plan: 01
subsystem: learning-core
tags: [sqlite, snapshots, review, csv, anki]
requires:
  - phase: 05.1-context
    provides: Exact persisted context/meaning snapshot
provides:
  - Independent immutable learning snapshots and safe history operations
  - Pure SM-2-derived preview with due/version guarded grading
  - Atomic CSV and escaped two-field Anki TSV exports
affects: [06-02, 06-03, 07-settings]
tech-stack:
  added: []
  patterns: [independent snapshots, compare-and-set review, atomic file replacement]
key-files:
  created:
    - lookup/learning.py
    - tests/test_learning.py
  modified:
    - lookup/store.py
    - tests/test_migrations.py
    - tests/test_core_imports.py
    - tests/test_store.py
key-decisions:
  - Cards copy one validated source pair and never follow later history enrichment or deletion.
  - Duplicate INSERT preserves every saved field and review state.
  - One pure preview supplies both button delays and persisted scheduler transitions.
  - Export materializes one cards-only SELECT before sibling temporary-file output and atomic replace.
requirements-completed: []
duration: 8min
completed: 2026-10-27
---

# Phase 6 Plan 01: Learning Core Summary

**Independent cards now preserve the exact selected translation/context pair, support deterministic persistent review, and export safely to CSV or two-field Anki TSV.**

## Accomplishments and API

- Additive V4 creates an independent `cards` table and due/word index, with no history foreign key. V3 words, contextual values, cache and counters survive migration.
- `list_words` provides bound literal search and allowlisted numeric/stable sorting; `delete_word` removes only history. Browsing never counts searches; deleting history leaves cards intact and the next lookup starts at one.
- `add_card(conn,snapshot,now=None)` returns `created` or `already_present`; duplicates do not replace source data or reset schedules. `add_history_card` reads the existing exact source pair once. Meaning requires its matching source span/provider; missing translation is refused. Exact context whitespace is preserved.
- `get_card`, `list_cards` and `due_cards` return plain dicts with word, translation, context, span, provider, created_at, due, repetitions, interval_days, ease and review_version. History rows retain the existing word/translation/context/count/first_seen/last_seen/lemma fields.
- `preview(state,rating)` returns repetitions, interval_days, ease and integer `delay` seconds. Hard/Good/Easy use the selected old-state SM-2-derived formula; Again resets repetitions/days and delays 600 seconds. Early successful intervals can match as explicitly researched.
- `grade_card(conn,word,expected_version,rating,now=None)` returns `applied` or `stale`, uses that same pure preview, and atomically checks version and due time. Double answers, concurrent state changes, invalid input and premature answers cannot overwrite accepted review state.
- `export_csv` preserves exact Unicode/quotes/newlines/tabs in three columns. `export_anki` emits documented directives and two escaped HTML fields, including visible context separation and safe line/tab encoding. Both read cards only, flush a sibling temporary file and atomically replace the destination; errors preserve its previous bytes and clean temporary files.
- Core import checks include the learning module and confirm stdlib-only imports with no side effects. Private errors use fixed `LearningError.reason` codes.

## Task Commits

1. Task 1 RED: `847d470` — immutable snapshots, history semantics and V3→V4 preservation.
2. Task 1 GREEN: `38a7be5` — independent cards and history queries.
3. Task 2 RED: `447f8cc` — preview/apply equality, stale review and lossless atomic export contracts.
4. Task 2 GREEN: `619370a` — deterministic scheduler and exporters.

## Validation Results

- Task 1 focused learning/migration/store/import suite: **71 tests OK, 2 skipped**.
- Final focused learning/migration/store/privacy/import suite: **82 tests OK, 2 skipped**.
- Final full discovery: **624 tests OK, 8 skipped**, 29.173 seconds, exit 0. Existing controlled VM setup-error output reported all restoration flags true.
- Covered exact contextual pair validation, late-history immutability, duplicate scheduling preservation, numeric 10-before-2 sorting, literal search, deletion/count reset, all ratings, ease floor, UTC due boundaries, restart persistence, concurrent compare-and-set refusal, huge invalid timestamps, CSV CR/LF/quotes/Unicode/tabs, escaped two-field TSV, and old destination preservation on replacement error.
- `git diff --check` for owned implementation/tests: exit 0. No tracked deletions or unresolved implementation stubs.

## Deviations and Limits

- **[Rule 1 — historical fixture compatibility]** The existing V2→V3 migration check and V3 schema-column check now open explicit `MIGRATIONS[:3]` fixtures; their historical assertions remain intact. Separate new coverage verifies default V4 and V3 data preservation. Parent authorized the narrow store-test ownership extension. The public current-version assertion is V4.
- **[Rule 2 — safe numeric boundary]** Time validation handles arbitrarily large integers with a fixed private error rather than `math.isfinite` integer-conversion overflow. Scheduler state and resulting delays are bounded before SQLite writes.
- **[Rule 1 — lossless line endings]** CSV uses CRLF record terminators so embedded bare CR as well as LF/CRLF is quoted and round-trips correctly. Anki HTML normalizes visible line breaks and encodes tabs inside fields.
- This unit validates the offline core and format semantics. Native windows, popup snapshot capture, physical tray paths, actual external Anki import and phase-level agent acceptance remain plans 02/03. No human acceptance or complete Phase 6 requirement is claimed here.
- No STATE, ROADMAP, config, requirement checkbox or pre-existing user document was changed by this executor. Parent owns workflow persistence.

## Self-Check: PASSED

All six implementation/test files and this summary exist. Task commits `847d470`, `38a7be5`, `447f8cc` and `619370a` exist. Fresh final verification passed after the last code change; no known stub prevents the core unit's goal.
