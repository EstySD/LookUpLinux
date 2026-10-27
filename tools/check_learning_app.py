"""Native synthetic learning acceptance and isolated official Anki core import."""
import argparse
import contextlib
import csv
from dataclasses import replace
import hashlib
import html
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

REQUIRED_GATES=frozenset(('owner_tray','history_sort_search','history_card_duplicate',
    'history_delete_count_reset','popup_exact_snapshot','review_reveal_intervals',
    'review_grade_persist_empty','export_roundtrip','dialog_cancel_atomic_failure',
    'native_light_dark'))
REQUIRED_CLEANUP=frozenset(('worker_stopped','windows_closed','database_closed',
                            'environment_restored','profile_removed','settings_paths_removed'))
SOURCE='They waited on the bank.\nA public <sign> & quoted "scene".'
MEANING='берег, "крутой" <b>буквально</b>'


def accepted(report):
    gates=report.get('gates',{});cleanup=report.get('cleanup',{})
    return (not report.get('error') and REQUIRED_GATES.issubset(gates) and
            all(value is True for value in gates.values()) and REQUIRED_CLEANUP.issubset(cleanup) and
            all(value is True for value in cleanup.values()))


def import_status(value):
    if value and value.get('verified') is True and value.get('unchanged_file') is True:
        return dict(value,status='verified',verified=True)
    return dict(status='unverified',verified=False,
                reason=(value or {}).get('reason','Anki core import did not verify unchanged exported fields.'
                       if value is not None else 'Official Anki core import was not run.'))


def finish_import(report,output,anki_python):
    imported=None
    if accepted(report) and anki_python:
        try:
            import_path=output/'anki-import.json'
            import_path.unlink(missing_ok=True)
            result=subprocess.run([str(anki_python),str(Path(__file__).resolve()),'--anki-import',str(output/'cards-anki.txt'),
                                   '--output',str(import_path)],capture_output=True,text=True,timeout=45)
            if result.returncode:
                raise ValueError('import_failed')
            imported=json.loads(import_path.read_text(encoding='utf-8'))
            if not isinstance(imported,dict):raise ValueError('invalid_import_report')
            if imported.get('verified') and (imported.get('sha256')!=digest(output/'cards-anki.txt') or
                                             imported.get('throwaway_collection_removed') is not True):
                raise ValueError('invalid_import_evidence')
        except (subprocess.TimeoutExpired,OSError,ValueError,UnicodeError):
            imported=dict(verified=False,reason='Anki core import failed or returned invalid evidence.')
    report['anki_import']=import_status(imported)
    report['passed']=accepted(report) and (not anki_python or report['anki_import']['verified'])
    return report


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def anki_import(path):
    """Uses Anki's actual Rust CSV importer, never a lookalike parser."""
    import importlib.metadata
    from anki.collection import Collection
    from anki import import_export_pb2
    before=digest(path)
    with Path(path).open(encoding='utf-8',newline='') as stream:
        expected=list(csv.reader((line for line in stream if not line.startswith('#')),delimiter='\t'))
    with tempfile.TemporaryDirectory(prefix='lookup-anki-import-') as directory:
        collection=Collection(str(Path(directory)/'collection.anki2'))
        try:
            model=next(model for model in collection.models.all()
                       if model['type']==0 and len(model['flds'])==2 and len(model['tmpls'])==1)
            metadata=collection.get_csv_metadata(str(Path(path).resolve()),None)
            assert metadata.is_html and list(metadata.column_labels)==['Front','Back']
            metadata.global_notetype.id=model['id']
            metadata.global_notetype.field_columns[:]=[1,2]
            metadata.deck_id=collection.decks.id('LookUp Synthetic Acceptance')
            collection.import_csv(import_export_pb2.ImportCsvRequest(path=str(Path(path).resolve()),metadata=metadata))
            actual=[list(collection.get_note(note_id).fields) for note_id in collection.find_notes('')]
            # Compare the actual imported fields byte-for-byte with the export
            # cells, then check visible Unicode/literal markup/newline semantics.
            assert sorted(actual)==sorted(expected) and len(actual)==2
            bank=next(fields for fields in actual if html.unescape(fields[0])=='bank')
            apple=next(fields for fields in actual if html.unescape(fields[0])=='apple')
            expected_back=html.escape(MEANING,quote=True)+'<hr>'+html.escape(SOURCE,quote=True).replace('\n','<br>')
            assert bank[1]==expected_back
            assert html.unescape(apple[1]).startswith('яблоко')
            assert '<br>' in bank[1] and '&lt;b&gt;' in bank[1] and '&lt;sign&gt;' in bank[1]
            report=dict(verified=True,backend='official anki Python/Rust core',
                        version=importlib.metadata.version('anki'),notes=len(actual),fields=actual,
                        ordinary_two_field_notetype=True,unicode_literal_html_multiline=True)
        finally:collection.close()
    report.update(unchanged_file=digest(path)==before,sha256=before,throwaway_collection_removed=not Path(directory).exists())
    return report


