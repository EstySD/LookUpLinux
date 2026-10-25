---
phase: 02-offline-dicts-translate
plan: 07
subsystem: dictionaries
tags: [mdx, mdict, lzo, ripemd128, adler32, stdlib, index-cache]

requires:
  - phase: 02-offline-dicts-translate
    provides: "lookup.dicts (Article, DictError, fold_key, html_to_text, index cache), lookup.lzo, lookup.ripemd128"
provides:
  - "lookup.mdx: open_mdx(path) -> MdxDictionary (versions 1.2 and 2.0, zlib/none/LZO, UTF-8/UTF-16/GBK/Big5, Encrypted=2)"
  - "tests/_mdx_writer.py: independent write_mdx() and lzo_literal_stream() for tests"
affects: [02-08, 02-09, 02-11]

tech-stack:
  added: []
  patterns:
    - "Reader and independent test writer written from the same format description, not from each other"
    - "Block decoder raises an internal _BlockError(reason); open converts to DictError, record reads skip the record"
    - "Index cache payload is checked against the live header and file size before it is believed"

key-files:
  created: [lookup/mdx.py, tests/_mdx_writer.py, tests/test_mdx.py]
  modified: []

key-decisions:
  - "Key info failures under Encrypted=2 (bad zlib stream, size mismatch, Adler-32) all report reason checksum, because a damaged ciphertext usually breaks the zlib stream before the Adler-32 can be compared"
  - "Head/tail key lengths in key info are counted in bytes for 8-bit encodings and in 16-bit units for UTF-16 (matches how the reference reader advances); the first and last keys are skipped, not decoded"
  - "entry_count is the number of usable entries; entries with an empty key, a key over 500 characters or an offset outside the record data go to skipped_entries"
  - "Extra safety caps beyond the plan: MAX_ENTRIES = 8,000,000 and MAX_KEY_TOTAL = 512 MiB of decompressed key blocks, so many small blocks cannot add up to a memory bomb"
  - "Header attributes are read with a bounded, word-anchored regular expression; a 500 KB hostile header is parsed in linear time"
  - "MDX >= 3.0 is rejected as unsupported (different layout)"

patterns-established:
  - "Record boundaries come from the sorted unique offsets, never from key order"
  - "@@@LINK= redirects: depth counter plus visited set, first resolvable target entry wins"

requirements-completed: [TRAN-01]

coverage:
  - id: D1
    description: "MDX 1.2 and 2.0 files open on the stdlib and answer lookups across zlib, none and LZO blocks and four encodings"
    requirement: TRAN-01
    verification:
      - kind: unit
        ref: "tests/test_mdx.py#MdxFormatTests"
        status: pass
    human_judgment: false
  - id: D2
    description: "Every Adler-32 is enforced; hostile sizes, counts, offsets and decompression bombs fail safely"
    requirement: TRAN-01
    verification:
      - kind: unit
        ref: "tests/test_mdx.py#MdxHostileInputTests"
        status: pass
    human_judgment: false
  - id: D3
    description: "Encrypted=2 key info is decrypted; registration encryption is reported as encrypted_registration"
    requirement: TRAN-01
    verification:
      - kind: unit
        ref: "tests/test_mdx.py#MdxEncryptionTests"
        status: pass
    human_judgment: false
  - id: D4
    description: "Redirects (3 hops, loops, missing targets) and the validated JSON index cache"
    requirement: TRAN-01
    verification:
      - kind: unit
        ref: "tests/test_mdx.py#MdxRecordTests"
        status: pass
      - kind: unit
        ref: "tests/test_mdx.py#MdxIndexCacheTests"
        status: pass
    human_judgment: false
  - id: D5
    description: "A real third-party MDX file (with real LZO blocks) opens and gives the same text as the original program"
    verification: []
    human_judgment: true
    rationale: "No real MDX file is available; the reader is verified only against an independent writer and real liblzo2 vectors. Queued for the VM UAT in plan 11. An absent file is 'unverified', not 'failed'."

duration: 35min
completed: 2026-10-25
status: complete
---

# Phase 2 Plan 07: MDX Reader Summary

**Stdlib MDX reader for versions 1.2 and 2.0 with zlib, plain and LZO blocks, Encrypted=2 key info, UTF-8/16/GBK/Big5, every Adler-32 verified, bounded sizes, 3-hop redirects and a validated JSON index cache.**

## Performance

- **Duration:** about 35 min
- **Completed:** 2026-10-25
- **Tasks:** 2 (delivered in one commit, see Deviations)
- **Files:** 3 created

## Accomplishments

