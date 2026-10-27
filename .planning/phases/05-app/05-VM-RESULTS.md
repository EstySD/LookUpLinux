# Phase5 production KDE evidence

Acceptance is agent judgment under the user's explicit `--auto` instruction.
The user subsequently requested stopping after this phase. No human or friend
hardware testing is claimed. Production source ran in an isolated checkout on
the existing Arch/KDE Wayland VirtualBox VM, using temporary public StarDict,
SQLite, configuration and cache roots. Test-only instrumentation is injected by
the owned profile; production exposes only its fixed Trigger IPC.

## Reproduction

From the Windows host, with current lookup/tests/tools synced into
`~/LookUpLinux-gsd-app-05`:

```
python tools/check_app.py --output .planning/phases/05-app/05-GATE-RESULTS.json
python tools/check_app.py --extra --output .planning/phases/05-app/05-EXTRA-GATES.json
```

Normal VM unlock is test preparation only. Production never unlocks a session.
Physical Meta+Shift+D, Escape, Tab and selection keys use VirtualBox scancodes;
pointer, button and drag delivery use its COM mouse API with observed cursor
feedback. No wl-copy, synthetic primary injection or clipboard-history changes
are used. The supplemental run creates its fresh primary by an actual mouse drag.

## Observed requirements

| Requirement | Actual proof |
|---|---|
| TRIG-02 | Existing owner accepts repeated keys; delayed A/dismiss/release never reopens or writes; queued B replaces A, with real temporary history checked. Deterministic barriers additionally cover bursts and queued Qt delivery. |
| TRIG-03 | Warm PID stays the same; two concurrent extra `--app` processes return0 without replacing it; physical cold key starts another owner and completes lookup. Physical native tray menu shows disabled future actions and its Quit removes both production/probe services. |
| CAPT-02 | New primary bypasses OCR; unchanged primary over the public `word` requires exactly mode=ocr/key=word. Absent and invalid primary reset freshness; same text becomes primary again. One/two/four/five-word cases distinguish word/phrase/sentence, and the sentence creates no word row. Supplemental physical mouse selection confirms real primary without keyboard Select All. |
| POP-01 | Actual cards contain public English, IPA, ordered two dictionary sources/POS/meanings, source context and committed count. A ready result appears while context is pending; completion keeps count, presentation count and deadline. Real rows retain public context; long article is scrollable/selectable. |
| POP-02 | Physical Escape, native Close, activation of fixture, outside mouse click and20s inactivity hide the card. Tab resets inactivity. Late main/context after dismissal cannot reopen or create an obsolete history event. |
| POP-03 | Blank public space yields not_found; controlled no_network/blocked/timeout, missing tesseract, capture/cursor errors and separate history/cache failures reach actual production cards. Useful translation survives persistence failure; no false saved count appears. Supplemental provider failure retains both offline sources. |
| POP-05 | Same owner switches between actual native Breeze palettes at100/125/150/200%. Qt/KWin geometry is compared with pixel-rounding tolerance; outer card is inside an output and has no intersection with independently read actual Plasma dock rectangles. |

The main run records23 true gates; supplemental gates cover blank space,
physical outside click, physical mouse primary and offline content preservation.
Both runs require all five restoration flags. Security controls and UI review
are independent artifacts, not substitutes for these native observations.

## Corrections proved during integration

- Fixed loading-to-result layout caching and wrapping of unbroken text. A long
  article now receives substantial bounded card height and one outer scrollbar.
- Refit late context documents without resetting focus/count/timer; nested
  layout tests run real event-loop turns before checking scroll growth.
- Native text viewports inherit the card background instead of drawing stripes.
- At125%, KWin can return fractional dimensions such as314.4; parsing preserves
  them and geometry comparisons tolerate at most one logical pixel.
- At150%, QScreen.availableGeometry alone allowed the footer under the panel.
  The worker now reads fixed Plasma dock metadata from KWin, computes the work
  area, and passes it with the frozen event. The final eight native appearances
  pass containment/nonintersection; both150% screenshots independently confirm
  the footer above the panel. UI audit is24/24 after remediation.
- Native tray menus are rendered by Plasma: QMenu.isVisible is false even when
  the real menu is open. The gate observes aboutToShow plus physical Quit and
  independent service disappearance rather than inventing Qt menu coordinates.
- Full Windows suites initially exposed nondeterministic Qt teardown access
  violations after unittest printed OK. Tests now explicitly dispose native
  windows/menu/owner and drain deferred deletions; final subprocess exit codes
  are0 on both Windows interpreters. Printed OK alone was not accepted.

## Timing and limits

In the final main run, first useful paint after engine request admission was
201.0ms for new primary,783.0ms for repeated-primary OCR,606.6ms for early
context preview,585.4ms for queued B, and259.8ms for the long article. Eight
primary appearance samples have median221.0ms. Cold-owner engine admission to
paint is210.6ms; this excludes process startup/launcher time and is not cold
end-to-end latency. Loading and final context are recorded separately.

Online transport is controlled fixture data/failures, not live-provider speed.
Only one VM monitor is exposed; negative origins/edge docks use portable tests.
These samples do not accept Phase8 PERF-01 or claim a general latency guarantee.
Historical Arch canceled multiprocessing-worker SemLock teardown traces can
appear on stderr; the final full suite still exits0. No human testing claimed.

## Regression and privacy

Final suites:561 tests on Windows Python3.14.3 (29.331s,7 skips), Windows
Python3.12.0 (29.144s,7 skips), Arch Python3.14.8 (11.613s,3 skips), all exit0.
Focused engine/Qt/platform/harness/translation-ready/CLI/import suite:53 pass.
Skips are existing platform/external-fixture limits, not substituted live gates.

Both runs restore display, unchanged real theme bytes, owned desktop bytes,
stopped owned processes and shortcut availability. Temporary native theme
configuration is isolated; unrelated desktop files/processes are preserved.
After independent visual review,29 specifically owned temporary PNG files from
successful and failed runs were deleted by exact path, then empty directories
removed. Final screenshot paths are absent and no owned runtime profile remains.
The raw JSON contains only fixed schema/public enums, booleans, geometry, counts,
timing and ownership identifiers; arbitrary primary/source text and activation
tokens are not retained. Re-running the harness requires repeating visual review
and explicit image cleanup before acceptance.
