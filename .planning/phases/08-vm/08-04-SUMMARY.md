---
phase: 08-vm
plan: 04
subsystem: captured-game-validation
tags: [chocolate-doom, freedoom, wayland, relative-pointer, verification-gap]
requires:
  - phase: 08-03
    provides: First real fullscreen game and unchanged capture observers
provides:
  - Official locally built Chocolate Doom and actual fullscreen Freedoom MAP01 evidence
  - Actual Wayland pointer-lock and physical camera/navigation observations
  - Retained failed captured-word attempts and strict incomplete requirement report
affects: [08-05, GAME-01-gap-closure]
tech-stack:
  added: [test-only Chocolate Doom 3.1.1, official Freedoom 0.13.0]
  patterns: [transparent SDL renderer observation, Wayland lock-event evidence, fail-closed game acceptance]
key-files:
  modified:
    - tools/check_games.py
    - tests/test_check_games.py
  created:
    - .planning/phases/08-vm/08-doom-final-report.json
    - .planning/phases/08-vm/08-doom-runtime-evidence.json
    - .planning/phases/08-vm/08-doom-cleanup-final.json
key-decisions:
  - Missing useful captured-game OCR proof keeps GAME-01 open despite actual grab and camera movement.
  - Official asset-list and archive inspection establish checksum absence; actual byte hashes remain recorded.
  - Bounded failed font and navigation attempts are retained without substituting another ungrabbed game.
requirements-completed: []
duration: approximately 22min
completed: 2026-10-30
---

# Phase 8 Plan 04: Captured-Mouse Game Attempt Summary

**Actual fullscreen Freedoom ran with verified relative pointer lock, but unchanged production OCR could not select the targeted game words; mandatory useful captured-game acceptance remains failed.**

Implementation: `tools/check_games.py` and `tests/test_check_games.py`.
Task commits: d05177a (RED captured-proof rejection), fc4c277 (GREEN native observer and strict captured contract).

## Validation Results

`08-doom-final-report.json` records **passed:false, game01_complete:false, zero accepted routes**. Its gates preserve actual acquisition/fullscreen/renderer/grab/input/fresh-capture observations while selected-word, useful-overlay, repeated-useful and return-after-useful gates remain false. This is an agent-recorded verification gap, not human acceptance or a completed GAME-01 requirement.

| Actual attempt | Result |
| --- | --- |
| MAP01, real quit confirmation, locked cursor at 670,440 | Physical configured chord produced a fresh authorized ScreenShot2 capture. Request1 reached production stage6 in830.013ms without a Query. No useful article accepted. |
| MAP01 HEALTH HUD label, locked cursor at312,778 | Physical chord produced another fresh source. Request3 reached stage6 in591.642ms without a Query. No useful article accepted. |
| Supported gamma / exact4x / integer / nearest settings | Actual screenshots retained; decorative red prompt remained unreadable to diagnostic OCR. No substituted text or images. |
| Actual EXIT fallback | Read-only official MAP01 metadata located EXITSGN2. Noclip movement hit authentic vanilla `R_FindPlane: no more visplanes`; rejected screenshot retained. A single bounded normal corridor trial opened the door and traversed rooms, but did not reach the EXIT sign. |

The exact unchanged production preprocessing/PSM diagnostic is retained for both physical sources. HEALTH produced no matching token; ARMOR was misread with confidence18.9. The observer stopped promptly on matching pid/run/request production stage6. No OCR, capture image, query or result was overridden to turn these failures into success.

Actual Wayland journal events show `lock_pointer`, `locked`, focus-related unlock/destroy and subsequent locking. Physical desktop-toggle/preposition/refocus preserved the observed cursor coordinate under lock. `08-doom-runtime-evidence.json` identifies the actual process and renderer; camera and movement PNGs show genuine subsequent physical gameplay changes. These observations prove relative control exists, **not** that it returned after a successful useful lookup.

