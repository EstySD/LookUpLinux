---
phase: 2
slug: offline-dicts-translate
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-10-24
updated: 2026-10-25
---

# Phase 2 — Validation

All six phase requirements have behavioral tests. Full suite: `python -m
unittest`; feedback sampling: affected modules after a task, full suite after
a wave and before acceptance. No watch flags. Core remains stdlib-only.

## Requirement Coverage

| Requirement | Tests | Result |
|---|---|---|
| TRAN-01 | test_stardict, test_dsl, test_mdx, test_lzo, test_ripemd128, test_dictzip, test_dicts, test_mueller_sample | Covered; real Mueller checked separately |
| TRAN-02 | test_online, test_translate, test_cli | Covered: parsing, fallback, deadline, failure reasons, redirect privacy |
| TRAN-03 | test_translate, test_store, test_migrations | Covered: no-network cache hits, schema v2, eviction and failure rules |
| TRAN-04 | test_lemma, test_dicts, test_mueller_sample | Covered: exact/base forms, pointers, real sample forms |
| TRAN-05 | test_translate | Covered: context thread, cache, timeout, offline/error |
| DATA-03 | test_translate, test_cli | Covered: phrases saved once; sentences/nonwords not saved |
| CLI / privacy / Phase 1 regression | test_cli, test_privacy, test_core_imports, test_concurrency and existing core tests | Covered |

Each listed file is in `tests/` with the `.py` extension. Task verification
commands and requirement IDs remain in the eleven PLAN files.

## Wave 0

- [x] Google and MyMemory JSON fixtures in tests/fixtures.
- [x] Independent LZO vectors and dictzip/StarDict/DSL/MDX fixture writers.
- [x] Writers are separate tests/_stardict_writer.py, _dsl_writer.py,
  _mdx_writer.py, _dictzip_writer.py rather than the proposed _writers.py.
- [x] tests/_support.py pins V1 and forbids both urlopen and custom openers.
- [x] Opt-in real Mueller tests; no dictionary archives committed.

## Fresh Verification — 2026-10-25

| Environment | Command | Result |
|---|---|---|
| Windows Python 3.14 | python -m unittest | 483 tests, 20.652s, OK, 6 skips |
| Windows Python 3.12 | py -3.12 -m unittest | 483 tests, 19.082s, OK, 6 skips |
| Arch Python 3.14.8 | python3 -m unittest | 483 tests, 10.782s, OK, 2 skips |
| Arch real Mueller | LOOKUP_TEST_DICTS=~/.local/share/lookup/dicts python3 -m unittest tests.test_mueller_sample -v | 2 tests, 0.116s, OK, no skips |

VM source bundle: ~/LookUpLinux-gsd-redirect-6a7c; includes working-tree lookup,
tests and tools. The initial bundle omitted tools and failed three generator
tests; corrected before the successful full rerun. Some intentionally
terminated concurrency workers emit SemLock teardown traces; suite result is
OK. Fixed-text live Google gtx probe returned бегать for run.

The new redirect regression exercises real urllib redirect handling for
301/302/303/307/308, cross-host, HTTP downgrade and same-host destinations,
and verifies zero follow-up requests. 61 focused transport/privacy/import
tests also passed.

## External Checks and Limits

Historical VM CLI, provider, proxy and D-09 timings: 02-VM-RESULTS.md. Real
Mueller and Google reachability were additionally rerun after the redirect fix.
Real MDX/DSL files remain unavailable and explicitly unverified under D-34;
carry to Phase 8. Synthetic fixtures cover these formats, including LZO and
Encrypted=2. Human testing is not claimed: agent acceptance is authorized by
the user's explicit --auto instruction.

## Sign-Off

- [x] Requirement coverage and task verify blocks inspected.
- [x] No missing automated fixture/test prerequisites.
- [x] Full suites and real Mueller checks pass.
- [x] Blocking security finding T-02-13 fixed and behaviorally verified.
- [x] Remaining real-file limits recorded without claiming a pass.

Approval: agent acceptance from verification evidence; no user checkpoint.
