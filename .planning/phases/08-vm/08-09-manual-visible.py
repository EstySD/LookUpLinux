"""Last read-only window verification before yielding all guest interaction."""
import json,runpy
from pathlib import Path
root=Path('.planning/phases/08-vm');n=runpy.run_path(str(root/'08-09-native.py'))
code='''import os,sys,json
sys.path.insert(0,'/usr/lib/lookup/app')
from lookup import platform
env=platform.session_env();os.environ.update(env)
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtDBus import QDBusConnection,QDBusMessage,QDBus
application=QCoreApplication([]);bus=QDBusConnection.sessionBus();rows=[]
ids=platform.run(['kdotool','search','--pid','917'],env).decode().split()
for identity in ids:
    message=QDBusMessage.createMethodCall('org.kde.KWin','/KWin','org.kde.KWin','getWindowInfo');message.setArguments([identity])
    reply=bus.call(message,QDBus.CallMode.Block,1200);info=reply.arguments()[0] if reply.arguments() else {}
    rows.append({key:info.get(key) for key in ('pid','caption','active','minimized','x','y','width','height')})
print(json.dumps(rows))'''
value=json.loads(n['guest']("import subprocess;p=subprocess.run(['sudo','-n','-H','-u','lookup07','python','-c',"+repr(code)+"],capture_output=True,text=True,timeout=8);print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)"))
(root/'08-09-manual-visible.json').write_text(json.dumps(value,indent=2));print(json.dumps(value))