def native(output,anki_python=None):
    from lookup import app as core,gui,learning,learning_gui,platform,store,translate
    from lookup.dicts import Article
    from tests._stardict_writer import write_stardict
    original_env=dict(os.environ)
    report=dict(acceptance='agent',gates={},cleanup={},observations={},
        limits=['Controlled public displayed events; capture/hotkey/provider are previous-phase acceptance.',
                'Actual Qt file dialogs use the in-process Qt dialog backend for deterministic selection.',
                'No human acceptance, personal Anki profile, external sync or Phase8 acceptance.'])
    owner=connection=application=None
    profile=tempfile.TemporaryDirectory(prefix='lookup-learning-06-')
    profile_path=Path(profile.name)
    try:
        session=platform.session_env()
        os.environ.update(session)
        os.environ.update(LOOKUP_DB=str(profile_path/'history.db'),LOOKUP_CONFIG=str(profile_path/'config.json'),
                          LOOKUP_DICTS=str(profile_path/'dicts'),LOOKUP_CACHE=str(profile_path/'cache'),
                          XDG_CONFIG_HOME=str(profile_path/'config'),XDG_CACHE_HOME=str(profile_path/'cache'),
                          XDG_DATA_HOME=str(profile_path/'data'))
        report['settings_isolation']=dict(owned_xdg_paths=['config','cache','data'],
            runtime_bus_unchanged=all(os.environ[key]==session[key] for key in ('XDG_RUNTIME_DIR','DBUS_SESSION_BUS_ADDRESS')))
        (profile_path/'config.json').write_text('{"online":false}',encoding='utf-8')
        write_stardict(profile_path/'dicts','public',[('apple','_n. яблоко'),('bank','_n. банк')])
        store.open_store().close()
        from PyQt6.QtCore import Qt,QPoint,QTimer,QEvent
        from PyQt6.QtGui import QPalette,QColor
        from PyQt6.QtTest import QTest
        from PyQt6.QtWidgets import QApplication,QFileDialog,QDialogButtonBox,QStyleFactory
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs,True)
        application=QApplication.instance() or QApplication([])
        application.setQuitOnLastWindowClosed(False)
        if 'Breeze' in QStyleFactory.keys():application.setStyle('Breeze')
        report['platform']=application.platformName()
        assert report['platform']=='wayland','native_wayland_required'

        def pump(milliseconds=50):
            QTest.qWait(milliseconds);application.processEvents()
        def wait(predicate,seconds=4):
            deadline=time.monotonic()+seconds
            while not predicate() and time.monotonic()<deadline:pump(25)
            assert predicate(),'native_condition_timeout'
        def click(widget):
            QTest.mouseClick(widget,Qt.MouseButton.LeftButton);pump()
        def check(name,value):
            report['gates'][name]=bool(value)
            assert value,name
        def theme(dark):
            palette=application.style().standardPalette()
            for role in (QPalette.ColorRole.Window,QPalette.ColorRole.Base,QPalette.ColorRole.Button):
                palette.setColor(role,QColor('#232629' if dark else '#fcfcfc'))
            for role in (QPalette.ColorRole.WindowText,QPalette.ColorRole.Text,QPalette.ColorRole.ButtonText):
                palette.setColor(role,QColor('#eff0f1' if dark else '#232629'))
            application.setPalette(palette);pump(100)
        def shot(widget,name):
            widget.show();widget.raise_();pump(100)
            assert widget.grab().save(str(output/name)),'screenshot_failed'
        def tray(index):
            owner.menu.popup(QPoint(60,60));pump()
            rectangle=owner.menu.actionGeometry(owner.future_actions[index])
            QTest.mouseClick(owner.menu,Qt.MouseButton.LeftButton,pos=rectangle.center());pump()
        def words(value):return [value.table.item(row,0).text() for row in range(value.table.rowCount())]
        def select(value,word):
            index=words(value).index(word)
            QTest.mouseClick(value.table.viewport(),Qt.MouseButton.LeftButton,
                             pos=value.table.visualItemRect(value.table.item(index,0)).center());pump()
        def save_dialog(button,path=None):
            observed=[]
            timer=QTimer();timer.setInterval(25)
            def choose():
                modal=application.activeModalWidget()
                if isinstance(modal,QFileDialog):
                    timer.stop();observed.append(True)
                    try:
                        if path is not None:
                            modal.setOption(QFileDialog.Option.DontConfirmOverwrite,True)
                            modal.selectFile(str(Path(path).resolve()))
                        box=modal.findChild(QDialogButtonBox)
                        button=box.button(QDialogButtonBox.StandardButton.Cancel if path is None else QDialogButtonBox.StandardButton.Save)
                        QTest.mouseClick(button,Qt.MouseButton.LeftButton)
                    except Exception as error:
                        observed.append(type(error).__name__)
                        modal.reject()
            timer.timeout.connect(choose);timer.start()
            deadline=QTimer();deadline.setSingleShot(True)
            def reject():
                modal=application.activeModalWidget()
                if modal is not None:modal.reject()
            deadline.timeout.connect(reject);deadline.start(4000)
            click(button);timer.stop();deadline.stop()
            assert observed,'qt_file_dialog_not_observed'
            assert len(observed)==1,'qt_file_dialog_callback_failed'

        class PublicSource:
            def freeze(self):return core.Frozen('primary',(120,120),platform.Monitor('synthetic',0,0,1920,1080,1),text='apple')
            def resolve(self,source,dictionaries):return core.Query('apple','A public apple.')
            def consume(self,source):pass
        def engine_factory(publish,**kwargs):return core.Engine(publish,source=PublicSource())
        _,Owner=gui.components()
        owner=Owner(platform.session_env(),engine_factory=engine_factory,focus=False,on_quit=lambda:None)
        connection=owner._learning_connection()
        for word,count,value in (('bank',2,'банк'),('river',10,'река'),('apple',2,'яблоко')):
            for _ in range(count):store.upsert_word(connection,word,value,'Public history context.',now=100)
        tray(0);value=owner.words_window
        check('owner_tray',owner.tray.isVisible() and value is not None and value.isVisible() and
              owner.future_actions[0].isEnabled() and owner.future_actions[1].isEnabled() and not owner.future_actions[2].isEnabled())
        before=connection.total_changes
        initial=words(value)
        header=value.table.horizontalHeader()
        QTest.mouseClick(header.viewport(),Qt.MouseButton.LeftButton,
                         pos=QPoint(header.sectionViewportPosition(2)+header.sectionSize(2)//2,header.height()//2));pump()
        ascending=words(value)
        value.search.setFocus();QTest.keyClicks(value.search,'BANK');pump()
        searched=words(value);value.search.clear();pump()
        check('history_sort_search',initial==['river','apple','bank'] and ascending==['apple','bank','river'] and
              searched==['bank'] and connection.total_changes==before)
        now=[int(time.time())+60]
        value.clock=lambda:now[0]
        select(value,'apple');click(value.add_button)
        apple=learning.get_card(connection,'apple')
        click(value.add_button)
        check('history_card_duplicate',bool(apple) and learning.get_card(connection,'apple')==apple and 'Уже' in value.status.text())
        click(value.delete_button)
        removed=connection.execute('SELECT count FROM words WHERE word="apple"').fetchone() is None
        owner.Trigger('')
        wait(lambda:connection.execute('SELECT count FROM words WHERE word="apple"').fetchone() is not None)
        wait(lambda:owner._displayed is not None)
        count=connection.execute('SELECT count FROM words WHERE word="apple"').fetchone()[0]
        check('history_delete_count_reset',removed and count==1 and learning.get_card(connection,'apple')==apple)
        owner.popup.dismiss();pump()

        identity=owner.engine.begin()
        span=(SOURCE.index('bank'),SOURCE.index('bank')+4)
        result=translate.Result('word','bank',articles=(Article('Public dictionary','bank',None,(('n',('банк','берег')),),'Публичная словарная статья.'),),
            translation='банк',context_meaning=MEANING,meaning_provider='google-gtx-marked-v1',
            saved=True,count=2,context_complete=True)
        event=core.Event(identity,'ready',result=result,context=SOURCE,point=(120,120),mode='primary',span=span)
        owner.receive(event);pump();click(owner.popup.card_button)
        bank=learning.get_card(connection,'bank')
        owner.receive(replace(event,stage='context',result=replace(result,context_meaning='другое значение')));pump()
        click(owner.popup.card_button)
        check('popup_exact_snapshot',bank is not None and bank['translation']==MEANING and bank['context']==SOURCE and
              bank['span']==span and bank['provider']=='google-gtx-marked-v1' and learning.get_card(connection,'bank')==bank)
        owner.popup.dismiss();value.refresh();select(value,'bank');click(value.delete_button)
        assert learning.get_card(connection,'bank')==bank,'history_delete_damaged_card'
        theme(False);shot(value,'words-light.png')
        tray(1);review=owner.review_window;review.clock=lambda:now[0];review.refresh();pump()
        hidden=not review.translation.isVisible() and not any(button.isEnabled() for button in review.rating_buttons.values())
        assert review.current and review.current['word']=='bank','expected_bank_due_first'
        transitions={rating:learning.preview(review.current,rating)['delay'] for rating in review.rating_buttons}
        click(review.reveal_button)
        check('review_reveal_intervals',hidden and review.translation.toPlainText()==MEANING and review.context.toPlainText()==SOURCE and
              all(button.isEnabled() and '\n' in button.text() for button in review.rating_buttons.values()))
        report['observations']['interval_seconds']=transitions
        shot(review,'review-light.png')
        theme(True);shot(review,'review-dark.png');shot(value,'words-dark.png')
        check('native_light_dark',all((output/name).is_file() for name in ('words-light.png','words-dark.png','review-light.png','review-dark.png')))
        click(review.rating_buttons['Good']);click(review.rating_buttons['Good'])
        graded=learning.get_card(connection,'bank')
        refused=learning.grade_card(connection,'bank',0,'Good',now=now[0])=='stale'
        assert graded['review_version']==1 and graded['due']==now[0]+transitions['Good'] and refused,'grade_duplicate_or_interval'
        assert review.current and review.current['word']=='apple','expected_next_card'
        click(review.reveal_button);click(review.rating_buttons['Good'])
        empty=review.current is None and 'Нет карточек для повторения' in review.front.text()
        with contextlib.closing(store.open_store(profile_path/'history.db')) as restarted:
            persisted=learning.get_card(restarted,'bank')==graded and not learning.due_cards(restarted,now=now[0])
        review.close();tray(1)
        check('review_grade_persist_empty',empty and persisted and owner.review_window is review and review.current is None)

        value.show();pump()
        before_files=set(output.iterdir())
        save_dialog(value.csv_button)
        canceled=set(output.iterdir())==before_files
        csv_path=output/'cards.csv';anki_path=output/'cards-anki.txt'
        save_dialog(value.csv_button,csv_path);save_dialog(value.anki_button,anki_path)
        expected=[[card['word'],card['translation'],card['context'] or ''] for card in learning.list_cards(connection)]
        with csv_path.open(encoding='utf-8',newline='') as stream:rows=list(csv.reader(stream))
        raw=anki_path.read_text(encoding='utf-8')
        with anki_path.open(encoding='utf-8',newline='') as stream:
            anki_rows=list(csv.reader((line for line in stream if not line.startswith('#')),delimiter='\t'))
        check('export_roundtrip',rows==[['word','translation','context']]+expected and len(anki_rows)==2 and
              all(len(row)==2 for row in anki_rows) and raw.startswith('#separator:Tab\n#html:true\n#columns:Front\tBack\n') and
              '&lt;b&gt;' in raw and '&lt;sign&gt;' in raw and '<br>' in raw)
        old_path=output/'old-export.csv';old_path.write_bytes(b'OLD_PUBLIC_EXPORT')
        with mock.patch('lookup.learning.os.replace',side_effect=OSError('controlled_export_failure')):
            save_dialog(value.csv_button,old_path)
        check('dialog_cancel_atomic_failure',canceled and old_path.read_bytes()==b'OLD_PUBLIC_EXPORT' and
              not list(output.glob('.old-export.csv.*.tmp')) and 'Не удалось экспортировать' in value.status.text())
        report['observations'].update(default_order=initial,ascending_order=ascending,searched=searched,
            history_reset_count=count,popup_card_snapshot=bank,graded_bank=graded,
            exports=dict(csv_sha256=digest(csv_path),anki_sha256=digest(anki_path),cards=len(expected)),
            dialogs='Actual QFileDialog observed and selected/canceled; os.replace fault injected only for atomic-failure gate.')
    except Exception as error:
        report['error']=type(error).__name__+':'+str(error)[:160]
    finally:
        if owner is not None:
            owner.quit()
            deadline=time.monotonic()+3
            while owner.engine.is_alive() and time.monotonic()<deadline:
                if application:application.processEvents()
                owner.engine.join(.025)
            report['cleanup']['worker_stopped']=not owner.engine.is_alive()
            report['cleanup']['windows_closed']=owner.words_window is None and owner.review_window is None and not owner.popup.isVisible() and not owner.tray.isVisible()
            if connection is not None:
                try:connection.execute('SELECT 1')
                except sqlite3.ProgrammingError:report['cleanup']['database_closed']=True
                else:report['cleanup']['database_closed']=False
            if application:
                application.sendPostedEvents(None,QEvent.Type.DeferredDelete);application.processEvents()
        else:
            report['cleanup'].update(worker_stopped=True,windows_closed=True,database_closed=True)
        os.environ.clear();os.environ.update(original_env)
        report['cleanup']['environment_restored']=dict(os.environ)==original_env
        profile.cleanup();report['cleanup']['profile_removed']=not profile_path.exists()
        report['cleanup']['settings_paths_removed']=all(not (profile_path/name).exists() for name in ('config','cache','data'))
    return finish_import(report,output,anki_python)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--anki-python',type=Path)
    parser.add_argument('--anki-import',type=Path)
    args=parser.parse_args()
    if args.anki_import:
        try:report=anki_import(args.anki_import)
        except Exception as error:report=dict(verified=False,reason=type(error).__name__+':'+str(error)[:180])
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        return int(not report.get('verified'))
    args.output.mkdir(parents=True,exist_ok=True)
    report=native(args.output,args.anki_python)
    (args.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(acceptance='agent',passed=report['passed'],anki_import=report['anki_import']['status'])))
    return int(not report['passed'])


if __name__=='__main__':raise SystemExit(main())
