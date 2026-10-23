---
phase: 01-core-db-normalize
verified: 2026-10-23T21:32:57Z
status: human_needed
score: 16/16 truths verified
behavior_unverified: 0
overrides_applied: 0
human_verification:
  - test: "On the Arch VM (no LOOKUP_DB, no XDG_DATA_HOME override) run: python -c \"import lookup.store as s; print(s.default_db_path())\" from the repo root"
    expected: "Prints a path ending in .local/share/lookup/lookup.db under the real home directory; nothing is created on disk"
    why_human: "Windows dev machine cannot exercise POSIX home and XDG resolution for real. Deferred item from plan 01-02 Task 1 human-check; the plan marks it non-blocking and it is scheduled for the Phase 8 VM pass."
  - test: "On the Arch VM, hold an exclusive lock on a lookup.db from another process and call open_store() on a file that is not yet in WAL mode"
    expected: "Fails with sqlite3.OperationalError 'could not switch database to WAL: database is locked' within about 2 s (default timeout 5 s), not minutes"
    why_human: "The 2 s bound (_WAL_MAX_WAIT) was measured by the review-fix pass on Windows only. The hotkey latency budget (PERF-01) is measured in the VM in Phase 8."
---

# Phase 1: Ядро: база и нормализация — Verification Report

**Phase Goal:** Слово нормализуется и записывается в SQLite со счётчиком поисков, контекстом, переводом и временами первого и последнего поиска. Схема версионируется, чтобы дальше добавлять кэш, карточки и настройки без потери данных. Всё проверяется набором unittest без Qt и без рабочего стола.
**Verified:** 2026-10-23T21:32:57Z (UTC)
**Status:** human_needed
**Re-verification:** No — initial verification (no prior VERIFICATION.md in the phase directory)

**Verified at commit:** ef5b5d6 (includes the six review-fix commits 29da8ac..38ec335)

## Goal Achievement

The phase goal is achieved in the code. No must-have is FAILED. The status is `human_needed` only because the Arch VM check that plan 01-02 deferred (harvested as a human-verification item under Step 8) is still open. The plan marks it non-blocking, and the user confirmed it is deferred to Phase 8.

### Observable Truths

