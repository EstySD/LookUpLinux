---
phase: 02-offline-dicts-translate
plan: 02
subsystem: dictionaries
tags: [lzo, ripemd128, dictzip, stdlib, unittest, mdx]

requires:
  - phase: 02-offline-dicts-translate
    provides: "plan 01 test sandbox (make_tempdir) used by the dictzip tests"
provides:
  - "lookup.lzo: LZO1X decompress-only codec (decompress, LzoError, MAX_OUT)"
  - "lookup.ripemd128: pure-Python RIPEMD-128 (digest, hexdigest) for MDX Encrypted=2 key info"
  - "lookup.dictzip: DictzipFile random-access reader (read, read_all, close) and DictzipError"
  - "tests/_dictzip_writer.py: make_dictzip() and assemble_dictzip() for the StarDict and DSL test plans"
  - "tests/fixtures/lzo/vectors.json: 14 real liblzo2 2.10 vectors"
affects: [02-04, 02-05, 02-06, 02-10, mdx, stardict, dsl]

tech-stack:
  added: []
  patterns:
    - "Hostile-input codecs: mandatory declared size, capped before any work, every failure is one ValueError subclass"
    - "Fixtures produced by the real C library, committed as JSON (name, algo, raw_len, raw_sha256, comp_b64)"

key-files:
  created:
    - lookup/lzo.py
    - lookup/ripemd128.py
    - lookup/dictzip.py
    - tests/test_lzo.py
    - tests/test_ripemd128.py
    - tests/test_dictzip.py
    - tests/_dictzip_writer.py
    - tests/fixtures/lzo/vectors.json
  modified: []

key-decisions:
  - "ROADMAP research flag answered: MDX LZO and RIPEMD-128 are pure stdlib Python, no python-lzo package, so the Phase 7 PKGBUILD gets no new dependency"
  - "DictzipFile requires every chunk, including the last, to inflate to exactly its expected length (stricter than the plan, which only demanded this for non-final chunks)"

patterns-established:
  - "Codec error classes subclass ValueError; messages carry no input content"
  - "dictzip reader keeps the file handle open between reads for the Phase 5 daemon"

requirements-completed: [TRAN-01]

coverage:
  - id: D1
    description: "lzo.decompress reproduces every committed liblzo2 vector (lzo1x_1 and lzo1x_999) by length and sha256, stdlib only"
    requirement: TRAN-01
    verification:
      - kind: unit
        ref: "tests/test_lzo.py#VectorTests.test_every_vector_roundtrips"
        status: pass
    human_judgment: false
  - id: D2
    description: "Truncated, oversized, trailing-byte and bad-lookbehind LZO input raises LzoError only (T-02-04, T-02-06)"
    requirement: TRAN-01
    verification:
      - kind: unit
        ref: "tests/test_lzo.py#MalformedTests (truncation at every cut length, lookbehind, out_len bounds, trailing bytes)"
        status: pass
    human_judgment: false
  - id: D3
    description: "ripemd128.digest matches the reference suite, a two-block vector, an 80-byte vector and the padding boundaries 55/56/63/64/65"
    requirement: TRAN-01
    verification:
      - kind: unit
        ref: "tests/test_ripemd128.py#Ripemd128Tests.test_vectors"
        status: pass
    human_judgment: false
  - id: D4
    description: "DictzipFile reads any range by inflating only covering chunks; rejects bad ranges, hostile headers, every truncation and chunks that inflate past their declared length (T-02-05, T-02-06)"
    requirement: TRAN-01
    verification:
      - kind: unit
        ref: "tests/test_dictzip.py (ReadTests, MalformedHeaderTests, BombTests)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Reading a real MDX file with LZO blocks"
    requirement: TRAN-01
    verification:
      - kind: manual
        ref: "no real MDX file available; covered by the UAT step planned for the MDX reader (RESEARCH Pitfall 12)"
        status: deferred
    human_judgment: true

duration: 25min
completed: 2026-10-24
status: complete
---

# Phase 2 Plan 02: Leaf codecs (LZO, RIPEMD-128, dictzip) Summary

**Stdlib-only LZO1X decoder verified against real liblzo2 output, a RIPEMD-128 digest checked against the reference vectors, and a bounded random-access dictzip reader, so the MDX and StarDict readers need no extra package.**

## Performance

