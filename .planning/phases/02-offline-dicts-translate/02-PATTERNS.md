# Phase 2: Офлайн-словари и перевод - Pattern Map

**Mapped:** 2026-10-24
**Files analyzed:** 22 (11 new modules and data files in `lookup/`, 1 modified module, 9 new and 4 modified test files)
**Analogs found:** 9 / 22 (the rest are new kinds of code with no close analog; the planner should use RESEARCH.md Format Reference and Code Examples for them)

## Scope of the codebase read

Read in full: `lookup/__init__.py`, `lookup/normalize.py`, `lookup/store.py`, `tests/_support.py`, `tests/_workers.py`, `tests/test_core_imports.py`, `tests/test_migrations.py`, `tests/test_store.py`.

Not read (check before planning the test files that depend on them): `tests/test_paths.py`, `tests/test_concurrency.py`, `tests/test_normalize.py`. `test_concurrency.py` very likely imports `_workers.child` and `_workers.migrate_child`, so it is affected by the `MIGRATIONS[:1]` change below.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `lookup/store.py` (modify: `_v2`, `upsert_word(lemma=)`) | model / store | CRUD | `lookup/store.py` itself | exact |
| `lookup/config.py` | config | file-I/O (read JSON) | `lookup/store.py` `default_db_path` (XDG + env) | role-match |
| `lookup/dicts.py` | service (discovery, search, base form) | request-response (in-memory index) | `lookup/store.py` `open_store` (open once, return handle) | role-match |
| `lookup/stardict.py` | model/reader | file-I/O, random access | none (no binary reader in repo) | no analog |
| `lookup/dsl.py` | reader | file-I/O, transform | none | no analog |
| `lookup/mdx.py` | reader | file-I/O, transform | none | no analog |
| `lookup/lzo.py` | utility (pure codec) | transform | `lookup/normalize.py` (pure function, module docstring, constants) | partial |
| `lookup/ripemd128.py` | utility (pure digest) | transform | `lookup/normalize.py` | partial |
| `lookup/online.py` | client (HTTP) | request-response, deadline | `lookup/store.py` error classes (`SchemaTooNewError`, `MigrationError`) | partial |
| `lookup/translate.py` | orchestrator | request-response, event flow | `lookup/store.py` `open_store` / `upsert_word` calls and `normalize.py` | role-match |
| `lookup/__main__.py` | CLI | request-response | none (no CLI yet) | no analog |
| `lookup/data/irregular.txt` | data | — | none | no analog |
| `lookup/data/NOTICE-wordnet.txt` | data | — | none | no analog |
| `tests/test_stardict.py`, `tests/test_dsl.py`, `tests/test_mdx.py`, `tests/test_lzo.py`, `tests/test_ripemd128.py` | test | — | `tests/test_normalize.py` style (unit) + `tests/_support.py` | role-match |
| `tests/test_dicts.py`, `tests/test_online.py`, `tests/test_translate.py`, `tests/test_config.py`, `tests/test_cli.py` | test | — | `tests/test_store.py` `UpsertTests` (setUp with `make_tempdir`, `addCleanup`) | role-match |
| `tests/test_core_imports.py` (modify) | test | — | itself | exact |
| `tests/test_migrations.py` (modify) | test | — | itself | exact |
| `tests/test_store.py` (modify) | test | — | itself | exact |
| `tests/_workers.py` (modify) | test helper | — | itself | exact |

## Pattern Assignments

### `lookup/store.py` (model/store, CRUD) — modify

**Analog:** itself.

**Module docstring and privacy rule** (lines 1-5). New modules copy this form:
```python
"""SQLite store for looked-up words: versioned schema, data path, atomic counter (DATA-01).

Privacy rule (V7): this module never prints or logs. Exception messages carry
versions and type names only, never word, context or translation text.
"""
```

**Imports** (lines 6-12): stdlib only, one name per line for `from` imports is not used; `import x` then `from pathlib import Path`.
```python
import glob
import os
import random
import re
import sqlite3
import time
from pathlib import Path
```

