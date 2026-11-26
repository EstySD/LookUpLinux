"""Public distribution must preserve licensing and exclude private workspace state."""
import hashlib
from pathlib import Path
import tarfile
import tempfile
import unittest

from tools.build_release import build


class ReleaseTests(unittest.TestCase):
    def test_assets_are_deterministic_and_public(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = (Path(directory)/name for name in ('first', 'second'))
            build(first, 'v0.3.0')
            build(second, 'v0.3.0')
            self.assertEqual(len(list(first.glob('*.tar.gz'))), 2)
            for path in first.iterdir():
                self.assertEqual(path.read_bytes(), (second/path.name).read_bytes())
            for line in (first/'SHA256SUMS').read_text().splitlines():
                digest, name = line.split('  ')
                self.assertEqual(digest, hashlib.sha256((first/name).read_bytes()).hexdigest())
            with tarfile.open(first/'lookup-linux-0.3.0-source.tar.gz') as archive:
                names = archive.getnames()
                self.assertIn('lookup-linux-0.3.0/LICENSE', names)
                self.assertIn('lookup-linux-0.3.0/docs/DICTIONARIES.md', names)
                self.assertIn('lookup-linux-0.3.0/docs/UBUNTU.md', names)
                self.assertIn('lookup-linux-0.3.0/docs/AUR.md', names)
                self.assertIn('lookup-linux-0.3.0/packaging/gnome/extension.js', names)
                self.assertIn('lookup-linux-0.3.0/packaging/gnome/metadata.json', names)
                self.assertIn('lookup-linux-0.3.0/packaging/gnome/schemas/org.gnome.shell.extensions.lookup-linux.gschema.xml', names)
                for name in ('CMakeLists.txt','capture.cpp','metadata.json','README.md'):
                    self.assertIn('lookup-linux-0.3.0/native/kwin-capture/'+name,names)
                self.assertFalse(any('/.omx/' in n or '/.planning/' in n or '/lookupper/' in n or n.endswith(('.db', '.pyc')) for n in names))
                self.assertFalse(any('/packaging/aur/' in n for n in names))
            with tarfile.open(first/'lookup-linux-0.3.0-archlinux-x86_64-build-kit.tar.gz') as archive:
                recipe = archive.extractfile('lookup-linux-0.3.0-build-kit/PKGBUILD').read()
                self.assertNotIn(b'mueller', recipe.lower())
                self.assertNotIn(b'@LOCAL_SOURCE_SHA256@', recipe)

    def test_invalid_or_mismatched_tag_and_nonempty_output_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'output'
            for tag in ('v9.9.9', 'main', 'v0.2.0;echo unsafe'):
                with self.subTest(tag=tag), self.assertRaises(ValueError):
                    build(output, tag)
            self.assertFalse(output.exists())
            output.mkdir()
            (output/'keep').write_text('private')
            with self.assertRaises(ValueError):
                build(output, 'v0.3.0')
            self.assertEqual((output/'keep').read_text(), 'private')
