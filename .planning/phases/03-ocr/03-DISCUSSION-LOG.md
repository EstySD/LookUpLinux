# Phase 3 autonomous decisions — 2026-10-25

All gray areas selected in a single pass under --auto. The user explicitly
delegated routine decisions and acceptance; no confirmation questions asked.

| Area | Choice | Reason |
|---|---|---|
| Coordinate contract | Original image pixels; explicit transforms | Stable offline API and testable HiDPI geometry |
| Process/image stack | tesseract TSV, stdlib core, lazy Qt image preparation | Existing target dependencies, no pip additions |
| Selection safety | Box hit, bounded nearest neighbor, confidence/normalization | Blank space must not save unrelated text |
| Compound priority | Offline pair candidates before final standalone lookup | Meets break out requirement without speculative side effects |
| Calibration | Reproducible light/dark scaled fixtures and measured comparison | Choose preprocessing from evidence |
| Acceptance | Agent judgment with traceable tests and limits | Explicit user --auto preference |

Canonical decisions: 03-CONTEXT.md D-01 through D-08. No deferred feature was
folded into the phase. Research/planning may resolve concrete thresholds and
API details within these decisions.
