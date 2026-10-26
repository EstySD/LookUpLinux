"""Drive the owned Plasma spike from Windows; target actions use the same script."""
import argparse
import base64
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
import uuid
import signal

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lookup import platform, capture, ocr
from tools import vm_spike as spike

REMOTE = 'LookUpLinux-gsd-spike-04'
VBOX = 'C:/Program Files/Oracle/VirtualBox/VBoxManage.exe'


class GateTimeout(RuntimeError):
    def __init__(self, last):
        super().__init__('gate_timeout')
        self.last = last


def setup_owned(desktop, content, register, launch, save, rollback):
    """Persist cleanup ownership before each potentially failing setup step."""
    save([])
    pids = []
    try:
        desktop.write_text(content)
        register()
        for flags in (['--public-window'], ['--controlled']):
            pids.append(launch(flags))
            save(pids)
        return pids
    except Exception:
        rollback()
        raise


def accepted(evidence):
    restoration = evidence.get('restoration', {})
    return (not evidence.get('error') and not evidence.get('restoration_error') and
            not evidence.get('key_release_error') and evidence.get('required_remaining') == [] and
            all(restoration.get(key) is True for key in
                ('display_restored','desktop_restored','processes_stopped','shortcut_restored')))


def ensure_unlocked(env, is_locked, uid):
    """VM experiment only: use the authorized normal session-unlock operation."""
    if not is_locked():
        return False
    rows=platform.run(['loginctl','list-sessions','--no-legend'],env).decode('ascii').splitlines()
    for row in rows:
        fields=row.split()
        if len(fields)<2 or fields[1]!=str(uid) or not fields[0].isalnum():
            continue
        session=fields[0]
        kind=platform.run(['loginctl','show-session',session,'--property=Type','--value'],env).strip()
        if kind==b'wayland':
            platform.run(['loginctl','unlock-session',session],env)
    wait_for(is_locked,lambda locked:not locked,3)
    return True


def wait_for(read, predicate, timeout=12):
    deadline = time.monotonic()+timeout
    value = None
    while time.monotonic() < deadline:
        try:
            value = read()
        except RuntimeError as error:
            value = {'read_error':str(error)}
            time.sleep(.15)
            continue
        if predicate(value):
            return value
        time.sleep(.15)
    raise GateTimeout(value)


