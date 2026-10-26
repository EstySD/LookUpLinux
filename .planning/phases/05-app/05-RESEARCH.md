# Phase 5: Production tray lookup — Research
Researched:2026-10-26. Confidence:HIGH for inspected contracts; GUI end-to-end
latency/focus remain execution measurements.

## User Constraints (from CONTEXT.md)
### Locked Decisions
- D-01: Preserve current CLI and stdlib-only core imports. Add lazy GUI entry
  actions to python -m lookup; keep one production session-bus owner with a small
  fixed Trigger interface and DBus-only warm client. Reuse validated session,
  capture, geometry and owned kdotool commands rather than import spike tooling.
- D-02: A new admissible bounded primary selection takes priority. Keep its
  previous consumed identity only in memory. The same unchanged selection next
  time falls through to OCR; no selection resets freshness. Define short text
  explicitly from existing classifier/online input bounds, never clipboard writes
  or history alterations. Preserve raw context separately from normalized key.
- D-03: Each trigger gets a monotonically increasing request identity. Newer
  triggers supersede earlier work; explicit dismissal invalidates presentation
  and pending history writes. One serial worker owns dictionary/SQLite resources
  and coalesces queued requests to the newest. Qt stays responsive. No QThread
  termination, unsafe shared SQLite connection or duplicate search-count write.
- D-04: Call existing translation APIs without speculative history persistence;
  commit one accepted word/phrase event only after checking its current identity
  under a short shared guard. Sentence lookups do not create word history.
  Existing safe translation caching may remain. Stale results never replace or
  reopen the card, and stale delayed network replies never increment history.
  Preserve existing valid-lookup/history semantics and show save failures honestly.
- D-05: Native Breeze popup, system font/palette/icons, Russian copy. Word and
  optional transcription/lemma, POS senses, ordered dictionary articles, original
  context/translation and confirmed count. No invented metadata. Bounded vertical
  scrolling; plain selectable text prevents article HTML/images/file access.
- D-06: Reuse Phase4 pointer-adjacent available-monitor clamping, actual KWin
  geometry and active UUID focus route. Escape, outside click/focus loss and a
  finite inactivity timeout dismiss. Loading/results/errors respect the same
  generation. Choose a default timeout now, persist settings in Phase7.
- D-07: Tray has Words, Review, Settings and Quit in Russian; future Phase6/7
  surfaces have explicit disabled actions until implemented, not fabricated
  workflows. Keep the menu/action integration points small. Quit closes worker,
  dictionaries, DBus ownership and Qt resources cleanly. No arbitrary IPC commands.
- D-08: Every trigger visibly shows loading then result or fixed, specific
  Russian errors. Distinguish not found, no network/blocked provider, missing
  package, unavailable capture/cursor and failed save. Offline articles remain
  useful if context translation fails. Preserve no private diagnostic output.
- D-09: Wire the unique owned production desktop trigger for real VM tests.
  Keep installation/autostart/settings/PKGBUILD work in Phase7. Never steal an
  unrelated shortcut, overwrite unrelated desktop entries or change KWin policy.
  Normal session unlock is VM harness tooling only, never production behavior.
- D-10: Verify production integration in the existing VM with controlled public
  content and throwaway config/dictionaries/DB. Actual primary selection, physical
  hotkey, warm/cold owner, dismissal, light/dark, four scales and repeated triggers
  need observed evidence. Delayed older response and close-while-pending require
  deterministic tests proving no stale card or DB write. Screenshots used for UI
  inspection contain only owned fixtures and are removed after bounded review.
### Delegated / Deferred
Choose minimal worker/controller seam and UI-SPEC defaults; Phase6/7 features
stay disabled until implemented. Full context:05-CONTEXT.md. No interview.
[VERIFIED: canonical context; decisions above copied verbatim]

## Project Constraints and Evidence
Preserve CLI/core stdlib-only import behavior, lazy Qt, fixed private errors,
scoped changes and fresh behavioral verification. --auto delegates acceptance.
No unrelated config/shortcut changes. [VERIFIED: AGENTS/session instructions]
Linux selection freshness/cancellation are project contracts, NOT established
Lookupper behavior: evidence.md Q04/Q05/Q06 remain unverified for original.
Windows Alt+Q/Fluent/autosave options do not override Meta+Shift+D/Breeze/v1.
[CITED: docs/lookupper/linux-requirements.md §§1–5; evidence.md remaining checks]
PRODUCT.md/DESIGN.md require native readable plain selectable text, actual
metadata, bounded scrolling and confirmed save count. UI-SPEC owns dimensions,
spacing and default timeout; recommend20s inactivity reset by interaction.
[VERIFIED: PRODUCT.md,DESIGN.md; timeout is delegated recommendation]

