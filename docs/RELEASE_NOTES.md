# LookUp Linux 0.1.0

**English → Russian. Right where you read.**

Point at a word, press **Meta+Shift+D**, and keep reading with a dictionary
card beside your text. Save words to learning cards and revisit them later.

## Downloads by platform

| Platform | Download | Install |
| --- | --- | --- |
| Arch Linux x86_64 · KDE Plasma 6 Wayland | `lookup-linux-0.1.0-1-x86_64.pkg.tar.zst` | `sudo pacman -U ./lookup-linux-0.1.0-1-x86_64.pkg.tar.zst` |
| Arch Linux build from source | `lookup-linux-0.1.0-archlinux-x86_64-build-kit.tar.gz` | Extract, enter the build-kit directory, run `makepkg -si` |
| Source for development | `lookup-linux-0.1.0-source.tar.gz` | See the included README and CONTRIBUTING |
| Windows / macOS / other desktops | No supported application builds | Porting contributions welcome |

Download `SHA256SUMS` and check your assets with
`sha256sum --ignore-missing -c SHA256SUMS`. Checksums are not publisher signatures.

## First run

1. Start `lookup --app` and wait for the tray icon.
2. [Download and add a dictionary](https://github.com/EstySD/LookUpLinux/blob/main/docs/DICTIONARIES.md).
3. Apply Settings, then hover over text and press **Meta+Shift+D**.
4. Use `lookup --doctor` if the shortcut or OCR needs attention.

**Dictionary databases are not bundled.** Mueller 7 is linked in the guide;
StarDict, DSL and MDX dictionaries can be added by the user. Online translation
is enabled by default; text and needed context may go to Google or MyMemory.
Turn it off in Settings for offline use. OCR images stay local.

## Included

- Cursor OCR and selected-text lookup, optional context translation.
- StarDict / DSL / MDX readers and configurable dictionary order.
- Lookup history, learning cards, scheduled review, CSV and Anki text export.
- Tray settings, autostart control and read-only diagnostics.

## Known limits

Early release for Arch Linux x86_64 / KDE Plasma 6 Wayland. OCR varies with
fonts, contrast and application; fullscreen games require separate checks.
Online endpoints may be unavailable or rate limited. Unit/headless GUI tests
do not establish real-session desktop acceptance. The public package is checked
by automated tests and by building, installing and launching its CLI in a clean
Arch container. A fresh interactive KDE Wayland session check has not been
performed for this release; please report desktop-specific problems with
`lookup --doctor` output.

Original code: GPL-3.0-or-later. Third-party components retain their licenses.
Report issues in English or Russian with version, reproduction and sanitized diagnostics.