**Current migration step and tuple** (lines 43-63). Add `_v2` here. The step receives `_StepConnection`, so it must not call `commit`/`rollback`/`BEGIN`:
```python
def _v1(conn):
    conn.execute(
        "CREATE TABLE words ("
        "word TEXT PRIMARY KEY, "
        "translation TEXT, "
        "context TEXT, "
        "count INTEGER NOT NULL DEFAULT 1, "
        "first_seen INTEGER NOT NULL, "
        "last_seen INTEGER NOT NULL, "
        "lemma TEXT)"
    )

# (comment block lines 56-61: a step runs inside the caller's transaction, must not control it)
MIGRATIONS = (_v1,)
CURRENT_VERSION = len(MIGRATIONS)
```
Planned addition (D-19), same shape:
```python
def _v2(conn):
    conn.execute(
        "CREATE TABLE translations ("
        "text TEXT NOT NULL, "
        "kind TEXT NOT NULL CHECK(kind IN ('word','phrase','sentence')), "
        "provider TEXT NOT NULL, "
        "payload TEXT NOT NULL, "
        "fetched_at INTEGER NOT NULL, "
        "PRIMARY KEY(text, kind))"
    )
    conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")

MIGRATIONS = (_v1, _v2)
```

**Path resolution with env override and XDG fallback** (lines 66-74). This is the pattern for `LOOKUP_DICTS`, the config path and the index cache path (D-01, D-03, D-08). Note the `os.path.isabs` guard: XDG values must be absolute, otherwise the default is used.
```python
def default_db_path() -> Path:
    """Resolve the database path (D-11). Creates nothing on disk."""
    explicit = os.environ.get(DB_ENV)
    if explicit:
        return Path(explicit)
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg and os.path.isabs(xdg):
        return Path(xdg) / "lookup" / "lookup.db"
    return Path.home() / ".local" / "share" / "lookup" / "lookup.db"
```
Constant naming: `DB_ENV = "LOOKUP_DB"` (line 14). Add `DICTS_ENV = "LOOKUP_DICTS"` and similar constants in the same style.

**Error classes** (lines 30-40): a one-line docstring, subclass of `RuntimeError`, message says what happened, not the user's text. `online.py` and `dicts.py` use the same shape for `TranslateError(reason)` and `DictError(reason)`:
```python
class SchemaTooNewError(RuntimeError):
    """The database was written by a newer version of the program."""


class MigrationError(RuntimeError):
    """Migrating the database failed (snapshot, write lock or a step); nothing was committed. ..."""
```

**Upsert with bound parameters and COALESCE** (lines 164-196). The `lemma` parameter (D-12) is added by the same rule as `translation`: a `None` never overwrites a stored value. The SQL shape to extend:
```python
def upsert_word(conn, word, translation=None, context=None, now=None) -> int:
    """Count one search of `word` and return the new counter value.
    ...
    """
    if not isinstance(word, str):
        raise TypeError("word must be str, got " + type(word).__name__)
    word = word.strip()
    if not word:
        raise ValueError("word must not be empty")
    translation = _clean_text(translation)
    ...
    cur = conn.execute(
        "INSERT INTO words (word, translation, context, first_seen, last_seen) "
        "VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(word) DO UPDATE SET "
        "count = words.count + 1, "
        "last_seen = excluded.last_seen, "
        # _clean_text already turned empty text into NULL.
        "translation = COALESCE(excluded.translation, words.translation), "
        "context = COALESCE(excluded.context, words.context) "
        "RETURNING count",
        (word, translation, context, now, now),
    )
    rows = cur.fetchall()
    return int(rows[0][0])
```
Add to this: `lemma=None` keyword (appended after `now` so existing callers do not change), `_clean_text(lemma)` before the call, `lemma` in the INSERT column list, and `lemma = COALESCE(excluded.lemma, words.lemma)` in the SET list. Keep the `TypeError`/`ValueError` validation for the new argument in the same style.

**Version floor and check order** (lines 79-80, 379-381): `open_store` raises `_too_new(v, target)` before any write. Reuse `open_store(path, migrations=...)` in tests; the `migrations` argument is the test seam (see the Tests section).

### `lookup/normalize.py` (utility, transform) — analog for pure modules

**Analog for:** `lzo.py`, `ripemd128.py`, `dicts.py` helpers (candidate generation for base form), `translate.py` classification.

**Module docstring and imports** (lines 1-3):
```python
"""Counting-key normalisation for looked-up words and short phrases (DATA-02)."""
import re
import unicodedata as ud
```

