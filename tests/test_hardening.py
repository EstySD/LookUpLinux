"""Adversarial evidence is rejected before any native acceptance is attempted."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import subprocess
import unittest

from tools import check_hardening as hardening


def sample(sequence,group='warm_distinct',case=None,latency=1000,pid=20):
    start=1_000_000_000+sequence*2_000_000_000
    identity=[pid,100*pid,1000*pid,sequence]
    return dict(attempt=sequence,input_sequence=sequence,status='success',group=group,case=case or sequence,
        mode='native',physical=True,released=True,pid=pid,process_start=100*pid,run=1000*pid,request=sequence,
        process_start_source='proc_stat',clock='guest_monotonic',frame_clock='guest_monotonic',origin='kernel_evdev',
        kernel_clock_verified=True,clock_ioctl_verified=True,input_ns=start,receipt_ns=start+20_000_000,
        trigger_ns=start+50_000_000,last_not_visible_ns=start+400_000_000,
        first_visible_start_ns=start+int((latency-50)*1e6),first_visible_end_ns=start+int(latency*1e6),
        frame_identity=identity,frame_sha256=f'{sequence:064x}',observed=True,fresh=True,useful_verified=True,
        loading=False,error_card=False,previous_card=False)


def performance():
    rows=[sample(i,'cold',pid=20+i) for i in range(1,4)]
    rows += [sample(i,'warm_distinct',case=i,pid=23) for i in range(4,22)]
    rows += [sample(i,'repeat',case=i-18,pid=23) for i in range(22,31)]
    return rows


def current_performance():
    import base64,hashlib,io,tarfile
    from tools.stage_package import stage
    with tempfile.TemporaryDirectory() as directory:
        destination=Path(directory)/'build';stage(destination)
        source=(destination/'lookup-source.tar.gz').read_bytes()
    members={};buffer=io.BytesIO()
    with tarfile.open(fileobj=io.BytesIO(source),mode='r:gz') as original,tarfile.open(fileobj=buffer,mode='w:gz') as package:
        for item in original.getmembers():
            data=original.extractfile(item).read();name=item.name.removeprefix('lookup-source/')
            members[name]=hashlib.sha256(data).hexdigest()
            entry=tarfile.TarInfo(hardening._package_member(name));entry.size=len(data)
            package.addfile(entry,io.BytesIO(data))
    package=buffer.getvalue();boot='12345678-1234-1234-1234-123456789abc';rows=performance();runtime={}
    for row in rows:
        offset=(row['process_start']*10_000_000-25_000_000-row['input_ns']) if row['group']=='cold' else 30_000_000_000
        for key in ('input_ns','receipt_ns','trigger_ns','last_not_visible_ns','first_visible_start_ns','first_visible_end_ns'):row[key]+=offset
        row.update(owner_absent_before_input=True,process_born_after_input=True)
        fields=['S']+['0']*51;fields[19]=str(row['process_start'])
        trace=[dict(stage=1,mono_ns=row['trigger_ns']),dict(stage=4,useful=1,mono_ns=row['first_visible_start_ns'])]
        for event in trace:event.update({key:row[key] for key in ('pid','run','request')})
        raw=json.dumps(dict(stat=str(row['pid'])+' (lookup) '+' '.join(fields),status='Uid:\t1001\t1001\t1001\t1001\n',
            cmdline_base64=base64.b64encode(b'/usr/bin/python\0/usr/bin/lookup\0--app\0').decode(),clock_ticks=100,
            observed_ns=row['first_visible_end_ns']+10_000_000,boot_id=boot,members=dict(members),
            timing_text='\n'.join('lookup-timing:'+json.dumps(event) for event in trace))).encode()
        digest=hashlib.sha256(raw).hexdigest();runtime[digest]=raw;row['runtime_sha256']=digest
    receipt=dict(build=dict(source_sha256=hashlib.sha256(source).hexdigest(),package_sha256=hashlib.sha256(package).hexdigest(),
        ocr_sha256=members['lookup/ocr.py']),installation=dict(members=members,boot_id=boot,completed_ns=1_000_000_000),stage_exit=0,build_exit=0,install_exit=0)
    return rows,receipt,dict(source=source,package=package,runtime=runtime)


def stability():
    def resource(after):
        return dict(after=after,identity=[20,2000,20000],rss_bytes=100<<20,threads=5,fds=20,
                    owned_children=[],observed=True)
    return dict(mode='native',protocol=hardening.protocol(),warmup=[sample(i) for i in range(1,21)],
                completions=[sample(i+20) for i in range(1,321)],resources=[resource(i) for i in range(10,321,10)],
                cooldown=dict(resource(320),idle_ms=5000),history_delta=320,enrichment_extra_count=0,integrity='ok')


def game(name,relative=False,multiline=False):
    return dict(name=name,version='1',renderer='actual SDL renderer',mode='fullscreen',pid=500,
        source_verified=True,evidence='actual_game',frame_sha256='a'*64,post_dismiss_sha256='b'*64,
        relative_mouse=relative,multiline=multiline,pointer_locked=relative,relative_gameplay_verified=relative,
        gates={key:True for key in hardening.GAME_GATES})


class EvidenceTests(unittest.TestCase):
    def test_current_privacy_rejects_detached_source_pass_input_and_classified_contents(self):
        root=Path('.planning/phases/08-vm');original=json.loads((root/'08-09-privacy-proof.json').read_text())
        artifacts=dict(source=(root/'08-07-privacy-observed-source.png').read_bytes(),
            frame=(root/'08-09-privacy-useful.png').read_bytes(),trace=(root/'08-07-privacy-observed-trace.log').read_bytes())
        self.assertTrue(hardening.current_privacy_report(original,artifacts)['passed'])
        for change in ('pid','run','request','start','source_time','pass_time','nan','missing_time','pass_input',
                'classified_hash','typed_exit','typed_hash','stderr','source_bytes','frame_bytes','trace'):
            data=deepcopy(original);loaded=dict(artifacts)
            if change in ('pid','run','request'):data['source'][change]+=1
            elif change=='start':data['timing']['process_start']+=1
            elif change=='source_time':data['source']['capture_start_ns']=1
            elif change=='pass_time':data['source']['ocr_passes'][1]['start_ns']=1
            elif change=='nan':data['source']['ocr_passes'][1]['end_ns']=float('nan')
            elif change=='missing_time':data['source']['ocr_passes'][1].pop('start_ns')
            elif change=='pass_input':data['source']['ocr_passes'][1]['input_sha256']='a'*64
            elif change=='classified_hash':data['after']['classified']['primary']['stdout_sha256']='b'*64
            elif change=='typed_exit':data['after']['typed']['primary_exit']=0
            elif change=='typed_hash':data['before']['typed']['primary']=data['after']['typed']['primary']='c'*64
            elif change=='stderr':data['after']['classified']['primary']['stderr']='Nothing is copied\nprivate extra'
            elif change=='source_bytes':loaded['source']=b'changed source'
            elif change=='frame_bytes':loaded['frame']=b'changed frame'
            else:loaded['trace']=loaded['trace'].replace(b'"request":98',b'"request":999').replace(b'"request": 98',b'"request": 999')
            self.assertFalse(hardening.current_privacy_report(data,loaded)['passed'],change)

    def test_suites_anchor_actual_git_code_allowing_only_metadata_after_tested_revision(self):
        import hashlib
        raw=b'Ran 12 tests in 1.234s\n\nOK\n';digest=hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            def git(*args):
                return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.DEVNULL,text=True).strip()
            git('init','-q');(root/'lookup').mkdir();(root/'lookup/app.py').write_text('original=1\n')
            git('add','lookup/app.py');git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','source')
            revision=git('rev-parse','HEAD');tree=git('rev-parse','HEAD^{tree}')
            suites={name:dict(exit=0,count=12,skips=0,log_sha256=digest,revision=revision,tree=tree,
                command=['python','-m','unittest','discover','-s','tests']) for name in ('host','target')}
            suites['target'].update(ocr_enabled=True,mueller_verified=True)
            self.assertTrue(hardening.closure_suites_report(suites,{digest:raw},repo=root)['passed'])
            for change in ('revision','tree','dirty','untracked','native'):
                data=deepcopy(suites)
                if change in ('revision','tree'):
                    for row in data.values():row[change]='a'*40
                elif change=='dirty':(root/'lookup/app.py').write_text('changed=2\n')
                elif change=='untracked':(root/'lookup/new.py').write_text('new=3\n')
                else:
                    path=root/'.planning/phases/08-vm/08-07-controller.py';path.parent.mkdir(parents=True);path.write_text('changed=4\n')
                self.assertFalse(hardening.closure_suites_report(data,{digest:raw},repo=root)['passed'],change)
                if change=='dirty':(root/'lookup/app.py').write_text('original=1\n')
                elif change=='untracked':(root/'lookup/new.py').unlink()
                elif change=='native':path.unlink()
            (root/'report.md').write_text('actual metadata\n');git('add','report.md')
            git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','metadata')
            self.assertTrue(hardening.closure_suites_report(suites,{digest:raw},repo=root)['passed'])
            (root/'lookup/app.py').write_text('new_code=5\n');git('add','lookup/app.py')
            git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','code')
            self.assertFalse(hardening.closure_suites_report(suites,{digest:raw},repo=root)['passed'])

    def test_final_review_requires_exact_current_headers_not_old_scoped_prose(self):
        import hashlib
        revision='a'*40
        review=('---\nphase_review_complete: true\ncode_review: passed\nsecurity_review: passed\nreview_head: '+revision+'\n---\n').encode()
        verifier=('---\nstatus: passed\nverified_revision: '+revision+'\n---\n').encode()
        artifacts={hashlib.sha256(raw).hexdigest():raw for raw in (review,verifier)}
        gates={name:dict(file='08-VERIFICATION.md' if name=='verifier' else '08-REVIEW.md',revision=revision,
            sha256=hashlib.sha256(verifier if name=='verifier' else review).hexdigest()) for name in ('code_review','security_review','verifier')}
        self.assertTrue(all(hardening.closure_reviews_report(gates,artifacts,revision).values()))
        for change in ('hash','revision','file','scope'):
            rows=deepcopy(gates);loaded=dict(artifacts)
            if change=='hash':rows['code_review']['sha256']='0'*64
            elif change=='revision':rows['code_review']['revision']='b'*40
            elif change=='file':rows['code_review']['file']='other.md'
            else:
                raw=review.replace(b'phase_review_complete: true',b'phase_review_complete: false').replace(b'code_review: passed',b'code_review: passed_in_reviewed_scope')
                digest=hashlib.sha256(raw).hexdigest();loaded[digest]=raw;rows['code_review']['sha256']=digest
            self.assertFalse(hardening.closure_reviews_report(rows,loaded,revision)['code_review'],change)

    def test_current_cleanup_requires_observed_postmanual_state_and_all_retained_data(self):
        clone='cf207909-94b5-4b49-8bd8-ccff973c1dc8';original='abc73254-ddf7-4f1f-9c66-7c2fcc5254d7'
        baseline=dict(files={'/config.json':{'sha256':'a'*64},'/history.db':{'sha256':'b'*64}},
            logical_counts={'/history.db':dict(integrity='ok')})
        retention=dict(files={'/config.json':True},databases={'/history.db':dict(actual_logical_sha256='b'*64,
            postmanual_backup_sha256='b'*64,integrity='ok',retained=True)})
        guest=dict(current_baseline_only=True,fallback_stop_only_owned=dict(ok=True,result=dict(stopped=[],remaining=[])),
            postmanual_retention=dict(ok=True,result=deepcopy(retention)),post_removal_retention=dict(ok=True,result=deepcopy(retention)),
            fixture_restore=dict(ok=True,result=dict(removed=True)),package_remove_preserve_profiles=dict(ok=True,result=dict(exit=0,absent=True)))
        state=dict(UUID='"'+clone+'"',VMState='"poweroff"',accelerate3d='"on"',clipboard='"disabled"')
        controller=dict(prior=deepcopy(state),final_clone=deepcopy(state),release=dict(ok=True),mouse_release=dict(ok=True),
            guest_cleanup=dict(ok=True,result=json.dumps(guest)),restore=dict(ok=True,result=dict(exit=0)),
            original_before=dict(UUID='"'+original+'"',VMState='"running"'),
            original_after=dict(UUID='"'+original+'"',VMState='"poweroff"'),
            host_actions=[dict(argv=['VBoxManage','modifyvm',clone],exit=0,mutating=True)])
        self.assertTrue(hardening.current_cleanup_report(controller,baseline,{'passed':True})['passed'])
        for change in ('original_action','wrong_clone','on_restore','database','missing_file','fixture','package','release','keys'):
            row=deepcopy(controller);saved=deepcopy(guest);keys={'passed':True}
            if change=='original_action':row['host_actions'][0]['argv'][2]=original
            elif change=='wrong_clone':row['final_clone']['UUID']='"other"'
            elif change=='on_restore':row['final_clone']['VMState']='"running"'
            elif change=='database':saved['post_removal_retention']['result']['databases']['/history.db']['actual_logical_sha256']='c'*64
            elif change=='missing_file':saved['postmanual_retention']['result']['files']={}
            elif change=='fixture':saved['fixture_restore']['result']['removed']=False
            elif change=='package':saved['package_remove_preserve_profiles']['result']['absent']=False
            elif change=='release':row['release']['ok']=False
            else:keys={'passed':False}
            row['guest_cleanup']['result']=json.dumps(saved)
            self.assertFalse(hardening.current_cleanup_report(row,baseline,keys)['passed'],change)

    def test_final_suite_metadata_cannot_replace_logs_or_same_revision(self):
        claimed={name:dict(exit=0,count=999,skips=0,log_sha256='a'*64,revision='a'*40)
            for name in ('host','target')}
        self.assertFalse(hardening.closure_suites_report(claimed,{})['passed'])
        import hashlib
        raw=b'Ran 12 tests in 1.234s\n\nOK\n'
        digest=hashlib.sha256(raw).hexdigest()
        suites={name:dict(exit=0,count=12,skips=0,log_sha256=digest,revision='a'*40,tree='b'*40,
            command=['python','-m','unittest','discover','-s','tests']) for name in ('host','target')}
        suites['target']['ocr_enabled']=True;suites['target']['mueller_verified']=True
        self.assertFalse(hardening.closure_suites_report(suites,{digest:raw})['passed'])
        for change in ('count','revision','tree','exit','ocr','log'):
            data=deepcopy(suites);logs={digest:raw}
            if change=='count':data['host']['count']=13
            elif change in ('revision','tree'):data['target'][change]='c'*40
            elif change=='exit':data['target']['exit']=1
            elif change=='ocr':data['target']['ocr_enabled']=False
            else:logs[digest]=b'FAILED (errors=1)\n'
            self.assertFalse(hardening.closure_suites_report(data,logs)['passed'],change)

    def test_exact_nested_owned_key_delta_and_actual_unrelated_markers(self):
        root=Path('.planning/phases/08-vm')
        read=lambda name:json.loads((root/name).read_text(encoding='utf-8'))
        proof=dict(registry=read('08-07-registry-clear-product.json'),baseline=read('08-07-postmanual-registry.json'),
            physical_before=read('08-07-unrelated-marker-before.json'),physical_after=read('08-07-unrelated-marker-after.json'))
        self.assertTrue(hardening.shortcut_preservation_report(proof)['passed'])
        for change in ('unrelated_key','missing_component','raw_hash','raw_unrelated','wrong_owned_action','missing_marker','reused_marker'):
            data=deepcopy(proof)
            if change=='unrelated_key':data['registry']['after']['bindings'][0]['keys']=[123]
            elif change=='missing_component':data['registry']['after']['components'].pop()
            elif change=='raw_hash':data['registry']['after']['kconfig_sha256']='0'*64
            elif change=='raw_unrelated':
                import base64,hashlib
                raw=base64.b64decode(data['registry']['after']['kconfig_base64'])+b'\n[unrelated.extra]\naction=Ctrl+Q\n'
                data['registry']['after'].update(kconfig_base64=base64.b64encode(raw).decode(),kconfig_sha256=hashlib.sha256(raw).hexdigest())
            elif change=='wrong_owned_action':data['registry']['product_action'][1]='other'
            elif change=='missing_marker':data['physical_after']['after']['rows']=[]
            else:data['physical_after']=deepcopy(data['physical_before'])
            self.assertFalse(hardening.shortcut_preservation_report(data)['passed'],change)

    def test_fallback_stability_requires_twenty_actual_completions_and_real_retry(self):
        from tools.check_hardening import fallback_stability_report
        rows=[]
        for index in range(1,21):
            timing=sample(index);passes=[dict(psm=mode,start_ns=timing['trigger_ns']+offset*10,end_ns=timing['trigger_ns']+offset*10+5,
                input_sha256='a'*64,stdout_sha256='b'*64,returncode=0) for offset,mode in enumerate((6,11))]
            rows.append(dict(timing=timing,ocr_passes=passes))
        resource=dict(identity=list(rows[0]['timing'][key] for key in ('pid','process_start','run')),rss_bytes=100<<20,threads=3,fds=20,owned_children=[],observed=True)
        data=dict(completions=rows,resources=[dict(resource,after=i) for i in range(1,21)],cooldown=dict(resource,idle_ms=5000),history_delta=20,integrity='ok')
        self.assertTrue(fallback_stability_report(data)['passed'])
        for field,value in (('history_delta',21),('integrity','bad'),('completions',rows[:19])):
            altered=deepcopy(data);altered[field]=value;self.assertFalse(fallback_stability_report(altered)['passed'])
        for alter in ('no_retry','different_input','timeout','orphan','growth','thread_growth','cooldown'):
            changed=deepcopy(data)
            if alter=='no_retry':
                for row in changed['completions']:row['ocr_passes']=row['ocr_passes'][:1]
            if alter=='different_input':changed['completions'][0]['ocr_passes'][1]['input_sha256']='c'*64
            if alter=='timeout':changed['completions'][0]['ocr_passes'][1]['error']='TimeoutExpired'
            if alter=='orphan':changed['resources'][0]['owned_children']=[999]
            if alter=='growth':changed['resources'][-1]['rss_bytes']=1000<<20
            if alter=='thread_growth':changed['resources'][-1]['threads']=10
            if alter=='cooldown':changed['cooldown']['idle_ms']=4999
            self.assertFalse(fallback_stability_report(changed)['passed'],alter)
    def test_real_old_thirty_cannot_be_relabelled_with_new_summary_hashes(self):
        rows=json.loads(Path('.planning/phases/08-vm/08-performance-final-attempts.json').read_text())
        build=dict(source_sha256='a'*64,package_sha256='b'*64,ocr_sha256='c'*64)
        for row in rows:row['build']=dict(build)
        receipt=dict(build=build,source_members={'lookup/ocr.py':'c'*64},
                     installed_members={'lookup/ocr.py':'c'*64},stage_exit=0,build_exit=0,install_exit=0)
        self.assertTrue(hardening.performance_report(rows)['passed'])
        self.assertFalse(hardening.current_performance_report(rows,receipt)['passed'])

    def test_current_performance_refuses_old_build_or_wrong_installed_ocr(self):
        rows,receipt,artifacts=current_performance()
        self.assertTrue(hardening.current_performance_report(rows,receipt,artifacts)['passed'])
        for change in ('old_rows','old_package','module','source','install_error'):
            current=deepcopy(receipt);attempts=deepcopy(rows);loaded=deepcopy(artifacts)
            if change=='old_rows':
                for row in attempts:row.pop('runtime_sha256')
            elif change=='old_package':current['build']['package_sha256']='e'*64
            elif change=='module':current['installation']['members']['lookup/ocr.py']='e'*64
            elif change=='source':loaded['source']=b'not the staged archive'
            else:current['install_exit']=1
            self.assertFalse(hardening.current_performance_report(attempts,current,loaded)['passed'],change)

    def test_current_runtime_rejects_old_proc_identity_or_new_labels_on_wrong_raw_trace(self):
        import hashlib
        rows,receipt,artifacts=current_performance()
        for change in ('pid','start','boot','uid','cmdline','modules','observed','trace','before_install'):
            attempts=deepcopy(rows);current=deepcopy(receipt);loaded=deepcopy(artifacts)
            raw=json.loads(loaded['runtime'][attempts[0]['runtime_sha256']])
            if change=='pid':raw['stat']='999'+raw['stat'][raw['stat'].index(' '):]
            elif change=='start':raw['stat']=raw['stat'].replace('2100','100')
            elif change=='boot':raw['boot_id']='87654321-4321-4321-4321-cba987654321'
            elif change=='uid':raw['status']='Uid:\t1000\t1000\t1000\t1000\n'
            elif change=='cmdline':raw['cmdline_base64']='b2xk'
            elif change=='modules':raw['members']={'lookup/ocr.py':current['build']['ocr_sha256']}
            elif change=='observed':raw['observed_ns']=1
            elif change=='trace':raw['timing_text']=raw['timing_text'].replace('"run": 21000','"run": 999')
            else:current['installation']['completed_ns']=30_000_000_000
            data=json.dumps(raw).encode();digest=hashlib.sha256(data).hexdigest()
            loaded['runtime'][digest]=data;attempts[0]['runtime_sha256']=digest
            self.assertFalse(hardening.current_performance_report(attempts,current,loaded)['passed'],change)
        old=json.loads(Path('.planning/phases/08-vm/08-performance-final-attempts.json').read_text())
        for row,label in zip(old,rows):row['runtime_sha256']=label['runtime_sha256']
        self.assertFalse(hardening.current_performance_report(old,receipt,artifacts)['passed'])

    def test_equally_truncated_real_archives_and_recomputed_runtime_are_not_full_production(self):
        import hashlib,io,tarfile
        rows,receipt,artifacts=current_performance()
        for key in ('source','package'):
            buffer=io.BytesIO()
            with tarfile.open(fileobj=io.BytesIO(artifacts[key]),mode='r:*') as source,tarfile.open(fileobj=buffer,mode='w:gz') as output:
                member=next(item for item in source.getmembers() if item.name.endswith('/lookup/ocr.py'))
                output.addfile(member,source.extractfile(member))
            artifacts[key]=buffer.getvalue();receipt['build']['source_sha256' if key=='source' else 'package_sha256']=hashlib.sha256(buffer.getvalue()).hexdigest()
        only={'lookup/ocr.py':receipt['build']['ocr_sha256']};receipt['installation']['members']=only
        for row in rows:
            raw=json.loads(artifacts['runtime'][row['runtime_sha256']]);raw['members']=only
            data=json.dumps(raw).encode();digest=hashlib.sha256(data).hexdigest()
            artifacts['runtime'][digest]=data;row['runtime_sha256']=digest
        self.assertFalse(hardening.current_performance_report(rows,receipt,artifacts)['passed'])

    def test_full_archives_containing_actual_old_single_pass_ocr_are_not_current(self):
        import hashlib,io,subprocess,tarfile
        rows,receipt,artifacts=current_performance()
        old=subprocess.check_output(['git','show','5d04a4c:lookup/ocr.py'])
        for key in ('source','package'):
            buffer=io.BytesIO()
            with tarfile.open(fileobj=io.BytesIO(artifacts[key]),mode='r:*') as source,tarfile.open(fileobj=buffer,mode='w:gz') as output:
                for member in source.getmembers():
                    data=old if member.name.endswith('/lookup/ocr.py') else source.extractfile(member).read()
                    member.size=len(data);output.addfile(member,io.BytesIO(data))
            artifacts[key]=buffer.getvalue();receipt['build']['source_sha256' if key=='source' else 'package_sha256']=hashlib.sha256(buffer.getvalue()).hexdigest()
        receipt['build']['ocr_sha256']=hashlib.sha256(old).hexdigest()
        receipt['installation']['members']['lookup/ocr.py']=receipt['build']['ocr_sha256']
        for row in rows:
            raw=json.loads(artifacts['runtime'][row['runtime_sha256']]);raw['members']=receipt['installation']['members']
            data=json.dumps(raw).encode();digest=hashlib.sha256(data).hexdigest()
            artifacts['runtime'][digest]=data;row['runtime_sha256']=digest
        self.assertFalse(hardening.current_performance_report(rows,receipt,artifacts)['passed'])

    def test_final_aggregate_cannot_promote_summary_flags_or_missing_captured_game(self):
        result=hardening.aggregate_report(dict(passed=True,gates={'all_seven':True},games={'passed':True}))
        self.assertFalse(result['passed']);self.assertFalse(result['game01_complete'])
        self.assertFalse(result['criteria']['games'])

    def test_final_cleanup_requires_all_scoped_raw_records_and_rejects_missing_or_false(self):
        root=Path('.planning/phases/08-vm')
        raw=dict(native=json.loads((root/'08-native-final-report.json').read_text())['cleanup'],
            wesnoth=json.loads((root/'08-wesnoth-cleanup-final.json').read_text()),
            doom=json.loads((root/'08-doom-cleanup-final.json').read_text()),
            installation=dict(gates={key:True for key in ('owner_stopped','fixture_stopped','input_released','session_override_restored',
                'clone_powered_off','original_powered_off','clipboard_restored')}))
        self.assertTrue(hardening.final_cleanup_report(raw)['passed'])
        for change in ('missing','false','unknown'):
            data=deepcopy(raw)
            if change=='missing':data.pop('doom')
            elif change=='false':data['native']['network_restored']=False
            else:data={'done':True}
            with self.subTest(change=change):self.assertFalse(hardening.final_cleanup_report(data)['passed'])
        result=hardening.aggregate_report({})
        self.assertFalse(result['cleanup']['passed'])

    def test_partial_transport_json_is_waited_for_without_a_new_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'result.json'
            path.write_text('')
            self.assertIsNone(hardening.read_record(path))
            path.write_text('{"attempt":1,')
            self.assertIsNone(hardening.read_record(path))
            hardening.write_record(path,dict(attempt=1,token=8,input_ns=100))
            self.assertEqual(hardening.read_record(path),dict(attempt=1,token=8,input_ns=100))

    def test_reused_attempt_cannot_reuse_previous_arm_result(self):
        command=dict(attempt=1,token=200)
        self.assertTrue(hardening.matching_result(dict(command),command))
        for result in (dict(attempt=1,token=100),dict(attempt=2,token=200),dict(attempt=1),{}):
            self.assertFalse(hardening.matching_result(result,command))
        self.assertFalse(hardening.matching_result(dict(command,request=2),dict(command,request=3)))

    def test_optical_article_match_needs_current_word_dictionary_and_body(self):
        self.assertTrue(hardening.optical_match('bank Mueller7 берег реки','bank','берег'))
        for text in ('bank','Ищем перевод bank','river Mueller7 берег','river Mueller7 берег bank','bank Mueller7','bank Mueller7 ошибка'):
            self.assertFalse(hardening.optical_match(text,'bank','берег'))

    def test_actual_phase7_report_is_carried_without_reclassification(self):
        raw=json.loads((Path(__file__).resolve().parents[1]/'.planning/phases/07-settings-package/07-native-report.json').read_text(encoding='utf-8'))
        carried=hardening.carry_phase7(raw)
        self.assertIs(carried['raw'],raw)
        self.assertFalse(carried['raw']['passed'])
        self.assertFalse(carried['raw']['cleanup']['original_preserved'])
        self.assertEqual(carried['actor'],'unknown')

    def test_statistics_and_predeclared_workload(self):
        self.assertEqual(hardening.summarize([1,2,3,4]),dict(count=4,median_ms=2.5,p95_ms=4))
        report=hardening.performance_report(performance())
        self.assertTrue(report['passed'])
        self.assertEqual((report['attempts'],report['successful'],report['median_ms']),(30,30,1000))
        for mutate in (lambda rows:rows.pop(4),lambda rows:rows[4].update(attempt=4),
                       lambda rows:rows[4].update(frame_identity=rows[3]['frame_identity']),
                       lambda rows:rows[4].update(status='error'),lambda rows:rows[4].update(case=rows[3]['case'])):
            rows=performance();mutate(rows)
            self.assertFalse(hardening.performance_report(rows)['passed'])

    def test_delayed_receipt_cannot_shorten_kernel_latency_or_pass_threshold(self):
        row=sample(1,latency=1800)
        before=hardening.physical_latency(row)
        row['receipt_ns']=row['trigger_ns']+1_000_000_000
        self.assertEqual(hardening.physical_latency(row),before)
        rows=performance()
        for row in rows:
            row['first_visible_end_ns']=row['input_ns']+1_800_000_000
            row['receipt_ns']=row['trigger_ns']+1_000_000_000
        self.assertFalse(hardening.performance_report(rows)['passed'])

    def test_bad_clock_origin_and_nonuseful_frames_reject(self):
        for changes in (dict(origin='userspace_receipt'),dict(clock_ioctl_verified=False),dict(kernel_clock_verified=1),
                        dict(frame_clock='host_monotonic'),dict(observed=False),dict(loading=True),dict(error_card=True),
                        dict(previous_card=True),dict(frame_sha256=''),dict(useful_verified=1),dict(mode='mock')):
            with self.subTest(changes=changes):
                row=sample(1);row.update(changes)
                with self.assertRaises(hardening.EvidenceError):hardening.physical_latency(row)
        row=sample(1)
        row.update(clock='host_monotonic',frame_clock='host_monotonic',origin='host_before_vbox',
                   kernel_clock_verified=False,clock_ioctl_verified=False,before_dispatch=True,dispatch_ns=row['input_ns']+10)
        self.assertEqual(hardening.physical_latency(row),1000)
        row['before_dispatch']=False
        with self.assertRaises(hardening.EvidenceError):hardening.physical_latency(row)

    def test_journal_reverse_order_cannot_select_old_request_as_newest(self):
        rows=[dict(mono_ns=300,request=3),dict(mono_ns=100,request=1),dict(mono_ns=200,request=2)]
        self.assertEqual([row['request'] for row in hardening.chronological(rows)],[1,2,3])
        self.assertEqual(rows[0]['request'],3)

    def test_resource_tree_includes_worker_thread_children_and_grandchildren(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for pid,start,tasks in ((100,1000,{100:[],101:[200]}),(200,2000,{200:[300]}),(300,3000,{300:[]})):
                process=root/str(pid);process.mkdir()
                fields=['0']*20;fields[0]='S';fields[19]=str(start)
                (process/'stat').write_text(str(pid)+' (owned process) '+' '.join(fields))
                for tid,children in tasks.items():
                    task=process/'task'/str(tid);task.mkdir(parents=True)
                    (task/'children').write_text(' '.join(map(str,children)))
            uid=(root/'100').stat().st_uid
            self.assertEqual(hardening.descendant_identities(100,1000,uid,root),
                [dict(pid=200,process_start=2000,uid=uid),dict(pid=300,process_start=3000,uid=uid)])
            with self.assertRaises(hardening.EvidenceError):hardening.descendant_identities(100,999,uid,root)
            with self.assertRaises(hardening.EvidenceError):hardening.descendant_identities(100,1000,uid+1,root)
            (root/'300/stat').unlink()
            with self.assertRaises(FileNotFoundError):hardening.descendant_identities(100,1000,uid,root)

    def test_scale_acceptance_requires_all_four_observations_and_restoration(self):
        rows=[dict(scale=value,passed=True) for value in (1,1.25,1.5,2)]
        self.assertTrue(hardening.scales_report(dict(records=rows,display_restored=True))['passed'])
        for data in (dict(records=rows[:1],display_restored=True),dict(records=rows,display_restored=False),
                     dict(records=rows[:3]+[rows[0]],display_restored=True)):
            self.assertFalse(hardening.scales_report(data)['passed'])

    def test_interrupted_scale_writer_preserves_partial_failure(self):
        import base64,io,json,tempfile
        from contextlib import redirect_stdout
        from pathlib import Path
        from unittest.mock import patch
        def command(value):
            action=value['action']
            if action=='outputs':return [dict(scale=1)]
            if action=='scale':
                if value['value']==1.25:raise RuntimeError('controlled_second_scale_failure')
                return dict(scale=1)
            if action=='arm':return dict(point=[5,5],logical_point=[5,5],token=9)
            if action=='result':return dict(request=1,status='success',popup_rect=[0,0,10,10],work_area=[0,0,100,100],actual_cursor=[5,5],monitor=dict(scale=1))
            if action=='frame':return dict(png_base64=base64.b64encode(b'unit fixture').decode())
            raise AssertionError(action)
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'scales.json'
            with patch.object(hardening,'vm_command',side_effect=command),patch.object(hardening,'vm_input'),redirect_stdout(io.StringIO()):
                result=hardening.run_scales(output)
            saved=json.loads(output.read_text())
            self.assertFalse(result['passed']);self.assertFalse(saved['passed']);self.assertFalse(saved['complete'])
            self.assertTrue(saved['display_restored']);self.assertEqual(len(saved['records']),1)
            self.assertEqual(saved['errors'],[dict(stage='observation',reason='RuntimeError')])

    def test_failed_live_meanings_keep_denominator_and_null_statistics(self):
        rows=[dict(case=i,kind='live',live=True,cached=False,mock=False,status='error',reason='blocked') for i in range(6)]
        report=hardening.meaning_report(rows)
        self.assertTrue(report['complete'])
        self.assertEqual((report['attempts'],report['successful'],report['success_fraction']),(6,0,0))
        self.assertIsNone(report['median_ms']);self.assertIsNone(report['p95_ms'])
        self.assertEqual(report['reasons'],{'blocked':6})
        rows[0]=dict(case=0,kind='live',live=True,cached=False,mock=False,status='success',meaning_verified=True,duration_ms=500)
        self.assertEqual(hardening.meaning_report(rows)['median_ms'],500)
        rows[0]['mock']=True
        self.assertFalse(hardening.meaning_report(rows)['complete'])

    def test_optional_online_cache_requires_real_successful_seed_and_bounded_workload(self):
        uncached=dict(sample(1),kind='uncached',from_cache=False)
        cached=dict(sample(2,case=1),kind='cache',from_cache=True,seeded=True)
        self.assertTrue(hardening.online_report([uncached,cached])['complete'])
        self.assertFalse(hardening.online_report([cached])['complete'])
        self.assertFalse(hardening.online_report([uncached]*4)['complete'])
        self.assertTrue(hardening.online_report([])['complete'])

    def test_sustained_protocol_growth_reset_and_missing_samples_reject(self):
        baseline=stability()
        self.assertTrue(hardening.stability_report(baseline)['passed'])
        for change in ('rss','protocol','reset','missing','children','count'):
            data=deepcopy(baseline)
            if change=='rss':
                for row in data['resources'][-6:]:row['rss_bytes']+=32<<20
            elif change=='protocol':data['protocol']['rss_absolute_bytes']=1<<30
            elif change=='reset':data['completions'][-1]['process_start']+=1
            elif change=='missing':data['resources'].pop()
            elif change=='children':data['cooldown']['owned_children']=[99]
            else:data['history_delta']=321
            with self.subTest(change=change):self.assertFalse(hardening.stability_report(data)['passed'])

    def test_burst_counts_only_accepted_completions_but_requires_latest_and_integrity(self):
        data=dict(mode='native',inputs=[dict(sequence=i,request=i,input_ns=i*50_000_000,physical=True,released=True) for i in range(1,11)],
                  accepted_requests=[3,10],final_request=10,history_delta=2,enrichment_extra_count=0,integrity='ok',
                  identity=[20,2000,20000],process_start_source='proc_stat',final_identity=[20,2000,20000,10],final_frame_sha256='a'*64,
                  gates={key:True for key in hardening.BURST_GATES})
        self.assertTrue(hardening.burst_report(data)['passed'])
        for changes in (dict(history_delta=10),dict(final_request=3),dict(integrity='corrupt')):
            self.assertFalse(hardening.burst_report(dict(data,**changes))['passed'])
        slow=deepcopy(data)
        for row in slow['inputs']:row['input_ns']*=10
        self.assertFalse(hardening.burst_report(slow)['passed'])

    def test_two_actual_fullscreen_games_relative_mouse_and_resumed_gameplay_required(self):
        rows=[game('Wesnoth',multiline=True),game('Freedoom',relative=True)]
        self.assertTrue(hardening.games_report(rows)['passed'])
        self.assertFalse(hardening.games_report(rows[:1])['passed'])
        for change in ('mock','windowed','relative','resume','same_frame'):
            data=deepcopy(rows)
            if change=='mock':data[0]['evidence']='qt_fixture'
            elif change=='windowed':data[0]['mode']='windowed'
            elif change=='relative':data[1]['pointer_locked']=False
            elif change=='resume':data[1]['gates']['control_returned']=False
            else:data[1]['post_dismiss_sha256']=data[1]['frame_sha256']
            with self.subTest(change=change):self.assertFalse(hardening.games_report(data)['passed'])

    def test_strict_gates_and_phase7_false_exception_remain_honest(self):
        for invalid in (False,None,1,'skipped','mock'):
            self.assertFalse(hardening.strict_gates({'required':invalid},{'required'}))
        self.assertFalse(hardening.strict_gates({}, {'required'}))
        raw=dict(passed=False,cleanup=dict(original_preserved=False),evidence='unchanged')
        carried=hardening.carry_phase7(raw)
        self.assertIs(carried['raw'],raw)
        self.assertIs(carried['raw']['passed'],False)
        self.assertEqual(carried['actor'],'unknown')

    def test_privacy_and_faults_need_actual_owned_observations_and_fixed_required_gates(self):
        data=dict(mode='native',capture_files=[],gates={key:True for key in hardening.PRIVACY_GATES})
        for name in ('primary','clipboard','klipper'):
            data[name+'_before']=data[name+'_after']='a'*64
        self.assertTrue(hardening.privacy_report(data)['passed'])
        self.assertFalse(hardening.privacy_report(dict(data,clipboard_after='b'*64))['passed'])
        self.assertFalse(hardening.privacy_report(dict(data,capture_files=['residual.png']))['passed'])
        faults=[dict(fault=name,kind='injected' if name=='capture' else 'real',mode='native',
                     gates={key:True for key in hardening.FAULT_GATES}) for name in ('network','dictionary','capture')]
        self.assertTrue(hardening.faults_report(faults)['passed'])
        faults[0]['kind']='injected'
        self.assertFalse(hardening.faults_report(faults)['passed'])
