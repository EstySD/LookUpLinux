---
phase: 08-vm
verified: 2026-10-30T15:54:03Z
rechecked: 2026-10-30T22:21:41Z
status: gaps_found
score: 6/7 roadmap must-haves verified
overrides_applied: 0
acceptance: agent verification, no human acceptance
requirements_verified: [PERF-01]
requirements_blocked: [GAME-01]
gaps:
  - truth: "SC6 / GAME-01: Two real fullscreen games include a useful fresh-capture OCR lookup while a game has captured mouse, followed by dismissal and resumed gameplay."
    requirement: GAME-01
    status: failed
    root_cause: production_ocr_no_valid_selected_captured_game_word
    reason: "Wesnoth has two valid useful routes, but it is one game. Freedoom/Chocolate Doom has genuine fullscreen/relative-lock/camera evidence and fresh physical captures, but QUIT and HEALTH attempts end at correlated production stage6 without a Query, selected word or useful overlay. Captured-game routes remain empty. Camera/movement observations without a preceding useful overlay cannot prove return-after-useful."
    artifacts:
      - path: lookup/ocr.py
        issue: "Unchanged production preprocessing/selection fails to recognize the actual targeted decorative game word in the retained QUIT and HEALTH sources. Any production correction needs a demonstrated source-based regression and retained existing accuracy/privacy behavior; lowering acceptance or selecting unrelated text is not a fix."
      - path: tools/check_games.py
        issue: "Captured-game observer/oracle exists and correctly rejects zero valid routes. It needs actual successful raw route records, not changed pass flags."
      - path: .planning/phases/08-vm/08-doom-final-report.json
        issue: "Zero accepted routes; real_selected_word, useful_overlay, return_after_useful and repeated_useful_routes are false."
      - path: .planning/phases/08-vm/08-doom-quit-target-failed-source.png
        issue: "Fresh actual source contains the targeted QUIT prompt, but the original production OCR diagnostic yields no valid selected Query at the locked cursor."
      - path: .planning/phases/08-vm/08-doom-health-target-failed-source.png
        issue: "Fresh actual HEALTH HUD source yields no matching token; unrelated ARMOR text is misread at confidence18.9."
    missing:
      - "Diagnose the retained real game sources in a portable OCR/selection regression and, if needed, apply the smallest demonstrated production fix; alternatively navigate to genuinely readable text in actual captured gameplay without replacing game assets, captured pixels, OCR or Query."
      - "Record at least two actual useful physical lookup routes for a second real fullscreen game, with fresh distinct source frames, exact selected word/context/span and cursor box, correlated lookup/game PID/start/run/request/window, kernel-clock input and actual useful overlay observations."
      - "For the captured routes, record recent actual relative-lock protocol evidence for that same game process, then physical dismissal and subsequent camera plus movement control, using distinct input/frame proofs after the useful overlay."
      - "Recompute the strict captured-game and final aggregate reports from raw evidence; keep rejected attempts and do not waive GAME-01 or substitute menu-only/ungrabbed/Qt scenes."
      - "At the final gap-closure revision, obtain fresh host/target suites, independent review and re-verification. Refresh target evidence rather than relabeling the old751-test target run."
warnings:
  - truth: "Plan05 final fresh target regression evidence covers the final closure revision."
    status: uncertain
    classification: WARNING
    reason: "Current host752 tests cover a10c5e1; last target751 tests cover d5488b3 before the host-only evidence-binding correction. Production bytes are unchanged, but current-target freshness is not proven and must be refreshed during gap closure."
---

# Phase 8: Goal Verification

**Goal:** The actual VM application meets the declared first-useful speed and long-run/fault/scaling/privacy contracts, installs cleanly, and works through useful OCR overlays in at least two real fullscreen games, including captured-mouse use and returned gameplay control.

**Status: gaps_found.** Six roadmap criteria are verified. Mandatory GAME-01 is not achieved: a real second captured game ran, but its useful selected-word/overlay route did not. Completed plans, passing unit tests and genuine pointer lock do not replace that missing behavior. No new override is applied; the historical Phase7 preservation exception does not waive this gap.

## Observable Truths

