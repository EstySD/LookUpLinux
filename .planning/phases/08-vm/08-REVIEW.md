---
phase: 08-vm
reviewed: 2026-11-01
depth: standard
review_scope: final_phase08_source_security_native_evidence
diff_base: 1b54572
review_head: fe021bdf68607d5b8026eb1d1494e945862618cd
tested_tree: 728957780ced4c36bcd2f64c9f96da345c6f134f
prior_final_review_commit: bbb1dbd
initial_source_snapshot: e7fb3d6
finding_recheck_head: 3114db8
incremental_production_head: 4ace8e9
incremental_harness_head: 9a2ec88
incremental_harness_recheck_head: a3c887f
phase_review_complete: true
code_review: passed
security_review: passed
phase_acceptance: ready_for_verification
independent_verifier: pending
files_reviewed: 20
files_reviewed_list:
  - lookup/timing.py
  - lookup/__main__.py
  - lookup/gui.py
  - tools/check_hardening.py
  - tests/test_timing.py
  - tests/test_hardening.py
  - tests/test_app_gui.py
  - tools/check_hardening_vm.ps1
  - tools/check_games.py
  - tests/test_check_games.py
  - tools/check_hardening_install.py
  - tests/test_hardening_install.py
  - lookup/ocr.py
  - tools/calibrate_ocr.py
  - tests/test_ocr_fallback.py
  - tests/test_ocr_game_sources.py
  - tests/test_ocr_image.py
  - tests/test_app.py
  - tests/test_concurrency.py
  - tests/test_hardening_cleanup_controller.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
resolved_findings: 19
status: clean
scope_result: clean
---

# Phase 8: Code and Security Review

## Final Assessment

**Code review PASSED. Security review PASSED.** Full submitted phase source scope is reviewed at tested revision `fe021bdf68607d5b8026eb1d1494e945862618cd` (tree `728957780ced4c36bcd2f64c9f96da345c6f134f`), including the20 source/test/tool files listed above, the immutable game fixture manifest, and the scoped native transport/controllers/collectors/registry/isolated-suite helpers documented below. All16 BLOCKER findings and three WARNING findings are resolved with retained reproductions/dispositions. No open finding remains. STRIDE/ASVS-L1 threat-model boundaries in08-07/08-08/08-09 were cross-checked against actual code and evidence; no certification claim is made.

Fresh final raw recomputation: host **797tests/11skips/exit0**, target **797tests/0skips/exit0**, both at the exact tested revision/tree, actual log digests verified, no Traceback in either current log. Target actual OCR/Mueller opt-ins and isolated UID/private DBus/offscreen execution are recorded. The Git source anchor passes; failed initial795-target discovery remains preserved.

Current evidence recomputes true for source-bound physical30 (median1088.2457725ms/p951431.759096ms), two actual same-instance AssaultCube routes with physical return controls and real6-to11 selection, exact-source current Wesnoth compatibility, declared nongame20 fallback resources, physical burst and classified privacy. Historical320/scales/install/fault/meaning evidence is reused only under the documented unchanged-path rationale and fresh current OCR/context/geometry coverage. Game latency4303.613319/4081.585538ms is retained without a new1500ms game claim. Live meaning availability remains0/6; second-output/borderless and software-renderer limits remain explicit.

Both actual post-manual7552 cleanup and latest explicit target recovery are accepted from raw readbacks. Latest target recovery uses the exact frozen reviewed controller finally AST, with source digest verified. Controller29428's missing process/stale running receipt and lost original memory remain explicit; no fabricated initial-finally execution or hot reload is claimed. Restoration uses the saved actual last-OFF pretarget snapshot, not active settings. Release succeeds; remaining private/normal product processes are empty; package is absent; post-manual config/dictionaries and16words/1card logical SQLite backup remain intact (matching8e6fd074… digest/integrityOK). Clone final OFF/3Don/BIDI and successful restoration exit0 are observed. Shutdown SSH disconnect stays a false transport receipt, resolved by later actual OFF readbacks. All mutations are clone-scoped under USER_KEEP_RUNNING; no original guest/disk/control action is accepted.

This completes the independent code/security review and makes the phase **ready for independent verification**; the verifier gate remains pending. No human testing claim is inferred. Historical Phase7 strict-false original-preservation/unknown-actor evidence, rejected Doom/06 routes, frozen09 false shortcut comparison, failed initial suites and earlier unsupported privacy attempts remain unchanged. New full registry/physical proof resolves current cleanup only. Reviewer made no VM/source/index changes; only this report was edited.

The remaining sections are retained chronological review history. Their earlier partial/pending statements describe those checkpoints; this final assessment and later explicit resolved dispositions govern current review status.

## Historical Incremental 09 Dispositions

CR-13 below is RESOLVED in source-binding GREEN `787ca19`, including its complete-inventory and current-byte residuals. Earlier clean reviewed increments remain historical. Current-performance binding code has clearance; actual native artifacts and expanded phase acceptance still require later review.

WR-02 below is RESOLVED in per-pass observer `57db97e`; unsupported observation modes preserve original calls/results/exceptions. Actual game/native evidence remains a separate gate.

CR-14 below is RESOLVED in `e2a5893`, including source/report I/O residuals. Actual execution of the old live controller and any recovery remain separate evidence obligations.

CR-15 is resolved in `d16c387`; CR-16 is resolved in `23cdaf5`, including root PKGBUILD anchoring. Phase completion remains pending actual final suites/latest cleanup and final independent gates.

## Historical Unit 06 Addendum Status

**Current isolation policy:** The explicit user instruction recorded in `9a6890c` and `08-VALIDATION.md` governs subsequent06/07 work: `USER_KEEP_RUNNING`. The original VM belongs to another active project and must receive zero reviewer/workflow guest, disk or control actions. Read-only host identity/state observations are permitted; original OFF, unchanged state and disk hashes are not new acceptance prerequisites. Every mutation still requires the independently identified owned clone and explicit guarded endpoint. This changes neither GAME-01/PERF-01 requirements nor historical07 strict-false evidence. Current clone cleanup, retained data and actual action provenance still require review; no new native result is accepted by this policy acknowledgment.

Incremental review of the approved gap-closure plan/GAP-RESEARCH and AssaultCube descriptor/SDL/protocol changes found CR-11 in pilot failure cleanup and CR-12 in GL-context binding, both now resolved. No open finding remains in reviewed source through `749076b`. No native operation was performed by this reviewer. Actual fresh second routes/control/GL binding and new06 cleanup remain pending; a useful pilot/preflight is not GAME-01 completion. The prior completed01–05 review remains valid historical evidence; expanded scope is partial until actual final evidence and source integration are reviewed.

## Prior Final Assessment: Units 01–05

**Code review: PASSED. Security review: PASSED.** Standard review covers all twelve submitted source/test/tool files from `1b54572` through final correction `a10c5e1`. No open BLOCKER or WARNING remains. Ten BLOCKER findings and one WARNING were corrected and independently rechecked; original findings, reproductions and dispositions are retained below as history.

This is a completed code/security review, **not phase acceptance**. Actual retained evidence has six of seven product groups true and11/11 global cleanup checks true; the captured game's useful OCR/overlay/return-after-useful route remains absent. GAME-01 and the overall phase aggregate correctly remain false. No historical Phase7 preservation failure is waived, rewritten or attributed to a known actor. No human acceptance is asserted.

Fresh final source verification by this reviewer: **87 scoped tests passed**, 6.712seconds, covering timing, CLI, GUI, game, raw-oracle and install contracts. Full751-test host/target runs inspected earlier belong to source through `d5488b3` (8/0 skips, exit0). Subsequent `a10c5e1` changes only pure evidence-binding/oracle code; its27 directly affected tests and the87-test scoped run passed freshly. A subsequent executor host discovery was in progress at report finalization; no new full-target execution or post-fix full-suite count is invented here.

The remaining sections preserve incremental review-time pending statements and failed reproductions as history. Later explicit resolved dispositions and this final assessment govern the current review status.

Standard review covers completed unit 01, commits `4d31f2b` through `41f3381`, using committed source snapshot `e7fb3d6`. Parallel uncommitted native-driver work is excluded. Units 02–05, real performance/resource/privacy/game measurements and final integration review remain pending. This report does not accept PERF-01 or GAME-01.

## Resolved findings

### CR-01: Historical preservation adapter rejects the authoritative Phase 7 report

**Classification:** BLOCKER
**Disposition:** RESOLVED in `3114db8`, with actual-report regression `34f35c9`. The adapter now validates the authoritative cleanup predicate while preserving the raw failed report and unknown actor. Original finding and reproduction below are retained as review history.
**File:** `tools/check_hardening.py:282–283`
**Related reliability gap:** `tests/test_hardening.py:137–145` in the original snapshot constructs the same incorrect historical schema instead of exercising the saved authoritative report shape.

**Issue:** `carry_phase7()` requires `raw['gates']['original_preserved'] is False`. The authoritative `.planning/phases/07-settings-package/07-native-report.json` stores this failed cleanup predicate under `raw['cleanup']['original_preserved']`; its product gates contain no such key. Calling the new adapter with the actual report raises `EvidenceError('historical')`, preventing D-02's required carry-forward of unchanged raw failed evidence. The existing synthetic test passes because it invents a `gates.original_preserved` field.

**Reproduction executed against the committed snapshot:** Load `e7fb3d6:tools/check_hardening.py` into an isolated Python namespace, parse the saved Phase 7 report with `json.loads`, and invoke `carry_phase7(raw)`. Observed `raw['passed'] == False`, `raw['cleanup']['original_preserved'] == False`, no `original_preserved` product gate, followed by `EvidenceError: historical` at line 282.

**Fix:** Validate the actual `cleanup` dictionary and its literal false `original_preserved` field, keeping `passed is False`, the exact raw object and unknown actor unchanged. Add a regression using the authoritative schema (preferably the saved report), with rejection of missing cleanup, missing predicate, true, integer and other nonliteral values. Do not rewrite the historical report or add a fabricated duplicate gate to make the adapter pass.

## Other reviewed boundaries

- Timing is opt-in. Stage/field allowlists reject unknown and textual payloads; exact numeric types reject booleans, nonfinite and oversized values. CLI formatting remains the established three-decimal millisecond format for measured fields. Daemon run correlation is explicitly distinguished from external kernel process-start ticks.
- GUI timing follows the existing accepted-generation filter. Trigger, delayed queue, nonempty internal useful-ready and meaning-ready are separate; loading and empty/header-only articles do not supply useful-ready. Internal presentation remains explicitly distinct from compositor-observed visibility. Late closed-popup meaning events do not acquire presentation telemetry.
- Physical latency uses verified kernel evdev monotonic timestamps or the same-host pre-VBox fallback; userspace receipt is diagnostic only. Delaying receipt leaves fixed kernel/frame latency unchanged. Identity, frame usefulness/freshness, literal booleans, timestamp bounds and clock-domain checks were traced.
- Performance fixes the 3/18/9 workload, process/request identities, ordinary median and nearest-rank p95. Stability fixes 20+320 requests, resource cadence, early/late RSS bounds, trend/cooldown, unchanged process, orphan/count/integrity checks. Burst distinguishes accepted completions from input count and requires the latest request. Optional online/cache and six live-meaning cases retain availability failures and null successful-latency statistics.
- Actual game routes require two distinct fullscreen games, verified source/process/rendering metadata, fresh/post-dismiss frames, gameplay return and a relative-mouse route. Pure evidence flags are structure checks; their actual truth remains a native execution and independent evidence-review obligation.

No additional concrete defect was established in these boundaries. A passing structural oracle alone does not establish physical input, actual frame content or game behavior.

## Threat-model review and verification

Reviewed the revised kernel-clock prescription in 08-01/RESEARCH, D-01 through D-10 in CONTEXT and canonical evidence/privacy distinctions. T-08-01 is addressed by the opt-in numeric schema; T-08-03 introduces no production capture/network/keyboard listener. T-08-02's clock/frame/gate restrictions remain intact; its historical-evidence adapter defect CR-01 is now corrected and narrowly verified below.

Independently executed the **10 committed `tests/test_hardening.py` tests**, loading both implementation and tests from `e7fb3d6` into an isolated process: **10 passed**, 0.050 seconds. The actual-report reproduction above then exposed the schema mismatch outside those fixtures. The executor's existing 716-test full-suite result was not duplicated or claimed as this reviewer's execution.

