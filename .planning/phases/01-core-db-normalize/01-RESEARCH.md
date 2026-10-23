# Phase 1: Ядро: база и нормализация (core-db-normalize) - Research

**Researched:** 2026-10-24
**Domain:** Pure-Python core (word normalisation) + SQLite storage (UPSERT counter, schema versioning, concurrency), stdlib only, tested with `unittest` on Windows and Arch
**Confidence:** HIGH for SQLite/Python behaviour (run locally on 3.14.3 and 3.12, checked against official docs); HIGH for Unicode facts (run on `unicodedata`); MEDIUM for the normalisation policy choices flagged in Open Questions

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
Пользователь делегировал все решения («сам реши, или посмотри как делает Lookupper»). Ориентир — поведение Lookupper и рекомендации из `.planning/research/`.

- **D-01:** Ключ — нормализованная поверхностная форма. Порядок: Unicode NFC → кривые апострофы/кавычки (’ ‘ “ ” « » ` ´) → ASCII → обрезка не-букв по краям (пунктуация, кавычки, скобки, цифры) → `casefold()`/lower → снять концевой притяжательный `'s` (и одиночный `'` после `s`: `dogs'` → `dogs`).
- **D-02:** Внутренние апостроф и дефис сохраняются: `don't`, `o'clock`, `well-known` — один токен. Склейку переносов строки делает OCR (Phase 3), не нормализатор.
- **D-03:** Регистр всегда сбрасывается, включая имена собственные (`Apple` = `apple`) — как в Lookupper и чтобы слово в начале предложения не давало вторую запись.
- **D-04:** Отклонять (возвращать `None`): нет латинских букв, есть кириллица/смешанный алфавит (шум OCR), длина < 2 кроме `a`/`i`. Нормализатор сам ничего не пишет; вызывающий код при `None` не трогает базу.
- **D-05:** Фразы: та же функция для 2–4 слов — пробелы схлопываются в один, нормализуются края фразы и каждое слово. Правило «длиннее 4 слов не сохранять» — уровень вызова (DATA-03, Phase 2), но нормализатор должен уметь фразу.
- **D-06:** Лемматизации в Phase 1 нет: `running` и `run` — разные записи. В схеме заранее есть nullable-колонка `lemma` (базовая форма из словаря), которую заполнит Phase 2; группировка по ней — решение Phase 2/6.
- **D-07:** В записи слова хранится последний непустой контекст (распознанная строка / предложение) — его покажут попап и карточка. Пустой контекст не затирает прежний (`COALESCE(excluded.context, context)`).
- **D-08:** Истории всех контекстов нет (минимальное полное решение); при нужде Phase 6 добавит таблицу миграцией. Скриншоты не хранятся — только текст.
- **D-09:** В `words.translation` — короткий перевод для списка/попапа (одна строка: главные значения). Полная статья и кэш словарей/онлайна — отдельная таблица в Phase 2.
- **D-10:** Перевод обновляется при каждом поиске, если пришёл непустой (`COALESCE(excluded.translation, translation)`); ошибка перевода не сбрасывает старый.
- **D-11:** Файл `$XDG_DATA_HOME/lookup/lookup.db` (по умолчанию `~/.local/share/lookup/`), каталог создаётся; переопределение `LOOKUP_DB` для тестов. `sqlite3.connect(timeout=5)`, `PRAGMA journal_mode=WAL`, `busy_timeout`.
- **D-12:** Счёт — одним оператором `INSERT … ON CONFLICT(word) DO UPDATE SET count=count+1, last_seen=excluded.last_seen, …` с `RETURNING count` (нужно попапу «искали N раз»). Никаких SELECT-затем-UPDATE.
- **D-13:** Время — UTC, целые секунды Unix epoch (INTEGER); форматирует UI.
- **D-14:** Версия схемы — `PRAGMA user_version`; миграции — упорядоченный список функций, применяются в `BEGIN IMMEDIATE`; перед миграцией существующей базы делается копия `lookup.db.bak-v{N}`. База новее кода — открыть отказом с понятной ошибкой, не портить.
- **D-15:** Пакет Python `lookup/` (не один файл): в прод-версии с трей-демоном, словарями, OCR, окнами и PKGBUILD один файл быстро вырастет за порог ~450 строк из ARCHITECTURE.md. Phase 1 создаёт `lookup/__init__.py`, `lookup/normalize.py`, `lookup/store.py`, тесты в `tests/` (`python -m unittest`). Ядро импортирует только stdlib.

### Claude's Discretion
- Точные имена функций/колонок, формат исключений, структура тестов, способ запуска 10 параллельных процессов в тесте (multiprocessing/subprocess).

### Deferred Ideas (OUT OF SCOPE)
- Объединение форм слова по базовой форме (`lemma`) — Phase 2 (заполнение) / Phase 6 (показ в списке).
- История всех контекстов слова — при необходимости в Phase 6.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-01 | Каждое найденное слово сохраняется с переводом, контекстом (распознанной строкой), счётчиком поисков, временем первого и последнего поиска | UPSERT with `RETURNING count` (verified, §Code Examples 2); schema v1 (§Architecture Patterns 2); `user_version` migrations (§Pattern 3) |
| DATA-02 | Перед подсчётом слово нормализуется: регистр, крайняя пунктуация, кавычки, `'s` | Tested `normalize()` reference implementation (§Code Examples 1); Unicode pipeline order (§Pattern 1); fuzz-verified idempotence |
</phase_requirements>

## Summary

Phase 1 is a pure stdlib core: one normalisation function (`lookup/normalize.py`) and one SQLite store (`lookup/store.py`) with a versioned schema. Nothing here needs Qt, a display, or a network. The phase is mostly about getting SQLite concurrency and transaction semantics right, plus a handful of Unicode edge cases that the locked decisions (D-01..D-05) do not spell out.

I checked the risky parts by running them, not by reasoning. Three findings change the plan and must reach the planner:

1. **A fresh database breaks under concurrent first-open, even with `busy_timeout`.** `PRAGMA journal_mode=WAL` on a database that is not yet in WAL mode fails immediately with `database is locked` and ignores the busy handler. With 10 processes opening a new file at once, 7 of 8 runs lost writers. The fix is to read `PRAGMA journal_mode` first and retry the switch on `locked`; this gave 8 of 8 clean runs. The naive pre-created-database test passes and would have hidden this.
2. **NFKC does not fold the typographic characters D-01 lists.** U+2019 and U+02BC stay non-ASCII, and U+00B4 (´) becomes a space plus a combining mark. Quote/apostrophe/dash variants need an explicit map that runs before NFKC. Soft hyphen U+00AD survives NFKC and must be removed as a format character.
3. **A single-pass possessive strip is not idempotent.** `book's's` normalises to `book's` and then to `book`. The strip must run to a fixed point. The fuzz test found this; with the fixed-point loop, 0 violations in 20,000 random inputs.

**Primary recommendation:** Build `normalize()` as the Unicode pipeline in §Architecture Patterns 1 (explicit quote/dash map → NFKC → drop Cf → casefold → NFC → drop Mn → per-token edge strip and possessive strip to a fixed point → Latin-only check). Build `store` on `isolation_level=None` with explicit `BEGIN IMMEDIATE` migrations, a read-first WAL switch with retry, one `INSERT ... ON CONFLICT DO UPDATE ... RETURNING count`, and a backup via `Connection.backup()` (not a file copy). Test concurrency with `multiprocessing` `spawn` and a `Barrier`, on both a pre-created and a fresh database.

## Architectural Responsibility Map

Phase 1 has no browser, server, or CDN tier. Its capabilities map to three layers of the core package.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Word normalisation (DATA-02) | Pure core (`lookup/normalize.py`) | — | Pure function of a string; no I/O; must be testable with no DB and no desktop |
| Counter upsert + timestamps (DATA-01) | Storage (`lookup/store.py`, SQLite) | — | Atomicity comes from one SQL statement; the store owns the only write path |
| Schema versioning and backup | Storage (`lookup/store.py`) | Filesystem (backup file beside DB) | `user_version` lives in the DB header; backup must be a consistent SQLite snapshot |
| DB path resolution | Process environment (`lookup/store.py` helper) | — | Reads `LOOKUP_DB`, `XDG_DATA_HOME`, then the home directory; tests override via env |
| Concurrency guarantees | Storage (SQLite WAL + busy_timeout) | Test harness (spawn workers) | Correctness is enforced by SQLite; the test only proves it |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `sqlite3` (stdlib) | Python 3.14.3 bundles SQLite 3.50.4 locally; 3.12 bundles 3.42.0 | Storage, UPSERT, WAL, `user_version` | Only persistence layer allowed by project constraints (stdlib only); `RETURNING` needs SQLite ≥ 3.35.0 [CITED: sqlite.org/lang_returning.html] |
| `unicodedata` (stdlib) | Python 3.14.3 | `normalize()`, `category()`, `name()` for script checks | Authoritative Unicode data; no hand-written tables |
| `unittest` (stdlib) | Python 3.14.3 | Test runner | Decision D-15; no pytest |
| `multiprocessing` (stdlib) | Python 3.14.3 | 10-writer concurrency test | `get_context("spawn")` is the only start method on Windows; verified working |
| `pathlib`, `os`, `time`, `random` (stdlib) | — | Paths, `os.replace`, epoch time, retry jitter | Stdlib only, per CLAUDE.md |

### Supporting
None. Phase 1 adds no third-party dependency.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Single UPSERT with `RETURNING` | `SELECT` then `UPDATE` | Lost updates under concurrency. Rejected by D-12 and PITFALLS. |
| `Connection.backup()` | Copy `lookup.db` as a file | A file copy misses rows still in the `-wal` file (verified: copy raised `no such table` while backup kept all 3 rows). Use backup. |
| `isolation_level=None` | `autocommit=False` (3.12+) | `autocommit=False` opens a transaction on connect, so `BEGIN IMMEDIATE` fails with `cannot start a transaction within a transaction` (verified on 3.14 and 3.12). `isolation_level=None` works on 3.10+ and needs no special casing. |
| `casefold()` | `lower()` | Both are locale-independent in Python (no Turkish rules). `casefold` also folds `ß`→`ss` and ligatures, and handles Kelvin/long-s. Use `casefold`; the `ß` effect is harmless for English. |

**Installation:** none (stdlib).

**Version verification:** the runtime floor is SQLite ≥ 3.35.0 for `RETURNING`. Verified locally on SQLite 3.50.4 (Python 3.14.3) and 3.42.0 (Python 3.12). The Arch target (Python 3.14.8) links the system SQLite, which is current on Arch [ASSUMED: rolling release; not checked this session]. The store should assert `sqlite3.sqlite_version_info >= (3, 35, 0)` at open and raise a clear error.

## Package Legitimacy Audit

Not applicable: Phase 1 installs no external packages. Every dependency is Python stdlib (`sqlite3`, `unicodedata`, `unittest`, `multiprocessing`, `pathlib`, `os`, `time`, `random`). No `checkpoint:human-verify` is needed.

## Architecture Patterns

### Pattern 1: Normalisation as an ordered Unicode pipeline
**What:** Each step fixes a specific class of input. The order is significant: the explicit quote/dash map must run before NFKC, because NFKC turns U+00B4 into `" \u0301"`.
**When to use:** Every call to `normalize()`.
**Order (verified):**
1. Explicit map: apostrophe-like → `'`, double-quote-like → `"`, dash-like → `-`.
2. `NFKC`: fullwidth → ASCII (`＇`→`'`, `＂`→`"`), ligatures (`ﬁ`→`fi`), nbsp → space, Kelvin sign → `K`, long-s `ſ` → `s`.
3. Drop `Cf` (format): soft hyphen U+00AD, zero-width space, BOM.
4. `casefold()`, then `NFC`.
5. Drop `Mn` (stray combining marks). Verified case: `İ`.casefold() = `i` + U+0307, which becomes `istanbul`.
6. Split on whitespace. Per token: strip non-letter edges, strip `'s` and re-strip, to a fixed point.
7. Validate: every letter must be Latin (`unicodedata.name(c).startswith("LATIN")`); internal characters must be letters, `'` or `-`.
8. Length: key length ≥ 2, or key is `a` or `i`.

### Pattern 2: Schema v1 (one table, all phase-1 columns)
**What:** Put every column this phase needs into `words` on day one, including the nullable `lemma` that D-06 requires. Later phases add tables through migrations.
```sql
CREATE TABLE words (
  word        TEXT PRIMARY KEY,   -- normalised key (D-01..D-05); lowercase, no edge punctuation
  translation TEXT,               -- short gloss, nullable (D-09, D-10)
  context     TEXT,               -- last non-empty recognised line (D-07); never a screenshot
  count       INTEGER NOT NULL DEFAULT 1,
  first_seen  INTEGER NOT NULL,   -- Unix epoch seconds, UTC (D-13); set on insert only
  last_seen   INTEGER NOT NULL,   -- Unix epoch seconds, UTC; updated on every search
  lemma       TEXT                -- nullable; filled by Phase 2 (D-06)
);
```
No secondary index: the list window sorts by `count DESC, last_seen DESC` on a personal-scale table (ARCHITECTURE.md). See Open Questions 5 on whether `lemma` belongs in v1 or v2.

### Pattern 3: Migrations via `user_version` in `BEGIN IMMEDIATE`
**What:** An ordered tuple of migration callables. `user_version` is the count of applied steps. Opening a database:
1. Connect, set `busy_timeout`.
2. Read `user_version` **before any write**. If it is greater than the code's version, close and raise `SchemaTooNewError`. The file must not change (verified: byte-identical, no `-wal` created).
3. Switch to WAL with read-first and retry (see Pitfall 1).
4. If `0 < version < CURRENT`, back up the file to `lookup.db.bak-v{version}` with `Connection.backup()`.
5. `BEGIN IMMEDIATE`, **re-read** `user_version` under the lock (another process may have migrated), apply pending steps, set `user_version`, `COMMIT`. On any exception, `ROLLBACK`.

Verified: `PRAGMA user_version` changes roll back with the transaction; DDL rolls back; `journal_mode` cannot change inside a transaction (`cannot change out of wal mode from within a transaction`), so WAL must be set before `BEGIN`.

### Pattern 4: Single-statement counter
See §Code Examples 2. The `RETURNING count` gives the post-update value; the popup uses it for "искали N раз" (verified: returned 1, 2, 3 across three calls).

### Anti-Patterns to Avoid
- **`SELECT` then `INSERT`/`UPDATE`:** lost updates under 10 writers (D-12).
- **Copying `lookup.db` as the backup:** misses WAL content (verified).
- **`autocommit=False` with explicit `BEGIN`:** raises immediately (verified).
- **Setting `journal_mode=WAL` unconditionally on every open:** on a fresh database this is the lock failure in Pitfall 1.
- **`lower()` for caseless matching:** use `casefold()` (Pattern 1, step 4).
- **Logging context or translation text** in the store or normalizer: a privacy leak (Security Domain).
- **Importing Qt or anything non-stdlib** under `lookup/`: breaks the no-desktop test layer (D-15).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Atomic counter | Read-modify-write in Python | `INSERT ... ON CONFLICT DO UPDATE ... RETURNING` | Single statement is atomic under WAL + busy_timeout (verified, 10 writers) |
| Cross-process lock | `flock` / lock file / PID file for the DB | SQLite's own locking + `busy_timeout` | SQLite already serialises writers; a second lock adds failure modes. (The single-instance lock belongs to Phase 5 for the overlay, not the store.) |
| Database backup | `shutil.copy` of the file | `sqlite3.Connection.backup()` | Copies WAL content as a consistent snapshot (verified) |
| Unicode case/compat folding | Hand-written case tables, `str.lower` | `str.casefold()`, `unicodedata.normalize` | Stdlib data; `lower()` misses `ß` and some compatibility forms |
| Script detection | Code-point range tables | `unicodedata.name(c).startswith("LATIN")` | Names are authoritative; ranges miss Latin Extended |
| Test-run isolation | Shared test DB | `tempfile.TemporaryDirectory(ignore_cleanup_errors=True)` + `LOOKUP_DB` | Keeps tests out of `~/.local/share`; see Pitfall 6 |
| Migration framework | Alembic / yoyo | Ordered tuple + `user_version` (~30 lines) | Stdlib only; project is one small DB |

**Key insight:** the three hard problems here (atomic counting, safe migration, consistent backup) each have a single SQLite or stdlib primitive. Custom code around them is where the bugs live.

## Common Pitfalls

### Pitfall 1: `PRAGMA journal_mode=WAL` ignores busy_timeout on a fresh database
**What goes wrong:** with 10 processes opening a new database at once, 7 of 8 runs had 1–9 workers fail with `OperationalError('database is locked')` at the `journal_mode` statement. The count came out short (1 to 9 instead of 10).
**Why it happens:** changing the journal mode needs an exclusive lock, and that path does not go through the busy handler. `busy_timeout=5000` set before the call does not help. (Verified locally. The SQLite WAL page documents SQLITE_BUSY for last-connection close and recovery [CITED: sqlite.org/wal.html §9]; it does not name the journal-mode switch, so the switch behaviour rests on the local runs.)
**How to avoid:** read first, switch only when needed, retry on `locked`:
```python
def _ensure_wal(conn):
    for _ in range(50):
        if conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal":
            return
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            return
        except sqlite3.OperationalError as e:
            if "locked" not in str(e):
                raise
            time.sleep(random.uniform(0.005, 0.05))
    raise sqlite3.OperationalError("could not switch database to WAL")
```
Verified: 8 of 8 clean runs with 10 processes.
**Warning signs:** `database is locked` only on the first run or in tests that create a new file; passing tests that pre-create the database.

### Pitfall 2: Unicode folding that NFKC does not do
**What goes wrong:** D-01 lists `’ ‘ “ ” « » ` ´` as things to fold, but NFKC leaves U+2019, U+02BC, and most dashes as non-ASCII, and turns U+00B4 into a space plus combining mark. Result: `Book’s` and `Book's` become different keys.
**Why it happens:** NFKC is a compatibility normalisation, not a "make it ASCII" normalisation (verified for each code point).
**How to avoid:** the explicit map in Pattern 1, step 1, before NFKC. Verified outputs: `“Book’s”` → `book`; `´run` → `run`; `run\u00A0out` → `run out`; `co\u00ADoperate` keeps the soft hyphen unless Cf is dropped.
**Warning signs:** two rows for the same word that differ only by apostrophe glyph.

### Pitfall 3: Possessive strip is not idempotent
**What goes wrong:** `book's's` → `book's` on the first call, `book` on the second. Breaks DATA-02 "one word, one key" and the invariant `normalize(normalize(x)) == normalize(x)`.
**How to avoid:** strip `'s` and edges to a fixed point (Pattern 1, step 6; §Code Examples 1). Fuzz test: 20,000 random strings from a noisy alphabet, 0 violations after the fix (found 15 before).

### Pitfall 4: Concurrent-write tests that prove nothing
**What goes wrong:** a test that pre-creates the database and then starts 10 writers passes even when the fresh-database path is broken (Pitfall 1).
**How to avoid:** run both variants, pre-created and fresh, and assert zero worker errors plus returned counts exactly `{1..10}` (`sorted(counts) == list(range(1, 11))`). Returned counts are stronger than the final count, because they prove each increment was seen once.
**Warning signs:** the test asserts only the final count.

### Pitfall 5: Spawn-start worker targets on Windows
**What goes wrong:** `multiprocessing` on Windows uses `spawn`, which re-imports the module that defines the worker. Lambdas, nested functions, or a test module with no `__main__` guard break or re-run tests in children.
**How to avoid:** put the worker in an importable module (verified: `tests/_workers.py` re-exporting `lookup/store_probe.child`), use `mp.get_context("spawn")` explicitly, and guard any script entry with `if __name__ == "__main__":`. Verified under `python -m unittest` on 3.14.3 and 3.12.
**Warning signs:** children print the test output again, or `AttributeError: Can't pickle local object`.

### Pitfall 6: Windows will not delete a database with an open connection
**What goes wrong:** `TemporaryDirectory.cleanup()` raised `PermissionError [WinError 32]` while a WAL connection was open (verified). On 3.12, the same scenario raised a different OSError (`NotADirectoryError`), so the failure looks different across versions.
**How to avoid:** close every connection before cleanup, and use `TemporaryDirectory(ignore_cleanup_errors=True)` (Python 3.10+, verified present) as a backstop.

### Pitfall 7: Contractions collapse under the possessive rule
**What goes wrong:** D-01's `'s` strip maps `it's` → `it`, `let's` → `let`, `that's` → `that`, `there's` → `there`. The user's lookup of "it's" (meaning "it is") lands on the entry for "it".
**Why it happens:** `'s` is both possessive and contraction; the string alone cannot tell them apart.
**How to avoid:** this is a locked-decision question, not a research fix. Surface it for confirmation (Open Question 1). Do not silently add an exception list.

### Pitfall 8: Digits at token edges
**What goes wrong:** D-01 strips digits at the edges, so `mp3` → `mp` and `4k` → `k` (rejected, too short). Digits inside a token are rejected, so `l00k5` → `None` (the trailing 5 is stripped first, then the internal `00` rejects the token), while `look5` → `look`.
**How to avoid:** a decision for the planner (Open Question 2). The literal D-01 behaviour is implemented.

## Code Examples

### 1. Normalisation reference implementation (verified)
```python
# lookup/normalize.py  -- stdlib only
import unicodedata as ud

# Explicit maps run BEFORE NFKC: NFKC does not fold these to ASCII
# (U+2019, U+02BC stay; U+00B4 becomes " \u0301").
_APOS = dict.fromkeys(map(ord, "\u2018\u2019\u201A\u201B\u02BC\u2032\u00B4\u0060"), "'")
_DQUO = dict.fromkeys(map(ord, "\u201C\u201D\u201E\u201F\u00AB\u00BB\u2033\u2039\u203A\""), '"')
_DASH = dict.fromkeys(map(ord, "\u2010\u2011\u2012\u2013\u2014\u2212"), "-")
_INNER_OK = frozenset("'-")


def _strip_edges(w: str) -> str:
    i, j = 0, len(w)
    while i < j and not w[i].isalpha():
        i += 1
    while j > i and not w[j - 1].isalpha():
        j -= 1
    return w[i:j]


def normalize(text: str) -> str | None:
    """Return the counting key for a word or 1-N word phrase, or None to reject."""
    if not isinstance(text, str):
        raise TypeError("text must be str")
    t = text.translate(_APOS).translate(_DQUO).translate(_DASH)
    t = ud.normalize("NFKC", t)                              # ligatures, fullwidth, nbsp, Kelvin
    t = "".join(c for c in t if ud.category(c) != "Cf")      # soft hyphen, ZWSP, BOM
    t = ud.normalize("NFC", t.casefold())
    t = "".join(c for c in t if ud.category(c) != "Mn")      # stray combining marks
    out = []
    for raw in t.split():
        w, prev = _strip_edges(raw), None
        while w != prev:                                     # fixed point -> idempotent
            prev = w
            if w.endswith("'s") and len(w) > 2:
                w = w[:-2]
            w = _strip_edges(w)
        if not w:
            return None
        for c in w:
            if c in _INNER_OK:
                continue
            if not c.isalpha():                              # digit or punctuation inside token
                return None
            if not ud.name(c, "").startswith("LATIN"):       # Cyrillic, mixed script, CJK
                return None
        out.append(w)
    key = " ".join(out)
    if len(key) < 2 and key not in ("a", "i"):              # also rejects the empty key
        return None
    return key
```
**Verified results** (Python 3.14.3): `Running`→`running`; `run,`→`run`; `“Book’s”`→`book`; `Apple`→`apple`; `dogs'`→`dogs`; `don't`, `o'clock`, `well-known`, `co-operate` unchanged; `word-`→`word`; `(running)`→`running`; `It's`→`it`; `I`→`i`; `a`→`a`; `x`, `1234`, `привет`, `hello мир`, `""`, `"   "`, `"..."` → `None`; `  Break   OUT, `→`break out`; `«run»`→`run`; `Straße`→`strasse`; `ﬁnd`→`find`; Kelvin `K`→`kelvin`; `run\u00ADning`→`running`; `´run`→`run`; `run\u200B`→`run`; `mp3`→`mp`; `İstanbul`→`istanbul`. Random fuzz (20,000 inputs, seeded): 0 idempotence violations.

### 2. Counter upsert (verified; SQLite 3.50.4 and 3.42.0)
```sql
INSERT INTO words (word, translation, context, first_seen, last_seen)
VALUES (?, NULLIF(?, ''), NULLIF(?, ''), ?, ?)
ON CONFLICT(word) DO UPDATE SET
  count       = words.count + 1,
  last_seen   = excluded.last_seen,                                  -- first_seen untouched
  translation = COALESCE(NULLIF(excluded.translation, ''), words.translation),
  context     = COALESCE(NULLIF(excluded.context, ''), words.context)
RETURNING count;
```
Verified sequence: first save → 1; second save with empty context and translation → 2 (old values kept); third save with new context and `None` translation → 3. Final row: `first_seen=100, last_seen=300, count=3`, context is the last non-empty value.

### 3. Connection and migration skeleton (pieces verified; assembled version not run as one unit)
```python
# lookup/store.py (sketch)
import os, sqlite3, time, random
from pathlib import Path

class SchemaTooNewError(RuntimeError): ...
class MigrationError(RuntimeError): ...

def _v1(conn):
    conn.execute("""CREATE TABLE words (
        word TEXT PRIMARY KEY, translation TEXT, context TEXT,
        count INTEGER NOT NULL DEFAULT 1,
        first_seen INTEGER NOT NULL, last_seen INTEGER NOT NULL, lemma TEXT)""")

MIGRATIONS = (_v1,)          # CURRENT_VERSION = len(MIGRATIONS)

def _backup(conn, path: Path, old: int):
    bak = path.with_name(f"{path.name}.bak-v{old}")
    tmp = path.with_name(f"{path.name}.bak-v{old}.tmp")
    dst = sqlite3.connect(tmp)
    try:
        conn.backup(dst)                     # consistent snapshot incl. -wal content
    finally:
        dst.close()
    os.replace(tmp, bak)

def open_store(path: Path, migrations=MIGRATIONS, timeout=5.0):
    if sqlite3.sqlite_version_info < (3, 35, 0):
        raise RuntimeError("SQLite >= 3.35 required (RETURNING)")
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=timeout, isolation_level=None)
    conn.execute(f"PRAGMA busy_timeout={int(timeout * 1000)}")
    target = len(migrations)
    v = conn.execute("PRAGMA user_version").fetchone()[0]
    if v > target:                            # refuse before any write
        conn.close()
        raise SchemaTooNewError(f"база версии {v}, код знает до {target}")
    _ensure_wal(conn)                         # defined in Pitfall 1
    if 0 < v < target:
        _backup(conn, path, v)
    conn.execute("BEGIN IMMEDIATE")
    try:
        v = conn.execute("PRAGMA user_version").fetchone()[0]   # re-check under lock
        for step in migrations[v:]:
            step(conn)
        if v < target:
            conn.execute(f"PRAGMA user_version = {int(target)}")
        conn.execute("COMMIT")
    except BaseException as e:
        conn.execute("ROLLBACK")
        conn.close()
        raise MigrationError(str(e)) from e
    conn.execute("PRAGMA synchronous=NORMAL")  # see Open Question 6
    return conn
```
Notes: the version check (step 2) precedes `_ensure_wal` because WAL switching changes the file header; refusing after switching would modify a rejected file. `_backup` runs before `BEGIN IMMEDIATE`, so the backup is a snapshot of the pre-migration state; a second process racing here writes the same bytes, and `os.replace` makes the final move atomic. `f"PRAGMA user_version = {int(target)}"` uses an int computed from the tuple length, never user input.

### 4. Spawn-based concurrency test (verified on 3.14.3 and 3.12)
```python
# tests/_workers.py
from lookup.store_probe import child  # importable top-level target; re-export for spawn

# tests/test_concurrency.py (excerpt)
ctx = mp.get_context("spawn")
barrier = ctx.Barrier(10)
q = ctx.Queue()
procs = [ctx.Process(target=_workers.child, args=(path, barrier, q, i)) for i in range(10)]
for p in procs: p.start()
results = [q.get(timeout=60) for _ in range(10)]
for p in procs: p.join(30)
assert all(r[0] == "ok" for r in results), results
assert sorted(r[1] for r in results) == list(range(1, 11))
```
The verification probe used a reduced table (`w(word, n)`) with the same UPSERT-with-`RETURNING` shape; the fresh-database probe used `words(word, first_seen, last_seen)` with the WAL-retry open from Pitfall 1. The planner's test should use the real `words` table and `open_store`, since that combination is not yet run as one unit.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `SELECT` then `INSERT`/`UPDATE` for counters | `INSERT ... ON CONFLICT DO UPDATE ... RETURNING` | UPSERT in SQLite 3.24; RETURNING 3.35.0 [CITED: sqlite.org/lang_returning.html] | One statement, atomic, returns the new count |
| `autocommit`-less `isolation_level` juggling | `autocommit` attribute (Python 3.12+) | Python 3.12 | Not used here: `isolation_level=None` is portable to 3.10+ and works with explicit `BEGIN IMMEDIATE` (Python `autocommit=False` blocks it, verified) |
| `datetime` objects passed straight to `sqlite3` | Store integers | Python 3.12 deprecated default datetime adapters [ASSUMED: training knowledge] | Store epoch ints (D-13); no adapters needed |

**Deprecated/outdated:**
- `pytesseract`/`Pillow` are out of scope for this phase; nothing here needs them.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The Arch target's system SQLite is ≥ 3.35.0 | Standard Stack | `RETURNING` fails at runtime; the store's version check catches it with a clear error |
| A2 | UPSERT itself requires SQLite ≥ 3.24 | Standard Stack | Irrelevant, since the 3.35 floor already covers it |
| A3 | Windows Defender or other AV can briefly lock a `.db` file and make tests flaky | Pitfalls / Validation | Test flake; re-run or add a retry on `PermissionError` in test teardown only |
| A4 | `os.replace` is atomic and overwrites an existing backup on Windows and POSIX | Code Examples 3 | Backup write not atomic; low impact, since the target is a backup file |
| A5 | Python 3.14.8 (Arch) behaves like 3.14.3 (verified locally) for these APIs | Environment Availability | Minor-version drift; the test suite is the guard |
| A6 | Default `datetime` adapter deprecation in 3.12 | State of the Art | None; the store uses integers |
| A7 | Contraction collapse (`it's`→`it`) is acceptable to the user | Pitfall 7 | Wrong dictionary entry for contractions; RESOLVED by D-16 (exceptions kept) |
| A8 | Digit-edge stripping (`mp3`→`mp`) is acceptable | Pitfall 8 | Junk two-letter keys; RESOLVED by D-17 (digits rejected) |

**If this table is empty:** it is not. A1, A3, A4, A5, A6 are low-impact and do not need user confirmation. A7 and A8 are resolved by D-16 and D-17.

## Open Questions (RESOLVED)

1. **Contraction exceptions (`it's`, `let's`, `that's`, `there's`, `he's`, `she's`, `what's`, `who's`, `here's`, `where's`, `how's`).**
   - What we know: D-01 strips `'s` unconditionally; the output is `it`, `let`, etc. (verified).
   - What's unclear: whether the user wants these to be looked up as the full contraction.
   - Recommendation: keep the literal D-01 behaviour for Phase 1 and ask the user. If they want exceptions, a small frozenset checked before the possessive strip is a one-line change; it is not a schema change.
   - **RESOLVED:** D-16 — keep the listed contractions as-is via an exception set; strip other `'s` to a fixed point.

2. **Digits in tokens.**
   - What we know: D-01 strips edge digits (`mp3`→`mp`); internal digits are rejected (`l00k` → None).
   - What's unclear: whether a token containing any digit should be rejected outright (OCR noise guard; PITFALLS.md §Security Mistakes already says "skip long/mixed-digit tokens").
   - Recommendation: reject any token containing a digit. It is safer for the network guard in Phase 2 and avoids `mp`-style keys. This changes D-01's literal edge-strip; confirm with the user first.
   - **RESOLVED:** D-17 — reject any token containing a digit (checked before edge stripping).

3. **Diacritics in Latin words (`café`, `naïve`, `résumé`).**
   - What we know: D-01 says `→ ASCII`, which can be read as "make the key ASCII" or as "fold the quote characters to ASCII". The implementation above keeps Latin diacritics (`café` stays `café`) and strips only stray combining marks.
   - What's unclear: the intent of D-01's "ASCII" step.
   - Recommendation: keep diacritics. Stripping them merges distinct entries (`resume`/`résumé`) and the dictionary keys in Phase 2 will carry them. Confirm the reading.
   - **RESOLVED:** D-18 — keep diacritics; "→ ASCII" applies only to quotes/apostrophes/dashes.

4. **Display form of the word.**
   - What we know: the key is lowercase (D-03). PITFALLS says to store the original form for display. D-03 does not say to store it.
   - What's unclear: whether the popup shows `apple` or `Apple`.
   - Recommendation: do not add a display column in Phase 1 (not required by any criterion). Phase 5 can add a nullable `display` column through migration v2, which is what the migration mechanism is for.
   - **RESOLVED (deferred):** no display column in Phase 1; Phase 5 adds it via migration if the popup needs it.

5. **Is `lemma` in schema v1 or a v2 migration?**
   - What we know: D-06 says the column is in the schema beforehand. Success criterion 4 requires that an old-version database opens under the new code without losing words.
   - What's unclear: with no shipped v1 database yet, a real v1→v2 path does not exist until a later release.
   - Recommendation (ponytail-minimal): put `lemma` in v1 (literal D-06). Prove the migration path with a test that injects a synthetic second step (`ALTER TABLE words ADD COLUMN probe TEXT`) on top of a v1 fixture database. Option B, placing `lemma` in a v2 `ALTER`, also works and exercises a real migration; choose one and state it in the plan.
   - **RESOLVED:** D-19 — `lemma` in v1; migration path proven by a synthetic v1→v2 test step.

6. **`PRAGMA synchronous`: `NORMAL` or `FULL`.**
   - What we know: in WAL mode, `NORMAL` keeps transactions consistent and durable across application crashes, but a committed transaction can roll back after a power loss or system crash (verified from the official docs).
   - Recommendation: `NORMAL`. A lost last-second counter increment on power loss is acceptable, and it keeps the hotkey path fast. Confirm if the user cares.
   - **RESOLVED:** D-19 — `synchronous=NORMAL`.

7. **Translation-failure write policy: conflicting research.**
   - What we know: SUMMARY.md says to save the word with a NULL translation on failure. FEATURES.md and PITFALLS.md say do not insert or increment on failure.
   - What's unclear: which is right.
   - Recommendation: not a Phase 1 decision. The store must accept `translation=None` and keep the old value (D-10), which supports both policies. Settle it in Phase 2 with the user.
   - **RESOLVED (deferred):** Phase 2 decides; the Phase 1 store accepts `translation=None` and keeps the old value (D-10).

8. **Context length cap.**
   - What we know: D-07 stores the last non-empty recognised line; nothing caps its length. Long OCR output could bloat rows.
   - Recommendation: the store truncates `context` to a fixed cap (e.g., 500 characters) and the planner picks the number. This is a store-level guard, not a normalisation rule.
   - **RESOLVED:** D-19 — context truncated to 500 characters at write.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.14 (Windows dev) | All code and tests | ✓ | 3.14.3 (`C:\Python314`), 3.14.7 (`py -3.14`) | — |
| Python 3.12 (Windows dev) | Compatibility check of tests | ✓ | 3.12 (`C:\Users\Denis\AppData\Local\Programs\Python\Python312`) | — |
| SQLite (via Python `sqlite3`) | Storage | ✓ | 3.50.4 (3.14), 3.42.0 (3.12) | — |
| Python 3.14 on Arch | Target runtime | not tested this phase | 3.14.8 per STACK.md | Verify in VM later |
| SQLite ≥ 3.35 on Arch | `RETURNING` | assumed | system SQLite | Runtime assertion in store |
| Any external package | — | not needed | — | — |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none.

## Validation Architecture

> `workflow.nyquist_validation` is `true` (absent-or-true → enabled).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | stdlib `unittest` (Python 3.14.3; verified also on 3.12) |
| Config file | none needed; discovery from project root |
| Quick run command | `python -m unittest tests.test_normalize tests.test_store tests.test_migrations -v` |
| Full suite command | `python -m unittest -v` |

Verified: a `tests/` package with `__init__.py` is discovered by plain `python -m unittest`, and the spawn worker imports cleanly under it (Windows, 3.14.3 and 3.12).

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-02 / SC1 | `Running`, `run,`, `“Book’s”` → `running`, `run`, `book`; case and edge punctuation | unit | `python -m unittest tests.test_normalize -v` | ❌ Wave 0 |
| DATA-02 | Quotes/apostrophes: `’ ‘ “ ” « » ` ´`, fullwidth, nbsp, soft hyphen, ligatures | unit | same | ❌ Wave 0 |
| DATA-02 | Internal `'` and `-` kept (`don't`, `o'clock`, `well-known`) | unit | same | ❌ Wave 0 |
| DATA-02 | Possessive: `dogs'`→`dogs`, `book's's`→`book`, `'s` alone → None | unit | same | ❌ Wave 0 |
| DATA-02 / D-04 | Rejects: no Latin letters, Cyrillic, mixed `hello мир`, digits-only, length 1 except a/i, empty | unit | same | ❌ Wave 0 |
| DATA-02 / D-05 | Phrases: whitespace collapsed, each word normalised, `  Break   OUT, `→`break out` | unit | same | ❌ Wave 0 |
| DATA-02 | Idempotence: `normalize(normalize(x)) == normalize(x)` on seeded random inputs (20k) | property (stdlib random, fixed seed) | same | ❌ Wave 0 |
| DATA-02 | Non-str input raises `TypeError` | unit | same | ❌ Wave 0 |
| DATA-01 / SC2 | Two saves of one word → one row, `count=2`, translation, context, `first_seen` unchanged, `last_seen` moved | unit (`:memory:` or temp file) | `python -m unittest tests.test_store -v` | ❌ Wave 0 |
| DATA-01 / D-07 | Empty context does not overwrite; `None` translation does not overwrite (D-10) | unit | same | ❌ Wave 0 |
| DATA-01 / D-12 | `RETURNING count` returns the post-update value (1, 2, 3) | unit | same | ❌ Wave 0 |
| Security | Parameter binding: `O'Neil`, `'; DROP TABLE words; --` stored literally, table intact | unit | same | ❌ Wave 0 |
| DATA-01 / SC3 | 10 spawn writers on a pre-created DB: returned counts `1..10`, one row, final 10, zero errors | integration (multiprocess) | `python -m unittest tests.test_concurrency -v` | ❌ Wave 0 |
| DATA-01 / SC3 (regression) | Same, on a **fresh** DB (no pre-create): zero `database is locked` errors | integration (multiprocess) | same | ❌ Wave 0 |
| DATA-01 | A reader SELECT completes while writers run (WAL readers not blocked) | integration | same | ❌ Wave 0 |
| SC4 | File created under a non-existent data dir (`LOOKUP_DB` nested path) | unit | `python -m unittest tests.test_migrations -v` | ❌ Wave 0 |
| SC4 | Reopen keeps existing rows; journal_mode is `wal` | unit | same | ❌ Wave 0 |
| SC4 | Old-version DB (v1 fixture with words) opened under code with a synthetic extra step: words preserved, `user_version` advanced, `*.bak-v1` exists and contains the rows | integration | same | ❌ Wave 0 |
| SC4 / D-14 | DB with `user_version` > code's: `SchemaTooNewError`, file SHA-256 unchanged, no `-wal` created | unit | same | ❌ Wave 0 |
| SC4 / D-14 | Failing migration step rolls back: version unchanged, rows intact, `MigrationError` raised | unit | same | ❌ Wave 0 |
| D-11 | Default path: `LOOKUP_DB` > `XDG_DATA_HOME` (empty or relative ignored) > `~/.local/share` | unit (env patched) | `python -m unittest tests.test_paths -v` | ❌ Wave 0 |
| D-15 | `lookup` package imports with stdlib only (no Qt in `sys.modules`) | unit | `python -m unittest tests.test_core_imports -v` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** the quick run command (under a few seconds).
- **Per wave merge:** full suite `python -m unittest -v`.
- **Phase gate:** full suite green on Windows Python 3.14, plus a run on Python 3.12, before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `lookup/__init__.py` — empty of Qt, no side effects
- [ ] `lookup/normalize.py` — §Code Examples 1
- [ ] `lookup/store.py` — §Code Examples 2 and 3
- [ ] `lookup/store_probe.py` (or `lookup/_workers.py`) — spawn-safe worker target
- [ ] `tests/__init__.py`, `tests/_workers.py` — re-export of the worker
- [ ] `tests/test_normalize.py`, `tests/test_store.py`, `tests/test_migrations.py`, `tests/test_concurrency.py`, `tests/test_paths.py`, `tests/test_core_imports.py`
- [ ] Framework install: none (stdlib)

Every test must set `LOOKUP_DB` (or `XDG_DATA_HOME`) to a temp path in `setUp`, so the suite never writes to the real `~/.local/share/lookup/`.

## Security Domain

> `security_enforcement` is `true` (absent-or-true, ASVS level 1, block on high).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Single-user local app; no login |
| V3 Session Management | no | No sessions |
| V4 Access Control | no | Single user; protection is the file location and its permissions |
| V5 Input Validation | yes | `normalize()` (Latin-only, length, character classes) + parameter binding on every SQL statement |
| V6 Cryptography | no | No encryption at rest; PROJECT.md does not require it (flag if the user wants it) |
| V7 Error Handling and Logging | yes | Errors must not echo context or translation text into logs or exceptions |
| V8 Data Protection | yes | Store only word, short translation, and recognised text; no screenshots; DB under the user data dir |

### Known Threat Patterns for Python + SQLite (local desktop)

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SQL injection through OCR text or a word | Tampering | Only `?` placeholders; no f-string SQL. The one f-string is `user_version = {int}` from a computed int (verified safe) |
| Concurrent writers losing increments | Tampering (integrity) | Single UPSERT with `RETURNING`; WAL + busy_timeout; spawn-based test (SC3) |
| Opening a newer schema and corrupting it | Tampering | Version check before any write; refuse with `SchemaTooNewError` (verified byte-identical) |
| Migration half-applied | Tampering | `BEGIN IMMEDIATE` + `ROLLBACK` on error; backup beside the DB before migrating (verified: backup includes WAL rows) |
| Personal text leaking via logs or exceptions | Information disclosure | No logging of `context` or `translation`; exception messages carry versions and counts only |
| Personal data copy left in a backup file | Information disclosure | Backup gets the same user-only location; mention in README that `.bak-v*` files are copies of the DB |
| `LOOKUP_DB` pointing at a shared path | Tampering | Accept: the user controls their own environment. Do not treat as a threat for a single-user app |
| Phrase/context length abuse (huge rows) | Denial of service (local) | Cap `context` (Open Question 8); cap phrase length at the call site (Phase 2, DATA-03) |

## Sources

### Primary (HIGH confidence)
- Local execution, Python 3.14.3 + SQLite 3.50.4 (`C:\Python314\python.exe`): UPSERT/RETURNING semantics, COALESCE/NULLIF, `user_version` rollback, DDL rollback, `journal_mode` inside transaction, `autocommit=False` + `BEGIN IMMEDIATE`, Unicode folding table, 10-process spawn tests (pre-created and fresh), `Connection.backup` on WAL, newer-DB refusal, Windows cleanup, normalisation fuzz (20,000)
- Local execution, Python 3.12 + SQLite 3.42.0 (`C:\Users\Denis\AppData\Local\Programs\Python\Python312\python.exe`): transaction-control behaviour, cleanup failure mode, `tests/` discovery and spawn workers
- https://www.sqlite.org/lang_returning.html: RETURNING since 3.35.0; all changes occur in the first `sqlite3_step()`; UPSERT RETURNING reports inserted and updated rows
- https://docs.python.org/3/library/sqlite3.html: `autocommit` (added 3.12, default `LEGACY_TRANSACTION_CONTROL`, `False` is recommended PEP 249 mode); `isolation_level=None` means transactions never implicitly opened; `Connection.backup()` added 3.7; `connect(timeout=5.0)`
- https://www.sqlite.org/wal.html: WAL does not work over network filesystems; readers and writers run concurrently; single writer; journal mode is persistent; `SQLITE_BUSY` possible during last-connection close and recovery
- https://www.sqlite.org/pragma.html: `user_version` is header offset 60, unused by SQLite; `synchronous=NORMAL` in WAL is consistent but not durable across power loss

### Secondary (MEDIUM confidence)
- `.planning/research/PITFALLS.md` §Pitfall 9, §Technical Debt, §Integration Gotchas, §Recovery Strategies: SQLite guidance (UPSERT, busy_timeout, WAL, user_version, backup before migration)
- `.planning/research/FEATURES.md` §Normalisation before counting; `.planning/research/ARCHITECTURE.md` §Component Responsibilities, §What Can Be Tested Without a Desktop, §Pattern 5
- `.planning/research/SUMMARY.md` (translation-failure policy; conflicts with FEATURES/PITFALLS, see Open Question 7)

### Tertiary (LOW confidence / ASSUMED)
- Items A1–A8 in the Assumptions Log

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH: stdlib only; behaviour verified on 3.14.3 and 3.12 and against official docs
- Architecture (schema, migrations, counter): HIGH: each piece run locally; the assembled `open_store` sketch is the one piece not executed as a single unit (planner should have the executor run it under the test suite)
- Normalisation rules: HIGH for the Unicode facts (run on `unicodedata`); MEDIUM for the policy choices in Open Questions 1–3
- Pitfalls: HIGH for 1, 3, 5, 6 (reproduced); MEDIUM for 7, 8 (policy)

**Scratch artefacts (not part of the repo):** the experiments and the normalisation prototype are in `C:\Users\Denis\AppData\Local\Temp\claude\D--User-Documents-GitHub-LutQuizApp-LookUpLinux\00328b32-92a9-41ec-8159-ee3768002ede\scratchpad\` (`exp_sql.py`, `exp_uni.py`, `exp_mp.py`, `exp_mp2.py`, `exp_mig.py`, `exp_norm.py`).

**Research date:** 2026-10-24
**Valid until:** 2026-11-23 (30 days; stdlib behaviour is stable. Re-check only if Python or SQLite versions change.)

## Project Constraints (from CLAUDE.md)

- Target runtime: Arch Linux, Python 3. The core (`lookup/normalize.py`, `lookup/store.py`) imports stdlib only: `sqlite3`, `unicodedata`, `re`, `os`, `pathlib`, plus `time`/`random`/`multiprocessing` for store retry and tests.
- Tests must run on the Windows development machine and on Arch: path handling uses `pathlib`; the concurrency test uses `spawn` explicitly.
- Layout is the package `lookup/` with `tests/` run by `python -m unittest` (D-15).
- Privacy: no screenshot is stored; the database is local; only the word, phrase, or sentence goes to the network (later phases). Phase 1 makes no network calls.
- Global CLAUDE.md local-model boundary: no local LLM is used for development work. Not triggered in this phase.
- GSD workflow: repo edits happen through GSD commands (`/gsd-execute-phase` for this phase).
- No project skills are defined (`.claude/skills`, `.agents/skills` absent).

## RESEARCH COMPLETE

**Phase:** 1 - Ядро: база и нормализация
**Confidence:** HIGH (storage and concurrency verified by execution; normalisation verified by execution, policy items flagged)

### Key Findings
- Fresh-database concurrent open fails with `database is locked` at `PRAGMA journal_mode=WAL` even with `busy_timeout`. Read the mode first and retry the switch; 8 of 8 clean runs versus 1 of 8 without it. The test suite must cover the fresh-database path, not only a pre-created file.
- NFKC does not fold `’ ‘ ‚ ʼ ´ ‐ –` to ASCII, and it leaves soft hyphens. The normaliser needs an explicit map before NFKC and a Cf-drop step. Verified reference implementation in §Code Examples 1.
- The possessive strip must run to a fixed point; a single pass is not idempotent (fuzz found it, 0 violations after the fix).
- The counter upsert with `RETURNING count`, COALESCE/NULLIF for empty context and translation, and `first_seen` kept on conflict all verified on SQLite 3.50.4 and 3.42.0. The floor is 3.35.0.
- Migration safety: check `user_version` before touching WAL (refusal leaves the file byte-identical); back up with `Connection.backup()` (a file copy misses WAL rows); `BEGIN IMMEDIATE` with a re-read of the version under the lock.
- Windows: spawn workers must be importable top-level targets; close connections before temp cleanup (`PermissionError [WinError 32]` verified).

### Open Questions (need user or planner decision)
1. Contractions `it's`→`it`, `let's`→`let` (D-01 literal). Keep literal or add an exception list?
2. Reject any token containing a digit (`mp3`→None) or keep edge-digit stripping (`mp3`→`mp`)?
3. Keep Latin diacritics (`café`) or strip them? D-01's "→ ASCII" is ambiguous.
4. Display form (`Apple` vs `apple`): defer to Phase 5 via migration (recommended).
5. `lemma` in schema v1 (recommended, literal D-06) or a v2 migration.
6. `synchronous=NORMAL` (recommended) or `FULL`.
7. Translation-failure policy conflict between SUMMARY.md and FEATURES/PITFALLS: Phase 2.
8. Context length cap value.

### File Created
`D:\User\Documents\GitHub\LutQuizApp\LookUpLinux\.planning\phases\01-core-db-normalize\01-RESEARCH.md`

### Not Done
- Not committed to git. The research workflow's optional commit step was skipped because the instructions say to commit only when asked. Run `/gsd-plan-phase` or commit it manually.
- The research-plan seam (`gsd-tools query research-plan`) was not used. The questions are answered by local execution and official sqlite.org and docs.python.org pages, fetched directly.

### Ready for Planning
Research complete. Planner can create PLAN.md files. Resolve Open Questions 1–3 with the user first, since they change normalisation behaviour.
