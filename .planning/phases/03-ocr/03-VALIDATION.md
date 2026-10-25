---
phase: 3
slug: ocr
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-10-25
verified: 2026-10-25
---

# Phase 3 — Validation

All seven planned tasks have behavioral checks and all four roadmap criteria
have observed evidence. Tests are stdlib unittest; image preparation uses
existing optional Qt. No new dependencies or watch-mode commands.

| Task | Requirements / proof | Automated check | Result |
|---|---|---|---|
| 03-01/T1 | CAPT-03, strict TSV, actual-ratio geometry, quiet imports | tests.test_ocr + tests.test_core_imports | Pass |
| 03-01/T2 | CAPT-03/04, bounded hits, rejection barriers, hyphens, offline pairs | tests.test_ocr | Pass |
| 03-02/T1 | CAPT-03, image/process caps, private errors, timeout, DPR and transparency | tests.test_ocr_image | Pass |
| 03-02/T2 | SC1, actual Breeze renders and independent layout expectations | tests.test_ocr_image manifest integrity | Pass |
| 03-02/T3 | SC1/3/4, measured preprocessing, all positive/negative points | tools/calibrate_ocr.py --fixtures tests/fixtures/ocr --check | 96/96, no skips |
| 03-03/T1 | SC1/3, CLI argument/error/timing/output behavior | tests.test_ocr_cli + tests.test_cli | Pass |
| 03-03/T2 | CAPT-03/04, exact final query/count/context, no side effects on rejection | LOOKUP_TEST_OCR=1 python3 -m unittest tests.test_ocr_cli -v | 5 tests, all 96 image points, no skips |

Full commands: python -m unittest; py -3.12 -m unittest; target python3 -m
unittest. Run affected modules after edits and full suites at wave/acceptance
boundaries. The ordinary full suite skips target opt-in OCR and real Mueller;
the required explicit actual OCR gate above ran without skips.

## Final evidence after independent review fixes

| Environment | Tests | Time | Result |
|---|---:|---:|---|
| Windows Python 3.14 | 509 | 25.010s | OK, 7 skips |
| Windows Python 3.12 | 509 | 24.763s | OK, 7 skips |
| Arch Python 3.14 | 509 | 10.016s | OK, 3 skips |
| Arch actual image CLI | 5 including 96 image cases | 21.225s | OK, no skips |
| Arch frozen defaults, strict ordered line check | 96 cases | median 218.1ms | All pass |

03-CALIBRATION.json records eight real settings; four 2x configurations pass.
Fastest passing matrix run: PSM6, 2x, auto inversion, median 212.8ms.
03-CHECK.json is the separate current-source defaults check. Confidence 50,
nearest X/Y 0.75/0.25, hyphen gap 0.5 and pair gap 1.5 remain the tested policy.

96 points span 16 actual Qt/Breeze widget renders: light/dark, scales
1/1.25/1.5/2, font sizes 9/16. Known public text and drawn nontext icon;
no private screenshot or live desktop capture. Geometry expectations use Qt
glyph layout, not OCR. Initial inter-word fixture geometry and empty icon
defects were corrected before final calibration, without relabeling words.

## Review and coverage closure

- Core/CLI tests first failed before implementation.
- Independent review reproduced DPR and split-hyphen defects; regressions failed
  before fixes and now pass. Ordered repeated-line regression also passes.
- All 746 historically passing matrix records additionally match strict
  ordered source-line expectations.
- 03-SECURITY.md closes the 14 authored threats at ASVS L1, with transferred
  decoder trust and predeclared trusted-process buffering residual explicit.
- Actual desktop capture, logical monitor geometry and focus are Phase 4/5.
- Genuine Breeze/tesseract availability restored by starting the powered-off VM.
- Real MDX/DSL compatibility remains Phase 8's explicit unverified follow-up.

Sign-off: all required automated, target fixture and privacy gates pass.
Acceptance is agent judgment under the user's explicit --auto instruction;
human testing is not claimed.
