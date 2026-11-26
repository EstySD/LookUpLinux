"""Bounded read-only diagnostics; no history, capture, clipboard or network."""
from dataclasses import dataclass
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys

from lookup import config,dicts,platform,lifecycle,session

DICTIONARY_TIMEOUT=8
_application=None
_REASONS={'corrupt':'повреждён','checksum':'повреждён (контрольная сумма)',
          'empty':'пустой','too_large':'слишком большой','missing_files':'не хватает файлов',
          'unsupported':'неподдерживаемый формат','encrypted_registration':'регистрационное шифрование не поддерживается',
          'unreadable':'не удалось прочитать'}


@dataclass(frozen=True)
class Diagnostic:
    code: str
    ok: bool
    message: str


def _probe(path,fmt):
    """Use pure reader internals; deliberately bypass cache-writing factories."""
    path=Path(path)
    if not stat.S_ISREG(path.stat().st_mode):raise dicts.DictError('unreadable')
    if fmt=='yomitan':
        from lookup.yomitan import open_yomitan
        reader=open_yomitan(path)
        try:return dict(entries=sum(len(rows) for rows in reader.entries.values()),skipped=0)
        finally:reader.close()
    if fmt=='stardict':
        from lookup.stardict import open_stardict
        reader=open_stardict(path)
        try:return dict(entries=reader.entry_count,skipped=reader.skipped_entries)
        finally:reader.close()
    if fmt=='mdx':
        from lookup import mdx
        with path.open('rb') as stream:
            size=os.fstat(stream.fileno()).st_size
            payload=mdx._build_index(stream,size,mdx._read_header(stream,size))
        if not payload['entries']:raise dicts.DictError('empty')
        return dict(entries=payload['count'],skipped=payload['skipped'])
    if fmt=='dsl':
        from lookup import dsl
        mm,dz,size=dsl._open_source(path)
        try:
            if size>dsl.MAX_DSL_BYTES:raise dicts.DictError('too_large')
            if not size:raise dicts.DictError('empty')
            data=dz.read_all(dsl.MAX_DSL_BYTES) if dz is not None else mm
            encoding,bom=dsl._detect(bytes(data[:4]))
            payload=dsl._scan(data,bom,encoding)
            if not payload['entries']:raise dicts.DictError('empty')
            return dict(entries=len(payload['entries']),skipped=payload['skipped'])
        finally:dsl._close_quietly(mm,dz)
    raise dicts.DictError('unsupported')


def _scan_dictionaries(cfg,roots):
    found=dicts.discover(roots);enabled=dict(cfg.dictionaries);rows=[];usable=0
    for index,item in enumerate(found,1):
        code='dictionary_'+str(index);label=f'Словарь №{index} ({item.fmt})'
        if not enabled.get(item.id,True):
            rows.append(Diagnostic(code,True,label+': выключен в настройках.'));continue
        try:
            result=_probe(item.path,item.fmt);usable+=1
            rows.append(Diagnostic(code,True,label+f': записей {result["entries"]}, пропущено {result["skipped"]}.'))
        except Exception as error:
            reason=_REASONS.get(getattr(error,'reason',None),'повреждён или недоступен')
            rows.append(Diagnostic(code,False,label+': '+reason+'. Проверьте файлы или выключите словарь в настройках.'))
    identities={item.id for item in found}
    for index,(ident,on) in enumerate(cfg.dictionaries):
        if ident not in identities:
            rows.append(Diagnostic('configured_'+str(index),not on,
                'Включённый словарь из настроек не найден. Проверьте каталог словарей.' if on else
                'Выключенный словарь из настроек не найден; он не используется.'))
    if not usable:rows.append(Diagnostic('dictionary_available',False,'Нет доступного включённого словаря. Установите Mueller 7 или включите словарь в настройках.'))
    return rows


def _scan_main(argv):
    try:
        value=json.loads(argv[0]);cfg=config.Config(dictionaries=tuple((key,on) for key,on in value['dictionaries']))
        rows=_scan_dictionaries(cfg,[Path(path) for path in value['roots']])
        return json.dumps([row.__dict__ for row in rows],ensure_ascii=True)
    except Exception:
        return '[]'


def _dictionary_checks(cfg,roots):
    # Discovery and all untrusted decompression/index parsing share one finite
    # child deadline. The child cannot create index caches or open history.
    script=('import sys;sys.path.insert(0,sys.argv[1]);'
            'from lookup.doctor import _scan_main;sys.stdout.write(_scan_main(sys.argv[2:]))')
    payload=json.dumps(dict(dictionaries=cfg.dictionaries,roots=[str(root) for root in roots]))
    try:
        value=subprocess.run([sys.executable,'-I','-c',script,str(Path(__file__).resolve().parents[1]),payload],
            stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=DICTIONARY_TIMEOUT,check=False)
        if value.returncode or len(value.stdout)>131072:raise ValueError
        rows=json.loads(value.stdout)
        if not isinstance(rows,list) or not rows:raise ValueError
        return [Diagnostic(str(row['code']),row['ok'] is True,str(row['message'])) for row in rows]
    except (OSError,ValueError,KeyError,TypeError,subprocess.TimeoutExpired):
        return [Diagnostic('dictionaries',False,'Проверка словарей не завершилась за отведённое время или файлы недоступны. Проверьте словари по отдельности.')]


