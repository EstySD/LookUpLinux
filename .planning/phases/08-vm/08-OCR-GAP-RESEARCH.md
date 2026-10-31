# Phase 8 OCR gap: evidence-backed bounded sparse-text retry

**Researched:** 2026-10-31. **Disposition:** Ready for checked gap planning; production change and native acceptance have not occurred. **Confidence:** HIGH for frozen-source comparison/current contracts; native corrected routes/performance remain execution gates.

## User Constraints

[VERIFIED: parent task, 08-CONTEXT.md, 08-VERIFICATION.md and canonical docs/lookupper architecture/linux-requirements/evidence] Keep actual GAME-01 criteria: unchanged current screenshot, actual production OCR/Query, useful overlay while same game process captures relative mouse, dismissal and subsequent genuine camera/movement. Do not lower confidence50, replace images/words/queries, waive the second game or use an observer result as product success. Game/font experimentation budget is spent; no new candidate or random config. Preserve the Phase7 strict-false/original-disk exception. Research owns only this new file; no VM access, source/tools/config edits or new game query was performed.

## Latest Failure Classification

[VERIFIED: 08-06-recovery-frozen-diagnostic.json, supplied by sole VM/source owner exec_context_02] Latest actual recovery route2 failed at production stage6. That trace alone contains no precise timeout reason. Exact frozen replay establishes a segmentation/no-selection failure: PSM6 completes successfully but returns no accepted selected word; PSM11 on identical prepared pixels selects `name` at confidence89.277435. Do not label the live failure a proven timeout, transport failure or observer failure.

```text
Actual Screenshot2 source SHA256:
9cbc077f181e3c564d21e5d3ec88d68129630811972b12cc659558fc8723497e
Cursor: (733,378)
Prepared SHA256, equal for PSM6 and11:
44a19eeceee75ffacee6071b15e38c1c4773dc8dff5189d8be50c1a723c8a443
PSM6: selection=None; prepare828.352ms, OCR2187.746ms,
      select4.862ms, total3020.960ms.
PSM11: name89.277435; box(716.5,374,34,8.5), context=name;
       prepare463.205ms, OCR1188.931ms, select10.885ms,
       total1663.022ms.
```

[VERIFIED: takeover-default-ocr-diagnostic and takeover-supported-psm11-ocr-diagnostic JSONs] Three earlier immutable default-font comparisons independently support the same general retry: successful `name`90.066467 becomes `name`88.848824 under11; failed `name`7.781235 becomes86.152245; failed `deaths`31.606735 becomes91.451462. Prepared SHA matches within each pair. These frozen comparisons prove feasibility, not a new native useful route. Latest source uses the already selected ordinary mono game setting; no further font experiment is needed.

## Smallest Correct Production Contract

[VERIFIED: lookup/ocr.py:recognize_image, parse_tsv, select_word] The API already supports PSM6 and11, one bounded image preparation and strict TSV parsing with existing coordinate Transform. Default6 is one Tesseract subprocess; timeout is3s per current call. Selection enforces confidence50, lexical validity, bounded proximity and context/occurrence recovery. App.Source.resolve maps a final selectionNone to `not_found`.

**Recommendation:** add one bounded6→11 retry inside the shared recognition implementation. Prepare once. Run PSM6 first and return its exact successful Selection unchanged. Only after a successful process, valid bounded TSV and `select_word(...)=None`, run PSM11 once on the **same prepared PNG bytes and Transform**, then use existing strict parse/selection/context logic. No merging unrelated words across segmentation passes. If second pass has no selection, return None. Existing failures (missing executable/eng, timeout, process failure, malformed TSV, invalid image/point) retain their reason and do not trigger a retry. Explicit PSM11 is always one pass. [Selected design grounded in verified comparison]

Use a small explicit keyword such as `fallback=True` on recognize_image. Existing production calls then receive the cascade without modifying capture/Query. `fallback=False` keeps standalone experiments and process-boundary tests deterministic. Preserve existing invalid-argument behavior; if exposing the flag validate boolean input. No global default-PSM switch, game-specific word rules, dependencies, registry or per-game configuration. [VERIFIED: current callers; selected interface]

**Calibration compatibility:** tools/calibrate_ocr.py currently calls recognize_image(...,psm=6/11) and labels results as independent PSM settings. Pass `fallback=False` there; otherwise the “PSM6” trial silently becomes a cascade and invalidates comparison meaning. Production-oriented context-image corpus should use the default cascade, with separate direct6/11 diagnostics only where explicitly intended. Existing tests mocking recognise_image may need proportional keyword adjustments. [VERIFIED: calibration evaluate and image test modules]

