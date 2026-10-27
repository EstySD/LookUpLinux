"""Learning operates on frozen cards, never mutable history or the network."""
import csv
import html
import math
import os
import unittest
from unittest import mock

from lookup import learning, store
from tests._support import make_tempdir, forbid_network


def snapshot(word='bank', translation='банк', context='The bank approved the loan.'):
    return dict(word=word,translation=translation,context=context,meaning=None,span=None,provider=None)


class LearningCase(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)
        self.conn = store.open_store(self.root/'cards.db')
        self.addCleanup(self.conn.close)
        self.network = forbid_network(self)


class CardTests(LearningCase):
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


class ReviewTests(LearningCase):
    def test_all_ratings_preview_equal_applied_and_no_recount(self):
        for rating in ('Again','Hard','Good','Easy'):
            with self.subTest(rating=rating):
                self.conn.execute('DELETE FROM cards')
                learning.add_card(self.conn,snapshot(),now=100)
                state = learning.get_card(self.conn,'bank')
                expected = learning.preview(state,rating)
                self.assertEqual(learning.grade_card(self.conn,'bank',0,rating,now=150),'applied')
                actual = learning.get_card(self.conn,'bank')
                for key in ('repetitions','interval_days','ease'):
                    self.assertEqual(actual[key],expected[key])
                self.assertEqual(actual['due'],150+expected['delay'])
                self.assertEqual(actual['review_version'],1)
                self.assertEqual(self.conn.execute('SELECT count(*) FROM words').fetchone()[0],0)
        self.network.assert_not_called()

    def test_selected_transition_uses_old_ease_and_restart(self):
        state = dict(repetitions=0,interval_days=0,ease=2.5)
        first = learning.preview(state,'Good')
        self.assertEqual((first['repetitions'],first['interval_days'],first['delay']),(1,1,86400))
        second = learning.preview(first,'Good')
        self.assertEqual(second['interval_days'],6)
        hard = learning.preview(second,'Hard')
        self.assertEqual(hard['interval_days'],15)
        self.assertAlmostEqual(hard['ease'],2.36)
        easy = learning.preview(dict(repetitions=2,interval_days=6,ease=2.36),'Easy')
        self.assertEqual(easy['interval_days'],math.ceil(6*2.36))
        self.assertAlmostEqual(easy['ease'],2.46)
        again = learning.preview(hard,'Again')
        self.assertEqual((again['repetitions'],again['interval_days'],again['delay'],again['ease']),(0,0,600,hard['ease']))
        self.assertEqual(learning.preview(again,'Good')['interval_days'],1)
        floor = learning.preview(dict(repetitions=2,interval_days=6,ease=1.3),'Hard')
        self.assertEqual(floor['ease'],1.3)

    def test_due_boundary_order_and_stale_duplicate_grading(self):
        learning.add_card(self.conn,snapshot(word='river'),now=100)
        learning.add_card(self.conn,snapshot(),now=100)
        self.assertEqual(learning.due_cards(self.conn,now=99),[])
        self.assertEqual([r['word'] for r in learning.due_cards(self.conn,now=100)],['bank','river'])
        self.assertEqual(learning.grade_card(self.conn,'bank',0,'Again',now=99),'stale')
        self.assertEqual(learning.grade_card(self.conn,'bank',0,'Again',now=100),'applied')
        self.assertEqual(learning.grade_card(self.conn,'bank',0,'Good',now=100),'stale')
        self.assertEqual(learning.grade_card(self.conn,'bank',1,'Good',now=699),'stale')
        self.assertEqual(learning.grade_card(self.conn,'bank',1,'Good',now=700),'applied')
        reopened = store.open_store(self.root/'cards.db')
        self.addCleanup(reopened.close)
        self.assertEqual(learning.get_card(reopened,'bank')['due'],87100)

    def test_invalid_ratings_state_versions_and_time_are_refused(self):
        state = dict(repetitions=2,interval_days=6,ease=2.5)
        for rating in ('good','Other',None,3):
            with self.assertRaises(learning.LearningError):
                learning.preview(state,rating)
        for changed in (dict(repetitions=-1),dict(repetitions=True),dict(interval_days=0),
                        dict(interval_days=1.5),dict(ease=1.2),dict(ease=float('nan')),
                        dict(ease=float('inf'))):
            with self.subTest(changed=changed):
                with self.assertRaises(learning.LearningError):
                    learning.preview(dict(state,**changed),'Good')
        learning.add_card(self.conn,snapshot(),now=0)
        for version in (True,-1,'0'):
            with self.assertRaises(learning.LearningError):
                learning.grade_card(self.conn,'bank',version,'Good',now=0)
        for now in (True,-1,float('nan'),float('inf'),'today'):
            with self.assertRaises(learning.LearningError):
                learning.due_cards(self.conn,now=now)


class ExportTests(LearningCase):
    def test_csv_exact_unicode_quotes_newlines_tabs_and_saved_pair(self):
        value = snapshot(translation='=Значение, "банк"\nстрока\tдва',context='<script>x</script>\n& "контекст"\tвкладка')
        learning.add_card(self.conn,value,now=1)
        store.upsert_word(self.conn,'bank','совсем другое','новый контекст',now=2)
        output = self.root/'cards.csv'
        learning.export_csv(self.conn,output)
        with output.open(encoding='utf-8',newline='') as stream:
            rows = list(csv.reader(stream))
        self.assertEqual(rows,[['word','translation','context'],[value['word'],value['translation'],value['context']]])
        self.network.assert_not_called()

    def test_anki_has_two_escaped_fields_and_recoverable_text(self):
        value = snapshot(translation='"берег" & <img src=x>',context='Строка 1\nСтрока 2\tконец')
        learning.add_card(self.conn,value,now=1)
        output = self.root/'cards.tsv'
        learning.export_anki(self.conn,output)
        text = output.read_text(encoding='utf-8')
        lines = text.splitlines()
        self.assertEqual(lines[:3],['#separator:Tab','#html:true','#columns:Front\tBack'])
        self.assertNotIn('#notetype:',text)
        fields = next(csv.reader(lines[3:],delimiter='\t'))
        self.assertEqual(len(fields),2)
        self.assertEqual(html.unescape(fields[0]),'bank')
        before,after = fields[1].split('<hr>')
        self.assertEqual(html.unescape(before),value['translation'])
        self.assertEqual(html.unescape(after.replace('<br>','\n')),value['context'])
        self.assertNotIn('<img',fields[1])

    def test_export_failure_keeps_old_destination_and_cleans_temp(self):
        learning.add_card(self.conn,snapshot(),now=1)
        for exporter in (learning.export_csv,learning.export_anki):
            output = self.root/'old.txt'
            output.write_bytes(b'old exact bytes')
            before = set(self.root.iterdir())
            with mock.patch.object(os,'replace',side_effect=OSError('private destination')):
                with self.assertRaises(learning.LearningError) as raised:
                    exporter(self.conn,output)
            self.assertEqual(str(raised.exception),'export_failed')
            self.assertEqual(output.read_bytes(),b'old exact bytes')
            self.assertEqual(set(self.root.iterdir()),before)
