# Pitfalls Research

**Domain:** Linux (Arch + KDE Plasma 6, Wayland primary / X11 secondary) "hotkey -> OCR word under cursor or PRIMARY selection -> EN->RU overlay -> SQLite counter" desktop tool. Python + Qt (via XWayland) + tesseract + spectacle + KWin scripting + unofficial Google translate endpoint. Tested in a VM.
**Researched:** 2026-10-23
**Confidence:** MEDIUM overall. The translation-endpoint breakage, Spectacle/KWin screenshot authorization, `wl-paste` hang, Qt/Wayland cursor and popup rules, and the SQLite WAL rules are backed by primary sources (HIGH). Items marked [MEDIUM] or [LOW] are inferred from forum threads, partial sources, or domain knowledge that I could not confirm against an official page. Every [LOW] item is a spike to run, not a fact to build on.

Confidence tags: [HIGH] = official docs or issue tracker read directly. [MEDIUM] = one community source, or an inference from solid sources. [LOW] = unverified / from memory, must be validated in a spike.

Method note: the GSD `research-plan` / `classify-confidence` seam was not run (WebSearch/WebFetch were used directly), so tiers above are my own assessment, not seam output.

---

## Critical Pitfalls

### Pitfall 1: The "free Google gtx endpoint" is being actively blocked right now (Sept 2026)

**What goes wrong:** `translate.googleapis.com/translate_a/single?client=gtx` starts returning HTTP 429 with an HTML "Sorry... automated queries" page instead of JSON. The tool shows "translation error" for every word, even at 1 lookup per minute. This is not a theoretical risk: it is happening in this exact ecosystem this month.
- eeeXun/gtt #43 (Arch, AUR package): `gtx` -> 429, `at` -> 200, `dict-chrome-ex` -> 200, `webapp`/`t` -> 403. Reported ~2026-09-14, reproduced on two unrelated Czech ISPs (so not simply per-IP). Fixed upstream 2026-09-24 by switching the client value.
- Mega-Gorilla/livecap-cli #442: `gtx` blocked, the HTML `/m` endpoint hits reCAPTCHA, `client=at` worked on 09-15 and then returned 429 from the same IP on 09-16, so they moved to `dict-chrome-ex` and decided on the paid official API as the permanent fix. Also saw `curl` get 200 while Python `requests` got 429 on the same `gtx` URL (client fingerprint matters), and adding browser-like headers did NOT help.
- noctalia-dev/official-plugins #64: the app treated the 429 HTML as success, failed JSON parsing and showed a generic error card.
- Asura7170/easydict_win32 PR #4: ~50% of queries got 429 at very low volume when sent as bare GETs; fell back to `translate-pa.googleapis.com/v1/translateHtml`.

**Why it happens:** The endpoint is an undocumented side door of Google's browser/extension clients. Google tunes bot detection on the `client=` identifier and request fingerprint with no notice. `PROJECT.md` already says "may break, isolate in one function" - that is correct but not sufficient; the failure mode (HTML body with 429, not an exception) and the *fallback policy* must be designed up front.

