"""Phase 8 pure evidence oracles. No VM, input, capture or network operations.

All timestamps are integer nanoseconds. A receipt timestamp is diagnostic only.
These checks validate evidence structure; native drivers must supply real proofs.
"""
import math
import re
import statistics

PERFORMANCE_GROUPS={'cold':3,'warm_distinct':18,'repeat':9}
GAME_GATES=frozenset(('actual_process','fullscreen_verified','physical_hotkey','fresh_capture','real_ocr',
                     'correct_word','useful_overlay','dismissed','control_returned','repeated_calls',
                     'changing_frames','post_dismiss_gameplay'))
BURST_GATES=frozenset(('daemon_alive','subsequent_lookup','no_owned_children','fresh_final'))
PRIVACY_GATES=frozenset(('owned_profile','observed_before_after','scanned_tmp','scanned_runtime','scanned_db_directory'))
FAULT_GATES=frozenset(('bounded','specific_status','daemon_alive','recovered','counts_intact','private_errors'))


class EvidenceError(ValueError):
    pass


def _require(condition,reason='invalid_record'):
    if not condition:raise EvidenceError(reason)


def _integer(value,minimum=0):
    return type(value) is int and minimum<=value<(1<<63)


def _number(value):
    return type(value) in (int,float) and 0<=value<1e15 and math.isfinite(value)


def _hash(value):
    return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None


def strict_gates(gates,required):
    return isinstance(gates,dict) and set(required)<=set(gates) and all(value is True for value in gates.values())


def summarize(values):
    values=list(values)
    _require(all(_number(value) for value in values),'statistics')
    ordered=sorted(values)
    return dict(count=len(values),median_ms=statistics.median(ordered) if ordered else None,
                p95_ms=ordered[math.ceil(.95*len(ordered))-1] if ordered else None)


def _identity(row):
    identity=tuple(row[key] for key in ('pid','process_start','run','request'))
    _require(all(_integer(value,1) for value in identity),'identity')
    _require(row.get('process_start_source')=='proc_stat','identity')
    return identity


def physical_latency(row):
    """Input-to-first-useful-capture END upper bound; never receipt-to-frame."""
    try:
        _require(isinstance(row,dict) and row.get('mode')=='native' and row.get('status')=='success')
        _require(row.get('physical') is True and row.get('released') is True)
        identity=_identity(row)
        _require(row.get('frame_identity') in (list(identity),identity),'identity')
        _require(_hash(row.get('frame_sha256')) and row.get('observed') is True
                 and row.get('fresh') is True and row.get('useful_verified') is True,'visibility')
        _require(all(row.get(key) is False for key in ('loading','error_card','previous_card')),'visibility')
        start=row['input_ns']
        last=row['last_not_visible_ns']
        capture_start=row['first_visible_start_ns']
        end=row['first_visible_end_ns']
        _require(all(_integer(value) for value in (start,last,capture_start,end)),'clock')
        _require(last<=capture_start<=end and start<=end,'clock')
        _require(row.get('frame_clock')==row.get('clock'),'clock')
        if row.get('origin')=='kernel_evdev':
            _require(row.get('clock')=='guest_monotonic' and row.get('kernel_clock_verified') is True
                     and row.get('clock_ioctl_verified') is True,'clock')
            _require(_integer(row.get('trigger_ns')) and start<=row['trigger_ns']<=end,'clock')
            if 'receipt_ns' in row:_require(_integer(row['receipt_ns']) and row['receipt_ns']>=start,'clock')
        elif row.get('origin')=='host_before_vbox':
            _require(row.get('clock')=='host_monotonic' and row.get('before_dispatch') is True,'clock')
            _require(_integer(row.get('dispatch_ns')) and start<=row['dispatch_ns']<=end,'clock')
        else:raise EvidenceError('clock')
        return (end-start)/1e6
    except (KeyError,TypeError,OverflowError):
        raise EvidenceError('invalid_record') from None


