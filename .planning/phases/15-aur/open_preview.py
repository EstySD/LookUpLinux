"""Open the current product in the visible owned VM for Denis's manual test."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from tools.stage_package import stage

OUT=Path(__file__).resolve().parent
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=5','-o','HostKeyAlias=lookup-gsd-07',
    '-o','UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-p','2227','archvm']
SCP=['scp','-o','BatchMode=yes','-o','HostKeyAlias=lookup-gsd-07',
    '-o','UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-P','2227']


def main():
    build=OUT/('manual-preview-'+str(int(time.time())))
    source=stage(build,public=True)
    report={'command':'python .planning/phases/15-aur/open_preview.py','pid':__import__('os').getpid(),
        'source_sha256':source['archive_sha256'],'vm':'cf207909-94b5-4b49-8bd8-ccff973c1dc8',
        'user_request':'visible GUI VM and latest app; leave running; no publishing'}
    (OUT/'manual-preview-job.json').write_text(json.dumps(report,indent=2))
    for _ in range(36):
        if subprocess.run([*SSH,'true'],capture_output=True).returncode==0:break
        time.sleep(2)
    else:raise RuntimeError('owned_clone_ssh_unavailable')
    remote='/home/lookup07/lookup-preview-0.2.1-'+str(int(time.time()))
    subprocess.run([*SCP,str(build/'lookup-source.tar.gz'),'archvm:/tmp/lookup-manual-preview.tar.gz'],check=True,capture_output=True,timeout=60)
    command='sudo -n install -d -m 755 -o lookup07 -g lookup07 '+remote+' && sudo -n -H -u lookup07 tar xzf /tmp/lookup-manual-preview.tar.gz -C '+remote
    subprocess.run([*SSH,command],check=True,capture_output=True,timeout=30)
    code='''from pathlib import Path
import hashlib,json,os,signal,subprocess,sys,time
root=Path(REMOTE)/'lookup-source'
sys.path.insert(0,str(root))
from lookup import platform,context,lifecycle
os.environ.update(platform.session_env())
for key in ('SUDO_UID','SUDO_GID','SUDO_USER','SUDO_COMMAND'):os.environ.pop(key,None)
assert os.getuid()==1001 and Path.home()==Path('/home/lookup07')
assert context.PROVIDER=='google-marked-v2'
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtDBus import QDBusConnection,QDBusMessage
application=QCoreApplication([]);bus=QDBusConnection.sessionBus()
reply=bus.interface().servicePid('org.lookup.Linux')
if reply.isValid() and reply.value():
 pid=reply.value();process=Path('/proc',str(pid))
 assert process.stat().st_uid==1001 and b'lookup' in (process/'cmdline').read_bytes()
 os.kill(pid,signal.SIGTERM)
 for _ in range(40):
  if not process.exists():break
  time.sleep(.1)
 else:raise RuntimeError('old_owner_did_not_stop')
log=open(Path(REMOTE)/'lookup-preview.log','a')
child=subprocess.Popen([sys.executable,'-m','lookup','--app'],cwd=root,env=dict(os.environ,PYTHONPATH=str(root)),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
for _ in range(80):
 reply=bus.interface().servicePid('org.lookup.Linux')
 if reply.isValid() and reply.value()==child.pid:break
 if child.poll() is not None:raise RuntimeError('preview_exited')
 time.sleep(.1)
else:raise RuntimeError('preview_bus_owner_missing')
time.sleep(1)
message=QDBusMessage.createMethodCall('org.lookup.Linux','/Lookup','org.lookup.Linux','Open');message.setArguments([''])
opened=bus.call(message)
print(json.dumps({'pid':child.pid,'source':str(root),'provider':context.PROVIDER,'open_reply':opened.arguments(),
 'effective_keys':[lifecycle.key_text(k) for k in lifecycle.inspect_shortcut().keys],
 'commandline':Path('/proc',str(child.pid),'cmdline').read_bytes().replace(b'\\0',b' ').decode(),'log':str(Path(REMOTE)/'lookup-preview.log')}))
'''.replace('REMOTE',repr(remote))
    encoded=base64.b64encode(code.encode()).decode()
    result=subprocess.run([*SSH,'echo '+encoded+' | base64 -d | sudo -n -H -u lookup07 python -'],capture_output=True,text=True,encoding='utf-8',timeout=30)
    if result.returncode:raise RuntimeError(result.stderr[-2000:])
    report.update(json.loads(result.stdout));report['left_running']=True;report['publication']='not_published'
    (OUT/'manual-preview-job.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':main()
