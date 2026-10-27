---
phase: 06-words-cards
plan: 03
subsystem: acceptance
tags: [native-qt, learning, exports, anki, vm]
requires:
  - phase: 06-01
    provides: History, immutable card snapshots, scheduling and atomic export core
  - phase: 06-02
    provides: Native Words/Review windows and tray/popup integration
provides:
  - Actual Wayland native learning acceptance with controlled public input
  - Real official Anki Rust-backend import of unchanged production TSV
  - Fresh host and target regression evidence with all target-only gates enabled
affects: [07-settings-package, 08-vm-hardening]
tech-stack:
  added: []
  patterns: [owned XDG verification profile, explicit available-import failure gate]
key-files:
  created:
    - tools/check_learning_app.py
    - tests/test_check_learning_app.py
    - .planning/phases/06-words-cards/learning-native/report.json
    - .planning/phases/06-words-cards/learning-native/anki-import.json
    - .planning/phases/06-words-cards/06-host-tests.txt
    - .planning/phases/06-words-cards/06-target-tests.txt
  modified: []
key-decisions:
  - Use actual production Owner, Engine and native widgets with controlled public Source/events; do not repeat previous-phase capture/hotkey/provider acceptance.
  - Select an ordinary two-field Anki note type structurally, without a localized name.
  - An explicitly available Anki import that fails makes the run fail; unavailable/not-requested import remains explicitly unverified.
  - Isolate Qt XDG settings/cache/data before importing Qt, while keeping the actual session runtime and DBus.
requirements-completed: [LIST-01, LIST-02, POP-04, LEARN-01, LEARN-02]
duration: approximately 17min
completed: 2026-10-27
---

# Phase 6 Plan 03: Native Learning and Actual Anki Import

**Native Words/Review/popup workflows passed all ten gates, and Anki 26.9.3 imported the unchanged production TSV into two verified notes in a throwaway collection.**

## Verification Results

- Final host: `python -m unittest discover -s tests` — **640 tests OK**, eight known Windows/environment/opt-in skips, **42.708s**. Log: `06-host-tests.txt`.
- Final target: `QT_QPA_PLATFORM=offscreen LOOKUP_TEST_OCR=1 LOOKUP_TEST_DICTS=/home/arch/.local/share/lookup/dicts python -m unittest discover -s tests` — **640 tests OK, zero skips**, **55.763s**. Log: `06-target-tests.txt`.
- Focused harness/native-widget/core suite — **27 tests OK**, zero skips, **1.084s**. Harness contracts independently cover missing/false gates, every cleanup flag, unavailable import, available import failure, timeout and invalid JSON.
- Actual native command on `archvm`, isolated source copy `/home/arch/LookUpLinux-gsd-learning-06`: `python tools/check_learning_app.py --output native-evidence --anki-python /home/arch/lookup-anki-core-06/bin/python` — **10/10 gates**, **6/6 final-run cleanup checks**, `platform: wayland`, actual Anki import `verified`.
- `git diff --check -- tools/check_learning_app.py tests/test_check_learning_app.py` — exit 0.

The target suite executes the four POSIX-only tests, two real Mueller dictionary tests, actual context-image test and opt-in Breeze OCR CLI test skipped on Windows. Phase 5.1 regressions remain in the full suite; its 144-case image matrix was not repeated because this unit changes no OCR code.

## Observed Native Behavior

- The actual tray menu opens production Words and Review windows; Settings remains disabled for Phase 7. The real Engine runs with an owned public Source for the accepted post-deletion lookup.
- Default order is numeric count descending (`river:10`, `apple:2`, `bank:2`), header clicking changes order, and `BANK` searches without increasing counts.
- History add creates one immutable card; a duplicate preserves its entire snapshot and schedule. Deleting history leaves the card intact. The next accepted Engine lookup recreates history with count **1**.
- The popup button stores its displayed Russian contextual meaning, multiline source, occurrence span and provider. Late displayed enrichment and duplicate clicks leave that stored snapshot unchanged. Deleting bank history also leaves its card unchanged.
- Review hides answers until reveal, then shows the exact saved plain text and all four interval labels. Initial intervals are Again **600s**, Hard/Good/Easy **86400s**, matching the shared scheduler preview.
- One Good response persists version **1** and the expected due time. Repeated grading is refused; reopening a separate database connection retains the schedule. The reusable Review window honestly shows no due cards after grading the queue.
- Actual in-process Qt save dialogs are observed and clicked, including Cancel. Production CSV/TSV exports round-trip Unicode, quotes, multiline context and literal HTML-like text. Injected `os.replace` failure retains the previous destination bytes and removes the temporary file.
- All four synthetic native screenshots were inspected: `learning-native/words-light.png`, `words-dark.png`, `review-light.png`, `review-dark.png`. Text, actions, count columns and revealed plain-text fields are legible.

