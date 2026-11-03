---
phase: 12-yomitan
plan: 01
subsystem: dictionaries
requirements-completed: [DICT-04, DICT-05]
duration: 24min
completed: 2026-11-03
---

# Yomitan v3 ZIP support

Added bounded, in-place ZIP parsing, structured/plain-text articles and source cross-reference resolution through the existing DictSet mechanism. Discovery, enable/order settings, same-path replacement, doctor and visible settings error labels use existing dictionary infrastructure. No new dependency and no dictionary redistribution.

Validation: host 864 tests, zero failures, 11 skips; owned Linux target 864 tests, zero failures, 4 skips. Supplied 48,523-entry archive passes cat/dog/hello/hallo, reopen and doctor on both hosts. `batch-manifest.json` pins tested working-tree hashes (including preserved user OCR edits); `batch-report.json` and logs record final successful batch. Earlier attempts are retained as failed checks, not overwritten acceptance claims.

Limit: cold archive opening takes 4.40 s on host and 4.46 s on Linux during batch load. Readers remain in memory for normal lookups. No warm startup cache is claimed. Only this supplied v3 text/structured archive is accepted; images/media and other versions are not accepted. Agent verification, no human acceptance.