**Narrow fix verification:** Inspected commits `34f35c9`/`3114db8` and independently executed the committed implementation/tests in an isolated process: **11 tests passed**, 0.052 seconds. Direct invocation with the authoritative saved report succeeds with the same raw object, `passed=False`, `cleanup.original_preserved=False` and `actor='unknown'`. CR-01 is resolved; no open finding remains in reviewed unit 01 plus this narrow correction. Native unit 02 implementation and evidence, and units 03–05, remain outside the completed scope. This preliminary status remains partial.

Only this preliminary review artifact was written. No source/state edits, commits, native VM operations or changes to another agent's work were performed.

## Incremental Unit 02 Production Review

Reviewed cold-spawn timing change `1297a16` and ready-visibility staging `4ace8e9`, including their real-widget/spawn tests. Native driver work and native acceptance evidence remain outside this increment. No additional concrete issue was established in the exact opt-in stderr inheritance change: non-opted-in values keep DEVNULL, while exact `LOOKUP_TIMING=1` preserves the collector's inherited stderr and existing singleton forwarding.

Ready staging retains the exposed loading buffer, guards reveal by current request/presentation and cancels deferred ready on dismissal/shutdown/new Trigger. Its bounded exposure retry and fixed placement-error handling were traced. One timer regression remains open below.

### CR-02: Auto-dismiss can cancel the request before its useful buffer is revealed

**Classification:** BLOCKER
**Disposition:** RESOLVED in `5d04a4c`, reviewed first as the working-tree timer correction after `52ea03f`. Immediately reported in `4ace8e9` and corrected by the owning agent. Source/history evidence below is retained.
**File:** `lookup/gui.py:621`, `lookup/gui.py:663` and `lookup/gui.py:697–705`

**Issue:** Ready handling disables widget updates until matching placement/focus completion, but `present()` immediately starts the configured auto-dismiss timer. If placement takes longer than the configured timeout, the timer hides the loading buffer and dismisses the Engine identity before useful content is ever painted. A later successful matching `focus_done` then fails the visible/current guard, so no answer is shown. A one-second timeout is valid; the existing bounded search/ownership/move/raise/activate subprocess sequence can take longer than that. This is a new correctness consequence of withholding ready paint.

**Reproduction executed:** Use `GuiTests`' actual Qt widgets, deliver frozen and wait for its exposure, set `_popup_timeout=1` after initial Settings load, enable focus, hold `start_focus` without completing it, and deliver a useful ready result. Observed `updatesEnabled=False`, visible true, duration1000. After `QTest.qWait(1200)`, popup is hidden and `engine.current(identity)` is false. Calling `focus_done((identity, matching_revision, 'owned', None))` leaves it hidden. This simulates a still-bounded placement delay; it does not depend on live VM mutation.

**Fix:** Suspend the auto-dismiss timer while useful paint is withheld, and start the full configured interval only when the matching presentation is revealed, including the bounded placement-error presentation. Preserve existing dismissal/new-request/shutdown guards. Add a real-widget regression holding placement beyond a short configured timeout, then asserting the useful/error card receives the full timeout after reveal; separately retain cancellation behavior.

**Focused verification:** Independently ran the cold-spawn test and four new staging widget regressions: **5 tests passed**, 0.184 seconds. The delayed-placement reproduction above establishes the missing case despite those passing tests. No full suite or native run was duplicated. Scope remains partial; no phase acceptance is claimed.

**Timer-fix re-review:** The exposure-wait branch stops auto-dismiss; presentations with disabled updates stop the timer; only matching visible/current reveal starts the full configured interval. Deliberate user events can restart an already active timer, so input cannot accidentally rearm the withheld presentation. Existing dismissal/new-request/shutdown guards remain in place. Independently ran the new delayed-placement regression and existing bounded exposure/cancellation regression: **2 tests passed**, 2.513 seconds. Also repeated the original real-widget reproduction, setting the one-second timeout after asynchronous initialization and asserting the actual duration is1000ms: after each1200ms held placement, the popup stays visible/current with its timer inactive; matching success and failure completion each start a fresh **1000ms** interval. No other concrete blocker was established in this narrow correction. Native driver additions in `52ea03f` are not reviewed by this timer-fix recheck; whole-phase scope remains partial.

## Incremental Native Harness Review

Read complete current `tools/check_hardening.py`, `tools/check_hardening_vm.ps1` and `tests/test_hardening.py` through `9a2ec88`, plus saved final performance/burst/scales observations. No VM commands were invoked by this reviewer. Final stress execution was still in progress; plans 03–05 and final acceptance remain pending.

### CR-03: Partial scale artifact can claim complete success

**Classification:** BLOCKER
**Disposition:** RESOLVED in `a3c887f` with RED regression `cb85788` and actual interrupted-writer coverage. Original issue/reproduction retained below.
**File:** `tools/check_hardening.py:1011`

**Issue:** `run_scales()` writes `passed=all(r['passed'] for r in rows)` inside the measurement loop. After only one successful scale, its durable artifact already says `passed:true`. If a subsequent scale, frame fetch or observer command fails, the exception bypasses the final four-row result and leaves this false passing artifact on disk. A consumer inspecting saved evidence cannot distinguish it from a complete success by the advertised field.

**Reproduction executed without VM access:** Mock first-scale success and throw `RuntimeError('second_scale_failed')` on the next scale change, while allowing final scale restoration. The saved JSON contains **one row and `passed:true`** even though `run_scales()` raised. Temporary synthetic output was removed afterward.

**Fix:** Persist initial/in-progress failure state and require the complete exact four-scale set before any artifact can advertise success. Persist bounded failure/completion metadata when later operations fail; retain measured rows and restoration status. Test interrupted/failed second and fourth scales as well as a complete run. Existing final four-scale observations are complete and need not be discarded merely because this writer defect exists.

### CR-04: Resource observer misses worker-thread children and descendants

**Classification:** BLOCKER
**Disposition:** RESOLVED in `a3c887f` with RED regression `cb85788`. Fresh affected resource execution remains the owning plan's evidence obligation; prior incomplete child observations are not upgraded. Original issue retained below.
**File:** `tools/check_hardening.py:818` (resource command), consumed at `tools/check_hardening.py:951` and in `stability_report()`.

**Issue:** The resource observer reads only `/proc/PID/task/PID/children`, the main task's immediate children. It neither enumerates other tasks nor traverses descendants. Production subprocesses originate in `lookup-worker` (`lookup/app.py:163`, capture/recognition path) and `lookup-focus` (`lookup/gui.py:692`), so surviving subprocesses owned by those tasks can be missed and reported as `owned_children:[]`. This fails the explicitly required recursive owned-child observation and can falsely pass sustained/burst no-helper gates.

**Fix:** Observe children from every task of the verified daemon and recursively inspect the resulting process tree, with UID and process-start identity checks and explicit race/error handling. Missing/unreadable inspection must not silently become an empty tree. Add behavioral Linux coverage for a child launched from a non-main thread and for a descendant, along with clean exit/PID-reuse cases. Do not mutate or kill unrelated processes to satisfy the check. Prior empty lists from the incomplete observer cannot alone certify this requirement; repeat affected resource checks after correction under the owning plan.

### Other native boundaries and fresh verification

- Passive input uses the exact owned keyboard, successful EVIOCSCLOCKID and kernel timestamp-domain bounds; receipt remains diagnostic. Full release records and monotonic ordering are retained. No unrelated keys are recorded and no EVIOCGRAB is introduced.
- Journal records are sorted by monotonic timestamp before latest-trigger selection. Exact arm tokens prevent stale attempt reuse; frame retrieval checks matching attempt/token/request and screenshot hash. Actual cropped optical word/dictionary/body checks supplement internal presentation telemetry. Poll/capture overhead stays in the conservative bound.
- The physical helper checks clone UUID/name/base-disk attachment before delegation, and inherited clone guards verify network identity/original powered-off state. Rapid input uses fully released physical chords; acceptance checks actual kernel cadence rather than host loop intent.
- Owned fault actions distinguish real UID-scoped network/dictionary faults from injected capture transport failure. Network rules target the owned UID and clone DMI identity. Clipboard/ordered Klipper hashes are measured in the dedicated account; file scanning is confined to the declared owned areas and avoids symlinks. No cleanup or privacy pass is inferred before final evidence exists.
- Independently recomputed the saved final30 report: **30/30 successful, median1128.057506ms, nearest-rank p951455.247426ms, passed=true**. Recomputed verified burst: **passed=true, ten inputs, one accepted completion**, kernel inter-input intervals28.273–83.119ms. Saved final scales contain all four requested values1/1.25/1.5/2 and their checks true; second output remains explicitly unverified. These observations do not close the incomplete resource/cleanup gates.
- Fresh local `python -m unittest tests.test_hardening`: **15 tests passed**, 0.035 seconds. No long suite, native run, live process manipulation or source edit was performed by this reviewer. Original Phase 7 failed-preservation history stays unchanged.

### CR-03/CR-04 narrow fix re-review

Independently inspected `a3c887f` and ran `python -m unittest tests.test_hardening`: **18 tests passed**, 0.084 seconds. No remaining code blocker was established in this correction.

- Scale evidence is written initially and after partial observations with failure status. Success requires exactly the four declared scales, literal true row results, verified restoration and no recorded error. Observation/restoration exceptions are retained as fixed stage/type metadata. The actual first-scale-success/second-scale-failure regression checks durable `passed=false`, `complete=false`, one retained row and restored display.
- Resource observation recursively visits children collected from every task, retains PID/start/UID identities, and rechecks owner/start/child sets after traversal. Root start/UID mismatch, missing/unreadable descendants and observed tree/identity races raise instead of being converted into an empty child list. Tests exercise a non-main-task child plus grandchild and failed identity/read cases. The resource result retains observed descendant identities beside its child list.

Parent/source owner were notified that the narrow fixes are clear before fresh stress execution. This review performs no fresh native resource sampling, does not reaccept earlier incomplete child observations, and remains partial pending actual resource/cleanup evidence and plans03–05.

## Incremental Unit 03 Game Review

Reviewed `68d9f6d`'s first-game contract and current uncommitted Wesnoth commands/read-only capture/resolve taps/route observer, plus `tests/test_check_games.py`, plan03 and saved pilot. Final repeated scenes, dismissal/control, renderer evidence and cleanup are still pending execution/review. No VM operation was performed by the reviewer.

### CR-05: Game routes do not enforce distinct physical requests or source/timing identity

**Classification:** BLOCKER
**Disposition:** RESOLVED in the current working-tree correction after RED `92773ed` (commit pending at re-review). Original finding/reproductions retained below.
**File:** `tools/check_games.py:35–59`

**Issue:** Each route's timing is checked individually, but the two required routes may reuse the same PID/start/run/request and physical input timestamps. The source capture's PID/run/request is also never required or compared with its timing, even though the actual tap emits those fields. Therefore changed declared source hashes/context do not establish that repeated gameplay produced distinct correlated physical routes; unrelated source capture and overlay timing can be combined into a passing record.

**Reproductions executed:** Starting from `tests.test_check_games.record()`, replace route2's timing and overlay with route1's, retain its changed source/context, and align source capture times with route1. `game_report()` returns `passed:true`, routes2. Independently add `source.pid=source.run=source.request=999` to a route whose timing has different identity; the report still passes. All four existing game tests pass because neither adversarial case is covered.

**Fix:** Require source capture identity to exactly match its timing's PID/run/request (and observed process-start identity where collected). Require distinct request and physical-input identities across routes, strict ordered route/attempt/input sequence agreement and non-replayed input timestamps. Update native source evidence and fixtures consistently; do not synthesize missing correlation into old artifacts. Add regressions for duplicate requests, duplicate physical input, swapped source identities and wrong sequence. Final repeated actual gameplay and independent frame/control review remain mandatory beyond these structural checks.

### WR-01: Observer error logging can change successful lookup behavior

**Classification:** WARNING
**Disposition:** RESOLVED in the current working-tree correction after RED `92773ed` (commit pending at re-review). Original finding/reproduction retained below.
**File:** `tools/check_games.py:15`