| #  | Truth | Status | Evidence |
| -- | ----- | ------ | -------- |
| 1  | SC1: `Running`, `"run,"`, `“Book’s”` normalise to `running`, `run`, `book`; all spellings of one word give one key (DATA-02) | VERIFIED | Ran `normalize()` directly: `'Running'->'running'`, `'"run,"'->'run'`, `'“Book’s”'->'book'`, `'Book’s'->'book'`, `"book's's"->'book'`, `'Apple'->'apple'`. Tests `test_success_criterion_examples`, `test_variants_share_one_key` pass (63/63). |
| 2  | Case folded, edge punctuation/quotes/brackets trimmed, possessive `'s` stripped to a fixed point, inner `'` and `-` kept (D-01..D-03) | VERIFIED | `lookup/normalize.py` lines 46-57 (edge trim plus `'s` loop until no change); `test_possessive_fixed_point`, `test_inner_apostrophe_and_hyphen_kept`, `test_apostrophe_and_quote_table` pass. |
| 3  | 11 contractions keep `'s`; any digit in a raw token rejects it before edge trimming (D-16, D-17) | VERIFIED | `CONTRACTIONS` frozenset has the 11 members (`lookup/normalize.py` 12-17); `c.isnumeric()` check runs on the raw token (line 46). `test_contraction_exceptions`, `test_digit_tokens_rejected` pass. |
| 4  | No Latin letters, mixed script, key < 2 chars (except `a`/`i`), empty input give None; non-str raises TypeError; phrases collapse whitespace; diacritics kept; no lemmatisation (D-04..D-06, D-18) | VERIFIED | Ran: `'мир'`-type inputs and `'mp3'`, `'x'` give None; `'a'->'a'`, `'I'->'i'`; `'  Break   OUT, '->'break out'`; `'café'`, `'café'` -> `'café'`; `'Straße'->'strasse'`; `'Ｒｕｎ'->'run'`; `'ﬁnd'->'find'`. Tests `test_rejects`, `test_phrases`, `test_unicode_folding`, `test_diacritics_kept`, `test_no_lemmatisation`, `test_non_str_raises_type_error` pass. |
| 5  | `normalize(normalize(x)) == normalize(x)` over 20,000 seeded random strings | VERIFIED | `tests/test_normalize.py` line 121 `random.Random(20261024)`, line 130 `for _ in range(20000)`, asserts idempotence and output alphabet. Test passes. |
| 6  | `lookup/` imports only the stdlib and has no import-time side effects (D-15) | VERIFIED | `test_core_imports_only_stdlib` runs a child under `-S` and compares loaded modules with `sys.stdlib_module_names`; ran the same check in-process: result `[]`. `test_import_has_no_side_effects` passes. `lookup/__init__.py` is a docstring only. |
| 7  | SC2: two saves of one word leave one row: count 2, translation, last non-empty context, first_seen from the first save, last_seen from the second (DATA-01) | VERIFIED | `lookup/store.py` lines 154-166: one `INSERT ... ON CONFLICT(word) DO UPDATE ... RETURNING count`; `first_seen` not in the UPDATE SET. `test_two_saves_one_row` (now=100, now=200 asserts first 100, last 200) passes. |
| 8  | upsert returns the post-update count from one statement, no SELECT-then-UPDATE (D-12) | VERIFIED | Code: single `conn.execute` with `RETURNING count` and `fetchall()` (lines 154-166). `test_returning_count_sequence` (1, 2, 3) passes. |
| 9  | Empty/whitespace context and None/empty translation never overwrite stored values; context cut to 500 on write; times are UTC integer seconds (D-07, D-10, D-13, D-19) | VERIFIED | `_clean_text` (122-132), `COALESCE(NULLIF(excluded.x,''), words.x)` in the SQL; float `now` truncated to int (lines 148-153, fix for WR-04). `test_empty_context_and_none_translation_keep_old`, `test_context_truncated_to_500`, `test_times_are_integer_utc_seconds`, `test_float_now_stored_as_integer_seconds`, `test_invalid_now_rejected` pass. |
| 10 | SC4: DB file created with missing parent dirs at `$LOOKUP_DB`, else `$XDG_DATA_HOME/lookup/lookup.db`, else `~/.local/share/lookup/lookup.db`; reopening keeps rows; journal mode WAL (D-11) | VERIFIED | `default_db_path` (61-69) and `_connect` creating parents with `mkdir(parents=True)` (79). Tests `test_lookup_db_wins`, `test_xdg_data_home_used`, `test_relative_xdg_ignored`, `test_home_fallback`, `test_creates_file_under_missing_data_dir`, `test_reopen_keeps_rows_and_wal` pass. Real-home resolution on Linux is the deferred VM item (see Human Verification). |
| 11 | SC4: an old-schema DB opens under the new version without losing words; a pre-migration copy `lookup.db.bak-v{N}` is left beside it (D-14, D-19) | VERIFIED (mechanism) | `test_old_version_db_migrated_without_losing_words` builds a v1 DB with two words, opens it with synthetic `M2 = MIGRATIONS + (_add_probe,)`, checks both rows and counts survive, `user_version` 2, and `t.db.bak-v1` opens as v1 with no `probe` column. Caveat: production `CURRENT_VERSION` is 1, so the real v1 to v2 path does not exist yet. D-19 locked the synthetic-step proof, so this is accepted for Phase 1. |
| 12 | Newer-version DB refused with `SchemaTooNewError`, file byte-identical afterwards (D-14) | VERIFIED | Version check at `open_store` step 3, before `_ensure_wal`. `test_newer_db_refused_untouched` compares SHA-256 before and after and checks no `-wal` file. Passes. |
| 13 | A failing migration step rolls back all steps and raises `MigrationError`; the DB keeps its old version and rows (D-14) | VERIFIED (see WARNING W1) | `test_failing_step_rolls_back_all_steps` passes (version 1, no `probe` column, rows intact, reopen works). Caveat W1: a step can still commit through `cursor.connection` (verified by running it). This does not affect the tested must-have, but it weakens the guarantee. |
| 14 | SQL-looking text in word, context, translation is stored literally and the table stays intact (V5) | VERIFIED | All values bound with `?`; the only formatted SQL is `PRAGMA user_version = %d` with an int and `busy_timeout` with an int. `test_sql_text_is_bound_not_interpolated` passes. Grep: no `execute(f` in `lookup/`. |
| 15 | SC3: ten spawn processes upserting one word into a pre-created DB return counts exactly 1..10, leave one row with count 10, raise no error, and a concurrent reader is never blocked (DATA-01) | VERIFIED | `test_ten_writers_on_precreated_db` passes. Ran the suite three times in a row for the concurrency module: OK each time. In my own run the reader collected 29 samples while writers ran (values None, 2, 2, 3 ... 7), so the reader overlapped the writers. See INFO I1. |
| 16 | SC3 / D-20: ten writers on a file that does not exist yet produce counts 1..10 with no `database is locked` (3 rounds) | VERIFIED | `test_ten_writers_on_fresh_db` (subTest x3, asserts `path.exists()` is False first) passes; `_ensure_wal` read-first plus bounded retry in `lookup/store.py` 89-119. |

