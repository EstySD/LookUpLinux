"""Actual-product KDE probe and strict evidence validation; fixtures are public."""
import argparse
import ast
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

EXITS=('escape','close','reinvoke','timeout','fault','external_focus','process_exit')
CLEANUP=('owned_processes_stopped','profiles_restored','bindings_restored','original_untouched')
PRODUCT_FILES=('lookup/app.py','lookup/gui.py','lookup/platform.py','lookup/selection_gui.py','lookup/ocr.py')


def _input(value,pid):
    rows=[value[key] for key in ('before','during','after')]
    return (all(type(row['pid']) is int and row['pid']==pid and type(row['count']) is int and row['count']>=0 for row in rows)
            and rows[0]['count']==rows[1]['count']<rows[2]['count']
            and type(value['layer_events']) is int and value['layer_events']>=2 and value['closed'] is True)


def accepted(value):
    """Only complete, internally consistent product observations pass."""
    try:
        if value['mode']!='native-product' or not set(PRODUCT_FILES).issubset(value['inventory']):return False
        if not all(isinstance(name,str) and re.fullmatch('[0-9a-f]{64}',digest)
                   for name,digest in value['inventory'].items()):return False
        if not all(isinstance(value['versions'][key],str) and value['versions'][key] for key in ('kwin','qt','game')):return False
        fixture=value['fixture'];selections=fixture['selections']
        if type(fixture['pid']) is not int or fixture['pid']<=0 or not re.fullmatch('[0-9a-f]{64}',fixture['frame']):return False
        if not fixture['hover'] or not fixture['source_ticks'][0]<fixture['source_ticks'][1]:return False
        if len(selections)<3 or len({row['word'] for row in selections})<3:return False
        if not all(row['frame']==fixture['frame'] and row['session']==selections[0]['session']
                   and row['word'] and row['translation'] for row in selections):return False
        if not all(type(row['id']) is int and row['id']>0 and type(row['session']) is int and row['session']>0 for row in selections):return False
        if not all(a['id']<b['id'] for a,b in zip(selections,selections[1:])):return False
        if not _input(fixture['input'],fixture['pid']):return False
        game=value['game']
        if type(game['pid']) is not int or game['pid']<=0:return False
        pids=game.get('pids',[game['pid']])
        if not pids or not all(type(pid) is int and pid>0 for pid in pids) or game['pid'] not in pids:return False
        if not all(game['exits'][name]['before']['pid'] in pids and
                   _input(game['exits'][name],game['exits'][name]['before']['pid']) for name in EXITS):return False
        if value['primary']['mode']!='primary' or value['primary']['scene'] is not False or not value['primary']['key']:return False
        return (value['no_hit_usable'] is True and value['internal_focus'] is True
                and {1,1.25,2}.issubset(value['scales'])
                and all(value['cleanup'][name] is True for name in CLEANUP))
    except (KeyError,TypeError,ValueError,IndexError):return False


def inventory(directory):
    root=Path(directory)
    return {str(path.relative_to(root)).replace('\\','/'):hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((root/'lookup').rglob('*')) if path.is_file() and path.suffix in ('.py','.txt')}


def write(path,value):
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8');temporary.replace(path)


def environment():
    if os.getuid()!=1001 or Path.home()!=Path('/home/lookup07'):raise RuntimeError('owned_user_required')
    from lookup import platform
    os.environ.update(platform.session_env())
    for key in ('SUDO_UID','SUDO_GID','SUDO_USER','SUDO_COMMAND'):os.environ.pop(key,None)


