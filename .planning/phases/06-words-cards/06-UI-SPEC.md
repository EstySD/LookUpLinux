---
phase: 06-words-cards
status: ready
source: agent-selected under explicit --auto
---
# Phase 6 Native UI Contract

Reuse Breeze/system fonts/palette/icons, native Qt widgets and Russian copy. No web rendering, fixed custom theme or learning navigation scaffold. Words/Review actions enabled; Settings remains Phase7. One reusable window per action; closing it hides/closes that surface without quitting the tray daemon.

Words: title «Слова», search field with accessible name «Поиск слов», sortable table «Слово / Перевод / Искали / Последний поиск». Default numeric count descending, stable word tie. Selected-row actions «В карточки», «Удалить из истории». Delete copy says «Учебная карточка сохранится»; no destructive card deletion in this phase. Empty states distinguish «История пока пуста» and «Ничего не найдено». Buttons disabled without eligible selection. Export controls «Экспорт CSV…» and «Экспорт для Anki…» export all learning cards, clearly labeled as such. Canceled native save dialog writes nothing.

Review: title «Повторение», word front; «Показать ответ» reveals saved translation and exact context, plain selectable text. Again / Hard / Good / Easy English labels with numeric localized duration on each button, from shared scheduler preview. No grade before reveal; disable immediately while applying. Due empty: «На сегодня всё. Нет карточек для повторения.» plus refresh action. Stale grade reloads current queue with honest status. Persisted due time never silently resets on window reopen.

Popup: existing bounded layout/lifecycle preserved; add «В карточки» beneath content near footer, not replacing confirmed lookup count. Only visible accepted word/phrase with translation can add. Success «Добавлено в карточки»; duplicate «Уже в карточках»; unavailable «Нет перевода для карточки»; database failure fixed «Не удалось сохранить карточку. Попробуйте ещё раз». Copy snapshot synchronously from displayed content; late meaning may update popup but never existing card.

Accessibility: labels/accessibility names for search/table/reveal/status; sensible native tab order, visible focus, Enter/Space actions, no color-only states. Word/translation/context plain text handles literal markup. Native resizing/scrolling must keep actions usable in narrow work area, representative scaling and light/dark themes. SQLite contention reports fixed retryable status without freezing UI. Agent inspects actual native Words and revealed Review screenshots; offscreen tests verify behavior separately.
