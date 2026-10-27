"""Early useful results, bounded context admission and persistence failures."""
import sqlite3
import threading
import unittest
from unittest.mock import patch

from lookup import translate as t, context as contextual
from lookup.dicts import Article, SearchResult
from lookup.online import OnlineResult
from lookup.store import open_store, get_word_context
from tests._support import make_tempdir, forbid_network


ANSWER = OnlineResult('google', 'gtx', 'translation', (), None, None, 'en')
ENTRY = Article('test', 'word', None, (('noun', ('meaning',)),), 'public entry')


class Dictionary:
    def find(self, key):
        return SearchResult((ENTRY,))


class ReadyTests(unittest.TestCase):
    def setUp(self):
        self.root=make_tempdir(self)
        forbid_network(self)

    def test_useful_snapshot_precedes_context_and_is_detached(self):
        entered,release=threading.Event(),threading.Event()
        self.addCleanup(release.set)
        snapshots=[]
        def network(*args,**kwargs):
            entered.set()
            self.assertTrue(release.wait(2))
            return ANSWER
        def ready(result):
            self.assertTrue(entered.wait(1))
            self.assertFalse(release.is_set())
            self.assertTrue(result.context_pending)
            self.assertEqual(result.articles,(ENTRY,))
            snapshots.append(result)
            result.timings['dicts']=-1
            release.set()
        with patch.object(t._online,'translate_online',side_effect=network):
            result=t.lookup('word',dictset=Dictionary(),context='Public source context',on_ready=ready)
        self.assertEqual(result.context_translation,'translation')
        self.assertFalse(result.context_pending)
        self.assertIsNone(snapshots[0].context_translation)
        self.assertGreaterEqual(result.timings['dicts'],0)

    def test_one_context_job_even_after_join_timeout_and_many_later_requests(self):
        entered,release=threading.Event(),threading.Event()
        self.addCleanup(release.set)
        gate=threading.BoundedSemaphore(1)
        def network(*args,**kwargs):
            entered.set()
            release.wait(2)
            return ANSWER
        with patch.object(t._online,'translate_online',side_effect=network) as request,patch.object(t,'CONTEXT_JOIN_S',.02):
            first=t.lookup('word',dictset=Dictionary(),context='Public source context',context_gate=gate)
            self.assertTrue(entered.wait(1))
            self.assertEqual(first.context_error,'timeout')
            for _ in range(8):
                value=t.lookup('word',dictset=Dictionary(),context='Public source context',context_gate=gate)
                self.assertEqual(value.context_error,'busy')
                self.assertEqual(value.articles,(ENTRY,))
            self.assertEqual(request.call_count,1)
            release.set()
            self.assertTrue(gate.acquire(timeout=1))
            gate.release()

    def test_failed_context_thread_start_releases_admission_slot(self):
        gate=threading.BoundedSemaphore(1)
        with patch.object(t.threading.Thread,'start',side_effect=RuntimeError('private detail')):
            value=t.lookup('word',dictset=Dictionary(),context='Public source context',context_gate=gate)
        self.assertEqual(value.context_error,'bad_response')
        self.assertTrue(gate.acquire(blocking=False))
        gate.release()

    def test_read_only_cache_preserves_main_and_context_without_retry(self):
        conn=open_store(self.root/'readonly.db')
        self.addCleanup(conn.close)
        conn.execute('PRAGMA query_only=ON')
        ready=[]
        with patch.object(t._online,'translate_online',return_value=ANSWER) as request:
            result=t.lookup('word',conn=conn,context='Public source context',save=False,on_ready=ready.append)
        self.assertEqual(request.call_count,2)
        self.assertEqual(result.online,ANSWER)
        self.assertEqual(result.context_translation,'translation')
        self.assertEqual(result.cache_error,'unavailable')
        self.assertEqual(ready[0].online,ANSWER)
        self.assertFalse(result.saved)
        self.assertEqual(conn.execute('SELECT count(*) FROM words').fetchone()[0],0)

    def test_cache_read_and_full_storage_errors_do_not_repeat_translation(self):
        conn=open_store(self.root/'cache.db')
        self.addCleanup(conn.close)
        with patch.object(t,'cache_get',side_effect=sqlite3.OperationalError('private read')), \
             patch.object(t,'get_meta',side_effect=sqlite3.OperationalError('private meta')), \
             patch.object(t,'cache_put',side_effect=sqlite3.DatabaseError('database full')), \
             patch.object(t._online,'translate_online',return_value=ANSWER) as request:
            result=t.lookup('word',conn=conn,save=False)
        self.assertEqual(request.call_count,1)
        self.assertEqual(result.online,ANSWER)
        self.assertEqual(result.cache_error,'unavailable')
        self.assertFalse(result.saved)

    def test_real_cache_contention_preserves_both_successful_responses(self):
        path=self.root/'busy.db'
        conn=open_store(path)
        self.addCleanup(conn.close)
        conn.execute('PRAGMA busy_timeout=20')
        other=sqlite3.connect(path,isolation_level=None)
        self.addCleanup(other.close)
        other.execute('BEGIN IMMEDIATE')
        try:
            with patch.object(t._online,'translate_online',return_value=ANSWER) as request:
                result=t.lookup('word',conn=conn,context='Public source context',save=False)
            self.assertEqual(request.call_count,2)
            self.assertEqual(result.online,ANSWER)
            self.assertEqual(result.context_translation,'translation')
            self.assertEqual(result.cache_error,'unavailable')
        finally:
            other.execute('ROLLBACK')

    def test_contextual_meaning_is_late_detached_and_saved_without_recount(self):
        conn=open_store(self.root/'meaning.db')
        self.addCleanup(conn.close)
        entered,release=threading.Event(),threading.Event()
        self.addCleanup(release.set)
        source='They sat on the bank of the river.'
        snapshots=[]
        def meaning(request):
            self.assertEqual((request.context,request.start,request.end),(source,16,20))
            entered.set();self.assertTrue(release.wait(2))
            return contextual.ContextResult('берегу',contextual.PROVIDER)
        def ready(value):
            self.assertTrue(entered.wait(1))
            self.assertTrue(value.meaning_pending)
            self.assertEqual(value.articles,(ENTRY,))
            self.assertIsNone(value.context_meaning)
            snapshots.append(value)
            release.set()
        with patch.object(t._online,'translate_online',return_value=ANSWER), \
             patch.object(contextual,'translate_context',side_effect=meaning):
            result=t.lookup('bank',dictset=Dictionary(),conn=conn,context=source,
                            context_span=(16,20),context_complete=True,on_ready=ready)
        self.assertEqual(result.context_meaning,'берегу')
        self.assertEqual(result.context_translation,'translation')
        self.assertEqual(result.count,1)
        self.assertFalse(result.meaning_pending)
        self.assertIsNone(snapshots[0].context_meaning)
        self.assertGreaterEqual(result.timings['meaning_ready'],result.timings['first_useful'])
        pair=get_word_context(conn,'bank')
        self.assertEqual((pair['context'],pair['span'],pair['meaning']),(source,(16,20),'берегу'))
        self.assertEqual(conn.execute('SELECT count FROM words').fetchone()[0],1)

    def test_cached_meaning_is_immediate_and_occurrence_specific(self):
        conn=open_store(self.root/'cached-meaning.db')
        self.addCleanup(conn.close)
        source='The bank by the bank.'
        request=contextual.ContextRequest(source,16,20,'bank')
        contextual.cache_put(conn,request,contextual.ContextResult('банк',contextual.PROVIDER))
        snapshots=[]
        with patch.object(t._online,'translate_online',return_value=ANSWER), \
             patch.object(contextual,'translate_context',side_effect=AssertionError('unexpected meaning network')):
            result=t.lookup('bank',dictset=Dictionary(),conn=conn,context=source,
                            context_span=(16,20),context_complete=True,on_ready=snapshots.append)
        self.assertEqual(snapshots[0].context_meaning,'банк')
        self.assertTrue(result.meaning_from_cache)
        self.assertFalse(result.meaning_pending)

    def test_disabled_missing_and_unreliable_context_never_request_meaning(self):
        source='They sat on the bank of the river.'
        with patch.object(t._online,'translate_online',return_value=ANSWER), \
             patch.object(contextual,'translate_context') as network:
            for options,status in ((dict(online=False,context_complete=True),'disabled'),
                                   (dict(context_complete=False),'no_context'),
                                   (dict(context_complete=True,context_span=(0,4)),'no_context')):
                kwargs=dict(context=source,context_span=(16,20));kwargs.update(options)
                result=t.lookup('bank',dictset=Dictionary(),**kwargs)
                self.assertEqual(result.meaning_error,status)
                self.assertTrue(result.articles)
            self.assertEqual(network.call_count,0)

    def test_meaning_timeout_keeps_gate_until_background_exit(self):
        gate=threading.BoundedSemaphore(1)
        release=threading.Event()
        self.addCleanup(release.set)
        def meaning(request):
            release.wait(2)
            return contextual.ContextResult('берег',contextual.PROVIDER)
        kwargs=dict(dictset=Dictionary(),context='The bank by the river.',
                    context_span=(4,8),context_complete=True,meaning_gate=gate)
        with patch.object(t._online,'translate_online',return_value=ANSWER), \
             patch.object(contextual,'translate_context',side_effect=meaning) as network, \
             patch.object(t,'CONTEXT_JOIN_S',.02):
            first=t.lookup('bank',**kwargs)
            self.assertEqual(first.meaning_error,'timeout')
            for _ in range(3):
                value=t.lookup('bank',**kwargs)
                self.assertEqual(value.meaning_error,'busy')
            self.assertEqual(network.call_count,1)
            release.set()
            self.assertTrue(gate.acquire(timeout=1));gate.release()

    def test_meaning_failure_preserves_article_and_private_reason(self):
        with patch.object(t._online,'translate_online',return_value=ANSWER), \
             patch.object(contextual,'translate_context',side_effect=RuntimeError('private source')):
            value=t.lookup('bank',dictset=Dictionary(),context='The bank by the river.',
                           context_span=(4,8),context_complete=True)
        self.assertEqual(value.meaning_error,'bad_response')
        self.assertTrue(value.articles)

    def test_late_meaning_persistence_error_retains_successful_answer(self):
        conn=open_store(self.root/'enrich-error.db')
        self.addCleanup(conn.close)
        with patch.object(t._online,'translate_online',return_value=ANSWER), \
             patch.object(contextual,'translate_context',return_value=contextual.ContextResult('берег',contextual.PROVIDER)), \
             patch.object(t,'enrich_word_context',side_effect=sqlite3.OperationalError('private write')):
            value=t.lookup('bank',dictset=Dictionary(),conn=conn,context='The bank by the river.',
                           context_span=(4,8),context_complete=True)
        self.assertEqual(value.context_meaning,'берег')
        self.assertTrue(value.articles)
        self.assertTrue(value.saved)
        self.assertTrue(value.meaning_save_error)
        self.assertIsNone(value.cache_error)
        self.assertEqual(conn.execute('SELECT count FROM words').fetchone()[0],1)


if __name__=='__main__':
    unittest.main()
