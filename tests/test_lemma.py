"""Dictionary-confirmed base forms and Mueller pointer resolution."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from lookup import dicts
from lookup.config import Config
from tests._dsl_writer import write_dsl
from tests._stardict_writer import write_stardict


class FormCandidateTests(unittest.TestCase):
    def tearDown(self):
        dicts.load_irregular.cache_clear()

    def test_suffix_order(self):
        expected = {
            'books': ['book'], 'boxes': ['boxe', 'box'], 'runs': ['run'],
            'studies': ['study', 'studie', 'studi'], 'tried': ['try', 'trie', 'tri'],
            'stopped': ['stoppe', 'stopp', 'stop'], 'walked': ['walke', 'walk'],
            'running': ['runne', 'runn', 'run'], 'making': ['make', 'mak'],
            'bigger': ['bigge', 'bigg', 'big'], 'nicest': ['nice', 'nic'],
            'glasses': ['glasse', 'glass'],
        }
        with mock.patch.object(dicts, 'load_irregular', return_value={}):
            for word, candidates in expected.items():
                with self.subTest(word=word):
                    self.assertEqual(dicts.form_candidates(word), candidates)
                    self.assertEqual(dicts.form_candidates(word.upper()), candidates)
            for word in ('is', 'as', 'go', 'a', 'us', '', 'break out', 'run\ning'):
                self.assertEqual(dicts.form_candidates(word), [])
        with self.assertRaises(TypeError):
            dicts.form_candidates(None)

    def test_real_data_and_cache(self):
        for word, base in [('ran', 'run'), ('went', 'go'), ('men', 'man'), ('children', 'child'), ('mice', 'mouse'), ('stopped', 'stop'), ('better', 'good')]:
            self.assertEqual(dicts.form_candidates(word)[0], base)
        forms = dicts.load_irregular()
        self.assertIs(forms, dicts.load_irregular())
        self.assertTrue(all(isinstance(v, tuple) for v in forms.values()))

    def test_bad_files(self):
        dicts.load_irregular.cache_clear()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'forms.txt'
            with mock.patch.object(dicts, '_IRREGULAR_PATH', path):
                self.assertEqual(dicts.load_irregular(), {})
                for raw, expected in [(b'# hi\n\nmen man\nsingle\nUP down\nfoo bar1\n', {'men': ('man',)}), (b'x' * 10_000_000, {}), (b'\xff', {})]:
                    path.write_bytes(raw)
                    dicts.load_irregular.cache_clear()
                    self.assertEqual(dicts.load_irregular(), expected)


ENTRIES = [
    ('run', '[rʌn] 1. _n. бег 2. _v. бежать'),
    ('ran', '[ræn] _p. от run 2'), ('go', '_v. идти'),
    ('went', '[went] _p. от go 1'), ('man', '_n. человек'),
    ('men', '[men] _pl. от man 1'),
    ('running', '[ˈrʌnıŋ] 1. _pres-p. от run 2 2. _n. бег'),
    ('gone', '[gɔn] 1. _p-p. от go 1; 2. _a. ушедший'),
    ('better', '[ˈbetə] _n. держащий пари _II [ˈbetə] 1. _a. (_comp. от good 1) лучший'),
    ('worse', '[wəːs] 1. _a. (_comp. от bad 1) худший'),
    ('news', '_n. новости'), ('book', '_n. книга'), ('stop', '_v. остановить'),
    ('box', '_n. коробка'), ('child', '_n. ребёнок'), ('mouse', '_n. мышь'),
    ('teeth', '_pl. от tooth 1'), ('loop', '_p. от loop 1'),
    ('first', '_p. от second 1'), ('second', '_p. от first 1'),
]


class FindTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        patch = mock.patch.dict(os.environ, {'LOOKUP_CACHE': str(self.root / 'cache')})
        patch.start()
        self.addCleanup(patch.stop)

    def open(self, entries=ENTRIES):
        write_stardict(self.root, 'mueller', entries, bookname='Mueller')
        result = dicts.open_all(Config(), [self.root])
        self.addCleanup(result.close)
        return result

    def test_exact_pointers_mixed_and_inflected(self):
        result = self.open()
        for word in ['run', 'better', 'worse', 'news', 'teeth', 'loop', 'first']:
            with self.subTest(word=word):
                found = result.find(word)
                self.assertIsNone(found.lemma)
                self.assertIsNone(found.articles[0].lemma_of)
                self.assertEqual(found.articles[0].headword, word)
        for word, base in [('ran', 'run'), ('went', 'go'), ('men', 'man'), ('running', 'run'), ('gone', 'go'), ('books', 'book'), ('stopped', 'stop'), ('boxes', 'box'), ('runs', 'run'), ('children', 'child'), ('mice', 'mouse')]:
            with self.subTest(word=word):
                found = result.find(word)
                self.assertEqual(found.lemma, base)
                self.assertTrue(all(a.lemma_of == base for a in found.articles))
                self.assertEqual(found.articles[0].headword, word if word in ('running', 'gone') else base)
        for word in ['', 'xyzzyq', 'break out']:
            self.assertFalse(result.find(word))

    def test_absent_bases_and_first_confirmed_candidate(self):
        result = self.open([('running', ENTRIES[7][1]), ('boxe', '_n. first'), ('box', '_n. second'), ('break', 'x')])
        self.assertIsNone(result.find('running').lemma)
        self.assertEqual(result.find('boxes').lemma, 'boxe')
        with mock.patch.object(dicts, 'form_candidates', side_effect=AssertionError('phrase rules')):
            self.assertFalse(result.find('break out'))

    def test_phrase_headword(self):
        result = self.open([('break out', 'вырваться')])
        self.assertEqual(result.find('Break Out').articles[0].headword, 'break out')

    def test_all_dictionary_targets_in_order_without_duplicates(self):
        write_stardict(self.root, 'other', [('run', '_v. другой'), ('ran', '_p. от run 2')], bookname='Other')
        result = self.open()
        self.assertEqual([a.dict_name for a in result.find('ran').articles], ['Mueller', 'Other'])
        self.assertEqual([a.headword for a in result.find('ran').articles], ['run', 'run'])
        # A second format participates in the same search.
        write_dsl(self.root / 'extra.dsl', [(['run'], ['бежать'])], name='DSL')
        extra = dicts.open_all(Config(), [self.root])
        self.addCleanup(extra.close)
        self.assertEqual([a.dict_name for a in extra.find('ran').articles], ['DSL', 'Mueller', 'Other'])
