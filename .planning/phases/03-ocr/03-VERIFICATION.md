---
phase: 03-ocr
verified: 2026-10-25T17:28:54Z
status: passed
score: 10/10 must-haves verified
overrides_applied: 0
acceptance_source: agent verification under explicit user --auto instruction
---

# Phase 3: OCR слова на готовых скриншотах — Verification

**Goal:** From a supplied screenshot and physical-pixel point, find the word
and its source line; choose tesseract settings from representative interface
fixtures and reject garbage. Verify portable logic outside the VM.

**Status:** passed. Initial goal-backward verification. No human test is claimed.
The user's explicit --auto instruction delegates routine acceptance. This phase
ships a CLI and offline recognition pipeline; live desktop capture/focus and
logical monitor coordinates remain the explicit Phase 4/5 scope.

## Observable Truths

Roadmap's four success criteria are retained in full; plan truths add six
implementation and integration requirements rather than reducing that scope.

| # | Truth | Status | Code and behavioral evidence |
|---|---|---|---|
| 1 | Image/point CLI prints word, source line and translation across light/dark Breeze, four scales and two text sizes; settings measured; per-stage timing available | VERIFIED | `lookup/__main__.py:137` recognizes, `:163` resolves query, `:174` calls real translator and prints query/line/result. `test_actual_breeze_fixture_cli` executes all 96 points with a real temporary StarDict; successful cases require dictionary answers. Manifest has all 16 combinations. Raw matrix/check reports independently audited; selected PSM6/2x/auto matches actual function defaults. Timing uses recognition stages plus compound/open/translation stages. |
| 2 | Between words, choose the nearest word deterministically (CAPT-03) | VERIFIED | `lookup/ocr.py:188` computes box-edge distance; `:193` prioritizes direct hits then bounded nearest candidates with deterministic tie order. Pure hit/nearest/tie tests and 16 independently positioned actual between-word cases pass. |
| 3 | Blank/icon/garbage and low confidence reject without word storage (CAPT-03) | VERIFIED | `_key` requires normalization and confidence >=50; rejected box hits remain barriers. Blank/icon points return no selection. CLI returns before config/dictionary/store/translation acquisition on rejection. Pure noise/low-confidence tests, no-resource/no-network CLI assertions and actual fixture negatives pass. |
| 4 | Over break, try break out before break; glue hyphenated words (CAPT-04) | VERIFIED | Selection emits forward then backward bounded same-line pairs; `choose_query` performs offline `DictSet.find` probes and returns the first hit. Real dictionary/SQLite tests prove break out is saved and absent phrase falls back to break. `_fragment`/`_units` join well-known, e-/mail, x/-/ray and state-/of-/the-/art; explicit review regressions pass. |
| 5 | Preserve original physical image coordinates through crops/scales/border | VERIFIED | Transform reverses actual x/y ratios and offsets. `_prepare_image` resets filename-derived DPR to 1 at `lookup/ocr.py:287`, then supplies actual ratios. Scale 1/1.25/1.5/2, negative-origin, edge, transparency and sample@2x.png regressions pass. |
| 6 | Portable OCR core imports without Qt, files or output | VERIFIED | Qt imports occur only inside `_prepare_image`; parsing/geometry/selection use stdlib. Existing python -S import/substance tests include lookup.ocr and pass. Public records/functions were imported and inspected independently. |
| 7 | Invalid image/point/output, missing packages and hung/failed child produce bounded private errors | VERIFIED | Regular-file/byte/dimension/pixel guards precede decoding; finite points and TSV shape/row/field/control checks; constant argv, shell=False, timeout=3 and controlled reasons. Image/process tests and all CLI reason/exit/privacy cases pass. |
| 8 | Production OCR writes no screenshot/TSV and sends no network request | VERIFIED | QBuffer encodes memory PNG; local tesseract receives stdin bytes and stdout TSV; no output path/debug config or network call in OCR module. Captured process errors are mapped to fixed codes. Fixture generation deliberately writes public test renders and is separate developer tooling. |
| 9 | Speculative compounds do not translate/save; one final query increments once | VERIFIED | `choose_query` calls only DictSet.find. CLI invokes translate.lookup once after choosing the query and passes recognized line as context. Test wraps real translator and reads real SQLite rows: only break out, count 1 then 2; no speculative break row; no-save leaves rows empty. |
| 10 | Existing word/text/list-dicts, offline/no-save, exit/error and resource behavior remain compatible | VERIFIED | Existing parser actions and result renderer retained, image/point pairing validated separately, final resource closure retained. Fresh verifier run includes legacy CLI/privacy/import tests; orchestrator's final full suites include previous phase tests. |

**Score:** 10/10. No override was needed.

## Artifact and Wiring Verification

