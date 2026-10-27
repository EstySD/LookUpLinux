"""Learning operates on frozen cards, never mutable history or the network."""
import sqlite3
import unittest

from lookup import learning, store
from tests._support import make_tempdir, forbid_network


def snapshot(word='bank', translation='банк', context='The bank approved the loan.'):
    return dict(word=word,translation=translation,context=context,meaning=None,span=None,provider=None)


class CardTests(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)
        self.conn = store.open_store(self.root/'cards.db')
        self.addCleanup(self.conn.close)
        self.network = forbid_network(self)

    def test_numeric_stable_history_sort_search_never_counts(self):
        for word,count in (('bank',2),('river',10),('apple',2)):
            for _ in range(count):
                store.upsert_word(self.conn,word,'слово',now=10)
        before = self.conn.total_changes
        self.assertEqual([row['word'] for row in learning.list_words(self.conn)],['river','apple','bank'])
        self.assertEqual([row['word'] for row in learning.list_words(self.conn,sort='word',descending=False)],['apple','bank','river'])
        self.assertEqual([row['word'] for row in learning.list_words(self.conn,search='AN')],['bank'])
        self.assertEqual(learning.list_words(self.conn,search='%'),[])
        self.assertEqual(self.conn.total_changes,before)
        self.network.assert_not_called()

    def test_query_allowlist_and_bound_values(self):
        store.upsert_word(self.conn,'bank',now=1)
        for kwargs in (dict(sort='word; DELETE FROM words'),dict(descending='DESC'),dict(search=None)):
            with self.assertRaises(learning.LearningError):
                learning.list_words(self.conn,**kwargs)
        self.assertEqual(learning.list_words(self.conn,search="' OR 1=1 --"),[])
        self.assertEqual(learning.list_words(self.conn)[0]['count'],1)

    def test_delete_resets_next_count_and_keeps_independent_card(self):
        store.upsert_word(self.conn,'bank','банк',now=1)
        self.assertEqual(learning.add_history_card(self.conn,'bank',now=2),'created')
        self.assertTrue(learning.delete_word(self.conn,'bank'))
        self.assertFalse(learning.delete_word(self.conn,'bank'))
        self.assertEqual(store.upsert_word(self.conn,'bank',now=3),1)
        self.assertEqual(learning.get_card(self.conn,'bank')['translation'],'банк')

    def test_snapshot_duplicate_preserves_pair_and_schedule(self):
        original = snapshot(context='A bank.\nOriginal context.')
        self.assertEqual(learning.add_card(self.conn,original,now=100),'created')
        self.conn.execute('UPDATE cards SET due=200,repetitions=2,interval_days=6,ease=2.1,review_version=3')
        before = learning.get_card(self.conn,'bank')
        changed = snapshot(translation='берег',context='Different river context.')
        self.assertEqual(learning.add_card(self.conn,changed,now=500),'already_present')
        self.assertEqual(learning.get_card(self.conn,'bank'),before)

    def test_history_enrichment_cannot_mutate_frozen_card(self):
        from lookup.context import ContextResult, PROVIDER
        source = '  They sat on the bank\nof the river.  '
        start = source.index('bank')
        span = (start,start+4)
        store.upsert_word(self.conn,'bank','банк',source,now=1,context_span=span,context_token='one')
        learning.add_history_card(self.conn,'bank',now=2)
        self.assertTrue(store.enrich_word_context(self.conn,'bank','one',source,span,ContextResult('берег',PROVIDER)))
        self.assertEqual(learning.get_card(self.conn,'bank')['translation'],'банк')
        self.assertEqual(learning.get_card(self.conn,'bank')['context'],source)
        self.conn.execute('DELETE FROM cards')
        learning.add_history_card(self.conn,'bank',now=3)
        card = learning.get_card(self.conn,'bank')
        self.assertEqual((card['translation'],card['context'],card['span'],card['provider']),('берег',source,span,PROVIDER))

    def test_contextual_pair_requires_matching_source_occurrence(self):
        value = snapshot()
        start = value['context'].index('bank')
        value.update(meaning='банк',provider='google-gtx-marked-v1',span=(start,start+4))
        for changes in (dict(span=(0,3)),dict(span=(True,4)),dict(provider=None),dict(context=None),dict(word='river')):
            with self.subTest(changes=changes):
                with self.assertRaises(learning.LearningError):
                    learning.add_card(self.conn,dict(value,**changes),now=1)
        self.assertEqual(learning.list_cards(self.conn),[])
        self.assertEqual(learning.add_card(self.conn,value,now=1),'created')

    def test_invalid_identity_and_empty_translation_are_private(self):
        for value in (None,{},snapshot(word='BANK'),snapshot(word='one two three four five'),
                      snapshot(translation='  '),snapshot(context='x'*501),snapshot(translation='x\x00'),
                      snapshot(word="word';drop")):
            with self.subTest(value=value):
                with self.assertRaises(learning.LearningError) as raised:
                    learning.add_card(self.conn,value,now=1)
                self.assertIn(str(raised.exception),learning.REASONS)
        self.assertEqual(learning.list_cards(self.conn),[])

    def test_card_initial_due_and_restart_snapshot(self):
        learning.add_card(self.conn,snapshot(),now=100)
        card = learning.get_card(self.conn,'bank')
        self.assertEqual((card['due'],card['created_at'],card['repetitions'],card['interval_days'],card['ease'],card['review_version']),
                         (100,100,0,0,2.5,0))
        reopened = store.open_store(self.root/'cards.db')
        self.addCleanup(reopened.close)
        self.assertEqual(learning.get_card(reopened,'bank'),card)
        self.assertIsNone(learning.get_card(reopened,'absent'))
