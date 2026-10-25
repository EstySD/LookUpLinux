"""CLI: 0 means an answer, 1 no answer, 2 usage error.

Only this module prints. stderr contains timings and fixed warnings with
exception type names, never exception messages or query text.
"""
import argparse
import os
import sqlite3
import sys
import time

from lookup import config, dicts, translate
from lookup.store import open_store, SchemaTooNewError, MigrationError

ONLINE_REASONS = {
    'no_network': 'нет сети',
    'timeout': 'онлайн-перевод не ответил вовремя',
    'blocked': 'онлайн-перевод заблокирован',
    'bad_response': 'онлайн-перевод вернул непонятный ответ',
    'not_found': 'не найдено',
}
DICT_REASONS = {
    'corrupt': 'повреждён',
    'unsupported': 'формат не поддерживается',
    'encrypted_registration': 'регистрационное шифрование не поддерживается',
    'missing_files': 'не хватает файлов',
    'too_large': 'слишком большой',
    'empty': 'пустой',
    'checksum': 'ошибка контрольной суммы',
}


def format_result(result) -> str:
    if result.kind == 'invalid':
        return 'Не слово: ввод не подходит для поиска.'
    lines = []
    for article in result.articles:
        header = f'{result.key} → {article.lemma_of}' if article.lemma_of else article.headword
        if article.transcription:
            header += f' [{article.transcription}]'
        lines.extend((f'== {article.dict_name} ==', header))
        for pos, values in article.senses:
            lines.append('  ' + (f'{pos}: ' if pos else '') + '; '.join(values))
        lines.append(article.text)
    if result.online:
        answer = result.online
        source = answer.provider + (f'/{answer.client}' if answer.client else '')
        if result.from_cache:
            source += ', из кэша'
        lines.extend((f'== Онлайн ({source}) ==', answer.main))
        if answer.transcription:
            lines.append(f'[{answer.transcription}]')
        for pos, values in answer.parts:
            lines.append(f'  {pos}: ' + '; '.join(values))
    if not result.articles and not result.online:
        lines.append('Не найдено.')
    if result.online_error and result.online_error != 'not_found':
        lines.append('Онлайн-перевод недоступен: ' + ONLINE_REASONS[result.online_error])
    if not result.online_enabled:
        lines.append('Онлайн-перевод выключен.')
    if result.context_translation:
        lines.append('Предложение: ' + result.context_translation)
    elif result.context_error:
        lines.append('Предложение: перевод недоступен (' + ONLINE_REASONS[result.context_error] + ')')
    if result.saved:
        lines.append(f'Записано: искали {result.count} раз')
    return '\n'.join(lines)


def format_dict_list(dictset, roots) -> str:
    lines = ['Каталоги словарей:'] + [f'  {root}' for root in roots]
    rows = dictset.info()
    if not rows:
        lines.append('Словари не найдены.')
    for row in rows:
        status = ('выключен' if row.status == 'disabled' else
                  DICT_REASONS.get(row.reason, 'повреждён') if row.status == 'error' else 'ok')
        lines.append(f'{row.order or "-"}\t{row.id}\t{row.fmt}\t{row.name}\t'
                     f'entries={row.entries}\tskipped={row.skipped}\t{status}')
    return '\n'.join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog='lookup')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--word')
    group.add_argument('--text')
    group.add_argument('--list-dicts', action='store_true')
    parser.add_argument('--context')
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--no-save', action='store_true')
    try:
        args = parser.parse_args(argv)
        if args.word is not None and len(args.word.split()) > translate.MAX_PHRASE_WORDS:
            parser.error('для предложения используйте --text')
    except SystemExit as exc:
        return exc.code
    dictionaries = None
    conn = None
    try:
        cfg = config.load()
        roots = dicts.dict_roots()
        started = time.perf_counter()
        try:
            dictionaries = dicts.open_all(cfg, roots)
        except Exception as exc:
            print(f'Словари недоступны: {type(exc).__name__}', file=sys.stderr)
        open_dicts = (time.perf_counter() - started) * 1000
        if args.list_dicts:
            if dictionaries is None:
                return 1
            print(format_dict_list(dictionaries, roots))
            return 0
        started = time.perf_counter()
        try:
            conn = open_store()
        except SchemaTooNewError as exc:
            print(str(exc), file=sys.stderr)
        except (MigrationError, sqlite3.Error, OSError) as exc:
            print(f'База недоступна: {type(exc).__name__}', file=sys.stderr)
        open_db = (time.perf_counter() - started) * 1000
        result = translate.lookup(args.word if args.word is not None else args.text,
                                  dictset=dictionaries, conn=conn, context=args.context,
                                  online=cfg.online and not args.offline,
                                  save=not args.no_save, clients=cfg.clients)
        print(format_result(result))
        if args.context and not result.online_enabled:
            print('Предложение: перевод выключен.')
        if os.environ.get('LOOKUP_TIMING') == '1':
            timings = dict(result.timings, open_dicts=open_dicts, open_db=open_db)
            timings['total'] += open_dicts + open_db
            print('timing: ' + ' '.join(f'{key}={value:.3f}ms' for key, value in timings.items()), file=sys.stderr)
        return 0 if result.articles or result.online else 1
    except Exception as exc:
        print(f'внутренняя ошибка: {type(exc).__name__}', file=sys.stderr)
        return 1
    finally:
        if conn is not None:
            conn.close()
        if dictionaries is not None:
            dictionaries.close()


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    sys.exit(main())
