# LookUp Linux

## What This Is

Аналог macOS-приложения LookUp для Linux (Arch + KDE Plasma). Наводишь курсор на слово, жмёшь хоткей, программа через OCR читает слово под курсором (или берёт выделенный текст) и показывает русский перевод в оверлее рядом с курсором. Каждое переведённое слово сохраняется в локальную базу вместе со счётчиком, сколько раз его искали. Делается для друга, который переходит на Linux и не хочет разбираться в Claude.

## Core Value

Хоткей над английским словом даёт перевод в оверлее у курсора примерно за 1–2 секунды, и слово попадает в базу со счётчиком.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Глобальный хоткей запускает поиск (через системные «Комбинации клавиш» KDE, которые вызывают команду)
- [ ] Выделенный мышкой текст, если он есть и новый, переводится без OCR
- [ ] Без выделения берётся скриншот вокруг курсора, OCR (EN), выбирается слово под курсором
- [ ] Перевод EN→RU через бесплатный онлайн-эндпоинт Google (варианты значений, если есть)
- [ ] Оверлей рядом с курсором: слово + перевод, закрывается по клику, Esc или таймауту
- [ ] SQLite-база: слово, перевод, счётчик поисков, первое и последнее время
- [ ] Окно со списком сохранённых слов, сортировка по счётчику
- [ ] Инструкция по установке на Arch (pacman-пакеты + настройка хоткея в KDE)

### Out of Scope

- Wayland GNOME / другие DE — у друга KDE, поддержка остальных не нужна для MVP
- Офлайн-перевод (Argos) — выбран онлайн Google; офлайн можно добавить позже
- Другие языки, кроме EN→RU — друг просил английский
- Карточки, интервальное повторение, экспорт в Anki — не просили; база со счётчиком это задел
- Демон в фоне / трей — одноразовый процесс на хоткей проще; переходить, только если запуск окажется медленным
- AUR-пакет — для MVP хватит скрипта установки

## Context

- Целевая система друга: Arch Linux + KDE Plasma (скорее всего Plasma 6, Wayland-сессия по умолчанию; возможна X11).
- Тестирование: VM с Arch + KDE у Дениса.
- Wayland мешает трём вещам: глобальному хоткею, чтению позиции курсора и позиционированию окна. Предварительные обходы:
  - хоткей: пользовательская комбинация KDE, которая запускает команду (работает и в X11, и в Wayland);
  - курсор: скрипт KWin (`workspace.cursorPos`) через D-Bus или `kdotool`;
  - скриншот: `spectacle` в фоновом режиме;
  - оверлей: Qt через XWayland (`QT_QPA_PLATFORM=xcb`), чтобы окно можно было разместить у курсора;
  - выделение: PRIMARY selection (`wl-paste --primary` или Qt clipboard).
- HiDPI-масштаб и несколько мониторов дают расхождение между логическими координатами курсора и пикселями скриншота.
- Режим работы: ponytail (минимальное полное решение, без лишних абстракций).

## Constraints

- **Платформа**: Arch + KDE Plasma, X11 и Wayland — так у друга
- **Стек**: Python 3 + PySide6/PyQt6 + tesseract из pacman, без pip-зависимостей там, где хватает stdlib — проще ставить на Arch
- **Перевод**: неофициальный Google-эндпоинт без ключа — бесплатно, но может сломаться; изолировать в одной функции
- **Задержка**: хоткей → оверлей ≤ ~2 с
- **Приватность**: в сеть уходит только распознанное слово, скриншоты не сохраняются

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Только KDE Plasma (X11 + Wayland) | Система друга | — Pending |
| Хоткей через KDE Shortcuts → команда | Не нужен свой слушатель клавиатуры, работает на Wayland | — Pending |
| Онлайн Google translate (gtx) | Без ключа, есть варианты значений | — Pending |
| OCR + режим выделения | Выделение точнее и быстрее, OCR для остального | — Pending |
| GUI-окно со списком слов | Выбор пользователя | — Pending |
| Отдельный git-репозиторий в LookUpLinux | Не смешивать с LutQuizApp | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-10-23 after initialization*
