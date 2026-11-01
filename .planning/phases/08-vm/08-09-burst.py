"""Existing ten-chord acceptance protocol on the real sparse fixture display."""
import base64,hashlib,json,runpy,subprocess,time
from pathlib import Path
from tools import check_hardening as hardening
root=Path('.planning/phases/08-vm');support=runpy.run_path(str(root/'08-09-fixture-support.py'));n=support['n'];resources=support['resources']

def command(value):
    if value['action'] in ('history','resource'):
        row=resources['snapshot']();return row['history'] if value['action']=='history' else row
    if value['action'] in ('trace','last-trigger'):
        deadline=time.monotonic()+4
        while True:
            text=n['guest']("print(__import__('pathlib').Path('/home/lookup07/.local/state/lookup-games-08/assaultcube/lookup/daemon.log').read_text())")
            rows=hardening.chronological(json.loads(line.split(':',1)[1]) for line in text.splitlines() if line.startswith('lookup-timing:'))
            rows=[row for row in rows if row['pid']==resources['pid'] and row['mono_ns']>=value.get('since_ns',0)]
            if value['action']=='trace':return rows
            matches=[row for row in rows if row['stage']==1 and row['request']>value.get('after',0)]
            if matches:return matches[-1]
            if time.monotonic()>deadline:raise TimeoutError('actual_trigger')
            time.sleep(.03)
    return support['command'](value)

def inputs(action,**values):
    if action!='Burst':return n['inputs'](action,**values)
    result=subprocess.run(['powershell','-NoProfile','-File',str(root/'08-09-burst.ps1')],capture_output=True,text=True,timeout=8,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    n['audit'](dict(transport='UUID/disk/MAC/NAT COM physical burst',action='Burst',chords=10,cadence_ms=50,exit=result.returncode))

if __name__=='__main__':
    print(support['command'](dict(action='stop-observer')),flush=True)
    code=(root/'08-09-fixture-observer.py').read_text(encoding='utf-8')
    code=code.replace("SCENES=(('name','name'),)","SCENES=(('name','name'),('name','name'))")
    code=code.replace("str(root/'data/history.db')+'?mode=ro'","'/home/lookup07/.local/state/lookup-games-08/assaultcube/lookup/data/history.db?mode=ro'")
    (root/'08-09-burst-observer.py').write_text(code,encoding='utf-8',newline='\n')
    previous=json.loads((root/'08-09-fixture-declaration.json').read_text())['observer_sha256']
    print(n['guest']('''import base64,hashlib,subprocess
from pathlib import Path
path=Path('/home/lookup07/check_fallback_09.py');assert hashlib.sha256(path.read_bytes()).hexdigest()=='''+repr(previous)+'''
path.write_bytes(base64.b64decode('''+repr(base64.b64encode(code.encode()).decode())+'''))
p=subprocess.run(['sudo','-n','-H','-u','lookup07','python',str(path),'--start-probe','--continuous'],capture_output=True,text=True,timeout=8);print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)'''),flush=True)
    hardening.vm_input=inputs;hardening.vm_command=command
    report=hardening.run_burst(root/'08-09-burst-attempt.json');print(json.dumps(report),flush=True)
