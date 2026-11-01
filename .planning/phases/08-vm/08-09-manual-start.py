"""Explicit user-requested visible session; deliberately no timeout or cleanup."""
import json,subprocess,time
from pathlib import Path
root=Path('.planning/phases/08-vm');vbox='C:/Program Files/Oracle/VirtualBox/VBoxManage.exe';clone='cf207909-94b5-4b49-8bd8-ccff973c1dc8'
cleanup=json.loads((root/'08-09-cleanup-final.json').read_text())
assert cleanup['gates']['clone_off'] and cleanup['gates']['settings_restored'] and cleanup['gates']['original_state_respected']
assert json.loads((root/'08-09-native-controller-state.json').read_text())['state']=='finished'
result=subprocess.run([vbox,'showvminfo',clone,'--machinereadable'],capture_output=True,text=True,check=True,timeout=15)
info=dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)
assert info['UUID']=='"'+clone+'"' and info['VMState']=='"poweroff"' and info['name']=='"lookup-gsd-07"'
assert info['"SATA-ImageUUID-0-0"']=='"2712d710-daaa-449c-843d-d570091127bc"' and info['macaddress1']=='"080027A05376"'
assert info['Forwarding(0)']=='"lookup-gsd-07-ssh,tcp,127.0.0.1,2227,,22"'
command=[vbox,'startvm',clone,'--type','gui'];result=subprocess.run(command,capture_output=True,text=True,timeout=30)
record=dict(user_requested_interactive=True,policy='Keep owned clone and normal app running for user; no watchdog or automatic shutdown; original untouched.',
    controller_finished=True,prior_off_cleanup='08-09-cleanup-final.json',cleanup_acceptance=cleanup['passed'],argv=command,exit=result.returncode,stdout=result.stdout,stderr=result.stderr,at_ns=time.time_ns())
(root/'08-09-manual-start.json').write_text(json.dumps(record,indent=2));print(json.dumps(record));assert result.returncode==0
