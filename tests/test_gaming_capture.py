"""Gamescope SIGUSR2 capture and bounded PipeWire fallback; no game required."""
import base64
import unittest
from unittest import mock

from lookup import gaming
from lookup.platform import PlatformError
from tests._support import make_tempdir

PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==')


class GamingCaptureTests(unittest.TestCase):
    def setUp(self):
        self.root=make_tempdir(self)

    def test_sigusr2_consumes_and_removes_temporary_frame(self):
        frame=self.root/'gamescope_fake.png'
        def signal_process(pid,code):
            self.assertEqual(code,gaming.SIGUSR2)
            frame.write_bytes(PNG)
        with mock.patch.object(gaming.session,'find_gamescope_pids',return_value=(123,)), \
             mock.patch.object(gaming.os,'kill',side_effect=signal_process):
            snapshot=gaming.capture_gamescope({'XDG_RUNTIME_DIR':str(self.root)})
        self.assertEqual((snapshot.width,snapshot.height),(1,1))
        self.assertEqual(snapshot.image().backend,'gamescope')
        self.assertEqual(snapshot.image().png,PNG)
        self.assertFalse(list(self.root.glob('gamescope_*.png')))

    def test_pipewire_fallback_when_gamescope_absent(self):
        with mock.patch.object(gaming.session,'find_gamescope_pids',return_value=()), \
             mock.patch.object(gaming,'run',return_value=PNG) as command:
            snapshot=gaming.capture_gamescope({})
        self.assertEqual(snapshot.image().backend,'pipewire')
        self.assertTrue(command.called)
        self.assertIn('pipewiresrc',command.call_args.args[0])

    def test_no_capture_path_is_bounded(self):
        with mock.patch.object(gaming.session,'find_gamescope_pids',return_value=()), \
             mock.patch.object(gaming,'run',side_effect=PlatformError('missing_command')):
            with self.assertRaises(PlatformError) as error:
                gaming.capture_gamescope({})
        self.assertEqual(error.exception.reason,'gaming_capture_unavailable')

    def test_readiness_uses_process_or_pipewire(self):
        with mock.patch.object(gaming.session,'find_gamescope_pids',return_value=(123,)):
            self.assertTrue(gaming.gamescope_capture_ready({}))
        with mock.patch.object(gaming.session,'find_gamescope_pids',return_value=()), \
             mock.patch.object(gaming.shutil,'which',return_value='/bin/gst-launch-1.0'):
            self.assertTrue(gaming.gamescope_capture_ready({}))
        with mock.patch.object(gaming.session,'find_gamescope_pids',return_value=()), \
             mock.patch.object(gaming.shutil,'which',return_value=None):
            self.assertFalse(gaming.gamescope_capture_ready({}))


if __name__=='__main__':
    unittest.main()
