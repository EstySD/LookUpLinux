---
phase: 13-gui
plan: 01
subsystem: gui
requirements-completed: [TRIG-07, SET-03]
completed: 2026-11-03
duration: 18min
---

# Discoverable native home

Explicit launcher and --app open a native home with actual shortcut instructions and existing settings/words/review navigation. Closing keeps background mode; tray clicks reopen home. --background and autostart do not show home; cold hotkey launch uses --background. Repeated launcher forwards validated token through DBus and activates the owned home window through the bounded KDE helper.

Added visible Home.desktop while retaining hidden shortcut desktop identity, owned source-entry protections, staging/public/local packaging and hardening inventories. Fixed legacy generated-entry recognition for both older and current exact layouts.

Final host and Linux suites: 865 tests each, zero failures/errors; 11 and 4 skips respectively. Native Wayland actual Owner probe opens all three child windows, reopens the singleton and launches real CLI --app against a scoped test DBus identity, proving existing home receives focus without interacting with installed owner. home-evidence/home.png visually inspected; no clipping or new styles. Real Yomitan checks continue passing on both platforms. Source hashes and command: batch-manifest.json and 13-VALIDATION.md.

Independent static review initially found activation-token/focus gap, corrected before final successful batch. Agent acceptance only; no human acceptance or full package-install claim.