**Module-level constants with a comment explaining the why** (lines 5-12). Copy this style for WordNet and suffix tables, and for the LZO constants:
```python
# Explicit maps run BEFORE NFKC: NFKC does not fold these to ASCII
# (U+2019, U+02BC stay; U+00B4 becomes " ́"). They run again after NFKC,
# which produces some of them (U+0149 -> U+02BC n, U+FE58 -> U+2014).
_APOS = dict.fromkeys(map(ord, "‘’‚‛ʼʻʹ′´`"), "'")
```

**Public function signature with type hints and TypeError guard** (lines 32-38). Pure functions raise `TypeError` for wrong types, never print:
```python
def normalize(text: str) -> str | None:
    """Return the counting key for a word or 1-N word phrase, or None to reject.

    The caller must not touch the database when None is returned (D-04).
    """
    if not isinstance(text, str):
        raise TypeError("text must be str, got " + type(text).__name__)
```
Apply: `lzo.decompress(data: bytes, out_len: int) -> bytes` should raise `ValueError` on malformed input (no text involved). `ripemd128.digest(data: bytes) -> bytes` should take `bytes` and raise `TypeError` otherwise.

**Pitfall to carry over:** `normalize` returns `None` as the reject signal (line 32). `dicts.lookup` and base-form candidates should use the same convention (`None` or empty list = not found), not exceptions, so the orchestrator does not need try/except for normal misses.

### `lookup/dicts.py` (service, request-response) — new

**Analog:** `lookup/store.py` `default_db_path` + `open_store` (open once, return a handle the caller keeps).

**Discovery roots** follow `default_db_path` (lines 66-74) plus D-01:
```python
def dict_roots() -> list[Path]:
    explicit = os.environ.get(DICTS_ENV)          # LOOKUP_DICTS, colon-separated (tests)
    if explicit:
        return [Path(p) for p in explicit.split(os.pathsep) if p]
    xdg = os.environ.get("XDG_DATA_HOME")
    user = (Path(xdg) if xdg and os.path.isabs(xdg) else Path.home() / ".local" / "share") / "lookup" / "dicts"
    return [user, Path("/usr/share/lookup/dicts")]
```
Note: `os.pathsep` is `;` on Windows; the spec says `:`. For the Windows host tests, the planner should use `os.pathsep` and say so, or tests set the variable with the platform separator.

**Open once, keep the handle, never re-read on search** (RESEARCH Pattern 2): mirror `open_store` returning `conn` and letting the caller close it. `open_dicts(roots, config) -> list[Dictionary]`; the CLI and Phase 5 daemon hold the list.

**Error reasons:** `DictError(reason)` follows the `MigrationError` shape (store.py lines 34-40): the message is a short reason, not file content.

### `lookup/config.py` (config, file-I/O) — new

**Analog:** `lookup/store.py` `default_db_path` for `$XDG_CONFIG_HOME/lookup/config.json` (D-03). Same absolute-path guard. Add `CONFIG_ENV` if needed for tests, following `DB_ENV = "LOOKUP_DB"`.

**Missing file is valid:** D-03 says no file means "everything enabled, alphabetical order". Follow the store convention that a missing file creates nothing on disk: `open_store` creates the file only on first use, and `test_import_has_no_side_effects` (test_core_imports.py lines 45-51) shows that import does nothing. `config.load()` must not create `~/.config/lookup/`.

### `lookup/translate.py` (orchestrator) — new

**Analog:** the call sequence in `tests/test_store.py` `UpsertTests` and `_workers.child` (`tests/_workers.py` lines 17-26): open store, call `upsert_word` with translation and context, close in `finally`.
```python
conn = open_store(Path(path))
try:
    count = upsert_word(conn, "run", translation="бежать", context="context %d" % index)
finally:
    conn.close()
```
Use the same `try/finally` shape for the connection in `__main__.py`. `translate.py` itself does not open the DB when the caller passes a connection (RESEARCH Integration Points: Phase 3/5 pass open dicts and connection in).

**Normalization and classification:** call `normalize(text)` first and return early on `None` (normalize.py line 35: the caller must not touch the database when None is returned, D-04/D-23).

**Sentence thread (D-18):** no analog in the repo. Use `concurrent.futures` per RESEARCH Standard Stack and `future.result(timeout=...)`. The threaded test in `tests/test_concurrency.py` (not read) is the nearest existing threading test; check it before writing the new one.

### `lookup/online.py` (client, request-response with deadline) — new

**Analog for the error type:** `lookup/store.py` error classes (lines 30-40). `TranslateError` carries one of the fixed reasons (D-16): `no_network`, `timeout`, `blocked`, `bad_response`, `not_found`.
```python
class TranslateError(RuntimeError):
    """Online translation failed; `reason` is one of the fixed D-16 codes."""

    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason
