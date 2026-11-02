"""One thread owns lookup resources; request identities guard history and UI."""
from contextlib import contextmanager, ExitStack
from dataclasses import dataclass, field, replace
import sqlite3
import math
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
class Scene:
    session_id: int
    source: Frozen


@dataclass(frozen=True)
class Query:
    text: str
    context: str | None
    timings: dict = field(default_factory=dict)
    span: tuple[int, int] | None = None
    context_complete: bool = False
    selection_box: tuple | None = None


@dataclass
class Resources:
    config: config.Config
    dictset: object = None
    conn: object = None
    save_error: str | None = None
    reload_error: str | None = None


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
    span: tuple[int, int] | None = None
    reload_revision: int | None = None
    scene: Scene | None = None
    selection_box: tuple | None = None


class Source:
    def __init__(self, env=None):
        self.env=env
        self.consumed=None

    def freeze(self,snapshot=None):
        if self.env is None:
            self.env=platform.session_env()
        try:
            point=snapshot.point if snapshot is not None else platform.cursor_position(self.env)
        except platform.PlatformError as error:
            if error.reason=='gnome_extension_unavailable':raise AppError('missing_gnome_extension') from None
            raise AppError('missing_kdotool' if error.reason=='missing_command' else 'cursor_failed') from None
        try:
            monitor=snapshot.monitor if snapshot is not None else platform.monitor_at(point,platform.monitors(self.env))
            available=snapshot.available if snapshot is not None else platform.work_area(self.env,monitor)
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
            frame=snapshot.image() if snapshot is not None else capture.capture_monitor(monitor,self.env,'screenshot2')
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
                     dict(timings,capture=source.image.elapsed_ms),span,selection.context_complete,selection.box)


