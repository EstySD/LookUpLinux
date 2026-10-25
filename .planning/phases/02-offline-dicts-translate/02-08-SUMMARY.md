---
phase: 02-offline-dicts-translate
plan: 08
subsystem: dictionaries
tags: [discovery, lemma, stardict, dsl, mdx]
requires:
  - phase: 02-offline-dicts-translate
    provides: dictionary readers and WordNet irregular forms
provides:
  - Bounded discovery, configured ordering and per-dictionary failure isolation
  - Exact and dictionary-confirmed base-form search with pointer resolution
affects: [02-10, 02-11]
tech-stack:
  added: []
  patterns: [lazy reader imports, immutable article replacement]
key-files:
  created: [tests/test_dicts.py, tests/test_lemma.py, tests/test_mueller_sample.py]
  modified: [lookup/dicts.py]
key-decisions:
  - Skip file symlinks as well as directory symlinks to prevent discovery escaping its roots.
requirements-completed: [TRAN-01, TRAN-04]
duration: 20min
completed: 2026-10-25
coverage:
  - id: D1
    description: Discovery, ordering and failure isolation
    verification:
      - kind: unit
        ref: python -m unittest tests.test_dicts
        status: pass
    human_judgment: false
  - id: D2
    description: Base-form candidates and pointer resolution
    verification:
      - kind: unit
        ref: python -m unittest tests.test_lemma
        status: pass
      - kind: integration
        ref: LOOKUP_TEST_DICTS=<Mueller directory> python -m unittest tests.test_mueller_sample -v
        status: pass
    human_judgment: false
---

# Phase 2 Plan 08: Dictionary Discovery and Base Forms

Dictionary roots now discover StarDict, DSL and MDX files recursively, apply
configured order and enablement, and expose metadata and stable error reasons.
Dictionary failures are isolated at open and lookup. Limits bound candidates
and depth; hidden files and symlinks are skipped. Readers close idempotently.

Search collects all exact matches, resolves Mueller pointers without recursive
loops or duplicate articles, and preserves mixed articles. Missing exact forms
try the cached WordNet list and ordered suffix rules, accepting only bases
actually present in a dictionary. Phrases use headwords only.

## Verification

- Python 3.14: 255 dictionary/config/reader tests passed in 8.703 s (4 skips).
- Python 3.12: 16 discovery/lemma/sample tests passed in 0.858 s (3 skips).
- Real Mueller 7 on Windows: both sample tests passed in 0.127 s, none skipped;
  46231 entries, one skipped index entry, transcription/POS and base forms verified.
- POSIX symlink behavior awaits plan 11's VM run.

## Deviations

File symlinks are also excluded, tightening the planned no-directory-symlink rule.
An exceptional abort while opening dictionaries closes previously opened readers.

## Next

Plan 09 already has implementation and summary in the working tree; plan 10 is next.
