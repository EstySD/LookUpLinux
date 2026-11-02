"""Observable request identity, resource ownership and history invariants."""
import contextlib
import sqlite3
import threading
import time
import unittest
from unittest.mock import patch

from lookup import app, config, translate, context as contextual, ocr, capture
from lookup.platform import Monitor
from lookup.store import open_store, get_word_context
from tests._support import make_tempdir, forbid_network
from tests.test_translate_ready import Dictionary, ANSWER

MONITOR=Monitor('public',0,0,1000,800,1)


class FixedSource:
    def __init__(self,text='word'):
        self.text=text
    def freeze(self):
        return app.Frozen('primary',(50,50),MONITOR,text=self.text)
    def resolve(self,frozen,dictset):
        return app.Query(frozen.text,frozen.text)
    def consume(self,frozen):
        pass


def fallback_source():
    """Real recognition with fixed public pixels; only the child process is controlled."""
    from PyQt6.QtCore import QBuffer,QIODevice
    from PyQt6.QtGui import QImage,QColor
    from lookup.capture import Capture
    image=QImage(200,80,QImage.Format.Format_RGB32);image.fill(QColor('white'))
    buffer=QBuffer();buffer.open(QIODevice.OpenModeFlag.WriteOnly);image.save(buffer,'PNG')
    frame=Capture(bytes(buffer.data()),200,80,'test',0)
    class Source(app.Source):
        def freeze(self):return app.Frozen('ocr',(25,25),Monitor('test',0,0,200,80,1),image=frame)
    return Source({})


class EngineCase(unittest.TestCase):
    def setUp(self):
        self.root=make_tempdir(self)
        self.network=forbid_network(self)
        self.path=self.root/'history.db'
        self.events=[]
        self.event=threading.Event()
        self.owners=[]
    @contextlib.contextmanager
    def resources(self):
        self.owners.append(('open',threading.get_ident()))
        owners=self.owners
        class SpyDictionary(Dictionary):
            def find(self,key):
                owners.append(('find',threading.get_ident()))
                return super().find(key)
        conn=open_store(self.path)
        conn.execute('PRAGMA busy_timeout=50')
        try:yield app.Resources(config.Config(online=False),SpyDictionary(),conn)
        finally:
            self.owners.append(('close',threading.get_ident()))
            conn.close()
    def engine(self,source=None,lookup=None,resources=None):
        def publish(event):
            self.events.append(event)
            self.event.set()
        engine=app.Engine(publish,source=source or FixedSource(),resources=resources or self.resources,lookup=lookup)
        def close():
            engine.stop();engine.join(2)
            self.assertFalse(engine.is_alive())
        self.addCleanup(close)
        return engine
    def wait(self,predicate):
        deadline=time.monotonic()+2
        while time.monotonic()<deadline:
            self.event.clear()
            if predicate():return
            self.event.wait(.05)
        self.fail('observable engine state did not arrive')
    def count(self):
        with contextlib.closing(open_store(self.path)) as conn:
            return conn.execute('SELECT coalesce(sum(count),0) FROM words').fetchone()[0]

class SceneSource(FixedSource):
    def __init__(self):
        self.frame=capture.Capture(b'public test pixels',1000,800,'test',0)
        self.freezes=[]
        self.resolved=[]
    def freeze(self,snapshot=None):
        self.freezes.append(snapshot)
        return app.Frozen('ocr',(50,50),MONITOR,image=self.frame,available=(0,0,1000,800))
    def resolve(self,frozen,dictset):
        self.resolved.append(frozen)
        text='word' if frozen.point[0]<100 else 'river'
        return app.Query(text,'The word flows.',timings={'capture':7},span=(4,8),selection_box=(40,40,30,20))


