---
phase: 01-core-db-normalize
fixed_at: 2026-10-23T21:28:38Z
review_path: .planning/phases/01-core-db-normalize/01-REVIEW.md
iteration: 1
findings_in_scope: 6
fixed: 6
skipped: 0
status: all_fixed
---

# Phase 1: Code Review Fix Report

**Fixed at:** 2026-10-23T21:28:38Z
**Source review:** .planning/phases/01-core-db-normalize/01-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 6 (Warnings only; the 8 Info items were left alone as instructed)
- Fixed: 6
- Skipped: 0
- Test suite: 47 -> 63 tests, green on Python 3.14.3 (`python -m unittest -v`) and 3.12 (`py -3.12 -m unittest -v`) after every fix; the 10-process concurrency tests passed 10/10 extra runs.

## Fixed Issues

### WR-01: `_ensure_wal` retry loop has no overall deadline

**Files modified:** `lookup/store.py`, `tests/test_migrations.py`
**Commit:** 29da8ac
**Status:** fixed: requires human verification (timing logic)
**Applied fix:** The retry loop is now bounded by wall-clock time, `min(timeout, _WAL_MAX_WAIT)` with `_WAL_MAX_WAIT = 2.0` s, to fit the hotkey latency budget. The bound is no longer 50 x busy_timeout. Each attempt runs with `PRAGMA busy_timeout=50`, so SQLite's busy handler cannot multiply the wait. The caller's busy_timeout is restored in `finally`. The final error now says "database is locked" and chains the last underlying `OperationalError`. The D-20 read-first-then-retry behaviour on a fresh DB is unchanged. Measured: about 2.06 s at `timeout=5` and 0.37 s at `timeout=0.3`, down from 21 s and about 250 s. Tests: lock failure stays within the bound for the default and a short timeout, and busy_timeout is restored after open.

### WR-02: All failures inside `open_store` become `MigrationError`

**Files modified:** `lookup/store.py`, `tests/test_migrations.py`
**Commit:** d24dfdf
**Applied fix:** `open_store` now has two error zones:
- Steps 3-4 (version read, WAL switch, synchronous): `sqlite3.Error`/`OSError` propagate unwrapped after the connection is closed. This matches the errors already escaping from `_connect`. `SchemaTooNewError` is unchanged.
- Steps 6-7 (snapshot, `BEGIN IMMEDIATE`, steps): failures are still wrapped in `MigrationError`. The message is now `"<TypeName>: <msg>"` and the cause is in `__cause__`.

The `open_store` and `MigrationError` docstrings now list the error contract. Tests: a garbage file raises `sqlite3.DatabaseError` (not `MigrationError`) and the file can then be deleted, which shows the connection was closed. A locked DB raises `sqlite3.OperationalError`. A failing step keeps its cause and type name.

### WR-03: The rule that a migration step must not commit is unenforced

**Files modified:** `lookup/store.py`, `tests/test_migrations.py`
**Commit:** 38a8803
**Status:** fixed: requires human verification (transaction-state logic)
**Applied fix:** The reviewer's after-the-fact check alone cannot undo a commit that already happened, so the fix has two parts:
1. **Prevention:** steps now receive a `_StepConnection` guard.
   - `execute`/`executemany` reject statements whose leading keyword (after whitespace and comments) is BEGIN, COMMIT, END or ROLLBACK. `ROLLBACK ... TO savepoint` is still allowed.
   - `commit()`/`rollback()` raise `MigrationError`.
   - `executescript()` splits the script with `sqlite3.complete_statement` and runs each statement through the guarded `execute`, so it stays inside the transaction. This also handles trigger bodies. sqlite3's own `executescript` would COMMIT first.
   - Only `create_function`, `create_aggregate`, `create_collation` and `total_changes` are passed through. Any other attribute, for example `cursor()`, raises.
2. **Detection:** after every step, `open_store` checks `conn.in_transaction` and raises `MigrationError("migration step to vN ended the transaction")`.

Tests:
- The reviewer's repro (`executescript` ALTER, then a failing step) now rolls back completely and the DB reopens normally.
- A multi-statement script with an index and a trigger migrates.
- Eight transaction-control variants are rejected with nothing committed.
- SAVEPOINT / ROLLBACK TO / RELEASE works.
- An out-of-band COMMIT on the raw connection is detected.

**Known limit:** a step could still run COMMIT through a cursor returned by `execute()`. The post-step check catches that, but it cannot undo the commit.

### WR-04: `upsert_word` accepts any `now`; a float stores REAL timestamps (D-13)

**Files modified:** `lookup/store.py`, `tests/test_store.py`
**Commit:** 6ea545b
**Applied fix:** `now` must be an int or a float, and bool is rejected. Other types raise `TypeError` before any write. Floats are truncated with `int(now)`, so `now=time.time()` stores INTEGER seconds. Tests: float input stores `typeof = 'integer'` with truncated values. `True`, `False`, `"100"`, `b"100"` and `[1]` raise `TypeError` and leave no row.

### WR-05: In the race path, the migration runs without any backup (D-14)

**Files modified:** `lookup/store.py`, `tests/test_migrations.py`
**Commit:** 732dc15
**Status:** fixed: requires human verification (concurrency logic)
**Applied fix:** This implements the full fix, not just the minimal raise. Steps 6-7 now run in a bounded loop (`_MIGRATE_ATTEMPTS = 5`). If the version under `BEGIN IMMEDIATE` (`locked_v`) differs from the step-3 read and `0 < locked_v < target`, the fixer:
- rolls back,
- discards the stale snapshot,
- sets `v = locked_v`,
- takes a new snapshot outside the transaction,
- tries again.

This also covers a case the reviewer's snippet missed: `v == 0`, where another process created a populated older-version DB after our read. `locked_v == target` still discards the snapshot and runs no steps, as before. If the attempts run out, the fixer raises `MigrationError` with no temp files left behind. Tests:
- A v1 -> v3 open while another process moves v1 -> v2 produces exactly `t.db.bak-v2` at v2 with the data.
- A fresh DB populated concurrently at v1 gets `t.db.bak-v1`.
- A version that never stops changing gives up cleanly.

All three tests were confirmed to fail on the pre-fix code.

### WR-06: The concurrency test's reader loop has no deadline

**Files modified:** `tests/test_concurrency.py`
**Commit:** 38ec335
**Applied fix:** The reader loop now has a `time.monotonic()` deadline (`_WRITERS_DEADLINE = 90` s) and calls `self.fail(...)` when it passes. The existing `_reap` cleanup terminates the children. A new test patches the deadline to -1 and checks that the loop fails with "did not finish" and does not hang.

---

_Fixed: 2026-10-23T21:28:38Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
