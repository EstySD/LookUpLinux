---
phase: 06-words-cards
status: complete
source: agent acceptance under explicit --auto
started: 2026-10-27
updated: 2026-10-27
---

# Phase 6 Agent Acceptance

No human acceptance is claimed. Independent verification is in `06-VERIFICATION.md`; detailed native/import evidence is in `learning-native/`.

## Current Test

[testing complete]

## Tests

### 1. Tray Words, sorting and search
expected: Actual Words window opens, initially sorts numeric count descending, changes sorting by header and searches without recounting.
result: pass
source: native production window observations and independent core/widget checks

### 2. History deletion and card independence
expected: History add creates an immutable card; duplicate preserves its data/schedule; history deletion retains the card; next accepted search starts at count 1.
result: pass
source: native Engine/storage observations and independent tests

### 3. Popup exact source pair
expected: Adding uses displayed contextual meaning, exact multiline source/span/provider or current dictionary fallback; late replies/newer history never rewrite the saved card.
result: pass
source: actual popup button/storage observations and independent event-to-snapshot trace/tests

### 4. Due review and persistence
expected: Reveal precedes grading; four displayed intervals equal applied transitions; duplicate/stale grade is refused; restart retains schedule; empty queue is explicit.
result: pass
source: native review/database restart observations and independent scheduling/widget tests

### 5. CSV and actual Anki import
expected: Exact snapshots survive CSV/unchanged Anki TSV export and actual import, including Unicode, literal markup and multiline context; cancel/failure preserves destination.
result: pass
source: production export/dialog observations, official Anki 26.9.3 Rust importer and independent exact-field/hash assertions

### 6. Native presentation and final cleanup
expected: Light/dark Words/Review fields/actions are readable and plain text; final owned worker/windows/database/environment/XDG profile are cleaned up.
result: pass
source: independent inspection of four native screenshots and six final-run cleanup flags

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0

## Limits

Acceptance is by agents with controlled public input and Qt events, not human or game testing. Actual Anki core backend import is verified; AQT GUI and sync are not claimed. Earlier calibration's QtProject.conf prior baseline is unknown and was left untouched; only final isolated-run cleanup is fully verified. See verification report for test-log diagnostics and Phase 7/8 boundaries.
