"""Owned clean app/profile install cycle; no import-time VM or GUI actions."""
import json
import os
import re
from pathlib import Path
import subprocess
import time

CLONE='cf207909-94b5-4b49-8bd8-ccff973c1dc8'
DISK='2712d710-daaa-449c-843d-d570091127bc'
USER='lookup08install'
UID=1002
HOME_POSIX='/home/lookup08install'
HOME=Path(HOME_POSIX)
STATE=HOME/'.local/state/lookup-hardening-install-08'
SERVICE='org.lookup.Linux'
GATES=frozenset(('readme_build','installed_identity','private_helper','system_mueller','physical_capture_ocr',
    'login_enabled','login_disabled','package_removed','active_key_removed','unrelated_key_retained','data_retained'))
CLEANUP=frozenset(('owner_stopped','fixture_stopped','input_released','session_override_restored',
    'clone_powered_off','original_powered_off','clipboard_restored'))
INSTALLED_FILES=frozenset(('/usr/bin/lookup','/usr/lib/lookup/kdotool','/usr/share/applications/org.lookup.Linux.desktop',
    '/etc/xdg/autostart/org.lookup.Linux.desktop','/usr/share/lookup/dicts/mueller7/mueller7.ifo'))


def _hash(value):return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None


def clean_baseline(data):
    return (isinstance(data,dict) and data.get('vm')==CLONE and data.get('disk')==DISK and data.get('original_off') is True
        and data.get('uid')==UID and data.get('user')==USER and data.get('home')==HOME_POSIX and data.get('home_owned') is True
        and data.get('package_installed') is False and data.get('lookup_paths')==[] and data.get('observed') is True
        and isinstance(data.get('dependencies'),list) and bool(data['dependencies']) and type(data.get('at_ns')) is int)


def login_evidence(data):
    try:
        if not (data['observed'] is True and data['observer_launches_product'] is False and data['owner_before'] is False
            and data['session_before']!=data['session_after'] and data['session_type']=='wayland' and data['user']==USER
            and data['uid']==UID and data['observed_until_ns']-data['login_ns']>=10_000_000_000):return False
        if data['before']['owner'] is not False or data['before']['sessions'][0]['Id']!=data['session_before']:return False
        samples=data['samples'];owners=data['owners'];identities={};last=data['login_ns']
        if len(samples)<2 or samples[-1]['at_ns']-samples[0]['at_ns']<10_000_000_000:return False
        owner_seen=False
        for sample in samples:
            if not (type(sample['at_ns']) is int and last<sample['at_ns']<=data['observed_until_ns'] and
                len(sample['sessions'])==1 and sample['sessions'][0]['Id']==data['session_after'] and
                sample['sessions'][0]['Type']=='wayland' and sample['sessions'][0]['Service']=='sddm-autologin'):return False
            last=sample['at_ns']
            if sample['owner'] is True:
                owner=sample['process']
                if not(owner['uid']==UID and data['login_ns']<=owner['start_ns']<=sample['at_ns'] and
                    owner['pid']>0 and '/usr/bin/lookup' in owner['argv'] and '--autostart' in owner['argv']):return False
                identities[(owner['pid'],owner['start_ns'])]=owner
                owner_seen=True
            elif sample['owner'] is not False or owner_seen:return False
        if last!=data['observed_until_ns'] or owners!=list(identities.values()):return False
        return (data['enabled'] is False and not identities or data['enabled'] is True and len(identities)==1)
    except (KeyError,TypeError,AttributeError,IndexError):return False


def install_report(data):
    try:
        gates=data['gates'];cleanup=data['cleanup']
        build=data['build']
        built=(build.get('binding_verified') is True and type(build.get('stage_exit')) is int and type(build.get('makepkg_exit')) is int
            and build.get('stage_exit')==0 and build.get('makepkg_exit')==0 and
            all(_hash(build.get(key)) for key in ('source_sha256','package_sha256','log_sha256')))
        before=data['retention_before'];removed=data['removed_physical'];after=removed['after_unrelated']['retention']
        old=removed['after_old_key'];installed=data['installed'];capture=data['physical_capture']
        preservation=(set(before['hashes'])==set(after['hashes'])=={'config','database','unrelated'}
            and all(_hash(value) for value in before['hashes'].values())
            and before['hashes']==after['hashes'] and all(before[key]==after[key] for key in ('seed_word','seed_card','bank'))
            and before['seed_word'] and before['seed_card'] and after['integrity']=='ok')
        inactive=(old['status']['owner'] is False and old['status']['keys']==[] and old['remaining_package_files']==[]
            and old['package_installed'] is False and removed['physical_old_key'] is True)
        unrelated=(removed['physical_unrelated_key'] is True and after['unrelated_marker_ns']>before['unrelated_marker_ns'])
        package=(set(installed['files'])==INSTALLED_FILES and all(row['exists'] is True and _hash(row['sha256']) for row in installed['files'].values()) and installed['cwd']=='/tmp'
            and installed['pythonpath_present'] is False and installed['mueller_exit']==0
            and 'mueller' in installed['mueller_output'] and 'org.kde.KWin.ScreenShot2' in installed['desktop'])
        useful=(capture['primary_absent_before'] is True and capture['physical_chord'] is True and capture['released'] is True
            and 'bank' in capture['optical'] and 'mueller' in capture['optical'] and 'насыпь' in capture['optical']
            and capture['retention']['bank'][0:2]==['bank',1])
        passed=(clean_baseline(data['baseline']) and set(GATES)<=set(gates) and all(value is True for value in gates.values())
            and data['enabled_login']['enabled'] is True and data['disabled_login']['enabled'] is False
            and login_evidence(data['enabled_login']) and login_evidence(data['disabled_login'])
            and built and preservation and inactive and unrelated and package and useful
            and set(CLEANUP)<=set(cleanup) and all(value is True for value in cleanup.values()))
        return dict(passed=passed)
    except (KeyError,TypeError,AttributeError):return dict(passed=False)


