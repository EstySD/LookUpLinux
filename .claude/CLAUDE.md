<!-- GSD:project-start source:PROJECT.md -->

## Project

**LookUp Linux**

Аналог [Lookupper для Windows](https://lookupper.com/) для Linux (Arch + KDE Plasma 6); поведение копируем с него. Наводишь курсор на слово, жмёшь хоткей, программа через OCR читает слово под курсором (или берёт выделенный текст) и показывает у курсора карточку: транскрипция, значения из офлайн-словарей, исходное предложение с переводом. Найденные слова сохраняются в локальную базу со счётчиком поисков; слова можно добавить в карточки и повторять по интервальной системе, экспортировать в Anki. Живёт в трее. Делается для друга, который переходит на Linux. Сразу прод-версия, а не MVP (решение от 2026-10-24).

**Core Value:** Хоткей над английским словом даёт перевод в оверлее у курсора примерно за 1–2 секунды, и слово попадает в базу со счётчиком.

### Constraints

- **Платформа**: Arch + KDE Plasma 6, Wayland; X11-сессии в Plasma 6.8 больше нет
- **Стек**: Python 3 + PyQt6 + tesseract + spectacle + wl-clipboard из pacman, kdotool из AUR; без pip-зависимостей там, где хватает stdlib
- **Перевод**: основной источник — офлайн-словари; онлайн (Google gtx блокируется с 09.2026 — перебор client= + запасной провайдер) при ошибке не ломает попап
- **Задержка**: хоткей → попап, медиана ≤ 1,5 с в VM Дениса
- **Приватность**: OCR и словари работают офлайн; в сеть уходят только слово, фраза или предложение для онлайн-перевода; скриншоты не сохраняются
- **Внешний вид**: тема KDE (Breeze, светлая и тёмная), не копия дизайна Lookupper

<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->

## Technology Stack

## Read this first: four findings that change the plan

## Recommended Stack

### Core

| Technology | Version (Arch, 2026-10-23) | Purpose | Why |
|------------|---------------------------|---------|-----|
| `python` | 3.14.8 (core) | Whole app, one file | Already on Arch. stdlib covers sqlite3, urllib, json, subprocess, re. |
| `python-pyqt6` | 6.11.0-4 (extra, 25 MB) | Overlay + word list window + image crop/upscale | Depends only on `qt6-base` + sip. Same QImage does crop/scale/grayscale/save, so no Pillow. See "PyQt6 vs PySide6" below. |
| `qt6-base` | 6.12.0 | Qt runtime | Pulled in by Plasma anyway. Includes the `xcb` and `wayland` platform plugins and `xcb-util-cursor`. |
| `tesseract` + `tesseract-data-eng` | 5.5.3-1 + 4.1.0-5 | OCR | Plain subprocess call with TSV output. LSTM engine auto-retries inverted lines (`tessedit_do_invert`/`invert_threshold`, present in 5.5), so dark themes need no manual invert in the common case. |
| `spectacle` | 6.8.1 (extra, in the `plasma` group) | Screenshot | The only CLI that works on KWin Wayland (grim/maim/scrot do not). Already installed on any Plasma desktop. It is the process KWin already authorizes for ScreenShot2. |
| `kdotool` | 0.3.0 (AUR, `kdotool`; released 2026-09-09) | Cursor position, output geometry, overlay placement | Generates a KWin script, runs it over D-Bus, returns results. One subprocess instead of ~45 lines of D-Bus plumbing. |
| `wl-clipboard` | 2.3.0-1 (extra) | Read PRIMARY selection from an unfocused process | Needs the `ext-data-control` support that KWin provides. |

### Database

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| stdlib `sqlite3` | bundled with Python 3.14 | Words, translations, counters | `INSERT ... ON CONFLICT(word) DO UPDATE SET count=count+1` (SQLite >= 3.24). File at `$XDG_DATA_HOME/lookup/lookup.db` (default `~/.local/share/lookup/`). `sqlite3.connect(path, timeout=5)` is enough for hotkey process + word list window overlapping. No ORM, no QtSql. |

### Infrastructure (integration points)

| Piece | Mechanism | Why |
|-------|-----------|-----|
| Global hotkey | `~/.local/share/applications/lookup.desktop` with `Exec=<abs path> ` and `X-KDE-Shortcuts=Meta+Shift+D`, then `kbuildsycoca6` | Source-verified registration path, scriptable, shows up in System Settings > Shortcuts, works on Wayland because KWin owns the shortcut. |
| Manual fallback | System Settings > Keyboard > Shortcuts > Add New > Command or Script | Same result (the KCM writes `~/.local/share/applications/net.local.<exe>.desktop` with `X-KDE-GlobalAccel-CommandShortcut=true`). Put these steps in the README. |
| Cursor / screen | `kdotool kwinscript --inline '<JS>'` | See snippet below. |
| Screenshot | `spectacle -b -n -m -o $XDG_RUNTIME_DIR/lookup-<pid>.png` | Flags verified, see below. |
| Selection | `wl-paste --primary --no-newline` (timeout 0.5 s) | Works from an unfocused one-shot process. |
| Translation | stdlib `urllib.request` to `translate.googleapis.com` | Verified live today, see below. |

## Per-question answers (with evidence)

### 1. Global hotkey

- `GlobalShortcutsRegistry::detectAppsWithShortcuts()` queries all applications with a non-empty `X-KDE-Shortcuts` and builds a `KServiceActionComponent` for each; `loadSettings()` registers a `_launch` shortcut whose default is that value. It is re-run on `KSycoca::databaseChanged`.
- Activation runs `KIO::ApplicationLauncherJob` on the service, so `Exec=` runs in the user session with `WAYLAND_DISPLAY`/`DBUS_SESSION_BUS_ADDRESS` set.
- Spectacle ships exactly this pattern (`X-KDE-Shortcuts=Print,Meta+Shift+S`, `Shift+Print`, `Meta+Print`...). Do not pick those keys.
- User overrides live in `~/.config/kglobalshortcutsrc` under `[services][lookup.desktop]` as `_launch=...`; the installer should not touch that file.
- Plasma 6 has no khotkeys "Custom Shortcuts" page. "Add New > Command or Script" in the Shortcuts KCM replaces it (source: `kcm_keys.cpp::addCommand`).
- `kwriteconfig6` edits of `kglobalshortcutsrc` are reported unreliable (not live-reloaded). Do not use them. D-Bus `setShortcutKeys` on `org.kde.kglobalaccel` also works but is more code than a file drop.

# ~/.local/share/applications/lookup.desktop

- Use an absolute `Exec` path (the shortcut environment is the session environment; `~/.local/bin` is not guaranteed to be on `PATH`).
- Pick a key that is free. `Ctrl+Alt+L` is the lock-screen default; avoid it. If the key is taken, kglobalacceld leaves the default unbound and the user must set it in System Settings.
- Add a second desktop file or a `[Desktop Action words]` entry (`Exec=... words`) for the word list window; launcher click = open list.

### 2. Cursor position and screen geometry on Wayland

- `kdotool getmouselocation [--shell]` exists. Its template is literally `let p = workspace.cursorPos; let screen = workspace.screenAt(p); ...` and prints `X= Y= SCREEN= WINDOW=` (screen is an index, no geometry).
- 0.3.0 (tag, 2026-09-09; `CHANGELOG`: "Add `kwinscript` subcommand", Plasma 5 support dropped) runs arbitrary JS with the helpers `output_result()`, `output_error()`. So one call can return cursor + output geometry + scale:
- Mechanism proof: kdotool loads the script via `org.kde.KWin /Scripting`, and the script returns data with `callDBus("<kdotool bus name>", "/", "", "result", msg)` into kdotool's own D-Bus service. That is exactly the "KWin script + callDBus" design; kdotool is that design already written (Rust, deps `dbus glibc libgcc`).
- Cost: ~50-100 ms per call (estimate, not measured).
- Works in X11 sessions too (README).

### 3. Screenshot

- Images are captured at **native pixel size** (`native-resolution` flag), not logical size. This is why the `sx = img_w / gw` derivation is needed.
- `-m` maps to KWin `CaptureActiveScreen` -> `workspace.activeOutput()`. KWin sets the active output on every pointer motion (`pointer_input.cpp`) and on window activation, so it is normally the cursor's monitor but not guaranteed (activating a window on another monitor by keyboard changes it). The probe returns `name` (cursor's output) and `active`; if they differ, fall back to `-f` and use virtual-screen geometry, or ask the user to nudge the mouse.
- Write to `$XDG_RUNTIME_DIR` (tmpfs) and delete right after loading. Satisfies "screenshots are not stored".
- Latency: published numbers are anecdotal (0.5-2 s on user machines, historically dominated by KWin's PNG encode; KWin now hands over raw data over a pipe). Estimate 300-800 ms. Measure in the VM with `time spectacle -b -n -m -o /run/user/$UID/t.png`; if too slow, try `.bmp`/`.ppm` as the output extension (skips PNG compression, untested).
- Start spectacle first (Popen) and do imports + probe while it runs.

### 4. OCR

- `python-pytesseract` 0.3.13 exists in `extra` but is a thin wrapper that also needs Pillow; it saves nothing.
- Command: `tesseract <png|stdin> stdout -l eng --psm 11 --dpi 300 tsv` (options before the `tsv` config; `stdout` as output base). TSV columns: `level page_num block_num par_num line_num word_num left top width height conf text`; use `level==5`, `conf>=0`, non-empty `text`. Run with env `OMP_THREAD_LIMIT=1` (reports say equal or faster for small images; not authoritative, measure).
- PSM: default is 3. For a crop with UI text use **11 (sparse text)** or 6 (single block); 7/8 only if you pre-isolate one line/word (we do not). Tesseract docs: sparse text -> 11/12, single line/word -> 7/8.
- Preprocessing, in this order, all with `QImage`:
- Binarization: leave Tesseract's own (Otsu; 5.x adds adaptive/Sauvola). Do not add OpenCV.
- Word under cursor: map the cursor into crop coordinates, pick the word whose bbox contains it, else the nearest bbox within ~0.75 box heights. Normalise (strip punctuation, `'s`, case) before DB/translation.
- Language data: `tesseract-data-eng` only (22 MB). Do not install `tesseract-data-osd` explicitly; it comes as a dependency.

### 5. Translation

- `d[0]` = list of segments `[translated, original, null, null, ...]`; join `s[0]`.
- `d[1]` (present when `dt=bd` and the input is a word with dictionary data) = `[[pos, [term, ...], [[term, reverse_translations_or_null, null, score], ...], source_word, ...], ...]`. `pos` is English ("noun", "verb", "adjective", "interjection"). `terms` is a flat ranked list; cap at 3-5 per part of speech for the overlay.
- `d[2]` = detected source language (`"en"`).
- Unknown/non-words: the main translation echoes the input and `d[1]` is `null`. Treat "translation == input" as "no translation".
- `dj=1` returns named JSON (`sentences`, `dict[].pos/terms/entry[].word/reverse_translation/score`) and is more readable, but it is a different shape; pick one and pin it with a fixture test. Use the array form above.
- Failure handling: wrap in one `TranslateError`; on error show it in the overlay and do **not** write the DB row. Cache hit in SQLite skips the network.

### 6. Overlay and word list window

- Qt's xcb plugin sets the "user specified position" ICCCM hint whenever the position was set explicitly (`QXcbWindow::propagateSizeHints`: `if (!win->positionAutomatic) xcb_icccm_size_hints_set_position(..., true, ...)`), and KWin's `X11Window` honors it (`m_geometryHints.hasPosition()` -> `placementDone = true`). XWayland windows are the same `X11Window` class as in the old X11 session.
- `Qt.ToolTip` / `Qt.Popup` windows are created `override_redirect=1` in Qt xcb, so KWin does not manage them at all: exact position, never focused (Esc will not work; click/timeout only). `Qt.Tool` + frameless is managed (gets `_KDE_NET_WM_WINDOW_TYPE_OVERRIDE`, no decoration) and can take focus.
- **Coordinate trap:** X11 coordinates of XWayland clients are `logical * xwaylandScale`. KWin sets `xwaylandScale = max(output scale)` when `kdeglobals [KScreen] XwaylandClientsScale` is true (the default, "Apply scaling themselves") else 1, and X11 apps see physical-ish pixels. Qt xcb's own scale comes from `Xft.dpi` and rounds to an integer, so fractional scales (1.25/1.5) can place the window wrong. At scale 1 and integer scales it should land correctly.
- Needs `DISPLAY` in the shortcut's environment (XWayland is started on demand; `xorg-xwayland` is a dependency of `plasma-workspace`). If `DISPLAY` is unset, skip xcb rather than crash.
- Use route B only as a fallback if route A's kdotool move proves flaky, or as the quick first spike on a scale-1 VM.

### 7. PRIMARY selection from an unfocused process

- KWin (`master`) registers `ExtDataControlManagerV1` unconditionally for non-sandboxed clients and `zwp_primary_selection_device_manager_v1` when `EnablePrimarySelection` is true (default true in `kwin.kcfg`; the KCM "Enable middle click selection pasting" toggles it). A shortcut-launched process is not sandboxed, so it may bind data-control.
- `wl-clipboard` 2.3.0 speaks `ext-data-control-v1` (release notes: contributed by KWin's maintainer). `wl-clipboard` <= 2.2.x only knows `wlr-data-control`, which KWin does not offer. The installer must check `pacman -Q wl-clipboard >= 2.3.0`.
- `wl-paste --primary` exits non-zero with an error when there is no selection or primary selection is disabled. Treat every non-zero exit, timeout (0.5 s) and empty output as "no selection".
- Qt QClipboard.Selection: a process with no focused window cannot read the Wayland selection natively, and under xcb the XWayland bridge only syncs when an X11 client has focus. Rejected.
- PRIMARY is *stale* by nature (it stays set until something else is selected). The "only if new since last consumed" rule lives in the logic layer (see ARCHITECTURE.md Pattern 4), not the stack.
- X11 session fallback (Plasma <= 6.7 only): `xclip -o -selection primary` (`xclip`, extra). Optional; skip in the MVP unless the friend is on 6.7 X11.

### 8. Storage

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Hotkey | `.desktop` + `X-KDE-Shortcuts` | `kwriteconfig6` on `kglobalshortcutsrc` | Reported not live-reloaded; flaky. |
| Hotkey | `.desktop` + `X-KDE-Shortcuts` | `kdotool --shortcut` (KWin script shortcut) | Runs a KWin script, not our command; ties the app to kdotool. |
| Hotkey | `.desktop` + `X-KDE-Shortcuts` | Own keyboard listener / evdev / `keyd` | Needs root/input group; unnecessary on Wayland. |
| Cursor | `kdotool kwinscript` | Hand-written KWin script + Python D-Bus receiver | ~45 more lines, Python D-Bus slot export unproven; same mechanism as kdotool. |
| Cursor | `kdotool kwinscript` | `QCursor.pos()`, `xdotool` | Stale/dummy values under Wayland and XWayland. |
| Screenshot | `spectacle -b` | KWin `ScreenShot2` D-Bus directly | Fastest (CaptureArea) but needs caller authorization tied to an absolute executable path; deferred. |
| Screenshot | `spectacle -b` | `grim`, `maim`, `scrot`, XDG portal | grim needs wlr-screencopy (KWin lacks it); maim/scrot are X11 only; portal shows consent UI. |
| OCR | `tesseract` subprocess + TSV | `pytesseract` | Wrapper over the same call, adds Pillow. |
| OCR | `tesseract` | EasyOCR/PaddleOCR/RapidOCR | Hundreds of MB, torch/onnx, slow cold start; violates "pacman only". |
| GUI | `python-pyqt6` | `pyside6` | Larger (52 MB + shiboken6); no functional gain here. |
| GUI | Qt widgets | GTK / Tk / KDE notification | Cannot be placed at cursor / KNotification is not cursor-anchored. |
| Overlay placement | Native Qt + KWin move | `QT_QPA_PLATFORM=xcb` + `move()` | Works at scale 1; breaks on fractional scale (xwayland coordinate scaling). Kept as fallback. |
| Selection | `wl-paste` | Qt `QClipboard.Selection` | Unfocused process cannot read it. |
| Translation | gtx via urllib | `translate-shell`, `deep-translator` (pip) | Same endpoint with extra dependencies. |

## What NOT to Use

- `kdotool-git` (AUR, v0.2.1.r51): old, lacks `kwinscript`.
- `pytesseract`, `Pillow`, `opencv`, `numpy`: nothing here needs them.
- Any local LLM/offline translator as part of the dev workflow: out of scope per PROJECT.md and the user's local-model boundary.
- `xdotool`, `xclip`, `xsel` as the primary path: X11 session is gone in Plasma 6.8.
- `wl-clipboard` < 2.3.0.
- Depending on a daemon/tray for the MVP.

## Installation

# Official repos (Arch), run as root

# AUR (not in official repos)

# no-build alternative: download kdotool-0.3.0-x86_64-unknown-linux-gnu.tar.gz from

#   https://github.com/jinliu/kdotool/releases/tag/v0.3.0 and put `kdotool` in ~/.local/bin

# Installer steps (user level)

## Verify in the Arch VM (known unknowns, in priority order)

## Confidence by choice

| Choice | Confidence | Basis |
|--------|------------|-------|
| Wayland-only Plasma 6.8 reality (no X11 session) | HIGH | KDE developer blog, Phoronix, Arch package search |
| Package names/versions | HIGH | Arch package JSON API, 2026-10-23 |
| `.desktop` + `X-KDE-Shortcuts` hotkey | HIGH (mechanism) / MEDIUM (unrun) | kglobalacceld source, spectacle desktop file |
| kdotool `kwinscript` for cursor/geometry | HIGH | kdotool v0.3.0 source/README/CHANGELOG, AUR RPC, KWin scripting source |
| spectacle flags | HIGH | spectacle `CommandLineOptions.h`, `SpectacleCore.cpp`, `ImagePlatformKWin.cpp` |
| spectacle latency | LOW | anecdotal only |
| ScreenShot2 direct | LOW | authorization rules unclear in current source |
| Tesseract via subprocess/TSV, no manual invert | MEDIUM | Tesseract docs and 5.5 source; accuracy untested |
| gtx endpoint | HIGH today, LOW longevity | live calls 2026-10-23 |
| PyQt6 over PySide6 | MEDIUM-HIGH | package metadata; judgement call |
| Native Qt + kdotool move for overlay | MEDIUM | all parts exist; combination unrun |
| XWayland placement | MEDIUM at scale 1, LOW at fractional | Qt and KWin source reading |
| `wl-paste --primary` | HIGH (protocol) / MEDIUM (runtime) | KWin source, wl-clipboard 2.3.0 release notes |

## Sources

- Arch package JSON API (`archlinux.org/packages/.../json`): versions of python 3.14.8, python-pyqt6 6.11.0-4, pyside6 6.12.0-3, qt6-base 6.12.0, tesseract 5.5.3, tesseract-data-eng 4.1.0, wl-clipboard 2.3.0, spectacle 6.8.1, kwin 6.8.1, xorg-xwayland 24.1.14; `plasma-workspace` depends on `xorg-xwayland`; no `plasma-x11-session`/`kwin-x11` (HIGH)
- AUR RPC `aur.archlinux.org/rpc/v5/info`: `kdotool` 0.3.0-1, `kdotool-git` v0.2.1.r51 (HIGH)
- https://github.com/jinliu/kdotool (README, `src/templates.rs`, `CHANGELOG.md` at tag v0.3.0; release asset list) (HIGH)
- https://blog.davidedmundson.co.uk/blog/596/ and https://www.phoronix.com/news/KDE-Plasma-68-Wayland-Exclusive : Plasma 6.8 drops the X11 session; XWayland remains (HIGH)
- KDE `spectacle` master: `src/CommandLineOptions.h`, `src/SpectacleCore.cpp`, `src/Platforms/ImagePlatformKWin.cpp`, `desktop/org.kde.spectacle.desktop.cmake` (HIGH)
- KDE `kwin` master: `src/plugins/screenshot/org.kde.KWin.ScreenShot2.xml` and `screenshotdbusinterface2.cpp`, `src/scripting/workspace_wrapper.h`, `src/core/output.h`, `src/wayland_server.cpp`, `src/kwin.kcfg`, `src/pointer_input.cpp`, `src/x11window.cpp`, `src/workspace.cpp` (HIGH for code reading; not run)
- KDE `kglobalacceld` master: `src/globalshortcutsregistry.cpp`, `src/kserviceactioncomponent.cpp` (HIGH)
- KDE `plasma-desktop` master: `kcms/keys/kcm_keys.cpp`, `globalaccelmodel.cpp`, `kcms/workspaceoptions/workspaceoptions_kwinsettings.kcfg` (HIGH)
- Qt `qtbase` `src/plugins/platforms/xcb/qxcbwindow.cpp` (position hints, override-redirect rules) (HIGH)
- https://github.com/bugaevc/wl-clipboard releases (v2.3.0, 2026-03-22: `ext-data-control-v1`) (HIGH)
- https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html and Command-Line-Usage.html; tesseract 5.5.0 `tesseractclass.cpp`/`linerec.cpp` (invert handling) (MEDIUM-HIGH)
- Live requests to `translate.googleapis.com/translate_a/single?client=gtx...` on 2026-10-23 (curl + Python urllib) (HIGH for today)
- KDE Discuss / KWin mailing list threads on ScreenShot2 authorization and Plasma 6 shortcut config (LOW-MEDIUM, anecdotal)
- Confidence-tier seam (`gsd-tools query classify-confidence`) rates bare web fetches LOW unless cross-verified; every HIGH above is backed by a primary-source read or a live call, not by a single web summary.

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