```
Message = reason code only (V7). Do not put the query text in the message.

**No analog for HTTP.** Use RESEARCH Pattern 4 (deadline chain) and Format Reference 6 (failure classification). Read at most 1 MiB (RESEARCH Format Reference 6).

### `lookup/stardict.py`, `lookup/dsl.py`, `lookup/mdx.py` (readers) — new

**No analog in the repo.** Use RESEARCH Format Reference 1-3 and Pattern 1 (`Article` dataclass and `Dictionary` protocol). Apply the store's conventions:
- Validate every offset and size before slicing (RESEARCH Finding 4, Format Reference 1 "Index entry validation"): skip the entry, count it in `skipped_entries`. Do not raise for a single bad entry.
- Open failures raise `DictError(reason)`; `dicts.py` records the reason and continues (D-02).
- Bounded decompression: `zlib.decompressobj(...).decompress(data, max_length)` (RESEARCH Pitfall 8).
- No `print`/`logging` (V7 rule from store.py lines 3-5).

### `lookup/lzo.py` (utility, transform) — new

**Analog:** `lookup/normalize.py` for module shape. Code: RESEARCH Code Examples 1 (verified against liblzo2 2.10). Check `out_len` before the loop and stop when output exceeds it (RESEARCH Pitfall 8). Test vectors come from liblzo2 in the VM (RESEARCH Supporting table: `tests/fixtures/lzo/`).

### `lookup/ripemd128.py` (utility, transform) — new

**Analog:** `lookup/normalize.py` for module shape. Test with the two standard vectors in RESEARCH Format Reference 8 (`cdf26213a150dc3ecb610f18f6b38b46` for empty input; `3fa9b57f053c053fbe2735b2380db596` for the fox sentence). Do not add it to the core as a security primitive; the module docstring should state that it is for MDX format compatibility only.

### `lookup/__main__.py` (CLI) — new

**No analog.** Requirements from CONTEXT D-25 and RESEARCH Anti-patterns:
- Only module that prints (V7, store.py lines 3-5).
- `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` at start (RESEARCH Anti-patterns: cp1251 console on the Windows host).
- Exit codes 0 / 1 / 2 (D-25).
- Plain text output only (D-06: UI renders plain text).

### Modified test files

#### `tests/_support.py` (test helper) — shared, analog for every new test file

Copy `make_tempdir` for every new test. It sets `LOOKUP_DB` to a temp path and registers cleanup, so no test touches the real `~/.local/share/lookup/` (lines 8-24):
```python
def make_tempdir(testcase) -> Path:
    tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    testcase.addCleanup(tmp.cleanup)
    root = Path(tmp.name)
    patcher = mock.patch.dict(
        os.environ, {"LOOKUP_DB": str(root / "data" / "lookup" / "lookup.db")}
    )
    patcher.start()
    testcase.addCleanup(patcher.stop)
    return root
```
Add `LOOKUP_DICTS`, `XDG_CONFIG_HOME` and `XDG_CACHE_HOME` to the same `mock.patch.dict` call (or a sibling helper) so tests for dictionaries, config and cache also stay inside the temp dir. The `addCleanup` order matters on Windows (RESEARCH Pitfall 6: close connections before the temp dir is deleted).

#### `tests/test_core_imports.py` (modify)

**Analog:** itself. Extend `_IMPORTS` (line 12) so the new modules are imported and checked for stdlib-only and no Qt:
```python
_IMPORTS = "import lookup, lookup.normalize, lookup.store\n"
```
Planned: `"import lookup, lookup.normalize, lookup.store, lookup.stardict, lookup.dsl, lookup.mdx, lookup.lzo, lookup.ripemd128, lookup.dicts, lookup.config, lookup.online, lookup.translate\n"`. Do not add `lookup.__main__` (it is a script entry point, and importing it runs the CLI). The test `test_import_has_no_side_effects` (lines 45-51) must keep passing: no module may create `~/.config/lookup` or the cache dir on import.

Also extend `test_public_names_present` (lines 53-69) with the new public names, following the existing loop shape.

#### `tests/test_migrations.py` (modify)

**Analog:** itself. These are the lines that break when `_v2` is added (D-35):

1. `_make_v1` (lines 42-48) calls `open_store(path)` with the full `MIGRATIONS`. After `_v2` this creates a v2 database, so "v1" is wrong. Change to:
```python
V1 = MIGRATIONS[:1]  # D-35: the schema that "v1" means in these tests

def _make_v1(path, rows):
    conn = open_store(path, migrations=V1)
    try:
        for word in rows:
            upsert_word(conn, word, "tr-" + word, "ctx " + word, now=10)
    finally:
        conn.close()