**Score:** 16/16 truths verified (0 present-behavior-unverified, 0 overrides)

### Deferred Items

None. No gap is addressed by a later phase, because there are no gaps. The Arch VM check is a human item, not a deferred gap. It is addressed by the Phase 8 VM pass (Roadmap Phase 8 "проверка в VM").

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `lookup/normalize.py` | `normalize()`, `CONTRACTIONS` | VERIFIED | 69 lines, substantive pipeline (D-01..D-06, D-16..D-18), stdlib only (`unicodedata`). Exercised by 9 normalization test methods. |
| `lookup/store.py` | `default_db_path`, `open_store`, `upsert_word`, `MIGRATIONS`, `CURRENT_VERSION`, `SchemaTooNewError`, `MigrationError`, `CONTEXT_MAX_CHARS` | VERIFIED | 377 lines. All names present (checked by `test_public_names_present`). Locked order of `open_store` steps 1-9 confirmed in code. |
| `lookup/__init__.py` | Docstring only | VERIFIED | One docstring line, no imports. |
| `tests/_support.py` | `make_tempdir` isolation helper | VERIFIED | Used by every test class (grep). |
| `tests/_workers.py` | Importable spawn worker `child` | VERIFIED | Calls `open_store` and `upsert_word`; reports `("ok", count)`. Its output is what the concurrency tests assert on. |
| `tests/test_normalize.py` | Unit and property tests | VERIFIED | 14 test methods; 20,000-iteration fuzz with `Random(20261024)`. |
| `tests/test_store.py` | Upsert, counter, security tests | VERIFIED | 14 test methods covering SC2, D-07..D-13, D-19, T-01-04. |
| `tests/test_paths.py` | Path precedence | VERIFIED | 8 test methods. |
| `tests/test_migrations.py` | Schema lifecycle | VERIFIED | Lifecycle, WAL failure, transaction-guard and race tests. |
| `tests/test_concurrency.py` | 10-process tests | VERIFIED | `get_context("spawn")`, `Barrier`, `path.exists()` check, reader loop with deadline (WR-06). |
| `tests/test_core_imports.py` | Stdlib-only and side-effect checks | VERIFIED | `-S` child process compared with `sys.stdlib_module_names`. |
| `.gitignore` | Ignores `__pycache__`, `*.db`, `*.db-wal`, `*.db-shm`, `*.bak-v*` | VERIFIED | Contents match the plan. |