def performance_report(rows):
    if not isinstance(rows,list):return dict(passed=False,attempts=0,successful=0,errors=['invalid_record'])
    values=[];errors=[];identities=set();groups={key:[] for key in PERFORMANCE_GROUPS}
    cases={key:[] for key in PERFORMANCE_GROUPS};cold_processes=set();warm_processes=set();uncertainties=[]
    for index,row in enumerate(rows,1):
        try:
            _require(isinstance(row,dict) and type(row.get('attempt')) is int and type(row.get('input_sequence')) is int
                     and row['attempt']==index and row['input_sequence']==index,'attempts')
            latency=physical_latency(row)
            identity=_identity(row)
            _require(identity not in identities,'identity');identities.add(identity)
            group=row.get('group');_require(isinstance(group,str) and group in groups and _integer(row.get('case'),1),'workload')
            groups[group].append(latency);cases[group].append(row['case']);values.append(latency)
            (cold_processes if group=='cold' else warm_processes).add(identity[:3])
            uncertainties.append((row['first_visible_end_ns']-max(row['input_ns'],row['last_not_visible_ns']))/1e6)
        except EvidenceError as error:errors.append(dict(attempt=index,reason=str(error)))
    stats=summarize(values)
    workload=(all(len(groups[key])==count for key,count in PERFORMANCE_GROUPS.items())
              and len(set(cases['warm_distinct']))==18 and set(cases['repeat'])<=set(cases['warm_distinct'])
              and len(cold_processes)==3 and len(warm_processes)==1 and warm_processes<=cold_processes)
    return dict(passed=not errors and len(rows)==30 and workload and stats['median_ms'] is not None and stats['median_ms']<=1500,
                attempts=len(rows),successful=len(values),errors=errors,**stats_without_count(stats),
                groups={key:summarize(values) for key,values in groups.items()},
                max_uncertainty_ms=max(uncertainties) if uncertainties else None,records=rows)


def stats_without_count(stats):
    return {key:value for key,value in stats.items() if key!='count'}


def online_report(rows):
    """Optional up-to-three uncached/cache physical requests, never fake seeds."""
    uncached=[];cached=[];seeds=set();identities=set();reasons={};errors=[];counts={'uncached':0,'cache':0}
    if not isinstance(rows,list):rows=[];errors.append('invalid_record')
    for index,row in enumerate(rows):
        try:
            _require(isinstance(row,dict) and row.get('kind') in ('uncached','cache'))
            kind=row['kind'];counts[kind]+=1
            _require(row.get('mode')=='native' and row.get('physical') is True and row.get('released') is True)
            if row.get('status')=='success':
                latency=physical_latency(row)
                identity=_identity(row);_require(identity not in identities,'identity');identities.add(identity)
                if kind=='uncached':
                    _require(row.get('from_cache') is False and _integer(row.get('case'),1))
                    seeds.add(row['case']);uncached.append(latency)
                else:
                    _require(row.get('from_cache') is True and row.get('seeded') is True and row.get('case') in seeds)
                    cached.append(latency)
            else:
                reason=row.get('reason')
                _require(kind=='uncached' and row.get('status')=='error'
                         and reason in ('blocked','timeout','no_network','bad_response','not_found'))
                reasons[reason]=reasons.get(reason,0)+1
        except (EvidenceError,TypeError):errors.append(index)
    return dict(complete=not errors and counts['uncached']<=3 and counts['cache']<=3,
                attempts=len(rows),uncached=summarize(uncached),cache=summarize(cached),reasons=reasons,errors=errors,records=rows)