- **Duration:** ~25 min
- **Completed:** 2026-10-24
- **Tasks:** 3 (each TDD: RED test commit, then GREEN feat commit)
- **Files created:** 8

## Accomplishments

- `lookup/lzo.py`: state-machine LZO1X decoder. `out_len` is mandatory and capped at `MAX_OUT = 64 << 20`; output size is checked before every literal and match copy; lookbehind distance is validated against bytes produced; `IndexError` from short input becomes `LzoError`. Passes all 14 real vectors (7 payloads, both `lzo1x_1` and `lzo1x_999`) and rejects truncation at every cut length of a 60-byte stream.
- `lookup/ripemd128.py`: written from the specification. Matches 13 vectors: empty, the quick-brown-fox string, the official suite, a 56-byte two-block input, an 80-byte input and the padding boundaries 55/56/63/64/65. It passed on the first run.
- `lookup/dictzip.py`: validates the gzip header, the `RA` table (version, chunk length, chunk count against table length), chunk sizes against the file size, and the trailer ISIZE against the chunk geometry. Each chunk is inflated with `decompressobj(-15)` and a bound of `chunk_len + 1`.
- `tests/_dictzip_writer.py`: `make_dictzip()` produces a real gzip stream (`gzip.decompress` reads it); `assemble_dictzip()` builds deliberately broken files for the hostile-input tests.

## Task Commits

1. **Task 1 RED: LZO tests and vectors** - `ba6dfdf` (test)
2. **Task 1 GREEN: LZO1X decompressor** - `4a7036f` (feat)
3. **Task 2 RED: RIPEMD-128 tests** - `98362ae` (test)
4. **Task 2 GREEN: RIPEMD-128** - `83586ab` (feat)
5. **Task 3 RED: dictzip tests and writer** - `e05347d` (test)
6. **Task 3 GREEN: dictzip reader** - `e05063f` (feat)

No refactor commits were needed.

## Decisions Made

- No `python-lzo` package: both missing codecs are pure Python, which answers the ROADMAP research flag and keeps the Phase 7 PKGBUILD free of new dependencies.
- The dictzip reader checks the last chunk's length against `size - chunk_len * (chunk_count - 1)` as well, not only non-final chunks. This holds for real files (the trailer ISIZE is the exact total) and closes a short-final-chunk gap.

## Deviations from Plan

### Auto-fixed Issues

None. One test of my own had inconsistent geometry (chunk length 500 against a 515-byte second chunk) and was corrected before commit; the reader was not at fault.

### Plan variations

- The optional extra vector `text_cyr_4k` was not added: `ssh archvm` refused the connection (VM not running), so the step was skipped as the plan allows. The 14 committed vectors cover short, repeated, random and zero-filled payloads in both algorithms; larger Cyrillic text (64 KiB), key-block-like data and 70 KB of random literals were verified earlier by the research prototype but are not committed.
- Extra tests beyond the plan list: truncation at every cut length (LZO and dictzip), runaway literal length, bytearray/memoryview input, unterminated FNAME, single-chunk file, and a check that an unrelated corrupt chunk does not break reads that do not touch it.

## Issues Encountered

None. Full suite: 127 tests OK (2 POSIX-only skipped) on Python 3.14.3; the three new test modules (43 tests) also pass on 3.12.0.

## Known Stubs

None.

## Threat Flags

None. T-02-04, T-02-05 and T-02-06 are mitigated and tested as listed in the plan; T-02-07 (RIPEMD-128 is not a security control) is stated in the module docstring.

## User Setup Required

None.

## Next Phase Readiness

The MDX reader can call `lzo.decompress(block, declared_size)` and `ripemd128.digest(...)`; the StarDict and DSL readers can open `.dict.dz` and `.dsl.dz` with `DictzipFile` and build test files with `make_dictzip`. A real LZO-compressed MDX file has not been seen yet; a user-supplied sample remains a UAT item for the MDX reader plan.

## Self-Check: PASSED

- Files found: `lookup/lzo.py`, `lookup/ripemd128.py`, `lookup/dictzip.py`, `tests/test_lzo.py`, `tests/test_ripemd128.py`, `tests/test_dictzip.py`, `tests/_dictzip_writer.py`, `tests/fixtures/lzo/vectors.json`
- Commits found: `ba6dfdf`, `4a7036f`, `98362ae`, `83586ab`, `e05347d`, `e05063f`