def _version_text(command,args,env=None):
    try:
        text=platform.run([command,*args],env=env,timeout=2,limit=4096).decode('utf-8','replace')
    except Exception:
        return None
    match=re.search(r'\b\d+(?:\.\d+){1,3}\b',text)
    return match.group(0) if match else (text.strip()[:80] or None)


def _steamos_row(info=None):
    info=session.os_release() if info is None else info
    version=session.steamos_version(info)
    if session.is_steamos(os.environ,info):
        return Diagnostic('steamos',True,'SteamOS '+version if version else 'SteamOS обнаружен.')
    return Diagnostic('steamos',True,'SteamOS не обнаружен (текущая система не SteamOS).')


def _dbus_ready():
    global _application
    try:
        from PyQt6.QtCore import QCoreApplication
        from PyQt6.QtDBus import QDBusConnection
        if QCoreApplication.instance() is None:_application=QCoreApplication(['lookup-doctor'])
        return QDBusConnection.sessionBus().isConnected()
    except Exception:
        return False


def _kde_plugin_rows(ready):
    return [Diagnostic('hotkey_capture',True,
                'Захват по событию хоткея KWin доступен; снимок не запрашивался.' if ready else
                'Плагин KWin не активен; используется fallback-захват ScreenShot2 после нажатия.'),
            Diagnostic('hotkey_capture_plugin',True,
                'Плагин KWin активен.' if ready else 'Плагин KWin не активен (опционально для SteamOS 3.9).')]


def _gaming_session_checks():
    info=session.os_release()
    rows=[Diagnostic('session',True,'Gaming Mode (gamescope) обнаружен.'),
          _steamos_row(info)]
    pids=session.find_gamescope_pids()
    rows.append(Diagnostic('gamescope',bool(pids),
        'gamescope запущен (PID '+str(pids[0])+').' if pids else
        'Процесс gamescope не найден. Запустите LookUp из Gaming Mode.'))
    try:env=platform.session_env()
    except Exception:env=None
    display=bool(env and (env.get('DISPLAY') or env.get('WAYLAND_DISPLAY')))
    rows.append(Diagnostic('display',display,
        'Дисплей gamescope доступен.' if display else 'Не найден DISPLAY/WAYLAND_DISPLAY gamescope.'))
    dbus=_dbus_ready()
    rows.append(Diagnostic('dbus',dbus,
        'Сеансовая шина D-Bus доступна.' if dbus else 'Сеансовая шина D-Bus недоступна.'))
    devices=session.input_devices()
    rows.append(Diagnostic('input',bool(devices),
        'Доступно устройств ввода: '+str(len(devices))+'.' if devices else
        'Нет доступных устройств ввода; проверьте права на /dev/input.'))
    version=_version_text('gamescope',['--version'],env)
    rows.append(Diagnostic('gamescope_version',True,
        'gamescope: '+version if version else 'Версия gamescope не определена.'))
    rows.append(Diagnostic('capture',False,'Захват Gaming Mode ещё не реализован (Phase 18).'))
    rows.append(Diagnostic('trigger',False,'Триггер Gaming Mode ещё не реализован (Phase 20).'))
    return rows


def _tool_checks():
    rows=[]
    mode=session.mode()
    is_gnome=mode==session.GNOME
    is_gaming=mode==session.GAMING
    try:env=platform.session_env()
    except Exception:env=None
    try:qt=importlib.util.find_spec('PyQt6.QtDBus') is not None
    except (ImportError,ValueError):qt=False
    rows.append(Diagnostic('pyqt6',qt,'Python/QtDBus доступны.' if qt else 'Установите python-pyqt6.'))
    for command,package in (() if (is_gnome or is_gaming) else (('kscreen-doctor','libkscreen'),('kbuildsycoca6','kservice'))):
        found=shutil.which(command) is not None
        rows.append(Diagnostic(command,found,command+' найден.' if found else 'Не найден '+command+'. Установите '+package+'.'))
    for command,args,package in (('kdotool',['--version'],'lookup-linux (или kdotool для запуска из исходников)'),
                                 ('wl-paste',['--version'],'wl-clipboard >= 2.3'),
                                 ('tesseract',['--list-langs'],'tesseract и tesseract-data-eng')):
        if (is_gnome or is_gaming) and command=='kdotool':continue
        try:
            output=platform.run([command,*args],env=env,timeout=2,limit=65536).decode('utf-8','replace')
            if command=='tesseract':ok='eng' in output.splitlines()
            elif command=='wl-paste':
                match=re.search(r'\b(\d+)\.(\d+)',output);ok=bool(match and tuple(map(int,match.groups()))>=((2,0) if (is_gnome or is_gaming) else (2,3)))
            else:
                match=re.search(r'\bkdotool\s+v?(\d+)\.(\d+)',output)
                ok=bool(match and tuple(map(int,match.groups()))>=(0,3))
        except Exception:ok=False
        rows.append(Diagnostic(command,ok,command+' доступен.' if ok else 'Не работает '+command+'. Установите или переустановите '+package+'.'))
    return rows


