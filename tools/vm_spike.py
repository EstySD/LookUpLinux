"""Temporary, observable Plasma spike. No translations or user data storage."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import subprocess

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lookup import platform, capture, ocr

SERVICE = 'org.lookup.Linux.VMSpike'
FIXTURE = 'org.lookup.Linux.VMFixture'
INTERFACE = SERVICE
DESKTOP = 'org.lookup.Linux.VMSpike.desktop'
POPUP_TITLE = 'LookUp VM Spike Popup'


def valid_token(token):
    try:
        return isinstance(token, str) and len(token.encode('utf-8')) <= 4096 and '\x00' not in token
    except UnicodeError:
        return False


def desktop_text(python, script):
    def quote(value):
        value = str(value)
        if not Path(value).is_absolute() or any(c in value for c in '\r\n\x00'):
            raise ValueError('invalid desktop path')
        # Desktop Entry Exec quoting, including literal percent field-code escape.
        for char in ('\\', '"', '`', '$'):
            value = value.replace(char, '\\'+char)
        return '"' + value.replace('%', '%%') + '"'
    return ('[Desktop Entry]\nType=Application\nName=LookUp VM Spike\n'
            'Comment=Owned temporary LookUp platform experiment\n'
            f'Exec={quote(python)} {quote(script)} --trigger --controlled\n'
            'Icon=accessories-dictionary\nTerminal=false\nStartupNotify=true\n'
            'X-KDE-Shortcuts=Meta+Shift+D\n')


def pipeline(env, backend, controlled):
    start = time.perf_counter()
    point = platform.cursor_position(env)
    monitor = platform.monitor_at(point, platform.monitors(env))
    probed = time.perf_counter()
    frame = capture.capture_monitor(monitor, env, backend)
    physical = platform.image_point(point, monitor, (frame.width, frame.height))
    result = ocr.recognize_image(frame.png, physical)
    return dict(point=point, monitor=monitor.name, pixels=[frame.width, frame.height],
                probe_ms=(probed-start)*1000, capture_ms=frame.elapsed_ms,
                ocr_ms=result.timings['total'], total_ms=(time.perf_counter()-start)*1000,
                word='english' if controlled and result.selection and result.selection.word == 'english' else None,
                found=result.selection is not None)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--trigger', action='store_true')
    mode.add_argument('--status', action='store_true')
    mode.add_argument('--quit', action='store_true')
    mode.add_argument('--public-window', action='store_true')
    mode.add_argument('--owner-trigger', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--controlled', action='store_true')
    parser.add_argument('--backend', choices=('screenshot2', 'spectacle'), default='screenshot2')
    parser.add_argument('--fixture-status', action='store_true')
    args = parser.parse_args(argv)
    token = os.environ.pop('XDG_ACTIVATION_TOKEN', '')
    os.environ.pop('DESKTOP_STARTUP_ID', None)
    env = platform.session_env()
    os.environ.update(env)
    from PyQt6.QtCore import QCoreApplication, QObject, QThread, QTimer, Qt, QEvent, pyqtSlot, pyqtSignal, pyqtClassInfo
    from PyQt6.QtGui import QIcon, QFont, QPainter, QColor, QFontMetricsF
    from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QSystemTrayIcon, QMenu
    from PyQt6.QtDBus import QDBusConnection, QDBusMessage, QDBus
    client = args.trigger or args.status or args.fixture_status or args.quit
    app = QCoreApplication(sys.argv[:1]) if client else QApplication(sys.argv[:1])
    app.setApplicationName('LookUp VM Spike')
    if not client:
        app.setDesktopFileName(DESKTOP.removesuffix('.desktop'))
        app.setQuitOnLastWindowClosed(False)
    bus = QDBusConnection.sessionBus()
    service = FIXTURE if args.public_window or args.fixture_status else SERVICE

    def remote(method, values=()):
        message = QDBusMessage.createMethodCall(service, '/VMSpike', INTERFACE, method)
        message.setArguments(list(values))
        reply = bus.call(message, QDBus.CallMode.Block, 2000)
        if reply.type() == QDBusMessage.MessageType.ErrorMessage:
            return None
        return reply.arguments()[0] if reply.arguments() else None

    if args.status or args.fixture_status or args.quit:
        value = remote('Quit' if args.quit else 'Status')
        print(value if isinstance(value, str) else json.dumps(value))
        return 0 if value is not None else 1
    if args.trigger:
        value = remote('Trigger', (token if valid_token(token) else '',))
        if value is None:
            flags = ['--owner-trigger', '--backend', args.backend]
            if args.controlled:
                flags.append('--controlled')
            subprocess.Popen([sys.executable, str(Path(__file__).resolve()), *flags],
                             env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
            for _ in range(20):
                status = remote('Status')
                if status is not None:
                    value = json.loads(status)['pid']
                    break
                time.sleep(.05)
        if value is not None:
            print(value)
            return 0
        return 1
    if not bus.registerService(service):
        for _ in range(10):
            value = remote('Trigger', (token if valid_token(token) else '',))
            if value is not None:
                print(value)
                return 0
            time.sleep(.05)
        return 1

    class Worker(QThread):
        finished_result = pyqtSignal(object)
        def run(self):
            try:
                value = pipeline(env, args.backend, args.controlled)
            except (platform.PlatformError, ocr.OcrError) as error:
                value = {'error': error.reason}
            except Exception:
                value = {'error': 'worker_failed'}
            self.finished_result.emit(value)

    class Popup(QLabel):
        def __init__(self, owner):
            super().__init__('LookUp public platform spike')
            self.owner = owner
            self.accept_deactivate = False
            self.setWindowTitle(POPUP_TITLE)
            self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
            self.setMinimumSize(240, 80)
        def keyPressEvent(self, event):
            if event.key() == Qt.Key.Key_Escape:
                self.owner.events.append('escape')
                self.hide()
            else:
                super().keyPressEvent(event)
        def event(self, event):
            if event.type() == QEvent.Type.WindowDeactivate and self.isVisible() and self.accept_deactivate:
                self.owner.events.append('deactivate')
                self.hide()
            return super().event(event)

    class PublicWindow(QWidget):
        def __init__(self):
            super().__init__()
            self.setWindowTitle('LookUp VM Public Fixture')
            self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
            self.setFont(QFont('Noto Sans', 20))
            self.showMaximized()
        def point(self):
            # Known glyph center, independent from OCR output or cursor placement.
            metrics = QFontMetricsF(self.font())
            bounds = metrics.tightBoundingRect('English')
            x = (self.width()-metrics.horizontalAdvance('English'))/2
            baseline = self.height()/2
            origin = self.mapToGlobal(self.rect().topLeft())
            return [origin.x()+x+bounds.center().x(), origin.y()+baseline+bounds.center().y()]
        def paintEvent(self, event):
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor('white'))
            painter.setPen(QColor('black'))
            metrics = QFontMetricsF(self.font())
            from PyQt6.QtCore import QPointF
            painter.drawText(QPointF((self.width()-metrics.horizontalAdvance('English'))/2,
                                     self.height()/2), 'English')

    @pyqtClassInfo('D-Bus Interface', INTERFACE)
    class Owner(QObject):
        def __init__(self):
            super().__init__()
            self.sequence = 0
            self.events = []
            self.result = {}
            self.worker = None
            self.popup = Popup(self)
            self.fixture = PublicWindow() if args.public_window else None
            self.tray = QSystemTrayIcon(QIcon.fromTheme('accessories-dictionary'), self)
            self.menu = QMenu()
            self.menu.aboutToShow.connect(lambda: self.events.append('tray-menu'))
            self.menu.addAction('Spike test action', lambda: self.events.append('tray-action'))
            self.menu.addAction('Quit spike', self.Quit)
            self.tray.setContextMenu(self.menu)
            self.tray.setToolTip('LookUp VM Spike')
            if not self.fixture:
                self.tray.show()
        @pyqtSlot(str, result=int)
        def Trigger(self, incoming):
            if not valid_token(incoming):
                return 0
            # Public PyQt API has no activation-token setter; test kdotool route.
            incoming = ''
            if self.worker is not None:
                return os.getpid()
            self.sequence += 1
            self.popup.hide()
            QTimer.singleShot(100, self.start_worker)
            self.worker = Worker()
            return os.getpid()
        def start_worker(self):
            self.worker.finished_result.connect(self.complete)
            self.worker.finished.connect(self.release_worker)
            self.worker.start()
        def release_worker(self):
            self.worker.deleteLater()
            self.worker = None
        def complete(self, result):
            self.result = result
            if 'point' not in result:
                return
            point = result['point']
            from PyQt6.QtCore import QPoint
            screen = app.screenAt(QPoint(round(point[0]), round(point[1]))) or app.primaryScreen()
            rect = screen.availableGeometry()
            placement = platform.popup_rect(point, (280, 100), (rect.x(), rect.y(), rect.width(), rect.height()))
            self.result['popup_target'] = placement
            self.popup.accept_deactivate = False
            self.popup.setGeometry(*placement)
            self.popup.show()
            self.popup.raise_()
            self.popup.activateWindow()
            self.popup.windowHandle().requestActivate()
            QTimer.singleShot(150, self.position_popup)
        def position_popup(self):
            try:
                candidates = platform.run(['kdotool', 'search', '--pid', str(os.getpid()), '--name', POPUP_TITLE], env).decode().split()
                uuid = candidates[0]
                x, y, _, _ = self.result['popup_target']
                platform.window_action(env, os.getpid(), uuid, 'windowmove', x, y)
                platform.window_action(env, os.getpid(), uuid, 'windowraise')
                platform.window_action(env, os.getpid(), uuid, 'windowactivate')
                self.result['popup_uuid'] = uuid
                QTimer.singleShot(300, self.arm_deactivation)
            except (platform.PlatformError, IndexError):
                self.result['focus_error'] = 'window_failed'
        def arm_deactivation(self):
            self.popup.accept_deactivate = True
            self.result['focus_ready'] = True
        @pyqtSlot(result=str)
        def Status(self):
            p = self.popup.geometry()
            value = dict(pid=os.getpid(), sequence=self.sequence, busy=self.worker is not None,
                         backend=args.backend, events=self.events[-30:], result=self.result,
                         popup_visible=self.popup.isVisible(), popup_active=self.popup.isActiveWindow(),
                         popup_rect=[p.x(), p.y(), p.width(), p.height()],
                         tray_visible=self.tray.isVisible(), tray_available=QSystemTrayIcon.isSystemTrayAvailable())
            if self.fixture:
                value['fixture_point'] = self.fixture.point()
            return json.dumps(value)
        @pyqtSlot(result=bool)
        def Quit(self):
            if self.worker is not None:
                QTimer.singleShot(100, self.Quit)
            else:
                app.quit()
            return True

    owner = Owner()
    if not bus.registerObject('/VMSpike', owner, QDBusConnection.RegisterOption.ExportAllSlots):
        return 1
    if args.owner_trigger:
        QTimer.singleShot(0, lambda: owner.Trigger(token if valid_token(token) else ''))
    token = ''
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
