---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Надёжность и распространение
current_phase: 14
current_phase_name: Надёжность в реальных сценариях
status: blocked
stopped_at: Phase14 real MDX/DSL downloaded and verified on both hosts; contextual provider blocked direct and proxy; second-monitor/borderless pending; clone off and tunnel closed
last_updated: "2026-11-03T10:49:47.535Z"
last_activity: 2026-11-03
last_activity_desc: Phase 13 complete, transitioned to Phase 14
progress:
  total_phases: 7
  completed_phases: 5
  total_plans: 10
  completed_plans: 9
  percent: 71
---

# Project State

## Project Reference

See: .planning/PROJECT.md (v1 scope expanded 2026-10-27)

**Core value:** Хоткей над английским словом даёт перевод в оверлее у курсора примерно за 1–2 секунды, и слово попадает в базу со счётчиком.
**Current focus:** Phase 14 — real MDX/DSL verified; target context provider blocked with and without configured proxy

## Current Position

Phase: 14 — Надёжность в реальных сценариях
Plan: 14-01 complete; 14-02 pending
Status: blocked
Last activity: 2026-11-03 — Phase 13 complete, transitioned to Phase 14

## Performance Metrics

**Velocity:**

- Total plans completed: 60
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

Phase 14 partial: downloaded real MDX/DSL pass six source-based lookup checks per platform; premature missing-input blocker resolved. Context provider reports blocked in six direct and six proxied target queries, offline articles retained. Second-monitor/borderless acceptance pending. See `phases/14-reliability/14-01-SUMMARY.md` and `continue.md`. Historical v1.0 limits remain in `milestones/v1.0-MILESTONE-AUDIT.md`.

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

Last session: 2026-11-03T10:49:47.525Z
Stopped at: Phase14 real MDX/DSL downloaded and verified on both hosts; contextual provider blocked direct and proxy; second-monitor/borderless pending; clone off and tunnel closed
Resume file: .planning/phases/14-reliability/continue.md

## Operator Next Steps

- Resume 14-02-PLAN.md: provider availability and second-monitor/borderless evidence. Real MDX/DSL are downloaded and verified; reuse valid checks while product code is unchanged.
