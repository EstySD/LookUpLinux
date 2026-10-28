"""Narrow owned KDE lifecycle adapter. Qt/DBus imports are lazy; errors are private."""
from dataclasses import dataclass
import os
from pathlib import Path
import sys
import tempfile

from . import config, platform

DESKTOP='org.lookup.Linux.desktop'
INSTALLED_EXECUTABLE=Path('/usr/bin/lookup')
INSTALLED_DESKTOP=Path('/usr/share/applications')/DESKTOP
INSTALLED_AUTOSTART=Path('/etc/xdg/autostart')/DESKTOP
MARKER='X-LookUpLinux-Owned=true'
_application=None
_REASONS=frozenset(('invalid_shortcut','shortcut_conflict','not_registered','registry_unavailable',
                   'apply_failed','rollback_failed','unowned_file','file_failed','registration_failed'))


class LifecycleError(ValueError):
    def __init__(self,reason):
        self.reason=reason if reason in _REASONS else 'registry_unavailable'
        super().__init__(self.reason)


def parse_shortcut(text):
    if not config._valid_scalar('shortcut',text):
        raise LifecycleError('invalid_shortcut')
    try:
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QKeySequence
        sequence=QKeySequence.fromString(text,QKeySequence.SequenceFormat.PortableText)
        if sequence.count()!=1 or sequence.isEmpty():
            raise LifecycleError('invalid_shortcut')
        combined=sequence[0].toCombined()
        if not combined or sequence[0].key()==Qt.Key.Key_unknown:
            raise LifecycleError('invalid_shortcut')
        return sequence.toString(QKeySequence.SequenceFormat.PortableText),combined
    except ImportError:
        raise LifecycleError('registry_unavailable') from None


def key_text(key):
    from PyQt6.QtGui import QKeySequence
    return QKeySequence(key).toString(QKeySequence.SequenceFormat.PortableText)


def _dbus_call(method,*args):
    global _application
    try:
        from PyQt6.QtCore import QCoreApplication,QMetaType
        from PyQt6.QtDBus import QDBusConnection,QDBusMessage,QDBus,QDBusArgument
        if QCoreApplication.instance() is None:
            _application=QCoreApplication(['lookup-lifecycle'])
        bus=QDBusConnection.sessionBus()
        converted=list(args)
        if method in ('allActionsForComponent','shortcut','setForeignShortcut'):
            converted[0]=QDBusArgument(list(args[0]),QMetaType.Type.QStringList.value)
        if method=='setForeignShortcut':
            keys=QDBusArgument()
            keys.beginArray(QMetaType.Type.Int.value)
            for value in args[1]:keys.add(value,QMetaType.Type.Int.value)
            keys.endArray()
            converted[1]=keys
        message=QDBusMessage.createMethodCall('org.kde.kglobalaccel','/kglobalaccel',
                                             'org.kde.KGlobalAccel',method)
        message.setArguments(converted)
        reply=bus.call(message,QDBus.CallMode.Block,1200)
        if reply.type()==QDBusMessage.MessageType.ErrorMessage:
            raise LifecycleError('registry_unavailable')
        values=reply.arguments()
        return values[0] if values else None
    except (ImportError,TypeError,RuntimeError):
        raise LifecycleError('registry_unavailable') from None


@dataclass(frozen=True)
class Binding:
    action: tuple
    keys: tuple


class ShortcutRegistry:
    def __init__(self,call=None):
        self._transport=call or _dbus_call

    def _call(self,method,*args):
        try:return self._transport(method,*args)
        except LifecycleError:raise
        except Exception:raise LifecycleError('registry_unavailable') from None

    def inspect(self):
        actions=self._call('allActionsForComponent',[DESKTOP,'','',''])
        if not isinstance(actions,(tuple,list)) or len(actions)>100:
            raise LifecycleError('registry_unavailable')
        owned=[tuple(action) for action in actions if isinstance(action,(tuple,list)) and len(action)==4
               and all(isinstance(value,str) and len(value)<=512 for value in action)
               and action[0]==DESKTOP and action[1]=='_launch']
        if len(owned)!=1:
            raise LifecycleError('not_registered')
        return Binding(owned[0],self._keys(owned[0]))

    def _keys(self,action):
        keys=self._call('shortcut',list(action))
        if (not isinstance(keys,(tuple,list)) or len(keys)>16 or
                any(type(key) is not int or not 0<=key<(1<<31) for key in keys)):
            raise LifecycleError('registry_unavailable')
        return tuple(key for key in keys if key)

    def _available(self,keys):
        for key in keys:
            available=self._call('isGlobalShortcutAvailable',key,DESKTOP)
            if available is not True:
                raise LifecycleError('shortcut_conflict' if available is False else 'registry_unavailable')

    def preflight(self,text):
        canonical,key=parse_shortcut(text)
        binding=self.inspect()
        self._available((key,))
        return binding,canonical,key

    def _replace(self,action,keys):
        if tuple(action[:2])!=(DESKTOP,'_launch'):
            raise LifecycleError('not_registered')
        self._available(keys)
        self._call('setForeignShortcut',list(action),list(keys))
        if self._keys(action)!=tuple(keys):
            raise LifecycleError('apply_failed')

    def change(self,text):
        before,canonical,key=self.preflight(text)
        transaction=ShortcutTransaction(self,before,(key,))
        if before.keys==transaction.desired:
            transaction.active=False
            return transaction
        try:self._replace(before.action,transaction.desired)
        except LifecycleError:
            transaction.rollback()
            raise LifecycleError('apply_failed') from None
        return transaction


