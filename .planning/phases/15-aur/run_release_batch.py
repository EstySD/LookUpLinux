"""Final release batch: host/target suites, exact-source package lifecycle."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time

ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from tools.build_release import build
from tools.stage_aur import stage

OUT=Path(__file__).resolve().parent/('release-'+str(int(time.time())))
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','HostKeyAlias=lookup-gsd-07','-o','UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-p','2227','archvm']
SCP=['scp','-o','BatchMode=yes','-o','HostKeyAlias=lookup-gsd-07','-o','UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-P','2227']


def run(name,command,timeout=300,**kwargs):
    with (OUT/(name+'.log')).open('w',encoding='utf-8') as log:
        try:
            p=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=timeout,**kwargs)
            return {'returncode':p.returncode,'log':name+'.log'}
        except Exception as error:return {'blocked':str(error)[-500:],'log':name+'.log'}


def target():
    guard=run('vm-guard',['powershell','-NoProfile','-File','tools/check_package_vm.ps1','-Action','Check']);assert guard['returncode']==0
    remote='/home/arch/lookup-release-021-'+str(int(time.time()))
    subprocess.run([*SSH,'mkdir -p '+remote+'/aur '+remote+'/tests-source'],check=True,capture_output=True)
    subprocess.run([*SCP,str(OUT/'aur/PKGBUILD'),str(OUT/'dist/lookup-linux-0.2.1-source.tar.gz'),'archvm:'+remote+'/aur/'],check=True,capture_output=True,timeout=60)
    subprocess.run([*SCP,str(OUT/'tests-source.tar.gz'),str(Path(__file__).with_name('check_package.py')),'archvm:'+remote+'/'],check=True,capture_output=True,timeout=60)
    result={'remote':remote}
    result['stage']=run('target-stage',[*SSH,'tar xzf '+remote+'/tests-source.tar.gz -C '+remote+'/tests-source'])
    suite='cd '+remote+'/tests-source && env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME='+remote+'/test-config XDG_DATA_HOME='+remote+'/test-data XDG_CACHE_HOME='+remote+'/test-cache python -m unittest discover -s tests -q'
    result['full_suite']=run('target-full',[*SSH,suite],360)
    result['package']=run('target-package',[*SSH,'python '+remote+'/check_package.py '+remote],900)
    subprocess.run([*SCP,'archvm:'+remote+'/package-report.json',str(OUT/'package-report.json')],capture_output=True,timeout=30)
    subprocess.run([*SCP,'archvm:'+remote+'/aur/lookup-linux-0.2.1-1-x86_64.pkg.tar.zst',str(OUT/'dist/')],capture_output=True,timeout=60)
    result['srcinfo']=run('srcinfo',[*SSH,'cd '+remote+'/aur && makepkg --printsrcinfo'])
    return result


def main():
    OUT.mkdir(parents=True)
    manifest={'command':'python .planning/phases/15-aur/run_release_batch.py','pid':os.getpid(),'revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'started':time.time(),'output':str(OUT),
        'source_hashes':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('lookup','tests','tools') for p in sorted((ROOT/folder).rglob('*.py'))}}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    (OUT.parent/'active-release-job.json').write_text(json.dumps(manifest,indent=2))
    build(OUT/'dist','v0.2.1');stage(OUT/'dist/lookup-linux-0.2.1-source.tar.gz',OUT/'aur')
    with tarfile.open(OUT/'tests-source.tar.gz','w:gz') as archive:
        paths=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
        for name in paths:
            if name and not name.startswith(('.planning/','.omx/','.claude/','.codex/','.agents/')) and (ROOT/name).is_file():archive.add(ROOT/name,arcname=name)
    with concurrent.futures.ThreadPoolExecutor() as pool:
        jobs={'host_full':pool.submit(run,'host-full',[sys.executable,'-m','unittest','discover','-s','tests','-q'],360,env=dict(os.environ,QT_QPA_PLATFORM='offscreen',PYTHONUTF8='1')),'target':pool.submit(target)}
        results={}
        for name,job in jobs.items():
            try:results[name]=job.result()
            except Exception as error:results[name]={'blocked':type(error).__name__+':'+str(error)[-700:]}
    (OUT/'report.json').write_text(json.dumps(results,indent=2));print(json.dumps({'output':str(OUT),'results':results}))


if __name__=='__main__':main()