These are agent observations with Qt input events and controlled public Source/displayed events. They are not human testing, new physical-hotkey/capture acceptance, or Phase 8 game/performance acceptance.

## Actual Anki Import

Anki was absent from the VM. Its official **26.9.3** Python/Rust core wheel was installed in the isolated development venv `/home/arch/lookup-anki-core-06`; no production dependency or personal Anki profile was added or used.

The harness uses the installed `Collection.get_csv_metadata()` and `Collection.import_csv(ImportCsvRequest)` API. It selects a regular type-0 note type with two fields and one template, maps columns 1/2, and creates a separate synthetic deck. No English or localized note-type name is hardcoded. The collection and media directory live in an automatically removed temporary directory.

Actual backend inspection verified both imported notes, including `яблоко` and the bank contextual meaning. Imported Front/Back fields match the generated export cells exactly. Escaped `<b>`/`<sign>`, Unicode, quotes and `<br>` preserve the intended literal text and multiline context. The input file is not edited before or during import.

- TSV SHA-256 before/after actual import: `b51e6aa2513fd5a34cfbd94bb12660971dd17959e319400fbaa68db21d4b11f6`.
- CSV SHA-256: `54aa08438eeae647958215df6d0a3e065b39bd69802fe3bf1c40c6877645a632`.
- Evidence: `learning-native/anki-import.json`, `cards-anki.txt`, `cards.csv`, and the matching import result in `learning-native/report.json`.
- Scoped `learning-native/.gitattributes` preserves the generated CSV CRLF and TSV LF bytes through Git. Index blob hashes were checked against the reported hashes.

The official [text import manual](https://docs.ankiweb.net/importing/text-files.html) documents UTF-8, tab headers, HTML and escaping. The official [core package README](https://github.com/ankitects/anki/blob/main/pylib/README.md) identifies this headless library as the wrapper around Anki's Rust backend. This verifies the real backend importer, not the AQT graphical import dialog or AnkiWeb sync.

An explicitly requested/available import failure, timeout, stale/malformed report or changed export checksum makes the acceptance run fail while retaining cleanup evidence. Omitting the optional Anki executable leaves actual import explicitly unverified rather than claiming success.

## Commits

1. Task 1 RED: `5009152` — missing/failed gate and cleanup contracts.
2. Task 1 GREEN: `4aa3a0b` — native harness, real Qt dialogs, controlled workflow and actual Anki importer with failure guards.
3. Task 2 evidence: `687c7dd` — native observations, four screenshots, export samples, actual import and fresh full suites.
4. Exact artifact bytes: `8d8e712`, `4ae746f` — scoped text attributes and explicit CSV renormalization.

## Deviations and Limits

1. **Earlier verification settings side effect:** Initial calibration runs isolated `LOOKUP_*` but not Qt XDG directories. Metadata-only inspection found `/home/arch/.config/QtProject.conf`, size **659 bytes**, modified **2026-10-27T18:15:52Z** during those runs. Its prior content/recent-directory baseline is unknown. The file was left untouched; its contents were not read, deleted or overwritten in an attempted rollback. Do not describe all earlier verification resources as restored. The final run isolates `XDG_CONFIG_HOME`, `XDG_CACHE_HOME` and `XDG_DATA_HOME` under its owned temporary profile before Qt initialization, and removes those paths successfully while preserving actual session runtime/DBus.
2. **Harness calibration:** Calling the protected `QFileDialog.accept()` method on a C++-created static dialog initially aborted the verification process. The tool now clicks the actual Save/Cancel buttons and guards callback errors. Only the two verified owned synthetic abandoned profiles were removed after checking their location, ownership and public database contents. No production fix was required.
3. **Expected test diagnostic noise:** The target log retains existing `multiprocessing.spawn` / `SemLock._rebuild` FileNotFoundError output from `test_reader_loop_has_deadline` deliberately forcing a negative deadline while children start. Phase 5.1's focused reproduction already identified that teardown race; positive writer queue/count tests pass. The current full target runner reports zero failures/errors. No Phase 6 timing test failed.
4. The final native run uses actual Qt file dialogs with the in-process dialog backend for deterministic automation. External KDE portal dialogs, a full graphical Anki session and sync are not claimed. Native UI palette changes are process-local; no global desktop theme, shortcut or display scale is changed.
5. STATE, ROADMAP, requirement checkboxes and user changes remain parent-owned. This unit changes only its harness/tests, evidence and summary. No known product stub was introduced.

## Self-Check: PASSED

Owned tool/test files, native JSON/screenshots/exports, both full-suite logs and this summary exist. The five listed task/evidence commits exist. Final native gates, six cleanup flags and actual import are true; the source export hashes match both working files and committed Git blobs. Parent owns final independent phase verification and state transition.
