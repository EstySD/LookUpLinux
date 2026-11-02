# Phase 10: Compact configurable popup — Research

**Researched:** 2026-11-02
**Domain:** Native Qt popup presentation and persistent preferences
**Confidence:** HIGH for code paths; live KDE acceptance remains to be run.

## User Constraints (from CONTEXT.md)

The following automatic decisions are copied verbatim from `10-CONTEXT.md`. [VERIFIED: 10-CONTEXT.md]

- Context visibility: hide source text and context translation by default for a compact result. Expose a single checkbox for this pair.
- Contextual word meaning: retain by default; expose a separate checkbox so users can hide it without hiding dictionary results.
- Full dictionary article: collapse behind an explicit expand control by default, preserving access to the complete article. Keep structured senses visible before details; do not invent semantic ranking for unstructured text.
- Core word, dictionary senses, errors and card controls remain available. Display preferences never change stored context or saved card content.
- Reuse native Qt settings controls, atomic config save and existing runtime apply/rollback. Existing configurations load sensible defaults; subsequent requests and restart honor saved choices.

**Reproduction limit:** Danila's missing photo and exact source article are unavailable. Use synthetic long articles and offline-only lookup to prove layout/order; do not claim the original defect has been reproduced or human tested. [VERIFIED: 10-CONTEXT.md]

## Phase Requirements

| ID | Description | Research support |
|---|---|---|
| POP-06 | With online translation disabled, the requested word and relevant meanings appear at the start of the popup without searching through a long article. | Render word and structured senses before expandable full text; test multi-dictionary long articles. [VERIFIED: REQUIREMENTS.md, lookup/gui.py] |
| SET-02 | User can hide context and configure the popup blocks agreed during phase discussion; choices apply to subsequent requests and survive restart. | Add independently validated booleans to existing atomic configuration and acknowledged settings transaction. [VERIFIED: REQUIREMENTS.md, lookup/config.py, lookup/settings_gui.py] |

## Project Constraints (from AGENTS.md)

No repository-root AGENTS.md was present when inspected. Session-provided AGENTS instructions require autonomous safe execution, small diffs, relevant inspection, preservation of user changes, proportional tests and verification before completion. Existing OCR changes must remain intact. [VERIFIED: Test-Path/read attempt for AGENTS.md; parent task/session instructions]

## Summary

Use the existing presentation layer and configuration transaction; no new dependencies or storage migration are necessary for the proposed additive booleans. `Popup.result()` currently inserts lemma, transcription, dictionary name, senses and each full article sequentially, so the first long article can precede another dictionary's useful senses. Contextual meaning widgets already precede `body`; source/translation widgets follow it. [VERIFIED: lookup/gui.py:116-349]

The smallest robust implementation adds three display booleans, applies them to Popup through `Owner._settings_applied`, gathers useful senses before details, and places full article widgets behind native expandable controls. Settings do not need to alter Engine, stored history or card snapshots. `translate.short_translation()` is an existing bounded fallback for useful article text when structured senses are absent, but its fallback is only the first line and must not be described as semantic relevance ranking. [VERIFIED: lookup/gui.py:510-549; lookup/translate.py:47-60]

**Primary recommendation:** Keep visibility preferences entirely in presentation; persist through existing Config/save/ApplyController and guard both initial render and asynchronous updates. [VERIFIED: existing architecture in lookup/config.py, lookup/settings_gui.py, lookup/gui.py]

## Architectural Responsibility Map

| Capability | Primary owner | Secondary owner | Rationale |
|---|---|---|---|
| Saved visibility choices | Config/atomic JSON storage | Settings GUI | Existing strict validation and merge preserve unrelated keys. [VERIFIED: lookup/config.py] |
| Apply/rollback | ApplyController | Owner | Existing worker reload acknowledgement governs success. [VERIFIED: lookup/settings_gui.py:135-245] |
| Summary/detail presentation | Popup | Existing Article/Result data | Existing model already exposes senses/text/short translation. [VERIFIED: lookup/gui.py; lookup/dicts.py:Article; lookup/translate.py:Result] |
| History/cards | Existing Engine/learning paths | Owner | Display choices must leave existing snapshot inputs unchanged. [VERIFIED: lookup/app.py:305-345; lookup/gui.py:534-549] |

## Standard Stack

| Component | Verified version | Use |
|---|---|---|
| Python | Host 3.14.3 | Existing stdlib unittest, dataclass and JSON implementation. [VERIFIED: python sys.version probe] |
| PyQt6 / Qt | Host 6.11.0 / 6.11.0 | Existing native checkbox, button, layouts, visibility and offscreen tests. [VERIFIED: PyQt6.QtCore version probe] |
| Target Qt | Prior Phase 9 evidence records 6.12 | KDE live acceptance must be repeated for changed UI; prior evidence does not prove new UI. [VERIFIED: 09-VERIFICATION.md] |