def meaning_report(rows):
    live=[];cached=[];reasons={};cases=set();attempts=0;errors=[]
    if not isinstance(rows,list):rows=[];errors.append('invalid_record')
    for index,row in enumerate(rows):
        try:
            _require(isinstance(row,dict) and row.get('mock') is False)
            if row.get('kind')=='cache':
                _require(row.get('cached') is True and row.get('live') is False and row.get('seeded') is True)
                _require(row.get('status')=='success' and _number(row.get('duration_ms')))
                cached.append(row['duration_ms']);continue
            attempts+=1
            _require(row.get('kind')=='live' and row.get('cached') is False and row.get('live') is True)
            _require(_integer(row.get('case')) and row['case'] not in cases,'workload');cases.add(row['case'])
            if row.get('status')=='success':
                _require(row.get('meaning_verified') is True and _number(row.get('duration_ms')))
                live.append(row['duration_ms'])
            else:
                reason=row.get('reason')
                _require(row.get('status')=='error' and reason in ('blocked','timeout','no_network','bad_response','not_found'))
                reasons[reason]=reasons.get(reason,0)+1
        except EvidenceError:errors.append(index)
    return dict(complete=not errors and attempts==6,attempts=attempts,successful=len(live),
                success_fraction=len(live)/attempts if attempts else 0,**stats_without_count(summarize(live)),
                reasons=reasons,cache=summarize(cached),errors=errors,records=rows)


def protocol():
    """Fixed before measurements; callers cannot supply looser thresholds."""
    return dict(warmup=20,completions=320,resource_every=10,rss_absolute_bytes=16<<20,rss_fraction=.15,
                late_absolute_bytes=4<<20,late_fraction=.05,cooldown_ms=5000,fd_allowance=4,thread_allowance=2)


def stability_report(data):
    result=dict(passed=False)
    try:
        rules=protocol()
        _require(isinstance(data,dict) and data.get('mode')=='native' and data.get('protocol')==rules,'protocol')
        warmup,completed=data['warmup'],data['completions']
        _require(isinstance(warmup,list) and len(warmup)==20 and isinstance(completed,list) and len(completed)==320,'workload')
        identities=set();processes=set()
        for index,row in enumerate(warmup+completed,1):
            _require(type(row.get('attempt')) is int and type(row.get('input_sequence')) is int
                     and row['attempt']==index and row['input_sequence']==index,'attempts')
            physical_latency(row);identity=_identity(row)
            _require(identity not in identities,'identity');identities.add(identity);processes.add(identity[:3])
        _require(len(processes)==1,'identity')
        resources=data['resources'];cooldown=data['cooldown']
        _require(isinstance(resources,list) and [row.get('after') for row in resources]==list(range(10,321,10)),'resources')
        _require(cooldown.get('after')==320 and _number(cooldown.get('idle_ms')) and cooldown['idle_ms']>=5000,'resources')
        for row in resources+[cooldown]:
            _require(tuple(row['identity'])==next(iter(processes)) and row.get('observed') is True,'resources')
            _require(all(_integer(row.get(key),1) for key in ('rss_bytes','threads','fds')) and row.get('owned_children')==[],'resources')
        early=statistics.median(row['rss_bytes'] for row in resources[:6])
        late=statistics.median(row['rss_bytes'] for row in resources[-6:])
        allowance=max(16<<20,early*.15);trend_allowance=max(4<<20,early*.05)
        trend=statistics.median(row['rss_bytes'] for row in resources[-3:])-statistics.median(row['rss_bytes'] for row in resources[-6:-3])
        result.update(early_rss_bytes=early,late_rss_bytes=late,rss_allowance_bytes=allowance,
                      late_trend_bytes=trend,cooldown_rss_bytes=cooldown['rss_bytes'])
        _require(late<=early+allowance and trend<=trend_allowance and cooldown['rss_bytes']<=late+trend_allowance,'rss')
        _require(cooldown['fds']<=max(row['fds'] for row in resources[:6])+4
                 and cooldown['threads']<=max(row['threads'] for row in resources[:6])+2,'resources')
        _require(data.get('history_delta')==320 and type(data['history_delta']) is int
                 and type(data.get('enrichment_extra_count')) is int and data['enrichment_extra_count']==0
                 and data.get('integrity')=='ok','count')
        result['passed']=True
    except (EvidenceError,KeyError,TypeError,AttributeError,StopIteration) as error:
        result['error']=str(error) if isinstance(error,EvidenceError) else 'invalid_record'
    return result