| Artifact | Existence/substance | Wiring and real data |
|---|---|---|
| lookup/ocr.py | Real parser, geometry, lexical selection and image/process adapter; no placeholder markers | CLI and calibration call recognize_image; TSV process bytes flow through parse_tsv/Transform/select_word into Selection. |
| lookup/__main__.py | Real image/point route and fixed diagnostics | Recognition -> offline candidate checks -> actual translate.lookup -> existing SQLite store -> requested terminal result. Rejection exits before resources. |
| tests/test_ocr.py | Independent TSV/Word inputs and explicit expected geometry/selection | Invokes production parser/selection/query functions, including review regressions. |
| tests/test_ocr_image.py | Generated QImages, fake process boundary and geometry/privacy/resource regressions | Production preparation/process wrapper is exercised; real pixel assertions cover DPR and transparency. |
| tests/test_ocr_cli.py | Temporary real StarDict and SQLite; optional actual OCR fixture loop | Mocked recognition isolates persistence contracts; explicit target test does not mock recognition and uses the same main route for all 96 points. |
| tests/test_core_imports.py and tests/test_privacy.py | Existing substantive import/privacy checks remain | OCR import checks were extended. OCR-specific process sentinel/error checks live in test_ocr_image/test_ocr_cli rather than changing test_privacy; coverage exists despite that planned file-placement variation. |
| tools/gen_ocr_fixtures.py | Actual Breeze availability check, Qt widgets/palettes, fresh scale processes, layout-derived points | Produces versioned public images and manifest; no OCR-derived expected words/points. |
| tools/calibrate_ocr.py | Actual tesseract availability and non-skipped matrix/check runner | Calls production recognition, compares word/ordered source-line tokens/candidate order, selects fastest fully passing setting. |
| tests/fixtures/ocr/manifest.json and images | 16 real image files, 96 unique expected cases, all theme/scale/font combinations | Used by calibration and actual CLI gate; origin is explicitly rendered-widget, not live desktop capture. |
| 03-CALIBRATION.json and 03-CHECK.json | Measured per-case outputs/environment/timing | Independent audit verified eight matrix settings, 746 historically passing records and current strict 96/96 check against manifest expectations; chosen defaults agree with source. |

Key links were traced manually through calls and actual values, not only imports.
`DictSet.find` yields actual reader articles; translate.lookup uses real cache/
dictionary/storage implementations, and CLI prints the resulting values.
No static empty result substitutes for the OCR or dictionary data path.

The GSD artifact heuristic incorrectly reports flow-style exports arrays as one
literal name (`[OcrError, Word, ...]` and `[Recognition, recognize_image]`). A
fresh Python import/callable check verified all nine actual public symbols;
source definitions and executing tests corroborate them. This is a tooling
false positive, not a missing export or an applied verification override.
The test-to-store link is also established by CLI's real open_store call and
test SQLite queries, regardless of the test file's direct sqlite3.connect use.

## Fresh Verifier Checks

| Check | Observed result |
|---|---|
| python -m unittest tests.test_ocr tests.test_ocr_image tests.test_ocr_cli tests.test_cli tests.test_privacy tests.test_core_imports | 39 tests in 2.633s, OK, one opt-in target OCR skip |
| Independent raw manifest/report audit | 16 combinations/96 unique cases; all 746 passing historical matrix records satisfy strict ordered line/word/candidate expectations; current check 96/96 |
| Actual Python export import/introspection | All nine required classes/functions callable |
| Source anti-pattern scan | No TODO/FIXME/placeholder or empty implementation in production OCR/CLI/tool scope |

The target skip in the verifier's local command is not counted as evidence of
actual OCR execution. Direct execution output supplied by the orchestrator
after the final source fixes separately records:

- Windows 3.14: 509 tests, 25.010s, OK, seven skips.
- Windows 3.12: 509 tests, 24.763s, OK, seven skips.
- Arch: 509 tests, 10.016s, OK, three skips.
- Explicit Arch LOOKUP_TEST_OCR=1 CLI gate: five tests, 21.225s, no skips,
  including all 96 actual image points.
- Separate current-source defaults gate: 96/96, strict ordered source line,
  median 218.1ms; raw current report independently audited above.

## Requirement Traceability

| Requirement | Plans | Outcome | Evidence |
|---|---|---|---|
| CAPT-03 | 03-01/02/03 | SATISFIED | Bounded nearest/direct selection, invalid/noise/low-confidence rejection, recognition-before-store route, actual negatives and SQL/network tests. |
| CAPT-04 | 03-01/02/03 | SATISFIED | Offline compound-first probing, fallback, explicit/multipart hyphens, real phrase dictionary and final-query count tests. |

REQUIREMENTS.md maps exactly these two IDs to Phase 3; no orphaned phase
requirement was found. Their pending checkboxes are transition bookkeeping
for the orchestrator, not absent implementation.

## Limits and Deferred Scope

No unresolved BLOCKER or WARNING affects this phase's must-have truths.
No human-only item is required to decide this deterministic CLI/fixture scope.
Agent acceptance under --auto is distinct from human testing.

These fixtures demonstrate representative actual Qt/Breeze widget rendering,
not arbitrary applications or desktop capture correctness. Global shortcuts,
cursor capture, screenshots, logical monitor coordinates and focus belong to
Phase 4/5. End-to-end desktop latency is Phase 8; the OCR median is not a claim
of that milestone's complete performance target. Real MDX/DSL compatibility
remains the explicitly unverified Phase 8 follow-up from Phase 2.

The predeclared low-risk subprocess buffering residual and decoder trust
transfer are documented in 03-SECURITY.md; no streaming allocation-bound or
exhaustive security-proof claim is made. Historical SUMMARY/security counts
precede the review fixes; the final results are in 03-REVIEW-FIX.md and this
report. Independent review findings CR-01/CR-02/WR-01 have substantive fixes
and passing regressions in the inspected current source.

_Verifier: independent gsd-verifier agent. No implementation/state/config
changes or commits performed._
