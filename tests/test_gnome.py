import os
import unittest
from unittest.mock import patch

from lookup import gnome,platform,capture,lifecycle,doctor


class GnomeTests(unittest.TestCase):
    def test_backend_selection_keeps_kde_and_other_desktops(self):
        for desktop,expected in (('ubuntu:GNOME',True),('GNOME',True),('KDE',False),
                                 ('KDE:GNOME',False),('',False),('XFCE',False)):
            self.assertEqual(gnome.active({'XDG_CURRENT_DESKTOP':desktop}),expected)
        with patch.dict(os.environ,{'XDG_CURRENT_DESKTOP':'KDE'}):
            self.assertIsInstance(lifecycle.shortcut_registry(),lifecycle.ShortcutRegistry)
        with patch.dict(os.environ,{'XDG_CURRENT_DESKTOP':'ubuntu:GNOME'}):
            self.assertIsInstance(lifecycle.shortcut_registry(),gnome.ShortcutRegistry)

    def test_gnome_geometry_never_calls_kde_tools(self):
        state={'point':[200,150],'monitors':[dict(name='0',x=0,y=0,width=800,height=600,
                                                scale=1.25,available=[50,30,750,570])]}
        env={'XDG_CURRENT_DESKTOP':'ubuntu:GNOME'}
        with patch.object(gnome,'state',return_value=state),patch.object(platform,'run',side_effect=AssertionError('KDE tool')):
            monitor=platform.monitors(env)[0]
            self.assertEqual(platform.cursor_position(env),(200,150))
            self.assertEqual(platform.work_area(env,monitor),(50,30,750,570))
            self.assertEqual(platform.image_point((200,150),monitor,(1000,750)),(250,187.5))

    def test_capture_dispatch_preserves_explicit_kde_backend(self):
        monitor=platform.Monitor('0',0,0,800,600,1)
        with patch.object(gnome,'capture',return_value=(b'png',800,600)) as bridge, \
             patch.object(capture,'_screenshot2',return_value=(b'kde',800,600)) as kde:
            frame=capture.capture_monitor(monitor,{'XDG_CURRENT_DESKTOP':'GNOME'})
            self.assertEqual((frame.png,frame.backend),(b'png','gnome'))
            kde.assert_not_called()
            frame=capture.capture_monitor(monitor,{'XDG_CURRENT_DESKTOP':'KDE'})
            self.assertEqual((frame.png,frame.backend),(b'kde','screenshot2'))
            bridge.assert_called_once_with(monitor)

    def test_malformed_bridge_output_is_rejected(self):
        for value in ('[]','null','{}','{"version":2}','{"version":1}',123,'x'*65537):
            with self.subTest(value=str(value)[:20]),patch.object(gnome,'call',return_value=value):
                with self.assertRaises(platform.PlatformError):gnome.state()
        with patch.object(gnome,'call',return_value='not-base64!'):
            with self.assertRaises(platform.PlatformError):gnome.capture(platform.Monitor('0',0,0,800,600,1))

    def test_shortcut_conversion(self):
        self.assertEqual(gnome.accelerator('Meta+Shift+D'),'<Super><Shift>d')
        self.assertEqual(gnome.accelerator('Ctrl+Alt+Space'),'<Control><Alt>space')
        self.assertEqual(gnome.accelerator('Meta+F2'),'<Super>F2')
        with self.assertRaises(ValueError):gnome.accelerator('Unknown+D')

    def test_missing_extension_has_actionable_diagnostic(self):
        with patch.dict(os.environ,{'XDG_CURRENT_DESKTOP':'GNOME'}), \
             patch.object(gnome,'state',side_effect=platform.PlatformError('gnome_extension_unavailable')):
            rows=doctor._session_checks()
            self.assertFalse(rows[0].ok)
            self.assertIn('install_ubuntu.py',rows[0].message)

    def test_missing_extension_is_not_reported_as_missing_kde_tool(self):
        from lookup.app import Source,AppError
        with patch.object(platform,'cursor_position',side_effect=platform.PlatformError('gnome_extension_unavailable')):
            with self.assertRaises(AppError) as error:Source({'XDG_CURRENT_DESKTOP':'GNOME'}).freeze()
            self.assertEqual(error.exception.reason,'missing_gnome_extension')

    def test_gnome_autostart_and_refresh(self):
        with patch.dict(os.environ,{'XDG_CURRENT_DESKTOP':'GNOME'}),patch.object(platform,'run') as run:
            self.assertIn('OnlyShowIn=GNOME;Unity;',lifecycle.desktop_text(autostart=True))
            lifecycle._refresh()
            run.assert_not_called()

    def test_shortcut_conflict_and_rollback(self):
        try:
            from PyQt6.QtGui import QKeySequence
        except ImportError:self.skipTest('PyQt6 unavailable')
        registry=gnome.ShortcutRegistry()
        before={'version':1,'shortcut':'Meta+Shift+D'}
        with patch.object(gnome,'state',return_value=before),patch.object(gnome,'call',return_value=False):
            with self.assertRaises(lifecycle.LifecycleError) as error:registry.change('Meta+Shift+E')
            self.assertEqual(error.exception.reason,'shortcut_conflict')
        with patch.object(gnome,'state',return_value=before),patch.object(gnome,'call',return_value=True) as call:
            transaction=registry.change('Meta+Shift+E')
            transaction.rollback()
            self.assertEqual(call.call_args.args,('SetShortcut','Meta+Shift+D','<Super><Shift>d'))
