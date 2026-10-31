---
phase: 08-vm
plan: 08
subsystem: ocr
tags:
  - bounded-retry
  - tesseract
  - immutable-sources
requires:
  - phase: 08-06
    provides: Same-source PSM6 miss and supported PSM11 recovery evidence
provides:
  - One shared-preparation sparse retry with explicit3s per-process and6s absolute process bounds
  - Real captured-source regressions, independent calibration, and actual returned-selection observation
affects:
  - 08-09
  - 08-07
tech-stack:
  added: []
  patterns:
    - Valid default6 no-selection alone may retry11; errors do not cascade
    - Generation guards suppress stale bounded OCR without claiming process cancellation
key-files:
  created:
    - tests/test_ocr_fallback.py
    - tests/test_ocr_game_sources.py
    - tests/fixtures/ocr-games/manifest.json
    - .planning/phases/08-vm/08-08-target-context-report.json
    - .planning/phases/08-vm/08-08-target-final-focused.json
  modified:
    - lookup/ocr.py
    - tools/calibrate_ocr.py
    - tools/check_games.py
    - tests/test_app.py
    - tests/test_app_gui.py
    - tests/test_check_games.py
key-decisions:
  - Preserve successful default6 exactly and reuse one PNG/Transform for one conditional11 retry
  - Keep calibration passes independent with fallbackFalse
  - Record the original returned Recognition selection instead of independently forcing diagnostic geometry
requirements-completed: []
duration: 27min
completed: 2026-10-31
status: implemented_native_acceptance_pending09
---

# Phase 8 Plan 08: Bounded Sparse OCR Retry Summary

`lookup/ocr.py` now retries valid PSM6 no-selection once using the same prepared pixels. `tests/test_ocr_fallback.py` pins fast-path, deadline, error and timing behavior; actual source and lifecycle checks passed on the owned target.

## Tasks and Commits

| Task | RED | GREEN | Outcome |
| --- | --- | --- | --- |
| Shared bounded retry | 8cb0a35 | f74ede4 | One preparation, at most two sequential children, exact successful6 result |
| Immutable source/calibration | 4935cfc | fec151d | Four exact captures, direct pass comparisons,96 Breeze points and144 context scenes |
| Lifecycle/observer | 1019960 | 5581acb | Held second-pass generation/quit guards and original-return selection provenance |

The retry is generic: no game/word rule, asset replacement, confidence/proximity change, new dependency, network or persistence path. Only a successful valid6 result with no accepted selection reaches11. Explicit11 and fallbackFalse stay single-pass; malformed/oversized output and transport errors retain fixed existing reasons. Each child has at most3s; one absolute6s process deadline begins immediately before the first subprocess. Preparation and bounded parsing/selection are additional work. Timings sum actual OCR and selection durations separately; no3s total or1.5s latency promise is made.

## Actual Validation

- Task1 host focused:54 tests passed,1 unavailable real-OCR skip.
- Task2 host focused:61 passed,4 honest unavailable Tesseract/rendered-fixture skips.
- Task3 host focused:106 passed,0 skipped.
- Target real OCR: all four unchanged captured PNG/point pairs passed the default cascade and independent direct-pass checks. Successful default6 stayed single; three sparse cases used6 then11. Word/box/span checks and identical retry input were observed without replacing child output.
- All four target prepared PNG hashes exactly match the original native references; decoded RGBA pixels and Transform also match the portable manifest.
- Target Breeze:16 actual rendered fixtures, all96 production-default cases passed, including blank/icon negatives, scales/themes/fonts, compound/hyphen and line expectations.
- Target multiline context corpus:144/144 passed, with actual context occurrence/span/completeness, speaker/column and continuation boundaries.
- Final target lifecycle/observer suite:106 passed in4.330s,0 skipped. Its report binds actual hashes of OCR, calibration, observer and lifecycle-test files.
- Held real recognition's second subprocess seam across replace/dismiss/reload/stop preserves stale rejection and one current history count. A real Engine/Qt owner remains event-responsive while quitting waits for the bounded child; no claim that generation invalidation kills Tesseract.
- Independent broader code/security review cleared the implementation and observer provenance before09 native work.

Target source snapshot and receipts are separate from native product acceptance. Initial target61-test run retained one unrelated existing scheduler-sensitive child-deadline assertion:3.195s against its unchanged2s limit. Its isolated retry passed in0.720s; this is not relabeled as an all-green first run. First final106 staging attempt omitted four historical camera PNGs required by an existing regression; the missing-file error remains recorded. After exact files were transferred without changing tests, current106 passed.

## Faithful Observation

The game observer transparently taps the original `recognize_image` return once and serializes its actual selection. New source records bind that returned word/box/context/span; wrong diagnostic origin or mismatched fields are refused. The observer no longer reruns unrelated full-frame11 to infer production geometry. Old failed06 artifacts remain unchanged and unaccepted; this code does not upgrade them.

## Target Lifetime and Limits

One target-only lifetime, controller86247, ran the corpus services serially in a private owned source directory. No package install, game, product hotkey query or original VM action occurred. Every guest operation used pinned SSH2227 and clone DMI assertion; boot/shutdown/restoration remained clone-only. Actual cleanup reports cloneOFF, prior3D/clipboard restored and original user policy respected. Retained profiles and historical06 evidence were preserved.

## Validation Results

Primary receipts:08-08-target-corpus.json (original scheduler failure),08-08-target-context-corpus.json (isolated retry plus144 and prepared hashes),08-08-target-context-report.json (full cases),08-08-target-final-focused.json (final106),08-08-target-missing-evidence-focused.json (staging error),08-08-target-cleanup.json (observed closure).

Full final-revision host/target discovery, new corrected package, affected physical30, same-instance captured routes and changed-path resource/privacy acceptance remain for09/07. GAME-01 and PERF-01 are not marked complete from replay or unit tests.

## Self-Check: PASSED

The six task commits, listed source/fixture files and actual target receipts exist; all four fixture source hashes match their retained original evidence. Native acceptance remains explicitly pending.
