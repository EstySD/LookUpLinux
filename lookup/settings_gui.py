"""Lazy native settings with serial off-GUI apply and revision acknowledgements."""
import threading
from pathlib import Path

from . import config, dicts, lifecycle

_components=None
INITIAL='Изменения применяются после нажатия кнопки'
PENDING='Применяем настройки…'
SUCCESS='Настройки применены. Автозапуск изменится при следующем входе в KDE'
FOLDER_HELP='Скопируйте в эту папку словари StarDict, Lingvo DSL, MDX или ZIP Yomitan, затем нажмите „Применить настройки“. ZIP Yomitan распаковывать не нужно. Для замены словаря замените файл с тем же именем. Для StarDict скопируйте весь комплект файлов. Можно использовать подпапки'
FOLDER_FAILED='Не удалось открыть папку словарей. Скопируйте указанный путь и откройте его в файловом менеджере. Проверьте доступ к папке'
MESSAGES={
    'invalid_shortcut':'Укажите одно сочетание клавиш',
    'shortcut_conflict':'Это сочетание занято в KDE. Выберите другое или измените его в системных настройках клавиатуры',
    'save_failed':'Не удалось сохранить настройки. Проверьте доступ к файлу настроек и попробуйте ещё раз',
    'runtime_failed':'Не удалось применить настройки. Проверьте состояние через lookup --doctor и попробуйте ещё раз',
    'rollback_shortcut':'Не удалось восстановить горячую клавишу. Проверьте сочетание LookUp Linux в системных настройках KDE',
    'rollback_config':'Не удалось восстановить сохранённые настройки. Проверьте состояние через lookup --doctor',
    'restore_unconfirmed':'Сохранённые настройки восстановлены. Рабочее состояние не подтверждено; проверьте lookup --doctor',
}


def _dictionary_rows():
    from .doctor import _REASONS
    with dicts.open_all() as dictionaries:
        return [dict(id=value.id,name=value.name+((' — '+_REASONS.get(value.reason,'не удалось прочитать')+
                    '. Проверьте ZIP или выключите словарь') if value.status=='error' else ''))
                for value in dictionaries.info()]


def _dictionary_folder():
    roots=dicts.dict_roots()
    return roots[0].absolute() if roots else None


def _fields(value,keys):
    result={key:getattr(value,key) for key in keys}
    if 'dictionaries' in result:
        result['dictionaries']=[dict(id=ident,enabled=enabled) for ident,enabled in value.dictionaries]
    return result


