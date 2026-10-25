# Phase 3: OCR words from saved screenshots — Research

Researched: 2026-10-25. Confidence: HIGH for APIs/core integration; MEDIUM for
the proposed selection/preprocessing policy until fixture calibration.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-01: Keep TSV parsing and geometric selection stdlib-only and independently
  testable without Qt, tesseract, a desktop or a VM. Image preparation may use
  lazily imported PyQt6, already in the target stack; no new pip dependency.
- D-02: Image point coordinates are physical pixels in the original image.
  Preserve/reverse crop and resize transforms explicitly. Monitor logical
  coordinates and offsets belong to Phase 4; cover geometry outside the VM.
- D-03: Use subprocess tesseract with English data, TSV stdout, finite timeout,
  fixed reason codes, no shell, no persisted screenshot or printed query/error
  details. Missing packages and invalid images receive actionable CLI errors.
- D-04: A word box hit wins; otherwise choose the nearest word only within
  a bounded neighborhood related to text height. Reject distant blank space,
  low confidence, icon/noise, non-Latin/digit garbage using normalization.
  Tune concrete thresholds against fixtures and lock them in behavioral tests.
- D-05: Preserve the selected line as context. Hyphens between nearby fragments
  join into one lexical unit; do not indiscriminately glue separate words.
  Adjacent two-word dictionary candidates (including break out over break)
  are tried before the standalone word. Avoid online calls and database writes
  for speculative candidates; persist just the chosen final query once.
- D-06: CLI python -m lookup --image PATH --at X,Y uses existing offline,
  no-save, output and exit-code conventions. No accepted word means no DB row
  and no network. LOOKUP_TIMING=1 exposes stage durations without query text.
- D-07: Build reproducible, versioned rendered-image fixtures in light/dark
  Breeze, scales 100/125/150/200%, small/large text, compound, hyphen, blank and
  icon cases. Record their origin honestly; synthetic fixtures do not count
  as live desktop captures. Use the accessible Arch VM to obtain representative
  real Qt/Breeze renders as needed. Compare PSM 6/11, enlargement and inversion
  against the same expected words/points; record chosen parameters and results.
- D-08: Acceptance is evidence-based and autonomous. Missing real MDX/DSL files
  remain the explicit Phase 8 follow-up from Phase 2, not an OCR blocker.

### Agent's Discretion
Concrete API names, thresholds and preprocessing parameters may be resolved
within D-01 through D-08. [VERIFIED: 03-CONTEXT.md]

### Deferred Ideas (OUT OF SCOPE)
Desktop screenshots, cursor acquisition, KWin positioning, shortcuts and tray
belong to Phases 4/5. Packaging and doctor belong to Phase 7. Do not expand
this phase into a desktop app or weaken the production roadmap scope.

The decisions and deferred text above are copied verbatim from the canonical
context. [VERIFIED: .planning/phases/03-ocr/03-CONTEXT.md]
</user_constraints>

## Project Constraints (from AGENTS.md)

No repository AGENTS.md or project .codex/skills or .agents/skills directory
exists. Session-provided AGENTS instructions require scoped autonomous work,
rg-first inspection, small diffs, preserving user edits, apply_patch for
manual edits, proportionate tests and fresh evidence. --auto delegates routine
acceptance decisions to the agent; do not claim human testing.
[VERIFIED: Test-Path probes and inherited user instructions]

<phase_requirements>
## Phase Requirements

| ID | Required behavior | Research support |
|---|---|---|
| CAPT-03 | Nearest word between words; reject noise/low confidence without saving | Geometric bounded selection, fail-closed token validation, CLI side-effect tests |
| CAPT-04 | Compound before standalone; join hyphenated tokens | Adjacent same-line candidates with offline DictSet.find, single final lookup |

All four roadmap success criteria additionally require CLI image/point input,
line/context, calibrated light/dark Breeze fixtures at 100/125/150/200%,
small/large text, and stage timings. [VERIFIED: .planning/ROADMAP.md Phase 3;
.planning/REQUIREMENTS.md]
</phase_requirements>

## Summary

Use one quiet OCR module with a stdlib parser/selector and lazy Qt preparation,
then connect its accepted result to the existing CLI. Keep provisional choices
measurable: PSM, enlargement, inversion and confidence thresholds must be
selected against fixtures during execution, not declared proven by this
research. [VERIFIED: 03-CONTEXT.md D-01/D-04/D-07]

