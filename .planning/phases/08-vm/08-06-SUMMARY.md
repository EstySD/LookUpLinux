---
phase: 08-vm
plan: 06
subsystem: verification
tags:
  - assaultcube
  - wayland
  - captured-mouse
  - frozen-source
requires:
  - phase: 08-05
    provides: Verified package and retained owned profiles
provides:
  - Pinned actual GL-context/window/grab evidence and world-only control guards
  - Bounded native attempts, positive frozen-source PSM11 fallback evidence, and observed cleanup
affects:
  - 08-07
  - bounded OCR fallback gap closure
tech-stack:
  added: []
  patterns:
    - Original calls and returned source objects remain unchanged
    - Clone-only guarded controls with external original lifecycle policy
key-files:
  created:
    - .planning/phases/08-vm/.gitattributes
    - .planning/phases/08-vm/08-assaultcube-final-report.json
    - .planning/phases/08-vm/08-06-artifact-manifest.json
    - .planning/phases/08-vm/08-06-recovery-frozen-diagnostic.json
  modified:
    - tools/check_games.py
    - tests/test_check_games.py
key-decisions:
  - Keep the two-route requirement false; never combine routes across dead game instances
  - Preserve all failures, unchanged production defaults, and the single supported shipped-font alternative
  - Respect USER_KEEP_RUNNING through observed clone-only action scope, without original state equality
requirements-completed: []
duration: 309min takeover elapsed including quota interruption and expired-session recovery
completed: 2026-10-31
status: gap_open
---

# Phase 8 Plan 06: AssaultCube Captured-Game Evidence Summary

`tools/check_games.py` and `tests/test_check_games.py` validate actual AssaultCube GL/window/grab bindings and reject HUD-only camera changes. Native acquisition and cleanup are recorded; the mandatory second useful changed-source route remains missing.

## Task Results and Commits

| Task | Result | Commits |
| --- | --- | --- |
| 1: bounded useful/grab pilot | Actual useful `name` lookup with genuine lock; unconditional cleanup path established | ff023d2 |
| 2: explicit candidate schema | Exact official RC1 provenance, original-call GL observation, same SDL window/context/grab, world ROI and separate physical pulse checks | 27c1657, dc1fe5e, ebe25e7, 3d1419f, 749076b |
| 3: two routes and cleanup | Cleanup observed complete; only one complete route in final instance, so native acceptance remains false | 874691a |

The TDD test commit precedes its feature commit. Takeover did not repeat those implementation tasks or modify production modules.

## Actual Native Outcome

- Official Linux RC1 archive: 52,071,427 bytes, SHA256 9b3118e7929253f0114fa06cad8310faab646d177b4660406011152f34086b55. Its private game directory and licenses remain retained.
- Cached package 7aa3cf123457c753fa572efbd58062f81cd1e4f4fc2387fe4a7505665ab480f3 was reinstalled with observed absence beforehand. All 28 installed Python application members exactly match revision 5d04a4c. Earlier 32-member comparison includes other archive members; this result does not inflate the application count.
- Actual software renderer is llvmpipe/Mesa, SDL Wayland, fullscreen 1280x800. GL context is original/current and bound to the same SDL window/pointer used by the grab; strict preflight precedes queries.
- Startup mouse suppression was investigated in official source. Eight separated small alternating physical pulses serve only as calibration. Accepted controls still require independent W input and the existing measured two +60 relative pulses, with unchanged world ROI threshold.
- The single planned readability alternative used the supported `menufont score mono` command. Shipped configuration and font atlas match the official archive byte hashes. Default production PSM6 and confidence threshold50 remain unchanged.
- Both pre-query mono-font frozen poses selected `name` above91% confidence. A first mono instance then lost its second observation to the observer's unchanged5s Tesseract timeout; no timed overlay frame was saved. That failure and expired controller86089 remain unaccepted history.
- One authorized fresh same-font recovery instance, PID1041/start3423, completed route1: selected `name`, useful actual overlay, physical Escape, latency6244.616646ms. Separate W changed134992 world pixels; measured camera changed138225. Both use distinct actual frames and kernel inputs.
- Recovery route2 emitted actual production stage6 and no selected Query. The final strict report is **passed:false, reason:routes**, with one route against two required. No cross-process route mixing, threshold relaxation, new game, or new1500ms game claim occurred.

## Concrete Remaining Gap

Exact frozen Screenshot2 source SHA256 9cbc077f181e3c564d21e5d3ec88d68129630811972b12cc659558fc8723497e at point733,378 reproduces default PSM6 no selection. Supported PSM11 on the identical prepared bytes selects `name` at89.277435 confidence, rectangle716.5,374,34,8.5. Prepared SHA256 is44a19eeceee75ffacee6071b15e38c1c4773dc8dff5189d8be50c1a723c8a443 for both modes. No overlay obscures the genuine scoreboard heading; it lies inside the actual production crop.

This establishes a specific segmentation fallback case for a separate production plan. The live numeric stage6 trace does not preserve its exact exception reason, so this summary does not invent a live timeout cause. These read-only diagnostics are not native acceptance and did not change production or retrigger lookups.

## Cleanup and Policy

Final guarded controller46069 completed. Actual release commands returned successfully; tray exit/game quit and process checks left no owned children. Package removal exited0. Actual owned shortcut301989957 was cleared via its introspected action; readback and a physical former hotkey left owner:false and keys:[]. Unrelated shortcut sections and retained database/config hashes were preserved. Retained UID1002 profiles were not modified.

Clone UUID cf207909-94b5-4b49-8bd8-ccff973c1dc8 is OFF; prior3D ON and bidirectional clipboard were restored only while OFF. The original VM belongs to an external agent and was never controlled, entered, or inspected for disk contents. USER_KEEP_RUNNING has no original OFF or before/after equality gate. Current policy respect is derived from actual host action targets plus pinned2227/DMI-guarded guest/input audit, rather than an initialized empty list. The historical Phase07 unknown-actor disk exception remains unchanged.

The old compiled controller86089 did not hot-reload later guards. Its actual expired cleanup remains separate; only the final controller loaded the current common DMI guard from startup.

## Validation Results

- Fresh focused suite: 105 tests passed in5.823s after final artifact generation. No production source changed during takeover; full host/target suites belong to the subsequent gap closure and aggregate verification.
- Raw artifact hashes and sizes: 08-06-artifact-manifest.json. Prior rejected Doom, zero-world-change cameras, failed headings, observer timeout, and expired cleanup are retained.
- All273 raw manifest entries match Git index bytes. Scoped attributes preserve raw CRLF and other evidence bytes across checkout; approved plan and summary prose are outside this raw manifest. Metadata follow-up8d862f5 recognizes literal CRLF endings without rewriting measurements.
- Current adapters for review: 08-06-owned-input.ps1, 08-06-native-takeover.py, 08-06-takeover-controller.py; final aggregate builder is08-06-close-takeover.py. No shared VM helper was relaxed.
- No human acceptance, second output, borderless, hardware-GPU, or original byte-preservation claim. GAME-01 remains open and old candidate aggregate must not be accepted by plan07.

## Self-Check: PASSED

The listed source and raw report files exist; the six prior task commits exist; current reports recompute to mandatory candidate false and observed cleanup true. Unfinished native acceptance is explicit above.
