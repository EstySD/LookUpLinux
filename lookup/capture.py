"""Bounded screenshot transports; Qt is loaded only at capture time."""
from dataclasses import dataclass
import math
import os
from pathlib import Path
import select
import tempfile
import threading
import time

from .platform import PlatformError, Monitor, run

MAX_RAW = 256 << 20
MAX_PNG = 64 << 20


@dataclass(frozen=True)
class Capture:
    png: bytes
    width: int
    height: int
    backend: str
    elapsed_ms: float


@dataclass(frozen=True)
class HotkeySnapshot:
    point: tuple
    monitor: Monitor
    available: tuple
    metadata: dict
    pixels: bytes
    input_ns: int
    capture_ns: int

    def image(self):
        image=raw_image(self.metadata,self.pixels)
        return Capture(_encode(image),image.width(),image.height(),'kwin-hotkey',self.metadata['capture_ms'])


def take_hotkey(env):
    """Consume the compositor's one-shot, memory-only key-event snapshot."""
    if os.name!='posix' or env.get('KDE_SESSION_VERSION')!='6':
        return None
    from PyQt6.QtDBus import QDBusConnection,QDBusMessage,QDBus,QDBusUnixFileDescriptor
    bus=QDBusConnection.sessionBus()
    message=QDBusMessage.createMethodCall('org.lookup.Capture','/org/lookup/Capture','org.lookup.Capture','Take')
    reply=bus.call(message,QDBus.CallMode.Block,500)
    if reply.type()==QDBusMessage.MessageType.ErrorMessage:
        return None
    values=reply.arguments()
    if len(values)!=1 or not isinstance(values[0],dict):
        raise PlatformError('bad_image')
    metadata=values[0]
    if not metadata:
        return None
    if metadata.get('status')=='consumed':
        raise PlatformError('hotkey_consumed')
    if 'error' in metadata:
        raise PlatformError('capture_failed')
    _,_,_,length=raw_layout(metadata)
    geometry=tuple(metadata.get(k) for k in ('x','y','logical_width','logical_height','scale'))
    point=tuple(metadata.get(k) for k in ('cursor_x','cursor_y'))
    available=tuple(metadata.get(k) for k in ('available_x','available_y','available_width','available_height'))
    numbers=geometry+point+available+(metadata.get('capture_ms'),)
    now=time.monotonic_ns()
    stamps=tuple(metadata.get(k) for k in ('input_ns','capture_ns'))
    descriptor=metadata.get('fd')
    if (any(type(v) not in (int,float) or not math.isfinite(v) for v in numbers)
            or min(geometry[2:])<=0 or min(available[2:])<=0 or metadata['capture_ms']<0
            or any(type(v) is not int for v in stamps) or not 0<stamps[0]<=stamps[1]<=now+1_000_000_000
            or now-stamps[0]>5_000_000_000 or not isinstance(metadata.get('name'),str)
            or not 0<len(metadata['name'])<=256 or not isinstance(descriptor,QDBusUnixFileDescriptor)
            or not descriptor.isValid()):
        raise PlatformError('bad_image')
    fd=descriptor.fileDescriptor()
    try:
        if os.fstat(fd).st_size!=length:
            raise PlatformError('bad_image')
        pixels=os.pread(fd,length,0)
        if len(pixels)!=length:
            raise PlatformError('bad_image')
    except OSError:
        raise PlatformError('bad_image') from None
    available=tuple(round(value) for value in available)
    if min(available[2:])<=0:
        raise PlatformError('bad_image')
    return HotkeySnapshot(point,Monitor(metadata['name'],*geometry),available,
                          {k:v for k,v in metadata.items() if k!='fd'},pixels,*stamps)


def enable_hotkey_bridge(env):
    if os.name!='posix' or env.get('KDE_SESSION_VERSION')!='6':
        return False
    from PyQt6.QtDBus import QDBusConnection,QDBusMessage,QDBus
    message=QDBusMessage.createMethodCall('org.kde.KWin','/Plugins','org.kde.KWin.Plugins','LoadPlugin')
    message.setArguments(['lookupcapture'])
    reply=QDBusConnection.sessionBus().call(message,QDBus.CallMode.Block,1000)
    return reply.type()!=QDBusMessage.MessageType.ErrorMessage


def raw_layout(metadata):
    """Validate KWin's native QImage layout before constructing any image."""
    # Native 32bpp and byte-ordered RGBX/RGBA8888; QImage owns channel decoding.
    if metadata.get('type') != 'raw' or metadata.get('format') not in (4, 5, 6, 16, 17, 18):
        raise PlatformError('bad_image')
    w, h, stride = (metadata.get(k) for k in ('width', 'height', 'stride'))
    scale = metadata.get('scale', 1)
    if (any(type(v) is not int or v <= 0 for v in (w, h, stride)) or
            not isinstance(scale, (int, float)) or isinstance(scale, bool) or
            not math.isfinite(scale) or scale <= 0):
        raise PlatformError('bad_image')
    if w > 16384 or h > 16384 or w*h > 64_000_000 or stride < w*4 or stride*h > MAX_RAW:
        raise PlatformError('bad_image')
    return w, h, stride, stride*h