The existing DictSet.find performs offline lookup and returns a truthy
SearchResult only for articles. translate.lookup owns network/cache/count
updates, so speculative compound candidates must never call it.
[VERIFIED: lookup/dicts.py:347; lookup/translate.py:139-229]

## Architectural Responsibility Map

| Capability | Primary owner | Secondary owner | Rationale |
|---|---|---|---|
| Image/point validation and preprocessing | Lazy image adapter in lookup/ocr.py | Qt QImageReader/QImage | Keep pure selection importable without Qt |
| Text/boxes/confidence | Local tesseract process | TSV parser | No remote OCR |
| Word and context selection | Pure OCR core | normalize.normalize | Deterministic geometry and lexical policy |
| Compound lookup | Quiet candidate resolver | Existing DictSet.find | Side-effect-free dictionary checks |
| Final translation/persistence | Existing translate.lookup | store.py | Count only final chosen query |
| Output/errors/timing | lookup/__main__.py | OCR result fields | Libraries remain quiet |

These are proposed assignments, grounded in the existing ownership pattern.
[VERIFIED: lookup/__main__.py, lookup/translate.py, 03-CONTEXT.md]

## Standard Stack

| Component | Verified availability/version | Use |
|---|---|---|
| Python stdlib | Windows 3.14.3 and 3.12.0 | dataclasses, csv or split-based TSV parser, math, subprocess, time, unittest |
| PyQt6 / Qt | Windows 6.11.0 / 6.11.0 | Lazy QImageReader, QImage, QBuffer, image scaling/inversion |
| tesseract | Not on Windows PATH; current VM probe unavailable | Local executable, eng data, stdin image and stdout TSV |
| Breeze style | Not among local Windows styles | Requires target VM/real Breeze renders |

Versions are installed versions, not a recommendation to upgrade packages.
[VERIFIED: python --version; py -3.12 --version; PyQt6.QtCore constants;
Get-Command tesseract; QStyleFactory.keys probes]

No package installation or extra Python dependency is required by this plan.
Use the target system's existing PyQt6/tesseract/English data; diagnose absent
dependencies explicitly before integration tests.
[VERIFIED: .planning/PROJECT.md stack; 03-CONTEXT.md D-01/D-03]

## Architecture Patterns

Input image + physical point → validate → bounded strip/preprocess in memory
→ tesseract → TSV records → word hit/bounded neighbor → same-line lexical
units → offline compound probes → one final translate.lookup → CLI result.

Recommended entry points: parse_tsv(bytes), select_word(records, point),
recognize_image(path, point), and choose_query(selection, dictset), with
small immutable records for word boxes and selected text/context/candidates.
These names are recommendations, not existing exports.
[VERIFIED: existing dataclass/error/helper conventions in lookup/dicts.py and
lookup/online.py; context D-01 through D-06]

### TSV and geometry