def components():
    global _components
    if _components is not None:return _components
    from PyQt6.QtCore import QObject,QTimer,Qt,QUrl,pyqtSignal
    from PyQt6.QtGui import QKeySequence,QShortcut,QDesktopServices
    from PyQt6.QtWidgets import (QWidget,QLabel,QVBoxLayout,QHBoxLayout,QFormLayout,QGroupBox,
        QScrollArea,QKeySequenceEdit,QListWidget,QListWidgetItem,QPushButton,QSpinBox,QCheckBox,QComboBox)

    class ApplyController(QObject):
        state=pyqtSignal(object)
        applied=pyqtSignal(object)
        initialized=pyqtSignal(object)
        invalidating=pyqtSignal()
        _completed=pyqtSignal(object)

        def __init__(self,engine,parent=None,*,registry=None,load=None,save=None,restore=None,discover=None,ack_timeout=8000):
            super().__init__(parent)
            self.engine=engine
            self.registry=registry or lifecycle.shortcut_registry()
            self._load=load or config.load
            self._save=save or config.save
            self._restore=restore or (lambda changes:config.save(changes,retain_missing=False))
            self._discover=discover or _dictionary_rows
            self._ack_timeout=ack_timeout
            self.pending=False
            self.reload_revision=None
            self._operation=0
            self._phase=None
            self._thread=None
            self._stopping=False
            self._prepared=None
            self._reason=None
            self._load_requested=False
            self._timer=QTimer(self)
            self._timer.setSingleShot(True)
            self._timer.timeout.connect(self._timeout)
            self._completed.connect(self._done,Qt.ConnectionType.QueuedConnection)

        def _start(self,phase,job):
            self._phase=phase
            operation=self._operation
            def run():
                try:value=job()
                except Exception:value=dict(status='runtime_failed')
                try:self._completed.emit((operation,phase,value))
                except RuntimeError:pass
            self._thread=threading.Thread(target=run,name='lookup-settings',daemon=False)
            try:self._thread.start()
            except (RuntimeError,OSError):
                self._done((operation,phase,dict(status='rollback_config' if phase=='rollback'
                    else 'folder_failed' if phase=='folder' else 'runtime_failed')))

        def load(self):
            if self.pending:
                if self._phase=='initial':self._load_requested=True
                return
            if self._stopping:return
            self._operation+=1
            self.pending=True
            self.state.emit(dict(kind='pending',loading=True))
            def read():
                value=self._load()
                try:rows=self._discover()
                except Exception:rows=[]
                try:
                    binding=self.registry.inspect()
                    actual=tuple(lifecycle.key_text(key) for key in binding.keys)
                    available=True
                except lifecycle.LifecycleError:
                    actual=();available=False
                folder=_dictionary_folder()
                return dict(config=value,rows=rows,actual=actual,available=available,
                            folder=str(folder) if folder is not None else '')
            self._start('load',read)

        def open_folder(self,path):
            if self.pending or self._stopping:return
            self._operation+=1
            self.pending=True
            self.state.emit(dict(kind='pending',loading=True,folder=True))
            def create():
                try:
                    destination=Path(path)
                    if not destination.is_absolute():raise ValueError
                    destination.mkdir(parents=True,exist_ok=True)
                    return dict(status='folder_ready',folder=str(destination))
                except (OSError,ValueError,TypeError):return dict(status='folder_failed')
            self._start('folder',create)

        def initialize(self):
            if self.pending or self._stopping:return
            self._operation+=1
            self.pending=True
            self._start('initial',lambda:dict(config=self._load()))

        def apply(self,snapshot):
            if self.pending or self._stopping:return
            self._operation+=1
            self.pending=True
            self.reload_revision=None
            self._prepared=None
            self.state.emit(dict(kind='pending',loading=False))
            self.invalidating.emit()
            # The GUI draft is never shared with a background transaction.
            changes={key:snapshot.get(key,getattr(config.Config(),key))
                     for key in ('online','popup_timeout','autostart','gaming_trigger')}
            changes.update({key:snapshot[key] for key in config.POPUP_FIELDS if key in snapshot})
            changes['dictionaries']=[dict(entry) for entry in snapshot['dictionaries']]
            if snapshot.get('shortcut_edited'):changes['shortcut']=snapshot['shortcut']
            def prepare():
                transaction=None
                try:
                    prior=self._load()
                    if 'shortcut' in changes:
                        canonical,_=lifecycle.parse_shortcut(changes['shortcut'])
                        transaction=self.registry.change(canonical)
                        changes['shortcut']=canonical
                    saved=self._save(changes)
                    try:rows=self._discover()
                    except Exception:rows=None
                    return dict(prior=prior,saved=saved,changes=changes,transaction=transaction,rows=rows)
                except Exception as error:
                    status=('save_failed' if isinstance(error,config.ConfigError) else
                            error.reason if isinstance(error,lifecycle.LifecycleError) and
                            error.reason in ('invalid_shortcut','shortcut_conflict') else
                            'rollback_shortcut' if isinstance(error,lifecycle.LifecycleError) and
                            error.reason=='rollback_failed' else 'runtime_failed')
                    if transaction is not None:
                        try:transaction.rollback()
                        except Exception:status='rollback_shortcut'
                    return dict(status=status)
            self._start('prepare',prepare)

        def _request_ack(self,phase):
            self._phase=phase
            self.invalidating.emit()
            self.reload_revision=self.engine.request_reload()
            if self.reload_revision is None:
                if phase=='ack':self._rollback('runtime_failed')
                else:self._finish('restore_unconfirmed')
            else:self._timer.start(self._ack_timeout)

        def ack(self,event):
            if (not self.pending or self._phase not in ('ack','restore_ack') or
                    event.stage!='reload' or event.reload_revision!=self.reload_revision):return
            self._timer.stop()
            if self._phase=='restore_ack':
                self._finish('restore_unconfirmed' if event.error else self._reason)
            elif event.error:
                self._rollback('runtime_failed')
            else:
                transaction=self._prepared['transaction']
                if transaction is not None:transaction.commit()
                saved=self._prepared['saved']
                rows=self._prepared['rows']
                self.applied.emit(saved)
                self._finish('success',config=saved,rows=rows)

        def _rollback(self,reason):
            self._timer.stop()
            self._reason=reason
            prepared=self._prepared
            def restore():
                status=None
                try:self._restore(_fields(prepared['prior'],prepared['changes']))
                except Exception:status='rollback_config'
                transaction=prepared['transaction']
                if transaction is not None:
                    try:transaction.rollback()
                    except Exception:status='rollback_shortcut'
                return dict(status=status)
            self._start('rollback',restore)

        def _timeout(self):
            if self._phase=='ack':self._rollback('runtime_failed')
            elif self._phase=='restore_ack':self._finish('restore_unconfirmed')

        def _done(self,message):
            operation,phase,value=message
            if operation!=self._operation:return
            if phase=='initial':
                self.pending=False;self._phase=None
                if not self._stopping:
                    if 'config' in value:self.initialized.emit(value['config'])
                    if self._load_requested:
                        self._load_requested=False
                        self.load()
            elif phase=='load':
                self.pending=False;self._phase=None
                if not self._stopping:
                    self.state.emit(dict(kind='loaded',**value) if 'config' in value
                                    else dict(kind='result',status='runtime_failed'))
            elif phase=='prepare':
                if 'status' in value:self._finish(value['status'])
                else:
                    self._prepared=value
                    if self._stopping:self._rollback('runtime_failed')
                    else:self._request_ack('ack')
            elif phase=='rollback':
                if value['status']:
                    self._finish(value['status'])
                elif self._stopping:
                    self._finish(self._reason)
                else:self._request_ack('restore_ack')
            elif phase=='folder':
                self._finish(value['status'],folder=value.get('folder'))

        def _finish(self,status,**values):
            self._timer.stop()
            self.pending=False
            self._phase=None
            self.reload_revision=None
            self._prepared=None
            if not self._stopping:self.state.emit(dict(kind='result',status=status,**values))

        def shutdown(self):
            self._stopping=True
            self._timer.stop()
            if self._phase in ('ack','restore_ack'):
                if self._phase=='ack':self._rollback('runtime_failed')
                else:self._finish(self._reason)

        def is_alive(self):return self.pending or (self._thread is not None and self._thread.is_alive())

    def label(text='',name=None):
        value=QLabel(text)
        value.setTextFormat(Qt.TextFormat.PlainText)
        value.setWordWrap(True)
        value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        if name:value.setAccessibleName(name)
        return value

    class SettingsWindow(QWidget):
        def __init__(self,controller):
            super().__init__()
            self.controller=controller
            self._baseline=None
            self._shortcut_baseline=''
            self._loading=False
            self._submitted_key_edit=False
            self._needs_rescan=False
            self.setWindowTitle('Настройки')
            self.resize(600,560)
            layout=QVBoxLayout(self)
            scroll=QScrollArea()
            scroll.setWidgetResizable(True)
            body=QWidget();form=QVBoxLayout(body)
            invocation=QGroupBox('Вызов');invocation_form=QFormLayout(invocation)
            self.shortcut=QKeySequenceEdit()
            if hasattr(self.shortcut,'setMaximumSequenceLength'):self.shortcut.setMaximumSequenceLength(1)
            self.shortcut.setAccessibleName('Горячая клавиша')
            invocation_form.addRow('Горячая клавиша',self.shortcut)
            self.actual_binding=label()
            invocation_form.addRow(self.actual_binding)
            form.addWidget(invocation)
            dictionaries=QGroupBox('Словари');dictionary_layout=QVBoxLayout(dictionaries)
            self.dictionaries=QListWidget()
            self.dictionaries.setAccessibleName('Порядок и включение словарей')
            self.dictionaries.setMinimumHeight(100)
            heading=label('Словари — сверху приоритетнее')
            heading.setBuddy(self.dictionaries)
            dictionary_layout.addWidget(heading);dictionary_layout.addWidget(self.dictionaries)
            reorder=QHBoxLayout()
            self.up_button=QPushButton('Выше');self.down_button=QPushButton('Ниже')
            self.up_button.setAccessibleName('Переместить словарь выше')
            self.down_button.setAccessibleName('Переместить словарь ниже')
            reorder.addWidget(self.up_button);reorder.addWidget(self.down_button)
            dictionary_layout.addLayout(reorder)
            self.dictionary_help=label()
            dictionary_layout.addWidget(self.dictionary_help)
            self.folder_path=label(name='Папка словарей')
            self.folder_path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse|
                                                     Qt.TextInteractionFlag.TextSelectableByKeyboard)
            self.folder_path.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.folder_button=QPushButton('Открыть папку словарей')
            self.folder_button.setAccessibleName('Открыть папку словарей')
            self.folder_help=label(FOLDER_HELP)
            dictionary_layout.addWidget(self.folder_path)
            dictionary_layout.addWidget(self.folder_button)
            dictionary_layout.addWidget(self.folder_help)
            form.addWidget(dictionaries)
            options=QGroupBox('Перевод и запуск');option_layout=QFormLayout(options)
            self.timeout=QSpinBox();self.timeout.setRange(1,300);self.timeout.setSuffix(' с')
            self.timeout.setAccessibleName('Закрывать попап через')
            option_layout.addRow('Закрывать попап через',self.timeout)
            self.online=QCheckBox('Онлайн-перевод')
            self.online.setAccessibleName('Онлайн-перевод')
            self.autostart=QCheckBox('Запускать при входе в KDE')
            self.autostart.setAccessibleName('Запускать при входе в KDE')
            self.gaming_trigger=QComboBox()
            self.gaming_trigger.addItems(('Хорд задних кнопок (evdev)','Клавиша Steam Input'))
            self.gaming_trigger.setAccessibleName('Триггер Gaming Mode')
            option_layout.addRow(self.online)
            option_layout.addRow(label('При отключении используются только локальные словари'))
            option_layout.addRow(self.autostart)
            option_layout.addRow('Триггер Gaming Mode',self.gaming_trigger)
            form.addWidget(options)
            popup=QGroupBox('Содержимое попапа');popup_layout=QVBoxLayout(popup)
            for key,text in zip(config.POPUP_FIELDS,('Показывать исходный текст и перевод контекста',
                    'Показывать значение слова в контексте','Разворачивать полные словарные статьи')):
                control=QCheckBox(text)
                control.setAccessibleName(text)
                setattr(self,key,control)
                popup_layout.addWidget(control)
                control.toggled.connect(self._edited)
            form.addWidget(popup)
            scroll.setWidget(body);layout.addWidget(scroll,1)
            self.status=label(INITIAL,'Применение настроек')
            layout.addWidget(self.status)
            actions=QHBoxLayout()
            self.apply_button=QPushButton('Применить настройки')
            self.close_button=QPushButton('Закрыть')
            actions.addWidget(self.apply_button);actions.addWidget(self.close_button)
            layout.addLayout(actions)
            for button in (self.apply_button,self.close_button,self.up_button,self.down_button,self.folder_button):
                button.setAutoDefault(True)
            self._editors=(self.shortcut,self.dictionaries,self.timeout,self.online,self.autostart,self.gaming_trigger)+tuple(
                getattr(self,key) for key in config.POPUP_FIELDS)
            self.shortcut.keySequenceChanged.connect(self._edited)
            self.dictionaries.itemChanged.connect(self._edited)
            self.dictionaries.currentRowChanged.connect(self._reorder_state)
            self.timeout.valueChanged.connect(self._edited)
            self.online.toggled.connect(self._edited);self.autostart.toggled.connect(self._edited)
            self.gaming_trigger.currentIndexChanged.connect(self._edited)
            self.up_button.clicked.connect(lambda:self._move(-1))
            self.down_button.clicked.connect(lambda:self._move(1))
            self.folder_button.clicked.connect(self.open_folder)
            self.apply_button.clicked.connect(lambda:self.controller.apply(self.snapshot()))
            self.close_button.clicked.connect(self.close)
            QShortcut(QKeySequence(Qt.Key.Key_Escape),self,activated=self.close)
            self.controller.state.connect(self._state)
            self._enabled()
            self.refresh()

        def refresh(self):
            self.controller.load()

        def showEvent(self,event):
            super().showEvent(event)
            self.refresh()
            QTimer.singleShot(0,lambda:self.shortcut.setFocus() if self.isVisible() else None)

        def snapshot(self):
            shortcut=self.shortcut.keySequence().toString(QKeySequence.SequenceFormat.PortableText)
            return dict(shortcut=shortcut,shortcut_edited=shortcut!=self._shortcut_baseline,
                dictionaries=[dict(id=self.dictionaries.item(i).data(Qt.ItemDataRole.UserRole),
                    enabled=self.dictionaries.item(i).checkState()==Qt.CheckState.Checked)
                    for i in range(self.dictionaries.count())],popup_timeout=self.timeout.value(),
                online=self.online.isChecked(),autostart=self.autostart.isChecked(),
                gaming_trigger=('back_chord','key')[self.gaming_trigger.currentIndex()],
                **{key:getattr(self,key).isChecked() for key in config.POPUP_FIELDS})

        def open_folder(self):
            if self.controller.pending or not self.folder_path.text():return
            self._needs_rescan=True
            self.controller.open_folder(self.folder_path.text())

        def _set_dictionaries(self,configured,discovered):
            selected=self.dictionaries.currentItem()
            selected=selected.data(Qt.ItemDataRole.UserRole) if selected is not None else None
            found={row['id']:row['name'] for row in discovered}
            rows=list(configured)
            included={ident for ident,_ in rows}
            rows.extend((ident,True) for ident in found if ident not in included)
            self.dictionaries.clear()
            for ident,enabled in rows:
                item=QListWidgetItem(found.get(ident,ident+' — недоступен'))
                item.setData(Qt.ItemDataRole.UserRole,ident)
                item.setFlags(item.flags()|Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked)
                self.dictionaries.addItem(item)
                if ident==selected:self.dictionaries.setCurrentItem(item)

        def _state(self,value):
            if value['kind']=='pending':
                if not value['loading']:self._submitted_key_edit=self.snapshot()['shortcut_edited']
                self.status.setText('Открываем папку словарей…' if value.get('folder') else
                                    'Загружаем настройки…' if value['loading'] else PENDING)
            elif value['kind']=='loaded':
                self._loading=True
                saved=value['config']
                actual=value['actual']
                shortcut=actual[0] if len(actual)==1 else saved.shortcut
                self._shortcut_baseline=shortcut
                self.shortcut.setKeySequence(QKeySequence(shortcut))
                self.actual_binding.setText('В KDE: '+(', '.join(actual) if actual else 'не назначено')
                                           if value['available'] else 'Сочетание в KDE недоступно для проверки')
                self._set_dictionaries(saved.dictionaries,value['rows'])
                self.folder_path.setText(value['folder'])
                self.folder_help.setText(FOLDER_HELP if value['folder'] else
                    'Поиск словарей отключён переменной LOOKUP_DICTS. Укажите в ней каталог или уберите переменную, затем перезапустите приложение.')
                self.timeout.setValue(saved.popup_timeout)
                self.online.setChecked(saved.online);self.autostart.setChecked(saved.autostart)
                self.gaming_trigger.setCurrentIndex(0 if saved.gaming_trigger=='back_chord' else 1)
                for key in config.POPUP_FIELDS:getattr(self,key).setChecked(getattr(saved,key))
                self._loading=False
                self._baseline=self.snapshot()
                self.status.setText(INITIAL)
            else:
                status=value['status']
                if status=='success':
                    self._loading=True
                    saved=value['config']
                    if value['rows'] is not None:self._set_dictionaries(saved.dictionaries,value['rows'])
                    self.timeout.setValue(saved.popup_timeout)
                    self.online.setChecked(saved.online);self.autostart.setChecked(saved.autostart)
                    self.gaming_trigger.setCurrentIndex(0 if saved.gaming_trigger=='back_chord' else 1)
                    for key in config.POPUP_FIELDS:getattr(self,key).setChecked(getattr(saved,key))
                    self._loading=False
                    self._shortcut_baseline=self.snapshot()['shortcut']
                    self._baseline=self.snapshot()
                    self._needs_rescan=False
                    if self._submitted_key_edit:self.actual_binding.setText('В KDE: '+self._shortcut_baseline)
                    self.status.setText(SUCCESS)
                elif status in ('folder_ready','folder_failed'):
                    opened=False
                    if status=='folder_ready':
                        try:opened=QDesktopServices.openUrl(QUrl.fromLocalFile(value['folder']))
                        except Exception:pass
                    self.status.setText(FOLDER_HELP if opened else FOLDER_FAILED)
                else:self.status.setText(MESSAGES.get(status,MESSAGES['runtime_failed']))
            self._enabled()

        def _enabled(self):
            editable=not self.controller.pending and self._baseline is not None
            for editor in self._editors:editor.setEnabled(editable)
            self.folder_button.setEnabled(not self.controller.pending and bool(self.folder_path.text()))
            self.apply_button.setEnabled(editable and self._valid() and
                                         (self._needs_rescan or self.snapshot()!=self._baseline))
            self._reorder_state()
            self._dictionary_help()

        def _valid(self):
            try:lifecycle.parse_shortcut(self.snapshot()['shortcut']);return True
            except lifecycle.LifecycleError:return False

        def _edited(self):
            if self._loading:return
            self._enabled()
            if not self.controller.pending:
                self.status.setText(INITIAL if self._valid() else MESSAGES['invalid_shortcut'])

        def _dictionary_help(self):
            if self.dictionaries.count()==0:
                self.dictionary_help.setText('Локальные словари не найдены\nУстановите Mueller 7 с пакетом или добавьте свои словари через кнопку „Открыть папку словарей“')
            elif not any(self.dictionaries.item(i).checkState()==Qt.CheckState.Checked for i in range(self.dictionaries.count())):
                self.dictionary_help.setText('Локальные словари отключены. При выключенном онлайн-переводе перевод будет недоступен')
            else:self.dictionary_help.setText('')

        def _reorder_state(self):
            row=self.dictionaries.currentRow()
            enabled=not self.controller.pending and self._baseline is not None
            self.up_button.setEnabled(enabled and row>0)
            self.down_button.setEnabled(enabled and 0<=row<self.dictionaries.count()-1)

        def _move(self,step):
            row=self.dictionaries.currentRow()
            if self.controller.pending or not 0<=row+step<self.dictionaries.count():return
            item=self.dictionaries.takeItem(row)
            self.dictionaries.insertItem(row+step,item)
            self.dictionaries.setCurrentRow(row+step)
            self._edited()

    _components=(SettingsWindow,ApplyController)
    return _components
