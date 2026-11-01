---
phase: 08-vm
verified: 2026-11-01T16:35:21Z
metadata_rechecked: 2026-11-01T16:42:17Z
verified_revision: fe021bdf68607d5b8026eb1d1494e945862618cd
verified_tree: 728957780ced4c36bcd2f64c9f96da345c6f134f
status: passed
score: 7/7 roadmap must-haves verified
overrides_applied: 0
acceptance: independent agent verification, no human acceptance
requirements_verified: [PERF-01, GAME-01]
requirements_blocked: []
re_verification:
  previous_status: gaps_found
  previous_score: 6/7
  gaps_closed:
    - Useful second fullscreen captured-game routes, selected production OCR and post-dismiss gameplay
    - Fresh same-code host and target full suites after closure changes
    - Source-bound current performance and affected OCR fallback validation
    - Current post-manual shortcut preservation and latest target cleanup observations
  gaps_remaining: []
  regressions: []
---

# Phase 8: Hardening and VM Verification

**Goal:** The VM application meets the declared first-useful latency, resource, scaling, privacy, fault and installation contracts, and completes real useful OCR overlay routes in two fullscreen games, including captured mouse and returned gameplay control.

**Status: passed — 7/7 roadmap truths independently verified.** This re-verification checks actual implementation and retained raw observations. SUMMARY claims were used to locate evidence, not to establish success. No Phase8 requirement is waived. The old Doom and incomplete06 attempts remain failures; approved gap plans supply current AssaultCube evidence instead. This is agent acceptance under the user's explicit automatic-workflow instruction, not a human test report.

## Observable Truths

| # | Roadmap contract | Status | Independently checked evidence |
|---|---|---|---|
| 1 | About30 physical requests, first useful median <=1500ms, recorded p95 and stages | VERIFIED | Current installed corrected package:30/30, exact3 cold/18 distinct/9 repeat workload. Direct kernel-input to actual useful-frame-END arithmetic gives median **1088.2457725ms**, nearest-rank p95 **1431.759096ms**. All30 frame PNG hashes, PID/start/run/request identities and verified kernel clocks match. Cold subgroup p95 **1916.468943ms** is retained; no subgroup threshold or dispatch subtraction is invented. |
| 2 | Correct word/cursor/popup at100/125/150/200%, with pure geometry and negative origins | VERIFIED | Historical four-scale native oracle recomputes true. Geometry/placement production code is unchanged by the OCR retry; current target discovery includes actual OCR/geometry coverage. The16-render/96-point production-default corpus and144 multiline scenes passed; four immutable game-source comparisons preserve transforms and native prepared-input hashes. The one-output environment leaves a second monitor explicitly unverified. |
| 3 | No retained capture PNGs or clipboard/history changes; bounded recoverable faults | VERIFIED | Historical real network/dictionary faults and explicitly injected active ScreenShot2 seam recompute true. Current changed-path privacy has an actual physical6-to11 request bound to saved source/useful PNGs and numeric trace. Both valid empty PRIMARY/CLIPBOARD observations have a present Wayland socket, exit1, exact `Nothing is copied` stderr and matching empty-channel hashes; typed15-item Klipper digest is unchanged. Both actual game-data and temporary/runtime file scans contain no unexpected PNG. Earlier unclassified read errors are not counted as proof. |
| 4 | Several hundred completions, bounded memory, ten-key burst and no corrupt history/orphans | VERIFIED | Historical20 warmups+320 actual completions recompute true: early/late median RSS174657536/174698496 bytes, late trend8192 bytes, no recursive children. Current changed path separately completes20/20 physical calls, **all20 actual6-to11**, same prepared bytes, one owner, history+20/integrityok. RSS medians185286656/185356288 bytes, stable9 threads/22 FDs, no children and5327.6ms cooldown. Current burst validates10 physical inputs, one latest accepted/count increment, integrity and subsequent recovery. |
| 5 | README clean install/login/autostart/removal without hidden setup | VERIFIED | Actual new lookup08install profile baseline, recorded system dependencies, staged makepkg/install, installed helper/Mueller capture, genuine enabled/disabled SDDM login and data/key-preserving removal recompute true. This is a clean application/profile baseline, not a newly provisioned minimal Arch claim. Current corrected archive/package/runtime inventories match all32 current normalized staging members; current installed doctor and offline no-save smoke exited0. Packaging/lifecycle production code did not change. |
| 6 | Two genuine fullscreen English games, repeated useful routes, captured mouse, multiline text and returned control | VERIFIED | The Battle for Wesnoth1.18.8 has two fullscreen multiline tutorial routes with actual movement/combat. Current-source replay of both exact original sources returns the same word/context/span through single-pass6. AssaultCube1.3.0.2 supplies **two current useful routes in the same PID7496/start32039/window4**; actual GL/current-window/grab state and pre-input Wayland locked-pointer events are bound. Actual source/Selection/Query/span and useful Mueller overlay agree. Latencies4303.613319/4081.585538ms; second route genuinely uses6-to11. Both physical Esc actions are followed by separate W and relative-camera world changes; all eight control PNGs and world-region pixel changes independently recompute. A displayed frozen game image is used only for changed-path resources, never as game acceptance. |
| 7 | Useful article timing is separate from contextual meaning latency and success fraction | VERIFIED | Numeric timing wiring separates trigger/queue/useful-ready/present/meaning-ready/error. Six retained live provider-only probes yield0/6 success with blocked reasons; successful meaning median/p95 and end-to-end UI latency remain null. No loading card, provider-only attempt duration or deterministic mock is counted as useful article or successful live enrichment. Current cancellation/nonblocking tests preserve the article-first path. |

