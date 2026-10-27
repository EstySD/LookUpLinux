---
phase: 05-app
verified: 2026-10-27T03:33:56Z
status: passed
score: 10/10 must-haves verified
overrides_applied: 0
acceptance_source: independent agent verification under explicit --auto delegation
---

# Phase 5 — Production tray application verification

**Goal:** A resident tray application uses the shortcut over a word or fresh
selection to show a useful native KDE card near the cursor, records eligible
history once, and visibly handles unsuccessful requests.

Initial goal-backward pass against current production source, all three plans/
summaries, roadmap criteria, raw native gate records and review/security/UI
artifacts. SUMMARY claims alone were not used as proof. No VM actions or source
edits were performed by this verifier. Agent acceptance is not human testing.

## Observable truths

| # | Must-have truth | Status | Implementation and observed evidence |
|---|---|---|---|
| 1 | SC1/TRIG-03: resident tray, working Quit, one owner on repeated launch, warm/cold shortcut lookup | VERIFIED | Lazy --app/--trigger dispatch reaches lookup.gui.run. Atomic fixed session-bus service admits one Engine; warm QCoreApplication client sends only Trigger, cold route launches resident owner then forwards. Native owner/new-primary/repeated-OCR share PID92510, two concurrent extra resident-start processes exit0, physical cold key reaches a different owner. Physical tray Quit leaves both production/probe services absent. Future Слова/Повторение/Настройки actions are present but deliberately disabled pending their later phases. |
| 2 | SC2/POP-01: useful word/IPA/POS/ordered meanings/article/source-context/translation/count, real history, fully contained cursor-adjacent card | VERIFIED | Engine resolves actual primary/OCR query and real translate.lookup; GUI renders actual article/transcription/senses/context/count with plain selectable widgets. Native new-primary record has english, meaning/IPA/source_order true, saved/count1 and public-context SQL evidence. Eight final native cards are inside independently recorded output and dock-derived work-area rectangles with zero panel intersection. |
| 3 | SC3/CAPT-02: new mouse primary bypasses OCR; unchanged primary falls back to OCR | VERIFIED | Source.freeze validates/bounds text and compares in-memory consumed identity, resets absence/invalid freshness, and consumes only accepted current ready work. Main evidence shows primary english then exactly mode=ocr/key=word over the other public word. Supplemental mouse drag yields primary english without OCR. Boundary/reset tests and raw one/two/four/five-word observations agree; sentence creates no history row. |
| 4 | SC4/POP-02/TRIG-02: outside click/Escape/focus/timeout close the card; replacement/bursts do not reopen stale work or corrupt history | VERIFIED | Popup dismissals invalidate the current generation; programmatic capture hiding is separate. Engine guards history under the same condition lock and coalesces to one latest pending request. GUI rechecks identity when queued signals/focus completion arrive. Native escape, focus_loss, native_close, inactivity, delayed dismissal and latest_B observations pass; supplemental physical outside click hides it. Deterministic barrier/real SQLite tests prove stale requests cannot write or publish. |
| 5 | SC5/POP-03/POP-05: blank/network/blocked/missing-tool failures are useful visible states; Breeze tracks light/dark live | VERIFIED | Fixed reason-specific Russian copy, recognition-specific OCR errors, native palette/font rendering and bounded plain text are substantive. Raw blank case is visible not_found, network/blocked/timeout records retain exact controlled reason, and missing/capture/cursor faults are visible. Same native owner passes both palettes at100/125/150/200%. Independent UI review is24/24 after panel/footer and OCR-copy remediation. |
| 6 | One serial worker owns database/dictionaries, one pending-latest slot, bounded context admission | VERIFIED | Engine creates/closes resources in its non-daemon worker, uses one pending tuple and BoundedSemaphore(1); context slot releases only in actual network completion finally, not join timeout. Worker busy_timeout=50 bounds guarded history contention. Thread/admission/busy-writer/Quit tests pass. |
| 7 | Production source is frozen before Loading, and old/late queued work cannot contaminate source or presentation | VERIFIED | Owner.Trigger hides old card, schedules enqueue; worker Source.freeze captures primary/pixels before emitting frozen, then drops pixel storage before GUI event delivery. receive checks current identity; context only changes an already-visible current card. Native capture/queued dismissal gates and stale Qt signal regressions pass. |
| 8 | Main answer can precede finite context completion; late context preserves count/focus/inactivity deadline | VERIFIED | translate.lookup optional on_ready emits a detached result before bounded context join. Engine commits/reuses one saved/count tuple; GUI context route updates only context. Native preview/completion/late-dismiss gates and real-event-loop long-context regression pass without additional presentation/reset or duplicate count. |
| 9 | Persistence/cache/provider failure preserves useful offline content and never invents saved success | VERIFIED | Translation cache/meta errors are controlled; save=False delegates one guarded upsert to Engine, with separate save_error. Native save_failure keeps meanings/IPA but saved=false/count=null, cache-failure remains useful; supplemental provider failure retains both offline sources with context_error=no_network. Real contended/read-only SQLite and detached-callback tests corroborate these paths. |
| 10 | Plain/bounded rendering, fixed private IPC/errors and owned rollback leave no retained private screenshots/profiles | VERIFIED | QLabel PlainText/read-only setPlainText, finite rendering budgets, bounded token and fixed Trigger, no app/gui imports of test tools or production unlock. Harness isolates data/theme/config and requires five restoration flags. Main23 and supplemental4 gates plus5+5 restoration flags all pass; cleanup records29 owned transient images deleted, and this verifier confirmed all eight final screenshot paths are absent. |

