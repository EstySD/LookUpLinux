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
        if len(samples)<2:return False
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
            elif sample['owner'] is not False:return False
        if last!=data['observed_until_ns'] or owners!=list(identities.values()):return False
        return (data['enabled'] is False and not identities or data['enabled'] is True and len(identities)==1)
    except (KeyError,TypeError,AttributeError,IndexError):return False


def install_report(data):
    try:
        gates=data['gates'];cleanup=data['cleanup']
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
            and preservation and inactive and unrelated and package and useful
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
