---
phase: 14-reliability
status: passed
score: 4/4
verified: 2026-11-03
acceptance: agent
---

# Phase 14 verification

| Requirement | Result | Evidence |
|---|---|---|
| TRAN-07 | PASS | Six actual target context requests through production lookup; google-marked-v2 fallback, cached repetition and independent offline articles. `native-provider.json`. |
| DICT-06 | PASS | Six source-article checks per platform using downloaded real MDX and DSL; unchanged readers, original hashes and receipts retained. `14-01-SUMMARY.md`. |
| CAPT-09 | PASS | Second output, scales 1 and 1.25: pointed river then selected bright, same frame/session; actual KWin popup bounds remain inside monitor. `second-monitor/report.json`. |
| GAME-02 | PASS | Actual borderless Wesnoth word selection and translation from a retained frame; all seven input-return exit cases pass. `borderless/11-native-batch.json`, `borderless-word/11-native-batch.json`. |

Verification command: `python .planning/phases/14-reliability/verify_acceptance.py`.
Compact receipt: `14-ACCEPTANCE.json`, with source hashes, counts, native monitor geometry and cleanup evidence. 28 functional cases passed, zero failed/blocked. Windows/Linux full suites: 868 tests each, zero failures/errors; 11/22 skips. Native tooling's validator: four tests pass.

Limits: owned VirtualBox clone running KDE Wayland, not physical hardware or human acceptance. Public Google clients are undocumented. Reader variant limits and startup performance remain as stated in plan 01. Historical unsuccessful native setup attempts remain separate from final evidence. Full suites for unchanged product/tests and real-dictionary checks for unchanged readers were reused.
