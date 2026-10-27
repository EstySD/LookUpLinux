"""Isolated production-app VM probe; instrumentation exists only in this tool."""
import argparse
import base64
import contextlib
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import sqlite3
import subprocess
import sys
import threading
import time
import uuid
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lookup import platform

REMOTE='LookUpLinux-gsd-app-05'
PROBE='org.lookup.Linux.AppProbe'
FIXTURE='org.lookup.Linux.AppFixture'
PUBLIC=('English','break out','one two three four','one two three four five',
        'networkprobe','blockedprobe','timeoutprobe','delayed','cacheprobe',
        'English public context','English another context','delayedagain','','12345','longword','word')
_state={'case':'normal','resources':None,'release':threading.Event()}
_state['release'].set()
REQUIRED_GATES=frozenset(('warm_primary','repeated_primary_ocr','boundaries','sentence_no_history',
    'focus_loss','escape','save_failure','network_errors','themes_scales','inactivity','cold_owner',
    'duplicate_owner','dismiss_pending','latest_pending','tray_quit','tool_capture_cursor_errors',
    'cache_failure','context_preview','late_context','invalid_absent_primary_reset',
    'long_article_selectable','native_close','deliberate_input_timer'))


def correct_repeat(status):
    return status.get('mode')=='ocr' and status.get('key')=='word'


