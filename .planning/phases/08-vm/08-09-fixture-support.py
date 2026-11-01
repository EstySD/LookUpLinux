"""Declared non-game physical resource target: unmodified captured sparse PNG."""
import base64,hashlib,json,runpy,sys,time
from pathlib import Path
from tools import check_hardening as hardening

root=Path('.planning/phases/08-vm');m=runpy.run_path(str(root/'08-09-games.py'));n=runpy.run_path(str(root/'08-09-native.py'))
resources=runpy.run_path(str(root/'08-09-fallback.py'))
fixture=Path('tests/fixtures/ocr-games/04-recovery-name.png')

def setup():
    assert hashlib.sha256(fixture.read_bytes()).hexdigest()=='9cbc077f181e3c564d21e5d3ec88d68129630811972b12cc659558fc8723497e'
    code=Path('tools/check_hardening.py').read_text(encoding='utf-8')
    code=code.replace('lookup-hardening-08','lookup-fallback-09').replace('check_hardening.py','check_fallback_09.py')
    code=code.replace('def guest_probe(continuous=False):',"SCENES=(('name','name'),)\n\ndef guest_probe(continuous=False):",1)
    start=code.index('    layout=QVBoxLayout(window);');end=code.index('    devices=',start)
    code=code[:start]+'''    from PyQt6.QtGui import QPixmap
    from PyQt6.QtCore import QPoint
    label=QLabel(window);label.setPixmap(QPixmap('/home/lookup07/fallback-09-source.png'));label.setGeometry(0,0,1280,800)
    window.showFullScreen()
'''+code[end:]
    code=code.replace("word=case['word'];body=case['body'];label.setText(case['sentence'])","word=case['word'];body=case['body']")
    start=code.index('            point=label.mapToGlobal');end=code.index('            physical=',start)
    code=code[:start]+'            point=QPoint(733,378)\n'+code[end:]
    start=code.index("            journal=subprocess.run(['journalctl'",code.index('def guest_probe'))
    end=code.index('            if (root/',start)
    code=code[:start]+"            numeric=Path('/home/lookup07/.local/state/lookup-games-08/assaultcube/lookup/daemon.log').read_text()\n"+code[end:]
    # This observer reads the real instrumented daemon's existing numeric log.
    (root/'08-09-fixture-observer.py').write_text(code,encoding='utf-8',newline='\n')
    files={'check_fallback_09.py':base64.b64encode(code.encode()).decode(),'fallback-09-source.png':base64.b64encode(fixture.read_bytes()).decode()}
    previous=json.loads((root/'08-09-fixture-declaration.json').read_text())['observer_sha256'] if (root/'08-09-fixture-declaration.json').exists() else None
    print(n['guest']('''import base64,json,os,subprocess
from pathlib import Path
files='''+repr(files)+'''
previous='''+repr(previous)+'''
for name,data in files.items():
    import hashlib
    path=Path('/home/lookup07')/name
    if path.exists():assert hashlib.sha256(path.read_bytes()).hexdigest()==(previous if name.endswith('.py') else '9cbc077f181e3c564d21e5d3ec88d68129630811972b12cc659558fc8723497e')
    path.write_bytes(base64.b64decode(data));os.chown(path,1001,1001)
p=subprocess.run(['sudo','-n','-H','-u','lookup07','python','/home/lookup07/check_fallback_09.py','--start-probe','--continuous'],capture_output=True,text=True,timeout=8);print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)'''),flush=True)
    (root/'08-09-fixture-declaration.json').write_text(json.dumps(dict(completions=20,required_second_pass=2,kind='non-game resource support only',
        fixture=str(fixture),sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),point=[733,378],display='ordinary fullscreen image window, native1280x800 pixels, no scaling or pixel edits',
        production='physical hotkey -> actual Screenshot2 -> default6-to11 cascade; original Source objects unchanged',observer_sha256=hashlib.sha256(code.encode()).hexdigest()),indent=2))

def command(value):
    encoded=base64.b64encode(json.dumps(value).encode()).decode()
    code="import subprocess;p=subprocess.run(['sudo','-n','-H','-u','lookup07','python','/home/lookup07/check_fallback_09.py','--guest-command',"+repr(encoded)+"],capture_output=True,text=True,timeout=25);print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)"
    return json.loads(n['guest'](code))

def run():
    output=root/'08-09-fixture-support-attempts.json';assert not output.exists()
    data=dict(kind='non-game resource support',before=resources['snapshot'](),privacy_before=n['command'](dict(action='privacy')),completions=[],resources=[],failures=[])
    hardening.write_record(output,data)
    try:
        for index in range(1,21):
            try:
                n['inputs']('Keys',Codes='01 81')
                ready=command(dict(action='arm',attempt=index,group='fallback',case=1,scene=1))
                n['inputs']('Pointer',X=733,Y=378,Buttons=0);n['inputs']('Keys',Codes='e0 5b 2a 12 92 aa e0 db')
                timing=command(dict(action='result',attempt=index,token=ready['token']))
                assert timing['status']=='success',timing
                key='-'.join(str(timing[name]) for name in ('pid','run','request'))
                observation=json.loads(n['guest']("print(__import__('pathlib').Path('/home/lookup07/.local/state/lookup-games-08/assaultcube/lookup/observations/request-"+key+".json').read_text())"))
                data['completions'].append(dict(timing=timing,ocr_passes=observation['ocr_passes'],source=observation,actual_selection=observation['production_selection']))
                frame=command(dict(action='frame',attempt=index,token=ready['token']))
                (root/('08-09-fixture-useful-'+str(index)+'.png')).write_bytes(base64.b64decode(frame['png_base64']))
                n['inputs']('Keys',Codes='01 81')
                resource=resources['snapshot']();resource['after']=index;data['resources'].append(resource)
                print(json.dumps(dict(completed=index,passes=[item['psm'] for item in observation['ocr_passes']],rss_bytes=resource['rss_bytes'])),flush=True)
            except BaseException as error:data['failures'].append(dict(attempt=index,error=repr(error)));raise
            finally:hardening.write_record(output,data)
    finally:
        began=time.monotonic();time.sleep(5);data['cooldown']=resources['snapshot']();data['cooldown']['idle_ms']=(time.monotonic()-began)*1000
        data['history_delta']=data['cooldown']['history']['count']-data['before']['history']['count'];data['integrity']=data['cooldown']['history']['integrity'];data['privacy_after']=n['command'](dict(action='privacy'))
        hardening.write_record(output,data)
        report=hardening.fallback_stability_report(data)
        report['privacy_unchanged']=all(data['privacy_before'][key]==data['privacy_after'][key] for key in ('primary','clipboard','klipper'))
        report['unexpected_capture_files']=sorted(set(data['privacy_after']['png_files'])-set(data['privacy_before']['png_files']))
        hardening.write_record(root/'08-09-fixture-support-report.json',report);print(json.dumps(report),flush=True)

if __name__=='__main__':
    if sys.argv[1]=='setup':setup()
    elif sys.argv[1]=='run':run()
