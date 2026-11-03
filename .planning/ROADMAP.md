# Roadmap: LookUp Linux

## Milestones

- [x] **v1.0 LookUp Linux** — shipped 2026-11-01; 9 phases, 43 plans, 32 requirements.
  - [Complete roadmap](milestones/v1.0-ROADMAP.md)
  - [Accepted requirements](milestones/v1.0-REQUIREMENTS.md)
  - [Closeout audit and limits](milestones/v1.0-MILESTONE-AUDIT.md)

## Current status

**v1.1 «Надёжность и распространение»** initialized 2026-11-02: [brief](v1.1-CONTEXT.md), [requirements](REQUIREMENTS.md). Phases 9–13 complete; 4 requirements remain pending in Phases 14–15. Actual MDX/DSL compatibility now passes on Windows/Linux. Yomitan and native home retain final full-suite evidence (865 tests each, zero failures/errors).

v1.0 is complete with agent verification. Phase 8 passes all seven criteria; final host and target each run 797 tests on the same code revision, with zero failures. All current product/review/verifier gates pass.

v1.1 is incomplete at Phase 14: [real MDX/DSL compatibility passes](phases/14-reliability/14-01-SUMMARY.md), resolving the premature missing-input blocker. Context provider remains blocked on both tested direct/proxy target routes; offline lookup stays usable. Second-monitor/borderless acceptance pending. Historical failed attempts and Phase 7 preservation exception remain unchanged.

## Phases

- [x] **Phase 9: Фиксация по хоткею и скорость** - Capture the requested moment and remove measured delays. (completed 2026-11-02)
- [x] **Phase 10: Компактный настраиваемый попап** - Show relevant meanings first and allow hiding context. (completed 2026-11-02)
- [x] **Phase 11: Выбор слов на замороженной сцене** - Select words on a retained scene while intercepting input. (completed 2026-11-03)
- [x] **Phase 12: Словари Yomitan** - Connect and use the user's real dictionaries. (completed 2026-11-03)
- [x] **Phase 13: Понятный первый запуск и GUI** - Discover the interface without knowing tray conventions. (completed 2026-11-03)
- [ ] **Phase 14: Надёжность в реальных сценариях** - Verify providers, real dictionaries, second monitor and borderless.
- [ ] **Phase 15: Подготовка распространения через AUR** - Build/install/update the distributable package safely.

## Phase Details

### Phase 9: Фиксация по хоткею и скорость

**Goal**: Lookup refers to the hotkey moment despite mouse movement or scene changes, without measured removable delays.
**Depends on**: v1.0 complete
**Requirements**: CAPT-06, CAPT-07, PERF-02
**Success Criteria** (what must be TRUE):

  1. Real hotkey over A followed immediately by movement to B returns A.
  2. A changing scene after invocation does not replace the captured original; frame and cursor coordinates agree.
  3. Comparable cold/warm runs report capture and first-result median/p95 before and after; budgets fixed before optimization are verified.

**Plans**: 1/2 plans executed

- [x] 09-01-PLAN.md
- [x] 09-02-PLAN.md

### Phase 10: Компактный настраиваемый попап

**Goal**: User sees the requested word and meanings first and controls unwanted popup blocks.
**Depends on**: Phase 9
**Requirements**: POP-06, SET-02
**Success Criteria** (what must be TRUE):

  1. Offline-only lookup places the requested word and relevant meanings at the start; reproduction limits for Danila's missing photo are explicit.
  2. User hides context and configures agreed blocks; subsequent requests and restart preserve choices.
  3. Hiding blocks preserves useful word results and existing card-saving behavior.

**Plans**: 0/1 plans executed

- [x] 10-01-PLAN.md

**UI hint**: yes

### Phase 11: Выбор слов на замороженной сцене