**Issue:** `tap()` catches the observer exception but invokes `on_error()` without protection. The actual error callback writes an observer-error file. A logging/storage failure can therefore propagate out of an otherwise successful `Source.freeze`/`Source.resolve` call, violating the stated unchanged-return/error behavior of this read-only instrumentation. This is especially relevant when the observer failed while writing its frame/metadata and the diagnostic write fails for the same reason.

**Reproduction executed:** An original returning a known object, an observer raising RuntimeError, and an error callback raising OSError cause the wrapped successful call to raise OSError instead of returning the identical object.

**Fix:** Make the diagnostic callback best-effort without propagating its failures into the original call. Keep missing/failed observer evidence unaccepted, and test failure of both observer and diagnostic callback while preserving the original return object and original exception behavior.

### Other game boundaries and fresh evidence

- The helper restricts commands to the dedicated account/profile. Process metadata includes boot/start/UID and the isolated userdata argument; commands validate these before using game windows. Launch explicitly requests fullscreen and records requested renderer separately from subsequently observed renderer. Actual acquisition/version/signature/renderer/fullscreen fields remain required in the final game record; a requested software driver alone is not proof.
- Capture and resolve taps call the original once and return its original object on the normal path; production image/OCR/selection payloads are not replaced. Actual source PNGs are saved and optically rechecked against cursor/word/context; displayed article proof uses cropped actual popup OCR, not only a show event.
- The observer uses verified kernel monotonic chord input with full release, correlated numeric daemon events, actual ScreenShot2 capture and frame-end bounds. Its `state=complete` means only the captured useful route portion; `game_report` still requires dismissal/control and two changed scenes, and never marks the two-game GAME-01 requirement complete.
- Independently parsed the current pilot: actual game PID1042, selected `movement`, two visual context lines, kernel-input-to-useful-frame bound **2252.612119ms**. It lacks `dismissal` and `gameplay`, and the raw pilot correctly fails the complete game-report oracle. The prior rejected 3D freeze and optional renderer/mode limits must remain separate from later successful evidence.
- Fresh `python -m unittest tests.test_check_games`: **4 tests passed**, 0.001 seconds. The two correlation and diagnostic-failure reproductions above establish additional uncovered cases. No full suite, game launch, native input or source mutation was performed. Review remains partial; no game acceptance is claimed.

### CR-05/WR-01 narrow fix verification

Independently inspected the current correction and RED regressions `92773ed`. Source PID/run/request must now match timing; route request identities and physical input timestamps must be unique; route/attempt/input sequences must agree. Source capture occurs after its correlated Trigger, and its exact context span must select the queried word. The tap protects both observer and diagnostic callback failures while preserving the original successful object or original exception.

Fresh `python -m unittest tests.test_check_games`: **6 tests passed**, 0.001 seconds. Direct reproduction now rejects mismatched source identity, and simultaneous observer/logger failures return the identical original object. No remaining blocker was established in this narrow correction. Actual post-dismiss control, changed second route, renderer/source evidence and final game acceptance remain pending; the prior pilot is still incomplete. No VM/source edits or commits were performed by the reviewer.

### Later Unit 03 Observer and Two-route Evidence Increment

Re-read the current source/error persistence and multiline changes after `92773ed`. No additional concrete BLOCKER or WARNING was established in this increment.

- Matching stage6 lookup errors are checked before requiring a completed Source.resolve observation, so an early failed production lookup is not forced to wait for a query that cannot arrive. Error matching uses PID/run/request and input-time bounds; input/trigger/source evidence is retained in the failed observer record. Wrong-process, wrong-request and older errors remain excluded.
- Source frames and metadata now use PID/run/request-scoped filenames. Retrieved images are restricted to owned regular nonsymlink paths, and saved route source/overlay hashes were independently checked against the actual files for both accepted lookup portions. Capture/resolve taps still return the original objects; correlation/sequence/span checks and verified kernel-clock latency boundaries remain in force.
- Requiring at least one multiline context across changed real scenes matches plan03; it does not require every later combat/UI label to be multiline. Current visual-line metadata explicitly refers to the unchanged production OCR context's line boundaries. Both saved routes currently contain two context lines.
- Inspected actual movement source and sword useful-overlay images: the first is the tutorial map/Welcome narrative, and the second is the actual Attack Enemy dialog with a useful Mueller sword article over the game. Independent parsing yields **movement2420.879482ms** and **sword8225.06615ms** from their raw kernel/frame bounds. Source/overlay hashes match for both. These game samples are reported separately from the declared offline performance median; their larger latency is not hidden or converted to the fixed30-sample result.
- `08-wesnoth-accepted-route1.json` and `08-wesnoth-accepted-route2-combat.json` each retain `lookup_complete=true`, `complete=false` and a physical Escape dismissal observation. Neither route file yet has its final gameplay field at review time. The supplied Konrad movement and in-progress attack-control evidence still require final assembly/independent checking; useful captures alone are not promoted to completed game acceptance.

Fresh `python -m unittest tests.test_check_games`: **8 tests passed**, 0.001 seconds. No game/native action, source edit, index operation or full-suite repeat was performed. Report remains partial; final first-game control/provenance/renderer evidence, the mandatory second-game/relative-mouse route and plan05 acceptance remain pending.

### Unit 03 Assembled First-game Report and Span Correction

Reviewed RED `c298ef9`, correction `1ebef6d`, and assembled `08-wesnoth-final-report.json`. No additional concrete BLOCKER or WARNING was established. The source span remains raw: movement's `[39,48)` selects `movement,`. Exact `lookup.normalize.normalize` comparison accepts that canonical boundary punctuation/case consistently with production. Regression cases reject multiple words, unrelated words and changed interior punctuation; the raw source/context/span are not rewritten to manufacture a match.

Independent fresh game tests: **9 passed**, 0.004 seconds. The assembled report recomputes **passed=true, routes2, game01_complete=false**, retaining both conservative game latencies2420.879482ms/8225.06615ms. For each route, source PID/run/request matches timing; previously checked source/overlay hashes and newly checked before/after gameplay image hashes match the saved artifacts. The recorded renderer hash also matches the text of the saved actual in-game renderer report (`software (sw)`), rather than merely its requested launch setting.

Inspected the gameplay evidence images: Konrad's post-dismiss move reaches hex12,5 with MP3/6 after the recorded9,6/MP6 starting state; settled physical combat shows HP17/32 after HP32/32 and the actual quintain-fights-back dialogue. These semantic changes supplement differing frame hashes and active-window observations. Final report labels agent acceptance true/human acceptance false and explicitly leaves the mandatory second game, borderless/exclusive scanout and final phase acceptance unverified. Rejected HUD OCR/vmwgfx attempts and historical Phase7 preservation limits are not converted to passes.

This closes this incremental first-game source/evidence review only. The broader phase review remains partial, with second-game/relative-mouse acceptance and plan05 final integration/cleanup review still pending. No VM, source, index or commit operation was performed by the reviewer.

## Unit 04 Captured-game Contract and Honest Failure Review

Reviewed `fc4c277`, current captured-game tests and `08-doom-final-report.json`/cleanup evidence. The actual report is correctly **failed**, with `routes=[]`, `agent_acceptance=false`, useful-word/overlay/return-after-useful/repeated-route gates false and GAME-01 explicitly open. Actual Map01/fullscreen/renderer/Wayland-lock/camera/navigation observations are not substitutes for the failed useful OCR route. The QUIT/request1 and HEALTH/request3 attempts retain their actual input, production source captures and matching stage6 errors without fabricated Query or useful overlay. No OpenTTD or fixture substitution is presented as a captured-game pass.

### CR-06: Captured control gates accept unrelated or duplicated action evidence

**Classification:** BLOCKER
**Disposition:** RESOLVED in `f9a6f55`, after RED `fad487c`. Original issue/reproductions retained below. Actual captured-game acceptance remains failed independently of this code correction.
**File:** `tools/check_games.py:120–124`

**Issue:** Camera and movement subproofs require physical/game-active flags and differing hashes, but neither is checked against the captured game's PID/start identity. The two subproofs may also reuse exactly the same input timestamp and before/after frame pair. Thus one action, or evidence explicitly labeled with another process, can satisfy both required relative-camera and movement-control gates. The passing `captured_record()` test already uses identical input timestamps and image pairs for both.

**Reproductions executed:** The unchanged fixture returns `passed:true` with identical camera/movement `input_ns`, `before_sha256` and `after_sha256`. Setting `game_pid=999, game_start=999` on both subproofs, while the report's game PID/start remain500/5000, still returns `passed:true`.

**Fix:** Require each control subproof's observed game PID/start to match the report and carry its actual physical action identity/time window. Enforce separate observed camera/movement actions and reject replay of one input/frame pair across both gates, unless an explicit combined-input protocol is designed and independently proves both semantic effects. Add adversarial regressions for foreign identity and duplicated action evidence. Preserve the current real failed report; no native rerun is required merely to correct this pure oracle defect.

Other reviewed boundaries retain the two unique physical/source identities, exact source/timing correlation, verified kernel/frame clock, actual source OCR and useful/dismiss/return requirements. Capture acquisition records fixed official source/assets URLs and local hashes while explicitly recording absent published release checksums, rather than inventing upstream checksum verification. Runtime Wayland-lock evidence filters the owned unit/PID and uses ordered lock/unlock/destroy events; recent observation is kept separate from the underlying lock event. The failed current route is not promoted by actual camera/navigation success or cleanup booleans.

Fresh `python -m unittest tests.test_check_games`: **12 tests passed**, 0.006 seconds. The direct reproductions above expose missing adversarial control correlation checks. No VM/source/index operation or broad suite repeat was performed. The supplied host/target suite results are executor evidence; phase review remains partial and GAME-01 remains unaccepted.

### CR-06 Narrow Resolution Check

Reviewed exact correction `f9a6f55` and regression `fad487c`. Each camera/movement subproof now requires the actual game PID/start, a positive integer physical-input timestamp after dismissal and its own action kind. Physical identities and before/after frame pairs cannot repeat across either control or any route. Corrected positive fixtures provide independent action/frame evidence; adversarial PID/start/input/frame reuse cases reject.

Fresh `python -m unittest tests.test_check_games`: **13 tests passed**, 0.006 seconds. Independently revalidated the authoritative Doom report: **passed=false, game01_complete=false, reason=routes**, matching its stored result. No remaining code blocker was established in this narrow correction. This does not supply missing native useful OCR/captured-control-after-useful evidence or permit GAME-01 acceptance. Review remains partial pending plan05 final integration/security/evidence review. No native/source/index operation was performed.

## Incremental Unit 05 Clean-install Review

Read current `tools/check_hardening_install.py`, its contract tests, plan05 and saved clean baseline/installed identity/physical capture/login/removal/retention observations. This increment does not review a not-yet-submitted final phase aggregation or accept all phase criteria.

### CR-07: Login oracle accepts the wrong mode, absent observations and multiple owners

**Classification:** BLOCKER
**Disposition:** RESOLVED through `24716f7`, after the initial `884933a` correction. Ordered samples, expected roles, actual observed duration and surviving singleton checks now cover all reproduced cases. Original issue and intermediate residuals below remain as history.
**File:** `tools/check_hardening_install.py:27–36` and `tools/check_hardening_install.py:53`

**Issue:** `install_report()` checks both login objects with the same generic function without requiring enabled_login.enabled=true and disabled_login.enabled=false. An enabled observation can therefore be reused as the disabled proof. `login_evidence()` ignores its samples entirely and accepts any nonempty owners list whose individual fields look valid, including multiple distinct owner PIDs. Neither the sustained ownerless interval nor the singleton enabled owner is structurally established.

**Reproductions executed:** Assembled the actual saved native install files in memory into a passing install input. Replacing disabled_login with enabled_login still returns `passed:true`. Passing the saved enabled login after changing samples to `[]` still returns true; appending a second different owner PID also returns true.

**Fix:** Enforce each report slot's expected mode and validate actual ordered native samples, the observed interval, matching new graphical session identity and singleton process identity. Require ownerless disabled samples across the interval and the expected installed autostart owner in enabled samples, allowing the observed startup transition without treating restart/multiple owners as singleton success. Reject empty/missing samples and swapped/reused mode evidence. Add regressions using actual report shapes; retain the existing genuine login observations.

### CR-08: Empty file/hash evidence and arbitrary cleanup dictionary can pass installation

