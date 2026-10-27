# Phase 6: Список слов и карточки — Context

**Gathered:** 2026-10-27
**Status:** Ready for research and planning
**Mode:** Agent-selected under explicit `gsd next --auto`; no human acceptance claimed.

<domain>
## Phase Boundary
LIST-01, LIST-02, POP-04, LEARN-01 and LEARN-02: native words window, explicit card creation from popup/history, persistent interval review and CSV/Anki file export. Consume the exact context/meaning pair delivered by Phase 5.1. Settings/package remain Phase 7; game/performance acceptance Phase 8.
</domain>

<decisions>
## Implementation Decisions
- **D-01:** Enable the existing tray Words and Review actions. Use native Qt/Breeze windows with system fonts/palette, keyboard access, readable empty/error states and no web rendering. Reuse one window per action and preserve popup lifecycle.
- **D-02:** Words initially sort by numeric search count descending; clicking column headers changes sorting. Provide a text search, delete selected history word and explicit add-to-cards. Browsing/searching/sorting never increments history counts. Deleting history resets the next lookup to count one.
- **D-03:** A learning card is a durable snapshot separate from lookup history. Unique normalized word/phrase identity prevents duplicates; repeated add reports already present and does not silently replace the saved context or reset review state. Deleting a history row leaves its independent learning snapshot intact; make this behavior clear in the delete UI.
- **D-04:** Popup add uses the currently displayed accepted word, its exact context and current contextual meaning when available, otherwise its dictionary/online short translation. A late enrichment or newer/closed popup cannot change a card already created. History add consumes one consistent Phase 5.1 store snapshot. Explain empty/unavailable translation rather than inventing it.
- **D-05:** Use a small deterministic persistent interval scheduler with Again / Hard / Good / Easy, showing the same computed interval that the action applies. Select a simple established method in research; no machine-learning dependency. Store UTC due times and state; review only due cards, prevent accidental repeated grading and show a clear no-due-cards state. Survive restarts.
- **D-06:** Export learning snapshots, not mutable current history. CSV preserves Unicode, quotes and multiline context with explicit word/translation/context fields. Anki export must import without manual file edits using a documented supported format and preserve all three values; verify against official documentation and an actual separate test import if Anki is available. `.apkg`, sync and AnkiConnect are not required.
- **D-07:** Preserve existing schema/migrations and worker-owned SQLite connection. Add only the minimum card/review schema and small tested core functions; no ORM or new dependency for scheduling/export. Use an owned GUI connection or a small existing command seam; never share a SQLite connection across threads or stall the GUI on long work.
- **D-08:** Agent acceptance includes core tests and native VM observations of words, add/duplicate, deletion/count reset, review persistence/empty state and exports. Keep human acceptance unclaimed and record external application/environment limits honestly. No routine confirmation under --auto.
- **Agent discretion:** Column details, native spacing, exact simple review algorithm and export file-dialog choices may follow project patterns. Favor the smallest complete implementation, not a reduced feature scope.
</decisions>

<canonical_refs>
## Canonical References
- `.planning/ROADMAP.md` — Phase 6 success criteria.
- `.planning/REQUIREMENTS.md` — LIST-01, LIST-02, POP-04, LEARN-01, LEARN-02.
- `.planning/PROJECT.md` — accepted v1 scope and prior decisions.
- `docs/lookupper/architecture.md` — original behavior and evidence limits.
- `docs/lookupper/linux-requirements.md` — Linux history/card/export contracts.
- `docs/lookupper/evidence.md` — observed versus claimed original behavior; own SRS remains a project decision.
- `.planning/phases/05.1-context/05.1-03-SUMMARY.md` — exact displayed/persisted pair and lifecycle contract.
- `.planning/phases/05.1-context/05.1-VERIFICATION.md` — accepted implementation and provider limitation.
</canonical_refs>

<code_context>
## Existing Code Insights
- `lookup/store.py`: additive guarded migrations, `get_word_context` snapshot and one-event history semantics; current schema V3.
- `lookup/gui.py`: lazy Qt components, native popup, owner/tray with disabled Words/Review/Settings placeholders; separate late meaning updates.
- `lookup/app.py`: accepted generations and detached ready/final Result, worker-local resources.
- `lookup/translate.py`: contextual meaning distinct from dictionary translation, explicit readiness/unavailable flags.
- `tests/test_app_gui.py`: offscreen real-widget tests and existing placeholder-action assertions that must be updated proportionately.
- `tools/check_context_app.py`: isolated VM profile, owned fixture, physical/native observation and safe restore pattern.
</code_context>

<specifics>
## Specific Ideas
Again / Hard / Good / Easy are required English button labels; the surrounding UI remains Russian. Anki's own review behavior is not claimed as original Lookupper functionality. Preserve Phase 5.1 provider HTTP 429 limitation without blocking offline learning/history/export.
</specifics>

<deferred>
## Deferred Ideas
Settings, hotkey re-registration, autostart and packaging remain Phase 7. Real games, sustained load and performance remain Phase 8. Audio, CEFR, screenshots, sync, Quizlet and card status categories remain accepted v2 scope.
</deferred>
