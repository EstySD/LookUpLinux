---
phase: 09-hotkey-capture
plan: 02
subsystem: capture
tags: [kwin, wayland, native, timing]
requires: [09-01]
provides: [key-event snapshot, cold-start-safe handoff, verified capture budgets]
affects: [10, 11, 14, 15]
tech-stack:
  added: [native KWin plugin, CMake, extra-cmake-modules, Vulkan SDK headers]
  patterns: [input-event snapshot, sealed anonymous memory FD, duplicate activation coalescing]
key-files:
  created: [native/kwin-capture/capture.cpp, native/kwin-capture/CMakeLists.txt, native/kwin-capture/metadata.json, native/kwin-capture/README.md, tests/test_hotkey_capture.py]
  modified: [lookup/app.py, lookup/gui.py, lookup/capture.py, lookup/timing.py, lookup/doctor.py, PKGBUILD, packaging/PKGBUILD.public, packaging/THIRD-PARTY.md, tools/stage_package.py, tools/check_hardening.py, tests/test_app.py, tests/test_app_gui.py, tests/test_package.py]
key-decisions:
  - Capture inside KWin before launching Python; queued recognition cannot recover a replaced scene.
  - Observe the configured shortcut without registering a competing binding.
  - Transfer one bounded five-second frame only to the application bus owner.
  - Coalesce late activations before invalidating the current request.
  - Use input timestamps for cursor history and verify actual device order in stress probes.
requirements-completed: [CAPT-06, CAPT-07, PERF-02]
duration: not aggregated
completed: 2026-11-02
---

# 09-02: Key-time capture implemented and verified

Commit 4623670 fixes the race inside the compositor, including a cold daemon.
Source.freeze consumes the retained frame; it survives resource initialization
and queued older work. Raw bytes are freed before translation and on resource
failure. Duplicate desktop clients do not cancel the latest retained request or
fall through to recapturing a later scene.

All three criteria pass with agent evidence in 09-VERIFICATION.md: 40 successful
real input requests, scale cases, rapid burst, visible popup and combined full
cold/scene/mouse probes. Actual raw capture medians are about 3 ms. Comparable
frozen-event medians improve from 342–350 ms to 181–202 ms; visible useful
resident results improve to 0.87–0.88 s. Full cold useful median is 1.20 s.
No baseline or budget was silently changed.

Host full suite: 828 tests, OK, 11 skipped. Target selected suite: 69 tests, OK.
The real Arch package builds/installs and source/package/workspace inventories
agree. The user's pre-existing OCR changes were tested and preserved outside
this implementation commit.

## Deviations

A timer/queue-only fix could not pass the reproduced temporal cases. A small
KWin module was required, with both package recipes, source staging, attribution,
diagnostics and inventory validation updated. Timestamped pointer history,
duplicate markers and raw-memory lifecycle regressions cover the new boundary.

VirtualBox initially reversed keyboard/mouse delivery. Final stress input uses
real kernel acknowledgement and independent mouse timestamps rather than a
weakened expected result. Historical failed attempts remain in their records.

## Limits and cleanup

Target: KWin 6.8.1/EGL; the native ABI needs a rebuild after KWin updates. No
human acceptance or other-GPU/second-monitor acceptance is claimed. Input ACLs
restored, retained user config unchanged, test hook/environment removed and
owned clone powered off. Original VM was not controlled or entered.
