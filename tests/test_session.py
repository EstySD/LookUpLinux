"""Session detection and Gaming Mode environment isolation; no desktop required."""
import os
import unittest
from unittest import mock

from lookup import capture,platform,session
from lookup.platform import Monitor,PlatformError
from tests._support import make_tempdir


class ModeTests(unittest.TestCase):
    def test_kde_gnome_gaming_and_unknown(self):
        self.assertEqual(session.mode({'XDG_CURRENT_DESKTOP':'KDE','KDE_SESSION_VERSION':'6'}),session.KDE)
        self.assertEqual(session.mode({'XDG_CURRENT_DESKTOP':'ubuntu:GNOME'}),session.GNOME)
        self.assertEqual(session.mode({'XDG_CURRENT_DESKTOP':'gamescope'}),session.GAMING)
        self.assertEqual(session.mode({'GAMESCOPE_WAYLAND_DISPLAY':'gamescope-0'}),session.GAMING)
        self.assertEqual(session.mode({}),session.UNKNOWN)

    def test_gaming_wins_and_steam_deck_alone_is_not_gaming(self):
        self.assertTrue(session.is_gaming({'XDG_CURRENT_DESKTOP':'KDE','GAMESCOPE_WAYLAND_DISPLAY':'gamescope-0'}))
        self.assertFalse(session.is_gaming({'SteamDeck':'1'}))
        self.assertEqual(session.mode({'SteamDeck':'1'}),session.UNKNOWN)

    def test_steamos_release_and_environment(self):
        info={'ID':'steamos','VERSION_ID':'3.9.7','PRETTY_NAME':'SteamOS 3.9.7'}
        self.assertTrue(session.is_steamos({},info))
        self.assertEqual(session.steamos_version(info),'3.9.7')
        self.assertTrue(session.is_steamos({'SteamDeck':'1'},{}))
        self.assertFalse(session.is_steamos({},{'ID':'arch'}))


class EnvironmentTests(unittest.TestCase):
    def test_parse_environ_is_bounded_and_keeps_equals(self):
        self.assertEqual(session.parse_environ(b'A=1\0B=x=y\0bad\0=no\0C='),
                         {'A':'1','B':'x=y','C':''})

    def test_find_gamescope_and_read_environment(self):
        root=make_tempdir(self)
        proc=root/'proc'
        for pid,comm in ((123,'gamescope\n'),(456,'bash\n'),(789,'gamescope-wl\n')):
            folder=proc/str(pid);folder.mkdir(parents=True)
            (folder/'comm').write_text(comm,encoding='ascii')
        (proc/'123'/'environ').write_bytes(b'DISPLAY=:0\0XAUTHORITY=/run/user/1000/xauth\0')
        self.assertEqual(session.find_gamescope_pids(proc,uid=None),(123,789))
        env=session.gamescope_env(proc,pids=(123,))
        self.assertEqual(env['DISPLAY'],':0')
        self.assertEqual(env['XAUTHORITY'],'/run/user/1000/xauth')

    def test_gaming_env_drops_kde_and_prefers_x11_for_gamescope(self):
        base={'KDE_SESSION_VERSION':'6','QT_QPA_PLATFORMTHEME':'kde',
              'DISPLAY':':0','PATH':'/bin'}
        gamescope={'DISPLAY':':1','XAUTHORITY':'/run/user/1000/xauth',
                   'WAYLAND_DISPLAY':'gamescope-0',
                   'DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/1000/bus'}
        env=session.build_gaming_env(base,gamescope,uid=1000)
        self.assertEqual(env['DISPLAY'],':1')
        self.assertEqual(env['XAUTHORITY'],'/run/user/1000/xauth')
        self.assertEqual(env['QT_QPA_PLATFORM'],'xcb')
        self.assertEqual(env['XDG_CURRENT_DESKTOP'],'gamescope')
        self.assertNotIn('KDE_SESSION_VERSION',env)
        self.assertNotIn('QT_QPA_PLATFORMTHEME',env)
        self.assertEqual(env['XDG_RUNTIME_DIR'],'/run/user/1000')

    def test_wayland_only_and_no_display(self):
        env=session.build_gaming_env({}, {'WAYLAND_DISPLAY':'gamescope-0'},uid=1000)
        self.assertEqual(env['QT_QPA_PLATFORM'],'wayland')
        env=session.build_gaming_env({}, {},uid=1000)
        self.assertNotIn('QT_QPA_PLATFORM',env)

    def test_report_contains_only_session_metadata(self):
        with mock.patch.object(session,'os_release',return_value={'ID':'steamos','VERSION_ID':'3.9.7'}), \
             mock.patch.object(session,'find_gamescope_pids',return_value=(123,)), \
             mock.patch.object(session,'input_devices',return_value=('event0','event1')):
            value=session.report({'XDG_CURRENT_DESKTOP':'gamescope','DISPLAY':':0'})
        self.assertEqual(value['mode'],session.GAMING)
        self.assertTrue(value['steamos'])
        self.assertEqual(value['steamos_version'],'3.9.7')
        self.assertEqual(value['gamescope_pids'],[123])
        self.assertEqual(value['input_devices'],['event0','event1'])
        self.assertEqual(value['display'],{'DISPLAY':True,'WAYLAND_DISPLAY':False,'XAUTHORITY':False})
        self.assertNotIn('query',value)
        self.assertNotIn('history',value)


class GamingGuardTests(unittest.TestCase):
    def setUp(self):
        self.monitor=Monitor('public',0,0,1280,800,1)
        patcher=mock.patch.object(session,'is_gaming',return_value=True)
        patcher.start();self.addCleanup(patcher.stop)

    def test_platform_never_calls_kde_services(self):
        for call in (lambda:platform.monitors({}),
                     lambda:platform.work_area({},self.monitor),
                     lambda:platform.cursor_position({}),
                     lambda:platform.panel_rects({}),
                     lambda:platform.owned_window({},1)):
            with self.assertRaises(PlatformError) as error:
                call()
            self.assertEqual(error.exception.reason,'gaming_session')

    def test_capture_has_no_kde_or_screenshot_path(self):
        self.assertIsNone(capture.take_hotkey({}))
        self.assertFalse(capture.enable_hotkey_bridge({}))
        with self.assertRaises(PlatformError) as error:
            capture.capture_monitor(self.monitor,{})
        self.assertEqual(error.exception.reason,'gaming_capture_unavailable')