def target(action, payload):
    env = platform.session_env()
    os.environ.update(env)
    from PyQt6.QtCore import QCoreApplication
    from PyQt6.QtDBus import QDBusConnection, QDBusMessage, QDBus
    app = QCoreApplication([])
    bus = QDBusConnection.sessionBus()
    def call(service, path, interface, method, values=()):
        msg = QDBusMessage.createMethodCall(service, path, interface, method)
        msg.setArguments(list(values))
        reply = bus.call(msg, QDBus.CallMode.Block, 2000)
        if reply.type() == QDBusMessage.MessageType.ErrorMessage:
            raise RuntimeError('dbus_failed:'+method)
        return reply.arguments()[0] if reply.arguments() else None
    def status(fixture=False):
        return json.loads(call(spike.FIXTURE if fixture else spike.SERVICE, '/VMSpike', spike.INTERFACE, 'Status'))
    def start(flags):
        return subprocess.Popen([sys.executable, str(Path('tools/vm_spike.py').resolve()), *flags],
                                stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,start_new_session=True).pid
    folder = Path(env['XDG_RUNTIME_DIR'])/'lookup-vm-spike-04'
    snapshot = folder/'snapshot.json'
    desktop = Path.home()/'.local/share/applications'/spike.DESKTOP
    def restore():
        if not snapshot.exists():
            return dict(display_restored=True,desktop_restored=True,processes_stopped=True,shortcut_restored=True)
        saved=json.loads(snapshot.read_text())
        if saved.get('run_id') != payload.get('run_id') or not payload.get('run_id'):
            raise RuntimeError('snapshot_owner_mismatch')
        for service in (spike.SERVICE,spike.FIXTURE):
            try:
                pid=call('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','GetConnectionUnixProcessID',(service,))
                if any(p['pid']==pid for p in saved.get('processes',[])):
                    call(service,'/VMSpike',spike.INTERFACE,'Quit')
            except RuntimeError:
                pass
        # Also clean a child which failed before it could register its bus object.
        time.sleep(.3)
        remaining=[]
        for process in saved.get('processes',[]):
            proc=Path('/proc')/str(process['pid'])
            try:
                if proc.stat().st_uid != os.getuid() or proc.joinpath('stat').read_text().split(') ',1)[1].split()[19] != process['start']:
                    continue
                if str(Path('tools/vm_spike.py').resolve()).encode() not in proc.joinpath('cmdline').read_bytes().split(b'\x00'):
                    continue
                os.kill(process['pid'],signal.SIGTERM)
                remaining.append(process['pid'])
            except (FileNotFoundError,ProcessLookupError):
                pass
        time.sleep(.3)
        processes_stopped=all(not Path('/proc',str(pid)).exists() or Path('/proc',str(pid),'stat').read_text().split(') ',1)[1].startswith('Z ') for pid in remaining)
        display_error=False
        for output in saved['outputs']:
            try:
                platform.run(['kscreen-doctor',f"output.{output['name']}.scale.{output['scale']}"],env,timeout=5)
            except platform.PlatformError:
                display_error=True
        if desktop.exists() and b'Owned temporary LookUp platform experiment' not in desktop.read_bytes():
            raise RuntimeError('desktop_ownership_changed')
        if saved['desktop'] is None:
            desktop.unlink(missing_ok=True)
        else:
            desktop.write_bytes(base64.b64decode(saved['desktop']))
        platform.run(['kbuildsycoca6'],env,timeout=10)
        if saved['desktop'] is None:
            call('org.kde.kglobalaccel','/kglobalaccel','org.kde.KGlobalAccel','unregister',(spike.DESKTOP,'_launch'))
        time.sleep(.5)
        actual=json.loads(platform.run(['kscreen-doctor','-j'],env))['outputs']
        fields=[dict(name=o['name'],scale=o['scale'],pos=o['pos'],mode=o['currentModeId']) for o in actual if o['enabled']]
        shortcut_restored=bool(saved['desktop']) or call('org.kde.kglobalaccel','/kglobalaccel','org.kde.KGlobalAccel','isGlobalShortcutAvailable',(0x12000044,''))
        result=dict(display_restored=not display_error and fields==saved['outputs'],
                    desktop_restored=(desktop.read_bytes() if desktop.exists() else None)==(base64.b64decode(saved['desktop']) if saved['desktop'] else None),
                    processes_stopped=processes_stopped,shortcut_restored=shortcut_restored)
        if all(result.values()):
            snapshot.unlink()
        return result
    if action == 'setup':
        folder.mkdir(mode=0o700, exist_ok=True)
        if snapshot.exists():
            raise RuntimeError('unfinished_previous_run')
        if not isinstance(payload.get('run_id'),str) or not payload['run_id'].isalnum() or len(payload['run_id']) != 32:
            raise RuntimeError('invalid_run_id')
        for service in (spike.SERVICE,spike.FIXTURE):
            if call('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','NameHasOwner',(service,)):
                raise RuntimeError('preexisting_owner')
        unlocked=ensure_unlocked(env,lambda:call('org.freedesktop.ScreenSaver','/ScreenSaver','org.freedesktop.ScreenSaver','GetActive'),os.getuid())
        old = desktop.read_bytes() if desktop.exists() else None
        if old and b'Owned temporary LookUp platform experiment' not in old:
            raise RuntimeError('unowned_desktop')
        outputs = json.loads(platform.run(['kscreen-doctor','-j'],env))['outputs']
        available = call('org.kde.kglobalaccel','/kglobalaccel','org.kde.KGlobalAccel',
                         'isGlobalShortcutAvailable',(0x12000044,spike.DESKTOP))
        if not available:
            raise RuntimeError('unrelated_shortcut_conflict')
        saved=dict(run_id=payload['run_id'],outputs=[dict(name=o['name'],scale=o['scale'],pos=o['pos'],mode=o['currentModeId']) for o in outputs if o['enabled']],
                   desktop=base64.b64encode(old).decode() if old else None,processes=[])
        def save(pids):
            saved['processes']=[dict(pid=pid,start=Path('/proc',str(pid),'stat').read_text().split(') ',1)[1].split()[19]) for pid in pids]
            snapshot.write_text(json.dumps(saved))
        desktop.parent.mkdir(parents=True,exist_ok=True)
        fixture_pid,owner_pid=setup_owned(desktop,spike.desktop_text(sys.executable,Path('tools/vm_spike.py').resolve()),
                                        lambda:platform.run(['kbuildsycoca6'],env,timeout=10),start,save,restore)
        return dict(fixture_pid=fixture_pid, owner_pid=owner_pid,shortcut_available=available,normal_unlock_needed=unlocked)
    if action == 'status':
        value = status()
        if snapshot.exists():
            saved=json.loads(snapshot.read_text())
            if saved.get('run_id')==payload.get('run_id') and not any(p['pid']==value['pid'] for p in saved['processes']):
                saved['processes'].append(dict(pid=value['pid'],start=Path('/proc',str(value['pid']),'stat').read_text().split(') ',1)[1].split()[19]))
                snapshot.write_text(json.dumps(saved))
        value['active_uuid'] = platform.run(['kdotool','getactivewindow'],env,limit=4096).decode().strip()
        uuid = value['result'].get('popup_uuid')
        if uuid and value['popup_visible']:
            value['compositor_geometry'] = platform.window_geometry(env,value['pid'],uuid)
        return value
    if action == 'cursor':
        return platform.cursor_position(env)
    if action == 'fixture':
        value = status(True)
        uuids = platform.owned_window(env,value['pid'])
        # Fixture process owns only its public content window.
        platform.window_action(env,value['pid'],uuids[0],'windowactivate')
        time.sleep(.3)
        value = status(True)
        monitor = platform.monitor_at(value['fixture_point'],platform.monitors(env))
        value['scale'] = monitor.scale
        value['monitor'] = monitor.__dict__
        return value
    if action == 'scale':
        output = platform.monitors(env)[0]
        scale = payload['scale']
        if scale not in (1,1.25,1.5,2):
            raise RuntimeError('invalid_scale')
        platform.run(['kscreen-doctor',f'output.{output.name}.scale.{scale}'],env,timeout=5)
        time.sleep(1)
        return [o.__dict__ for o in platform.monitors(env)]
    if action == 'samples':
        point = status(True)['fixture_point']
        monitor = platform.monitor_at(point,platform.monitors(env))
        results=[]
        for _ in range(5):
            frame=capture.capture_monitor(monitor,env,payload['backend'])
            result=ocr.recognize_image(frame.png,platform.image_point(point,monitor,(frame.width,frame.height)))
            results.append(dict(capture_ms=frame.elapsed_ms,ocr_ms=result.timings['total'],word='english' if result.selection and result.selection.word=='english' else None))
        return results
    if action == 'quit-owner':
        call(spike.SERVICE,'/VMSpike',spike.INTERFACE,'Quit')
        time.sleep(.5)
        return True
    if action == 'conflict':
        # A different owned component must see our registered binding as occupied.
        return dict(other_available=call('org.kde.kglobalaccel','/kglobalaccel','org.kde.KGlobalAccel',
                                        'isGlobalShortcutAvailable',(0x12000044,'org.lookup.Linux.VMSpike.Conflict.desktop')))
    if action == 'primary':
        start_time=time.perf_counter()
        value=platform.read_primary(env)
        return dict(elapsed_ms=(time.perf_counter()-start_time)*1000,offered=value is not None)
    if action == 'finish':
        return restore()
    raise RuntimeError('unknown_action')