def product(root):
    """Observe the real GUI/Engine; only test-only fault injection changes behavior."""
    environment()
    from PyQt6.QtCore import QTimer,QT_VERSION_STR
    from lookup import gui,app as core
    root.mkdir(parents=True,exist_ok=True)
    state={'pid':os.getpid(),'events':[],'inventory':inventory(Path(core.__file__).resolve().parents[1]),'qt':QT_VERSION_STR}
    Popup,Owner=gui.components();receive=Owner.receive;initialize=Owner.__init__;resolve=core.Source.resolve
    owners=[];fault=[False]
    def observed(self,event):
        row=dict(id=event.id,stage=event.stage,mode=event.mode,error=event.error,point=event.point)
        if event.scene is not None:
            image=event.scene.source.image
            row.update(session=event.scene.session_id,frame=hashlib.sha256(image.png).hexdigest())
            (root/'capture.png').write_bytes(image.png)
            state['frame']=row['frame'];state['session']=row['session']
        if event.result is not None:
            row.update(word=event.result.key,translation=event.result.translation)
        state['events'].append(row)
        receive(self,event)
    def resolving(self,*args,**kwargs):
        if fault[0]:fault[0]=False;raise core.AppError('ocr_failed')
        return resolve(self,*args,**kwargs)
    def init(self,*args,**kwargs):
        initialize(self,*args,**kwargs);owners.append(self)
        timer=QTimer(self)
        def poll():
            command=root/'command.json'
            if command.exists():
                value=json.loads(command.read_text());command.unlink();action=value['action']
                if action=='fault':fault[0]=True
                elif action=='close' and self.scene_window is not None:self.scene_window.close_button.click()
                elif action=='quit':self.quit()
                elif action=='settings':self.open_settings()
                elif action=='card':self.popup.card_button.click()
                elif action=='timeout':self.popup.timer.setInterval(600);self.popup.timer.start()
            layer=self.scene_window
            state.update(layer=bool(layer is not None and layer.isVisible()),popup=self.popup.isVisible(),
                title=self.popup.title.text(),scene_id=self._scene_id,
                card_status=self.popup.card_status.text(),timer=self.popup.timer.isActive(),popup_uuid=self.popup_uuid,
                configured_timeout=self._popup_timeout,timer_interval=self.popup.timer.interval(),
                timer_remaining=self.popup.timer.remainingTime())
            if layer is not None:
                state['layer_geometry']=[layer.x(),layer.y(),layer.width(),layer.height()]
                state['close']=[layer.close_button.mapToGlobal(layer.close_button.rect().center()).x(),
                                layer.close_button.mapToGlobal(layer.close_button.rect().center()).y()]
            write(root/'state.json',state)
        timer.timeout.connect(poll);timer.start(100);self._probe_timer=timer
        QTimer.singleShot(600000,self.quit)
        signal.signal(signal.SIGTERM,lambda *_:self.quit())
    Owner.receive=observed;Owner.__init__=init;core.Source.resolve=resolving
    try:return gui.run()
    finally:
        state['stopped']=True;write(root/'state.json',state)


