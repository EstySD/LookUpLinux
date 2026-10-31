"""Serialized clone-only physical controls for the user-kept-running original."""
import base64,json,subprocess,time
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from tools import check_games as games,check_hardening as hardening
root=Path('.planning/phases/08-vm')
def audit(value):
    with (root/'08-06-guarded-actions.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(dict(at_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),target='cf207909-94b5-4b49-8bd8-ccff973c1dc8',**value))+'\n')
def input_command(action,**values):
    args=['powershell','-NoProfile','-File',str(root/'08-06-owned-input.ps1'),'-Action',action]
    for key,value in values.items():args+=['-'+key,str(value)]
    result=subprocess.run(args,capture_output=True,timeout=8,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    audit(dict(transport='UUID/disk/MAC/NAT guarded physical input',action=action,values=values,exit=result.returncode))
hardening.vm_input=input_command
def guest(script):
    script="from pathlib import Path; assert Path('/sys/class/dmi/id/product_uuid').read_text().strip()=='097920cf-b594-494b-8bd8-ccff973c1dc8'\n"+script
    payload=base64.b64encode(script.encode()).decode()
    child=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=5','-o','HostKeyAlias=lookup-gsd-07','-o',
        'UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-p','2227','archvm',
        "sudo -n python -c \"import base64; exec(base64.b64decode('"+payload+"'))\""],capture_output=True,text=True,timeout=30)
    audit(dict(transport='pinned SSH',port=2227,alias='lookup-gsd-07',dmi='097920cf-b594-494b-8bd8-ccff973c1dc8',payload_sha256=__import__('hashlib').sha256(script.encode()).hexdigest(),exit=child.returncode))
    if child.returncode:raise RuntimeError((child.stderr or child.stdout)[-1500:])
    return child.stdout
_vm_command=games.vm_command
def guarded_command(value):
    guest('pass')
    if value['action']=='start-route':
        encoded=base64.b64encode(json.dumps(value).encode()).decode()
        code="import subprocess; p=subprocess.run(['sudo','-n','-H','-u','lookup07','env','OMP_THREAD_LIMIT=1','python','/home/lookup07/check_games.py','--guest-command',"+repr(encoded)+"],capture_output=True,text=True,timeout=25);print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)"
        result=json.loads(guest(code))
        audit(dict(transport='DMI guarded guest command',action=value['action'],observer_only_OMP_THREAD_LIMIT=1))
        return result
    audit(dict(transport='DMI checked pinned guest command',port=2227,action=value['action']))
    return _vm_command(value)
games.vm_command=guarded_command
def command(action,**values):return games.vm_command(dict(action=action,game_kind='assaultcube',**values))
def record(name,value):hardening.write_record(root/name,value);return value
def settle():
    values=[]
    for index in range(8):
        stamp=time.time_ns();input_command('Relative',X=4 if index%2==0 else -4,Y=0)
        values.append(dict(host_wall_ns=stamp,x=4 if index%2==0 else -4));time.sleep(.15)
    return record('08-06-takeover-settle-'+str(time.time_ns())+'.json',dict(calibration_only=True,events=values))
def text(value):
    codes=dict(zip('abcdefghijklmnopqrstuvwxyz',[0x1e,0x30,0x2e,0x20,0x12,0x21,0x22,0x23,0x17,0x24,0x25,0x26,0x32,0x31,0x18,0x19,0x10,0x13,0x1f,0x14,0x16,0x2f,0x11,0x2d,0x15,0x2c]))
    codes.update({' ':0x39,'/':0x35,'1':0x02,'0':0x0b})
    input_command('Keys',Codes=' '.join(f'{codes[c]:02x} {codes[c]+128:02x}' for c in value))
def console(value):
    text('/');time.sleep(.3);text(value);time.sleep(.2)
    input_command('Keys',Codes='1c 9c');time.sleep(.5)

