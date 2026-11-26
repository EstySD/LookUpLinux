# SteamOS: Desktop Mode и экспериментальный Gaming Mode

Это docs для SteamOS 3.x (Steam Deck). **Физической Steam Deck в окружении
разработки нет.** Desktop Mode проверен в VM Arch Linux; Gaming Mode проверен
только блоками/в VM и явно помечен как hardware-unverified. Не считайте
поведение ниже подтверждённым на железе до отдельной приёмки на Deck.

## Что поддерживается

| Режим | Статус | Что работает |
|-------|--------|--------------|
| Desktop Mode | Поддерживается | Хоткей, OCR/выделение, карточка, история, словари, карточки; полный UX как в KDE Plasma 6 |
| Gaming Mode | Эксперимент | Захват кадра gamescope, полноэкранный выбор слова, карточка, возврат в игру; без трея и KDE |

Gaming Mode — **не оверлей**. Gamescope не позволяет стороннему приложению
рисовать поверх игры, поэтому LookUp показывает отдельное полноэкранное окно с
замороженным кадром и закрывает его после выбора.

## Установка без root

Используйте переносимую установку: все файлы приложения живут в
`~/.local/lib/lookup`, пользовательские данные — в обычных XDG-каталогах
(`~/.local/share/lookup`, `~/.config/lookup`). uninstall не удаляет слова,
карточки, настройки и словари.

```bash
# из распакованного бандла или исходного checkout
python3 tools/install_steamos.py install --bundle ./lookup-steamos-bundle.tar.gz
# при работе из исходников:
python3 tools/install_steamos.py install --source .
python3 tools/install_steamos.py status
```

Запуск из меню приложений или `~/.local/bin/lookup --app`. Автозапуск Desktop
Mode создаётся как KDE-запись; Gaming Mode использует systemd user unit
`lookup-gaming.service`, который установщик пытается включить командой
`systemctl --user enable --now`. Если это не удалось, сделайте это вручную.

Бандл может содержать `runtime/` с PyQt6, данными Tesseract eng, kdotool и
wl-clipboard. Обёртка добавляет `runtime/bin`, `runtime/lib` и
`runtime/share/tessdata` в `PATH`, `LD_LIBRARY_PATH` и `TESSDATA_PREFIX`; без
бандла используется системный `python3` и системные пакеты.

## Desktop Mode

- Хоткей по умолчанию: **Meta+Shift+D**. Наведите курсор на английское слово или
  выделите текст и нажмите его.
- На SteamOS 3.9 (Plasma 6.7.3) нативный KWin-плагин захвата недоступен:
  требуется KWin ≥ 6.8. Используется fallback `ScreenShot2` — снимок после
  нажатия. В `lookup --doctor` это честно видно как «плагин не активен,
  используется fallback».
- На SteamOS 3.10+ (Plasma 6.8.2) можно собрать KWin-плагин под KWin прошивки;
  он опционален.
- Сгенерированный `.desktop` для триггера содержит
  `X-KDE-DBUS-Restricted-Interfaces=org.kde.KWin.ScreenShot2`. Без этой строки
  fallback-захват будет запрещён политикой KWin.

## Gaming Mode (эксперимент)

1. Включите игру и режим игры.
2. Нажмите настроенный триггер: хорд задних кнопок через evdev (по умолчанию)
   или клавишу, назначенную в Steam Input.
3. Появится полноэкранное окно с замороженным кадром. Выберите слово:
   - тап/щелчок по слову;
   - стрелки 또는 DPad перемещают видимый прицел, **Enter** выбирает;
   - **F1** показывает панель с кнопкой закрытия, **Esc** закрывает.
4. Прочитайте карточку и закройте окно, чтобы вернуться в игру.

В настройках (`~/.local/bin/lookup --app` → «Настройки») выберите тип триггера:
`Хорд задних кнопок (evdev)` или `Клавиша Steam Input`. В Gaming Mode
KDE-хоткей скрыт. Для Steam Input назначьте в раскладке конкретной игры клавишу,
которая запускает `~/.local/bin/lookup --trigger`; глобальной раскладки для
Gaming Mode нет.

Снимок не сохраняется на диск: gamescope получает SIGUSR2, новый
`gamescope_*.png` читается и сразу удаляется. Если SIGUSR2 не работает, пробуется
ограниченный по времени PipeWire/GStreamer fallback. Настоящего оверлея нет.

## Диагностика

```bash
~/.local/bin/lookup --doctor
python3 tools/check_steamos.py
```

`lookup --doctor` сообщает сессию, версии SteamOS/Plasma/KWin/gamescope,
доступность захвата и триггера. `tools/check_steamos.py` печатает обезличенный
JSON (только метаданные сессии, PID'ы, флаги DISPLAY и INPUT); он не читает
историю, запросы, скриншоты и буфер обмена. В Gaming Mode capture/trigger
могут честно сообщать о недоступности — это не ошибка установки, а отсутствие
проверенного окружения.

## Обновление и удаление

```bash
python3 tools/install_steamos.py install --bundle ./new-bundle.tar.gz
python3 tools/install_steamos.py uninstall
```

Uninstall удаляет только помеченные как-owned файлы: код, обёртку, desktop entries,
systemd unit. `~/.local/share/lookup` и `~/.config/lookup` не трогаются.

## Ограничения приёмки

- Нет физической Steam Deck: SIGUSR2-захват, возврат фокуса в игру, evdev-коды
  back-кнопок и Steam Input не проверены на железе.
- SteamOS 3.9 стабильна на Plasma 6.7.3; KWin-плагин возможен только на 3.10+.
- Ubuntu 24.04 / GNOME 46 — отдельный desktop preview ([docs/UBUNTU.md](UBUNTU.md)),
  не Gaming Mode.
- X11, другие DE, новые языки, аудио и перевод всего экрана не поддерживаются.
