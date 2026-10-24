import json
import os
import pathlib
import unittest
from unittest import mock

from lookup import config
from lookup.config import Config
from tests._support import make_tempdir


class PathTests(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)

    def env(self, **values):
        return mock.patch.dict(os.environ, values, clear=True)

    def test_config_env_wins(self):
        explicit = self.root / "a" / "c.json"
        with self.env(LOOKUP_CONFIG=str(explicit), XDG_CONFIG_HOME=str(self.root / "x")):
            self.assertEqual(config.config_path(), explicit)

    def test_config_xdg(self):
        xdg = self.root / "xdg"
        with self.env(XDG_CONFIG_HOME=str(xdg)):
            self.assertEqual(config.config_path(), xdg / "lookup" / "config.json")

    def test_config_empty_and_relative_ignored(self):
        home = self.root / "home"
        for bad in ("", "relative/dir"):
            with self.env(LOOKUP_CONFIG="", XDG_CONFIG_HOME=bad), mock.patch.object(
                pathlib.Path, "home", return_value=home
            ):
                self.assertEqual(config.config_path(), home / ".config" / "lookup" / "config.json")

    def test_cache_env_wins(self):
        explicit = self.root / "cc"
        with self.env(LOOKUP_CACHE=str(explicit), XDG_CACHE_HOME=str(self.root / "x")):
            self.assertEqual(config.cache_dir(), explicit)

    def test_cache_xdg(self):
        xdg = self.root / "xdg"
        with self.env(XDG_CACHE_HOME=str(xdg)):
            self.assertEqual(config.cache_dir(), xdg / "lookup")

    def test_cache_home_fallback(self):
        home = self.root / "home"
        for bad in ("", "relative"):
            with self.env(XDG_CACHE_HOME=bad), mock.patch.object(
                pathlib.Path, "home", return_value=home
            ):
                self.assertEqual(config.cache_dir(), home / ".cache" / "lookup")

    def test_resolvers_create_nothing(self):
        xdg = self.root / "xdg"
        with self.env(XDG_CONFIG_HOME=str(xdg), XDG_CACHE_HOME=str(xdg)):
            config.config_path()
            config.cache_dir()
        self.assertFalse(xdg.exists())


class LoadTests(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)
        self.path = self.root / "c.json"

    def write(self, obj):
        self.path.write_text(json.dumps(obj), encoding="utf-8")

    def load(self):
        return config.load(self.path)

    def test_missing_file_defaults(self):
        self.assertEqual(self.load(), Config(dictionaries=(), online=True, clients=None))

    def test_load_uses_config_path_by_default(self):
        self.write({"online": False})
        with mock.patch.dict(os.environ, {"LOOKUP_CONFIG": str(self.path)}):
            self.assertFalse(config.load().online)

    def test_valid_file(self):
        self.write(
            {
                "dictionaries": [{"id": "b/b.ifo", "enabled": False}, {"id": "a/a.ifo"}],
                "online": False,
                "clients": ["at", "gtx"],
            }
        )
        cfg = self.load()
        self.assertEqual(cfg.dictionaries, (("b/b.ifo", False), ("a/a.ifo", True)))
        self.assertIs(cfg.online, False)
        self.assertEqual(cfg.clients, ("at", "gtx"))

    def test_invalid_json(self):
        self.path.write_text("{not json", encoding="utf-8")
        self.assertEqual(self.load(), Config())

    def test_top_level_array(self):
        self.write([1, 2])
        self.assertEqual(self.load(), Config())

    def test_oversized(self):
        pad = "x" * (config.MAX_CONFIG_BYTES + 10)
        self.write({"online": False, "pad": pad})
        self.assertEqual(self.load(), Config())

    def test_non_utf8(self):
        self.path.write_bytes(b'{"online": false, "x": "\xff\xfe"}')
        self.assertEqual(self.load(), Config())

    def test_deep_nesting_does_not_raise(self):
        self.path.write_text("[" * 100000 + "]" * 100000, encoding="utf-8")
        self.assertEqual(self.load(), Config())

    def test_dictionaries_not_a_list(self):
        self.write({"dictionaries": "x", "online": False})
        cfg = self.load()
        self.assertEqual(cfg.dictionaries, ())
        self.assertIs(cfg.online, False)

    def test_bad_dictionary_entries_dropped_one_by_one(self):
        self.write(
            {
                "dictionaries": [
                    "str",
                    5,
                    None,
                    {"enabled": True},
                    {"id": 7},
                    {"id": ""},
                    {"id": "nul\u0000x"},
                    {"id": "a" * 513},
                    {"id": "ok1", "enabled": "yes"},
                    {"id": "good", "enabled": False},
                    {"id": "a" * 512},
                ]
            }
        )
        self.assertEqual(self.load().dictionaries, (("good", False), ("a" * 512, True)))

    def test_duplicate_ids_first_wins(self):
        self.write(
            {"dictionaries": [{"id": "d", "enabled": False}, {"id": "d", "enabled": True}]}
        )
        self.assertEqual(self.load().dictionaries, (("d", False),))

    def test_online_must_be_bool(self):
        for bad in (1, 0, "false", None, []):
            self.write({"online": bad})
            self.assertIs(self.load().online, True)

    def test_clients_filtered(self):
        self.write(
            {
                "clients": [
                    "ok",
                    "has space",
                    "a/b",
                    "q?x=1",
                    "a" * 33,
                    "",
                    5,
                    "a" * 32,
                    "dot.dash-under_",
                    "new\nline",
                ]
            }
        )
        self.assertEqual(self.load().clients, ("ok", "a" * 32, "dot.dash-under_"))

    def test_clients_none_when_nothing_valid(self):
        self.write({"clients": ["a b", "x/y"]})
        self.assertIsNone(self.load().clients)
        self.write({"clients": []})
        self.assertIsNone(self.load().clients)
        self.write({"clients": "gtx"})
        self.assertIsNone(self.load().clients)

    def test_load_does_not_create_parent(self):
        missing = self.root / "nope" / "deeper" / "c.json"
        config.load(missing)
        self.assertFalse((self.root / "nope").exists())

    def test_config_is_frozen(self):
        with self.assertRaises(Exception):
            Config().online = False


if __name__ == "__main__":
    unittest.main()
