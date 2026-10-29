---
phase: 08-vm
plan: 01
subsystem: hardening-evidence
tags: [timing, privacy, clocks, statistics, evidence]
requires:
  - phase: 07-settings-package
    provides: Installed generation-safe application and explicitly retained preservation exception
provides:
  - Opt-in numeric daemon/CLI timing with honest internal boundaries
  - Predeclared physical latency, memory, burst, privacy, fault and game oracles
  - Adversarial clock/receipt/frame/evidence rejection coverage
affects: [08-02, 08-03, 08-04, 08-05]
tech-stack:
  added: []
  patterns: [numeric allowlist, single-clock upper bound, strict raw evidence]
key-files:
  created:
    - lookup/timing.py
    - tests/test_timing.py
    - tools/check_hardening.py
    - tests/test_hardening.py
  modified:
    - lookup/__main__.py
    - lookup/gui.py
key-decisions:
  - A per-interpreter numeric run token is correlation metadata, never a claimed kernel process start.
  - Guest acceptance starts only at a verified kernel monotonic evdev timestamp; receipt never supplies the origin.
  - Otherwise use same-host pre-VBox input to actual-frame capture-end upper bound without overhead subtraction.
  - Fixed workload/resource thresholds precede native measurement; missing or false evidence cannot pass.
requirements-completed: []
duration: 17min
completed: 2026-10-29
---

# Phase 8 Plan 01: Timing and Strict Evidence Oracles Summary

**Numeric internal timing and strict predeclared raw-evidence checks are ready for native measurement; no performance or game acceptance is claimed.**

Implementation: `lookup/timing.py` and `tools/check_hardening.py`.

## Production Timing Contract

- `timing.Sink.emit(stage,request,at_ns=None,**fields)` returns whether it emitted one numeric JSON line prefixed `lookup-timing:`. It is silent unless LOOKUP_TIMING=1, rejects unknown/text/bool/nonfinite/oversized values and never serializes word/context/translation/URL/provider exception/activation token.
- Every record has numeric pid, run, request, stage and mono_ns. The run token is stable across Sink instances within one interpreter and is **not** kernel start time. Native observers separately obtain process_start from /proc start ticks. Correlate by pid/process_start/run/request.
- STAGES maps trigger=1, queue=2, useful_ready=3, present=4, meaning_ready=5, error=6. Trigger records entry to the daemon slot after dispatch; queue records the existing delayed enqueue. useful_ready means an accepted nonempty article/translation has arrived internally. present is the internal show call with numeric useful=0/1, **not compositor visibility**. meaning_ready is independent, with numeric meaning_cache.
- elapsed_ms is measured from Trigger entry; engine_ms retains Event.elapsed_ms. Existing Result/OCR stage fields remain their measured durations. FIELDS is the explicit numeric allowlist. `print_cli` keeps the existing timing line and three-decimal millisecond formatting for known fields.
- Old generations, closed-popup late meanings, loading and header-only articles cannot create useful-ready/meaning acceptance telemetry. No listener, synchronous capture/network or worker/resource ownership change was introduced.

## Native Consumer Raw Schema

All physical timestamps below are integer nanoseconds; no host/guest subtraction is permitted. The canonical synthetic schema fixture is sample() in tests/test_hardening.py. These are test fixtures, not actual measurements.

| Fields | Required meaning |
|---|---|
| attempt, input_sequence | Integer sequence 1..N, with no dropped/relabelled attempts within the declared workload. |
| mode, status, physical, released | native / success and literal true physical/full-release observations for an accepted sample. Failed/replaced records stay in the input list and prevent the main batch passing. |
| pid, process_start, run, request | Positive numeric identity; process_start_source must be proc_stat. process_start is external kernel start ticks, run is the daemon numeric token. |
| clock, frame_clock, origin, input_ns | Matching guest_monotonic with kernel_evdev, or matching host_monotonic with host_before_vbox. |
| kernel_clock_verified, clock_ioctl_verified, trigger_ns | Guest route requires both literal true after successful EVIOCSCLOCKID verification and input <= Trigger <= useful capture end. receipt_ns is optional diagnostic delivery time only and can be later than Trigger. |
| before_dispatch, dispatch_ns | Host fallback requires literal true and input_ns <= same-host VBox dispatch <= useful capture end. Guest Trigger values are not subtracted from host timestamps. |
| last_not_visible_ns, first_visible_start_ns, first_visible_end_ns | Ordered capture bracket; accepted latency is capture END minus input, never internal show time or receipt. Uncertainty is retained, not subtracted. |
| frame_identity, frame_sha256 | Matching four-field identity and actual useful-frame SHA-256. observed/fresh/useful_verified must be literal true; loading/error_card/previous_card literal false. Native drivers must actually verify these facts. |
| group, case | Main batch groups cold/warm_distinct/repeat and positive synthetic case identity. |

