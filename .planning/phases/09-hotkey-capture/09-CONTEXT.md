---
phase: 09-hotkey-capture
status: ready
source: autonomous decisions under explicit gsd next --auto
created: 2026-11-02
---

# Phase 9: Hotkey capture and speed

## Scope

CAPT-06, CAPT-07, PERF-02 from ROADMAP.md. Preserve v1.0 data, PRIMARY selection behavior, cancellation and screenshot privacy. Existing uncommitted OCR changes belong to the user and must remain intact.

## Decisions selected in auto mode

- Capture semantics: hotkey over A followed by movement to B must resolve A; changing scenes must not replace the retained frame. A test of immutable bytes alone does not establish real hotkey correctness.
- Measurement: keep cold and warm samples separate, measure hotkey-to-capture and first useful result independently, retain median/p95 and failures. Fix numeric budgets after measuring baseline and before optimizing. Do not invent latency promises from historical results.
- Optimization: remove measured delays at the shared capture/dispatch boundary, preserve hide-before-capture and supersession. No new OCR engine or popup redesign in this phase.
- Environment: use only the independent owned lookup-gsd-07 clone (UUID cf207909-94b5-4b49-8bd8-ccff973c1dc8, disk 2712d710-daaa-449c-843d-d570091127bc, pinned SSH2227). Preserve its existing profiles and return it powered off. Never control or access the original VM guest.
- Acceptance: agent testing is distinct from human acceptance. If target capture or real input cannot be exercised, retain the exact blocker and do not advance or accept these requirements.

## Canonical references

- .planning/v1.1-CONTEXT.md
- .planning/REQUIREMENTS.md
- .planning/ROADMAP.md
- .planning/phases/08-vm/08-CONTEXT.md (owned environment and evidence constraints)
- docs/lookupper/architecture.md
- docs/lookupper/linux-requirements.md
- docs/lookupper/evidence.md
- lookup/gui.py, lookup/app.py, lookup/capture.py, lookup/platform.py, lookup/timing.py

## Deferred

Popup configuration, frozen selection layer, Yomitan, discoverability and packaging remain phases 10–15. No user questions required to select routine defaults.
