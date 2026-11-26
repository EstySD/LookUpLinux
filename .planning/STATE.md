---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Steam Deck
current_phase: 7
status: completed
stopped_at: Milestone v1.2 complete; all seven phases have host/VM evidence and honest blockers.
last_updated: "2026-11-26T10:37:36.196Z"
last_activity: 2026-11-26
last_activity_desc: "Phase 22 complete: host 901 passed, VM 914 passed, source bundle built"
progress:
  total_phases: 7
  completed_phases: 7
  total_plans: 7
  completed_plans: 7
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-11-26)

**Core value:** Хоткей над английским словом даёт перевод в оверлее у курсора примерно за 1–2 секунды, и слово попадает в базу со счётчиком.
**Current focus:** v1.2 Steam Deck — Phase 16, session abstraction and diagnostics

## Current Position

Phase: All 7 phases complete
Plan: —
Status: complete
Last activity: 2026-11-26 — Phase 22 complete: host 901 passed, VM 914 passed, source bundle built

Progress: [██████████] 100%

## Performance Metrics

**Velocity:**

- Total plans completed: 63
- Average duration: -
- Total execution time: not aggregated

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 3 | - | - |
| 02 | 11 | - | - |
| 03 | 3 | - | - |
| 04 | 3 | - | - |
| 05 | 3 | - | - |
| 5.1 | 3 | - | - |
| 6 | 3 | - | - |
| 7 | 5 | - | - |
| 8 | 9 | - | - |
| 8 | 9 | - | - |
| 9 | 2 | - | - |
| 10 | 1 | - | - |
| 11 | 3 | - | - |
| 12 | 1 | - | - |
| 13 | 1 | - | - |
| 14 | 2 | - | - |
| 15 | 1 | - | - |

**Recent Trend:**

- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
| Phase 01 P01 | 10min | 2 tasks | 5 files |
| Phase 01 P02 | 20min | 4 tasks | 5 files |
| Phase 01 P03 | 8min | 2 tasks | 3 files |
| Phase 2 P01 | 25min | 2 tasks | 6 files |
| Phase 2 P02 | 25min | 3 tasks | 8 files |
| Phase 2 P03 | 20min | 3 tasks | 8 files |
| Phase 2 P04 | 30min | 2 tasks | 13 files |
| Phase 2 P05 | 30min | 2 tasks | 3 files |
| Phase 02 P06 | 50min | 2 tasks | 3 files |
| Phase 02 P07 | 35min | 2 tasks | 3 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [v1.2]: Both SteamOS modes; Desktop Mode supported, Gaming Mode experimental.
- [v1.2]: Gaming Mode uses a fullscreen selection window, not an overlay.
- [v1.2]: Portable home-directory bundle; no pacman install into immutable `/usr`.
- [v1.2]: Fallback ScreenShot2 on SteamOS 3.9; KWin plugin optional on 3.10+.
- [v1.2]: Gaming trigger via evdev back-button chord; Steam Input key fallback.
- [v1.2]: No physical Deck; hardware acceptance is a blocked external gate.
- [v1.2 Phase 16]: Gaming daemon skips KDE lifecycle/tray/shortcut and exposes a D-Bus no-op trigger until Phase 18.
- [v1.2 Phase 16]: KWin hotkey plugin is optional; doctor reports ScreenShot2 fallback instead of failing.
- [v1.2 Phase 17]: Portable app lives in `~/.local/lib/lookup`; user data stays in the normal XDG paths and uninstall never removes it.
- [v1.2 Phase 17]: Portable trigger entry owns the ScreenShot2 D-Bus permission; autostart is KDE-only.
- [v1.2 Phase 18]: SIGUSR2 frame is consumed and unlinked; PipeWire fallback is bounded; no screenshot is stored permanently.
- [v1.2 Phase 19]: Gaming trigger reuses the desktop scene pipeline; repeated triggers close instead of stacking.
- [v1.2 Phase 20]: Gaming autostart is an owned systemd user unit; trigger choice is in settings and diagnostics.
- [v1.2 Phase 21]: SteamOS docs mark Desktop supported and Gaming experimental/hardware-unverified.
- [2026-10-27]: V1 adds multiline context and contextual word sense in inserted Phase 5.1 before Phase 6; real fullscreen game validation in Phase 8. Completed Phases 1–5 retain original acceptance. New requirements remain Pending.
- [Roadmap]: Прод-версия вместо MVP, 8 фаз по горизонтальным слоям (выбор пользователя)
- [Roadmap]: Фоновое приложение в трее; команда хоткея только будит его и стартует, если оно не запущено
- [Roadmap]: Тестируем только в VM Дениса, фазы с железом друга нет; PERF-01 (медиана до 1,5 с) проверяется в Phase 8
- [Roadmap]: Phase 4 — спайк с двумя гейтами: kdotool или свой скрипт KWin + QtDBus; spectacle или ScreenShot2
- [Roadmap]: Режим ponytail — минимальное полное решение; относится к реализации, не к объёму фич
- [Phase 01-01]: Digit check (D-17) runs on raw token before edge trimming; possessive loop stops at D-16 contractions
- [Phase 01]: Snapshot taken before BEGIN IMMEDIATE and published only if user_version unchanged under the lock — Connection.backup inside the write lock hangs on WAL
- [Phase 01]: 01-03: store.py needed no change; 10-process spawn tests pass on pre-created and fresh DBs
- [Phase 01]: IN-02: правило D-04 (длина < 2, кроме a/i) действует на весь ключ фразы, не на токен ("plan b" допустим); токен из одной пунктуации отклоняет всю фразу, а не выбрасывается ("rock & roll" не превращается в "rock roll")
- [Phase 01]: Тестовая VM — VirtualBox `arch-kde` (Windows-хост, QEMU/KVM недоступен), `ssh archvm`
- [Phase 02-01]: assert_untouched in StepTransactionGuardTests reopens a copy of the V1 fixture with the real tuple, since the real tuple now upgrades V1 to v2
- [Phase 02-02]: LZO1X and RIPEMD-128 are pure stdlib Python, no python-lzo package (Phase 7 PKGBUILD gets no new dependency); dictzip reader requires exact chunk lengths including the last chunk
- [Phase 02-03]: index cache tag validated; irregular.txt generated from WordNet 3.1 exception lists (5814 forms) with Princeton notice
- [Phase 02-04]: word without dictionary block is not_found; not_found from any provider ends the chain; failure reasons ranked blocked > bad_response > timeout > no_network
- [Phase 02-05]: StarDict entries failing validation become None slots so .syn numbering counts them; POS tokens right after '(' are usage notes; pointer_only requires a single m field
- [Phase 02-06]: [!trs] keeps its text in DSL articles; only [s]/[video] and {{..}} are dropped; a DSL cache payload with any out-of-range offset, key target, encoding or BOM length is rebuilt
- [Phase 02-06]: warm open of one 200000-article DSL dictionary is 0.28 s (JSON load); the D-09 budget of 0.3 s for all dictionaries must be measured in the VM
- [Phase 02-07]: MDX key info failures under Encrypted=2 report reason checksum; extra caps MAX_ENTRIES 8M and MAX_KEY_TOTAL 512 MiB; real-file MDX check (LZO, Encrypted=2) remains a UAT item in plan 11

