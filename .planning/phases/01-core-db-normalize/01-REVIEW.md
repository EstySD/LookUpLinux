---
phase: 01-core-db-normalize
reviewed: 2026-10-23T21:19:54Z
depth: standard
files_reviewed: 13
files_reviewed_list:
  - lookup/__init__.py
  - lookup/normalize.py
  - lookup/store.py
  - tests/__init__.py
  - tests/_support.py
  - tests/_workers.py
  - tests/test_concurrency.py
  - tests/test_core_imports.py
  - tests/test_migrations.py
  - tests/test_normalize.py
  - tests/test_paths.py
  - tests/test_store.py
  - .gitignore
findings:
  critical: 0
  warning: 6
  info: 8
  total: 14
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-10-23T21:19:54Z
**Depth:** standard
**Files Reviewed:** 13
**Status:** issues_found

## Narrative Findings (AI reviewer)

## Summary

I reviewed the stdlib-only core (`lookup/normalize.py`, `lookup/store.py`) and the unittest suite against locked decisions D-01..D-20. The suite passes (47 tests, Python 3.14.3 on Windows). I also ran probe scripts against edge cases.

The happy paths hold up. The upsert is a single atomic `INSERT ... ON CONFLICT ... RETURNING`, all SQL is parameterised (the only `%d` interpolation is an int), the order D-14 requires (version check, then WAL, then snapshot, then `BEGIN IMMEDIATE`, then steps plus version bump in one transaction) is in place, and `normalize()` is idempotent on 20k random inputs.

The defects are in error handling and robustness:
- The WAL retry loop can block for minutes. I measured about 21 s with `timeout=0.3`; with the default `timeout=5` the worst case is about 250 s.
- Every failure inside `open_store`, including a locked DB or a corrupt file, is reported as `MigrationError`.
- The "a step never commits" rule for migrations is not enforced, and I showed that breaking it leaves a half-migrated DB.
- `upsert_word` accepts a float `now`, which stores REAL timestamps and breaks D-13.
- In one race, a migration runs with no backup, which D-14 forbids.
- One test loop has no deadline.

I found no blockers: none of these break behaviour on the paths Phase 1 actually exercises.

## Warnings

### WR-01: `_ensure_wal` retry loop has no overall deadline; worst case is minutes, not milliseconds

**File:** `lookup/store.py:77-89` (with `_WAL_RETRIES = 50` at line 15)
**Issue:** `PRAGMA journal_mode=WAL` needs an exclusive lock, and SQLite runs the busy handler (`busy_timeout`, 5 s by default) before it returns "database is locked". The loop retries this 50 times and sleeps 5-50 ms between tries, so the worst case is about 50 × (5 s + 0.05 s) ≈ 250 s. I reproduced it: with a rollback-mode reader holding a SHARED lock, `open_store(p, timeout=0.3)` took **21.3 s** before it failed. A process launched by the hotkey would hang for minutes, against a 1.5 s latency budget. The final error ("could not switch database to WAL") also drops the last underlying exception.
**Fix:** Bound the loop by wall-clock time based on `timeout`, and run the WAL switch with a short busy timeout so the backoff loop owns the waiting:
```python
def _ensure_wal(conn, timeout):
    deadline = time.monotonic() + timeout
    conn.execute("PRAGMA busy_timeout=50")
    try:
        last = None
        while True:
            try:
                if conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal":
                    return
                row = conn.execute("PRAGMA journal_mode=WAL").fetchone()
                if row is not None and str(row[0]).lower() == "wal":
                    return
                raise sqlite3.OperationalError("could not switch database to WAL")
            except sqlite3.OperationalError as exc:
                if "locked" not in str(exc).lower():
                    raise
                last = exc
            if time.monotonic() >= deadline:
                raise sqlite3.OperationalError("could not switch database to WAL") from last
            time.sleep(random.uniform(0.005, 0.05))
    finally:
        conn.execute("PRAGMA busy_timeout=%d" % int(timeout * 1000))
```

### WR-02: All failures inside `open_store` become `MigrationError`, including a locked DB, a corrupt file and a failed WAL switch

**File:** `lookup/store.py:218-221`
**Issue:** `except Exception as exc: raise MigrationError(str(exc))` wraps everything after `_connect`: the `PRAGMA user_version` read, `_ensure_wal`, `PRAGMA synchronous`, `_snapshot` and `os.replace`. My probes showed:
- garbage file → `MigrationError: file is not a database`
- up-to-date DB under an exclusive lock → `MigrationError: database is locked`
- `":memory:"` → `MigrationError: could not switch database to WAL`

