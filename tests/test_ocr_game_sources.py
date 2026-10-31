"""Immutable actual-game sources; real OCR is never replaced by fixture output."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest import mock

from lookup import ocr
try:
    from PyQt6.QtGui import QImage
except ImportError:
    QImage=None

ROOT=Path(__file__).parent/'fixtures/ocr-games'


@unittest.skipIf(QImage is None,'PyQt6 unavailable')
class GameSourceIntegrityTests(unittest.TestCase):
    def test_sources_match_original_hash_and_prepared_pixel_transform(self):
        from PyQt6.QtGui import QImage
        cases=json.loads((ROOT/'manifest.json').read_text())['cases']
        self.assertEqual(len(cases),4)
        for case in cases:
            with self.subTest(source=case['path']):
                self.assertEqual(hashlib.sha256((ROOT/case['path']).read_bytes()).hexdigest(),case['source_sha256'])
                prepared,transform=ocr._prepare_image(ROOT/case['path'],case['point'],2,'auto')
                image=QImage.fromData(prepared).convertToFormat(QImage.Format.Format_RGBA8888)
                pixels=image.constBits().asstring(image.sizeInBytes())
                self.assertEqual(hashlib.sha256(pixels).hexdigest(),case['prepared_pixels_sha256'])
                self.assertEqual([transform.left,transform.top,transform.scale_x,transform.scale_y,transform.border],case['transform'])


@unittest.skipUnless(shutil.which('tesseract') and QImage is not None,'real OCR requires Tesseract and PyQt6')
class GameSourceOcrTests(unittest.TestCase):
    def test_actual_default_cascade_and_independent_passes(self):
        original=subprocess.run
        for case in json.loads((ROOT/'manifest.json').read_text())['cases']:
            with self.subTest(source=case['path']):
                calls=[]
                def observe(*args,**kwargs):
                    calls.append((args[0],kwargs['input']))
                    return original(*args,**kwargs)
                with mock.patch.object(ocr.subprocess,'run',side_effect=observe):
                    result=ocr.recognize_image(ROOT/case['path'],case['point'])
                self.assertEqual((result.selection.word,result.selection.span),(case['word'],tuple(case['span'])))
                self.assertEqual(result.selection.box,tuple(case['box']))
                self.assertEqual([call[0][6] for call in calls],['6'] if case['first_pass_selects'] else ['6','11'])
                if len(calls)==2:self.assertIs(calls[0][1],calls[1][1])
                direct=ocr.recognize_image(ROOT/case['path'],case['point'],fallback=False)
                self.assertEqual(direct.selection is not None,case['first_pass_selects'])
                eleven=ocr.recognize_image(ROOT/case['path'],case['point'],psm=11,fallback=False)
                self.assertEqual(eleven.selection.word,case['word'])

    def test_blank_and_distant_points_do_not_promote_unrelated_words(self):
        from PyQt6.QtCore import QBuffer,QIODevice
        from PyQt6.QtGui import QImage,QColor
        image=QImage(1280,800,QImage.Format.Format_RGB32);image.fill(QColor('white'))
        buffer=QBuffer();buffer.open(QIODevice.OpenModeFlag.WriteOnly);image.save(buffer,'PNG')
        self.assertIsNone(ocr.recognize_image(bytes(buffer.data()),(640,400)).selection)
        self.assertIsNone(ocr.recognize_image(ROOT/'04-recovery-name.png',(1200,700)).selection)


if __name__=='__main__':unittest.main()