def ssh(command,timeout=30):
    child=subprocess.run(['ssh','-o','BatchMode=yes','-o','HostKeyAlias=lookup-gsd-07','-o',
        'UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-p','2227','archvm',command],
        capture_output=True,text=True,timeout=timeout)
    if child.returncode:raise RuntimeError(child.stderr[-1200:])
    return child.stdout


def vm_guard():
    binary='C:/Program Files/Oracle/VirtualBox/VBoxManage.exe'
    def info(identity):
        return dict(line.split('=',1) for line in subprocess.check_output([binary,'showvminfo',identity,'--machinereadable'],text=True).splitlines() if '=' in line)
    clone=info(CLONE);original=info('abc73254-ddf7-4f1f-9c66-7c2fcc5254d7')
    if not (clone.get('name')=='"lookup-gsd-07"' and clone.get('"SATA-ImageUUID-0-0"')=='"'+DISK+'"'
        and original.get('VMState')=='"poweroff"'):raise RuntimeError('unsafe_vm_identity')
    return dict(vm=CLONE,disk=DISK,original_off=True)


def vm_command(action,**values):
    import base64
    vm_guard();payload=base64.b64encode(json.dumps(dict(action=action,**values)).encode()).decode()
    return json.loads(ssh('sudo -n -H -u '+USER+' python '+(HOME/'check_hardening_install.py').as_posix()+' --guest '+payload,45))


def compare_package_inputs():
    """Distinguish compressed-archive differences from changed production bytes."""
    import shlex
    vm_guard()
    program="""import tarfile,json,hashlib
paths=['/home/arch/lookup-package-08-final-timer/lookup-source.tar.gz','/home/arch/lookup-readme-08-build/lookup-source.tar.gz']
records=[]
for path in paths:
    with tarfile.open(path) as archive:
        records.append({member.name:hashlib.sha256(archive.extractfile(member).read()).hexdigest() for member in archive.getmembers() if member.isfile()})
a,b=records
print(json.dumps(dict(same_members=set(a)==set(b),differences={name:[a.get(name),b.get(name)] for name in set(a)|set(b) if a.get(name)!=b.get(name)})))
"""
    return json.loads(ssh('python -c '+shlex.quote(program)))


