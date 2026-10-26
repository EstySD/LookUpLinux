---
phase: 4
slug: vm
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-10-25
---

# Phase 4 — Validation Strategy

Execution evidence is recorded in 04-GATE-RESULTS.json, 04-VM-RESULTS.md and
04-REVIEW-FIX.md; the portable and live checks below have been exercised.

## Infrastructure

Existing stdlib unittest; proposed quick command python -m unittest
tests.test_platform. Full regression: python -m unittest, py -3.12 -m unittest,
target python3 -m unittest. Real VM checks use a uniquely named spike service,
window and desktop entry, public controlled test text, and bounded harness.

## Requirement / Success Criterion Map

| Contract | Portable tests | Actual VM gate |
|---|---|---|
| TRIG-01 / SC1 | Single-instance decision, bounded IPC, command construction | New desktop entry/cache refresh; repeated trigger same PID, cold start one owner; real Meta+Shift+D separate from DBus invokeShortcut; relogin/conflict observed |
| CAPT-01 / SC2 | Cursor parser, monitor selection, pixel ratios at1/1.25/1.5/2 and negative origins | Public word recognized from actual current-monitor capture at four scales; second monitor if exposed |
| SC3 placement | Clamp each edge, monitor offset, oversized popup | Compositor geometry matches intended pointer-adjacent bounded position |
| SC3 focus/events | Separate Escape and deactivate handlers | Actual active-window UUID/isActive; distinguish event reasons |
| SC3 tray | Qt icon/menu lifetime | Watcher registration plus visible/menu interaction evidence |
| SC4 primary | Empty, no offer, oversized bytes,500ms timeout, child cleanup | Read known public selection or bounded no-offer; preserve unrelated history |
| Capture/privacy | Raw metadata/length bounds, partial pipe, timeout, FD/temp finally cleanup | Spectacle timing first; FD candidate if gate requires; no retained private screenshots or clipboard copy |

## Measured Research Baseline

## Executable Task / Source Coverage

| Task | Required coverage | Automated command |
|---|---|---|
| 04-01/T1 | CAPT-01; D-01/D-02/D-03/D-07; geometry/parser/primary/owned window boundary | python -m unittest tests.test_platform tests.test_core_imports |
| 04-01/T2 | CAPT-01; D-02/D-04; raw FD, finite cleanup, compatible memory OCR | python -m unittest tests.test_platform tests.test_ocr_image tests.test_core_imports |
| 04-02/T1 | TRIG-01/CAPT-01; D-01/D-03/D-04/D-05; one owner/worker and timed pipeline | python -m unittest tests.test_vm_spike tests.test_platform |
| 04-02/T2 | TRIG-01; D-03/D-05/D-06; owned shortcut, popup events, token/tray lifetimes | python -m unittest tests.test_vm_spike tests.test_platform tests.test_core_imports |
| 04-03/T1 | All four SCs; D-01..D-08; host handshake, observed gate decisions and tested rollback | python -m unittest tests.test_vm_spike tests.test_platform |
| 04-03/T2 | TRIG-01/CAPT-01; all four actual SCs, measured gates and PROJECT decisions | Windows host: python tools/check_vm_spike.py --output .planning/phases/04-vm/04-GATE-RESULTS.json; target actions driven over SSH |

Multi-source audit: GOAL/SC1..SC4, REQ TRIG-01/CAPT-01, every CONTEXT
D-01..D-08, and RESEARCH constraints are covered by the task map. In
particular, raw QImage format/stride/exact bytes/concurrent pipe drain are
04-01/T2; actual physical keys, focus and tray action evidence are 04-03/T2;
both platform decisions and restoration are 04-03/T1/T2. Phase5 production
UI/daemon and other explicitly deferred features remain excluded. No required
source item is missing. Sequential waves 1/2/3 respect shared adapter/spike
contracts. Test files are created by their owning task before verification.

## Historical Research Baseline

- kdotool0.3.0 getmouselocation works with KDE_SESSION_VERSION=6.
- Current output: Virtual-1,1920x1080,origin0,0,scale1; only one monitor exposed.
- ScreenShot2 version5 exposes FD-based CaptureScreen/CaptureArea; UnixFD
  transport available; safe nonexistent-screen call returned InvalidScreen.
- PyQt options must be nonempty for tested automatic map marshalling.
- StatusNotifier host registered, but no new icon/menu proved yet.
- Session currently LOCKED: ScreenSaver.GetActive=true. Primary list-types
  returns x-kde-lockscreen. No clipboard content was read or changed.

These are capability probes, not passes of the four end-to-end criteria.

## Execution and Cleanup Contract

Discover current session values. Recheck lock before desktop tests. Back up
only affected spike-owned desktop/shortcut entries; check availability before
binding and never steal unrelated shortcuts. Save affected display JSON fields
before scale tests; restore in finally and compare after. No global focus,
screen-capture permission or lock policy changes. Do not whitelist system
Python for old KWin authorization recipes. Keep captured public test frames
in memory where possible; private temporary spike files must be removed on
success/failure/timeout and never enter repository artifacts.

Record probe/capture/OCR timing, chosen cursor/window and capture gate decisions,
actual event/PID outcomes, restored settings and any unavailable second display.
Update PROJECT.md decisions before Phase5. Acceptance is agent judgment from
evidence under --auto, never mislabeled human testing.

## Sign-Off

- [x] Pure geometry/parsing/failure tests exist and pass.
- [x] kdotool versus fallback gate resolved by observed window operations.
- [x] Spectacle versus ScreenShot2 gate resolved by measurement.
- [x] Actual shortcut/same-process/cold-start/conflict behavior recorded.
- [x] Four-scale capture/OCR checks pass; optional hardware classified.
- [x] Popup focus/placement/Escape/focus-loss and tray interaction proven.
- [x] Primary read is bounded; screenshot/FD/child/settings cleanup verified.
- [x] Full host/VM suites and security check pass.
- [x] Decisions persisted and agent acceptance recorded.

Approval: agent acceptance authorized by --auto; all four final JSON gates
and all four restoration flags are true. No human test is claimed.