class SceneTests(EngineCase):
    @staticmethod
    def lookup(text,**kwargs):
        return translate.Result('word',text,translation='meaning')

    def test_one_scene_reuses_exact_frame_and_existing_history_for_each_point(self):
        source=SceneSource()
        engine=self.engine(source=source,lookup=self.lookup)
        first=engine.begin();engine.enqueue_scene(first)
        self.wait(lambda:any(e.id==first and e.stage=='context' for e in self.events))
        scene_event=next(e for e in self.events if e.stage=='scene')
        scene=scene_event.scene
        self.assertIsInstance(scene,app.Scene)
        self.assertIs(scene.source.image,source.frame)
        self.assertEqual([e.stage for e in self.events],['scene','frozen','ready','context'])
        next_id=engine.begin()
        self.assertTrue(engine.select_scene(next_id,scene.session_id,(150,50)))
        self.wait(lambda:any(e.id==next_id and e.stage=='context' for e in self.events))
        self.assertEqual(len(source.freezes),1)
        self.assertEqual([f.point for f in source.resolved],[(50,50),(150,50)])
        self.assertTrue(all(f.image is source.frame for f in source.resolved))
        self.assertEqual(len([e for e in self.events if e.stage=='scene']),1)
        self.assertEqual(self.count(),2)
        ready=[e for e in self.events if e.stage=='ready']
        self.assertEqual([e.result.key for e in ready],['word','river'])
        self.assertEqual([e.selection_box for e in ready],[(40,40,30,20)]*2)
        self.assertEqual([e.result.timings['capture'] for e in ready],[7,0])

    def test_invalid_or_oversized_frame_is_not_published_or_retained(self):
        for frame in (None,capture.Capture(b'png',0,800,'test',0),
                      capture.Capture(b'png',16385,1,'test',0),
                      capture.Capture(b'png',10000,10000,'test',0),
                      capture.Capture('not bytes',1000,800,'test',0),
                      capture.Capture(b'oversized',1000,800,'test',0)):
            with self.subTest(frame=frame),patch.object(capture,'MAX_PNG',4):
                self.events.clear()
                source=SceneSource();source.frame=frame
                engine=self.engine(source=source,lookup=self.lookup)
                identity=engine.begin();engine.enqueue_scene(identity)
                self.wait(lambda:any(e.stage=='error' for e in self.events))
                self.assertEqual(next(e.error for e in self.events if e.stage=='error'),'capture_failed')
                self.assertFalse(any(e.stage=='scene' for e in self.events))
                self.assertFalse(engine.select_scene(engine.begin(),identity,(50,50)))
                self.assertEqual(self.count(),0)
                engine.stop();engine.join(2)

    def test_primary_scene_request_preserves_normal_path_without_scene(self):
        engine=self.engine()
        identity=engine.begin();engine.enqueue_scene(identity)
        self.wait(lambda:any(e.stage=='context' for e in self.events))
        self.assertEqual([e.stage for e in self.events],['frozen','ready','context'])
        self.assertFalse(engine.select_scene(engine.begin(),identity,(50,50)))
        self.assertEqual(self.count(),1)

    def test_wrong_session_or_invalid_point_never_resolves_or_writes(self):
        source=SceneSource();engine=self.engine(source=source,lookup=self.lookup)
        identity=engine.begin();engine.enqueue_scene(identity)
        self.wait(lambda:any(e.stage=='context' for e in self.events))
        scene=next(e.scene for e in self.events if e.stage=='scene')
        identity=engine.begin()
        self.assertFalse(engine.select_scene(identity,scene.session_id+1,(50,50)))
        self.assertFalse(engine.select_scene(identity,True,(50,50)))
        self.assertFalse(engine.select_scene(identity,float(scene.session_id),(50,50)))
        for point in (None,(float('nan'),50),(float('inf'),50),(10**1000,50),(-1,0),(1000,50),(50,800),('50',50),(True,50),(50,)):
            with self.subTest(point=point):
                self.assertFalse(engine.select_scene(identity,scene.session_id,point))
        self.assertEqual(len(source.resolved),1)
        self.assertEqual(self.count(),1)

    def test_close_scene_invalidates_held_lookup_and_rejects_stale_session(self):
        entered,release,finished=threading.Event(),threading.Event(),threading.Event()
        self.addCleanup(release.set)
        def lookup(text,**kwargs):
            entered.set();release.wait(2)
            value=self.lookup(text,**kwargs)
            kwargs['on_ready'](value)
            finished.set()
            return value
        engine=self.engine(source=SceneSource(),lookup=lookup)
        self.addCleanup(release.set)
        identity=engine.begin();engine.enqueue_scene(identity)
        self.assertTrue(entered.wait(1))
        scene=next(e.scene for e in self.events if e.stage=='scene')
        self.assertFalse(engine.close_scene(scene.session_id+1))
        self.assertTrue(engine.current(identity))
        self.assertTrue(engine.close_scene(scene.session_id))
        self.assertFalse(engine.current(identity))
        release.set();self.assertTrue(finished.wait(1))
        self.assertEqual(self.count(),0)
        self.assertFalse(any(e.stage in ('ready','context') for e in self.events))
        self.assertFalse(engine.select_scene(engine.begin(),scene.session_id,(50,50)))

    def test_new_selection_suppresses_old_ready_and_context_on_same_frame(self):
        entered,release=threading.Event(),threading.Event()
        self.addCleanup(release.set)
        def lookup(text,**kwargs):
            if text=='word':entered.set();release.wait(2)
            value=self.lookup(text,**kwargs)
            kwargs['on_ready'](value)
            return value
        source=SceneSource();engine=self.engine(source=source,lookup=lookup)
        first=engine.begin();engine.enqueue_scene(first)
        self.assertTrue(entered.wait(1))
        scene=next(e.scene for e in self.events if e.stage=='scene')
        latest=engine.begin();self.assertTrue(engine.select_scene(latest,scene.session_id,(150,50)))
        release.set()
        self.wait(lambda:any(e.id==latest and e.stage=='context' for e in self.events))
        self.assertEqual([e.id for e in self.events if e.stage in ('ready','context')],[latest,latest])
        self.assertEqual(self.count(),1)
        self.assertEqual(len(source.freezes),1)
        with contextlib.closing(open_store(self.path)) as conn:
            self.assertEqual(conn.execute('SELECT word,context FROM words').fetchall(),[('river','The word flows.')])

    def test_scene_frame_released_on_close_dismiss_reload_and_stop(self):
        import weakref
        for action in ('close','dismiss','reload','stop'):
            with self.subTest(action=action):
                self.events.clear()
                frame=capture.Capture(b'public pixels',1000,800,'test',0)
                reference=weakref.ref(frame);frames=[frame];del frame
                class Source(FixedSource):
                    def freeze(self):return app.Frozen('ocr',(50,50),MONITOR,image=frames.pop())
                    def resolve(self,frozen,dictset):return app.Query('word','word')
                engine=self.engine(source=Source(),lookup=self.lookup)
                identity=engine.begin();engine.enqueue_scene(identity)
                self.wait(lambda:any(e.stage=='context' for e in self.events))
                session_id=next(e.scene.session_id for e in self.events if e.stage=='scene')
                self.events.clear()
                self.assertIsNotNone(reference())
                if action=='close':engine.close_scene(session_id)
                elif action=='dismiss':engine.dismiss(identity)
                elif action=='reload':
                    revision=engine.request_reload()
                    self.wait(lambda:any(e.reload_revision==revision for e in self.events))
                else:engine.stop();engine.join(2)
                self.assertIsNone(reference())
                engine.stop();engine.join(2)

    def test_close_releases_queued_raw_capture_before_resources_open(self):
        import weakref
        opened,release=threading.Event(),threading.Event()
        self.addCleanup(release.set)
        @contextlib.contextmanager
        def resources():
            opened.set();release.wait(2)
            with self.resources() as value:yield value
        class Snapshot:pass
        snapshot=Snapshot();reference=weakref.ref(snapshot)
        engine=self.engine(resources=resources)
        self.addCleanup(release.set)
        self.assertTrue(opened.wait(1))
        identity=engine.begin();engine.enqueue_scene(identity,snapshot)
        del snapshot
        engine.close_scene()
        self.assertIsNone(reference())
        release.set()
        engine.stop();engine.join(2)
        self.assertEqual(self.events,[])

    def test_no_hit_keeps_scene_but_operational_failure_releases_it(self):
        class Source(SceneSource):
            def resolve(self,frozen,dictset):
                if frozen.point[0]<100:raise app.AppError('not_found')
                if frozen.point[0]>=200:raise ocr.OcrError('timeout')
                return super().resolve(frozen,dictset)
        engine=self.engine(source=Source(),lookup=self.lookup)
        identity=engine.begin();engine.enqueue_scene(identity)
        self.wait(lambda:any(e.id==identity and e.stage=='error' for e in self.events))
        scene=next(e.scene for e in self.events if e.stage=='scene')
        self.assertEqual(next(e.error for e in self.events if e.stage=='error'),'not_found')
        identity=engine.begin();self.assertTrue(engine.select_scene(identity,scene.session_id,(150,50)))
        self.wait(lambda:any(e.id==identity and e.stage=='context' for e in self.events))
        identity=engine.begin();self.assertTrue(engine.select_scene(identity,scene.session_id,(250,50)))
        self.wait(lambda:any(e.id==identity and e.stage=='error' for e in self.events))
        self.assertEqual(next(e.error for e in self.events if e.id==identity and e.stage=='error'),'ocr_timeout')
        self.assertFalse(engine.select_scene(engine.begin(),scene.session_id,(150,50)))


