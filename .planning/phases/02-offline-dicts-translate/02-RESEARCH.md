# Phase 2: Офлайн-словари и перевод - Research

**Researched:** 2026-10-24
**Domain:** Offline dictionary formats (StarDict, Lingvo DSL, MDX/MDict) on stdlib only, LZO1X decompression, dictzip random access, online translation fallback, SQLite cache and schema migration v2
**Confidence:** MEDIUM overall. HIGH for StarDict, dictzip and LZO1X (checked against the real Mueller 7 file and against liblzo2 output). MEDIUM for MDX (no real MDX file was available; the format is taken from the reference reader and the format document). LOW for how long the online endpoints keep working.

<user_constraints>
## User Constraints (from CONTEXT.md)

**Source:** `.planning/phases/02-offline-dicts-translate/02-CONTEXT.md` (Mode `--auto`, gathered 2026-10-24). Copied verbatim.

### Locked Decisions

### Папки словарей и порядок (TRAN-01)
- **D-01:** Словари ищутся в двух каталогах: пользовательский `$XDG_DATA_HOME/lookup/dicts/` (по умолчанию `~/.local/share/lookup/dicts/`) и системный `/usr/share/lookup/dicts/` (туда PKGBUILD в Phase 7 положит Mueller 7). Переопределение `LOOKUP_DICTS` (список путей через `:`) — для тестов. Обход рекурсивный: словарь может лежать в своей подпапке.
- **D-02:** Формат определяется по файлам, без правки кода: StarDict — `.ifo` (+ `.idx`/`.idx.gz`, `.dict`/`.dict.dz`, опционально `.syn`); DSL — `.dsl` или `.dsl.dz` (UTF-16LE/UTF-8 с BOM, `#NAME`, `#INDEX_LANGUAGE`, `#CONTENTS_LANGUAGE`); MDX — `.mdx` (`.mdd` с ресурсами игнорируется). Сломанный или неподдерживаемый словарь пропускается с понятной причиной в `--list-dicts`, остальные работают.
- **D-03:** Порядок и включение хранятся в `$XDG_CONFIG_HOME/lookup/config.json`, ключ `dictionaries`: список `{"id": <относительный путь от корня каталога словарей>, "enabled": bool}`. Phase 7 только даёт окно для этого ключа. Словари, которых нет в списке, идут после перечисленных, по алфавиту названия; пользовательский каталог раньше системного. Нет файла — всё включено, порядок по алфавиту.
- **D-04:** `lookup --word X` показывает статьи из **всех** включённых словарей, где слово нашлось, в этом порядке (как GoldenDict/Lookupper), а не только из первого.

### Модель статьи (TRAN-01: транскрипция, части речи, значения по отдельности)
- **D-05:** Каждый парсер возвращает общий `Article`: `dict_name`, `headword`, `transcription | None`, `senses: list[(pos | None, [значения])]` (best effort), `text` — вся статья простым текстом (всегда есть, фолбэк для UI), `lemma_of | None` (если статья найдена через базовую форму). Поля, которых в словаре нет, — `None`/пусто, не выдумываются.
- **D-06:** Разметка в простой текст: DSL — теги `[trn] [p] [m1..] [ex] [c] [i] [b] [com] [ref] [t]` (транскрипция из `[t]`, часть речи из `[p]`), MDX — HTML → текст через stdlib `html.parser` (без lxml/bs4), StarDict — типы `m`/`t`/`x`/`h`/`g`; Mueller 7 (`m`) разбирается по его соглашениям (`[транскрипция]`, `_n.`/`_v.`/`_a.`, нумерация `1)` `2.`). Нераспознанная структура — только `text`, без падения. В UI позже всё рисуется как plain text (PITFALLS: markup injection).

### MDX и LZO (research flag ROADMAP)
- **D-07:** MDX читается на чистом stdlib: zlib-блоки — `zlib`, без сжатия — как есть, LZO-блоки — собственная функция распаковки LZO1X (~100 строк, только decompress, покрывается тестами). Пакет `python-lzo` не тянем — это противоречит «без pip, где хватает stdlib» и усложняет PKGBUILD. Ключевой индекс с `Encrypted=2` расшифровывается (ripemd128 + простая XOR-схема, тоже на stdlib); словари с регистрационным шифрованием (`Encrypted=1`) не поддерживаются и помечаются в `--list-dicts`. Исследователь проверяет формат v1.2 и v2.0 и, если LZO1X окажется недостаточным, сообщает об этом до плана.

### Скорость индексов
- **D-08:** Индекс строится один раз на словарь и держится в памяти процесса (в Phase 5 это демон, поэтому важна стоимость открытия, а не поиска). StarDict `.idx` уже индекс; `.dict.dz` читается с произвольным доступом по таблице чанков dictzip, без распаковки всего файла. DSL и MDX: индекс «заголовок → смещение» кэшируется на диске в `$XDG_CACHE_HOME/lookup/index/` с ключом путь+размер+mtime; несовпадение — пересборка. Поиск без учёта регистра (casefold), заголовки DSL с `{}`-скрытыми частями и вариантами разворачиваются.
- **D-09:** Цель для CLI на Mueller 7: открытие всех словарей с тёплым кэшем ≤ 300 мс, поиск слова ≤ 20 мс; `LOOKUP_TIMING=1` печатает время стадий (открытие словарей, поиск, сеть, БД). Холодная сборка индекса может быть дольше, один раз.

### Базовая форма (TRAN-04)
- **D-10:** Порядок поиска: точная форма → встроенный список неправильных форм (≈200 глаголов: `ran→run`, `went→go`, …; неправильные множественные: `men→man`, `children→child`, `mice→mouse`, …) → правила окончаний. Кандидат принимается, только если он **есть в каком-нибудь словаре**; первый найденный выигрывает. Если точная форма есть в словаре (`news`, `better`, `ceiling`), правила не применяются.
- **D-11:** Правила окончаний: `-s`, `-es`, `-ies→y`, `-ed`, `-d`, `-ied→y`, `-ing`, `-ing→+e`, удвоенная согласная (`running→run`, `stopped→stop`), `-er/-est` и `-ier/-iest→y` для прилагательных. Список неправильных форм — файл данных внутри пакета (`lookup/data/irregular.txt`), а не код.
- **D-12:** Ключ в `words` остаётся поверхностной формой (D-06 Phase 1: `running` и `run` — разные записи); найденная базовая форма пишется в `words.lemma`. Группировка по `lemma` — решение Phase 6. Онлайн-фолбэк тоже может подсказать базовую форму (ответ gtx `dt=bd` для `ran` даёт статью `run`) — она пишется в `lemma`, только если в словарях базовой формы не нашлось.

### Онлайн-перевод (TRAN-02, TRAN-05)
- **D-13:** Основной провайдер — Google `translate_a/single` через `urllib`, `sl=en&tl=ru`, `dt=t&dt=bd&dt=rm` (перевод, варианты по частям речи, транскрипция). `client=` — упорядоченный список в конфиге (по умолчанию `gtx`, `dict-chrome-ex`, `at`); последний сработавший клиент запоминается в БД (таблица `meta`) и пробуется первым.
- **D-14:** 429, 403, HTML вместо JSON, пустой или неожиданный JSON → причина `blocked`/`bad_response`, сразу переход к следующему клиенту, без повторов того же. Разбор ответа — по безопасным индексам, с фикстурами реальных ответов в тестах (слово с блоком словаря, слово без него, фраза, предложение, мусор). «Перевод == входу» и пустой `d[1]` для слова = «не найдено».
- **D-15:** Запасной провайдер — второй независимый сервис за той же функцией-интерфейсом `translate(text) -> Result | raise TranslateError(reason)`; кандидат по умолчанию — MyMemory (без ключа). Исследователь проверяет текущие бесплатные варианты без ключа (MyMemory, Lingva-инстансы и др.) и выбирает один; окончательное «нужен ли второй провайдер» решается по проверке доступности из сети VM (SC4). Провайдеры — это просто упорядоченный список функций, без классов и плагинов (ponytail).
- **D-16:** Бюджет — общий дедлайн ≈3 с на весь онлайн-путь (все клиенты и провайдеры вместе), а не 3 с на попытку; таймаут каждой попытки = остаток дедлайна (минимум ~0,5 с). Причины ошибок — фиксированный набор: `no_network`, `timeout`, `blocked`, `bad_response`, `not_found`; CLI и потом попап показывают их по-русски («нет сети», «онлайн-перевод заблокирован», …).
- **D-17:** Онлайн идёт, только если слова нет ни в одном словаре (включая базовую форму), для фраз, которых нет в словарях (сначала ищем фразу в словарях — `break out` в Mueller есть), и для предложений. Флаг `--offline` и настройка `online: false` в конфиге выключают сеть полностью (нужно для SET-01 в Phase 7 и для приватности).
- **D-18:** Перевод предложения (TRAN-05) запрашивается параллельно с поиском слова (поток), чтобы не складывать задержки; ошибка или отключённый онлайн дают ответ без перевода предложения и без падения. В сеть уходят только слово/фраза/предложение (ограничение приватности PROJECT.md).

### Кэш (TRAN-03)
- **D-19:** Миграция схемы v2 (через механизм `MIGRATIONS` Phase 1): таблица `translations(text TEXT, kind TEXT CHECK(kind IN ('word','phrase','sentence')), provider TEXT, payload TEXT /*JSON*/, fetched_at INTEGER, PRIMARY KEY(text, kind))` и таблица `meta(key TEXT PRIMARY KEY, value TEXT)`. Кэшируются только **успешные** онлайн-ответы; ошибки не кэшируются. Статьи словарей не кэшируются (они офлайн и быстрые).
- **D-20:** Слова и фразы в кэше бессрочно; предложения — с ограничением на последние 1000 записей (обрезка при вставке). Ключ — нормализованный текст (для слова/фразы — `normalize()`, для предложения — схлопнутые пробелы). Повторный поиск переведённого слова отвечает из кэша, не трогая сеть (проверяется тестом с запрещённой сетью).

### Классификация ввода и запись в базу (DATA-03)
- **D-21:** Число слов после нормализации: 1 → слово, 2–4 → фраза, больше 4 → предложение. Слово и фраза сохраняются одной записью через `upsert_word` (ключ — нормализованная фраза, D-05 Phase 1); предложение только показывается и в `words` не пишется.
- **D-22:** Что пишется в `words.translation`: короткая строка — первые 2–3 значения первой статьи по порядку словарей (или основной онлайн-перевод плюс 2–3 варианта). Полная статья в `words` не копируется.
- **D-23:** Когда запись делается: слово/фраза нашлись в словаре или переведены онлайн → `upsert_word` со счётчиком. Сеть недоступна и в словарях нет → запись **со счётчиком и `translation=NULL`** (слово не отвергнуто, перевод добирается при следующем удачном поиске через `COALESCE`, D-10 Phase 1). Онлайн ответил «не найдено» (эхо) или `normalize()` вернул `None` → в базу ничего не пишется.
- **D-24:** Контекст для `upsert_word` в CLI — опция `--context "предложение"` (в Phase 3/5 это распознанная строка); она же — предложение для TRAN-05.

### CLI
- **D-25:** Точка входа `python -m lookup` (`lookup/__main__.py`, argparse). Команды: `--word TEXT` (слово или фраза), `--text TEXT` (автоклассификация по D-21), `--context TEXT`, `--offline`, `--no-save`, `--list-dicts` (найденные словари, формат, порядок, число статей, причина пропуска). Вывод — читаемый текст по словарям; `LOOKUP_TIMING=1` в stderr. Скрипт `lookup` в PATH появится с PKGBUILD (Phase 7). Код возврата: 0 — что-то показано, 1 — не найдено нигде, 2 — ошибка использования.

### Приватность и логи
- **D-26:** Правило V7 из Phase 1 продолжается: модули словарей, перевода и кэша сами ничего не печатают и не логируют текст запросов; печатает только CLI. Сообщения исключений несут причину и тип, без текста слова/предложения.

### Структура кода
- **D-27:** Плоские модули в пакете `lookup/` (ponytail, без подпакетов-провайдеров): `stardict.py`, `dsl.py`, `mdx.py` (+ `lzo.py`), `dicts.py` (поиск каталогов, порядок, `Article`, поиск во всех словарях, базовая форма), `online.py` (Google + запасной провайдер, `TranslateError`), `translate.py` (оркестратор: словари → кэш → онлайн → запись), `config.py` (чтение `config.json`), `__main__.py`. Ядро — только stdlib; Qt по-прежнему не импортируется (тест чистоты ядра из Phase 1 расширяется на новые модули).

