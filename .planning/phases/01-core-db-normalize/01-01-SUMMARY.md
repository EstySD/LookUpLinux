---
phase: 01-core-db-normalize
plan: 01
subsystem: core
tags: [python, unicode, normalization, unittest]
requires: []
provides:
  - "lookup package skeleton (stdlib only)"
  - "lookup.normalize.normalize(text) counting-key function"
  - "lookup.normalize.CONTRACTIONS frozenset (D-16)"
affects: [01-02, 01-03]
tech-stack:
  added: []
  patterns: ["ordered Unicode pipeline with fixed-point possessive strip", "seeded property test for idempotence"]
key-files:
  created:
    - .gitignore
    - lookup/__init__.py
    - lookup/normalize.py
    - tests/__init__.py
    - tests/test_normalize.py
  modified: []
key-decisions:
  - "Digit check (D-17) runs on the raw token before edge trimming, so mp3, 1st, run1 are rejected"
  - "Possessive loop stops as soon as the token is one of the 11 D-16 contractions"
  - "TypeError message names the type only, never the value"
requirements-completed: [DATA-02]
duration: 10min
completed: 2026-10-24
status: complete
---

# Phase 1 Plan 01: Package skeleton and normalize() Summary

Pure stdlib `normalize()` turns any spelling of a word or 1-4 word phrase (`Running`, `"run,"`, `“Book’s”`) into one counting key, or None to reject, pinned by 14 unittest methods including a 20,000-sample seeded idempotence fuzz.

## Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | Package skeleton and normalize() | 2d0fc5d |
| 2 | Unit and property tests for normalize() | 3623c07 |

## What was built

- `lookup/normalize.py`: explicit apostrophe/quote/dash translate tables, NFKC, Cf and Mn removal, casefold, whitespace split, digit rejection, edge trimming, possessive `'s` strip to a fixed point with the D-16 contraction exceptions, Latin-only validation, length rule. Only import is `unicodedata`.
- `tests/test_normalize.py`: `NormalizeTests` with one method per rule (D-01..D-06, D-16..D-18) and the idempotence property.
- `.gitignore`, `lookup/__init__.py` (docstring only), `tests/__init__.py`.

## Verification

- `python -m unittest tests.test_normalize`: 14 tests OK on Python 3.14.3 and 3.12.
- Task 1 acceptance one-liners all pass (contractions count, no Qt imports, TypeError on `normalize(5)`, `__init__.py` has no imports).

## Deviations from Plan

None - plan executed exactly as written. The fuzz found no violations, so no implementation fixes were needed after the tests were written.

## Known Stubs

None.

## Threat Flags

None. T-01-01 is mitigated (output alphabet is Latin letters, `'`, `-`, space; asserted in the fuzz test); T-01-03 is mitigated (no I/O or logging).

## Self-Check: PASSED

- Files present: .gitignore, lookup/__init__.py, lookup/normalize.py, tests/__init__.py, tests/test_normalize.py
- Commits present: 2d0fc5d, 3623c07