**Classification:** BLOCKER
**Disposition:** RESOLVED in `884933a`; exact installed paths/valid hashes, exact retention hash keys and seven required cleanup names now reject the reproduced missing-evidence cases. Original finding/reproductions retained below.
**File:** `tools/check_hardening_install.py:43–55`

**Issue:** Installed file validation applies `all()` to caller-supplied values without requiring any named paths, so `{}` vacuously proves installed identity/private helper/etc. Retention compares two arbitrary hash dictionaries without requiring config/database/unrelated keys or valid SHA256 values; two empty dictionaries prove data preservation. Cleanup requires only one arbitrary true field, with no required cleanup schema. Thus missing mandatory evidence can satisfy strict install acceptance even while the generic top-level gate booleans remain true.

**Reproductions executed:** Starting from actual saved native files, setting installed.files to `{}` leaves `passed:true`. Independently replacing both retention_before.hashes and final after-unrelated retention.hashes with `{}` leaves `passed:true`. The assembled passing input uses cleanup `{'done':true}`, demonstrating that no actual cleanup predicate is required.

**Fix:** Declare and require the exact installed path set and valid observed file hashes; declare config/database/unrelated retention hash keys and validate their SHA256 form before comparison; require all named owned-process/input/network/layout/profile/VM cleanup predicates needed by this scenario. Reject missing, empty, unknown-only, nonboolean and malformed evidence. Include the system autostart entry in clean-baseline path inventory so leftover startup files cannot be hidden from the baseline. Add adverse missing/empty schema tests while retaining the actual complete observations.

### Native observations and other reviewed boundaries

- The baseline is explicitly the new UID1002/lookup08install account on the identified owned full clone, with package/path absence and preinstalled dependency versions recorded. It is not claimed as pristine Arch or obtained by erasing the retained lookup07 profile. Host command guards check clone/base-disk identity and original powered-off state before guest commands.
- The actual enabled login changes session21→66, records16 samples over13.084804741seconds and stable installed autostart PID4929. Disabled login changes66→90, records10 ownerless samples over14.152199568seconds. The observer restarts SDDM and polls status; it does not invoke app/autostart during those observations. These supplied records are stronger than the incomplete validator currently requires.
- Actual removal observations already show absent package paths/action/owner before manual cache refresh. Physical old key leaves no owner and retained data; unrelated physical input advances its owned marker. Config/database/unrelated hashes and seeded word/card/bank data match the retention baseline. Later documented manual refresh remains separate evidence.
- Guest command paths and seeded fixtures are confined to the dedicated synthetic account; tray Exit validates the bus owner's UID/installed argv, fixture termination checks saved UID/start identity, and retention uses read-only SQLite. No broad personal-profile cleanup is introduced. Missing final owned-process/network/layout/VM cleanup evidence must remain unaccepted until submitted.
- Fresh `python -m unittest tests.test_hardening_install`: **3 tests passed**, no skips. The direct mutation reproductions above establish gaps beyond those passing tests. No VM/source/index action or full-suite repeat was performed. The final phase aggregate must remain false while the captured useful GAME-01 route is missing, irrespective of corrected install acceptance.

### Install-oracle Recheck of `884933a`

Fresh `python -m unittest tests.test_hardening_install`: **5 tests passed**, 0.007 seconds. Exact five installed paths and valid SHA256 fields, config/database/unrelated retention hashes, expected enabled/disabled roles and the seven required cleanup names now address CR-08 and the first portion of CR-07. Supplied source comparison records identical32 production archive members/no differences; no later production change is inferred.

**CR-07 remains open for two concrete interval/liveness false passes:**

1. Mutating the actual enabled-login samples to owner=false after its first successful owner sample, leaving the consistent owners metadata intact, still returns true. A daemon which dies during the remainder of the observation window can pass the enabled login requirement.
2. Keeping only the final two actual disabled-login samples still returns true, although they span only **0.775194029seconds**. The ten-second duration is measured from session login instead of the actual sample observation interval, so a late subsecond observation can masquerade as sustained absence.

Require at least the declared ten seconds between actual first/last observation samples, and require the enabled singleton to remain present with unchanged identity after its initial startup through the final sample. Add regressions for disappearance after startup and truncated late observations. The unmodified saved records already span **12.246793795seconds enabled /12.777537824seconds disabled**, with stable PID4929, so these pure oracle corrections do not require a native rerun. No VM/source/index operation was performed by the reviewer.

### Login Residual Resolution and Build Guard

Reviewed `24716f7` and `6ebf81c`. Login now requires at least ten seconds between actual first/last samples and rejects any absent owner after the initial successful startup, while retaining singleton PID/start and ordered new-session observations. The added build guard requires successful staging/makepkg exits and valid source/package/build-log hashes. Source archive member comparison remains an explicit observed equality record, not an inference from differing compressed-archive hashes.

Fresh `python -m unittest tests.test_hardening_install tests.test_hardening`: **25 tests passed**, 0.093 seconds. CR-07 and CR-08 have no remaining reproduced defect after these corrections; their actual native evidence remains reusable.

### CR-09: Final aggregate does not require final phase cleanup

**Classification:** BLOCKER
**Disposition:** RESOLVED in `d5488b3`, after RED `322b65c`. Original issue/reproduction retained below. Final actual cleanup/VM state remains an execution-evidence gate independently of this code correction.
**File:** `tools/check_hardening.py:314–347` (`aggregate_report`)

**Issue:** The aggregate recomputes product groups and validates suites/review/historical status but never reads final phase cleanup. Installation's seven cleanup predicates do not cover the other native plans' observer/game/helper termination, scoped network/dictionary restoration, display/environment restoration and input cleanup. Therefore a future otherwise successful aggregate can pass with all such cleanup evidence absent or failed, contrary to plan05's required final cleanup boundary.

**Reproduction executed without native access:** Assemble a pure valid seven-group input using existing valid synthetic performance/stability/game fixtures, saved actual burst/scales/install inputs, raw Phase7 history and valid suite/review schema. With no aggregate cleanup field at all, `aggregate_report()` returns **passed=true**, all seven criteria true. This is an adversarial oracle fixture, not a native game acceptance claim; the authoritative current Doom report still fails.

**Fix:** Declare required final cleanup predicates spanning all executed native plans and validate their exact literal booleans from the saved cleanup evidence before aggregate success. Missing, false, malformed or unknown-only cleanup must reject. Preserve original powered-off/historical-preservation distinction; do not relabel the historical disk failure as restored. Add positive complete-cleanup and adverse missing/false/partial regressions. Existing native cleanup records appear available, so no native replay is needed merely for this aggregate correction.

No VM/source/index operation, historical-report rewrite or full-suite repeat was performed by the reviewer. Final phase review remains partial; GAME-01 remains independently unaccepted.

### CR-09 Narrow Resolution Check

Reviewed `d5488b3` and RED `322b65c`. `final_cleanup_report` now derives eleven named checks from native02, Wesnoth03, Doom04 and current-install05 cleanup observations. The checks cover observer/game/helper shutdown, retained config/environment restoration, network/dictionary/display restoration, input/clipboard restoration and both VM powered-off states. Final aggregate `passed` explicitly depends on this cleanup result. Missing scoped records, false predicates and unknown-only cleanup reject.

Fresh `python -m unittest tests.test_hardening tests.test_hardening_install`: **26 tests passed**, 0.091 seconds. No additional code blocker was established in this correction. No current VM-off status or final independent completion is inferred from the pure test fixture. Report now has zero open code findings in its reviewed incremental scope, but remains partial until final submitted source/evidence/security review. Missing captured useful game evidence continues to prevent phase/GAME-01 acceptance. No native/source/index operation was performed.

## Final Full-scope Review: Raw Binding Finding

Final source/evidence review started at `144d1e6`, explicit twelve-file scope from `1b54572`. All five unit summaries and the final frozen source were submitted. No broader unrelated source was added to scope. The new assembler binding below was not part of earlier narrow aggregate-fix checks.

### CR-10: Evidence assembler replaces failed raw outcomes with success constants

**Classification:** BLOCKER
**Disposition:** RESOLVED in `a10c5e1`, after RED `49e6659`. Original issue and isolated reproduction retained below.
**File:** `tools/check_hardening_install.py:139–155` (`assemble_reports`)

**Issue:** The assembler writes `build.stage_exit=0`, `makepkg_exit=0` and a fixed package SHA256 instead of consuming the saved `08-install-build-provenance.json`. It likewise declares negative-origin test exit0/count1 independently of the test outcome in the saved log. Thus the successful-exit/hash checks added to the lower-level validators do not protect this final binding step: failed or changed supplied evidence is rewritten to look successful before validation.

**Reproduction executed:** Copy only the necessary retained JSON/log evidence into a temporary isolated directory. Change saved build provenance to stage_exit1/makepkg_exit1 and a different package hash; replace the negative-origin log with `FAILED (failures=1)`. Invoke `assemble_reports()` on that copy. Observed native install `passed:true`, emitted build exits0/fixed original package hash and aggregate geometry criteriontrue. Original workspace evidence remained untouched; temporary data was removed.

**Fix:** Bind build statuses/package hash to the actual saved provenance and check its source hash against the staged-source metadata. Bind the geometry test result to an observed result record or validate the actual test log/result schema, including failed/malformed/missing outcomes. Hashing a failing log must not make it a successful test. Add assembler-level regressions using failed provenance and failed negative-origin evidence; keep actual successful observations unchanged.

**Fresh verification during this final pass:** Scoped timing/CLI/GUI/game/hardening/install suite: **86 tests passed**, 5.760 seconds. All final aggregate raw-source digests and both final suite-log hashes match saved files. Independent raw-oracle recomputation yields six true groups, games=false, overall=false and11/11 global cleanup true. The fixed751-test host/target logs contain successful final results with8/0 skips respectively; these executor runs were inspected, not rerun by this reviewer. The assembler defect concerns false-pass resilience and does not convert the actual failed Doom/game aggregate to success.

## Final Security Threat-model Coverage

The ASVS L1/STRIDE review is scoped to the submitted application instrumentation, native tooling and evidence boundaries. It is not a blanket certification of dependencies or all possible OCR/game scenes.

| Threats | Reviewed mitigation and disposition |
|---|---|
| T-08-01..03: numeric telemetry, acceptance truth, GUI | Opt-in finite numeric allowlist, no query/context/token/error serialization in production telemetry; internal ready/presentation is distinguished from actual frame evidence. Existing generation filtering and worker ownership remain intact. Ready placement/timer regression corrected and verified. |
| T-08-04..07: passive keyboard, VM/fault ownership, privacy, performance | Exact owned keyboard/chord only, no grab/unrelated key recording, verified monotonic kernel clock and receipt diagnostic; fixed clone/base-disk/account identities and bounded commands. UID-scoped marked network table with identity checks before deletion; owned dictionary fault paths. Exact public-profile clipboard/history hashes and scoped PNG inventory. Raw30/stress/burst records and immutable thresholds retained. |
| T-08-08..10: Wesnoth acquisition/session, route truth, screenshots | Official acquisition/provenance, isolated profile, actual game PID/start/boot/window and observed renderer. Original capture/resolve objects preserved by transparent taps; correlated source/overlay/input identities and distinct gameplay changes checked. Error callback failure cannot change production outcome after correction. Public game evidence only. |
| T-08-11..13: captured-game source, locked input, session control | Fixed official engine/assets locations and honest absent published-checksum evidence. Actual owned Wayland lock events and renderer observations; no privileged production input grab or KWin policy relaxation. Failed useful OCR remains failed. Foreign/reused camera/movement proof rejects after correction. No captured-route success is inferred from real camera/navigation alone. |
| T-08-14..16: clean install lifecycle, final evidence, retention/cleanup | Separate UID1002 baseline without erasing retained UID1001 data; genuine SDDM sessions and ordered sustained enabled/disabled observations. Exact installed/retention hashes and required cleanup names. Final cleanup derives eleven checks across all scoped execution records. Raw Phase7 false preservation report/unknown actor is retained unchanged. Final assembler binding CR-10 is corrected and independently verified in `a10c5e1`. |

Actual retained evidence independently supports the submitted six positive groups and explicit negative captured-game outcome; security review does not waive the missing mandatory product scenario. Original VM byte preservation is still the historical failed predicate, distinct from the final recorded powered-off state. No repair/revert/write of the original VM was performed by this review.

