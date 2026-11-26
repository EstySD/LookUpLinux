"""Temporary gamescope frame capture for the experimental Gaming Mode.

Gamescope writes a PNG when it receives SIGUSR2. The file is consumed and
unlinked immediately: no screenshot is kept in permanent storage. A bounded
PipeWire/GStreamer fallback covers setups without that signal handler.
"""
from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import signal
import time

from . import session
from .platform import PlatformError,Monitor,run

MAX_WAIT=2.5
POLL=.05
SIGUSR2=getattr(signal,'SIGUSR2',12)


@dataclass(frozen=True)
class GamescopeSnapshot:
    point: tuple
    monitor: Monitor
    available: tuple
    png: bytes
    width: int
    height: int
    elapsed_ms: float
    backend: str = 'gamescope'

    def image(self):
        from .capture import Capture
        return Capture(self.png,self.width,self.height,self.backend,self.elapsed_ms)


def gamescope_capture_ready(env=None):
    if session.find_gamescope_pids():return True
    return shutil.which('gst-launch-1.0') is not None


def _candidate_dirs(pid,env):
    result=[Path('/tmp')]
    runtime=env.get('XDG_RUNTIME_DIR','')
    if runtime and Path(runtime).is_absolute():result.append(Path(runtime))
    try:
        cwd=Path(os.readlink('/proc/'+str(pid)+'/cwd'))
        if cwd.is_absolute():result.append(cwd)
    except OSError:
        pass
    home=env.get('HOME','')
    if home and Path(home).is_absolute():result.append(Path(home))
    seen=[]
    for path in result:
        if path in seen or not path.is_dir():continue
        seen.append(path)
    return seen[:8]


def _existing(directories):
    result=set()
    for directory in directories:
        try:result.update(directory.glob('gamescope_*.png'))
        except OSError:continue
    return result


def _png_size(data):
    from .capture import _png_image
    image=_png_image(data)
    return image.width(),image.height()


def _wait_for_frame(directories,before,deadline):
    while time.monotonic()<deadline:
        found=[]
        for directory in directories:
            try:candidates=directory.glob('gamescope_*.png')
            except OSError:continue
            for path in candidates:
                if path in before or not path.is_file():continue
                try:size=path.stat().st_size
                except OSError:continue
                if size<=0 or size>64<<20:continue
                found.append((path,size))
        for path,size in found[:4]:
            time.sleep(POLL)
            try:
                if not path.is_file() or path.stat().st_size!=size:continue
                data=path.read_bytes()
            except OSError:
                continue
            if len(data)!=size:continue
            return path,data
        time.sleep(POLL)
    return None,None


def capture_gamescope(env=None):
    """Capture one gamescope frame; the temporary PNG is always removed."""
    start=time.perf_counter()
    env=dict(os.environ if env is None else env)
    pids=session.find_gamescope_pids()
    if not pids:
        return _pipewire_capture(env,start)
    directories=_candidate_dirs(pids[0],env)
    before=_existing(directories)
    signalled=False
    for pid in pids[:4]:
        try:
            os.kill(pid,SIGUSR2)
            signalled=True
            break
        except (ProcessLookupError,PermissionError,OSError):
            continue
    if not signalled:raise PlatformError('capture_failed')
    path,data=_wait_for_frame(directories,before,time.monotonic()+MAX_WAIT)
    if path is None:
        return _pipewire_capture(env,start)
    try:
        width,height=_png_size(data)
    except PlatformError:
        raise
    finally:
        try:path.unlink(missing_ok=True)
        except OSError:pass
    monitor=Monitor('gamescope',0,0,width,height,1)
    return GamescopeSnapshot((width//2,height//2),monitor,(0,0,width,height),
                             data,width,height,(time.perf_counter()-start)*1000)


def _pipewire_capture(env,start):
    from .capture import MAX_PNG,_png_image
    try:
        data=run(['gst-launch-1.0','-q','pipewiresrc','num-buffers=1',
                  '!','videoconvert','!','pngenc','!','fdsink','fd=1'],
                 env=env,timeout=3,limit=MAX_PNG+1)
        image=_png_image(data)
    except (PlatformError,OSError):
        raise PlatformError('gaming_capture_unavailable') from None
    monitor=Monitor('pipewire',0,0,image.width(),image.height(),1)
    return GamescopeSnapshot((image.width()//2,image.height()//2),monitor,
                             (0,0,image.width(),image.height()),data,
                             image.width(),image.height(),(time.perf_counter()-start)*1000,
                             backend='pipewire')
