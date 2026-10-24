---
phase: 02-offline-dicts-translate
plan: 04
subsystem: translation
tags: [urllib, google-gtx, mymemory, deadline, fixtures, stdlib, unittest]

requires:
  - phase: 02-offline-dicts-translate
    provides: "plan 01 test helpers (forbid_network); plan 03 client-name rule used for config clients"
provides:
  - "lookup.online: translate_online, TranslateError, OnlineResult, parse_google, parse_mymemory, prepare_text, DEFAULT_CLIENTS, REASONS"
  - "Captured Google (7) and MyMemory (4) response fixtures under tests/fixtures"
affects: [02-09, 02-11, orchestrator, translation cache]

tech-stack:
  added: []
  patterns:
    - "Exceptions carry only a fixed reason code; transport exceptions are converted with raise ... from None"
    - "One wall-clock deadline shared by all attempts; per-attempt timeout is the remaining time (min 0.5 s)"
    - "urlopen is looked up by attribute, _fetch is the module-level test seam"
    - "Cache payloads are untrusted: from_payload validates the whole shape and returns None on mismatch"

key-files:
  created:
    - lookup/online.py
    - tests/test_online.py
    - tests/fixtures/gtx/word_run.json
    - tests/fixtures/gtx/word_ran.json
    - tests/fixtures/gtx/word_books.json
    - tests/fixtures/gtx/word_news.json
    - tests/fixtures/gtx/phrase_breakout.json
    - tests/fixtures/gtx/sentence.json
    - tests/fixtures/gtx/nonword.json
    - tests/fixtures/mymemory/run.json
    - tests/fixtures/mymemory/break_out.json
    - tests/fixtures/mymemory/sentence.json
    - tests/fixtures/mymemory/xyzzyq.json
  modified: []

key-decisions:
  - "A word whose answer has no dictionary block is not_found even though Google returns a transliteration (D-30); phrases and sentences do not need the block"
  - "not_found from any provider, including MyMemory, ends the chain at once; only blocked/bad_response/timeout/no_network are collected and ranked in that order"
  - "Stopping because less than 0.5 s remains records a timeout, but an earlier blocked still wins by priority"
  - "MyMemory fixtures keep only segment, translation and match per match entry; contributor names and e-mails were dropped before commit"

patterns-established:
  - "Provider parsers take (body, kind, text) and raise TranslateError; callers set client with dataclasses.replace"
  - "Chain tests patch online._fetch with a URL-keyed fake; transport tests patch urllib.request.urlopen"

requirements-completed: [TRAN-02, TRAN-05]

coverage:
  - id: D1
    description: "Captured Google responses parse into OnlineResult (main, parts capped at 8x5, transcription, base form, source language) with safe indexing; a word without a dictionary block is not_found, echoes of phrases and sentences are not_found (D-13, D-14, D-30)"
    requirement: TRAN-02
    verification:
      - kind: unit
        ref: "tests/test_online.py#ParseGoogleTests"
        status: pass
    human_judgment: false
  - id: D2
    description: "HTTP 429/403, HTML or Sorry bodies, non-JSON, wrong shapes, oversized body, cross-host redirect and http downgrade each map to exactly one fixed reason (D-14, D-16, T-02-13, T-02-15)"
    requirement: TRAN-05
    verification:
      - kind: unit
        ref: "tests/test_online.py (ParseGoogleTests, FetchTests)"
        status: pass
    human_judgment: false
  - id: D3
    description: "One shared 3 s deadline across all clients and the fallback; per-attempt timeout is the remaining time, at least 0.5 s; no request when less is left (D-16, T-02-14)"
    requirement: TRAN-05
    verification:
      - kind: unit
        ref: "tests/test_online.py#DeadlineTests"
        status: pass
    human_judgment: false
  - id: D4
    description: "Ordered client list, last working client first, no retry of a failed client, invalid client names dropped, not_found ends the chain (D-13, D-14, T-02-17)"
    requirement: TRAN-02
    verification:
      - kind: unit
        ref: "tests/test_online.py#ChainTests"
        status: pass
    human_judgment: false
  - id: D5
    description: "MyMemory is used only for phrases and sentences, sends only q and langpair, a single word never reaches it (D-15, D-31, T-02-16)"
    requirement: TRAN-05
    verification:
      - kind: unit
        ref: "tests/test_online.py (ChainTests.test_mymemory_word_is_not_found_without_transport, test_mymemory_url_carries_no_identity)"
        status: pass
    human_judgment: false
  - id: D6
    description: "TranslateError text is the reason only, __cause__ is None and the query never appears in str or repr (D-26, T-02-12)"
    requirement: TRAN-05
    verification:
      - kind: unit
        ref: "tests/test_online.py#FetchTests.test_error_never_carries_the_query"
        status: pass
    human_judgment: false
  - id: D7
    description: "Real-network behaviour of the clients from the VM (Google gtx blocking since 09.2026) is not exercised by unit tests"
    requirement: TRAN-05
    verification:
      - kind: manual
        ref: "plan 11 VM check runs the same translate_online code path"
        status: deferred
    human_judgment: true

