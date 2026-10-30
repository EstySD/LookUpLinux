"""Strict actual-game evidence and owned Wesnoth native observation."""
import time


def pilot_cleanup_steps(prior,record,info,run,guest,input_command):
    """Every safe cleanup action is attempted even if a preceding action fails."""
    clone='cf207909-94b5-4b49-8bd8-ccff973c1dc8';original='abc73254-ddf7-4f1f-9c66-7c2fcc5254d7'
    vbox='C:/Program Files/Oracle/VirtualBox/VBoxManage.exe'
    def attempt(name,operation):
        try:record[name]=dict(ok=True,result=operation())
        except BaseException as error:record[name]=dict(ok=False,error=repr(error))
        return record[name]
    observed=attempt('identity',lambda:info(clone))
    current=observed.get('result',{})
    owned=current.get('UUID')=='"'+clone+'"' and current.get('"SATA-ImageUUID-0-0"')=='"2712d710-daaa-449c-843d-d570091127bc"'
    if owned and current.get('VMState')=='"running"':
        attempt('release',lambda:input_command('Keys',Codes='8f 81 91 9f 9e a0 aa b6 e0 db e0 dc'))
        attempt('mouse_release',lambda:input_command('Pointer',X=640,Y=400,Buttons=0))
        attempt('guest_cleanup',lambda:guest('sudo -n python /home/arch/lookup-games-08-pilot-cleanup.py'))
        attempt('shutdown',lambda:guest('sudo -n systemctl poweroff'))
        deadline=time.monotonic()+45
        while time.monotonic()<deadline:
            observed=attempt('power_poll',lambda:info(clone))
            if observed.get('result',{}).get('VMState')=='"poweroff"':break
            time.sleep(1)
    if owned:
        observed=attempt('power_before_restore',lambda:info(clone));off=observed.get('result',{}).get('VMState')=='"poweroff"'
        if not off:
            attempt('forced_stop',lambda:run(vbox,'controlvm',clone,'poweroff'))
            observed=attempt('power_after_forced_stop',lambda:info(clone));off=observed.get('result',{}).get('VMState')=='"poweroff"'
        if off:
            attempt('restore',lambda:run(vbox,'modifyvm',clone,'--clipboard-mode',prior['clipboard'].strip('"'),
                '--accelerate-3d',prior['accelerate3d'].strip('"')))
    final=attempt('final_clone',lambda:info(clone)).get('result',{})
    record['clone_off']=owned and final.get('VMState')=='"poweroff"'
    record['settings_restored']=owned and all(final.get(key)==prior.get(key) for key in ('clipboard','accelerate3d'))
    final_original=attempt('final_original',lambda:info(original)).get('result',{})
    record['original_off']=final_original.get('VMState')=='"poweroff"'
    return record


def pilot_session():
    """Bounded owned-clone lifetime; every exit runs observed failure cleanup."""
    import json,subprocess
    from pathlib import Path
    from tools.check_hardening import write_record,vm_input
    clone='cf207909-94b5-4b49-8bd8-ccff973c1dc8';original='abc73254-ddf7-4f1f-9c66-7c2fcc5254d7'
    vbox='C:/Program Files/Oracle/VirtualBox/VBoxManage.exe'
    root=Path('.planning/phases/08-vm');state=root/'08-06-pilot-session.json'
    stop=root/'08-06-pilot-stop.json';cleanup=root/'08-06-cleanup-final.json'
    _require(not stop.exists(),'existing_pilot_stop')
    def run(*args):
        result=subprocess.run(args,capture_output=True,text=True,timeout=30)
        return dict(exit=result.returncode,stdout=result.stdout,stderr=result.stderr)
    def info(identity):
        result=run(vbox,'showvminfo',identity,'--machinereadable');_require(result['exit']==0,'vm_info')
        return dict(line.split('=',1) for line in result['stdout'].splitlines() if '=' in line)
    prior=info(clone)
    _require(prior.get('UUID')=='"'+clone+'"' and prior.get('VMState')=='"poweroff"' and
        prior.get('"SATA-ImageUUID-0-0"')=='"2712d710-daaa-449c-843d-d570091127bc"' and
        info(original).get('VMState')=='"poweroff"','pilot_vm_baseline')
    record=dict(prior=prior,commands=[],passed=False)
    write_record(state,dict(state='prepared',prior=prior,controller_pid=__import__('os').getpid()))
    try:
        changed=run(vbox,'modifyvm',clone,'--clipboard-mode','disabled','--accelerate-3d','off')
        record['commands'].append(dict(action='isolate',**changed));_require(changed['exit']==0,'pilot_isolation')
        started=run(vbox,'startvm',clone,'--type','headless');record['commands'].append(dict(action='boot',**started))
        _require(started['exit']==0,'pilot_boot')
        write_record(state,dict(state='running',prior=prior,controller_pid=__import__('os').getpid()))
        deadline=time.monotonic()+5400
        while time.monotonic()<deadline:
            if stop.exists():
                record['stop']=json.loads(stop.read_text());break
            time.sleep(1)
        else:record['error']='pilot_deadline'
    except BaseException as error:record['error']=type(error).__name__
    finally:
        from tools.check_hardening_install import ssh
        pilot_cleanup_steps(prior,record,info,run,ssh,vm_input)
        write_record(cleanup,record);write_record(state,dict(state='finished',cleanup=str(cleanup)))

# Test-only transparent SDL observation: original call exactly once, same return.
SDL_OBSERVER = r'''
#define _GNU_SOURCE
#include <SDL.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <time.h>
#include <unistd.h>
SDL_Renderer *SDL_CreateRenderer(SDL_Window *window, int index, Uint32 flags) {
    SDL_Renderer *(*original)(SDL_Window*,int,Uint32)=dlsym(RTLD_NEXT,"SDL_CreateRenderer");
    SDL_Renderer *result=original(window,index,flags); int saved=errno;
    const char *path=getenv("LOOKUP_GAME_SDL_LOG");
    if (result && path) { SDL_RendererInfo info; struct timespec stamp;
        if (!SDL_GetRendererInfo(result,&info) && !clock_gettime(CLOCK_MONOTONIC,&stamp)) {
            FILE *output=fopen(path,"a"); if(output) {
                fprintf(output,"{\"pid\":%d,\"at_ns\":%lld,\"renderer\":\"%s\",\"flags\":%u,\"driver\":\"%s\"}\n",
                    getpid(),(long long)stamp.tv_sec*1000000000+stamp.tv_nsec,info.name,info.flags,SDL_GetCurrentVideoDriver());
                fclose(output);
            }
        }
    }
    errno=saved; return result;
}
int SDL_SetRelativeMouseMode(SDL_bool enabled) {
    int (*original)(SDL_bool)=dlsym(RTLD_NEXT,"SDL_SetRelativeMouseMode");
    int result=original(enabled);int saved=errno;
    const char *path=getenv("LOOKUP_GAME_SDL_LOG");
    struct timespec stamp;
    if(path && !clock_gettime(CLOCK_MONOTONIC,&stamp)) {
        FILE *output=fopen(path,"a");if(output) {
            fprintf(output,"{\"pid\":%d,\"at_ns\":%lld,\"operation\":\"relative\",\"requested\":%d,\"result\":%d,\"state\":%d,\"driver\":\"%s\"}\n",
                getpid(),(long long)stamp.tv_sec*1000000000+stamp.tv_nsec,enabled,result,SDL_GetRelativeMouseMode(),SDL_GetCurrentVideoDriver());
            fclose(output);
        }
    }
    errno=saved;return result;
}
void SDL_SetWindowGrab(SDL_Window *window,SDL_bool enabled) {
    void (*original)(SDL_Window*,SDL_bool)=dlsym(RTLD_NEXT,"SDL_SetWindowGrab");
    original(window,enabled);int saved=errno;
    const char *path=getenv("LOOKUP_GAME_SDL_LOG");struct timespec stamp;
    if(path && !clock_gettime(CLOCK_MONOTONIC,&stamp)) {
        FILE *output=fopen(path,"a");if(output) {
            fprintf(output,"{\"pid\":%d,\"at_ns\":%lld,\"operation\":\"grab\",\"requested\":%d,\"state\":%d,\"window\":%u,\"driver\":\"%s\"}\n",
                getpid(),(long long)stamp.tv_sec*1000000000+stamp.tv_nsec,enabled,SDL_GetWindowGrab(window),SDL_GetWindowID(window),SDL_GetCurrentVideoDriver());
            fclose(output);
        }
    }
    errno=saved;
}
'''

