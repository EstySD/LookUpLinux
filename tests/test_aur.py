"""Prepared AUR metadata is bound to public source and never implies publication."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from tools.build_release import build
from tools.stage_aur import stage


class AurTests(unittest.TestCase):
    def test_recipe_uses_exact_public_source_hash_and_build_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);build(root/'release','v0.2.1')
            source=root/'release/lookup-linux-0.2.1-source.tar.gz'
            receipt=stage(source,root/'aur')
            recipe=(root/'aur/PKGBUILD').read_text(encoding='utf-8')
            self.assertIn('v0.2.1/lookup-linux-0.2.1-source.tar.gz',recipe)
            self.assertIn(hashlib.sha256(source.read_bytes()).hexdigest(),recipe)
            self.assertIn('cmake -S lookup-linux-0.2.1/native/kwin-capture',recipe)
            self.assertNotIn('lookup-source/',recipe)
            self.assertNotIn('mueller',recipe.lower())
            self.assertNotIn('@LOCAL_SOURCE_SHA256@',recipe)
            self.assertEqual(receipt['publication'],'not_published')
            with self.assertRaisesRegex(ValueError,'output_not_empty'):
                stage(source,root/'aur')

    def test_wrong_version_source_is_refused_before_writing(self):
        import io
        import tarfile
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'wrong.tar.gz'
            with tarfile.open(source,'w:gz') as archive:
                entry=tarfile.TarInfo('lookup-linux-9.9.9/LICENSE');entry.size=1
                archive.addfile(entry,io.BytesIO(b'x'))
            with self.assertRaisesRegex(ValueError,'unsafe_release_archive'):
                stage(source,root/'output')
            self.assertFalse((root/'output').exists())