def source(root,game=False):
    environment()
    from PyQt6.QtCore import Qt,QTimer
    from PyQt6.QtGui import QPainter,QFont
    from PyQt6.QtWidgets import QApplication,QWidget,QToolTip
    root.mkdir(parents=True,exist_ok=True)
    state={'pid':os.getpid(),'motion':0,'click':0,'ticks':0};child=None
    application=QApplication([]);application.setQuitOnLastWindowClosed(False)
    class Fixture(QWidget):
        def __init__(self):
            super().__init__();self.setMouseTracking(True);self.setWindowTitle('Phase11 product source');self.setFont(QFont('Sans Serif',24))
        def paintEvent(self,event):
            painter=QPainter(self);painter.fillRect(self.rect(),Qt.GlobalColor.white);painter.setPen(Qt.GlobalColor.black);painter.setFont(self.font())
            painter.drawText(150,200,'The bright river flows.');painter.drawText(150,300,'Frame '+str(state['ticks']))
        def mouseMoveEvent(self,event):
            state['motion']+=1;QToolTip.showText(event.globalPosition().toPoint(),'Captured hover vocabulary',self)
        def mousePressEvent(self,event):state['click']+=1
    fixture=Fixture()
    if game:
        # Reuse the research observer's exact source, not its substitute Layer.
        tree=ast.parse(Path(__file__).with_name('check_frozen_selection.py').read_text())
        code=next(node.args[0].value for node in ast.walk(tree) if isinstance(node,ast.Call)
            and isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name)
            and node.func.value.id=='observer' and node.func.attr=='write_text')
        (root/'observer.c').write_text(code)
        flags=subprocess.check_output(['pkg-config','--cflags','--libs','sdl2'],text=True).split()
        subprocess.run(['cc','-shared','-fPIC',str(root/'observer.c'),'-o',str(root/'observer.so'),'-ldl',*flags],check=True)
        child=subprocess.Popen(['wesnoth','--fullscreen','--language','en_US','--userdata-dir',str(root/'userdata'),
            '--usercache-dir',str(root/'cache'),'--userconfig-dir',str(root/'config'),'--nomusic','--nosound','--noaddons'],
            env=dict(os.environ,SDL_VIDEODRIVER='wayland',LD_PRELOAD=str(root/'observer.so'),PROBE_SDL_LOG=str(root/'events.log')),
            stdout=open(root/'game.log','w'),stderr=subprocess.STDOUT)
        state['pid']=child.pid
    else:fixture.showFullScreen()
    def poll():
        state['ticks']+=1;fixture.update();log=root/'events.log'
        state['count']=len(log.read_text().splitlines()) if log.exists() else state['motion']+state['click']
        write(root/'state.json',state)
        command=root/'command.json'
        if command.exists():
            action=json.loads(command.read_text())['action'];command.unlink()
            if action=='quit':application.quit()
            elif action=='focus':fixture.raise_();fixture.activateWindow()
    timer=QTimer();timer.timeout.connect(poll);timer.start(100);QTimer.singleShot(900000,application.quit)
    signal.signal(signal.SIGTERM,lambda *_:application.quit())
    try:return application.exec()
    finally:
        if child is not None:
            child.terminate()
            try:child.wait(timeout=8)
            except subprocess.TimeoutExpired:child.kill();child.wait()
        state['stopped']=True;write(root/'state.json',state)