try:
    from tools.check_hardening import EvidenceError,physical_latency,_require,_hash,_integer
except ModuleNotFoundError:
    from check_hardening import EvidenceError,physical_latency,_require,_hash,_integer


def tap(original,observer,on_error=lambda unused:None):
    """Observe original returned objects without changing payload or error behavior."""
    def wrapped(*args,**kwargs):
        start=time.monotonic_ns();result=original(*args,**kwargs);end=time.monotonic_ns()
        try:observer(result,start,end)
        except Exception as error:
            try:on_error(type(error).__name__)
            except Exception:pass  # Failed evidence cannot change the production operation.
        return result
    return wrapped


def captured_game_report(data):
    return game_report(data,_captured=True)


def assaultcube_grab(grab,process,input_ns):
    """Bind the pre-input observation to actual SDL state and Wayland events."""
    import hashlib,json,re
    rows=grab['sdl'];events=grab['events']
    _require(grab.get('driver')=='wayland' and isinstance(rows,list) and rows and events,'assaultcube_driver')
    _require(all(row.get('pid')==process['pid'] and _integer(row.get('at_ns'),1) and row['at_ns']<=input_ns for row in rows+events),'runtime_identity')
    relative=sorted((row for row in rows if row.get('operation')=='relative'),key=lambda row:row['at_ns'])
    _require(relative and relative[-1].get('requested')==1 and relative[-1].get('result')==0 and
        relative[-1].get('state')==1 and relative[-1].get('driver')=='wayland','sdl_relative_state')
    _require(hashlib.sha256(json.dumps(events).encode()).hexdigest()==grab.get('events_sha256'),'protocol_digest')
    states=sorted((row for row in events if re.search(r'\.(?:locked|unlocked|destroy)\(',row.get('message',''))),key=lambda row:row['at_ns'])
    _require(states and '.locked()' in states[-1]['message'] and states[-1]['at_ns']==grab.get('lock_event_ns'),'protocol_locked_at_input')


def game_report(data,*,_captured=False):
    from lookup.normalize import normalize
    try:
        assaultcube=_captured and data.get('name')=='AssaultCube'
        expected=('AssaultCube' if assaultcube else 'Freedoom Phase 2') if _captured else 'The Battle for Wesnoth'
        _require(data.get('name')==expected and isinstance(data.get('version'),str) and data['version'],'game')
        process=data['process'];renderer=data['renderer'];window=data['window']
        if assaultcube:
            import hashlib
            acquisition=data['acquisition']
            _require(data.get('engine')=='AssaultCube' and data.get('engine_version')=='1.3.0.2' and data.get('version')=='1.3.0.2'
                and acquisition.get('url')=='https://github.com/assaultcube/AC/releases/download/v1.3.0.2/AssaultCube_v1.3.0.2_LockdownEdition_RC1.tar.bz2'
                and acquisition.get('bytes')==52071427 and acquisition.get('sha256')=='9b3118e7929253f0114fa06cad8310faab646d177b4660406011152f34086b55'
                and acquisition.get('release_asset')=='RC1','assaultcube_provenance')
            executable='/home/lookup07/.local/state/lookup-games-08/assaultcube/package/bin_unix/linux_64_client'
            text=renderer.get('text')
            _require(isinstance(text,str) and 'Renderer: '+renderer.get('name','') in text and '\nDriver: ' in text
                and renderer.get('kind')=='game_gl_log' and renderer.get('pid')==process.get('pid') and renderer.get('start')==process.get('start')
                and hashlib.sha256(text.encode()).hexdigest()==renderer.get('log_sha256'),'actual_game_gl_log')
        elif _captured:
            acquisition=data['acquisition']
            _require(data.get('source_verified') is True and data.get('engine')=='Chocolate Doom' and data.get('engine_version')=='3.1.1'
                and acquisition.get('source_url')=='https://api.github.com/repos/chocolate-doom/chocolate-doom/tarball/chocolate-doom-3.1.1'
                and acquisition.get('assets_url')=='https://github.com/freedoom/freedoom/releases/download/v0.13.0/freedoom-0.13.0.zip'
                and all(_hash(acquisition.get(key)) for key in ('source_sha256','assets_sha256','wad_sha256'))
                and acquisition.get('checksum_status') in ('verified','not_published')
                and (acquisition.get('checksum_status')!='not_published' or acquisition.get('checksum_absence_evidence')),'provenance')
            executable='/home/lookup07/.local/state/lookup-games-08/doom/chocolate-doom'
        else:
            package=data['package'];executable='/usr/bin/wesnoth'
            _require(data.get('source_verified') is True and package.get('source')=='official_arch' and
            package.get('name')=='wesnoth' and package.get('repository')=='extra' and package.get('signature_verified') is True
            and _hash(package.get('archive_sha256')) and isinstance(package.get('version'),str),'package')
        _require(_integer(process.get('pid'),1) and _integer(process.get('start'),1) and process.get('uid')==1001
            and process.get('executable')==executable,'process')
        _require(isinstance(renderer.get('name'),str) and renderer['name'] and renderer.get('observed') is True
            and _hash(renderer.get('log_sha256')),'renderer')
        _require(data.get('mode')=='fullscreen' and window.get('fullscreen') is True and window.get('observed') is True
            and window.get('pid')==process['pid'] and window.get('id') and window.get('rect')==window.get('screen'),'fullscreen')
        rows=data['routes'];_require(isinstance(rows,list) and len(rows)>=2,'routes')
        hashes=set();contexts=set();latencies=[];requests=set();inputs=set();multiline=False
        control_inputs=set();control_frames=set()
        for index,row in enumerate(rows,1):
            source=row['source'];overlay=row['overlay'];closed=row['dismissal'];play=row['gameplay'];timing=row['timing']
            latency=physical_latency(timing)
            request_identity=tuple(timing['frame_identity'])
            _require(request_identity not in requests and timing['input_ns'] not in inputs and
                row.get('sequence')==timing.get('input_sequence')==timing.get('attempt'),'unique_route_input')
            requests.add(request_identity);inputs.add(timing['input_ns'])
            scene='local_map_scoreboard' if assaultcube else 'map01_captured_prompt' if _captured else 'tutorial_map_dialogue'
            _require(row.get('sequence')==index and row.get('scene')==scene and
                row.get('game_pid')==process['pid'] and row.get('game_start')==process['start'] and
                row.get('window_id')==window['id'] and row.get('game_active_before') is True,'game_source')
            _require(source.get('kind')=='actual_game' and source.get('mode')=='ocr' and source.get('backend')=='screenshot2'
                and _hash(source.get('sha256')) and source.get('unchanged_objects') is True,'source')
            _require(all(source.get(key)==timing[key] for key in ('pid','run','request')),'source_request_identity')
            _require(timing['trigger_ns']<=source['capture_start_ns']<=source['capture_end_ns']<=timing['first_visible_end_ns'],'fresh_source')
            _require(isinstance(source.get('word'),str) and source['word'] and source.get('query')==source['word']
                and isinstance(source.get('context'),str) and source['word'].casefold() in source['context'].casefold()
                and _integer(source.get('visual_lines'),1),'ocr')
            _require(source['visual_lines']==len(source['context'].splitlines()),'context_lines')
            multiline|=source['visual_lines']>=2
            span=source['span'];query_key=normalize(source['query']);_require(query_key and len(span)==2 and all(type(value) is int for value in span) and
                0<=span[0]<span[1]<=len(source['context']) and normalize(source['context'][span[0]:span[1]])==query_key,'context_span')
            x,y=source['cursor'];left,top,width,height=source['word_rect']
            _require(width>0 and height>0 and left<=x<=left+width and top<=y<=top+height,'target')
            _require(overlay.get('useful') is True and overlay.get('loading') is False and overlay.get('error') is False
                and overlay.get('current_word')==source['word'] and overlay.get('sha256')==timing['frame_sha256']
                and overlay.get('identity')==timing['frame_identity'],'overlay')
            _require(closed.get('physical') is True and closed.get('released') is True and closed.get('closed') is True
                and closed['at_ns']>=timing['first_visible_end_ns'],'dismiss')
            _require(play.get('physical') is True and play.get('game_active') is True and play.get('game_pid')==process['pid']
                and play.get('game_start')==process['start'] and isinstance(play.get('action'),str) and play['action']
                and play['input_ns']>=closed['at_ns'] and play.get('observed_change') is True
                and _hash(play.get('before_sha256')) and _hash(play.get('after_sha256'))
                and play['before_sha256']!=play['after_sha256'],'resumed_gameplay')
            if _captured:
                grab=row['grab'];camera=play['camera'];movement=play['movement']
                if assaultcube:assaultcube_grab(grab,process,timing['input_ns'])
                _require(grab.get('relative') is True and grab.get('observed') is True and grab.get('pid')==process['pid']
                    and grab.get('start')==process['start'] and grab.get('at_ns')<=timing['input_ns']
                    and timing['input_ns']-grab['at_ns']<=2_000_000_000 and grab.get('protocol')=='zwp_locked_pointer_v1'
                    and _hash(grab.get('events_sha256')) and grab.get('lock_event_ns',timing['input_ns']+1)<=grab['at_ns'],'actual_relative_grab')
                for change in (camera,movement):
                    _require(change.get('physical') is True and change.get('game_active') is True
                        and change.get('game_pid')==process['pid'] and change.get('game_start')==process['start']
                        and _integer(change.get('input_ns'),1) and change['input_ns']>=closed['at_ns'] and _hash(change.get('before_sha256'))
                        and _hash(change.get('after_sha256')) and change['before_sha256']!=change['after_sha256'],'relative_control')
                    identity=(change['game_pid'],change['game_start'],change['input_ns'])
                    frames=(change['before_sha256'],change['after_sha256'])
                    _require(identity not in control_inputs and frames not in control_frames,'reused_relative_control')
                    control_inputs.add(identity);control_frames.add(frames)
                _require(camera.get('kind')=='relative_pointer' and movement.get('kind')=='movement_key','relative_control_kind')
            hashes.add(source['sha256']);contexts.add(source['context']);latencies.append(latency)
        _require(len(hashes)>=2 and (_captured or len(contexts)>=2 and multiline),'changed_scenes')
        return dict(passed=True,game01_complete=False,routes=len(rows),latencies_ms=latencies)
    except EvidenceError as error:return dict(passed=False,game01_complete=False,reason=str(error))
    except (KeyError,TypeError,ValueError,AttributeError) as error:return dict(passed=False,game01_complete=False,reason=type(error).__name__)


