---
phase: 03-ocr
plan: 01
subsystem: ocr
status: complete
completed: 2026-10-25
requirements-completed: [CAPT-03, CAPT-04]
key-files:
  created: [lookup/ocr.py, tests/test_ocr.py]
  modified: [tests/test_core_imports.py]
provides: [strict TSV parser, reversible transforms, bounded word selection, offline compound probes]
affects: [03-02, 03-03, 04]
---

# Phase 3 Plan 1 — Portable OCR core

Implemented Word/Transform/Selection/OcrError, strict bounded UTF-8 TSV parsing,
full line identities, actual-ratio inverse geometry, direct and bounded nearest
selection, rejected-hit barriers, explicit hyphen joins and offline compound
priority. Parsing/selection import no Qt, launch no process and write no files.
choose_query uses only DictSet.find and falls back to the standalone word.

Fresh checks: 13 focused OCR/import tests passed in 0.271s; full Windows
Python 3.14 suite: 493 tests, 20.138s, OK, six skips. Initial test run failed
with missing lookup.ocr before implementation (test-first).

Policy starts at confidence 50, horizontal nearest 0.75 height, vertical 0.25,
hyphen gap 0.5 and pair gap 1.5. These are provisional until Plan 02's real
fixture calibration; this summary does not claim real OCR accuracy.

Threats T-03-01/02/03: finite/shape/byte/row/field validation, positioned rejection
barriers, offline-only candidate tests and quiet python -S import checks pass.
No implementation deviation. Core accepts negative transform origins for later
monitor mapping while parsed prepared-image boxes remain nonnegative.