class EngineTests(EngineCase):
    def test_raw_snapshot_is_released_before_translation_and_worker_idle(self):
        import weakref
        class Snapshot:pass
        snapshot=Snapshot();reference=weakref.ref(snapshot)
        class Source(FixedSource):
            def freeze(self,snapshot=None):return super().freeze()
        observed=[]
        def lookup(text,**kwargs):
            observed.append(reference() is None)
            return translate.Result('word',text,translation='meaning')
        opened,release=threading.Event(),threading.Event()
        self.addCleanup(release.set)
        @contextlib.contextmanager
        def resources():
            opened.set();release.wait(2)
            with self.resources() as value:yield value
        engine=self.engine(source=Source(),lookup=lookup,resources=resources)
        self.assertTrue(opened.wait(1))
        identity=engine.begin();engine.enqueue(identity,snapshot)
        del snapshot
        release.set()
        self.wait(lambda:any(e.stage=='context' for e in self.events))
        self.assertEqual(observed,[True])
        self.assertIsNone(reference())
    def test_failed_resources_do_not_retain_raw_snapshot_while_worker_is_idle(self):
        import weakref
        class Snapshot:pass
        snapshot=Snapshot();reference=weakref.ref(snapshot)
        @contextlib.contextmanager
        def resources():
            raise OSError('controlled unavailable resources')
            yield
        engine=self.engine(resources=resources)
        identity=engine.begin();engine.enqueue(identity,snapshot)
        del snapshot
        self.wait(lambda:any(e.stage=='error' for e in self.events))
        self.assertIsNone(reference())
    def test_request_snapshot_survives_resource_initialization_and_live_source_changes(self):
        opened,release=threading.Event(),threading.Event()
        self.addCleanup(release.set)
        @contextlib.contextmanager
        def resources():
            opened.set();release.wait(2)
            with self.resources() as value:yield value
        class Source(FixedSource):
            def freeze(self,snapshot=None):
                return snapshot if snapshot is not None else super().freeze()
        source=Source('later')
        engine=self.engine(source=source,resources=resources)
        self.assertTrue(opened.wait(1))
        identity=engine.begin()
        snapshot=app.Frozen('primary',(50,50),MONITOR,text='word')
        engine.enqueue(identity,snapshot)
        source.text='changed again'
        release.set()
        self.wait(lambda:any(e.stage=='ready' for e in self.events))
        ready=next(e for e in self.events if e.stage=='ready')
        self.assertEqual(ready.result.key,'word')
        self.assertEqual(ready.point,(50,50))

    def test_held_second_ocr_pass_preserves_generation_reload_stop_and_one_count(self):
        import subprocess
        from tests.test_ocr import tsv
        try:source=fallback_source()
        except ImportError:self.skipTest('PyQt6 unavailable')
        for action in ('replace','dismiss','reload','stop','current'):
            with self.subTest(action=action):
                with contextlib.closing(open_store(self.path)) as conn:conn.execute('DELETE FROM words')
                self.events.clear();entered=threading.Event();release=threading.Event();calls=[]
                self.addCleanup(release.set)
                def child(argv,**kwargs):
                    output=tsv()
                    if argv[6]=='11':
                        entered.set();release.wait(3)
                        output=tsv((5,1,1,1,1,1,48,48,60,20,95,'word'))
                    return subprocess.CompletedProcess(argv,0,output,b'')
                def lookup(*args,**kwargs):calls.append(args[0]);return translate.lookup(*args,**kwargs)
                with patch.object(ocr.subprocess,'run',side_effect=child):
                    engine=self.engine(source=source,lookup=lookup)
                    first=engine.begin();engine.enqueue(first)
                    self.assertTrue(entered.wait(1));self.assertEqual(calls,[])
                    if action=='replace':
                        latest=engine.begin();engine.enqueue(latest)
                    elif action=='dismiss':engine.dismiss(first)
                    elif action=='reload':revision=engine.request_reload()
                    elif action=='stop':
                        engine.stop();engine.join(.03);self.assertTrue(engine.is_alive())
                    release.set()
                    if action=='reload':self.wait(lambda:any(e.stage=='reload' and e.reload_revision==revision for e in self.events))
                    elif action in ('replace','current'):
                        wanted=latest if action=='replace' else first
                        self.wait(lambda:any(e.id==wanted and e.stage=='ready' for e in self.events))
                    engine.stop();engine.join(2);self.assertFalse(engine.is_alive())
                self.assertEqual(self.count(),1 if action in ('replace','current') else 0)
                self.assertEqual(len(calls),1 if action in ('replace','current') else 0)
                if action!='current':self.assertFalse(any(e.id==first and e.stage in ('ready','context') for e in self.events))

    def test_ready_and_final_count_once_on_worker_thread(self):
        engine=self.engine()
        identity=engine.begin();engine.enqueue(identity)
        self.wait(lambda:any(e.stage=='context' for e in self.events))
        self.assertEqual([e.stage for e in self.events],['frozen','ready','context'])
        self.assertEqual(self.count(),1)
        for event in self.events[1:]:
            self.assertEqual(event.result.count,1)
            self.assertTrue(event.result.saved)
        engine.stop();engine.join(2)
        self.assertEqual(len(set(owner for _,owner in self.owners)),1)
        self.assertNotEqual(self.owners[0][1],threading.get_ident())

    def test_replacement_and_dismiss_before_ready_never_write_stale_history(self):
        for dismiss in (False,True):
            with self.subTest(dismiss=dismiss):
                entered,release,completed=threading.Event(),threading.Event(),threading.Event()
                def lookup(text,**kwargs):
                    entered.set();release.wait(2)
                    value=translate.Result('word',text,translation='meaning')
                    kwargs['on_ready'](value)
                    completed.set()
                    return value
                engine=self.engine(lookup=lookup)
                first=engine.begin();engine.enqueue(first)
                self.assertTrue(entered.wait(1))
                if dismiss:engine.dismiss(first)
                else:engine.begin()
                release.set()
                self.assertTrue(completed.wait(1))
                self.assertEqual(self.count(),0)
                self.assertFalse(any(e.stage=='ready' for e in self.events))
                engine.stop();engine.join(2)
                self.events.clear()

    def test_burst_retains_only_latest_and_stale_ready_is_suppressed(self):
        entered,release=threading.Event(),threading.Event()
        calls=[]
        def lookup(text,**kwargs):
            calls.append(text)
            if len(calls)==1:
                entered.set();release.wait(2)
            result=translate.Result('word',text,translation='meaning')
            kwargs['on_ready'](result)
            return result
        engine=self.engine(lookup=lookup)
        first=engine.begin();engine.enqueue(first)
        self.assertTrue(entered.wait(1))
        for _ in range(15):
            latest=engine.begin();engine.enqueue(latest)
        release.set()
        self.wait(lambda:any(e.id==latest and e.stage=='context' for e in self.events))
        self.assertEqual(len(calls),2)
        self.assertEqual(self.count(),1)
        self.assertEqual([e.id for e in self.events if e.stage=='ready'],[latest])

    def test_real_busy_writer_preserves_answer_without_false_count(self):
        opened,go=threading.Event(),threading.Event()
        @contextlib.contextmanager
        def resources():
            with self.resources() as value:
                opened.set();go.wait(1)
                yield value
        engine=self.engine(resources=resources)
        self.assertTrue(opened.wait(1))
        other=sqlite3.connect(self.path,isolation_level=None)
        self.addCleanup(other.close)
        other.execute('BEGIN IMMEDIATE')
        identity=engine.begin();engine.enqueue(identity)
        started=time.monotonic();go.set()
        self.wait(lambda:any(e.stage=='ready' for e in self.events))
        ready=next(e for e in self.events if e.stage=='ready')
        self.assertLess(time.monotonic()-started,1)
        self.assertEqual(ready.save_error,'unavailable')
        self.assertIsNone(ready.result.count)
        self.assertFalse(ready.result.saved)
        self.assertTrue(ready.result.articles)
        other.execute('ROLLBACK')

    def test_sentence_never_creates_word_row(self):
        engine=self.engine(source=FixedSource('one two three four five'))
        identity=engine.begin();engine.enqueue(identity)
        self.wait(lambda:any(e.stage=='context' for e in self.events))
        self.assertEqual(self.count(),0)
        self.assertEqual(next(e for e in self.events if e.stage=='ready').result.kind,'sentence')

    def test_ocr_timeout_has_recognition_error_identity(self):
        from lookup import ocr
        class FailedSource(FixedSource):
            def resolve(self,*args):raise ocr.OcrError('timeout')
        engine=self.engine(source=FailedSource())
        identity=engine.begin();engine.enqueue(identity)
        self.wait(lambda:any(e.stage=='error' for e in self.events))
        self.assertEqual(next(e.error for e in self.events if e.stage=='error'),'ocr_timeout')
        self.assertEqual(self.count(),0)

    def test_quit_closes_owned_resources_while_timed_out_context_is_still_alive(self):
        entered,release=threading.Event(),threading.Event()
        self.addCleanup(release.set)
        class ContextSource(FixedSource):
            def resolve(self,frozen,dictset):
                return app.Query('word','Public source context')
        @contextlib.contextmanager
        def resources():
            with self.resources() as value:
                value.config=config.Config(online=True)
                yield value
        def network(*args,**kwargs):
            entered.set();release.wait(2)
            return ANSWER
        with patch.object(translate,'CONTEXT_JOIN_S',.02),patch.object(translate._online,'translate_online',side_effect=network) as request:
            engine=self.engine(source=ContextSource(),resources=resources)
            identity=engine.begin();engine.enqueue(identity)
            self.wait(lambda:any(e.id==identity and e.stage=='context' for e in self.events))
            self.assertTrue(entered.is_set())
            for _ in range(4):
                identity=engine.begin();engine.enqueue(identity)
                self.wait(lambda:any(e.id==identity and e.stage=='context' for e in self.events))
            self.assertEqual(request.call_count,1)
            engine.stop();engine.join(.5)
            self.assertFalse(engine.is_alive())
            self.assertEqual(self.owners[-1][0],'close')
            self.assertFalse(release.is_set())
            release.set()

    def test_contextual_enrichment_counts_once_and_stale_reply_cannot_update_pair(self):
        for stale in ('none','dismiss','replace'):
            with self.subTest(stale=stale):
                entered,release,finished=threading.Event(),threading.Event(),threading.Event()
                self.addCleanup(release.set)
                with contextlib.closing(open_store(self.path)) as conn:
                    conn.execute('DELETE FROM contextual_translations')
                source='They sat on the bank of the river.'
                class ContextSource(FixedSource):
                    def resolve(self,frozen,dictset):
                        return app.Query('bank',source,span=(16,20),context_complete=True)
                @contextlib.contextmanager
                def resources():
                    with self.resources() as value:
                        value.config=config.Config(online=True)
                        yield value
                def meaning(request):
                    entered.set();release.wait(2)
                    return contextual.ContextResult('берегу',contextual.PROVIDER)
                original=translate.lookup
                def lookup(*args,**kwargs):
                    try:return original(*args,**kwargs)
                    finally:finished.set()
                with patch.object(translate._online,'translate_online',return_value=ANSWER), \
                     patch.object(contextual,'translate_context',side_effect=meaning):
                    engine=self.engine(source=ContextSource(),resources=resources,lookup=lookup)
                    identity=engine.begin();engine.enqueue(identity)
                    self.wait(lambda:any(e.id==identity and e.stage=='ready' for e in self.events))
                    self.assertTrue(entered.is_set())
                    ready=next(e for e in self.events if e.id==identity and e.stage=='ready')
                    self.assertTrue(ready.result.meaning_pending)
                    self.assertEqual(ready.span,(16,20))
                    if stale=='dismiss':engine.dismiss(identity)
                    elif stale=='replace':engine.begin()
                    release.set();self.assertTrue(finished.wait(1))
                    if stale=='none':
                        self.wait(lambda:any(e.id==identity and e.stage=='context' for e in self.events))
                        final=next(e for e in self.events if e.id==identity and e.stage=='context')
                        self.assertEqual(final.span,(16,20))
                    else:
                        self.assertFalse(any(e.id==identity and e.stage=='context' for e in self.events))
                    engine.stop();engine.join(2)
                with contextlib.closing(open_store(self.path)) as conn:
                    pair=get_word_context(conn,'bank')
                    self.assertEqual(pair['context'],source)
                    self.assertEqual(pair['span'],(16,20))
                    self.assertEqual(pair['meaning'],'берегу' if stale=='none' else None)
                    self.assertEqual(conn.execute('SELECT count FROM words WHERE word=?',('bank',)).fetchone()[0],
                                     ('none','dismiss','replace').index(stale)+1)
                self.events.clear()

    def test_late_enrichment_error_or_unmatched_pair_has_separate_warning(self):
        class ContextSource(FixedSource):
            def resolve(self,frozen,dictset):
                return app.Query('bank','The bank by the river.',span=(4,8),context_complete=True)
        def lookup(text,**kwargs):
            value=translate.Result('word',text,translation='meaning',context_meaning='берег',
                                   meaning_provider=contextual.PROVIDER)
            kwargs['on_ready'](value)
            return value
        for error in (sqlite3.OperationalError('private detail'),None):
            with self.subTest(error=type(error).__name__):
                with patch.object(app,'enrich_word_context',side_effect=error,return_value=False):
                    engine=self.engine(source=ContextSource(),lookup=lookup)
                    identity=engine.begin();engine.enqueue(identity)
                    self.wait(lambda:any(e.id==identity and e.stage=='context' for e in self.events))
                    final=next(e for e in self.events if e.id==identity and e.stage=='context')
                    self.assertTrue(final.result.meaning_save_error)
                    self.assertTrue(final.result.saved)
                    self.assertIsNone(final.result.cache_error)
                    self.assertEqual(final.result.context_meaning,'берег')
                    engine.stop();engine.join(2)
                self.events.clear()

    def test_dismiss_after_cached_ready_keeps_the_already_shown_meaning(self):
        source='The bank by the river.'
        release,finished=threading.Event(),threading.Event()
        self.addCleanup(release.set)
        class ContextSource(FixedSource):
            def resolve(self,frozen,dictset):
                return app.Query('bank',source,span=(4,8),context_complete=True)
        @contextlib.contextmanager
        def resources():
            with self.resources() as value:
                value.config=config.Config(online=True)
                contextual.cache_put(value.conn,contextual.ContextRequest(source,4,8,'bank'),
                                     contextual.ContextResult('берег',contextual.PROVIDER))
                yield value
        def sentence(*args,**kwargs):
            release.wait(2)
            return ANSWER
        original=translate.lookup
        def lookup(*args,**kwargs):
            try:return original(*args,**kwargs)
            finally:finished.set()
        with patch.object(translate._online,'translate_online',side_effect=sentence):
            engine=self.engine(source=ContextSource(),resources=resources,lookup=lookup)
            self.addCleanup(release.set)
            identity=engine.begin();engine.enqueue(identity)
            self.wait(lambda:any(e.id==identity and e.stage=='ready' for e in self.events))
            ready=next(e for e in self.events if e.id==identity and e.stage=='ready')
            self.assertEqual(ready.result.context_meaning,'берег')
            with contextlib.closing(open_store(self.path)) as conn:
                self.assertEqual(get_word_context(conn,'bank')['meaning'],'берег')
            engine.dismiss(identity)
            release.set();self.assertTrue(finished.wait(1))
            engine.stop();engine.join(2)
        self.assertFalse(any(e.id==identity and e.stage=='context' for e in self.events))
        with contextlib.closing(open_store(self.path)) as conn:
            pair=get_word_context(conn,'bank')
            self.assertEqual((pair['context'],pair['span'],pair['meaning']),(source,(4,8),'берег'))
            self.assertEqual(conn.execute('SELECT count FROM words').fetchone()[0],1)


