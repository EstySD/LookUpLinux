# Feature Research

**Domain:** Personal "hotkey -> word under cursor / selection -> EN->RU popup -> vocabulary log" desktop tool (Arch Linux, KDE Plasma 6, X11 + Wayland)
**Researched:** 2026-10-23
**Confidence:** MEDIUM overall. The Google gtx response shape is HIGH (probed live during this research). Competitor feature lists are MEDIUM (from training knowledge, not re-fetched). UX recommendations are opinionated judgement.

## Verified fact that shapes the feature set

A live probe of `translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ru&dt=t&dt=bd&dt=rm&q=running` returned, in one request:

- `[0][0]`: the main translation (`"бег"`).
- `[0][1][3]`: a Google-style phonetic respelling of the source (`"ˈrəniNG"`). It is not strict IPA, but it works as a transcription and costs nothing extra (the `dt=rm` flag).
- `[1]`: dictionary entries grouped by part of speech (`noun`, `adjective`, `verb`, ...). Each has a flat list of Russian variants plus per-variant back-translations and a frequency score (0.25, 0.05, ...), already sorted by relevance.
- `dt=bd` also works on inflected forms. For `Ran` it returned the verb variants of "run" (`работать`, `бежать`, ...). So variants-by-POS covers most of what lemmatisation would give the reader.
- Capitalisation changes the main translation. `Ran` became `Ран` (a proper name), while the dictionary block stayed verb-based. Lowercase the word before the request.

So "transcription", "POS variants" and "main translation" arrive in one HTTP call. There is no need for a second source.

## Competitor snapshot (what each does that matters here)