All of the above are tracked in git (`git ls-files`); the working tree has no uncommitted changes under `lookup/`, `tests/` or `.gitignore`.

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `tests/test_store.py` | `lookup/normalize.py` | `upsert_word(conn, normalize(v))` | WIRED | `test_normalized_variants_share_one_row` passes: `Book`, `“Book’s”`, `book,` give 1, 2, 3 and one row. |
| `lookup/store.py` `upsert_word` | SQLite `words` table | single parametrised `INSERT ... ON CONFLICT(word) DO UPDATE ... RETURNING count` | WIRED | Code lines 154-166; counts 1..10 confirmed by the concurrency tests. |
| `lookup/store.py` `open_store` | `_connect` / `_ensure_wal` / `_snapshot` / `BEGIN IMMEDIATE` | locked order in code | WIRED | Order confirmed by reading lines 293-364: version check, WAL, snapshot, lock, steps, `user_version`, `COMMIT`. |
| `open_store(path=None)` | `default_db_path()` | `path = Path(path) if path is not None else default_db_path()` | WIRED | Line 293; `test_open_store_without_argument_uses_lookup_db` passes. |
| `tests/_workers.py` `child` | `lookup/store.py` | `open_store(Path(path))` then `upsert_word(...)` | WIRED | Results 1..10 and final count 10 could not occur otherwise. |
| `tests/test_concurrency.py` | `tests/_workers.py` | `ctx.Process(target=_workers.child)` under spawn | WIRED | Passes on Windows, where spawn is the only start method. |

Note on wiring: outside `tests/` nothing imports `lookup` yet. That is expected for a core-only phase; Phase 2 and later are the first production consumers.

### Data-Flow Trace (Level 4)

Not applicable in the UI sense (no rendering artifacts in this phase). Data flow for the data path was checked end to end in the tests: normalized key to `upsert_word` to a real SQLite row to a count read back by `open_store` in a fresh connection (`test_two_saves_one_row`, `_assert_writers_ok`). Status: FLOWING.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Full phase suite, Python 3.14.3 (gate) | `python -m unittest -v` | Ran 63 tests in 5.6 s, OK, exit 0 | PASS |
| Full phase suite, Python 3.12.0 (gate) | `py -3.12 -m unittest -v` | Ran 63 tests in 5.2 s, OK, exit 0 | PASS |
| Concurrency flake check (3 runs) | `python -m unittest tests.test_concurrency` x3 | OK, OK, OK | PASS |
| SC1 examples | `python -c` with `normalize()` on `Running`, `run,`, `“Book’s”`, `mp3`, `x`, Cyrillic, `Straße`, `ﬁnd`, `Ｒｕｎ` | Values as expected (see truth 1 and 4) | PASS |
| Reader overlaps writers | Instrumented run of `_run_writers` with a reader | 29 reader samples during writes | PASS |
| Step-guard bypass probe | Migration step calls `c.execute('SELECT 1').connection.commit()` then fails | `MigrationError` raised, but `z` and `y` columns stayed committed at `user_version` 1; reopen fails with `duplicate column name: z` | FAIL (see W1) |
| Probe execution (Step 7c) | `find . -path '*/tests/probe-*.sh'` | No probe scripts exist and the phase declares none | SKIPPED (no probes declared) |

Note on the console: printing non-ASCII from Python on this Windows console failed with a cp1251 `UnicodeEncodeError`. That is the console codepage, not the code. The same values print correctly with `PYTHONIOENCODING=utf-8`.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| DATA-02 | 01-01 | Word is normalised before counting: case, edge punctuation, quotes, `'s` | SATISFIED | Truths 1-5; `lookup/normalize.py`; 14 unittest methods pass. REQUIREMENTS.md marks it Complete for Phase 1. |
| DATA-01 | 01-02, 01-03 | Each found word saved with translation, context, count, first and last seen | SATISFIED | Truths 7-16; `lookup/store.py`; store and concurrency tests pass. REQUIREMENTS.md marks it Complete for Phase 1. |

