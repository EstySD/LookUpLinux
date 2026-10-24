---
phase: 02-offline-dicts-translate
plan: 05
subsystem: dictionaries
tags: [stardict, mueller, dictzip, stdlib, unittest]
status: complete

requires:
  - phase: 02-offline-dicts-translate
    provides: "plan 02 DictzipFile random-access reader; plan 03 Article, DictError, fold_key, clean_text, html_to_text, MAX_ARTICLE_BYTES"
provides:
  - "lookup.stardict: open_stardict, StarDictDictionary, parse_mueller, MuellerParts, MAX_IDX_BYTES, MAX_IFO_BYTES"
  - "tests._stardict_writer.write_stardict for every StarDict layout, including Mueller-style index defects"
affects: [02-06, 02-07, 02-08, 02-09, translate orchestrator, base-form search]

tech-stack:
  added: []
  patterns:
    - "Dictionary contract: name, fmt, path, entry_count, skipped_entries, lookup(key), has(key), close(); keys are pre-folded"
    - "Index entries validated one by one; invalid ones become None slots so .syn entry numbers still count them"
    - "parse_mueller is pure and bounded: 20000-char scan window, 600-char pointer window, no nested unbounded quantifiers"

key-files:
  created:
    - lookup/stardict.py
    - tests/_stardict_writer.py
    - tests/test_stardict.py
  modified: []

key-decisions:
  - "extra_idx records in write_stardict are appended after the normal entries; a leading bad entry is built with an empty-headword item in entries"
  - "Entries whose headword folds to an empty key are skipped and counted like empty headwords"
  - "POS tokens directly after an opening parenthesis (usage notes such as '(_comp. от good 1)') are not parts of speech; _II style homograph markers with their transcription end the previous segment"
  - "pointer_only is false when the article is longer than the scan window or the entry has more than one field"

patterns-established:
  - "Fallback for a malformed field layout is the whole entry decoded as UTF-8 with replacement, never an exception"
  - "lookup() swallows read failures per entry (OSError, ValueError, DictzipError) and returns the remaining articles"

requirements-completed: [TRAN-01, TRAN-04]

duration: 30min
completed: 2026-10-24
---

# Phase 2 Plan 05: StarDict Reader and Mueller Parser Summary

**StarDict reader with per-entry index validation, random-access dictzip data and a bounded Mueller parser that exposes transcription, parts of speech and "от X" pointer flags.**

## Performance

- **Duration:** about 30 min
- **Tasks:** 2 (both TDD, RED then GREEN commits)
- **Files:** 3 created

## Accomplishments

- `open_stardict(ifo)` opens `.idx`/`.idx.gz` with `.dict` (preferred) or `.dict.dz`, optional `.syn`, 32 and 64-bit offsets (64 only with version 3.0.0). Every index record is checked against the real data length and `MAX_ARTICLE_BYTES`; bad records (empty headword, size 0, out of range, absurd size) are counted in `skipped_entries` and the dictionary still opens. `wordcount` is ignored.
- Index, syn and ifo reads are bounded (`MAX_IDX_BYTES`, `MAX_IFO_BYTES`), a gzip index is capped after decompression. Failures raise `DictError` with the codes `missing_files`, `corrupt`, `unsupported`, `too_large`, `unreadable`; none carries file content.
- Field decoding for m, l, w, t, y, x, h, g, k in both `sametypesequence` layouts and the per-field type-byte layout. Malformed layouts fall back to the whole entry as text.
- `parse_mueller` returns `MuellerParts(transcription, senses, form_of, pointer_only)`. Pure pointers (`ran`, `went`, `men`) are `pointer_only`, mixed articles (`running`, `gone`) carry `form_of` only, and `better`, `worse`, `data`, `news` are not pointers. A 1 MB hostile string parses well under a second.

## Task Commits

1. Task 1 RED: `2e2de8b` test(02-05): add failing StarDict reader, validation and field-type tests
2. Task 1 GREEN: `5186e84` feat(02-05): StarDict reader with validated index, dictzip data and field decoding
3. Task 2 RED: `1a5895a` test(02-05): add failing Mueller parser tests
4. Task 2 GREEN: `482005e` feat(02-05): Mueller article parser for transcription, parts of speech and pointers

## Verification

- `python -m unittest tests.test_stardict` (48 tests) passes on 3.14 and 3.12.
- `python -m unittest discover -s tests -t .` passes: 308 tests, 3 skipped.
- `python -S` import of `lookup.stardict` works (stdlib only); all plan acceptance one-liners pass.

## Deviations from Plan

None - plan executed exactly as written.

Minor additions inside the plan's intent: `write_stardict` gained two optional keywords (`wordcount`, `dz_chunk_len`) because the plan asks for an overridable wordcount; `parse_mueller` caps the result at 64 senses as an extra bound.

## Known Stubs

None.

## Threat Flags

None. Mitigations T-02-18 to T-02-21 are implemented and covered by tests (per-entry validation, bounded reads, bounded regex windows with a timing test, markup always through `html_to_text`).

## Next Phase Readiness

Plans 06 and 07 can follow the same dictionary contract; plan 08 can use `form_of` and `pointer_only` for base-form search. Not yet verified against the real Mueller 7 files (UAT).

## Self-Check: PASSED

- lookup/stardict.py, tests/_stardict_writer.py, tests/test_stardict.py exist.
- Commits 2e2de8b, 5186e84, 1a5895a, 482005e exist in git log.