| # | Roadmap criterion | Status | Evidence |
|---|---|---|---|
| 1 | SC1: about30 physical hotkeys to actual useful visibility, median <=1500ms and recorded p95 | VERIFIED | Raw30 independently recomputed from verified kernel evdev CLOCK_MONOTONIC input to same-clock useful-frame capture end. Median **1128.057506ms**, nearest-rank p95 **1455.247426ms**. Three cold,18 distinct and9 repeat samples; matching PID/start/run/request/frame identity and numeric stages. No userspace receipt origin or overhead subtraction. |
| 2 | SC2: actual100/125/150/200% cursor/word/popup correctness plus pure scale/negative-origin tests | VERIFIED | Four complete native scale records, actual work-area/cursor/result evidence and restored layout; current focused geometry/OCR checks pass. Only one output existed, so optional second-output behavior remains unverified rather than passed. |
| 3 | SC3: no retained production capture files/clipboard changes; specific recoverable faults | VERIFIED | Exact PRIMARY/CLIPBOARD/ordered Klipper hashes match; capture-file list is empty. Real network outage and actual owned dictionary unavailability recover. Active ScreenShot2 transport failure is explicitly injected and recovers; this is not described as killing Spectacle, which is not the current backend. |
| 4 | SC4: several hundred completions, bounded resources and ten-key burst without corrupt history/orphans | VERIFIED |20 warmups plus320 physical completions; one PID/start/run,32 resource observations, no owned descendants and integrityok. Early/late median RSS174657536/174698496 bytes, late trend8192, cooldown174702592 within predeclared bounds. Ten actual chords have required cadence; newest completion/history/integrity/recovery checks pass. |
| 5 | SC5: README install/login/autostart/removal from honest clean owned baseline | VERIFIED | New owned lookup08install UID1002 and genuine SDDM session; no installed product or existing product user paths. Official dependencies are explicitly inventoried, not claimed absent. Actual staging/makepkg-si, installed helper/Mueller/authorized physical OCR, enabled/disabled login and data/key-preserving pacman removal:11 product and7 cleanup gates. This is a clean application/profile baseline, not a claim of a newly provisioned minimal Arch OS. |
| 6 | SC6 / GAME-01: two real fullscreen useful game routes, including captured mouse and resumed control | **FAILED — BLOCKER** | Wesnoth1.18.8 has two distinct useful fullscreen routes and actual subsequent movement/combat. Freedoom0.13.0/Chocolate Doom3.1.1 has fullscreen, software renderer, real Wayland lock and camera/navigation evidence, but **zero accepted useful routes**. See structured gap. |
| 7 | SC7: first-useful timing distinct from contextual meaning latency/success rate | VERIFIED | Offline article/real visibility is measured independently. Six live provider probes yield0/6 success, six blocked reasons; successful meaning median/p95 and physical-UI success latency remain **null**. Provider-only attempts are not UI latency or fake successful enrichment. Controlled nonblocking tests remain separate. |

**Score:** 6/7 roadmap truths verified. Additional plan final-target freshness is a WARNING, not a claim that the current Linux suite ran. Mandatory second-game failure is concrete, not UNCERTAIN and not eligible for the Phase7 exception.

## Substantive Artifacts and Wiring

- `lookup/timing.py` implements an opt-in numeric allowlist with fixed stages and correlation identity; it refuses text/nonfinite/unknown fields. CLI and GUI call it. Internal readiness/presentation is explicitly separate from external compositor proof.
- `lookup/gui.py` preserves early useful lookup semantics, waits for compositor placement before useful paint and starts inactivity timeout at actual reveal. Source changes are tied to demonstrated defects/regressions, not benchmark-threshold relaxation.
- `tools/check_hardening.py` consumes real physical/workload/resource/privacy/fault records. Kernel clock ioctl verification, same-domain input/frame timestamps, identity/fresh useful frame, exact workloads and predeclared bounds are substantive rejection checks. It recomputes the seven criteria rather than accepting summary booleans.
- `tools/check_games.py` observes original Source.freeze/resolve returned objects, actual game process/window, fresh source pixels, selected production OCR/context/span and useful overlay. The captured oracle additionally requires recent same-process protocol lock and post-dismiss distinct camera/movement inputs/frames. It correctly fails empty Doom routes.
- `tools/check_hardening_install.py` binds build/negative-origin evidence to actual log/source hashes and validates clean owned baseline, exact installed paths, sustained real login observations, retention and cleanup. Latest pure binding correction does not change deployed application code.
- Guarded VM controls target the owned clone/account/disk; this verification performed no VM operation. Existing production/dictionary/learning paths remain connected; no placeholder was found that explains away or fulfills the missing second-game result.

## Independent Checks and Evidence Identity

Fresh current-tree command:

`python -m unittest tests.test_hardening tests.test_check_games tests.test_hardening_install tests.test_timing tests.test_platform tests.test_ocr tests.test_app_gui`

**108 tests OK, zero skips,5.334s.** This is independent focused verification at the current tree, not a new full target run.

Continuation recheck at2026-10-30T22:21:41Z (October31 local time) reconfirmed the raw six-of-seven aggregate, failed captured-game oracle, exact performance statistics, all referenced raw hashes, explicit host/target revision difference and unchanged historical Phase7 false preservation report. No new native workload or full target run was performed or claimed during this artifact close-out.

