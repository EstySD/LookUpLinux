"""Phase 8 strict oracles and explicitly selected owned-clone native scenarios.

All timestamps are integer nanoseconds. A receipt timestamp is diagnostic only.
Imports and pure checks perform no VM operations; native CLI modes supply proofs.
"""
import math
import re
import statistics


def optical_match(text,word,body):
    """Match actual cropped popup OCR, not numeric show/paint telemetry."""
    tokens=re.findall(r"[\w]+",text.casefold())
    matched=(body.casefold() in tokens if isinstance(body,str) else len(set(body)&set(tokens))>=2)
    return bool(tokens) and tokens[0]==word.casefold() and any('mueller' in token for token in tokens) and matched


def matching_result(result,command):
    return (isinstance(result,dict) and type(command.get('token')) is int and command['token']>0 and
            result.get('attempt')==command['attempt'] and result.get('token')==command['token'] and
            ('request' not in command or result.get('request')==command['request']))


def read_record(path):
    import json
    try:return json.loads(path.read_text())
    except (json.JSONDecodeError,FileNotFoundError):return None


def write_record(path,value):
    import json
    temporary=path.with_name(path.name+'.tmp');temporary.write_text(json.dumps(value));temporary.replace(path)

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


def _archive_hashes(data):
    import hashlib,io,tarfile
    _require(isinstance(data,bytes) and 0<len(data)<=64<<20,'raw_archive')
    values={};total=0
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:*') as archive:
        for member in archive:
            if not member.isfile():continue
            name=member.name.removeprefix('./');total+=member.size
            _require(name not in values and '..' not in name.split('/') and member.size<=64<<20
                and total<=128<<20 and len(values)<512,'archive_inventory')
            values[name]=hashlib.sha256(archive.extractfile(member).read()).hexdigest()
    return values


def _package_member(name):
    if name.startswith('lookup/'):return 'usr/lib/lookup/app/'+name
    return {'packaging/lookup':'usr/bin/lookup',
        'packaging/org.lookup.Linux.desktop':'usr/share/applications/org.lookup.Linux.desktop',
        'packaging/org.lookup.Linux.autostart.desktop':'etc/xdg/autostart/org.lookup.Linux.desktop',
        'packaging/THIRD-PARTY.md':'usr/share/licenses/lookup-linux/THIRD-PARTY.md'}[name]


