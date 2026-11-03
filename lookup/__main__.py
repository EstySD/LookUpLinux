"""CLI: 0 means an answer, 1 no answer, 2 usage error.

User-facing output comes from this module. stderr contains numeric timings and fixed warnings with
exception type names, never exception messages or query text.
"""
import argparse
import math
import os
import re
import sqlite3
import sys
import time

from lookup import config, dicts, translate, ocr
from lookup.store import open_store, SchemaTooNewError, MigrationError
from lookup.normalize import normalize

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
OCR_REASONS = {
    'missing_pyqt6': 'не установлен пакет python-pyqt6',
    'missing_tesseract': 'не установлен пакет tesseract',
    'missing_eng': 'не установлен пакет tesseract-data-eng',
    'invalid_image': 'не удалось прочитать изображение',
    'invalid_point': 'точка должна находиться внутри изображения',
    'too_large': 'изображение слишком большое',
    'timeout': 'распознавание не ответило вовремя',
    'bad_output': 'распознавание вернуло непонятный ответ',
    'process_failed': 'не удалось выполнить распознавание',
}


def _image_point(value):
    try:
        x, y = (float(v) for v in value.split(','))
        if not math.isfinite(x) or not math.isfinite(y):
            raise ValueError
        return x, y
    except ValueError:
        raise argparse.ArgumentTypeError('нужна конечная точка X,Y') from None


def _print_timing(timings):
    from .timing import print_cli
    print_cli(timings)


def _context_span(text,context):
    """Manual context has an occurrence only when whole-token matching is unique."""
    key=normalize(text)
    if not key or not context:
        return None
    tokens=list(re.finditer(r'\S+',context))
    width=len(text.split())
    matches=[]
    for index in range(len(tokens)-width+1):
        start,end=tokens[index].start(),tokens[index+width-1].end()
        if normalize(context[start:end])==key:
            matches.append((start,end))
    return matches[0] if len(matches)==1 else None


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
    if result.context_meaning:
        lines.append('Значение в контексте: '+result.context_meaning)
    elif result.meaning_error:
        reasons={
            'disabled':'онлайн-перевод выключен',
            'no_context':'Недостаточно надёжного контекста для определения значения',
            'busy':'пока недоступно',
        }
        reason=reasons.get(result.meaning_error,ONLINE_REASONS.get(result.meaning_error,'не удалось надёжно определить значение'))
        lines.append('Значение в контексте недоступно: '+reason+'.')
    if result.saved:
        lines.append(f'Записано: искали {result.count} раз')
    if result.meaning_save_error:
        lines.append('Не удалось сохранить значение в контексте. Перевод доступен.')
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
    group.add_argument('--image')
    group.add_argument('--list-dicts', action='store_true')
    group.add_argument('--app', action='store_true')
    group.add_argument('--trigger', action='store_true')
    group.add_argument('--autostart', action='store_true')
    group.add_argument('--background', action='store_true', help='запустить в трее без главного окна')
    group.add_argument('--doctor', action='store_true')
    parser.add_argument('--context')
    parser.add_argument('--at', type=_image_point)
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--no-save', action='store_true')
    try:
        args = parser.parse_args(argv)
        if (args.app or args.trigger or args.autostart or args.background or args.doctor) and any((args.context is not None,args.at is not None,args.offline,args.no_save)):
            parser.error('--app, --trigger, --autostart и --doctor не принимают параметры разового поиска')
        if args.word is not None and len(args.word.split()) > translate.MAX_PHRASE_WORDS:
            parser.error('для предложения используйте --text')
        if bool(args.image) != (args.at is not None):
            parser.error('--image требует --at X,Y; --at используется только с --image')
        if args.image and args.context is not None:
            parser.error('для изображения контекст берётся из распознанной строки')
    except SystemExit as exc:
        return exc.code
    if args.doctor:
        from lookup.doctor import run
        return run(sys.stdout)
    if args.autostart and not config.load().autostart:
        return 0
    if args.app or args.trigger or args.autostart or args.background:
        try:
            from lookup.gui import run
            code=run(trigger=False,background=True) if args.autostart or args.background else run(trigger=args.trigger)
            if code:
                print('Не удалось запустить LookUp Linux. Повторите запуск.',file=sys.stderr)
            return code
        except ImportError:
            print('Не установлен пакет python-pyqt6.',file=sys.stderr)
            return 1
        except Exception:
            print('Не удалось запустить LookUp Linux в сеансе KDE Wayland.',file=sys.stderr)
            return 1
    dictionaries = None
    conn = None
    recognition = None
    try:
        if args.image:
            try:
                recognition = ocr.recognize_image(args.image, args.at)
            except ocr.OcrError as exc:
                print('OCR: ' + OCR_REASONS[exc.reason], file=sys.stderr)
                return 2 if exc.reason == 'invalid_point' else 1
            if recognition.selection is None:
                print('Не найдено.')
                _print_timing(recognition.timings)
                return 1
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
        query = args.word if args.word is not None else args.text
        context = args.context
        context_span=_context_span(query,context) if query is not None else None
        context_complete=context_span is not None
        compound = 0
        if recognition is not None:
            started = time.perf_counter()
            query = ocr.choose_query(recognition.selection, dictionaries)
            compound = (time.perf_counter() - started) * 1000
            selection=recognition.selection
            context = selection.context if selection.context is not None else selection.line
            context_span=(selection.span if query==selection.word else dict(selection.candidate_spans).get(query))
            context_complete=selection.context_complete
        started = time.perf_counter()
        try:
            conn = open_store()
        except SchemaTooNewError as exc:
            print(str(exc), file=sys.stderr)
        except (MigrationError, sqlite3.Error, OSError) as exc:
            print(f'База недоступна: {type(exc).__name__}', file=sys.stderr)
        open_db = (time.perf_counter() - started) * 1000
        result = translate.lookup(query,
                                  dictset=dictionaries, conn=conn, context=context,
                                  context_span=context_span,context_complete=context_complete,
                                  online=cfg.online and not args.offline,
                                  save=not args.no_save, clients=cfg.clients)
        if recognition is not None:
            print('Слово: ' + query)
            print('Строка: ' + context)
            if not context_complete:
                print('Показан доступный фрагмент; границы предложения не определены.')
        print(format_result(result))
        if context and not result.online_enabled:
            print('Предложение: перевод выключен.')
        if os.environ.get('LOOKUP_TIMING') == '1':
            timings = dict(result.timings, open_dicts=open_dicts, open_db=open_db)
            timings['total'] += open_dicts + open_db
            if recognition is not None:
                timings.update({k: v for k, v in recognition.timings.items() if k != 'total'})
                timings['compound'] = compound
                timings['total'] += recognition.timings['total'] + compound
            _print_timing(timings)
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
