"""Collect independent available target checks; never invent missing source inputs."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=5','-o','HostKeyAlias=lookup-gsd-07',
     '-o','UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-p','2227','archvm']
SCP=['scp','-o','BatchMode=yes','-o','HostKeyAlias=lookup-gsd-07',
     '-o','UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-P','2227']


def run(name,command,timeout=180):
    with (OUT/(name+'.log')).open('w',encoding='utf-8') as log:
        value=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
    return {'returncode':value.returncode,'log':name+'.log'}


def main():
    manifest={'command':'python .planning/phases/14-reliability/run_readiness.py','started':time.time(),
              'source_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted((ROOT/'lookup').glob('*.py'))}}
    (OUT/'batch-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    guard=run('vm-guard',['powershell','-NoProfile','-File','tools/check_package_vm.ps1','-Action','Check'])
    assert guard['returncode']==0
    live='cd /tmp/lookup-yomitan-12 && python tools/check_context_app.py --output /tmp/lookup-phase14-live.json'
    code="from lookup import platform; import json,os; env=platform.session_env(); print(json.dumps([m.__dict__ for m in platform.monitors(env)]))"
    monitors=('cd /tmp/lookup-yomitan-12 && sudo -n -H -u lookup07 env PYTHONPATH=/tmp/lookup-yomitan-12 '
              'XDG_RUNTIME_DIR=/run/user/1001 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1001/bus '
              'python -c '+"'"+code+"'")
    results={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        jobs={'live':pool.submit(run,'target-live',[*SSH,live]),
              'monitors':pool.submit(run,'target-monitors',[*SSH,monitors],30)}
        for name,job in jobs.items():
            try:results[name]=job.result()
            except Exception as error:results[name]={'blocked':repr(error)}
    subprocess.run([*SCP,'archvm:/tmp/lookup-phase14-live.json/report.json',str(OUT/'target-live.json')],check=True,capture_output=True,timeout=30)
    results['source_inputs']={'blocked':['real MDX dictionary and expected source articles','real DSL dictionary and expected source articles']}
    (OUT/'batch-report.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results))


if __name__=='__main__':main()
