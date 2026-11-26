# Phase 21 Summary: Mode-aware settings and documentation

**Status:** Complete
**Completed:** 2026-11-26
**Requirements:** DOC-01, DOC-02

## What changed

- Settings components are cached per mode; Gaming Mode hides the KDE shortcut
  widgets and skips `kglobalaccel` inspection while keeping the Gaming trigger
  selector.
- Added `docs/STEAMOS.md`: portable install, Desktop Mode behavior, fallback
  capture on SteamOS 3.9, optional KWin plugin on 3.10+, Gaming Mode workflow,
  Steam Input key fallback, diagnostics, update/uninstall and explicit
  limitations.
- README and `docs/README.ru.md` now link SteamOS docs and show Desktop Mode as
  supported and Gaming Mode as experimental/hardware-unverified.

## Verification

| Check | Result | Evidence |
|-------|--------|----------|
| Host full pytest suite | 899 passed, 13 skipped, 1737 subtests | `.planning/phases/21-docs-mode-aware/full-tests.log` |
| Shared `arch-kde` VM full unittest suite | 912 passed, 22 skipped | `.planning/phases/21-docs-mode-aware/vm-tests.log` |
| Gaming settings offscreen test | KDE registry not called; shortcut hidden | `tests/test_settings_gui.py` |

## Known limitations (honest status)

- Documentation deliberately does not claim Steam Deck hardware verification.
- Per-game Steam Input layout is documented as manual, since no global Gaming
  Mode layout exists.
