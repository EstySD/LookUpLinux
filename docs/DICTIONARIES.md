# Dictionaries / Словари

Supported formats: **StarDict**, **Lingvo DSL** (`.dsl`, `.dsl.dz`) and **MDX**.
Public packages ship without dictionary databases. Dictionary licenses are
independent of the application's GPL license. Check each download's terms.
Not every format variant or real-world dictionary has been tested.

## Download sources

| Source | What you can find | Notes |
| --- | --- | --- |
| [QStarDict catalog](https://qstardict.ylsoftware.com/dictionaries.php) | English–Russian Mueller 7, StarDict | Labeled GPL by the catalog; the pinned archive lacks license text and exact GPL version. Not bundled by LookUp. |
| [Mueller 7 archive](https://qstardict.ylsoftware.com/files/mueller7.tar.bz2) | Direct download from QStarDict | External database, not a LookUp release asset. Review the catalog and attribution above. |
| [FreeDict downloads](https://freedict.org/downloads/) | StarDict dictionaries for available language pairs | Choose a compatible download and check its language direction. LookUp's translation UI remains EN→RU. |

See [third-party notices](../packaging/THIRD-PARTY.md) for the pinned Mueller
archive's SHA-256 and licensing uncertainty. Links do not grant redistribution rights.

## Install a dictionary

1. Download and extract the archive. Do not copy the outer `.zip` or `.tar.bz2` as-is.
2. Open the tray menu → **Settings → Open dictionary folder**
   (**Настройки → Открыть папку словарей**).
3. Copy the dictionary files there. Subfolders are supported.
4. Choose **Apply settings** (**Применить настройки**), enable the dictionary
   and set its order if needed. No restart is required.
5. Check with `lookup --list-dicts` and `lookup --word run --offline --no-save`.

Keep StarDict's `.ifo`, index (`.idx` or `.idx.gz`) and data (`.dict` or
`.dict.dz`) together with matching base names. DSL can be plain or
dictzip-compressed. MDX support is for text entries; audio and resource packs
are not promised.

Default folder: `~/.local/share/lookup/dicts`. If `LOOKUP_DICTS` is set, the
settings button opens its first configured directory instead.

## По-русски

Скачайте словарь по ссылкам выше и распакуйте архив. В каталоге QStarDict есть
англо-русский Mueller 7. Приложение его не распространяет из-за неопределённости
лицензии конкретного архива; ссылка не меняет условий использования данных.

В трее откройте **Настройки → Открыть папку словарей**, скопируйте файлы,
нажмите **Применить настройки** и включите словарь. Для StarDict нужны вместе
`.ifo`, индекс и данные с одинаковым именем. Подкаталоги допустимы.
Проверка: `lookup --list-dicts`, затем `lookup --word run --offline --no-save`.
Без словаря офлайн-статей нет; онлайн-перевод требует сети и включённой настройки.
