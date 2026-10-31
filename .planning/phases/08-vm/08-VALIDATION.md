---
phase: 08
slug: vm
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-10-29
---

# Phase 8 — Validation Strategy

## Infrastructure and sampling

Existing Python stdlib unittest; native KDE/game checks in an explicitly owned VM/profile. No new production dependency or generic benchmark framework. Run focused regression tests after each meaningful change and the full suite at integration boundaries. Full command: python -m unittest discover -s tests; target enables LOOKUP_TEST_OCR and LOOKUP_TEST_DICTS. Current full suite is about40s; long physical/game scenarios report bounded progress separately.

Exact task IDs/commands are mapped below. Implementation tasks create behavioral tests with their contracts; existing unittest/native tools need no separate scaffold wave. Structural Nyquist compliance is established; runtime acceptance remains pending actual evidence. No three consecutive tasks without automated feedback; no watch mode.

## Required verification map

| Task | Requirements / criteria | Automated feedback | Actual acceptance |
|---|---|---|---|
| 01-1 | PERF-01 SC1/7 | python -m unittest tests.test_timing tests.test_cli tests.test_app_gui tests.test_translate_ready tests.test_privacy | Numeric daemon stage schema; no compositor-time fiction |
| 01-2 | PERF-01/GAME-01 SC1/2/4/6/7 | python -m unittest tests.test_hardening tests.test_platform tests.test_ocr tests.test_app tests.test_privacy | Predeclared strict clock/resource/game/null-meaning oracles |
| 02-1 | PERF-01 SC1/7 | python -m unittest tests.test_hardening tests.test_timing tests.test_app tests.test_privacy | 30 physical useful frames incl dispatch, median<=1500/p95, cold/warm/online/live meaning denominator |
| 02-2 | PERF-01 SC2/3/4 | python -m unittest tests.test_hardening tests.test_platform tests.test_ocr tests.test_app tests.test_privacy | Actual20+320/stress/burst/privacy/fault/scales with raw samples/cleanup |
| 03-1 | GAME-01 SC6 | python -m unittest tests.test_check_games tests.test_hardening tests.test_platform tests.test_app | Actual official Wesnoth process/map/renderer/fullscreen contract |
| 03-2 | GAME-01 SC6 | python -m unittest tests.test_check_games tests.test_platform tests.test_ocr tests.test_app | Repeated changed multiline narrative -> physical OCR/useful overlay -> resumed gameplay |
| 04-1 | GAME-01 SC6 | python -m unittest tests.test_check_games tests.test_hardening tests.test_platform | Official Chocolate3.1.1/Freedoom0.13 bytes/hash/build/actual fullscreen gameplay |
| 04-2 | GAME-01 SC6 | python -m unittest tests.test_check_games tests.test_hardening tests.test_app tests.test_platform tests.test_ocr | Actual grabbed-target word, fresh OCR/overlay, close and visible relative camera/movement return |
| 05-1 | SC5 | python -m unittest tests.test_hardening_install tests.test_package tests.test_lifecycle tests.test_doctor | Honest clean app/profile owned snapshot, README install/real login/remove/data retention |
| 05-2 | PERF-01/GAME-01 SC1–7 | python -m unittest discover -s tests | Fresh host/target, all raw-backed mandatory gates and independent review/verifier |

All five execution units are serialized by dependencies and waves1–5 because they share owned clone/account/native input. Plan03 and04 also share tools/check_games.py. No same-VM parallel acceptance. Pure/exclusive file work alone may be delegated without VM access. Long native loops report progress and preserve raw evidence; focused command feedback is distinct from actual runtime gate success.

## Source Coverage Audit

| Source | Item | Plans | Status |
|---|---|---|---|
| GOAL | Actual VM speed/stability without masking geometry/selection bugs | 01–05 | COVERED |
| REQ | PERF-01 | 01,02,05 | COVERED |
| REQ | GAME-01 | 01,03,04,05 | COVERED |
| ROADMAP | SC1 full physical first-useful median/p95 | 01,02,05 | COVERED |
| ROADMAP | SC2 actual scales/optional output + pure negative geometry | 01,02,05 | COVERED |
| ROADMAP | SC3 privacy/fault/capture production interpretation | 02,05 | COVERED |
| ROADMAP | SC4 sustained/burst/integrity | 01,02,05 | COVERED |
| ROADMAP | SC5 clean owned README install/login/remove | 05 | COVERED |
| ROADMAP | SC6 two real fullscreen/captured/multiline/resumed control | 03,04,05 | COVERED |
| ROADMAP | SC7 independent contextual success metrics | 01,02,05 | COVERED |
| CONTEXT | D-01 owned clone/account/path guard | 02–05 | COVERED |
| CONTEXT | D-02 unchanged Phase7 strict-false exception | 01–05 | COVERED |
| CONTEXT | D-03 actual first-useful clock/workload | 01,02,05 | COVERED |
| CONTEXT | D-04 live conditional meaning metrics/null on zero | 01,02,05 | COVERED |
| CONTEXT | D-05 actual four scales/pure geometry | 01,02 | COVERED |
| CONTEXT | D-06 predeclared20+320/burst/RSS/children | 01,02 | COVERED |
| CONTEXT | D-07 owned clipboard/Klipper/files/real-vs-injected faults | 02,05 | COVERED |
| CONTEXT | D-08 actual two games/fullscreen/relative mouse | 03,04,05 | COVERED |
| CONTEXT | D-09 honest clean owned baseline | 05 | COVERED |
| CONTEXT | D-10 raw evidence/fresh tests/independent acceptance | 01–05 | COVERED |
| RESEARCH | No daemon LOOKUP_TIMING, dispatch omitted, compositor visibility missing | 01,02 | COVERED |
| RESEARCH | Passive exact-chord observer or host upper bound, no clock mixing | 01,02 | COVERED |
| RESEARCH | Official Wesnoth/Chocolate/Freedoom; real locked targeting unresolved | 03,04 | COVERED |
| RESEARCH | OpenTTD fallback cannot replace captured-mouse requirement | 04 | COVERED |
| RESEARCH | Original unchanged report, license/provider limits, no pristine-Arch fiction | 05 | COVERED |

