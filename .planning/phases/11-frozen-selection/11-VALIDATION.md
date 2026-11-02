---
phase: 11
slug: frozen-selection
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-11-02
---

# Phase 11 — Validation Strategy

Planning coverage only; implementation tests and integrated native product acceptance remain pending. Live feasibility research passed on the owned clone and does not replace product verification.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | Existing Python unittest, PyQt6.QtTest and target native fixture/observer |
| Focused command | `python -m unittest tests.test_app tests.test_selection_gui tests.test_app_gui tests.test_settings_gui tests.test_frozen_product -q` |
| Full command | `python -m unittest discover -s tests -q` |
| Availability | Host Python/PyQt6 and owned Arch/KDE clone already available; no new framework/dependency |
| Runtime | Previous full suite 834 tests in about42 seconds; record fresh runtime after implementation |

## Sampling and Wave 0

Add behavior regressions in each implementation task before its source changes. Existing app/app-GUI tests and temporary-store helpers cover worker/generation/history behavior; create tests/test_selection_gui.py for the new native widget and tests/test_frozen_product.py for evidence validation. Run the task's focused command after each edit, then focused/full discovery at the phase gate. Planned feedback target is under60 seconds per automated command; record actual timing, failures and skips.

| Task | Wave | Requirements | Threats | Automated check | Status |
|---|---|---|---|---|---|
| 11-01-1 | 1 | CAPT-08, TRIG-05 | T-11-01, T-11-02 | `python -m unittest tests.test_app -q` | Pending; add scene cases |
| 11-01-2 | 1 | CAPT-08, TRIG-06 | T-11-02, T-11-03 | `python -m unittest tests.test_app tests.test_hotkey_capture -q` | Pending; add lifetime/stale cases |
| 11-02-1 | 2 | CAPT-08, TRIG-05, TRIG-06 | T-11-04, T-11-05, T-11-07 | `python -m unittest tests.test_selection_gui -q` | Wave0 creates file in task |
| 11-02-2 | 2 | CAPT-08, TRIG-05, TRIG-06 | T-11-04, T-11-06, T-11-07 | `python -m unittest tests.test_selection_gui tests.test_app_gui tests.test_settings_gui -q` | Pending; add integration cases |
| 11-03-1 | 3 | CAPT-08, TRIG-05, TRIG-06 | T-11-08, T-11-09, T-11-10 | `python -m unittest tests.test_frozen_product -q` | Wave0 creates file in task |
| 11-03-2 | 3 | CAPT-08, TRIG-05, TRIG-06 | All phase threats | `python -m unittest discover -s tests -q` plus native product report validation | Pending; real product run required |

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
- [ ] New tests executed; counts/failures/skips and fresh runtimes recorded.
- [ ] Integrated native product evidence passes all required behavior and cleanup checks.

`nyquist_compliant: true` describes the plan's coverage. Set wave_0_complete only after the new tests exist and are exercised. No human acceptance or completion is claimed here.