### Pending Todos

None yet.

### Blockers/Concerns

- No physical Steam Deck: Gaming Mode cannot be hardware-verified in this environment.
- SteamOS 3.9 stable is Plasma 6.7.3, below `kwin>=6.8`; the native plugin is unavailable there.
- Gamescope SIGUSR2 capture, focus return, and evdev permissions are unverified on real hardware; Phase 16 diagnostics deliberately report Gaming capture/trigger as not implemented until Phases 18/20.
- Steam Input has no global Gaming Mode layout; per-game layout may be required for the key fallback.
- `kdotool` compatibility with SteamOS's KWin is unverified.
- PUB-03 runtime-complete binary bundle is blocked: builder and offline install are verified, but PyQt6/Tesseract/kdotool/wl-clipboard binaries for the SteamOS ABI were not produced here.

Phase 14 complete: provider fallback passes six live target cases; real dictionaries pass twelve source checks; second monitor at 100%/125%, borderless word selection and seven exits pass. Both full suites: 868 tests, zero failures/errors. See `phases/14-reliability/14-ACCEPTANCE.json`. Historical v1.0 limits remain in `milestones/v1.0-MILESTONE-AUDIT.md`.

#### Historical planning concerns (recorded before implementation)

- [Phase 2]: LZO для MDX решён в 02-02 чистой реализацией на stdlib; настоящий MDX-файл с LZO-блоками ещё не проверен (UAT)
- [Phase 2]: VM probes 2026-10-25: all Google clients and MyMemory work via urllib; keep MyMemory for phrases/sentences. Real MDX/DSL remain unverified (no files supplied).
- [Phase 3]: Точность tesseract на мелком тексте интерфейса при 125–200% не измерена (PSM 11 или 6, увеличение, инверсия)
- [Phase 4]: Цепочка kdotool (cursor, windowmove, windowactivate) на Plasma 6.8.1 не запускалась; регистрация хоткея без перелогина не проверена
- [Phase 4]: Демон в трее держит долгое соединение и не перечитывает `user_version`: после обновления программы (миграции) он должен переоткрыть базу (01-REVIEW IN-06, docstring `open_store`)
- [Phase 4]: Фокус окна, созданного фоновым процессом, под защитой KWin от кражи фокуса; нужна передача activation token от команды хоткея
- [Phase 4]: Задержка spectacle (оценка 300–800 мс) может съесть бюджет 1,5 с; запасной путь ScreenShot2; поведение `wl-paste --primary` замерить
- [Phase 5]: Esc и потеря фокуса под активацией KWin; клик и таймаут должны закрывать всегда
- [Phase 7]: kdotool есть только в AUR, а `makepkg -si` ставит зависимости лишь из репозиториев; решить: вложить бинарник, собирать из исходников или optdepends
- [Phase 7]: Смена хоткея из настроек требует перерегистрации `.desktop` и `kbuildsycoca6` на лету
- [Phase 8]: VM врёт про курсор и рендер, на железе друга не проверяем; логику масштаба и выбора слова покрыть тестами вне VM

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

## Session Continuity

Last session: 2026-11-26
Stopped at: Milestone v1.2 complete; all seven phases have host/VM evidence and honest blockers.
Resume file: .planning/phases/22-bundle-acceptance/22-SUMMARY.md

## Operator Next Steps

- Build and publish the runtime-complete bundle on a SteamOS/Linux target, then validate on real hardware.
- Do not claim Desktop or Gaming Mode hardware verification without a Deck acceptance run.
- Do not claim Steam Deck hardware verification; record VM-tested and hardware-unverified separately.