### Budget that can actually execute the demonstrated remedy

Do **not** impose a new shared3s OCR deadline. On the latest exact source,6 subprocess2187.746ms leaves812.254ms, while11 subprocess alone needs1188.931ms: that proposed cap would defeat the demonstrated retry. The1663ms standalone11 total includes its own463ms preparation and must not be mislabeled subprocess time. [VERIFIED: latest frozen timing]

**Selected bounded budget:** at most two processes, each with current OCR_TIMEOUT3s; one absolute recognition-process deadline at first subprocess start +2*OCR_TIMEOUT. Each subprocess timeout is min(OCR_TIMEOUT, positive remaining deadline). If no positive budget remains, raise existing timeout without launching. Prepare only once and account its time separately. This explicitly expands the no-selection path's subprocess bound to6s; it is not an unchanged3s or1.5s promise. Both parses/preparation still have existing byte/row/pixel bounds. No retry after first process times out. [Selected design]

With recorded durations and reused preparation, arithmetic suggests ~4221ms recognition for the latest frame, before dispatch/capture/GUI; this is **an estimate**, not observed cascade latency. Actual source capture itself lasted~1800ms in that sample. An unchanged source-based success does not automatically satisfy performance. Keep the1.5s median criterion and remeasure instead of subtracting retry or capture cost. [VERIFIED: frozen source timestamps; explicitly inferred estimate]

### Cancellation, reload, quit and stale protection

[VERIFIED: lookup/app.py:Engine._process, Source.resolve; gui.py:quit/poll_quit] Capture/recognition runs on the worker, not GUI. After source.resolve returns, Engine checks current identity before dictionary/network/history work. New trigger, dismissal, reload and stop invalidate generations. GUI quit polls25ms until worker/focus/settings work finish; no global3s deadline currently cancels OCR.

Preserve those boundaries; do not create another Engine/reset identities or a SQLite-writing retry thread. The smallest change does not need a new cancellation callback threaded through every Source mock/API. A superseded worker may finish its bounded retry, but must never emit current UI/save/enrich afterward; next queued request can wait longer, and quit can wait for up to the new bound plus already-bounded stages. If prompt intra-pass cancellation becomes a requirement, design it separately rather than pretending generation invalidation kills Tesseract. Tests must hold the second pass and exercise new trigger/dismiss/reload/quit; GUI remains responsive and stale work cannot persist. [Selected design grounded in current behavior]

### Timing semantics

Keep current timing keys and sum all actual work: prepare_image once, ocr across both process executions, select across parse/selection attempts, total across the full recognition. Avoid assigning selection time to OCR by subtracting only one global timestamp. A fallback diagnostic can inspect actual subprocess modes/counts without introducing private text telemetry or changing numeric timing allowlists unnecessarily. Successful6 must keep one process/no extra prepare and equivalent result semantics. [VERIFIED: current Recognition.timings/app merge; selected accounting]

## Validation Architecture

**Framework:** existing stdlib unittest. Focused commands: `python -m unittest tests.test_ocr tests.test_ocr_image tests.test_ocr_cli tests.test_app tests.test_privacy tests.test_timing`; include new fallback module if split. Full fresh host and target discovery follows the final closure revision, with real target OCR and system Mueller enabled per existing harness. No fixed count or inherited pass is promised. [VERIFIED: tests and prior verifier freshness warning]

Required behavioral regressions:

- Good default6 returns original selected word/context/span and launches exactly one subprocess; explicit11/direct fallbackFalse remains one. Preparation is once and identical input bytes/Transform are supplied to retry.
- Valid6 no-selection then valid11 gives selected word at the actual cursor; both None stays None. The current minconf50, nearest-word limit, invalid-hit/no-neighbor-jump rules and context separation remain intact.
- Missing eng/tool, timeout, nonzero process, malformed/oversized TSV and invalid image/point retain current errors without retry. Second-process failure is bounded and explicit, no partial guessed success.
- Absolute retry deadline and per-process caps tested with controlled monotonic clock; elapsed first6≈2188ms must leave enough allowance for the demonstrated≈1189ms second pass. Reject exhausted deadline and never launch a third process.
- Real-source regression corpus: all four immutable source/point pairs above; verify file SHA, expected selected word/box/span and unchanged prepared SHA per pair. Add actual sparse-background negatives/points outside text and low-confidence/noise cases to avoid promoting nearby junk. Do not merely mock a successful Selection as the image regression.
- Existing actual-image Breeze16-render96-point corpus,144 multiline-context scenes, scaling/negative-origin, phrase/hyphen/speaker/column exclusions and noise/blank/distant cases must be rerun with production defaults. PSM11 can segment lines/blocks differently; do not assume context behavior stays correct simply because one word passes.
- Hold fallback while accepting/dismissing/reloading/stopping: no stale Query/result repaint, count write or contextual enrichment. Preserve one-event persistence/card snapshot contracts.

