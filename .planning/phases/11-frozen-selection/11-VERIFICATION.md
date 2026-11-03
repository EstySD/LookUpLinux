---
phase: 11-frozen-selection
status: passed
score: 9/9 must-haves verified
overrides_applied: 0
verified_at: 2026-11-03
implementation_verification: passed_native_agent
independent_phase_verification: passed_agent
human_acceptance: not_performed
requirements: [CAPT-08, TRIG-05, TRIG-06]
---

# Phase 11 — Native product verification evidence

**Phase Goal:** User selects words on a retained scene without sending pointer movements to the underlying application and regains control afterward.

**Independent acceptance:** Passed by the agent on 2026-11-03. Initial goal-backward verification of the provisional evidence report; there was no prior gaps frontmatter. All three roadmap criteria and additional plan truths are verified below. Overlapping plan truths are merged into the roadmap criteria; none are subtracted. No human acceptance is claimed.

Plan 03 executed the actual product through `gui.run`. Product source hashes, including the user's unchanged working-tree OCR edits, are in `11-product-evidence.json`; root independently matched all 30 native inventory hashes and all five host evidence hashes against the working tree. Acceptance is bound to that inventory (HEAD at report reconciliation: `c2b689d93e6ae57bc4d5d841cde95ef4fb36b865`), not to HEAD alone.

## Observable truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | A translucent layer supports selecting words from one captured scene while the underlying scene changes. | VERIFIED | `selection_gui.py:114` paints retained pixels then a 20% tint; fixture session 9 resolves three words from one frame while PID 997 ticks advance 2996 to 3076. |
| 2 | Real hover text remains available on the captured scene; pointer movements on the layer do not reach the underlying application. | VERIFIED | Captured tooltip word `captured` resolves usefully; source pointer count remains 6 during seven layer interactions, then reaches 10 after exit. Native edge/corner input included. |
| 3 | Esc, close, repeated invocation and error return control, including a real fullscreen application. | VERIFIED | All seven fullscreen exit cases below close actual product surfaces and restore source counters within the same PID per case. Includes timeout, external focus and process termination. |
| 4 | One OCR invocation retains exactly one frame; later points require neither recapture nor another PRIMARY read. | VERIFIED | `app.py:330` reuses `replace(self._scene.source,point=...)`; only initial branch calls freeze. Fixture records stable session/frame and increasing request IDs. |
| 5 | Fresh valid PRIMARY keeps precedence and does not create a scene. | VERIFIED | `Source.freeze` returns primary before capture; scene creation requires OCR. Native public `river` run records normal primary popup without a scene. |
| 6 | Selected results use existing lookup, history, enrichment and generation rules. | VERIFIED | `app.py:367` onward converges on the sole ready/upsert/enrich path with current-generation checks; app regressions and native card save exercise it. |
| 7 | Close, reload and shutdown release retained frame ownership and invalidate queued/late work. | VERIFIED | `app.py:215` close clears scene/pending and increments generation; reload/stop do likewise. `gui.py:692` releases image and surfaces, clears pending UI state. Lifecycle regressions cover stale work. |
| 8 | Useful-first popup, preferences, cards and request-generation behavior work inside selection. | VERIFIED | `gui.py:744` begins new selection generations; ready/context use existing popup and binding paths. Native card save, usable internal focus/no-hit, and GUI/settings regressions pass. |
| 9 | Host/target regressions and evidence distinguish product acceptance, feasibility, untested variants and human feedback. | VERIFIED | Matching inventory, raw per-case provenance, suite outputs, historical failures, affected timeout rerun and limits are retained separately. Native acceptance is explicitly agent-only. |

**Score:** 9/9 merged truths verified. No FAILED or UNCERTAIN must-have remains.

## Required artifacts and wiring

