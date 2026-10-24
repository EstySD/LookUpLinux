"""Unit and property tests for lookup.normalize (DATA-02)."""
import random
import unittest

from lookup.normalize import normalize, CONTRACTIONS

APOSTROPHES = "‘’‚‛ʼ′´`"
QUOTES = "“”„‟«»″‹›\""


class NormalizeTests(unittest.TestCase):
    def check(self, table):
        for src, expected in table:
            with self.subTest(src=src):
                self.assertEqual(normalize(src), expected)

    def test_success_criterion_examples(self):
        self.check([
            ("Running", "running"),
            ("run,", "run"),
            ('"run,"', "run"),
            ("“Book’s”", "book"),
            ("Apple", "apple"),  # D-03
        ])

    def test_variants_share_one_key(self):
        variants = [
            "book", "Book", "BOOK", "book,", "Book’s", "Book's", "Book`s",
            "book´s", "“Book’s”", "(book)", "«book»",
            "'book'", "book's's",
        ]
        self.check([(v, "book") for v in variants])

    def test_apostrophe_and_quote_table(self):
        self.check([("don" + ch + "t", "don't") for ch in APOSTROPHES])
        self.check([(ch + "run" + ch, "run") for ch in QUOTES])
        self.check([("book＇s", "book")])

    def test_inner_apostrophe_and_hyphen_kept(self):
        self.check([
            ("don't", "don't"), ("o'clock", "o'clock"), ("well-known", "well-known"),
            ("co-operate", "co-operate"), ("rock'n'roll", "rock'n'roll"),
            ("well–known", "well-known"), ("well—known", "well-known"),
            ("word-", "word"), ("-word", "word"), ("(running)", "running"),
        ])

    def test_possessive_fixed_point(self):
        self.check([
            ("dogs'", "dogs"), ("dog's", "dog"), ("John's", "john"),
            ("book's's", "book"), ("'s", None), ("s", None),
        ])

    def test_contraction_exceptions(self):
        self.assertEqual(len(CONTRACTIONS), 11)
        for c in sorted(CONTRACTIONS):
            self.check([
                (c, c), (c.capitalize(), c), (c.replace("'", "’"), c),
            ])
        self.check([("it's's", "it's"), ("dog's", "dog")])

    def test_digit_tokens_rejected(self):
        self.check([
            (s, None) for s in
            ["mp3", "1st", "abc2", "run1", "l00k5", "4k", "1234", "3.14", "run 2", "(2) run"]
        ])

    def test_rejects(self):
        self.check([
            ("", None), ("   ", None), ("...", None), ("x", None), ("B", None),
            ("привет", None),
            ("hello мир", None), ("мир hello", None),
            ("日本語", None),
            ("a", "a"), ("I", "i"), ("A.", "a"),
        ])

    def test_phrases(self):
        self.check([
            ("  Break   OUT, ", "break out"),
            ("break\tout\nnow", "break out now"),
            ("“Break out”", "break out"),
            ("Well-Known Fact", "well-known fact"),
            ("the dog's bone", "the dog bone"),
            ("a dog", "a dog"),
            ("Take it for granted", "take it for granted"),
            ("hello - world", None),
            ("run, 2 times", None),
        ])

    def test_nfkc_outputs_mapped_again(self):
        # IN-01: NFKC produces apostrophes/dashes the pre-NFKC tables never saw.
        self.check([
            ("well﹘known", "well-known"),   # small em dash -> U+2014
            ("well︱known", "well-known"),   # vertical em dash -> U+2014
            ("well︲known", "well-known"),   # vertical en dash -> U+2013
            ("Hawaiʻi", "hawai'i"),         # okina
            ("donʹt", "don't"),             # modifier prime
            ("ŉ", None),                    # -> 'n: one letter after trimming
        ])

    def test_inner_runs_collapsed(self):
        # IN-03: OCR noise must not create a second key for the same word.
        self.check([
            ("well--known", "well-known"),
            ("well---known", "well-known"),
            ("don''t", "don't"),
            ("a'-'b", "a'b"),
            ("book''s", "book"),
            ("rock'n'roll", "rock'n'roll"),
        ])

    def test_phrase_tokens_keep_d04_scope(self):
        # IN-02, decided: D-04's length rule applies to the whole key, so
        # "plan b" survives; a punctuation-only token rejects the phrase rather
        # than silently dropping it ("rock & roll" must not become "rock roll").
        self.check([
            ("plan B", "plan b"),
            ("vitamin C", "vitamin c"),
            ("rock & roll", None),
        ])

    def test_unicode_folding(self):
        self.check([
            ("Ｒｕｎ", "run"),
            ("ﬁnd", "find"),
            ("Kelvin", "kelvin"),
            ("run out", "run out"),
            ("run­ning", "running"),
            ("run​", "run"),
            ("´run", "run"),
            ("İstanbul", "istanbul"),
            ("Straße", "strasse"),
        ])

    def test_diacritics_kept(self):
        self.check([
            ("café", "café"), ("CAFÉ", "café"),
            ("café", "café"),
            ("naïve", "naïve"), ("résumé", "résumé"),
        ])
        self.assertNotEqual(normalize("résumé"), normalize("resume"))

    def test_no_lemmatisation(self):
        keys = {normalize(w) for w in ["running", "run", "ran", "books", "book"]}
        self.assertEqual(len(keys), 5)

    def test_non_str_raises_type_error(self):
        for bad in (None, 5, b"x", ["a"]):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    normalize(bad)

    def test_idempotent_on_random_inputs(self):
        rng = random.Random(20261024)
        alphabet = (
            list("abcdeiknorsty") + list("ABKS")
            + ["İ", "ß", "ﬁ", "é", "́"]
            + list(APOSTROPHES) + list(QUOTES)
            + ["-", "–", "—", " ", "\t", " ", "­", "​"]
            + list("015") + list(".,()")
            + ["п", "м", "日"]
        )
        for _ in range(20000):
            s = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 12)))
            r = normalize(s)
            if r is None:
                continue
            msg = repr(s)
            self.assertEqual(normalize(r), r, msg)
            self.assertEqual(r, r.casefold(), msg)
            self.assertTrue(r[0].isalpha() and r[-1].isalpha(), msg)
            for ch in r:
                self.assertTrue(ch.isalpha() or ch in "'- ", msg)


if __name__ == "__main__":
    unittest.main()