No optional unavailable mode, external provider failure or historical operational exception waives mandatory GAME-01/PERF-01 observation. Production changes beyond numeric timing require demonstrated defect, scoped owning-file task and behavioral regression before retest.

## Execution evidence

Keep raw samples with process/start/request/input identity and clock domain, stage timings, capture visibility brackets/uncertainty, every attempt/error and live-provider success denominator. Guest acceptance requires successful verified EVIOCSCLOCKID(CLOCK_MONOTONIC) and KERNEL completing-key event timestamp, with actual visible-capture end in the SAME guest CLOCK_MONOTONIC domain. Userspace receipt is diagnostic ONLY, NEVER an acceptance origin. If kernel clock/event timestamp cannot be verified, mandatory fallback is HOST monotonic BEFORE VBox physical input to SAME-host actual useful-frame capture end conservative upper bound, no overhead subtraction or cross-clock arithmetic. Tasks01-2/02-1 must behaviorally test receipt delayed beyond Trigger: fixed event/frame latency and failed-threshold status cannot improve, receipt-origin records reject, unknown kernel clock requires host fallback. Use nearest-rank p95 and ordinary median. A loading frame or fake provider reply is not a useful live result. Successful meaning latency is null if none succeeds.

Predeclared sustained gate: after20 warmups,320 physical completions; late60 median RSS <= early60 median +max(16MiB,15%), with late-batch trend and cooldown samples. Exceedance requires diagnosis/retest, not a retrospective threshold change. Require integrity_check=ok and no orphaned owned helpers after burst/idle.

Game renderer/fullscreen/cursor lock and post-dismiss gameplay are execution observations. Missing mandatory fullscreen/captured-mouse evidence cannot pass through unit tests. Optional unavailable second output/borderless mode remains explicitly unverified.

## Scope and cleanup

Never boot/revert/delete original arch-kde. Validate clone UUID/disk/account and owned resolved paths. Passive input observer matches only the test chord, never grabs keys or logs unrelated input. Original Phase7 raw report remains false; its separate GUI-run byte-preservation exception is historical and must be carried forward. Start a new owned baseline rather than falsely asserting original identity. Restore owned layout/network/input state, stop owned children, retain synthetic evidence and power off owned clone.

## Sign-off

- [ ] Exact tasks and automated commands mapped by planner.
- [ ] Timing samples and median/p95 gates verified from raw data.
- [ ] Stress/burst/privacy/fault evidence and cleanup verified.
- [ ] Clean install/login/remove cycle verified.
- [ ] Two real fullscreen game routes and captured mouse verified.
- [ ] Fresh appropriate host/target regression suites and independent review/verification.
- [ ] Nonblocking limits and Phase7 preservation exception retained honestly.

Approval: pending agent acceptance under explicit --auto.

## Gap Closure — 2026-10-31 (08-06/08-07)

Source: 08-VERIFICATION.md at1a6b6f3 has6/7 criteria verified and one mandatory GAME-01 blocker. No useful Doom captured route exists; GL/SDL lock or passing tests alone cannot close it. 08-GAP-RESEARCH.md atb4f6e94 selects ONE bounded AssaultCube pilot; old04 failure stays unchanged. Final prior target suite is stale relative to host-only fixes. Existing six accepted raw groups are reused, not unnecessarily remeasured.