## Final CR-10 Resolution and Evidence Disposition

Inspected `a10c5e1` and RED `49e6659`. The assembler now consumes saved build provenance, checks successful recorded staging/makepkg exits, valid source/package hashes, source metadata agreement, the actual recorded build-log digest and expected successful build/install markers. Negative-origin evidence binds the observed exit/count/test identity/digest to the actual successful unittest log. Failed, changed, malformed or missing outcomes cannot be promoted merely by hashing their log; aggregate geometry requires the verified binding.

Fresh affected verification: **27 tests passed**, 0.815seconds. Actual saved build/negative records bind successfully; failed provenance and failed negative-log cases reject, including the original temporary-copy reproduction's failure class. The final **87-test** scoped run passed afterward. Production32-member equality remains the executor's recorded archive comparison, inspected with no differences; post-`d5488b3` changes are limited to evidence tooling/tests and do not relabel game or performance executions.

Final raw binding checks performed independently during this review: all recorded aggregate raw-source digests matched files; final full-suite hashes matched their then-current saved logs; raw-oracle recomputation yielded performance/stability/geometry/privacy-faults/install/live-meaning-observation true and games false. Native installation had11/11 product gates and7/7 installation cleanup true. Scoped global cleanup recomputed11/11 true from native02/Wesnoth03/Doom04/install05 records. The six live meaning attempts remain blocked6/6, successful-latency median/p95 null; observation completeness is not provider success. Both-VM-off cleanup is distinct from the preserved historical original-disk failure.

The captured game's two real failed attempts, stage6/no Query outcomes and zero accepted useful routes remain authoritative. Real lock/camera/navigation observations do not close that gap. Optional second output/borderless and universal decorative-font/game compatibility remain unverified; code/security review does not replace the independent phase verifier or authorize milestone completion.

Only this review artifact was edited and committed by the reviewer. No source/state changes, native VM input/boot/session operations, personal-profile cleanup or historical-report mutations were performed.

## Unit 06 Task 2 Incremental Review

Read approved08-06 plan and GAP-RESEARCH, changes through `dc1fe5e` after RED `27c1657`, new transparent SDL hooks and candidate launch/observation seams. The one explicit AssaultCube asset URL/52071427byte/SHA256 pin, RC1 identity, version and owned executable are required; no arbitrary engine/executable fallback was introduced. GL proof requires actual game-log text/digest and matching game PID/start rather than accepting a requested software environment. Current acceptance is Wayland-only; an X11 driver is rejected rather than mislabeled.

Same-process SDL relative calls must report successful requested/enabled state; protocol events are digest-bound, ordered and must end locked before physical input, with no intervening unlock/destroy. Existing source/request/run identity, verified kernel-input/capture-end clock, exact canonical span, word-box, useful overlay and distinct input/control evidence checks remain active. SDL wrappers call the original once, query actual state/driver, and return its original result/errno. Actual final GL text and final controlled routes are still execution-evidence obligations.

### CR-11: One early pilot cleanup failure skips shutdown and settings restoration

**Classification:** BLOCKER
**Disposition:** RESOLVED in `ebe25e7`, reviewed initially as a working-tree correction after `dc1fe5e`. Parent/owner notified; original issue/reproduction retained below. Actual cleanup is not inferred from the correction alone.
**File:** `tools/check_games.py:38–60` (`pilot_session` finally)

**Issue:** Key release, mouse release, guest process/package cleanup, shutdown, OFF verification and restoration are all inside one try. An exception in an early operation exits directly to `cleanup_error`, then writes state finished. Remaining safe cleanup actions are never attempted. For example, a failed keyboard release or SSH cleanup can leave the owned clone running with isolation settings changed, even though the approved plan explicitly requires an unconditional bounded shutdown and OFF-only restoration attempt on failure/exception. Recording a false cleanup result is necessary but does not fulfill the required independent best-effort cleanup path.

**Reproduction executed without VM or filesystem mutation:** Mock VBox info/start operations and record writes, arrange a normal stop request, then make the first `vm_input` release raise `RuntimeError('release_failed')`. Observed cleanup_error, **shutdown_attempted=false**, **restore_attempted=false**, and final state finished. All subprocess/record operations were mocked; no original/clone action occurred.

**Fix:** Separate cleanup steps into independently guarded attempts, accumulate failed gates/errors, and continue to the safe owned shutdown/OFF verification/restoration sequence despite earlier release or guest-cleanup failures. Preserve the prohibition on restoring settings while running, exact UUID/base-disk ownership and original read-only behavior. Add controller regressions for key/mouse release failure, guest-cleanup SSH failure and shutdown failure, proving later safe attempts occur and unsuccessful steps remain false. Do not turn a partial cleanup into success.

Fresh `python -m unittest tests.test_check_games`: **14 tests passed**, 0.011seconds. The mocked cleanup reproduction establishes an uncovered path beyond those passing tests. The saved feasibility pilot explicitly retains failed held-TAB/stage6 history and marks renderer/final acceptance pending; its successful `name` useful bound4232.717534ms alone does not close GAME-01. No source/VM/index edits or commits were made by this incremental review.

### CR-11 Narrow Cleanup Resolution Check

Read the current `pilot_cleanup_steps` correction. Each release, guest cleanup and shutdown operation is independently guarded, so an early failure no longer skips safe remaining attempts. Ownership is checked before clone mutation; shutdown/power polling/forced-stop fallback and settings restoration run afterward, with restoration restricted to observed OFF state. Per-step errors and final clone/original/settings readbacks remain explicit.

Fresh `python -m unittest tests.test_check_games`: **15 tests passed**, 0.043seconds, including simultaneous key-release and guest-cleanup SSH failures while proving shutdown and OFF-only restoration still occur. No additional blocker was established in this narrow correction. The already-running old controller is not assumed to reload changed source; actual execution of updated cleanup and final raw readbacks remain required. New actual GL/client-log, repeated route and camera/movement evidence is still being assembled and is not accepted by this code-only recheck. Expanded06 review remains partial; no VM/source/index operation was performed.

### Unit 06 Meaningful World-motion Guard Recheck

Read the current semantic guard and durable old-bad/old-real control regression. No additional concrete code blocker was established. For the fixed1280x800 local-map scenario, `world_change()` compares RGB pixels in `[128,160,384,360]`, an inspected world area outside weapon/HUD/FPS/scoreboard controls. The strict candidate requires at least1383 of138240 world pixels to differ and different ROI hashes; a full-frame difference alone is insufficient. Camera proof additionally requires two distinct ordered kernel EV_REL/X60 events, bounded by the recorded capture end. Existing game PID/start, post-dismiss timing and globally distinct input/frame proof checks remain intact.

Fresh `python -m unittest tests.test_check_games`: **16 tests passed**, 0.229seconds. Independently recomputed the retained old false-camera pair: **121/138240** changed world pixels, correctly below threshold; the retained genuine rotation pair gives **138120/138240**, correctly accepted by the world-change condition. Visually inspected the map landmarks/ROI location in those actual frames. This is a bounded scene-specific semantic guard, not a universal guarantee against animated-world content.

The new run's initial `08-06-final-route1-camera.json` for game PID986/start4587 reports **zero** world change despite two physical pulses; it is rejected/retained and must not be selected for acceptance merely because observer state says complete. Subsequent W input reports138182 changed world pixels. `08-06-final-route1-camera-after-w.json` records later, distinct EV_REL/X60 events at152740415000/153226544000ns and138103 changed world pixels, after the same route's dismissal. Both W and camera may occur in either post-dismiss order; W→camera does not waive either requirement. Those new values were parsed from raw records; final source/control-image hash recomputation and second-route/GL/cleanup binding remain pending assembly.

The prior first native candidate report stays false, and failed old-controller cleanup is retained separately from observed updated recovery. No GAME-01/candidate acceptance is inferred in this increment. No VM/source/index operation was performed by the reviewer.

### CR-12: GL-context evidence is not bound to its current game window

**Classification:** BLOCKER
**Disposition:** RESOLVED in `749076b`. Parent and owning agent notified with code clearance; original issue/reproduction retained below. Fresh native routes and their actual pre-input binding remain separate evidence obligations.
**File:** `tools/check_games.py:110–123` and `tools/check_games.py:219–227` — new GL wrapper and actual-context validation branch at review time.

**Issue:** The new raw GL row carries PID/time/renderer/version/driver but no SDL window/current-context identity. The validator checks PID/start/time/digest but ignores whether the returned context is current for the captured game window or matches that window's actual SDL grab evidence. A valid record from another same-process window/context, or one explicitly marked noncurrent, can therefore satisfy renderer acceptance. This misses the requested raw PID/start/window/context binding.

**Reproduction executed:** Construct a valid explicit-candidate fixture with GL row `window=999`, `current_window=888`, `current_context_matches=false`, while its actual SDL grab row declares window1. Keep matching PID/start, valid pre-input timestamp and recomputed canonical digest. `captured_game_report()` returns **passed=true** for both routes. The current positive GL fixture also accepts missing window fields entirely.

**Fix:** Observe the actual SDL window ID and verify `SDL_GL_GetCurrentWindow()==window` and `SDL_GL_GetCurrentContext()==original_result` before reading GL strings. Put `SDL_GL_GetProcAddress` inside the successful/current-context branch rather than calling it even after an original NULL result. Bind the captured raw window/currentness evidence to the same-process SDL grab/window observation used for the route, and reject absent, mismatched or explicitly noncurrent records. Add adversarial wrong-window/currentness tests without replacing actual returned contexts or synthesizing a verified flag.

Fresh `python -m unittest tests.test_check_games`: **17 tests passed**, 0.221seconds; the direct foreign/noncurrent-window reproduction above exposes an uncovered acceptance gap. Prior PID986 zero-byte/lost GL evidence remains unaccepted; old PID1139 logs must not be borrowed. New PID2509's actual pre-input GL observation is a new attempt and needs its complete raw binding/final routes before acceptance. No native/source/index operation was performed by the reviewer.

### CR-12 Resolution and Fresh GL Preflight

Reviewed `749076b`. C GL queries now occur only after a successful original return, current-context equality to that return, and current-window equality to the original window. NULL original return short-circuits before context/window/GL procedure queries; no extra diagnostic lookup runs on that failure path. The original is called once; original pointer and saved errno are returned. Successful logging checks nonnull renderer/version strings and closes the record stream immediately.

The AssaultCube oracle accepts only the actual SDL GL-context record path. It requires matching PID/start, valid context timestamp after process birth and before every route input, canonical record digest, actual current SDL window ID, nonzero raw window/context pointers and true observed context equality. Each route's actual SDL grab window/pointer must match that same GL window; the old text-only game-log escape is removed. Fresh **17 game tests passed**, 0.217seconds. The original foreign/noncurrent-window fixture now rejects with `gl_current_window_context`; adverse PID/time/digest/driver/window/pointer cases remain covered.

Parsed `08-06-window-gl-preflight.json` for the new game **PID3661/start69061**: actual GL timestamp690729560221ns, current/window ID4, matching grab/window pointer0xe39a640 and current context pointer0xe39c6b0, observed true equality. Actual renderer is llvmpipe LLVM23.1.3 with Compatibility4.6/Mesa26.2.5 and SDL Wayland. Successful relative-state1 and an actual ordered Wayland locked event belong to that same PID. These are source-bound preflight observations, not borrowed PID1139/986/2509 output and not a requested environment inference. No physical lookup had been accepted for this new process at this review checkpoint; all fresh routes/control/cleanup still need final binding.

No additional concrete blocker was established. Parent/source owner received code clearance before fresh controlled routes. No VM/source/index operation was performed by the reviewer; expanded06 review remains partial.

### Unit 06 USER_KEEP_RUNNING Input Adapter Review

Read the artifact-local `08-06-owned-input.ps1`, `08-06-native-takeover.py` and `08-06-takeover-controller.py` snapshot. The input adapter checks fixed clone UUID/name/running state, independent disk UUID, MAC and loopback NAT2227 before input; keyboard and COM mouse calls target only that clone UUID. It does not inspect or control the original guest. Replacing the host input transport preserves existing physical kernel-event and compositor-frame observation; calibration motions are separately recorded and cannot substitute for measured world-control proofs. Fresh nonexecuting PowerShell parser and Python AST checks passed for these three artifacts. No adapter, guest command or VM operation was executed by the reviewer.

