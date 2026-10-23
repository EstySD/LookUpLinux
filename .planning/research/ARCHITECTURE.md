# Architecture Research

**Domain:** Hotkey -> OCR word under cursor (or selected text) -> EN->RU overlay -> SQLite counter, desktop tool for Arch Linux + KDE Plasma 6 (Wayland primary, X11 supported)
**Researched:** 2026-10-23
**Confidence:** MEDIUM-HIGH. KWin/spectacle/gtx facts were verified against current upstream source and a live call. Latency numbers are estimates (not measured). Items in "Verify in the Arch VM" are the known unknowns.

## Verdict (read this first)

| Question | Recommendation |
|----------|----------------|
| One-shot vs daemon | **One-shot** process per hotkey. Code `run_once()` so a daemon is a ~25-line wrapper later. Upgrade only when the built-in stage timing shows Python+Qt start-up is >= 25% of a total that exceeds 2 s (see "Upgrade trigger"). |
| Compositor glue | **One seam: a tiny generated KWin script** loaded over D-Bus. It returns cursor position + output geometry, and later moves the overlay window. Works in both Wayland and X11 sessions, so there is no per-session branching and no `QT_QPA_PLATFORM=xcb` hack. |
| Capture | `spectacle -b -n -m -o <tmpfile>` (current monitor only, no pointer, no notification). Stored in `$XDG_RUNTIME_DIR` (tmpfs), deleted immediately. |
| HiDPI / multi-monitor | Do not model scale factors. **Derive the scale from data**: `sx = image_width / output_logical_width`. Works for fractional scale, negative offsets, and mixed-DPI setups. |
| Selection vs OCR | Read PRIMARY, then use it only if it is short, word-like, and **different from the last PRIMARY value we consumed** (hash kept in a `meta` table in the same SQLite file). Otherwise OCR. |
| Layout | **One file** `lookup.py` (~300 lines, pure core on top, Qt shell below, Qt imported lazily), plus `test_lookup.py`, `install.sh`, `README.md`. Do not split into packages. |
| DB | `$XDG_DATA_HOME/lookup/lookup.db` (default `~/.local/share/lookup/lookup.db`), stdlib `sqlite3`. Doubles as a translation cache (DB hit skips the network). |

## Standard Architecture

### System Overview

```
 KDE Shortcut (Meta+Shift+D) --exec--> `lookup`            (one short-lived process)
                                           |
 +-----------------------------------------+------------------------------------------+
 | t=0  PARALLEL START                                                                |
 |   (a) Popen spectacle -b -n -m -o $XDG_RUNTIME_DIR/lookup-<pid>.png   [dominant]   |
 |   (b) import PySide6, start QGuiApplication, register D-Bus name org.lookup.p<pid> |
 |   (c) read PRIMARY (wl-paste --primary | xclip -o -selection primary)  [~20 ms]    |
 +-----------------------------------------+------------------------------------------+
                                           |
              +----------------------------v-----------------------------+
              | KWIN SEAM (generated JS, loaded via org.kde.kwin.Scripting) |
              |  probe:  workspace.cursorPos + screenAt(cursor).geometry    |
              |          + output name + activeScreen name -> callDBus      |
              |  place:  find window "lookup-overlay", set frameGeometry,   |
              |          keepAbove, activate -> callDBus                    |
              +----------------------------+-----------------------------+
                                           |
      mode = decide(selection, last_consumed)    selection -> text            OCR -> text
                                           |                  |                    |
                                           |        crop+upscale+(invert) QImage   |
                                           |                  |         tesseract stdin stdout tsv
                                           |                  |         pick_word(tsv, cursor_in_crop)
                                           +------------------+--------------------+
                                                              |
                                              normalise(text) -> key or None
                                                              |
                                      DB lookup (hit: skip net) / gtx translate (miss)
                                                              |
                                          upsert(word, translation, variants)  -> SQLite
                                                              |
                                      Overlay (QWidget, frameless) -> KWin place -> show
                                                              |
                                          click | Esc | focus-out | 8 s timeout -> exit
```

### Component Responsibilities

