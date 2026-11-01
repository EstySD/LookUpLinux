"""Assemble the two current routes from retained native sources and controls."""
import base64,copy,hashlib,json,runpy
from pathlib import Path
from tools.check_games import captured_game_report
root=Path('.planning/phases/08-vm');m=runpy.run_path(str(root/'08-09-games.py'))
def read(name):return json.loads((root/name).read_text())
runtime=m['command'](dict(action='doom-runtime-evidence'));m['save']('08-09-game-runtime-final.json',runtime)
process=runtime['process'];gl=next(row for row in runtime['renderer'] if row['operation']=='gl_context')
rows=[];files=[]
for index in (1,2):
    raw=read('08-09-game-route'+str(index)+'.json');row=copy.deepcopy(raw['route']);before=raw['runtime_before_input']
    row['grab']=dict(before['grab'],driver='wayland',sdl=before['renderer'],events=before['events'])
    movement=read('08-09-game-movement'+str(index)+'.json')['observation']['proof'];camera=read('08-09-game-camera'+str(index)+'.json')['observation']['proof']
    row['gameplay']=dict(physical=True,action='W movement, eight calibration-only +/-4 pulses, separate measured two +60 relative camera pulses',
        game_active=movement['game_active'] and camera['game_active'],game_pid=process['pid'],game_start=process['start'],input_ns=movement['input_ns'],
        observed_change=all(proof['world_change']['changed_pixels']>=1383 for proof in (movement,camera)),
        before_sha256=movement['before_sha256'],after_sha256=camera['after_sha256'],movement=movement,camera=camera)
    rows.append(row)
    for proof in (movement,camera):files.extend(proof[key] for key in ('before_path','after_path'))
paths=m['guest']('''import base64,json
from pathlib import Path
files='''+repr(files)+'''
files+=['/home/lookup07/.local/state/lookup-games-08/assaultcube/'+name for name in ('sdl-observer.c','sdl-observer.jsonl','profile/clientlog.txt','acquisition.json','lookup/daemon.log')]
print(json.dumps({name:base64.b64encode(Path(name).read_bytes()).decode() for name in files}))''')
directory=root/'08-09-game-raw';directory.mkdir(exist_ok=True)
for name,value in json.loads(paths).items():(directory/Path(name).name).write_bytes(base64.b64decode(value))
acquisition=read('08-06-raw-preserved-acquisition.json');acquisition['release_asset']='RC1'
data=dict(name='AssaultCube',engine='AssaultCube',engine_version='1.3.0.2',version='1.3.0.2',release_qualification='Official Linux LockdownEdition_RC1 asset',
    acquisition=acquisition,process=process,renderer=dict(kind='actual_sdl_gl_context',name=gl['renderer'],observed=True,pid=process['pid'],start=process['start'],record=gl,
        log_sha256=hashlib.sha256(json.dumps(gl,sort_keys=True,separators=(',',':')).encode()).hexdigest()),mode='fullscreen',
    window=dict(id=rows[0]['window_id'],pid=process['pid'],fullscreen=True,observed=True,rect=[0,0,1280,800],screen=[0,0,1280,800],sdl_window=gl['window']),
    routes=rows,package_receipt='08-09-package-receipt.json',configuration=dict(command='menufont score mono',shipped_assets='08-06-font-assets-unchanged.json'),
    human_acceptance=False,limits=['Game latencies are independent of the1500ms desktop median criterion.','Software llvmpipe, one output, fullscreen1280x800; historical06 remains unaccepted.'])
data['report']=captured_game_report(data);m['save']('08-assaultcube-cascade-report.json',data);print(json.dumps(data['report']))
