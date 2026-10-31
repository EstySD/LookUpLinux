"""Recompute observed cleanup and the still-incomplete captured-game candidate."""
import copy,hashlib,json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from tools.check_games import captured_game_report
from tools.check_hardening import write_record

root=Path('.planning/phases/08-vm')
def read(name):return json.loads((root/name).read_text())
def save(name,value):write_record(root/name,value)
for name in ('08-assaultcube-final-report.json','08-06-cleanup-final.json'):
    destination=root/('08-06-pre-takeover-'+name)
    if not destination.exists():destination.write_bytes((root/name).read_bytes())

controller=read('08-06-takeover-cleanup-observations.json')
guest=read('08-06-recovery-guest-cleanup-final.json')
removal=read('08-06-recovery-guest-cleanup-removal.json')
registry=json.loads(guest['registry']['stdout']);key=read('08-06-takeover-removed-key.json')
actions=[json.loads(line) for line in (root/'08-06-guarded-actions.jsonl').read_text().splitlines()]
host_mutations=[row for row in controller['host_actions'] if row['mutating']]
scope=bool(host_mutations and actions) and all(row['argv'][2]=='cf207909-94b5-4b49-8bd8-ccff973c1dc8' for row in host_mutations)
scope=scope and all(row['target']=='cf207909-94b5-4b49-8bd8-ccff973c1dc8' and row.get('port',2227)==2227 for row in actions)
gates=dict(input_release_observed=controller['release']['ok'] is True and controller['mouse_release']['ok'] is True,
    owner_stopped=registry['owner'] is False,owned_processes_stopped=guest['remaining']==[],
    package_absent=guest['package_absent'] is True,package_removal_exit_zero=removal['package']['exit']==0,
    product_key_inactive=registry['keys']==[] and all(row['after']==[] for row in key['changed']),
    unrelated_shortcuts_preserved=key['unrelated_preserved'] is True,
    pilot_data_retained=guest['retained'] is True,original_data_retained=guest['original_data_retained'] is True,
    clone_off=controller['clone_off'] is True,settings_restored=controller['settings_restored'] is True,
    original_state_respected=scope and controller['original_state_respected'] is True)
save('08-06-cleanup-final.json',dict(passed=all(gates.values()),gates=gates,
    policy='USER_KEEP_RUNNING: external original lifecycle is untouched; no original OFF or state-equality gate',
    observations='08-06-takeover-cleanup-observations.json',guest='08-06-recovery-guest-cleanup-final.json',
    removal='08-06-recovery-guest-cleanup-removal.json',action_audit='08-06-guarded-actions.jsonl',
    historical_limits=['Expired controller86089 did not hot-reload later DMI guard; its cleanup receipt remains separately retained.',
        'Historical Phase07 unknown-actor original-disk exception is unchanged; no original disk or guest inspected.']))

runtime=read('08-06-recovery-preflight.json');process=runtime['process']
gl=next(row for row in runtime['renderer'] if row['operation']=='gl_context')
raw=read('08-06-recovery-route1.json');row=copy.deepcopy(raw['route']);before=raw['runtime_before_input']
row['grab']=dict(before['grab'],driver='wayland',sdl=before['renderer'],events=before['events'])
movement=read('08-06-recovery-movement1.json')['observation']['proof']
camera=read('08-06-recovery-camera1.json')['observation']['proof']
row['gameplay']=dict(physical=True,action='W movement, eight calibration-only +/-4 pulses, separate measured two +60 relative camera pulses',
    game_active=movement['game_active'] and camera['game_active'],game_pid=process['pid'],game_start=process['start'],
    input_ns=movement['input_ns'],observed_change=all(proof['world_change']['changed_pixels']>=1383 for proof in (movement,camera)),
    before_sha256=movement['before_sha256'],after_sha256=camera['after_sha256'],movement=movement,camera=camera)
acquisition=read('08-06-raw-preserved-acquisition.json');acquisition['release_asset']='RC1'
data=dict(name='AssaultCube',engine='AssaultCube',engine_version='1.3.0.2',version='1.3.0.2',
    release_qualification='Official Linux LockdownEdition_RC1 asset; no final/stable binary claim',acquisition=acquisition,process=process,
    renderer=dict(kind='actual_sdl_gl_context',name=gl['renderer'],observed=True,pid=process['pid'],start=process['start'],record=gl,
        log_sha256=hashlib.sha256(json.dumps(gl,sort_keys=True,separators=(',',':')).encode()).hexdigest()),
    mode='fullscreen',window=dict(id=row['window_id'],pid=process['pid'],fullscreen=True,observed=True,
        rect=[0,0,1280,800],screen=[0,0,1280,800],sdl_window=gl['window']),routes=[row],
    cleanup='08-06-cleanup-final.json',configuration=dict(command='menufont score mono',shipped_assets='08-06-font-assets-unchanged.json'),
    completed_routes=1,required_routes=2,failed_attempt='08-06-recovery-route2.json',
    frozen_diagnostic='08-06-recovery-frozen-diagnostic.json',rejected_history='08-doom-final-report.json',
    prior_candidate='08-06-pre-takeover-08-assaultcube-final-report.json',
    raw_manifest='08-06-artifact-manifest.json',human_acceptance=False,
    limits=['Second changed-source actual production lookup emitted stage6 without a selected Query; mandatory two-route gate remains open.',
        'Same frozen source/default PSM6 reproduces no selection; supported PSM11 selects name at89.277435 confidence. Diagnostic only, production unchanged.',
        'Earlier observer timeout and expired-controller attempts remain unaccepted history; no stale-process route mixing.',
        'No new1500ms game claim; complete current route latency6244.616646ms. Software llvmpipe, one output, fullscreen only.'])
data['report']=captured_game_report(data)
save('08-assaultcube-final-report.json',data)
manifest={path.name:dict(bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    for path in root.iterdir() if path.is_file() and (path.name.startswith('08-06-') or path.name=='08-assaultcube-final-report.json')
    and path.name not in ('08-06-artifact-manifest.json','08-06-SUMMARY.md','08-06-PLAN.md')}
save('08-06-artifact-manifest.json',manifest)
print(json.dumps(dict(candidate=data['report'],cleanup=gates,manifest_files=len(manifest))))