| Component | Responsibility | Pure? | Implementation |
|-----------|----------------|-------|----------------|
| `trigger` | Receives hotkey; single process entry (`lookup`, `lookup words`, `lookup --timing`) | no | `main()` + `sys.argv` switch, no argparse needed |
| `kwin` (seam) | Cursor+geometry probe, overlay placement; owns D-Bus service for callbacks | no | `QDBusConnection` + 2 JS string templates; ~45 lines |
| `capture` | Run spectacle, return `QImage`, delete file | no | `subprocess.Popen` started at t=0, `wait()` later |
| `geometry` | Cursor (logical) -> image pixels; crop rect; overlay position clamp | **yes** | 3 small functions on tuples |
| `ocr` | Prepare crop (upscale, optional invert), run tesseract, return TSV text | no (subprocess) | `subprocess.run(["tesseract","stdin","stdout","-l","eng","--psm","6","tsv"], input=png)` |
| `pick` | TSV -> words with boxes -> best word for cursor | **yes** | `parse_tsv()`, `pick_word()` |
| `normalise` | Strip OCR punctuation, quotes, case; validate "looks English" | **yes** | one function, regex |
| `selection` | Read PRIMARY, decide selection-vs-OCR | read: no; decide: **yes** | `read_primary()` + `choose_mode()` |
| `translate` | gtx call + parse | call: no; parse: **yes** | `urllib.request`, `parse_gtx(json)` |
| `store` | Schema, upsert, cache lookup, meta k/v, list query | **yes** (with `:memory:`) | `sqlite3`, `ON CONFLICT DO UPDATE` |
| `overlay` | Frameless widget: word, translation, variants, count; dismissal rules | no | `QWidget` + `QLabel` |
| `words window` | Table of saved words sorted by count; refresh on focus | no | `QTableWidget` filled from `store.list_words()` |

## Recommended Project Structure

```
LookUpLinux/
├── lookup.py          # whole app (~300 lines). Pure functions first, Qt/subprocess shell below.
├── test_lookup.py     # stdlib unittest; no desktop, no PySide6 import needed
├── fixtures/          # tsv samples, gtx json samples, 5-10 tiny crop PNGs + expected word
├── install.sh         # pacman deps, install to ~/.local/bin, .desktop files, prints shortcut steps
├── lookup.desktop     # "Lookup Words" launcher (Exec=lookup words) -> shows up in app menu
└── README.md          # Russian install + shortcut instructions for the friend
```

### Structure Rationale

- **One file:** ~300 lines, one author, one reader. Modules would add import-time cost, install-path fiddling (`PYTHONPATH`), and navigation overhead for zero benefit.
- **Pure core above the shell:** the top half of `lookup.py` imports only stdlib (`sqlite3, json, re, hashlib, urllib, subprocess, os`). `import lookup` in tests therefore never touches PySide6 or a display. Qt is imported **inside** `run_once()` / `show_words()`.
- **Split trigger:** split only when the file passes ~450 lines or the words window grows features. First cut would be `ui.py` (overlay + words window). Do not split earlier.
- **Install target:** `~/.local/bin/lookup` (a copy or symlink of `lookup.py` with shebang `#!/usr/bin/env python3`, `chmod +x`). `~/.local/bin` is on PATH in a default KDE session, which matters because the KDE shortcut exec environment is the session environment. Use the absolute path in the shortcut anyway.
- **DB location:** `Path(os.environ.get("XDG_DATA_HOME", "~/.local/share")).expanduser() / "lookup" / "lookup.db"`. Allow `LOOKUP_DB` env override (tests, debugging).

## Architectural Patterns

### Pattern 1: One-shot process, overlapped stages

**What:** Kick off the slowest independent thing (spectacle) first, do imports and the KWin probe while it runs, then join.
**When to use:** Always here; this is what lets one-shot stay inside budget.
**Trade-offs:** Cursor is sampled ~0.1-0.4 s before the screenshot completes. Users hold the cursor still on the word, so this is acceptable. If it proves wrong, sample the cursor a second time right after capture finishes and prefer that value.

