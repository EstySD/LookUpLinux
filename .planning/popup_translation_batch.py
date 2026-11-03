import base64,hashlib,json,os,subprocess,sys,tarfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'.planning/popup-translation-validation';out.mkdir(exist_ok=True)
ssh=['ssh','-o','BatchMode=yes','-o','HostKeyAlias=lookup-gsd-07','-o','UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-p','2227','archvm']
scp=['scp','-q','-o','BatchMode=yes','-o','HostKeyAlias=lookup-gsd-07','-o','UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-P','2227']
report={'command':'python .planning/popup_translation_batch.py','pid':os.getpid(),'revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'sha256':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in ['lookup/gui.py','tests/test_app_gui.py']}}
(out/'job.json').write_text(json.dumps(report,indent=2))
with tarfile.open(out/'source.tar.gz','w:gz') as archive:
    for directory in ['lookup','tests','tools']:
        for p in (root/directory).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:archive.add(p,arcname=p.relative_to(root))
with open(out/'host.log','w') as h,open(out/'vm.log','w') as v:
    host=subprocess.Popen([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=root,env=dict(os.environ,QT_QPA_PLATFORM='offscreen',PYTHONUTF8='1'),stdout=h,stderr=subprocess.STDOUT)
    subprocess.run([*scp,str(out/'source.tar.gz'),'archvm:/tmp/popup-translation-tests.tar.gz'],check=True)
    vm=subprocess.Popen([*ssh,'mkdir -p /tmp/popup-translation-tests && tar xzf /tmp/popup-translation-tests.tar.gz -C /tmp/popup-translation-tests && cd /tmp/popup-translation-tests && QT_QPA_PLATFORM=offscreen python -m unittest tests.test_app_gui tests.test_translate -v'],stdout=v,stderr=subprocess.STDOUT)
    report['host_exit']=host.wait();report['vm_exit']=vm.wait()
(out/'report.json').write_text(json.dumps(report,indent=2))
for name in ['host','vm']:
    print(name,report[name+'_exit'],'\n'.join((out/(name+'.log')).read_text(errors='replace').splitlines()[-12:]))
if report['host_exit'] or report['vm_exit']:sys.exit(1)
