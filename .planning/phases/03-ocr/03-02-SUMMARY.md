---
phase: 03-ocr
plan: 02
subsystem: ocr
status: complete
completed: 2026-10-25
requirements-completed: [CAPT-03, CAPT-04]
key-files:
  created: [tests/test_ocr_image.py, tools/gen_ocr_fixtures.py, tools/calibrate_ocr.py, tests/fixtures/ocr/manifest.json]
  modified: [lookup/ocr.py, tests/test_ocr.py]
provides: [memory-only image preparation, bounded tesseract process, genuine Breeze fixtures, measured defaults]
affects: [03-03, 04, 08]
---

# Phase 3 Plan 2 — Real OCR and calibration

Lazy Qt decoding preflights regular-file size, dimensions and finite in-image
points; crops at most 4096x256 source pixels, flattens transparency, optionally
inverts dark backgrounds, scales and adds a border. QBuffer sends PNG bytes
through tesseract stdin; TSV returns through stdout. No production screenshot,
TSV or debug file is written. Three-second timeout; fixed private error codes.
One OpenMP thread avoids CPU oversubscription in the VM.

VirtualBox arch-kde was powered off during research; started it headlessly and
reprobed tools: Qt 6.12.0, actual Breeze style, tesseract 5.5.3, eng/osd data.
Generated 16 Qt widget renders: light/dark palettes, scales 1/1.25/1.5/2,
font sizes 9/16. Source is honestly rendered-widget, not live desktop capture.
96 independent public-text points cover words, inter-word gap, compound,
hyphen, blank space and a visible drawn icon. Expected points use Qt layout,
not OCR output; manifest includes gap bounds and integrity tests verify them.

The first matrix exposed an expectation-construction defect: advance widths
placed large-font gap points at a tie, not nearer English. Corrected fixture
geometry using QFontMetricsF tight glyph bounds, retained the same expected
words and reran all eight settings. Also replaced an empty theme-provided
close icon with a drawn visible cross. These are fixture corrections, not
relabeled OCR outcomes. Initial exploratory matrices are not acceptance proof.

Final matrix: PSM6/11 x enlargement1/2 x invert never/auto. Four 2x settings
passed 96/96. Fastest passing run: PSM6, 2x, auto inversion, median 212.8ms.
Frozen defaults passed a separate 96/96 --check run, median 234.7ms. Full
per-case outputs, settings, environment and timings are in 03-CALIBRATION.json
and 03-CHECK.json. Confidence 50, nearest X/Y 0.75/0.25 text height, hyphen gap
0.5 and pair gap 1.5 remain unchanged; all positive/negative cases pass.

Verification: focused portable/image/CLI checks passed; Windows 3.14/3.12 full
suites each passed 506 tests (7 skips). Target actual CLI fixture integration
passed all five tests, including all 96 image cases without skips, in 22.167s.

Threats T-03-04..10: file/pixel bounds and pre-decode tests; constant argv and
shell=False; timeout; private errors and Unicode control rejection; truthful
fixture origin; target-distributed decoder trust transfer. Planned low-risk
T-03-09 remains accepted: subprocess buffers trusted executable output before
the 4MiB TSV validation, not a streaming allocation bound.

Limit: finite representative widget renders do not establish arbitrary desktop
OCR accuracy. Desktop capture and logical monitor coordinates remain Phase 4.
