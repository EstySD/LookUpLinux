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

    def test_deadline_starts_at_first_process_and_timings_sum_both_passes(self):
        clock=[0,.2,2,4.188,4.238,4.3,5.489,5.539]
        with mock.patch.object(ocr.time,'perf_counter',side_effect=clock), \
             mock.patch.object(ocr.subprocess,'run',side_effect=[self.completed(tsv()),self.completed(self.hit)]) as run:
            result=self.recognize()
        self.assertEqual([call.kwargs['timeout'] for call in run.call_args_list],[3,3])
        self.assertAlmostEqual(result.timings['ocr'],3377)
        self.assertAlmostEqual(result.timings['select'],100)
        self.assertAlmostEqual(result.timings['prepare_image'],200)
        self.assertAlmostEqual(result.timings['total'],5539)

    def test_successful_six_returns_unchanged_first_selection_without_retry(self):
        with mock.patch.object(ocr.subprocess,'run',side_effect=[self.completed(self.hit),AssertionError('extra process')]) as run:
            result=self.recognize()
        self.assertEqual((result.selection.word,result.selection.context,result.selection.span),('run','run',(0,3)))
        run.assert_called_once()

    def test_explicit_eleven_and_disabled_fallback_remain_single_pass(self):
        for options in ({'psm':11},{'fallback':False},{'psm':11,'fallback':True}):
            with self.subTest(options=options), \
                 mock.patch.object(ocr.subprocess,'run',return_value=self.completed(tsv())) as run:
                self.assertIsNone(self.recognize(**options).selection)
                run.assert_called_once()

    def test_two_valid_misses_stop_without_third_process(self):
        with mock.patch.object(ocr.subprocess,'run',return_value=self.completed(tsv())) as run:
            self.assertIsNone(self.recognize().selection)
        self.assertEqual(run.call_count,2)

    def test_retry_uses_remaining_absolute_budget_and_exhaustion_launches_nothing(self):
        with mock.patch.object(ocr.time,'perf_counter',side_effect=[0,.1,.2,2.2,4.1,4.3,5.0,5.1]), \
             mock.patch.object(ocr.subprocess,'run',side_effect=[self.completed(tsv()),self.completed(self.hit)]) as run:
            self.assertEqual(self.recognize().selection.word,'run')
        self.assertAlmostEqual(run.call_args_list[1].kwargs['timeout'],1.9)
        with mock.patch.object(ocr.time,'perf_counter',side_effect=[0,.1,.2,2.2,6.3,6.4]), \
             mock.patch.object(ocr.subprocess,'run',return_value=self.completed(tsv())) as run:
            with self.assertRaisesRegex(ocr.OcrError,'^timeout$'):self.recognize()
        run.assert_called_once()

    def test_process_or_parser_failure_never_retries_and_errors_stay_private(self):
        outcomes=[FileNotFoundError('secret'),OSError('secret'),
            subprocess.TimeoutExpired('secret',3,output=b'secret'),
            subprocess.CompletedProcess([],1,b'secret',b'secret'),
            subprocess.CompletedProcess([],1,b'',b'eng.traineddata secret'),
            self.completed(b'secret'),self.completed(b'x'*(ocr.MAX_TSV_BYTES+1))]
        for outcome in outcomes:
            with self.subTest(outcome=type(outcome).__name__):
                options={'side_effect':outcome} if isinstance(outcome,Exception) else {'return_value':outcome}
                with mock.patch.object(ocr.subprocess,'run',**options) as run:
                    with self.assertRaises(ocr.OcrError) as caught:self.recognize()
                self.assertNotIn('secret',str(caught.exception));run.assert_called_once()

    def test_second_pass_failure_propagates_without_more_processes(self):
        for outcome in (subprocess.TimeoutExpired('secret',3),self.completed(b'bad-tsv')):
            with self.subTest(outcome=type(outcome).__name__), \
                 mock.patch.object(ocr.subprocess,'run',side_effect=[self.completed(tsv()),outcome]) as run:
                with self.assertRaises(ocr.OcrError):self.recognize()
                self.assertEqual(run.call_count,2)

    def test_fallback_requires_boolean_before_preparation_or_process(self):
        for value in (None,0,1,'false'):
            with self.subTest(value=value),mock.patch.object(ocr.subprocess,'run') as run:
                with self.assertRaisesRegex(ocr.OcrError,'^invalid_image$'):self.recognize(fallback=value)
                run.assert_not_called()

    def test_retry_does_not_jump_from_rejected_hit_to_valid_neighbor(self):
        for text,confidence in (('bad123',95),('noise',10)):
            output=tsv((5,1,1,1,1,1,48,48,20,20,confidence,text),
                       (5,1,1,1,1,2,72,48,60,20,95,'run'))
            with self.subTest(text=text),mock.patch.object(ocr.subprocess,'run',side_effect=[self.completed(tsv()),self.completed(output)]):
                self.assertIsNone(self.recognize().selection)


if __name__=='__main__':unittest.main()
