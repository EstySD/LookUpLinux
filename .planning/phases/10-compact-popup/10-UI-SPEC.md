---
phase: 10
slug: compact-popup
status: approved
reviewed_at: 2026-11-02
reviewed_by: independent-gsd-ui-checker
shadcn_initialized: false
preset: none
created: 2026-11-02
---

# Phase 10 — UI Design Contract

Native Qt contract for POP-06 and SET-02. Decisions come from `10-CONTEXT.md`; measurements and visual defaults come from existing `lookup/gui.py` and `lookup/settings_gui.py`. Agent-selected under `--auto`, without human acceptance.

## Design System

| Property | Value |
|----------|-------|
| Tool | Existing native PyQt6 widgets; no web design system |
| Preset | KDE system style, normally Breeze |
| Component library | QCheckBox, QPushButton/QToolButton, QGroupBox, QScrollArea and existing PlainBlock |
| Icon library | QIcon.fromTheme with existing QStyle fallback |
| Font | QApplication system font; preserve user family and size |

No dependency, asset, theme or stylesheet addition. shadcn initialization and registry gates are not applicable to native Qt.

## Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4 logical px | Optional compact inline gap |
| sm | 8 logical px | Existing popup layout, heading/body and control gaps |
| md | 16 logical px | Existing popup outer margins and section separation |
| lg | 24 logical px | Reserved; no new use required |
| xl | 32 logical px | Existing available-screen inset budget |

Exceptions: native settings control metrics remain style-owned. Preserve 440-logical-pixel maximum popup width and existing monitor-aware height/position constraints. Never introduce horizontal scrolling.

## Typography

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body and controls | 1.00 × system point size | Normal (400) | Native font/document metrics |
| Dictionary heading / structured meaning | 1.00 × system point size | DemiBold (600) | Native font/document metrics |
| Requested-word heading | 1.50 × system point size | DemiBold (600) | Native font metrics |
| Error/loading heading | 1.75 × system point size | DemiBold (600) | Native font metrics |

Three size levels, two weights. These preserve the existing accessible scaling contract; do not replace system metrics with fixed web pixel sizes or force a new line height.

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (approximately 60%) | QPalette.Window / Base | Popup and text surface |
| Secondary (approximately 30%) | QPalette.WindowText / Text and native neutral control surfaces | All content and ordinary controls |
| Accent (up to 10%) | QPalette.Highlight / HighlightedText, native focus palette | Text selection and keyboard focus |
| Destructive | Not introduced | No destructive operation in this phase |

The ratios describe visual emphasis, not required painted areas. Accent is reserved for selected text and native focused/active control states. Never hard-code light-theme colors; native dark and high-contrast palettes remain authoritative. Warning icon plus explicit text carries error meaning without relying on color.

## Content and Interaction

1. Requested word remains the top-level title. Preserve requested/lemma distinction and available transcription.
2. Structured dictionary meanings remain visible in configured dictionary order. All dictionary summaries precede full article bodies, so a long early article cannot bury later meanings.
3. For articles without structured senses, show a plain-text excerpt of at most 240 characters with a visible ellipsis when shortened. This is an excerpt, not a fabricated relevance ranking.
4. Put full article bodies after the summary area. Each nonempty body has a named, keyboard-focusable expand control. Default is collapsed. Expanded state is indicated by control text and checkable state; Enter/Space activates it. Collapsing does not remove the summary.
5. The `popup_expand_articles` preference sets initial expansion for every new result. Manual expansion affects the current popup only. Loading, error and new results clear old disclosure controls.
6. Source context and its translation form one optional block, hidden by default. The contextual word meaning is independent and visible by default. Hidden blocks, including pending/error labels belonging to them, remain hidden after asynchronous result updates.
7. Preserve dictionary/source labels, useful results, history count, save warnings and the existing explicit card action. Hidden display blocks do not change stored context or the card snapshot.
8. Keep native text selection/copy behavior and existing bounded plain-text rendering. Disclosure never enables rich text, browser navigation or unbounded rendering. Existing truncation indication remains visible if a display safety limit is reached.
9. Expanding content updates popup sizing using existing screen constraints; long content remains reachable through the existing scroll area. Expanding/collapsing must not dismiss the popup as an outside click or restart lookup.
10. Preserve Esc, close button, timeout, outside-click/focus behavior and request-generation rules.

## Settings Controls

Reuse the existing settings apply transaction. Add one native group, `Содержимое попапа`, with three checkboxes:

| Config field | Label / accessible name | Default |
|--------------|-------------------------|---------|
| popup_show_context | Показывать исходный текст и перевод контекста | Unchecked |
| popup_show_meaning | Показывать значение слова в контексте | Checked |
| popup_expand_articles | Разворачивать полные словарные статьи | Unchecked |

Connect edits to existing dirty-state detection. Disable controls during pending apply and restore their saved values on load/rollback. The established `Применить настройки` action persists preferences; next lookup and restart use them. No immediate config write on checkbox click.

## Copywriting Contract

| Element | Copy |
|---------|------|
| Primary settings CTA | Применить настройки |
| Expand article | Показать полную статью — {dictionary name} |
| Collapse article | Свернуть статью — {dictionary name} |
| Empty/no-match heading | Preserve existing `REASONS['not_found']` heading |
| Empty/no-match body | Preserve existing no-match explanation and retry guidance |
| Loading | Ищем перевод… |
| Offline indication | Онлайн-перевод выключен. |
| Save/apply failures | Preserve existing actionable save/apply messages; never hide with optional context |
| Destructive confirmation | Not applicable; no destructive actions introduced |

Every disclosure control includes its dictionary name so assistive technology can distinguish repeated controls. Preserve native focus visibility, tab traversal and system language copy. Article text remains selectable plain text.

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| None | Existing native Qt only | Not applicable — no registry or downloaded UI code |

## Acceptance Evidence

- Offscreen native Qt tests assert summary ordering with a long first article and useful later senses, bounded unstructured excerpts, expand/collapse via keyboard, and new-result reset.
- Assert that disabled context/meaning stays hidden after late updates; dictionary results, count and card snapshot remain useful.
- Config round-trip and native settings apply/reload/rollback tests cover all three fields and defaults for older configuration files.
- Verify popup screen constraints and scrolling remain valid after disclosure; existing plain-text and size-limit tests still pass.
- Any target KDE run is agent evidence. Danila's missing photo and unavailable exact article remain explicit reproduction limits.

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** Independent gsd-ui-checker approved all six dimensions on 2026-11-02. Implementation and native KDE acceptance are separate gates.
