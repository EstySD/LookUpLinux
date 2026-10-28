"""Native acceptance must fail closed without required observations and cleanup."""
import unittest
from tools import check_settings_app as harness


class AcceptanceTests(unittest.TestCase):
    def report(self):
        return dict(acceptance='agent',mode='native-installed',
                    gates=dict.fromkeys(harness.REQUIRED_GATES,True),
                    cleanup=dict.fromkeys(harness.REQUIRED_CLEANUP,True))

    def test_complete_native_report(self):
        self.assertTrue(harness.accepted(self.report()))

    def test_missing_false_or_skipped_gate_fails(self):
        for value in (None,False,'skipped',1):
            report=self.report();report['gates'][next(iter(harness.REQUIRED_GATES))]=value
            self.assertFalse(harness.accepted(report))
        report=self.report();report['gates'].pop(next(iter(harness.REQUIRED_GATES)))
        self.assertFalse(harness.accepted(report))

    def test_cleanup_or_mock_report_cannot_pass(self):
        report=self.report();report['cleanup'][next(iter(harness.REQUIRED_CLEANUP))]=False
        self.assertFalse(harness.accepted(report))
        for mode in ('mock','offscreen','native-source'):
            report=self.report();report['mode']=mode
            self.assertFalse(harness.accepted(report))
        report=self.report();report['error']='bounded_failure'
        self.assertFalse(harness.accepted(report))