Fresh focused verification: **82 tests passed**. Host discovery: **742 tests passed, 8 host platform/opt-in skips, 30.291s, Python exit0**. Target with `LOOKUP_TEST_OCR=1` and real system Mueller: **742 tests passed, zero skips, 41.119s, Python exit0**. Raw logs are `08-doom-host-tests.txt` and `08-doom-target-tests.txt`. The target retains the previously diagnosed forced-deadline multiprocessing SemLock teardown traceback; positive assertions and the actual process exit passed. No historical suite was promoted as this unit's result.

## Acquisition and Actual Environment

Official tagged Chocolate Doom3.1.1 source and Freedoom0.13.0 zip were fetched over HTTPS. Actual source/archive/WAD/executable hashes are in `08-doom-build-hashes.txt` and the final report. The official release API asset list and zip contain no CHECKSUM; the proposed release CHECKSUM URL returned404. No upstream checksum verification is falsely claimed. Public official provenance and actual local hashes are recorded explicitly, without invented expected values.

Chocolate was built in the owned test build directory with existing CMake/compiler/SDL2, disabling optional SDL2_net and SDL2_mixer. No production dependency or paid IWAD was introduced. Actual renderer observation reports **software, flags9, Wayland** from the running process. The small test-only SDL wrapper invokes original SDL_CreateRenderer exactly once, returns its original pointer unchanged and records actual SDL_GetRendererInfo. The official game executable and WAD bytes were not modified. WAYLAND_DEBUG was scoped only to the owned game service. Read-only original production capture/query observation remained unchanged.

The game was observed fullscreen at1280×800 in the owned clone with3D disabled; no exclusive scanout claim is made. Actual gameplay, door traversal, camera rotation and automap MAP01 were observed rather than inferring success from a CLI fullscreen flag. All config/cache/saves belonged to the isolated test profile. Source production remained unchanged from plan02.

## Deviations and Remaining Gap

- **[Rule 3 - Environment]** No Arch package was assumed. Legitimate source was built locally as planned. The nonexistent CHECKSUM was replaced by honest published-asset inspection and byte-hash evidence, consistent with verifying checksums where supplied.
- **[Rule 1 - Harness]** The captured oracle extends existing source/input correlation with recent actual protocol-lock evidence and separate physical relative-camera and movement observations. Tests reject missing grab, stale grab, changed process identity, absent event digest, false camera/movement changes, absolute-pointer substitution and missing provenance evidence.
- **Mandatory verification gap:** Two useful repeated captured-game lookups and return from their overlays were not achieved. GAME-01 remains open. Another ungrabbed/menu-only game was not substituted. A subsequent focused gap plan must supply actual useful captured-game proof; this summary does not waive it.

## Cleanup

Owned game/service and instrumented lookup exited; one-shot observers completed. Keys and modifiers were released. PRIMARY remained absent and unchanged. Clipboard contents were not written in this unit; Klipper history was not cleared. The accidental empty arch config directory from an unsupported help probe was verified empty and removed with nonrecursive rmdir. Isolated test profiles/builds/evidence remain for reproducibility; no personal game profile was modified.

Guest shutdown completed and both clone and original are verified powered off. Only after clone poweroff, its prior bidirectional clipboard and prior enabled3D setting were restored; the tested environment remains explicitly3D-off. `08-doom-cleanup-final.json` records final settings and limits. No original VM boot, revert or write occurred; the historical phase07 original-disk exception remains unchanged. Borderless and second output remain unverified.

## TDD Gate Compliance

RED d05177a precedes GREEN fc4c277. Twelve game contract tests now include positive structural proof plus adversarial captured-route rejection. No fabricated native success or production stub was introduced.

## Self-Check: PASSED

Implementation files, both task commits, final report, actual source/frame/control records and fresh host/target logs exist. Native acceptance remains explicitly incomplete. Parent owns global state and requirement transitions.
