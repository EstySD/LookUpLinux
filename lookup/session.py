"""Session detection and the portable SteamOS Gaming Mode environment.

The module is deliberately stdlib-only: ``platform`` imports it, so importing
``platform`` from here would create a cycle.  It never reads query text,
history, screenshots or the clipboard.
"""
import os
from pathlib import Path
import re

KDE='kde'
GNOME='gnome'
GAMING='gaming'
UNKNOWN='unknown'

_GAMING_KEYS=('XDG_CURRENT_DESKTOP','XDG_SESSION_DESKTOP','DESKTOP_SESSION')
_GAMESCOPE_KEYS=frozenset((
    'DISPLAY','XAUTHORITY','WAYLAND_DISPLAY','XDG_RUNTIME_DIR','XDG_SESSION_TYPE',
    'DBUS_SESSION_BUS_ADDRESS','GAMESCOPE_WAYLAND_DISPLAY',
))
_KDE_ONLY=('KDE_SESSION_VERSION','KDE_FULL_SESSION','KDE_SESSION_UID',
           'QT_QPA_PLATFORMTHEME','XDG_ACTIVATION_TOKEN','DESKTOP_STARTUP_ID')
_MAX_VALUE=65536


def _parts(env,key):
    return [part.strip().lower() for part in env.get(key,'').replace(',',':').split(':') if part.strip()]


def is_gaming(env=None):
    env=os.environ if env is None else env
    if any(key.startswith(('GAMESCOPE_','STEAM_GAMESCOPE_')) for key in env):
        return True
    return any(any('gamescope' in part for part in _parts(env,key)) for key in _GAMING_KEYS)


def _is_gnome(env):
    parts=set(_parts(env,'XDG_CURRENT_DESKTOP'))
    return 'gnome' in parts and 'kde' not in parts


def _is_kde(env):
    if env.get('KDE_SESSION_VERSION')=='6':return True
    return any(part=='kde' or part=='plasma' or part.startswith(('kde-','plasma-'))
               for part in _parts(env,'XDG_CURRENT_DESKTOP'))


def mode(env=None):
    env=os.environ if env is None else env
    if is_gaming(env):return GAMING
    if _is_gnome(env):return GNOME
    if _is_kde(env):return KDE
    return UNKNOWN


def os_release(path='/etc/os-release'):
    try:
        text=Path(path).read_text(encoding='utf-8',errors='replace')
    except OSError:
        return {}
    result={}
    for line in text.splitlines():
        line=line.strip()
        if not line or line.startswith('#') or '=' not in line:continue
        key,value=line.split('=',1)
        if not re.fullmatch(r'[A-Z0-9_]+',key):continue
        if len(value)>=2 and value[0]==value[-1] and value[0] in '"\'':
            value=value[1:-1]
        result[key]=value[:256]
    return result


def is_steamos(env=None,info=None):
    env=os.environ if env is None else env
    info=os_release() if info is None else info
    if info.get('ID','').lower()=='steamos':return True
    if 'steamos' in info.get('ID_LIKE','').lower().split():return True
    return env.get('SteamDeck')=='1'


def steamos_version(info=None):
    info=os_release() if info is None else info
    return info.get('VERSION_ID') or info.get('BUILD_ID') or ''


def parse_environ(data):
    if isinstance(data,bytes):
        data=data.decode('utf-8','surrogateescape')
    result={}
    for item in data.split('\0'):
        if not item or '=' not in item:continue
        key,value=item.split('=',1)
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',key):continue
        if len(value)>_MAX_VALUE:continue
        result[key]=value
    return result


def find_gamescope_pids(root='/proc',uid=None):
    root=Path(root)
    if uid is None and hasattr(os,'getuid'):uid=os.getuid()
    result=[]
    try:
        entries=sorted(root.iterdir())
    except OSError:
        return ()
    for entry in entries:
        if not entry.name.isdigit():continue
        try:
            if uid is not None and entry.stat().st_uid!=uid:continue
            comm=(entry/'comm').read_text(encoding='ascii',errors='replace').strip()
        except OSError:
            continue
        if comm in ('gamescope','gamescope-wl') or comm.startswith('gamescope'):
            result.append(int(entry.name))
    return tuple(sorted(result))


def gamescope_env(root='/proc',pids=None):
    pids=find_gamescope_pids(root) if pids is None else tuple(pids)
    for pid in pids[:8]:
        if type(pid) is not int or pid<=0:continue
        try:
            with (Path(root)/str(pid)/'environ').open('rb') as stream:
                data=stream.read(262144)
        except OSError:
            continue
        env=parse_environ(data)
        if env.get('DISPLAY') or env.get('WAYLAND_DISPLAY') or env.get('GAMESCOPE_WAYLAND_DISPLAY'):
            return env
    return {}


def _copy_value(value):
    return isinstance(value,str) and value and len(value)<=4096


def build_gaming_env(base,gamescope,uid=None,runtime=None):
    """Return a sanitized gamescope environment without KDE session markers."""
    env=dict(base)
    for key in _KDE_ONLY:
        env.pop(key,None)
    for key,value in gamescope.items():
        if (key in _GAMESCOPE_KEYS or key.startswith(('GAMESCOPE_','STEAM_GAMESCOPE_'))) and _copy_value(value):
            env[key]=value
    env['XDG_CURRENT_DESKTOP']='gamescope'
    env['XDG_SESSION_DESKTOP']='gamescope'
    env['DESKTOP_SESSION']='gamescope'
    if uid is None and hasattr(os,'getuid'):uid=os.getuid()
    if uid is not None:
        runtime=runtime or ('/run/user/'+str(uid))
        env.setdefault('XDG_RUNTIME_DIR',runtime)
        env.setdefault('DBUS_SESSION_BUS_ADDRESS','unix:path='+runtime+'/bus')
    env.setdefault('XDG_SESSION_TYPE','wayland')
    if env.get('DISPLAY'):
        env['QT_QPA_PLATFORM']='xcb'
    elif env.get('WAYLAND_DISPLAY'):
        env['QT_QPA_PLATFORM']='wayland'
    else:
        env.pop('QT_QPA_PLATFORM',None)
    return env


def gaming_session_env(env=None,root='/proc',uid=None,runtime=None):
    base=dict(os.environ if env is None else env)
    return build_gaming_env(base,gamescope_env(root),uid=uid,runtime=runtime)


def input_devices(root='/dev/input'):
    try:
        entries=sorted(Path(root).iterdir())
    except OSError:
        return ()
    result=[]
    for entry in entries:
        if not entry.name.startswith('event'):continue
        try:
            if not os.access(entry,os.R_OK):continue
        except OSError:
            continue
        result.append(entry.name)
    return tuple(result)


def report(env=None):
    """Sanitized, read-only data for tools/check_steamos.py."""
    env=dict(os.environ if env is None else env)
    info=os_release()
    return {
        'mode':mode(env),
        'steamos':is_steamos(env,info),
        'steamos_version':steamos_version(info),
        'os_release':{key:info.get(key) for key in ('ID','ID_LIKE','VERSION_ID','BUILD_ID','PRETTY_NAME')},
        'desktop':(env.get('XDG_CURRENT_DESKTOP') or '')[:128],
        'session_desktop':(env.get('XDG_SESSION_DESKTOP') or '')[:128],
        'display':{
            'DISPLAY':bool(env.get('DISPLAY')),
            'WAYLAND_DISPLAY':bool(env.get('WAYLAND_DISPLAY')),
            'XAUTHORITY':bool(env.get('XAUTHORITY')),
        },
        'gamescope_pids':list(find_gamescope_pids()),
        'input_devices':list(input_devices()),
    }
