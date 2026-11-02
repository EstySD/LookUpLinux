"""Disposable KDE Wayland research probe; no product/profile changes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import csv
import io
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPainter, QPixmap, QFont
from PyQt6.QtWidgets import QApplication, QWidget, QToolTip

root=Path(sys.argv[1]);root.mkdir(exist_ok=True,parents=True)
observer=root/'observer.c'
observer.write_text(r'''
#define _GNU_SOURCE
#include <SDL.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
int SDL_PollEvent(SDL_Event *event) {
 int (*original)(SDL_Event*)=dlsym(RTLD_NEXT,"SDL_PollEvent");
 int result=original(event);int saved=errno;
 if(result && event && (event->type==SDL_MOUSEMOTION || event->type==SDL_MOUSEBUTTONDOWN || event->type==SDL_KEYDOWN)) {
  FILE *f=fopen(getenv("PROBE_SDL_LOG"),"a");if(f){fprintf(f,"%u %u\n",event->type,event->common.timestamp);fclose(f);}
 }
 errno=saved;return result;
}
''')
flags=subprocess.check_output(['pkg-config','--cflags','--libs','sdl2'],text=True).split()
subprocess.run(['cc','-shared','-fPIC',str(observer),'-o',str(root/'observer.so'),'-ldl',*flags],check=True)
app=QApplication([])
app.setQuitOnLastWindowClosed(False)
state={'source_motion':0,'source_click':0,'ticks':0,'layer_motion':0,'selections':[], 'exits':[]}
class Source(QWidget):
    def __init__(self):
        super().__init__();self.setMouseTracking(True);self.setWindowTitle('Phase11 source fixture');self.setFont(QFont('Sans Serif',24))
    def paintEvent(self,event):
        p=QPainter(self);p.fillRect(self.rect(),Qt.GlobalColor.white);p.setPen(Qt.GlobalColor.black);p.setFont(self.font())
        p.drawText(150,200,'The bright river flows.');p.drawText(150,300,'Frame '+str(state['ticks']))
    def mouseMoveEvent(self,event):
        state['source_motion']+=1
        QToolTip.showText(event.globalPosition().toPoint(),'Captured hover vocabulary',self)
    def mousePressEvent(self,event):state['source_click']+=1
source=Source();source.showFullScreen();layer=None;game=None
class Layer(QWidget):
    def __init__(self,image):
        super().__init__();self.image=image;self.setWindowTitle('Phase11 retained scene');self.setWindowFlags(Qt.WindowType.Window|Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint);self.setMouseTracking(True)
    def paintEvent(self,event):
        p=QPainter(self);p.drawPixmap(self.rect(),self.image);p.fillRect(self.rect(),Qt.GlobalColor.transparent)
    def mouseMoveEvent(self,event):state['layer_motion']+=1
    def mousePressEvent(self,event):
        x,y=event.position().x(),event.position().y()
        state['selections'].append([x,y,state['frame_hash']])
        for row in state.get('ocr_words',[]):
            if row['x']<=x<=row['x']+row['w'] and row['y']<=y<=row['y']+row['h']:
                state.setdefault('selected_words',[]).append(row['word'])
    def keyPressEvent(self,event):
        if event.key()==Qt.Key.Key_Escape:finish('escape')
    def closeEvent(self,event):state['exits'].append('close');event.accept()
def finish(reason):
    global layer
    if layer is not None:layer.close();layer.deleteLater();layer=None
    state['exits'].append(reason)
def command(value):
    global layer,game
    if value=='capture':
        finish('replace')
        path=root/'capture.png'
        result=subprocess.run(['spectacle','-b','-n','-m','-o',str(path)],capture_output=True,timeout=12)
        state['capture_return']=result.returncode
        if result.returncode:state['capture_error']=result.stderr.decode(errors='replace');return
        state['frame_hash']=hashlib.sha256(path.read_bytes()).hexdigest();state['captured_tick']=state['ticks']
        tsv=subprocess.check_output(['tesseract',str(path),'stdout','--psm','11','tsv'],text=True)
        state['ocr_words']=[dict(word=r['text'],x=int(r['left']),y=int(r['top']),w=int(r['width']),h=int(r['height'])) for r in csv.DictReader(io.StringIO(tsv),delimiter='\t') if r['level']=='5' and r['text']]
        layer=Layer(QPixmap(str(path)));layer.showFullScreen();layer.activateWindow()
    elif value=='game':
        finish('game');source.hide()
        game=subprocess.Popen(['wesnoth','--fullscreen','--language','en_US','--userdata-dir',str(root/'userdata'),'--usercache-dir',str(root/'cache'),'--userconfig-dir',str(root/'config'),'--nomusic','--nosound','--noaddons'],env=dict(os.environ,SDL_VIDEODRIVER='wayland',WAYLAND_DEBUG='1',LD_PRELOAD=str(root/'observer.so'),PROBE_SDL_LOG=str(root/'events.log')),stdout=open(root/'game.log','w'),stderr=subprocess.STDOUT)
        state['game_pid']=game.pid
    elif value=='fault':raise RuntimeError('injected_layer_failure')
    elif value in ('close','error','reinvoke'):finish(value)
    elif value=='quit':finish('quit');app.quit()
def poll():
    state['ticks']+=1;source.update()
    path=root/'command.json'
    if path.exists():
        raw=path.read_text();path.unlink()
        try:value=json.loads(raw);command(value['action']);state['command_error']=None
        except Exception as error:finish('exception');state['command_error']=repr(error)
    state['layer_visible']=layer is not None and layer.isVisible();state['source_fullscreen']=source.isFullScreen();state['pid']=os.getpid()
    events=root/'events.log'
    state['game_events']=len(events.read_text().splitlines()) if events.exists() else 0
    (root/'state.json').write_text(json.dumps(state))
timer=QTimer();timer.timeout.connect(poll);timer.start(100)
QTimer.singleShot(240000,app.quit)
app.exec()
finish('shutdown')
if game is not None:
    game.terminate()
    try:game.wait(timeout=10)
    except subprocess.TimeoutExpired:game.kill();game.wait()
