# Roadmap: LookUp Linux

## Milestones

- ✅ **v1.0 LookUp Linux** — shipped 2026-11-01; 9 phases, 43 plans, 32 requirements.
  - [Complete roadmap](milestones/v1.0-ROADMAP.md)
  - [Accepted requirements](milestones/v1.0-REQUIREMENTS.md)
  - [Closeout audit and limits](milestones/v1.0-MILESTONE-AUDIT.md)
- ✅ **v1.1 Надёжность и распространение** — shipped 2026-11-03; 7 phases, 11 plans, 17 requirements.
  - [Roadmap](milestones/v1.1-ROADMAP.md)
  - [Requirements](milestones/v1.1-REQUIREMENTS.md)
  - [Verified closeout](milestones/v1.1-MILESTONE-AUDIT.md)
- 🚧 **v1.2 Steam Deck** — Phases 16–22 (in progress)

## Current status

**v1.2 «Steam Deck»** started 2026-11-26. Desktop Mode is the supported target; Gaming Mode is
experimental and hardware-unverified because no physical Steam Deck is available. Phase 16 is the
session abstraction and diagnostics gate; implementation proceeds in numeric order.

## Phases

- [ ] **Phase 16: SteamOS-сессия и диагностика** - Detect KDE/GNOME/gamescope and report actionable SteamOS diagnostics. (Not started)
- [ ] **Phase 17: Переносимая установка Desktop Mode** - Install, run and remove LookUp under the home directory without root. (Not started)
- [ ] **Phase 18: Gaming Mode: захват и демон** - Capture the gamescope frame and run headless without KDE. (Not started)
- [ ] **Phase 19: Полноэкранный выбор слова** - Select a word on the frozen frame with touch, controller or keyboard. (Not started)
- [ ] **Phase 20: Триггер и автозапуск** - Trigger Gaming Mode from a controller chord and start the daemon reliably. (Not started)
- [ ] **Phase 21: Настройки, диагностика, документация** - Make settings mode-aware and document both modes honestly. (Not started)
- [ ] **Phase 22: Бандл и приёмка** - Build the portable bundle and run the available acceptance gates. (Not started)

## Phase Details

### Phase 16: SteamOS-сессия и диагностика

**Goal**: The app distinguishes KDE Desktop, GNOME and gamescope sessions and reports actionable diagnostics without changing existing KDE behavior.
**Depends on**: v1.1 complete
**Requirements**: SESS-01, SESS-02, SESS-03, DTOP-02
**Success Criteria** (what must be TRUE):

  1. In the shared `arch-kde` VM, existing Desktop Mode behavior and tests are unchanged.
  2. A simulated gamescope environment selects the Gaming path and never calls KWin, kdotool or a tray.
  3. `lookup --doctor` reports session, Plasma/KWin/gamescope versions, missing components and the capture/trigger path without private content.
  4. `tools/check_steamos.py` produces sanitized diagnostics that can be run later on a real Deck.

**Plans**: TBD

### Phase 17: Переносимая установка Desktop Mode

**Goal**: The user can install, launch, autostart and remove LookUp on immutable SteamOS entirely from the home directory, with fallback capture when the KWin plugin is unavailable.
**Depends on**: Phase 16
**Requirements**: INST-03, INST-04, INST-05, INST-06, DTOP-01
**Success Criteria** (what must be TRUE):

  1. A clean `arch-kde` VM installs without root, launches from the menu, autostarts, and passes hotkey/OCR/popup/cards.
  2. A simulated rootfs replacement leaves the app and user data usable.
  3. Uninstall removes the app, entries and unit while preserving words, cards, settings and dictionaries.
  4. Diagnostics show fallback capture when the KWin hotkey plugin is absent.

**Plans**: TBD

### Phase 18: Gaming Mode: захват и демон