def burst_report(data):
    try:
        _require(isinstance(data,dict) and data.get('mode')=='native')
        identity=data['identity']
        _require(isinstance(identity,(tuple,list)) and len(identity)==3 and all(_integer(value,1) for value in identity)
                 and data.get('process_start_source')=='proc_stat','identity')
        inputs=data['inputs'];accepted=data['accepted_requests']
        _require(isinstance(inputs,list) and len(inputs)==10 and isinstance(accepted,list) and accepted,'burst')
        for index,row in enumerate(inputs,1):
            _require(type(row.get('sequence')) is int and row['sequence']==index and row.get('physical') is True and row.get('released') is True
                     and _integer(row.get('request'),1),'burst')
        requests=[row['request'] for row in inputs]
        _require(all(_integer(value,1) for value in accepted) and len(set(requests))==10
                 and requests==sorted(requests) and len(set(accepted))==len(accepted) and set(accepted)<=set(requests),'burst')
        _require(data.get('final_request')==requests[-1] and requests[-1] in accepted,'burst')
        _require(data.get('final_identity')==list(identity)+[requests[-1]] and _hash(data.get('final_frame_sha256')),'visibility')
        _require(type(data.get('history_delta')) is int and data['history_delta']==len(accepted)
                 and type(data.get('enrichment_extra_count')) is int and data['enrichment_extra_count']==0
                 and data.get('integrity')=='ok','count')
        _require(strict_gates(data.get('gates'),BURST_GATES),'gates')
        return dict(passed=True,inputs=10,accepted=len(accepted))
    except (EvidenceError,KeyError,TypeError,AttributeError):return dict(passed=False)


def privacy_report(data):
    try:
        _require(data.get('mode')=='native' and strict_gates(data.get('gates'),PRIVACY_GATES))
        for name in ('primary','clipboard','klipper'):
            before,after=data[name+'_before'],data[name+'_after']
            _require(_hash(before) and before==after)
        _require(data.get('capture_files')==[])
        return dict(passed=True)
    except (EvidenceError,KeyError,TypeError,AttributeError):return dict(passed=False)


def faults_report(rows):
    if not isinstance(rows,list) or len(rows)!=3:return dict(passed=False)
    try:
        _require({row['fault'] for row in rows}=={'network','dictionary','capture'})
        for row in rows:
            _require(row.get('mode')=='native' and strict_gates(row.get('gates'),FAULT_GATES))
            _require(row.get('kind') in ('real','injected') and (row['fault']=='capture' or row['kind']=='real'))
        return dict(passed=True)
    except (EvidenceError,KeyError,TypeError,AttributeError):return dict(passed=False)


def games_report(rows):
    try:
        _require(isinstance(rows,list) and len(rows)==2,'game')
        names=set();relative=False;multiline=False
        for row in rows:
            _require(all(isinstance(row.get(key),str) and row[key].strip() for key in ('name','version','renderer')),'game')
            names.add(row['name'])
            _require(row.get('mode')=='fullscreen' and row.get('evidence')=='actual_game' and row.get('source_verified') is True
                     and _integer(row.get('pid'),1) and strict_gates(row.get('gates'),GAME_GATES),'game')
            _require(_hash(row.get('frame_sha256')) and _hash(row.get('post_dismiss_sha256'))
                     and row['frame_sha256']!=row['post_dismiss_sha256'],'game')
            multiline|=row.get('multiline') is True
            relative|=(row.get('relative_mouse') is True and row.get('pointer_locked') is True
                       and row.get('relative_gameplay_verified') is True)
        return dict(passed=len(names)==2 and relative and multiline)
    except (EvidenceError,KeyError,TypeError,AttributeError):return dict(passed=False)


def carry_phase7(raw):
    _require(isinstance(raw,dict) and raw.get('passed') is False
             and isinstance(raw.get('cleanup'),dict) and raw['cleanup'].get('original_preserved') is False,'historical')
    return dict(raw=raw,actor='unknown',scope='historical_preservation_exception')
