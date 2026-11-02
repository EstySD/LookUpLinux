import json
import os
import sys
import time
import unittest
from unittest.mock import patch

from lookup import capture
from lookup.platform import (Monitor, PlatformError, image_point, monitor_at,
                             parse_monitors, popup_rect, read_primary, run,
                             cursor_position, window_action)


class GeometryTests(unittest.TestCase):
    def test_actual_ratios_and_negative_origins(self):
        for scale in (1, 1.25, 1.5, 2):
            monitor = Monitor('left', -1920/scale, -200, 1920/scale, 1080/scale, scale)
            point = (monitor.x+100, monitor.y+50)
            self.assertEqual(monitor_at(point, [monitor]), monitor)
            self.assertEqual(image_point(point, monitor, (1920, 1080)), (100*scale, 50*scale))
            with self.assertRaises(PlatformError):
                monitor_at((0, 0), [monitor])
        self.assertEqual(image_point((50, 25), Monitor('x', 0, 0, 100, 50, 1.25), (128, 64)), (64, 32))

    def test_invalid_and_popup_edges(self):
        for value in (float('nan'), float('inf'), True, '4'):
            with self.assertRaises(PlatformError):
                Monitor('x', value, 0, 100, 100, 1)
        for point in ((0, 0), (99, 99), (99, 0), (0, 99)):
            x, y, w, h = popup_rect(point, (30, 20), (0, 0, 100, 100))
            self.assertTrue(0 <= x <= 100-w and 0 <= y <= 100-h)
        self.assertEqual(popup_rect((99, 99), (300, 200), (-10, -20, 100, 100)), (-10, -20, 100, 100))

    def test_kscreen_metadata(self):
        output = dict(enabled=True, connected=True, name='Virtual-1', scale=1.25,
                      pos={'x': -1536, 'y': 0}, currentModeId='1',
                      modes=[{'id': '1', 'size': {'width': 1920, 'height': 1080}}])
        self.assertEqual(parse_monitors(json.dumps({'outputs': [output]}))[0].width, 1536)
        for bad in (b'{}', b'[]', b'bad', json.dumps({'outputs': [dict(output, scale=0)]})):
            with self.assertRaises(PlatformError):
                parse_monitors(bad)


