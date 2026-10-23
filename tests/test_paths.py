import os
import pathlib
import unittest
from unittest import mock

from lookup.store import default_db_path, open_store
from tests._support import make_tempdir


class DefaultDbPathTests(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)

    def env(self, **values):
        return mock.patch.dict(os.environ, values, clear=True)

    def test_lookup_db_wins(self):
        explicit = self.root / "a" / "x.db"
        with self.env(LOOKUP_DB=str(explicit), XDG_DATA_HOME=str(self.root / "xdg")):
            self.assertEqual(default_db_path(), explicit)

    def test_empty_lookup_db_ignored(self):
        xdg = self.root / "xdg"
        with self.env(LOOKUP_DB="", XDG_DATA_HOME=str(xdg)):
            self.assertEqual(default_db_path(), xdg / "lookup" / "lookup.db")

    def test_xdg_data_home_used(self):
        xdg = self.root / "xdg"
        with self.env(XDG_DATA_HOME=str(xdg)):
            self.assertEqual(default_db_path(), xdg / "lookup" / "lookup.db")

    def test_empty_xdg_ignored(self):
        home = self.root / "home"
        with self.env(XDG_DATA_HOME=""), mock.patch.object(pathlib.Path, "home", return_value=home):
            self.assertEqual(default_db_path(), home / ".local" / "share" / "lookup" / "lookup.db")

    def test_relative_xdg_ignored(self):
        home = self.root / "home"
        with self.env(XDG_DATA_HOME="relative/dir"), mock.patch.object(
            pathlib.Path, "home", return_value=home
        ):
            self.assertEqual(default_db_path(), home / ".local" / "share" / "lookup" / "lookup.db")

    def test_home_fallback(self):
        home = self.root / "home"
        with self.env(), mock.patch.object(pathlib.Path, "home", return_value=home):
            self.assertEqual(default_db_path(), home / ".local" / "share" / "lookup" / "lookup.db")

    def test_default_db_path_creates_nothing(self):
        xdg = self.root / "xdg"
        with self.env(XDG_DATA_HOME=str(xdg)):
            path = default_db_path()
        self.assertFalse(path.exists())
        self.assertFalse(path.parent.exists())

    def test_open_store_without_argument_uses_lookup_db(self):
        expected = pathlib.Path(os.environ["LOOKUP_DB"])
        self.assertFalse(expected.parent.exists())
        conn = open_store()
        self.addCleanup(conn.close)
        self.assertTrue(expected.is_file())


if __name__ == "__main__":
    unittest.main()
