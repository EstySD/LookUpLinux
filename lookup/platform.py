"""Small, bounded KDE session probes. Importing this module needs only stdlib."""
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import re
import subprocess
import threading
import time


class PlatformError(Exception):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


def run(argv, env=None, timeout=2, limit=1 << 20):
    """Bound both a child's lifetime and bytes retained from stdout."""
    try:
        child = subprocess.Popen(argv, env=env, stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL, shell=False)
    except FileNotFoundError:
        raise PlatformError('missing_command') from None
    except OSError:
        raise PlatformError('process_failed') from None
    deadline = time.monotonic()+timeout
    chunks = []
    def read():
        try:
            chunks.append(child.stdout.read(limit + 1))
        except OSError:
            pass
    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    try:
        reader.join(timeout)
        if reader.is_alive():
            raise PlatformError('timeout')
        data = chunks[0] if chunks else b''
        if len(data) > limit:
            raise PlatformError('too_large')
        try:
            code = child.wait(timeout=max(.001, deadline-time.monotonic()))
        except subprocess.TimeoutExpired:
            raise PlatformError('timeout') from None
        if code:
            raise PlatformError('process_failed')
        return data
    finally:
        if child.poll() is None:
            child.kill()
        child.wait()
        reader.join(1)
        child.stdout.close()


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
               KDE_SESSION_VERSION='6', XDG_SESSION_TYPE='wayland', QT_QPA_PLATFORM='wayland')
    env.pop('XDG_ACTIVATION_TOKEN', None)
    env.pop('DESKTOP_STARTUP_ID', None)
    return env


def cursor_position(env):
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


def read_primary(env):
    try:
        return run(['wl-paste', '--primary', '--no-newline'], env, timeout=.5, limit=65536).decode('utf-8') or None
    except (PlatformError, UnicodeError):
        return None