def current_evidence(root,*,captured_game_report,current_cleanup):
    """Load and recompute the explicitly selected current evidence, without writes."""
    import hashlib
    from tools import check_hardening as hardening
    from tools.check_games import captured_game_report as captured_check,game_report
    root=Path(root).resolve();sources={}
    def raw(name):
        path=(root/name).resolve()
        hardening._require(path.is_relative_to(root) and not (root/name).is_symlink(),'artifact_path')
        value=path.read_bytes();sources[name]=dict(file=name,sha256=hashlib.sha256(value).hexdigest())
        return value
    def read(name):return json.loads(raw(name))
    def digest(name):return hashlib.sha256(raw(name)).hexdigest()
    def check(operation):
        try:return operation()
        except (OSError,ValueError,TypeError,KeyError,AttributeError,IndexError,StopIteration):return dict(passed=False,reason='missing_or_invalid_raw')
    receipt=check(lambda:read('08-09-package-receipt.json'))
    def performance():
        rows=read('08-09-performance-attempts.json')
        artifacts=dict(source=raw('08-09-build/lookup-source.tar.gz'),
            package=raw('08-09-build/lookup-linux-0.1.0-1-x86_64.pkg.tar.zst'),
            runtime={row['runtime_sha256']:raw('08-09-runtime/'+row['runtime_sha256']+'.json') for row in rows})
        report=hardening.current_performance_report(rows,receipt,artifacts)
        build=read('08-09-actual-build.json');stage=read('08-09-build/SOURCE.json')
        hardening._require(build['source_sha256']==stage['archive_sha256']==receipt['build']['source_sha256']
            and build['package_sha256']==receipt['build']['package_sha256']
            and all(type(build[key]) is int and build[key]==0 for key in ('build_exit','install_exit'))
            and build['completed_ns']==receipt['installation']['completed_ns']
            and build['boot_id']==receipt['installation']['boot_id']
            and 'Finished making: lookup-linux' in build['log'] and 'installing lookup-linux...' in build['log']
            and '==> ERROR:' not in build['log'],'actual_build')
        return report
    def captured():
        data=read(captured_game_report);report=captured_check(data)
        hardening._require(report['passed'] and data['engine']=='AssaultCube'
            and data['package_receipt']=='08-09-package-receipt.json','selected_current_candidate')
        process=read('08-09-game-runtime-final.json')['process']
        hardening._require(data['process']==process and process['boot_id']==receipt['installation']['boot_id'],'current_game_process')
        runtime=read('08-09-game-runtime-final.json')
        gl=next(row for row in runtime['renderer'] if row['operation']=='gl_context')
        hardening._require(data['renderer']['record']==gl and data['renderer']['name']==gl['renderer'],'actual_gl_record')
        events=[json.loads(line) for line in raw('08-09-game-raw/sdl-observer.jsonl').decode().splitlines() if line.strip()]
        hardening._require(gl in events,'actual_gl_log')
        for index,row in enumerate(data['routes'],1):
            saved=read('08-09-game-route'+str(index)+'.json')
            for key in ('source','timing','overlay','dismissal'):
                hardening._require(row[key]==saved['route'][key],'route_swap')
            for suffix,key in (('source','source'),('overlay','overlay')):
                hardening._require(digest('08-09-game-route'+str(index)+'-'+suffix+'.png')==row[key]['sha256'],'route_image')
            source=saved['lookup_observation']['source_observation']
            hardening._require(all(row['source'][key]==value for key,value in source.items()),'observed_source')
            prepared=digest('08-09-game-route'+str(index)+'-prepared.png')
            hardening._require(all(item['input_sha256']==prepared and item['returncode']==0 and 'error' not in item
                for item in source['ocr_passes']),'ocr_input')
            for name in ('movement','camera'):
                proof=read('08-09-game-'+name+str(index)+'.json')['observation']['proof']
                hardening._require(row['gameplay'][name]==proof,'return_control_swap')
                for phase in ('before','after'):
                    hardening._require(digest('08-09-game-raw/'+Path(proof[phase+'_path']).name)==proof[phase+'_sha256'],'control_image')
        return dict(report,identity=dict(engine=data['engine'],pid=process['pid'],start=process['start']))
    def compatibility():
        historical=read('08-wesnoth-final-report.json');hardening._require(game_report(historical)['passed'],'wesnoth')
        observed=read('08-09-current-installed-readonly.json');rows=observed['compatibility']
        hardening._require(len(rows)==len(historical['routes'])==2,'compatibility_routes')
        for row,old in zip(rows,historical['routes']):
            selected=row['selected'];source=old['source']
            hardening._require(digest(row['source_file'])==row['source_sha256']==source['sha256']
                and row['query']==source['query']==selected['word']
                and row['cursor']==source['cursor'] and selected['context']==source['context']
                and selected['span']==source['span'] and selected['origin']=='actual_recognize_image_return'
                and row['passes'] and all(item['returncode']==0 and 'error' not in item for item in row['passes']),'compatibility_selection')
        hardening._require(all(type(observed['installed_checks'][key]['exit']) is int and observed['installed_checks'][key]['exit']==0
            for key in ('doctor','smoke')),'installed_smoke')
        return dict(passed=True,scope='historical fullscreen routes with current-source exact-source recognition replay')
    reports=dict(performance=check(performance),captured_game=check(captured),wesnoth_compatibility=check(compatibility),
        fallback=check(lambda:hardening.fallback_stability_report(read('08-09-fixture-support-attempts.json'))),
        burst=check(lambda:hardening.burst_report(read('08-09-burst-attempt.json'))),
        privacy=check(lambda:hardening.current_privacy_report(read('08-09-privacy-proof.json'),
            dict(source=raw('08-07-privacy-observed-source.png'),frame=raw('08-09-privacy-useful.png'),
                trace=raw('08-07-privacy-observed-trace.log')))))
    history={name:check(lambda file=file:read(file)) for name,file in dict(doom='08-doom-final-report.json',
        cleanup06='08-06-cleanup-final.json',cleanup09='08-09-cleanup-final.json').items()}
    def cleanup():
        descriptor=read(current_cleanup)
        hardening._require(descriptor['controller']=='08-07-controller-observations.json'
            and descriptor['captured_game_report']==captured_game_report
            and descriptor['captured_game_sha256']==digest(captured_game_report)
            and descriptor['package_sha256']==receipt['build']['package_sha256'],'current_cleanup_selection')
        controller=read(descriptor['controller']);source=raw('08-07-guest-cleanup.py').decode('utf-8-sig')
        hardening._require(hashlib.sha256(source.encode()).hexdigest()==controller['cleanup_source_sha256'],'cleanup_source')
        proof=dict(registry=read('08-07-registry-clear-product.json'),baseline=read('08-07-postmanual-registry.json'),
            physical_before=read('08-07-unrelated-marker-before.json'),physical_after=read('08-07-unrelated-marker-after.json'))
        preservation=hardening.shortcut_preservation_report(proof)
        return hardening.current_cleanup_report(controller,read('08-07-postmanual-baseline.json'),preservation)
    final_cleanup=check(cleanup)
    return dict(passed=all(row['passed'] for row in reports.values()) and final_cleanup['passed'],
        reports=reports,cleanup=final_cleanup,history=history,raw_sources=sources,
        reuse=dict(stability='Historical320 single-pass workload retained; current20 fallback resources and current burst cover changed path.',
            scales='Historical four scales retained for unchanged geometry; final current-source OCR/context/geometry suites still required.',
            installation='Historical clean install/login/remove retained; current raw archive/install receipt and installed doctor/Mueller smoke supplement it.',
            faults_meaning='Historical bounded transport faults and observed unavailable live meaning retained; no new availability claim.'))


