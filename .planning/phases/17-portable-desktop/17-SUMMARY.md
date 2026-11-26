# Phase 17 Summary: Portable Desktop Mode install

**Status:** Complete (Desktop Mode verified in VM; SteamOS hardware remains unverified)
**Completed:** 2026-11-26
**Requirements:** INST-03, INST-04, INST-05, INST-06, DTOP-01

## What changed

- Added `lookup/portable.py`: XDG-aware `~/.local` paths, marker-based ownership,
  bounded tar.gz extraction (no symlinks, hardlinks or `..`), an owned launcher
  wrapper, three desktop entries, install/uninstall/status and a no-root guard.
- The generated trigger entry carries
  `X-KDE-DBUS-Restricted-Interfaces=org.kde.KWin.ScreenShot2`; autostart is
  `OnlyShowIn=KDE;` so Gaming Mode does not autostart a desktop daemon.
- Added `tools/install_steamos.py` with `install`, `uninstall` and `status`.
  The wrapper prefers a bundled `runtime/bin/python` and adds bundled `bin`,
  `lib` and `share/tessdata` to `PATH`, `LD_LIBRARY_PATH` and `TESSDATA_PREFIX`,
  falling back to system `python3` when no bundle runtime is installed.
- `lookup/gui.py` skips source-launcher regeneration when `LOOKUP_PORTABLE=1`
  but keeps KDE shortcut registration.
- `lookup/doctor.py` checks the owned portable trigger entry for the
  ScreenShot2 permission when running from a portable install.
- Added `tests/test_portable.py` covering ownership, trusted entry text, safe
  bundle extraction, install/status/uninstall and preservation of the database
  and config under the user's normal XDG data paths.

## Verification

| Check | Result | Evidence |
|-------|--------|----------|
| Host full pytest suite | 884 passed, 13 skipped, 1737 subtests | `.planning/phases/17-portable-desktop/full-tests.log` |
| Shared `arch-kde` VM full unittest suite | 897 passed, 22 skipped | `.planning/phases/17-portable-desktop/vm-tests.log` |
| VM install/status/launcher/uninstall check | Owned app, wrapper and entries created; `lookup --help` runs through wrapper; user DB preserved after uninstall | run in `/tmp/lookup-phase17.*/check.sh` |

The VM source was copied to a fresh `/tmp/lookup-phase17.*` directory; no shared
VM apps, settings or user data were altered beyond the temporary test home.

## Known limitations (honest status)

- The actual SteamOS runtime bundle (PyQt6 wheels, Tesseract eng data,
  kdotool and wl-clipboard binaries) is built in Phase 22; Phase 17 verifies the
  install layout and wrapper semantics, not a Deck-specific wheel set.
- A simulated rootfs replacement was not performed physically; the layout keeps
  all application files under `$HOME`, so no `/usr` state is required.
- Gaming Mode remains experimental and hardware-unverified; this phase only
  covers Desktop Mode.
