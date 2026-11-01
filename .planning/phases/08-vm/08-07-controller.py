"""One bounded post-manual validation lifetime with independent finally steps."""
import hashlib,json,runpy,subprocess,time
from pathlib import Path
root=Path('.planning/phases/08-vm');adapter=runpy.run_path(str(root/'08-07-native.py'))
vbox='C:/Program Files/Oracle/VirtualBox/VBoxManage.exe';clone=adapter['CLONE'];original='abc73254-ddf7-4f1f-9c66-7c2fcc5254d7';actions=[]
def run(*argv):
    assert argv[0]==vbox and argv[2] in (clone,original) and (argv[1]=='showvminfo' or argv[2]==clone)
    child=subprocess.run(argv,capture_output=True,text=True,timeout=30);actions.append(dict(argv=list(argv),exit=child.returncode,mutating=argv[1]!='showvminfo'))
    return dict(exit=child.returncode,stdout=child.stdout,stderr=child.stderr)
def info(identity):
    result=run(vbox,'showvminfo',identity,'--machinereadable');assert result['exit']==0
    value=dict(line.split('=',1) for line in result['stdout'].splitlines() if '=' in line)
    return {key:value.get(key) for key in ('UUID','VMState')} if identity==original else value
def save(name,value):(root/name).write_text(json.dumps(value,indent=2))
def attempt(name,operation):
    try:record[name]=dict(ok=True,result=operation())
    except BaseException as error:record[name]=dict(ok=False,error=repr(error))
    save('08-07-controller-observations.json',record)
    return record[name]
prior=info(clone);record=dict(prior=prior,original_before=info(original),host_actions=actions)
try:
    assert prior['UUID']=='"'+clone+'"' and prior['VMState']=='"poweroff"' and prior['name']=='"lookup-gsd-07"'
    assert prior['"SATA-ImageUUID-0-0"']=='"2712d710-daaa-449c-843d-d570091127bc"' and prior['macaddress1']=='"080027A05376"'
    assert prior['Forwarding(0)']=='"lookup-gsd-07-ssh,tcp,127.0.0.1,2227,,22"'
    assert run(vbox,'startvm',clone,'--type','headless')['exit']==0
    save('08-07-controller-state.json',dict(state='running',pid=__import__('os').getpid()))
    deadline=time.monotonic()+7200
    while time.monotonic()<deadline and not (root/'08-07-controller-stop.json').exists():time.sleep(1)
finally:
    attempt('release',lambda:adapter['inputs']('Keys',Codes='8f 81 91 9f 9e a0 aa b6 e0 db e0 dc'))
    attempt('mouse_release',lambda:adapter['inputs']('Pointer',X=640,Y=400,Buttons=0))
    cleanup=root/'08-07-guest-cleanup.py'
    if cleanup.exists():
        source=cleanup.read_text(encoding='utf-8');record['cleanup_source_sha256']=hashlib.sha256(source.encode()).hexdigest()
        attempt('guest_cleanup',lambda:adapter['guest'](source,timeout=60))
    else:record['guest_cleanup']=dict(ok=False,error='No post-manual cleanup source established; no stale profile restore attempted.')
    attempt('shutdown',lambda:adapter['guest']("import subprocess;subprocess.run(['systemctl','poweroff'],check=True,timeout=10)"))
    deadline=time.monotonic()+45
    poll=0
    while time.monotonic()<deadline:
        poll+=1
        current=attempt('power_poll_'+str(poll),lambda:info(clone)).get('result',{})
        if current.get('VMState')=='"poweroff"':break
        time.sleep(1)
    current=attempt('power_before_restore',lambda:info(clone)).get('result',{})
    if current.get('UUID')=='"'+clone+'"' and current.get('VMState')=='"poweroff"':
        attempt('restore',lambda:run(vbox,'modifyvm',clone,'--accelerate-3d',prior['accelerate3d'].strip('"'),'--clipboard-mode',prior['clipboard'].strip('"')))
    else:record['restore']=dict(ok=False,error='Not OFF; refusing settings change')
    record['final_clone']=attempt('final_clone_readback',lambda:info(clone)).get('result',{})
    record['original_after']=attempt('original_readback',lambda:info(original)).get('result',{})
    record['original_state_respected']=all(row['argv'][2]==clone for row in actions if row['mutating'])
    save('08-07-controller-observations.json',record);save('08-07-controller-state.json',dict(state='finished'))
