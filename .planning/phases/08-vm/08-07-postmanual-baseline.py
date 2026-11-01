"""Snapshot current user files and logical counts before any owned mutation."""
import base64,json,runpy
from pathlib import Path
root=Path('.planning/phases/08-vm');n=runpy.run_path(str(root/'08-07-native.py'))
code='''import os,sys,json,hashlib,sqlite3,subprocess,time
from pathlib import Path
assert Path('/home/lookup07').stat().st_uid==1001
baseline=Path('/home/arch/lookup-final-07');assert not baseline.exists();baseline.mkdir(mode=0o700)
home=Path('/home/lookup07');files={};counts={}
for directory in (home/'.config/lookup',home/'.local/share/lookup'):
    for path in directory.rglob('*'):
        if path.is_file() and not path.is_symlink():
            data=path.read_bytes();files[str(path)]=dict(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
            if path.suffix=='.db':
                with sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True) as conn:
                    tables={row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                    counts[str(path)]=dict(integrity=conn.execute('PRAGMA integrity_check').fetchone()[0],rows={name:conn.execute('SELECT count(*) FROM "'+name.replace('"','""')+'"').fetchone()[0] for name in tables})
                    destination=sqlite3.connect(str(baseline/(path.name+'.backup')));conn.backup(destination);destination.close()
config=home/'.config/lookup/config.json';data=config.read_bytes();(baseline/'config.json.backup').write_bytes(data)
registry=home/'.config/kglobalshortcutsrc';raw=registry.read_bytes();(baseline/'kglobalshortcutsrc.before').write_bytes(raw)
result=dict(files=files,logical_counts=counts,config=json.loads(data),shortcut_file_sha256=hashlib.sha256(raw).hexdigest(),
    package_present=subprocess.run(['pacman','-Q','lookup-linux'],capture_output=True).returncode==0,at_ns=time.monotonic_ns(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
(baseline/'baseline.json').write_text(json.dumps(result,indent=2));os.chmod(baseline/'config.json.backup',0o600)
print(json.dumps(result))'''
value=json.loads(n['guest'](code));(root/'08-07-postmanual-baseline.json').write_text(json.dumps(value,indent=2));print(json.dumps(value))
code='''import os,sys,json
sys.path.insert(0,'/usr/lib/lookup/app')
from lookup import platform
os.environ.update(platform.session_env())
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtDBus import QDBusConnection,QDBusMessage,QDBus
application=QCoreApplication([]);bus=QDBusConnection.sessionBus()
message=QDBusMessage.createMethodCall('org.kde.kglobalaccel','/kglobalaccel','org.freedesktop.DBus.Introspectable','Introspect')
reply=bus.call(message,QDBus.CallMode.Block,1200);print(reply.arguments()[0])'''
value=n['guest']("import subprocess;p=subprocess.run(['sudo','-n','-H','-u','lookup07','python','-c',"+repr(code)+"],capture_output=True,text=True,timeout=8);print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)")
(root/'08-07-registry-introspection.xml').write_text(value,encoding='utf-8');print(value[:3000])
