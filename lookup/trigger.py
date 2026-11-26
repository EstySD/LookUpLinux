"""Gaming Mode trigger: back-button chord via evdev, key fallback via Steam Input.

Hardware behavior is unverified: this module is deliberately small, testable and
fails closed when evdev or accessible input devices are unavailable.
"""
import os
import selectors
import threading
import time

from . import config

BACK_CHORD=(0x9e,0x9c)  # KEY_BACK + KEY_ENTER, remappable by Steam Input
WATCH_INTERVAL=.2


class ChordDetector:
    """One fire per chord press, with a bounded cooldown against repeats."""

    def __init__(self,codes=BACK_CHORD,*,window=.35,cooldown=.8):
        self.codes=frozenset(codes)
        self.window=window
        self.cooldown=cooldown
        self._down=set()
        self._first=None
        self._last=-cooldown

    def feed(self,code,value,now=None):
        now=time.monotonic() if now is None else now
        if value==1:
            self._down.add(code)
            if self._first is None:self._first=now
        elif value==0:
            self._down.discard(code)
            if not self._down:self._first=None
        else:
            return False
        if (self.codes and self.codes.issubset(self._down) and
                self._first is not None and now-self._first<=self.window and
                now-self._last>=self.cooldown):
            self._last=now
            return True
        return False


def evdev():
    try:
        import evdev as module
        return module
    except (ImportError,OSError):
        return None


def devices(root='/dev/input'):
    module=evdev()
    if module is None:return ()
    result=[]
    try:entries=sorted(os.listdir(root))
    except OSError:return ()
    for name in entries[:64]:
        if not name.startswith('event'):continue
        try:
            device=module.InputDevice(os.path.join(root,name))
        except (OSError,PermissionError):
            continue
        result.append(device)
    return tuple(result)


def gaming_trigger_ready():
    """Read-only readiness for diagnostics; never reads input events."""
    return config.load().gaming_trigger=='key' or bool(devices())


def watch(callback,*,root='/dev/input',codes=None,stop=None):
    """Watch evdev keys and call callback() on each accepted chord.

    Returns a stop function. A Steam Input key layout can call --trigger
    directly instead, so no evdev device is required for the fallback.
    """
    module=evdev()
    if module is None:return lambda:None
    found=devices(root)
    if not found:return lambda:None
    detector=ChordDetector(codes or BACK_CHORD)
    selector=selectors.DefaultSelector()
    for device in found:selector.register(device.fd,selectors.EVENT_READ,device)
    stopped=threading.Event() if stop is None else stop
    def run():
        try:
            while not stopped.is_set():
                for key,_ in selector.select(WATCH_INTERVAL):
                    device=key.data
                    try:events=device.read()
                    except OSError:continue
                    for event in events:
                        if getattr(event,'type',None)==getattr(module.ecodes,'EV_KEY',1) and detector.feed(event.code,event.value):
                            callback()
        finally:
            for device in found:
                try:device.close()
                except OSError:pass
            selector.close()
    thread=threading.Thread(target=run,name='lookup-gaming-trigger',daemon=True)
    thread.start()
    def finish():
        stopped.set()
        thread.join(1)
    return finish
