# Phase 20 Summary: Gaming trigger and autostart

**Status:** Complete (evdev and Steam Input remain hardware-unverified)
**Completed:** 2026-11-26
**Requirements:** TRIG-08, TRIG-09, TRIG-10

## What changed

- Added `lookup/trigger.py`: pure `ChordDetector` with a bounded press window
  and cooldown, optional evdev watcher that fails closed when devices are
  unavailable, and a Steam Input key fallback that needs no evdev.
- Added `gaming_trigger` config key (`back_chord` or `key`) with validation and
  a visible settings combo, and Gaming trigger readiness in diagnostics.
- Extended the portable install with an owned systemd user unit
  (`~/.config/systemd/user/lookup-gaming.service`) that starts the daemon with
  `--background`; the CLI attempts `systemctl --user enable --now` and reports
  clearly when it cannot. Uninstall removes the unit but preserves user data.
- The Gaming daemon starts the watcher and routes chord callbacks through
  `QTimer` so input never touches Qt from a worker thread; quit stops it.

## Verification

| Check | Result | Evidence |
|-------|--------|----------|
| Host full pytest suite | 898 passed, 13 skipped, 1737 subtests | `.planning/phases/20-gaming-trigger/full-tests.log` |
| Shared `arch-kde` VM full unittest suite | 911 passed, 22 skipped | `.planning/phases/20-gaming-trigger/vm-tests.log` |
| Chord/cooldown/fallback tests | Pass | `tests/test_trigger.py` |
| Settings + owned systemd unit tests | Pass | `tests/test_settings_gui.py`, `tests/test_portable.py` |

## Known limitations (honest status)

- One VM run hit a timing-only migrations lock test (4.13s vs a 3.5s bound); it
  passed in isolation and in the clean final batch. No product change was needed.
- No physical Steam Deck: real back-button evdev codes, Steam Input key mapping
  and systemd behavior in Gaming Mode are unverified; diagnostics report
  readiness rather than claiming success.
- The default chord uses remappable `KEY_BACK`/`KEY_ENTER` codes because exact
  Deck back-button codes cannot be observed here.
