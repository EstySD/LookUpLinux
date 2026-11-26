# Requirements: LookUp Linux v1.2

**Defined:** 2026-11-26
**Core Value:** Хоткей над английским словом даёт перевод в оверлее у курсора примерно за 1–2 секунды, и слово попадает в базу со счётчиком.

## v1.2 Requirements

### Session and diagnostics

- [x] **SESS-01**: User can run LookUp in SteamOS Desktop Mode and get the existing KDE Wayland lookup behavior; the app detects the session and does not require a separate build.
- [x] **SESS-02**: User can start LookUp in SteamOS Gaming Mode; the app detects gamescope and operates without KWin, kglobalaccel, kdotool, a tray, or KDE D-Bus services.
- [x] **SESS-03**: User can run a read-only diagnostic that reports the detected session, SteamOS/Plasma/KWin/gamescope versions, missing dependencies, and available capture/trigger paths without exposing query text, screenshots, or history.

### Portable Desktop Mode

- [x] **INST-03**: User can install LookUp on immutable SteamOS entirely under the home directory without root; the installation remains usable after a SteamOS update replaces the root filesystem.
- [x] **INST-04**: User can launch LookUp from the application menu and have it autostart after Desktop Mode login.
- [x] **INST-05**: User can remove the portable installation without deleting words, cards, settings, dictionaries, or history.
- [x] **INST-06**: User can use the bundled runtime (PyQt6, Tesseract eng data, kdotool, wl-clipboard) without installing system packages; any system fallback is documented.
- [x] **DTOP-01**: User can use the hotkey, OCR/primary selection, popup, history and cards in SteamOS Desktop Mode; when the KWin hotkey plugin is unavailable, the fallback capture path is used and the limitation is visible.
- [x] **DTOP-02**: User can see in diagnostics whether the KWin hotkey plugin is active, optional, or unavailable, and whether fallback capture is in use.

### Gaming Mode capture and daemon

- [x] **GAME-03**: User can trigger LookUp over a running game in Gaming Mode and get a capture of the current game frame; the frame is held only temporarily and is not written to permanent storage.
- [x] **GAME-04**: User can keep the LookUp daemon running in Gaming Mode without a tray, KDE shortcut, or KWin; it registers its D-Bus service and survives normal session startup.
- [x] **GAME-05**: User can close the LookUp window and return to the game with controller/touch input restored; repeated triggers do not leave a stuck window or captured input.

### Selection and card

- [x] **SEL-01**: User can select a word by touching the captured game frame; the word at the tapped point is recognized and translated.
- [x] **SEL-02**: User can select a word without a mouse using a controller or keyboard: a visible crosshair moves, confirm selects, cancel closes.
- [x] **SEL-03**: User can read the translation card at 1280×800 with readable text and touch targets, and can return to the game with one action.

### Trigger

- [x] **TRIG-08**: User can trigger LookUp in Gaming Mode with a controller chord or configured key; the default path works without per-game Steam Input configuration where the hardware permits, and the fallback is documented.
- [x] **TRIG-09**: User can see and configure the Gaming Mode trigger in settings and verify its status in diagnostics.
- [x] **TRIG-10**: Rapid or repeated triggers produce one active lookup at a time and never stack windows or lose game control.

### Documentation and distribution

- [x] **DOC-01**: User can follow `docs/STEAMOS.md` to install, configure, use, update and uninstall LookUp in Desktop and Gaming modes, including Steam Input setup and known limitations.
- [x] **DOC-02**: User can see the verification status of each mode (VM-tested vs hardware-unverified) in README and docs; no unverified Deck behavior is presented as confirmed.
- [ ] **PUB-03**: User can download a reproducible portable SteamOS bundle with checksums and license notices, and install it without network access for runtime dependencies. Builder, determinism, manifest/checksum/license contents and offline install are verified; the runtime-complete binary bundle is blocked on a SteamOS/Linux build environment and Deck validation.

## Future Requirements

- True in-game overlay (Decky Loader QAM or Vulkan layer) — deferred until the fullscreen-window MVP is validated on hardware.
- KWin hotkey plugin for SteamOS 3.10+ — optional; build against the device's KWin and document the ABI constraint.
- Automatic Steam Input layout provisioning — deferred; manual setup and fallback are documented in v1.2.
- Other handhelds / non-SteamOS immutable systems — not targeted in v1.2.

## Out of Scope

| Feature | Reason |
|---------|--------|
| True overlay over a running game | Gamescope does not support a normal third-party overlay; Decky/Vulkan is a separate large project |
| pacman install into `/usr` on SteamOS | Immutable rootfs; updates can reset system packages |
| Flatpak/AppImage | Portable tar.gz with a venv/bundled runtime is simpler to verify and update |
| Dictionary/settings management in Gaming Mode | Configuration is done in Desktop Mode; Gaming Mode is lookup-focused |
| Gamepad support in KDE Desktop Mode | Only needed for Gaming Mode navigation |
| Real Steam Deck acceptance in this environment | No physical device; recorded as blocked/unverified |
| X11, other DEs, new languages, audio, CEFR, whole-screen translation | Existing exclusions remain |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SESS-01 | Phase 16 | Complete |
| SESS-02 | Phase 16 | Complete |
| SESS-03 | Phase 16 | Complete |
| DTOP-02 | Phase 16 | Complete |
| INST-03 | Phase 17 | Complete |
| INST-04 | Phase 17 | Complete |
| INST-05 | Phase 17 | Complete |
| INST-06 | Phase 17 | Complete |
| DTOP-01 | Phase 17 | Complete |
| GAME-03 | Phase 18 | Complete |
| GAME-04 | Phase 18 | Complete |
| SEL-01 | Phase 19 | Complete |
| SEL-02 | Phase 19 | Complete |
| SEL-03 | Phase 19 | Complete |
| GAME-05 | Phase 19 | Complete |
| TRIG-08 | Phase 20 | Complete |
| TRIG-09 | Phase 20 | Complete |
| TRIG-10 | Phase 20 | Complete |
| DOC-01 | Phase 21 | Complete |
| DOC-02 | Phase 21 | Complete |
| PUB-03 | Phase 22 | Blocked: runtime bundle pending |

**Coverage:**
- v1.2 requirements: 21 total
- Mapped to phases: 21
- Unmapped: 0 ✓

---
*Requirements defined: 2026-11-26*
*Last updated: 2026-11-26 after initial definition*