No package addition or upgrade is recommended. This phase changes an established local stack, so installed versions matter more than introducing the latest registry release. [VERIFIED: existing imports and phase scope]

## Architecture Patterns

```text
Settings checkboxes -> snapshot -> atomic config merge -> Engine reload acknowledgement
                                                        -> Owner display preferences
Lookup Result -> requested word + useful senses -> expandable dictionary details
Late context Result -> visibility guards -> optional meaning and context blocks
Lookup Result -> unchanged history/card snapshot
```

- Extend `Config`, `_valid_scalar`, `_from_data`; `save` already delegates scalar validation. Missing or malformed values should independently fall back to the chosen defaults. [VERIFIED: lookup/config.py]
- Extend settings controls, signal/editor lists, `snapshot`, loaded-state fill and success-state fill. `ApplyController.apply` explicitly selects changed fields: adding Config fields alone will not save them. Rollback uses `_fields(prior, changes)`, so include new fields in the normal transaction and it will restore them too. [VERIFIED: lookup/settings_gui.py:33-38,135-147,200-209,270-449]
- `Owner` receives both initialized and applied signals through `_settings_applied`; this is the existing point to transfer preferences to Popup. [VERIFIED: lookup/gui.py:447-454,510-512]
- Keep all useful summaries before any full-text article, including when another dictionary has no structured senses. Preserve dictionary identity and user order. [VERIFIED: lookup/gui.py:294-300; Article contract in lookup/dicts.py]
- Expansion should resize the existing popup using its existing screen-clamped sizing path; use native controls with keyboard access and accessible labels. [VERIFIED: lookup/gui.py:size_for, label; native control conventions in lookup/settings_gui.py]

## Don't Hand-Roll

| Problem | Use existing solution | Why |
|---|---|---|
| Persistent preferences | `config.save` | Atomic replace, private permissions, strict input validation and unknown-key merge already exist. [VERIFIED: lookup/config.py:save] |
| Runtime consistency | `ApplyController` reload/rollback | Existing revision acknowledgement and timeout handling. [VERIFIED: lookup/settings_gui.py] |
| Rich-text safety | Existing QLabel PlainText and PlainBlock | Third-party article content already remains inert plain text. [VERIFIED: lookup/gui.py:PlainBlock,label; tests/test_app_gui.py:test_actual_fields_order_plain_text_and_no_invented_metadata] |
| Sense extraction | Existing Article.senses and bounded short_translation fallback | Avoid a new heuristic parser or invented semantic ranking. [VERIFIED: lookup/dicts.py:Article; lookup/translate.py:47-60] |

## Common Pitfalls

1. **Late callbacks reveal hidden context.** `update_context` currently calls `setVisible(bool(text))` independently; guard these calls with preferences, including pending/error states. Source context rendering needs the same guard. [VERIFIED: lookup/gui.py:306-349]
2. **Settings appear saved but reset at runtime.** Extend both snapshot and ApplyController's explicit field selection; test initialized/applied signals, restart, rollback and config merge. [VERIFIED: lookup/settings_gui.py:135-147,365-373,394-439]
3. **Hiding article text consumes the summary display budget.** `Popup.add()` shares a bounded character/block budget; reserve useful summaries before creating details and preserve an explicit truncation indication. Do not let a hidden first article suppress all later senses. [VERIFIED: lookup/gui.py:clear_body,add,result]
4. **Disclosure creates stale widget references.** `clear_body()` removes dynamic widgets and label bookkeeping. New detail widgets must be cleaned through the same ownership path, and asynchronous context updates must not rebuild or reset disclosures. [VERIFIED: lookup/gui.py:223-253; tests/test_app_gui.py:test_meaning_and_sentence_update_independently_without_resetting_article]
5. **Visibility accidentally changes card contents.** Card snapshots read Result/event data, so leave `_bind_displayed`, `add_card`, Engine persistence and provider decisions unchanged. [VERIFIED: lookup/gui.py:534-566; lookup/app.py:305-345]
6. **Old tests assume context default-visible.** Tests that explicitly cover context should opt in, while new defaults tests should assert hidden source/translation and preserved summaries/cards. [VERIFIED: tests/test_app_gui.py:163-207; 10-CONTEXT.md]

## Code Examples

```python
# Existing project pattern: field-level validation and independent fallback.
# Source: lookup/config.py:_valid_scalar,_from_data
if key in ('online', 'autostart', 'popup_context', 'popup_meaning', 'popup_articles'):
    return isinstance(value, bool)

# New names are illustrative; planner/executor should choose one consistent set.
# Source: existing lookup/gui.py:update_context visibility pattern.
self.context_value.setVisible(self.show_context and bool(text))
self.meaning_value.setVisible(self.show_meaning and bool(meaning))
```

