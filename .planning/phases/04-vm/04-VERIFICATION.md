---
phase: 04-vm
verified: 2026-10-26
status: passed
score: 9/9 must-haves verified
overrides_applied: 0
acceptance_source: independent agent verification under user --auto instruction
---

# Phase 4 — VM platform spike verification

**Goal:** In the existing VirtualBox Arch/KDE Wayland VM, prove shortcut wakeup
of a background process, actual cursor/monitor capture and OCR, popup placement/
focus and tray interaction; select working platform backends before Phase 5.

Initial goal-backward verification. Actual source, tests and precise VM JSON
were checked independently of SUMMARY claims. No VM commands were run by this
verifier and no human test is claimed.

## Observable truths

| # | Required truth | Status | Evidence |
|---|---|---|---|
| 1 | SC1/TRIG-01: physical Meta+Shift+D invokes the owned desktop command, wakes the existing process, cold-starts one owner, and registration/conflict behavior is known | VERIFIED | `desktop_text` generates absolute escaped Exec plus X-KDE-Shortcuts; target setup calls kbuildsycoca6 and checks binding availability. Host `keys` uses actual VBox scancodes, not a substitute DBus trigger. Raw observations show owner PID13605 at sequences1/2/3/4; physical cold key starts PID14375, sequence1. Another owned component reports binding unavailable. Registration works in the same session, without relogin. Atomic registerService plus loser forwarding supplies ownership. |
| 2 | SC2/CAPT-01: actual cursor over public text yields the captured-monitor word at 100/125/150/200%, with optional second-monitor outcome honest | VERIFIED | `pipeline` queries real cursor/outputs, captures the selected monitor, maps using actual pixel dimensions and invokes real recognize_image on PNG bytes. All four recorded scales identify Virtual-1,1920x1080 and english; cursor is within one logical pixel of the independent fixture glyph point. Only one output is exposed, explicitly recorded; no second-monitor measurement is claimed. |
| 3 | SC3: frameless popup is clamped near cursor with real compositor focus; Escape/deactivate and panel tray interaction are observable | VERIFIED | Popup uses FramelessWindowHint. Each scale records KWin geometry equal to intended target, matching active UUID, Qt active/visible and focus_ready. Independent audit confirms target lies within the corresponding monitor bounds. Escape count increases separately for each scale. Cold-owner focus loss records deactivate and hidden popup. Physical panel right-click/menu click produces tray-menu then tray-action with tray visible/available. |
| 4 | SC4: primary read is bounded near0.5s and probe/capture/OCR stages are measured | VERIFIED | read_primary delegates to bounded run(timeout=.5,limit65536); tests cover timeout/invalid UTF-8. Actual offer read takes3.942ms; evidence contains only offered/elapsed, not text. Each scale records positive finite probe/capture/OCR/total timings. |
| 5 | Pure geometry preserves fractional scaling, actual capture ratios and negative origins | VERIFIED | Monitor/monitor_at/image_point validate geometry and map using actual image width/height, not an assumed nominal scale. Portable tests cover1/1.25/1.5/2, negative monitor origins, nonmatching pixel ratios and popup edge clamping. |
| 6 | Session probes/capture/IPC terminate within finite bounds and validate ownership/layout | VERIFIED | platform.run caps retained stdout and lifetime, kills owned process groups/tree and avoids buffered-close deadlock. ScreenShot2 drains capped FD concurrently with bounded DBus/read waits and finally closure; raw layout/length/channel checks detach QImage memory. Owned UUID/PID checks precede window operations; token length/NUL checks and one coalescing worker bound spike IPC. Focused regressions pass. |
| 7 | Captured bytes reach OCR without retained private screenshots, arbitrary OCR/selection/token logging or production data writes | VERIFIED | ScreenShot2 raw data -> in-memory PNG -> QBuffer OCR input is substantive and wired. Spectacle's measured alternative uses a scoped TemporaryDirectory and cleanup. Spike never opens translation/store; diagnostic word is english only after actual recognition matches the controlled fixture. Tokens are removed from child environments and omitted from status. Primary evidence omits contents. |
| 8 | Owned display/desktop/process/shortcut resources are restored, including setup/key-release failures | VERIFIED | Snapshot precedes mutation, fresh run ID and PID/start-time/UID/cmdline constrain cleanup; desktop bytes/display fields/binding and stopped processes are compared. Host separately guards final key release and still attempts restore/evidence writing. accepted rejects restoration/key-release errors and requires all four restoration flags. Final JSON has all four true; injected failure regressions pass. |
| 9 | Both roadmap backend decisions are measured and persisted before Phase5 | VERIFIED | Five real samples per backend all recognize english: Spectacle median370.146ms, ScreenShot2 median82.126ms. PROJECT Key Decisions records kdotool cursor/move/activate and ScreenShot2 UnixFD capture, plus KDE theme/QCoreApplication client choices. No KWin fallback script was needed, loaded or installed because observed kdotool operations passed. |

**Score:** 9/9. No overrides or unresolved must-have warnings/blockers.

