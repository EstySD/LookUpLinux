"""Adversarial evidence is rejected before any native acceptance is attempted."""
from copy import deepcopy
import json
from pathlib import Path
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
    def test_reused_attempt_cannot_reuse_previous_arm_result(self):
        command=dict(attempt=1,token=200)
        self.assertTrue(hardening.matching_result(dict(command),command))
        for result in (dict(attempt=1,token=100),dict(attempt=2,token=200),dict(attempt=1),{}):
            self.assertFalse(hardening.matching_result(result,command))

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
        data=dict(mode='native',inputs=[dict(sequence=i,request=i,physical=True,released=True) for i in range(1,11)],
                  accepted_requests=[3,10],final_request=10,history_delta=2,enrichment_extra_count=0,integrity='ok',
                  identity=[20,2000,20000],process_start_source='proc_stat',final_identity=[20,2000,20000,10],final_frame_sha256='a'*64,
                  gates={key:True for key in hardening.BURST_GATES})
        self.assertTrue(hardening.burst_report(data)['passed'])
        for changes in (dict(history_delta=10),dict(final_request=3),dict(integrity='corrupt')):
            self.assertFalse(hardening.burst_report(dict(data,**changes))['passed'])

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