def _session_checks():
    global _application
    mode=session.mode()
    if mode==session.GAMING:return _gaming_session_checks()
    from . import gnome
    if mode==session.GNOME or gnome.active():
        try:
            state=gnome.state()
            binding=lifecycle.inspect_shortcut()
            return [Diagnostic('session',bool(state['monitors']),'GNOME Wayland: расширение LookUp Linux доступно; захват не выполнялся.'),
                    Diagnostic('shortcut',bool(binding.keys),'Хоткей GNOME: '+state['shortcut'])]
        except Exception:
            return [Diagnostic('session',False,'Недоступно расширение LookUp Linux для GNOME. Выполните python3 tools/install_ubuntu.py, затем выйдите из сеанса и войдите снова.')]
    before=dict(os.environ)
    try:
        os.environ.update(platform.session_env())
        from PyQt6.QtCore import QCoreApplication
        from PyQt6.QtDBus import QDBusConnection
        if QCoreApplication.instance() is None:_application=QCoreApplication(['lookup-doctor'])
        bus=QDBusConnection.sessionBus()
        interface=bus.interface()
        if interface is None:raise ValueError
        interface.setTimeout(1200)
        for service in ('org.kde.KWin','org.kde.KWin.ScreenShot2','org.kde.kglobalaccel'):
            reply=interface.isServiceRegistered(service)
            if not reply.isValid() or not reply.value():raise ValueError
        binding=lifecycle.inspect_shortcut()
        key=', '.join(lifecycle.key_text(key) for key in binding.keys)
        rows=[Diagnostic('session',True,'KDE Wayland, сеансовая шина и ScreenShot2 доступны; захват не выполнялся.'),
              Diagnostic('shortcut',bool(binding.keys),'Активный хоткей: '+key if key else 'Хоткей не назначен. Задайте его в настройках LookUp Linux или KDE.'),
              _steamos_row()]
        for code,command in (('plasma','plasmashell'),('kwin','kwin_wayland')):
            version=_version_text(command,['--version'])
            rows.append(Diagnostic(code,True,command+': '+version if version else command+': версия не определена.'))
        bridge=interface.isServiceRegistered('org.lookup.Capture')
        ready=bridge.isValid() and bridge.value()
        rows.extend(_kde_plugin_rows(bool(ready)))
        if lifecycle.is_installed():
            with lifecycle.INSTALLED_DESKTOP.open(encoding='utf-8') as stream:text=stream.read(65537)
            allowed=len(text)<=65536 and 'X-KDE-DBUS-Restricted-Interfaces=org.kde.KWin.ScreenShot2' in text
            rows.append(Diagnostic('capture_identity',allowed,'Файл разрешений установленного приложения найден.' if allowed else 'Повреждён файл запуска/разрешений. Переустановите lookup-linux.'))
        return rows
    except lifecycle.LifecycleError as error:
        return [Diagnostic('shortcut',False,'Хоткей не зарегистрирован. Запустите lookup --app и проверьте «Комбинации клавиш» KDE.'
                           if error.reason=='not_registered' else 'Недоступен реестр хоткеев KDE. Повторите проверку из сеанса Plasma.')]
    except Exception:
        return [Diagnostic('session',False,'Недоступен сеанс KDE Wayland или его службы. Запустите проверку из терминала Plasma; нужны kwin и kglobalacceld.')]
    finally:
        os.environ.clear();os.environ.update(before)


def check(*,roots=None):
    return tuple(_tool_checks()+_dictionary_checks(config.load(),dicts.dict_roots() if roots is None else roots)+_session_checks())


def run(stream,*,roots=None):
    """Write only to the diagnostic stream explicitly supplied by the CLI."""
    rows=check(roots=roots)
    for row in rows:stream.write(('OK' if row.ok else 'ОШИБКА')+' — '+row.message+'\n')
    return 0 if all(row.ok for row in rows) else 1
