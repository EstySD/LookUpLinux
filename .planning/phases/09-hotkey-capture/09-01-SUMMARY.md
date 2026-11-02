---
phase: 09-hotkey-capture
plan: 01
subsystem: capture
tags: [baseline, wayland, timing]
requires: []
provides: [resident-daemon capture baseline, pre-optimization budgets, real temporal failure reproductions]
affects: [09-02]
tech-stack:
  added: []
  patterns: [kernel evdev input timestamps, optical first-useful observer]
key-files:
  created: [.planning/phases/09-hotkey-capture/09-BASELINE.md, .planning/phases/09-hotkey-capture/09-baseline-samples.json, .planning/phases/09-hotkey-capture/09-movement-baseline.json, .planning/phases/09-hotkey-capture/09-scene-baseline.json]
  modified: []
key-decisions:
  - Use isolated current source because installed target package differs.
  - Separate resident cold requests from process-absent cold starts.
  - Fix capture median/p95 budgets at 300/330 ms before optimization.
requirements-completed: []
duration: not aggregated
completed: 2026-11-02
---

# 09-01: Baseline established

Five first requests from restarted daemons and twenty resident requests all produced optically verified dictionary results from actual hotkeys. Raw samples and nearest-rank statistics are retained in 09-BASELINE.md. The two temporal probes fail: pointer movement selects B, and scene replacement selects river instead of bank.

Both PLAN files passed gsd-tools plan-structure validation; existing Engine tests passed 19/19 before runtime edits. No Phase 9 requirement is accepted by this measurement task. Full process-absent cold startup is outside this resident baseline and remains required at phase verification.

Target cleanup is owned by the remaining execution unit: restore saved keyboard ACL and return the clone OFF. Existing installed package/config and original VM guest remain untouched. Failed harness setup and startup observations are retained separately, not counted as measured workload successes.