Independent read-only assertions also:

1. Rehashed every raw source referenced by `08-final-aggregate.json` and matched the recorded SHA256.
2. Recomputed30 latency values directly from kernel input/frame-end timestamps, median and nearest-rank p95; checked all clock-verification flags and frame PID/start/run/request identities.
3. Re-ran pure performance, stability, burst, scale, privacy, faults, install and game oracles against retained raw records. Six product groups pass; captured game and overall aggregate remain false.
4. Matched both Wesnoth source and useful-overlay PNGs to recorded hashes, plus before/after gameplay images for movement and combat. Inspected actual useful overlay/source and actual failed Doom HUD/prompt images.
5. Matched both failed Doom source PNG hashes to their source observations and correlated physical input -> capture -> production stage6 by lookup PID/run/request. Capture really happened; the failure is lack of a valid selected production Query/useful result, not proof that capture or physical input was absent.
6. Validated actual build-log/source binding and negative-origin test-log binding; installation11/11 and cleanup7/7 are supported. The retained source comparison reports identical32 source member names/bytes despite differing compressed archive hashes. Git comparison from production5d04a4c through a10c5e1 shows no lookup/packaging/PKGBUILD changes.
7. Confirmed final aggregate has6/7 criteria, all11 global cleanup checks, `passed:false`, `game01_complete:false`. Independent completion remains pending in the retained aggregate and is not silently promoted by this report.

Principal evidence: `08-performance-final-attempts.json`, `08-stability-recursive-final-attempts.json`, `08-burst-final-verified.json`, `08-scales-final-complete-report.json`, privacy/fault reports, `08-wesnoth-final-report.json`, `08-doom-final-report.json`, `08-install-native-report.json`, `08-final-aggregate.json` and their referenced source/frame/log artifacts.

## Concrete GAME-01 Gap and Next Implementation Slice

Both Doom attempts have current real ScreenShot2 sources and correlated stage6 completion. QUIT at670,440 produced no Query in830.013ms; HEALTH at312,778 produced no Query in591.642ms. Original diagnostic files show no matching HEALTH token and low-confidence misread ARMOR, while the red decorative QUIT text is not selected. The screenshots contain the actual intended game text; unrelated recognized fragments elsewhere in the image cannot count as that word.

Primary gap slice: reproduce these real sources in portable preprocessing/selection tests, then either fix the demonstrated production read/selection defect conservatively or reach genuinely readable real text while actual captured gameplay remains active. Do not patch the reported selected word, source pixels, Query, dictionary result or pass flags. Supported game rendering/settings and legitimate navigation may be used, with actual resulting pixels/provenance retained.

Closure needs two successful, changed-source, physical fullscreen routes for a second actual game, including current selected occurrence/context/span and useful overlay. For captured mouse, record same-process recent lock evidence, physical close, and later distinct relative-camera and movement proof. Existing camera/navigation evidence without a preceding useful overlay remains partial evidence only. Preserve all rejected attempts. Recompute strict reports, run current host/target suites, then independently re-review and re-verify.

## Requirements Coverage and Freshness

| Requirement | Plans | Result |
|---|---|---|
| PERF-01 | 01,02,05 | SATISFIED for the declared actual30-request first-useful workload; raw median/p95 and separate meaning denominator verified. Game observations do not claim the same1500ms bound. |
| GAME-01 | 01,03,04,05 | **BLOCKED** by the absent useful second fullscreen/captured route and its post-useful return sequence. |

No mapped Phase8 requirement is orphaned. Neither requirement is waived here.

Whole-suite records are explicit: host **752 OK,8 skips,31.220s at a10c5e1**; last target **751 OK,0 skips,40.223s at d5488b3**, before the host-only raw-binding correction. The latter is relevant production/regression evidence but not fresh current-target evidence. Refresh the target run at final gap closure instead of inventing a752-test Linux result. Existing negative-deadline SemLock teardown noise is retained; no new assertion failure is inferred from that known diagnostic.

## Scope, Cleanup and No Waiver

The final install has package absent, owned profiles/data retained and both VMs powered off; no original VM action was performed by this verification. Raw global cleanup is11/11. One output and optional borderless modes remain explicitly unverified. Software-renderer/3D-disabled game conditions are recorded, not universal game compatibility.

Historical Phase7 `original_preserved:false`, unknown actor and its narrow continuation exception remain unchanged. That earlier exception does not accept GAME-01, fresh-target evidence, performance or any missing Phase8 criterion. No new override is applied. Agent observations are not human testing. The remaining gap is actionable implementation/verification work for automatic gap planning, not a request to waive it or stop the authorized workflow.