## Substantive Artifacts and Wiring

| Artifact | Existence, substance and active connection |
|---|---|
| `lookup/timing.py`, `lookup/__main__.py`, `lookup/gui.py` | Numeric opt-in stage allowlist is called from real CLI/GUI paths. Useful readiness is distinct from compositor capture. Deferred placement keeps useful paint hidden until placement; timeout begins at actual reveal. |
| `lookup/ocr.py` | Default valid PSM6 no-selection prepares once and retries11 once on identical PNG/Transform. Existing selection/confidence/proximity/context rules are reused. Successful6, explicit11 and fallbackFalse remain single-pass; malformed output/process errors/timeouts do not retry. Each child is bounded by3s and one absolute6s process deadline. Preparation/parsing are separately bounded work; no unchanged3s total or1.5s failure-path promise is made. |
| `lookup/app.py` | Real Source.freeze captures Screenshot2; Source.resolve calls the shared recognizer and constructs Query from its returned selection. Engine checks request identity after resolve and before lookup/persistence. Current held-second-pass replace/dismiss/reload/stop and Qt quit tests exercise that path. |
| `tools/check_games.py` | Transparent once-only Source/recognizer/subprocess taps preserve original objects/results/exceptions. Actual returned Selection supplies geometry, context and span. GL/SDL observations, recent same-process lock, fresh useful image, separate camera/movement identities and static-world region checks are substantive rejection gates. |
| `tools/check_hardening.py`, `tools/check_hardening_install.py` | Current source/package archives, complete independent32-member inventory, installed bytes, boot/install epoch, raw proc/stat/status/cmdline and numeric traces bind physical samples. Current privacy binds raw request/images/passes/classification. Suites bind real logs and Git commit/tree/current tracked and untracked code, including root PKGBUILD. Final independent gates require hashed final frontmatter at the tested revision. |
| Regression fixtures and target runner | Four original game images retain exact source hashes. Target executes a full detached Git history at the same tested commit, real OCR and verified private read-only Mueller, isolated UID1000 HOME/XDG/LOOKUP/runtime/private D-Bus/offscreen/NoNewPrivs. It does not borrow the normal lookup07 session or database. |

The data flow is actual physical input -> original current capture -> original recognition -> selected occurrence/Query -> real dictionary article -> matching visible frame -> dismissal -> observed game-world input response. No empty/static result or observer-only forced11 value substitutes for that route.

## Independent Behavioral and Raw Checks