[VERIFIED: current game tooling] Update readonly diagnostic/evidence extraction if it independently reruns raw PSM6 and assumes those words always equal the cascade's selected result. It must faithfully identify actual selected production box/span from the successful pass; never substitute a separately forced PSM11 result into Source or acceptance. Native capture/Query observation still observes the real function's returned object unchanged.

## Evidence Refresh / Safe Reuse Map

| Existing evidence | Disposition after OCR production change |
| --- | --- |
| Earlier failed Doom/AssaultCube attempts, stage6 and frozen diagnostics | Preserve historical failures unchanged. They are repro sources, not new successes. |
| Existing successful default6 corpus/performance records | Preserve historically; not proof of current binary behavior even if fast path is designed unchanged. |
| PERF-01 thirty physical samples | **Remeasure affected30** on newly staged/installed corrected production, same3cold/18distinct/9repeat workload, kernel-clock→actual useful frame, median/p95/rejections and stage identity. Include fallback games separately; no relaxed1.5s claim. |
| GAME-01 | At least two current corrected-production captured routes with distinct fresh frames, actual lock/Query/box/span/useful overlay/dismiss/camera+movement and exact PID/start/run/request/input identity. Frozen replay alone cannot close it. Retain existing Wesnoth as historical first-game proof; refresh its installed-source identity or rerun relevant routes if source binding requires same product revision. |
| Native320-completion resource/privacy/fault checks | No claim that this implementation automatically invalidates all unchanged subsystems. If workload remains all single-pass6, existing evidence can remain narrowly scoped historical support, with fresh bounded fallback burst/resource/cancel/privacy/child-cleanup checks. If fallback is exercised in that workload or changes leak/orphan/latency behavior, rerun affected sustained/burst run. Independent verifier decides adequacy; never relabel old320 as new. |
| Clean install/login/removal | Packaging/autostart source unchanged: retain scoped evidence. Refresh staged archive/package/executable hashes, actual installed OCR module and source receipts, installed smoke/doctor and removal/cleanup for this package; rerun complete lifecycle if installer/package code changed. |
| Four-scale/negative-origin/clipboard invariants | Reuse unchanged implementation rationale, rerun complete target OCR/context corpus and focused geometry/privacy tests; current fallback native source/box/privacy checks cover the affected path. New false positives or transform issues require actual affected scale rerun. |
| Full suites/review/verification | Fresh full host+target at final recorded revision, independent code review and re-verification. Old host752/target751 freshness issue cannot be resolved by renaming a log. Current actual counts must be measured. |

## Security and Remaining Limits

[VERIFIED: current privacy/import contracts] Retry stays stdlib/lazy Qt, one in-memory prepared PNG and bounded TSV; no screenshots/network/cache writes, no private OCR text in timing/errors, no confidence/proximity weakening. At most one live Tesseract child at a time, cleaned up by subprocess.run on timeout. Existing output-byte handling should not be broadened in this task.

**What is established:** identical actual frozen source becomes correctly selectable under supported11 while6 returns None; current default path has no retry. **What remains unproven:** successful integrated cascade on that source, exact native latency and two accepted current captured routes. The latest failure's precise live exception was not logged; frozen replay supports segmentation cause without proving every live stage6 is that cause. No native acceptance or production fix is claimed by this document.

Primary documentation: https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html (page-segmentation/TSV interface). Project evidence: `08-06-recovery-frozen-diagnostic.json`, `08-06-takeover-default-ocr-diagnostic.json`, `08-06-takeover-supported-psm11-ocr-diagnostic.json`; current `lookup/ocr.py`, `lookup/app.py`, `lookup/gui.py`, tests and calibration callers. [CITED / VERIFIED: read this session]
