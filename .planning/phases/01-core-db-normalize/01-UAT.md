---
status: testing
phase: 01-core-db-normalize
source: [01-VERIFICATION.md]
started: 2026-10-23T21:34:07Z
updated: 2026-10-23T21:34:07Z
---

## Current Test

number: 1
name: default_db_path() на Arch VM указывает в домашнюю папку
expected: |
  Без LOOKUP_DB и XDG_DATA_HOME команда
  python -c "import lookup.store as s; print(s.default_db_path())"
  из корня репозитория печатает путь, оканчивающийся на .local/share/lookup/lookup.db в настоящем домашнем каталоге; на диске ничего не создаётся.
awaiting: user response

## Tests

### 1. default_db_path() на Arch VM указывает в домашнюю папку
expected: путь ~/.local/share/lookup/lookup.db под настоящим HOME, файл не создаётся
result: [pending]

### 2. Переход в WAL при занятой базе сдаётся примерно за 2 с на Arch VM
expected: open_store() на базе не в WAL, пока другой процесс держит эксклюзивную блокировку, падает с sqlite3.OperationalError "could not switch database to WAL: database is locked" примерно через 2 с, а не через минуты
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