def remote(action,payload=None):
    encoded=base64.b64encode(json.dumps(payload or {}).encode()).decode()
    proc=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=5','archvm',
                         f'cd {REMOTE} && python3 tools/check_vm_spike.py --target {action} --payload {encoded}'],
                        capture_output=True,text=True,timeout=45)
    if proc.returncode:
        raise RuntimeError('target_'+action+': '+proc.stderr[-300:])
    return json.loads(proc.stdout)


def keys(codes):
    subprocess.run([VBOX,'controlvm','arch-kde','keyboardputscancode',*codes.split()],check=True,capture_output=True,timeout=5)


def pointer(x,y,buttons=0):
    # VirtualBox COM is the supported absolute pointer API absent from its CLI.
    x,y,buttons=round(x)+1,round(y)+1,int(buttons)
    code=("$v=New-Object -ComObject VirtualBox.VirtualBox; $s=New-Object -ComObject VirtualBox.Session; "
          "$v.FindMachine('arch-kde').LockMachine($s,1); try { "
          f"$s.Console.Mouse.PutMouseEventAbsolute({x+1},{y},0,0,{buttons}); "
          f"$s.Console.Mouse.PutMouseEventAbsolute({x},{y},0,0,{buttons})"
          " } finally { $s.UnlockMachine() }")
    subprocess.run(['powershell','-NoProfile','-Command',code],check=True,capture_output=True,timeout=10,
                   creationflags=subprocess.CREATE_NO_WINDOW)
    time.sleep(.15)  # VirtualBox queues guest input; COM return is not delivery proof.