**How to avoid:**
1. One `translate(word) -> Result` function, strict contract: returns `ok(translations)` / `fail(reason in {blocked, timeout, parse, network})`. Never raises into the UI.
2. Treat any non-200, any non-JSON body, or any body containing `automated queries` / `<title>Sorry` (case-insensitive: livecap-cli's first marker missed the inline variant because it was case-sensitive) as `blocked`. Do NOT retry a `blocked` result in a loop. One immediate failure beats a 10 s hang.
3. Make the `client=` value a config setting with an ordered try-list (`gtx`, `dict-chrome-ex`, `at`) and remember the last working one in the state file. Be honest in docs that this is cat-and-mouse: `at` died on the same IP within a day in one report, and livecap-cli explicitly logged the concern that rotating to Google-app client IDs circumvents an intentional block. Do not add TLS-fingerprint spoofing or proxy rotation (scope creep, fragile, and ethically murky).
4. Add a second, independent provider behind the same interface before declaring the translation phase done. Candidates: the official Cloud Translation API with a user-supplied key (stable, paid beyond free tier, needs key setup for the friend), or another keyless service (MyMemory-style; unverified, [LOW] - spike before committing). Pick one; do not build a provider zoo.
5. Cache every successful translation in SQLite (word -> translations). Repeat lookups (the whole point of the counter) then cost zero network and survive an outage.
6. When translation fails, still save the lookup (word + count) with `translation = NULL` and show "translation unavailable - word saved"; back-fill later. The core value (word lands in the DB with a counter) must not depend on Google being up.
7. Version-stamp the parser: response is nested arrays (`data[0]` segments, `data[1]` dictionary entries via `dt=bd`, etc). Access with a safe-index helper (every level may be `None`/missing); a layout change should degrade to "main translation only", not crash.

**Warning signs:** works from the VM/dev machine but not on the friend's network (or vice versa); `curl` works but Python does not; error is "JSONDecodeError" (means you got HTML); intermittent 429s at 1 request per few minutes.

**Phase to address:** Translation phase, but start with a 1-hour *spike in the very first phase*: run the exact URL from Python from the VM and from the friend's network. This is the single most likely thing to make the MVP dead-on-arrival, and it is cheap to check first.

**Confidence:** HIGH that the block exists and is recent (4 independent trackers); MEDIUM on which `client=` values will survive (they are changing weekly).

---

### Pitfall 2: Believing Qt can give you the cursor position or place the overlay on Wayland

**What goes wrong:** `QCursor.pos()` returns stale/zero/last-seen-over-our-window coordinates; `window.move(x, y)` is ignored or lands wrong; overlay appears centered, at (0,0), or on another monitor.
- KDE's own Wayland porting notes: "On Wayland there is no global cursor position and QCursor::pos() only works by tracking the mouse move events"; popups without a transient parent cannot be placed correctly by the compositor. A 2019 KDE review concluded QCursor::pos() "is not reliable on Wayland and should not be used". [HIGH]
- KWin exposes `workspace.cursorPos` (+ `cursorPosChanged`) to KWin scripts (MR !3134) - the only supported way to read it. A KDE Discuss thread confirms KWin script is the practical read path; uinput/RemoteDesktop portal can only *move* the pointer. [HIGH]
- Getting the value *out of* the script is the hard part: `loadScript/run/stop` over D-Bus return only IDs/status; `console.error` goes to journald (slow, grows the journal, ~1 KB per call); kdotool avoids this by having the generated script call back into a D-Bus interface. [HIGH]
- Even under XWayland (`QT_QPA_PLATFORM=xcb`), the X server only knows the pointer while it is over an X11 surface, so `QCursor.pos()` in a one-shot xcb process launched from a shortcut is not trustworthy. [MEDIUM, inferred from Wayland architecture; verify in spike]

**Why it happens:** Wayland deliberately has no global pointer/geometry for clients. Developers test on X11 or with the pointer over their own window and it "works".

**How to avoid:**
- Write the project's own tiny KWin script (stdlib + `dbus`-capable path, see below) rather than depending on `kdotool`: **`kdotool` is not in the official Arch repos** (official package search: 0 results; AUR only), which breaks the "pacman-only, no extras" install constraint, and kdotool generates/loads/deletes a script per call anyway. [HIGH for not-in-extra as of 2026-10-23]
- Pattern: Python process registers a one-shot D-Bus service name, calls `org.kde.KWin /Scripting loadScript`, script does `callDBus(myservice, ..., workspace.cursorPos.x, workspace.cursorPos.y, <output geometry, scale>)`, then `unloadScript` in a `finally`. Use a unique script/plugin name per run (include PID) and unload stale ones at startup so a crashed run cannot leave a loaded script or block the next load. [MEDIUM on the stale-script detail]
- Have the same script return the **output (monitor) geometry and scale** under the cursor, not just x/y. Everything downstream (screenshot crop, overlay placement) needs the monitor.
- On X11 sessions (`XDG_SESSION_TYPE=x11`) use `QCursor.pos()` (or xdotool-free equivalent) directly; branch on session type once, in one module.
- **Measure** script round-trip latency in phase 1. No source gives a number for load+run+call-back; it is part of the 2 s budget.

**Warning signs:** overlay always at top-left or screen center; position correct only when cursor happens to be over the overlay's own previous location; works in X11 session, fails in Wayland.

**Phase to address:** Phase 1 (platform spike: cursor + monitor query) - before any OCR work. Everything depends on it.

---

### Pitfall 3: Overlay placement and focus under XWayland / fractional scaling (logical vs physical coordinate mismatch)

**What goes wrong:**
- `move()` on an XWayland (xcb) window: KWin treats it as a *managed* window and may apply its own placement policy instead of the requested position; or the requested coordinates are interpreted in different units than `workspace.cursorPos`.
- Under fractional scaling, XWayland behaviour depends on the per-user setting "Legacy applications (X11): Scaled by the system / Apply scaling themselves". "Scaled by the system" -> blurry window, logical-ish coordinates; "Apply scaling themselves" -> X11 sees physical pixels and clients must scale. KWin sets `Xft.dpi` but the X server keeps reporting 96 DPI. At fractional values (e.g. 137.5%) X11 text stays blurry. [HIGH on the existence and effect of the setting from KDE Discuss threads; MEDIUM on exact coordinate consequence]
- Result: overlay is offset by a factor of the scale (e.g. at 150% it lands 1.5x too far right/down), worse on a second monitor whose origin is also scaled.
- Focus: the overlay window needs the keyboard (requirement: close on Esc) but KWin's focus-stealing prevention may deny activation of a window launched by a global-shortcut command. KWin historically activated every newly-mapped toplevel; a "Focus Stealing Prevention" level system (Extreme/High/Medium/Low/None) is being introduced (MR !7952 still open when I read it) and a KDE dev said Plasma 6.5+ "Medium" should prevent focus stealing without much annoyance. Behaviour on the friend's Plasma version is therefore a moving target. [MEDIUM]

**Why it happens:** two coordinate systems (compositor logical coordinates, which is what `workspace.cursorPos` returns [MEDIUM - KWin docs do not say it explicitly], vs X11 pixel coordinates) plus a window manager that is allowed to disagree with the client about position and focus.

**How to avoid:**
- **Do not compute final overlay coordinates inside Qt.** Show the Qt window (frameless, `Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint`, `WA_X11NetWmWindowTypeTooltip`-style hints), then let the *KWin script* find it (by caption/`resourceClass`) and set its `frameGeometry` in logical coordinates - the same space as the cursor position. This sidesteps XWayland unit mismatch entirely and honours KWin's clamping. [MEDIUM - scripts can move any window incl. XWayland; confirm in spike]
- Clamp overlay rect to the output geometry returned by the script (right/bottom edges, second monitor with negative origin, panel areas).
- Place the overlay offset from the hotspot (e.g. +12/+18 px) so it never sits under the pointer; otherwise it steals the click meant for the app and flickers on re-hover.
- Install a **KWin window rule** for the overlay's window class (written by the install script) to set: no titlebar, keep above, skip taskbar/pager, and focus-stealing prevention = none/accept-focus. This is the supported way to make focus behaviour independent of the user's global level. [MEDIUM - rule keys from memory; verify names in System Settings > Window Rules]
- Define Esc as best-effort. If activation is denied, the overlay still closes on click and on timeout (requirement already lists both). Never design the only exit path around keyboard focus.
- Alternative to try in the spike: `Qt.ToolTip` windows on xcb are override-redirect (unmanaged): exact position, no WM interference, but no keyboard focus [LOW - verify under XWayland]. Pick whichever of the two passes "right place + closable" at 100%, 125%, 150%, 200%.
- Never set `QT_QPA_PLATFORM=xcb` globally (e.g. in the `.desktop` for the word-list window). Only the one-shot overlay process needs XWayland; the saved-words window should be native Wayland to avoid blur at fractional scale.
- Plasma 6 may start Xwayland lazily on the first X11 client [LOW - verify], so the first overlay after login can be slower than subsequent ones. Include a cold-start measurement.

**Warning signs:** correct at 100%, offset at 125/150%; correct on primary monitor, wrong on secondary; overlay appears under the pointer; overlay blurry; Esc does nothing but click works.

**Phase to address:** Overlay phase, with the scale matrix (100/125/150/200%, 2 monitors) as acceptance criteria. Unit-testable part: geometry clamp function.

---

### Pitfall 4: Screenshot crop coordinates do not match cursor coordinates (HiDPI, multi-monitor, scale)

**What goes wrong:** OCR runs on the wrong patch of the screen, or on the right patch at the wrong scale, so "the word under the cursor" is a neighbouring word or the crop is empty. PROJECT.md already flags this; the failure is usually at the *combination* of multi-monitor origin offset and fractional scale.

**Why it happens:** `spectacle -f` captures the whole virtual desktop (all monitors, native pixels); cursor is logical coordinates in global space. Naive `crop(cursor.x - w/2, ...)` ignores both the output origin and the scale. Rounding at 125%/150% adds off-by-one-pixel errors that matter little, but a wrong output origin or scale is off by hundreds of pixels.

**How to avoid:**
- Capture **only the monitor under the cursor** (`spectacle -b -m ...` "capture the current monitor") and crop in monitor-local space: `local = (cursor - output.origin)`, `scale = image_width_px / output.logical_width` (derive scale from the real image vs. the logical size from the KWin script; do not read `QT_SCALE_FACTOR` or Plasma config). This also shrinks the PNG to encode and decode.
- Keep this transform as a pure function (`cursor_to_image_xy(cursor, output_origin, output_logical_size, image_size)`) and unit-test it with fixture numbers for 1x/1.25x/1.5x/2x and a left-of-primary monitor (negative origin).
- If later optimizing: KWin's `org.kde.KWin.ScreenShot2.CaptureArea(x, y, w, h, options, pipe)` captures just a small rectangle, with option `native-resolution` choosing native pixels vs logical. Docs do not state the units of x/y/w/h [source gap]. Needs spike before use (see Pitfall 5).
- Crop is a *band* around the cursor, e.g. ~600 x 100 logical px, not a square; text is horizontal and the target word may be near the band edge, so keep margin and require the target word box to be fully inside the crop (else widen once).

**Warning signs:** works on one monitor, wrong word on the other; works at 100%, "nearby" word at 150%; OCR output has no words at all (crop off-screen or wrong region).

**Phase to address:** Capture phase (same phase as Pitfall 5). Pure-function tests in Phase 1.

---

### Pitfall 5: Spectacle as a "capture API": slowness, hangs, leaks, notifications, authorization

**What goes wrong (each is separate):**
1. **Latency eats the 2 s budget.** Reported Spectacle start-to-capture on Wayland is anecdotally 0.3-2 s (KDE Discuss, Fedora KDE 42 reporter: 1.5-2 s). A KWin commit says PNG encoding of Wayland screenshots is expensive and the main cause of Spectacle appearing with a huge delay after PrtScr. [MEDIUM - anecdotal numbers, mechanism confirmed]
2. **Leaves files / pollutes clipboard.** Background mode with no `-o` writes into the user's default screenshots folder; `-c` puts the *image* in the clipboard (and Klipper history) - both violate "screenshots are not saved" and `-c` can clobber the clipboard that the selection logic reads. Always pass `-o <tmpfile>`; never `-c`/`-C`. Use `-n` (no notification) or every lookup pops a KDE notification. [HIGH: man page]
3. **Hang/no-exit.** There was a bug where background-mode captures never quit (rect capture; fixed by MR !198, 2023, still "options applied to a running instance" afterwards). A NixOS report shows KWin "Did not receive a reply" timeouts even though the screenshot was taken. Exit status is not proof of a file. [MEDIUM]
4. **Running instance changes behaviour.** After MR !198, a `spectacle -b` command against an already-running Spectacle (GUI open, or `--dbus` instance) applies its options *there*. Test with Spectacle GUI open. [MEDIUM]
5. **Capture includes your own previous overlay.** If the old overlay is still visible when the hotkey fires again, the OCR reads your own translation text. [HIGH - design-level certainty]
6. **Authorization if you bypass Spectacle.** Calling KWin's `ScreenShot2` D-Bus API directly from Python is only allowed for apps that list `org.kde.KWin.ScreenShot2` in `X-KDE-DBUS-Restricted-Interfaces` in their `.desktop` file; reports show "not authorized" even with the file in place (maintainer reply: `Exec=` must be an absolute path, and for a Python script it must point at the interpreter), plus a thread where large-area captures intermittently hang reading the pipe. `KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1` exists but is a debugging tool, not an installable solution. [HIGH on rules; MEDIUM on how fragile it is]
7. **Portal route.** Do not use `xdg-desktop-portal` Screenshot for a hotkey tool: portal permission handling is app-id/Flatpak-database based (a stale Flatpak permission entry broke Flameshot after Plasma 6.4 in one Arch report; Spectacle avoids it by talking to KWin directly). Whether a portal prompt appears on every call could not be confirmed [source gap]; it is not worth finding out. [MEDIUM]

**How to avoid:**
- Phase-1 spike: time `spectacle -b -n -m -o /run/user/$UID/lookup-XXXX.png` end-to-end on the VM *and* real hardware; record cold vs warm.
- Always: temp file in `$XDG_RUNTIME_DIR` (tmpfs), mode 0600, `unlink` in `finally`; clean stale files at startup; subprocess with a hard `timeout=` (e.g. 3 s) and kill-on-timeout; success = file exists and size > 0, not return code.
- Kick off capture **and** the cursor query concurrently, and keep the very first entry script stdlib-only so it can fork Spectacle *before* importing PySide6 (see Pitfall 11).
- Acquire a single-instance lock; if a previous overlay is alive, close it (and wait for it to be gone) before capturing.
- Optional speed-up if budget is blown: `spectacle --dbus` as a systemd user unit (reported memory < 50 MiB, `Restart=always` required because it exits after each shot, bind to `plasma-workspace.target`, not `graphical-session.target`). That contradicts the "no daemon" decision, so treat it as a documented escape hatch, not default.
- Only escalate to a direct `ScreenShot2.CaptureArea` implementation if measured Spectacle latency fails the budget; it needs a generated `.desktop` file with an absolute `Exec`, `kbuildsycoca6`, and fallback to Spectacle on authorization failure.
- Reported "screen flash" could not be found in any source for Spectacle background mode. Only an old report of the taskbar entry/startup animation being captured (bug 376865). Check visually in the VM rather than assuming. [source gap]

**Warning signs:** Pictures folder fills with screenshots; KDE notifications on each lookup; Klipper history shows images; occasional lookups take 5+ s or never return; OCR text contains words from the previous translation.

**Phase to address:** Capture phase. Latency numbers feed the daemon-vs-one-shot decision documented in PROJECT.md.

---

### Pitfall 6: Reading PRIMARY selection: stale content, focus rules, and `wl-paste` hangs

**What goes wrong:**
1. **Hang.** `wl-paste` blocks until the selection owner sends the data; it has no timeout. Confirmed upstream: wl-clipboard #185 ("hangs when pasting text from a closed XWayland application"), maintainer: not a wl-clipboard bug, "blocking is normal", suggest running it async and `pkill` it. A hung `wl-paste` makes the hotkey do nothing. [HIGH]
2. **Qt can't be used instead.** On Wayland only the focused client can read the latest clipboard/selection; Crow Translate's `translateSelection` returned an empty window until they fixed it by showing/focusing the window first (MR !596; issue #324). Qt's Wayland plugin returns empty `Selection` data without a seat/offer. GoldenDict-ng v26.6.1 still had to fix "a crash on Wayland when accessing QClipboard::Selection (#2969)". So a one-shot, unfocused `QClipboard.text(QClipboard.Selection)` is both empty-prone and crash-prone. [HIGH]
3. **Staleness.** PRIMARY persists after the user deselects/clicks elsewhere in many apps; yesterday's selected word will shadow the OCR path forever ("selection exists, so skip OCR"). The requirement "selected text, **if it exists and is new**" needs a concrete definition. [HIGH for X11/Wayland PRIMARY semantics; the specific app list is not sourced]
4. **Empty vs error.** Empty/no selection makes `wl-paste` exit non-zero (AutoKey treats rc=1 as "nothing selected"). [MEDIUM]
5. **Protocol availability.** `wl-paste` reading without focus depends on the compositor offering a data-control protocol; KWin moved from `wlr-data-control` to stable `ext-data-control` in Plasma 6.4. Older Plasma 6 may behave differently. [MEDIUM]
6. **X11 session:** `wl-paste` does not exist there; need `xclip`/`xsel` with the same timeout discipline (`xsel` has its own timeout option).

**How to avoid:**
- Use `subprocess.run(["wl-paste", "--primary", "--no-newline", "--type", "text"], timeout=0.4, capture_output=True)`; on timeout, kill and treat as "no selection". Run in the same concurrent step as capture so it adds no latency. Put it in its own module with one function `get_primary(timeout) -> str | None`.
- Define "new": non-empty, <= ~40 chars and <= 3 words, not whitespace/URL/number-only, and **different from the last selection handled** (state file with hash + timestamp). If identical to the last handled one, fall through to OCR. State the consequence in docs: selecting the same word twice in a row uses OCR the second time (usually yields the same word since the cursor is over it).
- Never use `QClipboard` Selection mode in this project. Never write to the clipboard.
- Test matrix for the selection path: Konsole, Kate, Firefox/Chromium, a Qt app, an Electron app, XWayland app, closed source app, plus "source app closed" (the #185 case).
- Check `XDG_SESSION_TYPE` once; choose `wl-paste` or `xclip -o -selection primary`.

**Warning signs:** hotkey occasionally "does nothing" and leaves a `wl-paste` process behind; translating the same old word on every press; works in Konsole, empty in Firefox.

**Phase to address:** Selection phase (small, early; before OCR integration so the "OCR only when no selection" branch exists from the start).

---

### Pitfall 7: Translation call freezes or stalls the overlay (timeouts that don't time out)

**What goes wrong:** The overlay never appears, or appears frozen, because the network call blocks the UI thread; or a "timeout=2" still takes 30+ s.

**Why it happens (Python specific):**
- `urllib`/`http.client` `timeout=` is per socket operation (connect, each read), **not** a wall-clock deadline.
- DNS resolution (`getaddrinfo`) ignores the timeout and can block for tens of seconds on a broken resolver.
- IPv6 black-holes: connection attempts are tried address by address; N addresses x timeout.
- Blocking in the Qt main thread stops painting; one-shot process looks hung.

**How to avoid:**
- Run translation in a worker thread (or a `subprocess` you can kill) with an overall deadline enforced by the caller (`future.result(timeout=3)`), not by the socket layer. On deadline: show failure state, then `os._exit(0)` after DB write; do not wait for the stuck thread (process is one-shot).
- Show the overlay *immediately* after OCR with the recognized word and "...", then fill in the translation. This makes the perceived latency the capture+OCR time only, and the failure state is just a different overlay text.
- Budget per stage (starting numbers, to be replaced with spike measurements): cursor+capture ~0.6 s, OCR ~0.5 s, network <= 1.5 s hard cap, overlay ~0.1 s.
- Cache hit skips network entirely (Pitfall 1).
- Don't let an in-flight earlier lookup keep running: single-instance lock (Pitfall 9) kills/replaces it.

**Warning signs:** overlay appears only after a delay equal to network timeout; process stays in `ps` after overlay closed; intermittent 20-60 s hangs on the friend's Wi-Fi or on IPv6-broken networks.

**Phase to address:** Translation + overlay phases (the deadline mechanism belongs in the translation module's interface).

---

### Pitfall 8: Tesseract on UI text returns the wrong word or junk

**What goes wrong:** small UI fonts, anti-aliased/subpixel text, dark themes, icons, and code fonts make Tesseract miss words or return garbage; the "word under the cursor" is selected incorrectly when the pointer sits between words or on a line gap; junk then gets translated and saved.

**Why it happens:** Tesseract is tuned for ~300 DPI document scans: it "works best at 300 DPI+" and benefits from upscaling small text; it expects dark text on light background (4.x/5.x LSTM; older 3.x handled inverted images better); its internal Otsu binarisation fails with uneven backgrounds; no border or an oversized border on a tiny crop can give "empty page"; PSM 8 ("single word") is wrong for a crop that contains several words. (tessdoc ImproveQuality) [HIGH]. A tiny crop (e.g. 2 px wide) triggers "Image too small to scale" and, in the legacy engine, even a floating-point crash fixed in 5.3.1 (tesseract #3995; use `--oem 1`). [HIGH]

**How to avoid (concrete pipeline):**
- Crop band around the cursor (Pitfall 4), grayscale, upscale 2-3x (Lanczos), add ~10 px border, auto-invert when mean luminance < ~128 (dark theme). When contrast polarity is ambiguous (colored buttons, syntax-highlighted code), optionally run both polarities and keep the higher-confidence result, only if the time budget allows. Benchmark 2x vs 3x on real screenshots: no source settles it. [source gap]
- Always `--oem 1` (LSTM), `-l eng`, and run via TSV/`image_to_data` (or `tesseract ... tsv`) to get **per-word boxes and confidences**. Do not use PSM 8. Try PSM 6 (block) vs PSM 11 (sparse) on a screenshot fixture set; pick one and keep it.
- Word choice rule: (1) the word whose box contains the cursor point (in upscaled crop coordinates, minus border); (2) otherwise the nearest box center *horizontally on the same line* within ~0.7 x line height; (3) otherwise nearest overall within ~1.5 x line height; else "no word here". Pointer hotspot (arrow tip) vs I-beam differs; use the hotspot, not a shape-dependent offset.
- Normalise: strip leading/trailing punctuation and quotes, normalise curly apostrophes, drop possessive `'s`, lowercase for the key (store original form for display). Keep inner hyphen/apostrophe (`well-known`, `don't`).
- Hyphenation: only merge when the hit token ends with `-` AND the next line's first token starts directly below (box x within a line-height) AND is lowercase; then look up the merged word. Otherwise look up as-is. Don't try to be smarter in the MVP.
- Junk filter before translation and before the DB: regex like `^[A-Za-z][A-Za-z'’-]*$`, length >= 2 (allow `a`, `I`), confidence >= ~60 (tune on fixtures); reject URLs/paths/numbers/camelCase identifiers/ALL-CAPS ids. If rejected: overlay says "Can't read this - select the word instead" and nothing is saved.
- Known confusions to test as fixtures: `l/I/1`, `0/O`, `rn/m`, ligatures (`fi`), italic UI text, tiny status-bar fonts, light-on-dark terminal, text over images/gradients.
- Set `OMP_THREAD_LIMIT=1` when spawning Tesseract; OpenMP thread spin-up commonly makes tiny crops *slower* [MEDIUM - widely repeated community advice; benchmark in spike].
- Arch packages: `tesseract` alone has no language data - need `tesseract-data-eng`. A missing language file yields a confusing error. [HIGH]
- Check Spectacle 6.6 built-in OCR: it exists in Plasma 6.6 but I found nothing saying it is scriptable from the command line [source gap]; do not plan around it.

**Warning signs:** fixture accuracy < ~90% on UI text; frequent "nearest word" picks; DB containing entries like `rn`, `0f`, `thc`; OCR taking > 1 s on a small crop (thread contention).

**Phase to address:** OCR phase; build a small fixture set of real screenshots (light, dark, 100%/150%, code editor, browser, Konsole) *before* tuning, and make the word-picking a pure function over TSV rows (unit-testable).

---

### Pitfall 9: Overlapping hotkey presses: multiple processes, DB races, runaway spawn

**What goes wrong:** key repeat or a double press launches several one-shot processes: each takes a screenshot (possibly of the other's overlay), each writes to SQLite, the counter is wrong or throws `database is locked`, two overlays stack up.

**Why it happens:** KDE runs the command per activation with no single-instance guarantee. SQLite allows only one writer at a time even in WAL mode (reads don't block writes, but `SQLITE_BUSY` still appears during recovery/last-connection-close, and WAL is not supported on network filesystems). [HIGH: sqlite.org/wal.html]

**How to avoid:**
- **Process-level:** `flock` on `$XDG_RUNTIME_DIR/lookup.lock`, non-blocking. Policy (pick one, opinionated): *new press replaces old* - the newcomer asks the holder to close (signal/D-Bus/PID file) then proceeds; plus a ~300 ms debounce so key repeat doesn't thrash. State it in docs.
- **DB-level:** `sqlite3.connect(path, timeout=5)` (or `PRAGMA busy_timeout=5000`), one atomic statement for counting: `INSERT INTO words(word, translation, count, first_seen, last_seen) VALUES(?,?,1,?,?) ON CONFLICT(word) DO UPDATE SET count = count+1, last_seen = excluded.last_seen, translation = COALESCE(excluded.translation, translation)` with `UNIQUE(word)` on the normalised (lowercase) key. Never `SELECT` then `UPDATE`.
- Schema creation/migration: `CREATE TABLE IF NOT EXISTS`; migrations guarded by `PRAGMA user_version` inside `BEGIN IMMEDIATE`.
- `journal_mode=WAL` is worth it because the word-list window will hold the DB open while lookups write; keep the DB on a local filesystem under `$XDG_DATA_HOME/lookup/` (never the install dir, never an NFS home).
- Never block the overlay on the DB: write after the overlay is shown, with a short timeout; a locked DB logs and retries once, not freezes the UI.
- The list window: short read transactions, re-query on window activation or a file-mtime timer; don't keep a cursor open.
- Don't count a lookup twice if the same normalised word is resolved twice within the debounce window.

**Warning signs:** `database is locked` in the log; counter occasionally +2 or +0 for one press; two overlays visible; leftover `-wal`/`-shm` files after the list window closes uncleanly (harmless, but confirm recovery).

**Phase to address:** Persistence phase (UPSERT + busy_timeout), Overlay/entry phase (single-instance lock). Test with a script that fires N parallel invocations and asserts the final count.

---

### Pitfall 10: The KDE shortcut runs a command in a different environment and fails silently

**What goes wrong:** Works from the terminal, silently does nothing from the shortcut: wrong `PATH`, no venv, missing `DISPLAY`/`WAYLAND_DISPLAY`, no stdout/stderr, relative paths, missing `QT_QPA_PLATFORM`. The friend sees "nothing happens" and cannot debug it. Also: certain keys can't be bound as global shortcuts on Plasma 6.5.4 Wayland (e.g. `²`), and bare Meta is claimed by the launcher.

**Why it happens:** Commands launched by KGlobalAccel get a minimal session environment and no terminal. [MEDIUM - architecture knowledge; the user's reports in the KDE threads show the custom-command route exists and works for ordinary keys]

**How to avoid:**
- The shortcut command is a single absolute-path launcher script/binary installed by the install script (e.g. `~/.local/bin/lookup`), which sets its own environment (including `QT_QPA_PLATFORM=xcb` for the overlay child only) and uses absolute interpreter paths.
- **Always log** to `$XDG_STATE_HOME/lookup/lookup.log` (rotate small) and surface fatal errors as an overlay/`notify-send` message ("LookUp: tesseract-data-eng missing"). A tool that fails silently will be abandoned.
- Recommend a combo with a normal key (e.g. `Meta+Shift+D` or `Ctrl+Alt+D`), not bare Meta, not non-alphanumeric keys. Ask the friend to test the key first for collisions in System Settings.
- Programmatic creation of the shortcut (`.desktop` + `X-KDE-Shortcuts`, or `kglobalshortcutsrc` editing) was not verifiable from the sources I found [source gap, LOW]. MVP: install doc gives exact click-path ("System Settings > Keyboard > Shortcuts > Add Command"); script only verifies and prints instructions. Revisit automation only if time permits.
- A "doctor" subcommand (`lookup --doctor`): checks session type, Plasma version, `spectacle`, `tesseract` + `eng` data, `wl-paste`, D-Bus/KWin scripting reachable, DB writable, translation reachable. This is the cheapest high-value feature for a remote friend.

**Warning signs:** "works in my terminal"; log file empty; works after re-login but not before.

**Phase to address:** Install/packaging phase, with the launcher + log + doctor created in the first integration phase.

---

### Pitfall 11: Cold-start latency makes the 2 s budget unachievable in a one-shot design

**What goes wrong:** Sum of Python interpreter start + PySide6 import + KWin script + Spectacle + Tesseract + HTTPS handshake exceeds 2 s on the friend's machine; users blame the tool. PROJECT.md decided one-shot over daemon "unless slow", so the trigger for reconsidering must be explicit.

**Evidence/assumptions:** Spectacle 0.3-2 s (anecdotal); PySide6 widget import commonly a few hundred ms cold [LOW - measure]; Tesseract process start on a small crop several hundred ms [LOW - measure]; TLS handshake ~100-300 ms. VM numbers are not representative (software rendering, fewer cores).

**How to avoid:**
- Entry script is stdlib-only and starts the three independent jobs *first and concurrently*: (a) cursor/monitor query via KWin script, (b) PRIMARY read, (c) Spectacle capture. Only then `import PySide6` (while Spectacle encodes). Lazy-import QtWidgets/QtNetwork-free modules; don't import `PySide6.QtWidgets` in the CLI path that only needs to exit.
- Keep a timing log per stage (monotonic ms) in the debug log from day one; the budget table in Pitfall 7 gets real numbers in phase 1 and again on real hardware.
- Define the pivot rule now: if p50 on friend's hardware > 2.0 s and Spectacle+Python start are >50% of it, move capture to a resident helper (`spectacle --dbus` user service, or a small resident Python process holding PySide6/D-Bus loaded). Write the stage boundaries so this swap is a module change, not a rewrite.
- Selection path (no OCR) should be near-instant; make sure the OCR/Spectacle work is not started when a valid new selection exists (check selection first, ~tens of ms).

**Warning signs:** total > 2 s while no single stage is slow; first lookup after login much slower than later ones (Xwayland lazy start, file cache cold).

**Phase to address:** Phase 1 (budget measurement), re-validated in the final hardening phase on real hardware.

---

### Pitfall 12: VM testing lies about pointer, cursor, rendering and clipboard

**What goes wrong:** Bugs that exist only in the VM get chased as app bugs; real bugs on the friend's machine are hidden. Reported VM-specific issues for Plasma Wayland:
- VirtualBox: Plasma 6 Wayland black screen unless 3D acceleration is on or graphics controller is VBoxSVGA; with 3D on, performance can be unusable; invisible pointer fixed with `KWIN_FORCE_SW_CURSOR=1`; (KDE Discuss, Arch forum, KaOS forum) [MEDIUM, mostly 2024 data].
- VMware: Wayland cursor shape wrong ~90% of the time and a few pixels off; fixed for one user by `KWIN_FORCE_SW_CURSOR=1`; X11 "much better" (Arch BBS #289760, Fusion community). [MEDIUM]
- virtio-gpu/virgl with 3D on: upside-down and offset cursor reported in a Fedora 40 KDE guest. Older KWin: click point offset vs drawn cursor in Wayland VMs (fixed in 5.22.5 / 5.24.4 era, so not relevant to Plasma 6 itself). [MEDIUM]
- Clipboard/PRIMARY: guest agents (spice-vdagent, VMware tools) sync host and guest clipboards and can interfere with selection tests. [LOW - not sourced, plausible]
- Software rendering (llvmpipe) makes Spectacle/KWin screenshot and Qt timing unrepresentative.

**How to avoid:**
- Recommended VM: QEMU/KVM + virt-manager, `Video: Virtio` with 3D accel on (virgl), USB tablet pointer (absolute), >= 2-4 vCPUs, Spice display, current Arch ISO (so Plasma matches the friend's rolling Arch). If the cursor misbehaves, try `KWIN_FORCE_SW_CURSOR=1` for the *guest session only* and note it in test logs. [MEDIUM - no single source gives a verified "good" config; treat as starting point]
- Separate "VM pointer weirdness" from "app coordinate bugs": ground truth is what the KWin script reports. Build a debug mode (`--debug-overlay`) that draws a crosshair at the script-reported cursor position and the crop rectangle on a full-screen transparent window; a mismatch with the *visible* cursor in the VM is VM, a mismatch with *screenshot content* is a bug.
- Keep geometry/word-pick logic pure and fixture-tested outside the VM (Pitfalls 4, 8). The VM is for the integration smoke test, not for tuning math.
- Test matrix in VM: X11 session and Wayland session; scale 100/125/150/200%; two virtual displays (virt-manager allows multiple video heads / spice displays) if possible; GUI Spectacle open vs closed; Esc/click/timeout close.
- **Mandatory real-hardware smoke test** on the friend's laptop (or any physical Plasma Wayland machine) before calling the MVP done: VM can't validate latency, HiDPI rendering, focus-stealing level, or multi-monitor.

**Warning signs:** "cursor jumps" or "overlay offset" reproducible only in the VM; screenshots black in the VM Wayland session (check 3D/VBoxSVGA first); timing numbers 3x worse than expected.

**Phase to address:** Phase 1 (VM baseline definition) and the final hardening phase (real hardware).

---

## Moderate Pitfalls

### Pitfall 13: Overlay requirements (close on click, Esc, timeout) collide with its own window flags
**What goes wrong:** A non-activating overlay (good for not stealing focus from the user's app) can't receive Esc; an activating one steals focus and breaks the user's flow (e.g. their selection in the source app collapses; typing goes to the overlay).
**Prevention:** Prefer non-activating by default (`WA_ShowWithoutActivating`, `Qt.WindowDoesNotAcceptFocus` where it works on xcb) with click-to-close and 4-6 s timeout; treat Esc as a bonus where the WM grants focus. If Esc is a hard requirement, make activation explicit via window rule/KWin script (Pitfall 3) and restore the previous active window on close. Never grab keyboard/pointer globally.
**Phase:** Overlay.

### Pitfall 14: Selection/mouse state changes between hotkey press and screenshot
**What goes wrong:** the user moves the mouse during the ~1 s pipeline, or the pressed hotkey's modifiers still held cause the app to change state; the cursor query and the screenshot are taken at different moments.
**Prevention:** query the cursor position *first* and snapshot it; take the screenshot immediately after; use the snapshot for all later math. Don't re-query the cursor after OCR. Place the overlay at the snapshotted position (or clamp), not the current one.
**Phase:** Capture.

### Pitfall 15: Translation result parsing and display edge cases
**What goes wrong:** unknown word returns the same string as the source (looks like a "translation" but isn't); multiple-meaning dictionary payload (`dt=bd`) missing for many words; very long or HTML-ish output; RTL/diacritics; English inflected forms (`running`, `went`) yield different DB rows than the base form.
**Prevention:** `identical_to_source -> "no translation found"` and don't count as a successful lookup (still log); render at most 3 senses by POS with a hard character cap; word-wrap overlay with max width; decide in the requirements phase that the DB key is the lowercase surface form (no stemming in MVP) and write that down so nobody "fixes" it ad hoc.
**Phase:** Translation / Persistence.

### Pitfall 16: Install script assumptions (Arch packaging)
**What goes wrong:** missing packages at runtime (`tesseract-data-eng`, `wl-clipboard`, `xclip` for X11, `pyside6` vs a pip wheel mixing with system Qt), venv shadowing system PySide6, `kdotool` assumed available.
**Prevention:** the install script checks `pacman -Q` for a single explicit package list (`tesseract tesseract-data-eng spectacle wl-clipboard python-pyside6 [xclip]`) and fails with the exact missing names; use the system Python (no venv) so PySide6 matches system Qt; avoid AUR dependencies entirely (kdotool is AUR-only). Pair with `lookup --doctor` (Pitfall 10).
**Phase:** Install/packaging.

### Pitfall 17: Plasma version drift
**What goes wrong:** Arch is rolling; KWin scripting, focus-stealing levels (MR !7952 in flight), data-control protocol switch (6.4), Qt 6.11 behaviours (a Spectacle workaround was mentioned in 6.6.4 notes) change under the app. Plasma 6.6.4 changelog mentions Xwayland scaling/pointer-positioning fixes. [MEDIUM]
**Prevention:** record Plasma/Qt/KWin versions in the log header of every run; the doctor command prints them; keep the KWin-script interaction in a single module with a version-tolerant call (property-exists checks, not version sniffing).
**Phase:** All; owned by the integration/hardening phase.

---

## Minor Pitfalls

### Pitfall 18: Journal spam from KWin script logging
**What goes wrong:** using `console.error`/`print` in the KWin script for debugging leaves ~1 KB per call in journald.
**Prevention:** return data over D-Bus only; guard debug output behind a flag.

### Pitfall 19: Leaving temp artifacts and PID/lock files
**What goes wrong:** crashed run leaves screenshot, lock, or loaded KWin script behind.
**Prevention:** `finally`/`atexit` cleanup + stale-file cleanup at startup (also covers "screenshots never saved").

### Pitfall 20: Fullscreen app foreground
**What goes wrong:** Spectacle capture was reported slow when a fullscreen app is focused (KDE Discuss), and Plasma 6.4 turns on Do Not Disturb when an app is fullscreen (hides notifications, including your error notifications).
**Prevention:** test with a fullscreen browser/video; don't rely on notifications for errors - use the overlay.

### Pitfall 21: Multiple word lookups of non-English text
**What goes wrong:** cursor over Russian/other-language UI text or mixed text produces OCR junk (`-l eng` can't read Cyrillic) that passes the regex filter by accident (Latin lookalikes).
**Prevention:** confidence threshold + junk filter (Pitfall 8); out of scope to support other languages; show "can't read" rather than guessing.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Use `kdotool` for cursor | Zero KWin-script code | AUR-only dependency, per-call script load, not in the Arch-repo-only install story | Only as a prototype in the spike; replace before release |
| `QCursor.pos()` everywhere | One line | Wrong on Wayland (Pitfall 2) | Only in the X11-session branch |
| Hard-code `client=gtx` | Matches PROJECT.md | Dead on any network Google is blocking (already happening) | Never: make it config + fallback list from day one |
| Fullscreen Spectacle + crop | Simple | Slow PNG encode, multi-monitor math, privacy surface | Prototype only; use `-m` current monitor in the real build |
| `QClipboard` for PRIMARY | No subprocess | Empty/crash on Wayland unfocused client | Never on Wayland |
| `SELECT` then `UPDATE` counter | Easy to read | Lost updates with overlapping presses | Never: single UPSERT |
| Skip the fixture OCR set | Faster to start | Tuning by feel on one screen; regressions invisible | Never: 20 screenshots are cheap and make OCR tuning testable |
| Silent `except: pass` around the pipeline | No crashes | Friend can't report a useful failure | Never: log + overlay error |
| Global `QT_QPA_PLATFORM=xcb` | One setting | Blurry list window at fractional scale | Only for the overlay child process |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Google gtx endpoint | Assume JSON; retry on error; parse by fixed index | Detect HTML/429 as `blocked`; no retry loop; configurable client list; safe-index parser; cache; second provider |
| KWin Scripting D-Bus | Read result from `run` return or journald | Script calls back over D-Bus; unique script name; unload in `finally`; clean stale scripts |
| Spectacle CLI | Omit `-o`, use `-c`, rely on exit code, ignore running instance | `-b -n -m -o tmpfile`, hard timeout, check file, test with GUI open |
| KWin `ScreenShot2` (if used directly) | Call without desktop-file authorization | `.desktop` with `X-KDE-DBUS-Restricted-Interfaces`, absolute `Exec` pointing at interpreter, fallback to Spectacle |
| `wl-paste` | Call with no timeout; assume non-empty | `timeout=0.4`, kill, rc!=0 -> none; own module |
| Tesseract | PSM 8 on a multi-word crop; no preprocessing; legacy engine | `--oem 1 -l eng`, TSV word boxes, upscale/invert/border, confidence filter |
| SQLite | Read-modify-write; default zero busy timeout; DB in install dir | UPSERT, `busy_timeout`, WAL, DB under `$XDG_DATA_HOME`, local FS |
| KDE Shortcuts | Command depends on shell/PATH/venv; no log | Single absolute launcher, own env, log file, doctor |
| Qt/XWayland overlay | Compute position in Qt; assume focus | KWin script sets geometry in logical coords; window rule; click/timeout always close |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Sequential pipeline (cursor -> capture -> import Qt -> OCR -> network) | > 2 s though each step looks fine | Concurrent kick-off, stdlib-only entry, lazy imports | First real hardware test |
| PNG encode of large multi-monitor capture | Spectacle 1-2 s | Capture current monitor only; consider ScreenShot2 CaptureArea | 4K or 2+ monitors |
| Tesseract on full-resolution large image / OpenMP spin-up | OCR 1-3 s | Small band crop, `OMP_THREAD_LIMIT=1`, upscale only the crop | Any HiDPI display |
| Network on UI thread / no wall-clock deadline | Frozen overlay | Worker + caller-side deadline; show word first | Bad Wi-Fi, IPv6 black hole, resolver issues |
| Cold Xwayland / cold Python cache | First lookup after login slow | Measure, document; optional warm-up in autostart | First use per session |
| Re-querying cursor after OCR | Overlay at wrong place when user moved | Snapshot first | Any slow step |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Screenshot persisted (default Spectacle save dir, `-c` into Klipper, leftover temp) | Passwords/chat/banking visible on screen end up on disk or in clipboard history; violates stated privacy constraint | tmpfs file 0600, unlink in `finally`, never `-c`, startup stale cleanup; verify Pictures folder stays empty |
| Sending more than the word to Google | Leaks surrounding on-screen text | Send only the normalised single token; log the outgoing query in debug mode to prove it |
| Junk OCR sent to the network (passwords, tokens recognised as "words") | Secrets leave the machine | Junk filter (alpha-only, length cap ~30), skip long/mixed-digit tokens, never send selection text longer than the cap |
| `KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1` shipped as "fix" | Disables KWin's screenshot authorization for the whole session | Debug-only; install uses a proper desktop-file authorization or Spectacle |
| Writing translated/selected text to a world-readable log | Privacy leak | Log stage timings and error classes, not clipboard/selection contents; log dir 0700 |
| Sourcing cached JSON/DB content into UI as rich text | Markup injection via translation text | Render as plain text (`Qt.PlainText`) in overlay and list |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No feedback during the 1-2 s pipeline | Friend presses again and again, spawning more processes | Immediate small "..." overlay as soon as a word is known; debounce/single-instance |
| Silent failure | "It doesn't work" with no clue | Overlay/notify message with specific cause + log path |
| Overlay under the pointer | Click goes to overlay, flicker | Offset from hotspot; clamp to screen |
| Overlay steals focus | Loses text selection, typing goes elsewhere | Non-activating by default |
| Same stale selection translated every time | Looks like OCR is broken | "New selection only" rule (Pitfall 6) and documented consequence |
| Showing junk "translations" for garbage OCR | Erodes trust, pollutes DB | Confidence + regex gate; "can't read this" message |
| Counter increments on failures/duplicates | Wrong statistics | Count only successful, recognised, non-duplicate lookups within debounce |
| Hotkey conflicts | Hotkey seems dead | Suggest a collision-safe combo, doctor check, instructions with screenshots |

## "Looks Done But Isn't" Checklist

- [ ] **Cursor position:** works under *Wayland* session, not just X11 - verify with a visible crosshair debug overlay at 100/150% and on the second monitor.
- [ ] **Overlay placement:** correct on second monitor with negative origin and near right/bottom edges; no overlap under pointer.
- [ ] **Overlay closing:** click, Esc (when focus granted), and timeout each tested; process exits (no leftover in `ps`).
- [ ] **Translation failure path:** disconnect network / block host / return HTML 429 (simulate with a local stub): overlay appears within the deadline and word is still saved.
- [ ] **gtx blocked:** simulate `blocked`; fallback client / second provider kicks in; message is human-readable.
- [ ] **PRIMARY path:** no-selection (`wl-paste` rc!=0), stale selection, source app closed (hang), long text selection, non-text selection.
- [ ] **OCR:** dark theme, light theme, 100%/150%/200%, Konsole, browser, code editor, tiny status-bar text, cursor between words, on whitespace, at line end with hyphenation, on junk.
- [ ] **Privacy:** after 50 lookups, no PNG anywhere (`~/Pictures`, `/tmp`, `$XDG_RUNTIME_DIR`), clipboard history unchanged.
- [ ] **Concurrency:** 10 parallel invocations -> exactly one overlay, correct counter, no `database is locked`.
- [ ] **Shortcut launch:** works from the actual KDE shortcut after logout/login, with no terminal and minimal env (not just from a shell).
- [ ] **Cold start:** first lookup after login within budget; p50/p95 recorded on real hardware.
- [ ] **Spectacle GUI open:** lookup behaviour correct while a Spectacle window is open.
- [ ] **Word list window:** native Wayland, not blurry at 150%; refreshes while lookups write.
- [ ] **Install doc:** a clean Arch VM snapshot can follow it from zero to working lookup without extra steps; `--doctor` is green.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Google endpoint blocked | MEDIUM | Switch `client=` via config; if all blocked, enable second provider / API key; cached words keep working; word saved with NULL translation and back-filled |
| Cursor/overlay offset on Wayland | MEDIUM | Switch positioning to KWin-script geometry; fall back to window rule; calibrate with debug crosshair |
| Spectacle too slow | MEDIUM | Move to `spectacle --dbus` service or direct `ScreenShot2.CaptureArea` with generated desktop file |
| `wl-paste` hang | LOW | Timeout+kill wrapper; users can `pkill wl-paste`; ship wrapper |
| Corrupt / locked DB | LOW | `busy_timeout`, WAL; DB is a single file - back up on each schema migration; export command for words |
| Stale loaded KWin script | LOW | Doctor command lists/unloads scripts with the project's name prefix |
| Plasma update breaks something | MEDIUM | Version logged per run; doctor shows versions; pin behaviours in single modules |

## Pitfall-to-Phase Mapping

Phase names are suggestions for the roadmapper (renumber as needed).

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 1 Google endpoint blocked | Phase 1 spike (reachability check from VM + friend's network) -> Translation phase (client list, fallback provider, cache) | Local stub returning 429 HTML; run on two networks |
| 2 No cursor on Wayland | Phase 1 platform spike (KWin script round-trip) | Debug crosshair matches visible pointer in Wayland session; latency number recorded |
| 3 XWayland placement / focus / scale | Overlay phase | Scale matrix 100/125/150/200% x 2 monitors; click/Esc/timeout |
| 4 Crop/coordinate mismatch | Capture phase (pure function + fixtures) | Unit tests on 4 scales incl. negative origin |
| 5 Spectacle quirks | Phase 1 spike -> Capture phase | Timing log; no files in Pictures; works with Spectacle GUI open |
| 6 PRIMARY selection / `wl-paste` | Selection phase | Hang test (source app closed), stale selection test |
| 7 Translation timeouts | Translation + Overlay phases | Blackholed host test: overlay <= deadline; no stuck process |
| 8 Tesseract junk / wrong word | OCR phase (fixture set first) | Fixture accuracy threshold; pure word-pick tests |
| 9 Overlapping presses / SQLite | Persistence phase + Entry-point phase | 10 parallel invocations -> correct count, single overlay |
| 10 Shortcut env / silent failure | Integration + Install phases | Launch from real KDE shortcut after re-login; log and doctor output |
| 11 Cold-start latency | Phase 1 budget; Hardening phase re-check | p50/p95 on real hardware; pivot rule documented |
| 12 VM testing lies | Phase 1 (VM definition); Hardening (real hardware) | Written VM config; real-hardware smoke checklist signed off |
| 13 Overlay flags vs requirements | Overlay phase | Focus and non-focus behaviours tested |
| 14 State changes between steps | Capture phase | Moving the mouse mid-pipeline doesn't move overlay |
| 15 Parsing/display edge cases | Translation phase | Unknown word, long output, missing `dt=bd` fixtures |
| 16 Install assumptions | Install phase | Fresh Arch VM snapshot walkthrough |
| 17 Plasma version drift | Hardening phase | Versions printed by doctor/logged |

## Research Flags for Phases (deeper research likely needed)

- **Phase 1 platform spike (KWin script + D-Bus callback + window geometry set from script):** needs hands-on prototyping, sources give no complete example. Highest technical uncertainty.
- **Overlay phase:** needs hands-on research on XWayland placement vs KWin script geometry vs window rule vs `Qt.ToolTip`; no source covers Qt `move()` under XWayland fractional scaling.
- **Translation phase:** needs re-research at implementation time; client list and fallback providers are changing week to week.
- **Install/shortcut automation:** the programmatic way to register a custom command shortcut on Plasma 6 was not found [source gap].
- Standard patterns, unlikely to need research: SQLite UPSERT/WAL, subprocess timeouts, unit-testing pure geometry/word-pick functions.

## Sources

- eeeXun/gtt issue #43 "Google engine returns HTTP 429 for every request: client=gtx is blocked, client=at works" (Sept 2026): https://github.com/eeeXun/gtt/issues/43 [HIGH]
- Mega-Gorilla/livecap-cli issue #442 (gtx block, client identifiers, bot detection findings, decision log): https://github.com/Mega-Gorilla/livecap-cli/issues/442 [HIGH]
- noctalia-dev/official-plugins issue #64 (gtx 429, HTML treated as success): https://github.com/noctalia-dev/official-plugins/issues/64 [HIGH]
- Asura7170/easydict_win32 PR #4 (429 at low volume; translate-pa fallback): https://github.com/Asura7170/easydict_win32/pull/4 [MEDIUM]
- KDE Wayland Porting Notes (no global cursor, QCursor::pos, popup transient parent): https://community.kde.org/Guidelines_and_HOWTOs/Wayland_Porting_Notes [HIGH]
- KDE Discuss "Is there a better way to obtain the mouse cursor location?" (KWin script is the read path; journal/D-Bus return issues; kdotool approach): https://discuss.kde.org/t/is-there-a-better-way-to-obtain-the-mouse-cursor-location/20559 [HIGH]
- KWin MR !3134 "scripting: Expose cursor position to the scripting API": https://invent.kde.org/plasma/kwin/-/merge_requests/3134 [HIGH]
- kdotool README (per-call generated KWin script, Plasma 6 only since v0.3.0): https://github.com/jinliu/kdotool [HIGH]; Arch official package search (0 results for kdotool): https://archlinux.org/packages/?q=kdotool [HIGH as of 2026-10-23]
- Spectacle man page / CLI options: https://mankier.com/1/spectacle [HIGH]; MR !198 (background/DBus mode not closing; options applied to running instance): https://invent.kde.org/graphics/spectacle/-/merge_requests/198 [MEDIUM]
- KDE Discuss "Make Spectacle launch faster" (startup times, `spectacle --dbus` user service): https://discuss.kde.org/t/make-spectacle-launch-faster/38030 [MEDIUM, anecdotal]
- KWin `org.kde.KWin.ScreenShot2` interface XML (methods, `native-resolution`, authorization note): https://lxr.kde.org/source/plasma/kwin/src/plugins/screenshot/org.kde.KWin.ScreenShot2.xml [HIGH]
- KDE Discuss "Occasionally freezes when using dbus to take screenshots" (pipe read hang; desktop-file authorization): https://discuss.kde.org/t/occasionally-freezes-when-using-dbus-to-take-screenshots/43733 [MEDIUM]
- KWin mailing list Oct 2024 (not authorized despite desktop file; absolute Exec): https://mail.kde.org/pipermail/kwin/2024-October/005338.html [MEDIUM]
- Arch forum thread on Flameshot/portal permission store breakage (Spectacle talks to KWin directly): https://bbs.archlinux.org/viewtopic.php?id=306394 [MEDIUM]
- KWin focus stealing prevention levels MR !7952: https://invent.kde.org/plasma/kwin/-/merge_requests/7952 (open when read) and issue https://invent.kde.org/plasma/kwin/-/issues/186 [MEDIUM]
- wl-clipboard issue #185 (`wl-paste` hangs; no timeout; maintainer response): https://github.com/bugaevc/wl-clipboard/issues/185 [HIGH]
- Crow Translate issue #324 and MR !596 (selection translate fails on Wayland; only active window can read selection): https://invent.kde.org/office/crow-translate/-/issues/324 , https://invent.kde.org/office/crow-translate/-/merge_requests/596 [HIGH]
- GoldenDict-ng v26.6.1 notes (scan-popup crash on Wayland accessing QClipboard::Selection, #2969): https://newreleases.io/project/github/xiaoyifang/goldendict-ng/release/v26.6.1 [MEDIUM]
- Qt Wayland client source (selection read path): https://codebrowser.dev/qt6/qtwayland/src/client/qwaylandclipboard.cpp.html [MEDIUM]
- KDE Plasma 6.4 ext-data-control switch (Russian-language report): https://habr.com/ru/articles/919350 [MEDIUM]
- Tesseract docs "Improving the quality of the output" (300 DPI, inversion, binarisation, borders, PSM 7/8/13): https://github.com/tesseract-ocr/tessdoc/blob/main/ImproveQuality.md [HIGH]
- Tesseract issue #3995 (tiny image crash in legacy engine; use `--oem 1`; fixed 5.3.1): https://github.com/tesseract-ocr/tesseract/issues/3995 [HIGH]
- SQLite WAL documentation (one writer, SQLITE_BUSY cases, no network FS): https://sqlite.org/wal.html [HIGH]
- KDE Discuss on XWayland scaling ("Apply scaling themselves" vs "Scaled by the system"; Xft.dpi vs 96 DPI): https://discuss.kde.org/t/whats-up-with-scaling-of-x11-applications-on-wayland/23809 and https://discuss.kde.org/t/137-5-scaling-for-xwayland-programs/22780 [MEDIUM]
- VM reports: Arch BBS #289760 (VMware/VirtualBox Wayland pointer), KDE Discuss 12289 (VirtualBox Plasma 6 black screen), Fedora Discussion 117289 (virtio guest cursor), VMware Fusion community (KWIN_FORCE_SW_CURSOR=1): https://bbs.archlinux.org/viewtopic.php?id=289760 , https://discuss.kde.org/t/cant-install-use-kde-neon-user-edition-in-virtualbox-after-update-to-plasma-6-it-shows-black-screen/12289 , https://discussion.fedoraproject.org/t/mouse-issues-in-virt-manager-inside-fedora-40-kde-guest/117289 [MEDIUM, mostly 2024]
- KDE shortcut custom-command route and Plasma 6 key limitations: https://discuss.kde.org/t/plasma-6-5-4-wayland-cannot-assign-key-as-global-shortcut-for-guake/42692 [MEDIUM]
- Not found / source gaps: Normcap- and dictpopup-specific tracker items (searches returned nothing relevant); programmatic KGlobalAccel registration on Plasma 6; units of `ScreenShot2.CaptureArea` coordinates; measured latency of KWin script load/run/call-back; a verified "good" VM config; whether Spectacle shows any flash in background mode.

---
*Pitfalls research for: Linux hotkey OCR + translation overlay tool (Arch + KDE Plasma 6, Wayland/X11)*
*Researched: 2026-10-23*