| Task | Requirement | Automated feedback | Native/acceptance gate |
|---|---|---|---|
| 06-1 | GAME-01 | python -m unittest tests.test_check_games tests.test_platform tests.test_ocr tests.test_app_gui | Early real useful/grab pilot before substantial expansion: official pinned archive, actual GL/driver/fullscreen, genuine scoreboard heading under actual grab, physical selected Query/useful overlay. Declared two-resolution/one-shipped-font budget and stop condition. |
| 06-2 | GAME-01 | python -m unittest tests.test_check_games tests.test_hardening tests.test_timing tests.test_platform tests.test_ocr tests.test_app_gui | Explicit candidate provenance/GL/SDL-call-and-return/queried relative state; actual Wayland lock only for real Wayland driver, never fabricated for X11; strict source/input/control correlation. |
| 06-3 | GAME-01 | python -m unittest tests.test_check_games tests.test_hardening tests.test_app_gui tests.test_platform | Two changed useful captured fullscreen routes, physical dismiss and distinct camera+movement proof, all keys released, new06 cleanup/product absence/data retention/clone settings restored OFF. |
| 07-1 | GAME-01 | python -m unittest tests.test_hardening tests.test_check_games tests.test_hardening_install tests.test_timing | Raw selected captured report/cleanup binding plus accepted Wesnoth; failed Doom retained, no hardcoded metadata/exits/count/digest or changed previous six groups. |
| 07-2 | GAME-01 | python -m unittest discover -s tests | Fresh actual full host+target at same recorded final code revision, latest07 cleanup, recomputed aggregate, then parent independent review/security/verifier. |

Dependencies: 06 depends05 (wave6);07 depends05/06 (wave7). All shared owned-VM/account access is serialized. No new frontend/UI gate, mapper regeneration, production dependency or production OCR edit is planned. Pilot failure stops further candidate expansion and leaves GAME-01 open; no new catalogue or blanket waiver. If a portable saved-source OCR fix becomes demonstrated later, separately scope exact source/test files and remeasure affected first-useful performance.

Durable rejection cases: wrong candidate URL/byte size/hash/executable/UID/version evidence; stale process; absent real GL log; failed/absent/stale/unlocked relative state; driver/protocol mismatch; stage6/no Query; incorrect box/span; previous/fake/empty overlay; duplicate source/input/control frames; report/cleanup swap, incomplete cleanup, old suite identity or fabricated outcome. Read-only taps call originals exactly once and return original objects/results/errno.

### Gap Source Coverage

| Source | Required closure item | Plan/task | Coverage |
|---|---|---|---|
| GOAL/REQ | Useful second real fullscreen captured game, post-close control (GAME-01) | 06-1..3,07 | COVERED |
| VERIFIER missing1 | Diagnose real sources OR reach genuinely readable unchanged actual captured text | 06-1 authentic scoreboard pilot; no speculative production fix | COVERED |
| VERIFIER missing2 | Two useful changed physical routes, exact source/span/box/identity/clock | 06-2/3 | COVERED |
| VERIFIER missing3 | Actual same-process grab then physical dismiss/camera/movement | 06-2/3 | COVERED |
| VERIFIER missing4 | Raw recomputation, rejected attempts and mandatory no-waiver | 06-3,07-1 | COVERED |
| VERIFIER missing5/warning | Fresh final host/target, independent review/verifier | 07-2 | COVERED |
| RESEARCH | Exact official RC1 asset/SDL2 GL runtime, pilot budget before adapters | 06-1/2 | COVERED |
| RESEARCH | Explicit selected-candidate aggregate and current cleanup, failed Doom history | 07-1/2 | COVERED |
| CONTEXT D-01/D-02 | Owned clone only; original strict-false unknown-actor exception unchanged | 06,07 | COVERED |
| CONTEXT D-03..D-07/D-09 | Accepted performance/meaning/scales/stress/privacy/install remain binding and reused unchanged | 06 production-member comparison,07 raw reuse | COVERED |
| CONTEXT D-08/D-10 | Actual useful game/returned control, raw evidence and independent final acceptance | 06,07 | COVERED |

No missed mandatory gap is deferred. Historical original-preservation exception, optional modes, provider429 and licensing limits remain separate from GAME-01 acceptance. Do not claim current target count/exit, actual renderer/grab/useful route or review outcome before execution evidence.

### Explicit Original-VM Policy Override — USER_KEEP_RUNNING

The original arch-kde was found RUNNING; user explicitly instructed: «другой агент с другим проектом там работает, не мешай ему». Leave it untouched by OUR actions; other agents may legitimately change its state. This supersedes ONLY original-OFF prerequisites and final-original-OFF checks in plans06/07 and their referenced older prescriptions. No original guest SSH, disk contents/read/hash, writes/stop/reboot, host VBoxSVC or global-network changes. Read-only host identity/state metadata is sufficient; do not access default archvm/SSH2223. Mutable operations require independent owned clone UUID cf207909-94b5-4b49-8bd8-ccff973c1dc8, explicit SSH2227 and guest DMI guard. Assigned native executor is the sole VM/source owner; documentation work does not start or block VM actions.

New cleanup must honestly record user_policy=USER_KEEP_RUNNING, observed actual original before/after host states (external changes allowed), zero original actions and computed original_state_respected from zero OUR original control/guest/disk actions and all mutations clone-guarded, not before/after state equality; no original VDI/config hash comparison while another project is active. Missing provenance/actions evidence stays unverified, never a fabricated original-OFF/pass. Clone cleanup still releases input/stops owned processes/removes reinstalled product retaining data, powers clone OFF and restores its prior3D/clipboard only while OFF. Preserve historical07 strict-false/unknown-actor reports unchanged. All six accepted criteria remain intact and mandatory GAME-01/PERF-01 are not waived.
