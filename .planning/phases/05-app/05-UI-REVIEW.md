---
phase: 05
slug: app
audited: 2026-10-27
status: passed
overall_score: 24
original_score: 21
screenshots_reviewed: 10
blockers: 0
warnings: 0
remediated_findings: [V-01, C-01]
baseline: 05-UI-SPEC.md
---

# Phase 5 — UI Review

**Baseline:** Approved native Qt/Breeze UI contract.
**Screenshots:** Eight actual Arch/KDE production screenshots reviewed, light/dark
at100/125/150/200%, run `e7db94e3b1284cac8df220214b86c7ac`.
This is the supplied confirmation batch after transparent-text-viewport fixes.
No additional captures or VM mutations were performed. Existing images are in
the host temporary directory, outside the repository; root owns their deletion.
Web dev-server, responsive browser and registry checks are inapplicable to this
native Qt surface. No project-local AGENTS.md or skills directories were found.

## Pillar Scores

| Pillar | Score | Key Finding |
|---|---|---|
| 1. Copywriting | 4/4 | C-01 remediated: OCR failures now use fixed recognition-specific Russian copy. |
| 2. Visuals | 4/4 | V-01 remediated: both150% confirmation screenshots expose the entire card/count above the panel. |
| 3. Color | 4/4 | Actual native palettes switch in place; text-view striping is gone. |
| 4. Typography | 4/4 | Three system-derived semantic sizes/two weights; IPA/Cyrillic remain readable. |
| 5. Spacing | 4/4 | Code and screenshots follow16px margins,8px rows and24px context separation. |
| 6. Experience Design | 4/4 | Actual cancellation, selection, Close, timeout, context and tray gates are recorded separately from Qt tests. |

**Current overall:24/24. Original score:21/24; both findings below are remediated.**

## Bounded Fix Confirmation —2026-10-27

Inspected only `BreezeLight-1.5.png` and `BreezeDark-1.5.png` from successful
run `7af92341505845a9b08cfd6e474f2697`, plus the targeted implementation and
regressions. No new captures, source edits or VM actions were performed.

**V-01: REMEDIATED.** `lookup/platform.py:135` computes a usable rectangle
from bounded, read-only Plasma dock metadata; `lookup/app.py:74` carries it
through Frozen/Event and `lookup/gui.py:429` uses it for sizing/placement.
Both150% screenshots now show the complete footer (“Искали11раз”/“Искали12раз”)
well above the bottom panel. Recorded card `[124,0,440,386]` lies inside work
area `[0,0,1280,658]`; the panel is `[0,658,1280,62]`. The harness also asserts
outer-monitor containment and zero panel intersection across all eight final
appearances (`tools/check_app.py:546`). The former Qt/KWin-equality-only gap is
closed. Native work-area regression: `tests/test_app_gui.py:198`.

**C-01: REMEDIATED.** `lookup/app.py:269` maps non-package OCR errors to
`ocr_timeout`/`ocr_failed`; `lookup/gui.py:19` supplies recognition-specific
Russian headings and retry guidance. Missing-package errors keep their useful
package guidance. Targeted regressions exist in `tests/test_app.py:158` and
`tests/test_app_gui.py:129`. This is code/regression evidence; the two inspected
confirmation screenshots are useful-result views, not OCR-error screenshots.

The final evidence records23 true gates and five true restoration flags.
No remaining blocker or warning was proved within this audit scope. This is
agent acceptance of the inspected native UI; no human testing is claimed.
Root still owns deletion of all reviewed/failed-run temporary screenshots.

## Original Priority Fixes —Remediated

1. **Former BLOCKER V-01 —REMEDIATED: Clamp against the real KDE work area.** At150%, move/shrink
   the complete card above the panel so confirmed history status remains readable.
   Add a work-area bounds assertion, not only Qt/KWin geometry equality.
2. **Former WARNING C-01 —REMEDIATED: Distinguish OCR failure copy.** Map OCR timeout/process failures
   to the agreed “Не удалось распознать текст”/retry wording at the source boundary.

No third independent priority defect was proved in this bounded pass.

## Original Detailed Findings —Historical Evidence

The original scores/findings are retained below to preserve the reason for the
fixes. The bounded confirmation above supersedes their open status.

### 1. Copywriting —3/4

