"""One guarded clone-only OCR corpus lifetime; historical06 evidence stays immutable."""
import json,shlex,subprocess,time
from pathlib import Path
from tools.check_games import pilot_cleanup_steps
from tools.check_hardening import write_record
import runpy
adapter=runpy.run_path(str(Path('.planning/phases/08-vm/08-09-native.py')))

root=Path('.planning/phases/08-vm');stop=root/'08-09-native-stop.json'
vbox='C:/Program Files/Oracle/VirtualBox/VBoxManage.exe'
clone='cf207909-94b5-4b49-8bd8-ccff973c1dc8';original='abc73254-ddf7-4f1f-9c66-7c2fcc5254d7'
actions=[]
def run(*args):
    assert args[0]==vbox and args[2] in (clone,original) and (args[1]=='showvminfo' or args[2]==clone)
    result=subprocess.run(args,capture_output=True,text=True,timeout=30)
    actions.append(dict(argv=list(args),exit=result.returncode,mutating=args[1]!='showvminfo'))
    return dict(exit=result.returncode,stdout=result.stdout,stderr=result.stderr)
def info(identity):
    result=run(vbox,'showvminfo',identity,'--machinereadable');assert result['exit']==0
    value=dict(line.split('=',1) for line in result['stdout'].splitlines() if '=' in line)
    return {key:value.get(key) for key in ('UUID','VMState')} if identity==original else value
prior=info(clone);record=dict(prior=prior,original_before=info(original),host_actions=actions)
try:
    assert prior['UUID']=='"'+clone+'"' and prior['VMState']=='"poweroff"'
    assert prior['"SATA-ImageUUID-0-0"']=='"2712d710-daaa-449c-843d-d570091127bc"'
    assert run(vbox,'modifyvm',clone,'--clipboard-mode','disabled','--accelerate-3d','off')['exit']==0
    assert run(vbox,'startvm',clone,'--type','headless')['exit']==0
    write_record(root/'08-09-native-controller-state.json',dict(state='running',pid=__import__('os').getpid()))
    deadline=time.monotonic()+7200
    while time.monotonic()<deadline and not stop.exists():time.sleep(1)
    record['stop']=json.loads(stop.read_text()) if stop.exists() else dict(reason='bounded_native_deadline')
except BaseException as error:record['error']=repr(error)
finally:
    def guest(command):
        if command=='sudo -n python /home/arch/lookup-games-08-pilot-cleanup.py':return adapter['cleanup']()
        import shlex
        return adapter['guest']('import subprocess;subprocess.run('+repr(shlex.split(command))+',check=True,timeout=15)')
    inputs=adapter['inputs']
    pilot_cleanup_steps(prior,record,info,run,guest,inputs)
    record['original_state_respected']=all(row['argv'][2]==clone for row in actions if row['mutating'])
    record['policy']='USER_KEEP_RUNNING; no original state equality gate'
    write_record(root/'08-09-native-cleanup.json',record)
    write_record(root/'08-09-native-controller-state.json',dict(state='finished'))
