"""Actual loaded archives, installed member bytes and per-frame raw proc/trace."""
import base64,hashlib,json,runpy,sys,time
from pathlib import Path
from tools import check_hardening as hardening

root=Path('.planning/phases/08-vm');native=runpy.run_path(str(root/'08-09-native.py'))
guest=native['guest'];command=native['command']
inventory=hardening._expected_source_inventory()

def setup():
    helper=Path('tools/check_hardening.py').read_bytes().replace(b'\r\n',b'\n').replace(b'lookup-hardening-08',b'lookup-hardening-09').replace(b'check_hardening.py',b'check_hardening_09.py')
    value=guest('''import base64,hashlib,json,os,subprocess
from pathlib import Path
data=base64.b64decode('''+repr(base64.b64encode(helper).decode())+''')
path=Path('/home/lookup07/check_hardening_09.py');assert not path.exists()
path.write_bytes(data);os.chown(path,1001,1001)
events=[]
for event in Path('/sys/class/input').glob('event*'):
    if event.joinpath('device/name').read_text().strip() in ('AT Translated Set 2 keyboard','ImExPS/2 Generic Explorer Mouse','VirtualBox USB Tablet','VirtualBox mouse integration'):events.append('/dev/input/'+event.name)
subprocess.run(['setfacl','-m','u:lookup07:r',*events],check=True)
print(json.dumps(dict(helper_sha256=hashlib.sha256(data).hexdigest(),temporary_acl=events)))''')
    (root/'08-09-helper-setup.json').write_text(value)
    build=json.loads((root/'08-09-actual-build.json').read_text())
    script='''import base64,hashlib,json,time
from pathlib import Path
members='''+repr({name:hardening._package_member(name) for name in inventory})+'''
observed={name:hashlib.sha256(Path('/'+path).read_bytes()).hexdigest() for name,path in members.items()}
package=Path('''+repr(build['package_path'])+''').read_bytes()
print(json.dumps(dict(members=observed,observed_ns=time.monotonic_ns(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),package_base64=base64.b64encode(package).decode())))'''
    installed=json.loads(guest(script));package=base64.b64decode(installed.pop('package_base64'))
    assert installed['members']==inventory and hashlib.sha256(package).hexdigest()==build['package_sha256']
    (root/'08-09-build/lookup-linux-0.1.0-1-x86_64.pkg.tar.zst').write_bytes(package)
    receipt=dict(stage_exit=0,build_exit=build['build_exit'],install_exit=build['install_exit'],
        build=dict(source_sha256=build['source_sha256'],package_sha256=build['package_sha256'],ocr_sha256=inventory['lookup/ocr.py']),
        installation=dict(members=installed['members'],boot_id=installed['boot_id'],completed_ns=build['completed_ns']),
        installed_readback=installed,revision=__import__('subprocess').check_output(['git','rev-parse','HEAD'],text=True).strip())
    (root/'08-09-package-receipt.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps(dict(installed_members=len(inventory),build=receipt['build'])),flush=True)
    print(command(dict(action='prepare')),flush=True)
    print(guest("import subprocess;p=subprocess.run(['sudo','-n','-H','-u','lookup07','python','/home/lookup07/check_hardening_09.py','--start-probe','--continuous'],capture_output=True,text=True,timeout=8);print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)"),flush=True)

def bound_command(value):
    result=command(value)
    if value['action']!='result' or result.get('status')!='success':return result
    script='''import base64,hashlib,json,os,subprocess,time
from pathlib import Path
row='''+repr(result)+'''
process=Path('/proc',str(row['pid']));assert process.stat().st_uid==1001
members='''+repr({name:hardening._package_member(name) for name in inventory})+'''
trace=subprocess.run(['sudo','-n','-H','-u','lookup07','env','XDG_RUNTIME_DIR=/run/user/1001','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1001/bus','journalctl','--user','-b','--no-pager','-o','cat','-g','^lookup-timing:','-n','5000'],capture_output=True,text=True,check=True,timeout=5).stdout
raw=dict(stat=(process/'stat').read_text(),status=(process/'status').read_text(),cmdline_base64=base64.b64encode((process/'cmdline').read_bytes()).decode(),
    clock_ticks=os.sysconf('SC_CLK_TCK'),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
    members={name:hashlib.sha256(Path('/'+path).read_bytes()).hexdigest() for name,path in members.items()},timing_text=trace,observed_ns=time.monotonic_ns())
directory=Path('/home/lookup07/.local/state/lookup-hardening-09/series')
files={name:base64.b64encode((directory/name).read_bytes()).decode() for name in ('probe-useful.png','inputs.jsonl','ready.json','result.json')}
print(json.dumps(dict(runtime=raw,files=files)))'''
    observation=json.loads(guest(script));raw=json.dumps(observation['runtime'],sort_keys=True,separators=(',',':')).encode()
    digest=hashlib.sha256(raw).hexdigest();result['runtime_sha256']=digest
    directory=root/'08-09-runtime';directory.mkdir(exist_ok=True)
    (directory/(digest+'.json')).write_bytes(raw)
    for name,encoded in observation['files'].items():(directory/(str(result['attempt'])+'-'+name)).write_bytes(base64.b64decode(encoded))
    return result

def assemble():
    rows=json.loads((root/'08-09-performance-attempts.json').read_text())
    receipt=json.loads((root/'08-09-package-receipt.json').read_text())
    artifacts=dict(source=(root/'08-09-build/lookup-source.tar.gz').read_bytes(),package=(root/'08-09-build/lookup-linux-0.1.0-1-x86_64.pkg.tar.zst').read_bytes(),
        runtime={path.stem:path.read_bytes() for path in (root/'08-09-runtime').glob('*.json') if len(path.stem)==64})
    report=hardening.current_performance_report(rows,receipt,artifacts)
    (root/'08-09-performance-current-report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({key:report.get(key) for key in ('passed','source_bound','successful','median_ms','p95_ms','source_error')}),flush=True)

if __name__=='__main__':
    if sys.argv[1]=='setup':setup()
    elif sys.argv[1]=='run':
        hardening.vm_input=native['inputs'];hardening.vm_command=bound_command
        hardening.run_performance(root/'08-09-performance-attempts.json');assemble()
    elif sys.argv[1]=='assemble':assemble()
