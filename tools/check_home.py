"""Agent native home acceptance using actual Owner and existing windows."""
import json
import os
from pathlib import Path
import sys
import time
import subprocess

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from lookup import gui,platform


def main():
    output=Path(sys.argv[1]);output.mkdir(parents=True,exist_ok=True)
    os.environ.update(platform.session_env())
    application=QApplication.instance() or QApplication([])
    application.setQuitOnLastWindowClosed(False)
    service='org.lookup.Linux.Phase13Probe'
    gui.SERVICE=service
    _,Owner=gui.components()
    owner=Owner(dict(os.environ),focus=True,on_quit=lambda:None)
    from PyQt6.QtDBus import QDBusConnection
    bus=QDBusConnection.sessionBus()
    assert bus.registerService(service)
    assert bus.registerObject(gui.OBJECT,owner,QDBusConnection.RegisterOption.ExportAllSlots)
    report={}
    try:
        assert owner.Open()==1
        home=owner.home_window
        QTest.qWait(500)
        assert home.isVisible() and owner.home_instructions.text()
        report['instructions']=owner.home_instructions.text()
        assert home.grab().save(str(output/'home.png'))
        for name,attribute in [('Настройки','settings_window'),('Слова','words_window'),('Повторение','review_window')]:
            owner.home_buttons[name].click();QTest.qWait(100)
            child=getattr(owner,attribute)
            assert child is not None and child.isVisible(),name
            child.close();report[name]=True
        home.close()
        assert not owner.engine.is_alive() or not owner._stopping
        assert owner.Open()==1 and owner.home_window is home and home.isVisible()
        report['reopen']=True
        home.close()
        code="from lookup import gui; from lookup.__main__ import main; gui.SERVICE='org.lookup.Linux.Phase13Probe'; raise SystemExit(main(['--app']))"
        child=subprocess.Popen([sys.executable,'-c',code],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        deadline=time.monotonic()+10
        while child.poll() is None and time.monotonic()<deadline:QTest.qWait(30)
        if child.poll() is None:child.kill()
        stdout,stderr=child.communicate(timeout=5)
        assert child.returncode==0,(stdout,stderr)
        deadline=time.monotonic()+5
        while not home.isActiveWindow() and time.monotonic()<deadline:QTest.qWait(30)
        assert home.isVisible() and home.isActiveWindow()
        report['second_launch_focus']=True
        report['dbus_identity']=service
        report['mode']=os.environ.get('QT_QPA_PLATFORM','native')
    finally:
        owner.quit()
        deadline=time.monotonic()+15
        while (owner.engine.is_alive() or owner.settings_controller.is_alive()) and time.monotonic()<deadline:
            application.processEvents();QTest.qWait(10)
        assert not owner.engine.is_alive() and not owner.settings_controller.is_alive()
        bus.unregisterObject(gui.OBJECT);bus.unregisterService(service)
    (output/'home-report.json').write_text(json.dumps(report,ensure_ascii=True,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=True))


if __name__=='__main__':main()
