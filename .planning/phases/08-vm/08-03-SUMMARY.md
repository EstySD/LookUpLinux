---
phase: 08-vm
plan: 03
subsystem: native-game-validation
tags: [wesnoth, wayland, fullscreen, physical-input, ocr]
requires:
  - phase: 08-02
    provides: Installed timing protocol and guarded clone input
provides:
  - Two distinct actual fullscreen Wesnoth lookup and resumed-gameplay routes
  - Strict correlated game evidence oracle and read-only capture observer
affects: [08-04, 08-05]
tech-stack:
  added: [official Arch wesnoth]
  patterns: [unchanged capture observation, kernel monotonic input, actual useful-frame verification]
key-files:
  created:
    - tools/check_games.py
    - tests/test_check_games.py
    - .planning/phases/08-vm/08-wesnoth-final-report.json
  modified: []
key-decisions:
  - Game acceptance requires two unique physical requests and observable subsequent gameplay.
  - Read-only instrumentation retains exact original capture and query objects.
  - Software SDL and clone-only disabled 3D qualify the tested environment explicitly.
  - One game does not complete GAME-01; captured-mouse acceptance remains plan04.
requirements-completed: []
duration: approximately 5h including quota pauses and driver recovery
completed: 2026-10-30
---

# Phase 8 Plan 03: Actual Fullscreen Wesnoth Summary

**Two physical lookups captured different real tutorial scenes, displayed useful Mueller articles, and returned control for unit movement and combat.**

Implementation: `tools/check_games.py` and `tests/test_check_games.py`.
Task commits: e2c790b (RED), 68d9f6d (GREEN), 92773ed (identity/tap RED), 584c04c (native observation), c298ef9 (punctuation RED), 1ebef6d and 27e323e (canonical-span validation and cleanup).

## Validation Results

`08-wesnoth-final-report.json` recomputes **passed:true, routes:2, game01_complete:false**. This is agent acceptance, not human testing. The independent reviewer inspected source, overlay and gameplay hashes and screenshots. GAME-01 remains open for the second real game with captured mouse in plan04.

| Actual route | Useful-frame upper bound | Returned gameplay |
| --- | --- | --- |
| Welcome tutorial narrative, `movement` | 2420.879482ms | Physical dismissal, hero selection, Konrad moved from keep (9,6) to grass (12,5); movement points 6/6 to 3/6 |
| Changed Attack Enemy combat dialogue, `sword` | 8225.066150ms | Physical dismissal and Attack; actual damage animation and Konrad HP 32/32 to 17/32, followed by NPC response |

Both routes carry distinct kernel CLOCK_MONOTONIC chord events, request identities, cursor/word rectangles, original ScreenShot2 source hashes, actual production OCR/context/span, and optically checked useful overlay frames. Timing ends at capture of the actual useful surface; it includes observation overhead. These game results make **no 1500ms game latency claim**. Dismissal timestamps are post-command observations; gameplay input timestamps are pre-command observation bounds, not kernel latency samples.

The first raw span selects `movement,`; the core canonical normalizer correctly maps it to `movement` while the raw punctuation remains intact. The second context is the two-line combat fragment `Sword\nblade`. The first route contains multiline tutorial narrative. Original Source.freeze/resolve each execute exactly once and their exact returned objects are preserved. The instrumented installed application is identified explicitly; there is no replacement capture, OCR, query, result or game text.

Official Arch extra/wesnoth 1:1.18.8-2 was installed with signature verification. The cached package SHA is recorded in the final report and installation log. Actual running game Version info reported **software (sw), Wayland**, and the observed KWin window was fullscreen at 1280×800. Production remained the installed source from plan02; no production code or game assets changed in this unit.

Fresh checks: 57 focused tests passed with Python exit0. Host discovery: 739 tests passed, 8 platform/opt-in skips, 30.381s. Final target discovery with actual OCR and real system Mueller: **739 tests passed, zero skips, 39.201s, Python exit0**, recorded in `08-wesnoth-target-tests.txt`. Host PowerShell stderr projection includes NativeCommandError/RemoteException decoration around unittest output; the actual log finishes OK. Target forced-deadline multiprocessing tests emit the previously diagnosed SemLock teardown traceback; the retained raw log and actual Python exit distinguish it from assertion failure.

Principal raw evidence: `08-wesnoth-accepted-route1.json`, `08-wesnoth-accepted-route2-combat.json`, their source/overlay PNGs, `08-wesnoth-konrad-selected.png`, `08-wesnoth-konrad-move.png`, `08-wesnoth-route2-before-attack.png`, `08-wesnoth-route2-combat-settled.png`, and `08-wesnoth-route2-combat-control.json`.

## Deviations from Plan

- **[Rule 3 - Environment blocker]** Initial default-renderer black frames and a later 3D-enabled vmwgfx kernel fault froze KWin. Both were rejected, not accepted as game evidence. A bounded guest shutdown stalled; only the guarded owned clone was force-stopped after that failure, then booted with 3D disabled. Actual supported software rendering was verified in the new running game. Kernel log, frozen/black images and rejected metadata remain available. No actor is assigned to the earlier unexplained game termination.
- **[Rule 1 - Evidence bugs]** Tests and reviewer feedback added unique request/input correlation, exact source identities, protected observer error logging, early matching production error detection and faithful core canonical-span validation. Absent, duplicated, stale or invalid evidence cannot pass.
- A textured/translucent HUD target `first` produced no production Query. Its physical attempt, original source and error observations are retained as failure. A clear changed combat scene supplied the second successful route; no production OCR override was introduced. Earlier lookup-only pilot remains incomplete and excluded from final acceptance.

## Cleanup and Limits

The owned transient game service and instrumented lookup exited. Per-process software/XDG environment ended with them. Only the exact known public renderer-report clipboard value was replaced with the previously established public test fixture; PRIMARY remained absent and Klipper history was not cleared. Owned isolated game saves/config and evidence are retained for reproducibility, without editing personal/default game settings. Final machine cleanup is recorded separately in `08-wesnoth-cleanup-final.json`.

The clone is preserved powered off for plan04 after successful guest shutdown. Its prior bidirectional clipboard mode was restored only after poweroff. Its prior enabled 3D setting is deliberately deferred across the two game plans; current 3D-disabled acceptance is explicit. Borderless, exclusive scanout and a second physical output remain unverified. No original VM boot, revert or write was performed. The historical phase07 separate-GUI-run/original-disk preservation exception remains unchanged and is not waived by this unit.

## TDD Gate Compliance

RED e2c790b precedes GREEN 68d9f6d; subsequent adversarial regressions and fixes are committed separately. Nine game tests cover absent real gameplay, stale/menu/fake routes, correlation, observer failures, early errors and canonical span boundaries. No production stubs were introduced.

## Self-Check: PASSED

Both implementation files, strict final report, supporting actual source/overlay/control images and the listed task commits exist. Final report was recomputed with the final oracle; focused checks passed. Parent retains ownership of global state and requirement transitions.
