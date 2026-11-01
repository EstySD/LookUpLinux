"""Owned AssaultCube pilot cleanup, including failed setup; no personal data removal."""
import hashlib,json,os,signal,subprocess,time
from pathlib import Path

if '--status' in __import__('sys').argv:
    assert os.getuid()==1001
    os.environ.update(XDG_RUNTIME_DIR='/run/user/1001',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/1001/bus')
    from PyQt6.QtCore import QCoreApplication,QMetaType
    from PyQt6.QtGui import QKeySequence
    from PyQt6.QtDBus import QDBusConnection,QDBusMessage,QDBusArgument,QDBus
    app=QCoreApplication([]);bus=QDBusConnection.sessionBus()
    owner=bus.interface().isServiceRegistered('org.lookup.Linux')
    assert owner.isValid()
    message=QDBusMessage.createMethodCall('org.kde.kglobalaccel','/kglobalaccel','org.kde.KGlobalAccel','allActionsForComponent')
    message.setArguments([QDBusArgument(['org.lookup.Linux.desktop','','',''],QMetaType.Type.QStringList.value)])
    reply=bus.call(message,QDBus.CallMode.Block,1200);assert reply.type()!=QDBusMessage.MessageType.ErrorMessage
    keys=[]
    for action in reply.arguments()[0] or []:
        if tuple(action[:2])!=('org.lookup.Linux.desktop','_launch'):continue
        message=QDBusMessage.createMethodCall('org.kde.kglobalaccel','/kglobalaccel','org.kde.KGlobalAccel','shortcut')
        message.setArguments([QDBusArgument(action,QMetaType.Type.QStringList.value)])
        reply=bus.call(message,QDBus.CallMode.Block,1200);assert reply.type()!=QDBusMessage.MessageType.ErrorMessage
        keys.extend(QKeySequence(key).toString(QKeySequence.SequenceFormat.PortableText) for key in reply.arguments()[0] if key)
    print(json.dumps(dict(owner=bool(owner.value()),keys=keys,at_ns=time.monotonic_ns())))
    raise SystemExit
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
if marker.exists() and run(['pacman','-Q','lookup-linux'])['exit']==0:
    receipt=json.loads(marker.read_text());assert receipt['baseline_absent'] is True
    report['package']=run(['pacman','-R','--noconfirm','lookup-linux'])
report['package_absent']=run(['pacman','-Q','lookup-linux'])['exit']!=0
report['retention_hashes_before']=before
report['retained']=all(pathlib.is_file() and hashlib.sha256(pathlib.read_bytes()).hexdigest()==digest for name,digest in before.items() for pathlib in [Path(name)])
report['installed_entry_absent']=not Path('/usr/share/applications/org.lookup.Linux.desktop').exists()
baseline=json.loads((root/'retention-before.json').read_text())
report['original_data_retained']=all(Path(name).is_file() and hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest for name,digest in baseline.items())
report['registry']=user(['python','-c',Path(__file__).read_text(),'--status'])
report['finished_ns']=time.monotonic_ns()
print(json.dumps(report))


# Phase09 current-profile readback, after the original owned removal procedure.
assert Path('/sys/class/dmi/id/product_uuid').read_text().strip()=='097920cf-b594-494b-8bd8-ccff973c1dc8'
expected09=json.loads(Path('/home/arch/lookup-cascade-09-retention.json').read_text())
observed09={name:hashlib.sha256(Path(name).read_bytes()).hexdigest() if Path(name).is_file() and not Path(name).is_symlink() else None for name in expected09}
remaining09=[]
for process09 in Path('/proc').glob('[0-9]*'):
    try:
        if process09.stat().st_uid!=1001:continue
        argv09=(process09/'cmdline').read_bytes().split(b'\0');fields09=(process09/'stat').read_text().split(') ',1)[1].split()
        owned09=any(value in argv09 for value in (b'/home/lookup07/check_games.py',b'/home/lookup07/check_hardening_09.py',b'/home/lookup07/check_fallback_09.py',b'/usr/bin/lookup',b'/home/lookup07/.local/state/lookup-games-08/assaultcube/package/bin_unix/linux_64_client'))
        if owned09 and fields09[0]!='Z':remaining09.append(dict(pid=int(process09.name),start=int(fields09[19]),argv=[os.fsdecode(value) for value in argv09 if value]))
    except (FileNotFoundError,ProcessLookupError):pass
supplement09=dict(expected=expected09,observed=observed09,retained=observed09==expected09,remaining=remaining09,package_absent=run(['pacman','-Q','lookup-linux'])['exit']!=0,at_ns=time.monotonic_ns())
Path('/home/arch/lookup-cascade-09-cleanup-readback.json').write_text(json.dumps(supplement09,indent=2))
print('lookup09-retention:'+json.dumps(supplement09))