def instrument():
    """Called by the owned test profile's sitecustomize, never by production."""
    from lookup import gui,app,translate,online
    from lookup import capture
    original_cursor=platform.cursor_position
    original_capture=capture.capture_monitor
    def cursor(*args,**kwargs):
        if _state['case']=='cursor_failure':raise platform.PlatformError('bad_output')
        return original_cursor(*args,**kwargs)
    def screenshot(*args,**kwargs):
        if _state['case']=='capture_failure':raise platform.PlatformError('bad_output')
        return original_capture(*args,**kwargs)
    platform.cursor_position=cursor;capture.capture_monitor=screenshot
    original_components=gui.components
    original_resources=app._resources
    class Connection:
        def __init__(self,conn):self.conn=conn
        def execute(self,sql,*args):
            lowered=sql.lstrip().lower()
            if _state['case']=='save_failure' and lowered.startswith('insert into words'):
                raise sqlite3.OperationalError('controlled persistence failure')
            if _state['case']=='cache_failure' and (lowered.startswith('insert into translations') or lowered.startswith('insert into meta')):
                raise sqlite3.OperationalError('controlled persistence failure')
            return self.conn.execute(sql,*args)
    @contextlib.contextmanager
    def resources():
        with original_resources() as value:
            if value.conn is not None:value.conn=Connection(value.conn)
            _state['resources']=value
            try:yield value
            finally:_state['resources']=None
    app._resources=resources
    def network(text,kind,**kwargs):
        case=_state['case']
        failures={'no_network':'no_network','blocked':'blocked','timeout':'timeout'}
        if case in failures:raise online.TranslateError(failures[case])
        if case=='delay' or (case=='context_delay' and kind=='sentence'):_state['release'].wait(10)
        return online.OnlineResult('google','gtx','контрольный перевод',(),None,None,'en')
    online.translate_online=network
    def components():
        Popup,Owner=original_components()
        from PyQt6.QtCore import QObject,QEvent,QTimer,pyqtSlot,pyqtClassInfo
        from PyQt6.QtWidgets import QLabel,QApplication,QTextEdit,QWidget
        from PyQt6.QtDBus import QDBusConnection
        @pyqtClassInfo('D-Bus Interface',PROBE)
        class Probe(QObject):
            def __init__(self,owner):
                super().__init__(owner)
                self.owner=owner
                QApplication.instance().installEventFilter(self)
            def eventFilter(self,watched,event):
                owner=self.owner
                if (event.type()==QEvent.Type.Paint and isinstance(watched,QWidget) and getattr(owner,'_test_ready',False)
                        and getattr(owner,'_test_useful_ms',None) is None
                        and (watched is owner.popup or owner.popup.isAncestorOf(watched))):
                    identity=owner._identity
                    def painted():
                        if owner.engine.current(identity) and owner.popup.isVisible():
                            owner._test_useful_ms=(time.perf_counter()-owner.engine._started)*1000
                    QTimer.singleShot(0,painted)
                return False
            @pyqtSlot(result=str)
            def Status(self):
                owner=self.owner
                event=getattr(owner,'_test_event',None)
                result=event.result if event else None
                allowed={text.lower() for text in PUBLIC}
                key=result.key if result and result.key in allowed else 'unexpected' if result else None
                texts='\n'.join(label.text() for label in owner.popup.findChildren(QLabel) if not label.isHidden())+'\n'+'\n'.join(widget.toPlainText() for widget in owner.popup.findChildren(QTextEdit) if not widget.isHidden())
                rect=owner.popup.geometry()
                palette=owner.popup.palette()
                from PyQt6.QtGui import QPalette
                tray=owner.tray.geometry();menu=owner.menu.geometry()
                quit_rect=owner.menu.actionGeometry(owner.menu.actions()[-1])
                quit_point=owner.menu.mapToGlobal(quit_rect.center())
                reading_point=owner.popup.scroll.viewport().mapToGlobal(owner.popup.scroll.viewport().rect().center())
                close_point=owner.popup.close_button.mapToGlobal(owner.popup.close_button.rect().center())
                return json.dumps(dict(pid=os.getpid(),run_id=os.environ['LOOKUP_RUN_ID'],identity=owner._identity,
                    visible=owner.popup.isVisible(),active=owner.popup.isActiveWindow(),armed=owner.popup._armed,
                    uuid=owner.popup_uuid,geometry=[rect.x(),rect.y(),rect.width(),rect.height()],
                    stage=event.stage if event else None,mode=event.mode if event else None,
                    useful_ms=getattr(owner,'_test_useful_ms',None),elapsed_ms=event.elapsed_ms if event else None,
                    key=key,count=result.count if result else None,saved=result.saved if result else False,
                    error=event.error if event else None,save_error=event.save_error if event else None,
                    context_error=result.context_error if result else None,cache_error=result.cache_error if result else None,
                    online_error=result.online_error if result else None,
                    context_pending=result.context_pending if result else False,
                    meaning='английский' in texts,ipa='ɪŋ' in texts,source_order=texts.find('First Public')<texts.find('Second Public') if 'Second Public' in texts else False,
                    cache_warning=gui.CACHE_ERROR in texts,save_warning=gui.SAVE_ERROR in texts,
                    background=palette.color(QPalette.ColorRole.Window).name(),
                    foreground=palette.color(QPalette.ColorRole.WindowText).name(),
                    disabled_future=all(not a.isEnabled() for a in owner.future_actions),
                    timer_remaining_ms=owner.popup.timer.remainingTime(),presentations=owner.presentations,
                    scroll_maximum=owner.popup.scroll.verticalScrollBar().maximum(),
                    scroll_value=owner.popup.scroll.verticalScrollBar().value(),reading_point=[reading_point.x(),reading_point.y()],
                    selected_characters=sum(len(widget.textCursor().selectedText()) for widget in owner.popup.findChildren(QTextEdit)),
                    close_point=[close_point.x(),close_point.y()],
                    available=event.available if event else None,
                    menu_visible=owner.menu.isVisible(),menu_shown=getattr(owner,'_test_menu_shown',0),menu_geometry=[menu.x(),menu.y(),menu.width(),menu.height()],
                    quit_point=[quit_point.x(),quit_point.y()],tray_geometry=[tray.x(),tray.y(),tray.width(),tray.height()],
                    queue_count=int(owner.engine._pending is not None),worker_alive=owner.engine.is_alive()))
            @pyqtSlot(str,result=bool)
            def Configure(self,case):
                if case not in ('normal','online','no_network','blocked','timeout','delay','context_delay','save_failure','cache_failure','missing_tesseract','cursor_failure','capture_failure'):
                    return False
                resources=_state['resources']
                if resources is None:return False
                _state['case']=case
                if case in ('delay','context_delay'):_state['release'].clear()
                else:_state['release'].set()
                resources.config=replace(resources.config,online=case not in ('normal','missing_tesseract','save_failure','cursor_failure','capture_failure'))
                if case=='missing_tesseract':os.environ['PATH']=os.environ['LOOKUP_EMPTY_PATH']
                else:os.environ['PATH']=os.environ['LOOKUP_ORIGINAL_PATH']
                return True
            @pyqtSlot(result=bool)
            def Release(self):
                _state['release'].set();return True
            @pyqtSlot(result=bool)
            def Dismiss(self):
                self.owner.popup.dismiss();return True
            @pyqtSlot(result=bool)
            def Quit(self):
                _state['release'].set();self.owner.quit();return True
        @pyqtClassInfo('D-Bus Interface',gui.SERVICE)
        class ObservedOwner(Owner):
            def __init__(self,*args,**kwargs):
                super().__init__(*args,**kwargs)
                self._test_menu_shown=0
                self.menu.aboutToShow.connect(self.menu_shown)
                self._probe=Probe(self)
                bus=QDBusConnection.sessionBus()
                if not bus.registerService(PROBE) or not bus.registerObject('/Probe',self._probe,QDBusConnection.RegisterOption.ExportAllSlots):
                    self.quit()
            def menu_shown(self):self._test_menu_shown+=1
            def receive(self,event):
                if self.engine.current(event.id):
                    self._test_event=event
                    if event.stage=='frozen':
                        self._test_useful_ms=None;self._test_ready=False
                    if event.stage=='ready':self._test_ready=True
                super().receive(event)
        return Popup,ObservedOwner
    gui.components=components


def profile(run_id):
    if len(run_id)!=32 or any(c not in '0123456789abcdef' for c in run_id):
        raise RuntimeError('invalid_run_id')
    return Path('/run/user')/str(os.getuid())/'lookup-app-05'/run_id


def environment(root):
    env=platform.session_env()
    repo=Path(__file__).resolve().parents[1]
    env.update(LOOKUP_DB=str(root/'history.db'),LOOKUP_CONFIG=str(root/'config.json'),
               LOOKUP_DICTS=str(root/'dicts'),LOOKUP_CACHE=str(root/'cache'),
               XDG_CONFIG_HOME=str(root/'kde'),PYTHONPATH=os.pathsep.join((str(root/'bootstrap'),str(repo))),
               LOOKUP_ORIGINAL_PATH=env['PATH'],LOOKUP_EMPTY_PATH=str(root/'empty-path'),LOOKUP_RUN_ID=root.name)
    return env


