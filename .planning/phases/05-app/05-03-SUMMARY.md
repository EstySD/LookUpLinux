---
phase: 05-app
plan: 03
status: complete
completed: 2026-10-27
requirements-completed: [TRIG-02, TRIG-03, CAPT-02, POP-01, POP-02, POP-03, POP-05]
key-files:
  created: [tools/check_app.py, tests/test_check_app.py, .planning/phases/05-app/05-GATE-RESULTS.json, .planning/phases/05-app/05-EXTRA-GATES.json, .planning/phases/05-app/05-VM-RESULTS.md]
  modified: [lookup/app.py, lookup/gui.py, lookup/platform.py, tests/test_app.py, tests/test_app_gui.py, tests/test_platform.py]
---

Completed actual production integration with isolated public fixtures and
physical VirtualBox input. Main23 gates cover warm/cold owner, real primary/OCR,
freshness boundaries, guarded history, pending/latest/dismissal, context-only
updates, failures, native themes/scales, long selection, timeout and native tray
Quit. Supplemental gates cover blank source, physical outside click, actual
mouse-drag primary and offline content surviving provider failure. Every run
requires all five restoration checks; setup-failure/key-release rollback and
acceptance predicates have deterministic regressions.

Review found and fixed clipped late context and an overly broad OCR evidence
predicate. Actual native review additionally found panel overlap at150%; fixed
KWin dock work-area metadata now travels from the worker to card sizing and
placement. Final native bounds checks and independent150% visual confirmation
pass. OCR errors have recognition-specific copy. Native text backgrounds,
unbroken wrapping and stale layout hints were corrected without adding styles
or dependencies. Rendering remains bounded/selectable/plain.

Fresh full regressions:561 tests on Windows3.14.3/3.12.0 and Arch3.14.8, all
subprocess exit0 (7/7/3 existing skips); focused53 pass. Explicit native test
object cleanup fixed a Windows exit access violation that occurred after printed
OK. Security14 controls verified, UI24/24 passed,29 owned images deleted and no
runtime profile retained. See VM-RESULTS for timings, actual source/provider
limits and detailed requirement mapping. This is agent acceptance; independent
phase verification and GSD finalization follow. Phase8 performance acceptance,
real user MDX/DSL and friend/human hardware checks are not claimed.