### Claude's Discretion
- Точные имена функций и полей, формат `--list-dicts`, структура тестов и фикстур.
- Как получить фикстуры словарей: маленькие синтетические StarDict/DSL/MDX, сгенерированные тестовым кодом или закоммиченные (MDX — можно мини-писателем в тестах с zlib- и LZO-блоками).
- Конкретный набор правил окончаний сверх D-11 и состав списка неправильных форм.
- Где взять Mueller 7 для ручной проверки в VM до Phase 7 (скрипт или шаг в UAT).

### Deferred Ideas (OUT OF SCOPE)
- Окно управления словарями (вкл/выкл, порядок) — Phase 7 (SET-01); здесь только формат `config.json`.
- Группировка слов по `lemma` в списке — Phase 6.
- Ресурсы `.mdd` (картинки, звук) и аудио-произношение — v2 (DICT-02).
- Формат Yomitan — v2 (DICT-03).
- Официальный Cloud Translation API с ключом пользователя — только если оба бесплатных провайдера окажутся недоступны; решение после проверки из VM.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TRAN-01 | Слово ищется в офлайн-словарях StarDict, Lingvo DSL, MDX из папки словарей; статьи нескольких словарей по порядку; транскрипция, части речи, значения доступны по отдельности, если есть в словаре | StarDict layout and `sametypesequence` (Format Reference 1), dictzip access (Format Reference 2), MDX reader outline (Format Reference 3), LZO1X decoder verified (Code Examples 1), DSL rules (Format Reference 4), Mueller 7 conventions and counts (Format Reference 5) |
| TRAN-02 | Нет слова в словарях или фраза: онлайн; ошибка видна, ожидание около 3 с; второй провайдер решён по проверке из VM | Online endpoint probes from VM (Format Reference 6), deadline design (Pattern 4), MyMemory as second provider (Standard Stack) |
| TRAN-03 | Повторный поиск переведённого слова берётся из кэша без сети | Cache schema v2 and migration coexistence (Pattern 5, Pitfall 11), test with network forbidden (Validation Architecture) |
| TRAN-04 | `running`, `ran`, `books` находят `run` и `book` по окончаниям и неправильным формам | Lookup order and pointer articles (Findings 1, Pattern 3), irregular data from WordNet exception lists (Standard Stack), presence table for test forms (Format Reference 5) |
| TRAN-05 | Исходное предложение переводится онлайн; без сети попап работает без перевода предложения | Parallel sentence translation pattern (Pattern 4), error and no-network path (Pitfall 9) |
| DATA-03 | Фраза из 2–4 слов сохраняется одной записью; длинный текст только показывается | Input classification (D-21) and `upsert_word` integration (Pattern 6); `lemma` parameter needed (Integration Points in CONTEXT) |
</phase_requirements>

## Summary

Phase 2 can be built on the Python 3.12/3.14 standard library alone. Each of the three dictionary formats needs a small reader: StarDict is a flat index plus a dictzip file; DSL is line-based text; MDX is a binary container with zlib or LZO blocks and an optional key-index obfuscation. The one piece with no stdlib support is LZO1X decompression, and RIPEMD-128 (needed only for `Encrypted=2` MDX key info), which `hashlib` does not provide on either Python version. Both can be written in pure Python. The LZO1X decoder in this document was checked against 20 streams produced by the real `liblzo2` 2.10 library and passes all of them at about 10 MB/s of output. The research therefore confirms D-07: no `python-lzo` is needed.

The research changed four things the CONTEXT assumed, and the planner must handle them explicitly. First, exact-form-first lookup returns useless pointer articles for many inflected forms: Mueller 7 has headwords such as `ran`, `went` and `men` whose whole article is only a `от X` pointer, and `running` whose article starts with one. Second, `break out` is not a Mueller headword; it is a sub-entry inside the `break` article. Third, the AUR package `mueller-dict` is dictd format and cannot be used as the StarDict default; the StarDict build comes from QStarDict (or SUSE and ALT packages). Fourth, the Google `gtx` client result depends on the HTTP client: from the VM, `curl` gets HTTP 429 while Python `urllib` gets 200 JSON on the same network. SC4 must therefore be checked through the same `urllib` code path the app uses.

**Primary recommendation:** Implement the flat modules from D-27 on stdlib. Add a pointer-follow rule (`от X` article → X) before the irregular list. Accept that `break out` is found only online unless the planner adds an in-article phrase index. Validate every offset and size in every reader, because the real Mueller 7 index contains one invalid entry. Use `at`/`dict-chrome-ex`/`gtx` through `urllib` as the online chain, with MyMemory as the second provider limited to sentences and phrases (see Open Question 3).

## Findings That Change the Plan (read first)