Final orchestration review remains pending on two source-owner follow-ups, reported immediately: the controller still calls the disclosed legacy original-OFF input-release helper and computes policy compliance using original state equality; this must be replaced by clone-only release and zero-our-original-actions/guarded-mutations accounting. Separately, `08-06-native-takeover.py:25` dispatches later guest commands directly through `games.vm_command`; its DMI assertion occurs only in the setup script, rather than guarding each dispatched mutable guest command. Add an artifact-local DMI-checked dispatch path retaining the pinned host key and explicit2227 endpoint. The input adapter itself has no demonstrated foreign-target path; these pending integration seams are not final cleanup or route acceptance. Original-running status is permitted by the explicit user policy and is not a finding.

**Correction recheck:** The controller now loads the clone-only input adapter and no longer compares original before/after states. Those two corrections are confirmed. The new `guarded_command()` protects the presently listed launch/route/control operations, but its selective action list leaves other mutable guest actions unguarded; direct `guest(script)` cleanup calls and the controller's plain SSH cleanup/poweroff callback also lack a common DMI precondition. This remaining isolation-contract gap was reported before final cleanup acceptance. Requested fix: a common guest-script DMI prefix, unconditional guarded dispatch, and the same precondition in the controller's guest callback. `original_state_respected` must ultimately bind actual scoped action provenance, rather than treating an initialized empty control list alone as evidence. Current source changes are partial and final cleanup/route evidence is not accepted by this recheck.

**Latest source disposition — resolved:** Current `guest()` prepends the exact clone DMI assertion before every supplied payload. `guarded_command()` checks unconditionally before dispatch, including clipboard, ACL/map/package and route/control operations. The controller passes `guarded_ssh()` to cleanup; its shell command uses DMI validation followed by `&&` before cleanup or poweroff. Release uses the fixed clone-only adapter, while original host identity/state observations remain read-only and state equality is not required. No remaining defect was established in these narrow corrected paths.

Fresh mocked verification, with no SSH/input/VM execution: seven formerly uncovered dispatch actions fail closed when the DMI check fails; decoded guest payload begins with DMI validation before its mutation; explicit2227 and pinned known-hosts arguments remain present; extracted controller callback puts the guard before both guest cleanup and poweroff. All checks passed. This is **on-disk source clearance only**. The owner identifies live controller86089 as compiled from an older prefix; it cannot inherit the correction. Actual executed receipts and any subsequent independently guarded cleanup must be preserved separately, and final action-scope provenance remains required. No route, aggregate, native cleanup or expanded phase acceptance is implied.

### Final Unit 06 Cleanup and Instrumentation Evidence Recheck

Reviewed current owned input/native/controller/closure artifacts and final raw cleanup bindings. The new controller46069 is reported launched with the guarded source from its start; expired86089 remains separately retained and is not relabeled as hot-reloaded. Boot/settings mutations now reside inside the protected lifetime. The controller restricts mutable host commands to the fixed clone UUID, records actual argv/exits, and derives original-policy compliance from those scoped actions. Input remains clone UUID/disk/MAC/NAT guarded; guest payloads and cleanup/poweroff retain the DMI precondition. Observer-only `OMP_THREAD_LIMIT=1` does not alter production OCR configuration or replace captured source pixels.

Independently verified **274 manifest entries**, with zero byte-count/hash mismatches. Parsed **13 controller host actions**, including three mutations all targeting the owned clone, and **152 guarded action-audit rows** consistent with the clone/explicit2227 scope. Original VM access in this reviewed scope is read-only host UUID/state observation; no original guest/disk/control action is present. This supports the explicit USER_KEEP_RUNNING policy without requiring original OFF or before/after state equality. Historical07 evidence is unchanged.

All12 final cleanup gates are backed by the saved release, owner/process/registry, package removal/absence, retained data, clone OFF and restored-settings observations. Controller shutdown's SSH disconnect remains explicitly recorded as a failed command receipt; the later actual host OFF and settings readbacks independently establish the resulting state. This is not a fabricated successful shutdown exit. Final guest cleanup records no remaining owned processes, owner false/keys empty, package absent and retained data. No concrete remaining cleanup/instrumentation blocker was established in this bounded review.

Recomputed `captured_game_report()` from the saved final candidate: **passed=false, game01_complete=false, reason=routes**. The report keeps only one complete current-process route (game PID1041/start3423); actual second-scene stage6/no-Query failures remain rejected. No stale process evidence or diagnostic PSM11 selection is promoted into a production route. Fresh `python -m unittest tests.test_check_games`: **17 tests passed**,0.290seconds. Expanded phase review stays partial and GAME-01 stays open pending the later broader07 gate/fallback work. Reviewer performed no VM/source/index operation and changed only this report.

### Unit 08 Task 1 Production OCR Fallback Review

Reviewed `lookup/ocr.py` and `tests/test_ocr_fallback.py` in committed GREEN `f74ede4`, against the approved08-08 task1 contract and prior implementation. No concrete bug/security regression was established in this bounded source change. Successful PSM6 returns its original first selection with one preparation/process; only valid no-selection output can lead to PSM11, reusing the same PNG and Transform with unchanged confidence/proximity rules. Explicit11/fallbackFalse stay single-pass. Process/parser failures stop immediately with existing private fixed errors. Each process receives at most3seconds and the second process receives the positive remaining budget from the first-process-start+6seconds deadline. Timings separately sum subprocess and parse/selection work.

Fresh verification: **44 tests ran,1 skipped, remainder passed** for fallback/core/CLI/privacy/timing; an in-memory load of the exact committed `f74ede4:tests/test_ocr_image.py` ran **10 tests, all passed**. No checkout or source file was changed. The initial current-tree combined run also encountered the concurrent task2 calibration RED requiring `fallback=False`; parent confirmed that active work, and it is excluded from task1's disposition. This clearance does not cover unfinished corpus/calibration task2, lifecycle/transparent observer task3, new native performance/game evidence or final broader acceptance. Only this report was edited; no VM/index operation occurred.

### Unit 08 Tasks 1–3 Production, Corpus and Observer Review

Reviewed committed `f74ede4`/`fec151d`/`5581acb`: `lookup/ocr.py`, `tools/calibrate_ocr.py`, `tools/check_games.py`, `tests/test_ocr_fallback.py`, `tests/test_ocr_game_sources.py`, `tests/test_ocr_image.py`, `tests/test_app.py`, `tests/test_app_gui.py`, `tests/test_check_games.py` and the four-source fixture manifest. No concrete remaining bug/security regression was established within this increment. Earlier review history and failed native attempts remain unchanged.

Calibration now explicitly disables fallback for independent PSM comparisons. Independently compared all four portable fixture PNGs byte-for-byte with their referenced retained actual source files and their declared SHA256: all match. Production defaults exercise the cascade without replacing actual Tesseract output; prepared RGBA/Transform integrity has a separate check. Actual target Breeze96/context144 and non-skipped target runs reported by the owner remain target evidence, not reviewer-run host results.

The game observer now taps the original `recognize_image()` return and records its actual Selection word/context/span/box. The original call/result identity is preserved and errors remain best effort. Route extraction binds that returned selection to the original resolved Query and cursor geometry; it no longer reruns a forced11 diagnostic to supply acceptance metadata. Existing request/process/capture/frame binding remains in force. Diagnostic output is not inserted into production Source or Query. Lifecycle regressions hold the actual recognition path at its second child-process seam and verify stale replace/dismiss/reload/stop cannot publish/persist/enrich; the current request counts once, and Qt quit stays responsive while awaiting bounded completion.

Fresh reviewer command covering fallback, game sources, image/calibration, Engine, GUI and game oracle: **93 tests ran,3 skipped, no failures**,6.865seconds. The skips are honest host real-OCR availability limits; no target or native execution was performed. Parent received code clearance for this reviewed increment. This does not accept the new09 game/performance workloads or final broader07 aggregation. Only `08-REVIEW.md` was edited; no VM/source/index operation occurred.

### CR-13: Current-performance binding accepts relabeled historical samples

**Classification:** BLOCKER
**Disposition:** RESOLVED in `787ca19`; original issue and intervening residual evidence retained below.
**File:** `tools/check_hardening.py:143–159`, `current_performance_report()` in `1e30b14`.

**Issue:** The validator compares copied per-row build labels with a receipt, but never binds the physical process/run identities to an observed loaded/current build. Its source-member map can contain only `lookup/ocr.py`, with arbitrary self-consistent source/package hashes and zero exit integers. It therefore accepts precisely the forbidden reuse of old physical measurements with a new source label, while reporting `source_bound=true`.

**Executed reproduction:** Load the actual tracked `08-performance-final-attempts.json` from the old5d04-era run. Add `build={source_sha256:'a'*64,package_sha256:'b'*64,ocr_sha256:'c'*64}` to every row. Supply a receipt with that build, source/installed maps containing only `lookup/ocr.py:'c'*64`, and zero stage/build/install exits. No physical timing/request/process value changes. The result is **passed=true, source_bound=true, attempts=30, median_ms=1128.057506, errors=[]**. This reproduction operated on in-memory objects only.

**Fix:** Bind the expected current source/module inventory and observed package/install evidence to raw runtime receipts for every measured PID/start/run, captured after installing that build. Require the measurement identities to match those verified runtime observations rather than accepting copied build labels. Reject missing/truncated module inventory and historical process/run receipts. Add an adversarial regression using the actual retained old samples with newly attached build labels, and keep all original physical performance thresholds intact.

Fresh existing `python -m unittest tests.test_hardening`: **21 tests passed**,0.139seconds; they do not cover this false acceptance. Review scope is only the new source-binding function/tests and their called performance validator. No VM/source/index action was performed; only this report was edited.

**CR-13 recheck at `c80dde0` — remains OPEN:** The new raw archive/runtime API rejects missing raw evidence and directly swapped old process/run identities. It parses observed proc UID/start/cmdline, same boot/post-install birth and matching raw timing events, which addresses the original copied-label path. However, complete source inventory is still self-selected: the validator requires only that the source TAR contains `lookup/ocr.py`, then compares installation/runtime maps to whatever that TAR contains.

Executed residual reproduction: start from the positive raw-byte fixture; retain **only `lookup/ocr.py`** in both source/package TARs, recompute their compressed archive hashes, reduce installation/runtime member maps to that one file, and recompute raw-runtime digests. Keep all actual process/timing constraints intact. Result: **passed=true, source_bound=true** despite missing every other production/module/packaging member. Require the independently defined staging inventory before source/package/runtime comparison; self-consistent subset archives must fail. Parent/source owner notified immediately. Fresh existing hardening suite: **23 tests passed**,0.285seconds. No additional concrete residual was established in the reviewed proc/boot/trace paths; no VM/source/index operation occurred.

**CR-13 recheck at `6e6ee38` — remains OPEN on current bytes:** Independent complete32-member name inventory now rejects the truncated archive reproduction; fresh hardening suite **24 tests passed**,0.507seconds. However, current source bytes are not independently checked. Executed another narrow mutation: retain the full inventory and replace only OCR content in both source/package TARs with the actual `git show 5d04a4c:lookup/ocr.py` bytes; recompute both archive hashes and installation/runtime OCR hashes/digests. Result remains **passed=true, source_bound=true**, accepting the historical single-pass OCR module as current. Compare the complete extracted source hash map against independently selected current repository files with the same CRLF-to-LF staging normalization, rather than names alone. Parent/source owner notified before long-workload clearance. No VM/source/index operation occurred.

**CR-13 final disposition at `787ca19` — RESOLVED:** The extracted complete source hash map must now equal independently selected current repository bytes, using the staging CRLF-to-LF normalization. Package archive members and installed/runtime maps must match that anchored map. Raw proc PID/start/UID/cmdline, same boot, post-install birth, post-frame observation and matching raw trigger/useful trace bind each measured identity to those installed bytes. All known false-acceptance variants now reject: actual historical30 with new labels, absent runtime artifacts, partial inventories with fully recomputed digests, actual old5d04 OCR bytes in otherwise complete archives, and mismatched runtime/process/trace/boot/install observations.

