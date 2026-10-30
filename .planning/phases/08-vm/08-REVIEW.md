---
phase: 08-vm
reviewed: 2026-10-30
depth: standard
review_scope: full_phase_units_01_through_05
diff_base: 1b54572
review_head: a10c5e1
initial_source_snapshot: e7fb3d6
finding_recheck_head: 3114db8
incremental_production_head: 4ace8e9
incremental_harness_head: 9a2ec88
incremental_harness_recheck_head: a3c887f
phase_review_complete: true
code_review: passed
security_review: passed
phase_acceptance: gaps_found
mandatory_gap: GAME-01-captured-useful-route
files_reviewed: 12
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
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
resolved_findings: 11
status: clean
scope_result: clean
---

# Phase 8: Final Code and Security Review

## Final Assessment

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