def _expected_source_inventory():
    """Independent current-repository inventory, matching the fixed staging seam."""
    import hashlib
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    names={path.relative_to(root).as_posix() for path in (root/'lookup').rglob('*')
        if path.is_file() and (path.suffix=='.py' or path.parent==root/'lookup/data' and path.suffix=='.txt')}
    names|={'packaging/lookup','packaging/org.lookup.Linux.desktop',
        'packaging/org.lookup.Linux.autostart.desktop','packaging/THIRD-PARTY.md'}
    _require(all(not (root/name).is_symlink() and (root/name).resolve().is_relative_to(root) for name in names),'unsafe_source')
    return {name:hashlib.sha256((root/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for name in names}


def current_performance_report(rows,receipt,artifacts=None):
    """Use loaded archive/proc/trace bytes, never copied build summary labels."""
    import base64,hashlib,json,tarfile
    report=performance_report(rows)
    try:
        _require(isinstance(artifacts,dict),'raw_build')
        source_bytes=artifacts['source'];package_bytes=artifacts['package']
        source_archive=_archive_hashes(source_bytes);package=_archive_hashes(package_bytes)
        _require(source_archive and all(name.startswith('lookup-source/') for name in source_archive),'source_inventory')
        source={name.removeprefix('lookup-source/'):value for name,value in source_archive.items()}
        _require(source==_expected_source_inventory()
            and all(package.get(_package_member(name))==value for name,value in source.items()),'package_source')
        build=receipt['build'];installed=receipt['installation']
        _require(isinstance(build,dict) and set(build)=={'source_sha256','package_sha256','ocr_sha256'}
            and all(_hash(value) for value in build.values()),'current_build')
        _require(build==dict(source_sha256=hashlib.sha256(source_bytes).hexdigest(),
            package_sha256=hashlib.sha256(package_bytes).hexdigest(),ocr_sha256=source['lookup/ocr.py'])
            and installed['members']==source,'installed_source')
        _require(isinstance(installed['boot_id'],str) and re.fullmatch(r'[0-9a-f-]{36}',installed['boot_id'])
            and _integer(installed['completed_ns'],1),'installation_epoch')
        _require(all(type(receipt.get(key)) is int and receipt[key]==0
            for key in ('stage_exit','build_exit','install_exit')),'build_exit')
        for row in rows:
            raw=artifacts['runtime'][row['runtime_sha256']]
            _require(isinstance(raw,bytes) and hashlib.sha256(raw).hexdigest()==row['runtime_sha256'],'runtime_artifact')
            runtime=json.loads(raw);stat=runtime['stat'];fields=stat.rsplit(') ',1)[1].split()
            pid=int(stat.split(' ',1)[0]);born=int(fields[19]);ticks=runtime['clock_ticks']
            _require(_integer(ticks,1) and pid==row['pid'] and born==row['process_start'] and fields[0]!='Z','runtime_process')
            uid=next(line for line in runtime['status'].splitlines() if line.startswith('Uid:')).split()[1:]
            cmdline=base64.b64decode(runtime['cmdline_base64'],validate=True).rstrip(b'\0').split(b'\0')
            _require(uid==['1001']*4 and cmdline==[b'/usr/bin/python',b'/usr/bin/lookup',b'--app'],'runtime_entrypoint')
            _require(runtime['boot_id']==installed['boot_id'] and runtime['members']==source
                and _integer(runtime['observed_ns'],1) and runtime['observed_ns']>=row['first_visible_end_ns']
                and installed['completed_ns']<=born*1_000_000_000//ticks<=row['trigger_ns'],'runtime_epoch')
            if row['group']=='cold':
                _require(row.get('owner_absent_before_input') is True and row.get('process_born_after_input') is True
                    and born*1_000_000_000//ticks>=row['input_ns'],'cold_runtime_birth')
            trace=[json.loads(line.split(':',1)[1]) for line in runtime['timing_text'].splitlines() if line.startswith('lookup-timing:')]
            events=[event for event in trace if all(event.get(key)==row[key] for key in ('pid','run','request'))]
            triggers=[event for event in events if event.get('stage')==1]
            _require(len(triggers)==1 and triggers[0]['mono_ns']==row['trigger_ns']
                and any(event.get('stage')==4 and event.get('useful')==1 and row['trigger_ns']<=event['mono_ns']<=row['first_visible_end_ns']
                    for event in events),'runtime_trace')
        report.update(source_bound=True,build=dict(build))
    except (EvidenceError,KeyError,TypeError,AttributeError,ValueError,IndexError,StopIteration,tarfile.TarError):
        report.update(passed=False,source_bound=False,source_error='current_source_binding')
    return report


def fallback_stability_report(data):
    """The declared twenty-call changed path, separate from historical 320."""
    try:
        rows=data['completions'];resources=data['resources'];cooldown=data['cooldown']
        _require(len(rows)==20 and len(resources)==20,'workload')
        identities=set();processes=set();retried=0
        for row in rows:
            timing=row['timing'];physical_latency(timing);identity=_identity(timing)
            _require(identity not in identities,'identity');identities.add(identity);processes.add(identity[:3])
            passes=row['ocr_passes'];modes=[item['psm'] for item in passes]
            _require(modes in ([6],[6,11]),'passes')
            for item in passes:
                _require(item.get('returncode')==0 and 'error' not in item and _hash(item.get('input_sha256'))
                    and _hash(item.get('stdout_sha256')) and timing['trigger_ns']<=item['start_ns']<=item['end_ns']<=timing['first_visible_end_ns'],'passes')
            if len(passes)==2:
                _require(passes[0]['input_sha256']==passes[1]['input_sha256'] and passes[0]['end_ns']<=passes[1]['start_ns'],'same_prepared_input')
                retried+=1
        _require(len(processes)==1 and retried>=2,'actual_retry')
        _require([row['after'] for row in resources]==list(range(1,21)) and cooldown['idle_ms']>=5000,'resources')
        for row in resources+[cooldown]:
            _require(tuple(row['identity'])==next(iter(processes)) and row.get('observed') is True
                and row.get('owned_children')==[] and all(_integer(row.get(key),1) for key in ('rss_bytes','threads','fds')),'resources')
        early=statistics.median(row['rss_bytes'] for row in resources[:5]);late=statistics.median(row['rss_bytes'] for row in resources[-5:])
        allowance=max(16<<20,early*.15);trend_allowance=max(4<<20,early*.05)
        _require(max(row['rss_bytes'] for row in resources+[cooldown])-early<=allowance
            and late-early<=allowance and statistics.median(row['rss_bytes'] for row in resources[-5:])-statistics.median(row['rss_bytes'] for row in resources[-10:-5])<=trend_allowance,'rss')
        _require(all(row['fds']<=resources[0]['fds']+4 and row['threads']<=resources[0]['threads']+2 for row in resources+[cooldown]),'handles')
        _require(type(data['history_delta']) is int and data['history_delta']==20 and data['integrity']=='ok','history')
        return dict(passed=True,completions=20,second_pass_completions=retried,early_rss_bytes=early,late_rss_bytes=late,rss_allowance_bytes=allowance)
    except (EvidenceError,KeyError,TypeError,AttributeError,IndexError):return dict(passed=False)


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
        stamps=[row.get('input_ns') for row in inputs]
        _require(all(_integer(stamp,1) for stamp in stamps) and
                 all(20_000_000<=right-left<=100_000_000 for left,right in zip(stamps,stamps[1:])),'burst_cadence')
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


def final_cleanup_report(raw):
    """Require the native, both game and current installation cleanup observations."""
    try:
        native=raw['native'];wesnoth=raw['wesnoth'];doom=raw['doom'];install=raw['installation']['gates']
        checks=dict(
            observers_stopped=native['observer_stopped'] is True and doom['one_shot_observers_finished'] is True and install['fixture_stopped'] is True,
            games_stopped=wesnoth['game_and_instrumented_lookup_stopped'] is True and doom['game_stopped'] is True,
            helpers_stopped=native['helpers_ended_with_guest_shutdown'] is True and doom['lookup_tray_exited'] is True and install['owner_stopped'] is True,
            activation_environment_restored=native['retained_config_restored'] is True and native['environment_script_removed'] is True and install['session_override_restored'] is True,
            network_restored=native['network_restored'] is True,
            dictionary_restored=native['dictionary_restored'] is True,
            layout_restored=native['display_restored'] is True and doom['prior_3d_restored_after_off'] is True,
            input_released=native['input_release_command_succeeded'] is True and wesnoth['keys_released'] is True and doom['keys_released'] is True and install['input_released'] is True,
            clipboard_restored=native['shared_clipboard_restored'] is True and wesnoth['owned_clipboard_fixture_restored'] is True and doom['prior_clipboard_restored_after_off'] is True and install['clipboard_restored'] is True,
            clone_powered_off=install['clone_powered_off'] is True,
            original_powered_off=install['original_powered_off'] is True)
        return dict(passed=all(checks.values()),checks=checks)
    except (KeyError,TypeError,AttributeError):return dict(passed=False,reason='missing_or_invalid_cleanup')


def aggregate_report(data):
    """Recompute the seven groups from raw records; summary booleans never substitute."""
    from tools.check_games import game_report,captured_game_report
    from tools.check_hardening_install import install_report
    reports={}
    checks=(('performance',performance_report,'performance'),('stability',stability_report,'stability'),
        ('burst',burst_report,'burst'),('scales',scales_report,'scales'),('privacy',privacy_report,'privacy'),
        ('faults',faults_report,'faults'),('meaning',meaning_report,'meaning'),('installation',install_report,'installation'),
        ('wesnoth',game_report,'wesnoth'),('captured_game',captured_game_report,'captured_game'))
    for name,check,key in checks:
        try:reports[name]=check(data[key])
        except (KeyError,TypeError,ValueError,AttributeError,IndexError):reports[name]=dict(passed=False,reason='missing_or_invalid_raw')
    negative=data.get('negative_origin_tests',{})
    negative_ok=(negative.get('verified') is True and negative.get('exit')==0 and type(negative.get('count')) is int and negative['count']>0 and
        _hash(negative.get('log_sha256')) and 'tests.test_platform.GeometryTests.test_actual_ratios_and_negative_origins' in negative.get('tests',[]))
    criteria=dict(performance=reports['performance'].get('passed') is True,
        stability_burst=reports['stability'].get('passed') is True and reports['burst'].get('passed') is True,
        geometry=reports['scales'].get('passed') is True and negative_ok,
        privacy_faults=reports['privacy'].get('passed') is True and reports['faults'].get('passed') is True,
        installation=reports['installation'].get('passed') is True,
        games=reports['wesnoth'].get('passed') is True and reports['captured_game'].get('passed') is True,
        live_meaning_observed=reports['meaning'].get('complete') is True)
    try:historical=carry_phase7(data['historical_phase7']);historical_valid=True
    except (EvidenceError,KeyError,TypeError):historical=None;historical_valid=False
    suites=data.get('suites',{})
    suites_ok=set(suites)=={'host','target'} and all(row.get('exit')==0 and type(row.get('count')) is int and row['count']>0
        and _hash(row.get('log_sha256')) for row in suites.values()) and suites['target'].get('skips')==0
    review=data.get('independent',{})
    reviewed=all(review.get(key)=='passed' for key in ('code_review','security_review','verifier'))
    cleanup=final_cleanup_report(data.get('cleanup',{}))
    passed=all(criteria.values()) and historical_valid and suites_ok and reviewed and cleanup['passed']
    return dict(passed=passed,game01_complete=criteria['games'] and reviewed,criteria=criteria,reports=reports,
        suites_valid=suites_ok,independent_complete=reviewed,historical_phase7=historical,
        historical_valid=historical_valid,human_acceptance=False,cleanup=cleanup)


SCENES=(('bank','They waited by the bank of the river.'),('cat','The cat sat beside the chair.'),
    ('dog','The dog ran across the garden.'),('tree','A tall tree stood beside the road.'),
    ('house','They entered the old house together.'),('water','The water flowed through the valley.'),
    ('fire','The fire burned brightly in the night.'),('book','She read the book beside the window.'),
    ('hand','He raised his hand above the table.'),('head','She turned her head toward the door.'),
    ('eye','The bird opened one eye slowly.'),('day','It was a bright day in spring.'),
    ('night','They returned home before night fell.'),('sun','The sun rose above the hills.'),
    ('moon','The moon shone over the quiet town.'),('road','The road crossed a narrow bridge.'),
    ('door','He opened the door very quietly.'),('room','The room was full of warm light.'))


def chronological(rows):
    """Journal transport ordering is not a request chronology guarantee."""
    return sorted(rows,key=lambda row:row['mono_ns'])


def descendant_identities(pid,start,uid,proc=None):
    """Inspect every thread's descendants; races reject evidence rather than hide children."""
    from pathlib import Path
    proc=Path('/proc') if proc is None else Path(proc)
    def read(number):
        _require(_integer(number,1),'process_identity')
        path=proc/str(number)
        owner=path.stat().st_uid
        born=int((path/'stat').read_text().split(') ',1)[1].split()[19])
        children=set()
        for task in (path/'task').iterdir():
            children.update(int(value) for value in (task/'children').read_text().split())
        _require(path.stat().st_uid==owner and int((path/'stat').read_text().split(') ',1)[1].split()[19])==born,'process_race')
        return owner,born,children
    found={}
    def visit(number,expected=None):
        _require(number not in found,'process_cycle')
        owner,born,children=read(number)
        _require(owner==uid and born>0 and (expected is None or born==expected),'process_identity')
        found[number]=dict(pid=number,process_start=born,uid=owner)
        for child in sorted(children):visit(child)
        _require(read(number)==(owner,born,children),'process_race')
    visit(pid,start)
    return [found[number] for number in sorted(found) if number!=pid]


def scales_report(data):
    rows=data.get('records',[])
    complete=len(rows)==4 and {row.get('scale') for row in rows}=={1,1.25,1.5,2}
    return dict(complete=complete,passed=complete and data.get('display_restored') is True and
                all(row.get('passed') is True for row in rows) and not data.get('errors'))


SCENES=(('name','name'),('name','name'))

def guest_probe(continuous=False):
    """First bounded real input/optical probe; production daemon is unmodified."""
    import fcntl,hashlib,json,os,struct,subprocess,sys,time
    from pathlib import Path
    assert os.getuid()==1001 and Path.home()==Path('/home/lookup07')
    root=Path.home()/'.local/state/lookup-fallback-09'
    if continuous:root=root/'series'
    root.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,'/usr/lib/lookup/app')
    from lookup import platform,capture,gui
    env=platform.session_env()
    env.update(XDG_CONFIG_HOME=str(root/'config'),XDG_CACHE_HOME=str(root/'cache'),XDG_DATA_HOME=str(root/'data'),
        LOOKUP_CONFIG=str(root/'config.json'),LOOKUP_DB=str(root/'data/history.db'),LOOKUP_DICTS='/usr/share/lookup/dicts',
        LOOKUP_CACHE=str(root/'cache'),LOOKUP_TIMING='1')
    for key in ('SUDO_UID','SUDO_GID','SUDO_USER','SUDO_COMMAND','PYTHONPATH'):env.pop(key,None);os.environ.pop(key,None)
    os.environ.update(env)
    (root/'config.json').write_text('{"online":false,"shortcut":"Meta+Shift+E","popup_timeout":60}')
    from PyQt6.QtCore import Qt,QTimer
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import QApplication,QWidget,QVBoxLayout,QLabel
    from PyQt6.QtDBus import QDBusConnection,QDBusMessage,QDBus
    application=QApplication([]);application.setDesktopFileName('org.lookup.Linux')
    import signal
    signal.signal(signal.SIGTERM,lambda *_:application.quit())
    window=QWidget();window.setWindowTitle('Public hardening scene')
    window.setWindowFlags(Qt.WindowType.Window|Qt.WindowType.FramelessWindowHint)
    from PyQt6.QtGui import QPixmap
    from PyQt6.QtCore import QPoint
    label=QLabel(window);label.setPixmap(QPixmap('/home/lookup07/fallback-09-source.png'));label.setGeometry(0,0,1280,800)
    window.showFullScreen()
    devices=[path for path in Path('/sys/class/input').glob('event*')
             if (path/'device/name').read_text().strip()=='AT Translated Set 2 keyboard']
    assert len(devices)==1,'exact_keyboard_required'
    device='/dev/input/'+devices[0].name
    descriptor=os.open(device,os.O_RDONLY|os.O_NONBLOCK)
    fcntl.ioctl(descriptor,0x400445a0,struct.pack('i',time.CLOCK_MONOTONIC))
    clock_set=time.monotonic_ns();keys=set();rows=[];pending=None;chord=None;started=time.monotonic()
    log=(root/'daemon.log').open('a')
    daemon=None if continuous else subprocess.Popen(['/usr/bin/lookup','--app'],env=env,cwd='/tmp',stdout=log,stderr=log,start_new_session=True)
    process_start=0 if daemon is None else int(Path('/proc',str(daemon.pid),'stat').read_text().split(') ',1)[1].split()[19])
    (root/'probe-process.json').write_text(json.dumps(dict(observer=os.getpid(),daemon=daemon.pid if daemon else None,start=process_start)))
    monitor=platform.monitors(env)[0];baseline=None;last=None;ready=False;next_capture=0
    command=dict(attempt=1,group='cold',case=1);arm_id=None;settle=started+1;word='bank';body='насыпь';pid=daemon.pid if daemon else 0
    if continuous:
        from lookup import dicts,config
        dictionaries=dicts.open_all(config.Config())
        catalog={}
        try:
            for index,(term,sentence) in enumerate(SCENES,1):
                articles=dictionaries.lookup_exact(term);assert articles,'missing_corpus_word'
                canonical=set(re.findall('[а-яё]{5,}',articles[0].text[:1800].casefold()))
                assert len(canonical)>=2,'missing_corpus_body'
                catalog[index]=dict(word=term,sentence=sentence,body=sorted(canonical))
        finally:dictionaries.close()
        (root/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False))
    def get_popup(owner_pid):
        values=platform.run(['kdotool','search','--pid',str(owner_pid),'--name',gui.TITLE],env).decode().split()
        for uuid in values:
            message=QDBusMessage.createMethodCall('org.kde.KWin','/KWin','org.kde.KWin','getWindowInfo');message.setArguments([uuid])
            reply=QDBusConnection.sessionBus().call(message,QDBus.CallMode.Block,400)
            info=reply.arguments()[0] if reply.arguments() else {}
            if info.get('caption')==gui.TITLE:return info
        return None
    def tick():
        nonlocal baseline,last,ready,pending,chord,next_capture,command,arm_id,settle,word,body,pid,process_start,monitor
        now=time.monotonic_ns()
        if time.monotonic()-started>(3600 if continuous else 120):application.quit();return
        arm=root/'arm.json'
        if continuous and arm.exists():
            value=json.loads(arm.read_text())
            if value.get('token',0)!=arm_id and pending is None:
                command=value;arm_id=value.get('token',0);case=catalog[value['scene']]
                word=case['word'];body=case['body']
                ready=False;settle=time.monotonic()+.3
        try:data=os.read(descriptor,24*64)
        except BlockingIOError:data=b''
        receipt=time.monotonic_ns()
        for offset in range(0,len(data),24):
            seconds,micros,kind,code,value=struct.unpack('llHHI',data[offset:offset+24])
            if kind==0 and code==3:raise EvidenceError('input_overflow')
            if kind!=1 or code not in (18,42,54,125,126):continue
            if value==1:keys.add(code)
            elif value==0:keys.discard(code)
            if ready and code==18 and value==1 and keys.intersection((42,54)) and keys.intersection((125,126)):
                stamp=seconds*1_000_000_000+micros*1000
                pending=dict(input_ns=stamp,receipt_ns=receipt,clock_ioctl_verified=True,
                    kernel_clock_verified=clock_set<=stamp<=receipt,last_not_visible_ns=last,rows_before=len(rows))
                chord=dict(input_ns=stamp,receipt_ns=receipt,token=command.get('token',0),physical=True,released=False)
            if pending:pending['released']=not keys
            if chord is not None and not keys:
                chord.update(released=True,release_ns=seconds*1_000_000_000+micros*1000)
                with (root/'inputs.jsonl').open('a') as output:output.write(json.dumps(chord)+'\n')
                chord=None
        if not ready:
            if continuous and arm_id is None:return
            if time.monotonic()<settle:return
            monitor=platform.monitors(env)[0]
            frame=capture.capture_monitor(monitor,env);baseline=hashlib.sha256(frame.png).hexdigest();last=time.monotonic_ns()
            point=QPoint(733,378)
            physical=platform.image_point((point.x(),point.y()),monitor,(frame.width,frame.height))
            write_record(root/'ready.json',dict(point=[round(value) for value in physical],logical_point=[point.x(),point.y()],
                monitor=monitor.__dict__,pid=pid,attempt=command['attempt'],token=command.get('token',0),clock_ioctl_verified=True,
                device=device,device_name='AT Translated Set 2 keyboard',baseline_sha256=baseline))
            ready=True
        if not pending or now<next_capture:return
        if command.get('verify_count'):
            released=[json.loads(line) for line in (root/'inputs.jsonl').read_text().splitlines()]
            if sum(row.get('token')==command['token'] for row in released)<10:return
        if now-pending['input_ns']>15_000_000_000:
            row=dict(pending,**command,status='error',reason='optical_deadline')
            with (root/'records.jsonl').open('a') as output:output.write(json.dumps(row)+'\n')
            write_record(root/'result.json',row);pending=None;return
        events=[]
        numeric=(root/'daemon.log').read_text()
        if continuous:
            numeric=Path('/home/lookup07/.local/state/lookup-games-08/assaultcube/lookup/daemon.log').read_text()
            if (root/'fault-daemon.log').exists():numeric+='\n'+(root/'fault-daemon.log').read_text()
            with (root/'daemon.log').open('w') as output:
                output.write('\n'.join(line for line in numeric.splitlines() if line.startswith('lookup-timing:'))+'\n')
        for line in numeric.splitlines():
            if line.startswith('lookup-timing:'):
                value=json.loads(line.split(':',1)[1])
                if value['mono_ns']>=pending['input_ns']:events.append(value)
        events=chronological(events)
        triggers=[value for value in events if value['stage']==1]
        if triggers:
            pid=triggers[-1]['pid'];process_start=int(Path('/proc',str(pid),'stat').read_text().split(') ',1)[1].split()[19])
            events=[value for value in events if value['pid']==pid]
        failed=[value for value in events if value['stage']==6 and value['mono_ns']>=pending['input_ns']]
        if failed:
            row=dict(pending,**command,status='error',reason='production_error',pid=pid,request=failed[-1]['request'],run=failed[-1]['run'])
            rows.append(row);(root/'probe-error.json').write_text(json.dumps(row))
            with (root/'records.jsonl').open('a') as output:output.write(json.dumps(row)+'\n')
            write_record(root/'result.json',row);pending=None;return
        if not triggers:return
        useful=[value for value in events if value['stage']==4 and value.get('useful')==1
                and value['request']==triggers[-1]['request'] and value['mono_ns']>=pending['input_ns']]
        if not useful:return
        event=useful[-1];info=get_popup(pid)
        if not info:return
        begin=time.monotonic_ns();frame=capture.capture_monitor(monitor,env);end=time.monotonic_ns()
        image=capture._png_image(frame.png)
        left,top=platform.image_point((info['x'],info['y']),monitor,(frame.width,frame.height))
        right,bottom=platform.image_point((info['x']+info['width'],info['y']+info['height']),monitor,(frame.width,frame.height))
        cropped=capture._encode(image.copy(int(left),int(top),int(right-left),int(bottom-top)))
        optical=subprocess.run(['tesseract','stdin','stdout','-l','eng+rus','--psm','11'],input=cropped,capture_output=True,timeout=5)
        text=optical.stdout.decode('utf-8','replace');matched=optical_match(text,word,body)
        if command.get('verify_count'):
            import sqlite3
            with sqlite3.connect('file:'+'/home/lookup07/.local/state/lookup-games-08/assaultcube/lookup/data/history.db?mode=ro',uri=True) as connection:
                expected_count=connection.execute('SELECT count FROM words WHERE word=?',(word,)).fetchone()[0]
            normalized=text.casefold().translate(str.maketrans({'c':'с','a':'а','e':'е','o':'о','p':'р','u':'и'}))
            footer=re.search(r'искали\s*(\d+)',normalized)
            matched=matched and footer is not None and int(footer[1])==expected_count
        (root/'probe-optical.txt').write_text(text)
        next_capture=time.monotonic_ns()+50_000_000
        if not matched:last=end;return
        (root/'probe-useful.png').write_bytes(frame.png)
        trigger=next(v for v in events if v['request']==event['request'] and v['stage']==1)
        row=dict(pending,**command,input_sequence=command['attempt'],status='success',mode='native',physical=True,
            pid=pid,process_start=process_start,process_start_source='proc_stat',run=event['run'],request=event['request'],
            clock='guest_monotonic',frame_clock='guest_monotonic',origin='kernel_evdev',trigger_ns=trigger['mono_ns'],
            first_visible_start_ns=begin,first_visible_end_ns=end,frame_identity=[pid,process_start,event['run'],event['request']],
            frame_sha256=hashlib.sha256(frame.png).hexdigest(),observed=True,fresh=hashlib.sha256(frame.png).hexdigest()!=baseline,
            useful_verified=True,loading=False,error_card=False,previous_card=False,latency_ms=(end-pending['input_ns'])/1e6,
            monitor=monitor.__dict__,popup_rect=[info[key] for key in ('x','y','width','height')],
            work_area=platform.work_area(env,monitor),actual_cursor=platform.cursor_position(env))
        if command.get('verify_count'):row.update(observed_footer_count=int(footer[1]),expected_count=expected_count)
        offset=time.clock_gettime_ns(time.CLOCK_BOOTTIME)-time.monotonic_ns();tick_ns=1_000_000_000//os.sysconf('SC_CLK_TCK')
        row['process_birth_mono_lower_ns']=process_start*tick_ns-offset-tick_ns
        row['process_born_after_input']=row['process_birth_mono_lower_ns']>pending['input_ns']
        rows.append(row);(root/'probe-result.json').write_text(json.dumps(row))
        with (root/'records.jsonl').open('a') as output:output.write(json.dumps(row)+'\n')
        write_record(root/'result.json',row);pending=None
    def safe_tick():
        nonlocal next_capture
        try:tick()
        except (platform.PlatformError,subprocess.TimeoutExpired) as error:
            diagnostic=dict(error=type(error).__name__,reason=getattr(error,'reason','observer_process_timeout'),
                            attempt=command['attempt'],at_ns=time.monotonic_ns())
            if pending is not None:pending.setdefault('observer_retries',[]).append(diagnostic)
            with (root/'observer-retries.jsonl').open('a') as output:output.write(json.dumps(diagnostic)+'\n')
            next_capture=time.monotonic_ns()+100_000_000
        except Exception as error:
            (root/'observer-error.json').write_text(json.dumps(dict(error=type(error).__name__,attempt=command['attempt'])))
            application.quit()
    timer=QTimer();timer.timeout.connect(safe_tick);timer.start(20)
    try:return application.exec()
    finally:
        os.close(descriptor);log.close()
        if daemon is not None and daemon.poll() is None:
            daemon.terminate()
            try:daemon.wait(4)
            except subprocess.TimeoutExpired:daemon.kill();daemon.wait(2)


def guest_command(encoded):
    """Bounded commands restricted to this owned verification account/profile."""
    import base64,json,os,subprocess,sys,time
    from pathlib import Path
    assert os.getuid()==1001 and Path.home()==Path('/home/lookup07')
    sys.path.insert(0,'/usr/lib/lookup/app')
    from lookup import platform,lifecycle
    env=platform.session_env()
    for key in ('SUDO_UID','SUDO_GID','SUDO_USER','SUDO_COMMAND','PYTHONPATH'):env.pop(key,None);os.environ.pop(key,None)
    os.environ.update(env)
    root=Path.home()/'.local/state/lookup-fallback-09/series';root.mkdir(parents=True,exist_ok=True)
    command=json.loads(base64.b64decode(encoded));action=command['action']
    from PyQt6.QtCore import QCoreApplication
    from PyQt6.QtDBus import QDBusConnection
    application=QCoreApplication([]);bus=QDBusConnection.sessionBus();interface=bus.interface();interface.setTimeout(1200)
    def owner():
        present=interface.isServiceRegistered('org.lookup.Linux')
        pid=interface.servicePid('org.lookup.Linux').value() if present.isValid() and present.value() else 0
        return dict(pid=pid,owner=bool(pid),keys=[lifecycle.key_text(key) for key in lifecycle.inspect_shortcut().keys])
    if action=='owner':return owner()
    if action=='outputs':return [item.__dict__ for item in platform.monitors(env)]
    if action=='scale':
        value=command['value'];_require(value in (1,1.25,1.5,2),'scale')
        monitor=platform.monitors(env)[0]
        subprocess.run(['kscreen-doctor','output.'+monitor.name+'.scale.'+str(value)],env=env,capture_output=True,timeout=5,check=True)
        time.sleep(.5)
        return dict(outputs=[item.__dict__ for item in platform.monitors(env)])
    if action=='frame':
        import hashlib
        result=read_record(root/'result.json');_require(matching_result(result,command),'frame_identity')
        png=(root/'probe-useful.png').read_bytes();_require(hashlib.sha256(png).hexdigest()==result['frame_sha256'],'frame_hash')
        return dict(png_base64=base64.b64encode(png).decode(),sha256=result['frame_sha256'])
    if action=='last-trigger':
        pid=owner()['pid'];deadline=time.monotonic()+4
        while time.monotonic()<deadline:
            child=subprocess.run(['journalctl','--user','-b','--no-pager','-o','cat','-g','^lookup-timing:', '-n','1000'],
                env=env,capture_output=True,text=True,timeout=3)
            records=[json.loads(line.split(':',1)[1]) for line in child.stdout.splitlines() if line.startswith('lookup-timing:')]
            matching=chronological(row for row in records if row['pid']==pid and row['stage']==1 and row['request']>command.get('after',0))
            if matching:return matching[-1]
            time.sleep(.03)
        raise TimeoutError('trigger_deadline')
    if action=='trace':
        pid=owner()['pid']
        child=subprocess.run(['journalctl','--user','-b','--no-pager','-o','cat','-g','^lookup-timing:', '-n','1000'],
            env=env,capture_output=True,text=True,timeout=3)
        rows=[json.loads(line.split(':',1)[1]) for line in child.stdout.splitlines() if line.startswith('lookup-timing:')]
        return chronological(row for row in rows if row['pid']==pid and row['mono_ns']>=command.get('since_ns',0))
    if action=='inputs':
        deadline=time.monotonic()+4
        while time.monotonic()<deadline:
            rows=[]
            for line in (root/'inputs.jsonl').read_text().splitlines():
                try:row=json.loads(line)
                except json.JSONDecodeError:continue
                if row.get('token')==command['token']:rows.append(row)
            if len(rows)>=command['count']:return rows
            time.sleep(.03)
        raise TimeoutError('input_release_deadline')
    if action=='meaning-provider':
        from lookup import context,online
        cases=[('They waited by the bank of the river before sunrise.',0),
            ('She deposited the money in the bank before going home.',0),
            ('The bank by the river was far from the bank downtown.',0),
            ('The bank by the river was far from the bank downtown.',1),
            ('We sat quietly on the bank\nand watched the river flow.',0),
            ('A steep bank rose above the narrow stream beside us.',0)]
        rows=[]
        for index,(sentence,occurrence) in enumerate(cases):
            start=sentence.index('bank') if not occurrence else sentence.rindex('bank')
            request=context.ContextRequest(sentence,start,start+4,'bank');began=time.monotonic_ns()
            row=dict(case=index,kind='live',origin='provider_call_only',live=True,cached=False,mock=False,
                     ui_end_to_end=False)
            try:
                value=context.translate_context(request)
                row.update(status='success',meaning_verified=True,meaning=value.meaning,duration_ms=(time.monotonic_ns()-began)/1e6)
            except online.TranslateError as error:row.update(status='error',reason=error.reason,duration_ms=None)
            row['attempt_duration_ms']=(time.monotonic_ns()-began)/1e6;rows.append(row)
        result=meaning_report(rows);result.update(origin='provider_call_only',physical_ui_meaning_median_ms=None,
            physical_ui_meaning_p95_ms=None,ui_limit='Provider availability probes do not measure UI end-to-end time.')
        write_record(root/'meaning-provider.json',result);return result
    if action=='stop-observer':
        import signal
        metadata=read_record(root/'probe-process.json');pid=metadata['observer'];process=Path('/proc',str(pid))
        if not process.exists():return dict(stopped=True,method='already_absent')
        argv=process.joinpath('cmdline').read_bytes().split(b'\0')
        _require(process.stat().st_uid==1001 and b'/home/lookup07/check_fallback_09.py' in argv and b'--guest-probe' in argv
                 and os.getsid(pid)==pid,'unowned_observer')
        os.killpg(pid,signal.SIGTERM);deadline=time.monotonic()+6
        while time.monotonic()<deadline:
            if not process.exists():return dict(stopped=True,pid=pid)
            time.sleep(.05)
        raise TimeoutError('observer_exit_deadline')
    if action=='privacy':
        import hashlib
        result={}
        for name,extra in (('primary',['--primary']),('clipboard',[])):
            child=subprocess.run(['wl-paste',*extra,'--no-newline'],env=env,capture_output=True,timeout=3)
            _require(len(child.stdout)<=1<<20,'clipboard_too_large')
            result[name]=hashlib.sha256(str(child.returncode).encode()+b'\0'+child.stdout).hexdigest()
            result[name+'_exit']=child.returncode
        from PyQt6.QtDBus import QDBusMessage,QDBus
        def klipper(method,*arguments):
            message=QDBusMessage.createMethodCall('org.kde.klipper','/klipper','org.kde.klipper.klipper',method)
            message.setArguments(list(arguments));reply=bus.call(message,QDBus.CallMode.Block,1200)
            _require(reply.type()!=QDBusMessage.MessageType.ErrorMessage,'klipper_unavailable')
            return reply.arguments()[0] if reply.arguments() else None
        menu=klipper('getClipboardHistoryMenu');_require(isinstance(menu,list) and len(menu)<=1000,'klipper_history')
        history=[klipper('getClipboardHistoryItem',index) for index in range(len(menu))]
        _require(all(isinstance(value,str) for value in history),'klipper_history')
        result['klipper']=hashlib.sha256(json.dumps(history,ensure_ascii=False).encode()).hexdigest()
        result['klipper_items']=len(history);files=[]
        for directory in (Path('/tmp'),Path('/run/user/1001'),root/'data'):
            for parent,dirs,names in os.walk(directory):
                dirs[:]=[name for name in dirs if (Path(parent)/name).stat().st_uid==1001 and not (Path(parent)/name).is_symlink()]
                for name in names:
                    path=Path(parent)/name
                    if path.is_symlink() or not path.is_file() or path.stat().st_uid!=1001 or path.stat().st_size<8:continue
                    with path.open('rb') as stream:magic=stream.read(8)
                    if magic==b'\x89PNG\r\n\x1a\n':files.append(str(path))
        result.update(png_files=sorted(files),scanned=['/tmp','/run/user/1001',str(root/'data')])
        return result
    if action=='privacy-seed':
        for extra,text in (([],b'Public hardening clipboard fixture 08'),):
            subprocess.run(['wl-copy',*extra],input=text,env=env,check=True,timeout=3,
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        return dict(seeded=True,history_cleared=False)
    if action=='restore-owned-primary':
        value=subprocess.run(['wl-paste','--primary','--no-newline'],env=env,capture_output=True,timeout=3)
        _require(value.returncode==0 and value.stdout in (b'Public hardening primary fixture 08',b'Public hardening clipboard fixture 08'),'unknown_primary')
        subprocess.run(['wl-copy','--primary','--clear'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True,timeout=3)
        return dict(restored_absent_selection=True,history_cleared=False)
    if action=='injection-evidence':
        path=root/'injected-capture.jsonl'
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    if action=='cleanup-profile':
        import hashlib,shlex
        _require(not owner()['owner'],'owner_still_running')
        settings=dict(LOOKUP_CONFIG=str(root/'config.json'),LOOKUP_DB=str(root/'data/history.db'),LOOKUP_CACHE=str(root/'cache'),
            LOOKUP_DICTS='/usr/share/lookup/dicts',LOOKUP_TIMING='1')
        script=Path.home()/'.config/plasma-workspace/env/lookup-fallback-09.sh'
        expected='# Owned lookup-fallback-09\n'+''.join('export '+key+'='+shlex.quote(value)+'\n' for key,value in settings.items())
        _require(script.is_file() and not script.is_symlink() and script.stat().st_uid==1001 and script.read_text()==expected,'unowned_environment_script')
        backup=root/'retained-config-before.bin';target=Path.home()/'.config/lookup/config.json'
        _require(backup.is_file() and not backup.is_symlink() and backup.stat().st_uid==1001 and target.is_file()
                 and not target.is_symlink() and target.stat().st_uid==1001,'unowned_retained_config')
        data=backup.read_bytes();temporary=target.with_name('config.hardening-restore.tmp')
        with os.fdopen(os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as output:output.write(data)
        temporary.replace(target);script.unlink()
        return dict(environment_script_removed=not script.exists(),retained_config_restored=target.read_bytes()==data,
            retained_config_sha256=hashlib.sha256(data).hexdigest(),owner_absent=not owner()['owner'],
            activation_environment='expires at controlled guest shutdown',input_acl='temporary device node expires at guest shutdown')
    if action=='environment':
        pid=interface.servicePid('org.kde.kglobalaccel').value()
        return dict(global_shortcut_pid=pid,
            installed_exec=next(line for line in Path('/usr/share/applications/org.lookup.Linux.desktop').read_text().splitlines() if line.startswith('Exec=')),
            user_desktop_present=(Path.home()/'.local/share/applications/org.lookup.Linux.desktop').exists(),owner=owner())
    if action=='work-area':
        monitor=platform.monitors(env)[0]
        return dict(monitor=monitor.__dict__,panels=platform.panel_rects(env),work_area=platform.work_area(env,monitor))
    if action=='popup-info':
        from lookup import gui
        from PyQt6.QtDBus import QDBusMessage,QDBus
        matches=platform.run(['kdotool','search','--pid',str(owner()['pid']),'--name',gui.TITLE],env).decode().split()
        result=[]
        for window in matches:
            message=QDBusMessage.createMethodCall('org.kde.KWin','/KWin','org.kde.KWin','getWindowInfo');message.setArguments([window])
            reply=bus.call(message,QDBus.CallMode.Block,1200);info=reply.arguments()[0] if reply.arguments() else {}
            if info.get('caption')==gui.TITLE:result.append({key:info.get(key) for key in ('x','y','width','height','caption','active')})
        return result
    if action=='snapshot':
        from lookup import capture
        image=capture.capture_monitor(platform.monitors(env)[0],env)
        text=subprocess.run(['tesseract','stdin','stdout','-l','eng+rus','--psm','11'],input=image.png,capture_output=True,timeout=5).stdout.decode()
        return dict(png_base64=base64.b64encode(image.png).decode(),text=text)
    if action=='dictionary-fixture':
        import shutil
        target=root/'dicts/mueller7';missing=root/'mueller7-unavailable'
        previous=root/'dicts/mueller7-unavailable'
        if previous.exists():
            _require(not target.exists() and not missing.exists(),'fixture_identity');previous.rename(missing)
        operation=command['operation']
        if operation=='prepare':
            _require(not target.exists() and not missing.exists(),'existing_fixture')
            shutil.copytree('/usr/share/lookup/dicts/mueller7',target)
        elif operation=='unavailable':
            _require(target.is_dir() and not missing.exists(),'fixture_identity');target.rename(missing)
        elif operation=='restore':
            _require(missing.is_dir() and not target.exists(),'fixture_identity');missing.rename(target)
        else:raise ValueError('fixture_operation')
        return dict(path=str(target.parent),available=target.exists(),operation=operation)
    if action=='settings-open':
        from PyQt6.QtDBus import QDBusMessage,QDBus
        pid=owner()['pid']
        message=QDBusMessage.createMethodCall('org.kde.StatusNotifierWatcher','/StatusNotifierWatcher','org.freedesktop.DBus.Properties','Get')
        message.setArguments(['org.kde.StatusNotifierWatcher','RegisteredStatusNotifierItems']);reply=bus.call(message,QDBus.CallMode.Block,1200)
        items=reply.arguments()[0]
        if hasattr(items,'variant'):items=items.variant()
        for item in items:
            service=item.split('/')[0]
            if interface.servicePid(service).value()!=pid:continue
            reply=subprocess.run(['qdbus6',service,'/MenuBar','com.canonical.dbusmenu.Event','3','clicked','0','0'],
                env=env,capture_output=True,timeout=3)
            return dict(opened=reply.returncode==0,pid=pid)
        raise EvidenceError('owned_notifier_missing')
    if action=='launch-owner':
        _require(not owner()['owner'],'preexisting_owner')
        config=json.loads((root/'config.json').read_text());config['online']=command.get('online',False)
        (root/'config.json').write_text(json.dumps(config))
        child_env=dict(env,LOOKUP_TIMING='1',LOOKUP_DB=str(root/'data/history.db'),LOOKUP_CONFIG=str(root/'config.json'),
            LOOKUP_CACHE=str(root/'cache'),LOOKUP_DICTS=command.get('dicts','/usr/share/lookup/dicts'))
        with (root/'fault-daemon.log').open('w') as stream:
            argv=([sys.executable,str(Path(__file__).resolve()),'--injected-capture'] if command.get('capture_fault') else ['/usr/bin/lookup','--app'])
            child=subprocess.Popen(argv,env=child_env,cwd='/tmp',stdin=subprocess.DEVNULL,
                stdout=stream,stderr=stream,start_new_session=True)
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            result=owner()
            if result['owner'] and result['pid']==child.pid:return result
            time.sleep(.05)
        raise TimeoutError('plain_owner_start')
    if action=='prepare':
        assert not owner()['owner'],'preexisting_owner'
        desktop=Path.home()/'.local/share/applications/org.lookup.Linux.desktop'
        if desktop.exists():
            _require('X-LookUpHardening-Owned=true' in desktop.read_text(),'unexpected_desktop_shadow')
            desktop.unlink()
        (root/'config.json').write_text('{"online":false,"shortcut":"Meta+Shift+E","popup_timeout":60}')
        settings=dict(LOOKUP_CONFIG=str(root/'config.json'),LOOKUP_DB=str(root/'data/history.db'),LOOKUP_CACHE=str(root/'cache'),
            LOOKUP_DICTS='/usr/share/lookup/dicts',LOOKUP_TIMING='1')
        actual=Path.home()/'.config/lookup/config.json';backup=root/'retained-config-before.bin'
        if not backup.exists():backup.write_bytes(actual.read_bytes())
        value=json.loads(actual.read_text());value['autostart']=False
        temporary=actual.with_suffix('.hardening-tmp');temporary.write_text(json.dumps(value));temporary.replace(actual)
        script=Path.home()/'.config/plasma-workspace/env/lookup-fallback-09.sh';script.parent.mkdir(parents=True,exist_ok=True)
        if script.exists():_require(script.read_text().startswith('# Owned lookup-fallback-09'),'unexpected_environment_file')
        import shlex
        script.write_text('# Owned lookup-fallback-09\n'+''.join('export '+key+'='+shlex.quote(value)+'\n' for key,value in settings.items()))
        subprocess.run(['dbus-update-activation-environment','--systemd',*[key+'='+value for key,value in settings.items()]],
            env=env,capture_output=True,timeout=5,check=True)
        refresh=subprocess.run(['kbuildsycoca6'],env=env,capture_output=True,timeout=15)
        _require(refresh.returncode==0,'desktop_refresh')
        registry=lifecycle.ShortcutRegistry()
        if registry.inspect().keys!=(lifecycle.parse_shortcut('Meta+Shift+E')[1],):
            registry.change('Meta+Shift+E').commit()
        return dict(prepared=True,owner_before=owner(),environment_script=str(script),installed_desktop_unchanged=True)
    if action=='arm':
        value={key:command[key] for key in ('attempt','group','case','scene')}
        value['verify_count']=command.get('verify_count',False)
        value['token']=time.monotonic_ns()
        temporary=root/'arm.tmp';temporary.write_text(json.dumps(value));temporary.replace(root/'arm.json')
        deadline=time.monotonic()+6
        while time.monotonic()<deadline:
            path=root/'ready.json'
            if path.exists():
                result=read_record(path)
                if result is None:
                    with (root/'command-read-retries.jsonl').open('a') as output:output.write(json.dumps(dict(action=action,attempt=command['attempt'],reason='incomplete_json',at_ns=time.monotonic_ns()))+'\n')
                if matching_result(result,value):
                    _require(path.stat().st_uid==1001,'transport_owner');return result
            time.sleep(.03)
        raise TimeoutError('arm_deadline')
    if action=='result':
        deadline=time.monotonic()+18
        while time.monotonic()<deadline:
            path=root/'result.json'
            if path.exists():
                result=read_record(path)
                if result is None:
                    with (root/'command-read-retries.jsonl').open('a') as output:output.write(json.dumps(dict(action=action,attempt=command['attempt'],reason='incomplete_json',at_ns=time.monotonic_ns()))+'\n')
                if matching_result(result,command):
                    _require(path.stat().st_uid==1001,'transport_owner')
                    return dict(result,transport_file_uid=path.stat().st_uid,transport_file_mode=oct(path.stat().st_mode&0o777))
            if (root/'observer-error.json').exists():raise RuntimeError('observer_failed')
            time.sleep(.03)
        raise TimeoutError('result_deadline')
    if action=='stop-owner':
        value=owner()
        if not value['pid']:return dict(stopped=True,method='already_absent')
        process=Path('/proc',str(value['pid']))
        expected=('LOOKUP_DB='+str(root/'data/history.db')).encode()
        scoped=expected in process.joinpath('environ').read_bytes().split(b'\0')
        if not scoped:
            argv=process.joinpath('cmdline').read_bytes().split(b'\0')
            _require(command.get('allow_retained') is True and argv[:3]==[b'/usr/bin/python',b'/usr/bin/lookup',b'--app']
                     and process.stat().st_uid==1001,'unowned_owner')
        items=subprocess.run(['qdbus6','org.kde.StatusNotifierWatcher','/StatusNotifierWatcher',
            'org.kde.StatusNotifierWatcher.RegisteredStatusNotifierItems'],env=env,capture_output=True,text=True,timeout=3,check=True).stdout.split()
        for item in items:
            service=item.split('/StatusNotifierItem')[0]
            if interface.servicePid(service).value()==value['pid']:
                subprocess.run(['qdbus6',service,'/MenuBar','com.canonical.dbusmenu.Event','5','clicked','0','0'],
                    env=env,capture_output=True,timeout=3,check=True)
        deadline=time.monotonic()+6
        while time.monotonic()<deadline:
            if not owner()['owner']:return dict(stopped=True,method='tray_exit',old_pid=value['pid'])
            time.sleep(.05)
        raise TimeoutError('owner_exit_deadline')
    if action=='resource':
        value=owner();pid=value['pid'];process=Path('/proc',str(pid));status=process.joinpath('status').read_text()
        start=int(process.joinpath('stat').read_text().split(') ',1)[1].split()[19])
        events=[json.loads(line.split(':',1)[1]) for line in (root/'daemon.log').read_text().splitlines()
                if line.startswith('lookup-timing:')]
        run=next(item['run'] for item in reversed(events) if item['pid']==pid)
        descendants=descendant_identities(pid,start,1001)
        return dict(identity=[pid,start,run],rss_bytes=int(re.search(r'^VmRSS:\s+(\d+)',status,re.M)[1])*1024,
            threads=len(list(process.joinpath('task').iterdir())),fds=len(list(process.joinpath('fd').iterdir())),
            owned_children=[row['pid'] for row in descendants],descendant_identities=descendants,observed=True)
    if action=='history':
        import sqlite3
        path=root/'data/history.db'
        if not path.exists():return dict(count=0,integrity='ok')
        with sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True) as conn:
            return dict(count=conn.execute('SELECT COALESCE(sum(count),0) FROM words').fetchone()[0],
                integrity=conn.execute('PRAGMA integrity_check').fetchone()[0])
    raise ValueError('unknown_owned_command')


def vm_command(value):
    import base64,json,subprocess
    encoded=base64.b64encode(json.dumps(value).encode()).decode()
    child=subprocess.run(['ssh','-o','BatchMode=yes','-o','HostKeyAlias=lookup-gsd-07','-o',
        'UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-p','2227','archvm',
        'sudo','-n','-H','-u','lookup07','python','/home/lookup07/check_fallback_09.py','--guest-command',encoded],
        capture_output=True,text=True,timeout=25)
    if child.returncode:raise RuntimeError('owned_guest_command_failed')
    return json.loads(child.stdout)


def vm_input(action,**values):
    import os,subprocess
    from pathlib import Path
    argv=['powershell','-NoProfile','-File',str(Path(__file__).with_name('check_hardening_vm.ps1')),'-Action',action]
    for key,value in values.items():argv+=['-'+key,str(value)]
    subprocess.run(argv,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=8,check=True,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)


def run_performance(output):
    import json
    from pathlib import Path
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():raise ValueError('attempt_file_must_be_new')
    rows=[]
    workload=[('cold',i,i) for i in range(1,4)]+[('warm_distinct',i,i) for i in range(1,19)]+[('repeat',i,i) for i in range(1,10)]
    for attempt,(group,case,scene) in enumerate(workload,1):
        before=None
        try:
            if group=='cold':
                vm_command(dict(action='stop-owner'));before=vm_command(dict(action='owner'))
                _require(before['owner'] is False,'cold_owner_present')
            vm_input('Keys',Codes='01 81')
            ready=vm_command(dict(action='arm',attempt=attempt,group=group,case=case,scene=scene))
            vm_input('Pointer',X=ready['point'][0],Y=ready['point'][1],Buttons=0)
            vm_input('Keys',Codes='e0 5b 2a 12 92 aa e0 db')
            row=vm_command(dict(action='result',attempt=attempt,token=ready['token']))
            if group=='cold':
                row['owner_absent_before_input']=not before['owner']
                if not row.get('process_born_after_input'):row.update(status='error',reason='cold_owner_birth')
        except Exception as error:
            row=dict(attempt=attempt,input_sequence=attempt,group=group,case=case,scene=scene,status='error',
                     reason=type(error).__name__,mode='native',physical=False,released=False)
        rows.append(row);output.write_text(json.dumps(rows,indent=2))
        print(json.dumps(dict(attempt=attempt,group=group,status=row['status'],latency_ms=row.get('latency_ms'))),flush=True)
    report=performance_report(rows);output.with_name(output.stem+'-report.json').write_text(json.dumps(report,indent=2))
    return report


def run_stability(output):
    import json,time
    from pathlib import Path
    output=Path(output)
    if output.exists():raise ValueError('attempt_file_must_be_new')
    vm_command(dict(action='stop-owner'))
    data=dict(mode='native',protocol=protocol(),warmup=[],completions=[],resources=[])
    baseline=None
    for attempt in range(1,341):
        group='warmup' if attempt<=20 else 'stress';case=(attempt-1)%len(SCENES)+1
        try:
            vm_input('Keys',Codes='01 81')
            ready=vm_command(dict(action='arm',attempt=attempt,group=group,case=case,scene=case))
            vm_input('Pointer',X=ready['point'][0],Y=ready['point'][1],Buttons=0)
            vm_input('Keys',Codes='e0 5b 2a 12 92 aa e0 db')
            row=vm_command(dict(action='result',attempt=attempt,token=ready['token']))
        except Exception as error:
            row=dict(attempt=attempt,input_sequence=attempt,case=case,group=group,status='error',reason=type(error).__name__)
        data['warmup' if attempt<=20 else 'completions'].append(row)
        if attempt==20:baseline=vm_command(dict(action='history'))
        if attempt>20 and (attempt-20)%10==0:
            value=vm_command(dict(action='resource'));value['after']=attempt-20;data['resources'].append(value)
        write_record(output,data)
        if attempt%10==0 or row['status']!='success':
            print(json.dumps(dict(attempt=attempt,measured=max(0,attempt-20),status=row['status'],
                last_latency_ms=row.get('latency_ms'),rss_bytes=data['resources'][-1]['rss_bytes'] if data['resources'] else None)),flush=True)
        if output.with_suffix('.stop').exists():
            data.update(controlled_stop=True,stopped_after=attempt);write_record(output,data)
            return dict(passed=False,controlled_stop=True,stopped_after=attempt)
    started=time.monotonic();time.sleep(protocol()['cooldown_ms']/1000)
    cooldown=vm_command(dict(action='resource'));cooldown.update(after=320,idle_ms=(time.monotonic()-started)*1000)
    final=vm_command(dict(action='history'));delta=final['count']-baseline['count']
    data.update(cooldown=cooldown,history_delta=delta,enrichment_extra_count=delta-320,integrity=final['integrity'],
        history_before=baseline['count'],history_after=final['count'])
    output.write_text(json.dumps(data,indent=2));report=stability_report(data)
    output.with_name(output.stem+'-report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report),flush=True);return report


def run_burst(output):
    import base64,json
    from pathlib import Path
    output=Path(output)
    if output.exists():raise ValueError('attempt_file_must_be_new')
    before=vm_command(dict(action='history'));resource=vm_command(dict(action='resource'))
    vm_input('Keys',Codes='01 81')
    ready=vm_command(dict(action='arm',attempt=1,group='burst',case=1,scene=1,verify_count=True))
    vm_input('Pointer',X=ready['point'][0],Y=ready['point'][1],Buttons=0)
    previous=vm_command(dict(action='last-trigger',after=0))
    vm_input('Burst')
    raw=vm_command(dict(action='inputs',token=ready['token'],count=10))
    trace=vm_command(dict(action='trace',since_ns=raw[0]['input_ns']))
    triggers=[row for row in trace if row['stage']==1 and row['request']>previous['request']]
    _require(len(raw)==10 and len(triggers)==10,'burst_input_trigger_count')
    inputs=[dict(row,sequence=index+1,request=trigger['request']) for index,(row,trigger) in enumerate(zip(raw,triggers))]
    latest=triggers[-1]
    final=vm_command(dict(action='result',attempt=1,token=ready['token'],request=latest['request']))
    frame=vm_command(dict(action='frame',attempt=1,token=ready['token'],request=latest['request']))
    output.with_suffix('.png').write_bytes(base64.b64decode(frame['png_base64']))
    trace=vm_command(dict(action='trace',since_ns=inputs[0]['input_ns']))
    accepted=sorted({row['request'] for row in trace if row['stage']==3})
    after=vm_command(dict(action='history'));delta=after['count']-before['count']
    vm_input('Keys',Codes='01 81')
    subsequent=vm_command(dict(action='arm',attempt=2,group='postburst',case=2,scene=2))
    vm_input('Pointer',X=subsequent['point'][0],Y=subsequent['point'][1],Buttons=0)
    vm_input('Keys',Codes='e0 5b 2a 12 92 aa e0 db')
    response=vm_command(dict(action='result',attempt=2,token=subsequent['token']))
    last=vm_command(dict(action='resource'))
    data=dict(mode='native',identity=resource['identity'],process_start_source='proc_stat',inputs=inputs,
        accepted_requests=accepted,final_request=latest['request'],final_identity=final.get('frame_identity'),
        final_frame_sha256=frame['sha256'],history_delta=delta,enrichment_extra_count=delta-len(accepted),integrity=after['integrity'],
        final_record=final,subsequent=response,trace=trace,gates=dict(daemon_alive=last['identity']==resource['identity'],
            subsequent_lookup=response.get('status')=='success',no_owned_children=not last['owned_children'],
            fresh_final=final.get('observed_footer_count')==final.get('expected_count') and final.get('request')==latest['request']))
    report=burst_report(data);write_record(output,data);write_record(output.with_name(output.stem+'-report.json'),report)
    print(json.dumps(report),flush=True);return report


def root_network(operation):
    import subprocess
    _require(operation in ('on','off','status'),'network_operation')
    child=subprocess.run(['ssh','-o','BatchMode=yes','-o','HostKeyAlias=lookup-gsd-07','-o',
        'UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-p','2227','archvm',
        'sudo','-n','python','/home/lookup07/check_fallback_09.py','--network-fault',operation],
        capture_output=True,text=True,timeout=8)
    _require(child.returncode==0,'owned_network_command');return child.stdout


def run_network_fault(output):
    import base64,re,time
    from pathlib import Path
    output=Path(output)
    if output.exists():raise ValueError('attempt_file_must_be_new')
    vm_command(dict(action='stop-owner'));owner=vm_command(dict(action='launch-owner',online=True))
    before=vm_command(dict(action='history'));active=False
    data=dict(fault='network',kind='real',mode='native',owner=owner,gates={})
    def physical(attempt,scene):
        ready=vm_command(dict(action='arm',attempt=attempt,group='network-fault',case=scene,scene=scene))
        vm_input('Keys',Codes='01 81');vm_input('Pointer',X=ready['point'][0],Y=ready['point'][1],Buttons=0)
        start=time.monotonic_ns();vm_input('Keys',Codes='e0 5b 2a 12 92 aa e0 db')
        row=vm_command(dict(action='result',attempt=attempt,token=ready['token']))
        return start,row
    def visible(name,predicate):
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            image=vm_command(dict(action='snapshot'))
            if predicate(image['text'].casefold()):
                output.with_name(output.stem+'-'+name+'.png').write_bytes(base64.b64decode(image['png_base64']))
                return image['text'],time.monotonic_ns()
        raise TimeoutError('network_status_frame')
    try:
        root_network('on');active=True
        start,row=physical(1,8)
        text,end=visible('unavailable',lambda value:bool(re.search(r'нет\s+сети',value)))
        rules=root_network('status');after=vm_command(dict(action='history'))
        alive=vm_command(dict(action='owner'))==owner
        data.update(record=row,frame_text=text,rules=rules,elapsed_upper_ms=(end-start)/1e6,
            history_before=before,history_after=after)
        root_network('off');active=False;data['network_restored']=True
        _,recovered=physical(2,9)
        recovery_text,_=visible('recovered',lambda value:'заблокирован' in value or
            ('значение в контексте' in value and 'недоступно' not in value))
        final=vm_command(dict(action='history'))
        data.update(recovered=recovered,recovery_text=recovery_text,history_recovered=final)
        counter=re.search(r'counter packets (\d+)',rules)
        data['gates']=dict(bounded=(end-start)<10_000_000_000,
            specific_status=bool(counter and int(counter[1])>0),daemon_alive=alive,
            recovered=recovered.get('status')=='success' and vm_command(dict(action='owner'))==owner,
            counts_intact=after['count']==before['count']+1 and final['count']==before['count']+2 and final['integrity']=='ok',
            private_errors=all(token not in text for token in ('Traceback','/home/','https://')))
    except Exception as error:data['error']=type(error).__name__
    finally:
        if active:
            try:root_network('off');data['network_restored']=True
            except Exception as error:data['restoration_error']=type(error).__name__
        write_record(output,data)
    print(__import__('json').dumps(dict(gates=data['gates'],error=data.get('error'))),flush=True)
    return data


def run_capture_fault(output):
    import base64,time
    from pathlib import Path
    output=Path(output)
    if output.exists():raise ValueError('attempt_file_must_be_new')
    vm_command(dict(action='stop-owner'))
    before=vm_command(dict(action='history'));injected_before=vm_command(dict(action='injection-evidence'))
    owner=vm_command(dict(action='launch-owner',capture_fault=True))
    ready=vm_command(dict(action='arm',attempt=1,group='injected-capture',case=1,scene=1))
    vm_input('Keys',Codes='01 81');vm_input('Pointer',X=ready['point'][0],Y=ready['point'][1],Buttons=0)
    start=time.monotonic_ns();vm_input('Keys',Codes='e0 5b 2a 12 92 aa e0 db')
    row=vm_command(dict(action='result',attempt=1,token=ready['token']))
    frame=vm_command(dict(action='snapshot'));end=time.monotonic_ns()
    output.with_suffix('.png').write_bytes(base64.b64decode(frame['png_base64']))
    after=vm_command(dict(action='history'));alive=vm_command(dict(action='owner'))==owner
    injection=vm_command(dict(action='injection-evidence'))[len(injected_before):]
    vm_command(dict(action='stop-owner'));normal=vm_command(dict(action='launch-owner'))
    ready=vm_command(dict(action='arm',attempt=2,group='capture-recovered',case=1,scene=1))
    vm_input('Keys',Codes='01 81');vm_input('Pointer',X=ready['point'][0],Y=ready['point'][1],Buttons=0)
    vm_input('Keys',Codes='e0 5b 2a 12 92 aa e0 db')
    recovered=vm_command(dict(action='result',attempt=2,token=ready['token']))
    final=vm_command(dict(action='history'))
    gates=dict(bounded=(end-start)<10_000_000_000,
        specific_status=all(part in frame['text'].casefold() for part in ('удалось получить','экрана','повторите поиск')),
        daemon_alive=alive,recovered=recovered.get('status')=='success',
        counts_intact=before==after and final['count']==before['count']+1 and final['integrity']=='ok',
        private_errors=bool(injection) and all(set(item)=={'site','kind','at_ns'} for item in injection))
    data=dict(fault='capture',kind='injected',mode='native',site='capture._screenshot2',gates=gates,
        frame_text=frame['text'],elapsed_upper_ms=(end-start)/1e6,owner=owner,recovery_owner=normal,
        record=row,injection=injection,history_before=before,history_after=after,history_recovered=final,recovered=recovered)
    write_record(output,data);print(__import__('json').dumps(gates),flush=True);return data


def run_scales(output):
    import base64,json
    from pathlib import Path
    output=Path(output)
    if output.exists():raise ValueError('attempt_file_must_be_new')
    rows=[];original=vm_command(dict(action='outputs'))[0]['scale']
    data=dict(records=rows,second_output='unverified: only one active output',display_restored=False,errors=[])
    data.update(scales_report(data));write_record(output,data)
    try:
        for index,value in enumerate((1,1.25,1.5,2),1):
            vm_input('Keys',Codes='01 81');metadata=vm_command(dict(action='scale',value=value))
            ready=vm_command(dict(action='arm',attempt=index,group='scale',case=1,scene=1))
            vm_input('Pointer',X=ready['point'][0],Y=ready['point'][1],Buttons=0)
            vm_input('Keys',Codes='e0 5b 2a 12 92 aa e0 db')
            row=vm_command(dict(action='result',attempt=index,token=ready['token']))
            image=vm_command(dict(action='frame',attempt=index,token=ready['token'],request=row['request']))
            output.with_name(output.stem+'-'+str(round(value*100))+'.png').write_bytes(base64.b64decode(image['png_base64']))
            x,y,w,h=row['popup_rect'];ax,ay,aw,ah=row['work_area'];expected=ready['logical_point']
            row.update(scale=value,output_metadata=metadata,expected_cursor=expected,
                cursor_correct=all(abs(a-b)<=2 for a,b in zip(expected,row['actual_cursor'])),
                popup_bounded=ax-1<=x and ay-1<=y and x+w<=ax+aw+1 and y+h<=ay+ah+1,
                actual_scale=row['monitor']['scale'])
            row['passed']=row.get('status')=='success' and row['cursor_correct'] and row['popup_bounded'] and abs(row['actual_scale']-value)<.001
            rows.append(row);data.update(scales_report(data));write_record(output,data)
            print(json.dumps(dict(scale=value,passed=row['passed'],cursor=row['actual_cursor'],popup=row['popup_rect'])),flush=True)
    except Exception as error:data['errors'].append(dict(stage='observation',reason=type(error).__name__))
    finally:
        try:
            vm_command(dict(action='scale',value=original))
            actual=vm_command(dict(action='outputs'))[0]['scale']
            data['display_restored']=abs(actual-original)<.001
        except Exception as error:data['errors'].append(dict(stage='restore',reason=type(error).__name__))
        data.update(scales_report(data));write_record(output,data)
    return data


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--guest-probe',action='store_true');parser.add_argument('--start-probe',action='store_true')
    parser.add_argument('--continuous',action='store_true');parser.add_argument('--guest-command')
    parser.add_argument('--performance')
    parser.add_argument('--stability')
    parser.add_argument('--burst')
    parser.add_argument('--scales')
    parser.add_argument('--capture-fault')
    parser.add_argument('--run-network-fault')
    parser.add_argument('--network-fault',choices=('on','off','status'))
    parser.add_argument('--injected-capture',action='store_true')
    parser.add_argument('--session-environment',type=int)
    args=parser.parse_args()
    if args.run_network_fault:
        result=run_network_fault(args.run_network_fault)
        raise SystemExit(0 if strict_gates(result['gates'],FAULT_GATES) and result.get('network_restored') is True else 1)
    if args.capture_fault:
        result=run_capture_fault(args.capture_fault);raise SystemExit(0 if all(result['gates'].values()) else 1)
    if args.injected_capture:
        import os,runpy,sys,time
        from pathlib import Path
        assert os.getuid()==1001 and Path.home()==Path('/home/lookup07')
        sys.path.insert(0,'/usr/lib/lookup/app')
        from lookup import capture,platform
        def fail_transport(name):
            with (Path.home()/'.local/state/lookup-fallback-09/series/injected-capture.jsonl').open('a') as output:
                output.write(__import__('json').dumps(dict(site='capture._screenshot2',kind='injected',at_ns=time.monotonic_ns()))+'\n')
            raise platform.PlatformError('capture_failed')
        capture._screenshot2=fail_transport
        sys.argv=['/usr/bin/lookup','--app'];runpy.run_path('/usr/bin/lookup',run_name='__main__')
        raise SystemExit(0)
    if args.network_fault:
        import json,os,subprocess
        from pathlib import Path
        _require(os.geteuid()==0 and Path('/sys/class/dmi/id/product_uuid').read_text().strip()=='097920cf-b594-494b-8bd8-ccff973c1dc8','unowned_root_network')
        if args.network_fault=='on':
            rules='create table inet lookup_hardening_08 { comment "Owned LookUp phase08 fault"; }\nadd chain inet lookup_hardening_08 output { type filter hook output priority 0; policy accept; }\nadd rule inet lookup_hardening_08 output meta skuid 1001 counter reject\n'
            subprocess.run(['nft','-f','-'],input=rules,text=True,check=True)
        else:
            value=subprocess.run(['nft','--json','list','table','inet','lookup_hardening_08'],capture_output=True,text=True,check=True)
            tables=[entry['table'] for entry in json.loads(value.stdout)['nftables'] if 'table' in entry]
            _require(len(tables)==1 and tables[0].get('comment')=='Owned LookUp phase08 fault','unowned_network_table')
            if args.network_fault=='off':subprocess.run(['nft','delete','table','inet','lookup_hardening_08'],check=True)
            else:subprocess.run(['nft','list','table','inet','lookup_hardening_08'],check=True)
        raise SystemExit(0)
    if args.scales:raise SystemExit(0 if run_scales(args.scales)['passed'] else 1)
    if args.burst:raise SystemExit(0 if run_burst(args.burst)['passed'] else 1)
    if args.stability:raise SystemExit(0 if run_stability(args.stability)['passed'] else 1)
    if args.session_environment:
        import json,os
        from pathlib import Path
        process=Path('/proc',str(args.session_environment))
        assert os.geteuid()==0 and process.stat().st_uid==1001 and process.joinpath('comm').read_text().strip()=='kwin_wayland'
        values=dict(item.split(b'=',1) for item in process.joinpath('environ').read_bytes().split(b'\0') if b'=' in item)
        print(json.dumps({key:values.get(key.encode(),b'').decode() for key in
            ('LOOKUP_TIMING','LOOKUP_CONFIG','LOOKUP_DB','LOOKUP_DICTS','LOOKUP_CACHE')}));raise SystemExit(0)
    if args.performance:
        import json
        value=run_performance(args.performance);print(json.dumps({key:value[key] for key in ('passed','attempts','successful','median_ms','p95_ms')}))
        raise SystemExit(0 if value['passed'] else 1)
    if args.guest_command:
        import json
        try:result=guest_command(args.guest_command)
        except Exception as error:
            import base64,time
            from pathlib import Path
            value=json.loads(base64.b64decode(args.guest_command));root=Path('/home/lookup07/.local/state/lookup-fallback-09/series')
            with (root/'command-errors.jsonl').open('a') as output:
                output.write(json.dumps(dict(action=value.get('action'),attempt=value.get('attempt'),token=value.get('token'),
                    error=type(error).__name__,at_ns=time.monotonic_ns()))+'\n')
            raise
        print(json.dumps(result));raise SystemExit(0)
    if args.guest_probe:raise SystemExit(guest_probe(args.continuous))
    if args.start_probe:
        import os,subprocess,sys
        from pathlib import Path
        assert os.getuid()==1001 and Path.home()==Path('/home/lookup07')
        output=Path.home()/'hardening-observer.log'
        if args.continuous:
            stale=Path.home()/'.local/state/lookup-fallback-09/series/observer-error.json'
            if stale.exists():
                saved=stale.with_name('observer-error-'+str(__import__('time').time_ns())+'.json');stale.replace(saved)
        with output.open('w') as stream:
            child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--guest-probe']+(['--continuous'] if args.continuous else []),cwd='/tmp',
                stdin=subprocess.DEVNULL,stdout=stream,stderr=stream,start_new_session=True)
        print(child.pid)
