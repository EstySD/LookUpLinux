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
        image=QImage(1000,800,QImage.Format.Format_RGB32)
        image.fill(QColor('white'))
        output=QBuffer();output.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(output,'PNG')
        frame=capture.Capture(bytes(output.data()),1000,800,'public',0)
        monitor=Monitor('public',-400,50,1000/scale,800/scale,scale)
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
                QTest.mouseClick(window,Qt.MouseButton.LeftButton,pos=QPoint(60,180))
                self.assertEqual(points,[(-340,230)])
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
        QTest.keyClick(window,Qt.Key.Key_F1)
        self.assertTrue(window.close_button.isVisible())
        self.assertLessEqual(window.close_button.geometry().right(),window.toolbar.width())
        QTest.mouseClick(window.instruction,Qt.MouseButton.LeftButton)
        self.assertEqual(selected,[])
        QTest.mouseClick(window.close_button,Qt.MouseButton.LeftButton)
        self.assertEqual(selected,[])
        self.assertEqual(closed,[True])
        self.assertIsNone(window._image)
        window.release()
        self.assertEqual(closed,[True])
        another=self.window()
        QTest.keyClick(another,Qt.Key.Key_Escape)
        self.assertFalse(another.isVisible())
        self.assertIsNone(another._image)

    def test_f1_panel_is_hidden_by_default_and_stays_put_when_shown(self):
        window=self.window()
        selected=[]
        window.selected.connect(selected.append)
        point=window.toolbar.geometry().center()
        for _ in range(2):
            self.assertFalse(window.toolbar.isVisible())
            self.assertEqual(window.popup_area(),window.geometry())
            QTest.mouseClick(window,Qt.MouseButton.LeftButton,pos=point)
            self.assertEqual(selected[-1],(-400+point.x(),50+point.y()))
            QTest.keyClick(window,Qt.Key.Key_F1)
            self.assertTrue(window.toolbar.isVisible())
            before=window.toolbar.geometry()
            QTest.mouseMove(window.close_button)
            self.application.processEvents()
            self.assertEqual(window.toolbar.geometry(),before)
            self.assertLess(window.toolbar.width(),window.width())
            area=window.popup_area()
            toolbar=window.toolbar.geometry().translated(-400,50)
            self.assertFalse(area.intersects(toolbar))
            QTest.keyClick(window.close_button,Qt.Key.Key_F1)

    def test_crosshair_moves_with_arrows_and_selects_with_enter(self):
        window=self.window()
        selected=[]
        window.selected.connect(selected.append)
        self.assertIsNone(window._crosshair)
        QTest.keyClick(window,Qt.Key.Key_Right)
        QTest.keyClick(window,Qt.Key.Key_Down)
        self.assertIsNotNone(window._crosshair)
        self.assertGreater(window._crosshair[0],window.width()/2)
        self.assertGreater(window._crosshair[1],window.height()/2)
        x,y=window._crosshair
        expected=(window.monitor.x+x*window.monitor.width/window.width(),
                  window.monitor.y+y*window.monitor.height/window.height())
        QTest.keyClick(window,Qt.Key.Key_Return)
        self.assertEqual(selected,[expected])
        window.release()
        self.assertIsNone(window._crosshair)

    def test_readable_controls_at_deck_resolution(self):
        window=self.window()
        window.resize(1280,800)
        QTest.keyClick(window,Qt.Key.Key_F1)
        self.application.processEvents()
        self.assertTrue(window.close_button.isVisibleTo(window))
        self.assertGreaterEqual(window.close_button.height(),24)
        self.assertLess(window.toolbar.width(),1280)
        self.assertIn('DPad',window.instruction.text())

    def test_bad_image_rejected_before_showing_surface(self):
        from lookup.selection_gui import components
        from dataclasses import replace
        scene=self.scene()
        for frame in (replace(scene.source.image,png=b'not a PNG'),
                      replace(scene.source.image,width=1)):
            with self.subTest(frame=frame):
                with self.assertRaises(ValueError):
                    components()(replace(scene,source=replace(scene.source,image=frame)))
