---
phase: 05
slug: app
status: approved
reviewed_at: 2026-10-26
shadcn_initialized: false
preset: not-applicable-native-qt
created: 2026-10-26
decision_source: accepted brief and explicit --auto delegation
---

# Phase 5 — UI Design Contract

Native Operate surface for reading EN→RU results while another application remains the task context. PRODUCT.md, DESIGN.md and 05-CONTEXT D-01..10 are authoritative. Sizes/timeouts below are delegated defaults, not reported user preferences. Original Lookupper selection/cancellation rules remain unverified (evidence.md Q04–Q06); the Linux contracts govern.

## Design System

| Property | Value |
|---|---|
| Tool / preset | Native Qt Widgets; shadcn and web registries not applicable |
| Component library | PyQt6 QWidget/QLabel/QScrollArea/QToolButton/QMenu/QSystemTrayIcon/QTimer |
| Style | Installed KDE Breeze through the KDE Qt platform theme; no global stylesheet |
| Icon library | QIcon.fromTheme with standard QStyle fallback; no downloaded assets |
| Font | QApplication system font family and configured point size; no bundled font |
| Existing evidence | Phase4 proves cursor capture, kdotool placement/focus and native tray menu |

## Spacing Scale

| Token | Logical Qt px | Usage |
|---|---:|---|
| xs | 4 | IPA/lemma inline separation, icon/text gap |
| sm | 8 | Related rows, title/close gap, footer padding |
| md | 16 | Popup outer margins, dictionary/context section breaks |
| lg | 24 | Major result/context separation when both exist |
| xl | 32 | Total reserve from available monitor width/height |

Exceptions: native control padding, scrollbar width, focus outline and menu geometry come from QStyle metrics; never force those to this scale. Cursor gap is the existing geometry helper's 12 logical px. Use one scroll surface, not nested decorative cards.

## Typography

Let P be QApplication.font().pointSizeF(); derive from pixelSize when necessary. Recompute on application-font changes. Exactly three sizes (P, 1.5P, 1.75P) and two weights (400/600); preserve user's family and scaling.

| Role | Size | Weight | Line height |
|---|---|---:|---|
| Body / IPA / context | P | 400 | Native QFontMetricsF.lineSpacing; paragraphs separated by 8px |
| Source / POS / status label | P | 600 | Native lineSpacing |
| Word / short phrase heading | 1.5P | 600 | Native lineSpacing, wrap rather than clip |
| State heading | 1.75P | 600 | Native lineSpacing |

Never render a whole article bold. Source text preserves paragraph/newline structure. Sentence requests use “Перевод выделения” as heading and put original text in the scroll body; no thousand-character title.

## Color

| Role | Palette value | Usage |
|---|---|---|
| Dominant (~60%) | QPalette.Window / WindowText | Popup chrome, heading and normal text |
| Secondary (~30%) | QPalette.Base / Text | Scrollable reading surface; preserve native Breeze contrast |
| Accent (at most ~10%) | QPalette.Highlight / HighlightedText | Actual text selection and native focused/active control indication |
| Destructive | Not used in this phase | No history deletion; Quit is not destructive |

Percentages describe attention hierarchy, not hardcoded fills. No custom hex palette, gradients, shadows or red error panels. Use standard information/warning icons with text. Palette/style changes recolor existing surfaces without restart; do not overwrite KDE colors.

## Popup Composition and Geometry

- Frameless, focusable native window; reuse validated owned kdotool move/raise/activate. Confirm placement from KWin, not Qt's possible Wayland (0,0) report.
- Preferred width 440 logical px; cap at available-monitor width minus 32px, with 280px minimum only when that reserve fits. Preferred content height follows sizeHint; cap at 540px and available height minus 32px. On smaller monitors clamp to available geometry instead of enforcing a minimum offscreen.
- Use platform.popup_rect with cursor gap 12px and current screen.availableGeometry. Keep the entire outer rectangle inside it at all four scales; native shadow is not extra layout padding.
- Top row: searched surface form (or state heading), optional lemma/IPA directly below, Close tool button at top right. Body: ordered dictionary sources → POS/value groups → full article → original context → context translation/status. Footer: confirmed count or distinct save warning. No guessed transcription/POS and no empty metadata placeholders.
- Exactly one vertical QScrollArea; horizontal scrolling disabled. Word-wrap body, context and long unbroken tokens; full text remains selectable. Keep Close outside scrolling; place long headings/content inside the scroll surface if needed to preserve the outer height cap.
- Every source/provider/user string uses explicit PlainText or setPlainText, never AutoText/rich HTML. No article hyperlinks, images, file resources or remote document loading.

## Interaction and Async States

