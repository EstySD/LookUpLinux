---
phase: 3
slug: ocr
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-10-25
---

# Phase 3 — Validation Strategy

Source: 03-RESEARCH.md Validation Architecture. This is a plan, not a passing
test report. Existing framework is stdlib unittest; no new dependency.

## Test Infrastructure

| Property | Value |
|---|---|
| Pure quick run | python -m unittest tests.test_ocr |
| Image/CLI quick run | python -m unittest tests.test_ocr_image tests.test_ocr_cli |
| Full host suite | python -m unittest; py -3.12 -m unittest |
| Full target suite | python3 -m unittest |
| Actual fixture gate | Non-skipped OCR fixture/calibration runner in target environment |

## Requirement Coverage Plan

| Requirement / SC | Required proof | Planned file | State |
|---|---|---|---|
| CAPT-03 / SC2 | Box hits, bounded neighbors, ties, line IDs, 1/1.25/1.5/2 transforms and edges | tests/test_ocr.py | Wave 0 |
| CAPT-03 / SC3 | Noise, low confidence, NaN/inf, malformed TSV, blank/far/icon points rejected | tests/test_ocr.py | Wave 0 |
| CAPT-03 / SC3 | Invalid image/point, missing Qt/tesseract/eng, timeout; fixed private errors | tests/test_ocr_image.py | Wave 0 |
| CAPT-03 / SC3 | Rejection causes no lookup/network/word row | tests/test_ocr_cli.py | Wave 0 |
| CAPT-04 / SC4 | Compound before word, pair fallback, explicit hyphen fragments, no cross-line/large-gap pair | tests/test_ocr.py | Wave 0 |
| CAPT-04 / SC4 | Independent dictionary containing break out; one chosen key saved once | tests/test_ocr_cli.py | Wave 0 |
| SC1 | --image + --at, word + line + translation, offline/no-save, exit and timing conventions | tests/test_ocr_cli.py | Wave 0 |
| SC1 | Light/dark Breeze, 100/125/150/200%, small/large text, positive and negative points | tests/fixtures/ocr manifest + actual integration | Wave 0 |
| Core/privacy regression | OCR imports under python -S; no output/files on imports | tests/test_core_imports.py, tests/test_privacy.py | Extend |

## Executable Task Map

| Task | Requirements / criteria | Automated verification |
|---|---|---|
| 03-01/T1 | CAPT-03; D-01/D-02/D-03; TSV/transform/import safety | python -m unittest tests.test_ocr tests.test_core_imports |
| 03-01/T2 | CAPT-03/CAPT-04; SC2/SC3/SC4; D-04/D-05 | python -m unittest tests.test_ocr tests.test_core_imports |
| 03-02/T1 | CAPT-03; image/process privacy, D-01/D-02/D-03 | python -m unittest tests.test_ocr tests.test_ocr_image tests.test_core_imports |
| 03-02/T2 | SC1; D-07/D-08; independent Breeze matrix | python -m unittest tests.test_ocr_image |
| 03-02/T3 | CAPT-03/CAPT-04; SC1/SC3/SC4; D-04/D-07/D-08 | python tools/calibrate_ocr.py --fixtures tests/fixtures/ocr --check |
| 03-03/T1 | CAPT-03/CAPT-04; CLI SC1/SC3; D-03/D-06 | python -m unittest tests.test_ocr_cli tests.test_cli tests.test_core_imports |
| 03-03/T2 | All four SCs; one final count, no network on rejection; D-04/D-05/D-07/D-08 | python -m unittest tests.test_ocr_cli tests.test_privacy tests.test_cli; target LOOKUP_TEST_OCR=1 integration |

All task verification files are created by their owning task before its check;
no task relies on an absent verification command without creating its tests.
Plans are sequential waves 1/2/3 because core, measured adapter and CLI consume
each other's contracts; no same-wave file ownership overlap.

## Multi-Source Coverage Audit

| Source | Item | Plans | State |
|---|---|---|---|
| GOAL | Saved screenshot + point gives word, line, translation | 01/02/03 | COVERED |
| GOAL | SC1 Breeze themes/scales/fonts, measured preprocessing and timings | 02/03 | COVERED |
| GOAL | SC2 nearest bounded between-word selection | 01/02 | COVERED |
| GOAL | SC3 reject noise/low confidence without saving | 01/02/03 | COVERED |
| GOAL | SC4 compound before word and hyphen joining | 01/03 | COVERED |
| REQ | CAPT-03 | 01/02/03 | COVERED |
| REQ | CAPT-04 | 01/02/03 | COVERED |
| RESEARCH | Strict TSV/line identities, positioned invalid barriers, actual transform ratios | 01 | COVERED |
| RESEARCH | Lazy Qt/caps/memory encoding, finite process/fixed errors, buffered-output limit | 02 | COVERED |
| RESEARCH | Independent fixture dictionary, single final lookup/save, side-effect tests | 01/03 | COVERED |
| RESEARCH | Target availability, actual Breeze origin, fixed matrix and non-skipped acceptance | 02/03 | COVERED |
| CONTEXT | D-01 portable core and existing stack | 01/02 | COVERED |
| CONTEXT | D-02 physical pixels and explicit transforms | 01/02 | COVERED |
| CONTEXT | D-03 local finite private OCR and controlled dependency errors | 01/02/03 | COVERED |
| CONTEXT | D-04 confidence/bounded selection/noise rejection | 01/02/03 | COVERED |
| CONTEXT | D-05 line/hyphen/compound and final-only side effects | 01/03 | COVERED |
| CONTEXT | D-06 CLI flags/conventions/timings | 03 | COVERED |
| CONTEXT | D-07 reproducible honest matrix and measured settings | 02/03 | COVERED |
| CONTEXT | D-08 autonomous evidence-based acceptance and preserved MDX/DSL limits | 02/03 | COVERED |

No required source item is omitted. Desktop capture, KWin, shortcuts, tray,
packaging and doctor remain excluded exactly as the context defers them.

## Calibration Execution

Compare PSM 6/11, enlargement 1/2 and inversion policy against the same fixed
manifest. Record original pixel points, expected words/line tokens, fixture
provenance, font/style/Qt versions and per-case output/timing. Choose settings
from observed results; do not pass a matrix by changing expectations to OCR
output. Real Breeze renders and synthetic/custom-palette renders must be
identified accurately. Full screenshot capture/tray behavior is Phase 4/5.

Confidence >=50 and bounded neighbor distances in research are starting
hypotheses only. Freeze final values after both positive and negative cases
pass. Compound tests need their own dictionary entry because real Mueller
has no break out headword (Phase 2 VM evidence).

## Sampling

- Per task: affected test modules.
- Per wave: full host suites.
- Before phase acceptance: full host/target suites plus actual non-skipped
  fixture test; all four SCs checked, security threats resolved.

## Current Environment Limit

Host Python 3.14.3/3.12.0 and PyQt6/Qt 6.11.0 available; in-memory image
encoding smoke passed. No tesseract on host PATH; no Breeze in host styles.
Two fresh ssh archvm probes failed with connection refused during research.
Recheck/recover target access before actual calibration; do not mark this
gate passed based on earlier Phase 2 evidence or skipped OCR integration.

## Sign-Off

- [ ] Wave 0 tests and independent fixtures exist.
- [ ] Pure selection and CLI side-effect tests pass.
- [ ] Fixture calibration completed and settings recorded.
- [ ] Host and target suites pass.
- [ ] Security and privacy checks pass.
- [ ] Agent acceptance recorded honestly under --auto.

Approval: pending execution evidence.
