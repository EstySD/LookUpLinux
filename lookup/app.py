"""One thread owns lookup resources; request identities guard history and UI."""
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
import sqlite3
import threading
import time
import unicodedata
import uuid

from . import config, dicts, translate, platform, capture, ocr, context as contextual
from .online import ONLINE_MAX_CHARS
from .store import open_store, upsert_word, enrich_word_context


class AppError(Exception):
    def __init__(self, reason):
        self.reason=reason
        super().__init__(reason)


@dataclass(frozen=True)
class Frozen:
    mode: str
    point: tuple
    monitor: platform.Monitor
    text: str | None = None
    image: capture.Capture | None = None
    available: tuple | None = None


@dataclass(frozen=True)
class Query:
    text: str
    context: str | None
    timings: dict = field(default_factory=dict)
    span: tuple[int, int] | None = None
    context_complete: bool = False


@dataclass
class Resources:
    config: config.Config
    dictset: object = None
    conn: object = None
    save_error: str | None = None


@dataclass(frozen=True)
class Event:
    id: int
    stage: str
    result: translate.Result | None = None
    context: str | None = None
    point: tuple | None = None
    monitor: platform.Monitor | None = None
    mode: str | None = None
    error: str | None = None
    save_error: str | None = None
    elapsed_ms: float = 0
    available: tuple | None = None


class Source:
    def __init__(self, env=None):
        self.env=env
        self.consumed=None

    def freeze(self):
        if self.env is None:
            self.env=platform.session_env()
        try:
            point=platform.cursor_position(self.env)
        except platform.PlatformError as error:
            raise AppError('missing_kdotool' if error.reason=='missing_command' else 'cursor_failed') from None
        try:
            monitor=platform.monitor_at(point,platform.monitors(self.env))
            available=platform.work_area(self.env,monitor)
        except platform.PlatformError as error:
            raise AppError('missing_kscreen' if error.reason=='missing_command' else 'monitor_failed') from None
        text=platform.read_primary(self.env)
        text=text.strip() if isinstance(text,str) else ''
        valid=(0<len(text)<=ONLINE_MAX_CHARS and
               not any(unicodedata.category(c).startswith('C') and c not in '\t\r\n' for c in text) and
               any(c.isascii() and c.isalpha() for c in text) and
               translate.classify(text).kind!='invalid')
        if valid:
            identity=' '.join(text.split())
            if identity!=self.consumed:
                return Frozen('primary',point,monitor,text=text,available=available)
        else:
            self.consumed=None
        try:
            frame=capture.capture_monitor(monitor,self.env,'screenshot2')
        except platform.PlatformError as error:
            raise AppError('missing_pyqt6' if error.reason=='missing_pyqt6' else 'capture_failed') from None
        return Frozen('ocr',point,monitor,image=frame,available=available)

    def consume(self,source):
        if source.mode=='primary':
            self.consumed=' '.join(source.text.split())

    def resolve(self,source,dictset):
        if source.mode=='primary':
            return Query(source.text,source.text)
        point=platform.image_point(source.point,source.monitor,(source.image.width,source.image.height))
        result=ocr.recognize_image(source.image.png,point)
        if result.selection is None:
            raise AppError('not_found')
        timings={key:value for key,value in result.timings.items() if key!='total'}
        selection=result.selection
        text=ocr.choose_query(selection,dictset)
        span=selection.span if text==selection.word else dict(selection.candidate_spans).get(text)
        return Query(text,selection.context if selection.context is not None else selection.line,
                     dict(timings,capture=source.image.elapsed_ms),span,selection.context_complete)


@contextmanager
def _resources():
    cfg=config.load()
    dictionaries=conn=None
    error=None
    try:
        try:
            dictionaries=dicts.open_all(cfg)
        except Exception:
            pass
        try:
            conn=open_store()
            conn.execute('PRAGMA busy_timeout=50')
        except Exception:
            if conn is not None:
                conn.close()
                conn=None
            error='unavailable'
        yield Resources(cfg,dictionaries,conn,error)
    finally:
        try:
            if dictionaries is not None:
                dictionaries.close()
        finally:
            if conn is not None:
                conn.close()


