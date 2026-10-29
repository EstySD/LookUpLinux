"""Numeric-only telemetry must not turn private contents into diagnostics."""
import contextlib
import io
import json
import os
import unittest
from unittest import mock

from lookup import timing, translate, app


def records(stream):
    return [json.loads(line.removeprefix('lookup-timing:')) for line in stream.getvalue().splitlines()]


class TimingTests(unittest.TestCase):
    def test_disabled_is_silent_and_numeric_identity_is_stable_per_process(self):
        stream=io.StringIO()
        with mock.patch.dict(os.environ,{'LOOKUP_TIMING':'0'}):
            sink=timing.Sink(stream=stream)
            self.assertFalse(sink.emit('trigger',1))
        self.assertEqual(stream.getvalue(),'')
        self.assertEqual(sink.run_id,timing.Sink().run_id)
        self.assertEqual(sink.pid,os.getpid())

    def test_numeric_allowlist_rejects_secret_nonfinite_unknown_and_bool(self):
        stream=io.StringIO()
        sink=timing.Sink(enabled=True,stream=stream,clock=lambda:123456)
        for values in (dict(word='secret-word'),dict(context='secret-context'),dict(token='secret-token'),
                       dict(provider='https://private'),dict(elapsed_ms=float('nan')),
                       dict(elapsed_ms=float('inf')),dict(elapsed_ms=True),dict(elapsed_ms=10**1000)):
            with self.subTest(values=tuple(values)):
                self.assertFalse(sink.emit('useful_ready',1,**values))
        self.assertFalse(sink.emit('private exception text',1))
        self.assertFalse(sink.emit('trigger',True))
        self.assertEqual(stream.getvalue(),'')
        self.assertTrue(sink.emit('useful_ready',7,elapsed_ms=12.5,engine_ms=10,ocr=3))
        row=records(stream)[0]
        self.assertTrue(all(type(value) in (int,float) for value in row.values()))
        self.assertEqual((row['pid'],row['run'],row['request'],row['stage'],row['mono_ns']),
                         (os.getpid(),sink.run_id,7,timing.STAGES['useful_ready'],123456))
        self.assertNotIn('process_start',row)

    def test_cli_known_field_format_is_compatible_and_unknowns_are_silent(self):
        stream=io.StringIO()
        self.assertTrue(timing.print_cli(dict(ocr=2.0,total=3.125),enabled=True,stream=stream))
        self.assertEqual(stream.getvalue(),'timing: ocr=2.000ms total=3.125ms\n')
        self.assertFalse(timing.print_cli(dict(secret='private'),enabled=True,stream=stream))
        self.assertNotIn('private',stream.getvalue())

    def test_only_nonempty_answer_counts_useful(self):
        from lookup.dicts import Article
        self.assertFalse(timing.useful(None))
        self.assertFalse(timing.useful(translate.Result('word','private')))
        header=Article('Source','private',None,(),'')
        self.assertFalse(timing.useful(translate.Result('word','private',articles=(header,))))
        self.assertTrue(timing.useful(translate.Result('word','private',translation='answer')))

    def test_gui_internal_stages_refuse_loading_and_stale_meaning_without_text_leaks(self):
        from tests.test_app_gui import GuiTests,QApplication
        if QApplication is None:self.skipTest('PyQt6 unavailable')
        fixture=GuiTests()
        fixture.setUpClass();fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        owner=fixture.owner
        stream=io.StringIO()
        owner._timing=timing.Sink(enabled=True,stream=stream)
        owner.Trigger('secret-activation-token')
        identity=owner.engine.generation
        def event(stage,result=None):
            return app.Event(identity,stage,result=result,point=(100,100),monitor=fixture.monitor,
                             context='secret-context',elapsed_ms=5)
        owner.receive(event('frozen'))
        self.assertNotIn(timing.STAGES['useful_ready'],[row['stage'] for row in records(stream)])
        value=translate.Result('word','secret-word',translation='secret-answer',context_meaning='secret-meaning')
        owner.receive(event('ready',value))
        owner.dismiss()
        owner.receive(event('context',value))
        rows=records(stream)
        self.assertEqual(sum(row['stage']==timing.STAGES['useful_ready'] for row in rows),1)
        self.assertEqual(sum(row['stage']==timing.STAGES['meaning_ready'] for row in rows),1)
        self.assertTrue(any(row['stage']==timing.STAGES['present'] and row['useful']==1 for row in rows))
        self.assertNotIn('secret-',stream.getvalue())