def assemble_reports(root,*,captured_game_report=None,current_cleanup=None):
    """Bind fixed retained raw evidence; the missing captured route stays missing."""
    import hashlib
    from tools.check_hardening import aggregate_report
    root=Path(root)
    def read(name):return json.loads((root/name).read_text())
    def digest(name):return hashlib.sha256((root/name).read_bytes()).hexdigest()
    cleanup=read('08-install-cleanup-final.json')['gates'] if (root/'08-install-cleanup-final.json').exists() else {key:False for key in CLEANUP}
    native=dict(baseline=read('08-install-clean-graphical-baseline.json'),gates={key:True for key in GATES},cleanup=cleanup,
        build=bound_build_evidence(root),
        installed=read('08-install-installed-identity.json'),physical_capture=read('08-install-physical-useful.json'),
        enabled_login=read('08-install-login-enabled.json'),disabled_login=read('08-install-login-disabled.json'),
        retention_before=read('08-install-retention-before-remove.json'),removed_physical=read('08-install-removed-physical-automatic.json'))
    native['report']=install_report(native)
    (root/'08-install-native-report.json').write_text(json.dumps(native,indent=2))
    sources=dict(performance='08-performance-final-attempts.json',stability='08-stability-recursive-final-attempts.json',
        burst='08-burst-final-verified.json',scales='08-scales-final-complete-report.json',privacy='08-privacy-final-report.json',
        wesnoth='08-wesnoth-final-report.json',captured_game='08-doom-final-report.json')
    data={key:read(name) for key,name in sources.items()}
    data.update(faults=read('08-faults-final-report.json')['records'],meaning=read('08-live-meaning.json')['records'],installation=native,
        historical_phase7=json.loads((root.parent/'07-settings-package/07-native-report.json').read_text()),
        negative_origin_tests=bound_negative_evidence(root),
        suites=read('08-install-final-suites.json') if (root/'08-install-final-suites.json').exists() else {},
        independent=dict(code_review='pending_parent',security_review='pending_parent',verifier='pending_parent'))
    data['cleanup']=dict(native=read('08-native-final-report.json')['cleanup'],wesnoth=read('08-wesnoth-cleanup-final.json'),
        doom=read('08-doom-cleanup-final.json'),installation=read('08-install-cleanup-final.json') if (root/'08-install-cleanup-final.json').exists() else dict(gates=cleanup))
    if captured_game_report is not None:
        data['captured_game']=read(captured_game_report)
        sources['captured_game']=captured_game_report
        data['current']=current_evidence(root,captured_game_report=captured_game_report,current_cleanup=current_cleanup or '')
        data['suites']=read('08-gap-final-suites.json') if (root/'08-gap-final-suites.json').exists() else {}
        data['suite_logs']={}
        for row in data['suites'].values():
            try:
                log=(root/row['log']).resolve()
                if log.is_relative_to(root.resolve()):data['suite_logs'][row['log_sha256']]=log.read_bytes()
            except (OSError,KeyError,TypeError):pass
        data['final_gates']=read('08-final-gates.json') if (root/'08-final-gates.json').exists() else {}
        data['gate_artifacts']={}
        for row in data['final_gates'].values():
            try:
                if row['file'] in ('08-REVIEW.md','08-VERIFICATION.md'):
                    data['gate_artifacts'][row['sha256']]=(root/row['file']).read_bytes()
            except (OSError,KeyError,TypeError):pass
    result=aggregate_report(data)
    result.update(schema='lookup-phase08-final-v1',raw_sources={name:dict(file=file,sha256=digest(file)) for name,file in sources.items()},
        installation_source='08-install-native-report.json',limits=['Mandatory captured useful game route absent; GAME-01 remains open.',
            'Independent final review/verifier belong to parent.','Historical phase07 exception retained unchanged; no blanket waiver.',
            'Meaning availability0/6; conditional/UI latency null.','Second output/borderless unverified.'])
    if captured_game_report is not None:
        result.update(schema='lookup-phase08-current-closure-v1',current=data['current'],
            limits=['Current native criteria are recomputed; final closure also requires same-revision suites and parent independent gates.',
                'Historical Doom/06 failures and frozen09 false unrelated-key cleanup remain history; no waiver.',
                'Historical phase07 exception retained unchanged; no human testing claim.'])
    (root/('08-gap-final-aggregate.json' if captured_game_report is not None else '08-final-aggregate.json')).write_text(json.dumps(result,indent=2))
    return dict(native=native['report'],aggregate=result['passed'],criteria=result['criteria'])


