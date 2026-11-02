"""Validate the native snapshot boundary without a compositor or live pixels."""
import contextlib
import unittest
from unittest import mock

from lookup import capture

try:
    from PyQt6 import QtDBus
except ImportError:
    QtDBus=None


class Descriptor:
    def isValid(self):return True
    def fileDescriptor(self):return 123


@unittest.skipIf(QtDBus is None,'PyQt6 unavailable')
class HotkeyCaptureTests(unittest.TestCase):
    def metadata(self):
        return dict(type='raw',format=16,width=2,height=2,stride=8,scale=1,
                    name='public',x=0,y=0,logical_width=2,logical_height=2,
                    cursor_x=1.25,cursor_y=1.25,available_x=0.,available_y=0.,
                    available_width=2.,available_height=2.,capture_ms=2.5,
                    input_ns=1_000_000_000,capture_ns=1_100_000_000,fd=Descriptor())

    @contextlib.contextmanager
    def boundary(self,metadata,*,pixels=b'x'*16,size=16):
        reply=mock.Mock()
        reply.type.return_value=QtDBus.QDBusMessage.MessageType.ReplyMessage
        reply.arguments.return_value=[metadata]
        bus=mock.Mock();bus.call.return_value=reply
        with mock.patch.object(capture.os,'name','posix'), \
             mock.patch.object(QtDBus.QDBusConnection,'sessionBus',return_value=bus), \
             mock.patch.object(QtDBus,'QDBusUnixFileDescriptor',Descriptor), \
             mock.patch.object(capture.os,'fstat',return_value=mock.Mock(st_size=size)), \
             mock.patch.object(capture.os,'pread',create=True,return_value=pixels) as read, \
             mock.patch.object(capture.time,'monotonic_ns',return_value=1_200_000_000):
            yield read

    def test_snapshot_retains_key_coordinates_and_has_integer_qt_work_area(self):
        with self.boundary(self.metadata()) as read:
            result=capture.take_hotkey({'KDE_SESSION_VERSION':'6'})
        self.assertEqual(result.point,(1.25,1.25))
        self.assertEqual(result.available,(0,0,2,2))
        self.assertTrue(all(type(v) is int for v in result.available))
        self.assertEqual(result.pixels,b'x'*16)
        self.assertNotIn('fd',result.metadata)
        read.assert_called_once_with(123,16,0)

    def test_expired_or_failed_snapshot_is_an_error_instead_of_a_new_live_capture(self):
        for reason in ('expired','capture_failed'):
            with self.subTest(reason=reason),self.boundary({'error':reason}) as read:
                with self.assertRaises(capture.PlatformError):capture.take_hotkey({'KDE_SESSION_VERSION':'6'})
                read.assert_not_called()

    def test_empty_reply_preserves_explicit_non_hotkey_capture(self):
        with self.boundary({}) as read:
            self.assertIsNone(capture.take_hotkey({'KDE_SESSION_VERSION':'6'}))
        read.assert_not_called()
    def test_consumed_snapshot_is_distinguished_from_a_non_hotkey_request(self):
        with self.boundary({'status':'consumed'}) as read:
            with self.assertRaises(capture.PlatformError) as caught:
                capture.take_hotkey({'KDE_SESSION_VERSION':'6'})
        self.assertEqual(caught.exception.reason,'hotkey_consumed')
        read.assert_not_called()

    def test_invalid_metadata_never_reads_fd(self):
        for field,value in [('width',20000),('stride',1),('scale',0),('cursor_x',float('nan')),
                            ('capture_ns',1),('input_ns',True),('available_width',0),('name','')]:
            data=self.metadata();data[field]=value
            with self.subTest(field=field),self.boundary(data) as read:
                with self.assertRaises(capture.PlatformError):capture.take_hotkey({'KDE_SESSION_VERSION':'6'})
                read.assert_not_called()

    def test_fd_size_and_short_reads_are_rejected(self):
        for size,pixels in [(15,b'x'*16),(16,b'x'*15)]:
            with self.subTest(size=size,pixels=len(pixels)),self.boundary(self.metadata(),size=size,pixels=pixels):
                with self.assertRaises(capture.PlatformError):capture.take_hotkey({'KDE_SESSION_VERSION':'6'})