## Artifact and wiring checks

| Artifact | Existence/substance/wiring |
|---|---|
| lookup/platform.py | Real bounded process/session/output/cursor/primary probes and geometry/owned-window functions; used by capture, spike and harness. |
| lookup/capture.py | Real Spectacle and QtDBus UnixFD ScreenShot2 transports, raw metadata/length/channel validation and detached pixels; called with the selected Monitor. |
| lookup/ocr.py | Existing accepted pipeline now accepts bounded encoded bytes through QBuffer as well as file input; equivalence regression passes. |
| tools/vm_spike.py | Real atomic DBus owner/client, worker, public fixture, frameless popup and retained tray/menu. Cursor/capture/OCR results flow into status and actual popup geometry; no hardcoded success replaces recognition. |
| tools/lookup-vm-spike.desktop.in | Deliberate registration template; actual runtime entry is resolved by desktop_text into absolute escaped Python/script paths and installed by owned setup. |
| tools/check_vm_spike.py | Real host physical input and bounded target observation/rollback, registration/conflict/sample/scale/focus/tray/primary actions. Gate acceptance is derived from returned state and cleanup flags. |
| tests/test_platform.py, tests/test_vm_spike.py | Portable geometry, process/FD/raw-memory, privacy/ownership, setup/key-release/restoration failures, normal owned-session unlock and bounded relative-input fallback regressions. |
| 04-GATE-RESULTS.json | Exact four-scale PID/geometry/UUID/event/timing records, ten backend samples, primary presence/timing, all four SCs and four restore flags; independently audited. |
| 04-VM-RESULTS.md and PROJECT.md decisions | Reproduction command, actual input route, measurements, decisions and explicit single-output/spike limits agree with source and raw JSON. |

The relevant data path was traced through actual calls:
physical VBox key -> KDE desktop command -> warm Trigger/cold atomic owner ->
cursor and monitor probes -> selected backend pixels -> memory OCR -> observed
result -> frameless popup -> owned KWin move/raise/activate -> compositor/Qt
status. Tray evidence arises from actual QMenu signals after physical input,
not manual insertion of acceptance events. Snapshot restore follows the owned
resource identities even when setup response or key release fails.

## Fresh verifier evidence

- `python -m unittest tests.test_platform tests.test_vm_spike tests.test_ocr_image tests.test_core_imports`:
  **32 tests in1.493s, OK, no skips**.
- Independent JSON audit recalculated same/cold PIDs, four increasing trigger
  sequences, cursor proximity, actual scale geometry/clamping, active UUID/Qt
  agreement, increasing Escape count, separate deactivate, real tray events,
  finite stage timings, ten matching backend samples and four restoration
  flags. All assertions passed; required_remaining is empty and no error,
  restoration_error or key_release_error exists.
- Final source suite results supplied as direct execution evidence by the
  orchestrator: **528 tests pass on Windows3.14, Windows3.12 and Arch**, with
  7/7/3 pre-existing skips. The verifier did not rerun those full suites or
  mutate VM state.
- Independent security audit closes14/14 authored threats at ASVS1; code review
  CR-01/02/03 has actual remediation and passing regressions, not only status
  changes in documentation.

## Requirement coverage

| Requirement | Plans | Result | Proof |
|---|---|---|---|
| TRIG-01 | 04-01/02/03 | SATISFIED | Real physical shortcut, same-owner and cold-owner PID evidence; conflict/no-relogin behavior and registration source. |
| CAPT-01 | 04-01/02/03 | SATISFIED | Real cursor and selected-monitor capture/OCR at all four scales; mapping and negative-origin tests. |

No additional requirement is mapped exclusively to Phase4. Pending phase plan/
requirement checkboxes are orchestrator transition bookkeeping, not missing
implementation.

## Scope and honest limits

This verifies the required platform spike in Denis's existing VirtualBox VM,
not the Phase5 production translation daemon, popup design, new-selection
semantics or the Phase8 end-to-end latency/hardening target. Four-scale
probe+capture+OCR median396.7ms is not a complete translation/card latency claim.

Only Virtual-1 is exposed; optional actual second-monitor testing is unavailable,
while negative-origin/ratio logic is covered portably. Qt Wayland geometry may
report0,0, so compositor geometry and active UUID are the placement authority;
that discrepancy is preserved in the raw evidence. Fixed panel coordinates are
specific to this spike's VM and are validated by actual menu/action events.

Final run reports normal_unlock_needed=false and absolute pointer input at all
four scales. The normal same-UID Wayland unlock recheck and bounded relative
feedback alternative are unit-tested implementation paths; this report does
not claim the final run exercised them. Source changes no global lock/focus/
capture policy. No friend-hardware or arbitrary-application accuracy claim.

No human confirmation is requested: explicit --auto authorizes agent acceptance
from the observed deterministic gates. Only this verification report was
written; concurrent user research/config/project files were preserved.

_Independent verifier: goal-backward source, wiring, behavioral and raw-evidence
checks. No commits or VM commands performed._
