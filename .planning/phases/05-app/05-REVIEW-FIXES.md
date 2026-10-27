# Phase5 review remediation

- CR-01: PlainBlock.setText now refits its document at current viewport width
  and signals geometry changes. A native Qt regression changes pending context
  to a long translation and asserts increased widget/outer-scroll height while
  count, presentation count and inactivity deadline remain unchanged.
- WR-01: Controlled public `word` is explicitly whitelisted; repeated-primary
  OCR requires mode=ocr and key=word. A gate predicate regression rejects both
  redacted unknown results and another known word.
- Related actual VM finding: long main articles could reuse a stale nested
  layout size hint. Native sizing invalidates body/content layouts after fitting
  document blocks; the long-token regression now requires a substantial card
  height in addition to wrapping and maximum bounds.
- Related actual VM finding: kdotool emits fractional logical dimensions at
  fractional scaling. Geometry parsing accepts decimal values and has a real
  440x314.4 output regression; native comparisons allow <=1 logical pixel of
  compositor pixel rounding.

Fresh focused validation:53 engine/native GUI/platform/harness/translation-ready/
CLI/import tests passed. Final main KDE run has23 true gates and five restored
resources; independent verification follows.

Formal UI audit V-01: QScreen's Wayland available geometry omitted panel space.
Fixed by worker-side read-only KWin dock metadata and explicit frozen work-area
event, with monitor containment/nonintersection gates at all scales. Both150%
native screenshots independently confirmed; UI review24/24 passed. C-01 fixed
OCR recognition-specific error identity/copy. See current UI-REVIEW.md.

Windows suite teardown was also made deterministic by explicitly disposing
native test windows/menu/owner and draining deferred deletion. Final561-test
subprocesses exit0 on3.14 and3.12; printed unittest OK without process success
was not used as completion evidence.
