# Phase 19 Summary: Fullscreen word selection

**Status:** Complete (offscreen/VM-tested; no Steam Deck hardware)
**Completed:** 2026-11-26
**Requirements:** SEL-01, SEL-02, SEL-03, GAME-05

## What changed

- Extended `lookup/selection_gui.SelectionLayer` with explicit touch handling
  (`TouchBegin`), a visible arrow/DPad crosshair, Enter to select, and a
  touch-sized close button (32 px minimum). The instruction text now names
  touch, DPad and Enter.
- Wired the Gaming `Trigger` to one bounded `gaming.capture_gamescope()` call
  and the existing `enqueue_scene` flow, so the frozen frame, word selection,
  translation card and Esc dismissal all reuse the tested scene pipeline.
- Repeated Gaming triggers close the active scene instead of stacking windows;
  a failed capture leaves no stuck window.

## Verification

| Check | Result | Evidence |
|-------|--------|----------|
| Host full pytest suite | 892 passed, 13 skipped, 1737 subtests | `.planning/phases/19-flexible-selection/full-tests.log` |
| Shared `arch-kde` VM full unittest suite | 905 passed, 22 skipped | `.planning/phases/19-flexible-selection/vm-tests.log` |
| Crosshair + deck-resolution offscreen tests | Pass | `tests/test_selection_gui.py` |
| Gaming trigger capture/debounce tests | Pass | `tests/test_app_gui.py` |

## Known limitations (honest status)

- Touch was verified through Qt touch-event handling and offscreen mouse
  mapping, not on a physical Steam Deck touchscreen.
- Controller DPad support relies on Steam Input mapping DPad to arrow keys;
  per-game layout setup is documented in Phase 21 and remains hardware-unverified.
- Focus return to the game was not verified on real gamescope.
