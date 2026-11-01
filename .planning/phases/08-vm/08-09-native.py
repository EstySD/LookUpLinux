"""Current-package native transport; every SSH payload checks the owned DMI."""
import base64,hashlib,json,subprocess,time
from pathlib import Path

ROOT=Path('.planning/phases/08-vm')
CLONE='cf207909-94b5-4b49-8bd8-ccff973c1dc8'
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=5','-o','HostKeyAlias=lookup-gsd-07',
    '-o','UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-p','2227','archvm']
DMI="from pathlib import Path;assert Path('/sys/class/dmi/id/product_uuid').read_text().strip()=='097920cf-b594-494b-8bd8-ccff973c1dc8'\n"

def audit(value):
    with (ROOT/'08-09-actions.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(dict(at_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),target=CLONE,**value))+'\n')

def guest(script,timeout=30):
    payload=DMI+script
    result=subprocess.run(SSH+['sudo','-n','python','-'],input=payload,
        capture_output=True,text=True,encoding='utf-8',timeout=timeout)
    audit(dict(transport='pinned SSH2227+DMI',payload_sha256=hashlib.sha256(payload.encode()).hexdigest(),exit=result.returncode))
    if result.returncode:raise RuntimeError((result.stderr or result.stdout)[-2000:])
    return result.stdout

def inputs(action,**values):
    args=['powershell','-NoProfile','-File',str(ROOT/'08-06-owned-input.ps1'),'-Action',action]
    for key,value in values.items():args+=['-'+key,str(value)]
    result=subprocess.run(args,capture_output=True,text=True,timeout=8,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    audit(dict(transport='UUID/disk/MAC/NAT physical guard',action=action,values=values,exit=result.returncode))
    return dict(exit=result.returncode,target=CLONE)

def command(value):
    encoded=base64.b64encode(json.dumps(value).encode()).decode()
    code="import subprocess;p=subprocess.run(['sudo','-n','-H','-u','lookup07','python','/home/lookup07/check_hardening_09.py','--guest-command',"+repr(encoded)+"],capture_output=True,text=True,timeout=25);print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)"
    return json.loads(guest(code,timeout=30))

def cleanup():
    results={}
    for action in ('stop-owner','cleanup-profile'):
        try:results[action]=command(dict(action=action))
        except BaseException as error:results[action]=dict(error=repr(error))
    try:results['product']=guest("import subprocess;p=subprocess.run(['python','/home/arch/lookup-games-08-pilot-cleanup.py'],capture_output=True,text=True,timeout=45);print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)",timeout=50)
    except BaseException as error:results['product']=dict(error=repr(error))
    (ROOT/'08-09-guest-cleanup.json').write_text(json.dumps(results,indent=2))
    return results