The official TSV example contains level, page_num, block_num, par_num,
line_num, word_num, left, top, width, height, conf and text. Word rows have
level 5; confidence is decimal, while structural rows use -1. Group lines by
the full page/block/paragraph/line identity, not line_num alone. PSM 6 expects
one uniform text block; PSM 11 targets sparse text. Output ordering is not a
substitute for geometric sorting. [CITED:
https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html;
https://github.com/tesseract-ocr/tesseract/blob/main/doc/tesseract.1.asc]

Recommendation: parse numeric fields strictly; reject non-finite confidence,
invalid/negative geometry, huge fields/row counts and malformed output. Retain
structural separators or rejected-token positions so removing noise never
makes distant words adjacent. A rejected box under the point must not silently
redirect selection to another nearby valid word. Preserve source punctuation
in displayed context, normalize only candidate counting/search keys.
[VERIFIED: normalize.normalize rejection rules; context D-04/D-05;
recommendation derived from those contracts]

Recommendation: measure distance to box edges, not box centers. Choose direct
hits before nearest neighbors; enforce both vertical line tolerance and a
finite horizontal distance scaled to text height. Start calibration with
confidence >=50, vertical expansion <=0.25 word height and horizontal gap
<=0.75 word height. These are tunable test hypotheses, NOT measured accuracy
claims. Resolve ties deterministically (distance, reading order).
[VERIFIED: CAPT-03 and context D-04; proposed policy awaiting calibration]

Keep coordinates in original pixels. If preprocessing maps
u=(x-crop_left)*scale_x+border, invert with
x=(u-border)/scale_x+crop_left; use actual resulting width/height ratios.
Do not apply Qt deviceIndependentSize or desktop scale to an image point.
Test 1/1.25/1.5/2 factors and crop edges independently.
[VERIFIED: context D-02; algebraic inverse]

### Image preparation

QImage supports crop/copy, smooth scaling, format conversion, invertPixels
and save to QIODevice. QBuffer provides memory-backed image encoding.
QImageReader offers dimensions before read and reports null images on failure;
canRead alone does not prove decoding succeeds. Guard source file size,
dimensions/pixels, scaled pixels and null results; keep metadata rotation off
unless coordinates are transformed deliberately. [CITED:
https://doc.qt.io/qt-6/qimage.html;
https://doc.qt.io/qt-6/qbuffer.html;
https://doc.qt.io/qt-6/qimagereader.html]

Recommendation: decode once, crop a horizontal strip around the point with
enough vertical padding and full bounded width for line context, then test
1x/2x enlargement and luminance-based inversion. Cap input dimensions and
prepared area explicitly; QImageReader's allocationLimit does not bound later
QImage.scaled allocations. Do not mutate the process-wide allocation limit
as the only defense. [VERIFIED: local QImage/QImageReader smoke test;
recommendation from image-boundary contract]

Tesseract's quality guide discusses rescaling, dark-text preparation,
transparency and borders, and warns that tight or excessive borders can
hurt recognition. This is motivation for a fixed fixture comparison, not
evidence that any particular multiplier wins on KDE UI text. Do not add
custom thresholding, deskew or trained models before the basic comparison.
[CITED: https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html]

### Process boundary

Use a fixed argument list:
`["tesseract", "stdin", "stdout", "-l", "eng", "--psm", str(psm), "tsv"]`.
stdin/stdout aliases and TSV config are documented; no temporary image/output
file is needed. Never enable debug-image configs. [CITED:
https://github.com/tesseract-ocr/tesseract/blob/main/doc/tesseract.1.asc]

Use subprocess.run(input=png_bytes, capture_output=True, timeout=finite,
check=False), binary mode, shell=False. TimeoutExpired contains captured
data and must become a fixed code with suppressed exception context; do not
print it. Use a modest prepared-image cap plus bounded parsed TSV; document
that capture_output itself buffers output, so a hard pre-allocation output
bound would require Popen streaming rather than a post-capture len check.
[CITED: https://docs.python.org/3/library/subprocess.html]

Suggested fixed reasons: missing_pyqt6, missing_tesseract, missing_eng,
invalid_image, invalid_point, too_large, timeout, bad_output, process_failed.
Missing English data must be distinguishable from generic process failure
with a controlled probe/message classification, not arbitrary stderr output.
[VERIFIED: existing TranslateError/DictError fixed-code pattern; D-03]

### Compound and hyphen behavior

Generate only adjacent same-line candidate pairs containing the selected
word, forward before backward; try full phrase via DictSet.find before the
single word. Require bounded gaps and no punctuation/invalid-token barrier.
Join explicit nearby hyphens with their neighboring fragments before pair
generation; also support already-single-token well-known. Return the chosen
text only, then call translate.lookup once with selected line context.
[VERIFIED: CAPT-04; DictSet.find and normalize; recommended resolver policy]

Important real-dictionary caveat: the Phase 2 Mueller probe found no break out
entry. Test compound priority using an independent fixture dictionary that
contains it; lack of a real Mueller phrase is not an OCR recognition failure.
[VERIFIED: .planning/phases/02-offline-dicts-translate/02-VM-RESULTS.md]

## Don't Hand-Roll

| Problem | Use | Avoid |
|---|---|---|
| Image decoding/resampling | Qt QImageReader/QImage | Custom PNG parser or image resampler |
| OCR | Local tesseract TSV | Remote OCR or model training |
| Token validation | Existing normalize | New inconsistent Latin/digit rules |
| Dictionary candidates | Existing DictSet.find | New dictionary parser or online speculation |
| Persistence/cache | Existing translate.lookup | Duplicate saves or direct ad-hoc SQL |
| Process lifecycle | subprocess.run finite timeout | Shell command concatenation |

[VERIFIED: project stack, existing APIs and locked context]

## Common Pitfalls

- Blindly selecting the nearest valid token converts blank space or a rejected
  icon into an unrelated word; test explicit rejection before persistence.
- Filtering malformed/low-confidence rows before adjacency checks can create
  nonexistent compounds across gaps.
- Reusing line_num across separate blocks mixes unrelated contexts.
- Applying resize twice or mixing logical/pixel coordinates shifts selection.
- Running final lookup for candidate phrases can send/snapshot/save unwanted
  text; restrict speculation to DictSet.find.
- A passing skipped integration suite is not calibrated OCR evidence.
- Windows Qt lacks Breeze locally; do not call Fusion/custom palettes actual
  Breeze captures.
These are implementation risks inferred from the verified contracts/APIs,
not claims of existing defects. [VERIFIED: code inspection and probes above]

## Code Examples

The following QImage operations were run successfully with local PyQt6
without creating QApplication or files:
[VERIFIED: local smoke probe 2026-10-25]
```python
from PyQt6.QtCore import QBuffer, QIODevice, Qt
from PyQt6.QtGui import QImage
image = QImage(24, 16, QImage.Format.Format_RGB32)
image.fill(Qt.GlobalColor.white)
image = image.scaled(48, 32, Qt.AspectRatioMode.IgnoreAspectRatio,
                     Qt.TransformationMode.SmoothTransformation)
image.invertPixels()
buffer = QBuffer()
buffer.open(QIODevice.OpenModeFlag.WriteOnly)
assert image.save(buffer, "PNG")
png_bytes = bytes(buffer.data())
```

Keep these imports inside image-preparation functions. Extend
tests/test_core_imports.py to import the new OCR module under python -S;
ordinary lookup --word must work without Qt.
[VERIFIED: tests/test_core_imports.py subprocess contract; D-01]

## Environment Availability

| Dependency | Current research probe | Fallback / action |
|---|---|---|
| Python host | 3.14.3 and 3.12.0 available | Pure tests and CLI mocks run now |
| PyQt6/Qt host | 6.11.0/6.11.0; QImage PNG smoke passed | Preprocessing tests run locally |
| tesseract host | Not on PATH | Target VM for actual OCR; explicit skip/missing-tool test locally |
| Breeze host | Windows/Fusion styles only | Genuine Breeze renders require target environment |
| ssh archvm | Two attempts failed: banner exchange, UNKNOWN port -1, connection refused | Recheck target availability; preserve earlier VM evidence as historical |

[VERIFIED: fresh read-only probes during research]

No installs or screenshot collection were performed. Parent had successfully
used tesseract and Arch 3.14.8 earlier in this session, but this research does
not claim current VM availability, tesseract version or installed eng data.
[VERIFIED: inherited parent evidence versus current failed SSH probes]

Documentation lookup: no Context7 MCP/installed ctx7 CLI was available;
official upstream pages were fetched instead. No npx install was attempted
because the parent prohibited package installation during research.
[VERIFIED: tool metadata and Get-Command ctx7; parent instruction]

## Validation Architecture

| Property | Value |
|---|---|
| Framework | Existing stdlib unittest |
| Config | None |
| Quick pure run | python -m unittest tests.test_ocr |
| Quick integration | python -m unittest tests.test_ocr_image tests.test_ocr_cli |
| Full | python -m unittest; py -3.12 -m unittest; target python3 -m unittest |

[VERIFIED: tests layout; proposed new test modules are Wave 0 work]

| Requirement / criterion | Tests to implement | Verification |
|---|---|---|
| CAPT-03 / SC2 | Hit, bounded between-word choice, ties, line identities, transforms | Pure TSV unit suite |
| CAPT-03 / SC3 | Low confidence, NaN/inf, garbage, icon, blank/far point, invalid image | Pure + image/CLI tests; forbidden network and unchanged DB |
| CAPT-04 / SC4 | break out before break, missing phrase fallback, hyphen joins, no cross-line candidates | Fixture dictionary; assert one saved final key |
| SC1 | Image CLI output includes word, source line, translation; timing stage names | CLI mocks + actual fixture integration |
| SC1 calibration | 2 themes ×4 scales ×2 font sizes, plus blank/icon/compound/hyphen cases | Fixed manifest, original-pixel points, expected words; PSM6/11 × enlargement1/2 × inversion comparison |

[VERIFIED: requirement mapping from roadmap; proposed tests satisfy contracts]

Per task: affected tests. Per wave: full host suites. Phase gate: full suites
plus non-skipped tesseract fixture verification on target; record chosen
parameters and per-case pass/fail, not just aggregate accuracy. Fixture
generation should record font, Qt/style versions, palette, scale, provenance
and expected boxes/points. Rendered widget captures are not screenshots of
an arbitrary live desktop. [VERIFIED: D-07 and project validation conventions]

Wave 0 gaps: tests/test_ocr.py, test_ocr_image.py, test_ocr_cli.py; independent
TSV and dictionary fixtures, a reproducible image fixture generator/manifest,
and calibration runner. No new framework installation.
[VERIFIED: rg --files tests; these files do not yet exist]

## Security Domain

Security enforcement is enabled at ASVS level 1 in project config.
This desktop/local phase primarily needs input validation, resource bounds,
process invocation safety and query/screenshot privacy, rather than new
authentication/session/cryptography mechanisms.
[VERIFIED: .planning/config.json and Phase 3 scope]

| Threat | STRIDE | Required mitigation / proof |
|---|---|---|
| Image/point/TSV malformed or huge | Tampering / DoS | Size/dimension/pixel/row/field bounds; non-finite numbers rejected |
| Subprocess command injection | Tampering / elevation | Constant executable/argument list, shell=False, bytes through stdin |
| Hung OCR child | DoS | Finite timeout, child reaped, fixed error |
| Screenshot/query in files/logs | Information disclosure | Memory-only PNG/TSV; no debug configs; suppressed exception details |
| Accidental online/save on noise | Information disclosure / data integrity | OCR acceptance before final lookup; no-network/no-row assertions |
| Speculative compound duplicate save | Data integrity | Offline probes; final lookup exactly once |

Recommended threat register for planner; no claim of an implemented
mitigation yet. [VERIFIED: boundary analysis against D-01..D-06]

## State of the Art

Use documented Tesseract 5 CLI/TSV and existing Qt6 APIs; no migration,
dependency upgrade or model training is required. Exact target executable
version and empirical recognition choices remain execution-time checks.
[CITED: upstream Tesseract manual; VERIFIED: project constraints]

## Assumptions Log

No unverified factual claim has been promoted to a locked decision. Numerical
selection/preprocessing proposals above are explicitly calibration hypotheses;
they require measurements, not a user confirmation question under --auto.

## Open Questions (RESOLVED for planning; execution checks pending)

1. RESOLVED planning procedure: Plan 03-02 reprobes the restarted VM and obtains
   actual Qt/Breeze fixtures. Availability is checked again during execution.
2. RESOLVED planning procedure: Plan 03-02 runs the fixed PSM/enlargement/inversion
   matrix and chooses a passing policy from measurements. Results pending.
3. RESOLVED planning procedure: Plan 03-02 calibrates confidence/distance bounds
   against positive/negative fixtures and freezes pure regression tests.

These are execution tasks, not reasons to stop planning or ask Denis.
[VERIFIED: --auto user instruction and scope]

## Sources

- https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html — TSV fields.
- https://github.com/tesseract-ocr/tesseract/blob/main/doc/tesseract.1.asc — stdin/stdout, modes, output configs.
- https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html — rescaling/background/border pitfalls.
- https://doc.qt.io/qt-6/qimage.html — image transforms and QIODevice encoding.
- https://doc.qt.io/qt-6/qimagereader.html — preflight and read failures.
- https://doc.qt.io/qt-6/qbuffer.html — memory-backed byte buffer.
- https://docs.python.org/3/library/subprocess.html — binary input, timeout, buffering.
- Canonical local source paths listed in 03-CONTEXT.md.

All web sources above are primary documentation fetched during research;
no community claim was used as authoritative. Qt site currently presents
6.12 docs; used APIs were additionally checked in installed 6.11 via smoke
probe, and no newly introduced 6.12 API is recommended.
[VERIFIED: fetched documentation and local probe]

## Metadata

Confidence: stack/API HIGH; integration architecture HIGH; selection parameters
and calibration MEDIUM pending execution. Research valid for planning now;
reprobe VM/tool versions before fixture generation.