## Architectural Responsibility Map
| Capability | Owner / seam |
|---|---|
| Current request,replace,dismiss,coalesced pending | Stdlib engine/controller with Condition+monotonic generation |
| Dictionaries,main cache/meta/history SQL | One serial worker,resources created/closed inside worker |
| QtDBus owner,warm client,popup,tray,timer | Lazy GUI module,main Qt thread |
| Cursor,monitor,capture,OCR | Existing platform/capture/ocr called from worker |
| Optional slow context | Existing bounded network-only context thread; do not multiply workers |
[VERIFIED: source inspection; recommended responsibility assignment]

## Existing Contracts — Important Differences
translate.Result is mutable: kind,key,ordered articles,lemma,online/error,
context translation/error,translation,saved,count,timings. Article is frozen
with dict_name/headword/transcription/senses/text/lemma_of/form_of/pointer_only.
Do not invent transcription/POS or replace surface form with guessed lemma.
[VERIFIED: lookup/translate.py Result; lookup/dicts.py Article]
lookup(save=False) suppresses ONLY upsert_word: translations cache and meta
still write. _context_request uses only a holder and network; main owner later
writes context cache. Context joins AFTER main result and can delay return
until its3.5s bound even when useful offline articles are ready.
[VERIFIED: lookup/translate.py lookup/_context_request]
upsert_word uses one autocommit INSERT..ON CONFLICT..RETURNING count; it expects
normalized key and keeps prior nonempty translation/context/lemma. Current
history eligibility is word/phrase and online_error!='not_found', including
valid offline/no-network words without an article. Preserve that contract,
rather than silently redefining found. Sentences never create word rows.
[VERIFIED: lookup/store.py upsert_word/_connect; lookup/translate.py]

