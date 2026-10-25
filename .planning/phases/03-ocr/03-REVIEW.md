---
phase: 03-ocr
reviewed: 2026-10-25
depth: standard
files_reviewed: 7
files_reviewed_list:
  - lookup/ocr.py
  - lookup/__main__.py
  - tests/test_ocr.py
  - tests/test_ocr_image.py
  - tests/test_ocr_cli.py
  - tools/gen_ocr_fixtures.py
  - tools/calibrate_ocr.py
findings:
  critical: 2
  warning: 1
  info: 0
  total: 3
status: resolved
unresolved: 0
---

# Phase 3 code review

Follow-up: all three findings resolved and regression-tested; see
03-REVIEW-FIX.md. Original findings below remain as audit history.

Reviewed actual source and the three plans/summaries. Two correctness defects
have local reproductions. Existing passing fixture results do not cover these
input forms. No implementation, state or configuration files were modified.

## Critical issues

### CR-01 — BLOCKER: Qt device-pixel ratio changes physical image coordinates

**File:** `D:/User/Documents/GitHub/LookUpLinux/lookup/ocr.py:268`
and `:284`.

**Issue:** QImageReader assigns DPR=2 to a filename such as sample@2x.png.
QPainter.drawImage honors that DPR when painting into the new DPR=1 image,
so pixels are rendered at half their physical extent. Transform still reports
only crop/enlargement ratios. This violates the original-image-pixel point
contract: a point over visible text can return no word or a different word.

**Reproduction:** Save a 200x80 RGB image as sample@2x.png with a black rectangle
at x=100..119, y=20..39. QImageReader.read().devicePixelRatio() is 2.0.
_prepare_image(path, (110,30), 1, 'never') produces a white pixel at the expected
prepared position (118,38), while the rectangle appears around (58,18).
Its returned Transform is still scale_x=scale_y=1, border=8.

**Fix:** Reset the decoded image's DPR to 1.0 before copying/painting; all
subsequent image operations are explicitly in physical pixels. Add a real
@2x filename pixel/coordinate regression, alongside an ordinary filename.

### CR-02 — BLOCKER: valid split hyphenated words are rejected or truncated

**File:** `D:/User/Documents/GitHub/LookUpLinux/lookup/ocr.py:150`
through `:166`.

**Issue:** Joining requires each fragment to pass standalone normalization.
That rejects a legitimate single-letter component such as e- or x, even though
the complete e-mail/x-ray passes normalization. Joining also replaces the raw
token with a normalized string that has lost the last fragment's trailing
hyphen, preventing continuation of a chain. A valid state-of-the-art can
therefore become state-of and even generate a false spaced compound candidate.
This directly breaks CAPT-04 for common hyphenated lexical units.

**Reproduction:** With confident same-line boxes separated by gaps <=0.5 text
height, select_word over e in ['e-', 'mail'] or x in ['x', '-', 'ray'] returns
None. Over state in ['state-', 'of-', 'the-', 'art'], it returns word=state-of,
line='state- of- the- art', candidates=('state-of the-art',), instead of the
complete state-of-the-art unit. All boxes and confidence values are valid.

**Fix:** Validate lexical fragments under a join-only policy that permits one
Latin letter, validate the final joined word with the existing normalize
policy, and preserve whether the last source fragment ends with a hyphen
until the entire chain is consumed. Keep confidence, gap and line barriers.
Add independent tests for e-mail, x-ray and a chain of three or more parts,
including points over each constituent fragment.

## Warnings

### WR-01 — WARNING: calibration accepts incorrect source-line ordering

**File:** `D:/User/Documents/GitHub/LookUpLinux/tools/calibrate_ocr.py:27`.

**Issue:** line_ok checks membership for each expected token, rather than
ordered equality or an ordered subsequence. A returned line with all words
reversed, additional words, or missing repetitions can pass. Since that line
becomes sentence-translation context, this weakens the explicit source-line
calibration gate and can hide parser/selection regressions.

**Fix:** Compare the normalized ordered token lists exactly for these fixed
single-line fixtures (or use a documented ordered-subsequence rule where
partial context is intentionally allowed). Add a runner test showing that
reversed/repeated-token corruption fails without invoking real OCR.

---

Review depth: standard. Local diagnostic probes only; the reviewer did not
rerun the historical 506-test suites or target matrix. No performance findings
or style-only findings are included.