def fixture(run_id):
    root=profile(run_id);os.environ.update(environment(root))
    from PyQt6.QtCore import QObject,Qt,pyqtSlot,pyqtClassInfo
    from PyQt6.QtGui import QFont,QPalette
    from PyQt6.QtWidgets import QApplication,QWidget,QVBoxLayout,QLineEdit,QStyle,QStyleOptionFrame
    from PyQt6.QtDBus import QDBusConnection
    application=QApplication([])
    application.setApplicationName('LookUp public fixture')
    class Line(QLineEdit):
        def span(self):
            option=QStyleOptionFrame();self.initStyleOption(option)
            rect=self.style().subElementRect(QStyle.SubElement.SE_LineEditContents,option,self)
            start=self.mapToGlobal(rect.topLeft());start.setY(start.y()+rect.height()//2)
            return [start.x()+1,start.y()],[start.x()+self.fontMetrics().horizontalAdvance(self.text())+5,start.y()]
        def point(self):
            option=QStyleOptionFrame();self.initStyleOption(option)
            rect=self.style().subElementRect(QStyle.SubElement.SE_LineEditContents,option,self)
            point=self.mapToGlobal(rect.topLeft())
            point.setX(point.x()+self.fontMetrics().horizontalAdvance(self.text()[:3]))
            point.setY(point.y()+rect.height()//2)
            return [point.x(),point.y()]
    window=QWidget();window.setWindowTitle('LookUp Linux Public App Test')
    window.setWindowFlags(Qt.WindowType.Window|Qt.WindowType.FramelessWindowHint)
    layout=QVBoxLayout(window);layout.setContentsMargins(64,32,64,32)
    layout.addStretch()
    line=Line(PUBLIC[0]);line.setReadOnly(True);line.setFont(QFont('Noto Sans',20))
    line.setFrame(False);line.setStyleSheet('QLineEdit { background: transparent; }')
    layout.addWidget(line)
    other=Line('word');other.setReadOnly(True);other.setFont(line.font())
    other.setFrame(False);other.setStyleSheet('QLineEdit { background: transparent; }')
    layout.addWidget(other);layout.addStretch()
    window.showMaximized()
    @pyqtClassInfo('D-Bus Interface',FIXTURE)
    class Fixture(QObject):
        @pyqtSlot(result=str)
        def Status(self):
            return json.dumps(dict(pid=os.getpid(),run_id=run_id,point=line.point(),span=line.span(),other_point=other.point(),case=PUBLIC.index(line.text())))
        @pyqtSlot(int,result=bool)
        def Case(self,index):
            if not 0<=index<len(PUBLIC):return False
            line.setText(PUBLIC[index]);line.setFocus();return True
        @pyqtSlot(result=bool)
        def Quit(self):application.quit();return True
    service=Fixture()
    bus=QDBusConnection.sessionBus()
    if not bus.registerService(FIXTURE):return 1
    bus.registerObject('/Fixture',service,QDBusConnection.RegisterOption.ExportAllSlots)
    return application.exec()


def target(action,payload):
    from tools.check_vm_spike import ensure_unlocked
    run_id=payload['run_id'];root=profile(run_id)
    env=platform.session_env();os.environ.update(env)
    from PyQt6.QtCore import QCoreApplication
    from PyQt6.QtDBus import QDBusConnection,QDBusMessage,QDBus
    application=QCoreApplication([]);bus=QDBusConnection.sessionBus()
    def call(service,path,interface,method,*values):
        msg=QDBusMessage.createMethodCall(service,path,interface,method);msg.setArguments(list(values))
        reply=bus.call(msg,QDBus.CallMode.Block,2000)
        if reply.type()==QDBusMessage.MessageType.ErrorMessage:raise RuntimeError('probe_'+method+'_unavailable')
        return reply.arguments()[0] if reply.arguments() else None
    from lookup import gui
    desktop=Path.home()/'.local/share/applications'/gui.DESKTOP
    snapshot=root/'snapshot.json'
    def remember(pid):
        saved=json.loads(snapshot.read_text())
        if not any(p['pid']==pid for p in saved['processes']):
            saved['processes'].append(dict(pid=pid,start=Path('/proc',str(pid),'stat').read_text().split(') ',1)[1].split()[19]))
            snapshot.write_text(json.dumps(saved))
    if action=='prepare':
        if root.exists():raise RuntimeError('profile_already_exists')
        for name in (gui.SERVICE,PROBE,FIXTURE):
            if call('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','NameHasOwner',name):raise RuntimeError('preexisting_owner')
        available=call('org.kde.kglobalaccel','/kglobalaccel','org.kde.KGlobalAccel','isGlobalShortcutAvailable',0x12000044,gui.DESKTOP)
        if not available:raise RuntimeError('shortcut_conflict')
        unlocked=ensure_unlocked(env,lambda:call('org.freedesktop.ScreenSaver','/ScreenSaver','org.freedesktop.ScreenSaver','GetActive'),os.getuid())
        old=desktop.read_bytes() if desktop.exists() else None
        if old and b'LookUp Linux owned application trigger' not in old:raise RuntimeError('unowned_desktop')
        outputs=json.loads(platform.run(['kscreen-doctor','-j'],env))['outputs']
        global_config=Path.home()/'.config/kdeglobals'
        original=global_config.read_bytes() if global_config.exists() else b''
        root.mkdir(parents=True,mode=0o700)
        snapshot.write_text(json.dumps(dict(run_id=run_id,desktop=base64.b64encode(old).decode() if old else None,
            outputs=[dict(name=o['name'],scale=o['scale'],pos=o['pos'],mode=o['currentModeId']) for o in outputs if o['enabled']],
            theme_hash=hashlib.sha256(original).hexdigest(),processes=[])))
        (root/'kde').mkdir();(root/'bootstrap').mkdir();(root/'empty-path').mkdir()
        (root/'kde/kdeglobals').write_bytes(original)
        (root/'config.json').write_text('{"online":false}')
        (root/'bootstrap/sitecustomize.py').write_text('from tools.check_app import instrument\ninstrument()\n')
        from tests._stardict_writer import write_stardict
        for name,label in (('first','First Public'),('second','Second Public')):
            write_stardict(root/'dicts',name,[('english','[ˈɪŋɡlɪʃ] _adj. английский; _n. английский язык'),('break out','_v. вырваться'),('word','_n. слово'),('longword','[lɔŋ] _n. '+('Long public definition '*100)+'\n'+'unbroken'*1000)],bookname=label)
        child_env=environment(root)
        overrides={k:v for k,v in child_env.items() if k.startswith('LOOKUP_') or k in ('XDG_CONFIG_HOME','PYTHONPATH')}
        (root/'launcher.py').write_text('import os,sys\nos.environ.update('+repr(overrides)+')\nsys.path[:0]='+repr(child_env['PYTHONPATH'].split(os.pathsep))+'\nfrom tools.check_app import instrument\ninstrument()\nfrom lookup.__main__ import main\nraise SystemExit(main(["--trigger"]))\n')
        text=gui.desktop_text(sys.executable,Path(__file__).resolve().parents[1])
        text=text.replace(' -m lookup --trigger',' "'+str(root/'launcher.py')+'"')
        desktop.parent.mkdir(parents=True,exist_ok=True);desktop.write_text(text)
        platform.run(['kbuildsycoca6'],env,timeout=10)
        for args in ([sys.executable,str(Path(__file__).resolve()),'--fixture','--run-id',run_id],[sys.executable,'-m','lookup','--app']):
            child=subprocess.Popen(args,env=child_env,cwd=Path(__file__).resolve().parents[1],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
            remember(child.pid)
        return dict(normal_unlock_needed=unlocked)
    if action=='status':
        status=json.loads(call(PROBE,'/Probe',PROBE,'Status'))
        if status['run_id']!=run_id:raise RuntimeError('owner_mismatch')
        remember(status['pid'])
        status['active_uuid']=platform.run(['kdotool','getactivewindow'],env,limit=4096).decode().strip()
        if status['visible'] and status['uuid']:
            try:status['compositor_geometry']=platform.window_geometry(env,status['pid'],status['uuid'])
            except platform.PlatformError as error:
                status['compositor_error']=error.reason
                status['compositor_output']=platform.window_action(env,status['pid'],status['uuid'],'getwindowgeometry').decode('ascii')
            status['panel_rects']=platform.panel_rects(env)
            status['monitor_rects']=[[m.x,m.y,m.width,m.height] for m in platform.monitors(env)]
        return status
    if action=='fixture':
        if 'case' in payload:call(FIXTURE,'/Fixture',FIXTURE,'Case',int(payload['case']))
        status=json.loads(call(FIXTURE,'/Fixture',FIXTURE,'Status'))
        if status['run_id']!=run_id:raise RuntimeError('owner_mismatch')
        ids=platform.owned_window(env,status['pid'])
        platform.window_action(env,status['pid'],ids[0],'windowraise')
        platform.window_action(env,status['pid'],ids[0],'windowactivate')
        time.sleep(.2)
        status=json.loads(call(FIXTURE,'/Fixture',FIXTURE,'Status'))
        monitor=platform.monitor_at(status['point'],platform.monitors(env))
        status['scale']=monitor.scale
        return status
    if action=='cursor':return platform.cursor_position(env)
    if action=='services':
        return {name:bool(call('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','NameHasOwner',name)) for name in (gui.SERVICE,PROBE)}
    if action=='duplicate':
        children=[subprocess.Popen([sys.executable,'-m','lookup','--app'],env=environment(root),
                  cwd=Path(__file__).resolve().parents[1],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL) for _ in range(2)]
        for child in children:remember(child.pid)
        return [child.wait(timeout=8) for child in children]
    if action=='configure':return call(PROBE,'/Probe',PROBE,'Configure',payload['case'])
    if action in ('dismiss','quit','release'):
        return call(PROBE,'/Probe',PROBE,action.title())
    if action=='rows':
        with contextlib.closing(sqlite3.connect(root/'history.db')) as conn:
            rows=conn.execute('SELECT word,count,context FROM words ORDER BY word').fetchall()
        allowed={text.lower() for text in PUBLIC}
        return [dict(word=word if word in allowed else 'unexpected',count=count,context_public=context in PUBLIC) for word,count,context in rows]
    if action=='scale':
        value=payload['scale']
        if value not in (1,1.25,1.5,2):raise RuntimeError('invalid_scale')
        output=platform.monitors(env)[0]
        platform.run(['kscreen-doctor',f'output.{output.name}.scale.{value}'],env,timeout=5)
        time.sleep(.7);return True
    if action=='theme':
        value=payload['theme']
        if value not in ('BreezeLight','BreezeDark'):raise RuntimeError('invalid_theme')
        platform.run(['plasma-apply-colorscheme',value],environment(root),timeout=5)
        time.sleep(.4);return True
    if action=='finish':
        if not snapshot.exists():return dict(restored=True)
        saved=json.loads(snapshot.read_text())
        if saved['run_id']!=run_id:raise RuntimeError('owner_mismatch')
        for name,path,method in ((PROBE,'/Probe','Release'),(PROBE,'/Probe','Quit'),(FIXTURE,'/Fixture','Quit')):
            try:
                status=json.loads(call(name,path,name,'Status'))
                if status.get('run_id')==run_id:call(name,path,name,method)
            except RuntimeError:pass
        time.sleep(.5)
        for process in saved['processes']:
            proc=Path('/proc',str(process['pid']))
            try:
                same=proc.stat().st_uid==os.getuid() and proc.joinpath('stat').read_text().split(') ',1)[1].split()[19]==process['start']
                owned=(b'LOOKUP_DB='+str(root/'history.db').encode()) in proc.joinpath('environ').read_bytes().split(b'\x00')
                if same and owned:os.kill(process['pid'],signal.SIGTERM)
            except (FileNotFoundError,ProcessLookupError):pass
        errors=[]
        for output in saved['outputs']:
            try:platform.run(['kscreen-doctor',f"output.{output['name']}.scale.{output['scale']}"],env,timeout=5)
            except Exception:errors.append('display_restore_failed')
        try:
            if desktop.exists() and b'LookUp Linux owned application trigger' not in desktop.read_bytes():raise RuntimeError('desktop_owner_changed')
            if saved['desktop'] is None:desktop.unlink(missing_ok=True)
            else:desktop.write_bytes(base64.b64decode(saved['desktop']))
            platform.run(['kbuildsycoca6'],env,timeout=10)
            if saved['desktop'] is None:call('org.kde.kglobalaccel','/kglobalaccel','org.kde.KGlobalAccel','unregister',gui.DESKTOP,'_launch')
        except Exception:errors.append('desktop_restore_failed')
        actual=json.loads(platform.run(['kscreen-doctor','-j'],env))['outputs']
        fields=[dict(name=o['name'],scale=o['scale'],pos=o['pos'],mode=o['currentModeId']) for o in actual if o['enabled']]
        global_config=Path.home()/'.config/kdeglobals'
        theme_hash=hashlib.sha256(global_config.read_bytes() if global_config.exists() else b'').hexdigest()
        result=dict(display_restored=fields==saved['outputs'],theme_unchanged=theme_hash==saved['theme_hash'],
                    desktop_restored=(desktop.read_bytes() if desktop.exists() else None)==(base64.b64decode(saved['desktop']) if saved['desktop'] else None))
        def running(process):
            try:
                fields=Path('/proc',str(process['pid']),'stat').read_text().split(') ',1)[1].split()
                return fields[19]==process['start'] and fields[0]!='Z'
            except FileNotFoundError:return False
        deadline=time.monotonic()+4
        while any(running(p) for p in saved['processes']) and time.monotonic()<deadline:time.sleep(.1)
        result['processes_stopped']=not any(running(p) for p in saved['processes'])
        result['shortcut_restored']=bool(call('org.kde.kglobalaccel','/kglobalaccel','org.kde.KGlobalAccel','isGlobalShortcutAvailable',0x12000044,gui.DESKTOP)) if saved['desktop'] is None else result['desktop_restored']
        result['errors']=errors
        if not errors and all(v for k,v in result.items() if k!='errors'):
            if root.is_symlink() or root.resolve().parent!=profile(run_id).parent.resolve():raise RuntimeError('unsafe_cleanup')
            shutil.rmtree(root)
        return result
    raise RuntimeError('unknown_action')


def remote(action,payload):
    encoded=base64.b64encode(json.dumps(payload).encode()).decode()
    proc=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=5','archvm',
        f'cd {REMOTE} && python3 tools/check_app.py --target {action} --payload {encoded}'],capture_output=True,text=True,timeout=45)
    if proc.returncode:raise RuntimeError('target_'+action+'_failed:'+proc.stderr[-250:])
    return json.loads(proc.stdout)


def accepted(evidence):
    restoration=evidence.get('restoration',{})
    return (not evidence.get('error') and not evidence.get('key_release_failed')
            and not evidence.get('restoration_error')
            and REQUIRED_GATES.issubset(evidence.get('gates',{}))
            and all(evidence['gates'].values()) and not restoration.get('errors')
            and all(restoration.get(k) is True for k in
                ('display_restored','theme_unchanged','desktop_restored','processes_stopped','shortcut_restored')))


def host(output):
    from tools.check_vm_spike import keys,move_pointer,relative_pointer,wait_for,GateTimeout
    run_id=uuid.uuid4().hex
    evidence=dict(acceptance='agent',run_id=run_id,observations={},gates={},
                  limits=['Controlled online transport; no live-provider latency claim.','Single VM monitor; negative origins covered by portable tests.'])
    def request(action,payload=None):return remote(action,dict(payload or {},run_id=run_id))
    def observe(name,predicate,timeout=12):
        evidence['stage']=name
        print('gate: '+name,flush=True)
        status=wait_for(lambda:request('status'),predicate,timeout)
        evidence['observations'][name]=status
        return status
    def select(index=0,other=False):
        fixture=request('fixture',{'case':index})
        point=fixture['other_point' if other else 'point']
        move_pointer(point,fixture['scale'],request)
        relative_pointer(0,0,1);relative_pointer(0,0,0)
        if not other:keys('1d 1e 9e 9d')
        return fixture
    def trigger(name,key=None,mode=None):
        before=request('status')['identity'] or 0
        keys('e0 5b 2a 20 a0 aa e0 db')
        return observe(name,lambda s:(s['identity'] or 0)>before and s['visible'] and s['armed']
                       and s['stage'] in ('ready','context','error') and s['active'] and s['useful_ms'] is not None
                       and (key is None or s['key']==key) and (mode is None or s['mode']==mode))
    try:
        evidence['stage']='prepare';evidence['setup']=request('prepare')
        initial=observe('owner',lambda s:s['worker_alive'])
        evidence['duplicate_exit_codes']=request('duplicate')
        if evidence['duplicate_exit_codes']!=[0,0] or request('status')['pid']!=initial['pid']:raise RuntimeError('duplicate_owner_gate')
        select();warm=trigger('new_primary','english','primary')
        if not (warm['meaning'] and warm['ipa'] and warm['source_order'] and warm['saved'] and warm['count']==1):raise RuntimeError('primary_content_gate')
        fixture=request('fixture');move_pointer(fixture['other_point'],fixture['scale'],request)
        repeated=trigger('repeated_primary_ocr',mode='ocr')
        if not correct_repeat(repeated):raise RuntimeError('repeated_primary_gate')
        keys('01 81');observe('escape',lambda s:not s['visible'])
        for index in (1,2,3):
            select(index);status=trigger('boundary_'+str(index),PUBLIC[index], 'primary')
            if index==3 and status['saved']:raise RuntimeError('sentence_saved')
        rows=request('rows');evidence['boundary_rows']=rows
        if any(row['word']==PUBLIC[3] for row in rows):raise RuntimeError('sentence_history_gate')
        request('fixture');observe('focus_loss',lambda s:not s['visible'])
        for index in (12,13):
            fixture=request('fixture',{'case':index})
            move_pointer(fixture['point'],fixture['scale'],request)
            relative_pointer(0,0,1);relative_pointer(0,0,0);keys('1d 1e 9e 9d')
            move_pointer(fixture['other_point'],fixture['scale'],request)
            trigger('invalid_primary_reset_'+str(index),mode='ocr')
            select();trigger('fresh_after_reset_'+str(index),'english','primary')
            select(1);trigger('reset_separator_'+str(index),'break out','primary')
        request('configure',{'case':'save_failure'});select()
        status=trigger('save_failure','english','primary')
        if not status['meaning'] or not status['save_warning'] or status['saved']:raise RuntimeError('save_failure_gate')
        for case,index in (('no_network',4),('blocked',5),('timeout',6)):
            request('configure',{'case':case});select(index)
            before=request('status')['identity'];keys('e0 5b 2a 20 a0 aa e0 db')
            status=observe(case,lambda s:s['identity']>before and s['visible'] and s['stage'] in ('ready','context') and s['key']==PUBLIC[index])
            if status['saved'] and status['count'] is None:raise RuntimeError('false_saved_count')
            if status['online_error']!=case:raise RuntimeError('network_reason_gate')
        request('configure',{'case':'delay'});select(7)
        before=request('status')['identity'];rows_before=request('rows')
        keys('e0 5b 2a 20 a0 aa e0 db')
        observe('delayed_loading',lambda s:s['identity']>before and s['visible'] and s['armed'] and s['stage']=='frozen')
        keys('01 81');observe('dismiss_pending',lambda s:not s['visible'])
        request('release');time.sleep(.8)
        if request('status')['visible'] or request('rows')!=rows_before:raise RuntimeError('dismiss_pending_gate')
        request('configure',{'case':'delay'});select(11)
        before=request('status')['identity'];keys('e0 5b 2a 20 a0 aa e0 db')
        observe('slow_A',lambda s:s['identity']>before and s['visible'] and s['stage']=='frozen')
        select();before=request('status')['identity'];keys('e0 5b 2a 20 a0 aa e0 db')
        observe('queued_B',lambda s:s['identity']>before and not s['visible'])
        request('configure',{'case':'normal'})
        observe('latest_B',lambda s:s['key']=='english' and s['visible'] and s['stage'] in ('ready','context') and s['useful_ms'] is not None)
        if any(row['word'] in ('delayed','delayedagain') for row in request('rows')):raise RuntimeError('stale_A_history_gate')
        for case,reason in (('missing_tesseract','missing_tesseract'),('capture_failure','capture_failed'),('cursor_failure','cursor_failed')):
            request('configure',{'case':case})
            fixture=request('fixture');move_pointer(fixture['other_point'],fixture['scale'],request)
            before=request('status')['identity'];keys('e0 5b 2a 20 a0 aa e0 db')
            observe(case,lambda s:s['identity']>before and s['visible'] and s['error']==reason)
        request('configure',{'case':'cache_failure'});select(8)
        status=trigger('cache_failure','cacheprobe','primary')
        if not status['cache_warning'] or not status['cache_error']:raise RuntimeError('cache_failure_gate')
        request('configure',{'case':'context_delay'})
        fixture=request('fixture',{'case':9});move_pointer(fixture['point'],fixture['scale'],request)
        status=trigger('context_preview','english','ocr')
        if not status['context_pending']:raise RuntimeError('context_preview_gate')
        remaining=status['timer_remaining_ms'];presentations=status['presentations'];count=status['count']
        request('release')
        final=observe('context_complete',lambda s:s['identity']==status['identity'] and s['stage']=='context' and not s['context_pending'])
        if final['count']!=count or final['presentations']!=presentations or final['timer_remaining_ms']>remaining:raise RuntimeError('context_only_update_gate')
        request('configure',{'case':'context_delay'})
        fixture=request('fixture',{'case':10});move_pointer(fixture['point'],fixture['scale'],request)
        trigger('late_context_preview','english','ocr')
        keys('01 81');observe('late_context_dismiss',lambda s:not s['visible'])
        rows_before=request('rows');request('release');time.sleep(.6)
        if request('status')['visible'] or request('rows')!=rows_before:raise RuntimeError('late_context_gate')
        request('configure',{'case':'normal'});select(14)
        long=trigger('long_article','longword','primary')
        if long['scroll_maximum']<=0:raise RuntimeError('long_article_scroll_gate')
        move_pointer(long['reading_point'],1,request)
        relative_pointer(0,0,1);relative_pointer(0,0,0);keys('1d 1e 9e 9d')
        selected=observe('select_article',lambda s:s['selected_characters']>1000)
        move_pointer(selected['close_point'],1,request)
        relative_pointer(0,0,1);relative_pointer(0,0,0)
        observe('native_close',lambda s:not s['visible'])
        request('configure',{'case':'normal'})
        evidence['appearance']=[]
        for scale in (1,1.25,1.5,2):
            request('scale',{'scale':scale})
            for theme in ('BreezeLight','BreezeDark'):
                request('theme',{'theme':theme})
                select(1);trigger(f'freshness_{theme}_{scale}','break out','primary')
                select()
                status=trigger(f'{theme}_{scale}','english','primary')
                actual=status.get('compositor_geometry',())
                if len(actual)!=4 or any(abs(a-b)>1 for a,b in zip(status['geometry'],actual)) or not status['disabled_future']:raise RuntimeError('geometry_or_tray_gate')
                x,y,w,h=actual
                if not any(x>=mx-1 and y>=my-1 and x+w<=mx+mw+1 and y+h<=my+mh+1 for mx,my,mw,mh in status['monitor_rects']):raise RuntimeError('monitor_containment_gate')
                if any(min(x+w,px+pw)-max(x,px)>1 and min(y+h,py+ph)-max(y,py)>1 for px,py,pw,ph in status['panel_rects']):raise RuntimeError('panel_overlap_gate')
                from tools.check_vm_spike import VBOX
                image_dir=Path(tempfile.gettempdir())/('lookup-phase05-visual-'+run_id)
                image_dir.mkdir(exist_ok=True)
                image_path=image_dir/f'{theme}-{scale}.png'
                subprocess.run([VBOX,'controlvm','arch-kde','screenshotpng',str(image_path)],check=True,capture_output=True,timeout=5)
                status['visual_file']=str(image_path)
                evidence['appearance'].append(dict(scale=scale,theme=theme,status=status))
        request('scale',{'scale':1});select(1);trigger('inactivity_separator','break out','primary');select()
        trigger('inactivity_start','english')
        time.sleep(1)
        before=request('status')['timer_remaining_ms'];keys('0f 8f')
        reset=request('status')['timer_remaining_ms']
        if reset<=before:raise RuntimeError('deliberate_input_timer_gate')
        observe('inactivity_20s',lambda s:not s['visible'],23)
        request('quit');time.sleep(1)
        fixture=request('fixture');move_pointer(fixture['other_point'],fixture['scale'],request)
        keys('e0 5b 2a 20 a0 aa e0 db')
        cold=observe('cold',lambda s:s['visible'] and s['armed'] and s['active'] and s['stage'] in ('ready','context') and s['useful_ms'] is not None)
        if cold['pid']==initial['pid']:raise RuntimeError('cold_owner_gate')
        request('fixture')
        move_pointer((1630,1057),1,request)
        relative_pointer(0,0,2);relative_pointer(0,0,0)
        menu=observe('tray_menu',lambda s:s['menu_shown']>0)
        move_pointer((1680,1020),1,request)
        relative_pointer(0,0,1);relative_pointer(0,0,0)
        time.sleep(.6)
        evidence['after_tray_quit']=request('services')
        if any(evidence['after_tray_quit'].values()):raise RuntimeError('tray_quit_gate')
        evidence['gates']=dict(warm_primary=True,repeated_primary_ocr=True,boundaries=True,sentence_no_history=True,
                               focus_loss=True,escape=True,save_failure=True,network_errors=True,
                               themes_scales=len(evidence['appearance'])==8,inactivity=True,cold_owner=True,
                               duplicate_owner=True,dismiss_pending=True,latest_pending=True,tray_quit=True)
        evidence['gates'].update(tool_capture_cursor_errors=True,cache_failure=True,context_preview=True,late_context=True)
        evidence['gates'].update(invalid_absent_primary_reset=True,long_article_selectable=True,native_close=True,deliberate_input_timer=True)
    except Exception as error:
        evidence['error']=str(error)
        if isinstance(error,GateTimeout):evidence['failed_observation']=error.last
    finally:
        try:keys('a0 aa e0 db 81');relative_pointer(0,0,0)
        except Exception:evidence['key_release_failed']=True
        try:evidence['restoration']=request('finish')
        except Exception as error:evidence['restoration_error']=str(error)
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps({k:evidence[k] for k in ('stage','error','restoration','restoration_error') if k in evidence}))
    return 0 if accepted(evidence) else 1


