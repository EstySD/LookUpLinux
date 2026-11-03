# Milestones

## v1.1 Надёжность и распространение (Shipped: 2026-11-03)

**Phases completed:** 7 phases, 11 plans, 17 requirements

**Key accomplishments:**

- Hotkey-moment capture, configurable compact popup and retained-frame word selection.
- Real Yomitan dictionaries, discoverable home/settings/learning windows and live context-client fallback.
- Actual MDX/DSL, second-monitor 100%/125% and borderless Wesnoth acceptance.
- Public 0.2.1 package: native build, clean install, v1.0 words/cards/settings upgrade, data-preserving removal and checksum-bound AUR metadata.

**Final verification:** 877 tests on Windows and Linux, zero failures/errors; 13/22 skips. Five native package gates pass. User-reported manual VM testing is recorded separately from agent scenarios. [Audit](milestones/v1.1-MILESTONE-AUDIT.md).

**Publication:** [GitHub v0.2.1](https://github.com/EstySD/LookUpLinux/releases/tag/v0.2.1), published 2026-11-03T17:34:43Z; internal milestone tag milestone/v1.1. Both remote workflows passed. Downloaded canonical CI binary passed installed lookup and linkage checks. AUR metadata is attached; AUR submission remains separate.

---

## v1.0 LookUp Linux (Shipped: 2026-11-01)

**Phases completed:** 9 phases, 43 plans

**Delivered:** KDE Wayland translator with a persistent tray client, physical hotkey, OCR/PRIMARY capture, offline dictionaries, contextual translation, history, learning cards, review, Anki export, settings and an Arch package.

**Final acceptance:** All 32 requirements and all nine phases are verified. Phase 8 passes 7/7; current full host/target suites each run 797 tests (11 host skips, zero target skips). Current physical30 median is 1088.246 ms and p95 is 1431.759 ms. Genuine fullscreen Wesnoth and AssaultCube routes return control to gameplay.

**Closeout:** Verified closeout with the existing Phase 7 original-VM preservation exception explicitly retained. Network/renderer/mode limitations and rejected attempts remain documented in the [closeout audit](milestones/v1.0-MILESTONE-AUDIT.md). Acceptance is agent verification, not an inferred human pass.

**What's next:** No next milestone started; remote publication is not part of this closeout.

**Selected execution history (intermediate gaps below were preserved and later closed):**

- SQLite schema v2 (translations cache + meta tables) with a lemma keyword on upsert_word, and the Phase 1 safety-net tests re-pinned to an explicit V1 tuple.
- Stdlib-only LZO1X decoder verified against real liblzo2 output, a RIPEMD-128 digest checked against the reference vectors, and a bounded random-access dictzip reader, so the MDX and StarDict readers need no extra package.
- Defensive config.json reader with XDG paths, the shared Article/SearchResult contract with plain-text helpers, a JSON index cache pinned to path+size+mtime, and a WordNet-derived irregular-forms file with its Princeton notice.
- Google translate_a/single over urllib with an ordered client list, MyMemory fallback for phrases and sentences, one shared 3-second deadline, and every failure reduced to one of five fixed reason codes with the query text never leaking.
- StarDict reader with per-entry index validation, random-access dictzip data and a bounded Mueller parser that exposes transcription, parts of speech and "от X" pointer flags.
- Lingvo DSL reader (.dsl and .dsl.dz in UTF-16 LE/BE or UTF-8, with or without BOM) with a cached byte-offset headword index, capped `{}` expansion, and a markup converter that yields plain text with separate transcription, parts of speech and values.
- Stdlib MDX reader for versions 1.2 and 2.0 with zlib, plain and LZO blocks, Encrypted=2 key info, UTF-8/16/GBK/Big5, every Adler-32 verified, bounded sizes, 3-hop redirects and a validated JSON index cache.
- Production OCR now returns a bounded sentence or explicit fragment with source occurrence offsets, verified on 104 actual Tesseract image cases.
- Occurrence-specific Russian meanings now have a strict text-only provider, bounded cache and exact token/context/span persistence without a second search count.
- Independent cards now preserve the exact selected translation/context pair, support deterministic persistent review, and export safely to CSV or two-field Anki TSV.
- Native Words/Review/popup workflows passed all ten gates, and Anki 26.9.3 imported the unchanged production TSV into two verified notes in a throwaway collection.
- Validated settings now save atomically, and the existing lookup worker reopens its own resources with a revision-specific acknowledgement while rejecting stale work.
- The application now has a bounded owned-shortcut transaction, config-gated login entrypoint, safe source/package launch paths and one private-helper resolver.
- Native settings apply runtime changes through revision-specific acknowledgement, expose the actual dictionary folder and connect copied dictionaries through unchanged-field Apply, with explicit restoration states.
- The local Arch package builds with verified upstream assets, and the doctor checks tools, dictionary indices and session registration without lookup side effects.
- The installed package passed fourteen native/product gates, including physical shortcut capture, effective Settings, real graphical logins and package removal; the strict report remains false because a separate original-VM GUI run changed its baseline disk.
- Numeric internal timing and strict predeclared raw-evidence checks are ready for native measurement; no performance or game acceptance is claimed.
- Installed physical lookups passed a 1128ms median, 320 sustained completions, rapid burst, four actual scales, privacy and fault recovery in the owned clone.
- Two physical lookups captured different real tutorial scenes, displayed useful Mueller articles, and returned control for unit movement and combat.
- Actual fullscreen Freedoom ran with verified relative pointer lock, but unchanged production OCR could not select the targeted game words; mandatory useful captured-game acceptance remains failed.
- A separate clean graphical profile passed actual local installation, physical OCR, enabled/disabled SDDM login and data-preserving removal; final phase acceptance remains false because useful captured-game proof is missing.

---
