---
phase: 03-ocr
status: complete
resolved: [CR-01, CR-02, WR-01]
unresolved: 0
verified: 2026-10-25
---

# Phase 3 review remediation

CR-01: decoded QImage devicePixelRatio is reset to 1 before copying/painting.
The sample@2x.png rectangle regression initially failed, now verifies physical
pixels and Transform agree.

CR-02: join-only Latin fragment validation permits one-letter parts without
accepting them as standalone words. Trailing hyphens survive intermediate
joins, so e-/mail, x/-/ray and state-/of-/the-/art become complete lexical
units. All three reproductions failed first, now pass with no false spaced
candidate. Confidence and gap rules remain enforced.

WR-01: calibration compares normalized ordered token lists exactly. Missing
or reordered repeated tokens now fail their regression. Also independently
rechecked all 746 historically passing matrix records against the stricter
ordered expectations; all match. No historical word expectations changed.

Fresh after fixes: Windows 3.14 509 tests/25.010s, Windows 3.12 509/24.763s,
each OK with 7 skips; Arch 509/10.016s, OK with 3 skips. Target explicit CLI
gate: 5 tests/21.225s, no skips, all 96 actual image cases. Separate defaults
check: 96/96, median 218.1ms, strict line order. Updated 03-CHECK.json records
current behavior; 03-CALIBRATION.json retains original measured settings and
raw results. git diff --check passed.
