"""Bounded Wayland session probes; the optional GNOME bridge is loaded lazily."""
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import threading
import time

PRIVATE_KDOTOOL=Path('/usr/lib/lookup/kdotool')


def resolve_command(command):
    """The package owns a private helper; source runs keep the normal PATH."""
    if command=='kdotool' and PRIVATE_KDOTOOL.is_file():
        return str(PRIVATE_KDOTOOL)
    return command


class PlatformError(Exception):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


def run(argv, env=None, timeout=2, limit=1 << 20):
    """Bound both a child's lifetime and bytes retained from stdout."""
    if argv and argv[0]=='kdotool':argv=[resolve_command(argv[0]),*argv[1:]]
    try:
        child = subprocess.Popen(argv, env=env, stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL, shell=False, bufsize=0,
                                 start_new_session=os.name == 'posix',
                                 creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    except FileNotFoundError:
        raise PlatformError('missing_command') from None
    except OSError:
        raise PlatformError('process_failed') from None
    deadline = time.monotonic()+timeout
    data = bytearray()
    stop = threading.Event()
    def read():
        try:
            while not stop.is_set():
                chunk = os.read(child.stdout.fileno(), min(65536, limit+1-len(data)))
                if not chunk:
                    return
                data.extend(chunk)
                if len(data) > limit:
                    return
        except OSError:
            pass
    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    try:
        reader.join(timeout)
        if reader.is_alive():
            raise PlatformError('timeout')
        if len(data) > limit:
            raise PlatformError('too_large')
        try:
            code = child.wait(timeout=max(.001, deadline-time.monotonic()))
        except subprocess.TimeoutExpired:
            raise PlatformError('timeout') from None
        if code:
            raise PlatformError('process_failed')
        return bytes(data)
    finally:
        stop.set()
        if os.name == 'posix':
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        elif child.poll() is None or reader.is_alive():
            try:
                subprocess.run(['taskkill', '/PID', str(child.pid), '/T', '/F'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=1, creationflags=subprocess.CREATE_NO_WINDOW)
            except (OSError, subprocess.TimeoutExpired):
                pass
        if child.poll() is None:
            child.kill()
        child.wait()
        # Unbuffered FileIO has no BufferedReader lock held by a blocked read.
        child.stdout.close()
        reader.join(.2)


def _numbers(values):
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
           for v in values):
        raise PlatformError('invalid_geometry')


@dataclass(frozen=True)
class Monitor:
    name: str
    x: float
    y: float
    width: float
    height: float
    scale: float

    def __post_init__(self):
        _numbers((self.x, self.y, self.width, self.height, self.scale))
        if not self.name or self.width <= 0 or self.height <= 0 or self.scale <= 0:
            raise PlatformError('invalid_geometry')


def monitor_at(point, outputs):
    _numbers(point)
    x, y = point
    for output in outputs:
        if output.x <= x < output.x + output.width and output.y <= y < output.y + output.height:
            return output
    raise PlatformError('outside_monitor')


def image_point(point, monitor, pixel_size):
    monitor_at(point, (monitor,))
    _numbers(pixel_size)
    w, h = pixel_size
    if w <= 0 or h <= 0:
        raise PlatformError('invalid_geometry')
    return ((point[0]-monitor.x)*w/monitor.width, (point[1]-monitor.y)*h/monitor.height)


def popup_rect(point, size, available_rect, gap=12):
    _numbers((*point, *size, *available_rect, gap))
    ax, ay, aw, ah = available_rect
    if min(*size, aw, ah) <= 0 or gap < 0:
        raise PlatformError('invalid_geometry')
    w, h = min(size[0], aw), min(size[1], ah)
    x, y = point[0]+gap, point[1]+gap
    if x+w > ax+aw:
        x = point[0]-gap-w
    if y+h > ay+ah:
        y = point[1]-gap-h
    return tuple(round(v) for v in (max(ax, min(x, ax+aw-w)), max(ay, min(y, ay+ah-h)), w, h))


def available_rect(monitor, docks):
    """Reserve compositor dock edges, including floating-panel edge gaps."""
    left,top=monitor.x,monitor.y
    right,bottom=left+monitor.width,top+monitor.height
    for x,y,w,h in docks:
        _numbers((x,y,w,h))
        if w<=0 or h<=0 or x>=right or x+w<=left or y>=bottom or y+h<=top:continue
        if w>=h and h<monitor.height/3:
            if y<=monitor.y+max(16,h):top=max(top,y+h)
            elif y+h>=monitor.y+monitor.height-max(16,h):bottom=min(bottom,y)
        elif h>w and w<monitor.width/3:
            if x<=monitor.x+max(16,w):left=max(left,x+w)
            elif x+w>=monitor.x+monitor.width-max(16,w):right=min(right,x)
    left,top=math.ceil(left),math.ceil(top)
    right,bottom=math.floor(right),math.floor(bottom)
    if right<=left or bottom<=top:raise PlatformError('invalid_geometry')
    return left,top,right-left,bottom-top


def panel_rects(env):
    """Read only fixed Plasma dock metadata; never move or activate a panel."""
    from PyQt6.QtDBus import QDBusConnection,QDBusMessage,QDBus
    ids=run(['kdotool','search','--class','plasmashell'],env,timeout=1,limit=4096).decode('ascii').split()
    if len(ids)>16 or any(not re.fullmatch(r'\{[0-9a-fA-F-]{36}\}',value) for value in ids):
        raise PlatformError('bad_output')
    bus=QDBusConnection.sessionBus()
    result=[]
    for uuid in ids:
        message=QDBusMessage.createMethodCall('org.kde.KWin','/KWin','org.kde.KWin','getWindowInfo')
        message.setArguments([uuid])
        reply=bus.call(message,QDBus.CallMode.Block,150)
        if reply.type()==QDBusMessage.MessageType.ErrorMessage:raise PlatformError('monitor_failed')
        values=reply.arguments()
        info=values[0] if values else {}
        if info.get('resourceClass')=='plasmashell' and info.get('type')==2:
            rect=tuple(info.get(key) for key in ('x','y','width','height'))
            _numbers(rect);result.append(rect)
    return tuple(result)


def work_area(env,monitor):
    from . import gnome
    if gnome.active(env):
        for item in gnome.state()['monitors']:
            if item['name']==monitor.name:
                rect=tuple(item['available']);_numbers(rect)
                if len(rect)!=4 or min(rect[2:])<=0:raise PlatformError('invalid_geometry')
                return rect
        raise PlatformError('outside_monitor')
    return available_rect(monitor,panel_rects(env))


def session_env():
    if os.name != 'posix' or not hasattr(os, 'getuid'):
        raise PlatformError('unsupported_session')
    runtime = Path('/run/user') / str(os.getuid())
    sockets = sorted(p for p in runtime.glob('wayland-*') if not p.name.endswith('.lock') and p.is_socket())
    selected = os.environ.get('WAYLAND_DISPLAY')
    if selected and (runtime / selected).is_socket():
        display = selected
    elif len(sockets) == 1:
        display = sockets[0].name
    else:
        raise PlatformError('unsupported_session')
    env = dict(os.environ, XDG_RUNTIME_DIR=str(runtime), WAYLAND_DISPLAY=display,
               DBUS_SESSION_BUS_ADDRESS='unix:path=' + str(runtime / 'bus'),
               KDE_SESSION_VERSION='6', XDG_SESSION_TYPE='wayland', QT_QPA_PLATFORM='wayland',
               QT_QPA_PLATFORMTHEME='kde')
    env.pop('XDG_ACTIVATION_TOKEN', None)
    env.pop('DESKTOP_STARTUP_ID', None)
    from . import gnome
    if gnome.active(env):
        env.pop('KDE_SESSION_VERSION',None)
        env.pop('QT_QPA_PLATFORMTHEME',None)
    return env


def cursor_position(env):
    from . import gnome
    if gnome.active(env):
        point=tuple(gnome.state()['point']);_numbers(point)
        if len(point)!=2:raise PlatformError('bad_output')
        return point
    try:
        output = run(['kdotool', 'getmouselocation'], env, limit=1024).decode('ascii', 'strict')
    except UnicodeError:
        raise PlatformError('bad_output') from None
    match = re.fullmatch(r'x:(-?\d+) y:(-?\d+) screen:\d+ window:[\w{}-]+\s*', output)
    if not match:
        raise PlatformError('bad_output')
    return tuple(int(n) for n in match.groups())


def parse_monitors(data):
    try:
        result = []
        for output in json.loads(data)['outputs']:
            if not output['enabled'] or not output['connected']:
                continue
            mode = next(m for m in output['modes'] if m['id'] == output['currentModeId'])
            scale = output['scale']
            size = mode['size']
            w, h = size['width'], size['height']
            if output.get('rotation', 1) in (2, 8):
                w, h = h, w
            result.append(Monitor(output['name'], output['pos']['x'], output['pos']['y'],
                                  w/scale, h/scale, scale))
        if not result:
            raise ValueError()
        return tuple(result)
    except (ValueError, KeyError, TypeError, StopIteration, ZeroDivisionError):
        raise PlatformError('bad_output') from None


def monitors(env):
    from . import gnome
    if gnome.active(env):
        return tuple(Monitor(*(item[key] for key in ('name','x','y','width','height','scale')))
                     for item in gnome.state()['monitors'])
    return parse_monitors(run(['kscreen-doctor', '-j'], env))


def owned_window(env, pid):
    if type(pid) is not int or pid <= 0:
        raise PlatformError('invalid_owner')
    value = run(['kdotool', 'search', '--pid', str(pid)], env, limit=4096).decode('ascii').split()
    if not value or any(not re.fullmatch(r'\{?[0-9a-fA-F-]{36}\}?', s) for s in value):
        raise PlatformError('bad_output')
    return tuple(value)


def window_action(env, pid, uuid, action, *args):
    if uuid not in owned_window(env, pid) or action not in ('windowmove', 'windowactivate', 'windowraise', 'getwindowgeometry'):
        raise PlatformError('invalid_owner')
    if action == 'windowmove':
        if len(args) != 2 or any(type(v) is not int for v in args):
            raise PlatformError('invalid_geometry')
    elif args:
        raise PlatformError('invalid_geometry')
    return run(['kdotool', action, uuid, *map(str, args)], env, limit=4096)


def window_geometry(env, pid, uuid):
    text = window_action(env, pid, uuid, 'getwindowgeometry').decode('ascii')
    match = re.search(r'Position: (-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)\s+Geometry: (\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)\s*$', text)
    if not match:
        raise PlatformError('bad_output')
    return tuple(map(float, match.groups()))


def read_primary(env):
    try:
        return run(['wl-paste', '--primary', '--no-newline'], env, timeout=.5, limit=65536).decode('utf-8') or None
    except (PlatformError, UnicodeError):
        return None
