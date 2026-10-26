---
phase: 04-vm
plan: 02
subsystem: platform-spike
status: complete
completed: 2026-10-26
requirements-completed: [TRIG-01, CAPT-01]
key-files:
  created: [tools/vm_spike.py, tests/test_vm_spike.py, tools/lookup-vm-spike.desktop.in]
---

Implemented the narrow Qt spike with atomic per-session DBus ownership, bounded
Trigger/Status/Quit slots, one coalescing capture worker, a public content fixture,
frameless popup, retained tray/menu, and safely quoted unique desktop entry.
The spike never opens dictionaries or SQLite. Only the known public word english
may enter diagnostic results. Activation tokens are bounded, forwarded on warm
IPC, discarded after handling, and removed from child environments.

Real VM testing found that the SSH environment must set QT_QPA_PLATFORMTHEME=kde
for Breeze icons and native tray menus. Warm clients use QCoreApplication to
avoid GUI startup focus effects; a cold client starts an atomic GUI owner.
Qt exposes no public activation-token setter in the installed PyQt binding;
the verified fallback is owned kdotool move/raise/activate, without KWin policy
changes. Qt geometry can remain (0,0) under Wayland, so KWin geometry is checked.
Deactivation handling arms after initial compositor placement/activation settles.

Live proof: physical Meta+Shift+D repeatedly wakes one owner; physical cold
launch creates a different owner. Popup placement/focus and Escape succeed at
four scales, separate focus loss hides it, and a physical panel right-click then
menu click emits tray-menu and tray-action. Plan03 retains detailed evidence.

Validation after review fixes: 528 tests on Windows 3.14/3.12 and Arch 3.14,
all successful (7/7/3 existing skips); 32 focused adapter/spike/image/import
tests pass. T-04-06..10 closed in independent 04-SECURITY.md.