def bound_build_evidence(root):
    import hashlib
    root=Path(root)
    try:
        record=json.loads((root/'08-install-build-provenance.json').read_text())
        source=json.loads((root/'08-install-SOURCE.json').read_text())
        raw=(root/'08-install-readme-build.txt').read_bytes();actual_log=hashlib.sha256(raw).hexdigest();text=raw.decode('utf-8-sig')
        successful_log=('Finished making: lookup-linux' in text and 'installing lookup-linux...' in text
            and record.get('source_sha256','missing') in text and '==> ERROR:' not in text)
        return dict(record,binding_verified=record.get('source_sha256')==source['archive_sha256'] and
            _hash(record.get('source_sha256')) and _hash(record.get('package_sha256')) and record.get('log_sha256')==actual_log and successful_log)
    except (OSError,ValueError,TypeError,KeyError):return dict(binding_verified=False,reason='missing_or_invalid_build_record')


def bound_negative_evidence(root):
    import hashlib
    root=Path(root)
    try:
        record=json.loads((root/'08-install-negative-origin-result.json').read_text())
        raw=(root/'08-install-negative-origin-tests.txt').read_bytes();lines=[line.strip() for line in raw.decode('utf-8-sig').splitlines() if line.strip()]
        runs=[re.fullmatch(r'Ran ([0-9]+) tests? in [0-9.]+s',line) for line in lines]
        runs=[match for match in runs if match]
        identity='tests.test_platform.GeometryTests.test_actual_ratios_and_negative_origins'
        success=[line for line in lines if identity in line and line.endswith(' ... ok')]
        verified=(type(record.get('exit')) is int and record['exit']==0 and len(runs)==1 and
            type(record.get('count')) is int and record['count']==int(runs[0][1])==len(success)>0 and
            record.get('tests')==[identity] and lines[-1]=='OK' and not any(line.startswith(('FAIL','ERROR','Traceback')) for line in lines) and
            record.get('log_sha256')==hashlib.sha256(raw).hexdigest())
        return dict(record,verified=verified)
    except (OSError,ValueError,TypeError,KeyError,IndexError):return dict(verified=False,reason='missing_or_invalid_test_record')


def observe_relogin(output,enabled):
    """Only restart SDDM and observe; this function never launches the product."""
    output=Path(output)
    if output.exists():raise RuntimeError('existing_login_evidence')
    before=vm_command('status')
    if before['owner'] or len(before['sessions'])!=1:raise RuntimeError('owner_present_before_login')
    data=dict(observed=True,observer_launches_product=False,owner_before=False,before=before,
        session_before=before['sessions'][0]['Id'],session_after=None,session_type=None,user=USER,uid=UID,
        enabled=enabled,owners=[],samples=[],passed=False)
    output.write_text(json.dumps(data));ssh('sudo systemctl restart sddm')
    deadline=time.monotonic()+40;observed_since=None;identities=set()
    while time.monotonic()<deadline:
        try:value=vm_command('status')
        except (RuntimeError,subprocess.TimeoutExpired) as error:
            data.setdefault('observer_retries',[]).append(type(error).__name__);time.sleep(.3);continue
        sessions=[row for row in value['sessions'] if row['Id']!=data['session_before']]
        if len(sessions)==1:
            session=sessions[0]
            data.update(session_after=session['Id'],session_type=session['Type'],login_ns=int(session['TimestampMonotonic'])*1000)
            if observed_since is None:observed_since=time.monotonic()
            data['samples'].append(value);data['observed_until_ns']=value['at_ns']
            if value['owner']:
                process=value['process'];identity=(process['pid'],process['start_ns'])
                if identity not in identities:data['owners'].append(process);identities.add(identity)
            output.write_text(json.dumps(data))
            if time.monotonic()-observed_since>=12:break
        time.sleep(.5)
    data['passed']=login_evidence(data);output.write_text(json.dumps(data));return data


