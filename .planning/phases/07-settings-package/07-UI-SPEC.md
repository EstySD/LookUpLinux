---
phase: 07
slug: settings-package
status: approved
reviewed_at: 2026-10-28
shadcn_initialized: false
preset: none
created: 2026-10-28
---

# Phase 7 — Native Settings UI Design Contract

Source: SET-01/TRIG-04, 07-CONTEXT D-01–D-05/D-10, 07-RESEARCH and existing Words/Review windows. Agent-selected defaults under explicit --auto. This is the Linux project's Breeze interface; original Lookupper observations do not impose its styling. Installation/doctor remain CLI/documentation surfaces.

## Design System

| Property | Value |
|---|---|
| Tool / preset | Native Qt Widgets / not applicable |
| Component library | Existing PyQt6, lazy GUI imports; no new UI dependency |
| Icon library | KDE system icon theme; textual labels remain sufficient without icons |
| Font | QApplication system font, live KDE font/palette/scaling |
| Existing analog | lookup/learning_gui.py reusable native windows, plain wrapped status labels |

One reusable nonmodal window titled «Настройки», raised by the enabled tray action. Closing it leaves the tray owner running. No stylesheet, hardcoded font family, custom color theme, web rendering or new navigation shell.

## Spacing Scale

| Token | Logical pixels | Usage |
|---|---|---|
| xs | 4 | Compact text/icon gaps if explicit spacing needed |
| sm | 8 | Adjacent controls and action buttons |
| md | 16 | Outer content margin and related field groups |
| lg | 24 | Major group separation |
| xl | 32 | Reserved; not needed in this compact window |
| 2xl | 48 | Reserved |
| 3xl | 64 | Reserved |

Native exception: prefer existing QLayout/QStyle layout margins, control padding, focus outlines and minimum target sizes over forcing this scale onto Qt internals. Explicit layout additions use the scale. Start near 600×560 logical pixels; resize freely, clamp initial size to available work area. A scrollable content region keeps every field reachable on small/high-DPI screens; action/status area remains reachable without clipped text.

## Typography

Let B be the current QApplication font point size. Declare three relative sizes and two weights, preserving user font/scaling choices rather than fixed screen pixels.

| Role | Size | Weight | Line height |
|---|---|---|---|
| Body / help / status | B | Normal (400) | Native Qt font metrics and wrapping |
| Control label | B | Normal (400) | Native Qt control metrics |
| Optional group heading | 1.2×B | DemiBold (600) | Native Qt font metrics |
| Display, reserved | 1.4×B | DemiBold (600) | Native Qt font metrics; no display text needed here |

Do not introduce extra typography roles. Native metrics are the explicit exception to web pixel/line-height tokens. Reflow on font/theme change. Status/help text is plain text, wraps and is selectable; file/dictionary names never become rich text.

## Color

| Role | Value | Usage |
|---|---|---|
| Dominant, roughly 60% | QPalette.Window / WindowText | Window and normal text |
| Secondary, roughly 30% | QPalette.Base / AlternateBase / Text | Dictionary list and editable fields |
| Accent, at most 10% | QPalette.Highlight / HighlightedText | Selected dictionary row and native focused/default action indication |
| Destructive | Native palette semantics only | No destructive action in this phase |

Percentages describe hierarchy, not painted-area quotas. Accent is reserved for selection/focus; do not color every button or status message. Native disabled palette handles unavailable controls. Every success/error/pending state has explicit text, never color alone. Verify Breeze light and dark.

## Components and Interaction

Use a single-column form grouped into «Вызов», «Словари», «Перевод и запуск», followed by persistent status and «Применить настройки» / «Закрыть» buttons. The shortcut group is the initial visual anchor and its editor receives initial keyboard focus. The first button is enabled only for valid changed values and no apply currently pending. It does not close the window. Closing never applies unsubmitted edits; reopening loads saved/effective state.

