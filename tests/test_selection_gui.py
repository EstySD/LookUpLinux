"""Native retained-scene painting, coordinates and local input handling."""
import os
import unittest

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
try:
    from PyQt6.QtCore import Qt, QPoint, QBuffer, QIODevice
    from PyQt6.QtGui import QImage, QColor
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtTest import QTest
except ImportError:
    QApplication=None

from lookup import app, capture
from lookup.platform import Monitor


@unittest.skipIf(QApplication is None,'PyQt6 unavailable')
class SelectionGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application=QApplication.instance() or QApplication([])

    def scene(self,scale=1):
        image=QImage(400,200,QImage.Format.Format_RGB32)
        image.fill(QColor('white'))
        output=QBuffer();output.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(output,'PNG')
        frame=capture.Capture(bytes(output.data()),400,200,'public',0)
        monitor=Monitor('public',-400,50,400/scale,200/scale,scale)
        return app.Scene(5,app.Frozen('ocr',(-350,100),monitor,image=frame))

    def window(self,scale=1):
        from lookup.selection_gui import components
        value=components()(self.scene(scale))
        self.addCleanup(value.deleteLater)
        self.addCleanup(value.release)
        value.show();self.application.processEvents()
        return value

    def test_same_frame_mapping_scales_and_opaque_paint(self):
        for scale in (1,1.25,2):
            with self.subTest(scale=scale):
                window=self.window(scale)
                points=[];window.selected.connect(points.append)
                QTest.mouseClick(window,Qt.MouseButton.LeftButton,pos=QPoint(60,80))
                self.assertEqual(points,[(-340,130)])
                window.set_selection('word',(100,120,40,30))
                rect=window.selection_rect()
                self.assertAlmostEqual(rect.x(),100/scale)
                self.assertAlmostEqual(rect.y(),120/scale)
                self.assertAlmostEqual(rect.width(),40/scale)
                painted=window.grab().toImage()
                self.assertEqual(painted.pixelColor(2,2).alpha(),255)
                self.assertIsNotNone(window._image)
                window.release()
                self.assertIsNone(window._image)
                self.assertFalse(window.isVisible())

    def test_controls_keyboard_status_and_release_are_local(self):
        window=self.window()
        selected=[];closed=[]
        window.selected.connect(selected.append);window.dismissed.connect(lambda:closed.append(True))
        window.set_status('word '*1000)
        self.assertEqual(window.status.accessibleName(),'word '*1000)
        self.assertTrue(window.close_button.isVisible())
        self.assertLessEqual(window.close_button.geometry().right(),window.toolbar.width())
        QTest.mouseClick(window.close_button,Qt.MouseButton.LeftButton)
        self.assertEqual(selected,[])
        self.assertEqual(closed,[True])
        self.assertIsNone(window._image)
        window.release()
        self.assertEqual(closed,[True])
        another=self.window()
        another.close_button.setFocus()
        QTest.keyClick(another.close_button,Qt.Key.Key_Escape)
        self.assertFalse(another.isVisible())
        self.assertIsNone(another._image)

    def test_bad_image_rejected_before_showing_surface(self):
        from lookup.selection_gui import components
        from dataclasses import replace
        scene=self.scene()
        for frame in (replace(scene.source.image,png=b'not a PNG'),
                      replace(scene.source.image,width=1)):
            with self.subTest(frame=frame):
                with self.assertRaises(ValueError):
                    components()(replace(scene,source=replace(scene.source,image=frame)))
