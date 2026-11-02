---
phase: 09-hotkey-capture
status: gaps_found
verified: 2026-11-02
score: 0/3
verification_kind: agent
---

# Phase 9 verification: temporal correctness blocks advancement

## Result

Phase incomplete. Plan 09-01 has a baseline summary; 09-02 is partially executed and intentionally has no completion summary. No v1.1 requirement has been marked complete. No human acceptance is claimed.

| Criterion | Result | Evidence |
|---|---|---|
| CAPT-06: real hotkey over A then immediate movement returns A | **FAIL — unresolved** | `09-movement-final.json`: frozen point (100,100) is B, while A was (684,376); final error is not_found. |
| CAPT-07: scene changes after hotkey do not replace the original | **FAIL — unresolved** | `09-scene-final.json`: expected bank, actual river after fixture replacement on the kernel chord. |
| PERF-02: comparable capture/result measurements and fixed budgets | Partial; resident experiment passes, full cold path outstanding | 25 baseline + 25 final requests, fixed budgets in `09-BASELINE.md`; full process-absent cold startup not covered. |

## Delivered scoped improvement

`Controller.Trigger` immediately queues an already-hidden popup, removing its unnecessary 75 ms wait. A currently visible popup retains the existing hide delay; the test proves stale delayed callbacks cannot enqueue superseded work. This change does not claim atomic capture, remove previous-translation queueing, or resolve the two failing temporal requirements.

All 50 measured static-scene requests produced optically verified useful offline dictionary results through actual hardware hotkeys. Nearest-rank p95:

| Group | Baseline frozen median / p95 | Final frozen median / p95 | Baseline useful median / p95 | Final useful median / p95 |
|---|---:|---:|---:|---:|
| cold_resident (5 each) | 342.263 / 351.868 | 278.412 / 285.710 | 1053.793 / 1106.957 | 968.354 / 985.463 |
| warm_distinct (20 each) | 350.308 / 362.585 | 286.089 / 311.580 | 1018.511 / 1098.510 | 961.587 / 1056.070 |

Milliseconds. Both groups meet the predeclared resident budgets: frozen median ≤300/p95 ≤330; useful median ≤1100/p95 ≤1200. Raw per-request samples and telemetry are retained in `09-baseline-samples.json` and `09-final-samples.json`.

## Regression evidence

- Host: `python -m unittest discover -s tests` — **816 tests, OK, 11 skipped**, 44.133 s. This includes the user's existing uncommitted OCR changes; those were preserved and are not owned by this change.
- Host focused: `python -m unittest discover -s tests -p test_app_gui.py` — **33 tests, OK**.
- Owned target, same modified gui.py: `QT_QPA_PLATFORM=offscreen python -m unittest tests.test_app_gui` — **33 tests, OK**, 3.663 s. Target log remains beside the isolated source.
- Both plan structures passed `gsd-tools verify plan-structure` with no errors/warnings.

## Why auto cannot advance

The exact first two roadmap success criteria fail on the real target, after the measured speed improvement. Per `workflows/next.md`, safety gate 3 stops routing on unresolved verification FAIL items. They have no override. The small speed improvement must not be represented as completing Phase 9.

The present desktop shortcut launches a Python trigger before the daemon receives Trigger. Source.freeze samples the cursor later and requests a current frame; it has no original key-event snapshot to recover. Faster OCR, an earlier worker, or a timer change alone cannot recover a frame already replaced before dispatch. This is an inference from the real failures and current code, not proof that every KDE implementation is impossible.

The official [KWin scripting API](https://develop.kde.org/docs/plasma/kwin/api/) exposes registerShortcut and cursorPos, suggesting a compositor-side pointer snapshot prototype. The [ScreenShot2 interface](https://raw.githubusercontent.com/KDE/kwin/master/src/plugins/screenshot/org.kde.KWin.ScreenShot2.xml) accepts current capture options and an output FD, with no historical key-event frame selector. Those docs do not prove an atomic frame/cursor route. A native compositor capture or explicitly bounded retained-frame design must be prototyped against these same temporal probes before resuming implementation; do not silently weaken the requirements or install a compositor plugin as an untested timing fix.

## Remaining work for 09-02

1. Establish and prove a compositor-bound trigger/cursor/frame path for immediate movement and scene replacement, including full process-absent cold startup. Current capture design is insufficient.
2. Ensure capture cannot wait behind prior translation or resource initialization; preserve PRIMARY precedence, cancellation and hide-before-capture behavior.
3. Repeat comparable static measurements and both temporal probes, plus full-cold, repeated visible-popup and error paths. Complete the summary and requirements only when the failures are resolved.

Cleanup evidence is tracked separately in `09-cleanup.json`; the owned source/harness/test artifacts remain for reproduction. The original VM was not controlled, stopped or entered.
