---
phase: 06
slug: words-cards
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-10-27
---
# Phase 6 Validation

Framework: stdlib unittest and existing real offscreen Qt widget pattern. New test modules are created in their implementation tasks, with assertions written before production branches; no separate scaffold wave. Focused commands target under 60 seconds; full suite once per plan and after fixes.

| Task | Automated command | Observable evidence |
|---|---|---|
| 01-1 | python -m unittest tests.test_learning tests.test_migrations tests.test_store | V3 preservation, numeric queries, delete/count reset, independent immutable duplicate cards |
| 01-2 | python -m unittest tests.test_learning tests.test_privacy tests.test_core_imports | All ratings/ease floor/UTC/due/CAS/restart, preview-applied equality, CSV/TSV round-trip/atomic failure |
| 02-1 | python -m unittest tests.test_learning_gui tests.test_learning tests.test_core_imports | Native windows/reveal/grade/empty/export dialogs and GUI connection ownership |
| 02-2 | python -m unittest tests.test_app_gui tests.test_learning_gui tests.test_app tests.test_privacy | Tray reachability, frozen shown pair, duplicate/stale/closed/later-enrichment protection |
| 03-1 | python -m unittest tests.test_check_learning_app tests.test_learning_gui tests.test_learning | Harness assertions/cleanup plus actual archvm native observations |
| 03-2 | python -m unittest discover -s tests | Host/target regression, real separate Anki import if available or explicit external limit |

Acceptance harness: `python tools/check_learning_app.py --output /tmp/lookup-learning-evidence` on archvm. Inspect synthetic native screenshots, exported values and persisted schedules. Agent evidence only; no human testing claimed. Existing Phase5.1 607-test/144-image acceptance is baseline, not a new task. Undocumented provider HTTP429 does not block offline learning.

Anki currently absent: format/round-trip verification is mandatory; actual isolated import is attempted when obtainable and otherwise explicitly unverified, not fabricated or silently equated to parser success.

## Source Coverage Audit

| Source | Item | Plans | Status |
|---|---|---|---|
| GOAL | Browse/search/card/review/export saved words | 01–03 | COVERED |
| REQ | LIST-01, LIST-02 | 01,02,03 | COVERED |
| REQ | POP-04 | 01,02,03 | COVERED |
| REQ | LEARN-01, LEARN-02 | 01,02,03 | COVERED |
| CONTEXT | D-01 native reusable tray windows | 02,03 | COVERED |
| CONTEXT | D-02 numeric history/search/delete/no recount | 01,02,03 | COVERED |
| CONTEXT | D-03 independent immutable duplicate snapshot | 01,02,03 | COVERED |
| CONTEXT | D-04 displayed pair/fallback/late protection | 01,02,03 | COVERED |
| CONTEXT | D-05 deterministic preview/apply UTC review | 01,02,03 | COVERED |
| CONTEXT | D-06 CSV/Anki immutable lossless format/import | 01,02,03 | COVERED |
| CONTEXT | D-07 migration/connection ownership/no deps | 01,02 | COVERED |
| CONTEXT | D-08 actual native agent evidence/honest limits | 03 | COVERED |
| RESEARCH | SM-2-derived exact rule/CAS/reveal | 01,02 | COVERED |
| RESEARCH | Two-field escaped HTML TSV/directives/no localized notetype | 01,03 | COVERED |
| RESEARCH | Atomic export/no overwrite loss/empty errors | 01,02,03 | COVERED |

No deferred settings/package/game/audio/sync/card-category scope appears in plans.
