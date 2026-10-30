"""Owned AssaultCube pilot cleanup, including failed setup; no personal data removal."""
import hashlib,json,os,signal,subprocess,time
from pathlib import Path

assert os.getuid()==0
home=Path('/home/lookup07');root=home/'.local/state/lookup-games-08/assaultcube'
assert home.stat().st_uid==1001 and root.is_relative_to(home)
env=dict(os.environ,XDG_RUNTIME_DIR='/run/user/1001',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/1001/bus')
def run(args):
    p=subprocess.run(args,env=env,capture_output=True,text=True,timeout=15)
    return dict(exit=p.returncode,stdout=p.stdout,stderr=p.stderr)
def user(args):return run(['sudo','-n','-H','-u','lookup07',*args])
report=dict(processes=[],package=None,retained=True)
for path in Path('/proc').glob('[0-9]*'):
    try:
        if path.stat().st_uid!=1001:continue
        argv=(path/'cmdline').read_bytes().split(b'\0');stat=(path/'stat').read_text().split(') ',1)[1].split()
        owned=(os.fsencode(str(root/'package/bin_unix/linux_64_client')) in argv or
               b'/home/lookup07/check_games.py' in argv and (path/'environ').read_bytes().find(b'LOOKUP_GAME_KIND=assaultcube')>=0)
        if not owned:continue
        pid=int(path.name);start=int(stat[19]);os.kill(pid,signal.SIGTERM)
        report['processes'].append(dict(pid=pid,start=start,uid=1001,signal='SIGTERM'))
    except (FileNotFoundError,ProcessLookupError):pass
time.sleep(1)
report['remaining']=[]
for old in report['processes']:
    path=Path('/proc',str(old['pid']))
    if path.exists():
        fields=(path/'stat').read_text().split(') ',1)[1].split()
        if path.stat().st_uid==1001 and int(fields[19])==old['start'] and fields[0]!='Z':report['remaining'].append(old)
before={}
for path in list(root.rglob('*.db'))+list(root.rglob('config.json')):
    before[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
marker=root/'package-reinstalled.json'
if marker.exists():
    receipt=json.loads(marker.read_text());assert receipt['baseline_absent'] is True
    report['package']=run(['pacman','-R','--noconfirm','lookup-linux'])
report['package_absent']=run(['pacman','-Q','lookup-linux'])['exit']!=0
report['retention_hashes_before']=before
report['retained']=all(pathlib.is_file() and hashlib.sha256(pathlib.read_bytes()).hexdigest()==digest for name,digest in before.items() for pathlib in [Path(name)])
report['installed_entry_absent']=not Path('/usr/share/applications/org.lookup.Linux.desktop').exists()
report['finished_ns']=time.monotonic_ns()
print(json.dumps(report))
