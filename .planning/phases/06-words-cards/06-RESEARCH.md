# Phase 6: Words, learning cards and export — Research

**Researched:** 2026-10-27
**Confidence:** HIGH for inspected interfaces and documented formats; real Anki import remains unverified.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked decisions
- **D-01:** Enable the existing tray Words and Review actions. Use native Qt/Breeze windows with system fonts/palette, keyboard access, readable empty/error states and no web rendering. Reuse one window per action and preserve popup lifecycle.
- **D-02:** Words initially sort by numeric search count descending; clicking column headers changes sorting. Provide a text search, delete selected history word and explicit add-to-cards. Browsing/searching/sorting never increments history counts. Deleting history resets the next lookup to count one.
- **D-03:** A learning card is a durable snapshot separate from lookup history. Unique normalized word/phrase identity prevents duplicates; repeated add reports already present and does not silently replace the saved context or reset review state. Deleting a history row leaves its independent learning snapshot intact; make this behavior clear in the delete UI.
- **D-04:** Popup add uses the currently displayed accepted word, its exact context and current contextual meaning when available, otherwise its dictionary/online short translation. A late enrichment or newer/closed popup cannot change a card already created. History add consumes one consistent Phase 5.1 store snapshot. Explain empty/unavailable translation rather than inventing it.
- **D-05:** Use a small deterministic persistent interval scheduler with Again / Hard / Good / Easy, showing the same computed interval that the action applies. Select a simple established method in research; no machine-learning dependency. Store UTC due times and state; review only due cards, prevent accidental repeated grading and show a clear no-due-cards state. Survive restarts.
- **D-06:** Export learning snapshots, not mutable current history. CSV preserves Unicode, quotes and multiline context with explicit word/translation/context fields. Anki export must import without manual file edits using a documented supported format and preserve all three values; verify against official documentation and an actual separate test import if Anki is available. `.apkg`, sync and AnkiConnect are not required.
- **D-07:** Preserve existing schema/migrations and worker-owned SQLite connection. Add only the minimum card/review schema and small tested core functions; no ORM or new dependency for scheduling/export. Use an owned GUI connection or a small existing command seam; never share a SQLite connection across threads or stall the GUI on long work.
- **D-08:** Agent acceptance includes core tests and native VM observations of words, add/duplicate, deletion/count reset, review persistence/empty state and exports. Keep human acceptance unclaimed and record external application/environment limits honestly. No routine confirmation under --auto.
- **Agent discretion:** Column details, native spacing, exact simple review algorithm and export file-dialog choices may follow project patterns. Favor the smallest complete implementation, not a reduced feature scope.

### Deferred ideas
Settings, hotkey re-registration, autostart and packaging remain Phase 7. Real games, sustained load and performance remain Phase 8. Audio, CEFR, screenshots, sync, Quizlet and card status categories remain accepted v2 scope.
</user_constraints>

## Integration

### 1. Exact snapshot boundary

[VERIFIED: lookup/store.py:get_word_context] History add must consume one returned dict: `word`, `translation`, `context`, `span`, `meaning`, `provider`. Select `meaning` when present, otherwise `translation`; carry the same context. Read the pair once, never query meaning/context separately. Refuse empty translation with explanatory UI; do not invent or fetch it.

[VERIFIED: lookup/gui.py:Owner.receive and lookup/app.py:Engine._process] The popup receives detached ready Results and late contextual updates only while visible/current. Maintain the currently displayed snapshot in the popup/owner and copy it synchronously on add. Freeze the chosen `result.context_meaning or result.translation` and displayed context then. Never re-query mutable history for popup add. Loading, error, sentence-only result, hidden/closed popup and superseded generation must disable/reject add. Once inserted, later enrichment never updates the learning row. Duplicate add returns existing status before replacing any data or schedule.

### 2. Small schema and connection ownership

[VERIFIED: store.py:MIGRATIONS currently (_v1,_v2,_v3)] Add `_v4` with an independent `cards` table keyed by normalized word/phrase, selected translation, exact context, optional source span/provider, creation timestamp, UTC due timestamp, repetitions, interval days, ease and monotonically increasing review version. Use no cascading history foreign key. Initial due is creation time; initial repetitions/interval are zero and ease 2.5.

[VERIFIED: store.py:_connect and app.py worker ownership] Use a separate GUI-owned connection via `open_store`, opened lazily and closed by Owner.quit; never pass the worker's connection to Qt. Use a short busy timeout for UI work and surface fixed save/database errors, allowing retry. New daemon startup normally opens current schema first; if any live old process has an old schema, restart/reopen rather than attempting to mutate its connection from another thread. Keep all SQL values bound; any sortable SQL column/direction must come from an explicit allowlist.