```python
def run_once():
    shot = Path(os.environ["XDG_RUNTIME_DIR"]) / f"lookup-{os.getpid()}.png"
    cap = subprocess.Popen(["spectacle", "-b", "-n", "-m", "-o", str(shot)])   # t=0
    sel = read_primary()                                                       # ~20 ms
    from PySide6.QtGui import QGuiApplication, QImage                          # overlaps with capture
    ...
    probe = kwin_probe()            # dict: cx,cy,gx,gy,gw,gh,out,active
    mode, text = choose_mode(sel, db.get_meta("last_sel"))
    if mode == "ocr":
        cap.wait(); img = QImage(str(shot)); shot.unlink(missing_ok=True)
        text = ocr_word(img, probe)
```

### Pattern 2: A single compositor-facing seam (generated KWin script)

**What:** Wayland deliberately hides global cursor position and window placement from clients. KWin scripts can do both and report back with `callDBus`. This is the same mechanism kdotool uses (`org.kde.kwin.Scripting.loadScript`, then `/Scripting/Script<id>` `org.kde.kwin.Script.run`, results via `callDBus` to a receiver service the caller registers). Our process registers `org.lookup.p<pid>` (unique per process, so no singleton races) with one exported slot per message.
**When to use:** For anything that needs compositor-global state. Everything else stays in plain Qt.
**Trade-offs:** Needs `PySide6.QtDBus`. If receiving D-Bus in Python proves flaky in the VM, fallbacks in order: (1) shell out to `kdotool` (AUR only, not in `extra`), (2) read the KWin script's `print()` from the journal (slow, noisy). Do not choose them up front.

```python
PROBE_JS = """
const p = workspace.cursorPos, o = workspace.screenAt(p), g = o.geometry;
callDBus("%(svc)s", "/", "", "probe", JSON.stringify({cx:p.x, cy:p.y, gx:g.x, gy:g.y,
         gw:g.width, gh:g.height, out:o.name, active:workspace.activeScreen.name}));
"""
PLACE_JS = """
for (const w of workspace.windowList()) if (w.caption === "lookup-overlay") {
  w.frameGeometry = {x:%(x)d, y:%(y)d, width:w.width, height:w.height};
  w.keepAbove = true; workspace.activeWindow = w;
}
callDBus("%(svc)s", "/", "", "placed", "");
"""
# Python: write JS to $XDG_RUNTIME_DIR, loadScript(path, name) -> id, call /Scripting/Script<id> run,
# wait for the slot (timeout 1 s), unloadScript(name) in finally.
```

KWin API facts verified in upstream source: `workspace.cursorPos`, `workspace.screenAt(pos)`, `workspace.activeScreen`, `workspace.windowList()`, `workspace.activeWindow` (writable), `Window.frameGeometry` (writable), `Window.keepAbove` (writable), `Window.caption`, output `geometry` / `devicePixelRatio` / `name`.

### Pattern 3: Derive the pixel scale from the data, capture one monitor only

**What:** Capture only the monitor under the cursor. `spectacle -m` maps to KWin `CaptureActiveScreen`, i.e. `workspace.activeOutput()`; KWin updates the active output on every pointer motion (and on window activation), so in practice it is the cursor's monitor. The probe returns both the cursor's output name and the active output name; if they differ, abort with a short overlay message ("Move the mouse slightly and retry") instead of OCR-ing the wrong monitor.
Then compute scale per axis from the image itself:

```python
def cursor_to_image(cx, cy, gx, gy, gw, gh, img_w, img_h):
    sx, sy = img_w / gw, img_h / gh          # 1.0, 1.5, 1.25, 1.333..., whatever
    return (cx - gx) * sx, (cy - gy) * sy, sx, sy
```

No `devicePixelRatio`, no `QT_SCALE_FACTOR`, no per-monitor tables. Negative `gx`/`gy` (monitor left of/above the primary) are handled because `gx,gy` are subtracted.
**Sanity check:** `abs(sx - sy) / sx < 0.02`, else abort (geometry/image mismatch means we captured something unexpected).

Worked cases (use as unit tests):