The class docstring says "A migration step failed; the database was rolled back", but none of these involved a migration step. Meanwhile, failures in `_connect` (mkdir `PermissionError`, `sqlite3.OperationalError: unable to open database file`) escape unwrapped. Callers in Phase 2/5 cannot tell "retry, DB busy" from "corrupt DB" from "migration bug", and need two different `except` clauses for the same problem class.
**Fix:** Wrap only steps 6-7 (snapshot, transaction, steps) in `MigrationError`. Let `sqlite3.Error`/`OSError` from steps 2-4 propagate unchanged, or wrap them in a separate `StoreOpenError`:
```python
    conn = _connect(path, timeout)
    try:
        v = ...; _ensure_wal(conn); ...
        if v == target:
            return conn
    except BaseException:
        conn.close()
        raise
    try:
        # steps 6-7
    except SchemaTooNewError: ...
    except Exception as exc:
        _abort(conn, tmp)
        raise MigrationError(type(exc).__name__ + ": " + str(exc)) from exc
```

### WR-03: The rule that a migration step must not commit is unenforced; a step that commits leaves a half-migrated DB that can never be migrated again

**File:** `lookup/store.py:39, 209-212`
**Issue:** The "one transaction" guarantee exists only as a comment ("never commits"). In legacy transaction-control mode, `conn.executescript(...)` issues a `COMMIT` before it runs, and a step can also call `conn.commit()` or run `COMMIT` itself. I reproduced it: `MIGRATIONS + (lambda c: c.executescript("ALTER TABLE words ADD COLUMN z TEXT;"), failing_step)` raised `MigrationError`, but column `z` stayed committed while `user_version` stayed 1. Every later open re-runs the step and fails with "duplicate column name", so the user is locked out. Phase 2 will add real migrations, and `executescript` is the natural way to write multi-statement DDL.
**Fix:** Check after every step that the transaction is still open:
```python
        for step in migrations[locked_v:]:
            step(conn)
            if not conn.in_transaction:
                raise MigrationError(
                    "migration step %s ended the transaction" % step.__name__
                )
```
Also add a test that uses a committing step.

### WR-04: `upsert_word` accepts any `now`; a float stores REAL timestamps and breaks D-13

**File:** `lookup/store.py:118-119`
**Issue:** D-13 requires INTEGER Unix seconds. A caller that passes `now=time.time()`, the obvious mistake, stores `typeof(first_seen) = 'real'` (verified: `('real', 1729771234.7)`). The column's INTEGER affinity only converts lossless values. `now=True` stores `1`. A future UI that does `datetime.fromtimestamp(int(...))` or sorts by integer would then see mixed types.
**Fix:**
```python
    if now is None:
        now = int(time.time())
    elif isinstance(now, bool) or not isinstance(now, (int, float)):
        raise TypeError("now must be int, got " + type(now).__name__)
    else:
        now = int(now)
```

### WR-05: In the race path, the migration runs without any backup (D-14)

**File:** `lookup/store.py:203-210`
**Issue:** If `locked_v != v` (another process changed the version between the step-3 read and `BEGIN IMMEDIATE`), the snapshot is thrown away. Migration then continues from `locked_v` up to `target` with no `.bak-v{locked_v}`. That is correct only when `locked_v == target`, the case the test covers. When `0 < locked_v < target`, for example an older and a newer build running side by side during a package upgrade, existing data is migrated with no backup. D-14 says every migration of an existing database is preceded by a copy.
**Fix:** If `0 < locked_v < target` and no matching backup exists, roll back, take a new snapshot at `locked_v` outside the transaction, and retry (loop steps 6-7 a bounded number of times). The minimum fix is to raise `MigrationError` in that case, so the next open migrates with a proper snapshot:
```python
        if tmp is not None and locked_v != v:
            _remove_quietly(tmp); tmp = None
            if 0 < locked_v < target:
                raise MigrationError("schema changed concurrently; reopen to migrate with backup")
```

### WR-06: The concurrency test's reader loop has no deadline and can hang the suite forever

