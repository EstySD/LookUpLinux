"""Gaming trigger chord detection, debounce and readiness; no hardware needed."""
import unittest
from unittest import mock

from lookup import config,trigger


class TriggerTests(unittest.TestCase):
    def test_chord_fires_once_and_cooldown_suppresses_repeats(self):
        detector=trigger.ChordDetector((10,11),cooldown=.8)
        self.assertFalse(detector.feed(10,1,now=0.0))
        self.assertTrue(detector.feed(11,1,now=0.1))
        self.assertFalse(detector.feed(11,1,now=0.2))
        detector.feed(10,0,now=0.3);detector.feed(11,0,now=0.3)
        self.assertFalse(detector.feed(10,1,now=0.4))
        detector.feed(10,0,now=0.8)
        self.assertFalse(detector.feed(10,1,now=0.9))
        self.assertTrue(detector.feed(11,1,now=1.0))
        self.assertFalse(detector.feed(10,1,now=1.05))

    def test_out_of_window_press_is_not_a_chord(self):
        detector=trigger.ChordDetector((10,11),window=.2,cooldown=0)
        detector.feed(10,1,now=0.0)
        self.assertFalse(detector.feed(11,1,now=0.5))

    def test_key_fallback_is_ready_without_evdev(self):
        with mock.patch.object(trigger,'devices',return_value=()), \
             mock.patch.object(config,'load',return_value=config.Config(gaming_trigger='key')):
            self.assertTrue(trigger.gaming_trigger_ready())
        with mock.patch.object(trigger,'devices',return_value=()), \
             mock.patch.object(config,'load',return_value=config.Config(gaming_trigger='back_chord')):
            self.assertFalse(trigger.gaming_trigger_ready())

    def test_missing_evdev_watch_is_a_noop(self):
        with mock.patch.object(trigger,'evdev',return_value=None):
            stop=trigger.watch(lambda:self.fail('callback must not fire'))
            stop()


if __name__=='__main__':
    unittest.main()
