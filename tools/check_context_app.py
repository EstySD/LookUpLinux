"""Synthetic contextual-flow acceptance; no user history or account data."""
import argparse
import base64
import contextlib
from dataclasses import replace
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import uuid

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

REMOTE = 'LookUpLinux-gsd-context-051'
CASES = [
    ('river','They sat on the bank of the river.',0,'bank','берег'),
    ('finance','She deposited her money in the bank.',0,'bank','банк'),
    ('repeat-river','The bank of the river is next to the bank that holds my savings.',0,'bank','берег'),
    ('repeat-finance','The bank of the river is next to the bank that holds my savings.',1,'bank','банк'),
    ('multiline','They sat on the bank\nof the river and watched\nthe ducks swim past.',0,'bank','берег'),
    ('phrase','The prisoners managed to break out of jail.',0,'break out','вырва'),
    ('fragment','walking by the bank\nnear the river',0,'bank',None),
]
_release=threading.Event()
_release.set()
_state={'case':'live','resources':None}


def selected_span(text,token,occurrence):
    start=-1
    for _ in range(occurrence+1):start=text.index(token,start+1)
    return start,start+len(token)


def write_report(output,report):
    output.mkdir(parents=True,exist_ok=True)
    (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report


def live(output):
    from lookup import context,translate
    from lookup.config import Config
    from lookup.dicts import open_all
    from lookup.store import open_store,get_word_context
    from tests._stardict_writer import write_stardict
    report=dict(acceptance='agent',provider=context.PROVIDER,cases=[],
                limits=['Finite synthetic live corpus; public endpoint is undocumented.',
                        'No human or Phase8 game/performance acceptance.'])
    with tempfile.TemporaryDirectory(prefix='lookup-context-live-') as directory:
        root=Path(directory)
        previous={key:os.environ.get(key) for key in ('LOOKUP_CACHE','LOOKUP_DICTS')}
        os.environ.update(LOOKUP_CACHE=str(root/'cache'),LOOKUP_DICTS=str(root/'dicts'))
        try:
            write_stardict(root/'dicts','public',[('bank','_n. банк; берег'),('break out','_v. вырваться')])
            with contextlib.closing(open_all(Config(),[root/'dicts'])) as dictionaries:
                with contextlib.closing(open_store(root/'history.db')) as conn:
                    for name,text,occurrence,word,expected in CASES:
                        if expected is None:continue
                        span=selected_span(text,word,occurrence)
                        ready=[]
                        value=translate.lookup(word,dictset=dictionaries,conn=conn,context=text,
                            context_span=span,context_complete=True,on_ready=ready.append)
                        stored=get_word_context(conn,word)
                        count=conn.execute('SELECT count FROM words WHERE word=?',(word,)).fetchone()[0]
                        matching=bool(stored and stored['context']==text and stored['span']==span and
                                      stored['meaning']==value.context_meaning and stored['provider']==value.meaning_provider)
                        passed=bool(value.context_meaning and expected in value.context_meaning.lower() and
                                    matching and ready and ready[0].articles and ready[0].meaning_pending and
                                    not ready[0].context_meaning and value.count==count)
                        report['cases'].append(dict(name=name,passed=passed,meaning=value.context_meaning,
                            meaning_error=value.meaning_error,matching_pair=matching,count=count,
                            first_useful_ms=value.timings.get('first_useful'),meaning_ready_ms=value.timings.get('meaning_ready')))
                    # Cache reuse and offline suppression use production orchestration.
                    _,text,occurrence,word,_=CASES[0]
                    cached=translate.lookup(word,dictset=dictionaries,conn=conn,context=text,
                        context_span=selected_span(text,word,occurrence),context_complete=True,save=False)
                    offline=translate.lookup(word,dictset=dictionaries,conn=conn,context=text,
                        context_span=selected_span(text,word,occurrence),context_complete=True,online=False,save=False)
                    report['cache_reused']=bool(cached.meaning_from_cache and cached.context_meaning)
                    report['offline_article_retained']=bool(offline.articles and offline.meaning_error=='disabled')
        finally:
            for key,value in previous.items():
                if value is None:os.environ.pop(key,None)
                else:os.environ[key]=value
    report['passed']=all(case['passed'] for case in report['cases']) and report['cache_reused'] and report['offline_article_retained']
    return write_report(output,report)


def fixture(run_id):
    from lookup import platform
    os.environ.update(platform.session_env())
    from tools import check_app
    from PyQt6.QtCore import QObject,QPointF,Qt,pyqtClassInfo,pyqtSlot
    from PyQt6.QtGui import QFont,QPainter
    from PyQt6.QtWidgets import QApplication,QWidget
    from PyQt6.QtDBus import QDBusConnection
    application=QApplication([])
    class Scene(QWidget):
        index=4
        def __init__(self):
            super().__init__()
            self.setWindowTitle('LookUp public contextual fixture')
            self.setWindowFlags(Qt.WindowType.Window|Qt.WindowType.FramelessWindowHint)
            font=QFont('Noto Sans');font.setPixelSize(26);self.setFont(font)
        def paintEvent(self,event):
            painter=QPainter(self);painter.fillRect(self.rect(),self.palette().window())
            painter.setPen(self.palette().windowText().color());painter.setFont(self.font())
            for row,line in enumerate(CASES[self.index][1].splitlines()):
                painter.drawText(QPointF(140,210+row*36),line)
        def point(self):
            _,text,occurrence,word,_=CASES[self.index]
            start,end=selected_span(text,word,occurrence)
            row=text[:start].count('\n');prefix=text[:start].rsplit('\n',1)[-1]
            metrics=self.fontMetrics()
            point=self.mapToGlobal(self.rect().topLeft())
            return [point.x()+140+metrics.horizontalAdvance(prefix)+metrics.horizontalAdvance(word)/2,
                    point.y()+210+row*36-metrics.ascent()/2]
    window=Scene();window.showMaximized()
    @pyqtClassInfo('D-Bus Interface',check_app.FIXTURE)
    class Fixture(QObject):
        @pyqtSlot(result=str)
        def Status(self):
            point=window.point()
            return json.dumps(dict(pid=os.getpid(),run_id=run_id,point=point,other_point=point,span=[point,point],case=window.index))
        @pyqtSlot(int,result=bool)
        def Case(self,index):
            if not 0<=index<len(CASES):return False
            window.index=index;window.update();return True
        @pyqtSlot(result=bool)
        def Quit(self):application.quit();return True
    service=Fixture();bus=QDBusConnection.sessionBus()
    if not bus.registerService(check_app.FIXTURE):return 1
    bus.registerObject('/Fixture',service,QDBusConnection.RegisterOption.ExportAllSlots)
    return application.exec()


def owner(run_id):
    from lookup import app,context,gui,online
    from lookup import platform
    from tools import check_app
    root=check_app.profile(run_id)
    # Force the owned OCR scenario without reading or changing existing PRIMARY.
    platform.read_primary=lambda *args,**kwargs:None
    (root/'config.json').write_text('{"online":true}')
    original_resources=app._resources
    @contextlib.contextmanager
    def resources():
        with original_resources() as value:
            _state['resources']=value
            try:yield value
            finally:_state['resources']=None
    app._resources=resources
    def meaning(request):
        if _state['case']=='delay':_release.wait(12)
        if _state['case']=='no_network':raise online.TranslateError('no_network')
        # Native lifecycle uses an explicit finite oracle; live transport is
        # independently exercised by live(). No production guesser is installed.
        for _,text,occurrence,word,expected in CASES:
            if request.context==text and (request.start,request.end)==selected_span(text,word,occurrence):
                return context.ContextResult('вырваться' if expected=='вырва' else expected,request.provider)
        raise online.TranslateError('bad_response')
    context.translate_context=meaning
    # Sentence translation is independently controlled here; contextual calls stay live.
    online.translate_online=lambda *args,**kwargs:online.OnlineResult('google','gtx','Публичный контекст',(),None,None,'en')
    original_components=gui.components
    def components():
        Popup,Owner=original_components()
        from PyQt6.QtCore import QObject,QTimer,pyqtClassInfo,pyqtSlot
        from PyQt6.QtDBus import QDBusConnection
        @pyqtClassInfo('D-Bus Interface',check_app.PROBE)
        class Probe(QObject):
            def __init__(self,owner):super().__init__(owner);self.owner=owner
            @pyqtSlot(result=str)
            def Status(self):
                current=self.owner;event=getattr(current,'observed',None);value=event.result if event else None
                row=None
                if (root/'history.db').exists():
                    with sqlite3.connect(root/'history.db') as conn:
                        row=conn.execute('SELECT word,count,context,context_start,context_end,context_meaning,context_provider FROM words WHERE word="bank"').fetchone()
                return json.dumps(dict(pid=os.getpid(),run_id=run_id,identity=current._identity,
                    event_id=event.id if event else None,
                    visible=current.popup.isVisible(),armed=current.popup._armed,uuid=current.popup_uuid,
                    stage=event.stage if event else None,mode=event.mode if event else None,
                    key=(value.key if value.key in ('bank','break out') else 'unexpected') if value else None,count=value.count if value else None,
                    meaning=value.context_meaning if value else None,meaning_pending=value.meaning_pending if value else False,
                    meaning_error=value.meaning_error if value else None,
                    context_complete=value.context_complete if value else False,
                    limited_fragment=not current.popup.context_fragment.isHidden(),
                    background=current.popup.palette().window().color().name(),
                    context=(event.context if event.context and any(event.context in case[1] for case in CASES) else 'unexpected') if event else None,
                    stored=row,first_useful_ms=getattr(current,'useful',None),
                    meaning_ready_ms=value.timings.get('meaning_ready') if value else None,
                    article_visible=bool(value and value.articles),error=event.error if event else None))
            @pyqtSlot(str,result=bool)
            def Configure(self,case):
                resources=_state['resources']
                if resources is None or case not in ('live','offline','delay','no_network'):return False
                _state['case']=case
                resources.config=replace(resources.config,online=case!='offline')
                if case=='delay':_release.clear()
                else:_release.set()
                return True
            @pyqtSlot(result=bool)
            def Release(self):_release.set();return True
            @pyqtSlot(result=bool)
            def Dismiss(self):self.owner.popup.dismiss();return True
            @pyqtSlot(result=bool)
            def Quit(self):_release.set();self.owner.quit();return True
            @pyqtSlot(result=str)
            def Shot(self):
                from PyQt6.QtCore import QBuffer,QIODevice
                buffer=QBuffer();buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                self.owner.popup.grab().save(buffer,'PNG')
                return base64.b64encode(bytes(buffer.data())).decode()
        @pyqtClassInfo('D-Bus Interface',gui.SERVICE)
        class ObservedOwner(Owner):
            def __init__(self,*args,**kwargs):
                super().__init__(*args,**kwargs);self.probe=Probe(self)
                bus=QDBusConnection.sessionBus()
                if not bus.registerService(check_app.PROBE):raise RuntimeError('probe_busy')
                bus.registerObject('/Probe',self.probe,QDBusConnection.RegisterOption.ExportAllSlots)
            def receive(self,event):
                if self.engine.current(event.id):
                    self.observed=event
                    if event.stage=='frozen':self.useful=None
                    if event.stage=='ready':
                        QTimer.singleShot(0,lambda:setattr(self,'useful',event.elapsed_ms) if self.popup.isVisible() else None)
                super().receive(event)
        return Popup,ObservedOwner
    gui.components=components
    return gui.run(False)


def target(action,payload):
    from tools import check_app
    check_app.REMOTE=REMOTE
    if action=='shot':
        from lookup import platform
        os.environ.update(platform.session_env())
        from PyQt6.QtCore import QCoreApplication
        from PyQt6.QtDBus import QDBusConnection,QDBusMessage,QDBus
        application=QCoreApplication([])
        msg=QDBusMessage.createMethodCall(check_app.PROBE,'/Probe',check_app.PROBE,'Shot')
        reply=QDBusConnection.sessionBus().call(msg,QDBus.CallMode.Block,2000)
        return reply.arguments()[0]
    if action!='prepare':return check_app.target(action,payload)
    original_popen=subprocess.Popen
    def launch(argv,**kwargs):
        argv=list(argv)
        if '--fixture' not in argv and argv[-3:]!=['-m','lookup','--app']:
            return original_popen(argv,**kwargs)
        env=dict(kwargs['env'])
        env['PYTHONPATH']=str(Path(__file__).resolve().parents[1])
        root=check_app.profile(payload['run_id'])
        from tests._stardict_writer import write_stardict
        write_stardict(root/'dicts','contextual',[('bank','_n. банк; берег')],bookname='Public Context Dictionary')
        if '--fixture' in argv:argv=[sys.executable,str(Path(__file__).resolve()),'--fixture','--run-id',payload['run_id']]
        elif argv[-3:]==['-m','lookup','--app']:argv=[sys.executable,str(Path(__file__).resolve()),'--owner','--run-id',payload['run_id']]
        kwargs['env']=env
        return original_popen(argv,**kwargs)
    subprocess.Popen=launch
    try:return check_app.target(action,payload)
    finally:subprocess.Popen=original_popen


def remote(action,payload):
    encoded=base64.b64encode(json.dumps(payload).encode()).decode()
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=5','archvm',
        f'cd {REMOTE} && python tools/check_context_app.py --target {action} --payload {encoded}'],
        capture_output=True,text=True,timeout=45)
    if result.returncode:raise RuntimeError(action+':'+result.stderr[-250:])
    return json.loads(result.stdout)


