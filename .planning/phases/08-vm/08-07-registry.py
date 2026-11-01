"""Typed full registry observations and exactly scoped final verification fixture."""
import base64,configparser,hashlib,json,os,sys,time
from pathlib import Path
sys.path.insert(0,'/usr/lib/lookup/app')
from lookup import platform,lifecycle
os.environ.update(platform.session_env())
from PyQt6.QtCore import QCoreApplication,QMetaType
from PyQt6.QtDBus import QDBusConnection,QDBusMessage,QDBus,QDBusArgument
application=QCoreApplication([]);bus=QDBusConnection.sessionBus()
base=Path.home()/'.local/state/lookup-final-07';base.mkdir(mode=0o700,exist_ok=True)
fixture='lookup-final-probe-07.desktop'

def strings(value):return QDBusArgument(list(value),QMetaType.Type.QStringList.value)
def call(method,*args):
    message=QDBusMessage.createMethodCall('org.kde.kglobalaccel','/kglobalaccel','org.kde.KGlobalAccel',method);message.setArguments(list(args))
    reply=bus.call(message,QDBus.CallMode.Block,1200)
    if reply.type()==QDBusMessage.MessageType.ErrorMessage:raise RuntimeError(reply.errorMessage())
    return reply.arguments()[0] if reply.arguments() else None
def dump():
    components=call('allMainComponents');assert isinstance(components,list) and len(components)<=500
    bindings=[]
    for component in components:
        assert isinstance(component,list) and len(component)==4
        actions=call('allActionsForComponent',strings(component));assert isinstance(actions,list) and len(actions)<=500
        for action in actions:
            keys=call('shortcut',strings(action));assert isinstance(keys,list) and all(type(key) is int for key in keys)
            bindings.append(dict(action=action,keys=keys))
    path=Path.home()/'.config/kglobalshortcutsrc';raw=path.read_bytes()
    return dict(at_ns=time.monotonic_ns(),components=components,bindings=sorted(bindings,key=lambda row:row['action'][:2]),
        kconfig_base64=base64.b64encode(raw).decode(),kconfig_sha256=hashlib.sha256(raw).hexdigest())
def write(name,value):(base/name).write_text(json.dumps(value,indent=2))

if __name__=='__main__':
    action=sys.argv[1]
    if action=='dump':print(json.dumps(dump()))
    elif action=='setup':
        before=dump();write('postmanual-registry.json',before)
        candidates=['Meta+Ctrl+Alt+F11','Meta+Ctrl+Alt+F12'];key=None
        for candidate in candidates:
            value=lifecycle.parse_shortcut(candidate)[1]
            if call('isGlobalShortcutAvailable',value,fixture) is True:key=candidate;break
        assert key,'No free predeclared fixture shortcut'
        desktop=Path.home()/'.local/share/applications'/fixture;assert not desktop.exists()
        marker=base/'marker.py';assert not marker.exists()
        marker.write_text("import json,os,time\nfrom pathlib import Path\np=Path.home()/'.local/state/lookup-final-07/marker.jsonl'\nwith p.open('a') as out:out.write(json.dumps(dict(at_ns=time.monotonic_ns(),pid=os.getpid(),uid=os.getuid(),start=int(Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19])))+'\\n')\n")
        text='[Desktop Entry]\nType=Application\nName=Owned final unrelated marker\nExec=/usr/bin/python '+str(marker)+'\nTerminal=false\nX-LookUpFinal07-Owned=true\nX-KDE-Shortcuts='+key+'\n'
        desktop.write_text(text);platform.run(['kbuildsycoca6'],os.environ,timeout=5)
        deadline=time.monotonic()+5;registered=None
        while time.monotonic()<deadline:
            values=call('allActionsForComponent',strings([fixture,'','','']))
            registered=next((row for row in values if row[:2]==[fixture,'_launch']),None)
            if registered:break
            time.sleep(.1)
        assert registered and call('shortcut',strings(registered))==[lifecycle.parse_shortcut(key)[1]]
        write('fixture.json',dict(action=registered,key=key,desktop=str(desktop),desktop_sha256=hashlib.sha256(text.encode()).hexdigest(),marker_sha256=hashlib.sha256(marker.read_bytes()).hexdigest()))
        print(json.dumps(dict(fixture=json.loads((base/'fixture.json').read_text()),registry=dump())))
    elif action=='retarget-fixture':
        metadata=json.loads((base/'fixture.json').read_text());desktop=Path(metadata['desktop'])
        assert hashlib.sha256(desktop.read_bytes()).hexdigest()==metadata['desktop_sha256']
        key='Meta+Ctrl+Shift+F11';value=lifecycle.parse_shortcut(key)[1]
        assert call('isGlobalShortcutAvailable',value,fixture) is True
        before=dump();text=desktop.read_text().replace('X-KDE-Shortcuts='+metadata['key'],'X-KDE-Shortcuts='+key)
        desktop.write_text(text)
        keys=QDBusArgument();keys.beginArray(QMetaType.Type.Int.value);keys.add(value);keys.endArray()
        call('setForeignShortcut',strings(metadata['action']),keys)
        assert call('shortcut',strings(metadata['action']))==[value]
        metadata.update(key=key,desktop_sha256=hashlib.sha256(text.encode()).hexdigest());write('fixture.json',metadata)
        print(json.dumps(dict(fixture=metadata,registry_before=before,registry=dump())))
    elif action=='clear-product':
        before=dump();write('before-product-clear.json',before)
        registry=lifecycle.ShortcutRegistry();binding=registry.inspect();registry._replace(binding.action,())
        time.sleep(.5);after=dump();write('after-product-clear.json',after)
        without=lambda rows:[row for row in rows if row['action'][:2]!=['org.lookup.Linux.desktop','_launch']]
        print(json.dumps(dict(before=before,after=after,product_action=binding.action,product_before=binding.keys,product_after=registry.inspect().keys,
            unrelated_typed_unchanged=without(before['bindings'])==without(after['bindings']))))
    elif action=='cleanup-fixture':
        metadata=json.loads((base/'fixture.json').read_text());desktop=Path(metadata['desktop']);marker=base/'marker.py'
        assert hashlib.sha256(desktop.read_bytes()).hexdigest()==metadata['desktop_sha256'] and hashlib.sha256(marker.read_bytes()).hexdigest()==metadata['marker_sha256']
        old=call('shortcut',strings(metadata['action']));keys=QDBusArgument();keys.beginArray(QMetaType.Type.Int.value);keys.endArray()
        call('setForeignShortcut',strings(metadata['action']),keys);assert not any(call('shortcut',strings(metadata['action'])))
        removed=call('unregister',fixture,'_launch');assert removed is True
        desktop.unlink();marker.unlink();platform.run(['kbuildsycoca6'],os.environ,timeout=5)
        print(json.dumps(dict(removed=True,old_keys=old,registry=dump())))
