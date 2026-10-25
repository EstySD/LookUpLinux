# Phase 4: VM platform spike — Context

Gathered: 2026-10-25. Status: Ready for planning.
Mode: --auto; decisions delegated by Denis, no confirmation interview.

<domain>
Prove the platform integrations in the existing Arch/KDE Wayland VM before
building the production daemon in Phase 5: shortcut activation of an existing
process, cursor/monitor geometry, capture and OCR, popup positioning/focus,
tray interaction and bounded primary selection. Requirements TRIG-01/CAPT-01
and all four Phase 4 roadmap criteria. This is a spike, not a complete app.
</domain>

<decisions>
- D-01: Use existing VirtualBox arch-kde through ssh archvm. The roadmap's
  QEMU/virtio wording is superseded by the recorded Windows/VirtualBox choice.
  Do not recreate or replace the VM. It is now running headlessly with an
  active Plasma Wayland session for arch (UID1000), wayland-1, KWin PID471
  at the latest probe. Discover current session values; do not hardcode PIDs.
- D-02: Reuse Phase 3's accepted OCR library and explicit physical-image point
  contract. Geometry transforms for scale1/1.25/1.5/2 and negative monitor
  origins must have portable behavioral tests, independently of VM rendering.
- D-03: Evaluate installed kdotool first for cursor, window positioning and
  activation. If cursor or move/focus is unsupported/unreliable, implement the
  roadmap's narrow KWin-script + QtDBus receiver fallback. Persist an observed
  decision in PROJECT.md before Phase 5; do not assume commands exist.
- D-04: Measure spectacle monitor capture first, including correct monitor,
  cursor inclusion and privacy/cleanup. If capture threatens the latency
  budget, probe ScreenShot2 DBus. Prefer an FD/in-memory path if available.
  Never retain private desktop PNGs as test artifacts. Capture a controlled
  public test window when demonstrating OCR; unrelated desktop text stays out
  of logs/repository. Record per-stage probe/capture/OCR timings.
- D-05: A uniquely named test .desktop entry with X-KDE-Shortcuts and
  kbuildsycoca6 should wake one already-running test process via Qt single-
  instance IPC. Repeated triggers must prove the same PID. Test Meta+Shift+D
  registration, relogin necessity and conflicts; preserve unrelated shortcuts
  and configs, back up/restore only any spike-owned entry touched.
- D-06: Use a minimal frameless Qt popup and QSystemTrayIcon/Menu in the active
  Plasma session. Prove actual pointer-adjacent monitor-clamped placement and
  focus; distinguish Escape from focus loss. Research activation token paths
  rather than disabling KWin focus protections. Record what is observed versus
  inferred. Avoid broad system-policy changes or new daemon architecture.
- D-07: Probe wl-paste --primary with ~0.5s timeout; no hanging subprocesses.
  Avoid modifying unrelated clipboard/history; selection tests use known public
  text and leave no copied screenshot/text artifacts behind.
- D-08: Test target scales100/125/150/200 and second monitor if exposed by VM.
  Restore display configuration after experimental changes. Record unavailable
  hardware explicitly; do not invent multi-monitor measurements. Autonomously
  accept observed evidence and carry honest external limits forward.
</decisions>

<canonical_refs>
- .planning/ROADMAP.md — Phase4 two decision gates and four success criteria.
- .planning/REQUIREMENTS.md — TRIG-01 and CAPT-01.
- .planning/PROJECT.md — platform, privacy, daemon and testing decisions.
- .planning/STATE.md — carried concerns and VM environment.
- .planning/phases/03-ocr/03-CONTEXT.md — source-pixel OCR contract.
- .planning/phases/03-ocr/03-VERIFICATION.md — accepted baseline and limits.
- lookup/ocr.py — Recognition/Transform and measured defaults.
- lookup/__main__.py — library/CLI error, timing and resource conventions.
- tests/_support.py — isolated test paths and network guard.
</canonical_refs>

<code_context>
Core is quiet, optional Qt imports are lazy, tesseract has a finite timeout,
OCR PNG/TSV are memory-only and final translation/save occurs once. Existing
source/test tree in ~/LookUpLinux-gsd-redirect-6a7c is an isolated VM checkout;
sync exact current tracked sources before spike runs. A separate spike source
directory is preferable to changing unrelated VM app setups.
Latest target probe: kdotool /usr/local/bin/kdotool, spectacle, wl-paste,
kbuildsycoca6 and qdbus6 installed. Qt6.12, tesseract5.5.3 eng, genuine Breeze.
No Phase4 functionality has been proven by merely finding these executables.
</code_context>

<deferred>
Production popup data/layout, tray app lifecycle/settings and new-selection
semantics belong to Phase5. Word list/review to6, packaging to7, sustained
performance/hardening to8. No machine-wide shortcut/focus/security policy
changes, VM recreation or unrelated dependency upgrades.
</deferred>