| Tool | Trigger / capture | Popup content | Saves words? | Notes for us |
|------|-------------------|---------------|--------------|--------------|
| macOS LookUp / Look Up | Hotkey or three-finger tap, word under cursor via accessibility API | Definition, transcription, audio, thesaurus, Wikipedia | No (the source of this project's idea) | We replace "definition" with RU translation. The popup is anchored to the word and dismisses on click-away or Esc. |
| Crow Translate (Qt, Linux) | Global shortcuts, selection and screen OCR (tesseract) | Translation window, TTS, history | History only | The closest analogue. Its main pain on Wayland is shortcuts and window positioning, which we sidestep with KDE shortcut -> command. It is a heavy "translator app"; we are a one-shot popup. |
| GoldenDict-ng scan popup | Hover/modifier or Ctrl+C+C on a selection | Multi-dictionary articles, audio, history, favourites | History, favourites | Shows the popup is only useful if it is fast and unobtrusive. Multi-dictionary support is the opposite of ponytail. |
| dictpopup (Linux) | Hotkey on selection, popup | Dictionary entries with a card-export button | Via Anki export | Its value is the export. We only log. |
| QTranslate (Windows) | Selection triggers an icon or hotkey | Several engines at once, TTS | History | The multi-engine switcher is not needed. |
| Linguee / DeepL popups | Selection | Translation plus example sentences, alternatives | Account-based glossaries | Examples are the premium feature. Out of MVP. |
| Language Reactor (word trackers) | Hover on subtitles | Translation plus known/unknown status | Yes, with status and flashcards | The "saved word + lookup count" idea comes from here. The per-word status (learning/known) is the natural v2. |

## Feature Landscape

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Global hotkey -> popup, with no main window | The whole product is "hover, press, read" | LOW | KDE custom shortcut runs `lookup` (one-shot process). No key listener of our own. |
| Single-instance guard / ignore key auto-repeat | Holding the key spawns N processes, N screenshots, N counts | LOW | Lock file or `QLockFile`. If a popup is open, a second press closes it or replaces it. |
| Selection mode (PRIMARY) before OCR | Exact text, instant, no OCR errors | LOW | See the stale-selection rule below. |
| OCR word under cursor | The headline feature for text that cannot be selected | MEDIUM | Crop around the cursor (about 400x120 logical px), upscale 2-3x, `tesseract` TSV output, pick the box containing the cursor, else the nearest box within a distance threshold. HiDPI/multi-monitor coordinate mapping is the real cost (see PITFALLS). |
| Popup shows the word | You must see what was recognised, because OCR can be wrong | LOW | Show the normalised word, large. This is the user's only way to spot an OCR error. |
| Popup shows main translation | The core output | LOW | `[0][0]` of the gtx response. |
| Popup shows translation variants grouped by part of speech | Every comparable tool does this, and a bare single word is often ambiguous (`running` is noun, adjective and verb) | LOW | Show at most 3 POS groups x 3-4 variants, in Google's order (already relevance-sorted). Cut the long tail so the popup stays small. |
| Popup near the cursor, clamped to the screen | macOS LookUp, QTranslate and Crow all anchor to the pointer | MEDIUM | Needs XWayland or a KWin script. Clamp to the monitor edges so it does not land half off-screen. |
| Popup dismissal: click, Esc, focus loss and a timeout (about 8-10 s) | An undismissable popup is the number one annoyance | LOW | Do not rely on Esc alone, since an unfocused Wayland/XWayland window may never receive it. Focus-out plus timeout are the reliable paths. A new hotkey press replaces the old popup. |
| Visible failure messages (below) | A silent failure feels broken, and the user cannot tell "no word" from "crashed" | LOW | One popup style, different text. |
| Persist word + translation + count + first/last time | Core value, stated in PROJECT.md | LOW | SQLite, `UPSERT` on the normalised word: `count = count + 1, last_seen = now`. |
| Word normalisation before saving and counting | Without it `Run`, `run,` and `"run"` become three rows | LOW | Rules below. |
| Saved-word list window, sorted by count desc | The user's explicit choice | MEDIUM | Columns: word, translation, count, last looked up. |
| Click-to-sort headers in the list | Free with `QSortFilterProxyModel` | LOW | Default sort is count desc, ties broken by last_seen desc. |
| Search/filter box in the list | Becomes useful after about 50 words | LOW | Substring filter on word and translation. Same proxy model. |
| Delete a row | OCR garbage (`rn` read as `m`, UI fragments) will get saved, and without delete the list becomes untrustworthy | LOW | Row context menu or Delete key, with no confirmation dialog. |
| Install instructions for Arch + KDE shortcut setup | The friend is a non-technical Linux newcomer | LOW | Already in the requirements. A one-page README plus an install script. |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Lookup count shown in the popup ("seen 3 times") | Ties the popup to the saved list, gives instant feedback that the word was logged, and nudges learning | LOW | Return the new count from the UPSERT. Highest value-to-cost ratio in the list. |
| Cache hit from the local DB before going to the network | Faster than the 2 s budget for repeat words, and works offline for known words | LOW | If the normalised word is already saved with a translation, skip the HTTP call. It costs one `SELECT`. It also reduces dependence on the unofficial endpoint. |
| Transcription line from `dt=rm` | Matches macOS LookUp; helps pronunciation | LOW | Free in the same request. Show it only when present. It is a respelling, not IPA, so do not label it "IPA". |
| Phrase translation for multi-word selections | Selections of "give up" or "look forward to" are common | LOW | Same endpoint. See the phrase rule below. |
| Stale-selection protection | Avoids the "popup shows the word I selected five minutes ago" bug | LOW | Store the last handled selection plus a timestamp. Use the selection only if it differs from the last handled one. If the user wants to re-look-up the same selected word, a second press falls through to OCR. This is a rule, not extra UI. |
| Last-looked-up highlight / "new" marker in the list | Shows which words were just added | LOW | Optional. Sorting by last_seen already covers it. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Lemmatisation / stemming before counting | "run/runs/ran/running should be one word" | Needs NLTK/spaCy (tens to hundreds of MB, pip dependencies, data downloads) or a hand-rolled suffix stripper that mangles words (`news`, `bus`, `was`). The popup already shows all senses of the form via `dt=bd`. Mis-merged rows silently corrupt the counts. | Count the surface form (lowercased). If merging is wanted later, add a manual or suffix-rule merge in v1.x, not a NLP library. |
| Pronunciation audio / TTS | macOS LookUp and Crow have it | Needs an audio stack, another network call, and cross-session plumbing | Show the transcription text only. |
| Examples, definitions, synonyms | Linguee/DeepL feel richer | More endpoints and a bigger popup, which breaks "glance and go" | Variants by POS only. |
| Flashcards, spaced repetition, Anki export | Natural next step for vocabulary tools | Already out of scope in PROJECT.md. The DB columns leave room for it. | Defer. CSV export is the cheapest first step. |
| Background daemon / tray icon | Faster response than process startup | More lifecycle, autostart and crash handling. Out of scope in PROJECT.md. | Revisit only if cold start misses the 2 s budget. |
| Multiple translation engines / language pairs | QTranslate and Crow offer it | Doubles the failure surface for one friend who needs EN->RU | One function `translate(word)`, so the provider can be swapped later. |
| Auto-detect language of the source | Looks smart | The friend reads English, and a wrong guess gives garbage translations | Hard-code `sl=en`. |
| Editing saved translations, tags, folders, "known" status | Language Reactor has statuses | UI surface and schema growth with no demand | Delete only. Status is the natural v2. |
| Whole-screen OCR or region-select translation | Crow does it | A different product (screenshot translator), plus heavy Wayland screenshot permission handling | Cursor-local crop only. |
| Saving screenshots / history of contexts | "Remember where I saw it" | Contradicts the privacy constraint | Store text only. |
| Retry loops / offline queue for failed translations | Feels robust | Hides failures and adds state | Show the error, the user presses the hotkey again. |

## Behaviour specification (answers to the specific questions)

### Overlay content and dismissal

Layout, top to bottom, compact (about 280-360 px wide):

1. Word (large) with transcription next to it, when present.
2. Main translation (prominent).
3. POS groups: `сущ.`/`noun`-style label, then 3-4 variants, at most 3 groups.
4. Footer in small text: "seen N times" (differentiator).

Dismissal: click anywhere on the popup, Esc, loss of focus, a timeout of about 8-10 s, or a new hotkey press (replace). The timeout should reset only on mouse hover over the popup, so the user can read a long entry. Treat the "any key" dismissal as optional.

### Failure behaviour

| Situation | Popup behaviour | DB effect |
|-----------|-----------------|-----------|
| Selection present and new | Translate it, no OCR | Save (see phrase rule) |
| OCR finds no text, or no box near the cursor | Short popup "Слово не найдено", auto-dismiss in about 2 s | None |
| OCR returns a non-word (digits, symbols, 1 character, no letters) | Same "not found" popup, which avoids sending junk to Google | None |
| OCR returns a wrong word | Nothing to detect. The word is shown prominently so the user sees the error. The delete action in the list cleans up. | Saved, until deleted |
| No network / timeout (about 3 s) / HTTP error / unexpected JSON | Popup shows the recognised word plus "Нет перевода (нет сети)". If the word is already in the DB, show the stored translation instead (cache differentiator). | Do not insert or increment on failure |
| Google changed the response format | Same as network failure, with a distinct text ("Сервис перевода недоступен"), logged to stderr or a log file | None |
| `tesseract` or `spectacle` missing | Popup with the exact missing package name (`pacman -S tesseract tesseract-data-eng`) | None |

Rule of thumb: every outcome produces something visible within the latency budget. The user never presses the hotkey and sees nothing.

### Saved-word list: minimal contents

Required: columns (word, translation, count, last looked up), default sort by count desc, click-to-sort on headers, a search box, delete (Delete key or context menu). Refresh on open; no live update is needed because the popup process writes to the DB and the list is a separate launch (same command with `--list`, plus a `.desktop` launcher entry so the friend can find it).

Skipped on purpose: edit, export, tags, status, pagination, statistics, import.

### Normalisation before counting (recommended rules)

1. Unicode NFC, then replace curly apostrophes (`'` U+2019) with ASCII `'`.
2. Strip leading and trailing characters that are not letters (punctuation, quotes, brackets, digits at the edges).
3. Lowercase (also fixes the `Ran` -> `Ран` proper-noun problem seen in the probe).
4. Strip a trailing possessive `'s` (`dog's` -> `dog`). Keep internal apostrophes and hyphens (`don't`, `well-known`).
5. Reject tokens with no letters, tokens under 2 characters (except `a`, `I`, though these are rarely worth saving), and tokens with mixed script (Cyrillic OCR noise).
6. Key the DB on the normalised string with a `UNIQUE` constraint.

Lemmatisation: not worth it. See the anti-feature row above for why. The practical cost of `run`/`ran`/`running` being three rows is small for a personal list, and the popup's POS variants already display the base-form meaning.

Phrase rule: a selection of 1 word goes through the same path. A selection of 2-4 words is translated and saved under the normalised phrase (lowercased, whitespace collapsed). A longer selection (above about 4 words or about 40 characters) is translated and shown but not saved, so the vocabulary list does not fill with sentences.

## Feature Dependencies

```
KDE shortcut -> command entrypoint
    └──requires──> Single-instance guard

Popup rendering (word + translation + variants)
    └──requires──> translate(word)  [one isolated function, gtx call]
    └──requires──> Word acquisition
                       ├──Selection read (PRIMARY) ──requires──> stale-selection state
                       └──OCR word pick
                              ├──requires──> Screenshot (spectacle)
                              ├──requires──> Cursor position (KWin / kdotool)
                              └──requires──> Logical->pixel coordinate mapping (HiDPI)

Normalisation ──requires before──> DB UPSERT ──requires before──> Count in popup
                                           └──requires before──> Saved-word list window

DB cache lookup ──enhances──> Popup (speed, offline)
Saved-word list: sort ──> search ──> delete   (all on one proxy model; delete is independent)

Lemmatisation ──conflicts──> "smallest version" (adds a dependency and mis-merge risk)
```

### Dependency Notes

- **Popup requires word acquisition:** both paths (selection, OCR) must produce a plain string. Everything after that point is shared, so build `acquire_word() -> str | None`, `translate()` and `save()` as three separate functions.
- **Normalisation before DB:** counts are only meaningful if the key is stable. Settle the rules before the first row is written, since changing them later means migrating data.
- **Cursor position and coordinate mapping precede OCR:** these are the highest-risk dependencies. Selection mode does not need them, so it can ship and be tested first.
- **Stale-selection state requires a tiny state file:** one text file in `$XDG_STATE_HOME`. No new component.
- **Cache lookup enhances failure handling:** it is the cheapest way to make the no-network case less bad.

## MVP Definition

### Launch With (v1)

- [ ] Hotkey -> one-shot command with a single-instance guard. This is the entry point.
- [ ] Selection mode with the stale-selection rule. It is the fastest path to a working end-to-end slice, with no coordinate problems.
- [ ] `translate()` against gtx returning main translation, POS variants and transcription.
- [ ] Popup: word, transcription, main translation, up to 3 POS groups, count line, positioned at the cursor, with click/Esc/focus-loss/timeout dismissal.
- [ ] Normalisation rules + SQLite UPSERT (word, translation, count, first_seen, last_seen).
- [ ] OCR word-under-cursor with a nearest-box fallback and the "not found" popup.
- [ ] Failure popups for no network, no word and missing dependencies.
- [ ] Saved-word list: count-desc default, click-sort, search, delete.
- [ ] DB cache hit before network.
- [ ] Arch install instructions + script + KDE shortcut steps.

### Add After Validation (v1.x)

- [ ] Manual merge of word forms, or a simple rule-based merge, if the friend reports duplicates as a nuisance.
- [ ] CSV export from the list window (small; the first step toward Anki).
- [ ] Re-translate button if a stored translation looks wrong.
- [ ] Daemon mode, if cold start misses 2 s.
- [ ] A "known / learning" flag per word.

### Future Consideration (v2+)

- [ ] Flashcards / spaced repetition / Anki export.
- [ ] Offline translation (Argos) as a fallback provider.
- [ ] Other languages and other desktop environments.
- [ ] Examples and definitions.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Hotkey entry + single-instance | HIGH | LOW | P1 |
| Selection mode + stale rule | HIGH | LOW | P1 |
| Translate (main + POS variants) | HIGH | LOW | P1 |
| Popup at cursor + dismissal | HIGH | MEDIUM | P1 |
| Normalisation + UPSERT | HIGH | LOW | P1 |
| OCR word under cursor | HIGH | MEDIUM-HIGH | P1 |
| Failure popups | HIGH | LOW | P1 |
| Saved list (sort/search/delete) | HIGH | MEDIUM | P1 |
| Install docs / script | HIGH | LOW | P1 |
| Count line in popup | MEDIUM | LOW | P1 (nearly free) |
| DB cache hit | MEDIUM | LOW | P1 (nearly free) |
| Transcription line | LOW-MEDIUM | LOW | P2 |
| Phrase rule (2-4 words) | MEDIUM | LOW | P2 |
| CSV export | LOW | LOW | P3 |
| Lemmatisation | LOW | HIGH | Skip |
| TTS / examples / flashcards | LOW (for this user) | HIGH | Skip |

## Competitor Feature Analysis

| Feature | macOS LookUp | Crow Translate | GoldenDict-ng | Our Approach |
|---------|--------------|----------------|---------------|--------------|
| Trigger | Hotkey / gesture | Global shortcut | Modifier / Ctrl+C+C | KDE shortcut -> one-shot command |
| Word source | Accessibility API | Selection / screen OCR | Selection / clipboard | PRIMARY selection first, cursor-local OCR otherwise |
| Content | Definition, audio, etc. | Translation, TTS | Dictionary articles | Translation, POS variants, transcription |
| History / saving | None | History | History / favourites | SQLite with counts (the unique part) |
| Weight | System feature | Full app | Full app | Minimal Python one-shot |

## Sources

- Live probe of the Google `translate_a/single` gtx endpoint (response structure and the `Ran`/`running` behaviour), 2026-10-23. HIGH.
- Project constraints from `.planning/PROJECT.md`. HIGH.
- Competitor behaviour (macOS Look Up, Crow Translate, GoldenDict-ng, dictpopup, QTranslate, Linguee/DeepL, Language Reactor) from prior knowledge, not re-fetched during this run. MEDIUM. Treat the per-tool details as orientation only.
- Normalisation, failure-handling and list-window recommendations are the researcher's judgement, based on how the response behaves and the "smallest complete solution" goal. MEDIUM.

---
*Feature research for: personal hotkey word-lookup + vocabulary log (Linux/KDE)*
*Researched: 2026-10-23*
