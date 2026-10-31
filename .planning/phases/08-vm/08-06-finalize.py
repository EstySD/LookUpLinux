"""Recompute the candidate from retained actual rows; finish old-controller cleanup."""
import copy,hashlib,json,subprocess
from pathlib import Path
from tools.check_games import captured_game_report,pilot_cleanup_steps
from tools.check_hardening import vm_input

root=Path('.planning/phases/08-vm')
def read(name):return json.loads((root/name).read_text())
def write(name,value):(root/name).write_text(json.dumps(value,indent=2))
prior_controller=read('08-06-cleanup-final.json')
if not (root/'08-06-cleanup-controller-original.json').exists():write('08-06-cleanup-controller-original.json',prior_controller)
else:prior_controller=read('08-06-cleanup-controller-original.json')
def run(*args):
    p=subprocess.run(args,capture_output=True,text=True,timeout=30)
    return dict(exit=p.returncode,stdout=p.stdout,stderr=p.stderr)
def info(identity):
    p=run('C:/Program Files/Oracle/VirtualBox/VBoxManage.exe','showvminfo',identity,'--machinereadable')
    assert p['exit']==0
    return dict(line.split('=',1) for line in p['stdout'].splitlines() if '=' in line)
def no_guest(command):raise RuntimeError('unexpected running VM during closure; explicit guest reconciliation required')
closure=pilot_cleanup_steps(prior_controller['prior'],{},info,run,no_guest,vm_input)
guest=json.loads(prior_controller['guest_cleanup']);registry=json.loads(guest['registry']['stdout'])
physical=read('08-06-removed-physical-key.json');first_remove=read('08-06-guest-cleanup-first.json')
gates=dict(input_release_observed='release' in prior_controller and 'mouse_release' in prior_controller,
    owner_stopped=registry['owner'] is False,owned_processes_stopped=guest['remaining']==[],
    package_absent=guest['package_absent'] is True,package_removal_exit_zero=first_remove['package']['exit']==0,
    product_key_inactive=registry['keys']==[] and physical['keys']==[] and physical['owner'] is False,
    pilot_data_retained=guest['retained'] is True,original_data_retained=guest['original_data_retained'] is True,
    clone_off=closure['clone_off'],original_off=closure['original_off'],settings_restored=closure['settings_restored'])
write('08-06-cleanup-final.json',dict(passed=all(gates.values()),gates=gates,observations=closure,
    prior_controller='08-06-cleanup-controller-original.json',guest=guest,
    original_action='read-only VM state only; historical Phase07 unknown-actor exception unchanged',
    notes=['SSH poweroff disconnect triggered the retained old-controller cleanup error; updated independent cleanup restored settings only after actual OFF.',
           '3Doff and shared clipboard disabled during game; prior3Don/bidirectional restored afterOFF.',
           'No network policy, monitor layout, input-grab policy or global activation environment changed.',
           'Owned one-shot helpers/input ACL ended with actual guest shutdown; profiles/history/config/cards/unrelated data retained.']))
process=read('08-06-raw-game-process.json');acquisition=read('08-06-raw-acquisition.json')
text=(root/'08-06-raw-profile-clientlog.txt').read_text()
assert 'init: world (1302)' in text and 'init: localconnect' in text
name=next(line.removeprefix('Renderer: ') for line in text.splitlines() if line.startswith('Renderer: '))
routes=[]
for index,filename,tokens in ((1,'08-06-pilot-name-persistent.json',('522383335795','537470263570')),
                              (2,'08-06-route2.json',('583541202128','586447583355'))):
    raw=read(filename);row=copy.deepcopy(raw['route']);runtime=raw['runtime_before_input']
    assert runtime['process']['pid']==process['pid'] and runtime['process']['start']==process['start']
    camera,movement=[read('08-06-raw-control-'+token+'.json')['proof'] for token in tokens]
    row['observer_scene']=row['scene'];row['scene']='local_map_scoreboard'
    row['scene_binding']='Actual ac_desert local map/scoreboard in raw unchanged PNG; original observer emitted its Wesnoth default label.'
    row['grab']=dict(runtime['grab'],driver='wayland',sdl=runtime['renderer'],events=runtime['events'])
    row['gameplay']=dict(physical=True,action='separate physical relative camera then W movement',game_active=camera['game_active'] and movement['game_active'],
        game_pid=process['pid'],game_start=process['start'],input_ns=camera['input_ns'],observed_change=True,
        before_sha256=camera['before_sha256'],after_sha256=movement['after_sha256'],camera=camera,movement=movement)
    routes.append(row)
data=dict(name='AssaultCube',engine='AssaultCube',engine_version='1.3.0.2',version='1.3.0.2',runtime_version='world1302',
    release_qualification='Official v1.3.0.2 Linux asset filename is LockdownEdition_RC1; no final/stable binary claim',
    acquisition=dict(acquisition,release_asset='RC1'),process=process,
    renderer=dict(name=name,observed=True,pid=process['pid'],start=process['start'],kind='game_gl_log',text=text,
        log_sha256=hashlib.sha256(text.encode()).hexdigest(),binding='Same owned process/profile clientlog flushed by physical /quit after both routes'),
    mode='fullscreen',window=dict(id=routes[0]['window_id'],pid=process['pid'],fullscreen=True,observed=True,rect=[0,0,1280,800],screen=[0,0,1280,800]),
    routes=routes,cleanup='08-06-cleanup-final.json',rejected_history='08-doom-final-report.json',
    limits=['Automatic startup HTTPHEAD updates.txt returned404; localconnect/map only, no multiplayer; no zero-network claim.',
            'Software llvmpipe/3Doff environment; borderless and second output unverified.',
            'Read-only Source and SDL taps; no image/OCR/Query/result replacement; no new1500ms game bound.'],human_acceptance=False)
data['report']=captured_game_report(data)
write('08-assaultcube-final-report.json',data)
print(json.dumps(dict(candidate=data['report'],cleanup=gates)))