duration: 30min
completed: 2026-10-24
status: complete
---

# Phase 2 Plan 04: Online translation client Summary

**Google translate_a/single over urllib with an ordered client list, MyMemory fallback for phrases and sentences, one shared 3-second deadline, and every failure reduced to one of five fixed reason codes with the query text never leaking.**

## Performance

- **Duration:** ~30 min
- **Completed:** 2026-10-24
- **Tasks:** 2
- **Files created:** 13

## Accomplishments

- `parse_google` reads the array-form answer through a safe-index helper: main translation from segment first elements, transcription from the segment with a null first element, up to 8 parts with up to 5 terms, base form from the first dictionary entry, source language. The `word_ran` fixture yields `побежал` with lemma `run`.
- `parse_mymemory` handles quota, 403/429 (int or string), the MYMEMORY WARNING text, echoes and bad shapes.
- `_fetch` uses default verified TLS, compares scheme and host of the final URL, reads in 16 KiB chunks with a 1 MiB cap and checks the wall clock between chunks, and maps `HTTPError`, `URLError`, timeouts, `HTTPException` and `OSError` to reasons, always with `from None`.
- `translate_online` sanitises client names, puts `first_client` first, never repeats a client, stops when under 0.5 s remain, and ranks collected failures blocked, bad_response, timeout, no_network.
- `OnlineResult.to_payload` and `from_payload` give the translation cache a strictly validated JSON round trip.

## Task Commits

1. **Task 1: fixtures, OnlineResult, parsers** - RED `4cc9b0c` (test), GREEN `58e27c3` (feat)
2. **Task 2: transport, providers, deadline chain** - RED `e629696` (test), GREEN `da05ada` (feat)

## Decisions Made

- Echo detection normalises with whitespace collapse, casefold and trailing `.!?` removal, and applies to MyMemory answers too.
- `OnlineResult.src_lang` is an empty string when Google omits it, so the payload type stays plain `str`.
- A completed response that arrives after the deadline is treated as a timeout (the clock check follows each chunk).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] HTTPError left open**
- **Found during:** Task 2 (ResourceWarning in the test run)
- **Issue:** the `HTTPError` caught in `_fetch` kept its response object open.
- **Fix:** call `e.close()` before mapping the reason.
- **Files modified:** lookup/online.py
- **Commit:** da05ada

None otherwise. Extra tests beyond the listed behaviours: http downgrade, tiny budget makes no request, earlier blocked wins over a timeout stop, long text is cut before sending, garbage-nesting body (`[` x 50000).

## Issues Encountered

None. `tests.test_online` has 54 tests and passes on Python 3.14.3 and 3.12.0 (also with `-W error::ResourceWarning`). Full suite: 260 tests OK, 3 skipped.

## Known Stubs

None.

## Threat Flags

None. The only new network surface is the two hard-coded hosts covered by T-02-12 to T-02-17. One residual note for T-02-13: urllib follows redirects before the host check runs, so a redirect would send the query to the target once before the response is rejected; the plan fixed the "plain urlopen, no private opener" design, so this was left as specified. Both providers are fixed Google and MyMemory hosts over TLS.

## Next Phase Readiness

The orchestrator (plan 09) calls `translate_online(text, kind, clients=cfg.clients, first_client=<last working client>)` and caches `result.to_payload()`. Real-network behaviour and Google gtx availability from the VM are checked in plan 11.

## Self-Check: PASSED

All 13 created files exist; commits 4cc9b0c, 58e27c3, e629696 and da05ada are in `git log`.
