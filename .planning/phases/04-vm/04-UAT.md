---
phase: 04-vm
status: complete
source: [04-VERIFICATION.md, 04-GATE-RESULTS.json, 04-VM-RESULTS.md]
acceptance_source: agent judgment authorized by explicit --auto instruction
---

# Phase 4 acceptance

## Current Test

[testing complete]

## Tests

### 1. Real desktop hotkey and one owner
expected: Physical Meta+Shift+D wakes the existing owner; cold trigger creates one new owner; cache registration/relogin and conflict behavior are observed.
result: pass
source: SC1, repeated warm PID 13605 and cold PID 14375; no relogin, unrelated component sees binding occupied

### 2. Monitor capture and real word at four scales
expected: Real cursor maps to captured monitor pixels and recognizes public English text at 100/125/150/200%.
result: pass
source: SC2, all four actual captures recognize english; both backends pass five public-word samples each

### 3. Popup focus, dismissal and tray
expected: KWin confirms pointer-adjacent placement and focus, Escape differs from focus loss, physical tray menu opens and test action fires.
result: pass
source: SC3, target geometry/active UUID plus Qt active, physical Escape, separate deactivate, tray-menu and tray-action events

### 4. Bounded primary, measurements, regression and cleanup
expected: Primary read terminates, stages are measured, no unrelated content is retained and owned settings/processes/shortcut restore.
result: pass
source: SC4; 3.94ms primary offer, 396.7ms median probe/capture/OCR; all four restoration flags true; 528-test suites on three interpreters; 32 independent focused tests; 14/14 security threats closed

## Summary

total: 4
passed: 4
issues: 0

## Limits

One VM monitor only; negative origins are portable tests. No human or friend
hardware testing is claimed. Production translation/card latency belongs to
later phases. Historical Arch canceled-worker teardown traces remain noted.