## Recommended Minimal Worker/Translation Seam
Use one non-daemon Python serial worker with Condition and one pending slot;
new trigger overwrites queued payload, never spawns a new lookup worker.
Worker opens DictSet+SQLite,uses them exclusively,and closes in finally.
QWidgets/timers remain GUI-owned; queued Qt signals carry detached payloads.
Do not disable sqlite check_same_thread or call worker slots as direct methods.
[CITED: https://doc.qt.io/qt-6/threads-qobject.html;
https://docs.python.org/3/library/sqlite3.html; VERIFIED: existing resource APIs]
Add optional stdlib-only lookup(...,on_ready=None) callback after main
translation/short_translation and BEFORE context join; existing CLI behavior
unchanged when absent. Pass a detached dataclasses.replace(result,
timings=dict(result.timings)) snapshot. Engine callback applies guarded history
commit and emits ready; final lookup result updates context under same request
with saved/count copied from the one commit. No duplicate dict/network lookup
or second history increment just to render an early offline card.
[VERIFIED: lookup phase order; proposed small compatible extension]
Keep existing finite context join as the smallest bounded policy in this phase:
obsolete context finishes within existing budget and blocks processing of the
next queued request meanwhile. Do NOT abandon joins then spawn new per-trigger
context threads: that creates unbounded overlapping obsolete work. Check current
identity between stages and before callback/publish; stale replies may safely
update translation cache/meta but never history or presentation. Document and
measure queued-latest latency honestly; do not call this instant cancellation.
[VERIFIED: current context threading/deadline; bounded recommended policy]

## Guarded Commit and Presentation
Under a short shared lock check generation==current,not dismissed/stopping,and
not already committed; execute ONE eligible upsert_word and record confirmed
count,then release. Trigger/dismiss advance generation under that same lock.
This linearizes commit versus cancellation; already-committed searches are not
undone. Every GUI queued slot rechecks generation as signals may arrive later.
Do not emit mutable Result then change it during context completion.
[VERIFIED: D-03/D-04; concurrency design derived from required invariant]
SQLite's default5s busy timeout would make that lock non-short. Initialize DB
outside guard,then set worker busy_timeout to a small bound(e.g.50ms) for guarded
upsert; busy/error yields a separate save_error with useful result retained,
no false saved/count. Do not retry obsolete history writes. Bound guard latency
with an actual competing-write test,not a sleep-based race guess.
[VERIFIED: lookup/store.py _connect and open_store(timeout=5);
CITED: Python sqlite3 timeout docs;50ms is proposed policy]
Quit invalidates generation,clears pending,wakes worker and hides popup/tray;
finish bounded in-flight work then close resources/release DBus. Keep Qt event
loop alive while polling worker completion; never QThread.terminate or block
GUI with an unbounded join. Existing online/context/capture deadlines bound
individual stages; no shutdown latency pass claimed by this research.
[VERIFIED: current bounded stages and context D-07]

## Primary Freshness and Capture Ordering
Admit stripped primary text only within online.ONLINE_MAX_CHARS(1000),no unsafe
controls,and classify-valid word/phrase or bounded sentence. Identity is
' '.join(raw.split()); preserve raw source/context separately. New admissible
identity is consumed once; unchanged offer falls to OCR; absent/invalid offer
resets consumed identity. Invalid bytes/timeouts become no usable primary.
This reset interpretation was confirmed by parent; no clipboard writes.
[VERIFIED: context D-02,parent instruction,online/translate/platform bounds]
Capture must see the source before our loading card. On trigger hide current
card under a capture generation,schedule capture after compositor has processed
hide,then worker emits frozen-frame/point acknowledgement; ONLY then show new
loading and proceed OCR. Stale capture acknowledgements never show a card.
Primary path may show loading after text/point selection without a screenshot.
Do not reuse previous frame under a new cursor. Existing capture helper sets
hide-caller-windows=False,so merely showing a loading card first WILL be unsafe.
[VERIFIED: lookup/capture.py _screenshot2 options; proposed freeze-first ordering]
Alternative hide-caller-windows=True requires a dedicated target proof and may
hide owned fixtures; do not assume Phase4 verified that variant. Reuse
session_env token removal,kdotool owned_window/window_action,image_point and
popup_rect; production must not import tools/vm_spike.py or unlock the session.
[VERIFIED: actual helper/spike code and D-01/D-09]

## UI, Error, IPC and Theme Contracts
Plan after UI-SPEC. PlainText labels or setPlainText only; never AutoText or
QTextBrowser rich resources for dictionary/provider text. One vertical scroll;
preserve source order,original key and optional lemma/IPA. Native style/palette
and widgets update on palette/theme events; no global stylesheet palette.
[CITED: https://doc.qt.io/qt-6/qt.html#TextFormat-enum; VERIFIED:DESIGN.md]
Keep a fixed Trigger signature with bounded token string and minimal return.
Atomic session-bus ownership resolves cold-launch races; warm command uses only
QCoreApplication/QtDBus. Token/startup env removed before child launches; do not
log values or introduce unverified token setters. Reuse observed kdotool focus.
[VERIFIED: tools/vm_spike.py validated path; 05-CONTEXT D-01]
Distinct states: loading,no match,missing tool/capture/cursor error,
network disabled/no_network/blocked/timeout,partial context failure,and save
failure. A ready offline article survives context failure. Dismiss on Escape,
outside/focus loss or timeout; programmatic hide for capture/reposition must
not act as user cancellation. Guard callbacks by generation and visibility.
[VERIFIED: POP requirements,linux-requirements §4,context]

## Validation Architecture
Existing unittest; proposed tests/test_app.py for pure controller/gates,
tests/test_app_gui.py for optional Qt rendering/signals,tests/test_translate.py
for callback compatibility. Full three-interpreter regression plus actual VM
production route,not spike-only proof. Detailed map in05-VALIDATION.md.
[VERIFIED: existing test conventions; proposed file assignments]
Use Events/barriers: delay A network or context,start B/close,release A,assert
no stale card/history; burst coalesces to latest; one accepted request counts
once across ready/final; old cache writes allowed; sentence no word row; save
failure renders useful content. Real held SQLite writer proves guarded busy
bound. Count background workers during bursts;no unbounded context threads.
[VERIFIED: required invariants and actual cache/history semantics]
VM gates: new/repeated/absent primary,physical hotkey,warm/cold owner,public
capture excluding loading,Escape/outside/focus/timeout,light/dark,four scales,
quit,repeated triggers,private artifact cleanup. Measure first USEFUL card
separately from loading and final context; do not extrapolate Phase4 timings.
[VERIFIED: 05-CONTEXT D-10; linux-requirements §5]

## Security / Execution Decisions
Threats: stale history/UI,SQL/thread misuse,unbounded queues/context threads,
IPC arbitrary command/token leakage,self-capture,rich-text resource loading,
clipboard mutation,save-failure false count. Above seams define mitigations
and deterministic tests; no broad audit or platform-policy change required.
No open interview gate: UI-SPEC fixes layout; implement+measure bounded wait
policy and first-useful-card latency; record limits and advance from evidence.
[VERIFIED: scoped boundary analysis and explicit --auto instruction]
