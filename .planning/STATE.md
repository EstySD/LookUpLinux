---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_phase: 2
current_phase_name: Офлайн-словари и перевод
status: ready_to_plan
stopped_at: Phase 1 complete (UAT and review debt closed)
last_updated: "2026-10-24T05:17:16.604Z"
last_activity: 2026-10-24
last_activity_desc: Phase 1 complete, transitioned to Phase 2
progress:
  total_phases: 8
  completed_phases: 1
  total_plans: 3
  completed_plans: 3
  percent: 13
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-24)

**Core value:** Хоткей над английским словом даёт перевод в оверлее у курсора примерно за 1–2 секунды, и слово попадает в базу со счётчиком.
**Current focus:** Phase 1 — Ядро: база и нормализация

## Current Position

Phase: 2 — Офлайн-словари и перевод
Plan: Not started
Status: Ready to plan
Last activity: 2026-10-24 — Phase 1 complete, transitioned to Phase 2

Progress: [█░░░░░░░░░] 13%

## Performance Metrics

**Velocity:**

- Total plans completed: 3
- Average duration: -
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 3 | - | - |

**Recent Trend:**

- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
| Phase 01 P01 | 10min | 2 tasks | 5 files |
| Phase 01 P02 | 20min | 4 tasks | 5 files |
| Phase 01 P03 | 8min | 2 tasks | 3 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

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

### Pending Todos

None yet.

### Blockers/Concerns

- [Phase 2]: MDX сжимается через LZO, которого нет в stdlib; нужен пакет из pacman или чистая реализация, иначе только zlib-словари
- [Phase 2]: Google gtx блокируется с 09.2026; проверить доступность из VM, решить про второй провайдер
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

Last session: 2026-10-24
Stopped at: Phase 1 complete; next: /gsd-discuss-phase 2 or /gsd-plan-phase 2
Resume file: None