Use atomic `INSERT ... ON CONFLICT DO NOTHING` for card creation and one compare-and-set UPDATE for grading. Guard by current review version plus `due <= now`; increment version on every successful answer. This prevents double clicks, queued signals and stale review views from scheduling the same state twice. [VERIFIED: SQLite operations already used in project; design prescription grounded in D-03/D-05]

## Scheduler

**Selected project adaptation:** map Hard/Good/Easy to quality 3/4/5. Compute their next whole-day interval from the *old* state: 1 if successful repetitions are zero, 6 if one, otherwise `ceil(previous_days * ease)`. Then increment successful repetitions and apply `ease = max(1.3, ease + 0.1 - (5-q)*(0.08 + (5-q)*0.02))`. Again resets successful repetitions/interval days to zero, preserves ease and schedules 600 seconds later. The 10-minute Again rule replaces SM-2's within-session retry handling; label this SM-2-derived, not exact SM-2. [VERIFIED: agent-selected implementation decision consistent with D-05; CITED: SM-2 source for underlying rules]

Hard/Good/Easy can legitimately display the same early interval; their ease changes affect later scheduling. Do not add arbitrary bonuses solely to force distinct labels. Store every state needed for restarts; avoid random fuzz. [VERIFIED: direct consequence of selected transition]

Implement one pure `preview(state, rating)` returning delay and next state. Rendering buttons and applying answers must call this same function with the same loaded review version. The displayed interval means a duration from the actual answer time; due is `answer_now + delay`. Query cards `due <= now`, stable order `(due, word)`. Show only front first, reveal translation/context before enabling grading, and show an explicit empty queue. [VERIFIED: D-05; CITED: https://docs.ankiweb.net/manual/studying for reveal/four-rating interaction]

## Export

[CITED: https://docs.ankiweb.net/manual/importing/text-files] Anki accepts UTF-8 delimited text; extra fields beyond a target note type may be discarded. Use **two TSV fields**, Front and Back, for an ordinary two-field note: escaped word on Front; escaped translation plus a visible separator and escaped context on Back. Convert context newlines to `<br>`. Include supported `#separator:Tab`, `#html:true` and `#columns:Front\tBack` directives, supported from Anki 2.1.54. Do not hardcode `#notetype:Basic`: its existing name can depend on the profile. Ordinary note-type selection in Anki's import dialog is allowed; file editing is unnecessary. Avoid synthetic GUIDs and unsupported third Basic fields.

[VERIFIED: project design using stdlib csv/html] CSV remains a distinct three-column format: `word,translation,context`, written with `csv.writer`, UTF-8 and `newline=''`. Both exporters read immutable card rows in one consistent snapshot. TSV HTML must be escaped before generated separators, including quotes/ampersands/angle brackets; replace literal tabs safely inside HTML fields so they cannot become extra columns. Do not emit media references or provider HTML. Preserve multiline context semantically rather than flattening it into spaces.

Write to a sibling temporary file and atomically replace the explicitly selected destination; cleanup on error. A canceled dialog writes nothing; an export failure leaves the previous destination intact and reports a fixed error. Do not silently add CSV formula prefixes that change required round-trip values; the app exports data, not spreadsheet-executed formulas. [VERIFIED: design prescription for D-06/no data loss]

## Environment Availability

[VERIFIED: command/path/registry/module probes] Anki not found on host or VM. SSH archvm responds. Execution may obtain an isolated official package with throwaway profile; otherwise actual Anki import remains unverified. No production dependency. Provider 429 does not block offline learning.

## Validation Architecture

[VERIFIED: existing unittest infrastructure; locked scope] Add focused learning core/GUI modules, then python -m unittest discover -s tests on VM. Cover numeric sorting/search/delete/count reset; immutable duplicate/snapshot/context fallback; stale or closed popup; all scheduler ratings/ease floor/UTC/preview-applied equality; restart/double-grade/empty state; CSV Unicode/quotes/newlines; two-field escaped TSV; export cancel/error/atomicity; v3-v4 preservation. Native VM observes both windows, add/duplicate, deletion/reset, review/restart/empty and exports. Actual isolated Anki import if available; otherwise mark unverified. Update GUI placeholder assertions; preserve Phase5.1 tests. Agent evidence only.

## Security and sources

[VERIFIED: existing privacy conventions] Bound text/rating inputs, bind SQL and allowlist sort columns, retain private SQLite permissions, plain-text native UI, escaped export HTML and fixed private errors. No new auth/network surface.

[CITED] https://super-memory.com/english/ol/sm2.htm ; https://docs.ankiweb.net/manual/importing/text-files ; https://docs.ankiweb.net/manual/studying ; https://docs.python.org/3/library/csv.html .

[VERIFIED: canonical refs read] docs/lookupper architecture/linux-requirements/evidence distinguish original observations from own SRS. Phase5.1 summary/verification preserve exact pair/provider limits. No implementation blocker; Anki import currently unverified. Routine design decisions resolved under --auto.