class BoundaryTests(unittest.TestCase):
    def test_window_ownership_requires_pid_filter_conjunction(self):
        from lookup import platform
        owned='{11111111-1111-1111-1111-111111111111}'
        foreign='{22222222-2222-2222-2222-222222222222}'
        def search(argv,*args,**kwargs):
            if argv[1]=='search':
                return (owned if '--all' in argv else owned+' '+foreign).encode('ascii')
            return b''
        with patch.object(platform,'run',side_effect=search) as command:
            self.assertEqual(platform.owned_window({},123),(owned,))
            with self.assertRaises(PlatformError):
                platform.window_action({},123,foreign,'windowactivate')
            platform.window_action({},123,owned,'windowactivate')
            self.assertEqual(command.call_args.args[0],['kdotool','windowactivate',owned])

    def test_private_kdotool_resolver_covers_every_run_call(self):
        from lookup import platform
        with patch.object(platform.Path,'is_file',return_value=True),patch.object(os,'access',return_value=True):
            self.assertEqual(platform.resolve_command('kdotool'),str(platform.PRIVATE_KDOTOOL))
            for action in ('search','getmouselocation','windowactivate'):
                with patch.object(platform.subprocess,'Popen',side_effect=FileNotFoundError) as child:
                    with self.assertRaises(PlatformError):run(['kdotool',action])
                    self.assertEqual(child.call_args.args[0],[str(platform.PRIVATE_KDOTOOL),action])
        with patch.object(platform.Path,'is_file',return_value=False):
            self.assertEqual(platform.resolve_command('kdotool'),'kdotool')
            self.assertEqual(platform.resolve_command('kscreen-doctor'),'kscreen-doctor')

    def test_child_deadline_and_output_cap(self):
        for code, reason in (("import time; time.sleep(5)", 'timeout'),
                             ("print('x'*10000)", 'too_large')):
            start = time.monotonic()
            with self.assertRaises(PlatformError) as caught:
                run([sys.executable, '-c', code], timeout=.15, limit=50)
            self.assertEqual(caught.exception.reason, reason)
            self.assertLess(time.monotonic()-start, 2)
        self.assertEqual(run([sys.executable, '-c', "print('ok')"]), b'ok\r\n' if os.name == 'nt' else b'ok\n')

    def test_inherited_stdout_cannot_block_cleanup(self):
        import subprocess
        child = "import subprocess,sys,time; subprocess.Popen([sys.executable,'-c','import time; time.sleep(4)']); time.sleep(4)"
        outer = ('from lookup.platform import run,PlatformError; import sys; '
                 f'\ntry: run([sys.executable,"-c",{child!r}],timeout=.05)'
                 '\nexcept PlatformError as e: print(e.reason)')
        started=time.monotonic()
        result=subprocess.run([sys.executable,'-c',outer],capture_output=True,text=True,timeout=3)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.strip(),'timeout')
        self.assertLess(time.monotonic()-started,2)

    def test_cursor_primary_and_ownership(self):
        with patch('lookup.platform.run', return_value=b'x:-12 y:30 screen:0 window:{01234567-89ab-cdef-0123-456789abcdef}\n'):
            self.assertEqual(cursor_position({}), (-12, 30))
        with patch('lookup.platform.run', return_value=b'wrong'):
            with self.assertRaises(PlatformError):
                cursor_position({})
        with patch('lookup.platform.run', side_effect=PlatformError('timeout')):
            self.assertIsNone(read_primary({}))
        with patch('lookup.platform.run', return_value=b'\xff'):
            self.assertIsNone(read_primary({}))
        with patch('lookup.platform.owned_window', return_value=('owned',)), patch('lookup.platform.run') as command:
            with self.assertRaises(PlatformError):
                window_action({}, 1, 'someone-else', 'windowactivate')
            command.assert_not_called()

    def test_compositor_geometry_parser(self):
        from lookup.platform import window_geometry
        with patch('lookup.platform.window_action',return_value=b'Window {owned}\n  Position: -200,40\n  Geometry: 280x100\n'):
            self.assertEqual(window_geometry({},1,'owned'),(-200,40,280,100))
        with patch('lookup.platform.window_action',return_value=b'Window {owned}\n  Position: -200.8,40\n  Geometry: 440x314.4\n'):
            self.assertEqual(window_geometry({},1,'owned'),(-200.8,40,440,314.4))
        with patch('lookup.platform.window_action',return_value=b'wrong'):
            with self.assertRaises(PlatformError):
                window_geometry({},1,'owned')

    def test_available_rect_reserves_real_docks_at_fractional_scales(self):
        from lookup.platform import Monitor,available_rect
        monitor=Monitor('public',0,0,1280,720,1.5)
        self.assertEqual(available_rect(monitor,[(0,673.3,1280,46.7)]),(0,0,1280,673))
        # Floating panel gap and a dock on another output.
        self.assertEqual(available_rect(monitor,[(200,660,800,48),(1280,0,40,720)]),(0,0,1280,660))
        negative=Monitor('negative',-1000,-800,1000,800,1)
        self.assertEqual(available_rect(negative,[(-1000,-800,40,800),(-1000,-800,1000,30)]),(-960,-770,960,770))
        self.assertEqual(available_rect(monitor,[]),(0,0,1280,720))

    def test_raw_metadata_rejections(self):
        valid = dict(type='raw', format=4, width=4, height=3, stride=16, scale=1.25)
        self.assertEqual(capture.raw_layout(valid), (4, 3, 16, 48))
        for change in ({'type': 'png'}, {'format': 999}, {'width': True}, {'stride': 15},
                       {'height': -1}, {'scale': float('nan')}, {'width': 20000}, {'stride': 1 << 30}):
            with self.assertRaises(PlatformError):
                capture.raw_layout(dict(valid, **change))

    def test_raw_bytes_exact_length_channel_order_and_detached_lifetime(self):
        try:
            from PyQt6.QtGui import QImage
        except ImportError:
            self.skipTest('PyQt6 unavailable')
        metadata = dict(type='raw', format=16, width=2, height=1, stride=8, scale=1)
        data = bytearray([255, 0, 0, 255, 0, 255, 0, 255])
        image = capture.raw_image(metadata, data)
        data[:] = b'\x00'*8
        self.assertEqual(image.pixelColor(0, 0).name(), '#ff0000')
        self.assertEqual(image.pixelColor(1, 0).name(), '#00ff00')
        for wrong in (b'\x00'*7, b'\x00'*9):
            with self.assertRaises(PlatformError):
                capture.raw_image(metadata, wrong)

    def test_memory_ocr_matches_path_preparation(self):
        try:
            from PyQt6.QtGui import QImage
        except ImportError:
            self.skipTest('PyQt6 unavailable')
        import tempfile
        from pathlib import Path
        from lookup.ocr import _prepare_image, OcrError
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'source.png'
            image = QImage(100, 40, QImage.Format.Format_RGB32)
            image.fill(0xffffffff)
            self.assertTrue(image.save(str(path)))
            self.assertEqual(_prepare_image(path, (25, 20), 2, 'auto'),
                             _prepare_image(path.read_bytes(), (25, 20), 2, 'auto'))
        with self.assertRaises(OcrError):
            _prepare_image(b'bad', (0, 0), 2, 'auto')


if __name__ == '__main__':
    unittest.main()
