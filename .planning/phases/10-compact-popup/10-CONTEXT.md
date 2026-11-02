# Phase 10 — Compact configurable popup

Date: 2026-11-02. Decisions selected by the agent under `gsd next --auto`; no human acceptance claimed.

## Boundary
POP-06 and SET-02: requested word and useful meanings first, persistent control of popup blocks, preserve saving/history/cards. No provider or capture redesign.

## Automatic decisions
- Context visibility: hide source text and context translation by default for a compact result. Expose a single checkbox for this pair.
- Contextual word meaning: retain by default; expose a separate checkbox so users can hide it without hiding dictionary results.
- Full dictionary article: collapse behind an explicit expand control by default, preserving access to the complete article. Keep structured senses visible before details; do not invent semantic ranking for unstructured text.
- Core word, dictionary senses, errors and card controls remain available. Display preferences never change stored context or saved card content.
- Reuse native Qt settings controls, atomic config save and existing runtime apply/rollback. Existing configurations load sensible defaults; subsequent requests and restart honor saved choices.

## Reproduction limits
Danila's missing photo and exact source article are unavailable. Use synthetic long articles and offline-only lookup to prove layout/order; do not claim the original defect has been reproduced or human tested.

## Verification
Config round-trip/invalid values; native offscreen Qt tests for defaults, settings apply/reload, asynchronous context updates, expandable details and card invariants. Follow existing target VM policy for any live verification; preserve user OCR edits.