```
2. `M2 = MIGRATIONS + (_add_probe,)` (line 55) becomes `M2 = V1 + (_add_probe,)` if the test means "v1 plus one synthetic step", or stays as `MIGRATIONS + (_add_probe,)` with the assertions updated to version 3. Pick one and update every assertion that says `2` (lines 105, 113, 147, 173) and the backup name `t.db.bak-v1` (line 116). The planner must choose the target number; the simplest rule is to keep `M2 = V1 + (_add_probe,)` so the synthetic version numbers stay as they are.
3. `M3 = M2 + (_add_probe2,)` (line 184) inherits the same choice.
4. `test_newer_db_refused_untouched` (lines 124-139) uses `CURRENT_VERSION` and `99`; it needs no change.
5. `test_intermediate_version_is_snapshotted_again` (lines 208-232) uses `bump_to_v2` (lines 198-206) which `ALTER`s `probe` onto `words` and sets version 2. With `_v2` real, this conflicts with the synthetic version numbers. Rewrite with `V1` base and a synthetic bump, or assert the backup of the real v2 schema.
6. `test_old_version_db_migrated_without_losing_words` (lines 109-122) and `test_failing_step_rolls_back_all_steps` (141-152) assert `user_version == 1` / `2`. Update with the same rule as item 2.

Helpers to keep as-is: `_Watchdog` (lines 22-31), `_columns` (lines 51-52), `_add_probe` (lines 34-35).

#### `tests/test_store.py` (modify)

**Analog:** itself. These assertions pin v1 and must change (D-35):
- Lines 27-44 `test_schema_v1_columns_and_only_words_table`: `tables == ["words"]` (line 40) and `CURRENT_VERSION == 1` (line 42) become `tables == ["meta", "translations", "words"]` and `CURRENT_VERSION == 2`. Rename the test to `test_schema_v2_...`.
- Line 41 uses `CURRENT_VERSION` directly and needs no change.
- `test_normalized_variants_share_one_row` (lines 129-141): no change; it does not depend on version.

Add a `lemma` test here (D-12): `upsert_word(conn, "running", lemma="run", now=1)` then assert `row("running")[6] == "run"`, and a second call with `lemma=None` keeps `"run"` (COALESCE).

#### `tests/_workers.py` (modify)

**Analog:** itself. `migrate_child` (lines 31-42) opens with `MIGRATIONS + (add_probe,)`. After `_v2`, the version reached is 3, not 2. Change to `MIGRATIONS[:1] + (add_probe,)` (the v1 base, as in D-35) so the expected value in `test_concurrency.py` (not read) stays the same. `child` (lines 12-26) needs no change.

### New test files

**Analog:** `tests/test_store.py` `UpsertTests` (lines 11-18):
```python
class UpsertTests(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)
        self.conn = open_store(self.root / "t.db")
        self.addCleanup(self.conn.close)
```
Pattern: `unittest.TestCase`, `setUp` with `make_tempdir(self)`, `addCleanup` for every connection and file handle, one assertion topic per `test_*` method, `if __name__ == "__main__": unittest.main()` at the end (test_store.py lines 151-152).

Use `tests/test_core_imports.py` `_run` (lines 25-33) for any test that checks a subprocess (CLI exit code, `-S` stdlib-only check).

Synthetic fixtures (CONTEXT Claude's Discretion): write tiny StarDict/DSL/MDX files in `setUp` into `self.root`, not committed binaries. For MDX, a mini-writer in the test file (zlib and LZO blocks) per RESEARCH Format Reference 3.

Network tests (D-20 cache test, "network forbidden"): patch `urllib.request.urlopen` to raise `AssertionError` with `mock.patch`, the same `unittest.mock` style as `test_store.py` line 145 (`mock.patch.object(store.sqlite3, "sqlite_version_info", ...)`).

## Shared Patterns

### XDG path resolution with env override
**Source:** `lookup/store.py` lines 66-74
**Apply to:** `dicts.py` (`LOOKUP_DICTS`, user dicts dir), `config.py` (`$XDG_CONFIG_HOME/lookup/config.json`), index cache in `dicts.py` or `mdx.py`/`dsl.py` (`$XDG_CACHE_HOME/lookup/index/`)
```python
xdg = os.environ.get("XDG_DATA_HOME")
if xdg and os.path.isabs(xdg):
    return Path(xdg) / "lookup" / "lookup.db"