**Goal**: User selects words on a retained scene without sending pointer movements to the underlying application and regains control afterward.
**Depends on**: Phase 9, Phase 10
**Requirements**: CAPT-08, TRIG-05, TRIG-06
**Success Criteria** (what must be TRUE):

  1. A translucent layer supports selecting words from one captured scene while the underlying scene changes.
  2. Real hover text remains available on the captured scene; pointer movements on the layer do not reach the underlying application.
  3. Esc, close, repeated invocation and error return control, including a real fullscreen application.

**Research gate**: Prove KDE Wayland capture/input and hover behavior before approving implementation. A retained image does not prove the source application is frozen. Record a blocker rather than silently weakening requirements if platform limits prevent the requested behavior.
**Plans**: 2/3 plans executed

- [x] 11-01-PLAN.md
- [x] 11-02-PLAN.md
- [x] 11-03-PLAN.md

**UI hint**: yes

### Phase 12: Словари Yomitan

**Goal**: User connects real Yomitan dictionaries and gets expected translations through normal lookup.
**Depends on**: Phase 10
**Requirements**: DICT-04, DICT-05
**Success Criteria** (what must be TRUE):

  1. Danila's real archives load and known words return expected meanings through normal lookup.
  2. Reconnecting a dictionary produces a predictable result without damaging connected dictionaries.
  3. Invalid/unsupported archives show understandable errors while existing offline lookup remains usable.

**Research gate**: Inspect actual format variants and user archives. General format work may proceed without Danila's files, but compatibility with his dictionaries cannot be accepted without them.
**Plans**: TBD
**UI hint**: yes

### Phase 13: Понятный первый запуск и GUI

**Goal**: New users discover the interface, translation trigger, settings and existing windows.
**Depends on**: Phase 10, Phase 12
**Requirements**: TRIG-07, SET-03
**Success Criteria** (what must be TRUE):

  1. First launch in a clean profile shows an understandable application entry and translation instructions without knowledge of tray right-click.
  2. Discoverable GUI opens settings, words and review while the existing background mode remains usable.

**Plans**: TBD
**UI hint**: yes

### Phase 14: Надёжность в реальных сценариях

**Goal**: Real sources, second-monitor lookup and borderless usage behave predictably.
**Depends on**: Phase 11, Phase 12, Phase 13
**Requirements**: TRAN-07, DICT-06, CAPT-09, GAME-02
**Success Criteria** (what must be TRUE):

  1. A live target-environment context query demonstrates provider availability; restrictions/failures are shown separately without hiding offline articles.
  2. Real MDX and DSL results agree with source articles; untested variants remain explicit.
  3. Second-monitor lookup chooses the pointed word and positions the popup correctly at tested scales.
  4. Real borderless lookup and frozen-scene selection return application control after closing.

**Plans**: 1/2 plans executed

- [x] 14-01-PLAN.md
- [ ] 14-02-PLAN.md

**UI hint**: yes

### Phase 15: Подготовка распространения через AUR

**Goal**: User can build, install and update an AUR-ready package while retaining data.
**Depends on**: Phase 14
**Requirements**: PUB-02
**Success Criteria** (what must be TRUE):

  1. Project instructions reproducibly build and install the package in a clean target profile.
  2. Upgrade from v1.0 retains words/cards/settings; removal preserves user data according to the existing contract.
  3. Metadata and instructions are AUR-ready; actual publication is separately recorded and requires access and authorization.

**Plans**: TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 9. Фиксация по хоткею и скорость | 2/2 | Complete    | 2026-11-02 |
| 10. Компактный настраиваемый попап | 1/1 | Complete    | 2026-11-02 |
| 11. Выбор слов на замороженной сцене | 3/3 | Complete    | 2026-11-03 |
| 12. Словари Yomitan | 1/1 | Complete    | 2026-11-03 |
| 13. Понятный первый запуск и GUI | 1/1 | Complete    | 2026-11-03 |
| 14. Надёжность в реальных сценариях | 1/2 | In Progress|  |
| 15. Подготовка распространения через AUR | 0/TBD | Not started | - |

Coverage: 17/17 requirements mapped exactly once. Next: `/gsd-discuss-phase 9`.
