"""Acceptance cannot pass with missing gates or incomplete cleanup."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from tools import check_learning_app as check


class EvidenceTests(unittest.TestCase):
    def evidence(self):
        return dict(gates=dict.fromkeys(check.REQUIRED_GATES,True),
                    cleanup=dict.fromkeys(check.REQUIRED_CLEANUP,True))

    def test_missing_false_or_failed_gate_cannot_pass(self):
        self.assertTrue(check.accepted(self.evidence()))
        for gate in check.REQUIRED_GATES:
            evidence=self.evidence();evidence['gates'].pop(gate)
            self.assertFalse(check.accepted(evidence),gate)
            evidence=self.evidence();evidence['gates'][gate]=False
            self.assertFalse(check.accepted(evidence),gate)
        evidence=self.evidence();evidence['error']='controlled_failure'
        self.assertFalse(check.accepted(evidence))

    def test_cleanup_is_required_and_recorded(self):
        for gate in check.REQUIRED_CLEANUP:
            evidence=self.evidence();evidence['cleanup'].pop(gate)
            self.assertFalse(check.accepted(evidence),gate)
            evidence=self.evidence();evidence['cleanup'][gate]=False
            self.assertFalse(check.accepted(evidence),gate)

    def test_import_unverified_is_not_reported_as_success(self):
        report=check.import_status(None)
        self.assertFalse(report['verified'])
        self.assertEqual(report['status'],'unverified')
        report=check.import_status(dict(verified=True,unchanged_file=True))
        self.assertTrue(report['verified'])

    def test_available_import_failure_fails_run_without_losing_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)
            for failure in ('timeout','invalid_json','failed_import'):
                report=self.evidence()
                def run(*args,**kwargs):
                    if failure=='timeout':raise subprocess.TimeoutExpired('anki',1)
                    (output/'anki-import.json').write_text('invalid' if failure=='invalid_json' else json.dumps(dict(verified=False)))
                    return subprocess.CompletedProcess([],0,'','')
                with mock.patch.object(check.subprocess,'run',side_effect=run):
                    check.finish_import(report,output,Path('isolated-anki-python'))
                self.assertFalse(report['passed'],failure)
                self.assertFalse(report['anki_import']['verified'],failure)
                self.assertEqual(report['cleanup'],self.evidence()['cleanup'])
            report=self.evidence()
            check.finish_import(report,output,None)
            self.assertTrue(report['passed'])
            self.assertFalse(report['anki_import']['verified'])
