# Phase 3: OCR слова на готовых скриншотах — Context

Gathered: 2026-10-25. Status: Ready for planning.
Mode: autonomous; choices below are agent decisions authorized by Denis's
explicit --auto instruction, not answers attributed to a human interview.

<domain>
Offline recognition from a supplied image and point, bounded nearest-word
selection, source line, compound/hyphen support, and integration with the
existing dictionary/translation CLI. No desktop capture or global shortcuts
until Phase 4. Requirements CAPT-03 and CAPT-04; all four roadmap criteria.
</domain>

<decisions>
- D-01: Keep TSV parsing and geometric selection stdlib-only and independently
  testable without Qt, tesseract, a desktop or a VM. Image preparation may use
  lazily imported PyQt6, already in the target stack; no new pip dependency.
- D-02: Image point coordinates are physical pixels in the original image.
  Preserve/reverse crop and resize transforms explicitly. Monitor logical
  coordinates and offsets belong to Phase 4; cover geometry outside the VM.
- D-03: Use subprocess tesseract with English data, TSV stdout, finite timeout,
  fixed reason codes, no shell, no persisted screenshot or printed query/error
  details. Missing packages and invalid images receive actionable CLI errors.
- D-04: A word box hit wins; otherwise choose the nearest word only within
  a bounded neighborhood related to text height. Reject distant blank space,
  low confidence, icon/noise, non-Latin/digit garbage using normalization.
  Tune concrete thresholds against fixtures and lock them in behavioral tests.
- D-05: Preserve the selected line as context. Hyphens between nearby fragments
  join into one lexical unit; do not indiscriminately glue separate words.
  Adjacent two-word dictionary candidates (including break out over break)
  are tried before the standalone word. Avoid online calls and database writes
  for speculative candidates; persist just the chosen final query once.
- D-06: CLI python -m lookup --image PATH --at X,Y uses existing offline,
  no-save, output and exit-code conventions. No accepted word means no DB row
  and no network. LOOKUP_TIMING=1 exposes stage durations without query text.
- D-07: Build reproducible, versioned rendered-image fixtures in light/dark
  Breeze, scales 100/125/150/200%, small/large text, compound, hyphen, blank and
  icon cases. Record their origin honestly; synthetic fixtures do not count
  as live desktop captures. Use the accessible Arch VM to obtain representative
  real Qt/Breeze renders as needed. Compare PSM 6/11, enlargement and inversion
  against the same expected words/points; record chosen parameters and results.
- D-08: Acceptance is evidence-based and autonomous. Missing real MDX/DSL files
  remain the explicit Phase 8 follow-up from Phase 2, not an OCR blocker.
</decisions>

<canonical_refs>
- .planning/ROADMAP.md — Phase 3 goal and four success criteria.
- .planning/REQUIREMENTS.md — CAPT-03, CAPT-04, DATA-01/02 and privacy context.
- .planning/PROJECT.md — stack, target, privacy and scope.
- .planning/phases/02-offline-dicts-translate/02-VERIFICATION.md — accepted
  dictionary/translation baseline and remaining limits.
- lookup/__main__.py — CLI output, timing, error and persistence conventions.
- lookup/translate.py — lookup orchestration and classification.
- lookup/dicts.py — DictSet.find, Article and SearchResult.
- lookup/normalize.py — Latin token acceptance and normalized counting key.
- tests/_support.py — temporary paths and network guards.
</canonical_refs>

<code_context>
Existing readers and transport are stdlib-only, quiet and return fixed errors.
CLI owns printing and resource closure. Reuse DictSet.find for speculative
offline candidates, translate.lookup for the final query/context, and the
existing store for one final count. Tests use unittest, independent fixture
writers, subprocess CLI probes and optional real integration suites. VM is
VirtualBox arch-kde via ssh archvm, Python 3.14.8; tesseract already available.
</code_context>

<deferred>
Desktop screenshots, cursor acquisition, KWin positioning, shortcuts and tray
belong to Phases 4/5. Packaging and doctor belong to Phase 7. Do not expand
this phase into a desktop app or weaken the production roadmap scope.
</deferred>