Fresh reviewer `python -m unittest tests.test_hardening tests.test_timing tests.test_hardening_install`: **37 tests passed**,2.450seconds. No further concrete blocker was established in this bounded recheck. Parent/source owner received code clearance before the long native workload. This validates the oracle implementation; actual new archive/install/runtime receipts and native measurements still require later evidence review. No VM/source/index operation occurred; only this report was edited.

### Unit 09 Initial Native Transport/Lifetime Review

Read the active `08-09-native.py` and `08-09-native-controller.py` snapshot. Guest dispatch prepends the exact clone DMI assertion and uses pinned SSH2227; fixed input adapter retains UUID/disk/MAC/NAT checks. Controller host mutations target only the clone, while original host UUID/state is read-only metadata under USER_KEEP_RUNNING. Boot/settings changes occur inside the protected lifetime; the existing cleanup helper independently attempts release, guest cleanup, shutdown, observed OFF and OFF-only restoration. No concrete blocker was established in these current transport/lifetime paths.

Fresh mocked guest-prefix/pinned-endpoint checks and controller AST parsing passed without any VM call. The adapter was actively amended from encoded command-line payload to Python stdin during review; the final successful mock exercised the latter snapshot. No actual performance receipt collector/assembler was present in the supplied artifacts at this checkpoint, so actual source/proc/runtime receipt usage is **not yet cleared**. Parent/owner were notified to provide that code before30 acceptance. Final cleanup must inspect nested per-step results from `cleanup()`, which catches its action failures, rather than infer success solely from the outer helper's `guest_cleanup.ok`. No native result or cleanup is accepted here; only this report was edited.

### Unit 09 Actual Receipt Collector/Assembler Pre30 Review

Read the subsequently supplied `08-09-performance.py`, current native transport, actual build and package receipts. No concrete collector/assembler blocker was established. Successful-result collection reads actual proc stat/status/cmdline, boot/tick rate, all installed member bytes and user-journal timing text after the observed frame. Raw runtime JSON bytes are saved under recomputed SHA references; PNG/input/ready/result files are retained separately. Assembly loads actual source/package archive bytes and saved runtime files into the corrected current-performance oracle rather than synthesizing successful process/runtime metadata.

Fresh local verification independently checked both actual archive digests, all **32 current normalized source/package/installed member hashes**, matching actual build/install boot and monotonic completion epoch, and collector AST syntax. All checks passed without VM calls. The helper's existing ordinary cold owner-absent/physical configured-chord launch, kernel input clock and matching useful captured-frame semantics remain unchanged; per-frame collection happens afterward. Parent/source owner received pre30 code clearance. Actual30 measurement/raw-image/input correlations and final cleanup remain later evidence obligations; no performance or phase pass is claimed by this review. Only this report was edited; no VM/source/index operation occurred.

### WR-02: Process-observation metadata can change the original subprocess result

**Classification:** WARNING
**Disposition:** RESOLVED in `57db97e`; original issue and reproduction retained. Current production byte-input/captured-byte-output calls were unaffected by the demonstrated modes.
**File:** `tools/check_games.py:619–623`, `observe_ocr_process()`.

**Issue:** Only the final observer callback is protected as best effort. Input hash/PSM metadata construction occurs before the original call, and output hashing occurs before returning the original result. Valid matching subprocess modes with text input or uncaptured stdout can therefore fail because of instrumentation. The wrapper is globally assigned to `subprocess.run`, so supported original call modes should remain transparent even when they cannot be measured.

**Executed reproduction:** A matching Tesseract argv with byte input and a successful `CompletedProcess(stdout=None)` causes the original to run once, then the wrapper raises TypeError instead of returning that result. A matching call with `text=True,input='png'` raises TypeError before the original runs (zero calls). Existing **20 game tests passed**,0.211seconds, but omit these modes.

**Fix:** Treat all metadata extraction/hashing as best effort, or explicitly skip observation for unsupported input/output modes while still calling the original exactly once. Preserve its exact result object/exception independently of observation failures. Add successful uncaptured-output/text-mode cases and a metadata-failure case. No raw OCR text/error contents need recording; retain only numeric/hash/fixed error-class metadata. No VM/source/index operation occurred; only this report was edited.

**WR-02 resolution recheck:** `57db97e` bypasses unsupported input metadata and suppresses unsupported output metadata without changing the wrapped call. Fresh game/fallback suite: **31 tests passed**,0.289seconds. Independently exercised text input, uncaptured stdoutNone, byte input with string stdout, and an original TimeoutExpired while the observation callback throws: original exactly once and exact result/exception identities are preserved. No additional concrete issue was established in this bounded recheck. Parent/source owner received observer code clearance; actual newly loaded helper/game routes remain later execution evidence. No VM/source/index operation occurred.

### Unit 09 Actual Current-source Physical30 Evidence Review

Independently recomputed `current_performance_report()` from the saved actual source/package archive bytes, package/install receipt and all30 SHA-referenced raw runtime observations. Result: **passed=true, source_bound=true,30/30 successful**, median **1088.2457725ms**, p95 **1431.759096ms**, zero errors and the exact3cold/18distinct/9repeat workload. Current complete32-member byte anchoring, post-install process birth, boot identity and raw matching journal trace checks all pass the corrected oracle.

For every sample, independently verified saved useful PNG SHA against the measured frame identity, raw result PID/start/run/request/input/frame timestamps, and matching saved physical kernel input/release records. Three cold lookups have separate new process identities; warm/repeat samples use the third current process. Visually inspected the first bank and final hand captures: each shows the matching useful Mueller article. The cold subgroup p95 is separately **1916.468943ms**; it is retained honestly rather than presented as the overall p95 or waived by relabeling.

This current-source performance evidence is accepted within its declared physical30 scope. It does not accept GAME-01, changed-path stability, the still-open per-pass observer warning or final cleanup. All failed historical attempts remain intact. No VM/source/index operation occurred; only this report was edited.

### Unit 09 Two-route Captured-game Raw Evidence Review

Recomputed the assembled `08-assaultcube-cascade-report.json`: **passed=true, routes=2**, with latencies **4303.613319/4081.585538ms**. Both routes use actual game PID7496/start32039/window4 and the current observer PID7595, with distinct fresh source/physical input/request/frame identities. Source Query/context/span/box agree with the actual returned production Selection. Route1 records one PSM6 pass; route2 records actual PSM6 then11 with the identical native prepared-input SHA and a genuine returned name Selection. No diagnostic result is substituted.

Independently checked both source/overlay hashes, all eight control PNG hashes and recomputed all four worldROI observations: route1 movement/camera **137602/137685**, route2 **137191/136696** changed pixels. Actual saved journal trigger/useful events match the source request identities and frame timing. Visually inspected changed actual source scenes, the useful Mueller name overlay and movement/camera wall landmarks. Distinct post-dismiss kernel W/relative pulses remain bound to the same game process; changes are not inferred from weapon idle or full-frame hashes alone.

No concrete raw-game blocker was established in this bounded review. A supplementary source-to-prepared cross-check was requested from the native owner: host PNG re-encoding gives different encoded hashes from native observations, consistent with the already recorded Qt encoder variation. Target prepared bytes or decoded RGBA/Transform digests can resolve that comparison without treating platform encoding as a product defect. Candidate route evidence supports the strict two-route result; changed-path20 support, this supplementary comparison and final cleanup/aggregate remain separately pending. No VM/source/index operation occurred; only this report was edited.

**Prepared-source comparison resolved:** Verified saved native prepared PNGs against their recorded SHA and actual per-pass input SHA for both game routes. Decoded native RGBA pixels and Transform also match independent host preparation of each exact source/point. The initial encoded difference came from PNG metadata/GUI encoder context, not changed pixels. No additional query or reviewer VM operation was used.

### Unit 09 Changed-path20 and Physical Burst Raw Review

Recomputed the declared **non-game** sparse-source support report:20/20 useful physical completions, all20 with actual6→11 and identical input bytes across each pair. Every source SHA equals the frozen9cbc source; source PID/run/request, actual returned Selection and all20 saved useful-frame hashes match. This is changed-path resource support, not extra game-route credit. Earlier game all6 support and failed initial fixture/privacy attempts remain unaccepted history.

Independently recomputed RSS first5 median **185286656**, last5 **185356288**, allowance **27792998.4bytes**; raw VmRSS values agree. No recursive children are recorded across20 samples/cooldown; threads9/FD22 remain stable after the first completion. Cooldown is **5327.6185ms**, history delta20 and integrityOK. Existing fallback resource oracle passes. Physical burst independently recomputes **10 inputs/1 accepted**; kernel intervals are **39.977–67.338ms**, final saved PNG hash matches and latest-result/history/recovery oracle passes.

Resource/burst evidence has no demonstrated blocker in this bounded review. Privacy remains a supplementary evidence check: top-level typed Klipper observations retain15items and matching content hashes, but wl-paste exits1 before/after still need retained classification as absent selection rather than read failure. Invalid nested resource-snapshot clipboard reads are not used as privacy proof. Top-level scan covers hardening09 data, while resource snapshots scan the actual AssaultCube profile data; both must be represented in final file-retention claims. Parent/source owner notified. Final cleanup/aggregate remain pending; no VM/source/index operation occurred.

### Unit 09 Classified Privacy Supplement and Cleanup Verification Gap

Independently checked `08-09-privacy-proof.json`: both PRIMARY/CLIPBOARD baselines and post-readbacks record exit1, empty stdout hash, exact stderr `Nothing is copied\n` and an existing Wayland socket. Typed Klipper content hash and15items match; both hardening09 and actual AssaultCube data scans show no PNG files. The intervening physical request matches its source PID/run/request and actual6→11 same-input observations; measured latency3778.160677ms. This bounded fresh privacy proof is accepted. It does **not** retrospectively classify the earlier20 missing-stderr reads or invalid nested resource probes.

Final09 cleanup remains honestly **11/12**, `passed=false`: `unrelated_shortcuts_preserved=false`. Read `08-09-prepare-cleanup.py`, the product-key-clear receipt, production ShortcutRegistry scope and saved cleanup/retention artifacts. The helper compares parsed dictionaries for every shortcut-config section except exact `org.lookup.Linux.desktop`; it retains only the boolean, not either snapshot or differing keys. Production replacement targets only exact product component/action and verifies its key readback. Available evidence cannot distinguish changed unrelated key assignments from metadata/background writes or comparison read issues. The12 retained profile paths do not include the shortcut configuration. No actual unrelated mutation or benign comparison cause can be asserted from this discarded evidence.

Required resolution path: preserve this historical false result; inspect an existing owned-clone KConfig backup/full baseline if available and compare actual nonproduct action assignments. Otherwise obtain a new bounded scoped exact-key-clear proof with complete before/after raw file bytes, typed unrelated bindings, retained read failures/diffs and the physical known-unrelated shortcut check. A new successful observation can support its own scoped cleanup; it cannot retroactively establish that the discarded old snapshots were equal. User-authorized subsequent GUI boot/install is separate from the completed OFF cleanup, and original VM USER_KEEP_RUNNING isolation remains mandatory. Parent/source owner notified; no VM/source/index operation occurred.

### New Post-manual 07 Registry Proof Review

Independently decoded/hashed both full KConfig snapshots in `08-07-registry-clear-product.json` and recomputed their textual diff: **only `[services][org.lookup.Linux.desktop]` `_launch=Meta+Shift+E` changes to `none`**. All **281 other typed action bindings** compare exactly equal. This new observation demonstrates the nested product-owned section missed by09's flat-section exclusion; old09 false remains unchanged and its discarded snapshots are not reconstructed by assumption.

Before/after known-unrelated fixture receipts use the same free Meta+Ctrl+Shift+F11 binding and guarded clone input, producing distinct fresh marker PID1395/1425, UID1001 and proc starts bounded by guest snapshot times. Input transport success and actual guest execution are retained; these marker artifacts do not contain separate evdev timestamps, so no kernel-clock latency proof is inferred. Initial CtrlAltF11 VT failure/fixture-only retarget remain history. New post-manual baseline records16words/1card, integrityOK and a SQLite backup that includes live WAL content. No pre-manual restoration is accepted.

New scoped registry proof is accepted. Lifetime review found CR-14 below before final cleanup; final broader07 acceptance remains pending. No VM/source/index operation occurred.

### CR-14: Final controller readback failure aborts remaining cleanup