@contextmanager
def _resources():
    cfg=config.load()
    dictionaries=conn=None
    error=dictionary_error=None
    try:
        try:
            dictionaries=dicts.open_all(cfg)
        except Exception:
            dictionary_error='unavailable'
        try:
            conn=open_store()
            conn.execute('PRAGMA busy_timeout=50')
        except Exception:
            if conn is not None:
                conn.close()
                conn=None
            error='unavailable'
        yield Resources(cfg,dictionaries,conn,error,dictionary_error)
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
        self._scene=None
        self._reload_revision=0
        self._reload_pending=None
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

    def enqueue(self,identity,snapshot=None):
        with self._condition:
            if self.current(identity):
                self._scene=None
                self._pending=(identity,self._started,snapshot,None)
                self._condition.notify()

    def enqueue_scene(self,identity,snapshot=None):
        with self._condition:
            if not self.current(identity):return False
            self._scene=None
            self._pending=(identity,self._started,snapshot,True)
            self._condition.notify()
            return True

    def select_scene(self,identity,session_id,point):
        with self._condition:
            if not self.current(identity) or self._scene is None or session_id!=self._scene.session_id:
                return False
            monitor=self._scene.source.monitor
            if (not isinstance(point,(tuple,list)) or len(point)!=2 or
                not all(isinstance(n,(int,float)) and not isinstance(n,bool) and math.isfinite(n) for n in point) or
                not (monitor.x<=point[0]<monitor.x+monitor.width and monitor.y<=point[1]<monitor.y+monitor.height)):
                return False
            self._pending=(identity,self._started,None,(session_id,tuple(point)))
            self._condition.notify()
            return True

    def current(self,identity):
        with self._condition:
            return identity is not None and identity==self._generation and not self._stopping

    def request_reload(self):
        """Invalidate lookup work and asynchronously apply the latest pending revision.

        Acknowledgements use stage='reload' and reload_revision, independently
        of lookup IDs. A newer pending request may coalesce an unopened one.
        """
        with self._condition:
            if self._stopping:
                return None
            self._generation+=1
            self._pending=None
            self._reload_revision+=1
            self._reload_pending=self._reload_revision
            self._condition.notify()
            return self._reload_revision

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

    def _ack_reload(self,revision,error):
        with self._condition:
            if not self._stopping:
                self._publish(Event(self._generation,'reload',error=error,reload_revision=revision))

    def _run(self):
        try:
            with ExitStack() as owned:
                resources=None
                try:
                    resources=owned.enter_context(self._resources())
                except Exception:
                    pass  # Keep the worker available for an explicit reload retry.
                while True:
                    with self._condition:
                        self._condition.wait_for(lambda:self._stopping or self._pending is not None or self._reload_pending is not None)
                        if self._stopping:
                            return
                        revision=self._reload_pending
                        if revision is not None:
                            self._reload_pending=None
                        else:
                            identity,started,*snapshots=self._pending
                            self._pending=None
                    if revision is not None:
                        resources=None
                        error=None
                        try:
                            owned.close()
                            resources=owned.enter_context(self._resources())
                            if resources.reload_error or resources.save_error:
                                raise AppError('reload_failed')
                        except Exception:
                            resources=None
                            error='reload_failed'
                            try:
                                owned.close()
                            except Exception:
                                pass
                        self._ack_reload(revision,error)
                    elif resources is None:
                        snapshots.clear()
                        self._emit(Event(identity,'error',error='reload_failed' if self._reload_revision else 'worker_failed'))
                    else:
                        self._process(identity,started,resources,snapshots)
        except Exception:
            # Last-resort boundary: never print a private worker traceback.
            with self._condition:
                identity=self._generation
            self._emit(Event(identity,'error',error='worker_failed'))

    def _process(self,identity,started,resources,snapshots):
        origin={}
        try:
            scene_request=snapshots.pop()
            snapshot=snapshots.pop()
            if not self.current(identity):
                return
            if isinstance(scene_request,tuple):
                with self._condition:
                    if self._scene is None or self._scene.session_id!=scene_request[0]:return
                    source=replace(self._scene.source,point=scene_request[1])
            else:
                source=self._source.freeze(snapshot) if snapshot is not None else self._source.freeze()
            snapshot=None  # Release raw pixels before OCR/translation; the caller's holder is empty.
            origin=dict(point=source.point,monitor=source.monitor,mode=source.mode,available=source.available)
            if not self.current(identity):
                return
            if scene_request is True and source.mode=='ocr':
                image=source.image
                if (not isinstance(image,capture.Capture) or not isinstance(image.png,bytes) or
                    not 0<len(image.png)<=capture.MAX_PNG or
                    not all(isinstance(n,int) and not isinstance(n,bool) and 0<n<=16384 for n in (image.width,image.height)) or
                    image.width*image.height>64_000_000):
                    raise AppError('capture_failed')
                with self._condition:
                    if not self.current(identity):return
                    self._scene=Scene(identity,source)
                    self._emit(Event(identity,'scene',scene=self._scene,**origin,
                                     elapsed_ms=(time.perf_counter()-started)*1000))
                image=None
            self._emit(Event(identity,'frozen',**origin,elapsed_ms=(time.perf_counter()-started)*1000))
            query=self._source.resolve(source,resources.dictset)
            origin['selection_box']=query.selection_box
            primary=source if source.mode=='primary' else None
            source=None  # Pixel storage never crosses the GUI signal boundary.
            if not self.current(identity):
                return
            history=None
            token=uuid.uuid4().hex
            enrichment_attempted=False
            enrichment_error=False
            def snapshot(result):
                timings=dict(result.timings,**query.timings)
                for key in ('first_useful','meaning_ready'):
                    if timings.get(key,0)>0:
                        timings[key]+=lookup_offset
                return replace(result,timings=timings)
            def enrich(result):
                nonlocal enrichment_attempted,enrichment_error
                if history[0] and query.span is not None and result.context_meaning is not None:
                    if not enrichment_attempted:
                        enrichment_attempted=True
                        try:
                            matched=enrich_word_context(resources.conn,result.key,token,query.context,query.span,
                                                        contextual.ContextResult(result.context_meaning,result.meaning_provider))
                            enrichment_error=not matched
                        except (sqlite3.Error,OSError,ValueError):
                            enrichment_error=True
                    result.meaning_save_error=enrichment_error
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
                    enrich(result)
                    value=snapshot(result)
                    value.saved,value.count=history[:2]
                self._emit(Event(identity,'ready',result=value,context=query.context,span=query.span,**origin,
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
                enrich(result)
            value=snapshot(result)
            value.saved,value.count=history[:2]
            self._emit(Event(identity,'context',result=value,context=query.context,span=query.span,**origin,
                             save_error=history[2],elapsed_ms=(time.perf_counter()-started)*1000))
        except (AppError,platform.PlatformError,ocr.OcrError) as error:
            reason=error.reason
            if isinstance(error,ocr.OcrError) and reason not in ('missing_tesseract','missing_eng','missing_pyqt6'):
                reason='ocr_timeout' if reason=='timeout' else 'ocr_failed'
            self._emit(Event(identity,'error',**origin,error=reason,elapsed_ms=(time.perf_counter()-started)*1000))
        except Exception:
            self._emit(Event(identity,'error',**origin,error='lookup_failed',elapsed_ms=(time.perf_counter()-started)*1000))