Cross-reference: the PLAN frontmatter `requirements:` fields (01-01: DATA-02; 01-02: DATA-01; 01-03: DATA-01) match REQUIREMENTS.md. REQUIREMENTS.md maps only DATA-01 and DATA-02 to Phase 1 (traceability table lines 112-113). No orphaned requirements.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `lookup/store.py` | 169-189, 192-245 | `_StepConnection` guard is advisory: a step reaches the real connection via `cursor.connection` or the `_conn` slot, so it can commit. Post-step `in_transaction` check detects this only after the commit. | WARNING (W1) | Does not affect any tested must-have. Real migrations do not exist yet (only `_v1`). Phase 2 authors of multi-step migrations must not rely on the guard. |
| `lookup/store.py` | 89-119 | WAL-switch wait is capped at 2.0 s (`_WAL_MAX_WAIT`) even when the caller asks for 5 s | INFO | Deliberate trade-off for the 1.5 s hotkey budget. Verified by tests; timing on the VM is a human item. |
| `tests/test_concurrency.py` | 48-51, 91-95 | Reader monotonicity loop passes vacuously if the reader collected no samples | INFO (I1) | In my run the reader collected 29 samples. A stronger test would add `self.assertTrue(seen)`. |
| `lookup/normalize.py` | 6-8, 36-37 | Review IN-01: NFKC can produce characters the translate tables do not map, so those tokens are rejected (not mis-keyed) | INFO | Rejection, not a wrong key. Left unfixed by the review-fix pass (Info items were out of scope). |
| `lookup/normalize.py` | 58-60 | Review IN-03: runs like `well--known` are accepted as a distinct key | INFO | Typo variant only; not a spelling of the same word in DATA-02's sense. |
| `lookup/store.py` | 135-166 | Review IN-07: `NULLIF(?, '')` is redundant with `_clean_text` | INFO | Defence in depth; no behavioural effect. |
| `lookup/store.py` | 278-367 | Review IN-05: DB file permissions depend on umask when the directory already exists | INFO | Arch home is normally 0700. Note for the Phase 7 README. |
| `lookup/store.py` | 344-354 | Review IN-06: stale `*.bak-v*.tmp` files after a crash are never cleaned up | INFO | Disk clutter only. |
| `lookup/store.py` | 310-313, 332-337 | If the version drops to 0 between the read and the lock, the snapshot is discarded and steps run with no backup | INFO | Requires the DB file to be replaced under a running process. Not reachable in normal use. |
| `tests/test_migrations.py` | 21-27 | Review IN-08: one module-wide faulthandler watchdog (120 s, `exit=True`) | INFO | Can kill the whole run on a slow VM. |

No debt markers (`TBD`, `FIXME`, `XXX`, `TODO`, `HACK`, `PLACEHOLDER`) in `lookup/` or `tests/`. No `print` or `logging` in `lookup/`. No f-string SQL. Stub scan: none. The review's six WARNINGs (WR-01..WR-06) are verified fixed in the final code, with regression tests (see below). Their Info items are listed above.

### Review Fix Verification (WR-01..WR-06 against the final code)

