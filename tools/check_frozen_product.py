"""Actual-product KDE probe and strict evidence validation; fixtures are public."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

EXITS=('escape','close','reinvoke','timeout','fault','external_focus','process_exit')
CLEANUP=('owned_processes_stopped','profiles_restored','bindings_restored','original_untouched')


def _input(value,pid):
    rows=[value[key] for key in ('before','during','after')]
    return (all(row['pid']==pid and type(row['count']) is int and row['count']>=0 for row in rows)
            and rows[0]['count']==rows[1]['count']<rows[2]['count']
            and type(value['layer_events']) is int and value['layer_events']>=2 and value['closed'] is True)


def accepted(value):
    """Only complete, internally consistent product observations pass."""
    try:
        if value['mode']!='native-product' or not value['inventory']:return False
        if not all(isinstance(name,str) and re.fullmatch('[0-9a-f]{64}',digest)
                   for name,digest in value['inventory'].items()):return False
        if not all(value['versions'][key] for key in ('kwin','qt','game')):return False
        fixture=value['fixture'];selections=fixture['selections']
        if not fixture['hover'] or not fixture['source_ticks'][0]<fixture['source_ticks'][1]:return False
        if len(selections)<3 or len({row['word'] for row in selections})<3:return False
        if not all(row['frame']==fixture['frame'] and row['session']==selections[0]['session']
                   and row['word'] and row['translation'] for row in selections):return False
        if not all(type(row['id']) is int for row in selections):return False
        if not all(a['id']<b['id'] for a,b in zip(selections,selections[1:])):return False
        if not _input(fixture['input'],fixture['pid']):return False
        game=value['game']
        if not all(_input(game['exits'][name],game['pid']) for name in EXITS):return False
        if value['primary']['mode']!='primary' or value['primary']['scene'] is not False or not value['primary']['key']:return False
        return (value['no_hit_usable'] is True and value['internal_focus'] is True
                and {1,1.25,2}.issubset(value['scales'])
                and all(value['cleanup'][name] is True for name in CLEANUP))
    except (KeyError,TypeError,ValueError,IndexError):return False


def inventory(directory):
    root=Path(directory)
    return {str(path.relative_to(root)).replace('\\','/'):hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((root/'lookup').rglob('*')) if path.is_file() and path.suffix in ('.py','.txt')}


def write(path,value):
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8');temporary.replace(path)


def environment():
    if os.getuid()!=1001 or Path.home()!=Path('/home/lookup07'):raise RuntimeError('owned_user_required')
    from lookup import platform
    os.environ.update(platform.session_env())
    for key in ('SUDO_UID','SUDO_GID','SUDO_USER','SUDO_COMMAND'):os.environ.pop(key,None)


def product(root):
    """Observe the real GUI/Engine; only test-only fault injection changes behavior."""
    environment()
    from PyQt6.QtCore import QTimer,QT_VERSION_STR
    from lookup import gui,app as core
    root.mkdir(parents=True,exist_ok=True)
    state={'pid':os.getpid(),'events':[],'inventory':inventory(Path(core.__file__).resolve().parents[1]),'qt':QT_VERSION_STR}
    Popup,Owner=gui.components();receive=Owner.receive;initialize=Owner.__init__;resolve=core.Source.resolve
    owners=[];fault=[False]
    def observed(self,event):
        row=dict(id=event.id,stage=event.stage,mode=event.mode,error=event.error)
        if event.scene is not None:
            image=event.scene.source.image
            row.update(session=event.scene.session_id,frame=hashlib.sha256(image.png).hexdigest())
            (root/'capture.png').write_bytes(image.png)
            state['frame']=row['frame'];state['session']=row['session']
        if event.result is not None:
            row.update(word=event.result.key,translation=event.result.translation)
        state['events'].append(row)
        receive(self,event)
    def resolving(self,*args,**kwargs):
        if fault[0]:fault[0]=False;raise core.AppError('ocr_failed')
        return resolve(self,*args,**kwargs)
    def init(self,*args,**kwargs):
        initialize(self,*args,**kwargs);owners.append(self)
        timer=QTimer(self)
        def poll():
            command=root/'command.json'
            if command.exists():
                value=json.loads(command.read_text());command.unlink();action=value['action']
                if action=='fault':fault[0]=True
                elif action=='close' and self.scene_window is not None:self.scene_window.close_button.click()
                elif action=='quit':self.quit()
                elif action=='settings':self.open_settings()
                elif action=='card':self.popup.card_button.click()
                elif action=='timeout':self.popup.timer.setInterval(600);self.popup.timer.start()
            layer=self.scene_window
            state.update(layer=bool(layer is not None and layer.isVisible()),popup=self.popup.isVisible(),
                title=self.popup.title.text(),scene_id=self._scene_id,
                card_status=self.popup.card_status.text(),timer=self.popup.timer.isActive())
            if layer is not None:
                state['layer_geometry']=[layer.x(),layer.y(),layer.width(),layer.height()]
                state['close']=[layer.close_button.mapToGlobal(layer.close_button.rect().center()).x(),
                                layer.close_button.mapToGlobal(layer.close_button.rect().center()).y()]
            write(root/'state.json',state)
        timer.timeout.connect(poll);timer.start(100);self._probe_timer=timer
        QTimer.singleShot(600000,self.quit)
    Owner.receive=observed;Owner.__init__=init;core.Source.resolve=resolving
    try:return gui.run()
    finally:
        state['stopped']=True;write(root/'state.json',state)


def source(root,game=False):
    environment()
    from PyQt6.QtCore import Qt,QTimer
    from PyQt6.QtGui import QPainter,QFont
    from PyQt6.QtWidgets import QApplication,QWidget,QToolTip
    root.mkdir(parents=True,exist_ok=True)
    state={'pid':os.getpid(),'motion':0,'click':0,'ticks':0};child=None
    application=QApplication([]);application.setQuitOnLastWindowClosed(False)
    class Fixture(QWidget):
        def __init__(self):
            super().__init__();self.setMouseTracking(True);self.setWindowTitle('Phase11 product source');self.setFont(QFont('Sans Serif',24))
        def paintEvent(self,event):
            painter=QPainter(self);painter.fillRect(self.rect(),Qt.GlobalColor.white);painter.setPen(Qt.GlobalColor.black);painter.setFont(self.font())
            painter.drawText(150,200,'The bright river flows.');painter.drawText(150,300,'Frame '+str(state['ticks']))
        def mouseMoveEvent(self,event):
            state['motion']+=1;QToolTip.showText(event.globalPosition().toPoint(),'Captured hover vocabulary',self)
        def mousePressEvent(self,event):state['click']+=1
    fixture=Fixture()
    if game:
        # Reuse the research observer's exact source, not its substitute Layer.
        tree=ast.parse(Path(__file__).with_name('check_frozen_selection.py').read_text())
        code=next(node.args[0].value for node in ast.walk(tree) if isinstance(node,ast.Call)
            and isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name)
            and node.func.value.id=='observer' and node.func.attr=='write_text')
        (root/'observer.c').write_text(code)
        flags=subprocess.check_output(['pkg-config','--cflags','--libs','sdl2'],text=True).split()
        subprocess.run(['cc','-shared','-fPIC',str(root/'observer.c'),'-o',str(root/'observer.so'),'-ldl',*flags],check=True)
        child=subprocess.Popen(['wesnoth','--fullscreen','--language','en_US','--userdata-dir',str(root/'userdata'),
            '--usercache-dir',str(root/'cache'),'--userconfig-dir',str(root/'config'),'--nomusic','--nosound','--noaddons'],
            env=dict(os.environ,SDL_VIDEODRIVER='wayland',LD_PRELOAD=str(root/'observer.so'),PROBE_SDL_LOG=str(root/'events.log')),
            stdout=open(root/'game.log','w'),stderr=subprocess.STDOUT)
        state['pid']=child.pid
    else:fixture.showFullScreen()
    def poll():
        state['ticks']+=1;fixture.update();log=root/'events.log'
        state['count']=len(log.read_text().splitlines()) if log.exists() else state['motion']+state['click']
        write(root/'state.json',state)
        command=root/'command.json'
        if command.exists():
            action=json.loads(command.read_text())['action'];command.unlink()
            if action=='quit':application.quit()
            elif action=='focus':fixture.raise_();fixture.activateWindow()
    timer=QTimer();timer.timeout.connect(poll);timer.start(100);QTimer.singleShot(900000,application.quit)
    try:return application.exec()
    finally:
        if child is not None:
            child.terminate()
            try:child.wait(timeout=8)
            except subprocess.TimeoutExpired:child.kill();child.wait()
        state['stopped']=True;write(root/'state.json',state)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--validate',type=Path);parser.add_argument('--product',type=Path)
    parser.add_argument('--source',type=Path);parser.add_argument('--game',action='store_true');args=parser.parse_args()
    if args.validate:
        result=accepted(json.loads(args.validate.read_text(encoding='utf-8-sig')));print(json.dumps({'accepted':result}));return 0 if result else 1
    if args.product:return product(args.product)
    if args.source:return source(args.source,args.game)
    parser.error('choose --validate, --product or --source')


if __name__=='__main__':raise SystemExit(main())
