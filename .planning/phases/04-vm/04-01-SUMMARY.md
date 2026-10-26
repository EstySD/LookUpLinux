---
phase: 04-vm
plan: 01
status: complete
requirements-completed: []
---

Implemented stdlib-only platform geometry/probes, owned-window commands, bounded
primary selection reads, Spectacle transport, ScreenShot2 concurrent pipe transport,
and compatible encoded-byte input to the existing OCR preparation pipeline.

Validation: Windows Python 3.14 and 3.12 each passed 517 tests (7 existing skips).
Focused platform/image/import tests: 21 passed on both interpreters. Tests cover
actual image ratios, negative origins, popup boundaries, malformed metadata,
child deadlines/output caps, ownership rejection, channel order, exact raw length,
detached image lifetime, and equivalent path/byte OCR preparation.

Actual Arch Plasma probes returned the cursor and Virtual-1 geometry. First sample
Spectacle: 1062.3 ms; ScreenShot2: 489.3 ms, both 1920x1080. These are preliminary
capability measurements, not the final backend decision or Phase 4 acceptance.
QtDBus must initialize the session connection before argument conversion; target
raw format is RGBX8888 (16), explicitly supported alongside other 32bpp formats.

T-04-01..05 implemented: validated geometry/layout, fixed argv, owned UUID checks,
bounded output/lifetimes, concurrent FD drain, detached pixels, private temporary
transport cleanup, no clipboard writes or diagnostic text/pixel output. Live
cleanup/scale/backend validation remains Plan 03. Requirements are not yet accepted.