**Goal**: A headless daemon captures the current gamescope frame and serves the existing engine without KDE services or a tray.
**Depends on**: Phase 16
**Requirements**: GAME-03, GAME-04
**Success Criteria** (what must be TRUE):

  1. With a fake gamescope that writes a PNG on SIGUSR2, capture returns the frame and removes its temporary file.
  2. In a simulated Gaming session the daemon registers its D-Bus service and skips KDE lifecycle, shortcut registration and tray.
  3. Nested gamescope in the VM captures a real frame if Vulkan/llvmpipe works; otherwise the limitation is recorded, not claimed.
  4. No screenshot or query content is written to permanent storage.

**Plans**: TBD

### Phase 19: Полноэкранный выбор слова

**Goal**: The user selects a word on the frozen frame with touch, controller or keyboard and reads a readable card, then returns to the game.
**Depends on**: Phase 18
**Requirements**: SEL-01, SEL-02, SEL-03, GAME-05
**Success Criteria** (what must be TRUE):

  1. Tapping the captured frame selects the correct word and shows its translation.
  2. A visible crosshair moves with D-pad/arrows, confirm selects and cancel closes without a mouse.
  3. The card is readable at 1280×800 and one action returns to the game.
  4. Rapid triggers produce one active window; closing restores input control.

**Plans**: TBD

### Phase 20: Триггер и автозапуск

**Goal**: The user can trigger Gaming Mode from a controller chord or configured key and rely on the daemon starting at session login.
**Depends on**: Phase 18, Phase 19
**Requirements**: TRIG-08, TRIG-09, TRIG-10
**Success Criteria** (what must be TRUE):

  1. A back-button chord triggers exactly one lookup; debounce and cooldown work.
  2. A Steam Input key fallback triggers the lookup and is documented.
  3. The systemd user service starts the daemon in Gaming Mode and does not duplicate it in Desktop Mode.
  4. Trigger configuration and status are visible in settings and diagnostics.

**Plans**: TBD

### Phase 21: Настройки, диагностика, документация

**Goal**: Settings and diagnostics are mode-aware, and the documentation states exactly what is verified and what is not.
**Depends on**: Phase 17, Phase 19, Phase 20
**Requirements**: DOC-01, DOC-02
**Success Criteria** (what must be TRUE):

  1. Settings hide the KDE shortcut in Gaming Mode, show the trigger, and leave Desktop settings unchanged.
  2. `docs/STEAMOS.md` covers install, Desktop Mode, Gaming Mode, Steam Input, limitations, update and uninstall.
  3. README and docs distinguish VM-tested from hardware-unverified behavior.
  4. Diagnostics and docs contain no query text, screenshots, history or other private content.

**Plans**: TBD

### Phase 22: Бандл и приёмка

**Goal**: A reproducible portable bundle is installable offline and the available acceptance gates are run and recorded honestly.
**Depends on**: Phase 17, Phase 18, Phase 19, Phase 20, Phase 21
**Requirements**: PUB-03
**Success Criteria** (what must be TRUE):

  1. The full test suite and relevant VM checks pass in one background batch with retained logs.
  2. The bundle installs in a clean VM without network runtime dependencies; checksums and license notices are verified.
  3. The real Deck checklist is recorded as blocked/unverified; no hardware behavior is claimed as confirmed.

**Plans**: TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 16. SteamOS-сессия и диагностика | 0/TBD | Not started | - |
| 17. Переносимая установка Desktop Mode | 0/TBD | Not started | - |
| 18. Gaming Mode: захват и демон | 0/TBD | Not started | - |
| 19. Полноэкранный выбор слова | 0/TBD | Not started | - |
| 20. Триггер и автозапуск | 0/TBD | Not started | - |
| 21. Настройки, диагностика, документация | 0/TBD | Not started | - |
| 22. Бандл и приёмка | 0/TBD | Not started | - |

**Execution Order:** 16 → 17 → 18 → 19 → 20 → 21 → 22.
