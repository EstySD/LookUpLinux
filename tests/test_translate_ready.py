"""Early useful results, bounded context admission and persistence failures."""
import sqlite3
import threading
import unittest
from unittest.mock import patch

from lookup import translate as t
from lookup.dicts import Article, SearchResult
from lookup.online import OnlineResult
from lookup.store import open_store
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


if __name__=='__main__':
    unittest.main()
