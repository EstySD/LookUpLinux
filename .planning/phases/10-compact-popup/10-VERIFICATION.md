---
phase: 10-compact-popup
status: passed
score: 4/4 must-haves verified
verified: 2026-11-02T11:56:54Z
overrides_applied: 0
acceptance: independent_agent
verified_at: 2026-11-02
implementation_verification: passed_offscreen
target_verification: not_performed_guard_blocked
human_acceptance: not_performed
requirements: [POP-06, SET-02]
---

# Phase 10 — Independent goal verification

**Goal:** User sees the requested word and meanings first and controls unwanted popup blocks.

Independent initial verification of final source `2cb628a`. The previous executor report and summary were inputs, not proof by themselves. Code, data flow, native tests and both screenshot artifacts were checked independently. No overrides applied. Acceptance is by agents; human and live KDE acceptance are not claimed.

## Observable truths

Roadmap criteria take precedence over plan wording. Overlapping plan truths are merged; article disclosure is retained as an additional plan truth.

| # | Truth | Status | Independent evidence |
|---|---|---|---|
| 1 | Offline-only lookup places the requested word and relevant meanings at the start; missing-photo limits are explicit. | VERIFIED | `lookup/gui.py:278` renders the key, then all dictionary summaries in one loop before the full-text loop. Structured senses remain visible and unstructured articles have a 240-character preview. `test_compact_offline_summaries_precede_expandable_articles` passes with a long first article, useful later dictionary and unstructured text. Both screenshots were independently viewed. |
| 2 | User hides context/configures agreed blocks; later requests and restart retain choices. | VERIFIED | Three strict boolean fields flow through JSON load/save, native snapshots, matching apply acknowledgement and rollback. Owner initialized/applied signals call `_settings_applied` (`lookup/gui.py:501`, `560`). Each result snapshots preferences; late callbacks use them. Config round-trip, controls/reopen/rollback, next-request and new-owner initialization tests pass. |
| 3 | Hidden blocks preserve useful results and card saving. | VERIFIED | Guards only change widgets. `_bind_displayed` (`lookup/gui.py:585`) still uses Result/event meaning, source and span; `add_card` ignores display preferences. A native test hides context, accepts late enrichment, saves and reads back the real SQLite card with the latest valid pair. Existing immutable-card/history/error tests also pass. |
| 4 | Full articles expand/collapse without removing summaries or changing request identity, within existing rendering bounds. | VERIFIED | Native checkable buttons toggle associated plain-text widgets and use existing screen sizing. Keyboard Space/Enter, identity/bounds and long-name checks pass. Caption elides only metadata; full accessible names/tooltips remain. Character/block caps and visible truncation are retained. |

**Score: 4/4.** No FAILED or UNCERTAIN must-have remains in this phase's stated contract.

## Artifacts, links and data flow

| Artifact | Substantive and wired evidence |
|---|---|
| `lookup/config.py` | Real JSON-backed defaults and strict independent parsing; existing atomic merge/save and invalid-write preservation. Native settings/controller and Engine resources consume loaded Config. |
| `lookup/settings_gui.py` | Actual checkboxes, snapshot/edit/pending state, saved-state refresh. Controller defaults to real config load/save; acknowledgement emits applied and rollback restores prior edited fields. |
| `lookup/gui.py` | Real summary/detail loops, disclosures and preference guards. Owner receives actual Engine ready/context Results; `value.articles` supplies rendered data. Config reaches Popup through initialized/applied signals; cards retain Result/event inputs. |
| `10-VERIFICATION.md` | Requirement-level canonical status/evidence report consumed by phase tooling. |

Artifact helper reports 4/4 passed. The key-link helper reports literal-path false negatives for Python relative imports and the coverage link to tests. Manual checks confirm intended links: settings imports/calls config; Owner imports settings components and connects initialized/applied; native GUI tests instantiate actual Owner/Popup and send ready/context events. Production correctly does not import tests. No orphaned/stub artifact or disconnected data source was found.

## Independent behavioral result

On the final source, the verifier registered installed Segoe UI in the offscreen test process only and ran all three focused modules: **88 tests, OK, zero skips, 4.529 s**. Both screenshots were independently inspected as readable. Source whitespace check passed. No product font code was changed. The executor's full result below is additional same-source regression evidence, not the sole acceptance basis; that broad run was not redundantly repeated.

## Automated evidence

| Check | Fresh result |
|---|---|
| `python -m unittest tests.test_config tests.test_settings_gui tests.test_app_gui -q` | 88 tests, OK, zero skips, 4.948 s |
| `python -m unittest discover -s tests -q` | 834 tests, OK, 11 platform skips, 42.323 s |
| Focused suite with registered system Segoe UI 10 font | 88 tests, OK, zero skips, 4.711 s |
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

`10-offscreen-long-name.png` verifies the review correction: even a 750-character dictionary name leaves the meanings and disclosure action visible. Summary names are bounded with full tooltips/accessibility; disclosure elides only the name portion using live font metrics. The long-name regression also verifies Enter activation.

## Target limitation

The documented owned-clone preflight `./tools/check_package_vm.ps1 -Action Check` rejects operation with `Original VM must remain powered off`. The original `arch-kde` VM is running. It was not stopped, controlled or entered; the guard was not bypassed. Live KDE expansion, focus, placement and restart acceptance therefore remains pending until the documented clone preconditions hold. Missing Danila source inputs and human feedback remain separate limitations.

## Threat checks

- T-10-01: new values require strict booleans; invalid saves retain original bytes; atomic merge is unchanged.
- T-10-02: all summaries precede detail budget consumption; existing character/block limits remain, with visible truncation notice and bounded screen sizing.
- T-10-03: per-result preference snapshot guards both initial context and late updates. Save/cache warnings stay independent.
- T-10-04: dictionary and context widgets remain plain text; disclosure introduces no HTML/navigation or network boundary.

## Adversarial checks and continuation decision

Possible saved-but-unwired preferences, late callbacks revealing hidden blocks, and long articles/metadata burying meanings were checked against actual paths and native regressions. Generic timeout, failed save/reload and rollback-error tests run in the same focused suite; the new preference rollback case confirms no successful apply signal after failure. The clean independent code review includes the caption and heading corrections through `2cb628a`.

The FakeEngine boundary is explicit: these tests establish native widget/application data flow, not actual KWin activation, focus or fullscreen behavior. No live claim follows from them. Both Phase 10 requirement IDs are in plan 10-01 and supported above; no orphaned phase requirement was found. Requirement checkboxes/state remain the orchestrator's responsibility.

**The remaining compositor limitation is nonblocking for Phase 10.** Its roadmap contract requires compact popup behavior, persistent visibility settings and preserved saving; all have actual code and executed native-widget evidence. The user authorizes agent acceptance under `--auto` and continuation with honest nonblocking limits. No new live fullscreen/input/capture proof is a Phase 10 success criterion. This is not an override or a claimed pass of KDE testing. Danila's missing-photo reproduction limit is explicitly required by the roadmap and remains recorded.

**Phase 11's live research gate remains mandatory:** prove real KDE Wayland capture/input/hover before approving implementation. This phase supplies no such proof and does not authorize bypassing the owned-clone preflight. Milestone-wide integrated target acceptance and human acceptance are not claimed.

No unresolved implementation gap or human-only decision is needed to accept the four Phase 10 truths. No human-verification items are required for this phase's canonical status.

Verified independently by gsd-verifier, 2026-11-02T11:56:54Z.
