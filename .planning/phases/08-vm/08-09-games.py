"""Current observer on the fixed genuine AssaultCube configuration."""
import base64,json,runpy,sys,time
from pathlib import Path
from tools import check_games as games,check_hardening as hardening

root=Path('.planning/phases/08-vm');native=runpy.run_path(str(root/'08-09-native.py'))
guest=native['guest'];inputs=native['inputs'];hardening.vm_input=inputs

def command(value):
    encoded=base64.b64encode(json.dumps(dict(value,game_kind='assaultcube')).encode()).decode()
    prefix=['env','OMP_THREAD_LIMIT=1'] if value['action'] in ('start-route','snapshot') else []
    code="import subprocess;p=subprocess.run(['sudo','-n','-H','-u','lookup07',*"+repr(prefix)+",'python','/home/lookup07/check_games.py','--guest-command',"+repr(encoded)+"],capture_output=True,text=True,timeout=35);print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)"
    return json.loads(guest(code,timeout=40))
games.vm_command=command

def save(name,value):
    (root/name).write_text(json.dumps(value,indent=2));return value

def settle():
    rows=[]
    for index in range(8):
        rows.append(dict(host_wall_ns=time.time_ns(),x=4 if index%2==0 else -4))
        inputs('Relative',X=rows[-1]['x'],Y=0);time.sleep(.15)
    save('08-09-calibration-'+str(time.time_ns())+'.json',dict(calibration_only=True,events=rows))

def text(value):
    codes=dict(zip('abcdefghijklmnopqrstuvwxyz',[0x1e,0x30,0x2e,0x20,0x12,0x21,0x22,0x23,0x17,0x24,0x25,0x26,0x32,0x31,0x18,0x19,0x10,0x13,0x1f,0x14,0x16,0x2f,0x11,0x2d,0x15,0x2c]))
    codes.update({' ':0x39,'/':0x35,'1':0x02,'0':0x0b})
    inputs('Keys',Codes=' '.join(f'{codes[c]:02x} {codes[c]+128:02x}' for c in value))

def console(value):
    text('/');time.sleep(.3);text(value);time.sleep(.2);inputs('Keys',Codes='1c 9c');time.sleep(.5)

def setup():
    print(native['command'](dict(action='stop-owner')),flush=True)
    print(native['command'](dict(action='stop-observer')),flush=True)
    files={name:base64.b64encode(Path('tools',name).read_bytes().replace(b'\r\n',b'\n')).decode() for name in ('check_games.py','check_hardening.py')}
    print(guest('''import base64,hashlib,json,os
from pathlib import Path
files='''+repr(files)+'''
result={}
for name,encoded in files.items():
    path=Path('/home/lookup07')/name;data=base64.b64decode(encoded);path.write_bytes(data);os.chown(path,1001,1001);result[name]=hashlib.sha256(data).hexdigest()
print(json.dumps(result))'''),flush=True)
    print(command(dict(action='archive-dead')),flush=True)
    print(command(dict(action='prepare-doom-observer')),flush=True)
    save('08-09-game-process.json',command(dict(action='launch')))
    print(command(dict(action='launch-lookup')),flush=True)

if __name__=='__main__':
    action=sys.argv[1]
    if action=='setup':setup()
    elif action=='runtime':print(json.dumps(save('08-09-gl-preflight.json',command(dict(action='doom-runtime-evidence')))))
    elif action=='snapshot':
        value=command(dict(action='snapshot'));(root/'08-09-game-snapshot.png').write_bytes(base64.b64decode(value.pop('png_base64')))
        print(json.dumps(save('08-09-game-snapshot.json',value)))
    elif action=='scores':console('showscores 1')
    elif action=='font':console('menufont score mono')
    elif action=='settle':settle()
    elif action.startswith('route'):
        index=int(action[5:]);games.run_lookup_route(root/('08-09-game-route'+str(index)+'.json'),'name',index,game_kind='assaultcube',point=[733,378])
    elif action.startswith('movement') or action.startswith('camera'):
        kind='movement' if action.startswith('movement') else 'camera'
        print(games.run_control(root/('08-09-game-'+action+'.json'),kind))
