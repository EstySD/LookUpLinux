"""Post-manual clone-only transport; never restore a pre-manual profile."""
import hashlib,json,subprocess,time
from pathlib import Path
ROOT=Path('.planning/phases/08-vm');CLONE='cf207909-94b5-4b49-8bd8-ccff973c1dc8'
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=5','-o','HostKeyAlias=lookup-gsd-07','-o','UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-p','2227','archvm']
DMI="from pathlib import Path;assert Path('/sys/class/dmi/id/product_uuid').read_text().strip()=='097920cf-b594-494b-8bd8-ccff973c1dc8'\n"
def audit(value):
    with (ROOT/'08-07-actions.jsonl').open('a',encoding='utf-8') as output:output.write(json.dumps(dict(target=CLONE,at_ns=time.time_ns(),**value))+'\n')
def guest(script,timeout=30):
    payload=DMI+script
    child=subprocess.run(SSH+['sudo','-n','python','-'],input=payload,capture_output=True,text=True,encoding='utf-8',timeout=timeout)
    audit(dict(transport='pinned2227+commonDMI',payload_sha256=hashlib.sha256(payload.encode()).hexdigest(),exit=child.returncode))
    if child.returncode:raise RuntimeError((child.stderr or child.stdout)[-2000:])
    return child.stdout
def inputs(action,**values):
    argv=['powershell','-NoProfile','-File',str(ROOT/'08-06-owned-input.ps1'),'-Action',action]
    for key,value in values.items():argv+=['-'+key,str(value)]
    child=subprocess.run(argv,capture_output=True,text=True,timeout=8,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    audit(dict(transport='fixedUUID/disk/MAC/NATphysical',action=action,values=values,exit=child.returncode))
    return dict(exit=child.returncode,target=CLONE)
