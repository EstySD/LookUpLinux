"""Close the current normal app through its actual tray before isolated tests."""
import json,runpy
from pathlib import Path
root=Path('.planning/phases/08-vm');n=runpy.run_path(str(root/'08-07-native.py'))
code='''import os,sys,json,subprocess,time
from pathlib import Path
sys.path.insert(0,'/usr/lib/lookup/app')
from lookup import platform
env=platform.session_env();os.environ.update(env)
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtDBus import QDBusConnection
application=QCoreApplication([]);interface=QDBusConnection.sessionBus().interface();interface.setTimeout(1200)
pid=interface.servicePid('org.lookup.Linux').value();assert pid
process=Path('/proc',str(pid));assert process.stat().st_uid==1001
argv=(process/'cmdline').read_bytes().split(b'\\0');assert argv[:2]==[b'/usr/bin/python',b'/usr/bin/lookup']
start=int((process/'stat').read_text().split(') ',1)[1].split()[19])
items=subprocess.run(['qdbus6','org.kde.StatusNotifierWatcher','/StatusNotifierWatcher','org.kde.StatusNotifierWatcher.RegisteredStatusNotifierItems'],env=env,capture_output=True,text=True,check=True,timeout=3).stdout.split()
for item in items:
    service=item.split('/StatusNotifierItem')[0]
    if interface.servicePid(service).value()!=pid:continue
    subprocess.run(['qdbus6',service,'/MenuBar','com.canonical.dbusmenu.Event','5','clicked','0','0'],env=env,capture_output=True,check=True,timeout=3)
deadline=time.monotonic()+8
while time.monotonic()<deadline and interface.isServiceRegistered('org.lookup.Linux').value():time.sleep(.05)
absent=not interface.isServiceRegistered('org.lookup.Linux').value();assert absent
print(json.dumps(dict(pid=pid,start=start,uid=1001,method='actual tray Exit',owner_absent=absent,at_ns=time.monotonic_ns())))'''
raw=n['guest']("import subprocess;p=subprocess.run(['sudo','-n','-H','-u','lookup07','python','-c',"+repr(code)+"],capture_output=True,text=True,timeout=15);print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)")
(root/'08-07-tray-stop.json').write_text(raw);print(raw)