- `lookup/mdx.py`: `open_mdx(path)` and `MdxDictionary` with the shared contract (`name`, `fmt = "mdx"`, `path`, `entry_count`, `skipped_entries`, `lookup`, `has`, `close`) plus `version` and `encoding`; constants `MAX_MDX_BLOCK`, `MAX_KEY_INFO`, `MAX_HEADER`, `MAX_BLOCKS`, `MAX_LINK_HOPS`, `INDEX_TAG` as specified.
- Block decoding is size-capped (`decompressobj().decompress(data, declared + 1)`, bounded `lzo.decompress`) and verifies the Adler-32 of every header, keyword header, key info, key block and record block. Structural failures are `DictError` (`checksum`, `corrupt`, `unsupported`, `encrypted_registration`, `empty`, `unreadable`); a bad record block skips that record only.
- `tests/_mdx_writer.py`: independent `write_mdx()` for both versions, four encodings, three codecs (including callables), Encrypted=2, optional explicit record offsets, and a `LAYOUT` dict so tests damage one exact field; `lzo_literal_stream()` produces valid literal-only LZO1X streams.
- `tests/test_mdx.py`: 58 tests in `MdxFormatTests`, `MdxEncryptionTests`, `MdxRecordTests`, `MdxIndexCacheTests`, `MdxHostileInputTests`. Real liblzo2 vectors (`run_1000`, both algorithms) are used as a record block.
- The Encrypted=2 key is checked by a decryption written separately in the test from `ripemd128.digest` over the stored checksum bytes plus `95 36 00 00`.

## Timing (generated files, Windows host, Python 3.14)

| File | Cold open | Warm open (cache) |
|------|-----------|-------------------|
| 100,000 identical keys | 0.15 s | 0.085 s |
| 100,000 distinct keys | 0.21 s | 0.13 s |

The D-09 budget is for all dictionaries together; real dictionaries are larger and the VM is slower, so it is measured in plan 11.

## Task Commits

1. **Tasks 1 and 2: writer, reader, tests** - `b47c427` (feat)

## Deviations from Plan

### Process

**1. Two tasks, one commit.** The reader and the writer were written together, so version 1.2, LZO, Encrypted=2, encodings, redirects and the cache landed in the same commit as the core path instead of two. The RED step (failing tests first) was not run separately. Final state satisfies both tasks' acceptance criteria.

### Auto-fixed / added

**2. [Rule 2 - Missing critical functionality] Total key and entry caps.**
- **Issue:** per-block caps alone let a file with up to `MAX_BLOCKS` blocks of 64 MiB each exhaust memory.
- **Fix:** `MAX_ENTRIES` (8,000,000) and `MAX_KEY_TOTAL` (512 MiB), plus a 500 character limit per key (longer keys are skipped and counted).
- **Files:** `lookup/mdx.py`

**3. [Rule 2 - Missing critical functionality] Bounded header regular expression.**
- **Issue:** a naive `(\w+)\s*=\s*"..."` is quadratic on a long header made of word characters.
- **Fix:** word-anchored, bounded pattern; `test_attribute_regex_is_linear_on_hostile_headers` covers it.
- **Files:** `lookup/mdx.py`, `tests/test_mdx.py`

**4. Reason code for a damaged encrypted key info.** The plan test expects `checksum` for a flipped byte in the encrypted key info, but that usually produces a zlib error. All decode failures of an encrypted key info are therefore reported as `checksum`.

**5. Version >= 3.0 is `unsupported`** (not covered by the plan; its layout differs).

## Known Stubs

None.

## Threat Flags

None. All threats of the plan's register (T-02-26 to T-02-30) have a test: caps and bombs (`MdxHostileInputTests`), counts and offsets, checksums (`test_checksum_failures_at_open`), link loops (`MdxRecordTests`), registration encryption (`MdxEncryptionTests`).

## Open Items

- Real-file check (including LZO blocks and Encrypted=2) is a UAT item in plan 11. Until then the LZO block meaning (raw stream after the 8-byte header, no `0xF0` prefix) is an assumption confirmed only by the Adler-32 design, not by a real dictionary.
- `StyleSheet` and `Compact` header options are ignored, as documented in the research.

## Verification

- `python -m unittest tests.test_mdx tests.test_lzo tests.test_ripemd128`: 76 tests OK on Python 3.14 and 3.12.
- Full suite `python -m unittest discover -s tests -t .`: 431 tests OK (3 skipped).
- `python -S -c "import lookup.mdx"` OK (stdlib only).

## Self-Check: PASSED

- lookup/mdx.py, tests/_mdx_writer.py, tests/test_mdx.py exist; commit b47c427 exists.