- A trigger replaces the current generation, hides its card programmatically, freezes selected text or source frame/point, then shows loading. Never capture the application's loading popup. Programmatic capture/reposition hides are not user dismissal.
- New admissible primary text bypasses OCR; unchanged consumed selection falls to OCR; absent/invalid primary resets in-memory freshness. Do not display or modify clipboard history.
- Loading is a real visible state after source freeze, but is not a useful-card latency result. The serial worker's detached main-result callback may replace loading before context translation finishes. A late context update changes only its context section and never increments count again.
- Every queued UI update checks current request identity. A new trigger or user dismissal makes old callbacks inert: no reopened card, replaced newer content or stale history write. Keep existing finite context join; queued-latest delay must be measured, not described as immediate cancellation.
- Dismiss by Close, Escape, click outside, focus loss, or 20 seconds of inactivity. Start/reset timeout when current loading/useful content becomes visible; reset on deliberate in-card key, pointer-button, selection or wheel interaction. A context-only update does not extend timeout. Passive hover/movement does not keep a card alive indefinitely.
- Arm focus-loss dismissal only after initial placement/activation settles, following Phase4. Once armed, actual outside/focus events dismiss the generation. Loading/errors use the same rules. Never disable KWin focus protections.

## Copywriting Contract

| Element | Russian copy / rule |
|---|---|
| Primary control | “Закрыть”; icon-only accessible name “Закрыть карточку”, tooltip “Закрыть (Esc)” |
| Loading | “Ищем перевод…”; context subsection “Переводим контекст…” only while that request is pending |
| Empty heading/body | “Не найдено” / “Наведите курсор на английское слово или выделите текст и повторите поиск.” |
| No network | “Нет сети” / “Проверьте подключение и повторите поиск. Офлайн-словари доступны.” |
| Provider blocked / timeout | “Онлайн-перевод заблокирован” / “Попробуйте позже.”; “Перевод не ответил вовремя” / “Повторите поиск.” |
| Online disabled | “Онлайн-перевод выключен.” Show alongside usable offline content; do not call it a connection failure |
| Missing dependency | “Не установлен пакет {known_package}” / “Установите {known_package} и повторите поиск.” Map fixed reasons to known package names only |
| Cursor / capture / OCR failure | “Не удалось получить положение курсора” / “Не удалось получить снимок экрана” / “Не удалось распознать текст”; follow with “Повторите поиск.” |
| Source/context labels | “Словарь: {name}”, “Исходный текст”, “Перевод контекста”; plain text and source order retained |
| Partial context failure | “Перевод контекста недоступен: {fixed_reason}.” Preserve the complete useful main result |
| Confirmed history | “Искали {N} раз”; show only the actual returned count after one successful guarded write |
| Save failure | “Не удалось сохранить поиск. Перевод доступен; повторите поиск позже.” Never show false saved/count success |
| Cache persistence failure | “Не удалось обновить кэш перевода.” Preserve the useful result and any genuinely confirmed history count |
| Busy context slot | “Перевод контекста пока недоступен.” Preserve the main card; do not describe an unstarted request as a network failure |
| Sentence history status | “Текст не добавлен в историю слов.” No invented word counter |
| Destructive confirmation | Not applicable; no destructive action in Phase5; Quit needs no confirmation |

Tray tooltip/application identity: “LookUp Linux”. Menu order: “Слова”, “Повторение”, “Настройки”, separator, “Выход”. The first three actions remain explicitly disabled until Phase6/7 supplies their real surfaces; no placeholder dialogs or fake navigation. Exit immediately hides tray/card, invalidates pending UI/history, and finishes bounded cleanup while Qt remains responsive.

## Keyboard and Accessibility

Escape always dismisses the current card; Tab/Shift+Tab follow actual interactive controls in visual order, with native focus indicators. Close is keyboard-focusable; text selection supports normal copying without an automatic clipboard write. Set accessible names for popup (“Перевод LookUp Linux”), Close, loading/status and context regions. Pair icons with readable text, preserve system contrast, user font size and text antialiasing. No animation required; no focus trap or forced pointer movement.

## Registry Safety

| Registry | Blocks used | Safety gate |
|---|---|---|
| None | Native installed Qt/KDE components only | Not applicable, verified from existing stack 2026-10-26 |

## Visual and Behavioral Acceptance

Use controlled public text, temporary dictionaries/config/DB and the actual production route in Arch VM. Inspect light/dark Breeze at 100/125/150/200%; verify full outer bounds, readable IPA/Cyrillic/POS, long multi-source article scrolling, palette changes without restart and visible native tray menu. Batch one visual inspection round and one confirmation after fixes; remove transient screenshots. Deterministic delayed-A/new-B and close-while-pending tests prove stale UI/history suppression; verify exactly one count across main/context updates, sentence no-row, save failure, all dismissal routes and fresh/repeated/absent selection. Record first useful-card timing separately from loading/final context; Phase4 timing is not production latency proof.

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS

**Approval:** independent UI checker verified all six dimensions; defaults are
agent decisions under --auto. No human design approval is claimed.