- Fresh read-only `current_evidence(...)`: all six current subreports and primary post-manual cleanup pass;80 referenced raw sources were consumed by the source-bound loader. Independent `closure_suites_report(...)` accepts the actual797/797 logs and Git anchor.
- `python -m unittest tests.test_ocr_fallback tests.test_check_games tests.test_hardening_cleanup_controller`: **34 tests OK, zero skips,0.309s** in this verification turn. This is a focused host check, not a new full Linux run.
- Independently recomputed all30 physical latency values and global median/p95; matched all30 useful PNG hashes and full frame identities. Both actual suite log SHA256 values match and neither current log contains `Traceback`.
- Captured-game and Wesnoth oracles pass on actual raw reports. Rehashed both AssaultCube sources/overlays and all eight movement/camera images. Recomputed world-region changed-pixel counts **137602/137685** and **137191/136696**. Viewed the second actual game scene and its readable useful Mueller overlay.
- Negative spot checks reject a mixed game PID, a forced-diagnostic selection origin, detached privacy request identity, differing retry input, clipboard read-error substitution and forged shared suite revision/tree.
- Recomputed prior320, scales, privacy, faults, clean-install and meaning oracles. Git comparison from prior production5d04a4c to testedfe021 changes **only `lookup/ocr.py`** in production/package scope. Current fast-path compatibility, full OCR/context corpus and affected30/fallback20/burst/lifecycle checks support the explicit proportional reuse; old320/scales/login evidence is not relabeled as a newly rerun workload.
- Actual144-case context report records144 passed/0 failed. Target final106 lifecycle/observer receipt is exit0 with actual file hashes. Current full target discovery is797/0 and exercises real OCR/dictionary tests that the host skips.

## Same-Code Full Regression Evidence

| Role | Actual command | Tests | Skips | Exit | Tested code |
|---|---|---:|---:|---:|---|
| Windows host | `python -m unittest discover -s tests` | 797 | 11 | 0 | `fe021bdf68607d5b8026eb1d1494e945862618cd` |
| Isolated Arch target | `python -m unittest discover -s tests` | 797 | 0 | 0 | `fe021bdf68607d5b8026eb1d1494e945862618cd` |

Both tree identities are `728957780ced4c36bcd2f64c9f96da345c6f134f`. Host log SHA256 is `a482fac420a7ff26c01a1ca16886a93189efe9c157ba45af05fea5ae9e238112`; target is `f7f937c611e88125ec56d2c0d133ec84d8d61e2d84985b543637e31acec9fdec`. Target elapsed time is98.566s. Metadata-only later commits do not claim a different tested code revision.

Initial2dbd host795 pass and target795 one-GUI-failure logs remain separate. Deterministic queued work reproduced a fixed-wait test race; the test now pumps until both hidden state and invalidated generation, retaining the20ms product timer and behavior assertions. The test multiprocessing fixture retains Barrier/Queue until child joins, eliminating reproduced startup SemLock errors without filtering stderr or changing deadlines/count/integrity. Final changes are tests/harness only and both full suites were rerun afterward.

## Anti-Patterns and Disconfirmation

No TODO/FIXME/placeholder marker was found in the inspected production OCR/timing/GUI and acceptance tools. Empty/default validator collections fail closed rather than rendering fabricated user results. There is no missing capture-to-recognizer or recognizer-to-Query link.

The disconfirmation pass explicitly checked three plausible false positives: old results relabeled as current code, a separately forced OCR selection substituted for production, and a clipboard read failure mislabeled as absence. Actual code and negative spot checks reject those paths. The former fixed-wait and multiprocessing tests were also checked against their retained failing observations and targeted regressions; successful final logs do not hide or filter their earlier errors.

Optional rendering/output coverage and unavailable live meaning remain limits below. Host-process disappearance cannot be made to execute Python finally code; the actual explicit recovery is verified separately, without promising otherwise.

## Current Cleanup and User Data

The original post-manual lifetime completed actual cleanup with its **old started controller source**. Full raw KConfig changes only nested `[services][org.lookup.Linux.desktop]` `_launch` from Meta+Shift+E to none; all281 other typed bindings match, and a physical unrelated fixture executes fresh UID1001 markers before/after. The synthetic fixture was removed. The old09 missing-snapshot11/12 failure remains false history.

