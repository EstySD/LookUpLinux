# Ubuntu 24.04 / GNOME Wayland

Ubuntu работает из исходников с отдельным расширением GNOME Shell 46. Arch Linux /
KDE Plasma 6 продолжает использовать KWin, ScreenShot2 и KGlobalAccel. Расширение
GNOME для KDE не требуется и в Arch-пакет не включается.

## Установка

В терминале обычного пользователя внутри графического сеанса Ubuntu:

```bash
sudo apt update
sudo apt install python3-pyqt6 qt6-wayland tesseract-ocr tesseract-ocr-eng wl-clipboard
cd /path/to/LookUpLinux
python3 tools/install_ubuntu.py
```

При первой установке выйдите из графического сеанса и войдите снова, затем:

```bash
gnome-extensions enable lookup-linux@lookup.local
python3 -m lookup --app
```

Пользовательские ярлыки ссылаются на каталог исходников: после его переноса повторите
установку. Для обновления расширения повторите установку и заново войдите в GNOME.

Добавьте свой словарь через настройки; форматы описаны в
[DICTIONARIES.md](DICTIONARIES.md). Проверка:

```bash
python3 -m lookup --list-dicts
python3 -m lookup --doctor
```

Наведите курсор на английское слово и нажмите **Meta+Shift+D**. Свежее PRIMARY-выделение
имеет приоритет перед OCR. Хоткей меняется в настройках приложения; расширение
сохраняет его между сеансами и отказывает при конфликте с занятой комбинацией.

## Доступ к рабочему столу

Расширение сообщает координаты курсора и мониторов, захватывает монитор и размещает
попап. Захват, размещение и смена хоткея доступны через сеансовую D-Bus шину только
текущему владельцу имени приложения `org.lookup.Linux`. Захват недоступен при
блокировке экрана. Снимки передаются в памяти; расширение не записывает их на диск
и не отправляет по сети.

Используются [формат расширений GNOME 45+](https://gjs.guide/extensions/overview/anatomy.html)
и [Shell.Screenshot GNOME 46](https://github.com/GNOME/gnome-shell/blob/gnome-46/src/shell-screenshot.h).

## Повторение проверки

Версии, результаты агентской проверки и ограничения записаны в
[ubuntu-vm-validation.md](ubuntu-vm-validation.md). Это не пользовательская приёмка.

```bash
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_gnome tests.test_platform tests.test_lifecycle tests.test_doctor tests.test_app tests.test_app_gui tests.test_settings_gui tests.test_learning_gui -q
LOOKUP_DICTS=/path/to/dictionaries python3 tools/check_ubuntu_app.py
```

Закройте обычный LookUp перед вторым вызовом. Проверка создаёт временный профиль и
окно со словом `dictionary`. После `READY_OCR` наведите курсор на слово и нажмите
хоткей; после `READY_PRIMARY` нажмите его повторно. Путь к JSON-отчёту выводится в
терминале. Используются настоящий захват, OCR, словарь, попап и SQLite; сетевой
перевод в тестовом профиле выключен.

Проверен GNOME 46 на Ubuntu 24.04. Другие версии GNOME, Ubuntu X11, игры,
полноэкранные приложения и несколько мониторов требуют отдельного прогона.
Системные модели Tesseract в Arch и Ubuntu различаются, поэтому точные результаты
старых OCR-фикстур могут отличаться.

Для удаления расширения:

```bash
gnome-extensions disable lookup-linux@lookup.local
gnome-extensions uninstall lookup-linux@lookup.local
```

Ярлыки созданы в `~/.local/share/applications/org.lookup.Linux.desktop` и
`~/.config/autostart/org.lookup.Linux.desktop`. Историю и словари удаление расширения
не затрагивает.
