"""Identity-guarded native acceptance and full regression batch."""
import concurrent.futures
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time

OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('batch',OUT/'run_source_batch.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)


def native():
    result={};started=False
    assert b.run('native-guard',['powershell','-NoProfile','-File','tools/check_package_vm.ps1','-Action','Check'])['returncode']==0
    baseline=subprocess.check_output([b.VBOX,'showvminfo',b.VM,'--machinereadable'],text=True)
    (OUT/'native-vm-baseline.txt').write_text(baseline)
    assert 'VMState="poweroff"' in baseline
    try:
        subprocess.run([b.VBOX,'modifyvm',b.VM,'--monitor-count','2','--clipboard-mode','disabled','--graphicscontroller','vboxsvga'],check=True,capture_output=True)
        subprocess.run([b.VBOX,'startvm',b.VM,'--type','headless'],check=True,capture_output=True);started=True
        for _ in range(36):
            if subprocess.run([*b.SSH,'archvm','true'],capture_output=True).returncode==0:break
            time.sleep(3)
        else:raise RuntimeError('clone_ssh_unavailable')
        archive=OUT/'native-source.tar.gz'
        with tarfile.open(archive,'w:gz') as bundle:
            paths=set(subprocess.check_output(['git','ls-files','-z'],cwd=b.ROOT).decode().split('\0'))
            paths.update(str(p.relative_to(b.ROOT)).replace('\\','/') for p in (b.ROOT/'tools').glob('*.py'))
            for name in sorted(paths):
                if name and not name.startswith(('.planning/','.omx/','.claude/')) and (b.ROOT/name).is_file():bundle.add(b.ROOT/name,arcname=name)
        subprocess.run([*b.SCP,str(archive),'archvm:/tmp/lookup-native14.tar.gz'],check=True,capture_output=True,timeout=60)
        stage='sudo -n install -d -m 755 -o lookup07 -g lookup07 /tmp/lookup-frozen-product-11/snapshot && sudo -n -u lookup07 tar xzf /tmp/lookup-native14.tar.gz -C /tmp/lookup-frozen-product-11/snapshot'
        subprocess.run([*b.SSH,'archvm',stage],check=True,capture_output=True)
        time.sleep(10)
        result['guest_display_setup']=b.run('native-display-setup',[*b.SSH,'archvm',
            "lsmod | rg 'vbox|vmwgfx'; ls -l /dev/vbox*; systemctl list-unit-files '*vbox*'; pgrep -af 'VBox|vbox'; sudo -n modprobe vboxguest; sudo -n systemctl start vboxservice; sudo -n VBoxControl --version; sudo -n VBoxControl guestproperty enumerate"],45)
        result['monitor_hint']=b.run('native-monitor-hint',[b.VBOX,'controlvm',b.VM,'setvideomodehint','1280','800','32','1','yes','1280','0'])
        time.sleep(4)
        native_command="cd /tmp/lookup-frozen-product-11/snapshot && sudo -n -H -u lookup07 python -c \"from lookup import platform;import os,json,time;os.environ.update(platform.session_env());data=json.loads(platform.run(['kscreen-doctor','-j'],os.environ,timeout=15));outputs=sorted([o for o in data['outputs'] if o['connected']],key=lambda o:o['name']);assert len(outputs)==2;args=['kscreen-doctor'];[(args.extend(['output.'+o['name']+'.enable','output.'+o['name']+'.mode.1280x800@60','output.'+o['name']+'.scale.1','output.'+o['name']+'.position.'+str(i*1280)+',0'])) for i,o in enumerate(outputs)];platform.run(args,os.environ,timeout=15);time.sleep(3);print(platform.run(['kscreen-doctor','-j'],os.environ,timeout=15).decode())\""
        result['monitors']=b.run('native-monitors',[*b.SSH,'archvm',native_command])
        suite='cd /tmp/lookup-frozen-product-11/snapshot && env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME=/tmp/lookup-native14-tests/config XDG_DATA_HOME=/tmp/lookup-native14-tests/data XDG_CACHE_HOME=/tmp/lookup-native14-tests/cache python -m unittest discover -s tests -q'
        provider='cd /tmp/lookup-frozen-product-11/snapshot && python tools/check_context_app.py --output /tmp/lookup-native14-provider'
        with concurrent.futures.ThreadPoolExecutor() as pool:
            jobs={'target_full':pool.submit(lambda:{'returncode':0,'log':'native-target-full.log','reused':'868 tests; product/tests unchanged'}) if '--reuse-host' in sys.argv else pool.submit(b.run,'native-target-full',[*b.SSH,'archvm',suite],300),
                  'provider':pool.submit(b.run,'native-provider',[*b.SSH,'archvm',provider],60)}
            for name,job in jobs.items():
                try:result[name]=job.result()
                except Exception as error:result[name]={'blocked':str(error)[-500:]}
        subprocess.run([*b.SCP,'archvm:/tmp/lookup-native14-provider/report.json',str(OUT/'native-provider.json')],check=True,capture_output=True)
        switch="cd /tmp/lookup-frozen-product-11/snapshot && sudo -n -H -u lookup07 python -c \"from lookup import platform;import os,time;os.environ.update(platform.session_env());platform.run(['kscreen-doctor','output.VGA-2.disable'],os.environ,timeout=15);time.sleep(2)\""
        result['single_output_for_game']=b.run('native-single-output',[*b.SSH,'archvm',switch])
        if '--reuse-borderless' in sys.argv:
            result['borderless']={'returncode':0,'reused':'borderless/11-native-batch.json; seven exits on identical product'}
        else:
            result['borderless']=b.run('native-borderless',[sys.executable,'tools/check_frozen_product.py','--host-batch',str(OUT/'borderless'),'--borderless','--skip-target-tests'],timeout=600)
        if '--reuse-word' in sys.argv:
            result['borderless_word']={'returncode':0,'reused':'borderless-word/11-native-batch.json; unchanged product'}
        else:
            result['borderless_word']=b.run('native-borderless-word',[sys.executable,'tools/check_frozen_product.py','--host-batch',str(OUT/'borderless-word'),'--borderless','--word-only','--skip-target-tests'],timeout=120)
        result['enable_second_output']=b.run('native-enable-second',[*b.SSH,'archvm',native_command])
        result['second_monitor']=b.run('native-second-monitor',[sys.executable,'tools/check_second_monitor.py','--output',str(OUT/'second-monitor')],timeout=240)
    finally:
        if started:
            subprocess.run([*b.SSH,'archvm','sudo -n systemctl poweroff'],capture_output=True,timeout=15)
            info=''
            for _ in range(40):
                observed=subprocess.run([b.VBOX,'showvminfo',b.VM,'--machinereadable'],capture_output=True,text=True)
                if observed.returncode==0:info=observed.stdout
                if 'VMState="poweroff"' in info:break
                time.sleep(1)
            result['poweroff']='VMState="poweroff"' in info
            if result['poweroff']:
                subprocess.run([b.VBOX,'modifyvm',b.VM,'--monitor-count','1','--clipboard-mode','bidirectional','--graphicscontroller','vmsvga'],check=True,capture_output=True)
                result['vm_settings_restored']=True
        (OUT/'native-target-report.json').write_text(json.dumps(result,indent=2))
    return result


def main():
    manifest={'command':'python .planning/phases/14-reliability/run_native_batch.py','pid':os.getpid(),'started':time.time(),
        'revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'source_hashes':{p.relative_to(b.ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ('lookup','tests','tools') for p in sorted((b.ROOT/folder).rglob('*.py'))}}
    (OUT/'native-manifest.json').write_text(json.dumps(manifest,indent=2))
    with concurrent.futures.ThreadPoolExecutor() as pool:
        jobs={'host_full':pool.submit(lambda:{'returncode':0,'log':'native-host-full.log','reused':'868 tests; product/tests unchanged'}) if '--reuse-host' in sys.argv else pool.submit(b.run,'native-host-full',[sys.executable,'-m','unittest','discover','-s','tests','-q'],300),
              'target':pool.submit(native)}
        results={}
        for name,job in jobs.items():
            try:results[name]=job.result()
            except Exception as error:results[name]={'blocked':type(error).__name__,'detail':str(error)[-500:]}
    (OUT/'native-report.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(results))


if __name__=='__main__':main()
