---
phase: 02-offline-dicts-translate
plan: 06
subsystem: dictionaries
tags: [dsl, lingvo, dictzip, mmap, stdlib, unittest]
status: complete

requires:
  - phase: 02-offline-dicts-translate
    provides: "plan 02 DictzipFile random-access reader; plan 03 Article, DictError, fold_key, clean_text, index_cache_load/save, MAX_ARTICLE_BYTES"
provides:
  - "lookup.dsl: open_dsl, DslDictionary, expand_headword, MAX_DSL_BYTES, MAX_VARIANTS, INDEX_TAG"
  - "tests._dsl_writer.write_dsl for every DSL encoding, optional dictzip"
affects: [02-07, 02-08, 02-09, translate orchestrator, dictionary discovery]

tech-stack:
  added: []
  patterns:
    - "Same dictionary contract as StarDict: name, fmt, path, entry_count, skipped_entries, lookup(key), has(key), close(); plus index_language and contents_language"
    - "Index entry per headword line (offset, size, first spelling); several keys can point to it; one article counted once in entry_count"
    - "Backslash-protected characters are swapped for private-use sentinels during markup conversion and restored at the end"

key-files:
  created:
    - lookup/dsl.py
    - tests/_dsl_writer.py
    - tests/test_dsl.py
  modified: []

key-decisions:
  - "[!trs] keeps its text (stripped like any unknown tag); only [s] and [video] with their content are dropped, since [!trs] wraps visible text in real DSL files"
  - "[s]/[video] removal is a bounded regex pass (no brackets inside, at most 300 characters), so an unclosed [s] cannot swallow the rest of an article"
  - "Fallback values (no [trn] in the article) come from non-example, non-comment lines under the part of speech active at the end of the line"
  - "Error codes: unreadable (cannot open), corrupt (bad dictzip or failure during the scan), too_large (size cap or MemoryError), empty (no registered articles)"
  - "A cache payload with zero articles or any out-of-range offset, size, key target, encoding or BOM length is treated as a miss and rebuilt"

patterns-established:
  - "UTF-16 line scanning accepts a newline hit only at an even offset from the start of data"
  - "Converter never raises: any internal error falls back to the decoded text with [..] groups removed"

requirements-completed: [TRAN-01]

duration: 50min
completed: 2026-10-25
---

# Phase 2 Plan 06: DSL Reader Summary

**Lingvo DSL reader (.dsl and .dsl.dz in UTF-16 LE/BE or UTF-8, with or without BOM) with a cached byte-offset headword index, capped `{}` expansion, and a markup converter that yields plain text with separate transcription, parts of speech and values.**

## Performance

- **Duration:** about 50 min (including a rate-limit pause)
- **Tasks:** 2 (both TDD, RED then GREEN commits)
- **Files:** 3 created

## Accomplishments

- `open_dsl(path)` detects the encoding from the first bytes (`FF FE`, `FE FF`, `EF BB BF`, `23 00`, `00 23`, else UTF-8). The scanner works on raw bytes in one pass over an mmap (plain) or the single decompressed buffer (dictzip, cold index only). For UTF-16 a newline match is accepted only at an even offset, so characters such as U+0A41 or U+1F600 never split lines or shift offsets.
- Header `#NAME`, `#INDEX_LANGUAGE`, `#CONTENTS_LANGUAGE` are read from inside double quotes; a missing name falls back to the file stem (`x.dsl.dz` gives `x`).
- Consecutive headword lines share one article; blank lines do not end it; a headword with no body is ignored; articles above `MAX_ARTICLE_BYTES` are skipped and counted in `skipped_entries`. Files above `MAX_DSL_BYTES`, empty files and dictionaries with no articles raise `DictError` (`too_large`, `empty`).
- `expand_headword` expands `{...}` optional parts with the plain spelling first, honours backslash escapes, and stops at `MAX_VARIANTS = 32` (T-02-22).
- The index (`folded key -> entry numbers`, entries of offset, size, headword) is cached as JSON through `index_cache_save` and validated on load against the real source size (types, ranges, key targets, encoding, BOM length); anything off rebuilds it (T-02-25). A warm open of a dictzip file does not decompress it.
- Markup converter: `[t]` gives the transcription (first one wins, shown as `[..]` on the first text line), `[p]` starts a part-of-speech group, `[trn]` contents and, without any `[trn]`, plain non-example non-comment lines are the values (80 characters, 5 per group). `[ex]` and `[com]` stay in the text but are never values; `[s]`, `[video]`, `{{..}}` are dropped; `[ref]` and `<<..>>` keep their word; other tags are stripped with their text; `[m]`/`[mN]` start a new line. Everything is a single regex pass plus flags, no recursion.

