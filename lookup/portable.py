"""Portable, root-free SteamOS install owned entirely by the desktop user.

Application code lives in ~/.local/lib/lookup; user data keeps using the normal
XDG paths (~/.local/share/lookup and ~/.config/lookup), so uninstall never
touches words, cards, dictionaries or settings.
"""
import os
from pathlib import Path
import shlex
import shutil
import tarfile

from . import config,lifecycle

MARKER='X-LookUpLinux-Owned=true'
RESTRICTED='X-KDE-DBUS-Restricted-Interfaces=org.kde.KWin.ScreenShot2'
TRIGGER='org.lookup.Linux.desktop'
AUTOSTART='org.lookup.Linux.autostart.desktop'
HOME_ENTRY='org.lookup.Linux.Home.desktop'
SERVICE='lookup-gaming.service'
OWNED_FILE='.lookup-owned'
MAX_FILE=64<<20
MAX_TOTAL=512<<20
MAX_ENTRIES=20000


class PortableError(ValueError):
    def __init__(self,reason):
        self.reason=reason if reason in ('unowned_file','unsafe_bundle','root_forbidden',
                                        'missing_source','file_failed','invalid_path') else 'file_failed'
        super().__init__(self.reason)


def _xdg(name,default):
    value=os.environ.get(name,'')
    path=Path(value) if value and Path(value).is_absolute() else Path(default)
    return path


def paths(home=None):
    home=Path(home or Path.home())
    if not home.is_absolute():raise PortableError('invalid_path')
    data=_xdg('XDG_DATA_HOME',home/'.local/share')
    settings=_xdg('XDG_CONFIG_HOME',home/'.config')
    binaries=_xdg('XDG_BIN_HOME',home/'.local/bin')
    return dict(app=home/'.local/lib/lookup',wrapper=binaries/'lookup',
                applications=data/'applications'/TRIGGER,
                autostart=settings/'autostart'/AUTOSTART,
                home_entry=data/'applications'/HOME_ENTRY,
                service=settings/'systemd/user'/SERVICE)


def desktop_text(executable,shortcut='Meta+Shift+D',kind='trigger'):
    if kind not in ('trigger','autostart','home'):raise PortableError('invalid_path')
    if not config._valid_scalar('shortcut',shortcut):raise PortableError('invalid_path')
    executable=Path(executable)
    if not executable.is_absolute() or any(c in str(executable) for c in '\r\n\x00'):
        raise PortableError('invalid_path')
    command=lifecycle._quote(executable)
    text=('[Desktop Entry]\nType=Application\nName=LookUp Linux\n'+
          'Comment=LookUp Linux portable SteamOS launcher\n'+MARKER+'\n'+
          'Exec='+command+' ')
    if kind=='trigger':
        text+='--trigger\nNoDisplay=true\nStartupNotify=true\nX-KDE-Shortcuts='+shortcut.replace('\\','\\\\')+'\n'
        text+=RESTRICTED+'\n'
    elif kind=='autostart':
        text+='--autostart\nTryExec='+lifecycle._entry_value(executable)+'\n'
        text+='StartupNotify=false\nOnlyShowIn=KDE;\n'
    else:
        text+='--app\nStartupNotify=true\nCategories=Education;Languages;\n'
    return text+'Icon=accessories-dictionary\nTerminal=false\n'


def service_text(home=None):
    wrapper=paths(home)['wrapper']
    return ('[Unit]\nDescription=LookUp Linux Gaming Mode daemon\n'
            '# '+MARKER+'\n'
            '[Service]\nType=simple\nExecStart='+lifecycle._quote(wrapper)+' --background\n'
            'Restart=on-failure\nRestartSec=2\n'
            '[Install]\nWantedBy=default.target\n')


def wrapper_text(home=None):
    root=paths(home)['app']
    return ('#!/bin/sh\n# '+MARKER+'\n'
            'ROOT='+shlex.quote(str(root))+'\n'
            'if [ -d "$ROOT/runtime/bin" ]; then PATH="$ROOT/runtime/bin:$PATH"; export PATH; fi\n'
            'if [ -d "$ROOT/runtime/lib" ]; then LD_LIBRARY_PATH="$ROOT/runtime/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"; export LD_LIBRARY_PATH; fi\n'
            'if [ -d "$ROOT/runtime/share/tessdata" ]; then TESSDATA_PREFIX="$ROOT/runtime/share/tessdata"; export TESSDATA_PREFIX; fi\n'
            'PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"; export PYTHONPATH\n'
            'LOOKUP_PORTABLE=1; export LOOKUP_PORTABLE\n'
            'if [ -x "$ROOT/runtime/bin/python" ]; then exec "$ROOT/runtime/bin/python" -m lookup "$@"; fi\n'
            'exec python3 -m lookup "$@"\n')


def _read_owned(path):
    if path.is_symlink():raise PortableError('unowned_file')
    try:
        raw=path.read_bytes()
    except FileNotFoundError:
        return None
    except OSError:
        raise PortableError('file_failed') from None
    if len(raw)>65536:raise PortableError('unowned_file')
    try:text=raw.decode('utf-8')
    except UnicodeError:raise PortableError('unowned_file') from None
    return text


def _owned_text(path):
    text=_read_owned(path)
    if text is not None and MARKER not in text.splitlines():raise PortableError('unowned_file')
    return text


def _owned_script(path):
    text=_read_owned(path)
    if text is not None and MARKER not in text:raise PortableError('unowned_file')
    return text


