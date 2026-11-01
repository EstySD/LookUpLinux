"""Transfer the frozen typed observer; physical proofs remain explicit actions."""
import base64,hashlib,json,runpy,sys
from pathlib import Path
root=Path('.planning/phases/08-vm');n=runpy.run_path(str(root/'08-07-native.py'))
def user(action):
    code="import subprocess;p=subprocess.run(['sudo','-n','-H','-u','lookup07','python','/home/lookup07/.local/state/lookup-final-07/registry.py',"+repr(action)+"],capture_output=True,text=True,timeout=25);print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)"
    return json.loads(n['guest'](code))
if __name__=='__main__':
    action=sys.argv[1]
    if action=='transfer':
        source=(root/'08-07-registry.py').read_bytes();payload=base64.b64encode(source).decode()
        print(n['guest']("import base64,os;from pathlib import Path;p=Path('/home/lookup07/.local/state/lookup-final-07');p.mkdir(mode=0o700,exist_ok=True);os.chown(p,1001,1001);q=p/'registry.py';assert not q.exists();q.write_bytes(base64.b64decode("+repr(payload)+"));os.chown(q,1001,1001)"))
        value=user('dump');(root/'08-07-postmanual-registry.json').write_text(json.dumps(value,indent=2));print(json.dumps(dict(components=len(value['components']),actions=len(value['bindings']))))
    else:
        value=user(action);(root/('08-07-registry-'+action+'.json')).write_text(json.dumps(value,indent=2));print(json.dumps({key:value[key] for key in value if key not in ('registry','before','after')}))
