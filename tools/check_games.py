"""Strict actual-game evidence and owned Wesnoth native observation."""
import time

from tools.check_hardening import EvidenceError,physical_latency,_require,_hash,_integer


def tap(original,observer,on_error=lambda unused:None):
    """Observe original returned objects without changing payload or error behavior."""
    def wrapped(*args,**kwargs):
        start=time.monotonic_ns();result=original(*args,**kwargs);end=time.monotonic_ns()
        try:observer(result,start,end)
        except Exception as error:on_error(type(error).__name__)
        return result
    return wrapped


def game_report(data):
    try:
        _require(data.get('name')=='The Battle for Wesnoth' and isinstance(data.get('version'),str) and data['version'],'game')
        package=data['package'];process=data['process'];renderer=data['renderer'];window=data['window']
        _require(data.get('source_verified') is True and package.get('source')=='official_arch' and
            package.get('name')=='wesnoth' and package.get('repository')=='extra' and package.get('signature_verified') is True
            and _hash(package.get('archive_sha256')) and isinstance(package.get('version'),str),'package')
        _require(_integer(process.get('pid'),1) and _integer(process.get('start'),1) and process.get('uid')==1001
            and process.get('executable')=='/usr/bin/wesnoth','process')
        _require(isinstance(renderer.get('name'),str) and renderer['name'] and renderer.get('observed') is True
            and _hash(renderer.get('log_sha256')),'renderer')
        _require(data.get('mode')=='fullscreen' and window.get('fullscreen') is True and window.get('observed') is True
            and window.get('pid')==process['pid'] and window.get('id') and window.get('rect')==window.get('screen'),'fullscreen')
        rows=data['routes'];_require(isinstance(rows,list) and len(rows)>=2,'routes')
        hashes=set();contexts=set();latencies=[]
        for index,row in enumerate(rows,1):
            source=row['source'];overlay=row['overlay'];closed=row['dismissal'];play=row['gameplay'];timing=row['timing']
            latency=physical_latency(timing)
            _require(row.get('sequence')==index and row.get('scene')=='tutorial_map_dialogue' and
                row.get('game_pid')==process['pid'] and row.get('game_start')==process['start'] and
                row.get('window_id')==window['id'] and row.get('game_active_before') is True,'game_source')
            _require(source.get('kind')=='actual_game' and source.get('mode')=='ocr' and source.get('backend')=='screenshot2'
                and _hash(source.get('sha256')) and source.get('unchanged_objects') is True,'source')
            _require(timing['input_ns']<=source['capture_start_ns']<=source['capture_end_ns']<=timing['first_visible_end_ns'],'fresh_source')
            _require(isinstance(source.get('word'),str) and source['word'] and source.get('query')==source['word']
                and isinstance(source.get('context'),str) and source['word'].casefold() in source['context'].casefold()
                and _integer(source.get('visual_lines'),2),'ocr')
            x,y=source['cursor'];left,top,width,height=source['word_rect']
            _require(width>0 and height>0 and left<=x<=left+width and top<=y<=top+height,'target')
            _require(overlay.get('useful') is True and overlay.get('loading') is False and overlay.get('error') is False
                and overlay.get('current_word')==source['word'] and overlay.get('sha256')==timing['frame_sha256']
                and overlay.get('identity')==timing['frame_identity'],'overlay')
            _require(closed.get('physical') is True and closed.get('released') is True and closed.get('closed') is True
                and closed['at_ns']>=timing['first_visible_end_ns'],'dismiss')
            _require(play.get('physical') is True and play.get('game_active') is True and play.get('game_pid')==process['pid']
                and play.get('game_start')==process['start'] and isinstance(play.get('action'),str) and play['action']
                and play['input_ns']>=closed['at_ns'] and play.get('observed_change') is True
                and _hash(play.get('before_sha256')) and _hash(play.get('after_sha256'))
                and play['before_sha256']!=play['after_sha256'],'resumed_gameplay')
            hashes.add(source['sha256']);contexts.add(source['context']);latencies.append(latency)
        _require(len(hashes)>=2 and len(contexts)>=2,'changed_scenes')
        return dict(passed=True,game01_complete=False,routes=len(rows),latencies_ms=latencies)
    except (EvidenceError,KeyError,TypeError,ValueError,AttributeError):return dict(passed=False,game01_complete=False)