**Classification:** BLOCKER
**Disposition:** RESOLVED in `e2a5893`; original issue and intervening residual evidence retained. Live controller7552's initial source remains separately identified.
**File:** `.planning/phases/08-vm/08-07-controller.py:47–58`, cleanup polling/final readbacks.

**Issue:** Release/guest/shutdown actions use independent attempt handling, but subsequent `info(clone)` polling and final clone/original readbacks are unprotected. A transient host readback failure exits the finally block, skipping later bounded polling, safe OFF-only restoration and final observation/controller-state persistence. This reintroduces an incomplete failure-cleanup path.

**Executed reproduction:** Compile/exercise only the saved finally AST with mocked adapter/attempt/time/info/save, no VM/file writes. Make its first poll raise `RuntimeError('transient_showvminfo')`. Executed steps are release, mouse release, guest cleanup, shutdown, poll; the exception escapes and neither restoration nor final persistence runs.

**Fix:** Record/readback failures independently, continue bounded polling after transient errors, and attempt remaining safe steps/readbacks/persistence regardless of prior errors. Require a successful current OFF observation before settings restoration; unknown state must stay false. Add the transient-poll regression. Live7552 does not inherit later source changes; retain its actual source/receipts and execute any corrected cleanup explicitly rather than claiming hot reload. No VM/source/index operation occurred; only this report was edited.

**CR-14 recheck at `d915ffb` — VM readbacks fixed, residual OPEN:** VM polling/final readbacks now use independent attempts; poll keys are unique so earlier errors persist. Fresh targeted transient-readback regression passes. However, cleanup source loading (`cleanup.read_text()`/hash) remains outside an attempt, and the attempt helper's per-step `save()` remains outside its catch. Either host I/O error still aborts later safe cleanup. Executed actual-finally AST with an existing cleanup path whose read raises PermissionError: only release/mouse_release execute, then shutdown/restoration are skipped. Make source loading part of guarded guest-cleanup work and per-step reporting best effort while retaining reporting failures; final evidence failures must remain explicit. Parent/source owner notified. Live old7552 source is retained separately, with no hot-reload claim. No VM/source/index operation occurred.

**CR-14 final disposition at `e2a5893` — RESOLVED:** Cleanup source read/hash now occurs inside the protected guest-cleanup operation. Per-step persistence failures are retained and reported to stderr while remaining safe actions continue; final evidence failure returns nonzero after cleanup attempts and is not labeled ordinary finished success. Poll/final readbacks remain independent with unique retained failed-poll entries, and restoration requires an actual current clone OFF observation.

Fresh reviewer targeted execution of the actual finally AST regressions: **3 tests passed**,0.011seconds, covering transient host readback, cleanup-source read failure and repeated report-write failure. Later shutdown, safe restoration and final readbacks/persistence attempts remain reachable. No additional concrete defect was established in this bounded recheck. Parent/source owner received code clearance; live7552 initial source/actual execution is not retroactively changed by this source fix. Final observed cleanup or explicit corrected recovery still needs review. No VM/source/index operation occurred; only this report was edited.

### CR-15: Current privacy acceptance does not correlate its raw observations

**Classification:** BLOCKER
**Disposition:** RESOLVED in `d16c387`; original issue/reproduction retained. Fresh68 focused tests passed,9.243seconds.
**File:** `tools/check_hardening.py:514–535`, `current_privacy_report()`.

**Issue:** The validator accepts a physical timing record and a separate6→11 source list without requiring matching PID/run/request, source capture/pass timing bounds or identical prepared input. Classified clipboard results are also not tied to their preserved typed-channel observations or compared as classified before/after values. A purported valid no-selection classification can therefore describe different content/request than the hash being declared unchanged.

**Executed reproduction:** Load actual `08-09-privacy-proof.json`; change source PID/run/request to999/111/222, second-pass input SHA to `'a'*64` and classified PRIMARY stdout SHA to `'b'*64`. `current_privacy_report()` still returns **passed=true**. No artifact was modified on disk.

**Fix:** Bind source identity/capture/pass intervals and same prepared bytes to the physical request; validate original returned selection/source semantics. Compare both classified channel observations across before/after and correlate exit/content with typed hashes. Absent-selection exit1 must require the actual empty stdout hash plus exact absence classification, rather than any SHA. Add raw mismatched-request/input/content regressions and keep read failures distinct from unchanged clipboard content.

### CR-16: Closure suites can name any shared revision rather than current final code

**Classification:** BLOCKER
**Disposition:** RESOLVED in `23cdaf5`; original issue and residual reproduction retained.
**File:** `tools/check_hardening.py:489–511` and current branch of `aggregate_report()`; `tools/check_hardening_install.py` current suite/gate assembly.

**Issue:** Host/target suite metadata must agree with each other, but neither their revision nor tree is checked against an independently obtained final repository identity. Review/verifier headers are subsequently compared only to that supplied suite revision. Thus internally consistent old suite/gate artifacts can satisfy new closure code without testing its final revision.

**Executed reproduction:** Supply actual-format successful12-test log bytes and matching digest for both suite roles with revision `'a'*40`, tree `'b'*40`, required command/target opt-ins. `closure_suites_report()` returns **passed=true** and those arbitrary identities. The current assembler/aggregate provides no additional current-repository identity check.

**Fix:** Obtain the expected tested final revision/tree independently in the assembler and require both suite roles and final gate headers to match it. Preserve explicit code-freeze/artifact-only commit semantics so source/test changes after the claimed suite run invalidate closure. Add both-roles-same-but-old revision/tree regressions; comparing only host to target is insufficient.

Fresh focused closure command: **66 tests passed**,7.579seconds. Existing cases do not cover these two false acceptances. Review is bounded to the four submitted closure files and their actual called evidence seams; no VM/source/index operation occurred. Final frontmatter completion and fresh final full-suite/native cleanup review remain pending.

### Final 07 Isolated Suite Runner Code Review

Read the native transport/controller/target-start/suite-runner/collector helpers committed in `0070781`, alongside the already reviewed post-manual baseline and exact registry/marker proof. No concrete new blocker was established in these runner paths. Full-history Git bundle transfer retains the old-OCR adversarial regression dependency and checks the requested detached revision. Target discovery uses unprivileged arch UID1000, env-i private HOME/XDG/LOOKUP directories,0700runtime, private dbus-run-session, forced offscreen, no inherited DISPLAY/Wayland/Xauthority/manual-session bus, NoNewPrivs and an unavailable system-bus address. Mueller files are rehashed against the actual pinned package inventory before launch and again by the runner.

The literal full discovery command runs once; the runner retains actual revision/tree, raw stdout/stderr log digest, return code/count/skips and opt-ins. Host/target collectors load those actual receipt/log bytes. New namespace and post-manual logical SQLite backup preserve the current16words/1card baseline; isolated discovery does not restore09 data or operate the normal lookup07 session. Live7552's initial controller source remains separately identified; corrected source is not assumed loaded retroactively.

Fresh AST parsing of six transport/lifetime/runner/collector/guest-cleanup helpers passed without native execution. Parent/native owner received runner-code clearance. This does not resolve CORE CR-15/CR-16, accept unexecuted full suites, or accept pending final cleanup. No VM/source/index operation occurred; only this report was edited.

**CR-15/CR-16 recheck at `d16c387`:** Original privacy identity/shared-input/classified-content mutations and arbitrary suite revision/tree now reject. Privacy additionally requires actual matching source/frame bytes and numeric request trace. Targeted regressions passed. One CR-16 residual remains: independently reproduced a tracked root `PKGBUILD` modification after the tested commit in an isolated Git repository; suite validation still returns passed=true because its path scope omits root `PKGBUILD`. Include that actual package build input in both tracked/untracked code anchoring and add the regression before final source freeze. Parent/integrator notified; no VM/source/index operation occurred.

**CR-16 final recheck at `23cdaf5` — RESOLVED:** Root PKGBUILD now participates in tracked/untracked Git code anchoring. Fresh isolated actual-Git regression passes,1.003seconds, including fake revision/tree, changed tracked code/root recipe, untracked/native code and metadata-only commit behavior. No further concrete residual was established; parent received CORE code clearance. Final full-suite execution remains separate.

### Actual Old7552 Lifetime Completion Review

Independently recomputed current cleanup from saved controller observations, post-manual baseline and full registry/marker proof: passed. Executed guest-cleanup source digest matches; all five nested cleanup operations succeeded, no owned processes remain, package removal exited0 and package absence was observed. Config/dictionaries remain intact; actual logical SQLite SHA equals post-manual backup `8e6fd07438e1d196cd395c11bdaf67db4197d4066a3effca4edabc82eb5cc2b7` for the16words/1card baseline. Final fixture-free typed registry preserves all baseline unrelated bindings; synthetic fixture is unregistered.

Actual final clone readback is OFF/3Don/BIDI with successful restoration exit0. Shutdown SSH disconnect remains an explicit false transport receipt, independently resolved by later actual OFF observation. All recorded host mutations target the clone. Original host state changes OFF-to-running externally; USER_KEEP_RUNNING permits that and no state-equality claim is made. This accepts actual normal completion of the retained OLD started7552 source, not retroactive loading of the CR-14 fix. A subsequent target-only lifetime still requires its own final readbacks. No VM/source/index operation occurred; only this report was edited.

### Final Target-only Native Delta Review at `2dbd48c`

No concrete new blocker was established in the target-only delta. Private Mueller extraction reads only regular members from the actual hash-verified798package, rejects duplicate/unsafe basenames, writes0400 dictionary files and rehashes the complete extracted inventory. Product remains uninstalled. The target controller is independently confirmed **exactly equal to the reviewed corrected CR-14 controller with scoped filename substitutions**. Fresh cleanup-dependency mocks: **3 tests passed**,0.018seconds, including the target controller's source/report failure continuation.

Target guest cleanup scopes process termination to arch UID1000 and exact HOME values under the owned private suite roots; it performs no broad deletion or pre-manual profile restoration. It checks current post-manual config/dictionary and logical SQLite backup retention, package absence and normal-product process absence. Parent/native owner received code clearance before the single final fullHOST-to-TARGET run. Actual same-revision logs and latest target cleanup remain pending; this is not final phase acceptance. No VM/source/index operation occurred; only this report was edited.

### WR-03: Fixed Qt wait races an overdue timeout dispatch

**Classification:** WARNING
**Disposition:** RESOLVED in `fe021bd`; test reliability issue, no production defect established.
**File:** `tests/test_app_gui.py:294–296`, `test_escape_timeout_and_programmatic_hide_have_distinct_effect`.

Actual final target discovery ran795tests and failed only this popup-hidden assertion after starting a20ms timer and waiting a fixed40ms. The test uses focus=False, so delayed useful-frame exposure/focus staging does not explain this path.

**Executed host reproduction:** Immediately before the existing40ms wait, schedule a pending Qt callback that blocks80ms. The unchanged test fails at the exact target assertion: popup remains visible because qWait consumes its budget within another callback and returns before dispatching the now-overdue timeout. Repeat with the same delayed callback plus one further `application.processEvents()` dispatch: the unchanged timer/product test passes. No source or timer setting was changed.

**Fix:** Replace the fixed sleep with a bounded event-pump predicate wait for hidden popup and invalidated generation, optionally retaining a timeout signal observation. Keep20ms timer and separate programmatic-hide/current-generation and Escape assertions; do not change product timeout or waive the failed discovery. Preserve the failed target log and rerun final same-revision suites after the test-only correction. No VM/source/index operation occurred; only this report was edited.

**WR-03 final recheck at `fe021bd` — RESOLVED:** Bounded predicate pumps events until both hidden popup and invalidated generation, retaining all final assertions and the unchanged20ms timer. Deterministic queued80ms work now passes without product modification. Fresh reviewer GUI/concurrency command: **36 tests passed**,6.202seconds. The accompanying cleanup callback defaults retain spawn Barrier/Queue references until every child joins, preventing premature synchronization-handle disposal without changing deadlines/count/integrity. No stderr filtering is introduced. CRLF log-count/skips parsing remains based on actual transcripts, and remote POSIX paths no longer acquire Windows separators.

No concrete remaining defect was established in these four test/harness changes. Parent/native owner received code clearance. The original failed795-target discovery and noisy earlier attempts remain retained; new same-revision full suites/latest target cleanup still require actual evidence. No VM/source/index operation occurred; only this report was edited.
