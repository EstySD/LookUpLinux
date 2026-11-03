---
phase: 11-frozen-selection
plan: 03
subsystem: native-product-validation
tags: [kde, wayland, retained-frame, input-isolation, evidence]
requires: [11-01, 11-02]
provides: [actual product hover and fullscreen evidence, reproducible batched native runner, strict evidence validation]
affects: [11-verification, 14]
tech-stack:
  added: []
  patterns: [one bounded native batch, affected-case rerun with explicit source PID provenance]
key-files:
  created: [.planning/phases/11-frozen-selection/11-product-evidence.json, .planning/phases/11-frozen-selection/11-VERIFICATION.md, .planning/phases/11-frozen-selection/11-native-batch.json, .planning/phases/11-frozen-selection/11-product-runtime-audit.json]
  modified: [tools/check_frozen_product.py, tests/test_frozen_product.py]
key-decisions:
  - Observe actual gui.run, Source and Engine; never replace the product layer or inject captured frames.
  - Measure delivery inside the same source process before, during and after each exit.
  - Preserve all batch failures, correct the collector, and rerun only affected checks against unchanged product sources.
  - Disable clone clipboard integration before PRIMARY setup and restore its mode only after final poweroff.
requirements-addressed: [CAPT-08, TRIG-05, TRIG-06]
requirements-completed: []
metrics:
  duration: interrupted_across_usage_resets
  tasks: 2
completed: 2026-11-03
target-acceptance: passed_agent
---

# Phase 11 Plan 03: Actual product selection and input-isolation evidence

The real hotkey/Owner/Engine selected three useful words from one retained frame, including a captured tooltip, and isolated input over actual fullscreen Wesnoth. All seven exit paths returned source input with honest per-case process identities.

## Tasks and commits

| Task | Commit | Result |
|---|---|---|
| 1 RED | `4a278d2` | Evidence validator rejects missing or contradictory native claims. |
| 1 GREEN | `bc6bc9c` | Import-safe actual-product observation, public fixture and transparent SDL observer. |
| Task 1 follow-up | `e35b547` | Deterministic complete/affected host batches, clipboard isolation precondition, timer diagnostics, explicit rerun PID registry and strict platform inventory. |
| Task 2 | `1d18a56` | Same-frame fixture, PRIMARY/card behavior, native scale/ownership checks, seven fullscreen exit cases, host/target regressions and audited cleanup. |

## Verification

- Host: 857 tests OK, 11 skips, 43.766 s, executed by the parent on matching production hashes.
- Target: 857 tests OK, 4 skips, 75.788 s.
- Final validator: 4 tests OK, zero skips; actual final report accepted by the CLI.
- Fixture session 9: `bright`, `river`, `captured`, each with an offline translation and unchanged frame/session. Source input 6→6→10 while source ticks continued.
- Fullscreen Wesnoth: Esc, close, repeated hotkey, timeout, fault, external focus and process kill passed. Six initial cases use PID 2450; affected timeout rerun uses PID 6456, with all comparisons staying within that case's PID.
- Native 100/125/200% bounds and selected word agree; foreign-window geometry request is rejected while the actual product layer is visible.

`11-product-evidence.json` links the raw JSON archives, source inventory, source-side counters, regression outputs and runtime cleanup audit. Screenshots were inspected as native product visuals. Historical failed placement screenshots and the failed timeout collector report remain separate.

## Deviations from Plan

### Auto-fixed issues

1. **[Rule 1 — Product bug, corrected by Plan 02]** Native testing found that OR-combined kdotool criteria moved the layer instead of the popup and weakened the ownership query. The parent-authorized GUI/platform fix `a3d0c50` was restaged before accepted evidence; no offset workaround was used.
2. **[Rule 3 — Test environment]** Shared clipboard could repopulate PRIMARY from another agent's host clipboard. Clone integration is disabled and the OCR fixture holds public invalid selection `0`; private baseline is restored while integration remains disabled.
3. **[Rule 1 — Collector bug]** The first timeout collector required terminal OCR output although timeout correctly cancels pending work. The affected runner allows closure, waits for deliberate request boundaries, records configured timer values and uses a 10-second setting. Only timeout and validator checks were rerun; the failed original report is retained.
4. **[Rule 3 — Fresh-run setup]** A fresh affected run needed its owned private directory and Wayland environment, and must not command nonexistent prior child processes. These setup-only failures were preserved and the runner now handles fresh roots explicitly.
5. **[Validation workflow preference]** The final work uses one deterministic batch that collects all cases and continues independent checks after failure, followed by one affected-case batch. No production fix was made between individual cases in a batch.

The popup can cover adjacent text. Physical blank no-hit clicks hide it before selecting another word; these extra actions remain explicit in the evidence. No new UI feature was added to disguise the interaction.

## Preservation and cleanup

No production module was edited by this executor. The user's OCR/OMX changes were retained and not staged. Staging included current OCR bytes, so the report does not claim a clean source revision. No original-VM guest command or input was issued.

The runtime audit confirms owned test processes stopped, profile files and shortcut restored, and live scale returned to 1. The clone remains running for the parent. **Parent final action:** power off the owned clone, then restore its original bidirectional clipboard mode; never re-enable synchronization before shutdown.

## Self-Check: PASSED

Both tasks have actual evidence. The final report passes validation, declared raw files and screenshots exist, and RED/GREEN/tooling commits `4a278d2`, `bc6bc9c`, `e35b547` plus production correction `a3d0c50` are present. Independent phase/requirement completion remains with the parent; no human acceptance or untested platform/game acceptance is claimed.