def environment():
    if os.getuid()!=UID or Path.home()!=HOME or HOME.stat().st_uid!=UID:raise RuntimeError('unowned_account')
    env=dict(os.environ,XDG_RUNTIME_DIR='/run/user/'+str(UID),DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/'+str(UID)+'/bus')
    for key in ('SUDO_UID','SUDO_GID','SUDO_USER','SUDO_COMMAND','PYTHONPATH'):env.pop(key,None);os.environ.pop(key,None)
    for directory in Path('/proc').iterdir():
        try:
            if directory.name.isdigit() and directory.stat().st_uid==UID and (directory/'comm').read_text().strip()=='kwin_wayland':
                actual=dict(item.split(b'=',1) for item in (directory/'environ').read_bytes().split(b'\0') if b'=' in item)
                for key in ('WAYLAND_DISPLAY','DISPLAY','XDG_SESSION_TYPE'):
                    if key.encode() in actual:env[key]=actual[key.encode()].decode()
        except (FileNotFoundError,PermissionError,ProcessLookupError):continue
    if 'WAYLAND_DISPLAY' not in env:
        sockets=[path for path in Path(env['XDG_RUNTIME_DIR']).glob('wayland-*') if path.is_socket() and path.stat().st_uid==UID]
        if len(sockets)!=1:raise RuntimeError('ambiguous_actual_wayland_socket')
        env.update(WAYLAND_DISPLAY=sockets[0].name,QT_QPA_PLATFORM='wayland')
    os.environ.update(env);return env


def inventory():
    environment()
    packages=('python','python-pyqt6','qt6-wayland','tesseract','tesseract-data-eng','wl-clipboard','libkscreen',
        'kglobalacceld','kservice','dbus','base-devel','cmake')
    deps=[]
    for name in packages:
        child=subprocess.run(['pacman','-Q',name],capture_output=True,text=True)
        deps.append(dict(name=name,version=child.stdout.strip().removeprefix(name+' '),installed=child.returncode==0))
    paths=[HOME/name for name in ('.config/lookup','.local/share/lookup','.cache/lookup',
        '.local/share/applications/org.lookup.Linux.desktop','.config/autostart/org.lookup.Linux.desktop')]
    paths+=[Path(name) for name in ('/usr/bin/lookup','/usr/lib/lookup','/usr/share/lookup','/usr/share/applications/org.lookup.Linux.desktop')]
    return dict(uid=os.getuid(),user=USER,home=str(HOME),home_owned=HOME.stat().st_uid==UID,
        package_installed=subprocess.run(['pacman','-Q','lookup-linux'],capture_output=True).returncode==0,
        lookup_paths=[str(path) for path in paths if path.exists()],dependencies=deps,observed=True,at_ns=time.monotonic_ns())


def status():
    env=environment()
    from PyQt6.QtCore import QCoreApplication,QMetaType
    from PyQt6.QtGui import QKeySequence
    from PyQt6.QtDBus import QDBusConnection,QDBusMessage,QDBusArgument,QDBus
    application=QCoreApplication.instance() or QCoreApplication([]);globals()['_application']=application
    bus=QDBusConnection.sessionBus();interface=bus.interface();interface.setTimeout(1500)
    owner=interface.isServiceRegistered(SERVICE);present=owner.isValid() and owner.value()
    message=QDBusMessage.createMethodCall('org.kde.kglobalaccel','/kglobalaccel','org.kde.KGlobalAccel','allActionsForComponent')
    message.setArguments([QDBusArgument(['org.lookup.Linux.desktop','','',''],QMetaType.Type.QStringList.value)])
    reply=bus.call(message,QDBus.CallMode.Block,1200)
    if reply.type()==QDBusMessage.MessageType.ErrorMessage:raise RuntimeError('registry_unavailable')
    actions=reply.arguments()[0] if reply.arguments() else [];keys=[]
    for action in actions or []:
        if tuple(action[:2])!=('org.lookup.Linux.desktop','_launch'):continue
        message=QDBusMessage.createMethodCall('org.kde.kglobalaccel','/kglobalaccel','org.kde.KGlobalAccel','shortcut')
        message.setArguments([QDBusArgument(action,QMetaType.Type.QStringList.value)]);reply=bus.call(message,QDBus.CallMode.Block,1200)
        if reply.type()==QDBusMessage.MessageType.ErrorMessage:raise RuntimeError('registry_unavailable')
        keys.extend(QKeySequence(key).toString(QKeySequence.SequenceFormat.PortableText) for key in reply.arguments()[0] if key)
    result=dict(owner=bool(present),keys=keys,at_ns=time.monotonic_ns())
    if present:
        pid=interface.servicePid(SERVICE).value();directory=Path('/proc',str(pid));ticks=int((directory/'stat').read_text().split(') ',1)[1].split()[19])
        result['process']=dict(pid=pid,uid=directory.stat().st_uid,start_ns=ticks*1_000_000_000//os.sysconf('SC_CLK_TCK'),
            argv=[arg.decode() for arg in (directory/'cmdline').read_bytes().split(b'\0') if arg])
    sessions=subprocess.run(['loginctl','list-sessions','--no-legend'],capture_output=True,text=True,timeout=3,check=True).stdout
    result['sessions']=[]
    for line in sessions.splitlines():
        fields=line.split()
        if len(fields)>3 and fields[1:4]==[str(UID),USER,'seat0']:
            value=subprocess.run(['loginctl','show-session',fields[0],'-p','Id','-p','Type','-p','Service','-p','TimestampMonotonic'],capture_output=True,text=True,timeout=3,check=True).stdout
            result['sessions'].append(dict(row.split('=',1) for row in value.splitlines() if '=' in row))
    return result


def retention():
    import hashlib,sqlite3
    environment();paths=dict(config=HOME/'.config/lookup/config.json',database=HOME/'.local/share/lookup/lookup.db',
        unrelated=HOME/'.local/share/applications/lookup-gsd-08-unrelated.desktop')
    result=dict(hashes={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in paths.items()})
    with sqlite3.connect('file:'+str(paths['database'])+'?mode=ro',uri=True) as conn:
        result['seed_word']=conn.execute('SELECT word,count,context FROM words WHERE word=?',('publicseed',)).fetchone()
        result['seed_card']=conn.execute('SELECT word,translation,context,due,repetitions FROM cards WHERE word=?',('publicseed',)).fetchone()
        result['bank']=conn.execute('SELECT word,count,context FROM words WHERE word=?',('bank',)).fetchone()
        result['integrity']=conn.execute('PRAGMA integrity_check').fetchone()[0]
    marker=STATE/'unrelated-trigger';result['unrelated_marker_ns']=marker.stat().st_mtime_ns if marker.exists() else None
    return result


def native_action(value):
    import sys
    env=environment();action=value['action'];STATE.mkdir(parents=True,exist_ok=True)
    if action=='seed':
        sys.path.insert(0,'/usr/lib/lookup/app');from lookup import config,store,learning
        config.save(dict(online=False,autostart=True,shortcut='Meta+Shift+D',popup_timeout=60))
        with store.open_store() as conn:
            store.upsert_word(conn,'publicseed','сохранить','Public retention fixture08.')
            learning.add_card(conn,dict(word='publicseed',translation='сохранить',context='Public retention fixture08.'))
        desktop=HOME/'.local/share/applications/lookup-gsd-08-unrelated.desktop';desktop.parent.mkdir(parents=True,exist_ok=True)
        desktop.write_text('[Desktop Entry]\nType=Application\nName=Public unrelated08 key\nExec=/usr/bin/touch '+str(STATE/'unrelated-trigger')+
            '\nX-KDE-Shortcuts=Meta+Shift+U\nNoDisplay=true\n')
        refresh=subprocess.run(['kbuildsycoca6'],env=env,capture_output=True,text=True,timeout=15,check=True)
        return dict(seeded=True,refresh_exit=refresh.returncode,retention=retention())
    if action=='autostart':
        sys.path.insert(0,'/usr/lib/lookup/app');from lookup import config
        config.save(dict(autostart=value['enabled']));return dict(autostart=config.load().autostart)
    if action=='start':
        if status()['owner']:raise RuntimeError('existing_owner')
        children=[]
        for name,argv in (('fixture',[sys.executable,str(Path(__file__).resolve()),'--fixture']),('lookup',['/usr/bin/lookup','--app'])):
            with (STATE/(name+'.log')).open('w') as output:
                child=subprocess.Popen(argv,env=env,cwd='/tmp',stdin=subprocess.DEVNULL,stdout=output,stderr=output,start_new_session=True)
            children.append(dict(kind=name,pid=child.pid,start=int(Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split()[19])))
        records=STATE/'children.json'
        if records.exists():records.rename(STATE/('children-previous-'+str(time.monotonic_ns())+'.json'))
        records.write_text(json.dumps(children));return dict(children=children)
    if action=='quit':
        current=status()
        if not current['owner']:return dict(stopped=True,already_absent=True)
        process=current['process']
        if process['uid']!=UID or '/usr/bin/lookup' not in process['argv']:raise RuntimeError('unowned_owner')
        from PyQt6.QtDBus import QDBusConnection
        interface=QDBusConnection.sessionBus().interface()
        items=subprocess.run(['qdbus6','org.kde.StatusNotifierWatcher','/StatusNotifierWatcher','org.kde.StatusNotifierWatcher.RegisteredStatusNotifierItems'],env=env,capture_output=True,text=True,timeout=3,check=True).stdout.split()
        for item in items:
            service=item.split('/StatusNotifierItem')[0]
            if interface.servicePid(service).value()==process['pid']:
                subprocess.run(['qdbus6',service,'/MenuBar','com.canonical.dbusmenu.Event','5','clicked','0','0'],env=env,capture_output=True,timeout=3,check=True)
        deadline=time.monotonic()+6
        while time.monotonic()<deadline:
            if not interface.isServiceRegistered(SERVICE).value():return dict(stopped=True,process=process,method='actual tray Exit')
            time.sleep(.05)
        raise TimeoutError('tray_exit_deadline')
    if action=='retention':return retention()
    if action=='stop-fixture':
        import signal
        records=json.loads((STATE/'children.json').read_text());result=[]
        for row in records:
            if row['kind']!='fixture':continue
            path=Path('/proc',str(row['pid']))
            if path.exists():
                if path.stat().st_uid!=UID or int((path/'stat').read_text().split(') ',1)[1].split()[19])!=row['start']:raise RuntimeError('fixture_identity_changed')
                os.kill(row['pid'],signal.SIGTERM)
            result.append(row['pid'])
        return dict(stopped=result)
    if action=='snapshot':
        import base64,hashlib
        sys.path.insert(0,'/usr/lib/lookup/app');from lookup import capture,platform
        env=platform.session_env();os.environ.update(env)
        from PyQt6.QtGui import QGuiApplication
        application=QGuiApplication([]);application.setDesktopFileName('org.lookup.Linux')
        monitor=platform.monitors(env)[0];frame=capture.capture_monitor(monitor,env)
        optical=subprocess.run(['tesseract','stdin','stdout','-l','eng+rus','--psm','11'],input=frame.png,capture_output=True,timeout=8,check=True).stdout.decode()
        return dict(at_ns=time.monotonic_ns(),sha256=hashlib.sha256(frame.png).hexdigest(),png_base64=base64.b64encode(frame.png).decode(),
            optical=optical,cursor=platform.cursor_position(env),retention=retention())
    if action=='selection':
        result=subprocess.run(['wl-paste','--primary','--no-newline'],env=env,capture_output=True,timeout=3)
        return dict(primary_absent=result.returncode==1,exit=result.returncode)
    if action=='installed':
        import hashlib
        files=('/usr/bin/lookup','/usr/lib/lookup/kdotool','/usr/share/applications/org.lookup.Linux.desktop',
            '/etc/xdg/autostart/org.lookup.Linux.desktop','/usr/share/lookup/dicts/mueller7/mueller7.ifo')
        results={name:dict(exists=Path(name).is_file(),sha256=hashlib.sha256(Path(name).read_bytes()).hexdigest() if Path(name).is_file() else None) for name in files}
        child=subprocess.run(['/usr/bin/lookup','--word','bank','--offline','--no-save'],env=env,cwd='/tmp',capture_output=True,text=True,timeout=15)
        desktop=Path('/usr/share/applications/org.lookup.Linux.desktop').read_text()
        return dict(files=results,cwd='/tmp',pythonpath_present='PYTHONPATH' in env,mueller_exit=child.returncode,
            mueller_output=child.stdout,desktop=desktop,package=subprocess.run(['pacman','-Q','lookup-linux'],capture_output=True,text=True,check=True).stdout.strip())
    if action=='removed':
        files=[str(path) for path in (Path('/usr/bin/lookup'),Path('/usr/lib/lookup'),Path('/usr/share/lookup'),
            Path('/usr/share/applications/org.lookup.Linux.desktop'),Path('/etc/xdg/autostart/org.lookup.Linux.desktop')) if path.exists()]
        return dict(status=status(),remaining_package_files=files,retention=retention(),package_installed=subprocess.run(['pacman','-Q','lookup-linux'],capture_output=True).returncode==0)
    if action=='refresh':
        result=subprocess.run(['kbuildsycoca6'],env=env,capture_output=True,text=True,timeout=15)
        return dict(exit=result.returncode,diagnostic=result.stderr[:1000])
    raise ValueError('unknown_action')


def fixture():
    env=environment();os.environ.update(env)
    from PyQt6.QtWidgets import QApplication,QLabel,QWidget,QVBoxLayout
    from PyQt6.QtCore import Qt
    application=QApplication([]);window=QWidget();window.setWindowTitle('Public install08 OCR fixture')
    window.setGeometry(100,100,1000,450);layout=QVBoxLayout(window)
    label=QLabel('They waited by the bank of the river.');font=label.font();font.setPointSize(26);label.setFont(font)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction);layout.addWidget(label)
    window.show();application.processEvents();metrics=label.fontMetrics();point=label.mapToGlobal(label.rect().topLeft())
    x=point.x()+metrics.horizontalAdvance('They waited by the ')+metrics.horizontalAdvance('bank')//2
    y=point.y()+label.height()//2
    (STATE/'fixture.json').write_text(json.dumps(dict(point=[x,y],text=label.text(),pid=os.getpid())))
    return application.exec()


if __name__=='__main__':
    import argparse,base64
    parser=argparse.ArgumentParser();parser.add_argument('--guest');parser.add_argument('--fixture',action='store_true');args=parser.parse_args()
    if args.fixture:raise SystemExit(fixture())
    if args.guest:
        value=json.loads(base64.b64decode(args.guest))
        if value['action']=='inventory':result=inventory()
        elif value['action']=='status':result=status()
        else:result=native_action(value)
        print(json.dumps(result))
