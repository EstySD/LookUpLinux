---
phase: 05-app
plan: 01
status: complete
completed: 2026-10-26
requirements-completed: []
key-files:
  created: [lookup/app.py, tests/test_app.py, tests/test_translate_ready.py]
  modified: [lookup/translate.py, tests/test_core_imports.py]
---

Implemented the stdlib request engine with one non-daemon worker, one pending
latest request, monotonic identity, guarded eligible history commit and detached
frozen/ready/context/error events. Dictionary/SQLite resources are created and
closed on that worker. Primary freshness resets on absent/invalid text and is
consumed only by the currently accepted ready result. Source freeze precedes
loading; no image bytes cross the event boundary. Errors remain fixed/private.

Translation now supports optional on_ready and context_gate. Main answers can
be displayed before context join. The single GUI-owned context slot remains
held until actual network completion, even beyond join timeout; busy context
does not suppress the useful main answer. Default callers retain their original
admission behavior. Cache/meta SQLite failures preserve main/context answers
with fixed cache_error; history failure has a distinct save_error envelope.

One current eligible event performs one upsert. Final context reuses its count.
History eligibility matches existing CLI semantics; sentences never create word
rows. Upsert contention uses worker busy_timeout=50ms under the shared generation
guard. Cache writes for obsolete requests are safe; stale history/UI are blocked.
GUI must still check identity when queued events arrive. Existing context/main
deadlines mean a newer pending request can wait; this is not instant cancellation.

Tests were first run red. Events/barriers verify early snapshot independence,
supersede/dismiss, burst coalescing, context held beyond join and bounded worker
Quit. Actual read-only/contended SQLite and injected full/read failures preserve
successful translations without network retries or duplicate history. Thread
ownership, one ready/final count, sentence no-row, source freshness and unchanged
CLI/core imports are tested. New callback cases use a separate focused test
module instead of enlarging the existing translation test file.

Fresh validation: 542 tests pass on Windows Python 3.14 (27.677s) and 3.12
(27.660s), 7 existing skips each. Focused engine/translation/core/CLI: 49 pass;
final engine/ready/import subset: 17 pass. git diff --check passes. Actual
production Qt/VM evidence belongs to plans 02/03 and no requirement is marked
accepted yet. T-05-01..04 controls implemented; independent phase security and
code review remain required before acceptance.