| Finding | Fix present in final code | Regression test present and passing |
| ------- | ------------------------- | ----------------------------------- |
| WR-01 WAL retry unbounded | Yes: `_WAL_MAX_WAIT`, deadline loop, `busy_timeout` restored in `finally` (lines 89-119) | `test_wal_switch_under_lock_fails_fast_with_default_timeout`, `test_wal_switch_deadline_follows_short_timeout`, `test_busy_timeout_restored_after_wal_switch` |
| WR-02 all open errors become MigrationError | Yes: steps 3-4 unwrapped, steps 6-7 wrapped (lines 295-310, 361-364) | `test_not_a_database_raises_sqlite_error_not_migration_error`, `test_migration_failure_keeps_cause_and_type_name` |
| WR-03 steps may commit | Partly: direct `commit()`, `rollback()`, `BEGIN`/`COMMIT` text and the attribute route are blocked; a post-step check exists. Bypass via `cursor.connection` still works (W1). | `test_transaction_control_rejected`, `test_executescript_runs_inside_the_transaction`, `test_step_that_ends_transaction_out_of_band_is_detected` |
| WR-04 float `now` | Yes: `int(now)`, bool and non-number rejected (lines 148-153) | `test_float_now_stored_as_integer_seconds`, `test_invalid_now_rejected` |
| WR-05 race migrates without backup | Yes: bounded re-snapshot loop, `_MIGRATE_ATTEMPTS = 5` (lines 316-357) | `test_intermediate_version_is_snapshotted_again`, `test_fresh_db_populated_concurrently_gets_backup`, `test_endlessly_changing_version_gives_up` |
| WR-06 reader loop without deadline | Yes: `_WRITERS_DEADLINE = 90` and `self.fail` (test_concurrency lines 42-47) | `test_reader_loop_has_deadline` |

### Human Verification Required

The two items below are the only items that need a human. Neither blocks Phase 2, per the plan and the user's note.

### 1. Arch VM: default_db_path under the real home

**Test:** On the Arch VM, with no `LOOKUP_DB` and no `XDG_DATA_HOME` override, run `python -c "import lookup.store as s; print(s.default_db_path())"` from the repo root.
**Expected:** Prints a path ending in `.local/share/lookup/lookup.db` under the real home directory. Nothing is created on disk.
**Why human:** This Windows machine cannot exercise POSIX home and XDG resolution for real. The test suite covers the logic with patched `Path.home` and env vars. This is the deferred human-check from plan 01-02 Task 1, scheduled for the Phase 8 VM pass.

### 2. Arch VM: WAL-switch failure timing

**Test:** On the Arch VM, hold an exclusive lock on a `lookup.db` from another process, then call `open_store()` on a file not yet in WAL mode.
**Expected:** Fails with `sqlite3.OperationalError` "could not switch database to WAL: database is locked" within about 2 s, not minutes.
**Why human:** The 2 s bound (`_WAL_MAX_WAIT`) was measured by the review-fix pass on Windows only. The 1.5 s hotkey budget (PERF-01) is measured on the VM in Phase 8.

## Gaps Summary

No BLOCKERS. Every must-have truth is VERIFIED, and both requirements (DATA-01, DATA-02) are satisfied by code and passing tests.

**WARNING W1 (residual, not a gap):** The migration transaction guard (WR-03 fix) is advisory. A migration step can commit by calling `Connection.commit()` on a cursor's `.connection` (or via `_StepConnection._conn`). The post-step `in_transaction` check raises `MigrationError` only after the commit has happened. I reproduced this: the step's `ALTER` statements stayed committed at `user_version` 1, and reopening the database then failed with `duplicate column name`, which is the lockout WR-03 describes. The review-fix report described this as a known limit covering only `COMMIT` through `execute()`. The actual bypass is wider. Recommended follow-up before the first real multi-step migration (Phase 2 or later): either document the rule as a convention with a test, or enforce it by running each step on a connection that cannot reach the transaction (for example, by checking `cursor.connection is conn` for each cursor returned by the guard). This does not change the status, because the tested must-have (a failing step rolls back every step) holds.

**Schema note:** Production `CURRENT_VERSION` is 1. The "old-schema DB opens under the new version" criterion is proven through a synthetic v2 step (D-19). A real v1 to v2 migration will first be exercised in a later phase.

## Notes for the Orchestrator

- The phase gate is green on both interpreters: `python -m unittest -v` (3.14.3) and `py -3.12 -m unittest -v` (3.12.0), 63 tests each.
- `.planning/config.json` shows as modified in `git status`. It is unrelated to this phase and was not touched by this verification.
- The verifier did not commit this file. The orchestrator bundles it with the phase artifacts.

---

_Verified: 2026-10-23T21:32:57Z_
_Verifier: Claude (gsd-verifier)_
