"""Independent TSV and word-selection contracts; no Qt or OCR executable."""
import math
import unittest
from unittest import mock

from lookup import ocr


HEADER = 'level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext'


def tsv(*rows):
    return (HEADER + '\n' + '\n'.join('\t'.join(map(str, r)) for r in rows) + '\n').encode()


def word(text, x=10, y=10, width=30, height=10, confidence=90, line=(1, 1, 1, 1), order=1):
    return ocr.Word(text, (x, y, width, height), confidence, line, order)


class ParserTests(unittest.TestCase):
    def test_words_and_line_identity(self):
        rows = ocr.parse_tsv(tsv((1, 1, 0, 0, 0, 0, 0, 0, 100, 100, -1, ''),
                                 (5, 1, 2, 3, 4, 1, 20, 30, 40, 10, 88.5, 'run')))
        self.assertEqual(rows, (word('run', 20, 30, 40, confidence=88.5, line=(1, 2, 3, 4)),))

    def test_transform_actual_ratios(self):
        for scale in (1, 1.25, 1.5, 2):
            tr = ocr.Transform(100, 50, scale, scale, 8)
            w = ocr.parse_tsv(tsv((5, 1, 1, 1, 1, 1, 8+20*scale, 8+10*scale,
                                   30*scale, 12*scale, 90, 'run')), tr)[0]
            self.assertEqual(w.box, (120, 60, 30, 12))
        tr = ocr.Transform(-100, -50, 1.25, 1.5, 8)
        self.assertEqual(tr.original_xy(33, 38), (-80, -30))

    def test_malformed_output_is_private(self):
        good = [5, 1, 1, 1, 1, 1, 10, 10, 20, 10, 90, 'secret']
        cases = [b'secret', b'\xff', tsv(good) + b'broken\n']
        for index, value in ((0, 9), (1, 0), (6, -1), (8, 0), (9, -1),
                             (10, 'nan'), (10, 'inf'), (10, 101), (11, 'x'*1025)):
            row = good.copy()
            row[index] = value
            cases.append(tsv(row))
        for text in ('secret\x1b', 'secret\u202e', 'secret\x9b'):
            row = good.copy()
            row[11] = text
            cases.append(tsv(row))
        cases.append(b'x'*(ocr.MAX_TSV_BYTES+1))
        for raw in cases:
            with self.subTest(raw=raw[:30]):
                with self.assertRaises(ocr.OcrError) as caught:
                    ocr.parse_tsv(raw)
                self.assertEqual(str(caught.exception), 'bad_output')

    def test_invalid_transforms(self):
        for scale in (0, -1, math.nan, math.inf):
            with self.assertRaises(ocr.OcrError):
                ocr.Transform(scale_x=scale)


class SelectionTests(unittest.TestCase):
    def test_hit_nearest_and_tie(self):
        words = (word('hello'), word('world', 45, width=35, order=2))
        self.assertEqual(ocr.select_word(words, (15, 15)).word, 'hello')
        self.assertEqual(ocr.select_word(words, (42, 15)).word, 'hello')
        self.assertEqual(ocr.select_word(words, (43, 15)).word, 'world')
        self.assertEqual(ocr.select_word(words, (42.5, 15)).word, 'hello')
        self.assertEqual(ocr.select_word(words, (15, 15)).line, 'hello world')
        self.assertIsNone(ocr.select_word(words, (200, 15)))
        self.assertIsNone(ocr.select_word(words, (15, 100)))

    def test_rejected_hit_does_not_jump(self):
        for bad in (word('bad123', width=10), word('Я', width=10),
                    word('noise', width=10, confidence=10), word('★', width=10)):
            self.assertIsNone(ocr.select_word((bad, word('run', 22)), (18, 15)))

    def test_words_never_cross_line_or_noise_barriers(self):
        variants = ((word('break'), word('★', 41, width=2, order=2), word('out', 45, order=3)),
                    (word('break'), word('out', 100, order=2)),
                    (word('break'), word('out', 45, line=(1, 2, 1, 1), order=2)),
                    (word('break,'), word('out', 45, order=2)))
        for words in variants:
            self.assertEqual(ocr.select_word(words, (15, 15)).candidates, ())

    def test_compound_forward_then_backward(self):
        words = (word('we', 0, width=8), word('break', 12, width=25, order=2),
                 word('out', 42, width=15, order=3))
        selection = ocr.select_word(words, (15, 15))
        self.assertEqual(selection.candidates, ('break out', 'we break'))
        dictionaries = mock.Mock()
        dictionaries.find.side_effect = [False, True]
        self.assertEqual(ocr.choose_query(selection, dictionaries), 'we break')
        self.assertEqual(dictionaries.find.call_args_list, [mock.call('break out'), mock.call('we break')])
        self.assertEqual(ocr.choose_query(selection), 'break')
        dictionaries.find.side_effect = OSError('secret')
        self.assertEqual(ocr.choose_query(selection, dictionaries), 'break')

    def test_hyphen_lexical_units(self):
        variants = ((word('well-known', width=65),),
                    (word('well', width=20), word('-', 32, width=3, order=2),
                     word('known', 37, width=25, order=3)),
                    (word('well-', width=25), word('known', 37, width=25, order=2)))
        for words in variants:
            with self.subTest(words=words):
                result = ocr.select_word(words, (15, 15))
                self.assertEqual(result.word, 'well-known')
                self.assertEqual(result.confidence, 90)
        separated = (word('well-', width=25), word('known', 90, order=2))
        self.assertEqual(ocr.select_word(separated, (15, 15)).word, 'well')

    def test_nonfinite_points(self):
        for point in ((math.nan, 1), (1, math.inf), ('x', 1), (1,)):
            with self.assertRaises(ocr.OcrError):
                ocr.select_word((word('run'),), point)

    def test_single_letter_and_multisegment_hyphen_fragments(self):
        variants = [('e-mail', ('e-', 'mail')), ('x-ray', ('x', '-', 'ray')),
                    ('state-of-the-art', ('state-', 'of-', 'the-', 'art'))]
        for expected, parts in variants:
            words = tuple(word(part, 10+i*22, width=20, order=i+1) for i, part in enumerate(parts))
            with self.subTest(parts=parts):
                selected = ocr.select_word(words, (15, 15))
                self.assertIsNotNone(selected)
                self.assertEqual(selected.word, expected)
                self.assertEqual(selected.candidates, ())