if __name__=='__main__':
    import sys
    action=sys.argv[1]
    if action=='install-font-pilot':
        import hashlib
        names=subprocess.check_output(['git','ls-tree','-r','--name-only','5d04a4c','lookup'],text=True).splitlines()
        expected={name:hashlib.sha256(subprocess.check_output(['git','show','5d04a4c:'+name])).hexdigest() for name in names}
        code='''from pathlib import Path
import subprocess,hashlib,json
assert Path('/sys/class/dmi/id/product_uuid').read_text().strip()=='097920cf-b594-494b-8bd8-ccff973c1dc8'
package=Path('/home/arch/lookup-readme-08-build/lookup-linux-0.1.0-1-x86_64.pkg.tar.zst')
digest=hashlib.sha256(package.read_bytes()).hexdigest()
assert digest=='7aa3cf123457c753fa572efbd58062f81cd1e4f4fc2387fe4a7505665ab480f3'
assert subprocess.run(['pacman','-Q','lookup-linux'],capture_output=True).returncode!=0
expected='''+repr(expected)+'''
observed={name:hashlib.sha256(subprocess.check_output(['bsdtar','-xOf',str(package),'usr/lib/lookup/app/'+name])).hexdigest() for name in expected}
assert observed==expected
result=subprocess.run(['pacman','-U','--noconfirm',str(package)],capture_output=True,text=True,timeout=20)
assert result.returncode==0,result.stderr
print(json.dumps(dict(package=str(package),sha256=digest,baseline_absent=True,application_members=len(observed),exact_5d04a4c_match=True,install_exit=result.returncode,stdout=result.stdout)))'''
        print(record('08-06-font-package-install.json',json.loads(guest(code))))
    if action=='setup':
        print(guest('''from pathlib import Path
import subprocess,json,hashlib
assert Path('/sys/class/dmi/id/product_uuid').read_text().strip()=='097920cf-b594-494b-8bd8-ccff973c1dc8'
subprocess.run(['install','-o','lookup07','-g','lookup07','-m','644','/home/arch/lookup-games-08-takeover.py','/home/lookup07/check_games.py'],check=True)
events=[]
for path in Path('/sys/class/input').glob('event*'):
    if path.joinpath('device/name').read_text().strip() in ('AT Translated Set 2 keyboard','ImExPS/2 Generic Explorer Mouse','VirtualBox USB Tablet','VirtualBox mouse integration'):
        events.append('/dev/input/'+path.name)
subprocess.run(['setfacl','-m','u:lookup07:r',*events],check=True)
print(json.dumps(dict(dmi_verified=True,input_devices=events,harness_sha256=hashlib.sha256(Path('/home/lookup07/check_games.py').read_bytes()).hexdigest())))'''))
        print(command('archive-dead'))
        print(command('prepare-doom-observer'))
        print(record('08-06-takeover-game-process.json',command('launch')))
        print(command('launch-lookup'))
    elif action=='runtime':print(json.dumps(record('08-06-takeover-gl-preflight.json',command('doom-runtime-evidence'))))
    elif action=='settle':print(settle())
    elif action=='scores':console('showscores 1')
    elif action=='font':console('menufont score mono')
    elif action in ('font-pose1','font-pose2'):
        code='''import sys,os,json,hashlib,base64,subprocess
from pathlib import Path
sys.path.insert(0,'/usr/lib/lookup/app')
from lookup import platform,capture,ocr
from PyQt6.QtGui import QGuiApplication
env=platform.session_env();os.environ.update(env);app=QGuiApplication([])
root=Path.home()/'.local/state/lookup-games-08/assaultcube';metadata=json.loads((root/'game-process.json').read_text())
path=Path('/proc',str(metadata['pid']));assert path.stat().st_uid==1001 and int((path/'stat').read_text().split(') ',1)[1].split()[19])==metadata['start']
point=platform.cursor_position(env);frame=capture.capture_monitor(platform.monitors(env)[0],env)
path=root/'''+repr(action+'.png')+''';path.write_bytes(frame.png)
result=ocr.recognize_image(path,point);prepared,transform=ocr._prepare_image(path,point,ocr.DEFAULT_ENLARGE,ocr.DEFAULT_INVERT)
raw=subprocess.run(['tesseract','stdin','stdout','-l','eng','--psm',str(ocr.DEFAULT_PSM),'tsv'],input=prepared,capture_output=True,check=True,timeout=ocr.OCR_TIMEOUT,env=dict(env,OMP_THREAD_LIMIT='1')).stdout
words=ocr.parse_tsv(raw,transform)
def distance(word):
    x,y,w,h=word.box;return (x+w/2-point[0])**2+(y+h/2-point[1])**2
print(json.dumps(dict(process=metadata,point=point,source_sha256=hashlib.sha256(frame.png).hexdigest(),prepared_sha256=hashlib.sha256(prepared).hexdigest(),psm=ocr.DEFAULT_PSM,selection=None if result.selection is None else dict(word=result.selection.word,context=result.selection.context),nearest=[dict(text=w.text,confidence=w.confidence,box=w.box) for w in sorted(words,key=distance)[:8]],png_base64=base64.b64encode(frame.png).decode())))'''
        payload=guest("import subprocess;from pathlib import Path;assert Path('/sys/class/dmi/id/product_uuid').read_text().strip()=='097920cf-b594-494b-8bd8-ccff973c1dc8';p=subprocess.run(['sudo','-n','-H','-u','lookup07','python','-c',"+repr(code)+"],capture_output=True,text=True,timeout=12);print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)")
        value=json.loads(payload);(root/('08-06-'+action+'.png')).write_bytes(base64.b64decode(value.pop('png_base64')))
        record('08-06-'+action+'.json',value);print(json.dumps(value))
    elif action=='snapshot':
        value=command('snapshot');record('08-06-takeover-snapshot.json',value)
        if 'png_base64' in value:(root/'08-06-takeover-snapshot.png').write_bytes(base64.b64decode(value['png_base64']))
        print(json.dumps({k:v for k,v in value.items() if k!='png_base64'}))
    elif action in ('route1','route2'):
        index=int(action[-1]);games.run_lookup_route(root/('08-06-takeover-route'+str(index)+'.json'),'name',index,game_kind='assaultcube',point=json.loads((root/'08-06-takeover-snapshot.json').read_text())['cursor'])
    elif action=='route2deaths':
        games.run_lookup_route(root/'08-06-takeover-route2-deaths.json','deaths',2,game_kind='assaultcube',point=json.loads((root/'08-06-takeover-snapshot.json').read_text())['cursor'])
    elif action in ('font-route1','font-route2'):
        index=int(action[-1]);games.run_lookup_route(root/('08-06-font-route'+str(index)+'.json'),'name',index,game_kind='assaultcube',point=[733,378])
    elif action in ('movement1','movement2','camera1','camera2'):
        kind='movement' if action.startswith('movement') else 'camera'
        print(games.run_control(root/('08-06-takeover-'+action+'.json'),kind))
    elif action in ('font-movement1','font-movement2','font-camera1','font-camera2'):
        kind='movement' if 'movement' in action else 'camera'
        print(games.run_control(root/('08-06-'+action+'.json'),kind))
    elif action=='collect':
        runtime=command('doom-runtime-evidence');record('08-06-takeover-runtime-final.json',runtime)
        record('08-06-takeover-observations.json',command('observations'))
        paths=['acquisition.json','game-process.json','sdl-observer.jsonl','profile/clientlog.txt','package-reinstalled.json','retention-before.json']
        for kind in ('movement1','camera1'):
            proof=json.loads((root/('08-06-takeover-'+kind+'.json')).read_text())['observation']['proof']
            paths.extend(Path(proof[key]).name for key in ('before_path','after_path'))
        payload=guest('''from pathlib import Path
import json,hashlib,base64,subprocess
root=Path('/home/lookup07/.local/state/lookup-games-08/assaultcube')
names='''+repr(paths)+'''
out={}
for name in names:
    path=root/name
    if path.is_file():out[name]=base64.b64encode(path.read_bytes()).decode()
archive=root/'AssaultCube_v1.3.0.2_LockdownEdition_RC1.tar.bz2'
members={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in Path('/usr/lib/lookup/app').rglob('*') if path.is_file() and '__pycache__' not in str(path)}
print(json.dumps(dict(files=out,acquisition_observed=dict(bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest()),installed_members=members,package=subprocess.run(['pacman','-Q','lookup-linux'],capture_output=True,text=True).stdout)))''')
        bundle=json.loads(payload)
        for name,encoded in bundle.pop('files').items():
            (root/('08-06-takeover-raw-'+name.replace('/','-'))).write_bytes(base64.b64decode(encoded))
        record('08-06-takeover-installed-source.json',bundle)
        for filename in ('08-06-takeover-route2.json','08-06-takeover-route2-deaths.json'):
            raw=json.loads((root/filename).read_text());source=raw['lookup_observation']['source_observation']
            image=command('image',kind='source',**{key:source[key] for key in ('pid','run','request')})
            (root/(Path(filename).stem+'-source.png')).write_bytes(base64.b64decode(image['png_base64']))
        print(dict(collected=True,installed_members=len(bundle['installed_members'])))
    elif action=='cleanup-guest':
        input_command('Keys',Codes='01 81 8f 91 9f 9e a0 aa b6 e0 db e0 dc')
        input_command('Pointer',X=640,Y=400,Buttons=0)
        record('08-06-takeover-release.json',dict(commands_returned=True,target='cf207909-94b5-4b49-8bd8-ccff973c1dc8',key_and_mouse_release=True))
        print(command('stop-lookup'))
        console('quit')
        time.sleep(1)
        result=guest("import subprocess; p=subprocess.run(['python','/home/arch/lookup-games-08-pilot-cleanup.py'],capture_output=True,text=True); print(p.stdout); print(p.stderr); raise SystemExit(p.returncode)")
        record('08-06-takeover-guest-cleanup.json',json.loads(result))
        print(dict(guest_cleanup_recorded=True))
    elif action=='clear-key':
        output=guest('''from pathlib import Path
import subprocess,base64
assert Path('/sys/class/dmi/id/product_uuid').read_text().strip()=='097920cf-b594-494b-8bd8-ccff973c1dc8'
code="""import os,json,configparser
from pathlib import Path
os.environ.update(XDG_RUNTIME_DIR='/run/user/1001',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/1001/bus')
from PyQt6.QtCore import QCoreApplication,QMetaType
from PyQt6.QtDBus import QDBusConnection,QDBusMessage,QDBus,QDBusArgument
app=QCoreApplication([]);bus=QDBusConnection.sessionBus()
def call(method,args):
    message=QDBusMessage.createMethodCall('org.kde.kglobalaccel','/kglobalaccel','org.kde.KGlobalAccel',method);message.setArguments(args)
    reply=bus.call(message,QDBus.CallMode.Block,1200)
    assert reply.type()!=QDBusMessage.MessageType.ErrorMessage
    return reply.arguments()[0] if reply.arguments() else None
def stringlist(value):return QDBusArgument(value,QMetaType.Type.QStringList.value)
def unrelated():
    parser=configparser.ConfigParser(interpolation=None,strict=False);parser.optionxform=str
    parser.read(Path.home()/'.config/kglobalshortcutsrc')
    return {section:dict(parser[section]) for section in parser.sections() if section!='org.lookup.Linux.desktop'}
before=unrelated();actions=call('allActionsForComponent',[stringlist(['org.lookup.Linux.desktop','','',''])]);changed=[]
for action in actions or []:
    if tuple(action[:2])!=('org.lookup.Linux.desktop','_launch'):continue
    old=call('shortcut',[stringlist(action)])
    keys=QDBusArgument();keys.beginArray(QMetaType.Type.Int.value);keys.endArray()
    call('setForeignShortcut',[stringlist(action),keys])
    observed=call('shortcut',[stringlist(action)]);assert not any(observed)
    changed.append(dict(action=action,before=old,after=observed))
print(json.dumps(dict(owner=bus.interface().isServiceRegistered('org.lookup.Linux').value(),changed=changed,unrelated_preserved=before==unrelated())))
"""
p=subprocess.run(['sudo','-n','-H','-u','lookup07','python','-c',code],capture_output=True,text=True,timeout=10)
print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)''')
        record('08-06-takeover-removed-key.json',json.loads(output));print(output)
        cleanup=json.loads(guest("import subprocess; p=subprocess.run(['python','/home/arch/lookup-games-08-pilot-cleanup.py'],capture_output=True,text=True); print(p.stdout); raise SystemExit(p.returncode)"))
        record('08-06-recovery-guest-cleanup-removal.json',cleanup);print(json.dumps(cleanup))
    elif action in ('diagnose','diagnose11'):
        sources=[]
        for filename in ('08-06-takeover-route1.json','08-06-takeover-route2.json','08-06-takeover-route2-deaths.json'):
            row=json.loads((root/filename).read_text())
            source=row.get('lookup_observation',{}).get('source_observation')
            sources.append(dict(attempt=filename,source=source))
        code='''from pathlib import Path
import sys,tarfile,json,subprocess,hashlib
assert Path('/sys/class/dmi/id/product_uuid').read_text().strip()=='097920cf-b594-494b-8bd8-ccff973c1dc8'
destination=Path('/home/lookup07/.local/state/lookup-games-08/assaultcube/diagnostic-source')
destination.mkdir(exist_ok=True)
with tarfile.open('/home/arch/lookup-games-08-diagnostic-source.tar') as archive:archive.extractall(destination,filter='data')
sys.path.insert(0,str(destination))
from lookup import ocr
from PyQt6.QtGui import QImage
rows=[]
for item in '''+repr(sources)+''':
    source=item['source']; path=Path(source['image_path']); point=source['cursor']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256']
    recognition=ocr.recognize_image(path,point)
    prepared,transform=ocr._prepare_image(path,point,ocr.DEFAULT_ENLARGE,ocr.DEFAULT_INVERT)
    raw=subprocess.run(['tesseract','stdin','stdout','-l','eng','--psm',str(ocr.DEFAULT_PSM),'tsv'],input=prepared,capture_output=True,check=True,timeout=ocr.OCR_TIMEOUT,env=dict(__import__('os').environ,OMP_THREAD_LIMIT='1')).stdout
    words=ocr.parse_tsv(raw,transform)
    def distance(word):
        x,y,w,h=word.box;return (x+w/2-point[0])**2+(y+h/2-point[1])**2
    nearest=sorted(words,key=distance)[:12]
    selected=recognition.selection
    rows.append(dict(attempt=item['attempt'],source_sha256=source['sha256'],point=point,defaults=dict(psm=ocr.DEFAULT_PSM,enlarge=ocr.DEFAULT_ENLARGE,invert=ocr.DEFAULT_INVERT),prepared_sha256=hashlib.sha256(prepared).hexdigest(),selection=None if selected is None else dict(word=selected.word,context=selected.context),nearest=[dict(text=w.text,confidence=w.confidence,box=w.box) for w in nearest]))
print(json.dumps(dict(rows=rows,package_reinstalled=False,source_revision='5d04a4c',tesseract=subprocess.run(['tesseract','--version'],capture_output=True,text=True).stdout.splitlines()[0])))'''
        if action=='diagnose11':code=code.replace('recognition=ocr.recognize_image(path,point)','recognition=ocr.recognize_image(path,point,psm=11)').replace('ocr.DEFAULT_PSM','11')
        result=json.loads(guest(code))
        if action=='diagnose11':
            result.pop('package_reinstalled',None);result['scope']='Read-only frozen-source diagnostic; separate font-pilot installation recorded independently'
        record('08-06-takeover-'+('supported-psm11' if action=='diagnose11' else 'default')+'-ocr-diagnostic.json',result);print(json.dumps(result))
    elif action=='diagnose-recovery':
        failed=json.loads((root/'08-06-recovery-route2.json').read_text())['lookup_observation']['source_observation']
        code='''import os,sys,json,time,hashlib,subprocess
from pathlib import Path
sys.path.insert(0,'/usr/lib/lookup/app')
from lookup import ocr
source='''+repr(failed)+'''
path=Path(source['image_path']);point=source['cursor'];assert hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256']
rows=[]
for psm in (6,11):
    start=time.monotonic_ns();row=dict(psm=psm)
    try:
        value=ocr.recognize_image(path,point,psm=psm)
        row.update(selection=None if value.selection is None else dict(word=value.selection.word,context=value.selection.context),timings=value.timings)
    except Exception as error:row.update(exception=type(error).__name__,reason=getattr(error,'reason',None))
    row['elapsed_ms']=(time.monotonic_ns()-start)/1e6
    prepared,transform=ocr._prepare_image(path,point,ocr.DEFAULT_ENLARGE,ocr.DEFAULT_INVERT)
    row['prepared_sha256']=hashlib.sha256(prepared).hexdigest()
    proc=subprocess.run(['tesseract','stdin','stdout','-l','eng','--psm',str(psm),'tsv'],input=prepared,capture_output=True,timeout=8,env=dict(os.environ,OMP_THREAD_LIMIT='1'))
    words=ocr.parse_tsv(proc.stdout,transform)
    def distance(word):
        x,y,w,h=word.box;return (x+w/2-point[0])**2+(y+h/2-point[1])**2
    row['nearest']=[dict(text=w.text,confidence=w.confidence,box=w.box) for w in sorted(words,key=distance)[:8]]
    rows.append(row)
print(json.dumps(dict(source=source,diagnostics=rows,actual_default_psm=ocr.DEFAULT_PSM,min_confidence=ocr.MIN_CONFIDENCE,source_unchanged=True)))'''
        value=json.loads(guest("import subprocess;p=subprocess.run(['sudo','-n','-H','-u','lookup07','python','-c',"+repr(code)+"],capture_output=True,text=True,timeout=22);print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)"))
        record('08-06-recovery-frozen-diagnostic.json',value);print(json.dumps(value))
    elif action=='collect-all':
        record('08-06-recovery-runtime-final.json',command('doom-runtime-evidence'))
        record('08-06-recovery-observations-final.json',command('observations'))
        names={'acquisition.json','game-process.json','sdl-observer.jsonl','profile/clientlog.txt','package-reinstalled.json','retention-before.json'}
        for path in root.glob('08-06-*.json'):
            try:value=json.loads(path.read_text())
            except (ValueError,OSError):continue
            if not isinstance(value,dict):continue
            proof=value.get('observation',value).get('proof',{})
            for key in ('before_path','after_path'):
                if key in proof:names.add(Path(proof[key]).name)
            observation=value.get('lookup_observation',{}).get('source_observation',{})
            if observation.get('image_path'):
                names.add('lookup/observations/'+Path(observation['image_path']).name)
        names=sorted(names)
        for offset in range(0,len(names),12):
            code='''from pathlib import Path
import base64,json
root=Path('/home/lookup07/.local/state/lookup-games-08/assaultcube')
out={}
for name in '''+repr(names[offset:offset+12])+''':
    path=root/name;assert path.resolve().is_relative_to(root)
    if path.is_file():out[name]=base64.b64encode(path.read_bytes()).decode()
print(json.dumps(out))'''
            for name,encoded in json.loads(guest(code)).items():
                (root/('08-06-raw-preserved-'+name.replace('/','-'))).write_bytes(base64.b64decode(encoded))
        value=json.loads(guest('''from pathlib import Path
import hashlib,json,tarfile
root=Path('/home/lookup07/.local/state/lookup-games-08/assaultcube')
archive=root/'AssaultCube_v1.3.0.2_LockdownEdition_RC1.tar.bz2'
results={}
with tarfile.open(archive,'r:bz2') as bundle:
    for suffix in ('config/font_monospace.cfg','packages/misc/chars_monospace.png'):
        member=next(item for item in bundle.getmembers() if item.name.endswith('/'+suffix))
        original=hashlib.sha256(bundle.extractfile(member).read()).hexdigest()
        actual=hashlib.sha256((root/'package'/suffix).read_bytes()).hexdigest()
        results[suffix]=dict(archive_sha256=original,actual_sha256=actual,unchanged=original==actual)
print(json.dumps(dict(font_assets=results,archive_bytes=archive.stat().st_size,archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())))'''))
        record('08-06-font-assets-unchanged.json',value);print(dict(collected_files=len(names),assets=value))
