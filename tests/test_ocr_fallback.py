"""Bounded shared-pixel OCR retry at the external process boundary."""
import subprocess
import unittest
from unittest import mock

from lookup import ocr
from tests._support import make_tempdir
from tests.test_ocr import tsv

try:
    from PyQt6.QtGui import QImage,QColor
except ImportError:
    QImage=None


@unittest.skipIf(QImage is None,'PyQt6 unavailable')
class FallbackTests(unittest.TestCase):
    def setUp(self):
        self.root=make_tempdir(self)
        self.image=self.root/'public.png'
        image=QImage(200,80,QImage.Format.Format_RGB32)
        image.fill(QColor('white'));image.save(str(self.image))
        self.hit=tsv((5,1,1,1,1,1,48,48,60,20,95,'run'))

    def recognize(self,**kwargs):
        return ocr.recognize_image(self.image,(25,25),**kwargs)

    def completed(self,output):
        return subprocess.CompletedProcess([],0,output,b'')

    def test_valid_six_miss_retries_eleven_on_same_prepared_pixels(self):
        with mock.patch.object(ocr,'_prepare_image',wraps=ocr._prepare_image) as prepare, \
             mock.patch.object(ocr.subprocess,'run',side_effect=[self.completed(tsv()),self.completed(self.hit)]) as run:
            result=self.recognize()
        self.assertIsNotNone(result.selection)
        self.assertEqual((result.selection.word,result.selection.box),('run',(20,20,30,10)))
        self.assertEqual([call.args[0][6] for call in run.call_args_list],['6','11'])
        self.assertIs(run.call_args_list[0].kwargs['input'],run.call_args_list[1].kwargs['input'])
        prepare.assert_called_once()


if __name__=='__main__':unittest.main()
