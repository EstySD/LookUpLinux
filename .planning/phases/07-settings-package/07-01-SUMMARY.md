---
phase: 07-settings-package
plan: 01
subsystem: settings-worker
tags: [config, atomic-save, reload, concurrency]
requires:
  - phase: 06-words-cards
    provides: Accepted generation-safe lookup and immutable learning snapshots
provides:
  - Compatible validated settings and private atomic JSON merge
  - Worker-owned resource reload with monotonic revision acknowledgement
  - Explicit retryable reload failure without stale history or card changes
affects: [07-02, 07-03, 07-05]
tech-stack:
  added: []
  patterns: [per-field validation, private atomic replacement, revision-specific acknowledgement]
key-files:
  created: []
  modified:
    - lookup/config.py
    - lookup/app.py
    - tests/test_config.py
    - tests/test_app.py
key-decisions:
  - Preserve existing Config positional fields and append defaulted shortcut, popup_timeout and autostart.
  - Save only validated edited fields while retaining unrelated keys, clients and configured-but-missing dictionary IDs.
  - Keep one Engine and monotonically increasing lookup generations; acknowledge reloads with a separate revision.
  - Failed resource reopen leaves an explicit retryable error state, never a false applied acknowledgement.
requirements-completed: []
duration: 8min
completed: 2026-10-28
---

# Phase 7 Plan 01: Settings Persistence and Worker Reload Summary

**Validated settings now save atomically, and the existing lookup worker reopens its own resources with a revision-specific acknowledgement while rejecting stale work.**

Implementation: `lookup/config.py` and `lookup/app.py`.

## Accomplishments and Consumer Contract

- Frozen `Config` retains dictionaries/online/clients positional compatibility and adds shortcut `Meta+Shift+D`, integer popup_timeout `20` seconds within 1–300, and autostart `True`. Loaded invalid scalar fields fall back independently; shortcut core validation is bounded text/control validation, with actual Qt single-chord validation reserved for the lifecycle adapter.
- `config.save(changes,path=None)` accepts edited JSON-shaped known fields and returns the validated Config. It preserves unknown existing keys, clients and configured dictionary IDs omitted from a discovered subset; dictionary edits establish the submitted order and append retained missing entries. Invalid edits refuse saving. An unmergeable existing file is preserved with a fixed error rather than silently discarded.
- Explicit save uses a private sibling temporary file, flush/fsync and atomic replace with cleanup. Loading/path resolution/import creates nothing. `ConfigError.reason` is one of invalid_value, invalid_file or unavailable and contains no file contents or private path details.
- `Engine.request_reload()` returns a monotonically increasing revision, or None after stop. It invalidates current lookup work through the existing ever-increasing generation and coalesces unopened pending reloads. The same Engine remains alive; it is never replaced or reset.
- Reload acknowledgements use `Event.stage == 'reload'`, `Event.reload_revision`, and `Event.error` equal to None or reload_failed. Consumers must handle these events before lookup-ID filtering and compare their expected revision; lookup identity is not the acknowledgement identity. Events contain no worker-owned SQLite or dictionary object.
- The owning worker closes/reopens resource contexts between jobs and prioritizes newer pending reloads before queued lookups. Superseded acknowledgements retain their old revision. Catastrophic dictionary/database reopen errors cannot falsely report success; the worker remains available, queued lookups receive an explicit reload_failed state, and another request_reload retries.
- Pre-reload replies cannot publish or enrich current history/cards. Accepted history remains counted once, saved card snapshots remain unchanged, and online-off controls new lookups after reload. Already-started network requests are not claimed to be canceled.

## Task Commits

1. Task 1 RED: `20fb6c5` — settings defaults, per-field fallback, preservation, private atomic replacement and refusal contracts.
2. Task 1 GREEN: `63facbb` — compatible validated atomic settings persistence.
3. Task 2 RED: `ef7d7e9` — acknowledged worker reload, stale generations, ownership and retry contracts.
4. Task 2 GREEN: `28b637a` — worker-owned reopen and revision-specific acknowledgements.

## Validation Results

- Config/path/core-import focused suite: **40 tests OK**.
- Final app/early-translation/learning/config focused suite: **75 tests OK**, 1.514 seconds.
- Final full discovery: **651 tests OK, 8 skipped**, 26.286 seconds, exit 0. Existing controlled VM setup-error output reported all restoration flags true.
- Barrier-based tests prove next lookup sees saved dictionary order/online state, old ready replies are rejected, all dictionary/resource open/close operations remain on one non-GUI worker thread, superseded acknowledgements retain separate revisions, reopen errors are retryable, partial resource errors do not report applied, and delayed contextual enrichment cannot alter saved history pairs/cards.
- Atomic-save tests verify preserved bytes and temporary cleanup on replacement error, strict edited-field refusal, unrelated-key/client/missing-ID retention and private POSIX modes when available.
- `git diff --check` on owned files: exit 0. No tracked deletions or unresolved implementation stubs. Parent audit reported no blocking finding.

## Deviations and Limits

- **[Rule 2 — preserve unmergeable source]** Saving malformed, oversized or unreadable existing JSON refuses with a fixed error instead of overwriting data that cannot be safely merged. Tolerant loading remains unchanged.
- **[Rule 2 — explicit partial reopen state]** Resources now carry a defaulted reload_error for catastrophic dictionary open errors, and save_error also prevents a successful reload acknowledgement. Normal initial lookup fallback behavior remains available; failed reload enters an explicit error state until retry.
- Native settings/timeout effects, physical shortcut replacement, actual login/autostart and package install/remove are not established by this core unit. They remain later plans, with native acceptance in plan 05. No human acceptance or completed Phase 7 requirement is claimed here.
- STATE, ROADMAP, requirements, workflow config, research changes and pre-existing user documents remain owned by the parent orchestrator and were not staged by this executor.

## Self-Check: PASSED

All four owned implementation/test files and this summary exist. Task commits `20fb6c5`, `63facbb`, `ef7d7e9` and `28b637a` exist. Fresh final verification passed after the last code change; no known stub prevents this core unit's goal.