`physical_latency` raises EvidenceError on invalid evidence. `performance_report` requires exactly 30 attempts: 3 distinct cold process identities, 18 unique warm cases on one of those processes and 9 repeats of warm cases. Every accepted request identity is unique. It retains raw records/errors, subgroup statistics, ordinary median, nearest-rank p95 and maximum capture uncertainty; median must be <=1500ms.

`online_report` is optional and allows up to 3 uncached plus 3 cache physical requests; cache cases require a preceding real successful uncached seed and distinct request identity. Failed availability attempts retain reasons with null conditional statistics. They cannot replace the main 30.

`meaning_report` requires six unique uncached live case attempts: kind=live, live=true, cached=false, mock=false, and either verified successful duration_ms or a fixed provider error reason. It reports attempted/success/reasons, success fraction and successful latency separately. Zero successes yields null median/p95. Optional kind=cache rows require cached=true/live=false/seeded=true and remain separate.

## Fixed Stability, Burst and Other Gates

- `protocol()` returns the fixed premeasurement settings. `stability_report` requires 20 warmup and 320 completion physical records, sequential 1..340 and one unchanged process identity. Resource rows occur after every 10 measured completions, exactly 10..320, with identity=[pid,start,run], observed=true, positive rss_bytes/threads/fds and owned_children=[]. Cooldown repeats after=320 after at least 5000 idle milliseconds.
- First/last 60 completion windows use their six resource samples. Last-window median RSS must be <= first-window median + max(16MiB,15%). The adjacent final three-sample medians may rise by at most max(4MiB,5% of early median); cooldown RSS is bounded by late median plus that same allowance. Cooldown FD count is at most early-six maximum+4, threads at most early-six maximum+2. All bounds were fixed before native measurements and are not caller-configurable. Require history_delta=320, integer enrichment_extra_count=0 and integrity=ok.
- `burst_report` requires ten sequential fully released physical inputs with distinct increasing request IDs. Top identity/process_start_source identifies the unchanged daemon; accepted_requests is a unique subset including the newest input, final_request is newest, and final_identity/frame hash prove its final useful frame. history_delta equals accepted count (not necessarily ten), enrichment adds zero, integrity is ok and all BURST_GATES are literal true.
- `privacy_report` requires owned native before/after hashes for PRIMARY, CLIPBOARD and ordered Klipper content, equality, empty capture_files and all PRIVACY_GATES including scans of temporary/runtime/database directories. `faults_report` requires network/dictionary/capture records and all FAULT_GATES; network/dictionary must be real faults, capture may be explicitly injected.
- `games_report` requires two distinct actual fullscreen games with version/renderer/PID/verified source, different actual/post-dismiss frame hashes and all GAME_GATES. At least one has multiline text, and one has relative_mouse/pointer_locked/relative_gameplay_verified all literal true. Missing, mock, windowed-only, loading or no-returned-gameplay evidence cannot pass. Optional borderless/second-output limits remain separate.
- `strict_gates` rejects absent, false, None, integer 1, skipped/mock strings and false extra gates. `carry_phase7` retains the original raw passed:false/original_preserved:false object and unknown actor in a separate historical field; it does not create a pass, new attribution or waiver.

## Task Commits and Validation Results

1. Task 1 RED: `4d31f2b`; GREEN: `67e57ab` — private numeric sink and honest GUI/CLI boundaries.
2. Task 2 RED: `8f0cfcd`; GREEN: `e7fb3d6` — strict phase-specific evidence oracles and adversarial fixtures.

- Timing/CLI/GUI/early-translation/privacy focused suite: **56 tests OK**.
- Final hardening/timing/geometry/OCR/app/privacy focused suite: **70 tests OK**, 1.975 seconds.
- Final full discovery: **716 tests OK, 8 skipped**, 29.301 seconds, exit 0. Existing controlled VM setup-error output reported all restoration flags true.
- Adversarial receipt delay with fixed kernel event/frame leaves latency unchanged and a slow batch failing. Tests also reject unverified clocks, receipt origins, clock mixing, old/loading/error/missing frames, missing/duplicate attempts, relaxed resource protocol, process reset/orphans/count drift, unseeded optional cache and incomplete/mock/gameplay-deficient game routes. Existing scale/negative-origin geometry/OCR regressions remain covered.
- `git diff --check` for owned files: exit 0. No tracked deletions or unresolved core stubs.

## Limits

No VM boot, live timing series, sustained workload, privacy/fault injection, game launch or new acceptance occurred in this unit. Evidence structure cannot itself prove an actual frame/game/input happened; later native drivers and independent verification must supply and inspect those observations. PERF-01/GAME-01 remain open. Phase7's historical false preservation report and unknown actor remain unchanged. Global planning state, research and pre-existing user changes remain parent-owned.

## Self-Check: PASSED

All six implementation/test files and this summary exist. Task commits `4d31f2b`, `67e57ab`, `8f0cfcd` and `e7fb3d6` exist. Final verification passed after the last code change; no known stub prevents this preparation unit's goal.
