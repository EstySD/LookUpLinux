---
phase: 05-app
status: complete
source: [05-VERIFICATION.md, 05-GATE-RESULTS.json, 05-EXTRA-GATES.json, 05-VM-RESULTS.md]
acceptance_source: agent judgment authorized by explicit --auto instruction
---

# Phase5 acceptance

## Current Test

[testing complete]

## Tests

### 1. Resident owner, physical shortcut and tray exit
expected: Warm trigger reaches one owner, cold trigger starts another, duplicate background launches create no second owner, physical native tray Quit stops it.
result: pass
source: Raw main gates and independent verification; duplicate exit codes0/0, stable warm PID, distinct cold PID, real menu event and services absent after physical Quit.

### 2. Useful card, real history and source freshness
expected: New primary bypasses OCR; unchanged selection uses the exact hovered word; absent/invalid resets freshness; word/phrase count once, sentence never enters word history.
result: pass
source: Main source/boundary/row gates, supplemental actual mouse-drag primary, IPA/source-order/context/count observations; exact repeated mode=ocr/key=word.

### 3. Replacement, dismissal and late context
expected: Escape, native Close, outside click, focus loss and20s inactivity close the card; interaction resets timer; obsolete A and late context never reopen or corrupt history.
result: pass
source: Main delay/latest/context/timer gates, supplemental physical outside click, deterministic barriers and independent53-test exit0 run.

### 4. Errors, persistence and native themes
expected: Blank source and fixed dependency/network/capture/cursor failures have readable states; useful answers survive history/cache/context failures; complete card stays inside actual work area in both native themes at four scales.
result: pass
source:23+4 actual gates; all8 raw geometries inside monitor/frozen work area with zero independent panel overlap; final UI audit24/24, both150% screenshots visually confirmed after correction.

### 5. Regression, security and resource cleanup
expected: Full suites pass with successful process exit; declared threats and operational cleanup are closed; owned settings/processes/shortcut restore and temporary screenshots disappear.
result: pass
source:561-test suites exit0 on Windows3.14/3.12 and Arch3.14; security14 controls, all five restoration flags in both final runs,29 owned PNG files deleted, zero retained runtime profiles; independent verifier10/10.

## Summary

total: 5
passed: 5
issues: 0

## Limits and stopping point

Agent acceptance only; no human/friend hardware testing. One VM monitor;
negative origins use portable tests. Controlled online transport does not accept
Phase8 performance or live-provider speed, and cold engine timing excludes
process startup. Real user MDX/DSL remain for later integration acceptance.
The user explicitly requested stopping after Phase5; Phase6 must remain unstarted.