1. **Pointer articles defeat exact-first (D-10).** In Mueller 7, 601 short articles have the form `[transcription] _p. от run 2`, `_pl. от man`, `_comp. от bad`, `_p-p. от go`, and 576 of their targets are themselves headwords. Examples: `ran` = `_p. от run 2`, `went` = `_p. от go 1`, `gone` = `_p-p. от go 1`, `men` = `_pl. от man 1`, `teeth` = `_pl. от tooth 1`, `worse` = `_comp. от bad 1`. Several are present as headwords, so D-10 ("exact form found, rules not applied") would show a one-line pointer to the user for `ran`, which contradicts TRAN-04. Resolution: when the exact-form article is a pointer, follow the target (`lemma_of = target`, show the target article, keep the pointer line as a header). `running` has its own noun sense as well as `от run`, so it is shown in full with the lemma noted.
2. **`break out` is not a headword.** `break out` appears only inside the `break` article (about 7.4 KB) as a numbered sub-entry (`break out а> выламывать; б> убежать ...`). D-17's justification ("break out в Mueller есть") holds only for in-article text. Phase 3's CAPT-04 example relies on this phrase. Options are listed under Open Questions 1.
3. **The Mueller 7 StarDict archive must be fetched from QStarDict or a distro package.** `mueller-dict` on AUR is a dictd package. The StarDict build is `mueller7.tar.bz2` (4 771 569 bytes) at `qstardict.ylsoftware.com/files/mueller7.tar.bz2`, licensed GPL (the SUSE package states GPL-2.0+ and 46 231 articles). The archive contains `mueller7.ifo`, `mueller7.idx.gz`, `mueller7.dict.dz`, a plain `mueller7.dict` and a stray `.mueller7.dict.swp`. The reader must ignore the `.swp` file and prefer one data file.
4. **The Mueller 7 index is not clean.** `wordcount=46231` in the `.ifo`, but the index parses to 46 232 entries. The first entry is an empty headword with offset 11835175 and size 1667331443 (out of range of the 8 099 010-byte data file). Every other entry is valid. A reader that trusts `wordcount` or rejects the whole dictionary on the first bad entry fails this real file. Skip invalid entries and count them.
5. **Google `gtx` blocking depends on the client, not only on the IP.** Verified 2026-10-24: VM `curl` to `client=gtx` returns HTTP 429 HTML for every query, including `run` and `xyzzyq`; VM `curl` to `dict-chrome-ex` and `at` returns 200 JSON; VM Python `urllib` returns 200 JSON for all three clients; the Windows host `curl` returns 200 JSON for `gtx`. Rotation is still needed, but acceptance testing must use `urllib`.
6. **`dict-chrome-ex` and `at` returned identical payloads** for `run` (byte-identical, 8782 bytes), so rotating between them adds less independence than D-13 assumes.
7. **Non-words get a transliteration, not an echo.** `xyzzyq` returns `d[0] = [["ксиззик", "xyzzyq", ...]]` and `d[1] = null`. The D-14 rule "перевод == входу" does not fire; a word must be classified "не найдено" when `d[1]` is absent. Sentences legitimately have `d[1] = null`, so this rule applies to word-kind inputs only.
8. **The migration tests hard-code version 1** (`test_store.py`: `CURRENT_VERSION == 1` and `tables == ["words"]`; `test_migrations.py`: `_make_v1` and `M2`/`M3` built on `MIGRATIONS`; `_workers.py` `migrate_child`). Adding `_v2` silently changes what "v1" means in these tests. See Pitfall 11.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Parsing StarDict / DSL / MDX files | Core library (stdlib, offline) | Filesystem | Pure local file parsing; no network, no Qt |
| Discovery, order, enabled flags | Core library (`dicts.py`, `config.py`) | Filesystem (`config.json`) | D-01..D-03 |
| Base-form search (lemma) | Core library (`dicts.py`) | Dictionary data (`irregular.txt`, pointer articles) | Needs dictionary contents to validate candidates (D-10) |
| Online translation (Google, fallback) | External HTTPS API | Core client (`online.py`) | Undocumented endpoints; isolated in one module |
| Translation and word-count cache | Database (SQLite `translations`, `meta`) | Core (`translate.py`) | D-19, D-20 |
| Word save with counter | Database (`upsert_word`) | `translate.py` decides when | Phase 1 contract |
| Deadline across network stages | Core (`online.py`, `translate.py`) | — | D-16 single budget |
| Index cache (DSL, MDX) | Filesystem (`$XDG_CACHE_HOME/lookup/index/`) | Core | D-08 |
| Presentation (text output) | CLI (`__main__.py`) in Phase 2; Qt popup in Phase 5 | — | Core returns data, never prints (V7) |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `zlib` | ZLIB 1.3.2 (VM) | MDX zlib blocks; dictzip raw deflate (`wbits=-15`) | Ships with Python; decompressobj supports `max_length` for bounded output |
| Python stdlib `gzip` | 3.14 | `.idx.gz`, `.ifo`-adjacent gzip, and the gzip header of `.dict.dz` | Stdlib, handles FEXTRA headers when read with raw parsing |
| Python stdlib `struct` | 3.14 | Big-endian/little-endian fields in idx, MDX, dictzip | Stdlib |
| Python stdlib `codecs` | 3.14 | MDX encodings: `utf-8`, `utf-16`, `gb18030`, `big5`; DSL `utf-16`/`utf-8-sig` | Covers all encodings MDX `Encoding` uses without an extra package |
| Python stdlib `html.parser` | 3.14 | MDX/XDXF/HTML article text (D-06) | Stdlib; no lxml/bs4 (CONTEXT) |
| Python stdlib `urllib.request` | 3.14 | Google and MyMemory HTTPS calls (D-13, D-15) | Stdlib; used identically in tests and VM |
| Python stdlib `json` | 3.14 | Config, online responses, index cache (see Pitfall 13) | Stdlib; safe for untrusted data |
| Python stdlib `sqlite3` | bundled; Phase 1 requires SQLite >= 3.35 | `translations`, `meta` tables | Phase 1 store |
| Python stdlib `concurrent.futures` or `threading` | 3.14 | Parallel sentence translation (D-18) | Stdlib |
| Python stdlib `unittest` | 3.14 | Test runner (`python -m unittest`) | Project convention |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `liblzo2` | 2.10-5 (VM `core/lzo`, already installed) | Test oracle only: generate LZO1X vectors | Only in the VM when regenerating `tests/fixtures/lzo/`; never a runtime dependency |
| WordNet 3.1 exception lists (`verb.exc`, `noun.exc`, `adj.exc`) | WordNet 3.1 (Princeton) | Source for `lookup/data/irregular.txt` (D-11) | Generate the data file once with a script; commit the output with the Princeton licence notice |
| Mueller 7 EN-RU StarDict | 2007 edition, 46 231 articles, GPL | Default dictionary for manual checks and the sample-dictionary test (skipped unless configured) | Do not commit the 4.7 MB archive; fetch in UAT |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Own LZO1X decoder (D-07) | `python-lzo` (pacman `python-lzo` 1.16-1 in extra) | Native and faster, but adds a pacman dependency and breaks "stdlib only" in the PKGBUILD. Decoder here is ~10 MB/s, so no speed reason to switch |
| Own RIPEMD-128 | `hashlib.new("ripemd128")` | Unavailable: `ValueError: unsupported hash type ripemd128` on local 3.14.3, 3.12.0 and VM 3.14.8 (OpenSSL 3.6.5). No alternative in stdlib |
| Google `gtx` alone | Official Cloud Translation API with key | Stable but needs a user key and billing; only if both free providers fail (CONTEXT Deferred) |
| MyMemory (second provider) | Lingva instances | Probed: `lingva.ml` echoes the input for every pair (`run` → `run`, `break out` → `break out`); `lingva.thedaviddelta.com` returns 503 DEPLOYMENT_PAUSED; `lingva.lunar.icu` times out; `lingva.garudalinux.org` returns a Cloudflare challenge; `lingva.nikaroo.com` has a TLS name mismatch. Rejected |
| MyMemory (second provider) | LibreTranslate public instances | `libretranslate.com` returns 403 (Cloudflare) from the VM. Rejected |
| MyMemory (second provider) | `translate-pa.googleapis.com` | Returns 403 "Method doesn't allow unregistered callers ... Please use API Key". Embedded web keys were not used (not this project's credential). Rejected |
| `pickle`/`marshal` for index cache | JSON or a plain versioned binary layout | Loading pickle/marshal from a user-writable cache can execute code; see Pitfall 13 |

**Version verification:** Versions were checked on this machine and the VM, not from a registry (no packages are installed):
- Local Windows host: `python` 3.14.3 (`C:\Python314`), `py -3.12` 3.12.0.
- VM `archvm` (`ssh archvm`): Arch Linux, Python 3.14.8, OpenSSL 3.6.5, liblzo2 2.10-5, zlib 1.3.2. The VM has no Python 3.12.
- MyMemory, Google and Lingva endpoints: see Format Reference 6.

**Installation:** None. Phase 2 adds no pip or pacman packages.

## Package Legitimacy Audit

No external packages are installed in this phase. The implementation uses only the Python standard library, and the project's stack rule forbids pip dependencies in `lookup/`. The Mueller 7 archive and WordNet exception lists are data files, not packages; they are not installed by the phase. The AUR `mueller-dict` package was inspected and is rejected for the reason in Findings 3.

**Packages removed due to [SLOP] verdict:** none (no packages checked).
**Packages flagged as suspicious [SUS]:** none.

## Architecture Patterns

### System Architecture Diagram

```
 CLI: python -m lookup --word X | --text T  [--context C] [--offline] [--no-save] [--list-dicts]
                 |
                 v
   classify (D-21): 1 word -> word | 2-4 -> phrase | >4 -> sentence       (translate.py)
                 |
                 v
   normalize(key) (lookup/normalize.py)  -- None -> exit 2/1, no DB write (D-23)
                 |
                 v
   +----------------------------------------------+
   | dicts.py: search all enabled dictionaries    |   (warm, in memory)
   |   exact form -> pointer-follow ("от X")     |
   |   -> irregular.txt -> suffix rules          |
   |   each candidate must exist in some dict    |
   +----------------------------------------------+
                 |  articles (0..N), lemma_of
                 |
   sentence? --yes--> start sentence thread (online, D-18) -----------+
                 |                                                    |
   dict hit? --yes--> (online skipped for word; phrase/sentence rules)|
                 |  no                                                |
                 v                                                    |
   translations cache (SQLite, D-19/20) hit? --yes--> result          |
                 |  no                                                |
                 v                                                    |
   online.py: clients gtx, dict-chrome-ex, at (urllib)                 |
              then fallback provider (MyMemory)                        |
              single deadline ~3 s (D-16), errors -> reason           |
                 |  ok -> cache write (only successes)                |
                 v                                                    v
   translate.py: upsert_word(conn, key, translation=short, context, lemma)  (D-22/23)
                 |
                 v
   __main__.py prints articles (plain text) + translation + reason; exit 0/1/2
```

### Recommended Project Structure

```
lookup/
├── __init__.py          # existing
├── normalize.py         # existing (Phase 1)
├── store.py             # existing; MIGRATIONS gains _v2 (translations, meta)
├── config.py            # config.json: dictionaries[], online flag, client list
├── dicts.py             # discovery, order, Article, search_all, base form, index cache
├── stardict.py          # .ifo/.idx(.gz)/.dict(.dz)/.syn; dictzip reader
├── dsl.py               # UTF-16/UTF-8 BOM, #headers, headword groups, {} expansion, tags
├── mdx.py               # header, key info (+Encrypted=2), key/record blocks, zlib/none/LZO
├── lzo.py               # LZO1X decompress only (Code Examples 1)
├── ripemd128.py         # pure-Python digest for Encrypted=2 (format compatibility only)
├── online.py            # gtx/dict-chrome-ex/at + fallback; TranslateError(reason)
├── translate.py         # orchestrator: classify, dicts, cache, online, upsert
├── __main__.py          # argparse CLI; sets stdout to UTF-8; prints; exit codes
└── data/
    ├── irregular.txt    # generated from WordNet exception lists (D-11)
    └── NOTICE-wordnet.txt
```

Note: the CONTEXT lists `lookup/data/irregular.txt` (D-11). `ripemd128.py` is an additional flat module that D-27 does not list; keep it flat (ponytail) and name it in the plan.

### Pattern 1: Reader contract (one `Dictionary` object per file, all readers identical)

**What:** Every reader exposes the same small surface, so `dicts.py` never branches on format except at discovery.
**When to use:** All three formats.
**Example:**
```python
# Source: this design (D-05, D-27); field names are the planner's choice within D-05
@dataclass(frozen=True)
class Article:
    dict_name: str
    headword: str
    transcription: str | None
    senses: tuple  # ((pos | None, (value, ...)), ...)  best effort
    text: str      # always present; plain text
    lemma_of: str | None = None

class Dictionary(Protocol):
    name: str
    fmt: str                      # "stardict" | "dsl" | "mdx"
    entry_count: int
    skipped_entries: int         # invalid entries dropped while opening (Finding 4)
    def lookup(self, key: str) -> list[Article]: ...   # key already casefolded
    def headwords(self) -> Iterable[str]: ...          # for lemma candidate checks
```
Opening failures (broken files, unsupported `Encrypted=1`) raise `DictError(reason)`; `dicts.py` records the reason for `--list-dicts` and continues (D-02).

### Pattern 2: Index once, read on demand

**What:** Build `key -> (offset, size)` (or DSL/MDX equivalent) when a dictionary opens. Read article bytes only on lookup.
**Measured (Mueller 7, this machine, 2026-10-24):** gunzip of the idx 2.4 ms; parse of 46 232 entries into a dict 24.8 ms; one dictzip article read (one 58 KB chunk, 12.8 KB article) 0.08 ms average over 100 reads. The warm-open budget in D-09 (300 ms for all dictionaries) fits StarDict comfortably.
**Estimate (not measured):** DSL and MDX cold builds are larger. Measure them on a real file in Wave 1 before fixing the index design.

### Pattern 3: Lemma resolution order with pointer following

**What:** The search order from D-10, with one addition made necessary by Finding 1.
```
1. exact casefolded key in dictionary D
   - if D's article is a pure pointer ("[t] _pos. от X" and nothing else) -> follow X:
       lookup X exactly; result.lemma_of = X; keep the pointer text as header
2. irregular.txt candidate (only if it exists as a headword in some dictionary)
3. suffix rules (D-11) in a fixed order; each candidate must exist in some dictionary
4. not found
```
Known outcomes on the real Mueller 7 file (from the presence check): `running` present (own noun sense plus `от run`), `ran` pointer to `run`, `went` pointer to `go`, `men` pointer to `man`, `stopped` absent (doubled consonant rule yields `stop`, present), `books` absent (`-s` rule yields `book`, present), `boxes` absent (`-es` rule yields `box`, present), `runs` absent (`-s` yields `run`).

### Pattern 4: One deadline for the whole online path

**What:** D-16 budget. Keep the monotonic deadline in `online.py`; each attempt gets `max(0.5, remaining)`; the first success stops the chain.
```python
# Source: this design; time budget from D-16
import time
def chain_translate(text, clients, fallback, deadline_s=3.0):
    t_end = time.monotonic() + deadline_s
    reasons = []
    for call in [*clients, fallback]:
        remaining = t_end - time.monotonic()
        if remaining < 0.5:
            reasons.append("timeout"); break
        try:
            return call(text, timeout=remaining)   # raises TranslateError(reason)
        except TranslateError as e:
            reasons.append(e.reason)
    raise TranslateError(_pick_reason(reasons))
```
Per-socket timeouts in urllib are not a wall clock (Pitfall 7 in PITFALLS.md); the deadline is enforced by the chain, and the sentence thread is joined with `future.result(timeout=...)` in `translate.py`.

Latency measured from the VM through `urllib`: 0.14 to 0.17 s per word query on `gtx`, `dict-chrome-ex` and `at`; one non-word query took 0.87 to 1.11 s (cause not isolated); MyMemory via `curl` took 0.37 to 0.80 s. A new CLI process also pays DNS and TLS setup, which was not measured in isolation. The daemon in Phase 5 keeps connections alive.

### Pattern 5: Migration v2 added without changing v1 semantics

**What:** Add `_v2` to `MIGRATIONS`; tests that mean "a v1 database" use an explicit `V1 = MIGRATIONS[:1]`. See Pitfall 11 for the exact changes.
```python
# store.py (sketch)
def _v2(conn):
    conn.execute("CREATE TABLE translations (text TEXT NOT NULL, "
                 "kind TEXT NOT NULL CHECK(kind IN ('word','phrase','sentence')), "
                 "provider TEXT NOT NULL, payload TEXT NOT NULL, "
                 "fetched_at INTEGER NOT NULL, PRIMARY KEY(text, kind))")
    conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
MIGRATIONS = (_v1, _v2)
CURRENT_VERSION = len(MIGRATIONS)
```

### Pattern 6: `upsert_word` with lemma and COALESCE

**What:** `upsert_word` (Phase 1) has no `lemma` parameter. D-12 needs one, with the same COALESCE rule as `translation` (never overwrite a stored value with NULL).
**Sketch:** add `lemma=None` as a keyword parameter; in `ON CONFLICT ... SET lemma = COALESCE(excluded.lemma, words.lemma)`. Existing callers are unaffected.

### Anti-Patterns to Avoid

- **Exact-first without the pointer rule:** returns one-line pointers for `ran`, `went`, `men`, `gone` (Finding 1).
- **Trusting `wordcount` or rejecting a dictionary on one bad entry:** the real Mueller 7 index has one (Finding 4).
- **Using `zlib.decompress()` on whole untrusted blocks:** no size cap, so a crafted block can expand without limit (Security Domain). Use `decompressobj(...).decompress(data, max_length)` or check the declared size first.
- **Printing or logging article or query text in library modules:** violates V7 (D-26).
- **Calling `hashlib.new("ripemd128")` on any Python version:** not available (see Standard Stack).
- **`print()` of Cyrillic or IPA text on the Windows host without UTF-8 stdout:** raises `UnicodeEncodeError` on the default cp1251 console (verified). The CLI must set `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`.
- **Sending the user's e-mail to MyMemory (`de=`) to raise the quota:** privacy rule (system instructions and PROJECT.md). Do not add `de=` or `key=`.

## Format Reference

### 1. StarDict (`stardict.py`) [CITED: https://github.com/huzheng001/stardict-3/blob/master/dict/doc/StarDictFileFormat]

- Files: `X.ifo` (required), `X.idx` or `X.idx.gz` (required), `X.dict` or `X.dict.dz` (required), `X.syn` (optional). Search for `.ifo` recursively; the other files share the basename.
- `.ifo`: first line is the magic `StarDict's dict ifo file`; `version=2.4.2` or `3.0.0`; `key=value` lines with UTF-8. Required: `bookname`, `wordcount`, `idxfilesize`; `sametypesequence` "very important"; `idxoffsetbits=64` allowed only in version 3.0.0 (otherwise 32-bit offsets).
- `.idx` entries, in order: `word` (UTF-8, NUL-terminated, shorter than 256 bytes), `offset` (4 bytes big-endian, or 8 when `idxoffsetbits=64`), `size` (4 bytes big-endian). Duplicate headwords are allowed.
- `.dict`: article data. If `sametypesequence` is set (Mueller 7: `m`), each article is just the concatenated fields with no type letters, and the last field has no terminator and no length prefix; its extent comes from `size` in the index. `m` = UTF-8 text, `t` = phonetic (English), `x` = XDXF markup, `h` = HTML, `g` = Pango markup, `y` = Chinese/Japanese phonetic, `k` = KingSoft XML, `w` = MediaWiki, `r` = resource list; uppercase types carry a 4-byte BE length prefix (`W`, `P`).
- `.dict.dz` is dictzip (see 2). `.idx.gz` is plain gzip.

**Mueller 7 verified facts (local parse 2026-10-24):** `version=2.4.2`, `wordcount=46231`, `idxfilesize=806608` (matches the decompressed idx exactly), `sametypesequence=m`, no `idxoffsetbits` so 32-bit offsets. The archive also contains a plain `mueller7.dict` (8 099 010 bytes, identical to the dictzip output) and a stray `.mueller7.dict.swp`. Articles are valid UTF-8 (0 undecodable of 46 231 entries under `utf-8` strict).

**Index entry validation (required):** skip an entry when the headword is empty, when `offset + size > len(data)`, or when `size == 0`; count the skipped entries in `Dictionary.skipped_entries` and show the count in `--list-dicts`.

### 2. dictzip (`.dict.dz`) [VERIFIED: local parse of mueller7.dict.dz; CITED: dictzip man page and cgit dissector via WebSearch, MEDIUM]

- It is a gzip file (`1f 8b 08`) with FLG bit 4 (FEXTRA) set. The FEXTRA field holds subfield `R` `A` (`SI1='R'`, `SI2='A'`), a 2-byte LE length, then `VER` (2 bytes, = 1), `CHLEN` (2 bytes, chunk uncompressed size, <= 65535), `CHCNT` (2 bytes), and `CHCNT` 2-byte LE compressed chunk sizes.
- Flag FNAME (bit 3) is usually set on dictzip output: skip the null-terminated name after the extra field (Mueller 7: flags = 12 = FEXTRA|FNAME).
- Each chunk is an independent raw deflate stream (`zlib.decompressobj(-15)`), starting at the byte after the header and advancing by each chunk's compressed size.
- Mueller 7 values: `VER=1`, `CHLEN=58315`, `CHCNT=139`, sum of compressed sizes 2 644 616, decompressed total 8 099 010 (matches the plain file byte for byte).
- Random access: `first = off // CHLEN`, `last = (off + size - 1) // CHLEN`, decompress chunks `first..last`, slice `[off - first*CHLEN : ... + size]`. Keep the chunk offset table (139 integers) in memory.

### 3. MDX / MDD (`mdx.py`) [CITED: writemdict fileformat.md (github.com/zhansliu/writemdict); CITED: readmdict.py (github.com/csarron/mdict-analysis, GPL-3 header; use as spec only, do not copy code); verified structure against the reference, no sample MDX available]

**Header.** Big-endian uint32 `L`; then `L` bytes of UTF-16LE XML text (ends with `\x00\x00`); then uint32 Adler-32 of those bytes, little-endian. Attributes: `GeneratedByEngineVersion` ("1.2" or "2.0"), `Encrypted` (`0`/`No`, `1`/`Yes`, `2`), `Encoding` (`UTF8`, `UTF-16`, `GBK` (use `gb18030`), `Big5`), `Format` (`Html`/`Text`), `StyleSheet` and `Compact` (not supported: ignore; document), `RegisterBy`, `RegCode` (not used).

**Number width.** Version < 2.0: 4-byte big-endian numbers. Version >= 2.0: 8-byte big-endian numbers.

**Keyword section header.**
- v2.0: five numbers (`num_blocks`, `num_entries`, `key_info_decomp_size`, `key_info_size`, `key_blocks_size`), 40 bytes, then a 4-byte big-endian Adler-32 over those 40 bytes.
- v1.2: four numbers (`num_blocks`, `num_entries`, `key_info_size`, `key_blocks_size`), no checksum.

**Key info block** (`key_info_size` bytes, called `key_index` in the format document).
- v2.0: block starts with type `02 00 00 00`, then Adler-32 (big-endian), then zlib data. If `Encrypted & 2`: decrypt bytes from offset 8 onward first (below), then `zlib.decompress(block[8:])`. Entries (`num_blocks` of them): `num_entries` (8 bytes BE); `first_key_len` (2 bytes BE), `first_key` text + terminator; `last_key_len` (2 bytes BE), `last_key` text + terminator; `comp_size` (8 BE); `decomp_size` (8 BE). Terminator is 1 unit for UTF-8/GBK, 2 bytes for UTF-16.
- v1.2: uncompressed; entry fields are 4-byte `num_entries`, 1-byte key lengths and text with no terminator, 4-byte sizes.

**Encrypted=2 key info decryption (verified to match both the format document and the reference code).**
```
key   = ripemd128(block[4:8] + b"\x95\x36\x00\x00")       # block[4:8] = stored Adler-32 bytes
prev  = 0x36
for i, c in enumerate(block[8:]):                         # ciphertext c
    t = swap_nibbles(c) ^ prev ^ (i & 0xff) ^ key[i % len(key)]
    prev = c
    plaintext[i] = t
```
`Encrypted & 1` (registration key, Salsa20/8) is not supported: mark the dictionary "регистрационное шифрование" in `--list-dicts` (D-07).

**Key blocks** (concatenated after the key info). Each block: `comp_type` (4 bytes LE: 0 none, 1 LZO, 2 zlib), Adler-32 (big-endian) of the decompressed data, then data of `comp_size` bytes including the 8-byte header. Decompressed size comes from key info. For LZO, the bytes after the 8-byte header are a raw LZO1X stream (the reference wraps it with a `0xF0` + big-endian size prefix only because python-lzo requires that header; the prefix is not part of the stream) [ASSUMED for the prefix meaning; verify by the Adler-32 check on a real file].
- Each decompressed key block: repeated `offset` (number width BE) followed by NUL-terminated key text (1-byte NUL for UTF-8/GBK/Big5, 2-byte NUL for UTF-16). Decode the key with the file's encoding; reference strips whitespace.

**Record section.** Numbers (width as above): `num_blocks`, `num_entries`, `index_len` (= 2 × width × `num_blocks`), `blocks_len`; then `num_blocks` pairs `(comp_size, decomp_size)`; then record blocks, each with the same 8-byte header (type, Adler-32) and data.
- Record `i` occupies bytes `[offset_i, next_offset)` of the concatenation of all decompressed record blocks. Compute `next_offset` as the next larger offset in offset order (not the next key in key order: the reference assumes key order equals offset order; do not rely on it). The last record ends at the end of the concatenation.
- Locate the block containing an offset by bisect on the cumulative decompressed sizes. A record can span two blocks; read both.
- Strip trailing `\x00`; decode with the file encoding; for `Format=Html` pass through `html.parser` to text (D-06).

**MDD** (`.mdd`) is ignored (D-02).

### 4. Lingvo DSL (`dsl.py`) [CITED: GoldenDict-ng src/dict/dsl_details.cc, github.com/xiaoyifang/goldendict-ng (staged branch), GPL; used as behaviour reference]

- Encoding: detected from the first bytes. UTF-16LE with BOM `FF FE` or without BOM when the first character is `#` (`23 00`); UTF-16BE `FE FF`; UTF-8 with or without BOM (`EF BB BF`). `.dsl.dz` is dictzip (see 2).
- Header: lines beginning with `#` at the start of the file: `#NAME "..."`, `#INDEX_LANGUAGE "..."`, `#CONTENTS_LANGUAGE "..."`, `#SOUND_DICTIONARY`, `#SOURCE_CODE_PAGE`. The value is inside double quotes. The header ends at the first line not starting with `#`.
- Article structure: one or more non-indented headword lines (column 0, non-empty) followed by indented body lines (starting with a space or tab). Every headword line is a key for the same article.
- Optional parts `{...}` in a headword are variants: `word{s}` yields `word` and `words`. GoldenDict caps variant expansion at 32 headwords (`headwords->size() >= 32` in `dsl_details.cc`); use the same cap.
- Escapes: a backslash escapes the next character (`\[`, `\{`, `\\`).
- Tags (Lingvo markup, handled by GoldenDict's parser): `[m1]`..`[m9]` senses by indent level; `[trn]` translation; `[p]` part of speech; `[t]` transcription (GoldenDict counts transcriptions for `[t]`); `[ex]` example; `[c]` colour; `[com]` comment; `[ref]` reference; `[i]`, `[b]` italic/bold; `[s]` sound file (GoldenDict counts media for `[s]`). Map to plain text per D-06; unknown tags are stripped, text is kept.

### 5. Mueller 7 article conventions (for the best-effort sense parser) [VERIFIED: local analysis of mueller7.dict, counts over 46 231 articles]

- Leading transcription in square brackets: `[rʌn]`, `[ˈbetə]`. Present in 45 677 articles (98.8%).
- POS tags `_n.` (31 244 occurrences), `_a.` (11 406), `_v.` (7 521), `_pl.` (3 067), `_attr.` (1 335), `_adv.` (1 253), `_p-p.` (936), `_pres-p.` (898), `_p.` (327) and others. Usage labels are also `_x.` with Cyrillic or Latin text (`_разг.`, `_ам.`, `_ав.`, `_горн.`, `_лат.`); they are not POS. The parser needs a POS whitelist (`n a v adv pl p p-p pres-p attr comp sup pred predic prep conj pron num int interj art aux`).
- Numbered POS blocks: `1. _n. ... 2. _v. ...`, 7 547 articles.
- Senses: `1>`, `2>` (18 184 articles; they are within a POS block).
- Homographs: `_I`, `_II` Roman numerals (1 441 articles), e.g. `better` = `_n. держащий пари ... _II [ˈbetə] 1. _a. ...`.
- Cross-references `{см. bet 2}` (278 articles); parenthetical `(тж. ...)`.
- Form pointers: `[transcription] _x. от LEMMA [n]`, where `_x.` is a POS-like tag (`_p.`, `_pl.`, `_comp.`, `_p-p.`, `_pres-p.`, `_сокр.` and others). 601 articles match the pure pointer pattern; 576 of the 601 targets are headwords.
- Articles can be long (`go` 16 010 bytes, `run` 12 789 bytes). Print the full text in the CLI; the UI truncates later.
- The `(C) Dictionary Format` headword and 198 headwords beginning with `_` (Russian label keys) are dictionary metadata: exclude them from search results.

Presence check of test forms (headword exists in Mueller 7):

| Form | Present | Article start | Implication |
|------|---------|---------------|-------------|
| running | yes | `[ˈrʌnıŋ] 1. _pres-p. от run 2 2. _n. ...` | exact hit with pointer plus own sense: show article, lemma hint `run` |
| ran | yes | `[ræn] _p. от run 2` | pointer only: follow to `run` (Finding 1) |
| went | yes | `[went] _p. от go 1` | pointer: follow to `go` |
| gone | yes | `[gɔn] 1. _p-p. от go 1; ...` | pointer plus own text: follow and show |
| men | yes | `[men] _pl. от man 1` | pointer: follow to `man` |
| teeth | yes | `[tiːθ] _pl. от tooth 1` | pointer: follow to `tooth` |
| worse | yes | `[wəːs] 1. _a. (_comp. от bad 1) ...` | own article with pointer in parentheses |
| better | yes | `[ˈbetə] _n. держащий пари ... _II [ˈbetə] 1. _a. (_comp. от good 1)` | homograph article; no lemma rule applies (D-10 example) |
| data | yes | `[ˈdeıtə] _n. _pl. 1> _pl. от datum ...` | exact hit; sense mentions `datum` |
| news | yes | `[njuːz] _n. _pl. (употр. как sing) 1> ...` | exact hit; rules off (D-10) |
| ceiling | yes | `[ˈsiːlıŋ] _n. 1> потолок ...` | exact hit |
| stop | yes | `[stɔp] 1. _n. ...` | target of `stopped` (doubled consonant) |
| stopped | no | — | rule `-ed` then doubled consonant gives `stopp` (absent), then `stop` (present) |
| book | yes | `[buk] 1. _n. 1> книга ...` | target of `books` |
| books | no | — | rule `-s` gives `book` (present) |
| runs | no | — | rule `-s` gives `run` (present) |
| boxes | no | — | rule `-es` gives `box` (present) |
| box | yes | `[bɔks] 1. _n. 1> коробка ...` | target of `boxes` |
| break out | no (headword) | sub-entry in `break` article: `break out а> выламывать; б> убежать ...` | Finding 2; phrase search misses |
| well-known | no (headword) | — | hyphenated compound not present; online fallback for phrases |

### 6. Online endpoints (`online.py`) [VERIFIED: live probes from `archvm` (curl and Python urllib) and from the Windows host, 2026-10-24]

Probe results (test words only, no user data):

| Endpoint | Client | Tool | Result |
|----------|--------|------|--------|
| `translate.googleapis.com/translate_a/single` | `gtx` | VM curl | 429, `text/html`, body "Sorry..." for every query |
| same | `gtx` | VM Python urllib | 200 JSON for `run`, `ran`, `break out`, `xyzzyq` |
| same | `gtx` | Windows host curl | 200 JSON |
| same | `dict-chrome-ex` | VM curl and urllib | 200 JSON; `run` payload byte-identical to `at` |
| same | `at` | VM curl and urllib | 200 JSON |
| same | `webapp`, `t` | VM curl | 403 HTML |
| `api.mymemory.translated.net/get` | — | VM curl | 200 JSON for all probes |
| `lingva.ml/api/v1/en/ru/...` | — | VM curl | 200 but echoes the input (`run` → `run`, `break out` → `break out`, sentence echoed); also echoes for `en/de` (`run`); rejected |
| `translate-pa.googleapis.com/v1/translateHtml` | — | VM | 403 "requires API key or other identity"; rejected |
| `libretranslate.com/translate` | — | VM | 403 Cloudflare; rejected |

**Google `translate_a/single` response shape (verified on the three working fixtures):**
- `d[0]`: list of segments `[translated, original, null, null, n]`. Join `s[0]` for the main translation. Some segments carry transliteration: `[null, null, "begat'", "rən"]` (`dt=rm`): index 2 is the target-language transliteration, index 3 the English pronunciation (e.g. `rən`, `no͞oz`). The source transcription is absent for some words (`books`, sentences).
- `d[1]`: present only for word-like inputs with dictionary data (`dt=bd`). Each element: `[pos, [terms...], [[term, [reverse...], null, score], ...], source_word, index]`. `source_word` is the input or its base form: for `ran` it is `run` (lemma) and the translation is `побежал`. For `books` the source word stays `books` and the top sense is an odd `сборник отчетов` (a quality warning).
- `d[1]` is `null` for sentences, for `xyzzyq`, and for the non-word transliteration.
- `d[2]`: detected source language (`"en"`).
- `d[6]`: a float that looks like detection confidence (0.979 for `run`, 0.494 for `xyzzyq`) [ASSUMED semantics].
- Example from `dict-chrome-ex` for `break out`: `d[1][0] = ["verb", ["разразиться", "вспыхивать", ...], [["разразиться", ["break out", "outbreak", ...], null, 0.0279], ...], "break out", 2]`.

**MyMemory response (verified live):** `responseData.translatedText` (string), `responseStatus` (200), `quotaFinished` (bool), `responseDetails`, `matches` (list with `translation`, `quality`, `created-by`). Single words are answered from translation memory (`run` → `бегу`, first-person; `break out` → `уход на перерыв`, which is a wrong sense); sentences are good (`The quick brown fox jumps over the lazy dog.` → `Коричневая лиса прыгает через собаку.`). Unknown words echo the input with `match 0.85`.
**Limits (WebFetch summary of the official page, to re-check):** 5000 characters per day anonymous; 50 000 per day with the `de=` e-mail parameter (not used here); `q` at most 500 bytes. Quota-exhausted response was not observed; treat any non-200 or `quotaFinished: true` as `blocked`.

**Non-word and echo rules (D-14 corrected):**
- For word-kind input: `not_found` if `d[1]` is absent or empty. Do not rely on `translation == input`, because the transliteration is different text.
- For sentence and phrase kinds: `not_found` if the translation equals the input after whitespace normalisation, or is empty.

**Failure classification (D-14/D-16):** HTTP 429 or 403, body starts with `<` or contains "automated queries" / "Sorry..." (case-insensitive), `Content-Type` not JSON, JSON that fails the shape check, timeout, DNS/connection error (`no_network`). Limit response size (read at most 1 MiB).

### 7. Irregular forms (`lookup/data/irregular.txt`) [CITED: WordNet 3.1 `dict/verb.exc`, `noun.exc`, `adj.exc`; Princeton WordNet licence in `dict/data.*`]

- Format: two whitespace-separated fields per line, `inflected base` (for example `ran run`).
- Counts: `verb.exc` 2 401 lines (1 423 distinct bases), `noun.exc` 2 054 lines (1 992 distinct bases), `adj.exc` 1 490 lines. Examples: `ran run`, `went go`, `ate eat`, `men man`, `children child`, `mice mouse`, `teeth tooth`, `better good`, `worst bad`.
- Licence: the WordNet 3.1 licence permits use, copying and distribution without fee, with the Princeton copyright notice retained and the Princeton name not used in advertising. Ship the notice in `lookup/data/NOTICE-wordnet.txt`.
- The list is larger than the ≈200 verbs of D-10. Keep it all (about 6 000 lines, tens of kilobytes) or filter to verbs and irregular plurals; the lookup rule (candidate must exist in a dictionary) prevents wrong lemmas either way.

### 8. RIPEMD-128 [VERIFIED: `hashlib.new('ripemd128')` raises ValueError on Python 3.14.3 and 3.12.0 (Windows host) and on 3.14.8 (VM); the reference implementation reproduces the standard vectors `RIPEMD-128("")` = `cdf26213a150dc3ecb610f18f6b38b46` and `RIPEMD-128("The quick brown fox jumps over the lazy dog")` = `3fa9b57f053c053fbe2735b2380db596`]

- Needed only for `Encrypted=2` key info. Not a security control here (format compatibility), so the project's no-hand-rolled-crypto rule is not violated by implementing the digest in pure Python.
- Licence: the reference `ripemd128.py` in `writemdict` is MIT (2015, zhansliu). The copy in `mdict-analysis` carries no licence statement. Write `lookup/ripemd128.py` from the RIPEMD-128 specification and test it with the two vectors above. Do not copy either file into the project.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LZO1X decompression | Anything beyond the decoder below | Own decoder (Code Examples 1), verified against liblzo2 | Decoder only is ~100 lines; compression is not needed (MDX is read-only) |
| Gzip/deflate | Own inflate | `zlib` with `wbits=-15` and `decompressobj(max_length)` | Stdlib; bounded output defeats decompression bombs |
| dictzip index | Own gzip parser | Raw parse of FEXTRA `RA` plus `zlib` per chunk (Format Reference 2) | Verified on the real file |
| Digest for MDX Encrypted=2 | Any cryptographic design | Own RIPEMD-128 (Format Reference 8) | Format requirement only; no security use |
| HTML to text (MDX/XDXF/`h`) | Regex stripping | `html.parser.HTMLParser` subclass | Handles entities and nested tags; no lxml/bs4 (CONTEXT) |
| Irregular verbs/plurals | Hand-written list in code | `lookup/data/irregular.txt` from WordNet exception lists | Data file, D-11; permissive licence |
| Language detection | Own detection | Google `d[2]` plus script check (`normalize()` already rejects non-Latin) | Phase 1 rules decide the input |
| Online retry/backoff | Retry loops | Single pass per client with the chain deadline (Pattern 4) | D-14: no repeats of the same client |
| Index persistence | `pickle`/`marshal` | JSON or fixed-layout binary with a version header | Safe to load from a user-writable cache (Pitfall 13) |

**Key insight:** The only non-trivial code is the byte-level readers. Their correctness is established by checks against real output (Mueller 7 for StarDict and dictzip, liblzo2 for LZO, reference vectors for RIPEMD-128), not by reading the reference code alone.

## Runtime State Inventory

Not applicable: this is a greenfield phase (new readers, new tables), not a rename, refactor or migration of existing names. The only existing data touched is the Phase 1 database, which gets migration v2 (Pitfall 11).

## Common Pitfalls

### Pitfall 1: Exact-first returns pointer articles
**What goes wrong:** `ran` returns `_p. от run 2`; the CLI looks broken for TRAN-04.
**Why it happens:** Mueller 7 has headwords for most irregular forms with a one-line pointer article.
**How to avoid:** Pointer-follow rule (Pattern 3). Test with `ran`, `went`, `men`, `teeth`, `gone`.
**Warning signs:** the printed result for an inflected form is shorter than 60 characters and starts with `[`.

### Pitfall 2: Phrase lookup assumes headwords
**What goes wrong:** `break out` misses in Mueller and goes online every time; CAPT-04 expects `break out` first.
**Why it happens:** the phrase is a sub-entry inside `break`.
**How to avoid:** Decide before planning (Open Question 1). If the online fallback is accepted, the test for "break out in dictionary" must be removed from D-17. If in-article search is wanted, it needs a separate index built from article text (not in Phase 2 scope as written).
**Warning signs:** `--word "break out"` returns `break` article only, or only online output.

### Pitfall 3: Dictionary rejected or shifted by one bad entry
**What goes wrong:** the real Mueller 7 is marked broken, or the wrong article is returned after a count-based slice.
**Why it happens:** the index contains an empty headword with an invalid offset/size; `wordcount` (46231) is one less than the parsed count (46232).
**How to avoid:** validate every entry; count skipped entries; never trust `wordcount` for array sizing.
**Warning signs:** `IndexError` or `MemoryError` near `size=1667331443`.

### Pitfall 4: Choosing the wrong data file
**What goes wrong:** both `.dict` and `.dict.dz` are present, or the stray `.swp` file is picked up.
**How to avoid:** match exact names `X.ifo` → `X.idx`/`X.idx.gz` and `X.dict`/`X.dict.dz` with the same basename; prefer `.dict` if present (no inflate on read), else `.dict.dz`; ignore dotfiles and any other suffix.

### Pitfall 5: Trusting the Google client status from curl
**What goes wrong:** a manual `curl` check says gtx is blocked (429), but the app's `urllib` works, or the reverse on another machine.
**Why it happens:** the endpoint's bot checks depend on the TLS/HTTP fingerprint, not only on the IP (Finding 5).
**How to avoid:** every acceptance check of online behaviour runs the app's own `urllib` code path from the VM (SC4). Keep the client chain; do not drop `gtx` because one probe failed.

### Pitfall 6: Non-word transliteration accepted as translation
**What goes wrong:** `xyzzyq` shows `ксиззик` as its translation and is saved to the database with a counter.
**Why it happens:** the echo rule ("translation == input") does not catch transliterations (Finding 7).
**How to avoid:** the word-kind rule in Format Reference 6; a test with the captured `xyzzyq` fixture.

### Pitfall 7: MyMemory quality for single words
**What goes wrong:** `break out` is answered `уход на перерыв` and `run` as `бегу`; the popup shows a wrong sense as if it were a dictionary result.
**How to avoid:** restrict MyMemory to sentence and phrase kinds, or label its answer as "машинный перевод" (Open Question 3).

### Pitfall 8: Unbounded decompression
**What goes wrong:** a crafted `.dict.dz` chunk or MDX block expands to gigabytes; memory blows up.
**How to avoid:** use `zlib.decompressobj().decompress(data, max_length)` with the declared size plus a cap (for example 16 MiB per article); reject declared sizes above the cap before allocating; for LZO, check `out_len` before the loop and stop when output exceeds it.

### Pitfall 9: Latency spikes and per-process setup in urllib
**What goes wrong:** occasional responses take about 1 s (observed 1.11 s once, on a non-word query), and a one-shot CLI also pays DNS and TLS setup on every run; together these can eat much of the 3 s budget.
**How to avoid:** measure the full path in the VM with the CLI's own process startup; reuse one `urllib` opener per process; in the CLI, start the sentence thread before the dictionary search so the network time overlaps (D-18).

### Pitfall 10: Windows console encoding
**What goes wrong:** `print()` of IPA or Cyrillic raises `UnicodeEncodeError` (cp1251) on the Windows host; tests that capture stdout may fail the same way.
**How to avoid:** `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` in `__main__.py` only; library modules never print (V7).

### Pitfall 11: Migration tests implicitly mean "schema v1"
**What goes wrong:** after `_v2` is added, these fail: `tests/test_store.py` line 42 (`CURRENT_VERSION == 1`) and the `tables == ["words"]` check; `tests/test_migrations.py` `_make_v1` (calls `open_store(path)` with full `MIGRATIONS`, so the "v1" file is already v2), `M2 = MIGRATIONS + (_add_probe,)` (becomes v3 and breaks `user_version == 2` assertions), `M3`, the step-guard tests that use `MIGRATIONS + (...)` as the base, and `tests/_workers.py` `migrate_child` (`MIGRATIONS + (add_probe,)`).
**How to avoid:** add `V1 = MIGRATIONS[:1]` in `tests/_support.py` (or in each file); replace every "v1 base" expression (`MIGRATIONS + (...)` used with synthetic steps, and `_make_v1`) with `V1`; set `CURRENT_VERSION == 2` and the table list to `["meta", "translations", "words"]` in `test_store.py`; `tests/test_concurrency.py` expects `("ok", 2)` after migrating a v1 file and stays correct once `_make_v1`/`open_store` in that test also use `V1`.
**Warning signs:** `AssertionError: 3 != 2` in migration tests right after adding `_v2`.

### Pitfall 12: Synthetic-only testing of MDX
**What goes wrong:** the writer used in tests and the reader share a misunderstanding (for example the key-info checksum scope), so the tests pass and a real file fails.
**How to avoid:** Adler-32 checks in the reader (the reference does them) turn most mistakes into hard errors; add one UAT step with a real MDX file the user supplies (none exists in this repository or on the reachable web sources checked); keep the RIPEMD-128 vectors and the LZO vectors as independent tests.

### Pitfall 13: Unsafe index cache
**What goes wrong:** `pickle` or `marshal` cache files in `$XDG_CACHE_HOME` are loaded and executed or trusted after tampering.
**How to avoid:** JSON (or a fixed binary layout) with a version field and the source path, size and mtime (D-08); reject mismatches; permissions 0600 for files and 0700 for the directory (Phase 1 pattern).

## Code Examples

### 1. LZO1X decoder (verified prototype, scratch; production version adds `LzoError` wrapping and an output cap)

Source of the algorithm: Oberhumer, LZO 2.10, `src/lzo1x_d.ch` [CITED: lzo-2.10 tarball, GPL-2.0-or-later]. This is a rewrite of the state machine, not a copy. Verified: 20 of 20 vectors from `liblzo2` 2.10 (`lzo1x_1_compress` and `lzo1x_999_compress`, payloads: empty, 1 byte, 3 bytes, 1000 `a`, 10 000 bytes of `ab`, 5000 random bytes, 65 536 bytes of Mueller 7 text, 54 000 bytes of key-block-like data, 70 000 random bytes, 3000 zero bytes), on Python 3.14.3 and 3.12.0. Speed: 9.8 to 10.0 MB/s of output on Mueller text. Truncated input raises `IndexError` in this version; the production wrapper must convert `IndexError` into `LzoError`.

```python
_MAIN, _FIRST_LIT, _MATCH_NEXT, _MATCH, _MATCH_DONE = range(5)


class LzoError(ValueError):
    pass


def lzo1x_decompress(src, out_len=None):
    src = bytes(src)
    n = len(src)
    out = bytearray()
    if n == 0:
        raise LzoError("empty input")

    def copy_back(dist, length):
        if dist == 0 or dist > len(out):
            raise LzoError("lookbehind out of range")
        start = len(out) - dist
        if dist >= length:
            out.extend(out[start:start + length])
        else:
            chunk = out[start:]
            reps, rem = divmod(length, dist)
            out.extend(chunk * reps + chunk[:rem])

    ip = 0
    if src[0] > 17:
        t = src[0] - 17
        ip = 1
        if t < 4:
            state, lits = _MATCH_NEXT, t
        else:
            out.extend(src[ip:ip + t])
            ip += t
            state = _FIRST_LIT
    else:
        state = _MAIN
    while True:
        if state == _MAIN:
            t = src[ip]; ip += 1
            if t >= 16:
                state = _MATCH
                continue
            if t == 0:
                while src[ip] == 0:
                    t += 255; ip += 1
                t += 15 + src[ip]; ip += 1
            t += 3
            out.extend(src[ip:ip + t]); ip += t
            state = _FIRST_LIT
        elif state == _FIRST_LIT:
            t = src[ip]; ip += 1
            if t >= 16:
                state = _MATCH
                continue
            dist = 1 + 0x800 + (t >> 2) + (src[ip] << 2); ip += 1
            copy_back(dist, 3)
            state = _MATCH_DONE
        elif state == _MATCH_NEXT:
            out.extend(src[ip:ip + lits]); ip += lits
            t = src[ip]; ip += 1
            state = _MATCH
        elif state == _MATCH:
            if t >= 64:                       # M2
                dist = 1 + ((t >> 2) & 7) + (src[ip] << 3); ip += 1
                length = (t >> 5) + 1
            elif t >= 32:                     # M3
                t &= 31
                if t == 0:
                    while src[ip] == 0:
                        t += 255; ip += 1
                    t += 31 + src[ip]; ip += 1
                dist = 1 + (src[ip] >> 2) + (src[ip + 1] << 6); ip += 2
                length = t + 2
            elif t >= 16:                     # M4, or end-of-stream marker
                hi = (t & 8) << 11
                t &= 7
                if t == 0:
                    while src[ip] == 0:
                        t += 255; ip += 1
                    t += 7 + src[ip]; ip += 1
                back = (src[ip] >> 2) + (src[ip + 1] << 6); ip += 2
                if hi + back == 0:
                    break
                dist = hi + back + 0x4000
                length = t + 2
            else:                             # M1: two bytes after literals
                dist = 1 + (t >> 2) + (src[ip] << 2); ip += 1
                copy_back(dist, 2)
                state = _MATCH_DONE
                continue
            copy_back(dist, length)
            state = _MATCH_DONE
        elif state == _MATCH_DONE:
            s = src[ip - 2] & 3
            if s == 0:
                state = _MAIN
            else:
                lits = s
                state = _MATCH_NEXT
    if ip != n:
        raise LzoError("input not fully consumed (%d of %d)" % (ip, n))
    if out_len is not None and len(out) != out_len:
        raise LzoError("output length %d != %d" % (len(out), out_len))
    return bytes(out)
```

Test strategy (committed fixtures): store 6 to 8 small vectors as hex or base64 in `tests/fixtures/lzo/vectors.json` (keep the 64 KiB text out of the repository: use a 4 KiB Cyrillic slice instead), each with `raw_len`, `raw_sha256`, `algo`. Add the truncation test (must raise `LzoError`, not `IndexError`) and an out-of-range distance test.

### 2. dictzip chunk table and random read (verified on Mueller 7)

```python
import struct, zlib

def dictzip_index(raw: bytes):
    if raw[:3] != b"\x1f\x8b\x08" or not raw[3] & 4:
        raise ValueError("not dictzip")
    xlen = struct.unpack_from("<H", raw, 10)[0]
    extra = raw[12:12 + xlen]
    if extra[0:2] != b"RA":
        raise ValueError("no RA subfield")
    ver, chlen, chcnt = struct.unpack_from("<HHH", extra, 4)
    if ver != 1:
        raise ValueError("unsupported dictzip version")
    sizes = struct.unpack_from("<%dH" % chcnt, extra, 10)
    pos = 12 + xlen
    if raw[3] & 8:                       # FNAME
        pos = raw.index(b"\x00", pos) + 1
    starts = [pos]
    for s in sizes:
        starts.append(starts[-1] + s)
    return chlen, starts, sizes

def dictzip_read(raw, index, off, size, max_out=16 << 20):
    chlen, starts, _ = index
    if size > max_out:
        raise ValueError("article too large")
    first, last = off // chlen, (off + size - 1) // chlen
    buf = bytearray()
    for c in range(first, last + 1):
        d = zlib.decompressobj(-15)
        buf += d.decompress(raw[starts[c]:starts[c + 1]], max_out)
    start = off - first * chlen
    return bytes(buf[start:start + size])
```

### 3. StarDict index parse with validation

```python
import struct

def parse_idx(idx: bytes, data_len: int, offset_bytes: int = 4):
    entries, skipped = [], 0
    pos, n = 0, len(idx)
    fmt = ">I" if offset_bytes == 4 else ">Q"
    while pos < n:
        j = idx.find(b"\x00", pos)
        if j < 0 or j + 1 + offset_bytes + 4 > n:
            raise ValueError("truncated idx")
        word = idx[pos:j]
        off = struct.unpack_from(fmt, idx, j + 1)[0]
        size = struct.unpack_from(">I", idx, j + 1 + offset_bytes)[0]
        pos = j + 1 + offset_bytes + 4
        if not word or size == 0 or off + size > data_len:
            skipped += 1
            continue
        entries.append((word.decode("utf-8", "replace"), off, size))
    return entries, skipped
```
Measured on the real Mueller 7 index: the parse loop costs about 25 ms for 46 232 entries (the dict build is included).

### 4. Google response: safe indexing and the word-kind rule

```python
import json

def _at(obj, *path):
    cur = obj
    for i in path:
        if not isinstance(cur, list) or not -len(cur) <= i < len(cur):
            return None
        cur = cur[i]
    return cur

def parse_gtx(body: bytes, query: str, kind: str):
    d = json.loads(body)
    segments = _at(d, 0) or []
    main = "".join(s[0] for s in segments
                   if isinstance(s, list) and s and isinstance(s[0], str))
    dict_parts = _at(d, 1)               # None for sentences and non-words
    if kind == "word" and not dict_parts:
        raise TranslateError("not_found")   # includes transliterated non-words
    lemma = _at(dict_parts, 0, 3) if dict_parts else None
    return {"main": main, "dict": dict_parts, "lemma": lemma,
            "src_lang": _at(d, 2)}
```

### 5. MyMemory response parse

```python
def parse_mymemory(body: bytes):
    d = json.loads(body)
    data = d.get("responseData") or {}
    if d.get("quotaFinished") or d.get("responseStatus") != 200:
        raise TranslateError("blocked")          # quota or error: treat as blocked
    text = data.get("translatedText")
    if not isinstance(text, str) or not text.strip():
        raise TranslateError("bad_response")
    return text
```

### 6. Mueller article parsing (best effort, plain text kept)

```python
import re

_TRANSCR = re.compile(r"^\s*\[([^\]]+)\]")
_POS = re.compile(r"(?:^|\s)(?:\d+\.\s+)?_(n|a|v|adv|pl|p|p-p|pres-p|attr|comp|sup|pred|predic|prep|conj|pron|num|int|interj|art|aux)\.")
_FORM_OF = re.compile(r"^\s*\[[^\]]*\]\s+_[\w-]+\.\s+от\s+([A-Za-z][A-Za-z' \-]*?)(?:\s+\d+)?\s*$")

def mueller_parse(text: str):
    m = _TRANSCR.match(text)
    transcription = m.group(1) if m else None
    pointer = _FORM_OF.match(text)
    lemma_hint = pointer.group(1).strip() if pointer else None
    pos_hits = [mm.group(1) for mm in _POS.finditer(text)]
    return transcription, pos_hits, lemma_hint
```
Use `lemma_hint` only for pure pointers (the whole article matches `_FORM_OF`). Full sense splitting (`N>`, `N.`, `_I`/`_II`) is best effort; anything not parsed stays in `text`.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `python-lzo` for MDX LZO blocks | Pure-Python LZO1X decode | — | Verified fast enough (≈10 MB/s); no pacman dependency |
| Google free endpoint `client=gtx` as the only client | Client rotation with `dict-chrome-ex` and `at`; behaviour depends on the HTTP stack | 2026 (per PITFALLS and today's probes) | Keep the list; check through the app's HTTP stack |
| Dictd-format Mueller (AUR `mueller-dict`) | StarDict Mueller 7 (QStarDict, SUSE, ALT) | — | The default dictionary in Phase 7 must be the StarDict build |
| StarDict 2.4.x 32-bit idx offsets | `idxoffsetbits=64` allowed in 3.0.0 | 3.0.0 | Support both; Mueller uses 32-bit |
| MDX version 1.2 | MDX 2.0 (8-byte numbers, zlib key info, Adler-32 on keyword header) | 2.0 | Support both; v2.0 is the common one |

**Deprecated/outdated:**
- `wl-clipboard`-style `kdotool` items are out of scope here.
- `Lingva` public instances: unusable for en→ru as of 2026-10-24 (echo).

## Assumptions Log

> Claims tagged `[ASSUMED]` or otherwise unverified. The planner and discuss-phase use this table to decide what needs user confirmation before execution.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The `0xF0` + BE32 prefix used by the reference reader is a python-lzo header, so MDX LZO blocks are raw LZO1X after the 8-byte block header | Format Reference 3 | Every LZO MDX block fails; detect early with the Adler-32 check on the first real file |
| A2 | MDX `Encrypted=2` key-info scheme and RIPEMD-128 key derivation are correct as described | Format Reference 3, 8 | Key info cannot be decoded; mitigated by reference agreement and Adler-32, but no real `Encrypted=2` sample was tested |
| A3 | MDX v1.2 field widths and the absence of terminators in key info (from the reference) | Format Reference 3 | Old v1.2 dictionaries fail; no v1.2 sample exists in this research |
| A4 | Meaning of `d[6]` in the Google response as detection confidence | Format Reference 6 | Unused in the plan; low impact |
| A5 | MyMemory quota numbers (5000 characters per day anonymous; 500-byte `q`) | Format Reference 6, Standard Stack | Quota could be lower; treat any `quotaFinished` as blocked and show "квота" |
| A6 | QStarDict keeps `mueller7.tar.bz2` available; GPL licence applies | Standard Stack, Findings 3 | PKGBUILD source may disappear; Phase 7 needs a mirror or the SUSE package |
| A7 | Cold build of the DSL and MDX indexes fits "one time" in D-08 (no measurement) | Pattern 2 | Long first open; measure on a real file in Wave 1 |
| A8 | Pure-Python MDX key-block parsing for 100 000+ keys runs in well under 1 s | Pattern 2 | Cold start slower; index cache (D-08) mitigates |
| A9 | `dict-chrome-ex` and `at` are independent of `gtx` in blocking behaviour | Findings 6 | Rotation gives no protection; the fallback to MyMemory carries the load |
| A10 | `gtx` will keep returning 429 to curl-like fingerprints and 200 to urllib (current observation) | Findings 5 | Either way the chain covers it; re-probe in UAT |
| A11 | Irregular-form data from WordNet 3.1 is complete enough for D-11 | Format Reference 7 | Some irregular forms missing; the dictionary-existence rule prevents wrong lemmas |
| A12 | Python 3.12 behaves the same as 3.14 for all readers (only the Windows host has 3.12 here) | Validation Architecture | Run the 3.12 suite on the Windows host before merge; the VM has only 3.14 |
| A13 | MyMemory `break out` and `run` answers are low quality (single observation each) | Pitfall 7 | Decision on MyMemory scope (Open Question 3) depends on this |
| A14 | DSL encoding detection by BOM and by a leading `#` (`23 00` for UTF-16LE without BOM), as in GoldenDict's logic; not tested on a real DSL file | Format Reference 4 | Mis-detected encoding garbles the whole dictionary; test with a real `.dsl` in UAT |

**If this table is empty:** not applicable; it lists 14 items.

## Open Questions

1. **How should phrases that exist only inside an article (`break out`) be handled?**
   - What we know: `break out` is a sub-entry of `break` in Mueller 7 (about 7.4 KB article); there is no headword. D-17 assumed it is a headword.
   - What's unclear: whether Phase 2 must find in-article phrases; Phase 3's CAPT-04 expects `break out` before `break`.
   - Recommendation: accept online-only for in-article phrases in Phase 2 and correct the D-17 example; record the decision in the phase plan. If in-article search is wanted, it is a separate index task (scan article bodies for `phrase а>` patterns), which the planner must size.

2. **Pointer articles: show the target only, or the pointer plus the target?**
   - What we know: `ran` is a pointer; `running` has its own sense plus a pointer.
   - What's unclear: the UX expectation of TRAN-04 ("находят статьи run и book").
   - Recommendation: for a pure pointer, show the target article with a header line `ran → run` and `lemma_of = run`; for mixed articles show the full article and the lemma hint. Put this in D-10 as an amendment.

3. **Should MyMemory answer single words at all?**
   - What we know: word answers are translation-memory matches with wrong senses (`break out` → `уход на перерыв`); sentence answers are good.
   - What's unclear: whether D-15 allows a second provider limited to some kinds.
   - Recommendation: use MyMemory only for sentences and multi-word phrases; for single words that reach the online path, return `not_found` plus the "онлайн-перевод недоступен" message rather than a misleading translation.

4. **How large should `irregular.txt` be?**
   - What we know: WordNet lists about 5 900 inflected forms across verbs, nouns and adjectives; D-10 says about 200 verbs.
   - Recommendation: generate the full file from WordNet (permissive, with notice), since the dictionary-existence check guards against errors.

5. **Who verifies the real MDX format?**
   - What we know: no MDX sample file was available; the reader follows the reference and the format document, with Adler-32 checks.
   - Recommendation: add a UAT step in Wave 1 or 2 where the user places one real `.mdx` (zlib, and ideally one LZO and one Encrypted=2 file) in `$XDG_DATA_HOME/lookup/dicts/` for `--list-dicts`; the tests stay synthetic.

6. **Python 3.12 coverage.**
   - What we know: the VM has only Python 3.14.8; the Windows host has 3.12.0 (`py -3.12`).
   - Recommendation: run the full suite on the Windows host with 3.12 and on the VM with 3.14, and record both in the verification step.

7. **Where does the second-provider decision get made?**
   - D-15 defers "окончательное решение" to a VM probe. Probes are done (Format Reference 6): MyMemory works from the VM; Lingva does not; so MyMemory is the candidate. Confirm in UAT with the real CLI through `urllib` before closing Phase 2.

## Suggested Plan Split (for the planner)

These are suggestions; the planner decides.

- **Wave 1:** `lzo.py` + tests (vectors), `ripemd128.py` + vectors, `dicts.py` skeleton (`Article`, `DictError`, discovery, `config.py`), `stardict.py` + synthetic and Mueller-shaped fixtures, validation rules. Migration `_v2` and the migration-test changes (Pitfall 11) can go in the same wave, since they touch only `store.py` and tests.
- **Wave 2:** `dsl.py` (BOM/encoding, headword groups, `{}` cap at 32, tags) and `mdx.py` (v1.2 and v2.0, zlib/none/LZO, Encrypted=2, index cache). Measure cold builds on a synthetic 50 MB DSL and a writer-made MDX.
- **Wave 3:** lemma resolution (`dicts.py`: pointer follow, irregular data file, suffix rules), `upsert_word` with `lemma`, CLI `--list-dicts`, `--word`, `--offline`, `--no-save`.
- **Wave 4:** `online.py` (gtx, dict-chrome-ex, at, MyMemory), deadline chain, `translate.py` orchestration with cache (`translations`, `meta`), sentence thread, DATA-03 rules, `LOOKUP_TIMING`.
- **Wave 5 (VM UAT):** SC4 through `urllib` in the VM; real Mueller 7 StarDict; one real MDX if the user provides it; `LOOKUP_TIMING` numbers; 3.12 on the Windows host.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.14 | Core, tests | ✓ (Windows `C:\Python314`, VM) | 3.14.3 (Windows), 3.14.8 (VM) | — |
| Python 3.12 | Compatibility target (CONTEXT) | ✓ Windows host only (`py -3.12`) | 3.12.0 | Run only on the Windows host; VM lacks it (Open Question 6) |
| SQLite >= 3.35 | Phase 1 store, `_v2` | ✓ not re-run in this research; Phase 1 requires it (`_MIN_SQLITE` check in `store.py`) | bundled with Python | — |
| zlib | MDX, dictzip | ✓ | 1.3.2 (VM) | — |
| liblzo2 | Test oracle only | ✓ VM (`core/lzo` 2.10-5) | 2.10 | Use committed vectors; no runtime need |
| Internet from VM | SC4 probes | ✓ (curl and urllib work) | — | — |
| Internet from Windows host | Probes, Mueller download | ✓ | — | — |
| Mueller 7 StarDict archive | Manual check and sample test | ✓ downloaded and extracted in scratch | 2007 edition | Fetch again from QStarDict; SUSE package as backup |
| WordNet 3.1 dict files | Generating `irregular.txt` | ✓ downloaded in scratch | 3.1 | — |
| Real MDX file | MDX acceptance | ✗ none found | — | Synthetic writer in tests; user supplies a file for UAT (Open Question 5) |
| `hashlib` ripemd128 | MDX Encrypted=2 | ✗ (all three interpreters) | — | Pure-Python implementation (Format Reference 8) |
| `pyglossary` or other MDX samples | MDX acceptance | ✗ not found in the repository tree query | — | As above |

**Missing dependencies with no fallback:** none blocking. A real MDX file is needed for full MDX acceptance (see Open Question 5).
**Missing dependencies with fallback:** `ripemd128` (pure Python); real MDX sample (synthetic tests plus UAT).

## Validation Architecture

> `workflow.nyquist_validation` is absent in `.planning/config.json`, so this section is included.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | stdlib `unittest` (Phase 1 convention; `tests/` package with `_support.py`) |
| Config file | none (discovery from repo root) |
| Quick run command | `python -m unittest tests.test_lzo tests.test_ripemd128 tests.test_stardict tests.test_dsl tests.test_mdx tests.test_lemma tests.test_online tests.test_translate` |
| Full suite command | `python -m unittest` |
| Windows host, 3.12 | `py -3.12 -m unittest` |
| VM, 3.14 | `ssh archvm 'cd ~/LookUpLinux && python3 -m unittest'` (repo copied to the VM) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TRAN-01 | StarDict parse, `sametypesequence`, 32/64-bit idx, invalid entries skipped | unit | `python -m unittest tests.test_stardict` | ❌ Wave 0 |
| TRAN-01 | dictzip random read equals plain data | unit | `python -m unittest tests.test_stardict.DictzipTests` | ❌ Wave 0 |
| TRAN-01 | DSL: UTF-16LE BOM, UTF-8 BOM, headword groups, `{}` expansion cap 32, escapes, tags | unit | `python -m unittest tests.test_dsl` | ❌ Wave 0 |
| TRAN-01 | MDX v2 zlib, v2 none, v1.2, LZO blocks, Encrypted=2 key info, Adler-32 failure is an error | unit | `python -m unittest tests.test_mdx` | ❌ Wave 0 |
| TRAN-01 | Real Mueller 7 StarDict: `run` returns transcription and POS senses | integration (skipped unless `LOOKUP_TEST_DICTS` set) | `python -m unittest tests.test_mueller_sample` | ❌ Wave 0 |
| TRAN-01 | Discovery order, enabled flags, unsupported `Encrypted=1` reason, broken dict skipped | unit | `python -m unittest tests.test_dicts` | ❌ Wave 0 |
| TRAN-02 | gtx/dict-chrome-ex/at parse from fixtures; HTML 429 → `blocked`; non-JSON → `bad_response`; `xyzzyq` → `not_found` | unit (fixtures) | `python -m unittest tests.test_online` | ❌ Wave 0 |
| TRAN-02 | Deadline chain stops after ~3 s with fake transport; first success short-circuits | unit (fake clock) | `python -m unittest tests.test_online.DeadlineTests` | ❌ Wave 0 |
| TRAN-02 | Second provider (MyMemory) parse from fixture; quota → `blocked` | unit | `python -m unittest tests.test_online.MyMemoryTests` | ❌ Wave 0 |
| TRAN-02 | Real online path through `urllib` from the VM (SC4) | manual UAT | `ssh archvm 'python3 -m lookup --word run --list-dicts'` plus online-only run (see Manual-Only) | — |
| TRAN-03 | Second lookup of a translated word makes no network call (transport patched to raise) | unit | `python -m unittest tests.test_translate.CacheTests` | ❌ Wave 0 |
| TRAN-03 | Errors are not cached; sentence cache trimmed to 1000 | unit | `python -m unittest tests.test_translate.CacheTests` | ❌ Wave 0 |
| TRAN-04 | `running`, `ran`, `went`, `men`, `books`, `stopped`, `boxes`, `better`, `news` give expected article or lemma | unit (uses a small fixture dictionary built in tests) | `python -m unittest tests.test_lemma` | ❌ Wave 0 |
| TRAN-04 | Pointer-follow, irregular list, suffix rules, candidate-must-exist rule | unit | `python -m unittest tests.test_lemma` | ❌ Wave 0 |
| TRAN-05 | Sentence translation runs in parallel; offline or error gives result without sentence translation | unit (threads, fake online) | `python -m unittest tests.test_translate.SentenceTests` | ❌ Wave 0 |
| DATA-03 | 2–4 words saved once; 5+ words not saved; sentence not saved; no-network with no dictionary hit saves with `translation=NULL` | unit | `python -m unittest tests.test_translate.SaveRulesTests` | ❌ Wave 0 |
| D-25 | CLI exit codes 0/1/2; `--list-dicts` lists reasons; UTF-8 stdout | CLI (subprocess) | `python -m unittest tests.test_cli` | ❌ Wave 0 |
| D-26 | Library modules print and log nothing (checked by capturing stdout/stderr around calls) | unit | `python -m unittest tests.test_privacy` | ❌ Wave 0 |
| Phase 1 | Core stays stdlib-only; new modules included in the import test | unit | `python -m unittest tests.test_core_imports` (extend `_IMPORTS`) | ✅ (extend) |
| Phase 1 | Migration v2 coexists with v1 tests (Pitfall 11) | unit | `python -m unittest tests.test_migrations tests.test_store tests.test_concurrency` | ✅ (update) |
| SC3 (Phase 2) | Dictionary and translation paths do not block on the network for the offline part | unit | `python -m unittest tests.test_translate.OfflineFirstTests` | ❌ Wave 0 |
| D-09 | Warm open ≤ 300 ms and search ≤ 20 ms on Mueller 7 | manual timing (VM and Windows host) | `LOOKUP_TIMING=1 python -m lookup --word run --offline --list-dicts` | — |

### Sampling Rate
- **Per task commit:** the quick command above (fixtures only, no network, no real dictionaries).
- **Per wave merge:** full suite on the Windows host (3.14 and `py -3.12`) and on the VM (3.14).
- **Phase gate:** full suite green on both interpreters; SC4 UAT and Mueller 7 manual check recorded before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `tests/fixtures/gtx/` — captured JSON from the VM: `dict-chrome-ex_word_run.json`, `dict-chrome-ex_word_ran.json`, `dict-chrome-ex_word_books.json`, `dict-chrome-ex_phrase_breakout.json`, `dict-chrome-ex_sentence.json`, `dict-chrome-ex_nonword.json`, `dict-chrome-ex_word_news.json`. These files are in `scratchpad/fx/` (copies of the VM responses; all were 200 JSON). Trim `word_run` and `word_ran` to the first segments if the 8 KB size is a problem.
- [ ] `tests/fixtures/mymemory/` — `run.json`, `break_out.json`, `sentence.json`, `xyzzyq.json` (from `scratchpad/fx/mm_*.json`).
- [ ] `tests/fixtures/lzo/vectors.json` — small subset of `scratchpad/lzo_vec/lzo_vectors.json` (payloads up to ~8 KB; drop the 54 KB and 70 KB ones to keep the repository small).
- [ ] `tests/_writers.py` — test-only writers: StarDict (`.ifo`/`.idx`/`.dict`/`.dict.dz`), DSL (UTF-16LE BOM and UTF-8), MDX v1.2 and v2.0 (zlib, none, LZO via committed vectors, Encrypted=2 using the test RIPEMD-128).
- [ ] `tests/test_mueller_sample.py` — skip unless `LOOKUP_TEST_DICTS` points at a folder with `mueller7.ifo`; never commit the archive.
- [ ] `tests/_support.py` — add `V1 = MIGRATIONS[:1]` and an `offline_transport` fixture that makes any `urlopen` call fail the test.
- [ ] Framework: none to install (stdlib).

### Manual-Only Verification (needs the VM)
| Behavior | Why Manual | Steps |
|----------|------------|-------|
| SC4: online path reachable from the VM and reason shown on failure | Requires real network and the app's urllib path | In the VM: `python3 -m lookup --word xyzzyq` (expect not_found, no DB write for word-kind not_found), `python3 -m lookup --text "The quick brown fox jumps over the lazy dog."` (expect translation), `python3 -m lookup --word run --no-save` (expect article and online info when no dictionary) |
| Mueller 7 real article check | Real file and real encoding | Copy `mueller7.ifo`, `mueller7.idx.gz`, `mueller7.dict.dz` to `~/.local/share/lookup/dicts/mueller7/`; run `--list-dicts` (expect 46 231 entries minus skipped 1) and `--word run` |
| MDX acceptance | No sample in repository | User supplies `.mdx` (zlib; ideally LZO and Encrypted=2); `--list-dicts` shows format and reason if unsupported |
| Timing D-09 | VM timing differs from Windows | `LOOKUP_TIMING=1` on the VM over 10 runs; record medians |

## Security Domain

> `security_enforcement` is enabled (absent in config = enabled). ASVS level 1, block on high.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No accounts; Google/MyMemory keys are not used (MyMemory `key=` and `de=` not sent) |
| V3 Session Management | no | No sessions; urllib requests are stateless |
| V4 Access Control | yes (local files) | Dictionary paths are user-controlled; resolve `id` in config under the dictionary root and reject `..` and absolute paths (path traversal) |
| V5 Input Validation | yes | Every offset, size, length and count in StarDict, dictzip, DSL, MDX and LZO is bounds-checked; JSON from the network is shape-checked by `_at`; config JSON is type-checked |
| V6 Cryptography | limited | RIPEMD-128 only for MDX format compatibility; no security use; no custom crypto for anything else |
| V7 Error Handling and Logging | yes | Project V7 rule (D-26): library modules do not print or log query text; exception messages carry type and reason only |
| V8 Data Protection | yes | Cache and index files 0600 (files) and 0700 (directory) like Phase 1; no network identifiers stored except the translated text |
| V9 Communications | yes | `urllib` default TLS verification; never `ssl._create_unverified_context`; no `de=` or `key=` parameters |
| V12 Files and Resources | yes | Decompression caps (Pitfall 8); reject overlarge declared sizes; read at most 1 MiB of network body; no execution of dictionary content |
| V14 Configuration | yes | `LOOKUP_DICTS` and `LOOKUP_DB` are test/override hooks; default paths only in production |

### Known Threat Patterns for stdlib dictionary and HTTP stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Crafted dictionary file with out-of-range offsets (Mueller already has one) | Denial of service, Tampering | Validate every entry; skip with count (Pitfall 3) |
| Decompression bomb in dictzip, zlib or LZO | Denial of service | Caps and `max_length` (Pitfall 8) |
| Path traversal through `config.json` dictionary `id` | Tampering, Information disclosure | Resolve under root, reject escape |
| Pickle/marshal index cache tampered | Tampering → code execution | JSON or fixed layout with version and checksum; never pickle (Pitfall 13) |
| Markup injection from dictionary text into the popup (later phase) | Tampering | Store and show plain text only (D-06) |
| Leaking query text via logs or error messages | Information disclosure | V7 rule; exceptions name reason, not text |
| Sending user identity to a third party (MyMemory `de=`) | Information disclosure | Do not send e-mail or any key |
| Oversized or malformed online response | Denial of service | 1 MiB read limit; shape checks; `bad_response` |
| Downgrade or fake provider | Spoofing | Default TLS verification; hardcoded provider hosts only |

## Project Constraints (from CLAUDE.md)

Directives from `.claude/CLAUDE.md` (project) and the user's global `CLAUDE.md`, applicable to this phase:
- Python 3 + stdlib in `lookup/` ("без pip-зависимостей там, где хватает stdlib"); no pip packages in this phase.
- Privacy: dictionaries and OCR work offline; only the word, phrase or sentence goes to the network for online translation; no screenshots stored (this phase handles no screenshots).
- Online translation must not break the popup; the offline part must not wait for the network (TRAN-02, D-16, D-18).
- Latency targets (hotkey → popup ≤ 1.5 s in the VM) constrain the online deadline (D-16 ~3 s for the online path is a Phase 2 budget; Phase 8 verifies the full path).
- Appearance: no UI in this phase.
- User's global rule: no local LLMs for development work. This research used no local model.
- GSD workflow: writing planning artifacts is the sanctioned route; no direct repo edits outside GSD commands.

## Sources

### Primary (HIGH confidence)
- StarDict file format specification, `huzheng001/stardict-3`, `dict/doc/StarDictFileFormat` (GPL-3.0) — https://github.com/huzheng001/stardict-3/blob/master/dict/doc/StarDictFileFormat (fetched via GitHub, 22 954 bytes)
- MDX/MDD format description (v2.0 and v1.2 notes), `zhansliu/writemdict` `fileformat.md` (MIT licence file present) — https://github.com/zhansliu/writemdict/blob/master/fileformat.md
- MDX reader reference, `csarron/mdict-analysis` `readmdict.py` (GPL-3 header; read as spec) — https://github.com/csarron/mdict-analysis/blob/master/readmdict.py
- RIPEMD-128 reference (`writemdict` `ripemd128.py`, MIT; `mdict-analysis` copy has no licence) — https://github.com/zhansliu/writemdict/blob/master/ripemd128.py
- LZO 2.10 decompressor source, `src/lzo1x_d.ch` and format notes `doc/LZO.TXT` — https://www.oberhumer.com/opensource/lzo/download/lzo-2.10.tar.gz (GPL-2.0-or-later; algorithm read, code rewritten)
- GoldenDict-ng DSL parser, `src/dict/dsl_details.cc` (GPL) — https://github.com/xiaoyifang/goldendict-ng/blob/staged/src/dict/dsl_details.cc
- WordNet 3.1 exception lists `dict/verb.exc`, `dict/noun.exc`, `dict/adj.exc` and licence in `dict/data.*` (Princeton) — https://wordnetcode.princeton.edu/wn3.1.dict.tar.gz
- Live probes, 2026-10-24: VM `archvm` (curl and Python urllib) to `translate.googleapis.com/translate_a/single` (`client=gtx`, `dict-chrome-ex`, `at`, `webapp`, `t`), `api.mymemory.translated.net/get`, `lingva.ml`, `lingva.thedaviddelta.com`, `lingva.lunar.icu`, `lingva.garudalinux.org`, `lingva.nikaroo.com`, `libretranslate.com`, `translate-pa.googleapis.com`; Windows host curl to `gtx`, `dict-chrome-ex`, `at`
- Local analysis of Mueller 7 StarDict archive (`mueller7.tar.bz2`, bzip2 integrity OK; `.ifo`, `.idx.gz`, `.dict.dz`, `.dict` parsed and cross-checked)
- liblzo2 2.10 on the VM via `ctypes` (`__lzo_init_v2`, `lzo1x_1_compress`, `lzo1x_999_compress`, `lzo1x_decompress_safe`) — 20 vectors generated, all round-trip
- Phase 1 code and tests: `lookup/store.py`, `lookup/normalize.py`, `tests/*.py` (read in this session)

### Secondary (MEDIUM confidence)
- QStarDict dictionaries page — https://qstardict.ylsoftware.com/dictionaries.php (Mueller 7 GPL; download link `files/mueller7.tar.bz2`)
- SUSE package page `stardict-dic-enru-mueller7` (GPL-2.0+, 46 231 articles) — https://packagehub.suse.com/packages/stardict-dic-enru-mueller7/
- ALT Linux package `stardict-mueller7` — https://packages.altlinux.org/en/p9/srpms/stardict-mueller7/
- AUR `mueller-dict` PKGBUILD (dictd, not StarDict) — https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h=mueller-dict
- dictzip manpage and cgit lua dissector (via WebSearch) — https://man.archlinux.org/man/dictzip.1.en ; https://cgit.janouch.name/hex/tree/plugins/gzip.lua
- MyMemory usage limits page (via WebFetch summary; numbers to re-check) — https://mymemory.translated.net/doc/usagelimits.php ; API spec — https://mymemory.translated.net/doc/spec.php

### Tertiary (LOW confidence)
- Web search about Google translate client status (no authoritative result; only context) — https://urlscan.io/result/019cf1af-6281-7468-a0fc-76b7224de9ca/
- Prior project research: `.planning/research/PITFALLS.md` §Pitfall 1 and `.planning/research/STACK.md` §5 (2026-10-23 observations)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH for stdlib choices (checked on 3.12 and 3.14); MEDIUM for the MyMemory second provider (quota from a summary).
- StarDict and dictzip: HIGH (verified on the real Mueller 7 archive).
- LZO1X: HIGH (20 of 20 liblzo2 vectors on 3.14 and 3.12).
- MDX: MEDIUM (no sample file; reader and format from reference documents; checksums give a built-in check).
- DSL: MEDIUM (behaviour from GoldenDict source; no DSL sample file was tested here).
- Online endpoints: HIGH for today's behaviour (live probes); LOW for longevity.
- Pitfalls: HIGH (each backed by a probe, a file check or a code reference).

**Research date:** 2026-10-24
**Valid until:** online endpoints 7 days (volatile: re-probe in UAT); dictionary formats and LZO 2000+ days (stable); Mueller 7 source availability 30 days.

---

## RESEARCH COMPLETE

Researched by gsd-phase-researcher. Output: `.planning/phases/02-offline-dicts-translate/02-RESEARCH.md`. Not committed (commit only on request).