class ReloadTests(EngineCase):
    def test_reload_invalidates_old_lookup_and_next_uses_saved_order_online(self):
        entered,release,opened = threading.Event(),threading.Event(),threading.Event()
        self.addCleanup(release.set)
        path = self.root/'settings.json'
        config.save(dict(dictionaries=[dict(id='a'),dict(id='b')],online=True),path)
        calls,closed = [],[]
        @contextlib.contextmanager
        def resources():
            cfg = config.load(path)
            class Dictionaries:
                order = cfg.dictionaries
                def close(self):closed.append(threading.get_ident())
            dictionaries = Dictionaries()
            with self.resources() as value:
                value.config,value.dictset = cfg,dictionaries
                opened.set()
                try:yield value
                finally:dictionaries.close()
        def lookup(text,**kwargs):
            calls.append((kwargs['dictset'].order,kwargs['online']))
            if len(calls)==1:
                entered.set();release.wait(2)
            value=translate.Result('word',text,translation='meaning')
            kwargs['on_ready'](value)
            return value
        engine=self.engine(resources=resources,lookup=lookup)
        self.addCleanup(release.set)
        self.assertTrue(opened.wait(1))
        first=engine.begin();engine.enqueue(first)
        self.assertTrue(entered.wait(1))
        config.save(dict(dictionaries=[dict(id='b'),dict(id='a',enabled=False)],online=False),path)
        revision=engine.request_reload()
        latest=engine.begin();engine.enqueue(latest)
        self.assertGreater(latest,first)
        self.assertFalse(engine.current(first))
        release.set()
        self.wait(lambda:any(e.id==latest and e.stage=='context' for e in self.events))
        acknowledgement=next(e for e in self.events if e.stage=='reload')
        self.assertEqual(acknowledgement.reload_revision,revision)
        self.assertIsNone(acknowledgement.error)
        self.assertEqual(calls,[((('a',True),('b',True)),True),((('b',True),('a',False)),False)])
        self.assertEqual([e.id for e in self.events if e.stage=='ready'],[latest])
        self.assertEqual(self.count(),1)
        engine.stop();engine.join(2)
        self.assertEqual(len(closed),2)
        self.assertEqual(len(set(closed+[owner for _,owner in self.owners])),1)
        self.assertNotEqual(closed[0],threading.get_ident())

    def test_superseded_acknowledgement_has_its_own_revision_and_reload_priority(self):
        initial,opening,release=threading.Event(),threading.Event(),threading.Event()
        self.addCleanup(release.set)
        attempts=[]
        @contextlib.contextmanager
        def resources():
            attempts.append(threading.get_ident())
            if len(attempts)==2:
                opening.set();release.wait(2)
            with self.resources() as value:
                initial.set()
                yield value
        engine=self.engine(resources=resources)
        self.assertTrue(initial.wait(1))
        self.addCleanup(release.set)
        first=engine.request_reload()
        self.assertTrue(opening.wait(1))
        obsolete=engine.begin();engine.enqueue(obsolete)
        second=engine.request_reload()
        latest=engine.begin();engine.enqueue(latest)
        release.set()
        self.wait(lambda:any(e.id==latest and e.stage=='context' for e in self.events))
        acknowledgements=[e for e in self.events if e.stage=='reload']
        self.assertEqual([e.reload_revision for e in acknowledgements],[first,second])
        self.assertGreater(second,first)
        self.assertEqual([e.id for e in self.events if e.stage=='ready'],[latest])
        self.assertLess(self.events.index(acknowledgements[-1]),next(i for i,e in enumerate(self.events) if e.stage=='ready'))
        self.assertEqual(len(attempts),3)

    def test_failed_reload_is_explicit_keeps_worker_alive_and_can_retry(self):
        opened=threading.Event()
        attempts=[]
        @contextlib.contextmanager
        def resources():
            attempts.append(1)
            if len(attempts)==2:
                raise RuntimeError('private resource path')
            with self.resources() as value:
                opened.set()
                yield value
        engine=self.engine(resources=resources)
        self.assertTrue(opened.wait(1))
        revision=engine.request_reload()
        waiting=engine.begin();engine.enqueue(waiting)
        self.wait(lambda:any(e.id==waiting and e.stage=='error' for e in self.events))
        ack=next(e for e in self.events if e.stage=='reload')
        self.assertEqual((ack.reload_revision,ack.error),(revision,'reload_failed'))
        self.assertEqual(next(e.error for e in self.events if e.id==waiting and e.stage=='error'),'reload_failed')
        self.assertTrue(engine.is_alive())
        retry=engine.request_reload()
        latest=engine.begin();engine.enqueue(latest)
        self.wait(lambda:any(e.id==latest and e.stage=='context' for e in self.events))
        self.assertIsNone(next(e.error for e in self.events if e.reload_revision==retry))
        self.assertEqual(self.count(),1)
        engine.stop();engine.join(2)
        self.assertIsNone(engine.request_reload())

    def test_reload_during_meaning_refuses_old_enrichment_and_preserves_card(self):
        from lookup import learning
        source='They sat on the bank of the river.'
        entered,release,finished=threading.Event(),threading.Event(),threading.Event()
        self.addCleanup(release.set)
        class ContextSource(FixedSource):
            def resolve(self,frozen,dictset):
                return app.Query('bank',source,span=(16,20),context_complete=True)
        def meaning(request):
            entered.set();release.wait(2)
            return contextual.ContextResult('берег',contextual.PROVIDER)
        original=translate.lookup
        def lookup(*args,**kwargs):
            try:return original(*args,**kwargs)
            finally:finished.set()
        @contextlib.contextmanager
        def resources():
            with self.resources() as value:
                value.config=config.Config(online=True)
                yield value
        with patch.object(translate._online,'translate_online',return_value=ANSWER), \
             patch.object(contextual,'translate_context',side_effect=meaning):
            engine=self.engine(source=ContextSource(),resources=resources,lookup=lookup)
            self.addCleanup(release.set)
            identity=engine.begin();engine.enqueue(identity)
            self.wait(lambda:any(e.id==identity and e.stage=='ready' for e in self.events))
            self.assertTrue(entered.is_set())
            with contextlib.closing(open_store(self.path)) as conn:
                learning.add_history_card(conn,'bank',now=1)
                card=learning.get_card(conn,'bank')
            revision=engine.request_reload()
            release.set();self.assertTrue(finished.wait(1))
            self.wait(lambda:any(e.stage=='reload' and e.reload_revision==revision for e in self.events))
            self.assertFalse(any(e.id==identity and e.stage=='context' for e in self.events))
            with contextlib.closing(open_store(self.path)) as conn:
                self.assertIsNone(get_word_context(conn,'bank')['meaning'])
                self.assertEqual(learning.get_card(conn,'bank'),card)
                self.assertEqual(conn.execute('SELECT count FROM words').fetchone()[0],1)

    def test_partial_resource_errors_cannot_report_settings_applied(self):
        for error_field in ('reload_error','save_error'):
            with self.subTest(error_field=error_field):
                opened=threading.Event()
                attempts=[]
                @contextlib.contextmanager
                def resources():
                    attempts.append(1)
                    with self.resources() as value:
                        if len(attempts)==2:
                            setattr(value,error_field,'unavailable')
                        opened.set()
                        yield value
                engine=self.engine(resources=resources)
                self.assertTrue(opened.wait(1))
                revision=engine.request_reload()
                self.wait(lambda:any(e.reload_revision==revision for e in self.events))
                self.assertEqual(next(e.error for e in self.events if e.reload_revision==revision),'reload_failed')
                engine.stop();engine.join(2)
                self.assertFalse(engine.is_alive())
                self.events.clear()


