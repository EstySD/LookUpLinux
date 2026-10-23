# Project Research Summary

**Project:** LookUp Linux
**Domain:** Personal hotkey → OCR word under cursor (or selection) → EN→RU popup → vocabulary log, on Arch Linux + KDE Plasma 6 Wayland
**Researched:** 2026-10-23
**Confidence:** MEDIUM-HIGH. Package versions and KWin/spectacle/kglobalacceld behaviour were checked against upstream source; nothing has been run on a real Plasma session yet.

## Executive Summary

A Linux clone of the core of Lookupper for Windows (https://lookupper.com/): press a hotkey over an English word, the tool reads the word by OCR (or takes the current selection), shows a popup next to the cursor with a dictionary entry or translation plus the source line, and saves the word with its context and a lookup count. Behaviour and UX are copied, not code. Out of scope: SRS, Anki/CSV export, DSL/MDX/Yomitan dictionaries, gamepad, whole-screen translation, audio, CEFR. The hard part is Wayland, not translation: hotkey, cursor position, window placement and screenshots all need compositor cooperation.

Recommended build: a single-file Python 3 + PyQt6 one-shot process launched once per hotkey press.
- **Hotkey:** `.desktop` file with `X-KDE-Shortcuts` + `kbuildsycoca6`; manual KDE GUI steps in the README as fallback.
- **Cursor / window placement:** `kdotool` returns cursor and output geometry, and moves/activates the overlay.
- **Screenshot:** `spectacle -b -n -m -o tmpfile`.
- **OCR:** `tesseract` via subprocess TSV; Qt `QImage` for crop/upscale.
- **Selection:** `wl-paste --primary` (wl-clipboard ≥ 2.3.0) under a kill timeout.
- **Translation:** offline StarDict dictionary first (default Mueller 7 EN→RU, GPL, ~46k articles, parsed with stdlib gzip, no pystardict); online fallback only when the word is missing or a phrase is selected.
- **Storage:** stdlib sqlite3 with a single atomic UPSERT.

Target is Plasma 6 Wayland only: Plasma 6.8 removed the X11 session, so no X11 code paths and no xclip.

Main risks are platform integration, not logic:
1. Google gtx is being blocked right now (Sept 2026) — hence offline dictionary first, and the online path must never break the popup.
2. The kdotool window-move chain, spectacle latency and shortcut activation are untested in combination — VM spike before building on them.
3. Tesseract accuracy on small UI text at 125–200% scale is unmeasured.
4. VMs misreport pointer and rendering — the friend must run a real-hardware smoke test before the MVP counts as done.

Mitigation: build and test the pure core first, spike the desktop seam early, wire everything together after.

## Orchestrator Decisions Applied

Fixed for the roadmapper:

1. **Reference:** Lookupper for Windows, not macOS LookUp. MVP core: hotkey → OCR word → popup (entry or translation + source line) → save with context and count.
2. **Translation:** offline StarDict first, online fallback = Google gtx with `client=` rotation, strict 429/HTML detection, short timeout. Translations cached in the DB.
3. **Platform:** Plasma 6 Wayland only. No X11 paths.
4. **Toolkit and glue:** PyQt6 + kdotool. Custom KWin script + QtDBus receiver only if kdotool fails the VM spike. Overrides ARCHITECTURE.md (which assumed PySide6 + custom KWin script).
5. **Process model:** one-shot per hotkey; daemon only if measured p50 > 2 s.
6. **Capture and OCR:** spectacle, tesseract TSV, Qt `QImage`.
7. **Selection:** `wl-paste --primary` with kill timeout; used only if non-empty, short and different from the last consumed value (hash in DB meta table); otherwise OCR.
8. **Concurrency:** SQLite UPSERT + `busy_timeout`, flock single-instance lock.
9. **Testing:** QEMU/KVM with virtio-gpu + real-hardware smoke test by the friend.

## Key Findings

### Recommended Stack (see STACK.md)

One Python file, no pip, no venv. Official `extra` packages plus one AUR / GitHub-binary tool.

- **Python 3 stdlib:** sqlite3, gzip, urllib, json, subprocess.
- **`python-pyqt6` 6.11:** overlay, word list, image prep. Smaller than PySide6.
- **`tesseract` 5.5.3 + `tesseract-data-eng`:** subprocess TSV. 5.5 retries inverted lines itself, so no manual invert at first.
- **`spectacle` 6.8.1:** the only screenshot CLI that works on KWin Wayland. Output to tmpfs.
- **`kdotool` 0.3.0** (AUR, or the 814 KB prebuilt GitHub binary): `kwinscript --inline` returns cursor, geometry and scale in one call; also moves/activates the overlay. Not `kdotool-git`.
- **`wl-clipboard` ≥ 2.3.0:** older versions fail on KWin.
- **StarDict Mueller 7 EN→RU:** offline primary source.
- **stdlib `sqlite3`:** words, translation cache, meta table.
- **`.desktop` + `X-KDE-Shortcuts` + `kbuildsycoca6`:** scriptable hotkey; absolute `Exec` path, free key such as Meta+Shift+D.

**Do not use:** pytesseract, Pillow, OpenCV, numpy, xdotool, xclip, `kwriteconfig6` on kglobalshortcutsrc, wl-clipboard < 2.3.0, daemon/tray for the MVP.

### Expected Features (see FEATURES.md)

FEATURES.md treated gtx as the main source (POS variants, transcription). Under decision 2 those become secondary; the dictionary entry is the primary popup content.

**Must have (table stakes):**
- Hotkey → popup, no main window; one-shot process with single-instance guard.
- Selection mode with the stale-selection rule, then OCR word under cursor with nearest-box fallback.
- Popup near the cursor, clamped to the screen: word, entry/translation, source line, lookup count. Dismiss on click, Esc, focus loss or timeout.
- Normalisation before the DB: NFC, curly quotes, strip edge punctuation, lowercase, strip `'s`, reject non-words.
- SQLite save with context, count, first/last seen, plus translation cache.
- Visible failure popups — every hotkey press shows something.
- Word-list window sorted by count desc, click-sort, search, delete.
- Arch install script + README with KDE shortcut fallback steps.

**Should have (differentiators):**
- "Seen N times" line in the popup.
- Cache hit before dictionary/network.
- Phrases: 2–4 words translated and saved; longer text shown but not saved.

**Defer (v2+):** SRS, Anki/CSV, known/learning status; DSL/MDX/Yomitan, audio, CEFR, gamepad, whole-screen translation; lemmatisation, daemon, AUR package, other languages and desktops.

### Architecture Approach (see ARCHITECTURE.md)

One file, `lookup.py`, ~300–450 lines: pure core on top, thin Qt/subprocess shell below, Qt imported lazily so tests run headless. Slow stages overlap: spectacle starts first; Qt import and cursor probe run while it captures. Only the monitor under the cursor is captured. Pixel scale derived from data (`sx = image_width / output_logical_width`), not from scale settings. All placement in KWin logical global coordinates via kdotool. DB doubles as cache and holds the consumed-selection hash. Per-stage timing (`LOOKUP_TIMING=1`) from day one.

**Major components:**
1. Entry + flock single-instance lock; a new press replaces the old one.
2. Desktop seam: kdotool probe, spectacle capture, overlay move/activate.
3. OCR pipeline: crop, upscale, grayscale, border, tesseract TSV, `pick_word`.
4. Selection reader + `choose_mode` with consumed-hash memory.
5. Translation: StarDict → cache → online fallback, behind one function that never raises into the UI.
6. Store: UPSERT, cache, meta, list query.
7. Overlay and word-list window in PyQt6.

### Critical Pitfalls (see PITFALLS.md)

PITFALLS.md items about `QCursor`/XWayland and kdotool-as-AUR-risk are superseded by decisions 3 and 4.

1. **gtx blocked (429 with HTML body, not an exception).** Offline dictionary first. Treat non-200, non-JSON and "automated queries" (case-insensitive) as `blocked`; never retry in a loop. Wall-clock deadline ~3 s in a worker. Cache every success. On failure still save the word with NULL translation. Spike reachability early.
2. **No client-side cursor or placement on Wayland.** Never `QCursor.pos()` or `move()`; cursor and geometry from kdotool, overlay placed with it. Paint nothing until the move completes. Esc is best-effort; click and timeout must always close.
3. **Logical cursor vs physical screenshot.** Capture one monitor with `-m`; per-axis scale = image size / logical size. Unit-test 1x, 1.25x, 1.5x, 2x and a negative-origin monitor. If probe's cursor output ≠ active output, abort with a hint.
4. **Spectacle quirks.** Always `-o` to tmpfs, never `-c`, use `-n`. Hard timeout; success = file exists. Delete in `finally`. Test with the Spectacle GUI open. Previous overlay must be gone before capturing.
5. **PRIMARY selection.** `wl-paste` can hang — kill after ~0.5 s. Never Qt `QClipboard` Selection. Re-looking up the same selection falls through to OCR (accepted).
6. **Tesseract on UI text.** Fixture set first. `--oem 1 -l eng`, `OMP_THREAD_LIMIT=1`; choose PSM 11 vs 6 on fixtures. Junk filter + confidence gate so garbage is neither translated nor saved.
7. **Overlapping presses, shortcut environment.** flock, single UPSERT, `busy_timeout`. Absolute-path launcher, log file, `--doctor`.
8. **VMs misreport pointer and rendering.** QEMU/KVM virtio-gpu; logic fixture-tested outside the VM; real-hardware smoke test.

## Implications for Roadmap

Six phases suggested. Phases 1–2 low risk, no desktop needed. Phase 3 carries almost all platform risk and is deliberately early.

### Phase 1: Pure core, StarDict, store, tests
**Rationale:** ~60% of logic is testable without a desktop. Normalisation and schema must be settled before the first row is written.
**Delivers:** `normalise`, `parse_tsv`, `pick_word`, geometry functions, `choose_mode`; StarDict reader (.ifo/.idx/.dict(.dz) via gzip); gtx parser with client rotation behind `TranslateError`/`blocked`; SQLite store (words, cache, meta, UPSERT, list query); unittest suite with fixtures.
**Avoids:** pitfalls 1, 4, 9, 15.

### Phase 2: CLI pipeline on fixtures + OCR tuning
**Rationale:** Proves OCR settings and the dictionary on real text before any Wayland work; adds timing.
**Delivers:** `lookup --image x.png --at X,Y` prints word and translation; fixture screenshots light/dark at 100/150/200%; chosen PSM, upscale factor, invert rule; stage timing; gtx reachability check from the VM and the friend's network.
**Avoids:** pitfalls 8, 1.

### Phase 3: Desktop seam spike (VM)
**Rationale:** Highest uncertainty; doing it early behind the pure core means failure changes the plan, not the logic.
**Delivers:** kdotool probe (cursor, geometry, scale) incl. exact `output_result` format on Plasma 6.8.1; `spectacle -b -n -m -o` timing; cursor→pixel mapping verified at VM scales; shortcut activation with/without re-login and with a conflicting key; kdotool windowmove/windowactivate on a throwaway Qt window; `wl-paste --primary` behaviour; measured stage timings.
**Decision gate:** if kdotool fails → custom KWin script + QtDBus receiver.
**Avoids:** pitfalls 2, 3, 5, 10, 11, 12.

### Phase 4: End-to-end hotkey path (overlay, selection, failures)
**Delivers:** `run_once` with flock and spectacle started first; selection mode with consumed-hash rule; overlay (word, entry/translation, source line, "seen N times") placed via kdotool, clamped, dismiss on click/Esc/focus-out/timeout; failure popups; DB write after popup shown; log file and `--debug`.
**Avoids:** pitfalls 6, 7, 9, 13, 14.

### Phase 5: Word list window + packaging
**Delivers:** word-list window (count desc, sort, search, delete); launcher `.desktop`; `install.sh` (pacman check, kdotool install, dictionary placement, `.desktop` + `kbuildsycoca6`); Russian README with manual shortcut steps; `--doctor`.
**Avoids:** pitfalls 10, 16, 17.

### Phase 6: Hardening + real-hardware validation
**Delivers:** friend's hardware smoke test; p50/p95 timings (daemon decision point if p50 > 2 s); scale matrix 100–200%; privacy check (no PNG left, clipboard history unchanged); parallel-invocation test; fresh-Arch walkthrough of the install doc.
**Avoids:** pitfalls 11, 12, 17.

### Phase Ordering Rationale

- Word acquisition, translation and saving exchange plain strings, so the pure core can be finished and tested first; the desktop seam stays in one module.
- Phase 3 precedes the overlay because every later step depends on cursor, capture and placement.
- The word list depends only on the DB, so it follows the hotkey path.
- Dictionary-first moves the unofficial gtx endpoint off the critical path.

### Research Flags

**Needs hands-on spike / deeper research:** Phase 3 (kdotool move chain, shortcut without re-login, spectacle latency, PRIMARY); Phase 2 (tesseract on UI text at 125–200%); Phase 4 (overlay focus and Esc under KWin activation).

**Standard patterns (skip research):** Phase 1, Phase 5, Phase 6.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM-HIGH | Versions and flags source-verified; kdotool, shortcut registration, wl-paste not run. |
| Features | MEDIUM | Scope follows PROJECT.md and the Lookupper reference; competitor details from prior knowledge. |
| Architecture | MEDIUM-HIGH | One-shot, derived scale, pure core sound; kdotool seam unrun in combination. |
| Pitfalls | MEDIUM-HIGH | gtx block backed by four trackers, Wayland rules by KDE docs; focus stealing and VM behaviour community-sourced. |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **Spectacle latency:** 300–800 ms is an estimate; measure in VM and on real hardware. Over budget → try .bmp/.ppm, then ScreenShot2 (low confidence on auth) or daemon.
- **kdotool window-move chain:** `search --pid … windowmove … windowactivate` syntax and movability of Qt Tool/Frameless windows unverified (phase 3). Fallbacks: custom KWin script + QtDBus, or XWayland (scale 1 only).
- **Tesseract on UI text at 125–200%:** PSM 11 vs 6, upscale factor, invert rule — decide on phase 2 fixtures.
- **PRIMARY readability:** depends on wl-clipboard ≥ 2.3.0 and the middle-click-paste setting; any failure = "no selection" → OCR.
- **Shortcut without re-login:** `.desktop` route source-verified but unrun; keep manual System Settings steps in README.
- **Online fallback longevity:** gtx `client=` values change weekly; decide in phase 2 whether a second keyless provider is worth it or "translation unavailable, word saved" is enough.
- **Dictionary coverage:** Mueller 7 has no inflected forms — measure misses (running, ran); maybe a light suffix fallback to the base form.
- **Real hardware and multi-monitor:** friend's smoke test is mandatory.

## Sources

### Primary (HIGH)
- Arch package JSON API and AUR RPC (2026-10-23): names, versions, kdotool availability.
- KDE kwin, spectacle, kglobalacceld, plasma-desktop upstream source: scripting API, CLI flags, shortcut registration.
- https://github.com/jinliu/kdotool (README, templates, CHANGELOG v0.3.0).
- wl-clipboard v2.3.0 release, issue #185 (wl-paste hang).
- https://blog.davidedmundson.co.uk/blog/596/ and Phoronix: Plasma 6.8 drops the X11 session.
- Tesseract tessdoc ImproveQuality; SQLite WAL docs.
- eeeXun/gtt #43, livecap-cli #442, noctalia official-plugins #64: gtx blocking.
- KDE Wayland Porting Notes, KWin MR !3134: no global cursor on Wayland.

### Secondary (MEDIUM)
- KDE Discuss threads: ScreenShot2 authorization, spectacle launch time, XWayland scaling, Plasma 6 shortcuts.
- Crow Translate #324 / MR !596, GoldenDict-ng release notes: selection on Wayland.
- VM reports: Arch BBS, Fedora Discussion, KDE Discuss.
- lookupper.com (home, FAQ, pricing) as the reference.

### Tertiary (LOW)
- Spectacle latency numbers, direct ScreenShot2 use, Xwayland lazy start, VM clipboard-agent interference.

---
*Research completed: 2026-10-23*
*Ready for roadmap: yes*
