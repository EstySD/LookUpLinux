---
phase: 07-settings-package
status: complete
source: agent acceptance under explicit --auto
started: 2026-10-28
updated: 2026-10-29
native_strict_accepted: false
verification_exceptions: 1
---

# Phase 7 Product Acceptance

These are agent observations, not human testing. Product tests pass; strict native acceptance remains false because original VM byte preservation failed. `07-VERIFICATION.md` records the explicit scoped agent continuation exception and unchanged raw evidence.

## Current Test

[product testing complete; preservation exception recorded]

## Tests

### 1. Effective native settings
expected: Saved physical key, dictionary order/enabled state, online policy and timeout affect the same running application; stale work cannot overwrite it.
result: pass
source: actual installed native/physical observations, controlled policy/error oracles and independent code/tests

### 2. Real configurable login
expected: A real subsequent SDDM login starts the installed app only when enabled, without observer invocation.
result: pass
source: enabled session48 PID2418 and disabled session22 samples; independent sample/argv/duration assertions

### 3. Package, authorized capture and removal
expected: makepkg installs dependencies, private helper, Mueller, launchers and key; authorized physical capture works; removal deactivates owned key/files and preserves user/unrelated data.
result: pass
source: actual makepkg/pacman, physical installed capture/removal input, registry/file/hash evidence; loaded daemon stopped separately via actual tray Quit

### 4. Dictionary folder and rescan
expected: Actual destination is selectable/openable in native file manager; copied dictionaries are discovered through unchanged-field Apply without restarting.
result: pass
source: actual Dolphin URL, copied StarDict sets, same-Engine acknowledged rescan/next results and focused failure/empty-root tests

### 5. Guide and diagnostic
expected: Russian README explains install/manual KDE shortcut/settings/removal; doctor reports actionable healthy/missing/damaged/offline status without lookup side effects.
result: pass
source: independent README/code inspection, installed doctor exit/profile-inventory records and focused tests

## Product Summary

total: 5
passed: 5
issues: 0
pending: 0
skipped: 0

## Explicit Operational Exception

Original disk preservation **failed**, leaving raw native `passed:false` and cleanup 5/6. This is not counted as a passing UAT product test or silently discarded. Separate original GUI activity has unknown actor; original bytes were not restored. One scoped agent exception permits workflow continuation under explicit --auto, as recorded in the verification frontmatter. Unrelated entries/data retention and five other cleanup predicates are independently verified. No human acceptance or all-resources-restored claim is made.
