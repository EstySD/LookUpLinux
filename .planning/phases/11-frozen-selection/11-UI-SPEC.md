---
phase: 11
slug: frozen-selection
status: approved
reviewed_at: 2026-11-02
reviewed_by: independent-gsd-ui-checker
shadcn_initialized: false
preset: none
created: 2026-11-02
---

# Phase 11 — UI Design Contract

Native Qt contract for CAPT-08, TRIG-05 and TRIG-06. Sources: `11-CONTEXT.md`, Phase 10's approved UI contract, existing `lookup/gui.py`, and the orchestrator's automatic entry/lifecycle decisions. Agent-selected under `--auto`; no human acceptance. The separate research gate must be recorded as passed before implementation approval; this document is not platform proof.

## Design System

| Property | Value |
|---|---|
| Tool | Existing native PyQt6 widgets and painter; no web design system |
| Preset | KDE system style, normally Breeze |
| Component library | QWidget, QLabel, QPushButton/QToolButton, existing Popup/PlainBlock |
| Icon library | Existing QIcon.fromTheme with QStyle fallback for close |
| Font | QApplication system font; retain user family and size |

No new dependencies, assets, custom stylesheet or configuration screen. shadcn and third-party registry initialization do not apply to this Python/native Qt project. Reuse Phase 10's popup layout, compact defaults, article disclosures and settings without restyling.

## Spacing Scale

| Token | Value | Usage |
|---|---|---|
| xs | 4 logical px | Compact instruction/control gap |
| sm | 8 logical px | Native control-row gaps and toolbar internal padding |
| md | 16 logical px | Toolbar inset from captured monitor edges; existing popup margin |
| lg | 24 logical px | Reserved; no new use required |
| xl | 32 logical px | Existing popup available-screen inset budget |

Exceptions: native widget/focus metrics remain style-owned. Scene pixels use the existing physical-to-logical capture transform rather than spacing tokens. Preserve the popup's 440-logical-pixel maximum width and existing bounded height/scroll behavior.

## Typography

| Role | Size | Weight | Line Height |
|---|---|---|---|
| Instructions, status and native controls | 1.00 × system point size | Normal (400) | Native font metrics |
| Dictionary summaries / selected-word emphasis | 1.00 × system point size | DemiBold (600) | Existing native document metrics |
| Requested-word / selection heading | 1.50 × system point size | DemiBold (600) | Native font metrics |
| Existing loading/error heading | 1.75 × system point size | DemiBold (600) | Native font metrics |

Exactly three size levels and two weights, inherited from Phase 10. Do not impose web line-height ratios or fixed pixel fonts on native controls. Captured text is image content and is never retypeset.

## Color

| Role | Value | Usage |
|---|---|---|
| Dominant (approximately 60%) | Opaque retained image, with a 20%-opacity QPalette.Window tint painted over that image | Frozen scene remains recognizable and visually distinct from ordinary live interaction |
| Secondary (approximately 30%) | Opaque QPalette.Window/Base with WindowText/Text | Instruction strip, status, close control and existing popup surfaces |
| Accent (up to 10%) | QPalette.Highlight/HighlightedText and native focus palette | Selected word outline, selected text and keyboard focus only |
| Destructive | Not introduced | No deletion or destructive action in this phase |

The ratios describe visual emphasis, not mandatory screen areas. Accent is reserved for the selected word, text selection and focus; do not use it across the whole captured screen. Paint the retained image as an opaque base **before** adding the translucent tint. Do not make the entire surface transparent onto the live application, and do not enable input transparency. The current application palette remains authoritative for light, dark and high-contrast modes.

## Scene Layout and Selection

1. Cover only the captured monitor/source area, using its recorded origin, dimensions and scale. Display the frame without cropping, stretching or mismatching pointer/OCR coordinates. Other-monitor support and borderless expansion remain later-phase work.
2. Preserve CAPT-02: a fresh valid PRIMARY selection follows the existing ordinary-popup path without opening a scene layer. In the OCR path, the existing hotkey starts one retained-scene session **and automatically looks up the initially pointed word**, preserving the one-hotkey result. No extra selection click, new shortcut, setting or new entry screen is required. Further primary-button clicks select individual words from the same retained frame; they do not recapture the source or consult PRIMARY again.
3. Render the retained frame, including hover text already captured at invocation, then its tint, selected-word outline, instruction strip and popup. Do not promise new source hover interactions while the source is covered. The raw untinted image remains the OCR input.
4. Place an opaque native instruction strip within a 16-logical-pixel monitor inset. Its close button is always visible and keyboard reachable. Prefer the top edge away from the current selection; if a popup would overlap it, clamp the popup within the remaining available monitor area. Never move the whole scene or alter its coordinate origin to make room.
5. Use the native crosshair cursor over the selectable scene and ordinary arrow over controls. After a successful choice, outline the selected word's mapped OCR box. A text status also identifies the choice; color alone must not convey success. Pointer motion over the layer is consumed without forwarding it to the source application.
6. Show results through the existing popup near the selected point, clamped to the captured monitor. Preserve Phase 10's requested-word title, useful-first dictionary summaries, context visibility, article expansion, save warnings and explicit card action. A second selection replaces the prior popup/result using existing request-generation rules while retaining the same scene.
7. Do not save the captured scene to user storage or add screenshot controls. Release scene pixels and owned input/surfaces when the session ends.