class SourceTests(unittest.TestCase):
    def test_compositor_snapshot_is_used_without_resampling_live_scene_or_cursor(self):
        from unittest.mock import Mock
        snapshot=Mock(point=(50,50),monitor=MONITOR,available=(0,0,1000,740))
        frame=snapshot.image.return_value
        source=app.Source({})
        with patch.object(app.platform,'cursor_position',side_effect=AssertionError('live cursor')), \
             patch.object(app.platform,'monitors',side_effect=AssertionError('live outputs')), \
             patch.object(app.capture,'capture_monitor',side_effect=AssertionError('live frame')), \
             patch.object(app.platform,'read_primary',return_value=None):
            frozen=source.freeze(snapshot)
        self.assertEqual(frozen.point,(50,50))
        self.assertIs(frozen.monitor,MONITOR)
        self.assertIs(frozen.image,frame)
        self.assertEqual(frozen.available,(0,0,1000,740))
    def test_recovered_context_and_selected_phrase_span_are_propagated(self):
        from types import SimpleNamespace
        text='The river bank by the bank.'
        selection=ocr.Selection('bank','original line',('river bank',),(10,10,20,10),90,
                                text,(10,14),True,(('river bank',(4,14)),))
        frame=SimpleNamespace(width=1000,height=800,png=b'public',elapsed_ms=1)
        frozen=app.Frozen('ocr',(20,20),MONITOR,image=frame)
        with patch.object(ocr,'recognize_image',return_value=SimpleNamespace(selection=selection,timings={})), \
             patch.object(ocr,'choose_query',return_value='river bank'):
            query=app.Source({}).resolve(frozen,None)
        self.assertEqual(query.context,text)
        self.assertEqual(query.span,(4,14))
        self.assertTrue(query.context_complete)
        self.assertEqual(query.selection_box,selection.box)

    def test_fresh_repeated_absent_invalid_primary_transitions(self):
        source=app.Source({})
        frames=object()
        with patch('lookup.app.platform.cursor_position',return_value=(50,50)), \
             patch('lookup.app.platform.monitors',return_value=(MONITOR,)), \
             patch('lookup.app.platform.work_area',return_value=(0,0,1000,750)), \
             patch('lookup.app.platform.read_primary',side_effect=['Word','Word',None,'Word','\x00bad','word '*251]), \
             patch('lookup.app.capture.capture_monitor',return_value=frames) as screenshot:
            states=[]
            for _ in range(6):
                frozen=source.freeze()
                states.append(frozen)
                source.consume(frozen)
        self.assertEqual([s.mode for s in states],['primary','ocr','ocr','primary','ocr','ocr'])
        self.assertEqual(screenshot.call_count,4)
        self.assertEqual(states[0].text,'Word')
        self.assertEqual(states[0].available,(0,0,1000,750))

    def test_unaccepted_source_is_not_marked_already_translated(self):
        source=app.Source({})
        with patch('lookup.app.platform.cursor_position',return_value=(50,50)), \
             patch('lookup.app.platform.monitors',return_value=(MONITOR,)), \
             patch('lookup.app.platform.work_area',return_value=(0,0,1000,750)), \
             patch('lookup.app.platform.read_primary',return_value='Word'), \
             patch('lookup.app.capture.capture_monitor') as screenshot:
            first=source.freeze()
            second=source.freeze()
            self.assertEqual((first.mode,second.mode),('primary','primary'))
            source.consume(second)
            self.assertEqual(source.freeze().mode,'ocr')
            self.assertEqual(screenshot.call_count,1)


if __name__=='__main__':
    unittest.main()
