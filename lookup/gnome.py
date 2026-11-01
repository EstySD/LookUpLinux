"""GNOME Shell bridge. The optional extension owns compositor-only operations."""
import base64
import json
import os

from .platform import PlatformError

INTERFACE='org.lookup.Linux.Gnome'
OBJECT='/org/lookup/Linux/Gnome'
_application=None


def active(env=None):
    env=os.environ if env is None else env
    desktops=env.get('XDG_CURRENT_DESKTOP','').lower().split(':')
    return 'gnome' in desktops and 'kde' not in desktops


def call(method,*args,timeout=2500):
    global _application
    try:
        from PyQt6.QtCore import QCoreApplication
        from PyQt6.QtDBus import QDBusConnection,QDBusMessage,QDBus
        if QCoreApplication.instance() is None:
            _application=QCoreApplication(['lookup-gnome'])
        message=QDBusMessage.createMethodCall('org.gnome.Shell',OBJECT,INTERFACE,method)
        message.setArguments(list(args))
        reply=QDBusConnection.sessionBus().call(message,QDBus.CallMode.Block,timeout)
        if reply.type()==QDBusMessage.MessageType.ErrorMessage:
            raise PlatformError('gnome_extension_unavailable')
        values=reply.arguments()
        if len(values)!=1:raise PlatformError('bad_output')
        return values[0]
    except ImportError:
        raise PlatformError('missing_pyqt6') from None


def state():
    try:
        value=call('State')
        if not isinstance(value,str) or len(value)>65536:raise ValueError
        result=json.loads(value)
        if type(result.get('version')) is not int or result['version']!=1:raise ValueError
        from .platform import Monitor,_numbers
        point=result['point']
        if not isinstance(point,list) or len(point)!=2:raise ValueError
        _numbers(point)
        outputs=result['monitors']
        if not isinstance(outputs,list) or not 1<=len(outputs)<=64:raise ValueError
        names=set()
        for item in outputs:
            name=item['name']
            if not isinstance(name,str) or len(name)>128 or name in names:raise ValueError
            names.add(name)
            Monitor(*(item[key] for key in ('name','x','y','width','height','scale')))
            area=item['available']
            if not isinstance(area,list) or len(area)!=4:raise ValueError
            _numbers(area)
            if min(area[2:])<=0:raise ValueError
        if not isinstance(result['shortcut'],str) or len(result['shortcut'])>128:raise ValueError
        return result
    except (ValueError,TypeError,AttributeError,KeyError):
        raise PlatformError('bad_output') from None


def capture(monitor):
    from .capture import MAX_PNG,_png_image
    value=call('Capture',monitor.name,timeout=5000)
    try:
        if not isinstance(value,str) or len(value)>4*((MAX_PNG+2)//3):raise ValueError
        png=base64.b64decode(value,validate=True)
        image=_png_image(png)
        return png,image.width(),image.height()
    except (ValueError,TypeError):
        raise PlatformError('capture_failed') from None


def place(pid,title,x,y):
    if type(pid) is not int or pid<=0 or any(type(v) is not int for v in (x,y)):
        raise PlatformError('invalid_owner')
    if call('Place',pid,title,x,y) is not True:raise PlatformError('placement_failed')


def accelerator(text):
    parts=text.split('+')
    modifiers={'Meta':'Super','Ctrl':'Control','Alt':'Alt','Shift':'Shift'}
    if not parts[-1] or any(part not in modifiers for part in parts[:-1]):
        raise ValueError('invalid_shortcut')
    key={'Space':'space','Esc':'Escape','Del':'Delete','PgUp':'Page_Up',
         'PgDown':'Page_Down','Backspace':'BackSpace','Return':'Return'}.get(parts[-1],parts[-1])
    if len(key)==1 and key.isalpha():key=key.lower()
    return ''.join('<'+modifiers[part]+'>' for part in parts[:-1])+key


class ShortcutRegistry:
    def inspect(self):
        from .lifecycle import Binding,LifecycleError,parse_shortcut,DESKTOP
        try:
            shortcut=state()['shortcut']
            keys=(parse_shortcut(shortcut)[1],) if shortcut else ()
            return Binding((DESKTOP,'_launch','LookUp Linux',''),keys)
        except (PlatformError,KeyError,ValueError):
            raise LifecycleError('registry_unavailable') from None

    def _replace(self,action,keys):
        from .lifecycle import key_text,LifecycleError
        if len(keys)>1:raise LifecycleError('invalid_shortcut')
        text=key_text(keys[0]) if keys else ''
        try:ok=call('SetShortcut',text,accelerator(text) if text else '')
        except (PlatformError,ValueError):raise LifecycleError('registry_unavailable') from None
        if ok is not True:raise LifecycleError('shortcut_conflict')

    def change(self,text):
        from .lifecycle import parse_shortcut,ShortcutTransaction
        before=self.inspect()
        _,key=parse_shortcut(text)
        if before.keys!=(key,):self._replace(before.action,(key,))
        return ShortcutTransaction(self,before,(key,),active=before.keys!=(key,))
