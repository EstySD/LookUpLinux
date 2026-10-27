"""Production gate evidence must reject incomplete runs and always roll back."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import check_app


class HarnessTests(unittest.TestCase):
    def evidence(self):
        return dict(gates=dict.fromkeys(check_app.REQUIRED_GATES,True),restoration=dict(display_restored=True,
            theme_unchanged=True,desktop_restored=True,processes_stopped=True,
            shortcut_restored=True,errors=[]))

    def test_acceptance_requires_every_restore_flag(self):
        evidence=self.evidence()
        self.assertTrue(check_app.accepted(evidence))
        for key in tuple(evidence['restoration']):
            if key=='errors':continue
            incomplete=self.evidence();del incomplete['restoration'][key]
            self.assertFalse(check_app.accepted(incomplete),key)
        evidence['gates']['physical']=False
        self.assertFalse(check_app.accepted(evidence))
        incomplete=self.evidence();incomplete['gates'].pop('tray_quit')
        self.assertFalse(check_app.accepted(incomplete))

    def test_repeat_gate_requires_the_exact_controlled_word_and_ocr(self):
        self.assertTrue(check_app.correct_repeat(dict(mode='ocr',key='word')))
        for status in (dict(mode='ocr',key='unexpected'),dict(mode='ocr',key='english'),dict(mode='primary',key='word')):
            self.assertFalse(check_app.correct_repeat(status))

    def test_failed_partial_prepare_releases_input_and_attempts_finish(self):
        calls=[]
        def remote(action,payload):
            calls.append(action)
            if action=='prepare':raise RuntimeError('controlled_setup_failure')
            return self.evidence()['restoration']
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'result.json'
            with patch.object(check_app,'remote',side_effect=remote), \
                 patch('tools.check_vm_spike.keys') as keys, \
                 patch('tools.check_vm_spike.relative_pointer') as pointer:
                self.assertEqual(check_app.host(output),1)
            self.assertEqual(calls,['prepare','finish'])
            keys.assert_called_once_with('a0 aa e0 db 81')
            pointer.assert_called_once_with(0,0,0)
            evidence=json.loads(output.read_text())
            self.assertEqual(evidence['error'],'controlled_setup_failure')
            self.assertTrue(evidence['restoration']['processes_stopped'])


if __name__=='__main__':unittest.main()
