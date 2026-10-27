"""Observable request identity, resource ownership and history invariants."""
import contextlib
import sqlite3
import threading
import time
import unittest
from unittest.mock import patch

from lookup import app, config, translate, context as contextual, ocr
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


class EngineTests(unittest.TestCase):
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
                    if stale=='dismiss':engine.dismiss(identity)
                    elif stale=='replace':engine.begin()
                    release.set();self.assertTrue(finished.wait(1))
                    if stale=='none':
                        self.wait(lambda:any(e.id==identity and e.stage=='context' for e in self.events))
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


class SourceTests(unittest.TestCase):
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