| Layout | Cursor (logical) | Output geometry (logical) | Image | Result (px) |
|--------|------------------|---------------------------|-------|-------------|
| 1 monitor, scale 1 | (400, 300) | (0,0,1920,1080) | 1920x1080 | (400, 300) |
| Laptop 2880x1800 @1.5 | (1000, 600) | (0,0,1920,1200) | 2880x1800 | (1500, 900) |
| Left external, negative offset | (-2000, 300) | (-2560,0,2560,1440) | 2560x1440 | (560, 300) |
| 2560x1600 @1.25 | (1000, 640) | (0,0,2048,1280) | 2560x1600 | (1250, 800) |

### Pattern 4: Selection decided by consumed-state memory

**What:** The PRIMARY selection stays set until something else is selected, so "there is a selection" cannot mean "the user just selected". Store `sha1(last_primary_we_consumed)` in `meta(k,v)`. Use selection only if it differs from that.

| PRIMARY now | vs. stored hash | Looks like a lookup target (<= 4 words, <= 60 chars, has a letter, no newline) | Mode | Then |
|-------------|-----------------|---------------------------------|------|------|
| empty / unreadable | - | - | OCR | - |
| text | same | - | OCR (stale) | keep hash |
| text | different | no (long paragraph, code, path) | OCR | do **not** store hash (so it stays "new" if the user then shortens it) |
| text | different | yes | SELECTION | store new hash |