def _owned_app(path):
    marker=path/OWNED_FILE
    if path.is_symlink() or not path.is_dir() or marker.is_symlink() or not marker.is_file():
        return None
    try:
        text=marker.read_text(encoding='utf-8')
    except OSError:
        return None
    return text if MARKER in text.splitlines() else None


def _write(path,text,mode=0o644):
    try:
        path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        path.write_text(text,encoding='utf-8',newline='\n')
        path.chmod(mode)
    except OSError:
        raise PortableError('file_failed') from None


def extract_bundle(bundle,target):
    """Extract a bounded tar.gz into target without symlinks or path escapes."""
    target=Path(target)
    if target.exists() and (target.is_symlink() or not target.is_dir() or any(target.iterdir())):
        raise PortableError('unowned_file')
    total=0;count=0
    try:
        with tarfile.open(bundle,'r:gz') as archive:
            members=archive.getmembers()
            for member in members:
                name=Path(member.name)
                if (member.issym() or member.islnk() or name.is_absolute() or
                        '..' in name.parts or not (member.isfile() or member.isdir())):
                    raise PortableError('unsafe_bundle')
                count+=1;total+=member.size
                if count>MAX_ENTRIES or total>MAX_TOTAL or member.size>MAX_FILE:
                    raise PortableError('unsafe_bundle')
            target.mkdir(parents=True,exist_ok=True)
            for member in members:
                destination=(target/member.name).resolve()
                if not destination.is_relative_to(target.resolve()):
                    raise PortableError('unsafe_bundle')
                if member.isdir():
                    destination.mkdir(parents=True,exist_ok=True)
                    continue
                destination.parent.mkdir(parents=True,exist_ok=True)
                source=archive.extractfile(member)
                if source is None:raise PortableError('unsafe_bundle')
                with source,destination.open('wb') as output:
                    shutil.copyfileobj(source,output,length=MAX_FILE+1)
                if destination.stat().st_size>MAX_FILE:raise PortableError('unsafe_bundle')
                destination.chmod(0o644)
    except (tarfile.TarError,OSError):
        raise PortableError('unsafe_bundle') from None
    return count


def copy_source(source,target):
    source=Path(source)
    if source.is_symlink() or not (source/'lookup').is_dir():raise PortableError('missing_source')
    target.mkdir(parents=True,exist_ok=True)
    ignore=shutil.ignore_patterns('__pycache__','*.pyc','.pytest_cache')
    try:
        shutil.copytree(source/'lookup',target/'lookup',ignore=ignore,dirs_exist_ok=True,symlinks=False)
        runtime=source/'runtime'
        if runtime.is_dir():
            shutil.copytree(runtime,target/'runtime',ignore=ignore,dirs_exist_ok=True,symlinks=False)
    except OSError:
        raise PortableError('file_failed') from None


def install(*,source=None,bundle=None,home=None,shortcut='Meta+Shift+D'):
    if hasattr(os,'geteuid') and os.geteuid()==0:raise PortableError('root_forbidden')
    if bool(source)==bool(bundle):raise PortableError('missing_source')
    location=paths(home)
    app=location['app']
    if app.exists() and _owned_app(app) is None:raise PortableError('unowned_file')
    if source is None and (not Path(bundle).is_file()):raise PortableError('missing_source')
    entries=(desktop_text(location['wrapper'],shortcut,'trigger'),
             desktop_text(location['wrapper'],shortcut,'autostart'),
             desktop_text(location['wrapper'],shortcut,'home'))
    existing={key:_owned_text(location[key]) for key in ('applications','autostart','home_entry')}
    existing['wrapper']=_owned_script(location['wrapper'])
    existing['service']=_owned_script(location['service'])
    temporary=app.parent/('.lookup-install-'+str(os.getpid()))
    if temporary.exists():raise PortableError('file_failed')
    try:
        temporary.mkdir(parents=True)
        if bundle is not None:extract_bundle(bundle,temporary)
        else:copy_source(source,temporary)
        (temporary/OWNED_FILE).write_text(MARKER+'\n',encoding='utf-8')
        if app.exists():shutil.rmtree(app)
        temporary.replace(app)
    except OSError:
        raise PortableError('file_failed') from None
    finally:
        if temporary.exists():
            shutil.rmtree(temporary,ignore_errors=True)
    for key,text in zip(('applications','autostart','home_entry'),entries):
        path=location[key]
        if path.is_symlink():raise PortableError('unowned_file')
        _write(path,text)
    _write(location['wrapper'],wrapper_text(home),0o755)
    _write(location['service'],service_text(home))
    refresh()
    return location


def refresh():
    from . import platform
    try:platform.run(['kbuildsycoca6'],timeout=3,limit=4096)
    except platform.PlatformError:pass


def uninstall(*,home=None):
    location=paths(home)
    if _owned_app(location['app']) is None:raise PortableError('unowned_file')
    for key,path in location.items():
        if key!='app':(_owned_script if key in ('wrapper','service') else _owned_text)(path)
    for key,path in location.items():
        if key=='app':
            shutil.rmtree(path,ignore_errors=True)
        else:
            try:path.unlink()
            except FileNotFoundError:pass
            except OSError:raise PortableError('file_failed') from None
    return location


def status(*,home=None):
    location=paths(home)
    result={}
    for key,path in location.items():
        try:
            owned=(_owned_app(path) if key=='app' else
                   (_owned_script if key in ('wrapper','service') else _owned_text)(path))
        except PortableError:owned=None
        result[key]=owned is not None
    return result