def relative_pointer(dx,dy,buttons=0):
    code=("$v=New-Object -ComObject VirtualBox.VirtualBox; $s=New-Object -ComObject VirtualBox.Session; "
          "$v.FindMachine('arch-kde').LockMachine($s,1); try { "
          f"$s.Console.Mouse.PutMouseEvent({int(dx)},{int(dy)},0,0,{int(buttons)})"
          " } finally { $s.UnlockMachine() }")
    subprocess.run(['powershell','-NoProfile','-Command',code],check=True,capture_output=True,timeout=10,
                   creationflags=subprocess.CREATE_NO_WINDOW)
    time.sleep(.15)


def move_pointer(point,scale,request):
    pointer(point[0]*scale,point[1]*scale)
    try:
        wait_for(lambda:request('cursor'),lambda p:abs(p[0]-point[0])<=1 and abs(p[1]-point[1])<=1,1)
        return 'absolute'
    except GateTimeout:
        pass
    # After guest unlock, VBox's absolute device can ignore events; relative
    # hardware input still works. Correct its acceleration using observed points.
    for _ in range(16):
        actual=request('cursor')
        dx,dy=point[0]-actual[0],point[1]-actual[1]
        if abs(dx)<=1 and abs(dy)<=1:
            return 'relative_feedback'
        relative_pointer(max(-300,min(300,round(dx*scale))),max(-300,min(300,round(dy*scale))))
    raise GateTimeout(request('cursor'))


