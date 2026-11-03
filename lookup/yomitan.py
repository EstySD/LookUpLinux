"""Read Yomitan v3 term banks in place; never extract archive resources."""
import json
from pathlib import Path
import re
import zipfile

from lookup.dicts import Article, DictError, clean_text, fold_key, html_to_text

MAX_ARCHIVE_BYTES = 256 << 20
MAX_TOTAL_BYTES = 512 << 20
MAX_BANK_BYTES = 64 << 20
MAX_ENTRIES = 1_000_000
MAX_MEMBERS = 10000
_BANK = re.compile(r'term_bank_([1-9][0-9]*)\.json\Z')
_BLOCKS = frozenset('div p li ul ol table tr td th br details summary'.split())


def _content(value, depth=0):
    if depth > 64:
        raise DictError('corrupt')
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return ''.join(_content(item, depth + 1) for item in value)
    if not isinstance(value, dict):
        raise DictError('corrupt')
    kind = value.get('type')
    if kind == 'image' or value.get('tag') in ('img', 'script', 'style'):
        return ''
    if kind == 'text':
        return value.get('text', '') if isinstance(value.get('text', ''), str) else ''
    if kind not in (None, 'structured-content'):
        raise DictError('unsupported')
    text = _content(value.get('content', ''), depth + 1)
    return '\n' + text + '\n' if value.get('tag') in _BLOCKS else text


class Yomitan:
    def __init__(self, name, entries, count):
        self.name = name
        self.entries = entries
        self.entry_count = count
        self.skipped_entries = count - sum(len(rows) for rows in entries.values())

    def has(self, key):
        return fold_key(key) in self.entries

    def lookup(self, key):
        return list(self.entries.get(fold_key(key), ()))

    def close(self):
        self.entries.clear()


def open_yomitan(path):
    try:
        if Path(path).stat().st_size > MAX_ARCHIVE_BYTES:
            raise DictError('too_large')
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) > MAX_MEMBERS or sum(m.file_size for m in members) > MAX_TOTAL_BYTES:
                raise DictError('too_large')
            names = [m.filename for m in members]
            if len(set(names)) != len(names):
                raise DictError('corrupt')
            if 'index.json' not in names:
                raise DictError('unsupported')

            def read(name, limit):
                info = archive.getinfo(name)
                if info.flag_bits & 1:
                    raise DictError('unsupported')
                if info.file_size > limit:
                    raise DictError('too_large')
                with archive.open(info) as stream:
                    raw = stream.read(limit + 1)
                if len(raw) > limit:
                    raise DictError('too_large')
                return json.loads(raw.decode('utf-8-sig'))

            index = read('index.json', 1 << 20)
            if not isinstance(index, dict) or type(index.get('format')) is not int or index['format'] != 3:
                raise DictError('unsupported')
            title = index.get('title')
            if not isinstance(title, str) or not clean_text(title):
                raise DictError('corrupt')
            name = clean_text(title)[:512]
            banks = sorted((n for n in names if _BANK.fullmatch(n)), key=lambda n: int(_BANK.fullmatch(n)[1]))
            if not banks:
                raise DictError('empty')
            if [int(_BANK.fullmatch(n)[1]) for n in banks] != list(range(1, len(banks) + 1)):
                raise DictError('corrupt')
            entries = {}
            count = 0
            for bank in banks:
                rows = read(bank, MAX_BANK_BYTES)
                if not isinstance(rows, list):
                    raise DictError('corrupt')
                count += len(rows)
                if count > MAX_ENTRIES:
                    raise DictError('too_large')
                for row in rows:
                    if (not isinstance(row, list) or len(row) != 8
                            or not isinstance(row[0], str) or not fold_key(row[0])
                            or not isinstance(row[1], str) or not isinstance(row[5], list)):
                        raise DictError('corrupt')
                    senses = tuple(text for value in row[5]
                                   if (text := (html_to_text(value) if isinstance(value, str)
                                                else clean_text(_content(value)))))
                    if not senses:
                        continue
                    text = clean_text('\n'.join(senses))
                    pointer = re.fullmatch(r'=\s*([A-Za-z][A-Za-z\s\x27-]*)', text)
                    article = Article(name, clean_text(row[0]), clean_text(row[1]) or None,
                                      ((None, senses),), text,
                                      form_of=pointer[1].strip() if pointer else None,
                                      pointer_only=pointer is not None)
                    entries.setdefault(fold_key(row[0]), []).append(article)
            if not entries:
                raise DictError('empty')
            return Yomitan(name, entries, count)
    except DictError:
        raise
    except (OSError, ValueError, KeyError, RuntimeError, RecursionError, EOFError,
            zipfile.BadZipFile, NotImplementedError) as exc:
        raise DictError('corrupt') from exc