`QWidget.setVisible(bool)` is the documented native visibility API. Context7 CLI resolved `/websites/riverbankcomputing_static_pyqt6` and fetched visibility examples; use existing Qt control patterns rather than adding a UI toolkit. [CITED: https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtwidgets/qsizegrip.html]

## Environment Availability

| Dependency | Availability | Fallback |
|---|---|---|
| Host Python/PyQt6 | Import and version probe succeeded. [VERIFIED: command output] | Native offscreen GUI tests on host. |
| KDE owned clone | Phase 9 records powered-off owned clone after cleanup; this research did not start it. [VERIFIED: 09-VERIFICATION.md] | Host offscreen tests establish logic; live target acceptance remains distinct. |
| VM harness | `tools/check_package_vm.ps1` enforces clone identity and network forwarding before SSH; owned name `lookup-gsd-07`, forwarding port 2227, dedicated known-host file. [VERIFIED: tools/check_package_vm.ps1:12-23] | Follow established ownership checks; do not operate original VM. |

Use existing VM tooling and public fixtures for live screenshots/input. Existing harness commands can be read and adapted after identity checks; do not claim the powered-off VM is currently accessible. [VERIFIED: tools/check_package_vm.ps1; 09-VERIFICATION.md]

## Validation Architecture

Framework: stdlib `unittest` with `PyQt6.QtTest`; `tests/test_app_gui.py` already sets `QT_QPA_PLATFORM=offscreen` and has fake Engine/generation fixtures. [VERIFIED: tests/test_app_gui.py:1-40; tests/test_settings_gui.py]

| Requirement | Behaviors to verify | Command |
|---|---|---|
| SET-02 | Defaults, valid/invalid fields, round-trip, merge preservation, rollback, settings controls, subsequent request/restart | `python -m unittest tests.test_config tests.test_settings_gui tests.test_app_gui` [VERIFIED: existing unittest module names] |
| POP-06 | Offline-only long article, multiple dictionaries, useful senses before full text, disclosure, plain text, unstructured fallback | Same focused command; add dedicated regressions to existing GUI tests. [VERIFIED: current GUI test infrastructure] |
| Preserved behavior | Card/history snapshots and late callback generation/timer rules | `python -m unittest discover -s tests` [VERIFIED: 09-VERIFICATION.md full suite command] |

Wave 0: add regressions to existing files; no new framework or fixture infrastructure needed. Run focused tests after implementation and full suite at phase gate. Live KDE check should demonstrate offline result, expansion, changed choices, subsequent request and restart, with agent acceptance recorded separately from human testing. [VERIFIED: existing test fixtures; 10-CONTEXT.md; roadmap phase criteria]

## Security Domain

This is a local presentation/config change. Authentication/session/cryptography changes are outside scope. Validate new config values with strict booleans; retain atomic writes/private permissions and inert plain-text dictionary/context rendering. This maps to input validation and data integrity controls without adding an HTTP/auth boundary. [VERIFIED: lookup/config.py; lookup/gui.py; phase boundary in 10-CONTEXT.md]

## Open Questions (RESOLVED)

- **RESOLVED design scope / KNOWN LIMIT:** The missing screenshot and original article prevent exact defect reproduction; synthetic cases prove only the stated contracts. The decision to proceed with synthetic coverage is settled; missing source evidence is not claimed recovered. [VERIFIED: brief and 10-CONTEXT.md]
- **RESOLVED validation strategy / KNOWN LIMIT:** Disclosure sizing and focus require KDE acceptance after host tests. Native KDE acceptance remains pending because the original `arch-kde` VM is running and the owned-clone preflight refuses that state. Do not stop, enter or otherwise control the original VM, or bypass the guard. Host offscreen verification may proceed. This is an explicit acceptance limitation, not an unresolved implementation choice. [VERIFIED: 10-01-PLAN.md verification section; parent report of preflight]
- **RESOLVED:** No unverified factual assumptions are required for the recommended implementation. Preference names and exact disclosure wording remain implementation discretion, not locked facts. [VERIFIED: recommendations above derive from inspected code and context]

## Sources and Confidence

**HIGH:** `.planning/REQUIREMENTS.md`, `10-CONTEXT.md`, `lookup/config.py`, `lookup/settings_gui.py`, `lookup/gui.py`, `lookup/translate.py`, `lookup/dicts.py`, `tests/test_config.py`, `tests/test_settings_gui.py`, `tests/test_app_gui.py`, `tools/check_package_vm.ps1`, Phase 9 summary/verification; all inspected in this research. [VERIFIED: tool reads/searches]

**HIGH for documented API:** Context7 PyQt6 official Riverbank documentation lookup for visibility; installed host Python/PyQt6 version probe. [VERIFIED: ctx7 CLI and Python command output]

**Validation freshness:** Recheck affected tests and live environment after implementation. Existing Phase 9 pass is historical evidence only. [VERIFIED: Phase 9 verification timestamp]