def control(root,action):
    """Private owned-clone launch/collection, with no commands for other VMs."""
    environment();root.mkdir(parents=True,exist_ok=True);root.chmod(0o700)
    snapshot=Path(__file__).resolve().parents[1];record=root/'baseline.json'
    if action=='prepare':
        if record.exists():raise RuntimeError('baseline_already_exists')
        from PyQt6.QtCore import QCoreApplication
        from PyQt6.QtDBus import QDBusConnection
        from lookup import lifecycle
        application=QCoreApplication([]);interface=QDBusConnection.sessionBus().interface()
        reply=interface.servicePid('org.lookup.Linux');old_pid=reply.value() if reply.isValid() else None
        files={}
        for relative in ('.config/lookup/config.json','.local/share/applications/org.lookup.Linux.desktop','.config/autostart/org.lookup.Linux.desktop'):
            path=Path.home()/relative
            if path.exists():
                backup=root/('backup-'+str(len(files)));backup.write_bytes(path.read_bytes());backup.chmod(0o600)
                files[relative]=dict(backup=str(backup),sha=hashlib.sha256(path.read_bytes()).hexdigest(),mode=path.stat().st_mode&0o777)
            else:files[relative]=None
        primary=subprocess.run(['wl-paste','--primary','--no-newline'],capture_output=True,timeout=3)
        if len(primary.stdout)>1<<20:raise RuntimeError('primary_too_large_to_preserve')
        (root/'primary.backup').write_bytes(primary.stdout);(root/'primary.backup').chmod(0o600)
        keys=lifecycle.inspect_shortcut().keys
        baseline=dict(old_pid=old_pid,files=files,keys=[lifecycle.key_text(key) for key in keys],primary=primary.returncode==0)
        write(record,baseline)
        if old_pid:
            command=Path('/proc')/str(old_pid)/'cmdline'
            if b'lookup' not in command.read_bytes():raise RuntimeError('unexpected_bus_owner')
            os.kill(old_pid,signal.SIGTERM);time.sleep(1)
        # A public invalid token avoids Klipper refilling an empty selection.
        subprocess.run(['wl-copy','--primary'],input=b'0',check=True,timeout=3,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        dictionaries=root/'dicts';dictionaries.mkdir(exist_ok=True)
        (dictionaries/'public.dsl').write_text('#NAME "Phase11 public"\n#INDEX_LANGUAGE "English"\n#CONTENTS_LANGUAGE "Russian"\nbright\n    яркий\nriver\n    река\nvocabulary\n    словарь\nCaptured\n    сохранённый\nhover\n    наведение\nflows\n    течёт\n',encoding='utf-16')
        write(root/'config.json',dict(online=False,popup_timeout=60,autostart=False,shortcut=baseline['keys'][0] if baseline['keys'] else 'Meta+Shift+D'))
        return dict(prepared=True,keys=baseline['keys'],old_owner=old_pid,inventory=inventory(snapshot))
    if action in ('product','source','game'):
        directory=root/action;directory.mkdir(exist_ok=True)
        env=dict(os.environ,PYTHONPATH=str(snapshot),QT_QPA_PLATFORM='wayland',LOOKUP_CONFIG=str(root/'config.json'),
            LOOKUP_DICTS=str(root/'dicts'),LOOKUP_DB=str(root/'lookup.db'),LOOKUP_CACHE=str(root/'cache'))
        command=[sys.executable,str(Path(__file__).resolve()),'--product' if action=='product' else '--source',str(directory)]
        if action=='game':command.append('--game')
        child=subprocess.Popen(['timeout','--kill-after=10s','900s',*command],env=env,stdout=open(directory/'run.log','a'),stderr=subprocess.STDOUT,start_new_session=True)
        write(directory/'process.json',dict(pid=child.pid));return dict(started=action,pid=child.pid)
    if action in ('status','brief'):
        values={name:json.loads((root/name/'state.json').read_text()) if (root/name/'state.json').exists() else None for name in ('product','source','game')}
        if action=='brief' and values['product']:
            values['product'].pop('inventory',None);values['product']['events']=values['product']['events'][-6:]
        return values
    if action=='diagnose':
        from lookup import platform,ocr
        current=json.loads((root/'product/state.json').read_text());pid=current['pid']
        identifiers=platform.run(['kdotool','search','--all','--pid',str(pid)],os.environ).decode().split()
        geometry={identifier:platform.run(['kdotool','getwindowgeometry',identifier],os.environ).decode() for identifier in identifiers}
        rejected={}
        for name in ('source','game'):
            path=root/name/'state.json'
            if path.exists():
                foreign=json.loads(path.read_text())['pid']
                windows=platform.run(['kdotool','search','--all','--pid',str(foreign)],os.environ).decode().split()
                if windows:
                    try:platform.window_geometry(os.environ,pid,windows[0]);rejected[name]=False
                    except platform.PlatformError as error:rejected[name]=error.reason=='invalid_owner'
        words={}
        for point in ((270,190),(265,280)):
            result=ocr.recognize_image((root/'product/capture.png').read_bytes(),point)
            words[str(point)]=result.selection.word if result.selection else None
        return dict(geometry=geometry,words=words,foreign_rejected=rejected)
    if action=='stop':
        for name in ('product','source','game'):
            path=root/name/'process.json'
            if path.exists():
                pid=json.loads(path.read_text())['pid'];command=Path('/proc')/str(pid)/'cmdline'
                if command.exists() and str(root).encode() in command.read_bytes():
                    os.killpg(pid,signal.SIGTERM)
        time.sleep(2);baseline=json.loads(record.read_text())
        for relative,item in baseline['files'].items():
            path=Path.home()/relative
            if item is None:
                if path.exists():path.unlink()
            else:path.write_bytes(Path(item['backup']).read_bytes());path.chmod(item['mode'])
        if baseline['primary']:subprocess.run(['wl-copy','--primary'],input=(root/'primary.backup').read_bytes(),check=True,timeout=3,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        else:subprocess.run(['wl-copy','--primary','--clear'],check=True,timeout=3)
        if baseline['old_pid']:
            env=dict(os.environ);env.pop('PYTHONPATH',None)
            subprocess.Popen(['/usr/bin/lookup','--autostart'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
        return dict(restored=True,profiles={relative:(not (Path.home()/relative).exists() if item is None else hashlib.sha256((Path.home()/relative).read_bytes()).hexdigest()==item['sha']) for relative,item in baseline['files'].items()})
    target,command=action.split(':',1)
    if target not in ('product','source','game'):raise ValueError('invalid_target')
    write(root/target/'command.json',{'action':command});return dict(sent=action)


def host_batch(output,cases=EXITS,run_target=True):
    """One bounded Windows batch; preserve all failures and finish independent checks.

    Disable this clone's shared clipboard before preparing PRIMARY; restore its
    original clipboard mode only after the root agent has powered the clone off.
    """
    root=Path(__file__).resolve().parents[1]
    output.mkdir(parents=True,exist_ok=True)
    guard=root/'tools/check_package_vm.ps1'
    ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','HostKeyAlias=lookup-gsd-07',
         '-o','UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-p','2227','archvm']
    guest='/tmp/lookup-frozen-product-11/run-batch-'+str(int(time.time()))
    snapshot='/tmp/lookup-frozen-product-11/snapshot'
    prelude="from pathlib import Path\nimport os,json,time,signal,subprocess\nfrom tools.check_frozen_product import control,write,environment\nenvironment()\nr=Path('"+guest+"')\n"
    report={'mode':'native-product-batch','cases':{},'started':time.time(),'errors':[],'guest_root':guest}
    def remote(code,timeout=25):
        encoded=base64.b64encode((prelude+code).encode()).decode()
        command='echo '+encoded+' | base64 -d | sudo -n -H -u lookup07 env PYTHONPATH='+snapshot+' python -'
        result=subprocess.run([*ssh,command],capture_output=True,text=True,timeout=timeout)
        if result.returncode:raise RuntimeError(result.stderr[-2000:] or result.stdout[-2000:])
        return json.loads(result.stdout)
    def physical(action,**values):
        command=['powershell','-NoProfile','-File',str(guard),'-Action',action]
        for key,value in values.items():command.extend(('-'+key,str(value)))
        result=subprocess.run(command,capture_output=True,text=True,timeout=20)
        if result.returncode:raise RuntimeError(result.stderr[-1500:])
    def pointer(x,y,button=0):physical('Pointer',X=x,Y=y,Buttons=button)
    def click(x,y):pointer(x,y,1);pointer(x,y);time.sleep(.35)
    def key(codes):physical('Keys',Codes=codes)
    hotkey=lambda:key('e0 5b 2a 12 92 aa e0 db')
    escape=lambda:key('01 81')
    def state():return remote("print(json.dumps(control(r,'status')))\n")
    def wait(predicate,limit=12):
        until=time.monotonic()+limit
        while time.monotonic()<until:
            value=state()
            if predicate(value):return value
            time.sleep(.2)
        raise RuntimeError('bounded_state_wait_expired')
    def save(label):
        return remote("v=control(r,'status');write(r/'evidence'/'"+label+".json',v);print(json.dumps(v))\n")
    def restart(seconds=60):
        remote("c=json.loads((r/'config.json').read_text());c['popup_timeout']="+str(seconds)+";write(r/'config.json',c);control(r,'product:quit') if (r/'product/state.json').exists() else None;time.sleep(.7);print(json.dumps(control(r,'product')))\n")
        wait(lambda v:v['product'] and not v['product'].get('stopped') and v['product'].get('configured_timeout')==seconds)
        remote("subprocess.run(['wl-copy','--primary'],input=b'0',check=True,timeout=3,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);print(json.dumps({'public_invalid_primary':True}))\n")
    def observer_count(value):return {'pid':value['game']['pid'],'count':value['game']['count']}
    # The existing source fixture has completed; give this batch a fresh bounded game.
    try:
        physical('Check')
        machine=subprocess.check_output(['C:/Program Files/Oracle/VirtualBox/VBoxManage.exe','showvminfo',
            'cf207909-94b5-4b49-8bd8-ccff973c1dc8','--machinereadable'],text=True)
        if 'clipboard="disabled"' not in machine:raise RuntimeError('disable_owned_clone_clipboard_before_preparing_PRIMARY')
        subprocess.run([*ssh,'sudo -n install -d -m 700 -o lookup07 -g lookup07 '+guest],check=True,capture_output=True,timeout=15)
        remote("v=control(r,'prepare') if not (r/'baseline.json').exists() else {'prepared':True};print(json.dumps({'prepared':v['prepared']}))\n")
        remote("(r/'evidence').mkdir(exist_ok=True);control(r,'game:quit') if (r/'game/state.json').exists() else None;time.sleep(.7);p=r/'game/events.log';p.rename(r/'evidence/game-events-prior.log') if p.exists() else None;print(json.dumps(control(r,'game')))\n")
        time.sleep(3)
        restart()
        for name in cases:
            case={'status':'failed'}
            try:
                if name=='timeout':restart(10)
                elif name=='fault':restart(60)
                pointer(500,200);pointer(520,220);time.sleep(.35);hotkey()
                wait(lambda v:v['product']['layer'])
                wait(lambda v:not v['product']['layer'] or v['product']['events'][-1]['stage'] in ('error','ready','context'))
                before=save('batch-game-'+name+'-before')
                if name=='timeout':
                    report['ownership']=remote("from lookup import platform\nv=control(r,'status');p=v['product']['pid'];g=v['game']['pid'];u=platform.owned_window(os.environ,g)[0];owned=platform.owned_window(os.environ,p);bad=False\ntry:platform.window_geometry(os.environ,p,u)\nexcept platform.PlatformError as error:bad=error.reason=='invalid_owner'\nprint(json.dumps({'foreign_rejected':bad,'foreign_uuid':u,'owned':owned,'windows':[{'uuid':x,'name':platform.run(['kdotool','getwindowname',x],os.environ).decode().strip(),'geometry':platform.window_geometry(os.environ,p,x)} for x in owned]}))\n")
                for x,y in ((5,5),(640,5),(1275,5),(1275,400),(1275,795),(640,795),(5,795),(5,400)):pointer(x,y)
                for x,y in ((900,650),(800,700)):
                    previous=state()['product']['events'][-1]['id'];click(x,y)
                    wait(lambda v:not v['product']['layer'] or (v['product']['events'][-1]['id']>previous and v['product']['events'][-1]['stage'] in ('error','ready','context')))
                # Measure timeout after the last OCR result, not while OCR can reset it.
                wait(lambda v:not v['product']['layer'] or v['product']['events'][-1]['stage'] in ('error','ready','context'))
                during=save('batch-game-'+name+'-during')
                events=sum(e['stage']=='frozen' and e['id']>before['product']['events'][-1]['id'] for e in during['product']['events'])
                case.update(before=observer_count(before),during=observer_count(during),layer_events=events,
                    frame_before=before['product']['frame'],frame_during=during['product']['frame'],
                    session_before=before['product']['scene_id'],session_during=during['product']['scene_id'])
                if name=='escape':escape()
                elif name=='close':click(*during['product']['close'])
                elif name=='reinvoke':hotkey()
                elif name=='timeout':pass
                elif name=='fault':
                    remote("print(json.dumps(control(r,'product:fault')))\n");click(950,650)
                elif name=='external_focus':
                    remote("from lookup import platform\nv=control(r,'status');p=v['game']['pid'];u=platform.owned_window(os.environ,p)[0];platform.window_action(os.environ,p,u,'windowactivate');print(json.dumps({'activated':p}))\n")
                else:
                    remote("v=control(r,'status');p=v['product']['pid'];os.kill(p,signal.SIGKILL);print(json.dumps({'killed':p}))\n")
                if name=='process_exit':
                    time.sleep(.5)
                    closed=remote("v=control(r,'status');p=v['product']['pid'];print(json.dumps(not Path('/proc',str(p)).exists()))\n")
                else:closed=not wait(lambda v:not v['product']['layer'],limit=14)['product']['layer']
                pointer(400,400);pointer(420,420);time.sleep(.4)
                after=save('batch-game-'+name+'-after');case.update(after=observer_count(after),closed=closed)
                case['status']='passed' if (_input(case,case['before']['pid']) and case['frame_before']==case['frame_during']
                    and case['session_before']==case['session_during']) else 'failed'
            except Exception as error:
                case['error']=str(error)[-2000:]
            report['cases'][name]=case
            write(output/'11-native-batch.json',report)
            # A failed independent case must not prevent later cleanup/exit checks.
            if name!='process_exit':
                try:escape();time.sleep(.2)
                except Exception as error:report['errors'].append(str(error)[-500:])
        remote("[control(r,name+':quit') for name in ('game','source','product') if (r/name/'state.json').exists()];time.sleep(1);print(json.dumps({'stopped':True}))\n")
        # Offscreen regressions cannot steal focus or generate physical input.
        test_code="env=dict(os.environ,QT_QPA_PLATFORM='offscreen',XDG_CONFIG_HOME=str(r/'regression-config'),XDG_DATA_HOME=str(r/'regression-data'),XDG_CACHE_HOME=str(r/'regression-cache'));result=subprocess.run([os.sys.executable,'-m','unittest','discover','-s','tests','-q'],cwd='"+snapshot+"',env=env,capture_output=True,text=True,timeout=180);write(r/'evidence'/'target-tests.json',{'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr});print(json.dumps({'returncode':result.returncode,'tail':result.stderr.splitlines()[-6:]}))\n"
        if run_target:report['target_tests']=remote(test_code,timeout=195)
        else:report['target_tests']={'reused':'../11-native-batch.json','not_repeated':True}
        result=subprocess.run([sys.executable,'-m','unittest','tests.test_frozen_product','-q'],cwd=root,capture_output=True,text=True,timeout=30)
        report['validator_tests']={'returncode':result.returncode,'tail':result.stderr.splitlines()[-5:]}
    except Exception as error:report['errors'].append(str(error)[-2000:])
    finally:
        try:report['cleanup']=remote("print(json.dumps(control(r,'stop')))\n",timeout=25)
        except Exception as error:report['cleanup_error']=str(error)[-2000:]
        try:
            remote("import tarfile\np=Path('/tmp/lookup-frozen-product-11-evidence.tar.gz')\nwith tarfile.open(p,'w:gz') as archive:\n archive.add(r/'evidence',arcname='evidence')\n archive.add(r/'game/events.log',arcname='game-events.log')\nprint(json.dumps({'archive':str(p)}))\n")
            subprocess.run(['scp','-o','BatchMode=yes','-o','HostKeyAlias=lookup-gsd-07',
                '-o','UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-P','2227',
                'archvm:/tmp/lookup-frozen-product-11-evidence.tar.gz',str(output/'11-native-raw.tar.gz')],check=True,timeout=30)
        except Exception as error:report['collection_error']=str(error)[-2000:]
        report['finished']=time.time();report['clipboard_restore_after_poweroff']='bidirectional'
        write(output/'11-native-batch.json',report)
    print(json.dumps({'cases':{k:v['status'] for k,v in report['cases'].items()},
        'target_tests':report.get('target_tests'),'errors':report['errors'],'cleanup_error':report.get('cleanup_error'),
        'collection_error':report.get('collection_error'),'report':str(output/'11-native-batch.json')}))
    return 0 if len(report['cases'])==len(cases) and all(v['status']=='passed' for v in report['cases'].values()) and (not run_target or report.get('target_tests',{}).get('returncode')==0) and report.get('validator_tests',{}).get('returncode')==0 and not report['errors'] and 'cleanup_error' not in report else 1


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--validate',type=Path);parser.add_argument('--product',type=Path)
    parser.add_argument('--source',type=Path);parser.add_argument('--game',action='store_true')
    parser.add_argument('--control',type=Path);parser.add_argument('--action');parser.add_argument('--host-batch',type=Path)
    parser.add_argument('--host-cases',nargs='+',choices=EXITS);parser.add_argument('--skip-target-tests',action='store_true');args=parser.parse_args()
    if args.host_batch:return host_batch(args.host_batch,args.host_cases or EXITS,not args.skip_target_tests)
    if args.validate:
        result=accepted(json.loads(args.validate.read_text(encoding='utf-8-sig')));print(json.dumps({'accepted':result}));return 0 if result else 1
    if args.product:return product(args.product)
    if args.source:return source(args.source,args.game)
    if args.control:print(json.dumps(control(args.control,args.action),ensure_ascii=False));return 0
    parser.error('choose --validate, --product or --source')


if __name__=='__main__':raise SystemExit(main())
