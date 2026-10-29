"""Opt-in numeric telemetry. Internal presentation is never compositor proof.

run_id is a per-interpreter random correlation value, NOT kernel process start.
External observers separately record /proc start ticks and actual visible frames.
"""
import json
import math
import os
import secrets
import sys
import time

STAGES={'trigger':1,'queue':2,'useful_ready':3,'present':4,'meaning_ready':5,'error':6}
FIELDS=frozenset(('elapsed_ms','engine_ms','useful','meaning_cache','classify','dicts','cache','online',
                  'context','db','total','first_useful','meaning_ready','prepare_image','ocr','select',
                  'capture','open_dicts','open_db','compound'))
_RUN_ID=secrets.randbits(52) or 1


def _number(value,limit=(1<<63)-1):
    return type(value) in (int,float) and 0<=value<=limit and math.isfinite(value)


def _enabled(value):
    return os.environ.get('LOOKUP_TIMING')=='1' if value is None else value is True


class Sink:
    def __init__(self,*,enabled=None,stream=None,clock=None):
        self.enabled=enabled
        self.stream=stream
        self.clock=clock or time.monotonic_ns
        self.pid=os.getpid()
        self.run_id=_RUN_ID

    def emit(self,stage,request,*,at_ns=None,**fields):
        if not _enabled(self.enabled):return False
        if (not isinstance(stage,str) or stage not in STAGES or type(request) is not int or not 0<request<(1<<63)
                or not set(fields)<=FIELDS or not all(_number(value,1e12) for value in fields.values())):
            return False
        timestamp=self.clock() if at_ns is None else at_ns
        if type(timestamp) is not int or not _number(timestamp):return False
        record=dict(pid=self.pid,run=self.run_id,request=request,stage=STAGES[stage],mono_ns=timestamp,**fields)
        try:
            (self.stream or sys.stderr).write('lookup-timing:'+json.dumps(record,separators=(',',':'),sort_keys=True)+'\n')
        except (OSError,ValueError):return False
        return True


def print_cli(timings,*,enabled=None,stream=None):
    """Retain the existing CLI line format for known measured fields only."""
    if (not _enabled(enabled) or not isinstance(timings,dict) or not set(timings)<=FIELDS
            or not all(_number(value,1e12) for value in timings.values())):
        return False
    try:
        (stream or sys.stderr).write('timing: '+' '.join(f'{key}={value:.3f}ms' for key,value in timings.items())+'\n')
    except (OSError,ValueError):return False
    return True


def useful(result):
    if result is None or result.kind=='invalid':return False
    if isinstance(result.translation,str) and result.translation.strip():return True
    if result.online is not None and isinstance(result.online.main,str) and result.online.main.strip():return True
    for article in result.articles:
        if isinstance(article.text,str) and article.text.strip():return True
        if any(isinstance(term,str) and term.strip() for _,terms in article.senses for term in terms):return True
    return False