def request_error(rows,trigger,input_ns):
    return next((row for row in rows if row.get('stage')==6 and row.get('mono_ns',0)>=input_ns and
        all(row.get(key)==trigger.get(key) for key in ('pid','run','request'))),None)


def guest_command(encoded):
    import base64,hashlib,json,os,subprocess,sys
    from pathlib import Path
    _require(os.getuid()==1001 and Path.home()==Path('/home/lookup07'),'unowned_account')
    sys.path.insert(0,'/usr/lib/lookup/app')
    from lookup import capture,platform
    command=json.loads(base64.b64decode(encoded));action=command['action'];kind=command.get('game_kind','wesnoth')
    _require(kind in ('wesnoth','doom','assaultcube'),'game_kind')
    root=Path.home()/'.local/state/lookup-games-08'/kind;root.mkdir(parents=True,exist_ok=True)
    env=platform.session_env()
    env.update(XDG_CONFIG_HOME=str(root/'xdg-config'),XDG_CACHE_HOME=str(root/'xdg-cache'),XDG_DATA_HOME=str(root/'xdg-data'))
    for key in ('SUDO_UID','SUDO_GID','SUDO_USER','SUDO_COMMAND','PYTHONPATH'):env.pop(key,None);os.environ.pop(key,None)
    os.environ.update(env)
    from PyQt6.QtCore import QCoreApplication
    from PyQt6.QtDBus import QDBus,QDBusConnection,QDBusMessage
    application=QCoreApplication([]);bus=QDBusConnection.sessionBus()
    metadata=root/'game-process.json'
    if action=='pilot-package-receipt':
        _require(kind=='assaultcube' and command.get('package_sha256')=='7aa3cf123457c753fa572efbd58062f81cd1e4f4fc2387fe4a7505665ab480f3','pilot_package')
        (root/'package-reinstalled.json').write_text(json.dumps(dict(baseline_absent=True,package_sha256=command['package_sha256'],
            absence_observation='pre-install SSH pacman -Q lookup-linux: package not found')))
        paths=[path for base in (Path.home()/'.config/lookup',Path.home()/'.local/share/lookup') if base.exists() for path in base.rglob('*') if path.is_file()]
        hashes={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
        (root/'retention-before.json').write_text(json.dumps(hashes));return dict(retained_hashes=hashes)
    def process():
        value=json.loads(metadata.read_text());path=Path('/proc',str(value['pid']))
        _require(value.get('boot_id')==Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'game_boot_identity')
        fields=(path/'stat').read_text().split(') ',1)[1].split()
        _require(path.stat().st_uid==1001 and int(fields[19])==value['start'] and fields[0]!='Z','game_identity')
        owned_argument=str(root/('userdata' if kind=='wesnoth' else 'main.cfg'))
        if kind=='assaultcube':owned_argument='--home='+str(root/'profile')
        _require(os.fsencode(owned_argument) in path.joinpath('cmdline').read_bytes().split(b'\0'),'unowned_game_profile')
        return value
    def windows():
        value=process();ids=platform.run(['kdotool','search','--pid',str(value['pid'])],env).decode().split();result=[]
        for window in ids:
            message=QDBusMessage.createMethodCall('org.kde.KWin','/KWin','org.kde.KWin','getWindowInfo');message.setArguments([window])
            reply=bus.call(message,QDBus.CallMode.Block,1200)
            if reply.type()==QDBusMessage.MessageType.ErrorMessage:continue
            info=reply.arguments()[0] if reply.arguments() else {}
            if info.get('pid')==value['pid']:result.append(dict(id=window,info=info))
        return result
    if action=='launch':
        _require(not metadata.exists(),'existing_game_metadata')
        argv=['/usr/bin/wesnoth','--fullscreen','--language','en_US','--userdata-dir',str(root/'userdata'),
            '--usercache-dir',str(root/'cache'),'--userconfig-dir',str(root/'config'),'--nomusic','--nosound','--noaddons',
            '--log-info=display']
        if command.get('software'):env['SDL_RENDER_DRIVER']='software'
        if kind=='doom':
            (root/'saves').mkdir(exist_ok=True)
            settings='force_software_renderer 1\nfullscreen 1\nfullscreen_width 1280\nfullscreen_height 800\n'
            if command.get('integer_pixels'):settings+='aspect_ratio_correct 0\nsmooth_pixel_scaling 0\ninteger_scaling 1\n'
            (root/'extra.cfg').write_text(settings)
            argv=[str(root/'chocolate-doom'),'-iwad',str(root/'freedoom2.wad'),'-config',str(root/'main.cfg'),
                '-extraconfig',str(root/'extra.cfg'),'-savedir',str(root/'saves'),'-warp','1','-nomonsters','-nosound','-fullscreen']
            env.update(WAYLAND_DEBUG='1',LD_PRELOAD=str(root/'sdl-observer.so'),LOOKUP_GAME_SDL_LOG=str(root/'sdl-observer.jsonl'),SDL_RENDER_SCALE_QUALITY='nearest')
        if kind=='assaultcube':
            argv=[str(root/'package/bin_unix/linux_64_client'),'--home='+str(root/'profile'),'--init','-t1',
                '-w'+str(command.get('width',1280)),'-h'+str(command.get('height',800)),'--loadmap=ac_desert']
            env.update(SDL_VIDEODRIVER='wayland',LIBGL_ALWAYS_SOFTWARE='true',WAYLAND_DEBUG='1',
                LD_PRELOAD=str(root/'sdl-observer.so'),LOOKUP_GAME_SDL_LOG=str(root/'sdl-observer.jsonl'))
        unit='lookup-'+kind+'-08-'+str(time.monotonic_ns())
        launch=['systemd-run','--user','--unit='+unit,'--service-type=exec','--property=WorkingDirectory='+str(root/'package' if kind=='assaultcube' else root),
            '--property=TimeoutStopSec=5','--property=RuntimeMaxSec=3600']
        launch+=['--setenv='+key+'='+env[key] for key in ('WAYLAND_DISPLAY','XDG_RUNTIME_DIR','DBUS_SESSION_BUS_ADDRESS',
            'XDG_CONFIG_HOME','XDG_CACHE_HOME','XDG_DATA_HOME','SDL_RENDER_DRIVER','WAYLAND_DEBUG','LD_PRELOAD','LOOKUP_GAME_SDL_LOG','SDL_RENDER_SCALE_QUALITY',
            'SDL_VIDEODRIVER','LIBGL_ALWAYS_SOFTWARE') if key in env]
        subprocess.run([*launch,*argv],env=env,capture_output=True,timeout=8,check=True)
        pid=int(subprocess.run(['systemctl','--user','show',unit,'--property=MainPID','--value'],env=env,capture_output=True,text=True,timeout=3,check=True).stdout)
        _require(pid>0,'game_service_not_running');path=Path('/proc',str(pid));value=dict(pid=pid,start=int((path/'stat').read_text().split(') ',1)[1].split()[19]),
            uid=1001,executable=argv[0],argv=argv,renderer_requested=env.get('SDL_RENDER_DRIVER','default'),unit=unit,
            boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
        value['control_group']=subprocess.run(['systemctl','--user','show',unit,'--property=ControlGroup','--value'],env=env,capture_output=True,text=True,timeout=3,check=True).stdout.strip()
        metadata.write_text(json.dumps(value));return value
    if action=='prepare-doom-observer':
        _require(kind in ('doom','assaultcube'),'game_kind');source=root/'sdl-observer.c';source.write_text(SDL_OBSERVER)
        subprocess.run(['cc','-shared','-fPIC','-I/usr/include/SDL2',str(source),'-o',str(root/'sdl-observer.so'),'-ldl','-lSDL2'],
            env=env,capture_output=True,timeout=15,check=True)
        return dict(observer='transparent original SDL_CreateRenderer return',sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    if action=='doom-map':
        import struct
        _require(kind=='doom','game_kind');data=(root/'freedoom2.wad').read_bytes();magic,count,offset=struct.unpack_from('<4sii',data)
        _require(magic==b'IWAD','not_iwad')
        entries=[struct.unpack_from('<ii8s',data,offset+16*index) for index in range(count)]
        start=next(index for index,entry in enumerate(entries) if entry[2].rstrip(b'\0')==b'MAP01')
        lumps={name.rstrip(b'\0').decode():data[position:position+size] for position,size,name in entries[start+1:start+11]}
        vertices=list(struct.iter_unpack('<hh',lumps['VERTEXES']));sides=lumps['SIDEDEFS'];exits=[]
        for line in struct.iter_unpack('<7H',lumps['LINEDEFS']):
            for side in line[-2:]:
                if side==65535:continue
                textures=[sides[side*30+item:side*30+item+8].rstrip(b'\0').decode() for item in (4,12,20)]
                if any('EXIT' in name for name in textures):exits.append(dict(vertices=[vertices[line[0]],vertices[line[1]]],textures=textures,special=line[3]))
        return dict(wad_sha256=hashlib.sha256(data).hexdigest(),map='MAP01',player_starts=[item for item in struct.iter_unpack('<5h',lumps['THINGS']) if item[3]==1],exit_lines=exits)
    if action=='doom-runtime-evidence':
        import re
        _require(kind in ('doom','assaultcube'),'game_kind');value=process()
        output=subprocess.run(['journalctl','--user','-u',value['unit'],'--no-pager','-o','json','--grep=zwp_locked_pointer_v1','-n','256'],
            env=env,capture_output=True,text=True,timeout=5,check=True).stdout
        events=sorted((dict(at_ns=int(row['__MONOTONIC_TIMESTAMP'])*1000,message=row['MESSAGE'],pid=int(row['_PID']))
            for row in (json.loads(line) for line in output.splitlines()) if int(row['_PID'])==value['pid']),key=lambda row:row['at_ns'])
        changes=[row for row in events if re.search(r'\.(?:locked|unlocked|destroy)\(',row['message'])]
        last=changes[-1] if changes else None;at=time.monotonic_ns();digest=hashlib.sha256(json.dumps(events).encode()).hexdigest()
        grab=dict(pid=value['pid'],start=value['start'],at_ns=at,observed=bool(last),relative=bool(last and '.locked()' in last['message']),
            protocol='zwp_locked_pointer_v1',events_sha256=digest,lock_event_ns=last['at_ns'] if last else None)
        renderers=[json.loads(line) for line in (root/'sdl-observer.jsonl').read_text().splitlines()]
        return dict(process=value,grab=grab,events=events,renderer=[row for row in renderers if row['pid']==value['pid']],windows=windows())
    if action=='archive-dead':
        value=json.loads(metadata.read_text());old=Path('/proc',str(value['pid']))
        if old.exists():
            fields=(old/'stat').read_text().split(') ',1)[1].split()
            _require(old.stat().st_uid==1001 and int(fields[19])==value['start'] and fields[0]=='Z','game_still_exists')
            value.update(exit_status=int(fields[49]),process_state='zombie');metadata.write_text(json.dumps(value))
        suffix=str(time.monotonic_ns());metadata.rename(root/('rejected-process-'+suffix+'.json'))
        if (root/'wesnoth.log').exists():(root/'wesnoth.log').rename(root/('rejected-launch-'+suffix+'.log'))
        return dict(archived=True,pid=value['pid'])
    if action=='stop':
        import signal
        value=process()
        if value.get('unit'):
            unit=value['unit'];prefix='lookup-'+kind+'-08-';_require(unit.startswith(prefix) and unit.removeprefix(prefix).isdigit(),'unowned_game_unit')
            pid=int(subprocess.run(['systemctl','--user','show',unit,'--property=MainPID','--value'],env=env,capture_output=True,text=True,timeout=3,check=True).stdout)
            _require(pid==value['pid'],'game_unit_identity')
            subprocess.run(['systemctl','--user','stop',unit],env=env,capture_output=True,timeout=8,check=True)
            pid=int(subprocess.run(['systemctl','--user','show',unit,'--property=MainPID','--value'],env=env,capture_output=True,text=True,timeout=3,check=True).stdout)
            _require(pid==0,'game_unit_still_running');return dict(stopped=True,pid=value['pid'],unit=unit,method='owned user-service stop')
        _require(os.getsid(value['pid'])==value['pid'],'unowned_game_session')
        os.killpg(value['pid'],signal.SIGTERM);deadline=time.monotonic()+6
        while time.monotonic()<deadline:
            if not Path('/proc',str(value['pid'])).exists():return dict(stopped=True,pid=value['pid'])
            time.sleep(.05)
        raise TimeoutError('game_stop_deadline')
    if action=='drivers':
        import ctypes
        class Info(ctypes.Structure):
            _fields_=[('name',ctypes.c_char_p),('flags',ctypes.c_uint32),('count',ctypes.c_uint32),
                ('formats',ctypes.c_uint32*16),('max_width',ctypes.c_int),('max_height',ctypes.c_int)]
        library=ctypes.CDLL('libSDL2-2.0.so.0');result=[]
        for index in range(library.SDL_GetNumRenderDrivers()):
            info=Info();_require(library.SDL_GetRenderDriverInfo(index,ctypes.byref(info))==0,'driver_query')
            result.append(dict(name=info.name.decode(),flags=info.flags))
        return result
    if action=='keyboard':
        matches=[path.name for path in Path('/sys/class/input').glob('event*') if path.joinpath('device/name').read_text().strip()=='AT Translated Set 2 keyboard']
        _require(len(matches)==1,'keyboard_identity');return dict(device='/dev/input/'+matches[0],name='AT Translated Set 2 keyboard')
    if action=='renderer-report':
        process()
        value=subprocess.run(['wl-paste','--no-newline'],env=env,capture_output=True,timeout=3,check=True).stdout.decode()
        _require(len(value)<65536 and 'Wesnoth' in value and 'Renderer' in value,'not_game_report')
        (root/'copied-report.txt').write_text(value)
        return dict(text=value,source='actual in-game copy_all report',pid=process()['pid'])
    if action=='clear-owned-primary':
        value=subprocess.run(['wl-paste','--primary','--no-newline'],env=env,capture_output=True,timeout=3)
        if value.returncode==1:return dict(absent=True,changed=False)
        report=root/'copied-report.txt'
        known=[b'Public hardening clipboard fixture 08',b'Public hardening primary fixture 08']
        if report.exists():known.append(report.read_bytes())
        _require(value.returncode==0 and value.stdout in known,'unknown_primary_not_cleared')
        subprocess.run(['wl-copy','--primary','--clear'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=3,check=True)
        return dict(absent=True,changed=True,history_cleared=False)
    if action=='restore-owned-clipboard':
        previous=b'Public hardening clipboard fixture 08';report=root/'copied-report.txt'
        value=subprocess.run(['wl-paste','--no-newline'],env=env,capture_output=True,timeout=3,check=True).stdout
        _require(report.exists() and value in (report.read_bytes(),previous),'unknown_clipboard_not_overwritten')
        subprocess.run(['wl-copy'],input=previous,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=3,check=True)
        return dict(restored_known_public_fixture=True,history_cleared=False)
    if action=='stop-lookup':
        interface=bus.interface();present=interface.isServiceRegistered('org.lookup.Linux')
        if not present.isValid() or not present.value():return dict(stopped=True,already_absent=True)
        pid=interface.servicePid('org.lookup.Linux').value();path=Path('/proc',str(pid));argv=path.joinpath('cmdline').read_bytes().split(b'\0')
        _require(path.stat().st_uid==1001 and (b'/usr/bin/lookup' in argv or b'/home/lookup07/check_games.py' in argv),'unowned_lookup')
        items=subprocess.run(['qdbus6','org.kde.StatusNotifierWatcher','/StatusNotifierWatcher','org.kde.StatusNotifierWatcher.RegisteredStatusNotifierItems'],env=env,capture_output=True,text=True,check=True,timeout=3).stdout.split()
        for item in items:
            service=item.split('/StatusNotifierItem')[0]
            if interface.servicePid(service).value()==pid:
                subprocess.run(['qdbus6',service,'/MenuBar','com.canonical.dbusmenu.Event','5','clicked','0','0'],env=env,capture_output=True,timeout=3,check=True)
        deadline=time.monotonic()+6
        while time.monotonic()<deadline:
            if not interface.isServiceRegistered('org.lookup.Linux').value():return dict(stopped=True,pid=pid)
            time.sleep(.05)
        raise TimeoutError('lookup_tray_exit')
    if action=='launch-lookup':
        _require(not bus.interface().isServiceRegistered('org.lookup.Linux').value(),'existing_lookup')
        profile=root/'lookup';(profile/'data').mkdir(parents=True,exist_ok=True)
        (profile/'config.json').write_text(json.dumps(dict(online=False,autostart=False,shortcut='Meta+Shift+E',popup_timeout=60)))
        child_env=dict(env,LOOKUP_GAME_KIND=kind,LOOKUP_TIMING='1',LOOKUP_CONFIG=str(profile/'config.json'),LOOKUP_DB=str(profile/'data/history.db'),LOOKUP_CACHE=str(profile/'cache'),LOOKUP_DICTS='/usr/share/lookup/dicts')
        if (profile/'daemon.log').exists():(profile/'daemon.log').rename(profile/('daemon-previous-'+str(time.time_ns())+'.log'))
        with (profile/'daemon.log').open('w') as output:
            child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--app-observer'],env=child_env,cwd=root,
                stdin=subprocess.DEVNULL,stdout=output,stderr=output,start_new_session=True)
        return dict(pid=child.pid,profile=str(profile),instrumentation='read-only Source.freeze/resolve taps; original returned objects unchanged')
    if action=='start-route':
        value=command['route'];value['game']=process();value['game_kind']=kind
        token=str(time.monotonic_ns());value['token']=token
        payload=base64.b64encode(json.dumps(value).encode()).decode()
        with (root/('observer-'+token+'.log')).open('w') as output:
            child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--observe-route',payload],env=env,cwd=root,
                stdin=subprocess.DEVNULL,stdout=output,stderr=output,start_new_session=True)
        return dict(pid=child.pid,token=token)
    if action=='start-control':
        _require(kind=='assaultcube','game_kind');value=process();token=str(time.monotonic_ns())
        payload=base64.b64encode(json.dumps(dict(game=value,token=token,kind=command['kind'])).encode()).decode()
        with (root/('control-'+token+'.log')).open('w') as output:
            child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--observe-control',payload],env=env,cwd=root,
                stdin=subprocess.DEVNULL,stdout=output,stderr=output,start_new_session=True)
        return dict(pid=child.pid,token=token)
    if action=='control-state':
        from check_hardening import read_record
        return read_record(root/('control-'+command['token']+'.json'))
    if action=='route-state':
        from check_hardening import read_record
        return read_record(root/('route-'+command['token']+'.json'))
    if action=='observations':
        profile=root/'lookup';paths=list((profile/'observations').glob('request-*.json'))
        records=sorted((json.loads(path.read_text()) for path in paths),key=lambda row:row['capture_start_ns'])
        trace=[json.loads(line.split(':',1)[1]) for line in (profile/'daemon.log').read_text().splitlines() if line.startswith('lookup-timing:')]
        return dict(records=records,trace=trace,observer_errors=(profile/'observer-errors.jsonl').read_text() if (profile/'observer-errors.jsonl').exists() else '')
    if action=='source-ocr-diagnostic':
        from lookup import ocr
        _require(all(_integer(command.get(key),1) for key in ('pid','run','request')),'source_request')
        key='-'.join(str(command[name]) for name in ('pid','run','request'))
        observation=json.loads((root/'lookup/observations'/('request-'+key+'.json')).read_text())
        png,transform=ocr._prepare_image(Path(observation['image_path']),observation['cursor'],ocr.DEFAULT_ENLARGE,ocr.DEFAULT_INVERT)
        result=subprocess.run(['tesseract','stdin','stdout','-l','eng','--psm',str(ocr.DEFAULT_PSM),'tsv'],input=png,capture_output=True,timeout=8,check=True)
        words=ocr.parse_tsv(result.stdout,transform)
        return dict(source=observation,prepared_sha256=hashlib.sha256(png).hexdigest(),
            words=[dict(text=word.text,confidence=word.confidence,box=word.box) for word in words])
    if action=='windows':return dict(process=process(),windows=windows(),active=platform.run(['kdotool','getactivewindow'],env).decode().strip(),at_ns=time.monotonic_ns())
    if action=='image':
        if command['kind']=='source':
            _require(all(_integer(command.get(key),1) for key in ('pid','run','request')),'image_request')
            key='-'.join(str(command[name]) for name in ('pid','run','request'));path=root/'lookup/observations'/('source-'+key+'.png')
        elif command['kind']=='overlay':
            _require(str(command.get('token','')).isdigit(),'image_token');path=root/('route-'+command['token']+'-useful.png')
        else:raise ValueError('unknown_image_kind')
        _require(path.is_file() and not path.is_symlink() and path.stat().st_uid==1001,'unowned_image');data=path.read_bytes()
        return dict(png_base64=base64.b64encode(data).decode(),sha256=hashlib.sha256(data).hexdigest())
    if action in ('snapshot','desktop-probe'):
        monitor=platform.monitors(env)[0];start=time.monotonic_ns();frame=capture.capture_monitor(monitor,env);end=time.monotonic_ns()
        optical=subprocess.run(['tesseract','stdin','stdout','-l','eng','--psm','11','tsv'],input=frame.png,capture_output=True,timeout=8)
        from lookup import ocr
        error=None
        try:words=ocr.parse_tsv(optical.stdout)
        except ocr.OcrError as failure:words=[];error=failure.reason
        return dict(png_base64=base64.b64encode(frame.png).decode(),sha256=hashlib.sha256(frame.png).hexdigest(),
            capture_start_ns=start,capture_end_ns=end,monitor=monitor.__dict__,cursor=platform.cursor_position(env),
            words=[dict(text=word.text,box=word.box,confidence=word.confidence,line_id=word.line_id) for word in words],ocr_error=error,
            windows=windows() if action=='snapshot' else [],game_verified=action=='snapshot')
    if action=='log':
        paths=sorted((root/'userdata/logs').glob('*.log'))
        return dict(text='\n'.join(path.read_text() for path in paths),files=[dict(name=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths],process=process())
    raise ValueError('unknown_game_command')


def vm_command(value):
    import base64,json,subprocess
    encoded=base64.b64encode(json.dumps(value).encode()).decode()
    child=subprocess.run(['ssh','-o','BatchMode=yes','-o','HostKeyAlias=lookup-gsd-07','-o',
        'UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-p','2227','archvm',
        'sudo','-n','-H','-u','lookup07','python','/home/lookup07/check_games.py','--guest-command',encoded],
        capture_output=True,text=True,timeout=30)
    if child.returncode:raise RuntimeError(child.stderr[-1500:])
    return json.loads(child.stdout)


def app_observer():
    import hashlib,json,os,runpy,sys
    from pathlib import Path
    _require(os.getuid()==1001 and Path.home()==Path('/home/lookup07'),'unowned_account')
    sys.path.insert(0,'/usr/lib/lookup/app')
    from lookup import app
    try:
        from tools.check_hardening import write_record
    except ModuleNotFoundError:
        from check_hardening import write_record
    kind=os.environ.get('LOOKUP_GAME_KIND','wesnoth');_require(kind in ('wesnoth','doom','assaultcube'),'game_kind')
    root=Path.home()/'.local/state/lookup-games-08'/kind/'lookup';(root/'observations').mkdir(exist_ok=True)
    current={}
    def frozen(value,start,end):
        events=[json.loads(line.split(':',1)[1]) for line in (root/'daemon.log').read_text().splitlines() if line.startswith('lookup-timing:')]
        queue=[row for row in events if row['pid']==os.getpid() and row['stage']==2 and row['mono_ns']<=start][-1]
        current.clear();current.update(pid=os.getpid(),run=queue['run'],request=queue['request'],mode=value.mode,
            cursor=value.point,monitor=value.monitor.__dict__,capture_start_ns=start,capture_end_ns=end,unchanged_objects=True)
        if value.image:
            key='-'.join(str(queue[name]) for name in ('pid','run','request'))
            png=value.image.png;path=root/'observations'/('source-'+key+'.png');path.write_bytes(png)
            current.update(backend=value.image.backend,sha256=hashlib.sha256(png).hexdigest(),image_path=str(path))
        key='-'.join(str(queue[name]) for name in ('pid','run','request'));write_record(root/'observations'/('request-'+key+'.json'),dict(current))
    def resolved(value,start,end):
        current.update(query=value.text,context=value.context,span=value.span,context_complete=value.context_complete,resolve_start_ns=start,resolve_end_ns=end)
        key='-'.join(str(current[name]) for name in ('pid','run','request'));write_record(root/'observations'/('request-'+key+'.json'),dict(current))
    def failed(name):
        with (root/'observer-errors.jsonl').open('a') as output:output.write(json.dumps(dict(error=name,at_ns=time.monotonic_ns()))+'\n')
    app.Source.freeze=tap(app.Source.freeze,frozen,failed);app.Source.resolve=tap(app.Source.resolve,resolved,failed)
    sys.argv=['/usr/bin/lookup','--app'];runpy.run_path('/usr/bin/lookup',run_name='__main__')


def observe_route(encoded):
    import base64,fcntl,hashlib,json,os,re,struct,subprocess,sys
    from pathlib import Path
    _require(os.getuid()==1001 and Path.home()==Path('/home/lookup07'),'unowned_account')
    sys.path.insert(0,'/usr/lib/lookup/app')
    from lookup import capture,config,dicts,gui,ocr,platform
    from lookup.normalize import normalize
    from check_hardening import chronological,optical_match,read_record,write_record
    from PyQt6.QtGui import QGuiApplication
    from PyQt6.QtDBus import QDBus,QDBusConnection,QDBusMessage
    command=json.loads(base64.b64decode(encoded));kind=command.get('game_kind','wesnoth');_require(kind in ('wesnoth','doom','assaultcube'),'game_kind')
    root=Path.home()/'.local/state/lookup-games-08'/kind;profile=root/'lookup'
    env=platform.session_env();env['LOOKUP_DICTS']='/usr/share/lookup/dicts';os.environ.update(env)
    application=QGuiApplication([]);application.setDesktopFileName('org.lookup.Linux');bus=QDBusConnection.sessionBus()
    target=root/('route-'+command['token']+'.json');descriptor=None;result=dict(state='preparing',token=command['token'])
    def window(pid,title=None):
        ids=platform.run(['kdotool','search','--pid',str(pid)],env).decode().split()
        for identity in ids:
            message=QDBusMessage.createMethodCall('org.kde.KWin','/KWin','org.kde.KWin','getWindowInfo');message.setArguments([identity])
            reply=bus.call(message,QDBus.CallMode.Block,600);info=reply.arguments()[0] if reply.arguments() else {}
            if info.get('pid')==pid and (title is None or info.get('caption')==title):return identity,info
        return None,None
    def events():
        return chronological(json.loads(line.split(':',1)[1]) for line in (profile/'daemon.log').read_text().splitlines() if line.startswith('lookup-timing:'))
    try:
        game_id,game_info=window(command['game']['pid']);active=platform.run(['kdotool','getactivewindow'],env).decode().strip()
        _require(game_info and game_info.get('fullscreen') is True and active==game_id,'game_not_active_fullscreen')
        monitor=platform.monitors(env)[0];baseline=capture.capture_monitor(monitor,env);baseline_end=time.monotonic_ns()
        devices=[path for path in Path('/sys/class/input').glob('event*') if path.joinpath('device/name').read_text().strip()=='AT Translated Set 2 keyboard']
        _require(len(devices)==1,'keyboard_identity');device=Path('/dev/input')/devices[0].name
        descriptor=os.open(device,os.O_RDONLY|os.O_NONBLOCK);fcntl.ioctl(descriptor,0x400445a0,struct.pack('i',time.CLOCK_MONOTONIC));clock_set=time.monotonic_ns()
        result.update(state='armed',device=str(device),game_window=game_id,game_info=game_info,baseline_sha256=hashlib.sha256(baseline.png).hexdigest())
        write_record(target,result);keys=set();pending=None;deadline=time.monotonic()+45;next_frame=0
        while time.monotonic()<deadline:
            application.processEvents()
            try:data=os.read(descriptor,24*64)
            except BlockingIOError:data=b''
            receipt=time.monotonic_ns()
            for offset in range(0,len(data),24):
                seconds,micros,kind,code,value=struct.unpack('llHHI',data[offset:offset+24])
                _require(not(kind==0 and code==3),'input_overflow')
                if kind!=1 or code not in (18,42,54,125,126):continue
                if value==1:keys.add(code)
                elif value==0:keys.discard(code)
                if code==18 and value==1 and keys.intersection((42,54)) and keys.intersection((125,126)):
                    stamp=seconds*1_000_000_000+micros*1000;_require(clock_set<=stamp<=receipt,'kernel_clock_domain')
                    _require(pending is None,'extra_physical_input');pending=dict(input_ns=stamp,receipt_ns=receipt,released=False)
                if pending:pending['released']=not keys
            if not pending:time.sleep(.01);continue
            result['input']=dict(pending);write_record(target,result)
            trace=events();triggers=[row for row in trace if row['stage']==1 and row['mono_ns']>=pending['input_ns']]
            if not triggers:time.sleep(.01);continue
            trigger=triggers[-1];request=trigger['request'];pid=trigger['pid']
            result['trigger']=trigger
            key='-'.join(str(trigger[name]) for name in ('pid','run','request'))
            observation=read_record(profile/'observations'/('request-'+key+'.json'))
            result['source_observation']=observation
            error=request_error(trace,trigger,pending['input_ns'])
            if error:
                result.update(state='failed',error='production_stage6',production_event=error);write_record(target,result);return 1
            if not observation or 'query' not in observation:time.sleep(.02);continue
            _require(observation['pid']==pid and observation['run']==trigger['run'] and observation['query']==command['word'] and observation['mode']=='ocr','actual_query_mismatch')
            ready=[row for row in trace if row['pid']==pid and row['request']==request and row['stage']==4 and row.get('useful')==1]
            if not ready or time.monotonic_ns()<next_frame:time.sleep(.02);continue
            popup_id,popup=window(pid,gui.TITLE)
            if not popup:time.sleep(.02);continue
            begin=time.monotonic_ns();frame=capture.capture_monitor(monitor,env);end=time.monotonic_ns();image=capture._png_image(frame.png)
            left,top=platform.image_point((popup['x'],popup['y']),monitor,(frame.width,frame.height));right,bottom=platform.image_point((popup['x']+popup['width'],popup['y']+popup['height']),monitor,(frame.width,frame.height))
            crop=capture._encode(image.copy(int(left),int(top),int(right-left),int(bottom-top)))
            optical=subprocess.run(['tesseract','stdin','stdout','-l','eng+rus','--psm','11'],input=crop,capture_output=True,timeout=5).stdout.decode()
            with dicts.open_all(config.Config()) as dictionaries:
                articles=dictionaries.lookup_exact(command['word']);body=sorted(set(re.findall('[а-яё]{5,}',articles[0].text[:1800].casefold())))
            if not optical_match(optical,command['word'],body):next_frame=time.monotonic_ns()+50_000_000;continue
            source_png=Path(observation['image_path']).read_bytes()
            source_tsv=subprocess.run(['tesseract','stdin','stdout','-l','eng','--psm','11','tsv'],input=source_png,capture_output=True,timeout=5).stdout
            words=ocr.parse_tsv(source_tsv);tokens=[normalize(word.text) for word in words];context_tokens=[normalize(value) for value in observation['context'].split()];context_tokens=[value for value in context_tokens if value]
            useful_words=[(word,token) for word,token in zip(words,tokens) if token];line_ids=set()
            for index in range(len(useful_words)-len(context_tokens)+1):
                if [token for _,token in useful_words[index:index+len(context_tokens)]]==context_tokens:
                    line_ids={word.line_id for word,_ in useful_words[index:index+len(context_tokens)]};break
            point=observation['cursor'];matched=[word for word in words if normalize(word.text)==command['word'] and word.box[0]<=point[0]<=word.box[0]+word.box[2] and word.box[1]<=point[1]<=word.box[1]+word.box[3]]
            _require(len(matched)==1,'source_target_geometry')
            born=int(Path('/proc',str(pid),'stat').read_text().split(') ',1)[1].split()[19]);sha=hashlib.sha256(frame.png).hexdigest()
            timing=dict(pending,attempt=command['sequence'],input_sequence=command['sequence'],status='success',mode='native',physical=True,
                pid=pid,process_start=born,process_start_source='proc_stat',run=trigger['run'],request=request,clock='guest_monotonic',frame_clock='guest_monotonic',origin='kernel_evdev',
                kernel_clock_verified=True,clock_ioctl_verified=True,trigger_ns=trigger['mono_ns'],last_not_visible_ns=baseline_end,
                first_visible_start_ns=begin,first_visible_end_ns=end,frame_identity=[pid,born,trigger['run'],request],frame_sha256=sha,
                observed=True,fresh=sha!=result['baseline_sha256'],useful_verified=True,loading=False,error_card=False,previous_card=False)
            source=dict(observation,kind='actual_game',word=command['word'],word_rect=matched[0].box,visual_lines=len(observation['context'].splitlines()),
                line_evidence='unchanged production OCR context line boundaries',source_words=[dict(text=word.text,box=word.box,line_id=word.line_id) for word in words])
            path=root/('route-'+command['token']+'-useful.png');path.write_bytes(frame.png)
            result.update(state='complete',route=dict(sequence=command['sequence'],scene='tutorial_map_dialogue',game_pid=command['game']['pid'],game_start=command['game']['start'],window_id=game_id,game_active_before=True,
                source=source,timing=timing,overlay=dict(useful=True,loading=False,error=False,current_word=command['word'],sha256=sha,identity=timing['frame_identity']),popup_geometry=popup,overlay_path=str(path)),optical=optical)
            write_record(target,result);return 0
        raise TimeoutError('game_useful_frame_deadline')
    except Exception as error:
        result.update(state='failed',error=type(error).__name__,reason=str(error) if isinstance(error,EvidenceError) else None);write_record(target,result);return 1
    finally:
        if descriptor is not None:os.close(descriptor)


def run_lookup_route(output,word,sequence,*,game_kind='wesnoth',point=None):
    """Close immediately after useful capture; interactive gameplay is recorded separately."""
    import base64,json
    from pathlib import Path
    try:
        from tools.check_hardening import vm_input,write_record
    except ModuleNotFoundError:
        from check_hardening import vm_input,write_record
    def command(value):return vm_command(dict(value,game_kind=game_kind))
    output=Path(output);_require(not output.exists(),'existing_route_output')
    frame=command(dict(action='snapshot'))
    targets=[item for item in frame['words'] if item['text'].strip('.,!?:;').casefold()==word.casefold()]
    if point is None:
        _require(len(targets)==1,'game_word_geometry')
        left,top,width,height=targets[0]['box'];point=[round(left+width/2),round(top+height/2)]
        vm_input('Pointer',X=point[0],Y=point[1],Buttons=0)
    else:_require(game_kind in ('doom','assaultcube') and frame['cursor']==point,'actual_locked_cursor')
    observer=command(dict(action='start-route',route=dict(sequence=sequence,word=word)))
    data=dict(complete=False,lookup_complete=False,observer=observer,target=targets[0] if len(targets)==1 else None,point=point)
    write_record(output,data);deadline=time.monotonic()+8
    while time.monotonic()<deadline:
        state=command(dict(action='route-state',token=observer['token']))
        if state and state['state'] in ('armed','failed'):break
        time.sleep(.05)
    _require(state and state['state']=='armed','observer_not_armed')
    if game_kind=='assaultcube':
        data['runtime_before_input']=command(dict(action='doom-runtime-evidence'))
        write_record(output,data)
    vm_input('Keys',Codes='e0 5b 2a 12 92 aa e0 db');deadline=time.monotonic()+45
    while time.monotonic()<deadline:
        state=command(dict(action='route-state',token=observer['token']))
        if state and state['state'] in ('complete','failed'):break
        time.sleep(.08)
    data['lookup_observation']=state;write_record(output,data)
    _require(state and state['state']=='complete','lookup_did_not_complete')
    vm_input('Keys',Codes='01 81')
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        active=command(dict(action='windows'))
        if active['active']==state['game_window']:break
        time.sleep(.05)
    route=state['route'];route['dismissal']=dict(physical=True,released=True,closed=active['active']==state['game_window'],
        at_ns=active['at_ns'],timestamp_kind='post-command observation',command='Escape full release')
    data.update(lookup_complete=True,route=route,after_dismiss=active)
    for kind in ('source','overlay'):
        arguments=dict(action='image',kind=kind)
        if kind=='source':arguments.update({key:route['timing'][key] for key in ('pid','run','request')})
        else:arguments['token']=observer['token']
        image=command(arguments);output.with_name(output.stem+'-'+kind+'.png').write_bytes(base64.b64decode(image['png_base64']))
    write_record(output,data);print(json.dumps(dict(lookup_complete=True,dismissed=route['dismissal']['closed'],word=word,
        latency_ms=physical_latency(route['timing']),visual_lines=route['source']['visual_lines'])),flush=True)
    return data


def observe_control(encoded):
    """Non-grabbing kernel input observation and actual game frames, never fixture data."""
    import base64,fcntl,hashlib,json,os,struct
    from pathlib import Path
    from check_hardening import write_record
    _require(os.getuid()==1001,'unowned_account')
    import sys
    sys.path.insert(0,'/usr/lib/lookup/app')
    from lookup import capture,platform
    from PyQt6.QtGui import QGuiApplication
    command=json.loads(base64.b64decode(encoded));kind=command['kind'];_require(kind in ('camera','movement'),'control_kind')
    root=Path.home()/'.local/state/lookup-games-08/assaultcube';target=root/('control-'+command['token']+'.json')
    app=QGuiApplication([]);app.setDesktopFileName('org.lookup.Linux');env=platform.session_env();descriptors=[]
    data=dict(state='preparing',game=command['game'],kind=kind)
    try:
        monitor=platform.monitors(env)[0];before=capture.capture_monitor(monitor,env)
        names=('AT Translated Set 2 keyboard',) if kind=='movement' else ('ImExPS/2 Generic Explorer Mouse','VirtualBox USB Tablet','VirtualBox mouse integration')
        for path in Path('/sys/class/input').glob('event*'):
            if path.joinpath('device/name').read_text().strip() in names:
                descriptor=os.open('/dev/input/'+path.name,os.O_RDONLY|os.O_NONBLOCK)
                fcntl.ioctl(descriptor,0x400445a0,struct.pack('i',time.CLOCK_MONOTONIC));descriptors.append((descriptor,path.name))
        _require(descriptors,'control_device');armed=time.monotonic_ns();data.update(state='armed',armed_ns=armed);write_record(target,data)
        deadline=time.monotonic()+12;event=None
        while time.monotonic()<deadline and event is None:
            for descriptor,name in descriptors:
                try:raw=os.read(descriptor,24*128)
                except BlockingIOError:continue
                for offset in range(0,len(raw),24):
                    sec,usec,event_kind,code,value=struct.unpack('llHHI',raw[offset:offset+24]);stamp=sec*1_000_000_000+usec*1000
                    _require(not(event_kind==0 and code==3),'control_input_overflow')
                    if stamp>=armed and ((kind=='movement' and event_kind==1 and code==17 and value==1) or
                        (kind=='camera' and event_kind in (2,3))):event=dict(input_ns=stamp,device=name,type=event_kind,code=code,value=value)
            app.processEvents();time.sleep(.01)
        _require(event is not None,'control_input_missing');time.sleep(.8)
        after=capture.capture_monitor(monitor,env);end=time.monotonic_ns()
        before_path=root/('control-'+command['token']+'-before.png');after_path=root/('control-'+command['token']+'-after.png')
        before_path.write_bytes(before.png);after_path.write_bytes(after.png)
        active=platform.run(['kdotool','getactivewindow'],env).decode().strip()
        windows=platform.run(['kdotool','search','--pid',str(command['game']['pid'])],env).decode().split()
        path=Path('/proc',str(command['game']['pid']));start=int((path/'stat').read_text().split(') ',1)[1].split()[19])
        _require(path.stat().st_uid==1001 and start==command['game']['start'],'control_game_identity')
        data.update(state='complete',proof=dict(physical=True,game_active=active in windows,game_pid=command['game']['pid'],game_start=start,
            kind='relative_pointer' if kind=='camera' else 'movement_key',**event,clock='kernel_evdev_monotonic',clock_ioctl_verified=True,
            capture_end_ns=end,before_sha256=hashlib.sha256(before.png).hexdigest(),after_sha256=hashlib.sha256(after.png).hexdigest(),
            before_path=str(before_path),after_path=str(after_path)))
    except Exception as error:data.update(state='failed',error=repr(error))
    finally:
        for descriptor,_ in descriptors:os.close(descriptor)
        write_record(target,data)


def run_control(output,kind):
    from pathlib import Path
    from tools.check_hardening import vm_input,write_record
    def command(value):return vm_command(dict(value,game_kind='assaultcube'))
    _require(not Path(output).exists(),'existing_control_output');child=command(dict(action='start-control',kind=kind))
    deadline=time.monotonic()+8;state=None
    while time.monotonic()<deadline:
        state=command(dict(action='control-state',token=child['token']))
        if state and state['state'] in ('armed','failed'):break
        time.sleep(.05)
    _require(state and state['state']=='armed','control_not_armed')
    try:
        if kind=='camera':vm_input('Relative',X=60,Y=0)
        else:vm_input('Keys',Codes='11');time.sleep(.4)
    finally:
        if kind=='movement':vm_input('Keys',Codes='91')
    deadline=time.monotonic()+8
    while time.monotonic()<deadline:
        state=command(dict(action='control-state',token=child['token']))
        if state and state['state'] in ('complete','failed'):break
        time.sleep(.05)
    write_record(Path(output),dict(child=child,observation=state));_require(state and state['state']=='complete','control_incomplete')
    return state


if __name__=='__main__':
    import argparse,json
    parser=argparse.ArgumentParser();parser.add_argument('--guest-command');parser.add_argument('--app-observer',action='store_true');parser.add_argument('--observe-route')
    parser.add_argument('--lookup-route');parser.add_argument('--word');parser.add_argument('--sequence',type=int)
    parser.add_argument('--pilot-session',action='store_true');parser.add_argument('--observe-control');args=parser.parse_args()
    if args.pilot_session:pilot_session()
    if args.lookup_route:run_lookup_route(args.lookup_route,args.word,args.sequence)
    if args.observe_route:raise SystemExit(observe_route(args.observe_route))
    if args.observe_control:observe_control(args.observe_control)
    if args.app_observer:app_observer()
    if args.guest_command:print(json.dumps(guest_command(args.guest_command)))