def _png_image(png):
    from PyQt6.QtCore import QBuffer, QIODevice
    from PyQt6.QtGui import QImageReader
    if len(png) > MAX_PNG:
        raise PlatformError('too_large')
    buf = QBuffer()
    buf.setData(png)
    buf.open(QIODevice.OpenModeFlag.ReadOnly)
    reader = QImageReader(buf)
    size = reader.size()
    if min(size.width(), size.height()) <= 0 or max(size.width(), size.height()) > 16384 or size.width()*size.height() > 64_000_000:
        raise PlatformError('bad_image')
    image = reader.read()
    if image.isNull():
        raise PlatformError('bad_image')
    return image


def _encode(image):
    from PyQt6.QtCore import QBuffer, QIODevice
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buf, 'PNG'):
        raise PlatformError('bad_image')
    png = bytes(buf.data())
    if len(png) > MAX_PNG:
        raise PlatformError('too_large')
    return png


def raw_image(metadata, data):
    from PyQt6.QtGui import QImage
    w, h, stride, length = raw_layout(metadata)
    if len(data) != length:
        raise PlatformError('bad_image')
    image = QImage(bytes(data), w, h, stride, QImage.Format(metadata['format'])).copy()
    if image.isNull():
        raise PlatformError('bad_image')
    return image


def _screenshot2(name):
    from PyQt6.QtDBus import QDBusConnection, QDBusMessage, QDBus, QDBusUnixFileDescriptor
    from PyQt6.QtGui import QImage
    # Initialize QtDBus metatypes before PyQt converts the QVariantMap/UnixFD.
    bus = QDBusConnection.sessionBus()
    read_fd, write_fd = os.pipe()
    data = bytearray()
    errors = []
    stop = threading.Event()
    deadline = time.monotonic()+3
    def drain():
        try:
            while not stop.is_set() and time.monotonic() < deadline:
                ready, _, _ = select.select([read_fd], [], [], .05)
                if not ready:
                    continue
                chunk = os.read(read_fd, min(65536, MAX_RAW+1-len(data)))
                if not chunk:
                    return
                data.extend(chunk)
                if len(data) > MAX_RAW:
                    errors.append('too_large')
                    return
            errors.append('timeout')
        except OSError:
            errors.append('process_failed')
    reader = threading.Thread(target=drain, daemon=True)
    descriptor = None
    reader.start()
    try:
        descriptor = QDBusUnixFileDescriptor(write_fd)
        os.close(write_fd)
        write_fd = -1
        message = QDBusMessage.createMethodCall('org.kde.KWin', '/org/kde/KWin/ScreenShot2',
                                               'org.kde.KWin.ScreenShot2', 'CaptureScreen')
        message.setArguments([name, {'include-cursor': False, 'native-resolution': True,
                                    'hide-caller-windows': False}, descriptor])
        reply = bus.call(message, QDBus.CallMode.Block, 2000)
        # Message retains the duplicated write FD until it is destroyed too.
        del message
        descriptor = None
        if reply.type() == QDBusMessage.MessageType.ErrorMessage:
            raise PlatformError('capture_failed')
        values = reply.arguments()
        if len(values) != 1 or not isinstance(values[0], dict):
            raise PlatformError('bad_image')
        metadata = values[0]
        w, h, stride, length = raw_layout(metadata)
        reader.join(max(0, deadline-time.monotonic()))
        if reader.is_alive() or errors:
            raise PlatformError(errors[0] if errors else 'timeout')
        if len(data) != length:
            raise PlatformError('bad_image')
        image = raw_image(metadata, data)
        return _encode(image), w, h
    finally:
        descriptor = None
        if write_fd >= 0:
            os.close(write_fd)
        stop.set()
        reader.join(.2)
        os.close(read_fd)


def capture_monitor(monitor, env, backend='screenshot2'):
    start = time.perf_counter()
    try:
        from . import gnome
        if backend=='screenshot2' and gnome.active(env):
            png,w,h=gnome.capture(monitor)
            backend='gnome'
        elif backend == 'spectacle':
            with tempfile.TemporaryDirectory(prefix='lookup-capture-') as folder:
                path = Path(folder) / 'frame.png'
                run(['spectacle', '-b', '-n', '-m', '-o', str(path)], env, timeout=3, limit=4096)
                with path.open('rb') as stream:
                    png = stream.read(MAX_PNG+1)
                image = _png_image(png)
                w, h = image.width(), image.height()
        elif backend == 'screenshot2':
            png, w, h = _screenshot2(monitor.name)
        else:
            raise PlatformError('unknown_backend')
    except ImportError:
        raise PlatformError('missing_pyqt6') from None
    except OSError:
        raise PlatformError('capture_failed') from None
    return Capture(png, w, h, backend, (time.perf_counter()-start)*1000)