**Score:** 10/10, no verification overrides. No concrete unresolved BLOCKER or
must-have WARNING was found in this focused pass.

## Production wiring and work-area delta

The data flow is real: lazy CLI -> atomic Qt owner -> Engine.begin/enqueue ->
Source.freeze/resolve -> actual dictionary/translation/cache result -> one
guarded upsert -> detached Event -> queued current-id check -> native card.
Tests isolate specific boundaries, while the native gate harness launches the
actual production command and reads a real temporary SQLite database. Its
test-only probe observes production widgets/state; it does not replace the
production owner with the Phase4 spike.

The panel fix was independently traced end to end:

1. `lookup/platform.py:panel_rects` issues a fixed, read-only bounded kdotool
   plasmashell search and KWin getWindowInfo query, validates resourceClass and
   dock type, and accepts only finite rectangles.
2. `available_rect` reserves actual monitor-edge dock space, including floating
   panel gaps, and returns integer work-area bounds.
3. Worker `Source.freeze` calls work_area and stores the snapshot in Frozen;
   `_process` carries it unchanged through Event.available.
4. `Owner.present` uses that explicit QRect for Popup.size_for and popup_rect;
   it does not rely on stale QScreen.availableGeometry when the worker supplied
   current compositor work-area metadata.
5. The harness separately records compositor card geometry, actual dock/output
   rectangles and Qt bounds. Independent raw-data assertions verified all eight
   appearances lie inside monitor/work area with strictly zero dock overlap.
   At150%, card[124,0,440,386] is inside work area[0,0,1280,658], above dock
   [0,658,1280,62]. The native work-area regression passes. UI confirmation
   separately inspected both150% footers before screenshot deletion.

The production `--app` action is resident startup; the user-facing desktop/
shortcut `--trigger` route performs searches and forwards to the existing owner.
Duplicate resident-start processes do not create another worker. Later word
list/review/settings actions remain disabled rather than pretending those
Phase6/7 implementations exist.

## Artifact and behavioral checks

| Artifact | Substantive implementation and wiring |
|---|---|
| lookup/app.py | Frozen/Query/Event records, Source freshness/capture, serial resource owner, current-generation guard, exactly-once guarded history and detached early/context events. |
| lookup/translate.py | Compatible optional on_ready/context_gate; real lookup/cache/provider result, bounded join, detached timings and actual-completion admission release. Existing CLI callers retain behavior. |
| lookup/gui.py | Lazy native components, actual field rendering, one outer scroll, bounded selectable plain text, timer/dismissals, queued bridge, native tray, owned focus and fixed owner/client IPC. |
| lookup/platform.py | Existing validated cursor/capture positioning plus fixed read-only dock metadata and actual work-area reservation; portable edge/negative-origin/decimal geometry tests. |
| lookup/__main__.py, tools/lookup.desktop.in | Lazy app/trigger routes preserve existing actions/imports; production desktop template resolves a unique absolute safely quoted trigger command. |
| tests/test_app.py, test_app_gui.py, test_translate_ready.py | Deterministic request/history/context races, real SQLite contention, actual Qt field/layout/timer/lifecycle/plain-text and work-area checks. |
| tools/check_app.py, tests/test_check_app.py | Physical VM input, actual production owner, public source fixtures, independent SQL/window observations, all required-gate/five-restore acceptance and setup-failure cleanup regressions. |
| 05-GATE-RESULTS.json / 05-EXTRA-GATES.json | Exact native observations for23main+4supplemental gates and successful rollback; no actual-provider latency claim. |
| REVIEW-FIXES / SECURITY / UI-REVIEW | Review defects have source fixes and regressions;14 declared security controls verified, UI24/24 after explicit work-area/footer and error-copy remediation. |

