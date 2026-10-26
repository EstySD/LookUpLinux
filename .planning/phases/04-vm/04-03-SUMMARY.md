---
phase: 04-vm
plan: 03
subsystem: vm-validation
status: complete
completed: 2026-10-26
requirements-completed: [TRIG-01, CAPT-01]
key-files:
  created: [tools/check_vm_spike.py, .planning/phases/04-vm/04-GATE-RESULTS.json, .planning/phases/04-vm/04-VM-RESULTS.md]
---

Executed the Windows-host/Arch-target gate harness against the existing arch-kde
VirtualBox VM in an isolated checkout. The host uses real VBoxManage keyboard
scancodes and VirtualBox COM absolute pointer events. Identical absolute events
can be suppressed after guest scale changes; a distinct adjacent event plus
KWin-observed delivery resolves this without synthesizing recognition results.
Cold DBus registration and initial focus settling use bounded observation polls.

All four required criteria pass: same-owner/cold physical shortcut, four-scale
public-word capture/OCR, compositor placement/focus/Escape/deactivate and physical
tray menu, bounded primary read with per-stage timing. Only one output is exposed;
negative origins are covered portably. No relogin needed after kbuildsycoca6.
Another owned component reports the shortcut unavailable, so existing bindings
are checked before registration and never stolen.

Chosen platform routes: kdotool cursor/window operations; ScreenShot2 raw FD
capture. Spectacle also works but its measured capture median is substantially
higher. Both remain bounded transports. No custom KWin fallback script was
needed or installed. Detailed samples and PID/event evidence are in the JSON.

The snapshot precedes mutations, is tied to a fresh run UUID, records child
PID/start identities, and remains available after failed restoration. Cleanup
compares display fields and desktop bytes, checks stopped owned processes and
shortcut availability, and runs even if setup response or key release fails.
All four restoration flags passed in the final real run.

Independent code review found three cleanup/acceptance defects; all remediated
with regressions, detailed in 04-REVIEW-FIX.md. Independent ASVS1 verification
closed 14/14 threats. Fresh full suites: 528 tests each on Windows 3.14/3.12 and
Arch 3.14, with 7/7/3 existing skips. Historical Arch cancellation-test child
SemLock teardown traces remain, but the suite exits successfully.

Acceptance is agent judgment under the explicit --auto instruction, never a
claim of human testing. Real friend hardware and a second physical monitor
remain outside this VM-only scope.