The later target controller disappeared with stale running state and no finally receipt. This is preserved as a failed controller lifetime, not attributed to a known actor or retroactively called clean. Its **explicit recovery** uses the exact reviewed frozen target-controller AST source (normalized SHA256 `1414bb1d46b69d7c4eea1824e80964aa1663075575320f273e38ec77c54ff100`). Independently matched that source to the tested Git blob and recipe's finally extraction. Restoration uses the saved actual pretarget OFF snapshot, not new active settings or reconstructed lost memory.

Latest descriptor SHA matches actual `08-07-target-controller-observations.json`. Independently checked all eight latest observations, released keys/mouse, no private/normal product children, package absent, successful restoration and actual clone **OFF/3DON/BIDIRECTIONAL** readbacks. Post-manual config/dictionaries match; logical SQLite hash `8e6fd07438e1d196cd395c11bdaf67db4197d4066a3effca4edabc82eb5cc2b7` exactly retains the saved **16-word/1-card** backup including manual WAL state, integrityok. SSH shutdown transport disconnects remain separate recorded errors.

All recorded mutating host actions target owned clone `cf207909-94b5-4b49-8bd8-ccff973c1dc8`. The external original VM has only read-only host metadata; its legitimate external state changes do not fail an equality check. This verification made no VM, SSH or input call.

## Requirements, Acceptance and Limits

| Requirement | Coverage | Result |
|---|---|---|
| PERF-01 | Plans01/02/05 plus08/09/07 current-source correction and fresh physical30 | SATISFIED: current median1088.2457725ms <=1500ms, recorded p95 and honest cold results. |
| GAME-01 | Plans03/04/06 exploration followed by approved08/09/07 closure | SATISFIED: actual Wesnoth multiline fullscreen routes with current fast6 compatibility, and two current same-instance AssaultCube captured-mouse useful routes with distinct post-dismiss controls. |

No Phase8 requirement is orphaned. Failed Doom/06 candidate-specific attempts are retained as superseded exploration, not claimed successful or waived into GAME-01. Existing Phase7 strict-false original-preservation report and unknown actor remain unchanged; its narrow prior exception is not applied to this phase.

**No mandatory human-only verification remains unresolved.** Actual visual/game behavior was inspected through retained source, useful-overlay and world-change evidence; no human acceptance is inferred from the user's requested VM clicking or later authorization to resume. Cosmetic preference, optional second output, unavailable borderless modes and friend's hardware are not asserted. Live contextual meanings remain0/6 in this VM, with successful/UI latency null. Compatibility is established for the declared scenes/renderer/settings, not all games. Current retry can extend a no-selection path to the explicit6s process bound.

The independent final review file hash matches `91a95f9eda028666981c05101776d7954b2aa89d4ca92843d2a4d8220e283e45`, with actual final code/security headers at testedfe021. Before this report is bound, aggregate `evidence_passed` and `ready_for_verification` are true while overall `passed`/`game01_complete` intentionally remain false solely because the verifier reference is absent. The parent must bind these actual final report bytes and regenerate acceptance; this verifier does not manufacture its own gate or commit.

## Closure Metadata Recheck

At2026-11-01T16:42:17Z, independently read the updated07 SUMMARY, including its `verified_parent_gates_passed` status, PERF-01/GAME-01 completion entries and parent closure acceptance. Its statement of agent7/7 acceptance, samefe021 test identity and retained failure/cleanup history agrees with the actual evidence.

Fresh read-only checks again confirmed current evidence and cleanup, both797-test log bindings and trusted Git identity, all seven aggregate criteria, and the three actual independent report references. The selected aggregate was fully passed after the parent bound the initial verifier bytes. No source, native observation, suite transcript, threshold or requirement changed; no new override or human acceptance is introduced. This is a substantive recheck of changed closure metadata, not a timestamp-only refresh. The parent must update the verifier reference to the final bytes of this amended report before regenerating acceptance.

---
_Verified: 2026-11-01T16:35:21Z; closure metadata rechecked: 2026-11-01T16:42:17Z._
_Independent verifier: gsd-verifier; agent evidence, no human acceptance._