@dataclass
class ShortcutTransaction:
    registry: ShortcutRegistry
    before: Binding
    desired: tuple
    active: bool=True

    def commit(self):self.active=False

    def rollback(self):
        if not self.active:return
        try:self.registry._replace(self.before.action,self.before.keys)
        except LifecycleError:raise LifecycleError('rollback_failed') from None
        self.active=False


def inspect_shortcut(registry=None):
    """Read-only diagnostic seam: never registers entries or changes keys."""
    return (registry or ShortcutRegistry()).inspect()


def is_installed():
    return INSTALLED_EXECUTABLE.is_file() and INSTALLED_DESKTOP.is_file()


def launch_command(action='--app',*,python=None,directory=None,installed=None):
    installed=is_installed() if installed is None else installed
    if installed:return [str(INSTALLED_EXECUTABLE),action],None
    return [str(python or sys.executable),'-m','lookup',action],Path(directory or Path(__file__).resolve().parents[1])


def _quote(path):
    path=Path(path)
    value=str(path)
    if not path.is_absolute() or any(c in value for c in '\r\n\x00'):
        raise ValueError('invalid_desktop_path')
    for char in ('\\','"','`','$'):value=value.replace(char,'\\'+char)
    return '"'+value.replace('%','%%')+'"'


def desktop_text(python=None,directory=None,*,installed=False,autostart=False,shortcut='Meta+Shift+D'):
    if not config._valid_scalar('shortcut',shortcut):raise LifecycleError('invalid_shortcut')
    workdir=''
    if installed:
        executable='/usr/bin/lookup'
        command=executable+(' --autostart' if autostart else ' --trigger')
    else:
        executable=_quote(python or sys.executable)
        directory=Path(directory or Path(__file__).resolve().parents[1])
        _quote(directory)
        workdir='Path='+str(directory).replace('\\','\\\\')+'\n'
        command=executable+' -m lookup'+(' --autostart' if autostart else ' --trigger')
    text=('[Desktop Entry]\nType=Application\nName=LookUp Linux\n'+
          'Comment=LookUp Linux owned application trigger\n'+MARKER+'\n'+
          'Exec='+command+'\n'+workdir+'Icon=accessories-dictionary\nTerminal=false\n')
    if autostart:
        # TryExec is one Desktop Entry string, not a shell command.
        attempt='/usr/bin/lookup' if installed else str(python or sys.executable).replace('\\','\\\\')
        return text+'OnlyShowIn=KDE;\nTryExec='+attempt+'\nStartupNotify=false\n'
    return text+'StartupNotify=true\nX-KDE-Shortcuts='+shortcut.replace('\\','\\\\')+'\n'


def _existing(path):
    if path.is_symlink():raise LifecycleError('unowned_file')
    try:
        with path.open('rb') as stream:raw=stream.read(65537)
    except FileNotFoundError:return None
    except OSError:raise LifecycleError('file_failed') from None
    if len(raw)>65536:raise LifecycleError('unowned_file')
    try:text=raw.decode('utf-8')
    except UnicodeError:raise LifecycleError('unowned_file') from None
    if (MARKER not in text.splitlines() and
            'Comment=LookUp Linux owned application trigger' not in text.splitlines()):
        raise LifecycleError('unowned_file')
    return raw


def _write_entry(path,text):
    temporary=None
    try:
        path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',newline='\n',dir=path.parent,
                                         prefix='.'+path.name+'.',suffix='.tmp',delete=False) as stream:
            temporary=Path(stream.name)
            os.chmod(temporary,0o600)
            stream.write(text);stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,path)
    except OSError:raise LifecycleError('file_failed') from None
    finally:
        if temporary is not None:
            try:temporary.unlink(missing_ok=True)
            except OSError:pass


def ensure_entries(*,python=None,directory=None,shortcut=None):
    if is_installed():return INSTALLED_DESKTOP,INSTALLED_AUTOSTART
    data=os.environ.get('XDG_DATA_HOME','')
    home=Path(data) if data and Path(data).is_absolute() else Path.home()/'.local/share'
    configuration=os.environ.get('XDG_CONFIG_HOME','')
    settings=Path(configuration) if configuration and Path(configuration).is_absolute() else Path.home()/'.config'
    paths=(home/'applications'/DESKTOP,settings/'autostart'/DESKTOP)
    existing=tuple(_existing(path) for path in paths)  # Refuse collisions before any writes.
    key=shortcut or config.load().shortcut
    texts=(desktop_text(python,directory,shortcut=key),desktop_text(python,directory,autostart=True))
    changed=False
    for path,text,old in zip(paths,texts,existing):
        if old!=text.encode('utf-8'):
            _write_entry(path,text);changed=True
    if changed:
        try:platform.run(['kbuildsycoca6'],timeout=3,limit=4096)
        except platform.PlatformError:raise LifecycleError('registration_failed') from None
    return paths
