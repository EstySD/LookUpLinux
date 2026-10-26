---
phase: 05-app
plan: 02
status: complete
completed: 2026-10-26
requirements-completed: []
key-files:
  created: [lookup/gui.py, tests/test_app_gui.py, tools/lookup.desktop.in]
  modified: [lookup/__main__.py, tests/test_cli.py, tests/test_core_imports.py]
---

Implemented the lazy native PyQt6 application, atomic session D-Bus owner,
bounded fixed Trigger client and cold launch. Existing CLI/core imports remain
Qt-free. A single worker owns dictionary/SQLite resources; GUI events recheck
request identity. One bounded focus worker places and activates the owned window
using the Phase4 kdotool route. Activation tokens are cleared without logging.

The native tray exposes three disabled future actions and Quit. The selectable
plain-text card follows the approved Breeze palette/font/layout, with one outer
scroll area, Close/Escape/focus-loss dismissal and a 20-second inactivity timer.
Context updates preserve focus/deadline/count. Programmatic capture hiding does
not invalidate a request; user dismissal does. Quit waits for worker cleanup.
Cache/history errors remain separate and useful translations stay visible.

Read-only QTextEdit blocks provide real wrapping for unbroken tokens without
loading rich resources or inserting copy-altering characters. Body rendering is
bounded to 32000 characters/128 blocks, context sections to 8000, with an explicit
truncation notice. Loading-to-result sizing accounts for newly visible children
synchronously. Native font changes update semantic text sizes.

Fresh validation: Windows Python3.14 full suite 554 tests, 25.846s, 7 skips;
Python3.12 full suite 554 tests, 23.602s, 7 skips. Native GUI/CLI/import subset
22 tests passed; Arch native GUI subset 10 tests passed. Qt coarse-timer rounding
required comparing remaining time before/after passive movement rather than
assuming an exact requested interval. git diff --check passed.

Actual production owner in Arch/KDE received physical Meta+Shift+D, displayed
new primary with IPA, ordered dictionary sources and one real history count;
repeat selection routed to OCR. Warm useful paint was observed separately from
engine ready and loading (about190ms for primary in an initial run). Light/dark
Breeze palettes were observed, with Qt and KWin geometry agreeing at100%.
These are preliminary integration observations: plan03 owns complete scale,
race, failure, lifecycle, visual and restoration acceptance. No requirement is
marked accepted here and no human testing is claimed.
