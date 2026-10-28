---
phase: 07-settings-package
plan: 02
subsystem: kde-lifecycle
tags: [kde, dbus, shortcut, desktop, autostart]
requires:
  - phase: 07-01
    provides: Config autostart/shortcut fields and acknowledged resource reload
provides:
  - Owned active-shortcut transaction with conflict/readback/rollback contracts
  - Source/package desktop ownership and safe shadow migration
  - Pre-Qt config-gated autostart and centralized private helper selection
affects: [07-03, 07-04, 07-05]
tech-stack:
  added: []
  patterns: [typed legacy DBus arrays, narrow owned action identity, private helper resolution]
key-files:
  created:
    - lookup/lifecycle.py
    - tests/test_lifecycle.py
  modified:
    - lookup/platform.py
    - lookup/gui.py
    - lookup/__main__.py
    - tests/test_platform.py
    - tests/test_cli.py
key-decisions:
  - Resolve the actual registered four-field action identity; never invent friendly labels.
  - Only explicit shortcut edits change active registry keys; ordinary entry registration preserves overrides.
  - Refuse symlinks/unowned files and preflight both source shadows before package migration.
  - Prefer a present private installed helper even if damaged, so errors remain visible rather than silently falling back.
requirements-completed: []
duration: 14min
completed: 2026-10-28
---

# Phase 7 Plan 02: Owned KDE Lifecycle Summary

**The application now has a bounded owned-shortcut transaction, config-gated login entrypoint, safe source/package launch paths and one private-helper resolver.**

Implementation: `lookup/lifecycle.py` and `lookup/platform.py`.

## Accomplishments and Consumer API

- `parse_shortcut(text)` returns canonical PortableText and one nonzero combined key; empty, invalid and multi-chord input is refused. `key_text(key)` formats a returned binding key. Qt imports remain lazy.
- `ShortcutRegistry(call=None).inspect()` resolves the actual registered action through allActionsForComponent, requiring exactly the owned desktop/_launch identity, and returns immutable `Binding(action,keys)`. Unknown identity fails safely; friendly labels are read, not assumed.
- `.preflight(text)` returns binding/canonical/key after conflict checking that excludes the owned component. `.change(text)` sets only that owned active action and verifies exact readback, returning `ShortcutTransaction(before,desired,active)`. The caller commits after its save/apply succeeds, or rolls back and verifies previous keys. Readback errors attempt restoration automatically; rollback uncertainty is a distinct fixed error. Restoration also refuses stealing keys from another component.
- Default DBus calls are finite at 1200 ms each. Explicit typed QStringList/int-array arguments avoid PyQt's plain-list variant-array signature. The narrow legacy method contract follows the [primary KDE DBus XML](https://raw.githubusercontent.com/KDE/kglobalaccel/master/src/org.kde.KGlobalAccel.xml). Settings must invoke these bounded synchronous operations on its worker and route completion by operation revision; no worker-owned Qt object is stored in the plain transaction.
- `inspect_shortcut` is a read-only doctor seam. It never registers desktop files or changes a binding. Ordinary startup calls only entry registration, leaving actual KDE overrides unchanged.
- `desktop_text` supports explicit installed/autostart modes; the existing GUI public builder delegates compatibly. Source Exec uses safely quoted absolute Python and checkout Path. Installed entries use /usr/bin/lookup without a checkout Path. Source entries carry an explicit ownership marker; old generated entries are recognized only by matching their generated content. Unowned files and symlinks are refused.
- `ensure_entries` returns desktop/autostart Paths. Source mode writes owned entries and performs finite KSycoca refresh. Package mode creates no user shadows and safely removes pre-existing explicitly owned source shadows only after both entries pass ownership preflight. It never removes settings/history/cards or unrelated files/preferences.
- `launch_command(action)` returns argv and cwd for installed versus source cold start. Only the singleton daemon ensures entries; repeated hotkey clients do not write them. Startup registration errors are retained as owner.lifecycle_error while the daemon remains usable.
- `--autostart` reads saved enabled state before importing GUI/creating Qt. Disabled login exits quietly; enabled login uses the existing singleton app path. Source/system autostart entries use OnlyShowIn=KDE and appropriate absolute Exec/TryExec values.
- `platform.resolve_command` centrally chooses the present /usr/lib/lookup/kdotool, otherwise the normal PATH command. All production kdotool calls, including direct GUI focus calls, pass through platform.run. A damaged present private helper fails visibly rather than selecting a competing global helper.

## Task Commits

1. Task 1 RED: `932ed49` — identity, conflict, readback, rollback and desktop ownership contracts.
2. Task 1 GREEN: `c24627a` — owned shortcut adapter, safe source entries and GUI desktop compatibility.
3. Task 2 RED: `402f456` — pre-Qt login gating, installed ownership migration and private helper contracts.
4. Task 2 GREEN: `a1796a7` — autostart dispatch, source/package cold start, shadow migration and centralized helper.

## Validation Results

- Task 1 lifecycle/GUI/CLI suite: **41 tests OK**.
- Final lifecycle/platform/CLI/core-import/GUI suite: **61 tests OK**, 3.954 seconds.
- Final full discovery: **667 tests OK, 8 skipped**, 26.384 seconds, exit 0. Existing controlled VM setup-error output reported all restoration flags true.
- Tests cover actual versus invented friendly identity, single-chord validation, conflict without writes, readback mismatch/restoration, distinct rollback error, external-override preservation during ordinary registration, owned/unowned/symlink entries, exact legacy recognition, preflight-before-migration, source quoting, installed no-shadow behavior, disabled login with Python -S, CLI exclusivity and every helper execution path through the resolver.
- Authorized read-only clone probe: plain Python action lists marshal as av and are refused by the target; typed QStringList marshals as as and allActionsForComponent returns successfully. The owned action was not registered at probe time. No active key/session/account mutation was performed.
- `git diff --check` for owned files: exit 0. No tracked deletions or unresolved core implementation stubs.

## Deviations and Limits

- **[Rule 2 — source-to-package ownership]** A package desktop could otherwise remain shadowed by an earlier source user entry. Parent authorized narrow same-user cleanup of explicitly owned desktop/autostart shadows, with both entries preflighted before any removal. Unowned entries, redirects, preferences and user data remain untouched.
- **[Rule 2 — PyQt marshalling]** Read-only target evidence required typed argument arrays rather than ordinary Python lists. No substitute unverified registry command or broad config-file edit was introduced.
- DBus setter semantics, old/new physical keys, actual native login/autostart, installed helper/capture and pacman removal are mandatory plan 05 gates. Mock contracts and the read-only probe do not claim those outcomes. Original arch-kde remained untouched; only the separately prepared clone was queried.
- Native Settings acknowledgement/status integration and package files remain following plans. No human acceptance or complete Phase 7 requirement is claimed by this adapter unit.
- Global planning state, research and pre-existing user changes were left to the parent orchestrator.

## Self-Check: PASSED

All seven implementation/test files and this summary exist. Task commits `932ed49`, `c24627a`, `402f456` and `a1796a7` exist. Final verification passed after the last code change; no known stub prevents this adapter unit's goal.