Fresh independent command:

`python -m unittest tests.test_app tests.test_app_gui tests.test_platform tests.test_check_app tests.test_translate_ready tests.test_cli tests.test_core_imports`

**53 tests in3.404s, OK, process exit0.** The printed controlled_setup_failure
record is an intentional rollback-regression scenario, not an actual setup
failure. No VM operation was invoked by this test pass.

Independent JSON assertions also verified23main and4supplemental true gates,
all5+5 restoration flags with empty errors, warm/cold owner identities, exact
repeated-primary OCR word, eligible boundary rows and sentence no-row, hidden
dismissed states, honest save failure, controlled provider reasons, tray service
disappearance, all eight dock-free appearances and absent final image paths.

Direct final execution evidence supplied by the orchestrator records561 tests
on Windows3.14.3/3.12.0 and Arch3.14.8, process exit0 with7/7/3 existing skips.
Earlier Windows printed-OK/access-violation runs were explicitly rejected and
native test objects are now disposed before deferred-deletion draining. This
verifier did not redundantly rerun the full suites.

## Requirement coverage

| Requirement | Plans | Result | Evidence |
|---|---|---|---|
| TRIG-02 | 01/02/03 | SATISFIED | Current-generation/replacement/coalescing guards, delayed A/dismiss/B live records and deterministic history/queued-GUI races. |
| TRIG-03 | 02/03 | SATISFIED | Native tray/Quit, one atomic owner, warm/cold physical trigger and duplicate-owner records. |
| CAPT-02 | 01/02/03 | SATISFIED | Source consumption/reset semantics; real new/repeated primary/OCR and supplemental physical mouse drag. |
| POP-01 | 01/02/03 | SATISFIED | Actual word/IPA/ordered sources/context/count with real public-context history and complete work-area-contained card. |
| POP-02 | 01/02/03 | SATISFIED | Escape, focus/native Close, physical outside click and inactivity, plus stale delivery invalidation. |
| POP-03 | 01/02/03 | SATISFIED | Visible blank/not-found, controlled network/blocked/timeouts/package/capture/cursor errors, useful failure preservation. |
| POP-05 | 02/03 | SATISFIED | Same-owner actual Breeze palettes at four scales, native plain selectable layout, work-area gates and independent visual confirmation. |

No additional requirement is mapped exclusively to Phase5. Pending checklist
ticks in REQUIREMENTS are orchestrator transition bookkeeping; user edits there
and in PROJECT/config/research files were preserved.

## Scope and limits

Agent acceptance under explicit --auto delegation does not claim human/friend
hardware testing. Online successes/failures are controlled fixture transport;
this is not fresh live-provider availability or latency evidence. Only one VM
output is exposed; negative origins/edge panels have portable coverage.

Native screenshot appearance was audited independently before cleanup. Final
screenshots intentionally no longer exist, so this verifier checked the prior
UI audit, raw bounds/palette/field observations and current source/regressions;
it did not invent a new screenshot review. Cleanup29 and no retained runtime
profiles are operational results reported by the parent/security audit; final
eight image paths were additionally checked absent locally.

Recorded first-useful-paint timings start at engine admission, not physical
keypress/cold process startup. No Phase8 PERF-01 acceptance, arbitrary desktop
accuracy guarantee or real user MDX/DSL verification is implied.

All five Phase5 roadmap criteria and their plan extensions are achieved within
the stated scope. User direction is to finish Phase5 and stop before Phase6;
this verification does not dispatch any later phase.

_Independent goal-backward verifier. Only this report written; no source edits,
VM commands, commits or next-phase launch._
