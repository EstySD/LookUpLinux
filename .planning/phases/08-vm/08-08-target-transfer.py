"""Pinned DMI-guarded transfer and status for the sole target corpus job."""
import base64,json,shlex,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from tools.check_hardening_install import ssh
root=Path('.planning/phases/08-vm');destination='/home/lookup07/.local/state/lookup-ocr-08-08-e236ee09'
def guest(code):
    code="from pathlib import Path;assert Path('/sys/class/dmi/id/product_uuid').read_text().strip()=='097920cf-b594-494b-8bd8-ccff973c1dc8'\n"+code
    return ssh('sudo -n python -c '+shlex.quote(code))
if sys.argv[1]=='prepare':
    print(guest('pass'))
    for name in ('08-08-target-source.tar','08-08-target-job.py'):
        subprocess.run(['scp','-q','-o','BatchMode=yes','-o','ConnectTimeout=5','-o','HostKeyAlias=lookup-gsd-07','-o',
            'UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-P','2227',str(root/name),'archvm:/home/arch/lookup-'+name],check=True,timeout=30)
    code='''import tarfile,os,subprocess,json,shutil,hashlib
destination=Path('''+repr(destination)+''');assert destination.is_relative_to(Path('/home/lookup07/.local/state')) and not (destination/'08-08-target-progress.json').exists()
destination.mkdir(exist_ok=True)
archive=Path('/home/arch/lookup-08-08-target-source.tar');assert hashlib.sha256(archive.read_bytes()).hexdigest()=='e236ee0903ded4e39b6bf82de17d8ef1c7f2af67d6e6785cc13353e69fde17fb'
with tarfile.open(archive) as bundle:bundle.extractall(destination,filter='data')
shutil.copyfile('/home/arch/lookup-08-08-target-job.py',destination/'08-08-target-job.py')
for path in (destination,*destination.rglob('*')):os.chown(path,1001,1001)
env=dict(os.environ,XDG_RUNTIME_DIR='/run/user/1001',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/1001/bus')
unit='lookup-ocr-corpus-08-08'
command=['sudo','-n','-H','-u','lookup07','env','XDG_RUNTIME_DIR=/run/user/1001','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1001/bus','systemd-run','--user','--unit='+unit,'--service-type=exec','--property=WorkingDirectory='+str(destination),'--property=RuntimeMaxSec=1800','--property=TimeoutStopSec=5','--setenv=QT_QPA_PLATFORM=offscreen','python',str(destination/'08-08-target-job.py')]
result=subprocess.run(command,env=env,capture_output=True,text=True,timeout=10);assert result.returncode==0,result.stderr
print(json.dumps(dict(unit=unit,root=str(destination),launch_exit=result.returncode)))'''
    print(guest(code))
elif sys.argv[1]=='context':
    guest('pass')
    subprocess.run(['scp','-q','-o','BatchMode=yes','-o','HostKeyAlias=lookup-gsd-07','-o','UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-P','2227',str(root/'08-08-target-context-job.py'),'archvm:/home/arch/lookup-08-08-target-context-job.py'],check=True,timeout=30)
    print(guest("import shutil,os,subprocess; p=Path("+repr(destination)+")/'08-08-target-context-job.py';shutil.copyfile('/home/arch/lookup-08-08-target-context-job.py',p);os.chown(p,1001,1001);r=subprocess.run(['sudo','-n','-H','-u','lookup07','env','XDG_RUNTIME_DIR=/run/user/1001','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1001/bus','systemd-run','--user','--unit=lookup-ocr-context-08-08','--service-type=exec','--property=WorkingDirectory='+str(p.parent),'--property=RuntimeMaxSec=1800','--setenv=QT_QPA_PLATFORM=offscreen','python',str(p)],capture_output=True,text=True,timeout=10);assert r.returncode==0,r.stderr;print(r.stdout)"))
elif sys.argv[1]=='lifecycle':
    import hashlib,tarfile
    paths=['tools/check_games.py','tests/test_app.py','tests/test_app_gui.py','tests/test_check_games.py','tests/test_ocr_game_sources.py']
    paths += [str(root/('08-06-raw-control-'+token+'-'+side+'.png')) for token in ('522383335795','583541202128') for side in ('before','after')]
    archive=root/'08-08-target-lifecycle.tar'
    with tarfile.open(archive,'w') as bundle:
        for path in paths:bundle.add(path,arcname=path)
        bundle.add(root/'08-08-target-lifecycle-job.py',arcname='08-08-target-lifecycle-job.py')
    guest('pass')
    subprocess.run(['scp','-q','-o','BatchMode=yes','-o','HostKeyAlias=lookup-gsd-07','-o','UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-P','2227',str(archive),'archvm:/home/arch/lookup-08-08-lifecycle.tar'],check=True,timeout=30)
    code="import tarfile,os,hashlib,subprocess;p=Path("+repr(destination)+");a=Path('/home/arch/lookup-08-08-lifecycle.tar');assert hashlib.sha256(a.read_bytes()).hexdigest()=="+repr(hashlib.sha256(archive.read_bytes()).hexdigest())+"\nwith tarfile.open(a) as bundle:bundle.extractall(p,filter='data')\nfor q in p.rglob('*'):os.chown(q,1001,1001)\nr=subprocess.run(['sudo','-n','-H','-u','lookup07','env','XDG_RUNTIME_DIR=/run/user/1001','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1001/bus','systemd-run','--user','--unit=lookup-ocr-lifecycle-08-08-retry','--service-type=exec','--property=WorkingDirectory='+str(p),'--property=RuntimeMaxSec=600','--setenv=QT_QPA_PLATFORM=offscreen','python',str(p/'08-08-target-lifecycle-job.py')],capture_output=True,text=True,timeout=10);assert r.returncode==0,r.stderr;print(r.stdout)"
    print(guest(code))
elif sys.argv[1]=='status-lifecycle':
    value=json.loads(guest('print((Path('+repr(destination)+")/'08-08-target-lifecycle.json').read_text())"))
    (root/'08-08-target-final-focused.json').write_text(json.dumps(value,indent=2));print(json.dumps(value))
else:
    name='08-08-target-context-progress.json' if sys.argv[1]=='status-context' else '08-08-target-progress.json'
    value=json.loads(guest('print((Path('+repr(destination)+')/'+repr(name)+').read_text())'))
    (root/('08-08-target-context-corpus.json' if sys.argv[1]=='status-context' else '08-08-target-corpus.json')).write_text(json.dumps(value,indent=2))
    print(json.dumps(dict(state=value['state'],active=value.get('active'),steps=[dict(name=row['name'],exit=row['exit']) for row in value['steps']],error=value.get('error'))))