return Path.home() / ".local" / "share" / "lookup" / "lookup.db"
```
Planner note: three functions now repeat this shape (data, config, cache). Put one helper (`_xdg_dir(env_name, default_rel)`) in `config.py` or a tiny module and use it in all three. This is the only place a shared helper is justified here.

### Error classes that carry a reason, not user text
**Source:** `lookup/store.py` lines 30-40 (`SchemaTooNewError`, `MigrationError`), and `_too_new` lines 339-343 which formats a version message in Russian
**Apply to:** `dicts.DictError(reason)`, `online.TranslateError(reason)` (D-16 fixed reasons), `translate` errors
Messages are type names, versions or fixed reason codes. Russian user-facing text (e.g., "нет сети") is produced by the CLI from the reason code, not inside the exception (D-16).

### V7 privacy: no print, no logging in library modules
**Source:** `lookup/store.py` lines 3-5 (module docstring) and `lookup/store.py` line 155 (`TypeError` text uses type name only)
**Apply to:** all new modules in `lookup/` except `__main__.py`. Only the CLI prints. The test for this can be a grep test: no `print(` or `logging` in `lookup/` except `__main__.py`. Add it to `test_core_imports.py` if the planner wants a hard check.

### Stdlib-only core, no Qt
**Source:** `tests/test_core_imports.py` lines 12-18 (`_STDLIB_CODE`) and lines 35-43 (`test_core_imports_only_stdlib`)
**Apply to:** every new `lookup/` module. Subprocess with `sys.executable -S` checks that `sys.modules` only has stdlib names. Extend `_IMPORTS` (line 12) as described above.

### Bound SQL parameters and validation before writing
**Source:** `lookup/store.py` lines 170-182 (type and value checks, then `?` placeholders at lines 183-194)
**Apply to:** the `translations` cache writes in `translate.py`/`online.py` and the `meta` table (`last_provider` key for D-13)
```python
conn.execute(
    "INSERT INTO translations (text, kind, provider, payload, fetched_at) "
    "VALUES (?, ?, ?, ?, ?) ON CONFLICT(text, kind) DO UPDATE SET ...",
    (text, kind, provider, payload_json, fetched_at),
)
```
Use `json.dumps` for `payload` and `json.loads` on read; never `pickle` (RESEARCH "Don't Hand-Roll").

### Test isolation and hang guard
**Source:** `tests/_support.py` lines 8-24 (`make_tempdir`) and `tests/test_migrations.py` lines 22-31 (`_Watchdog`, `faulthandler.dump_traceback_later(60, exit=True)`)
**Apply to:** any test that uses threads (D-18 sentence thread, D-16 deadline), and any test that opens SQLite connections. Use `_Watchdog` for threaded tests.

### Stop-on-first-match ordering with explicit lists
**Source:** `lookup/normalize.py` lines 14-20 (`CONTRACTIONS` frozenset) and lines 49-70 (ordered rules)
**Apply to:** `dicts.py` base-form order (D-10: exact, pointer, irregular, suffix rules). Keep the order in one function with a comment naming D-10 and D-28, as `normalize` does with its numbered comments.

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md patterns instead):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `lookup/stardict.py` | reader | file-I/O, random access | No binary-format reader exists. Use RESEARCH Format Reference 1-2 and Code Examples. |
| `lookup/dsl.py` | reader | file-I/O, transform | No text-format parser exists. Use RESEARCH Format Reference 4. |
| `lookup/mdx.py` | reader | file-I/O, transform | No binary container reader exists. Use RESEARCH Format Reference 3 and Pattern 2. |
| `lookup/online.py` (HTTP part) | client | request-response | No HTTP code in the repo. Use RESEARCH Format Reference 6 and Pattern 4. |
| `lookup/__main__.py` | CLI | request-response | No CLI yet. Use D-25 and RESEARCH Anti-patterns (UTF-8 stdout). |
| `lookup/data/irregular.txt` | data | — | Generate from WordNet 3.1 `*.exc` (RESEARCH Format Reference 7). |
| `lookup/data/NOTICE-wordnet.txt` | data | — | WordNet licence notice (RESEARCH Format Reference 7). |
| `lookup/ripemd128.py` | digest | transform | Pure-Python digest; no analog. Use RESEARCH Format Reference 8 and its two test vectors. |

## Metadata

**Analog search scope:** `lookup/` (all `.py`), `tests/` (all `.py` from Glob)
**Files read in full:** 8 of 13 `.py` files (see "Scope of the codebase read")
**Files scanned:** 13
**Pattern extraction date:** 2026-10-24