def host(output):
    from tools.check_vm_spike import keys,move_pointer,wait_for
    run_id=uuid.uuid4().hex
    report=dict(acceptance='agent',run_id=run_id,gates={},observations={},
                limits=['Native VM hotkey/capture/OCR, Engine, UI and storage; both network replies controlled.',
                        'Contextual replies held until explicit release; timings measure the controlled scenario.',
                        'Live production provider verified separately on host; VM public endpoint returned429.',
                        'Single monitor; no human, game or Phase8 performance acceptance.'])
    def request(action,**values):return remote(action,dict(run_id=run_id,**values))
    def observe(name,predicate,timeout=15):
        print('gate: '+name,flush=True)
        status=wait_for(lambda:request('status'),lambda value:
                       value.get('event_id')==value.get('identity') and predicate(value),timeout)
        report['observations'][name]=status;return status
    def trigger(index):
        fixture=request('fixture',case=index)
        move_pointer(fixture['point'],fixture['scale'],lambda action:request(action))
        before=request('status')['identity'] or 0
        keys('e0 5b 2a 20 a0 aa e0 db')
        return before
    try:
        request('prepare')
        observe('owner_ready',lambda s:s['identity'] is None)
        request('configure',case='delay');before=trigger(4)
        early=observe('offline_early',lambda s:(s['identity'] or 0)>before and s['stage']=='ready' and s['article_visible'])
        request('release')
        final=observe('live_multiline',lambda s:s['meaning'] and 'берег' in s['meaning'].lower())
        report['gates']['physical_hotkey_capture_ocr']=final['mode']=='ocr' and final['visible'] and '\n' in final['context']
        report['gates']['one_count_matching_pair']=bool(final['stored'] and final['stored'][1]==early['stored'][1]==1 and final['stored'][2]==final['context'] and final['stored'][5]==final['meaning'])
        report['gates']['independent_timings']=bool(early['first_useful_ms'] and final['meaning_ready_ms']>early['first_useful_ms'])
        output.mkdir(parents=True,exist_ok=True)
        (output/'native-light.png').write_bytes(base64.b64decode(request('shot')))
        request('dismiss');request('configure',case='delay');before=trigger(1)
        pending=observe('delayed_early',lambda s:(s['identity'] or 0)>before and s['stage']=='ready' and s['meaning_pending'])
        request('dismiss');request('release');time.sleep(2)
        closed=request('status')
        report['observations']['closed_after_release']=closed
        report['gates']['closed_reply_ignored']=not closed['visible'] and closed['stored'][5] is None and closed['stored'][1]==pending['stored'][1]
        request('configure',case='delay');before=trigger(2)
        observe('older_pending',lambda s:(s['identity'] or 0)>before and s['meaning_pending'])
        request('fixture',case=3);request('release');before=trigger(3)
        newer=observe('newer_result',lambda s:(s['identity'] or 0)>before and s['stage']=='context' and s['meaning'] and 'банк' in s['meaning'].lower())
        report['gates']['newer_occurrence_wins']=bool(newer['stored'][5]==newer['meaning'] and newer['stored'][3]>30)
        request('dismiss');request('configure',case='offline');before=trigger(0)
        offline=observe('online_disabled',lambda s:(s['identity'] or 0)>before and s['stage']=='context')
        report['gates']['disabled_keeps_article']=offline['article_visible'] and offline['meaning_error']=='disabled'
        request('dismiss');request('configure',case='no_network');before=trigger(5)
        failed=observe('no_network',lambda s:(s['identity'] or 0)>before and s['stage']=='context')
        report['gates']['no_network_keeps_article']=failed['article_visible'] and failed['meaning_error']=='no_network'
        request('dismiss');request('scale',scale=1.25);request('theme',theme='BreezeDark')
        request('configure',case='offline');before=trigger(6)
        fragment=observe('dark_fragment_125',lambda s:(s['identity'] or 0)>before and s['stage']=='context' and s['visible'])
        (output/'native-dark-fragment-125.png').write_bytes(base64.b64decode(request('shot')))
        report['gates']['native_dark_fragment']=fragment['limited_fragment'] and not fragment['context_complete']
    except Exception as error:
        report['error']=type(error).__name__+':'+str(error)[:200]
        if hasattr(error,'last'):report['last_observation']=error.last
    finally:
        try:report['restoration']=request('finish')
        except Exception as error:report['restoration_error']=type(error).__name__
    restored=report.get('restoration',{})
    report['passed']=bool(report['gates']) and all(report['gates'].values()) and not report.get('error') and not report.get('restoration_error') and not restored.get('errors') and all(restored.get(key) for key in ('display_restored','theme_unchanged','desktop_restored','processes_stopped','shortcut_restored'))
    return write_report(output,report)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path)
    parser.add_argument('--host',action='store_true')
    parser.add_argument('--target');parser.add_argument('--payload')
    parser.add_argument('--owner',action='store_true');parser.add_argument('--fixture',action='store_true')
    parser.add_argument('--run-id')
    args=parser.parse_args()
    if args.owner:return owner(args.run_id)
    if args.fixture:return fixture(args.run_id)
    if args.target:
        print(json.dumps(target(args.target,json.loads(base64.b64decode(args.payload)))));return 0
    if args.output is None:parser.error('--output required')
    report=host(args.output) if args.host else live(args.output)
    print(json.dumps({key:report[key] for key in ('acceptance','passed')}))
    return int(not report['passed'])


if __name__=='__main__':raise SystemExit(main())
