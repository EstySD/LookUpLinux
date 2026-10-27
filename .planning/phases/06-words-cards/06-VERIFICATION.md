---
phase: 06-words-cards
verified: 2026-10-27
status: passed
score: 6/6 roadmap must-haves verified
overrides_applied: 0
acceptance: agent under explicit --auto
---

# Phase 6: Words and Learning Cards Verification

**Goal:** Saved words can be viewed, searched, added to cards and reviewed on a persistent interval schedule; cards export to CSV and an Anki-importable file.

**Status:** passed. All six roadmap criteria and all five mapped requirements are verified against substantive production code, direct data-flow inspection, independent checks and detailed execution artifacts. No human acceptance is claimed.

## Observable Truths

| # | Roadmap contract | Status | Evidence |
|---|---|---|---|
| 1 | Tray Words opens history, default numeric count descending; headers change sort | VERIFIED | Owner enables/reuses WordsWindow. Its default count/DESC query reaches real SQLite, with bound search and allowlisted sort columns. Native observations show river/apple/bank initially, then apple/bank/river after count-header sorting. |
| 2 | Search, delete/reset count and add from history work | VERIFIED | Live history SELECT/search, selected add and DELETE are wired to widgets. Native search returns bank; post-delete accepted Engine lookup recreates count 1. Independent cards have no history FK and survive deletion. Core/widget tests assert browsing does not count. |
| 3 | Popup adds its shown word/context/translation once and reports duplicates | VERIFIED | Owner freezes the displayed result, event context and exact span; it does not reread newer history. Generation/visibility guards reject closed or superseded views. Cards INSERT uses normalized primary key and ON CONFLICT DO NOTHING; duplicate preserves all snapshot and schedule fields. |
| 4 | Due review has reveal, four rating intervals, matching persistent transitions and honest empty queue | VERIFIED | ReviewWindow uses due_cards and shared preview for labels; answer reveal enables grading. grade_card checks UTC due and review_version in a compare-and-set UPDATE. Native version 1/due persistence, repeat refusal, next card and empty queue pass. Reopening a separate connection preserves state. |
| 5 | CSV and unchanged Anki-importable export retain word/translation/context | VERIFIED | Exports read immutable cards in one SELECT. CSV exact round-trip and two-field escaped Anki TSV are verified independently. Official Anki 26.9.3 Python/Rust importer created two notes with exact exported Front/Back fields; input SHA remains unchanged. Atomic failure and dialog Cancel retain existing destination/no output. |
| 6 | Popup's contextual meaning and exact multiline context remain paired in review/export; unavailable sense uses dictionary fallback | VERIFIED | Source span propagates Query to Event and displayed snapshot. add_card prefers current meaning only with matching source span/provider, otherwise the shown short translation. Stored bank snapshot retains selected source substring, multiline context and provider. Late meaning/history mutations do not change the card. Review/export consume that frozen row. |

**Score:** 6/6. No overrides, missing artifacts, unwired data flow or unresolved product blockers found.

## Artifacts, Wiring and Data Flow

| Artifact | Existence and substantive behavior | Wiring and actual data source |
|---|---|---|
| `lookup/store.py` | Additive V4 cards table, due index, independent snapshot/schedule columns | Existing guarded migrations preserve V3 history/cache. Real SQLite rows back all learning operations. |
| `lookup/learning.py` | Validated history/card APIs, immutable duplicate insert, deterministic preview, due/version CAS, atomic exports | Used by native widgets and popup. History queries and card snapshots are actual SELECT/INSERT/UPDATE operations, not fixtures or empty fallbacks. |
| `lookup/learning_gui.py` | Native searchable/sortable WordsWindow and reveal/grade ReviewWindow; fixed retryable errors and empty states | Tray creates one reusable window per action using a GUI-owned connection; actions call real core methods. Ratings use the same preview as persisted grading. |
| `lookup/gui.py`, `lookup/app.py` | Accepted Event carries exact source span; popup action copies rendered state and reports creation/duplicate/error | Source result to Query to Event to displayed snapshot to cards; history worker and GUI connections remain separate. Late updates never rewrite stored cards. |
| `tools/check_learning_app.py` | Actual Wayland Qt windows/dialog interactions, production Owner/Engine, controlled public input, isolated XDG profile and real Anki backend import | Native report derives ten gates from explicit assertions. Import reads the unchanged production export into an actual temporary Collection and compares retrieved fields; final cleanup removes the throwaway profile/settings/collection. |
| Related learning/application/migration/harness tests | Nontrivial behavioral regressions, including exact pair/immutability, stale grading, export rollback and harness failure guards | Tests exercise production APIs/widgets with isolated storage. They do not substitute for the separate native/import evidence. |

### Key Links Checked