| Control | Label / default | Contract |
|---|---|---|
| Native shortcut editor | «Горячая клавиша», Meta+Shift+D default | One nonempty chord; show actual KDE binding when overridden externally. Invalid/multichord input gets an inline explanation. Check availability before applying; never steal another action's shortcut. |
| Checkable dictionary list | «Словари — сверху приоритетнее» | Show discovered dictionaries in configured order, each enabled checkbox and readable name. Preserve temporarily unavailable configured IDs with «недоступен» status. Selection is separate from enabled state. |
| Reorder buttons | «Выше» / «Ниже» | Accessible names «Переместить словарь выше» / «Переместить словарь ниже». Move selected dictionary one place without changing its checkbox. Disable at boundaries/no selection. Provide keyboard-operable alternative to any drag operation. |
| Integer spin box | «Закрывать попап через», suffix «с» | Default 20 seconds, range 1–300 seconds inclusive; visible bound validation. Next popup uses saved duration. Existing hover/close lifecycle remains intact. |
| Checkbox | «Онлайн-перевод» | Saved off prevents new online requests; current bounded requests may finish but stale replies cannot publish. Help: «При отключении используются только локальные словари». |
| Checkbox | «Запускать при входе в KDE» | Default enabled; saved choice governs next login. No immediate logout or application exit. |

Changing fields does not mutate live state before Apply. Capture a settings snapshot at Apply; disable Apply and editable controls for that bounded operation, keep Close responsive. Show pending status until worker-owned reload and shortcut/config application outcomes are known. Queue completions use request identity so late acknowledgements cannot overwrite newer state. Shortcut failure retains/restores old actual binding and saved settings; clearly distinguish saved values from values not applied at runtime. No success toast before acknowledgement. On recoverable error keep edits for retry.

## Copywriting Contract

| Element | Exact copy |
|---|---|
| Primary CTA | «Применить настройки» |
| Secondary action | «Закрыть» |
| Initial status | «Изменения применяются после нажатия кнопки». |
| Pending | «Применяем настройки…» |
| Success | «Настройки применены. Автозапуск изменится при следующем входе в KDE». |
| Empty dictionary heading | «Локальные словари не найдены» |
| Empty dictionary body | «Установите Mueller 7 с пакетом или добавьте словари в каталог lookup/dicts. Для проверки запустите lookup --doctor». |
| All dictionaries disabled help | «Локальные словари отключены. При выключенном онлайн-переводе перевод будет недоступен». |
| Invalid shortcut | «Укажите одно сочетание клавиш». |
| Shortcut conflict | «Это сочетание занято в KDE. Выберите другое или измените его в системных настройках клавиатуры». |
| Save failure | «Не удалось сохранить настройки. Проверьте доступ к файлу настроек и попробуйте ещё раз». |
| Runtime failure | «Не удалось применить настройки. Проверьте состояние через lookup --doctor и попробуйте ещё раз». |
| Rollback uncertainty | «Не удалось восстановить горячую клавишу. Проверьте сочетание LookUp Linux в системных настройках KDE». |
| Destructive confirmation | None: dictionary disable/reorder and autostart toggle preserve history/cards and need no confirmation. |

Do not display raw exception messages, captured text, history content or network payloads. Missing dictionaries do not disable unrelated settings; all-off remains a valid explicit configuration with the explanatory text above.

## Accessibility and Acceptance

Associate every field label with its control; accessible names match Russian labels. Dictionary list name «Порядок и включение словарей»; row exposes name, checked state and availability. Status name «Применение настроек». Native visible focus, tab order follows form/list/reorder/toggles/actions; Space toggles, Enter activates focused button, Escape closes. Shortcut capture must not trap tab navigation or trigger Apply accidentally. No focus stealing from lookup when Settings is closed.

Agent checks actual native window in both Breeze themes and representative scaling, small available work area, keyboard-only edits, empty/unavailable dictionaries, conflict/save/runtime errors and asynchronous acknowledgement. Behavior checks prove changed physical key works and old key stops, selected dictionary/order affects next lookup, online-off makes no new request, next-popup timeout changes, and actual subsequent login follows autostart flag. Isolate XDG paths before Qt in fixtures; report agent evidence honestly.

## Registry Safety

| Registry | Blocks used | Safety gate |
|---|---|---|
| None | Native existing Qt Widgets | Not applicable; no React/shadcn/third-party registry assets |

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

Approval: pending independent UI checker.