Known residual: user selects "foo" in app A, later hovers another word and presses the hotkey without selecting anything: the old "foo" is still new-to-us only if it was never consumed, which is correct (the user did select it). If it was consumed, it is stale and OCR runs. The one failing case is deliberate re-lookup of the same still-selected text; OCR then reads the highlighted word at the cursor, which normally returns the same word. Accept it.
**Rejected alternative:** clearing PRIMARY after use (`wl-copy --primary --clear`). It is stateless, but destroys the user's middle-click paste buffer, may drop highlight in some apps, and has no clean X11 equivalent.
**Reading PRIMARY:** Wayland: `wl-paste --primary --no-newline` with a 0.5 s timeout (works from a non-focused process through KWin's data-control protocol; KWin implements it, `wl-clipboard` 2.3.0 in `extra` speaks both `wlr-` and `ext-data-control`). X11: `xclip -o -selection primary`. Choose by `XDG_SESSION_TYPE`. Do **not** use Qt's `QClipboard` Selection mode for this: a process with no focused window cannot read it on native Wayland, and an XWayland client does not reliably see Wayland-side selections.

### Pattern 5: Pure core, impure shell, DB as cache

**What:** Every decision (word pick, normalise, parse, mode, geometry, placement clamp, upsert) is a function of plain data. Process calls (spectacle, tesseract, wl-paste, D-Bus, urllib, Qt) are thin and listed in one place.
**Cache rule:** after `normalise`, `SELECT translation, variants FROM words WHERE word=?`. Hit: bump `count`, skip the network (saves 150-500 ms and works offline). Miss: call gtx, then upsert. Failed translation: show the error and **do not** write the row.

```sql
CREATE TABLE IF NOT EXISTS words(
  word TEXT PRIMARY KEY, translation TEXT NOT NULL, variants TEXT,
  count INTEGER NOT NULL DEFAULT 1, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);

INSERT INTO words(word,translation,variants,first_seen,last_seen) VALUES(?,?,?,?,?)
ON CONFLICT(word) DO UPDATE SET count=count+1, last_seen=excluded.last_seen,
  translation=excluded.translation, variants=excluded.variants;
```

Open with `sqlite3.connect(path, timeout=5)`; the words window (second process) and the hotkey process can overlap, and the default rollback journal plus a 5 s timeout is enough at this write rate.

## Data Flow

### Pipeline (OCR mode)

```
cursor (logical, KWin) ----+
output geometry (logical) -+--> cursor_to_image() --> (px,py,sx,sy)
screenshot (physical px) --+            |
                                        v
        crop_rect(px,py, w=600*sx, h=100*sx) clamped to image
                                        |
         QImage.copy -> upscale x2 (SmoothTransformation) -> invert if mean luma < 128
                                        |
         tesseract stdin stdout -l eng --psm 6 tsv     (OMP_THREAD_LIMIT=1)
                                        |
         parse_tsv -> [Word(text,left,top,w,h,conf)]  (level 5, conf >= 0, text.strip())
                                        |
         cursor_in_crop = ((px - crop_x) * up, (py - crop_y) * up)
         pick_word(): box contains point -> that word
                      else min point-to-rect distance, accept if <= 0.75 * box height
                      ties: smaller horizontal distance
                                        |
         normalise(): NFKC, curly quotes -> ', strip leading/trailing non-letters,
                      strip trailing "'s", casefold; require [a-z] and len >= 2,
                      allow inner ' and -; reject if it has Cyrillic (EN->RU only)
                                        |
         store.get() -> hit: count++ ; miss: translate() -> store.upsert()
                                        |
         overlay.show(word, translation, variants, count)
```

### Selection mode

Skips capture and OCR. `spectacle` was started at t=0 speculatively; if PRIMARY is already valid at step (c), kill it immediately (`cap.terminate()`) and delete the file. Alternatively read PRIMARY **before** starting spectacle (20 ms) and only start it when needed; this is simpler and costs almost nothing, so prefer it.

### Latency budget (estimates, to be replaced by `lookup --timing` numbers)

| Stage | Estimate | Notes |
|-------|----------|-------|
| Python start + `PySide6.QtGui/QtWidgets/QtDBus` import | 150-350 ms (first run after boot up to ~1 s) | Runs while spectacle captures |
| KWin probe (load, run, callback, unload) | 30-80 ms | |
| `spectacle -b` start + capture + PNG write | 300-800 ms | Critical path; a daemon cannot remove it |
| Crop / upscale / invert | < 30 ms | |
| tesseract on ~1200x200 px | 150-400 ms | Includes model load; cap threads with `OMP_THREAD_LIMIT=1` |
| DB hit (skips network) / gtx call | 5 ms / 150-500 ms | `urllib`, 3 s timeout |
| Overlay build + KWin place + show | 50-100 ms | Opacity 0 until `placed`, then 1 |
| **Critical path total** | **~0.8-1.8 s** | max(import+probe, spectacle) + OCR + net + overlay |

Instrumentation is part of the design, not a later nicety: `LOOKUP_TIMING=1` (or `--timing`) prints per-stage milliseconds to stderr. About 8 lines of `time.perf_counter()` deltas.

### Overlay placement

```
size = overlay.sizeHint()                          # after setText + adjustSize, before show
(x,y) = place(cursor, output_geom, size, offset=(12,16), margin=8)
         # default: right/below cursor; if it overflows right/bottom, flip to left/above; clamp to geom
overlay.setWindowTitle("lookup-overlay"); overlay.setWindowOpacity(0); overlay.show()
kwin.place(x, y)          # sets frameGeometry in logical global coords, keepAbove, activates
on "placed" (or 300 ms fallback): overlay.setWindowOpacity(1)
```

Because `cursorPos`, output geometry and `frameGeometry` are all KWin logical global coordinates, placement needs no scale math and works for native Wayland Qt (no XWayland). The XWayland `move()` route was rejected: X11 coordinates for XWayland clients depend on the "Legacy applications (X11)" scaling mode in Plasma settings, which is a per-user setting you cannot assume.

### Key Data Flows

1. **Selection path:** PRIMARY -> `choose_mode` -> normalise -> DB/translate -> overlay. No screenshot.
2. **OCR path:** KWin probe + spectacle PNG -> crop -> tesseract TSV -> pick -> normalise -> DB/translate -> overlay.
3. **Persistence:** only `store` touches SQLite; the words window reads it via `list_words()` ordered by `count DESC, last_seen DESC`.

## What Can Be Tested Without a Desktop

| Unit | Input -> output | Notes |
|------|-----------------|-------|
| `parse_tsv`, `pick_word` | TSV fixture + cursor point -> word | Cases: cursor inside box, in gap between words, above/below line, far from any word -> None, low-conf junk, empty TSV, header-only TSV |
| `normalise` | `"“Hello,”"`, `"don’t."`, `"(running)"`, `"word-"`, `"co-operate"`, `"1234"`, `"привет"`, `"|"`, `"It's"` -> key or None | Pin the rules; this is where most real-world bugs surface |
| `parse_gtx` | Recorded JSON (word with dictionary block, word without, phrase, empty/odd shape) -> `(main, variants)` | Format verified live: `[0]` = `[[translation, original, ...]]`, `[1]` = `[[pos, [translations...], ...]]` present with `dt=bd`. Unexpected shape -> raise one `TranslateError`. |
| `store` | `:memory:` DB: insert, repeat -> count 2 and `last_seen` moved, `first_seen` unchanged, cache hit, `list_words` order, meta get/set | |
| `cursor_to_image`, `crop_rect`, `place` | Table above (fractional, negative offset, edge of screen, overlay flip) | Pure arithmetic |
| `choose_mode` | Truth table in Pattern 4 | |
| `looks_like_lookup` | `"word"`, `"two words"`, 3-line paragraph, URL, code | |
| OCR end-to-end | `fixtures/*.png` crop + cursor point -> word | Needs only the `tesseract` binary; `skipUnless(shutil.which("tesseract"))`. Run Qt-free by feeding PNG bytes straight to `ocr_tsv()`. |
| Qt image prep | `QImage` upscale/invert | Works headless with `QT_QPA_PLATFORM=offscreen` (optional) |

**Needs the real desktop (manual VM checklist, not automated):** KWin probe/D-Bus callback, spectacle capture, overlay placement/activation/dismissal, PRIMARY reading, KDE shortcut. Add `lookup --debug` that saves the crop PNG and prints the TSV, picked word and probe dict, so any wrong-word report from the friend can be reproduced by sending one file (the screenshot is otherwise never kept).

## Suggested Build Order

Each step is runnable on its own; earlier steps are testable without a desktop.

1. **Pure core + tests** (`normalise`, `parse_tsv`, `pick_word`, `parse_gtx`, geometry functions, `store`, `choose_mode`). No Qt. This is ~60% of the logic and the highest-value test surface.
2. **CLI pipeline on fixtures:** `lookup --image fixtures/x.png --at 400,300` prints the word and translation. Proves OCR settings (`--psm`, upscale, invert) and gtx on real text before any Wayland work. Include the stage-timing hook here.
3. **Desktop seam, spike first:** KWin probe + spectacle capture on the Arch VM, saving the crop. Confirms D-Bus receive from PySide6, `-m` selects the cursor's monitor, geometry/scale math on the VM's scale settings. Highest technical risk; do it early, behind the pure core.
4. **Overlay + KWin placement:** frameless widget, opacity-until-placed, dismissal rules, error states ("no word", "offline"). Wire the full hotkey path; DB write happens here.
5. **Selection mode:** PRIMARY reader (Wayland + X11) and the stale-selection rule.
6. **Words window:** `lookup words`, `.desktop` launcher, refresh on focus.
7. **install.sh + README:** pacman deps, `~/.local/bin`, KDE shortcut instructions, X11 smoke test.

Roadmap implication: steps 1-2 can be one phase; step 3 deserves its own phase or spike because it carries all the platform risk; 4-5 are one phase; 6-7 are packaging.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Personal use (thousands of words) | Single SQLite file, no index beyond the primary key. |
| Slow machine / lag complaints | Upgrade trigger below. |
| Many words (>50k) | Add index on `count`; irrelevant in practice. |

### Upgrade trigger (one-shot -> resident daemon)

Move to a daemon only if **both** hold: (1) `--timing` shows p50 hotkey->overlay above ~2 s on the friend's real machine, and (2) Python+Qt import/start-up is >= 25% of that (>= ~500 ms). A daemon removes only import and warm-up cost; spectacle (the biggest stage), tesseract and the network call stay. If spectacle dominates, a daemon is the wrong fix (the real alternative is a persistent ScreenCast/PipeWire stream, which is a much bigger step and out of scope).
How: `run_once(ctx)` already has no process-level state. Add `lookup --daemon` that registers `org.lookup.Daemon` with a `Trigger()` slot calling `run_once`, start it via `~/.config/autostart/lookup.desktop`, and change the KDE shortcut command to `dbus-send --session --dest=org.lookup.Daemon / org.lookup.Trigger` (no Python start per press). The per-process service name becomes the fixed one; the KWin script templates take the name as a parameter already.

## Anti-Patterns

### Anti-Pattern 1: Overlay positioned with Qt `move()` under XWayland

**What people do:** Force `QT_QPA_PLATFORM=xcb` and call `move(x, y)` with coordinates from `QCursor.pos()`.
**Why it's wrong:** `QCursor.pos()` is stale outside XWayland-owned windows; X11 coordinates also change meaning with Plasma's per-user "Legacy applications (X11)" scaling mode, and fractional/mixed-DPI setups break differently on each monitor.
**Do this instead:** Cursor and placement both go through the KWin seam in logical global coordinates.

### Anti-Pattern 2: Full-desktop screenshot plus manual stitching math

**What people do:** `spectacle -f`, then reason about a combined image across monitors with different scales.
**Why it's wrong:** The combined image's pixel space does not map linearly to logical coordinates when scales differ; negative origins and fractional rounding make this the largest source of "OCR reads the wrong place" bugs.
**Do this instead:** `-m`, one monitor, scale derived from `image_size / output_size`.

### Anti-Pattern 3: Treating "PRIMARY is non-empty" as "user selected text"

**What people do:** Always prefer selection when present.
**Why it's wrong:** Stale selection hijacks every later lookup.
**Do this instead:** Consumed-hash memory in `meta` (Pattern 4).

### Anti-Pattern 4: Module/class hierarchy for 300 lines

**What people do:** `ocr/`, `translate/`, `ui/`, provider interfaces and base classes.
**Why it's wrong:** Violates the ponytail constraint, and the one place that really needs isolation (the unofficial gtx endpoint) is isolated by being a single function that returns `(main, variants)` or raises `TranslateError`.
**Do this instead:** Flat functions in one file; split only at the trigger noted above.

### Anti-Pattern 5: Keeping screenshots or logging OCR text

**What people do:** Leave the PNG in `/tmp` or Pictures, log everything for debugging.
**Why it's wrong:** Violates the stated privacy constraint (only the recognised word leaves the machine; screenshots are not kept).
**Do this instead:** tmpfs path in `$XDG_RUNTIME_DIR`, `unlink` in a `finally`; the crop is saved only under explicit `--debug`.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Google gtx | `GET https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ru&dt=t&dt=bd&q=<word>`, `urllib`, set a normal `User-Agent`, 3 s timeout | Verified working on 2026-10-23. Unofficial, can break or rate-limit; only the normalised word is sent. Cache in DB so repeated words never hit it. |
| spectacle 6.8.1 (`extra`) | `-b -n -m -o <file>`; pointer is excluded unless `-p` is given (verified in source: background mode uses only CLI flags) | Authorised for KWin `ScreenShot2`, which is why we shell out instead of calling KWin directly. With `-n`, exit is immediate after save. |
| KWin scripting | `org.kde.KWin /Scripting` `org.kde.kwin.Scripting.loadScript(path, name)`, `/Scripting/Script<id>` `org.kde.kwin.Script.run`, `unloadScript(name)` | Use unique script names per process; always unload in `finally`. |
| tesseract 5.5.3 + `tesseract-data-eng` (`extra`) | `tesseract stdin stdout -l eng --psm 6 tsv` | `--psm 6` first guess; try `11` (sparse) if UI text performs better on fixtures. White-on-dark text needs the invert step. |
| wl-clipboard 2.3.0 / xclip (`extra`) | `wl-paste --primary --no-newline` / `xclip -o -selection primary` | |
| KDE global shortcut | User adds Command shortcut in System Settings -> Shortcuts (documented in README) | Scripted creation via `kglobalshortcutsrc` is unreliable on Plasma 6 (changes often need relogin); do not automate in MVP. |

Arch packages: `pyside6` (extra, 6.12.0; there is no `python-pyside6`), `tesseract`, `tesseract-data-eng`, `spectacle`, `wl-clipboard`; optional `xclip` for X11 sessions. All from `extra`; no AUR, no pip.

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| shell <-> pure core | Plain tuples / dataclasses | Core never imports Qt or calls subprocess |
| process <-> KWin | D-Bus (script load/run, `callDBus` back to `org.lookup.p<pid>`) | Timeout 1 s -> overlay shows "cannot read cursor" error |
| hotkey process <-> words window | SQLite file only | Words window refreshes on focus-in |
| hotkey process <-> previous overlay | `$XDG_RUNTIME_DIR/lookup.pid`: new run SIGTERMs the old pid first | Prevents the old overlay appearing in the new screenshot; if a ghost still shows, add `-d 100` to spectacle |

## Verify in the Arch VM (known unknowns, ordered by risk)

1. PySide6 can receive `callDBus` from the KWin script (`registerService` + `registerObject(..., ExportAllSlots)` with `@Slot(str)`; the official PySide6 pingpong example uses this pattern). Fallbacks in Pattern 2.
2. `wl-paste --primary` actually returns a mouse-selected word from a non-focused process on the VM's Plasma version, and middle-click paste setting does not disable PRIMARY.
3. `spectacle -m` picks the cursor's monitor in a two-monitor VM (use the name comparison in the probe to detect mismatch).
4. A KWin-activated frameless Qt window receives Esc and fires focus-out reliably (the activation line in `PLACE_JS`).
5. Overlay is not visible in the screenshot taken by a rapid second hotkey press.
6. Real stage timings (replace the estimates above).
7. X11 session: the same KWin script path works; if not, `QCursor.pos()` plus `move()` is a trivial fallback there.

## Sources

- KWin scripting API, upstream source (HIGH): `src/scripting/workspace_wrapper.h` (`cursorPos`, `screenAt`, `windowList`, `activeWindow`), `src/window.h` (`frameGeometry` writable, `keepAbove`, `caption`), `src/core/output.h` (`geometry`, `devicePixelRatio`, `name`), https://github.com/KDE/kwin
- KWin active output follows pointer motion and window activation (HIGH): `src/pointer_input.cpp`, `src/activation.cpp`, and `ScreenShotDBusInterface2::CaptureActiveScreen` uses `workspace()->activeOutput()` in `src/plugins/screenshot/screenshotdbusinterface2.cpp`
- KWin data-control protocol implemented (`datacontroldevicemanager_v1`, currently `ext_data_control_manager_v1`; v6.3 used `wlr-data-control`) (HIGH for presence, MEDIUM for primary selection behaviour on Plasma 6.8 until tested): https://github.com/KDE/kwin/tree/master/src/wayland
- kdotool, KWin-script + D-Bus callback mechanism and flow (HIGH): https://github.com/jinliu/kdotool (`src/main.rs`, `src/templates.rs`); AUR packages `kdotool` 0.3.0 and `kdotool-bin`, not in `extra`
- KDE discussion confirming a KWin script is the only practical public way to read the pointer on Wayland (MEDIUM): https://discuss.kde.org/t/is-there-a-better-way-to-obtain-the-mouse-cursor-location/20559
- Spectacle CLI flags and background-mode pointer handling (HIGH): https://github.com/KDE/spectacle (`src/CommandLineOptions.h`, `src/SpectacleCore.cpp`, `src/Platforms/ImagePlatformKWin.cpp`)
- wl-clipboard 2.3.0 adds `ext-data-control-v1` (HIGH): https://github.com/bugaevc/wl-clipboard/releases
- Qt for Python D-Bus pingpong example (receiving calls with `registerObject` and `ExportAllSlots`) (HIGH): https://doc.qt.io/qtforpython-6/examples/example_dbus_pingpong.html
- XWayland scaling modes in Plasma (MEDIUM; default for Plasma 6 not confirmed): https://discuss.kde.org/t/scaling-improvements-for-x11-applications/47791
- Custom shortcut scripting on Plasma 6 is unreliable (MEDIUM): https://discuss.kde.org/t/plasma-6-method-to-refresh-kglobalaccel-shortcuts/17995
- Package names and versions checked against the Arch package API on 2026-10-23 (HIGH): pyside6 6.12.0, tesseract 5.5.3, tesseract-data-eng 4.1.0, spectacle 6.8.1, wl-clipboard 2.3.0, xclip 0.13
- gtx response shape verified with a live request on 2026-10-23 (HIGH, but unofficial endpoint)

---
*Architecture research for: LookUp-style OCR translate overlay, Arch + KDE Plasma 6*
*Researched: 2026-10-23*
