---
phase: 05-app
gathered: 2026-10-26
status: ready-for-research
source: explicit --auto delegation and accepted repository requirements
---

# Phase 5 autonomous context

Production tray application, global trigger, selection/OCR and a useful native
Breeze translation popup. Phase4 platform evidence is accepted; no new capture
or window-positioning backend research is needed. No confirmation interview is
required under Denis's explicit --auto direction.

## Decisions

- D-01: Preserve current CLI and stdlib-only core imports. Add lazy GUI entry
  actions to python -m lookup; keep one production session-bus owner with a small
  fixed Trigger interface and DBus-only warm client. Reuse validated session,
  capture, geometry and owned kdotool commands rather than import spike tooling.
- D-02: A new admissible bounded primary selection takes priority. Keep its
  previous consumed identity only in memory. The same unchanged selection next
  time falls through to OCR; no selection resets freshness. Define short text
  explicitly from existing classifier/online input bounds, never clipboard writes
  or history alterations. Preserve raw context separately from normalized key.
- D-03: Each trigger gets a monotonically increasing request identity. Newer
  triggers supersede earlier work; explicit dismissal invalidates presentation
  and pending history writes. One serial worker owns dictionary/SQLite resources
  and coalesces queued requests to the newest. Qt stays responsive. No QThread
  termination, unsafe shared SQLite connection or duplicate search-count write.
- D-04: Call existing translation APIs without speculative history persistence;
  commit one accepted word/phrase event only after checking its current identity
  under a short shared guard. Sentence lookups do not create word history.
  Existing safe translation caching may remain. Stale results never replace or
  reopen the card, and stale delayed network replies never increment history.
  Preserve existing valid-lookup/history semantics and show save failures honestly.
- D-05: Native Breeze popup, system font/palette/icons, Russian copy. Word and
  optional transcription/lemma, POS senses, ordered dictionary articles, original
  context/translation and confirmed count. No invented metadata. Bounded vertical
  scrolling; plain selectable text prevents article HTML/images/file access.
- D-06: Reuse Phase4 pointer-adjacent available-monitor clamping, actual KWin
  geometry and active UUID focus route. Escape, outside click/focus loss and a
  finite inactivity timeout dismiss. Loading/results/errors respect the same
  generation. Choose a default timeout now, persist settings in Phase7.
- D-07: Tray has Words, Review, Settings and Quit in Russian; future Phase6/7
  surfaces have explicit disabled actions until implemented, not fabricated
  workflows. Keep the menu/action integration points small. Quit closes worker,
  dictionaries, DBus ownership and Qt resources cleanly. No arbitrary IPC commands.
- D-08: Every trigger visibly shows loading then result or fixed, specific
  Russian errors. Distinguish not found, no network/blocked provider, missing
  package, unavailable capture/cursor and failed save. Offline articles remain
  useful if context translation fails. Preserve no private diagnostic output.
- D-09: Wire the unique owned production desktop trigger for real VM tests.
  Keep installation/autostart/settings/PKGBUILD work in Phase7. Never steal an
  unrelated shortcut, overwrite unrelated desktop entries or change KWin policy.
  Normal session unlock is VM harness tooling only, never production behavior.
- D-10: Verify production integration in the existing VM with controlled public
  content and throwaway config/dictionaries/DB. Actual primary selection, physical
  hotkey, warm/cold owner, dismissal, light/dark, four scales and repeated triggers
  need observed evidence. Delayed older response and close-while-pending require
  deterministic tests proving no stale card or DB write. Screenshots used for UI
  inspection contain only owned fixtures and are removed after bounded review.

## Mandatory research context

Read docs/lookupper/linux-requirements.md and corresponding evidence.md claims
before planning. Separate observed original behavior from project decisions.
V1 remains unchanged. Phase4 choices are kdotool + ScreenShot2 UnixFD; actual
capture median 82.1ms, four-scale probe/capture/OCR median 396.7ms. Translation
and card rendering still need end-to-end measurement, not inferred performance.

## Open design details delegated to agents

Select the smallest thread/controller seam supporting cancellation and one
history write; inspect existing Result/Article/store contracts first. Specify
popup sizing, spacing, default timeout and GUI error states in UI-SPEC before
task planning. Avoid framework scaffolding or implementing Phase6/7 prematurely.
