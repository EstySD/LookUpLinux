import re
import subprocess
import sys
import unittest
from pathlib import Path

from tests._support import make_tempdir

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "lookup" / "data"
GENERATOR = ROOT / "tools" / "gen_irregular.py"


def read_entries(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    return [ln for ln in lines if ln.strip() and not ln.startswith("#")]


class CommittedDataTests(unittest.TestCase):
    def setUp(self):
        self.entries = read_entries(DATA / "irregular.txt")

    def test_size(self):
        self.assertTrue(4000 <= len(self.entries) <= 8000, len(self.entries))

    def test_shape(self):
        for line in self.entries:
            fields = line.split()
            self.assertGreaterEqual(len(fields), 2, line)
            for tok in fields:
                self.assertEqual(tok, tok.lower(), line)
                self.assertNotIn("_", tok, line)
                self.assertRegex(tok, r"^[a-z][a-z'-]*$")

    def test_forms_unique_and_sorted(self):
        forms = [ln.split()[0] for ln in self.entries]
        self.assertEqual(len(forms), len(set(forms)))
        self.assertEqual(forms, sorted(forms))

    def test_known_forms(self):
        table = {ln.split()[0]: ln.split()[1:] for ln in self.entries}
        for form, base in (
            ("ran", "run"),
            ("went", "go"),
            ("men", "man"),
            ("children", "child"),
            ("mice", "mouse"),
            ("teeth", "tooth"),
            ("stopped", "stop"),
            ("running", "run"),
            ("better", "good"),
        ):
            self.assertIn(form, table)
            self.assertEqual(table[form][0], base, form)

    def test_header_is_comments(self):
        text = (DATA / "irregular.txt").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("#"))
        self.assertIn("WordNet 3.1", text[:600])

    def test_notice(self):
        text = (DATA / "NOTICE-wordnet.txt").read_text(encoding="utf-8")
        self.assertIn("Princeton University", text)
        self.assertIn("WordNet 3.1 Copyright 2011", text)
        self.assertIn("This software and database is being provided to you", text)
        self.assertFalse(re.search(r"^\s*\d+ ", text, re.M), "line numbers left in notice")


class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)
        self.src = self.root / "dict"
        self.out = self.root / "out"
        self.src.mkdir()

    def run_gen(self):
        return subprocess.run(
            [sys.executable, "-I", str(GENERATOR), str(self.src), str(self.out)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def write_sources(self):
        (self.src / "verb.exc").write_text(
            "ran run\nwent go\nbad_form go\nTitle word\nsaw see saw\n", encoding="utf-8"
        )
        (self.src / "noun.exc").write_text(
            "men man\nsaw saw sawn\ngo_betweens go-between\nteeth tooth\n", encoding="utf-8"
        )
        (self.src / "adj.exc").write_text(
            "better good well\nbest good well\nmy-own x extra bases here\nodd1 x\n",
            encoding="utf-8",
        )

    def test_merge_filter_sort(self):
        self.write_sources()
        res = self.run_gen()
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(
            read_entries(self.out / "irregular.txt"),
            [
                "best good well",
                "better good well",
                "men man",
                "my-own x extra bases here",
                "ran run",
                "saw see saw sawn",
                "teeth tooth",
                "went go",
            ],
        )
        self.assertFalse((self.out / "NOTICE-wordnet.txt").exists())

    def test_notice_from_data_noun(self):
        self.write_sources()
        lines = [
            "  1 This software and database is being provided to you, the LICENSEE, by  ",
            "  2 Princeton University under the following license.  ",
            "  3   ",
            " 14 WordNet 3.1 Copyright 2011 by Princeton University.  All rights reserved.  ",
        ]
        lines += ["%3d filler line" % n for n in range(5, 30)]
        lines += ["00001740 03 n 01 entity 0 003 | not licence text"]
        (self.src / "data.noun").write_text("\n".join(lines) + "\n", encoding="utf-8")
        res = self.run_gen()
        self.assertEqual(res.returncode, 0, res.stderr)
        notice = (self.out / "NOTICE-wordnet.txt").read_text(encoding="utf-8")
        self.assertIn("This software and database is being provided to you, the LICENSEE, by\n", notice)
        self.assertIn("WordNet 3.1 Copyright 2011 by Princeton University.", notice)
        self.assertNotIn("not licence text", notice)
        self.assertNotIn("  \n", notice)

    def test_wrong_data_noun_fails(self):
        self.write_sources()
        (self.src / "data.noun").write_text("something else\n", encoding="utf-8")
        self.assertNotEqual(self.run_gen().returncode, 0)

    def test_empty_input_fails(self):
        self.assertNotEqual(self.run_gen().returncode, 0)

    def test_regenerating_matches_committed_file_header(self):
        self.write_sources()
        self.run_gen()
        generated = (self.out / "irregular.txt").read_text(encoding="utf-8")
        committed = (DATA / "irregular.txt").read_text(encoding="utf-8")
        head = lambda t: [ln for ln in t.splitlines() if ln.startswith("#")]
        self.assertEqual(head(generated), head(committed))


if __name__ == "__main__":
    unittest.main()