class Engine:
    def __init__(self,publish,*,source=None,resources=None,lookup=None):
        self._publish=publish
        self._source=source if source is not None else Source()
        self._resources=resources or _resources
        self._lookup=lookup or translate.lookup
        self._condition=threading.Condition()
        self._generation=0
        self._started=0
        self._pending=None
        self._stopping=False
        self._context_slot=threading.BoundedSemaphore(1)
        self._meaning_slot=threading.BoundedSemaphore(1)
        self._worker=threading.Thread(target=self._run,name='lookup-worker',daemon=False)
        self._worker.start()

    def begin(self):
        with self._condition:
            if self._stopping:
                return None
            self._generation+=1
            self._started=time.perf_counter()
            self._pending=None
            return self._generation

    def enqueue(self,identity):
        with self._condition:
            if self.current(identity):
                self._pending=(identity,self._started)
                self._condition.notify()

    def current(self,identity):
        with self._condition:
            return identity is not None and identity==self._generation and not self._stopping

    def dismiss(self,identity):
        with self._condition:
            if self.current(identity):
                self._generation+=1
                self._pending=None

    def stop(self):
        with self._condition:
            self._stopping=True
            self._generation+=1
            self._pending=None
            self._condition.notify()

    def join(self,timeout):
        self._worker.join(timeout)

    def is_alive(self):
        return self._worker.is_alive()

    def _emit(self,event):
        if self.current(event.id):
            self._publish(event)

    def _run(self):
        try:
            with self._resources() as resources:
                while True:
                    with self._condition:
                        self._condition.wait_for(lambda:self._stopping or self._pending is not None)
                        if self._stopping:
                            return
                        identity,started=self._pending
                        self._pending=None
                    self._process(identity,started,resources)
        except Exception:
            # Last-resort boundary: never print a private worker traceback.
            with self._condition:
                identity=self._generation
            self._emit(Event(identity,'error',error='worker_failed'))

    def _process(self,identity,started,resources):
        origin={}
        try:
            if not self.current(identity):
                return
            source=self._source.freeze()
            origin=dict(point=source.point,monitor=source.monitor,mode=source.mode,available=source.available)
            if not self.current(identity):
                return
            self._emit(Event(identity,'frozen',**origin,elapsed_ms=(time.perf_counter()-started)*1000))
            query=self._source.resolve(source,resources.dictset)
            primary=source if source.mode=='primary' else None
            source=None  # Pixel storage never crosses the GUI signal boundary.
            if not self.current(identity):
                return
            history=None
            token=uuid.uuid4().hex
            def snapshot(result):
                timings=dict(result.timings,**query.timings)
                for key in ('first_useful','meaning_ready'):
                    if timings.get(key,0)>0:
                        timings[key]+=lookup_offset
                return replace(result,timings=timings)
            def ready(result):
                nonlocal history
                with self._condition:
                    if not self.current(identity):
                        return
                    if history is None:
                        if primary is not None:
                            self._source.consume(primary)
                        saved,count,error=False,None,None
                        if result.kind in ('word','phrase') and result.online_error!='not_found':
                            if resources.conn is None:
                                error=resources.save_error or 'unavailable'
                            else:
                                try:
                                    pair=dict(context_span=query.span,context_token=token) if query.span is not None else {}
                                    count=upsert_word(resources.conn,result.key,result.translation,query.context,
                                                      lemma=result.lemma,**pair)
                                    saved=True
                                except (sqlite3.Error,OSError,ValueError):
                                    error='unavailable'
                        history=(saved,count,error)
                    value=snapshot(result)
                    value.saved,value.count=history[:2]
                self._emit(Event(identity,'ready',result=value,context=query.context,**origin,
                                 save_error=history[2],elapsed_ms=(time.perf_counter()-started)*1000))
            lookup_offset=(time.perf_counter()-started)*1000
            result=self._lookup(query.text,dictset=resources.dictset,conn=resources.conn,
                                context=query.context,online=resources.config.online,
                                clients=resources.config.clients,save=False,on_ready=ready,
                                context_gate=self._context_slot,meaning_gate=self._meaning_slot,
                                context_span=query.span,context_complete=query.context_complete)
            if not self.current(identity):
                return
            if history is None:
                ready(result)
            with self._condition:
                if not self.current(identity):
                    return
                if history[0] and query.span is not None and result.context_meaning is not None:
                    try:
                        matched=enrich_word_context(resources.conn,result.key,token,query.context,query.span,
                                                    contextual.ContextResult(result.context_meaning,result.meaning_provider))
                        result.meaning_save_error=not matched
                    except (sqlite3.Error,OSError,ValueError):
                        result.meaning_save_error=True
            value=snapshot(result)
            value.saved,value.count=history[:2]
            self._emit(Event(identity,'context',result=value,context=query.context,**origin,
                             save_error=history[2],elapsed_ms=(time.perf_counter()-started)*1000))
        except (AppError,platform.PlatformError,ocr.OcrError) as error:
            reason=error.reason
            if isinstance(error,ocr.OcrError) and reason not in ('missing_tesseract','missing_eng','missing_pyqt6'):
                reason='ocr_timeout' if reason=='timeout' else 'ocr_failed'
            self._emit(Event(identity,'error',**origin,error=reason,elapsed_ms=(time.perf_counter()-started)*1000))
        except Exception:
            self._emit(Event(identity,'error',**origin,error='lookup_failed',elapsed_ms=(time.perf_counter()-started)*1000))
