---
phase: 07-settings-package
plan: 03
subsystem: settings-native
tags: [qt, settings, asynchronous-apply, rollback, reload]
requires:
  - phase: 07-01
    provides: Validated atomic config and monotonic worker reload acknowledgements
  - phase: 07-02
    provides: Owned actual-shortcut transaction with readback and rollback
provides:
  - Reusable native Settings with effective binding and ordered dictionary identities
  - Serial asynchronous apply and exact config/key restoration with acknowledgement
  - Owner reload-event routing and acknowledged next-popup timeout
affects: [07-05, 08-vm]
tech-stack:
  added: []
  patterns: [lazy native factory, queued operation completion, separate reload revision]
key-files:
  created:
    - lookup/settings_gui.py
    - tests/test_settings_gui.py
  modified:
    - lookup/gui.py
    - lookup/config.py
    - tests/test_app_gui.py
    - tests/test_config.py
key-decisions:
  - Preserve external KDE bindings unless the shortcut field was explicitly edited.
  - Run config/discovery/registry operations on one serial background transaction and wait for the worker revision before success.
  - Retain configured missing dictionary IDs during normal saves but allow exact known-field rollback without dropping unrelated keys or clients.
  - Reopening discards ordinary unsaved drafts; an in-flight captured apply survives window closure and remains disabled until its outcome.
requirements-completed: []
duration: not-recorded
completed: 2026-10-28
---

# Phase 7 Plan 03: Native Acknowledged Settings Summary

**Native settings now apply shortcut, dictionary/order, online, timeout and autostart changes through a serial transaction and revision-specific worker acknowledgement, with explicit restoration states.**

Implementation: `lookup/settings_gui.py` and `lookup/gui.py`.

## Accomplishments and Consumer Contract

- Lazy `settings_gui.components()` returns `(SettingsWindow, ApplyController)`. `SettingsWindow(controller)` is reusable and nonmodal; it uses the system font/palette, plain status/help text, scrollable groups and native keyboard controls. Closing ordinary edits does not save; reopening loads current saved/effective values. Closing during an apply does not cancel or replace its captured snapshot.
- The window exposes `shortcut`, `actual_binding`, `dictionaries`, `up_button`, `down_button`, `timeout`, `online`, `autostart`, `apply_button`, `close_button` and `status`. Dictionary IDs live in each item's UserRole; check state and order stay independent, including unavailable configured IDs. All-off is valid and explained. Timeout is an integer 1–300 seconds, default 20.
- `ApplyController(engine,parent=None,...)` owns serial background config/discovery/KDE operations and queues plain results to its QObject. Optional registry/load/save/restore/discover seams support deterministic tests. No worker-owned dictionary set, SQLite connection or retained Qt widget crosses threads.
- `pending` and `reload_revision` expose operation state. `state` emits fixed pending/loaded/result payloads; `applied` carries only an acknowledged Config. `ack(event)` matches reload_revision separately from lookup identity; wrong/late revisions are ignored. Finite acknowledgement timeouts start restoration rather than announcing success.
- Actual KDE binding readback populates the shortcut editor and label. The snapshot's shortcut_edited flag gates active registry changes and saving the shortcut field, preserving external overrides during unrelated edits. Explicit edits use the owned transaction, conflict checking/readback and rollback. The verified label updates only after successful acknowledgement.
- Save errors restore a changed key before reporting. Reload errors/timeouts restore the previous known config fields and key, then request/await a separate restoration reload. Config restoration, key restoration and unconfirmed runtime restoration have distinct private messages; no result claims false success. Failed edits remain available for retry.
- `shutdown()` waits through bounded pending preparation and restores uncommitted config/key changes before controller completion. Owner quit keeps its event loop alive until the settings job and existing worker/focus jobs finish. A closed settings widget is never reopened by a background reply.
- Owner enables and reuses the Settings tray action, retaining all three actions. It invalidates the displayed lookup/card snapshot on Apply and reload, routes reload events before lookup-ID filtering, and updates only the next popup's timeout after acknowledgement. Startup timeout config is also read off the GUI thread. Existing accepted card/history snapshots and connection ownership remain unchanged.

## Task Commits

1. Task 1 RED: `dc8db45` — native controls, effective binding, serial apply, acknowledgement, restoration and responsive-close contracts.
2. Task 1 GREEN: `35bdeae` — native Settings/controller and exact rollback config seam.
3. Task 2 GREEN: `c3f4c8a` — reusable Owner wiring, independent revision routing, next-popup timeout and shutdown behavior.

## Validation Results

- Final focused settings/GUI/app/learning/config/core-import suite: **93 tests OK**, 2.735 seconds, exit 0.
- Final full discovery: **692 tests OK, 8 skipped**, 26.499 seconds, exit 0. Existing controlled VM setup-error output reported every restoration flag true.
- Real offscreen widget tests cover ordered enabled/missing dictionary IDs, all-off/offline help, external override preservation, no speculative field effects, single-chord validation, Space/Enter/Escape actions, actual-key label, empty dictionaries and immutable pending snapshots.
- Barrier/queued tests cover off-main-thread config and registry calls, responsive close/reopen, mismatched acknowledgements, conflict/save errors, key/config restoration, acknowledgement timeout, restoration errors, thread-start retry, shutdown during preparation, stale lookup rejection and exact next-popup timer duration.
- Core regression proves normal saves retain missing IDs, explicit rollback restores the exact old dictionary set, and unrelated JSON data/clients survive both paths.
- Whitespace checks on all six owned source/test files: exit 0. No tracked deletions or unresolved implementation stubs.

## Deviations and Limits

- **[Rule 2 — exact config restoration; parent-authorized ownership extension]** Normal config.save intentionally retains omitted dictionary IDs, so using it unchanged for rollback retained newly applied dictionaries. Added keyword-only retain_missing=True with unchanged normal behavior; the restoration path passes False. Only known edited fields are restored; unrelated keys and clients remain preserved. Added a meaningful regression in tests/test_config.py.
- **[Rule 1 — initial asynchronous load race]** Opening Settings while the startup config read was pending initially skipped form loading. It now queues the full read after initialization, keeping untouched controls disabled until loaded.
- **[Rule 2 — shutdown ownership]** Owner quit waits for settings restoration before final exit. Background completion uses private fixed statuses and queued plain values; it does not access a deleted window or share SQLite resources.
- This unit establishes deterministic/offscreen agent evidence, not human acceptance or actual physical KDE key replacement, native themes/scaling, login/autostart, installation or removal. Those mandatory native/package gates remain plan 05. No live clone/session/shortcut mutation was performed here.
- The parallel packaging/doctor executor owns its files and native build evidence. Global STATE/ROADMAP/requirements/config and pre-existing user documents were left to the parent orchestrator and were not staged.

## Self-Check: PASSED

All six owned implementation/test files and this summary exist. Task commits dc8db45, 35bdeae and c3f4c8a exist. Fresh final verification passed after the last source change; no known stub prevents this unit's goal.
