# LookUp Linux

## Platform

Native Linux desktop application for Arch Linux, KDE Plasma 6 Wayland.
Python/PyQt6 with Tesseract and KDE platform tools are already established.

## Users and purpose

A Russian-speaking friend moving to Linux reads English in another application,
points at an unfamiliar word, presses Meta+Shift+D, and reads its translation in
a nearby popup. A new short primary selection takes priority over OCR. Searches
enter local history; explicit study-card actions and review follow in Phase 6.

## Operating context

The application remains in the tray and must leave the reader in control.
Repeated triggers replace earlier work, closing a card cancels its pending
presentation, and errors are visible without exposing private content in logs.
The accepted performance target is a median useful-card latency <=1.5 seconds
in Denis's Arch VM, measured end to end in Phase 8.

## Capabilities and constraints

V1 is EN to RU, StarDict/DSL/MDX with online fallback, cursor OCR/selection,
history, independent spaced repetition, CSV/Anki import export, settings and
Arch packaging. Existing CLI/core behavior remains supported. Audio, screen
translation, screenshots in study cards, CEFR, cloud sync and other languages
are deferred. Source: .planning/PROJECT.md, REQUIREMENTS.md and ROADMAP.md.

V1 scope expanded by Denis on 2026-10-27: reconstruct sentence context across
multiple lines in one text block (CAPT-05), translate the selected word's sense
using that context (TRAN-06), and verify actual fullscreen games (GAME-01).
Phase 5.1 implements context/sense before Phase 6 study cards; Phase 8 verifies
at least two real games, fullscreen and borderless where available. Unsupported
VM modes remain unverified. These are pending requirements, not existing features.

## Brand commitments

Native KDE Breeze, including the user's light/dark palette, fonts, icons and
interaction conventions. Russian interface copy. No Windows Fluent imitation
or independent visual identity exercise is required.

## Principles and accessibility

Readable dictionary hierarchy, selectable text, visible keyboard focus, Escape
to dismiss, bounded scrollable content, monitor-clamped placement, accessible
names, and clear loading/error/save states. Source content is treated as text,
not executable or remotely loaded rich content.

## Evidence and delegated defaults

Phases 1–4 provide tested core APIs, dictionary data models, calibrated OCR and
actual VM platform gates. docs/lookupper/linux-requirements.md clarifies stale
results and cancellation without expanding v1. User explicitly delegated all
routine choices with --auto; this document is synthesized from that accepted
brief. Exact popup sizing, spacing and timeout defaults are agent choices to
validate in Phase 5, rather than reported user preferences.