**File:** `tests/test_concurrency.py:37-43`
**Issue:** `while any(p.is_alive() for p in procs)` polls with no time limit. If a child blocks (the snapshot-in-transaction hang described in `store._snapshot`'s docstring, a stuck barrier, or the WR-01 loop), the test never reaches `queue.get(timeout=60)` and never fails. Unlike `test_migrations.py`, this module has no faulthandler watchdog. On CI or in the VM this shows up as a hung run, not a red test.
**Fix:**
```python
            deadline = time.monotonic() + 90
            while any(p.is_alive() for p in procs):
                if time.monotonic() > deadline:
                    self.fail("writer processes did not finish in 90 s")
                ...
```

## Info

### IN-01: The apostrophe/dash table runs only before NFKC, so NFKC can produce characters the table never maps

**File:** `lookup/normalize.py:6-8, 36-37`
**Issue:** NFKC turns U+0149 `ŉ` into U+02BC + `n`, U+FE58/U+FE31 into U+2014, U+FE32 into U+2013, and U+2034 into U+2032×3. These outputs appear after the `translate()` calls, so they are never mapped (`"ŉ"` → None; `"well﹘known"` → None). U+02BB (ʻ) and U+02B9 (ʹ) are also missing from `_APOS`. Because they are `isalpha()` (category Lm) but not LATIN, they reject the whole token.
**Fix:** Run the three `translate()` calls again after NFKC (keep the pre-NFKC pass for U+00B4), and add U+02BB/U+02B9 to `_APOS`.

### IN-02: Phrase rules: one punctuation-only token rejects the whole phrase, and single-letter tokens pass

**File:** `lookup/normalize.py:56-57, 67-68`
**Issue:** `"rock & roll"` and `"hello — world"` return None because one token strips to empty. Meanwhile `"x y"` and `"l i"` (typical OCR noise) are accepted, because the D-04 length check applies to the joined key, not to each token. Tests pin the first behaviour, so it is intentional, but Phase 2 (DATA-03, selected phrases) will feed real typography into this.
**Fix:** Before Phase 2, decide whether empty-after-strip tokens should be dropped rather than rejecting the phrase. Consider applying the `< 2 except a/i` rule per token.

### IN-03: Runs of inner apostrophes and hyphens are accepted

**File:** `lookup/normalize.py:58-60`
**Issue:** `"well--known"` → `"well--known"` and `"a'-'b"` → `"a'-'b"`. OCR noise therefore creates keys separate from `well-known`.
**Fix:** Collapse runs (`re.sub(r"([-'])[-']+", r"\1", w)`), or reject tokens that contain consecutive `'`/`-`.

### IN-04: `MigrationError(str(exc))` cannot guarantee the module's V7 privacy rule

**File:** `lookup/store.py:3-4, 221`
**Issue:** The module docstring promises that exception messages never contain word, context or translation text. However, `str(exc)` passes through whatever a migration step raises, and a future data-migrating step could raise with row values.
**Fix:** Use `type(exc).__name__` plus, for `sqlite3.Error` only, `str(exc)`. Keep the cause in `__cause__` for debugging.

### IN-05: DB and backup file permissions depend on umask

**File:** `lookup/store.py:62-63, 144`
**Issue:** `mode=0o700` applies only if the leaf directory is created here. If `~/.local/share/lookup` already exists (for example, created by an installer with 0755), `lookup.db` and `lookup.db.bak-vN` are created 0644. They hold the user's lookup history. Arch homes are 0700 by default, so exposure is limited.
**Fix:** Call `os.chmod(path.parent, 0o700)` if the directory is owned by the user, or create files under `os.umask(0o077)`.

### IN-06: A stale snapshot temp file is never cleaned up, and the backup can miss late rows

**File:** `lookup/store.py:143, 194-205`
**Issue:** A crash or kill between `_snapshot` and `os.replace` leaves `lookup.db.bak-vN.<pid>.tmp` forever. Also, the snapshot is taken before `BEGIN IMMEDIATE`, so rows that an old-version process (for example, a running tray daemon) upserts in that window are missing from `.bak-vN`. Long-lived connections never re-check `user_version`, so an old daemon keeps writing to a DB that a newer build has migrated.
**Fix:** On successful open, glob and delete `*.bak-v*.tmp` files whose PID is not alive. Document that Phase 4's daemon must reopen, or check `user_version`, after an upgrade.

### IN-07: Duplicated error construction and redundant SQL/PRAGMA

**File:** `lookup/store.py:182-185, 199-202, 65, 122`
**Issue:** The `SchemaTooNewError` message is built twice. `NULLIF(?, '')` in the INSERT is dead logic, because `_clean_text` already maps empty strings to `None`. `PRAGMA busy_timeout` repeats what `sqlite3.connect(timeout=...)` already sets.
**Fix:** Add a `_too_new(v, target)` helper and drop the redundant `NULLIF` and PRAGMA, or comment why they are kept as defence in depth.

### IN-08: Test gaps and the scope of the test watchdog

**File:** `tests/test_migrations.py:21-27`; `tests/test_migrations.py` (missing cases)
**Issue:**
- The watchdog `faulthandler.dump_traceback_later(120, exit=True)` covers the whole module and calls `exit`, so a slow VM run kills the entire unittest process and hides every other result.
- No test covers the step-7 `SchemaTooNewError` branch (`locked_v > target`).
- No test covers multi-process migration from v1 to v2 (only a simulated race).
- No test checks which exception type a locked or corrupt DB raises.

**Fix:** Re-arm the timer per test in `setUp`/`tearDown`, and add the three missing cases.

---

_Reviewed: 2026-10-23T21:19:54Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
