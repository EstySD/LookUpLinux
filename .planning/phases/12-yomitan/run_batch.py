"""Deterministic host/owned-clone batch; full logs stay beside this script."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ARCHIVE = Path('D:/User/Downloads/English-Russian_dict_Yomitan.zip')
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', '-o', 'HostKeyAlias=lookup-gsd-07',
       '-o', 'UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts', '-p', '2227', 'archvm']
SCP = ['scp', '-o', 'BatchMode=yes', '-o', 'HostKeyAlias=lookup-gsd-07',
       '-o', 'UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts', '-P', '2227']
VM = 'cf207909-94b5-4b49-8bd8-ccff973c1dc8'
VBOX = 'C:/Program Files/Oracle/VirtualBox/VBoxManage.exe'


def run(name, command, timeout=240, **kwargs):
    with (OUT / (name + '.log')).open('w', encoding='utf-8') as log:
        result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                timeout=timeout, **kwargs)
    return {'returncode': result.returncode, 'log': name + '.log'}


def target():
    booted = False
    try:
        guard = run('vm-guard', ['powershell', '-NoProfile', '-File', 'tools/check_package_vm.ps1', '-Action', 'Check'])
        if guard['returncode']:
            return {'blocked': 'VM identity guard', **guard}
        info = subprocess.check_output([VBOX, 'showvminfo', VM, '--machinereadable'], text=True)
        if 'VMState="poweroff"' in info:
            subprocess.run([VBOX, 'startvm', VM, '--type', 'headless'], check=True, capture_output=True)
            booted = True
        elif 'VMState="running"' not in info:
            return {'blocked': 'VM is neither running nor powered off'}
        for attempt in range(36):
            ready = subprocess.run([*SSH, 'true'], capture_output=True, timeout=12)
            if ready.returncode == 0:
                break
            time.sleep(3)
        else:
            return {'blocked': 'Owned clone SSH unavailable'}
        bundle = OUT / 'source.tar.gz'
        with tarfile.open(bundle, 'w:gz') as archive:
            tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
            names = set(n for n in tracked if n and not n.startswith(('.omx/', '.claude/')))
            names.update(str(p.relative_to(ROOT)).replace('\\', '/') for folder in ('lookup', 'tests', 'tools')
                         for p in (ROOT / folder).rglob('*.py'))
            for name in sorted(names):
                if (ROOT / name).is_file():
                    archive.add(ROOT / name, arcname=name)
        subprocess.run([*SSH, 'mkdir -p /tmp/lookup-yomitan-12'], check=True, capture_output=True)
        subprocess.run([*SCP, str(bundle), str(ARCHIVE), 'archvm:/tmp/lookup-yomitan-12/'], check=True, capture_output=True, timeout=60)
        command = ('cd /tmp/lookup-yomitan-12 && tar xzf source.tar.gz && '
                   'env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME=/tmp/lookup-yomitan-12/config '
                   'XDG_DATA_HOME=/tmp/lookup-yomitan-12/data XDG_CACHE_HOME=/tmp/lookup-yomitan-12/cache '
                   'python -m unittest discover -s tests -q; test_status=$?; '
                   'python tools/check_yomitan.py English-Russian_dict_Yomitan.zip --output real-target.json; '
                   'real_status=$?; echo TEST_EXIT=$test_status REAL_EXIT=$real_status; '
                   'test $test_status -eq 0 && test $real_status -eq 0')
        result = run('target-full', [*SSH, command], timeout=360)
        subprocess.run([*SCP, 'archvm:/tmp/lookup-yomitan-12/real-target.json', str(OUT / 'real-target.json')], capture_output=True, timeout=30)
        return result
    finally:
        if booted:
            run('vm-cleanup', [VBOX, 'controlvm', VM, 'acpipowerbutton'], timeout=20)


def main():
    manifest = {'started': time.time(), 'command': 'python .planning/phases/12-yomitan/run_batch.py',
                'pid': os.getpid(), 'source_hashes': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for folder in ('lookup', 'tests', 'tools') for p in sorted((ROOT / folder).rglob('*.py'))},
                'archive_sha256': hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()}
    (OUT / 'batch-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen')
    jobs = {'host_full': lambda: ({'returncode': 0, 'log': 'host-full.log', 'reused': 'product/tests unchanged since first batch'}
                                 if '--reuse-host' in sys.argv else
                                 run('host-full', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-q'], env=env)),
            'real_host': lambda: run('real-host', [sys.executable, 'tools/check_yomitan.py', str(ARCHIVE), '--output', str(OUT / 'real-host.json')]),
            'target': target}
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {name: pool.submit(job) for name, job in jobs.items()}
        for name, future in futures.items():
            try:
                results[name] = future.result()
            except Exception as error:
                results[name] = {'blocked': repr(error)}
    (OUT / 'batch-report.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results))


if __name__ == '__main__':
    main()
