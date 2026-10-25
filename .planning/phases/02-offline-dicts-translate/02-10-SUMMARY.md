---
phase: 02-offline-dicts-translate
plan: 10
subsystem: cli
tags: [cli, utf8, privacy, stdlib]
requires:
  - phase: 02-offline-dicts-translate
    provides: DictSet, translation orchestrator, online providers
provides:
  - Word, phrase, sentence, context and dictionary-list commands
  - Package-wide privacy and stdlib import checks
affects: [02-11, 03, 05]
tech-stack:
  added: []
  patterns: [UTF-8 entrypoint, fixed reason messages, AST privacy checks]
key-files:
  created: [lookup/__main__.py, tests/test_cli.py, tests/test_privacy.py]
  modified: [lookup/online.py, tests/test_core_imports.py]
key-decisions:
  - Exercise real urllib boundary in privacy tests so transport exception sanitization is tested.
requirements-completed: [TRAN-01, TRAN-02, TRAN-03, TRAN-04, TRAN-05, DATA-03]
duration: 20min
completed: 2026-10-25
status: complete
coverage:
  - id: D1
    description: CLI rendering, exit codes, cache, contexts and degraded database behavior
    verification:
      - kind: unit
        ref: python -m unittest tests.test_cli
        status: pass
      - kind: integration
        ref: tests.test_cli.CliSubprocessTests.test_utf8_and_stdlib_entrypoint
        status: pass
    human_judgment: false
  - id: D2
    description: Privacy and side-effect-free stdlib-only library imports
    verification:
      - kind: unit
        ref: python -m unittest tests.test_privacy tests.test_core_imports
        status: pass
    human_judgment: false
---

# Phase 2 Plan 10: CLI and Library Gate

The CLI renders every dictionary article, base-form headers, online/cache
answers, context translations and save counts in Russian. It lists dictionary
roots, metadata and skip reasons without opening the database. Errors return
0/1/2 as specified, database failures preserve dictionary answers, stage timing
is optional on stderr, and the module entrypoint explicitly emits UTF-8.

## Verification

- Python 3.14 full suite: 482 tests passed in 20.583 s, 6 skipped.
- Python 3.12 full suite: 482 tests passed in 20.045 s, 6 skipped.
- Focused CLI/privacy/import/online gate: 67 tests passed in 2.017 s.
- Python 3.12 CLI/privacy/import gate: 13 tests passed in 1.924 s.
- `python -S -m lookup --help` exposes all planned flags; subprocess tests
  verify UTF-8 IPA/Cyrillic output and lookup with site packages disabled.

## Defect Fixed

The final online-provider failure raised a sanitized reason without explicitly
suppressing exception context. It now uses `raise ... from None`; behavioral
privacy tests assert suppression and absence of user text in all output/logs.

## Deviations

Transport errors are injected at urllib.request.urlopen, the actual external
boundary, instead of breaking the private _fetch helper's sanitized contract.
Existing plan 09 implementation and summary were preserved, fully tested and
committed so VM verification can use a complete committed archive.

## Next

Ready for plan 11: three-interpreter verification, Mueller and network probes in archvm.
