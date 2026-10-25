---
phase: 03-ocr
plan: 03
subsystem: cli
status: complete
completed: 2026-10-25
requirements-completed: [CAPT-03, CAPT-04]
key-files:
  created: [tests/test_ocr_cli.py]
  modified: [lookup/__main__.py]
provides: [image-point CLI, source context, compound-first single save, private OCR errors and timing]
affects: [04, 05, 07]
---

# Phase 3 Plan 3 — Image CLI and persistence

python -m lookup --image PATH --at X,Y recognizes before opening dictionaries
or SQLite. Rejected OCR returns not found without network, dictionary opening
or store creation. Accepted selection probes offline compounds, calls the
existing translate.lookup exactly once and prints the chosen query/source
line before the normal dictionary/translation result. The recognized line
is context; no separate context override. Existing word/text/list commands
remain compatible. Finite points and argument combinations are validated.

Fixed Russian diagnostics cover missing PyQt6/tesseract/eng, invalid input,
resource caps, process timeout/failure and bad TSV; process/path details never
reach stderr. Timing combines preparation/OCR/selection/compound stages with
existing dictionary/database/translation timing without double-counting total.

Independent throwaway StarDict and real SQLite assertions verify break out
before break, fallback on absent phrase, well-known, repeat count, no-save,
rejection and zero speculative network/save effects. Tests started red before
CLI integration. Existing sentinel process privacy tests and new fixed-error
tests pass; no extra privacy module change was needed.

Fresh validation after implementation/default freeze:
- Windows 3.14: 506 tests, 26.683s, OK, 7 skips.
- Windows 3.12: 506 tests, 26.731s, OK, 7 skips.
- Arch 3.14: 506 tests, 10.252s, OK, 3 skips.
- LOOKUP_TEST_OCR=1 python3 -m unittest tests.test_ocr_cli -v: 5 tests,
  22.167s, OK, no skips; actual CLI executes all 96 fixture points.
- Separate frozen-default calibration: 96/96, median 234.7ms.
- git diff --check: no whitespace errors.

Ordinary suites skip opt-in actual OCR and real Mueller; Phase 2 real Mueller
was independently checked. Arch concurrency cancellation tests may emit child
SemLock teardown traces despite the passing suite, as recorded previously.

T-03-11..14 mitigations: finite argparse points/route tests, recognition before
resources, offline probes/one final save SQL assertions, fixed diagnostics and
finally resource closure. Agent acceptance is authorized by --auto; no human
testing or real MDX/DSL verification is claimed.
