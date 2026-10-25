---
phase: 02-offline-dicts-translate
plan: 09
subsystem: translation
tags: [orchestrator, cache, sqlite, threads, stdlib]
requires:
  - phase: 02-offline-dicts-translate
    provides: normalize, store schema v2, OnlineResult, SearchResult
provides:
  - lookup.translate lookup, classification, cache and meta helpers
  - Dictionary-first lookup and bounded parallel context translation
affects: [02-08, 02-10, 02-11]
key-files:
  created: [lookup/translate.py, tests/test_translate.py]
  modified: []
requirements-completed: [TRAN-02, TRAN-03, TRAN-05, DATA-03]
completed: 2026-10-25
status: complete
---

# Phase 2 Plan 09: Translation Orchestrator

Implemented all three tasks in `lookup/translate.py`, with 25 tests in
`tests/test_translate.py`. The previous session had left no implementation.

- Classification preserves sentence case and normalizes word/phrase keys.
  Invalid input bypasses dictionaries, network and database access.
- Words and headword phrases search dictionaries before validated cache and
  online fallback. Dictionary failures permit online fallback. Optional
  dictionaries and connections support degraded operation.
- Cache entries use bound parameters and validated OnlineResult payloads;
  sentence insertion retains the newest 1000 entries with deterministic ties.
  Successful Google clients are persisted for subsequent requests.
- Word/phrase saves preserve dictionary lemmas, use online word lemmas only
  when appropriate, store short translations and apply the not_found/offline
  counting rules. Sentences are never counted in words.
- Context translation starts before dictionary search in a daemon thread,
  uses a bounded remaining join budget, and reports reason codes on failures.
  Cache access and writes remain exclusively on the calling thread; late
  results after timeout cannot write to the database.
- Library calls produce no output and return stage timings as data.

## Contract Clarification

The plan's top-level truth says `save=False` writes nothing, whereas Task 2's
explicit behavior says it writes nothing to `words` but still caches successful
online answers. Implemented the detailed Task 2 contract: save controls word
counting, while successful answers and client preference remain cached.

## Verification

Tests were added first and failed with ImportError for the missing module.
After implementation and final changes:

- Python 3.14: `python -m unittest discover -s tests -t .` — 456 tests, OK,
  3 skipped.
- Python 3.12: `py -3.12 -m unittest discover -s tests -t .` — 456 tests, OK,
  3 skipped.
- `py -3.12 -m unittest tests.test_translate tests.test_online tests.test_store`
  — 99 tests, OK.
- `tests.test_translate.SentenceTests` — 9 tests, OK on three consecutive runs.
- `python -S` import, classification and keyword-only signature assertions pass.

## Limits

Network responses and dictionary search are mocked here. Real dictionary-set
integration is pending plan 08; live provider and VM checks belong to plan 11.
No new dependencies or known stubs.
