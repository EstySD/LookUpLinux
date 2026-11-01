"""Fresh, classified native privacy proof; earlier unclassified reads stay limited."""
import base64,json,runpy
from pathlib import Path
root=Path('.planning/phases/08-vm');s=runpy.run_path(str(root/'08-09-fixture-support.py'));n=s['n']

def read():
    code='''import sys,subprocess,json,hashlib
from pathlib import Path
sys.path.insert(0,'/usr/lib/lookup/app')
from lookup import platform
env=platform.session_env();rows={}
for name,extra in (('primary',['--primary']),('clipboard',[])):
    p=subprocess.run(['wl-paste',*extra,'--no-newline'],env=env,capture_output=True,timeout=3)
    rows[name]=dict(exit=p.returncode,stdout_sha256=hashlib.sha256(p.stdout).hexdigest(),stderr=p.stderr.decode(),socket_exists=Path(env['XDG_RUNTIME_DIR'],env['WAYLAND_DISPLAY']).is_socket())
print(json.dumps(rows))'''
    payload=n['guest']("import subprocess;p=subprocess.run(['sudo','-n','-H','-u','lookup07','python','-c',"+repr(code)+"],capture_output=True,text=True,timeout=10);print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)")
    actual=s['resources']['snapshot']()
    return dict(classified=json.loads(payload),typed=n['command'](dict(action='privacy')),
        actual_data_scan=dict(png_files=actual['png_files'],scanned=actual['scanned'],at_ns=actual['at_ns']))

if __name__=='__main__':
    path=root/'08-09-privacy-proof.json';assert not path.exists()
    data=dict(before=read(),limit='Earlier twenty-call top wl-paste reads lack retained stderr; not retroactively classified. Nested resource clipboard probes are excluded.')
    path.write_text(json.dumps(data,indent=2))
    n['inputs']('Keys',Codes='01 81')
    ready=s['command'](dict(action='arm',attempt=3,group='privacy',case=1,scene=1))
    n['inputs']('Pointer',X=733,Y=378,Buttons=0);n['inputs']('Keys',Codes='e0 5b 2a 12 92 aa e0 db')
    data['timing']=s['command'](dict(action='result',attempt=3,token=ready['token']))
    key='-'.join(str(data['timing'][name]) for name in ('pid','run','request'))
    data['source']=json.loads(n['guest']("print(__import__('pathlib').Path('/home/lookup07/.local/state/lookup-games-08/assaultcube/lookup/observations/request-"+key+".json').read_text())"))
    frame=s['command'](dict(action='frame',attempt=3,token=ready['token']))
    (root/'08-09-privacy-useful.png').write_bytes(base64.b64decode(frame['png_base64']))
    n['inputs']('Keys',Codes='01 81');data['after']=read()
    valid=all(row['socket_exists'] and (row['exit']==0 or row['exit']==1 and row['stderr'].strip()=='Nothing is copied') for phase in ('before','after') for row in data[phase]['classified'].values())
    data['passed']=valid and data['timing']['status']=='success' and [row['psm'] for row in data['source']['ocr_passes']]==[6,11]
    data['passed']=data['passed'] and all(data['before']['typed'][name]==data['after']['typed'][name] for name in ('primary','clipboard','klipper'))
    data['passed']=data['passed'] and data['before']['actual_data_scan']['png_files']==data['after']['actual_data_scan']['png_files']==[] and data['before']['typed']['png_files']==data['after']['typed']['png_files']==[]
    path.write_text(json.dumps(data,indent=2));print(json.dumps(dict(passed=data['passed'],before=data['before']['classified'],after=data['after']['classified'])))
