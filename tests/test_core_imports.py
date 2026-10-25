"""D-15: the core imports only the stdlib and creates nothing on import."""
import os
import subprocess
import sys
import unittest
from pathlib import Path

from tests._support import make_tempdir

ROOT = Path(__file__).resolve().parents[1]

_IMPORTS = "import lookup, lookup.normalize, lookup.store, lookup.stardict, lookup.dsl, lookup.mdx, lookup.lzo, lookup.ripemd128, lookup.dictzip, lookup.dicts, lookup.config, lookup.online, lookup.translate, lookup.ocr\n"
_STDLIB_CODE = (
    "import json, sys\n"
    + _IMPORTS
    + "print(json.dumps(sorted({m.split('.')[0] for m in sys.modules}"
    " - set(sys.stdlib_module_names) - {'lookup', '__main__'})))\n"
)


class CoreImportTests(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)

    def _run(self, code):
        return subprocess.run(
            [sys.executable, "-S", "-c", code],
            cwd=ROOT,
            env=os.environ.copy(),
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_core_imports_only_stdlib(self):
        proc = self._run(_STDLIB_CODE)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        import json

        extra = json.loads(proc.stdout.strip().splitlines()[-1])
        gui = [m for m in extra if m in ("PyQt6", "PyQt5", "PySide6", "PySide2")]
        self.assertEqual(gui, [], "GUI toolkit imported by the core")
        self.assertEqual(extra, [], "non-stdlib modules imported by the core")

    def test_import_has_no_side_effects(self):
        db = Path(os.environ["LOOKUP_DB"])
        self.assertFalse(db.parent.exists())
        for key in ('LOOKUP_CONFIG', 'LOOKUP_CACHE', 'LOOKUP_DICTS'):
            path = Path(os.environ[key])
            self.assertFalse(path.parent.exists() if key == 'LOOKUP_CONFIG' else path.exists())
        proc = self._run(_IMPORTS)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(db.exists())
        self.assertFalse(db.parent.exists())
        for key in ('LOOKUP_CONFIG', 'LOOKUP_CACHE', 'LOOKUP_DICTS'):
            path = Path(os.environ[key])
            self.assertFalse(path.parent.exists() if key == 'LOOKUP_CONFIG' else path.exists())

    def test_public_names_present(self):
        from lookup import normalize as norm_mod
        from lookup import store

        import importlib
        names = {
            'dicts': 'Article SearchResult DictError DictSet open_all discover dict_roots form_candidates fold_key',
            'config': 'load Config config_path cache_dir',
            'online': 'translate_online TranslateError OnlineResult REASONS DEFAULT_CLIENTS',
            'translate': 'lookup classify Result',
            'ocr': 'OcrError Word Transform Selection parse_tsv select_word choose_query',
            'stardict': 'open_stardict', 'dsl': 'open_dsl', 'mdx': 'open_mdx',
            'lzo': 'decompress LzoError', 'ripemd128': 'digest', 'dictzip': 'DictzipFile DictzipError',
        }
        for module, public in names.items():
            loaded = importlib.import_module('lookup.' + module)
            for name in public.split():
                self.assertTrue(hasattr(loaded, name), f'{module}.{name}')
        self.assertEqual(store.CURRENT_VERSION, 2)

        for name in ("normalize", "CONTRACTIONS"):
            self.assertTrue(hasattr(norm_mod, name), name)
        for name in (
            "open_store",
            "upsert_word",
            "default_db_path",
            "SchemaTooNewError",
            "MigrationError",
            "MIGRATIONS",
            "CURRENT_VERSION",
            "CONTEXT_MAX_CHARS",
        ):
            self.assertTrue(hasattr(store, name), name)


if __name__ == "__main__":
    unittest.main()
