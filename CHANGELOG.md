# Changelog

## 0.2.1 — 2026-11-03

- Retry context translation with existing Google clients when gtx is restricted,
  under one shared deadline; retain strict marked-word validation.
- Include native KWin plugin sources in the public source archive.
- Prepare checksum-bound AUR metadata and package lifecycle instructions.
- Agent verification on KDE Wayland: live contextual translation, real MDX/DSL,
  second monitor at 100%/125%, and borderless Wesnoth lookup/input return.
- Local OCR passes for faint UI text and the reproduced Discover “games” case.
- Highlighted popup translations, snapshot hover retention and F1 toolbar toggle.

## 0.2.0 — 2026-11-02

- Ubuntu 24.04 / GNOME Shell 46 Wayland support through an optional extension.
- GNOME cursor and monitor detection, in-memory capture, popup placement and
  persistent global shortcuts, including conflict detection and rollback.
- User-level Ubuntu installer, desktop/autostart entries and GNOME diagnostics.
- Fix popup height restoration on Mutter with Ubuntu's Qt 6.4.
- Include the GNOME extension, schema and setup guide in public source archives.
- Document physical-input VM acceptance and include a real desktop screenshot.

Arch keeps its KWin / ScreenShot2 / KGlobalAccel backend. Agent validation:
814 tests on Arch (20 skipped), 118 targeted tests on Ubuntu, native OCR and
PRIMARY lookup with real dictionary/history. Ubuntu's full default-model run
has 11 known OCR fixture differences; GNOME fullscreen games are not verified.

## 0.1.0 — 2026-11-02

Initial public release for Arch Linux x86_64 / KDE Plasma 6 Wayland.

- Cursor OCR and selected-text English–Russian lookup.
- StarDict, DSL / compressed DSL and MDX dictionary readers.
- Optional online translation and context meaning.
- Tray settings, history, learning cards and scheduled review.
- CSV / Anki text export and `--doctor` diagnostics.
- GPL-3.0-or-later, public packaging without bundled dictionaries, community
  documentation and automated draft releases.

Known limits: no Windows/macOS application builds or support promise for other
desktops; variable OCR/game compatibility; online service rate limits. Real
desktop acceptance is separate from unit tests.
