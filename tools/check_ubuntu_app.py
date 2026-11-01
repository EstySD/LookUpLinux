"""Native, physical-input Ubuntu smoke check; run inside the GNOME VM.

Set LOOKUP_DICTS to real dictionaries. This uses a fresh private test profile,
shows a known word, and waits for two physical Meta+Shift+D presses.
"""
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    from lookup import config,gnome,gui,lifecycle,platform
    if not gnome.active():raise SystemExit('Run inside a GNOME Wayland session.')
    profile=Path(tempfile.mkdtemp(prefix='lookup-ubuntu-smoke-'))
    os.environ.update(LOOKUP_CONFIG=str(profile/'config.json'),LOOKUP_DB=str(profile/'history.sqlite3'),
                      LOOKUP_CACHE=str(profile/'cache'))
    config.save({'online':False,'autostart':False})
    env=platform.session_env()
    os.environ.update(env)
    from PyQt6.QtWidgets import QApplication,QLabel
    from PyQt6.QtGui import QFont
    from PyQt6.QtCore import QTimer,Qt
    from PyQt6.QtDBus import QDBusConnection
    application=QApplication(['lookup-ubuntu-smoke'])
    application.setQuitOnLastWindowClosed(False)
    bus=QDBusConnection.sessionBus()
    if not bus.registerService(gui.SERVICE):raise SystemExit('Close the existing LookUp instance first.')
    lifecycle.ensure_entries()
    lifecycle.ensure_shortcut()
    _,Owner=gui.components()
    owner=Owner(env)
    assert bus.registerObject(gui.OBJECT,owner,QDBusConnection.RegisterOption.ExportAllSlots)
    label=QLabel('dictionary')
    label.setWindowTitle('LookUp Ubuntu smoke source')
    label.setFont(QFont('DejaVu Sans',38))
    label.setMargin(40)
    label.resize(700,220)
    label.setStyleSheet('background: white; color: black;')
    label.show()
    report={'profile':str(profile),'results':[],'input':'VirtualBox physical keyboard and pointer; agent acceptance'}
    report_path=profile/'report.json'
    phases=set()
    def write():report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    def prepare():
        gnome.place(os.getpid(),label.windowTitle(),120,180)
        subprocess.run(['wl-copy','--primary','--clear'],check=False,env=env,timeout=3)
        print('READY_OCR point=330,290 report='+str(report_path),flush=True)
    def received(event):
        if len(report['results'])>=2:return
        if event.stage=='error':
            print('ERROR '+str(event.error),flush=True)
        if event.stage!='ready' or event.id in phases:return
        phases.add(event.id)
        def verify():
            value=event.result
            row=dict(mode=event.mode,word=value.key,articles=len(value.articles),saved=value.saved,
                     visible=owner.popup.isVisible(),focus_error=owner.focus_error,
                     updates=owner.popup.updatesEnabled(),elapsed_ms=event.elapsed_ms,
                     popup_geometry=owner.popup.geometry().getRect(),
                     content_height=owner.popup.content_layout.sizeHint().height(),
                     scroll=owner.popup.scroll.verticalScrollBar().value())
            report['results'].append(row);write()
            print('RESULT '+json.dumps(row),flush=True)
            if len(report['results'])==1:
                owner.dismiss()
                subprocess.run(['wl-copy','--primary'],input=b'running',env=env,check=True,timeout=3)
                print('READY_PRIMARY press Meta+Shift+D',flush=True)
            else:
                with sqlite3.connect(profile/'history.sqlite3') as conn:
                    report['history']=[row[0] for row in conn.execute('SELECT word FROM words ORDER BY word')]
                report['ok']=(len(report['results'])==2 and
                    [(r['mode'],r['word']) for r in report['results']]==[('ocr','dictionary'),('primary','running')] and
                    all(r['articles']>0 and r['visible'] and r['saved'] and not r['focus_error'] and r['updates']
                        and r['popup_geometry'][3]>=min(400,r['content_height']) for r in report['results']))
                write();print('FINISHED '+json.dumps(report),flush=True)
                QTimer.singleShot(20000,owner.quit)
        QTimer.singleShot(900,verify)
    owner.bridge.event.connect(received)
    QTimer.singleShot(1000,prepare)
    QTimer.singleShot(180000,owner.quit)
    application.aboutToQuit.connect(owner.quit)
    application.exec()
    return 0 if report.get('ok') else 1


if __name__=='__main__':raise SystemExit(main())
