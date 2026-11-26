# Phase 22 Summary: Bundle and acceptance

**Status:** Complete with an explicit hardware blocker
**Completed:** 2026-11-26
**Requirements:** PUB-03

## What changed

- Added `tools/build_steamos_bundle.py`: deterministic gzip/USTAR bundle with
  bounded inputs, POSIX tar names, `MANIFEST.json`, `SHA256SUMS`, license
  notices and an optional verbatim `runtime/` directory.
- Added tests for determinism, license/checksum contents and offline bundle
  installation through the portable installer.
- Built `dist/lookup-linux-steamos-1.2.0-source.tar.gz` (source-only,
  `offline_runtime: false`, 86 files) with SHA-256
  `773534DFD74887E621B6A7133C581E1E8FBA735E81512B561D2E178375DB883B`.

## Verification

| Check | Result | Evidence |
|-------|--------|----------|
| Final host full pytest suite | 901 passed, 13 skipped, 1737 subtests | `.planning/phases/22-bundle-acceptance/full-tests.log` |
| Final shared `arch-kde` VM suite + bundle install | 914 passed, 22 skipped; bundle installed and uninstalled with data preserved | `.planning/phases/22-bundle-acceptance/vm-tests.log` |
| Deterministic bundle build | Identical bytes on repeat builds | `tests/test_steamos_bundle.py` |
| Bundle checksum/license/install | MANIFEST, SHA256SUMS, GPL notice, installed wrapper | `tests/test_steamos_bundle.py`, VM check |

## Honest blocker

- A runtime-complete bundle (PyQt6, Tesseract eng data, kdotool, wl-clipboard
  for the SteamOS ABI) cannot be produced in this Windows environment and was
  not published. The builder supports it via `--runtime`, and the test proves
  the layout, but the actual binary artifact requires a SteamOS/Linux build
  environment and Deck validation.
- No physical Steam Deck: gamescope SIGUSR2, focus return, evdev back buttons,
  Steam Input and systemd autostart in Gaming Mode remain hardware-unverified.
