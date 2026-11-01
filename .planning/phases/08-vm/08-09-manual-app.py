"""Reinstall the reviewed artifact and open the ordinary app for the user."""
import json,runpy
from pathlib import Path
root=Path('.planning/phases/08-vm');n=runpy.run_path(str(root/'08-09-native.py'))
code='''import hashlib,json,subprocess
from pathlib import Path
package=Path('/home/arch/lookup-cascade-09-build/lookup-linux-0.1.0-1-x86_64.pkg.tar.zst')
assert hashlib.sha256(package.read_bytes()).hexdigest()=='7981792e6b2b7a512ebd3465331a9f58ec717c6d6b7d7c24b2046187c6c4d7ea'
p=subprocess.run(['pacman','-Q','lookup-linux'],capture_output=True,text=True)
if p.returncode:p=subprocess.run(['pacman','-U','--noconfirm',str(package)],capture_output=True,text=True,timeout=30)
print(json.dumps(dict(exit=p.returncode,stdout=p.stdout,stderr=p.stderr)))
assert p.returncode==0
'''
receipt=json.loads(n['guest'](code,timeout=40));(root/'08-09-manual-package.json').write_text(json.dumps(receipt,indent=2))
code='''import os,sys,json,subprocess,time
from pathlib import Path
sys.path.insert(0,'/usr/lib/lookup/app')
from lookup import platform,lifecycle,config,dicts
env=platform.session_env()
for key in list(env):
    if key.startswith('LOOKUP_') or key in ('SUDO_UID','SUDO_GID','SUDO_USER','SUDO_COMMAND'):env.pop(key,None)
os.environ.clear();os.environ.update(env)
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtDBus import QDBusConnection
app=QCoreApplication([]);bus=QDBusConnection.sessionBus();interface=bus.interface();interface.setTimeout(1200)
present=interface.isServiceRegistered('org.lookup.Linux')
if not present.isValid() or not present.value():
    child=subprocess.Popen(['/usr/bin/lookup','--app'],env=env,cwd=str(Path.home()),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
    deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        present=interface.isServiceRegistered('org.lookup.Linux')
        if present.isValid() and present.value():break
        time.sleep(.1)
pid=interface.servicePid('org.lookup.Linux').value();assert pid
settings=config.load();registry=lifecycle.ShortcutRegistry()
subprocess.run(['kbuildsycoca6'],env=env,capture_output=True,timeout=10,check=True)
deadline=time.monotonic()+4
while True:
    try:registry.inspect();break
    except lifecycle.LifecycleError:
        if time.monotonic()>deadline:raise
        time.sleep(.1)
if registry.inspect().keys!=(lifecycle.parse_shortcut(settings.shortcut)[1],):registry.change(settings.shortcut).commit()
with dicts.open_all(settings) as dictionaries:
    ready=bool(dictionaries.lookup_exact('bank'))
items=subprocess.run(['qdbus6','org.kde.StatusNotifierWatcher','/StatusNotifierWatcher','org.kde.StatusNotifierWatcher.RegisteredStatusNotifierItems'],env=env,capture_output=True,text=True,check=True,timeout=3).stdout.split()
opened=False
for item in items:
    service=item.split('/StatusNotifierItem')[0]
    if interface.servicePid(service).value()!=pid:continue
    result=subprocess.run(['qdbus6',service,'/MenuBar','com.canonical.dbusmenu.Event','3','clicked','0','0'],env=env,capture_output=True,text=True,timeout=3)
    opened=result.returncode==0
print(json.dumps(dict(pid=pid,uid=os.getuid(),home=str(Path.home()),desktop_session=env.get('XDG_SESSION_TYPE'),shortcut=settings.shortcut,registered_keys=[lifecycle.key_text(key) for key in registry.inspect().keys],dictionary_bank_ready=ready,settings_open_requested=opened,
    normal_profile=True,process_argv=Path('/proc',str(pid),'cmdline').read_bytes().decode().split('\\0'),timing_enabled='LOOKUP_TIMING' in env)))
'''
value=json.loads(n['guest']("import subprocess;p=subprocess.run(['sudo','-n','-H','-u','lookup07','python','-c',"+repr(code)+"],capture_output=True,text=True,timeout=25);print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)",timeout=30))
(root/'08-09-manual-app.json').write_text(json.dumps(value,indent=2));print(json.dumps(value))
