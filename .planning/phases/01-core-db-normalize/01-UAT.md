---
status: diagnosed
phase: 01-core-db-normalize
source: [01-VERIFICATION.md]
started: 2026-10-23T21:34:07Z
updated: 2026-10-24T04:57:34Z
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
result: issue
reported: "Claude, Arch-контейнер: под SHARED (BEGIN; SELECT) — 2.01 с и под RESERVED (BEGIN IMMEDIATE) — 2.04 с, сообщение 'could not switch database to WAL: database is locked', как ожидалось. Под EXCLUSIVE (BEGIN EXCLUSIVE) — 5.01 с и голое 'database is locked'."
severity: minor

## Summary

total: 2
passed: 1
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "open_store() на базе не в WAL под эксклюзивной блокировкой другого процесса сдаётся примерно за 2 с с 'could not switch database to WAL: database is locked'"
  status: failed
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
