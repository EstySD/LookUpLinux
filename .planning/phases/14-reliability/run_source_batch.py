"""One bounded real-dictionary/target-provider batch, with explicit routes."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
DOWNLOADS=OUT/'downloads'
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=5','-o','HostKeyAlias=lookup-gsd-07',
     '-o','UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-p','2227']
SCP=['scp','-o','BatchMode=yes','-o','HostKeyAlias=lookup-gsd-07',
     '-o','UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-P','2227']
VBOX='C:/Program Files/Oracle/VirtualBox/VBoxManage.exe'
VM='cf207909-94b5-4b49-8bd8-ccff973c1dc8'


def run(name,command,timeout=300):
    with (OUT/(name+'.log')).open('w',encoding='utf-8') as log:
        process=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
    return {'returncode':process.returncode,'log':name+'.log'}


def fetch(remote,local):
    subprocess.run([*SCP,'archvm:'+remote,str(OUT/local)],check=True,capture_output=True,timeout=30)


def guest():
    started=False
    tunnel=None
    result={}
    try:
        assert run('source-vm-guard',['powershell','-NoProfile','-File','tools/check_package_vm.ps1','-Action','Check'])['returncode']==0
        info=subprocess.check_output([VBOX,'showvminfo',VM,'--machinereadable'],text=True)
        if 'VMState="poweroff"' in info:
            subprocess.run([VBOX,'startvm',VM,'--type','headless'],check=True,capture_output=True);started=True
        elif 'VMState="running"' not in info:raise RuntimeError('owned clone unsafe state')
        for attempt in range(30):
            if subprocess.run([*SSH,'archvm','true'],capture_output=True).returncode==0:break
            time.sleep(3)
        else:raise RuntimeError('owned clone SSH unavailable')
        bundle=DOWNLOADS/'source-inputs.tar.gz'
        with tarfile.open(bundle,'w:gz') as archive:
            for name in ('direct-en-ru_wikidict.dsl','direct-ecdict-mdx-headless-28.zip','direct-ecdict.csv'):
                archive.add(DOWNLOADS/name,arcname=name)
            for folder in ('lookup','tests','tools'):
                for path in (ROOT/folder).rglob('*'):
                    if path.is_file() and '__pycache__' not in path.parts and path.suffix in ('.py','.txt'):
                        archive.add(path,arcname='repository/'+path.relative_to(ROOT).as_posix())
        subprocess.run([*SSH,'archvm','mkdir -p /tmp/lookup-phase14-sources'],check=True,capture_output=True)
        subprocess.run([*SCP,str(bundle),str(ROOT/'tools/check_real_dictionaries.py'),'archvm:/tmp/lookup-phase14-sources/'],check=True,capture_output=True,timeout=90)
        setup='cd /tmp/lookup-phase14-sources && tar xzf source-inputs.tar.gz && test -f repository/tools/check_real_dictionaries.py'
        assert run('source-stage',[*SSH,'archvm',setup])['returncode']==0
        direct=('cd /tmp/lookup-phase14-sources/repository && env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u http_proxy -u https_proxy -u all_proxy '
                'python tools/check_context_app.py --output /tmp/lookup-phase14-direct')
        proxied=('cd /tmp/lookup-phase14-sources/repository && env HTTP_PROXY=http://127.0.0.1:20123 HTTPS_PROXY=http://127.0.0.1:20123 '
                 'http_proxy=http://127.0.0.1:20123 https_proxy=http://127.0.0.1:20123 NO_PROXY=localhost,127.0.0.1 '
                 'python tools/check_context_app.py --output /tmp/lookup-phase14-proxy')
        # Forward the existing host proxy only within this owned-clone SSH connection.
        tunnel=subprocess.Popen([*SSH,'-o','ExitOnForwardFailure=yes','-N','-R','127.0.0.1:20123:127.0.0.1:20122','archvm'],
                                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        time.sleep(.5)
        if tunnel.poll() is not None:raise RuntimeError('proxy tunnel setup failed')
        dictionary=('cd /tmp/lookup-phase14-sources/repository && python tools/check_real_dictionaries.py /tmp/lookup-phase14-sources '
                    '--output /tmp/lookup-phase14-sources/target-dicts.json')
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            jobs={'dictionaries':pool.submit(run,'target-real-dicts',[*SSH,'archvm',dictionary]),
                  'provider_direct':pool.submit(run,'provider-direct',[*SSH,'archvm',direct]),
                  'provider_proxy':pool.submit(run,'provider-proxy',[*SSH,'archvm',proxied])}
            for name,job in jobs.items():
                try:result[name]=job.result()
                except Exception as error:result[name]={'blocked':type(error).__name__}
        for remote,local in [('/tmp/lookup-phase14-sources/target-dicts.json','target-real-dicts.json'),
                             ('/tmp/lookup-phase14-direct/report.json','provider-direct.json'),
                             ('/tmp/lookup-phase14-proxy/report.json','provider-proxy.json')]:
            try:fetch(remote,local)
            except Exception as error:result[local]={'blocked':type(error).__name__}
        return result
    finally:
        if tunnel is not None:
            tunnel.terminate()
            try:tunnel.wait(timeout=5)
            except subprocess.TimeoutExpired:tunnel.kill();tunnel.wait()
        if started:
            subprocess.run([*SSH,'archvm','sudo -n systemctl poweroff'],capture_output=True,timeout=15)
            off=False
            for attempt in range(40):
                info=subprocess.check_output([VBOX,'showvminfo',VM,'--machinereadable'],text=True)
                if 'VMState="poweroff"' in info:off=True;break
                time.sleep(1)
            cleanup={'owned_clone':VM,'poweroff':off,'original_controlled':False,'proxy_tunnel_closed':tunnel is None or tunnel.poll() is not None}
            (OUT/'source-cleanup.json').write_text(json.dumps(cleanup,indent=2),encoding='utf-8')


def main():
    manifest={'command':'python .planning/phases/14-reliability/run_source_batch.py','pid':os.getpid(),
              'started':time.time(),'source_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in sorted((ROOT/'lookup').glob('*.py'))}}
    (OUT/'source-batch-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        jobs={'host':pool.submit(lambda:{'returncode':0,'log':'host-real-dicts.log','reused':True}) if '--reuse-host' in sys.argv else
                      pool.submit(run,'host-real-dicts',[sys.executable,'tools/check_real_dictionaries.py',str(DOWNLOADS),
                                                     '--output',str(OUT/'host-real-dicts.json')]),'target':pool.submit(guest)}
        results={}
        for name,job in jobs.items():
            try:results[name]=job.result()
            except Exception as error:results[name]={'blocked':type(error).__name__}
    (OUT/'source-batch-report.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results))


if __name__=='__main__':main()