**C-01 — WARNING.** `lookup/gui.py:18`, `lookup/gui.py:237` and
`lookup/app.py:263` forward OCR reasons into the shared translation reason table.
OCR `timeout` therefore displays “Перевод не ответил вовремя”; `process_failed`
falls to “Не удалось выполнить поиск”. The approved contract names recognition
failure explicitly. Users can retry, so this is not a completion blocker. Keep
fixed safe copy but distinguish the failed recognition step from provider failure.

Other inspected strings match the contract: Close tooltip/accessibility name,
loading, network disabled, original context, real count, distinct history/cache
warnings and disabled future menu actions. No fabricated metadata or saved count
is shown in the inspected code/evidence.

### 2. Visuals —2/4

**V-01 — BLOCKER.** `lookup/gui.py:427` uses QScreen.availableGeometry directly
for sizing and `popup_rect` clamping. In both `BreezeLight-1.5.png` and
`BreezeDark-1.5.png`, the card's lower footer is obscured by the KDE bottom panel.
Recorded geometry is `[124,326,440,386]` logical pixels: bottom712, or1068 physical
pixels at150%. The panel starts around physical y1010. Unlike100/125/200%, the
150% screenshots do not expose “Искали…раз” below the original context. This
violates the complete-outer-rectangle contract and hides the save/count result.
Qt/KWin geometry equality is true but does not prove work-area containment.

Use an independently verified actual KDE work area (or a bounded conservative
fallback proven on this target), then assert all four card edges remain inside
it. Confirm the150% footer in both themes and keep Close outside scrolling.

The main visual hierarchy otherwise holds: heading, IPA, ordered sources, POS,
article, context and footer. Close is visible and text viewport striping from
the initial round is absent. Source-window text behind the card is fixture
content, not an application overlay defect.

### 3. Color —4/4

**Passing finding:** All eight screenshots show the expected native text contrast.
The same owner reports light Window/WindowText `#eff0f1/#232629` and dark
`#202326/#fcfcfc`. These are observed palette values, not hardcoded production
colors. `lookup/gui.py:86` disables text-viewport autofill; there are no per-row
black/white stripes or custom accent panels. Actual selection uses native
highlight. Native attention hierarchy meets the contract without requiring a
literal pixel-percentage fill split.

### 4. Typography —4/4

**Passing finding:** `lookup/gui.py:193` derives fonts from QApplication, using
P/1.5P/1.75P and normal/demibold only. The body article is normal weight while
source/POS labels establish hierarchy (`lookup/gui.py:271`). IPA and Cyrillic
are legible through200%; no substituted web font, clipped title or invented
phonetic metadata was observed. Native Qt tests additionally cover font changes
and long unbroken text; those tests are not labeled as live screenshot proof.

### 5. Spacing —4/4

**Passing finding:** `lookup/gui.py:129`, `lookup/gui.py:158` and
`lookup/gui.py:162` establish16px margins,8px related-row spacing and16px extra
context separation plus the layout's8px gap. Screenshots preserve that rhythm
at all scales. Native Close/menu metrics are valid QStyle exceptions. The
bottom-panel failure is recorded under V-01, not reclassified as arbitrary
spacing or addressed with cosmetic extra padding.

### 6. Experience Design —4/4

**Passing finding:** The actual run records23 true gates, including new/repeated/
absent-invalid primary, exact public OCR word, word-count boundaries, sentence
no-history, loading/dismissal, delayed-A/new-B, late context without reopen,
history/cache failures, missing tool/capture/cursor reasons, long article text
selection, native Close, physical Escape, focus loss, deliberate-input reset,
20-second timeout, cold/warm owner, duplicate launches and actual native tray
Quit. Five restoration flags are true. These observations substantiate the
interaction model, while V-01 independently limits complete visual acceptance.

Code additionally keeps explicit plain text, a single outer scroll surface,
keyboard-focusable Close, accessible names and generation rechecks. The late
multiline-context height fix and passive-pointer behavior have offscreen Qt
regressions. Browser screen-reader behavior and human/friend-hardware testing
were not performed and are not claimed.

## Files Audited

- `.planning/phases/05-app/05-UI-SPEC.md`
- `.planning/phases/05-app/05-02-SUMMARY.md`
- `.planning/phases/05-app/05-GATE-RESULTS.json`
- `lookup/gui.py`, relevant OCR error boundary in `lookup/app.py`/`lookup/ocr.py`
- `tests/test_app_gui.py`
- Eight supplied temporary native screenshots, names listed above by theme/scale

Registry audit: not applicable; no components.json or third-party web registry.
Root must remove reviewed screenshots, including earlier failed-run batches,
before final privacy/security acceptance. No human UI acceptance is implied.
