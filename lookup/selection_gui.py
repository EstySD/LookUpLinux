"""Lazy native, input-taking view of one transient captured monitor."""
import math

from . import capture

_components=None
TITLE='Выбор слова по снимку'
INSTRUCTION='Нажмите или коснитесь слова · Стрелки/DPad — прицел · Enter — выбор · F1 — панель · Esc — закрыть'
EXPLANATION='Снимок экрана сохранён для выбора. Приложение под ним продолжает работать.'
NO_WORD='Слово не найдено. Нажмите на другое слово на снимке или закройте снимок клавишей Esc.'


def components():
    global _components
    if _components is not None:return _components
    from PyQt6.QtCore import Qt,QEvent,QRectF,QRect,QPoint,QBuffer,QIODevice,pyqtSignal
    from PyQt6.QtGui import QImageReader,QPainter,QColor,QPen,QShortcut,QKeySequence
    from PyQt6.QtWidgets import QWidget,QFrame,QHBoxLayout,QVBoxLayout,QLabel,QPushButton,QApplication,QSizePolicy

    class SelectionLayer(QWidget):
        selected=pyqtSignal(object)
        dismissed=pyqtSignal()

        def __init__(self,scene):
            super().__init__()
            frame=scene.source.image
            if (scene.source.mode!='ocr' or not isinstance(frame,capture.Capture) or
                not isinstance(frame.png,bytes) or not 0<len(frame.png)<=capture.MAX_PNG or
                not all(isinstance(n,int) and not isinstance(n,bool) and 0<n<=16384 for n in (frame.width,frame.height)) or
                frame.width*frame.height>64_000_000):
                raise ValueError('invalid captured frame')
            buffer=QBuffer();buffer.setData(frame.png);buffer.open(QIODevice.OpenModeFlag.ReadOnly)
            reader=QImageReader(buffer,b'png')
            if (reader.size().width(),reader.size().height())!=(frame.width,frame.height):
                raise ValueError('invalid captured dimensions')
            image=reader.read()
            if image.isNull():raise ValueError('invalid captured image')
            self._image=image
            self._box=None
            self._released=False
            self._crosshair=None
            self._step=48
            self.session_id=scene.session_id
            self.monitor=scene.source.monitor
            self.setWindowTitle(TITLE);self.setAccessibleName(TITLE)
            self.setAccessibleDescription(EXPLANATION+' '+INSTRUCTION)
            self.setWindowFlags(Qt.WindowType.Window|Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint)
            self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.setCursor(Qt.CursorShape.CrossCursor)
            self.setMouseTracking(True)
            self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents,True)
            self.setGeometry(round(self.monitor.x),round(self.monitor.y),round(self.monitor.width),round(self.monitor.height))
            self.toolbar=QFrame(self)
            self.toolbar.setAutoFillBackground(True)
            self.toolbar.setCursor(Qt.CursorShape.ArrowCursor)
            row=QHBoxLayout(self.toolbar);row.setContentsMargins(6,4,6,4);row.setSpacing(6)
            labels=QVBoxLayout();labels.setSpacing(2)
            self.instruction=QLabel(INSTRUCTION)
            self.instruction.setTextFormat(Qt.TextFormat.PlainText)
            self.instruction.setWordWrap(True)
            labels.addWidget(self.instruction)
            self.status=QLabel('Ищем перевод…')
            self.status.setTextFormat(Qt.TextFormat.PlainText)
            self.status.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Preferred)
            labels.addWidget(self.status);row.addLayout(labels,1)
            self.close_button=QPushButton('Закрыть')
            self.close_button.setMinimumHeight(32)
            self.close_button.setAccessibleName('Закрыть снимок')
            self.close_button.setToolTip('Закрыть снимок (Esc)')
            self.close_button.clicked.connect(self.dismiss)
            row.addWidget(self.close_button,0,Qt.AlignmentFlag.AlignTop)
            self.shortcut=QShortcut(QKeySequence(Qt.Key.Key_Escape),self,activated=self.dismiss)
            self.panel_shortcut=QShortcut(QKeySequence(Qt.Key.Key_F1),self,activated=self.toggle_toolbar)
            self._layout_controls()
            self.toolbar.hide()

        def toggle_toolbar(self):
            if self._released:return
            self.toolbar.setVisible(not self.toolbar.isVisible())
            if self.toolbar.isVisible():self.close_button.setFocus()
            else:self.setFocus()

        def _layout_controls(self):
            width=min(560,max(1,self.width()-32))
            self.toolbar.setGeometry(max(0,(self.width()-width)//2),16,width,max(1,self.toolbar.heightForWidth(width)))
            height=self.toolbar.sizeHint().height()
            self.toolbar.setFixedHeight(min(max(1,height),max(1,self.height()-32)))
            self._elide_status()

        def _elide_status(self):
            text=self.status.accessibleName() or self.status.text()
            self.status.setText(self.status.fontMetrics().elidedText(text,Qt.TextElideMode.ElideRight,max(1,self.toolbar.width()-self.close_button.sizeHint().width()-40)))

        def set_status(self,text):
            self.status.setAccessibleName(text);self.status.setToolTip(text)
            self._elide_status()

        def set_selection(self,word,box=None):
            self._box=None
            if (box is not None and len(box)==4 and
                all(isinstance(n,(int,float)) and math.isfinite(n) for n in box)):
                self._box=tuple(box)
            self.set_status('Выбрано слово: '+word if word else NO_WORD)
            self.update()

        def selection_rect(self):
            if self._box is None or self._image is None:return QRectF()
            x,y,width,height=self._box
            return QRectF(x*self.width()/self._image.width(),y*self.height()/self._image.height(),
                          width*self.width()/self._image.width(),height*self.height()/self._image.height())

        def popup_area(self):
            if not self.toolbar.isVisible():
                return QRect(round(self.monitor.x),round(self.monitor.y),self.width(),self.height())
            top=self.toolbar.geometry().bottom()+8
            return QRect(round(self.monitor.x),round(self.monitor.y)+top,self.width(),max(1,self.height()-top))

        def present(self,focus=True):
            if focus:
                self.winId()
                screen=QApplication.screenAt(QPoint(round(self.monitor.x+self.monitor.width/2),round(self.monitor.y+self.monitor.height/2)))
                if screen is not None:self.windowHandle().setScreen(screen)
                self.showFullScreen();self.raise_();self.activateWindow()
                self.windowHandle().requestActivate()
                self.setFocus()
            else:self.show()

        def paintEvent(self,event):
            painter=QPainter(self)
            painter.fillRect(self.rect(),self.palette().window())
            if self._image is not None:
                painter.drawImage(self.rect(),self._image)
                tint=QColor(self.palette().window().color());tint.setAlphaF(0.2)
                painter.fillRect(self.rect(),tint)
                if self._box is not None:
                    painter.setPen(QPen(self.palette().highlight().color(),2))
                    painter.drawRect(self.selection_rect())
                if self._crosshair is not None:
                    x,y=self._crosshair
                    painter.setPen(QPen(QColor('white'),3))
                    painter.drawEllipse(QRectF(x-14,y-14,28,28))
                    painter.setPen(QPen(QColor('black'),1))
                    painter.drawLine(QPoint(round(x-22),round(y)),QPoint(round(x+22),round(y)))
                    painter.drawLine(QPoint(round(x),round(y-22)),QPoint(round(x),round(y+22)))

        def mousePressEvent(self,event):
            if (event.button()==Qt.MouseButton.LeftButton and not self._released and
                not (self.toolbar.isVisible() and self.toolbar.geometry().contains(event.position().toPoint()))):
                self.selected.emit((self.monitor.x+event.position().x()*self.monitor.width/self.width(),
                                    self.monitor.y+event.position().y()*self.monitor.height/self.height()))
            event.accept()

        def mouseMoveEvent(self,event):event.accept()
        def mouseReleaseEvent(self,event):event.accept()
        def mouseDoubleClickEvent(self,event):event.accept()
        def wheelEvent(self,event):event.accept()
        def _emit_point(self,x,y):
            self.selected.emit((self.monitor.x+x*self.monitor.width/self.width(),
                                self.monitor.y+y*self.monitor.height/self.height()))

        def event(self,event):
            if (not self._released and event.type()==QEvent.Type.TouchBegin and event.points()):
                point=event.points()[0].position()
                if not (self.toolbar.isVisible() and self.toolbar.geometry().contains(point.toPoint())):
                    self._emit_point(point.x(),point.y())
                    return True
            return super().event(event)

        def keyPressEvent(self,event):
            key=event.key()
            if key==Qt.Key.Key_Escape:
                self.dismiss();event.accept();return
            moves={Qt.Key.Key_Left:(-1,0),Qt.Key.Key_Right:(1,0),
                   Qt.Key.Key_Up:(0,-1),Qt.Key.Key_Down:(0,1)}
            if key in moves and not self._released:
                if self._crosshair is None:
                    self._crosshair=[self.width()/2,self.height()/2]
                dx,dy=moves[key]
                self._crosshair[0]=max(0,min(self.width()-1,self._crosshair[0]+dx*self._step))
                self._crosshair[1]=max(0,min(self.height()-1,self._crosshair[1]+dy*self._step))
                self.set_status('Прицел: стрелки/DPad перемещают, Enter выбирает')
                self.update();event.accept();return
            if key in (Qt.Key.Key_Return,Qt.Key.Key_Enter) and self._crosshair is not None and not self._released:
                self._emit_point(*self._crosshair);event.accept();return
            event.accept()
        def resizeEvent(self,event):
            super().resizeEvent(event)
            if hasattr(self,'toolbar'):self._layout_controls()
        def release(self):
            self._released=True
            self.hide();self._image=None;self._box=None;self._crosshair=None
        def dismiss(self):
            if self._released:return
            self.release();self.dismissed.emit()
        def closeEvent(self,event):
            self.dismiss();event.accept()

    _components=SelectionLayer
    return SelectionLayer
