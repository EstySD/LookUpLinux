---
phase: 10-compact-popup
status: pending
verified_at: 2026-11-02
implementation_verification: passed_offscreen
target_verification: blocked
human_acceptance: not_performed
requirements: [POP-06, SET-02]
---

# Phase 10 — Implementation verification

Agent evidence for implementation commit `5dab98f`; independent phase acceptance belongs to the orchestrator/verifier.

## Automated evidence

| Check | Fresh result |
|---|---|
| `python -m unittest tests.test_config tests.test_settings_gui tests.test_app_gui -q` | 87 tests, OK, zero skips, 4.655 s |
| `python -m unittest discover -s tests -q` | 833 tests, OK, 11 platform skips, 41.851 s |
| Focused suite with registered system Segoe UI 10 font | 87 tests, OK, zero skips, 4.630 s |
| `git diff --check` | No whitespace errors; Git emitted only existing LF/CRLF conversion notices |

The full suite's controlled setup-failure JSON is expected restoration-test output; its unittest result is successful. Existing user OCR edits were present during verification and preserved outside these commits.

## Requirement evidence

| Requirement | Implemented behavior and executable evidence | Acceptance boundary |
|---|---|---|
| POP-06 | `test_compact_offline_summaries_precede_expandable_articles`: offline requested-word header, all structured summaries and bounded unstructured preview precede full article details; keyboard expand/collapse preserves request identity and bounded popup height. Existing oversized-text/plain-text tests pass. | Synthetic articles prove ordering; Danila's missing photo/source article cannot be reproduced exactly. |
| SET-02 | Config defaults/strict validation/round-trip preserve unrelated keys; native controls save/reopen and rollback after failed reload. Owner initialized/applied preferences affect the next request and a restarted owner. | Host native offscreen tests pass; real KDE compositor interaction remains pending. |
| Preserved cards/context | `test_hidden_blocks_stay_hidden_after_late_updates_and_cards_keep_context` proves disabled blocks remain hidden after enrichment while cards retain the latest valid meaning, source and span. Existing immutable-card/history and timer/focus/cancellation tests pass. | No card/history/provider storage path was changed. |

## Visual evidence

`10-offscreen-compact.png` shows a readable synthetic offline result: requested word, IPA, two dictionary summaries, offline status, two collapsed article controls and history count. Context is hidden. The host offscreen Qt platform reports zero font families by default; the evidence-only process registered `C:/Windows/Fonts/segoeui.ttf` and selected Segoe UI 10. No product font or theme code was changed. This is host offscreen rendering, not Breeze/KDE or human acceptance.

## Target limitation

The documented owned-clone preflight `./tools/check_package_vm.ps1 -Action Check` rejects operation with `Original VM must remain powered off`. The original `arch-kde` VM is running. It was not stopped, controlled or entered; the guard was not bypassed. Live KDE expansion, focus, placement and restart acceptance therefore remains pending until the documented clone preconditions hold. Missing Danila source inputs and human feedback remain separate limitations.

## Threat checks

- T-10-01: new values require strict booleans; invalid saves retain original bytes; atomic merge is unchanged.
- T-10-02: all summaries precede detail budget consumption; existing character/block limits remain, with visible truncation notice and bounded screen sizing.
- T-10-03: per-result preference snapshot guards both initial context and late updates. Save/cache warnings stay independent.
- T-10-04: dictionary and context widgets remain plain text; disclosure introduces no HTML/navigation or network boundary.
