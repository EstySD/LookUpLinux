---
status: complete
phase: 01-core-db-normalize
source: [01-VERIFICATION.md]
started: 2026-10-23T21:34:07Z
updated: 2026-10-24T05:03:18Z
---

## Current Test

[testing complete]

## Environment

Arch VM недоступна с машины разработки, поэтому оба теста прогнаны Claude в Docker-контейнере `archlinux:latest` (Python 3.14.8, SQLite 3.54.0), под обычным пользователем `tester` с настоящим HOME `/home/tester`. Это тот же Arch и тот же Python, что в VM, но не сама VM: задержку хоткея (PERF-01) по-прежнему мерить в VM в фазе 8. Полный набор `python -m unittest` в контейнере: 63 теста, OK.

## Tests

### 1. default_db_path() на Arch VM указывает в домашнюю папку
expected: путь ~/.local/share/lookup/lookup.db под настоящим HOME, файл не создаётся
result: pass
evidence: без LOOKUP_DB и XDG_DATA_HOME напечатано `/home/tester/.local/share/lookup/lookup.db`; после вызова `~/.local` не существует (на диске ничего не создано)

### 2. Переход в WAL при занятой базе сдаётся примерно за 2 с на Arch VM
expected: open_store() на базе не в WAL, пока другой процесс держит эксклюзивную блокировку, падает с sqlite3.OperationalError "could not switch database to WAL: database is locked" примерно через 2 с, а не через минуты
result: pass
note: "Первый прогон — issue (minor): под EXCLUSIVE 5.01 с и голое 'database is locked'. Исправлено (см. Gaps). Повторный прогон в Arch-контейнере: SHARED 2.07 с, RESERVED 2.00 с — 'could not switch database to WAL: database is locked'; EXCLUSIVE 2.02 с — 'could not read the schema version: database is locked' (блокировка мешает уже чтению версии, поэтому текст другой; тип и граница 2 с как ожидалось)."

## Summary

total: 2
passed: 2
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "open_store() на базе не в WAL под эксклюзивной блокировкой другого процесса сдаётся примерно за 2 с с 'could not switch database to WAL: database is locked'"
  status: resolved
  resolution: "Шаги 3-4 open_store() теперь делят один дедлайн min(timeout, _WAL_MAX_WAIT): чтение user_version идёт с коротким busy_timeout через общий цикл _until_unlocked. Добавлены тесты test_exclusive_lock_blocks_version_read_within_same_bound и test_exclusive_lock_deadline_follows_short_timeout (на старом коде падают). 65/65 на Python 3.14 и 3.12 и в Arch-контейнере."
  reason: "Claude, Arch-контейнер: под BEGIN EXCLUSIVE open_store() упал через 5.01 с с 'database is locked'; под SHARED и RESERVED — 2.0 с, как ожидалось"
  severity: minor
  test: 2
  root_cause: "Шаг 3 open_store() (`PRAGMA user_version`) выполняется до _ensure_wal() с полным busy_timeout (по умолчанию 5 с). Rollback-журнал под EXCLUSIVE блокирует и чтение, поэтому шаг 3 ждёт все 5 с и падает с ошибкой SQLite, не доходя до ограниченного _WAL_MAX_WAIT цикла. Регрессионный тест WR-01 держит только SHARED-блокировку (_locked_rollback_db), поэтому этот путь не покрыт. Поведение соответствует docstring (ошибки шагов 1-5 не оборачиваются), расходится только оценка 2 с. На практике достижимо редко: база не в WAL бывает лишь до первого успешного open_store, а EXCLUSIVE держится только на время коммита."
  artifacts:
    - path: "lookup/store.py"
      issue: "шаг 3 читает user_version с полным busy_timeout, вне дедлайна _WAL_MAX_WAIT"
    - path: "tests/test_migrations.py"
      issue: "_locked_rollback_db держит SHARED, а не EXCLUSIVE; случай EXCLUSIVE не тестируется"
  missing:
    - "Ограничить чтение user_version тем же дедлайном min(timeout, _WAL_MAX_WAIT) (короткий busy_timeout на шаг 3), либо принять 5 с как достаточно редкий случай и поправить ожидание в VERIFICATION"
    - "Добавить тест с BEGIN EXCLUSIVE в другом процессе/соединении"
  debug_session: ""