def host(output):
    evidence=dict(acceptance='agent',physical_input='VirtualBox keyboard scancodes and COM absolute mouse',scales=[],samples={},limits=['Only one VM output is exposed; negative origins use portable tests.'])
    run_id=uuid.uuid4().hex
    def request(action,payload=None):
        return remote(action,dict(payload or {},run_id=run_id))
    setup=False
    try:
        setup=True
        evidence['setup']=request('setup')
        time.sleep(1)
        evidence['conflict']=request('conflict')
        for backend in ('spectacle','screenshot2'):
            request('fixture');time.sleep(.3)
            evidence['samples'][backend]=request('samples',{'backend':backend})
        for scale in (1,1.25,1.5,2):
            evidence['stage']=f'scale_{scale}_cursor'
            request('scale',{'scale':scale})
            fixture=request('fixture');time.sleep(.3)
            point=fixture['fixture_point'];m=fixture['monitor']
            before=request('status')
            input_route=move_pointer(point,scale,request)
            keys('e0 5b 2a 20 a0 aa e0 db')
            evidence['stage']=f'scale_{scale}_popup'
            observed=wait_for(lambda:request('status'),lambda s:s['sequence']>before['sequence'] and not s['busy'] and s['popup_visible'] and s['popup_active']
                             and s['result'].get('focus_ready') and s['result'].get('popup_uuid')==s.get('active_uuid') and s.get('compositor_geometry')==s['result'].get('popup_target'))
            evidence['scales'].append(dict(scale=scale,fixture_point=point,input_route=input_route,observed=observed))
            if observed['result'].get('word')!='english' or observed['pid']!=before['pid']:
                raise RuntimeError('capture_or_owner_gate')
            keys('01 81')
            escaped=wait_for(lambda:request('status'),lambda s:'escape' in s['events'] and not s['popup_visible'])
            evidence['scales'][-1]['escape']=escaped['events']
        # Cold start through the same physical registered key.
        request('quit-owner');request('fixture')
        keys('e0 5b 2a 20 a0 aa e0 db')
        evidence['stage']='cold_start'
        cold=wait_for(lambda:request('status'),lambda s:not s['busy'] and s['sequence']==1 and s['popup_active']
                      and s['result'].get('focus_ready') and s['result'].get('popup_uuid')==s.get('active_uuid'))
        evidence['cold']=cold
        if cold['pid']==evidence['setup']['owner_pid']:
            raise RuntimeError('cold_owner_gate')
        request('fixture')
        evidence['stage']='focus_loss'
        evidence['deactivate']=wait_for(lambda:request('status'),lambda s:'deactivate' in s['events'] and not s['popup_visible'])
        evidence['primary']=request('primary')
        request('scale',{'scale':1})
        request('fixture')
        # Calibrated on this existing 1920x1080 VM panel; event proof detects drift.
        evidence['tray_input_route']=move_pointer((1630,1057),1,request)
        relative_pointer(0,0,2);relative_pointer(0,0,0)
        evidence['stage']='tray_menu'
        wait_for(lambda:request('status'),lambda s:'tray-menu' in s['events'])
        move_pointer((1680,986),1,request)
        relative_pointer(0,0,1);relative_pointer(0,0,0)
        evidence['tray']=wait_for(lambda:request('status'),lambda s:'tray-action' in s['events'])
        evidence['tray']['physical_icon_point']=[1630,1057]
        evidence['tray']['physical_action_point']=[1680,986]
        evidence['gates']={
            'SC1':all(s['observed']['pid']==evidence['setup']['owner_pid'] for s in evidence['scales']) and cold['pid']!=evidence['setup']['owner_pid'] and not evidence['conflict']['other_available'],
            'SC2':len(evidence['scales'])==4 and all(s['observed']['result']['word']=='english' for s in evidence['scales']),
            'SC3':all(s['observed']['compositor_geometry']==s['observed']['result']['popup_target'] and s['observed']['popup_active'] and 'escape' in s['escape'] for s in evidence['scales']) and 'deactivate' in evidence['deactivate']['events'] and 'tray-action' in evidence['tray']['events'],
            'SC4':evidence['primary']['elapsed_ms']<600 and all(s['observed']['result']['total_ms']>0 for s in evidence['scales'])}
        if not all(evidence['gates'].values()):
            raise RuntimeError('required_gate_failed')
        evidence['required_remaining']=[]
    except Exception as error:
        evidence['error']=str(error)
        if isinstance(error,GateTimeout):
            evidence['failed_observation']=error.last
    finally:
        try:keys('a0 aa e0 db 81')
        except Exception as error:evidence['key_release_error']=str(error)
        if setup:
            try:evidence['restoration']=request('finish')
            except Exception as error:evidence['restoration_error']=str(error)
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps({k:v for k,v in evidence.items() if k in ('error','restoration','restoration_error','required_remaining')}))
    return 0 if accepted(evidence) else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target')
    parser.add_argument('--payload',default='e30=')
    parser.add_argument('--output',type=Path,default=Path('/tmp/lookup-vm-spike-results/results.json'))
    args=parser.parse_args()
    if args.target:
        print(json.dumps(target(args.target,json.loads(base64.b64decode(args.payload)))))
        return 0
    if os.name!='nt':
        raise SystemExit('Run the host orchestrator on Windows; --target actions run inside Arch.')
    return host(args.output)


if __name__=='__main__':
    raise SystemExit(main())
