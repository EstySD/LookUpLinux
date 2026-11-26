# LookUp Linux 0.3.0 — SteamOS Desktop Mode and experimental Gaming Mode

**English → Russian. Right where you read.**

This release keeps the existing Arch Linux / KDE Plasma 6 Wayland and Ubuntu
GNOME 46 desktop preview behavior and adds **SteamOS support**: a portable
Desktop Mode install and an **experimental Gaming Mode** workflow.

> **Honest status:** there was no physical Steam Deck in the development
> environment. Desktop Mode is verified in the shared Arch KDE VM; Gaming Mode
> is only unit/offscreen/VM-tested and is explicitly **hardware-unverified**.
> It is a fullscreen selection window over a captured frame, not an in-game
> overlay.

## Choose your download

| System | Asset | Install |
| --- | --- | --- |
| **Arch Linux x86_64 · KDE Plasma 6 Wayland** | `lookup-linux-0.3.0-1-x86_64.pkg.tar.zst` | `sudo pacman -U ./lookup-linux-0.3.0-1-x86_64.pkg.tar.zst` |
| **Arch Linux · build locally** | `lookup-linux-0.3.0-archlinux-x86_64-build-kit.tar.gz` | Extract, enter the build-kit directory, run `makepkg -si` |
| **SteamOS / development / other ports** | `lookup-linux-0.3.0-source.tar.gz` | Follow [docs/STEAMOS.md](https://github.com/EstySD/LookUpLinux/blob/v0.3.0/docs/STEAMOS.md) |
| **SteamOS portable source bundle** | `lookup-linux-steamos-1.2.0-source.tar.gz` | Extract and run `python3 tools/install_steamos.py install --bundle ...` (source-only; no runtime binaries) |

Download `SHA256SUMS` and verify your files:

```bash
sha256sum --ignore-missing -c SHA256SUMS
```

Checksums detect download corruption; they are not publisher signatures.

## SteamOS quick start

Install from a checkout or a downloaded bundle **as the normal user, no sudo**:

```bash
python3 tools/install_steamos.py install --source .
# or: python3 tools/install_steamos.py install --bundle ./lookup-steamos-bundle.tar.gz
~/.local/bin/lookup --app
```

Desktop Mode uses the usual hotkey (**Meta+Shift+D**) and, on SteamOS 3.9,
ScreenShot2 fallback capture because Plasma 6.7.3 is below the plugin's
`kwin>=6.8` requirement. Gaming Mode captures a gamescope frame, shows a
fullscreen selection window, then closes it to return to the game.

In Gaming Mode choose a touch tap, arrow/DPad crosshair plus **Enter**, **F1**
for the toolbar, or **Esc** to close. Set the trigger in Settings:
`back_chord` (evdev) or a Steam Input key. See the full
[SteamOS guide](https://github.com/EstySD/LookUpLinux/blob/v0.3.0/docs/STEAMOS.md).

## What changed

- Session abstraction for KDE, GNOME and gamescope; Gaming Mode skips KWin,
  kglobalaccel, kdotool and the tray.
- Portable user-level install under `~/.local` with owned launchers and data
  preservation on uninstall.
- Bounded gamescope SIGUSR2 capture with immediate temporary-file removal and
  a PipeWire/GStreamer fallback.
- Fullscreen selection layer with touch, DPad/keyboard crosshair and readable
  controls at 1280×800.
- Back-button chord trigger with debounce plus a Steam Input key fallback,
  owned systemd user unit and mode-aware diagnostics.
- `tools/check_steamos.py` prints sanitized JSON session diagnostics; no query
  text, history or screenshots.
- Deterministic SteamOS bundle builder with `MANIFEST.json`, `SHA256SUMS` and
  license notices.

Features retained from 0.2.1: context translation retry, faint-text OCR
fallback, highlighted popup translations and F1 toolbar, native KWin plugin
build inputs and checksum-bound AUR preparation.

Also included: StarDict, DSL / compressed DSL, MDX and Yomitan v3 readers,
selected-text priority, optional online context translation, history, scheduled
vocabulary review and CSV / Anki text export.

## Add your dictionary

**Dictionary databases are not bundled.** Open Settings and add your own using
the [dictionary guide](https://github.com/EstySD/LookUpLinux/blob/v0.3.0/docs/DICTIONARIES.md).
On Arch start with `lookup --app`; on SteamOS use `~/.local/bin/lookup --app`.

Online translation is enabled by default. Text and needed context may be sent
to Google or MyMemory; switch it off in Settings for offline use. OCR images
stay local. Online endpoints may be unavailable or rate limited.

## Validation and known limits

- Full host and shared-Arch VM suites are release gates; final counts and
  results are recorded in the GitHub workflow for this tag. All checks are
  **agent/VM checks**, not human hardware acceptance.
- Desktop Mode on SteamOS was exercised in the shared Arch KDE VM; no physical
  Deck was available.
- Gaming Mode's gamescope capture, focus return, evdev back-button codes,
  Steam Input mapping and systemd behavior are **not verified on hardware**.
- The included SteamOS bundle is source-only (`offline_runtime: false`). A
  runtime-complete bundle with PyQt6/Tesseract eng data/kdotool/wl-clipboard
  for the SteamOS ABI must be built in a SteamOS/Linux target environment.
- SteamOS 3.9 is Plasma 6.7.3: the native KWin plugin is unavailable and the
  ScreenShot2 fallback is used. Ubuntu 24.04 / GNOME 46 remains a separate
  desktop preview with its own documented OCR fixture differences; GNOME
  fullscreen games are not verified. No `.deb`, Windows or macOS build exists.
- Dictionary-free installs need a user-supplied dictionary for offline
  definitions.

[Full SteamOS guide](https://github.com/EstySD/LookUpLinux/blob/v0.3.0/docs/STEAMOS.md)
· [Changes since v0.2.1](https://github.com/EstySD/LookUpLinux/compare/v0.2.1...v0.3.0)

Report issues in **English or Russian** with your desktop/session, reproduction
and sanitized `--doctor` output. Original code is **GPL-3.0-or-later**; third-party
components retain their licenses.
