"""Owned-clone native acceptance. All fixture content is public and synthetic."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HOME=Path('/home/lookup07')
STATE=HOME/'.local/state/lookup-gsd-07'
SERVICE='org.lookup.Linux'
CLONE='cf207909-94b5-4b49-8bd8-ccff973c1dc8'
REQUIRED_GATES=frozenset(('physical_installed_capture','effective_shortcut','dictionary_order_disable',
    'online_off','popup_timeout','stale_reload','folder_rescan','native_appearance_keyboard',
    'failure_states','installed_package','login_enabled','login_disabled','removal','doctor'))
REQUIRED_CLEANUP=frozenset(('owned_processes_stopped','keys_released','user_data_retained',
    'unrelated_entry_retained','clone_powered_off','original_preserved'))


def accepted(report):
    if not isinstance(report,dict) or report.get('mode')!='native-installed' or report.get('error'):return False
    return all(isinstance(report.get(group),dict) and keys.issubset(report[group]) and
               all(value is True for value in report[group].values())
               for group,keys in (('gates',REQUIRED_GATES),('cleanup',REQUIRED_CLEANUP)))


def environment():
    assert os.getuid()==1001 and Path.home()==HOME,'owned_test_user_required'
    sys.path.insert(0,'/usr/lib/lookup/app')
    from lookup import platform
    env=platform.session_env()
    env.update(XDG_CONFIG_HOME=str(HOME/'.config'),XDG_CACHE_HOME=str(HOME/'.cache'),XDG_DATA_HOME=str(HOME/'.local/share'))
    env.pop('PYTHONPATH',None)
    # kbuildsycoca preserves SUDO_UID ownership; a cross-user verification
    # subprocess must not ask lookup07 to chown its cache to SSH user arch.
    for key in ('SUDO_UID','SUDO_GID','SUDO_USER','SUDO_COMMAND'):
        env.pop(key,None);os.environ.pop(key,None)
    return env


def fixture():
    os.environ.update(environment())
    from PyQt6.QtCore import Qt,QTimer
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import QApplication,QWidget,QVBoxLayout,QLineEdit
    application=QApplication([])
    window=QWidget();window.setWindowTitle('LookUp public settings fixture')
    window.setWindowFlags(Qt.WindowType.Window|Qt.WindowType.FramelessWindowHint)
    layout=QVBoxLayout(window);layout.setContentsMargins(100,100,100,100);layout.addStretch()
    line=QLineEdit('They waited by the bank of the river.')
    font=QFont('Noto Sans');font.setPixelSize(26);line.setFont(font)
    line.setReadOnly(True);line.setFrame(False);layout.addWidget(line);layout.addStretch()
    window.showMaximized();line.setFocus()
    def ready():
        rect=line.contentsRect();point=line.mapToGlobal(rect.center())
        point.setX(line.mapToGlobal(rect.topLeft()).x()+line.fontMetrics().horizontalAdvance('They waited by the ')+line.fontMetrics().horizontalAdvance('bank')//2+2)
        STATE.mkdir(parents=True,exist_ok=True)
        (STATE/'fixture.json').write_text(json.dumps(dict(pid=os.getpid(),point=[point.x(),point.y()])))
    QTimer.singleShot(400,ready)
    return application.exec()


def status():
    os.environ.update(environment())
    from PyQt6.QtCore import QCoreApplication
    from PyQt6.QtDBus import QDBusConnection
    from lookup import lifecycle,platform
    application=QCoreApplication([]);bus=QDBusConnection.sessionBus();interface=bus.interface();interface.setTimeout(1500)
    present=interface.isServiceRegistered(SERVICE)
    result=dict(owner=present.isValid() and present.value(),cursor=platform.cursor_position(os.environ))
    if result['owner']:result['pid']=interface.servicePid(SERVICE).value()
    try:
        binding=lifecycle.inspect_shortcut();result['keys']=[lifecycle.key_text(key) for key in binding.keys]
    except lifecycle.LifecycleError as error:result['key_error']=error.reason
    path=HOME/'.local/share/lookup/lookup.db'
    if path.exists():
        import sqlite3
        with sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True) as conn:
            result['bank']=conn.execute('SELECT word,count,context FROM words WHERE word="bank"').fetchone()
    if (STATE/'fixture.json').exists():result['fixture']=json.loads((STATE/'fixture.json').read_text())
    return result


def start():
    env=environment();STATE.mkdir(parents=True,exist_ok=True)
    config=HOME/'.config/lookup/config.json';config.parent.mkdir(parents=True,exist_ok=True)
    if not config.exists():config.write_text('{"online":false}')
    processes=[]
    for argv in ([sys.executable,str(Path(__file__).resolve()),'--fixture'],['/usr/bin/lookup','--app']):
        process=subprocess.Popen(argv,env=env,cwd='/tmp',stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
        processes.append(dict(pid=process.pid,start=Path('/proc',str(process.pid),'stat').read_text().split(') ',1)[1].split()[19]))
    (STATE/'processes.json').write_text(json.dumps(processes))
    return dict(started=[item['pid'] for item in processes])


def start_server(scale='1'):
    env=environment()
    env['QT_SCALE_FACTOR']=scale
    for name in ('command.json','native-state.json'):(STATE/name).unlink(missing_ok=True)
    with (HOME/'native.log').open('w') as output:
        child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--native-server'],
            env=env,cwd='/tmp',stdin=subprocess.DEVNULL,stdout=output,stderr=output,start_new_session=True)
    return dict(pid=child.pid)


def seed():
    os.environ.update(environment())
    from lookup import store,learning
    desktop=HOME/'.local/share/applications/lookup-gsd-unrelated.desktop';desktop.parent.mkdir(parents=True,exist_ok=True)
    desktop.write_text('[Desktop Entry]\nType=Application\nName=Public unrelated key\nExec=/usr/bin/touch '+
        str(STATE/'unrelated-trigger')+'\nX-KDE-Shortcuts=Meta+Shift+U\nNoDisplay=true\n')
    with store.open_store() as conn:
        store.upsert_word(conn,'publicseed','сохранить','Public retention fixture.')
        learning.add_card(conn,dict(word='publicseed',translation='сохранить',context='Public retention fixture.'))
    path=HOME/'.config/lookup/config.json';value=json.loads(path.read_text());value['public_retention']='retain'
    path.write_text(json.dumps(value,ensure_ascii=False))
    refresh=subprocess.run(['kbuildsycoca6','--noincremental'],env=dict(os.environ),capture_output=True,text=True,timeout=15)
    return dict(seeded=True,desktop=str(desktop),refresh_exit=refresh.returncode,refresh_diagnostic=refresh.stderr[:1000])


def snapshot():
    import hashlib,sqlite3
    os.environ.update(environment())
    result={}
    for name,path in dict(config=HOME/'.config/lookup/config.json',database=HOME/'.local/share/lookup/lookup.db',
                         unrelated=HOME/'.local/share/applications/lookup-gsd-unrelated.desktop').items():
        result[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    with sqlite3.connect('file:'+str(HOME/'.local/share/lookup/lookup.db')+'?mode=ro',uri=True) as conn:
        result['seed_word']=list(conn.execute('SELECT word,count,context FROM words WHERE word="publicseed"').fetchone())
        result['seed_card']=list(conn.execute('SELECT word,translation,context FROM cards WHERE word="publicseed"').fetchone())
    result['unrelated_triggered']=(STATE/'unrelated-trigger').exists()
    result['unrelated_trigger_mtime_ns']=(STATE/'unrelated-trigger').stat().st_mtime_ns if result['unrelated_triggered'] else None
    return result


def login_probe(seconds):
    """Read-only: never invokes an app/autostart command while observing login."""
    env=environment();samples=[];started=time.monotonic()
    while True:
        child=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--target','status'],
            env=env,capture_output=True,text=True,timeout=8,check=True)
        value=json.loads(child.stdout);value.pop('fixture',None)
        value['elapsed']=round(time.monotonic()-started,3)
        if value.get('pid'):
            directory=Path('/proc',str(value['pid']))
            value['argv']=directory.joinpath('cmdline').read_bytes().replace(b'\0',b' ').decode().strip()
            value['start_ticks']=directory.joinpath('stat').read_text().split(') ',1)[1].split()[19]
        samples.append(value)
        if time.monotonic()-started>=seconds:break
        time.sleep(2)
    sessions=subprocess.run(['loginctl','list-sessions','--no-legend'],capture_output=True,text=True,check=True).stdout
    graphical=[]
    for line in sessions.splitlines():
        fields=line.split()
        if len(fields)>3 and fields[1:4]==['1001','lookup07','seat0']:
            graphical.append(subprocess.run(['loginctl','show-session',fields[0],'-p','Id','-p','Name','-p','Type',
                '-p','Service','-p','State','-p','Timestamp','-p','Leader'],capture_output=True,text=True,check=True).stdout)
    return dict(samples=samples,graphical_sessions=graphical,observer_never_launched_product=True)


def doctor_probe():
    import hashlib,tempfile
    base=environment();results=[]
    with tempfile.TemporaryDirectory(prefix='doctor-',dir=STATE) as directory:
        root=Path(directory)
        for case in ('healthy','missing_tool','damaged_dictionary','offline'):
            profile=root/case;profile.mkdir();cfg=profile/'config.json';cfg.write_text('{"online":false}')
            env=dict(base,LOOKUP_CONFIG=str(cfg),LOOKUP_DB=str(profile/'absent.db'),LOOKUP_CACHE=str(profile/'cache'),
                XDG_CONFIG_HOME=str(profile/'config'),XDG_CACHE_HOME=str(profile/'cache'),XDG_DATA_HOME=str(profile/'data'),
                LOOKUP_DICTS='/usr/share/lookup/dicts')
            if case=='missing_tool':env['PATH']=str(profile/'absent-bin')
            if case=='damaged_dictionary':
                dictionaries=profile/'dicts';dictionaries.mkdir();(dictionaries/'broken.ifo').write_text('damaged public fixture')
                env['LOOKUP_DICTS']=str(dictionaries)
            def inventory():return {str(path.relative_to(profile)):hashlib.sha256(path.read_bytes()).hexdigest()
                for path in profile.rglob('*') if path.is_file()}
            before=inventory()
            child=subprocess.run(['/usr/bin/lookup','--doctor'],env=env,cwd='/tmp',capture_output=True,text=True,timeout=20)
            unchanged=before==inventory()
            expected=0 if case in ('healthy','offline') else 1
            results.append(dict(case=case,exit=child.returncode,expected_exit=expected,unchanged=unchanged,
                                output=child.stdout,passed=child.returncode==expected and unchanged))
    return dict(cases=results,passed=all(row['passed'] for row in results),profile_removed=not root.exists())


def removed_probe():
    """Read actual registry with system Qt after installed modules are gone."""
    assert os.getuid()==1001 and Path.home()==HOME
    os.environ.update(XDG_RUNTIME_DIR='/run/user/1001',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/1001/bus')
    from PyQt6.QtCore import QCoreApplication,QMetaType
    from PyQt6.QtGui import QKeySequence
    from PyQt6.QtDBus import QDBusConnection,QDBusMessage,QDBusArgument,QDBus
    application=QCoreApplication([]);interface=QDBusConnection.sessionBus().interface();interface.setTimeout(1500)
    owner=interface.isServiceRegistered(SERVICE)
    result=dict(owner=owner.isValid() and owner.value())
    def registry(method,action):
        message=QDBusMessage.createMethodCall('org.kde.kglobalaccel','/kglobalaccel','org.kde.KGlobalAccel',method)
        message.setArguments([QDBusArgument(action,QMetaType.Type.QStringList.value)])
        reply=QDBusConnection.sessionBus().call(message,QDBus.CallMode.Block,1200)
        if reply.type()==QDBusMessage.MessageType.ErrorMessage:raise RuntimeError('registry_unavailable')
        return reply.arguments()[0] if reply.arguments() else []
    actions=registry('allActionsForComponent',['org.lookup.Linux.desktop','','',''])
    owned=[action for action in actions or [] if tuple(action[:2])==('org.lookup.Linux.desktop','_launch')]
    result['keys']=[QKeySequence(key).toString(QKeySequence.SequenceFormat.PortableText)
        for action in owned for key in registry('shortcut',action) if key]
    result['registered_actions']=len(owned)
    if result['owner']:result['pid']=interface.servicePid(SERVICE).value()
    result['remaining_package_files']=[str(path) for path in (Path('/usr/bin/lookup'),Path('/usr/lib/lookup'),
        Path('/usr/share/applications/org.lookup.Linux.desktop'),Path('/etc/xdg/autostart/org.lookup.Linux.desktop'),
        Path('/usr/share/lookup')) if path.exists()]
    import hashlib
    result['retained_hashes']={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in
        dict(config=HOME/'.config/lookup/config.json',database=HOME/'.local/share/lookup/lookup.db',
             unrelated=HOME/'.local/share/applications/lookup-gsd-unrelated.desktop').items()}
    marker=STATE/'unrelated-trigger'
    result['unrelated_trigger_mtime_ns']=marker.stat().st_mtime_ns if marker.exists() else None
    return result


def write_fixture(directory,stem,meaning):
    """One-entry real StarDict fixture; no test suite on the installed import path."""
    import struct
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    data=meaning.encode('utf-8');index=b'bank\0'+struct.pack('>II',0,len(data))
    (directory/(stem+'.dict')).write_bytes(data)
    (directory/(stem+'.idx')).write_bytes(index)
    (directory/(stem+'.ifo')).write_text("StarDict's dict ifo file\nversion=2.4.2\nbookname="+stem+
        '\nwordcount=1\nidxfilesize='+str(len(index))+'\nsametypesequence=m\n',encoding='utf-8')


def native_server():
    """Observe installed Owner; commands operate real widgets, engine and registry.

    Synthetic query/delay and counted offline provider are explicit test seams.
    Physical capture is separately proven with the unmodified installed daemon.
    """
    import threading
    os.environ.update(environment())
    from lookup import gui,app as core,online,config
    from PyQt6.QtCore import QTimer,Qt
    from PyQt6.QtGui import QKeySequence,QPalette,QColor
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtTest import QTest
    Popup,Owner=gui.components()
    release=threading.Event();release.set()
    observed=dict(events=[],network_calls=0,held=False,query=None,cases={},failure_results=[])
    original_resolve=core.Source.resolve
    def resolve(source,frozen,dictset):
        if not release.is_set():
            observed['held']=True
            if not release.wait(20):raise RuntimeError('bounded_test_hold')
            observed['held']=False
        if observed['query'] is not None:return core.Query(observed['query'],None)
        return original_resolve(source,frozen,dictset)
    core.Source.resolve=resolve
    def network(*args,**kwargs):
        observed['network_calls']+=1
        raise online.TranslateError('no_network')
    online.translate_online=network
    class ObservedOwner(Owner):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            self.settings_controller.state.connect(lambda value:observed.update(last_apply=value.get('status'))
                if value.get('kind')=='result' else None)
            self.probe=QTimer(self);self.probe.timeout.connect(self.tick);self.probe.start(100)
            self.last_command=None;self.started=time.monotonic()
        def receive(self,event):
            super().receive(event)
            result=event.result
            observed['events'].append(dict(stage=event.stage,id=event.id,mode=event.mode,
                key=result.key if result else None,translation=result.translation if result else None,
                articles=[a.text for a in result.articles] if result else [],error=event.error,
                revision=event.reload_revision,time=round(time.monotonic(),3)))
            observed['events']=observed['events'][-60:]
        def tick(self):
            path=STATE/'command.json'
            if path.exists():
                command=json.loads(path.read_text())
                if command['id']!=self.last_command:
                    self.last_command=command['id']
                    try:self.execute(command);observed['command_error']=None
                    except Exception as error:observed['command_error']=type(error).__name__
            window=self.settings_window
            visible=self.popup.isVisible()
            if visible!=observed.get('last_popup',False):
                observed.setdefault('popup_changes',[]).append(dict(visible=visible,time=round(time.monotonic(),3)))
                observed['last_popup']=visible
            data=dict(observed,pid=os.getpid(),command=self.last_command,presentations=self.presentations,
                popup=self.popup.isVisible(),popup_duration=self.popup._duration if hasattr(self.popup,'_duration') else None,
                pending=self.settings_controller.pending,identity=self._identity,
                config=dict(online=config.load().online,autostart=config.load().autostart,timeout=config.load().popup_timeout))
            if window is not None:
                data.update(settings_visible=window.isVisible(),status=window.status.text(),
                    folder=window.folder_path.text(),apply_enabled=window.apply_button.isEnabled(),
                    rows=[dict(id=window.dictionaries.item(i).data(Qt.ItemDataRole.UserRole),
                        name=window.dictionaries.item(i).text(),enabled=window.dictionaries.item(i).checkState()==Qt.CheckState.Checked)
                        for i in range(window.dictionaries.count())])
            temporary=STATE/'native-state.tmp';temporary.write_text(json.dumps(data,ensure_ascii=False))
            temporary.replace(STATE/'native-state.json')
            if time.monotonic()-self.started>1800:release.set();self.quit()
        def execute(self,command):
            action=command['action'];window=self.settings_window
            if action=='open':self.open_settings()
            elif action=='apply':
                observed['last_apply']=None
                for name in ('online','autostart'):
                    if name in command:getattr(window,name).setChecked(command[name])
                if 'timeout' in command:window.timeout.setValue(command['timeout'])
                if 'shortcut' in command:window.shortcut.setKeySequence(QKeySequence(command['shortcut']))
                if 'order' in command:
                    for target,name in enumerate(command['order']):
                        index=next(i for i in range(window.dictionaries.count()) if name in window.dictionaries.item(i).text())
                        window.dictionaries.setCurrentRow(index)
                        while index>target:
                            QTest.mouseClick(window.up_button,Qt.MouseButton.LeftButton);index-=1
                if 'enabled' in command:
                    for i in range(window.dictionaries.count()):
                        item=window.dictionaries.item(i)
                        item.setCheckState(Qt.CheckState.Checked if any(name in item.text() for name in command['enabled']) else Qt.CheckState.Unchecked)
                if window.apply_button.isEnabled():QTest.mouseClick(window.apply_button,Qt.MouseButton.LeftButton)
                else:observed['last_apply']='unchanged'
            elif action=='folder':QTest.mouseClick(window.folder_button,Qt.MouseButton.LeftButton)
            elif action=='fixture':write_fixture(Path(window.folder_path.text())/command['stem'],command['stem'],command['meaning'])
            elif action=='query':observed['query']=command.get('text');self.Trigger('')
            elif action=='hold':observed['query']='bank';release.clear();self.Trigger('')
            elif action=='release':release.set()
            elif action=='dismiss':self.dismiss();self.popup.hide()
            elif action=='close':window.close()
            elif action=='appearance':
                dark=command.get('dark',False);palette=QPalette()
                if dark:
                    for role,color in ((QPalette.ColorRole.Window,'#242424'),(QPalette.ColorRole.Base,'#181818'),
                        (QPalette.ColorRole.Text,'#efefef'),(QPalette.ColorRole.WindowText,'#efefef'),
                        (QPalette.ColorRole.Button,'#333333'),(QPalette.ColorRole.ButtonText,'#efefef')):
                        palette.setColor(role,QColor(color))
                QApplication.setPalette(palette);window.resize(command.get('width',600),command.get('height',560))
                window.shortcut.setFocus();QTest.keyClick(window.shortcut,Qt.Key.Key_Tab)
                QApplication.processEvents()
                observed['keyboard_focus']=window.focusWidget() is not None
                observed['device_pixel_ratio']=window.devicePixelRatioF()
                window.grab().save(str(STATE/('settings-dark.png' if dark else 'settings-light.png')))
            elif action=='quit':release.set();self.quit()
            elif action=='status':pass
            elif action=='suite':self.suite()
            elif action=='failure-suite':self.failure_suite()
            else:raise ValueError('unknown_action')
        def wait(self,predicate,seconds=12):
            deadline=time.monotonic()+seconds
            while time.monotonic()<deadline:
                QApplication.processEvents();QTest.qWait(20)
                if predicate():return
            raise TimeoutError('native_case_deadline')
        def suite(self):
            from contextlib import contextmanager
            results={};observed['cases']=results
            self.open_settings();self.wait(lambda:not self.settings_controller.pending)
            window=self.settings_window
            def apply(**changes):
                self.execute(dict(action='apply',**changes))
                self.wait(lambda:not self.settings_controller.pending)
                assert observed.get('last_apply') in ('success','unchanged'),observed.get('last_apply')
            def query(text):
                self.execute(dict(action='query',text=text));identity=self._identity
                self.wait(lambda:any(e['id']==identity and e['stage']=='ready' for e in observed['events']))
                return next(e for e in reversed(observed['events']) if e['id']==identity and e['stage']=='ready')
            apply(order=['public-second','public-first'],enabled=['public-second','public-first'],timeout=2,online=False)
            result=query('bank');assert result['articles']==['SECOND PUBLIC BANK','FIRST PUBLIC BANK']
            apply(enabled=['public-second'])
            result=query('bank');assert result['articles']==['SECOND PUBLIC BANK']
            results['dictionary_order_disable']=True
            apply(online=True)
            query('zxpublicone');before=observed['network_calls'];assert before>0
            apply(online=False)
            query('zxpublictwo');assert observed['network_calls']==before
            results['online_off']=True;observed['online_off_calls']=[before,observed['network_calls']]
            window.close();result=query('bank')
            self.wait(lambda:self.popup.isVisible());started=time.monotonic()
            self.wait(lambda:not self.popup.isVisible(),5)
            elapsed=time.monotonic()-started
            observed['timeout_seconds']=round(elapsed,3)
            assert 1.5<=elapsed<=4,elapsed
            results['popup_timeout']=True
            self.open_settings();self.wait(lambda:not self.settings_controller.pending)
            self.execute(dict(action='hold'));old=self._identity
            self.wait(lambda:observed['held'])
            self.execute(dict(action='apply',timeout=3))
            self.wait(lambda:self.settings_controller.reload_revision is not None)
            assert self.settings_controller.pending
            release.set();self.wait(lambda:not self.settings_controller.pending)
            assert observed['last_apply']=='success'
            assert not any(e['id']==old and e['stage']=='ready' for e in observed['events'])
            results['stale_reload']=True;observed['stale_id']=old
            controller=self.settings_controller;save=controller._save;resources=self.engine._resources
            def fail(_changes):raise config.ConfigError('unavailable')
            try:
                controller._save=fail
                self.execute(dict(action='apply',timeout=4));self.wait(lambda:not controller.pending)
                assert observed['last_apply']=='save_failed'
                controller._save=save
                calls=[0]
                @contextmanager
                def fail_once():
                    calls[0]+=1
                    if calls[0]==1:raise RuntimeError('synthetic_resource_failure')
                    with resources() as value:yield value
                self.engine._resources=fail_once
                self.execute(dict(action='apply',timeout=5));self.wait(lambda:not controller.pending)
                assert observed['last_apply']=='runtime_failed'
                observed['failure_results']=['save_failed','runtime_failed']
            finally:controller._save=save;self.engine._resources=resources;release.set()
            apply(timeout=3,online=False)
            self.execute(dict(action='appearance',dark=False))
            self.execute(dict(action='appearance',dark=True,width=450,height=420))
            assert observed['keyboard_focus']
            results['native_appearance_keyboard']=True
            (STATE/'suite.json').write_text(json.dumps(dict(cases=results,observations=observed),ensure_ascii=False))
        def failure_suite(self):
            from contextlib import contextmanager
            from lookup import lifecycle
            self.open_settings();self.wait(lambda:not self.settings_controller.pending)
            controller=self.settings_controller;window=self.settings_window
            prior=config.load();save=controller._save;restore=controller._restore;resources=self.engine._resources
            failures=[]
            def apply(**changes):
                self.execute(dict(action='apply',**changes));self.wait(lambda:not controller.pending)
                result=observed['last_apply'];failures.append(result)
                window.grab().save(str(STATE/('failure-'+result+'.png')))
                return result
            assert apply(shortcut='Meta+L',timeout=4)=='shortcut_conflict'
            assert lifecycle.inspect_shortcut().keys==(lifecycle.parse_shortcut('Meta+Shift+E')[1],)
            window.shortcut.setKeySequence(QKeySequence('Meta+Shift+E'))
            calls=[0]
            @contextmanager
            def fail_once():
                calls[0]+=1
                if calls[0]==1:raise RuntimeError('controlled_reload_failure')
                with resources() as value:yield value
            def fail(_):raise config.ConfigError('unavailable')
            try:
                self.engine._resources=fail_once;controller._restore=fail
                assert apply(timeout=6)=='rollback_config'
            finally:
                controller._save=save;controller._restore=restore;self.engine._resources=resources
                restore(dict(popup_timeout=prior.popup_timeout,online=prior.online))
                self.engine.request_reload()
            self.wait(lambda:not controller.pending)
            controller.load();self.wait(lambda:not controller.pending)
            registry=controller.registry
            class BrokenRollback:
                def inspect(self):return registry.inspect()
                def change(self,text):
                    transaction=registry.change(text)
                    class Transaction:
                        def commit(self):transaction.commit()
                        def rollback(self):raise lifecycle.LifecycleError('rollback_failed')
                    return Transaction()
            try:
                controller.registry=BrokenRollback();controller._save=fail
                assert apply(shortcut='Meta+Shift+F',timeout=7)=='rollback_shortcut'
            finally:
                controller.registry=registry;controller._save=save
                registry.change('Meta+Shift+E').commit()
            controller.load();self.wait(lambda:not controller.pending)
            # The synthetic missing identity remains visibly retryable.
            missing=dict(id='public-missing/public-missing.ifo',enabled=True)
            config.save(dict(dictionaries=[dict(id=i,enabled=e) for i,e in prior.dictionaries
                if i!=missing['id']]+[missing]),retain_missing=False)
            controller.load();self.wait(lambda:not controller.pending)
            assert any('public-missing' in window.dictionaries.item(i).text() for i in range(window.dictionaries.count()))
            window.grab().save(str(STATE/'settings-missing.png'))
            window.online.setFocus();before=window.online.isChecked();QTest.keyClick(window.online,Qt.Key.Key_Space)
            assert window.online.isChecked()!=before
            window.online.setChecked(False);window.timeout.setValue(prior.popup_timeout+1 if prior.popup_timeout<299 else 2)
            window.apply_button.setFocus();QTest.keyClick(window.apply_button,Qt.Key.Key_Return)
            self.wait(lambda:not controller.pending)
            assert observed['last_apply']=='success'
            observed['failure_results']+=failures;observed['cases']['failure_states']=True
            observed['keyboard_applied']=True
    gui._components=(Popup,ObservedOwner)
    try:return gui.run()
    finally:release.set();core.Source.resolve=original_resolve


def command(encoded):
    import base64
    value=json.loads(base64.b64decode(encoded));value['id']=time.time_ns()
    temporary=STATE/'command.tmp';temporary.write_text(json.dumps(value));temporary.replace(STATE/'command.json')
    deadline=time.monotonic()+45
    while time.monotonic()<deadline:
        path=STATE/'native-state.json'
        if path.exists():
            result=json.loads(path.read_text())
            if result.get('command')==value['id']:return result
        time.sleep(.1)
    raise TimeoutError('native_command_deadline')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--target',choices=('start','status','server-start','seed','snapshot','login','doctor','removed'));parser.add_argument('--fixture',action='store_true')
    parser.add_argument('--observe-seconds',type=int,choices=range(0,21),default=0)
    parser.add_argument('--scale',choices=('1','1.5'),default='1')
    parser.add_argument('--native-server',action='store_true');parser.add_argument('--command')
    args=parser.parse_args()
    if args.fixture:return fixture()
    if args.native_server:return native_server()
    if args.command:print(json.dumps(command(args.command),ensure_ascii=False));return 0
    operations={'start':start,'server-start':lambda:start_server(args.scale),'status':status,'seed':seed,'snapshot':snapshot,
                'login':lambda:login_probe(args.observe_seconds),'doctor':doctor_probe,'removed':removed_probe}
    print(json.dumps(operations[args.target or 'status'](),ensure_ascii=False))


if __name__=='__main__':raise SystemExit(main())
