---
phase: 01-core-db-normalize
plan: 02
subsystem: database
tags: [python, sqlite, wal, migrations, upsert, unittest]
requires:
  - phase: 01-core-db-normalize
    provides: "lookup package skeleton and normalize() counting key"
provides:
  - "lookup.store.open_store: WAL connection, versioned schema, safe migrations with pre-migration backup"
  - "lookup.store.upsert_word: atomic counter via INSERT ... ON CONFLICT ... RETURNING count"
  - "lookup.store.default_db_path: LOOKUP_DB / XDG_DATA_HOME / ~/.local/share resolver"
  - "SchemaTooNewError, MigrationError, MIGRATIONS, CURRENT_VERSION, CONTEXT_MAX_CHARS"
  - "tests._support.make_tempdir isolation helper"
affects: [01-03, 02-translation-lemma, 06-word-list]
tech-stack:
  added: []
  patterns:
    - "PRAGMA user_version migrations tuple applied inside one BEGIN IMMEDIATE transaction"
    - "Read-first WAL switch with retry on 'locked'"
    - "Connection.backup snapshot taken before the write lock, published only if version unchanged under the lock"
key-files:
  created:
    - lookup/store.py
    - tests/_support.py
    - tests/test_store.py
    - tests/test_paths.py
    - tests/test_migrations.py
  modified: []
key-decisions:
  - "Snapshot is taken before BEGIN IMMEDIATE (backup inside the write lock hangs on WAL) and published with os.replace only when user_version under the lock still equals the pre-lock value"
  - "Version check precedes the WAL switch so a refused newer database stays byte-identical"
  - "Context truncated to 500 chars and empty/None values never overwrite stored translation or context"
requirements-completed: [DATA-01]
duration: 20min
completed: 2026-10-24
status: complete
---

# Phase 1 Plan 02: SQLite store with versioned schema and atomic counter Summary

Stdlib-only `lookup/store.py` gives an atomic one-statement word counter (`RETURNING count`), a WAL database at `$LOOKUP_DB` / `$XDG_DATA_HOME/lookup/lookup.db`, and `user_version` migrations that keep words and leave a `.bak-vN` copy, proven by 28 new unittest methods.

## Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | constants, schema v1, path resolver, connection setup, WAL helper, upsert | 2c0d668 |
| 2 | snapshot and open_store (version check, WAL, backup, locked migration) | 0f8841d |
| 3 | test support helper, upsert tests, path tests | e417930 |
| 4 | schema lifecycle tests | abe0bdf |

## What was built

- `lookup/store.py`: `_v1` creates the single `words` table (word PK, translation, context, count, first_seen, last_seen, lemma). `upsert_word` runs one parametrised statement; first_seen is never touched on update, empty context or translation keep the old value, context is cut to 500 characters, times are UTC integer seconds. `open_store` follows the locked order: path, connect (SQLite >= 3.35 floor, 0o700 parent dir, autocommit, busy_timeout), version check, WAL plus `synchronous=NORMAL`, early return when current, snapshot, `BEGIN IMMEDIATE`, re-read version, stale-snapshot guard, steps, `user_version`, `COMMIT`. Failures roll back, close the connection and raise `MigrationError` (or `SchemaTooNewError` unwrapped).
- `tests/_support.py`: `make_tempdir` creates a temp dir and points `LOOKUP_DB` at a not-yet-existing nested path.
- `tests/test_store.py` (11 methods), `tests/test_paths.py` (8), `tests/test_migrations.py` (8).

## Verification

- `python -m unittest tests.test_normalize tests.test_store tests.test_paths tests.test_migrations`: 42 tests OK on Python 3.14.3.
- `py -3.12 -m unittest tests.test_store tests.test_paths tests.test_migrations`: OK on 3.12.
- All task acceptance one-liners pass (ordering check on `open_store`, no f-string SQL, no printing or logging, no Qt imports).
- The real `~/.local/share/lookup` was not created by the test run.

## Deviations from Plan

None - plan executed exactly as written. The `_remove_quietly` and `_abort` helpers were added as small private functions to share cleanup code; they do not change the specified behaviour.

## Known Stubs

None.

## Threat Flags

None. T-01-04 (bound parameters, injection test), T-01-05 (newer DB refused byte-identical), T-01-06 (single transaction, backup, stale-snapshot guard), T-01-07 (no printing or logging), T-01-09 (context cap) are mitigated and covered by tests. T-01-08 and T-01-10 are accepted as planned; the README (Phase 7) must state that `.bak-v*` files are full database copies.

## Open items for the Arch VM pass

- Confirm `default_db_path()` resolves under the real home with no overrides (plan human-check, Phase 8).

## Self-Check: PASSED

- Files present: lookup/store.py, tests/_support.py, tests/test_store.py, tests/test_paths.py, tests/test_migrations.py
- Commits present: 2c0d668, 0f8841d, e417930, abe0bdf
