"""Owned clone lifetime after takeover; original intentionally stays running."""
import json,subprocess,time
from pathlib import Path
from tools.check_games import pilot_cleanup_steps
from tools.check_hardening import write_record
from tools.check_hardening_install import ssh

root=Path('.planning/phases/08-vm')
stop=root/'08-06-takeover-stop.json'
vbox='C:/Program Files/Oracle/VirtualBox/VBoxManage.exe'
clone='cf207909-94b5-4b49-8bd8-ccff973c1dc8'
original='abc73254-ddf7-4f1f-9c66-7c2fcc5254d7'
actions=[]
def run(*args):
    assert args[0]==vbox and args[1] in ('showvminfo','modifyvm','startvm','controlvm')
    assert args[2] in (clone,original) and (args[1]=='showvminfo' or args[2]==clone)
    result=subprocess.run(args,capture_output=True,text=True,timeout=30)
    actions.append(dict(argv=list(args),exit=result.returncode,mutating=args[1]!='showvminfo'))
    return dict(exit=result.returncode,stdout=result.stdout,stderr=result.stderr)
def info(identity):
    result=run(vbox,'showvminfo',identity,'--machinereadable')
    if result['exit']:raise RuntimeError('vm_readback')
    value=dict(line.split('=',1) for line in result['stdout'].splitlines() if '=' in line)
    return {key:value.get(key) for key in ('UUID','VMState')} if identity==original else value
prior=json.loads((root/'08-06-cleanup-controller-original.json').read_text())['prior']
record=dict(user_keep_original_running=True,original_before=info(original),host_actions=actions,prior=prior)
try:
    current=info(clone)
    assert current['UUID']=='"'+clone+'"' and current['"SATA-ImageUUID-0-0"']=='"2712d710-daaa-449c-843d-d570091127bc"'
    assert current['VMState']=='"poweroff"'
    assert run(vbox,'modifyvm',clone,'--clipboard-mode','disabled','--accelerate-3d','off')['exit']==0
    assert run(vbox,'startvm',clone,'--type','headless')['exit']==0
    write_record(root/'08-06-takeover-controller-state.json',dict(state='running',controller_pid=__import__('os').getpid()))
    deadline=time.monotonic()+3600
    while time.monotonic()<deadline and not stop.exists():time.sleep(1)
    record['stop']=json.loads(stop.read_text()) if stop.exists() else dict(reason='bounded_controller_deadline')
except BaseException as error:record['error']=repr(error)
finally:
    import runpy,shlex
    input_command=runpy.run_path(str(root/'08-06-native-takeover.py'))['input_command']
    def guarded_ssh(command):
        check="from pathlib import Path; assert Path('/sys/class/dmi/id/product_uuid').read_text().strip()=='097920cf-b594-494b-8bd8-ccff973c1dc8'"
        return ssh('sudo -n python -c '+shlex.quote(check)+' && '+command)
    pilot_cleanup_steps(prior,record,info,run,guarded_ssh,input_command)
    record['original_policy']='USER_KEEP_RUNNING: external owner controls lifecycle; no required before/after state equality'
    record['original_controls']=[item for item in actions if item['mutating'] and item['argv'][2]==original]
    record['original_state_respected']=not record['original_controls'] and all(item['argv'][2]==clone for item in actions if item['mutating'])
    write_record(root/'08-06-takeover-cleanup-observations.json',record)
    write_record(root/'08-06-takeover-controller-state.json',dict(state='finished',cleanup='08-06-takeover-cleanup-observations.json'))