def host_extra(output):
    """Independent physical mouse selection, empty scene and outside-click proof."""
    from tools.check_vm_spike import keys,move_pointer,relative_pointer,wait_for,GateTimeout
    run_id=uuid.uuid4().hex
    evidence=dict(acceptance='agent',run_id=run_id,gates={},observations={})
    def request(action,payload=None):return remote(action,dict(payload or {},run_id=run_id))
    try:
        request('prepare')
        wait_for(lambda:request('status'),lambda s:s['worker_alive'])
        fixture=request('fixture',{'case':13})
        move_pointer(fixture['point'],fixture['scale'],request)
        relative_pointer(0,0,1);relative_pointer(0,0,0);keys('1d 1e 9e 9d')
        move_pointer((900,100),fixture['scale'],request)
        keys('e0 5b 2a 20 a0 aa e0 db')
        blank=wait_for(lambda:request('status'),lambda s:s['visible'] and s['armed'] and s['error']=='not_found' and s['mode']=='ocr')
        evidence['observations']['blank']=blank
        move_pointer(fixture['point'],fixture['scale'],request)
        relative_pointer(0,0,1);relative_pointer(0,0,0)
        evidence['observations']['outside']=wait_for(lambda:request('status'),lambda s:not s['visible'])
        fixture=request('fixture',{'case':0});start,end=fixture['span']
        move_pointer(start,fixture['scale'],request)
        relative_pointer(0,0,1)
        try:
            for _ in range(20):
                actual=request('cursor');dx,dy=end[0]-actual[0],end[1]-actual[1]
                if abs(dx)<=1 and abs(dy)<=1:break
                relative_pointer(max(-50,min(50,round(dx*fixture['scale']))),round(dy*fixture['scale']),1)
            else:raise RuntimeError('mouse_drag_delivery_failed')
        finally:relative_pointer(0,0,0)
        keys('e0 5b 2a 20 a0 aa e0 db')
        selected=wait_for(lambda:request('status'),lambda s:s['visible'] and s['armed'] and s['key']=='english' and s['mode']=='primary' and s['saved'])
        if selected['count']!=1 or not selected['meaning']:raise RuntimeError('mouse_primary_content_gate')
        evidence['observations']['mouse_primary']=selected
        request('configure',{'case':'no_network'})
        fixture=request('fixture',{'case':9});move_pointer(fixture['point'],fixture['scale'],request)
        keys('e0 5b 2a 20 a0 aa e0 db')
        offline=wait_for(lambda:request('status'),lambda s:s['visible'] and s['armed'] and s['key']=='english' and s['stage']=='context')
        if offline['context_error']!='no_network' or not offline['source_order'] or not offline['saved']:raise RuntimeError('offline_preserved_gate')
        evidence['observations']['offline_preserved']=offline
        evidence['gates']=dict(blank_not_found=True,physical_outside_click=True,physical_mouse_primary=True,offline_preserved=True)
    except Exception as error:
        evidence['error']=str(error)
        if isinstance(error,GateTimeout):evidence['failed_observation']=error.last
    finally:
        try:keys('a0 aa e0 db 81');relative_pointer(0,0,0)
        except Exception:evidence['key_release_failed']=True
        try:evidence['restoration']=request('finish')
        except Exception as error:evidence['restoration_error']=str(error)
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps({k:v for k,v in evidence.items() if k!='observations'}))
    restoration=evidence.get('restoration',{})
    return 0 if (not evidence.get('error') and not evidence.get('key_release_failed') and len(evidence['gates'])==4
                 and not restoration.get('errors') and all(restoration.get(k) is True for k in
                 ('display_restored','theme_unchanged','desktop_restored','processes_stopped','shortcut_restored'))) else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target');parser.add_argument('--payload',default='e30=')
    parser.add_argument('--fixture',action='store_true');parser.add_argument('--run-id')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--extra',action='store_true')
    args=parser.parse_args()
    if args.fixture:return fixture(args.run_id)
    if args.target:
        print(json.dumps(target(args.target,json.loads(base64.b64decode(args.payload)))))
        return 0
    if args.output:
        if os.name!='nt':parser.error('Run the physical-input orchestrator on Windows.')
        return host_extra(args.output) if args.extra else host(args.output)
    parser.error('use the Windows orchestrator or a bounded target action')


if __name__=='__main__':raise SystemExit(main())
