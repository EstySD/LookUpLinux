---
phase: 02-offline-dicts-translate
plan: 03
subsystem: dictionaries
tags: [config, article-model, html-to-text, json-cache, wordnet, stdlib, unittest]

requires:
  - phase: 02-offline-dicts-translate
    provides: "plan 01 test sandbox (make_tempdir sets LOOKUP_CONFIG and LOOKUP_CACHE)"
provides:
  - "lookup.config: Config, load, config_path, cache_dir (LOOKUP_CONFIG, LOOKUP_CACHE, MAX_CONFIG_BYTES)"
  - "lookup.dicts foundation: Article, SearchResult, DictError, fold_key, clean_text, html_to_text, index_cache_path/load/save"
  - "lookup/data/irregular.txt: 5814 irregular forms (form base [base ...]) from WordNet 3.1 exception lists"
  - "lookup/data/NOTICE-wordnet.txt: Princeton licence text"
  - "tools/gen_irregular.py: reproducible generator for both data files"
affects: [02-04, 02-05, 02-06, 02-07, 02-08, 02-09, readers, search, orchestrator]

tech-stack:
  added: []
  patterns:
    - "Per-key defensive validation of user-editable JSON; damage degrades to defaults, never raises"
    - "On-disk caches are JSON wrappers pinned to path+size+mtime; every mismatch is a silent miss"
    - "Dictionary text leaves the layer as plain text only (control/format chars removed, markup flattened)"

key-files:
  created:
    - lookup/config.py
    - lookup/dicts.py
    - lookup/data/irregular.txt
    - lookup/data/NOTICE-wordnet.txt
    - tools/gen_irregular.py
    - tests/test_config.py
    - tests/test_dicts_base.py
    - tests/test_irregular_data.py
  modified: []

key-decisions:
  - "Cache tag is validated against ^[A-Za-z0-9._-]{1,32}$ so a tag can never escape the index directory"
  - "clean_text maps Unicode Zs spaces (nbsp etc.) to a plain space and U+2028/2029 to newline before collapsing"
  - "Generator keeps self-mapping entries such as 'acer acer' (harmless, matches the source)"

patterns-established:
  - "Cache load/save take the source path and a tag; the payload is any JSON-able value"
  - "html_to_text never raises: parser failure falls back to a regex tag strip, then clean_text"

requirements-completed: [TRAN-01, TRAN-04]

coverage:
  - id: D1
    description: "config.load returns safe defaults for missing, oversized, non-JSON, non-UTF-8 or wrongly typed files and validates dictionaries, online and clients key by key; resolvers create nothing (D-03, T-02-08)"
    requirement: TRAN-01
    verification:
      - kind: unit
        ref: "tests/test_config.py (PathTests, LoadTests)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Article and SearchResult are frozen with the fixed field names and defaults; DictError carries a short reason (D-05, D-28)"
    requirement: TRAN-01
    verification:
      - kind: unit
        ref: "tests/test_dicts_base.py#ArticleTests"
        status: pass
    human_judgment: false
  - id: D3
    description: "fold_key, clean_text and html_to_text produce plain text only and never raise on garbage markup (D-06, T-02-10)"
    requirement: TRAN-01
    verification:
      - kind: unit
        ref: "tests/test_dicts_base.py (FoldKeyTests, CleanTextTests, HtmlToTextTests)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Index cache is JSON, round-trips, and any size/mtime/path/tag/format mismatch, corruption or oversize is a miss; save failure returns False; 0600 file in 0700 dir on POSIX (D-08, T-02-09)"
    requirement: TRAN-01
    verification:
      - kind: unit
        ref: "tests/test_dicts_base.py#IndexCacheTests"
        status: pass
      - kind: manual
        ref: "POSIX mode test is skipped on the Windows dev host; runs in the Arch VM"
        status: deferred
    human_judgment: false
  - id: D5
    description: "irregular.txt has 5814 sorted unique forms including ran/went/men/children/mice/teeth/stopped/running/better, and the notice carries the Princeton licence (D-11, D-32, T-02-11)"
    requirement: TRAN-04
    verification:
      - kind: unit
        ref: "tests/test_irregular_data.py (CommittedDataTests, GeneratorTests)"
        status: pass
    human_judgment: false