## Measured timings (not asserted)

Synthetic file from `write_dsl`: 200000 articles, UTF-16 LE, 30.6 MB, on the Windows development host (Python 3.14.3, not the Arch VM):

| Step | Time |
|------|------|
| Cold open (scan, build index, write cache) | 1.43 s |
| Warm open (cache load 0.21 s, validation 0.06 s) | 0.28 s |
| One lookup after open | 0.1 to 0.2 ms |

D-09 targets 0.3 s of warm open for all dictionaries together. A single 200000-article DSL file already uses about 0.28 s of it, almost all of it JSON parsing. Typical English-Russian DSL dictionaries are smaller than this synthetic one, but the real total has to be measured in the VM with the real dictionaries (see Next Phase Readiness).

## Task Commits

1. Task 1 RED: `debd5b2` test: failing scanner, encoding and headword tests
2. Task 1 GREEN: `b56b4b8` feat: DSL scanner with encoding detection, headword groups and cached byte-offset index
3. Task 2 RED: `65eb057` test: failing markup, index cache and hostile input tests
4. Task 2 GREEN: `466ba31` feat: DSL markup converter

## Deviations from Plan

### Judgment calls

**1. [!trs] kept as text.** The plan lists "`[!trs]`-style media" among the content that is dropped with its text. In real DSL files `[!trs]` wraps visible words (it only excludes them from the reverse index), so dropping it would lose article text. It is stripped like any unknown tag instead; `[s]` and `[video]` are dropped as planned. No test depends on the other reading.

**2. Cache test import.** The cache tests import `index_cache_path` from `lookup.dicts` rather than through `lookup.dsl`.

### Auto-fixed Issues

None. During Task 2 an escaping slip in a generated edit (backslash sequences in string literals) produced a syntax error in `lookup/dsl.py` before the Task 2 GREEN commit; it was corrected in the same working copy and never committed.

## Known Stubs

None.

## Threat Flags

None. The new surface (DSL files, cache JSON) is the one covered by T-02-22 to T-02-25, and each is mitigated and tested: variant cap, size caps and timing tests for 1 MB lines and 100000 nested tags, plain-text output through `clean_text`, and cache bounds validation with 11 tampering cases.

## Issues Encountered

- No real DSL file (for example a Lingvo-exported ABBYY dictionary) was available. Encoding detection and markup handling are tested only against files from `write_dsl` and the documented format (assumption A14 stays open for UAT).

## Next Phase Readiness

- Dictionary discovery (next plans) can treat `.dsl` and `.dsl.dz` like StarDict through the common contract.
- Warm open time of all dictionaries together should be measured in the VM; if it exceeds 0.3 s the cache could use a more compact layout (single-entry keys as plain integers, parallel arrays), or dictionaries could be opened lazily by the tray daemon.

## Self-Check: PASSED

- FOUND: lookup/dsl.py, tests/_dsl_writer.py, tests/test_dsl.py
- FOUND commits: debd5b2, b56b4b8, 65eb057, 466ba31
- `python -m unittest tests.test_dsl tests.test_dictzip tests.test_dicts_base tests.test_stardict` passes on Python 3.14 (183 tests) and `py -3.12 -m unittest tests.test_dsl tests.test_dictzip tests.test_dicts_base` passes (135 tests)
- `python -S -c "import lookup.dsl"` exits 0
