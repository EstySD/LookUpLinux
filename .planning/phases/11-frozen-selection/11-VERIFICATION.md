---
phase: 11-frozen-selection
status: pending
verified_at: 2026-11-03
implementation_verification: passed_native_agent
independent_phase_verification: pending
human_acceptance: not_performed
requirements: [CAPT-08, TRIG-05, TRIG-06]
---

# Phase 11 — Native product verification evidence

Plan 03 executed the actual product, not the research replacement layer. Final phase acceptance remains with the independent verifier. Product source hashes, including the user's unchanged working-tree OCR edits, are in `11-product-evidence.json`; they match the host working tree and the staged target.

## Results

| Contract | Actual evidence |
|---|---|
| One captured frame and subsequent selections | Fixture session 9 returned `bright` → `яркий`, `river` → `река`, and the captured tooltip word `captured` → `сохранённый`, with increasing request IDs and one unchanged frame hash. |
| Source continues while the displayed scene stays retained | Source PID 997 ticks advanced 2996→3076; its pointer/click count stayed 6→6 during selections, corner/edge motions and blank clicks. After Esc, the same PID's count advanced to 10. |
| Useful no-hit and internal focus | Physical blank no-hit clicks hid a popup covering adjacent words, then further physical selections worked in the same session. This interaction is recorded rather than hidden as a direct adjacent-word click. |
| Primary selection and cards | Public fresh PRIMARY `river` used ordinary `mode=primary`, without a scene. A real card action saved `bright` with `яркий` and the source context in the isolated database. |
| Coordinate and display scaling | Native 125% and 200% runs both returned `bright` → `яркий`; KWin layer rectangles were exactly `(0,0,1024,640)` and `(0,0,640,400)`. The 100% run covered `(0,0,1280,800)`. Screenshot controls stayed reachable. |
| KWin ownership and placement correction | Active-layer inspection rejected a foreign game UUID with `invalid_owner`; owned UUIDs contained only the product layer. Actual KWin geometry matched the captured monitor. Raw scale records also distinguish the exact popup title from the layer. |

Raw fixture data: `11-native-data/evidence/fixture-{before,words-final,during,after}.json`; captured PNG hash is checked against the report. The layer screenshot is a separate actual-product visual sample, not asserted to be the identical fixture session.

The earlier `11-native-data/evidence/ownership.json` diagnostic had no active scene and did not establish the requested rejection. It is not accepted proof. The later active-layer check in `11-timeout-recheck/11-native-batch.json` explicitly records `foreign_rejected: true` and the owned layer geometry.

## Real fullscreen Wesnoth

Target: KWin `6.8.1-2`, Qt `6.12.0`, Wesnoth `1:1.18.8-2`, owned `lookup-gsd-07` clone. A transparent `SDL_PollEvent` observer called the original exactly once, preserving its return, event and errno. Source counters came from the game process, not the overlay.

| Exit | Source PID | Before → during → after | Result |
|---|---:|---|---|
| Esc | 2450 | 14 → 14 → 21 | Pass |
| Visible close | 2450 | 28 → 28 → 35 | Pass |
| Repeated hotkey | 2450 | 42 → 42 → 49 | Pass |
| Configured timeout, affected rerun | 6456 | 15 → 15 → 22 | Pass |
| Injected operational OCR error | 2450 | 84 → 84 → 91 | Pass |
| External focus | 2450 | 98 → 98 → 105 | Pass |
| Product process termination | 2450 | 112 → 112 → 119 | Pass |

Every reused case has raw before/during records proving a visible actual OCR scene, stable session/frame and the same source PID within its three measurements. The timeout rerun has a separately declared PID; no cross-process counter comparison is presented as same-process evidence. Corner/edge input and two actual layer selections were included.

The original batch's timeout collector incorrectly waited for OCR completion after a short timeout could cancel it. Its failure remains in `11-native-batch.json`. The affected batch used a real configured 10-second timeout, collected actual closure and reran only timeout plus the evidence validator. Production code did not change. Setup-only failures are retained separately; none are counted as product passes.

## Regressions and acceptance

| Check | Fresh result |
|---|---|
| Host full suite, parent-run | 857 tests, OK, 11 skips, 43.766 s; `11-host-tests.json` |
| Target full suite | 857 tests, OK, 4 skips, 75.788 s; `11-native-data/evidence/target-tests.json` |
| Final evidence validator tests | 4 tests, OK, zero skips; affected batch report |
| Final evidence CLI | `python tools/check_frozen_product.py --validate .planning/phases/11-frozen-selection/11-product-evidence.json` returns `accepted: true` |

Full-suite results are reused against unchanged production inventory; the later test-harness-only collector correction was checked separately, without repeating either full suite. Skips are reported honestly, not counted as executed acceptance cases.

## Safety and cleanup

`11-product-runtime-audit.json` confirms no remaining owned probe/game PIDs, original config/desktop/autostart/screen-file hashes restored, original `Meta+Shift+E` binding, and restored live scale 1. Only the independent clone was entered or controlled; concurrent original-VM activity is not treated as something this run preserved globally.

Shared clipboard initially allowed cross-agent interference. It was disabled on the owned clone; deterministic public invalid PRIMARY `0` then exercised the OCR path without relying on an empty selection that KDE can refill. The independent public `river` test separately verified PRIMARY precedence. Private baseline contents were neither included in artifacts nor committed. Root must power the clone off before restoring its original bidirectional clipboard mode, avoiding a stale guest-to-host clipboard push.

## Limits

This is agent acceptance on the documented KDE clone and fullscreen Wesnoth main menu. Other games, relative-pointer-lock modes, second monitors and borderless remain outside this evidence. The underlying application was not suspended; only its displayed scene was retained. No human or Danila acceptance is claimed.
