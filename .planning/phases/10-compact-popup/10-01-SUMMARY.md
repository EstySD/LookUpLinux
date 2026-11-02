---
phase: 10-compact-popup
plan: 01
subsystem: popup
tags: [qt, settings, offline, accessibility]
requires: [09-02]
provides: [compact dictionary summaries, expandable articles, persistent popup block preferences]
affects: [11, 12, 13, 14]
tech-stack:
  added: []
  patterns: [per-result display preference snapshot, native checkable article disclosure]
key-files:
  created: [.planning/phases/10-compact-popup/10-VERIFICATION.md, .planning/phases/10-compact-popup/10-offscreen-compact.png, .planning/phases/10-compact-popup/10-offscreen-long-name.png]
  modified: [lookup/config.py, lookup/settings_gui.py, lookup/gui.py, tests/test_config.py, tests/test_settings_gui.py, tests/test_app_gui.py]
key-decisions:
  - Keep all dictionary summaries before full article details and preserve a bounded unstructured preview.
  - Hide context by default while keeping contextual word meaning independently configurable.
  - Preserve provider/history/card data regardless of presentation preferences.
metrics:
  duration: not_aggregated
  tasks: 3
  files: 10
completed: 2026-11-02
target-acceptance: pending
---

# Phase 10 Plan 01 — Compact popup implementation

Offline results now show dictionary meanings before expandable full articles; three native settings persist context, contextual meaning and initial article expansion preferences through existing acknowledged apply/rollback.

## Tasks and commits

| Task | Commit | Result |
|---|---|---|
| 1 RED | `7b2aceb` | New config and native settings tests failed on missing fields/controls. |
| 1 GREEN | `05fbaff` | Add strict boolean defaults, persistence and native transactional controls; 49 config/settings tests pass. |
| 2 RED | `5cf446e` | Compact ordering, late-hidden blocks/cards and owner-restart regressions fail before implementation. |
| 2 GREEN | `5dab98f` | All dictionary summaries precede details; native keyboard disclosures, snapshot visibility and initialization/apply wiring; 87 focused tests pass. |
| 3 | `0a28c15` | Full suite and readable native offscreen screenshot recorded; target KDE acceptance remains pending. |
| Review correction | `0e6758e`, `2cb628a` | Preserve disclosure action for long names, bound dictionary headings, retain full accessible names/tooltips and add Enter-key/font-metric regression. |

## Validation

Final focused suite: 88 tests, OK, zero skips. Final full suite: 834 tests, OK, 11 platform skips. A focused rerun with registered Segoe UI system font also passes all 88 tests. See `10-VERIFICATION.md` for commands, counts, threat checks and acceptance boundaries. Both screenshot artifacts were visually inspected: ordinary summaries precede collapsed controls, and very long dictionary names preserve useful meanings and the disclosure action.

## Deviations from Plan

- Existing direct settings snapshots may omit the new preference keys; the controller saves only supplied preference edits, preserving compatible callers and existing saved values.
- Presentation regressions that require visible context or large full article geometry explicitly opt into those settings; they continue testing their original contracts under the new compact defaults.
- The offscreen platform has no fonts by default. Screenshot and one additional suite run register an installed font inside the evidence process only; product system-font behavior remains unchanged.
- Live target acceptance could not run: the owned-clone safety guard rejects operation while original `arch-kde` is running. No original VM action or guard bypass was attempted. This is retained as a verification limit; requirements and phase acceptance are left to the independent verifier.
- Independent review found centered long dictionary captions could hide the action. Name-only font-metric elision and bounded summary names correct the same input case while retaining full accessibility/tooltips; the final full suite was rerun after both corrections.

## TDD Gate Compliance

Both implementation tasks have failing-test commits before their corresponding feature commits. Task 2 fixture corrections preserve existing card semantics: a late valid result includes its context/span, and a card created afterward saves that latest displayed pair.

## Preservation and limits

No dependency, database migration, capture or provider behavior change. Existing user edits in `lookup/ocr.py`, `tests/test_ocr_fallback.py` and `.omx/` were not staged or reverted. No human acceptance, reproduction of Danila's missing photo, or live KDE acceptance is claimed.

## Self-Check: PASSED

All six implementation/test files, both screenshots and verification document exist. RED/GREEN commits `7b2aceb`, `05fbaff`, `5cf446e`, `5dab98f` and review corrections `0e6758e`, `2cb628a` are present. Fresh host checks pass after the final source edit. Target acceptance remains explicitly pending.