duration: 20min
completed: 2026-10-24
status: complete
---

# Phase 2 Plan 03: Config, Article model, safe index cache and irregular forms Summary

**Defensive config.json reader with XDG paths, the shared Article/SearchResult contract with plain-text helpers, a JSON index cache pinned to path+size+mtime, and a WordNet-derived irregular-forms file with its Princeton notice.**

## Performance

- **Duration:** ~20 min
- **Completed:** 2026-10-24
- **Tasks:** 3
- **Files created:** 8

## Accomplishments

- `lookup/config.py`: path resolvers mirror `default_db_path` (env override, absolute-XDG guard, home fallback) and create nothing. `load` reads at most 1 MiB, validates every key independently (dictionary ids 1 to 512 chars without NUL, bool flags, first duplicate wins, `clients` restricted to `^[A-Za-z0-9._-]{1,32}$` because it reaches a request URL).
- `lookup/dicts.py` foundation: frozen `Article` and `SearchResult` (falsy when empty), `DictError.reason`, `fold_key` reusing `_APOS` and `_DASH` from `normalize`, `clean_text` (Cc/Cf/Cs removed, line endings and blank runs tidied, 200 000 char cap at a line boundary), `html_to_text` on `html.parser` with script/style dropped.
- Index cache: JSON wrapper `{format, tag, path, size, mtime_ns, data}`, written via `mkstemp` (0600) plus `os.replace` into a 0700 directory; `load` checks size cap and all five fields (with strict int checks so `True` is not format 1). No pickle or marshal anywhere.
- `tools/gen_irregular.py` run once over the WordNet 3.1 `dict` folder: 5814 forms, sorted, first-seen base order (`better good well`), collocations and non-lowercase entries filtered. The notice is the first 29 lines of `data.noun` with line numbers stripped.

## Task Commits

1. **Task 1: config reader and paths** - `255c962` (feat)
2. **Task 2: Article model, text helpers, index cache** - `75d2dad` (feat)
3. **Task 3: irregular forms data and generator** - `fe02efe` (feat)

Tasks were committed as one implementation-plus-tests commit each rather than separate RED/GREEN commits.

## Decisions Made

- Cache tags are validated, so `index_cache_path` raises `ValueError` for a tag with path characters; save returns False and load returns None for such a tag.
- Non-breaking and other Unicode space separators become plain spaces in `clean_text`, so dictionary text renders uniformly.
- Self-mapping entries from WordNet (`acer acer`) are kept to stay faithful to the source.

## Deviations from Plan

### Auto-fixed Issues

None - plan executed as written. Small additions beyond the listed behaviours: a deep-nesting JSON test (RecursionError is caught in `load`), a deep-nesting HTML test, a missing-`data`-key cache test, and a generator test that a wrong `data.noun` header fails instead of writing a bad notice.

### Plan variations

- RED and GREEN were not split into separate commits for the two TDD tasks (tests and implementation landed together after both were written and run).

## Issues Encountered

None. Full suite: 206 tests OK (3 POSIX-only skipped) on Python 3.14.3; the three new test modules (79 tests) also pass on 3.12.0. `python -S -c "import lookup.config, lookup.dicts"` succeeds and creates nothing on disk.

## Known Stubs

None.

## Threat Flags

None. New surface (config file, cache directory) is exactly what the plan's threat model covers (T-02-08, T-02-09, T-02-10, T-02-11).

## Next Phase Readiness

Readers (02-05, 02-06, 02-07), the search layer (02-08) and the orchestrator (02-09) can build against `Article`, `SearchResult`, `DictError`, `fold_key`, `clean_text`, `html_to_text`, the index cache helpers and `config.load`. Plan 08 reads `irregular.txt` with `Path(__file__).with_name("data")`; the file may have CRLF endings on a Windows checkout, so use `splitlines()` or `split()`.

## Self-Check: PASSED

All eight created files exist; commits 255c962, 75d2dad and fe02efe are in `git log`.
