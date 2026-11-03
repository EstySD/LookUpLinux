"""Bounded owned-clone diagnostics; preserve HTTP evidence and VM baseline."""
import concurrent.futures
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time
import tarfile

OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('source_batch', OUT/'run_source_batch.py')
batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)


def main():
    report = {'command': 'python .planning/phases/14-reliability/diagnose_remaining.py', 'started': time.time()}
    assert batch.run('remaining-vm-guard', ['powershell', '-NoProfile', '-File', 'tools/check_package_vm.ps1', '-Action', 'Check'])['returncode'] == 0
    baseline = subprocess.check_output([batch.VBOX, 'showvminfo', batch.VM, '--machinereadable'], text=True)
    (OUT/'remaining-vm-baseline.txt').write_text(baseline)
    started = 'VMState="poweroff"' in baseline
    assert started or 'VMState="running"' in baseline
    tunnel = None
    try:
        if started:
            subprocess.run([batch.VBOX, 'modifyvm', batch.VM, '--monitor-count', '2', '--clipboard-mode', 'disabled'], check=True, capture_output=True)
            subprocess.run([batch.VBOX, 'startvm', batch.VM, '--type', 'headless'], check=True, capture_output=True)
        for _ in range(30):
            if subprocess.run([*batch.SSH, 'archvm', 'true'], capture_output=True).returncode == 0:
                break
            time.sleep(3)
        else:
            raise RuntimeError('clone_ssh_unavailable')
        time.sleep(12)
        report['layout'] = batch.run('remaining-layout', [batch.VBOX, 'controlvm', batch.VM, 'setscreenlayout', '1', 'on', '1280', '0', '1280', '800', '32'])
        archive = OUT/'remaining-source.tar.gz'
        with tarfile.open(archive, 'w:gz') as bundle:
            for folder in ('lookup', 'tests', 'tools'):
                for path in (batch.ROOT/folder).rglob('*.py'):
                    bundle.add(path, arcname=path.relative_to(batch.ROOT).as_posix())
            for path in (batch.ROOT/'packaging').glob('*.desktop'):
                bundle.add(path, arcname=path.relative_to(batch.ROOT).as_posix())
        subprocess.run([*batch.SCP, str(archive), 'archvm:/tmp/lookup-phase14-remaining.tar.gz'], check=True, capture_output=True)
        subprocess.run([*batch.SSH, 'archvm', 'sudo -n install -d -m 755 -o lookup07 -g lookup07 /tmp/lookup-phase14-remaining && sudo -n -u lookup07 tar xzf /tmp/lookup-phase14-remaining.tar.gz -C /tmp/lookup-phase14-remaining'], check=True, capture_output=True)
        tunnel = subprocess.Popen([*batch.SSH, '-o', 'ExitOnForwardFailure=yes', '-N', '-R', '127.0.0.1:20123:127.0.0.1:20122', 'archvm'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
        assert tunnel.poll() is None
        probe = '''import concurrent.futures,json,urllib.request,urllib.parse,urllib.error
q=urllib.parse.urlencode(dict(client='gtx',sl='en',tl='ru',dt='t',q='They sat on the <b>bank</b> of the river.'))
def probe(route):
 host,proxied,ua=route
 try:
  opener=urllib.request.build_opener(urllib.request.ProxyHandler({'https':'http://127.0.0.1:20123'} if proxied else {}))
  req=urllib.request.Request('https://'+host+'/translate_a/single?'+q,headers={'User-Agent':ua})
  with opener.open(req,timeout=10) as r:return dict(host=host,proxy=proxied,ua=ua,status=r.status,body=r.read(2000).decode('utf-8','replace'))
 except urllib.error.HTTPError as e:return dict(host=host,proxy=proxied,ua=ua,status=e.code,body=e.read(1000).decode('utf-8','replace'))
 except Exception as e:return dict(host=host,proxy=proxied,ua=ua,error=type(e).__name__)
with concurrent.futures.ThreadPoolExecutor() as p:print(json.dumps(list(p.map(probe,[(h,r,u) for h in ['translate.googleapis.com'] for r in [False,True] for u in ['Python-urllib/3.14','Mozilla/5.0','LookUpLinux/1.1']]))))
'''
        import base64
        encoded = base64.b64encode(probe.encode()).decode()
        commands = {
            'provider-http': [*batch.SSH, 'archvm', 'echo '+encoded+' | base64 -d | python -'],
            'displays': [*batch.SSH, 'archvm', "cd /tmp/lookup-phase14-remaining && sudo -n -H -u lookup07 python -c \"from lookup import platform;import os;os.environ.update(platform.session_env());print(platform.run(['kscreen-doctor','-j'],os.environ).decode())\""],
            'guest-tools': [*batch.SSH, 'archvm', 'command -v VBoxControl; VBoxControl --version; command -v wesnoth; loginctl list-sessions; VBoxControl guestproperty enumerate'],
            'host-live': ['python', 'tools/check_context_app.py', '--output', str(OUT/'remaining-host-live')],
            'native-session': [*batch.SSH, 'archvm', "ps -eo user,pid,args | rg 'kwin_wayland|startplasma|sddm'; sudo -n -u lookup07 sh -c 'cat ~/.config/kwinrc; cat ~/.config/environment.d/*.conf 2>/dev/null'; sudo -n cat /etc/sddm.conf /etc/sddm.conf.d/*.conf 2>/dev/null; cat /proc/cmdline; ls /dev/dri; printenv NO_PROXY no_proxy"],
            'curl-proxy': [*batch.SSH, 'archvm', "curl --max-time 12 --noproxy '' --proxy http://127.0.0.1:20123 -sS -w '\\nHTTP_STATUS=%{http_code}\\n' 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ru&dt=t&q=They%20sat%20on%20the%20%3Cb%3Ebank%3C%2Fb%3E%20of%20the%20river.'"],
        }
        with concurrent.futures.ThreadPoolExecutor() as pool:
            jobs = {name: pool.submit(batch.run, 'remaining-'+name, command, 45) for name, command in commands.items()}
            for name, job in jobs.items():
                report[name] = job.result()
    finally:
        if tunnel is not None:
            tunnel.terminate()
            tunnel.wait(timeout=10)
        if started:
            subprocess.run([*batch.SSH, 'archvm', 'sudo -n systemctl poweroff'], capture_output=True, timeout=15)
            for _ in range(40):
                state = subprocess.check_output([batch.VBOX, 'showvminfo', batch.VM, '--machinereadable'], text=True)
                if 'VMState="poweroff"' in state:
                    break
                time.sleep(1)
            report['poweroff'] = 'VMState="poweroff"' in state
            if report['poweroff']:
                subprocess.run([batch.VBOX, 'modifyvm', batch.VM, '--monitor-count', '1', '--clipboard-mode', 'bidirectional'], check=True, capture_output=True)
        report['finished'] = time.time()
        (OUT/'remaining-diagnostic-report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report))


if __name__ == '__main__':
    main()
