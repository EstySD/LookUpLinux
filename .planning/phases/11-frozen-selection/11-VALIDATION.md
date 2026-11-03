---
phase: 11
slug: frozen-selection
status: executed
nyquist_compliant: true
wave_0_complete: true
validated: 2026-11-03
acceptance: passed_agent
human_acceptance: not_performed
created: 2026-11-02
---

# Phase 11 — Validation Strategy

Implementation tests and actual native product acceptance passed. Independent goal-backward verification records 9/9 merged truths and all three roadmap criteria in `11-VERIFICATION.md`. This is agent acceptance; no human sign-off is claimed. The planning strategy below is retained as the coverage contract, with execution results recorded here.

## Executed batch results

| Check | Result | Evidence |
|---|---|---|
| Host full discovery | 857 tests, OK, 11 skips, 43.766 s | `11-host-tests.json` |
| Target full discovery | 857 tests, OK, 4 skips, 75.788 s | `11-native-data/evidence/target-tests.json` |
| Final validator tests | 4 tests, OK, zero skips, 0.001 s | `11-timeout-recheck/11-native-batch.json` |
| Evidence CLI | accepted true; root independently executed | `11-product-evidence.json` |
| Source identity | All 30 native and five host evidence SHA-256 values match working tree | Root independent hash check; product inventory and host report |
| Final cleanup | All recorded checks true; owned clone powered off, clipboard restored afterward | `11-root-cleanup.json` |

Full command is listed below; validator command: `python -m unittest tests.test_frozen_product -q`. Evidence command: `python tools/check_frozen_product.py --validate .planning/phases/11-frozen-selection/11-product-evidence.json`.

Acceptance binds to the inventory, including preserved user OCR changes, rather than HEAD alone (report reconciliation HEAD `c2b689d93e6ae57bc4d5d841cde95ef4fb36b865`). Full-suite results were reused after the harness-only timeout collector correction against unchanged production sources. Final target duration exceeds the original under-60-second feedback target and is recorded honestly. New native-widget and validator test files were exercised; Wave 0 is complete.

Actual product fixture session 9 resolved three useful words including captured hover text on one retained frame while source ticks advanced. Pointer count 6 stayed unchanged during layer input and reached 10 after Esc. Native PRIMARY, card save, no-hit/internal focus, 100/125/200% geometry and active-layer foreign-window rejection passed. Fullscreen Wesnoth passed all seven exits; six cases use source PID 2450, affected timeout rerun PID 6456, with no cross-PID comparison. Historical failures are retained separately and not counted as passes.

Completed batch commands, timestamps, guest roots, per-case provenance and results are retained in `11-native-batch.json`, `11-timeout-recheck/11-native-batch.json` and their raw evidence directories/archives. No running validation job remains. Runtime audit confirms restored profiles/binding/scale and no owned probe/game PIDs. Final root cleanup powered off only clone `cf207909-94b5-4b49-8bd8-ccff973c1dc8` before restoring clipboard; original VM not controlled. No private PRIMARY data is reproduced.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | Existing Python unittest, PyQt6.QtTest and target native fixture/observer |
| Focused command | `python -m unittest tests.test_app tests.test_selection_gui tests.test_app_gui tests.test_settings_gui tests.test_frozen_product -q` |
| Full command | `python -m unittest discover -s tests -q` |
| Availability | Host Python/PyQt6 and owned Arch/KDE clone already available; no new framework/dependency |
| Runtime | Final host 857 tests in 43.766 s; target 857 tests in 75.788 s |

## Sampling and Wave 0

Add behavior regressions in each implementation task before its source changes. Existing app/app-GUI tests and temporary-store helpers cover worker/generation/history behavior; create tests/test_selection_gui.py for the new native widget and tests/test_frozen_product.py for evidence validation. Run the task's focused command after each edit, then focused/full discovery at the phase gate. Planned feedback target is under60 seconds per automated command; record actual timing, failures and skips.

| Task | Wave | Requirements | Threats | Automated check | Status |
|---|---|---|---|---|---|
| 11-01-1 | 1 | CAPT-08, TRIG-05 | T-11-01, T-11-02 | `python -m unittest tests.test_app -q` | Passed; included in final discovery |
| 11-01-2 | 1 | CAPT-08, TRIG-06 | T-11-02, T-11-03 | `python -m unittest tests.test_app tests.test_hotkey_capture -q` | Passed; included in final discovery |
| 11-02-1 | 2 | CAPT-08, TRIG-05, TRIG-06 | T-11-04, T-11-05, T-11-07 | `python -m unittest tests.test_selection_gui -q` | Passed; new file exercised |
| 11-02-2 | 2 | CAPT-08, TRIG-05, TRIG-06 | T-11-04, T-11-06, T-11-07 | `python -m unittest tests.test_selection_gui tests.test_app_gui tests.test_settings_gui -q` | Passed; included in final discovery |
| 11-03-1 | 3 | CAPT-08, TRIG-05, TRIG-06 | T-11-08, T-11-09, T-11-10 | `python -m unittest tests.test_frozen_product -q` | Passed; final 4 tests OK |
| 11-03-2 | 3 | CAPT-08, TRIG-05, TRIG-06 | All phase threats | `python -m unittest discover -s tests -q` plus native product report validation | Passed agent acceptance; see recorded evidence |

## Required Native Product Evidence

- Guarded owned clone only: independent disk/MAC/SSH2227; concurrent original arch-kde is explicitly authorized but never controlled or entered.
- Actual physical hotkey consumes Phase9 frame; automatic initial result and at least two later selected words use that frame while source ticks advance.
- Captured real hover text remains selectable; source-side counters do not advance during layer input and do resume after teardown, using the same source PID.
- Actual fullscreen Wesnoth plus fixture checks: Esc, close, repeat hotkey, timeout, injected operational error, external focus and forced product/layer exit. Internal owned-surface focus remains active; no-hit is nonfatal; useful offline results/cards/preferences remain usable.
- Recorded supported scale cases and captured-monitor coordinate mapping. Other games/relative-pointer-lock modes are not generalized from one game; second monitor and borderless remain later-phase requirements.
- Retain source inventory, event/frame/session identities, code versions, screenshots and failures; restore temporary profiles/bindings/environment and stop owned processes. Root coordinates final clone poweroff.

## Sign-Off

- [x] All six tasks have an automated command and continuous feedback coverage.
- [x] Every phase requirement maps to implementation and actual product verification.
- [x] Existing infrastructure and exact new test files are named; no framework setup needed.
- [x] Native compositor proof is separate from offscreen tests and prior research.
- [x] New tests executed; counts/failures/skips and runtimes recorded.
- [x] Integrated native product evidence passes all required behavior and final cleanup checks.

`nyquist_compliant: true` now describes executed coverage, and wave_0_complete records exercised new tests. Agent acceptance passed; no human acceptance is claimed. Underlying application execution continued while its displayed scene was retained. Other games, relative-pointer-lock modes and other compositors remain untested; second-monitor and borderless acceptance remain Phase 14 scope.
