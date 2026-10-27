---
phase: 05-app
reviewed: 2026-10-26T17:48:56Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - lookup/app.py
  - lookup/gui.py
  - lookup/translate.py
  - lookup/__main__.py
  - tools/check_app.py
  - tests/test_app.py
  - tests/test_app_gui.py
  - tests/test_check_app.py
  - tests/test_translate_ready.py
  - tests/test_core_imports.py
findings:
  critical: 1
  warning: 1
  info: 0
  total: 2
status: issues_found
---

# Phase 5 code review

One targeted pass over request/history ownership, presentation, lazy native
entry, translation callback changes and the current gate harness. No source,
configuration or VM modifications; no acceptance claim from an in-flight or
previous gate result. The local Qt reproduction below uses fixed public text.

## CR-01 — BLOCKER: late context translation remains clipped to its old height

**File:** `lookup/gui.py:94`, `lookup/gui.py:301`.

PlainBlock.fit() fixes the widget height from its current document. Initial
presentation runs size_for(), sizing context_value for the short pending
message. The context-only completion path then calls setPlainText() without
recomputing height. The width is unchanged, so resizeEvent does not run.
Both inner scrollbars are disabled; the outer scroll surface sees the old
fixed widget height and cannot expose the remaining translated context.

**Reproduction:** Construct the actual native Popup with context_pending=True,
render it and process events. context_value.height() is 14. Replace pending
with `'long public translated context '*200` through update_context and process
events again. Its height and maximumHeight remain 14, while
heightForWidth(viewport.width()) reports 2814. The translation has become
unreadable beyond the first line despite the displayed full result state.

**Fix:** Refit PlainBlock after its document text changes, using the current
viewport width, and notify/update the outer layout so the existing scroll
surface can reach the complete bounded text. Preserve the context-only
contract: no focus, history count or inactivity timer reset. Add an actual Qt
test transitioning from one-line pending to a multiline translation at fixed
card width and assert widget/content height and outer scroll range grow.

## WR-01 — WARNING: repeated-primary OCR gate accepts any redacted wrong word

**File:** `tools/check_app.py:100`, `tools/check_app.py:443`.

The fixture deliberately shows the known public token `word`, but PUBLIC omits
that token. Status therefore returns `key='unexpected'` for the correct result
and every other recognized query outside the whitelist. The repeated-primary
gate requires precisely this redaction sentinel. Consequently a different OCR
word can satisfy the gate; mode='ocr' alone does not prove correct source
selection/recognition. This affects reliability of the native gate evidence.

**Fix:** Add the known project-owned `word` token to the status whitelist and
require exact `key='word'` for this gate. Keep unrelated query redaction.
Add a gate-predicate test demonstrating that a different unlisted query fails.

---

No additional concrete stale-history or context-worker admission defect was
proved in this pass. This statement does not validate the entire feature.
Native VM actions and the running harness remained exclusively root-owned.
