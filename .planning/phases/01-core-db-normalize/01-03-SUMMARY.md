---
phase: 01-core-db-normalize
plan: 03
subsystem: testing
tags: [python, sqlite, wal, multiprocessing, spawn, unittest]
requires:
  - phase: 01-core-db-normalize
    provides: "lookup.store open_store/upsert_word and tests._support.make_tempdir"
provides:
  - "tests._workers.child: importable spawn worker"
  - "10-process concurrency proof on pre-created and fresh databases (SC3)"
  - "Stdlib-only, side-effect-free import proof for the lookup core (D-15)"
affects: [verify-work, 02-translation-lemma]
tech-stack:
  added: []
  patterns:
    - "multiprocessing.get_context('spawn') with Barrier so all workers hit open_store simultaneously"
    - "child interpreter under -S compared with sys.stdlib_module_names"
key-files:
  created:
    - tests/_workers.py
    - tests/test_concurrency.py
    - tests/test_core_imports.py
  modified: []
key-decisions:
  - "lookup/store.py left untouched: both concurrency tests passed as written, so the conditional edit was not needed"
requirements-completed: [DATA-01]
duration: 8min
completed: 2026-10-24
status: complete
---

# Phase 1 Plan 03: Concurrency and import-purity proof Summary

Ten spawn-started processes upserting the same word return counts exactly 1..10 and leave one row with count 10 on both a pre-created and a non-existent database (3 fresh rounds), with a concurrent reader never blocked; the `lookup` core is proven stdlib-only and creates nothing on import.

## Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | Spawn worker and 10-process concurrency tests | 7057337 |
| 2 | Core import purity test and phase gate | 9ccbd6f |

## What was built

- `tests/_workers.py`: top-level `child(path, barrier, queue, index)`; waits on the barrier, calls `open_store` and `upsert_word`, closes the connection, reports `("ok", count)` or `("err", ...)` and never re-raises.
- `tests/test_concurrency.py`: `ConcurrentWriterTests` with `_run_writers`, `test_ten_writers_on_precreated_db` (with a polling reader whose values must be None or 1..10 and non-decreasing) and `test_ten_writers_on_fresh_db` (3 subTest rounds, asserts the file does not exist first).
- `tests/test_core_imports.py`: `CoreImportTests` with the `-S` stdlib check (names GUI toolkits explicitly on failure), the no-side-effects check (neither the db file nor its parent directory appears) and the public-names check.

## Verification

- `python -m unittest tests.test_concurrency`: green 3 times in a row on 3.14.3 (about 1.1-1.6 s each); green on 3.12.
- Phase gate, full suite `python -m unittest -v`: 47 tests OK in 2.3 s on Python 3.14.3; all six test modules discovered.
- Phase gate, `py -3.12 -m unittest -v`: 47 tests OK in 2.2 s.

## Deviations from Plan

None - plan executed exactly as written. `lookup/store.py` was not modified.

## Known Stubs

None.

## Threat Flags

None. T-01-11, T-01-12 and T-01-13 are mitigated and now covered by tests; T-01-14 accepted as planned.

## Self-Check: PASSED

- Files present: tests/_workers.py, tests/test_concurrency.py, tests/test_core_imports.py
- Commits present: 7057337, 9ccbd6f
