# Requirements: LookUp Linux v1.1

Defined 2026-11-02 from [agreed brief](v1.1-CONTEXT.md). All requirements are pending; archived v1.0 acceptance is unchanged. IDs continue archived categories, including deferred IDs.

## v1.1 Requirements

### First priority: capture and speed

- [x] **CAPT-06**: Hotkey over A followed immediately by movement to B translates A; cursor coordinates and frame are captured consistently before OCR and translation.
- [x] **CAPT-07**: A scene change immediately after the hotkey does not replace the original captured scene used for recognition.
- [x] **PERF-02**: First useful results avoid measured removable delays. Comparable cold/warm baseline and final runs report hotkey-to-capture and hotkey-to-result separately, median and p95; numeric budgets are fixed after baseline before optimization.

### First priority: compact popup

- [x] **POP-06**: With online translation disabled, the requested word and relevant meanings appear at the start of the popup without searching through a long article.
- [x] **SET-02**: User can hide context and configure the popup blocks agreed during phase discussion; choices apply to subsequent requests and survive restart.

### First priority: frozen scene selection

- [x] **CAPT-08**: User can open a translucent layer with a captured scene and select words from that scene without recapturing the underlying application for each selection.
- [x] **TRIG-05**: Mouse movements during layer selection do not reach the underlying application; captured hover text remains available for selection.
- [x] **TRIG-06**: Esc, closing, repeated invocation and layer errors return control to the underlying application, including real fullscreen applications.

### First priority: Yomitan

- [x] **DICT-04**: User can connect Danila's real Yomitan dictionaries and obtain their expected meanings through normal lookup.
- [x] **DICT-05**: Invalid or unsupported dictionary archives produce understandable errors without damaging connected dictionaries; repeated connection has predictable behavior.

### First priority: discoverable GUI

- [x] **TRIG-07**: First launch exposes an understandable interface and how to translate without prior knowledge of right-clicking the tray.
- [x] **SET-03**: User can explicitly open settings and existing words/review windows from a discoverable application interface.

### Second priority: reliability and distribution

- [x] **TRAN-07**: Available context providers return live results in the target environment; restrictions/failures have understandable states and preserve ready offline articles. Error handling is not counted as successful provider availability.
- [x] **DICT-06**: Real MDX and DSL dictionaries return results checked against their source articles; synthetic fixtures alone do not establish compatibility.
- [x] **CAPT-09**: On a second monitor the word under the cursor and popup position remain correct with tested scaling and coordinates.
- [x] **GAME-02**: Real borderless applications support translation and frozen-scene selection, then regain control without stuck input capture.
- [ ] **PUB-02**: User receives a reproducibly buildable AUR-ready package and installation/update instructions; clean install, data-preserving upgrade and removal are verified. Actual public AUR submission requires access and publication authorization and is recorded separately.

## Future Requirements

Synonyms and permanent scene screenshots remain deferred. Secondary phase details may be refined after first-priority work.

## Out of Scope

Audio pronunciation, CEFR and new Anki synchronization are excluded. Existing cards/export are retained. No X11, other DE, new languages, gamepad or whole-screen translation.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CAPT-06 | Phase 9 | Complete |
| CAPT-07 | Phase 9 | Complete |
| PERF-02 | Phase 9 | Complete |
| POP-06 | Phase 10 | Complete |
| SET-02 | Phase 10 | Complete |
| CAPT-08 | Phase 11 | Complete |
| TRIG-05 | Phase 11 | Complete |
| TRIG-06 | Phase 11 | Complete |
| DICT-04 | Phase 12 | Complete |
| DICT-05 | Phase 12 | Complete |
| TRIG-07 | Phase 13 | Complete |
| SET-03 | Phase 13 | Complete |
| TRAN-07 | Phase 14 | Complete |
| DICT-06 | Phase 14 | Complete |
| CAPT-09 | Phase 14 | Complete |
| GAME-02 | Phase 14 | Complete |
| PUB-02 | Phase 15 | Pending |

Coverage: 17/17 mapped exactly once; 0 unmapped.
