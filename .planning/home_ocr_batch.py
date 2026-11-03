import hashlib,json,os,subprocess,sys,tarfile,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'.planning/home-ocr-validation';out.mkdir(exist_ok=True)
ssh=['ssh','-o','BatchMode=yes','-o','HostKeyAlias=lookup-gsd-07','-o','UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-p','2227','archvm']
scp=['scp','-q','-o','BatchMode=yes','-o','HostKeyAlias=lookup-gsd-07','-o','UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-P','2227']
report={'command':'python .planning/home_ocr_batch.py','pid':os.getpid(),'revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'sha256':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in ['lookup/app.py','tests/test_app.py','lookup/ocr.py','tests/test_ocr_fallback.py','tests/fixtures/ocr-selected-home.png']}}
(out/'job.json').write_text(json.dumps(report,indent=2))
env=dict(os.environ,QT_QPA_PLATFORM='offscreen',PYTHONUTF8='1')
with open(out/'host.log','w') as hostlog,open(out/'vm.log','w') as vmlog:
    host=subprocess.Popen([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=root,env=env,stdout=hostlog,stderr=subprocess.STDOUT)
    with tarfile.open(out/'source.tar.gz','w:gz') as archive:
        for directory in ['lookup','tests','tools']:
            for p in (root/directory).rglob('*'):
                if p.is_file() and '__pycache__' not in p.parts:archive.add(p,arcname=p.relative_to(root))
    subprocess.run([*scp,str(out/'source.tar.gz'),'archvm:/tmp/home-ocr-tests.tar.gz'],check=True)
    vm=subprocess.Popen([*ssh,'mkdir -p /tmp/lookup-home-ocr-tests && tar xzf /tmp/home-ocr-tests.tar.gz -C /tmp/lookup-home-ocr-tests && cd /tmp/lookup-home-ocr-tests && QT_QPA_PLATFORM=offscreen python -m unittest tests.test_app tests.test_app_gui tests.test_ocr tests.test_ocr_image tests.test_ocr_fallback tests.test_ocr_game_sources tests.test_ocr_cli tests.test_context_images -v'],stdout=vmlog,stderr=subprocess.STDOUT)
    report['host_exit']=host.wait();report['vm_exit']=vm.wait()
(out/'report.json').write_text(json.dumps(report,indent=2))
for name in ['host','vm']:
    lines=(out/(name+'.log')).read_text(errors='replace').splitlines()
    print(name,report[name+'_exit'],'\n'.join(lines[-12:]))