- Tray Words/Review actions -> `_open_learning` -> native windows -> GUI-owned SQLite connection.
- History search/header/selection/add/delete/save-dialog handlers -> bound/allowlisted core functions and immutable cards.
- Query span -> ready/context Event span -> `_bind_displayed` -> `learning.add_card` using a copied shown snapshot.
- Review queue -> saved translation/context -> shared preview -> due/version-guarded persistent grade -> refresh/empty state.
- Cards SELECT -> CSV/escaped TSV temporary file -> fsync/atomic replace -> actual Anki Rust import -> retrieved fields.

## Independent Behavioral Checks

- Preflight: `python -m unittest tests.test_learning tests.test_learning_gui tests.test_app_gui tests.test_app tests.test_migrations` — **90 tests OK**, two Windows POSIX skips, 10.633 seconds.
- Final focused check: `python -m unittest tests.test_learning tests.test_learning_gui tests.test_app_gui tests.test_check_learning_app` — **47 tests OK**, zero skips, 2.275 seconds.
- Independent artifact assertions verified all **10 native gates**, all **6 final cleanup flags**, actual Wayland platform, default/header sort orders, bank search and history reset count 1.
- Independently verified bank's stored context substring at its span equals bank, retained source provider, and graded review_version 1.
- Parsed generated CSV and TSV independently, decoded escaped Back translation/context and matched exact CSV values. Retrieved actual imported fields equal TSV cells; both notes, Unicode, literal HTML-like text and multiline content are retained.
- Verified working-file and committed Git-blob SHA-256 for both exports against reported hashes. TSV: `b51e6aa2513fd5a34cfbd94bb12660971dd17959e319400fbaa68db21d4b11f6`; CSV: `54aa08438eeae647958215df6d0a3e065b39bd69802fe3bf1c40c6877645a632`.
- Independently inspected all four native light/dark Words/Review screenshots. Search/table/actions and revealed plain-text translation/context are legible; rating labels and independent-card deletion copy are visible.
- Inspected final whole-suite logs: host **640 OK, eight known Windows/environment/opt-in skips**, 42.708 seconds; target **640 OK, zero skips**, 55.763 seconds. Root additionally captured host Python exit code 0.

Evidence: `learning-native/report.json`, `learning-native/anki-import.json`, generated CSV/TSV and four images, `06-host-tests.txt`, `06-target-tests.txt`.

## Requirements Coverage

| Requirement | Plans | Result |
|---|---|---|
| LIST-01 | 01, 02, 03 | SATISFIED — numeric initial sort, header switching and actual tray window. |
| LIST-02 | 01, 02, 03 | SATISFIED — search, add, independent deletion and next count 1. |
| POP-04 | 01, 02, 03 | SATISFIED — frozen displayed snapshot, visible success/duplicate, no reset or late rewrite. |
| LEARN-01 | 01, 02, 03 | SATISFIED — due/reveal/rating intervals, persisted CAS transition and empty/restart behavior. |
| LEARN-02 | 01, 02, 03 | SATISFIED — exact CSV and actual unchanged-file Anki backend import. |

No Phase 6 requirement is orphaned. Roadmap SC6 is additionally traced to Phase 5.1's accepted source-pair contract.

## Disconfirmation and Limits

- A passing export unit test alone would not prove Anki compatibility. The separate real official importer retrieved two notes with exact Front/Back values; this closes that gap without claiming the graphical AQT import dialog or sync was tested.
- First Hard/Good/Easy intervals can all be one day under the selected documented SM-2-derived rule. The requirement is four working labeled responses with preview/application equality; no unrequested distinct-first-interval algorithm was imposed.
- Native acceptance uses controlled public Source/displayed events and Qt input against actual windows, Owner, Engine, storage and dialogs. It is agent acceptance, not human testing or a new physical-hotkey/capture/game claim.
- Earlier calibration left `/home/arch/.config/QtProject.conf` (659 bytes) with unknown prior baseline. It was not read or overwritten in an attempted rollback; that earlier settings side effect is not described as restored. The final run isolates Qt config/cache/data before Qt initialization, verifies all six owned-resource cleanup flags and preserves actual session runtime/DBus. This verification deviation remains disclosed, separate from product-goal completion.
- Host log's RemoteException line is the independently reproduced PowerShell stderr projection with Python exit 0. Target SemLock tracebacks are from the existing forced-negative-deadline test; positive writer results/counts pass. Neither is treated as a hidden test failure.
- External KDE portal dialogs and a full graphical Anki session remain unclaimed. Phase 5.1 provider HTTP 429 does not affect these offline workflows. Settings/package work remains Phase 7; real games, extended load and performance acceptance remain Phase 8.

## Human Verification

None required to advance under the explicit --auto agent-acceptance instruction. No human acceptance has been recorded. All required observable behaviors have code, focused tests and the applicable actual native/import evidence; remaining limits are explicitly scoped above.
