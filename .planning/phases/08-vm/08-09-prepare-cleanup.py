"""Actual tray/game/observer stops, exact product key clear and retained data receipt."""
import json,runpy
from pathlib import Path
root=Path('.planning/phases/08-vm');s=runpy.run_path(str(root/'08-09-fixture-support.py'));n=s['n'];m=s['m']
record={}
for name,operation in (('fixture_observer',lambda:s['command'](dict(action='stop-observer'))),
    ('product_tray',lambda:m['command'](dict(action='stop-lookup'))),('game',lambda:m['command'](dict(action='stop')))):
    try:record[name]=dict(ok=True,result=operation())
    except BaseException as error:record[name]=dict(ok=False,error=repr(error))
    (root/'08-09-pre-cleanup-stops.json').write_text(json.dumps(record,indent=2))
code='''import sys,os,json,configparser,time
from pathlib import Path
sys.path.insert(0,'/usr/lib/lookup/app')
from lookup import platform,lifecycle
os.environ.update(platform.session_env())
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtDBus import QDBusConnection
application=QCoreApplication([])
def unrelated():
    parser=configparser.ConfigParser(interpolation=None,strict=False);parser.optionxform=str;parser.read(Path.home()/'.config/kglobalshortcutsrc')
    return {name:dict(parser[name]) for name in parser.sections() if name!='org.lookup.Linux.desktop'}
before=unrelated();registry=lifecycle.ShortcutRegistry();binding=registry.inspect();registry._replace(binding.action,())
time.sleep(.5);observed=registry.inspect()
print(json.dumps(dict(action=binding.action,before=list(binding.keys),after=list(observed.keys),unrelated_preserved=before==unrelated(),owner=QDBusConnection.sessionBus().interface().isServiceRegistered('org.lookup.Linux').value())))'''
payload=n['guest']("import subprocess;p=subprocess.run(['sudo','-n','-H','-u','lookup07','python','-c',"+repr(code)+"],capture_output=True,text=True,timeout=10);print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)")
(root/'08-09-product-key-cleared.json').write_text(payload)
payload=n['guest']('''import hashlib,json
from pathlib import Path
home=Path('/home/lookup07');base=home/'.local/state/lookup-games-08/assaultcube'
original=json.loads((base/'retention-before.json').read_text());paths=set(original)
for directory in (base/'lookup',home/'.local/state/lookup-hardening-09'):
    paths.update(str(path) for path in directory.rglob('*') if path.is_file() and not path.is_symlink() and ('.db' in path.name or path.name=='config.json'))
observed={name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in sorted(paths)}
backup=home/'.local/state/lookup-hardening-09/series/retained-config-before.bin'
observed[str(home/'.config/lookup/config.json')]=hashlib.sha256(backup.read_bytes()).hexdigest()
assert all(observed[name]==digest for name,digest in original.items())
target=Path('/home/arch/lookup-cascade-09-retention.json');target.write_text(json.dumps(observed,indent=2))
print(json.dumps(dict(expected_after_cleanup=observed,original_baseline_unchanged=True,normal_config_expected='exact pre-prepare backup bytes')))''')
(root/'08-09-retention-before-cleanup.json').write_text(payload)
print(json.dumps(record));print('Owned key cleared; retained data receipt saved; controller finally remains responsible for profile restore/removal/shutdown.')
