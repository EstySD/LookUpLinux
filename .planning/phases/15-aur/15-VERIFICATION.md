---
phase: 15-aur
status: passed
score: 3/3
verified: 2026-11-03
acceptance: agent
---

# Phase 15 verification

| Criterion | Result | Actual evidence |
|---|---|---|
| Reproducible build and clean target install | PASS | Allowlisted deterministic public archive, checksum-bound AUR recipe, native makepkg build as arch UID1000, installed bank lookup/count and required files/licenses. |
| v1.0 upgrade and removal retain user data | PASS | Genuine 0.1.0 package installed; valid words/cards/settings seeded through its installed API; 0.2.1 upgrade preserves bytes and logical rows; pacman removal preserves data. |
| AUR metadata/instructions ready; publication distinct | PASS | makepkg --printsrcinfo exit0; recipe/source SHA match; docs/AUR.md; GitHub publication now authorized, actual AUR submission not performed. |

Source identity and full reports are bound by 15-ACCEPTANCE.json. Final Windows/Linux suites each run 877 tests, zero errors/failures, 13/22 skips. Five package gates pass. VM stays running with lookup-linux 0.2.1-1 installed, as the final release candidate; synthetic profiles are retained for review.

Native desktop/two-monitor/game evidence remains documented in Phase 14. Later OCR/popup fixes have full regression coverage and user-reported manual VM exercise. Ubuntu GNOME preview limits remain in docs/ubuntu-vm-validation.md; its full OCR fixture differences are not claimed fixed by this KDE release gate.