## Lifecycle and Keyboard Contract

| Event | Required visible and input behavior |
|---|---|
| Open in OCR path | Retained scene becomes input-taking, instructions and close action appear, initial lookup uses the key-time point; underlying pointer input remains blocked |
| Fresh valid PRIMARY at invocation | Existing ordinary popup appears without a scene layer; retain current selection precedence |
| Initial lookup / next selection pending | Existing loading state belongs to the current point; layer continues intercepting input; Esc and close remain available |
| Successful selection | Highlight selected word, show existing result popup; subsequent scene clicks remain available |
| No reliable word at clicked point | Show the no-word status below; keep the retained scene available for another choice; do not create a history/card entry |
| Esc from layer **or its popup** | End the entire session, cancel pending requests, close both surfaces and return application control |
| Layer close or popup close | End the entire session and release input; never leave an invisible input-taking layer |
| Repeated hotkey while active | Dismiss the active session and return control; a later invocation captures a new scene |
| Existing popup/inactivity timeout | End the entire session, not just the result popup; reuse the existing timeout policy rather than introducing a new setting |
| Capture, OCR execution or layer operational error | Tear down layer/input ownership first; report the normal actionable error afterward without leaving a blocking surface |
| Focus moves between the owned layer and popup | Remain in the same session; do not mistake the popup for an external application |
| Focus moves to another application | End the session, cancel pending results and release input; do not reacquire focus with a late callback |
| Process/session shutdown | Release all owned surfaces/input and transient frame data; preserve the existing background daemon lifecycle |

The layer receives keyboard focus only after its surface is visible. Use native strong focus on its close control, ordinary Tab/Shift+Tab traversal among owned controls, and a session-wide Esc route that also works while a popup control has focus. Do not claim generic Qt focus APIs guarantee Wayland input isolation; the research and final live verification supply that evidence. Keyboard-only activation/closing of controls is required; do not add a new keyboard word-navigation feature.

## Copywriting Contract

| Element | Copy |
|---|---|
| Layer title / accessible name | Выбор слова по снимку |
| Primary selection instruction | Нажмите на слово, чтобы увидеть перевод. Esc — закрыть снимок. |
| Scene explanation | Снимок экрана сохранён для выбора. Приложение под ним продолжает работать. |
| Close CTA / accessible name | Закрыть снимок |
| Close tooltip | Закрыть снимок (Esc) |
| Successful selection status | Выбрано слово: {word} |
| Empty/no-word heading | Слово не найдено |
| Empty/no-word body | Нажмите на другое слово на снимке или закройте снимок клавишей Esc. |
| Selection pending | Ищем перевод… |
| Capture unavailable | Не удалось получить снимок. Повторите вызов горячей клавишей. |
| Layer operational error | Не удалось продолжить выбор по снимку. Управление возвращено приложению. Повторите вызов горячей клавишей. |
| Provider/result errors | Preserve existing actionable popup messages; ready offline results remain useful |
| Destructive confirmation | Not applicable; no destructive actions introduced |

Place the scene explanation in the instruction strip or its native accessible description; it must be discoverable without developer terminology. Never label the source application “paused” or “frozen.” All source text and dictionary content remains inert plain text. Elide unusually long visible word/status text within the strip, with its full text available to assistive technology and a tooltip; do not allow it to push close off-screen.

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|---|---|---|
| None | Existing native Qt only | Not applicable — no registry or downloaded UI code |

## Acceptance Evidence

- Native Qt tests: retained frame identity across initial and repeated choices, correct monitor/scale coordinates, no-word state, generation cancellation and transient image cleanup.
- Keyboard/lifecycle tests: Esc from both owned surfaces, visible close and Tab focus, reinvocation, timeout, shutdown/error teardown, internal focus transfer and external-focus termination.
- Existing Phase 10 tests continue to verify compact settings, immutable card payloads, plain text, disclosure, useful offline results and saved preferences.
- Live KDE tests must separately establish captured hover text, source-side input absence while selecting, restored input afterward and a real fullscreen application. A picture of the overlay alone is insufficient. Record raw evidence, same-source-process identity and source execution state without claiming suspension.
- Parent-reported live probe evidence is positive; `11-RESEARCH.md` must contain the final gate decision before implementation approval. Final integrated product acceptance remains separate from the proof-of-feasibility probe and from human feedback.

## Sources and Documentation

- `11-CONTEXT.md`, roadmap and requirements provide the boundary and retained-scene/input/cleanup obligations.
- Approved `10-UI-SPEC.md` and `lookup/gui.py` supply system-font ratios, palette roles, spacing, popup bounds and existing native controls.
- `docs/lookupper/architecture.md`, `linux-requirements.md` and `evidence.md` distinguish Linux contracts from unverified Windows observations; they do not prove this layer's platform behavior.
- Context7 CLI lookup of official Riverbank PyQt6 QWidget/QGuiApplication documentation confirmed visible-widget focus, focus policy and palette contracts. These APIs do not replace live Wayland proof. Source: https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtwidgets/qwidget.html.

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** Independent gsd-ui-checker approved all six dimensions on 2026-11-02. Research gate and implemented-product acceptance remain separate.
