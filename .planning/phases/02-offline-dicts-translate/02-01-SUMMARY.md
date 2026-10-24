---
phase: 02-offline-dicts-translate
plan: 01
subsystem: database
tags: [sqlite, migration, schema-v2, lemma, unittest]

requires:
  - phase: 01-core-store
    provides: versioned SQLite store with snapshot and guarded migration steps
provides:
  - "Schema version 2: translations cache table and meta key/value table"
  - "upsert_word(..., lemma=None) with COALESCE semantics"
  - "tests/_support.py: V1, extended make_tempdir sandbox (LOOKUP_DICTS/CONFIG/CACHE), forbid_network"
affects: [02-03, 02-08, 02-09, 02-10, translate, dictionaries]

tech-stack:
  added: []
  patterns:
    - "Tests that mean 'a version-1 database' open with migrations=V1 (V1 = MIGRATIONS[:1])"
    - "New nullable text columns are written with COALESCE(excluded.x, words.x) so None never erases data"

key-files:
  created: []
  modified:
    - lookup/store.py
    - tests/_support.py
    - tests/_workers.py
    - tests/test_store.py
    - tests/test_migrations.py
    - tests/test_concurrency.py

key-decisions:
  - "assert_untouched in StepTransactionGuardTests reopens a copy of the V1 file with the real tuple, because the real tuple now upgrades V1 to v2 and would break later subtests"

patterns-established:
  - "forbid_network(testcase) patches urllib.request.urlopen to raise AssertionError; tests assert call_count == 0 for cache hits"

requirements-completed: [TRAN-03, TRAN-04]

coverage:
  - id: D1
    description: "Fresh database is created at version 2 with tables meta, translations, words; kind is CHECK-constrained; PK is (text, kind)"
    requirement: TRAN-03
    verification:
      - kind: unit
        ref: "tests/test_store.py#test_schema_v2_tables_and_columns, test_translations_kind_check"
        status: pass
    human_judgment: false
  - id: D2
    description: "A Phase 1 database (user_version 1) migrates to 2, keeps its rows, and gets a .bak-v1 backup"
    requirement: TRAN-03
    verification:
      - kind: unit
        ref: "tests/test_store.py#SchemaV2Tests.test_phase1_database_migrates_to_v2_keeping_words"
        status: pass
    human_judgment: false
  - id: D3
    description: "upsert_word accepts lemma; a stored lemma is never overwritten by None or blank text; type-checked; bound parameter"
    requirement: TRAN-04
    verification:
      - kind: unit
        ref: "tests/test_store.py#test_lemma_stored_and_coalesced, test_lemma_type_checked, test_lemma_bound_not_interpolated, test_positional_callers_unchanged"
        status: pass
    human_judgment: false
  - id: D4
    description: "Phase 1 migration, concurrency and store tests pinned to explicit V1; suite green on Python 3.14 and 3.12"
    verification:
      - kind: unit
        ref: "python -m unittest; py -3.12 -m unittest (84 tests, 2 POSIX-only skipped)"
        status: pass
    human_judgment: false

duration: 25min
completed: 2026-10-24
status: complete
---

# Phase 2 Plan 01: Schema v2 and lemma Summary

**SQLite schema v2 (translations cache + meta tables) with a lemma keyword on upsert_word, and the Phase 1 safety-net tests re-pinned to an explicit V1 tuple.**

## Performance

- **Duration:** ~25 min
- **Completed:** 2026-10-24
- **Tasks:** 2 (Task 2 as TDD: RED then GREEN)
- **Files modified:** 6

## Accomplishments

- `_v2` creates `translations(text, kind, provider, payload, fetched_at)` with `PRIMARY KEY(text, kind)` and `CHECK(kind IN ('word','phrase','sentence'))`, plus `meta(key PRIMARY KEY, value)`. `MIGRATIONS = (_v1, _v2)`, `CURRENT_VERSION == 2`.
- `upsert_word(conn, word, translation=None, context=None, now=None, lemma=None)`: lemma goes through `_clean_text` (TypeError for non-str, blank becomes NULL) and is written with `COALESCE(excluded.lemma, words.lemma)`. All SQL stays parameterised.
- `tests/_support.py` gained `V1 = MIGRATIONS[:1]`, a `make_tempdir` that also sandboxes `LOOKUP_DICTS`, `LOOKUP_CONFIG`, `LOOKUP_CACHE` (none created), and `forbid_network`.
- Migration, worker and concurrency tests now start from `V1`; a real Phase 1 to v2 upgrade test checks rows, tables and the `.bak-v1` backup (its `user_version` is 1).

## Task Commits

1. **Task 1: Pin Phase 1 tests to V1, extend sandbox** - `0e5aff2` (test)
2. **Task 2 RED: failing tests for schema v2 and lemma** - `a24a126` (test)
3. **Task 2 GREEN: `_v2` migration and lemma keyword** - `a727e35` (feat)

No refactor commit was needed.

## Files Created/Modified

- `lookup/store.py` - `_v2` step, `MIGRATIONS`, `lemma` keyword and docstring
- `tests/_support.py` - `V1`, env sandbox, `forbid_network`
- `tests/_workers.py` - `migrate_child` opens with `V1 + (add_probe,)`
- `tests/test_migrations.py` - re-pinned to `V1`; `test_up_to_date_open_makes_no_backup` builds a current-version file
- `tests/test_concurrency.py` - first open uses `migrations=V1`
- `tests/test_store.py` - schema v2, kind CHECK, lemma tests, `SchemaV2Tests`

## Decisions Made

- `assert_untouched` (StepTransactionGuardTests) now runs its "still opens with the real migrations" check on a backup copy of the file instead of the file itself.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] assert_untouched reopened the V1 fixture with the real tuple**
- **Found during:** Task 2 (GREEN run)
- **Issue:** The plan says to keep the real tuple there. Once `_v2` exists, that reopen upgrades the V1 file to version 2, so every later subtest of `test_transaction_control_rejected` (i=1..7) saw version 2 and failed its `== 1` assertion.
- **Fix:** Copy the file with `Connection.backup` and open the copy with the real tuple. The check is unchanged; no assertion was loosened.
- **Files modified:** `tests/test_migrations.py`
- **Commit:** `a727e35`

Otherwise the plan was executed as written.

## Issues Encountered

None beyond the deviation above. Two tests are skipped on this Windows host (POSIX file-mode tests); they are skipped by their own `skipUnless`, and the V1 change to `test_new_files_private_in_existing_0755_dir` is therefore not exercised here.

## Known Stubs

None.

## Threat Flags

None. T-02-01 (bound parameters) is covered by `test_lemma_bound_not_interpolated` and the existing injection test. T-02-02 (v1 to v2 migration) is covered by `test_phase1_database_migrates_to_v2_keeping_words`.

## Next Phase Readiness

Later plans can import `V1`, `make_tempdir` (with `LOOKUP_DICTS`, `LOOKUP_CONFIG`, `LOOKUP_CACHE`) and `forbid_network`, and write the cache into `translations` and `meta`.

## Self-Check: PASSED

- `lookup/store.py` contains `def _v2`, the lemma COALESCE and the CHECK/PK clauses
- Commits `0e5aff2`, `a24a126`, `a727e35` exist
- Full suite: 84 tests OK on Python 3.14.3 and 3.12.0