| Artifact | Substantive behavior and wiring | Status |
|---|---|---|
| `lookup/app.py` | Immutable Scene, bounded capture, selection queue, shared lookup/store flow; called by Owner. | VERIFIED |
| `lookup/selection_gui.py` | Opaque retained painting, logical coordinates, consumed pointer events and release; lazily instantiated by Owner. | VERIFIED |
| `lookup/gui.py` | Normal hotkey to enqueue_scene; selected signal to select_scene; all teardown to close_scene; existing learning action retained. | VERIFIED |
| `lookup/platform.py` | PID-conjunctive ownership check precedes window actions; exact conjunctive popup title/PID query in GUI. Native foreign-window rejection confirmed. | VERIFIED |
| `tests/test_app.py`, `tests/test_selection_gui.py`, `tests/test_app_gui.py` | Real assertions cover frame/generation/lifecycle, paint/input/coordinates, focus/settings/cards; included in recorded discovery runs. | VERIFIED |
| `tools/check_frozen_product.py`, `tests/test_frozen_product.py` | Probe invokes actual gui.run, reuses fixture/SDL technique from check_frozen_selection; evidence validator rejects contradictory claims and is CLI reachable. Four validator tests pass. | VERIFIED |
| `11-product-evidence.json`, this report | Inventory, actual source/session/frame counters, provenance, regressions and acceptance are linked. | VERIFIED |

## Data-flow trace (Level 4)

| Rendered data | Upstream source | Result |
|---|---|---|
| Layer image and word outline | HotkeySnapshot to Source.freeze to Scene/Capture to decoded QImage; Source.resolve OCR selection box to Event to set_selection | FLOWING: retained PNG and actual OCR box, not an empty/static prop. |
| Popup word/translation/context and card pair | Retained source point to recognize_image/choose_query to existing lookup/dictionary/store to ready/context to popup and displayed-result binding | FLOWING: three useful native translations and real persisted card. |

## Requirements coverage

| Requirement | Source plans | Status | Evidence |
|---|---|---|---|
| CAPT-08 | 11-01, 11-02, 11-03 | SATISFIED | Truths 1, 4, 6 and same-frame product fixture. |
| TRIG-05 | 11-01, 11-02, 11-03 | SATISFIED | Truth 2, captured hover and source-side input counters. |
| TRIG-06 | 11-01, 11-02, 11-03 | SATISFIED | Truths 3, 7 and seven native fullscreen exits. |

No orphaned Phase 11 requirement IDs found. Requirement/roadmap checkboxes are left to the orchestrator.

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

Final cleanup supersedes the pre-cleanup instruction above and the old running-clone note in product evidence: `11-root-cleanup.json` confirms only owned clone `cf207909-94b5-4b49-8bd8-ccff973c1dc8` was gracefully powered off before restoring bidirectional clipboard mode. Every recorded cleanup check is true; original VM not controlled.

## Behavioral checks and adversarial review

Recorded commands: full discovery `python -m unittest discover -s tests -q` (host and target); validator `python -m unittest tests.test_frozen_product -q`; evidence CLI listed above. These valid completed batch results were reused, with no suite/server/VM operation repeated by this verifier. Root independently reran the CLI and checked current inventory hashes.

Disconfirmation checked recapture behind a stable UI (actual source branch/frame trace), source pointer leakage (source counters), and closure without an active layer (raw before/during session evidence). The initial inactive ownership diagnostic and failed timeout collector are not accepted proof; their affected reruns supply the missing evidence. A passing validator alone does not prove runtime behavior; native records and independent inventory checks provide that proof.

Anti-pattern scan of app/gui/selection/platform/product probe found no TODO/FIXME/placeholder/NotImplemented implementation. `11-CODE-REVIEW.md` is clean through `a3d0c50`; three historical blockers were fixed, regressed and followed by native evidence on the corrected inventory. No outstanding BLOCKER or WARNING within the phase contract was established.

## Human verification required

None remains as a Phase 11 acceptance gate under the user's autonomous agent-acceptance instruction. Recorded native visual/input/focus checks are agent tests; personal visual preference and human feedback remain unclaimed.

## Gaps summary

No blocking goal gap remains. All nine merged truths, all three requirements and final cleanup are verified. No override was used. Second-monitor and borderless behavior are explicitly Phase 14 criteria (CAPT-09/GAME-02), not failures silently deferred from this phase.

## Limits

This is agent acceptance on the documented KDE clone and fullscreen Wesnoth main menu. Other games, relative-pointer-lock modes, second monitors and borderless remain outside this evidence. The underlying application was not suspended; only its displayed scene was retained. No human or Danila acceptance is claimed.
