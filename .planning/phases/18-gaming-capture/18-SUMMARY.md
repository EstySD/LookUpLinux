# Phase 18 Summary: Gaming Mode capture and daemon

**Status:** Complete (capture is VM-tested only; no Steam Deck hardware)
**Completed:** 2026-11-26
**Requirements:** GAME-03, GAME-04

## What changed

- Added `lookup/gaming.py` with bounded gamescope frame capture: it discovers
  same-user gamescope processes, sends SIGUSR2, watches bounded candidate
  directories for a new `gamescope_*.png`, validates the PNG, returns a
  `GamescopeSnapshot`, and unlinks the temporary file immediately.
- Added a bounded PipeWire/GStreamer fallback (`gst-launch-1.0 pipewiresrc`
  → `pngenc` → stdout) for gamescope versions without the signal handler;
  when neither path works it raises `PlatformError('gaming_capture_unavailable')`.
- Gaming diagnostics now report capture readiness from pids or PipeWire,
  without requesting an actual screenshot. The trigger row remains explicitly
  not implemented until Phase 20.
- The headless D-Bus daemon from Phase 16 is reused: Gaming Mode still skips
  tray, KDE lifecycle, shortcut bridge and KWin capture.

## Verification

| Check | Result | Evidence |
|-------|--------|----------|
| Host full pytest suite | 889 passed, 13 skipped, 1737 subtests | `.planning/phases/18-gaming-capture/full-tests-final.log` |
| Shared `arch-kde` VM full unittest suite | 902 passed, 22 skipped | `.planning/phases/18-gaming-capture/vm-tests.log` |
| Fake gamescope SIGUSR2 test | PNG consumed, validated and removed | `tests/test_gaming_capture.py` |
| PipeWire fallback / no-path tests | Bounded fallback and honest failure | `tests/test_gaming_capture.py` |

## Known limitations (honest status)

- No physical Steam Deck: gamescope SIGUSR2 behavior, real screenshot paths and
  focus return are unverified on hardware.
- Phase 18 provides the capture backend and headless daemon; wiring capture into
  the fullscreen selection UI is Phase 19, and the evdev/Steam Input trigger is
  Phase 20.
- The frame is never written to permanent storage; it lives in memory only for
  the duration of one lookup.
