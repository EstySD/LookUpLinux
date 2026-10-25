---
status: testing
phase: 02-offline-dicts-translate
source: [02-VERIFICATION.md, 02-08-SUMMARY.md, 02-10-SUMMARY.md, 02-11-SUMMARY.md]
started: 2026-10-25T12:15:00Z
updated: 2026-10-25T12:15:00Z
---

## Current Test

number: 1
name: Confirm Phase 2 CLI user flow
expected: |
  Offline lookup shows readable Russian Mueller articles and IPA. `ran` shows
  `ran → run`; `running` keeps its own article and marks run as its base.
  Missing words fall back online; repeats come from cache. A 2–4 word phrase
  is saved once, sentences are translated without creating words rows.
  Network errors show a Russian reason and preserve available articles.
  All these behaviors passed machine/VM checks recorded in 02-VM-RESULTS.md.
  Optional inspection in the VM:
  cd ~/LookUpLinux-gsd-e92a26a
  python3 -m lookup --word ran --offline --no-save
  python3 -m lookup --list-dicts
awaiting: user response

## Tests

### 1. Confirm Phase 2 CLI user flow
expected: The dictionary, base-form, online/cache, phrase/sentence and failure behavior above meets the Phase 2 goal.
result: [pending]

### 2. Dictionary discovery and base-form search
expected: Format discovery, configuration, failure isolation, exact and base forms pass fixture and real Mueller checks.
result: pass
source: automated
coverage_id: 02-08/D1,D2

### 3. CLI, privacy and core imports
expected: CLI rendering, exit codes, UTF-8, cache/context and degraded database behavior pass, and libraries stay quiet and stdlib-only.
result: pass
source: automated
coverage_id: 02-10/D1,D2

### 4. Cross-platform and live VM integration
expected: 482 tests pass on Windows 3.14/3.12 and Arch 3.14.8, real Mueller sample passes, timing targets are met, and provider/proxy checks behave as recorded.
result: pass
source: automated
coverage_id: 02-11/D1,D2

## Summary

total: 4
passed: 3
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps

None found by machine or VM checks.

## Non-blocking Real-file Follow-up

Real MDX and DSL remain unverified (no file supplied), as explicitly permitted
by D-34. For later verification, place an MDX (ideally LZO or Encrypted=2) and
optionally DSL/DSL.DZ into `~/.local/share/lookup/dicts/` in the VM.
Do not treat this as an automated pass or a code failure; carry it to Phase 8.
