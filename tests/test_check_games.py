"""Game routes require real process/frame/input/control proof, not fixture success."""
from copy import deepcopy
import unittest

from tests.test_hardening import sample
from tools import check_games


def route(index):
    timing=sample(index,latency=1200)
    return dict(sequence=index,scene='tutorial_map_dialogue',game_pid=500,game_start=5000,
        window_id='real-game-window',game_active_before=True,
        source=dict(kind='actual_game',mode='ocr',backend='screenshot2',sha256=f'{index+100:064x}',
            pid=timing['pid'],run=timing['run'],request=timing['request'],span=[4,8],
            capture_start_ns=timing['input_ns']+100_000_000,capture_end_ns=timing['input_ns']+300_000_000,
            word='move',query='move',context='Now move your unit\nto the marked keep. '+str(index),
            visual_lines=2,cursor=[320,400],word_rect=[300,390,80,25],unchanged_objects=True),
        timing=timing,overlay=dict(useful=True,loading=False,error=False,current_word='move',
            sha256=timing['frame_sha256'],identity=timing['frame_identity']),
        dismissal=dict(physical=True,released=True,at_ns=timing['first_visible_end_ns']+100_000_000,closed=True),
        gameplay=dict(physical=True,action='select_unit',game_active=True,game_pid=500,game_start=5000,
            before_sha256=f'{index+200:064x}',after_sha256=f'{index+300:064x}',observed_change=True,
            input_ns=timing['first_visible_end_ns']+200_000_000))


def record():
    return dict(name='The Battle for Wesnoth',version='1.18.8',source_verified=True,
        package=dict(name='wesnoth',repository='extra',version='1:1.18.8-2',signature_verified=True,
                     archive_sha256='a'*64,source='official_arch'),
        process=dict(pid=500,start=5000,uid=1001,executable='/usr/bin/wesnoth'),
        renderer=dict(name='software',observed=True,log_sha256='b'*64),
        mode='fullscreen',window=dict(id='real-game-window',pid=500,fullscreen=True,observed=True,
            rect=[0,0,1280,800],screen=[0,0,1280,800]),routes=[route(1),route(2)])


class GameContractTests(unittest.TestCase):
    def test_complete_changed_actual_game_routes_pass_without_closing_two_game_requirement(self):
        report=check_games.game_report(record())
        self.assertTrue(report['passed']);self.assertFalse(report['game01_complete'])

    def test_menu_qt_unverified_mode_and_absent_real_process_reject(self):
        for change in ('menu','qt','fullscreen','process','renderer','package'):
            data=record()
            if change=='menu':data['routes'][0]['scene']='main_menu'
            elif change=='qt':data['routes'][0]['source']['kind']='qt_fixture'
            elif change=='fullscreen':data['window'].pop('observed')
            elif change=='process':data['process']['pid']=0
            elif change=='renderer':data['renderer']['observed']=False
            else:data['package']['signature_verified']=False
            with self.subTest(change=change):self.assertFalse(check_games.game_report(data)['passed'])

    def test_stale_frame_missing_physical_resume_wrong_word_and_fixed_wait_reject(self):
        for change in ('same_scene','stale','resume','physical','word','clock','multiline'):
            data=record();row=data['routes'][1]
            if change=='same_scene':row['source']=deepcopy(data['routes'][0]['source'])
            elif change=='stale':row['source']['capture_end_ns']=row['timing']['input_ns']-1
            elif change=='resume':row['gameplay']['after_sha256']=row['gameplay']['before_sha256']
            elif change=='physical':row['gameplay']['physical']=False
            elif change=='word':row['overlay']['current_word']='previous'
            elif change=='clock':row['timing']['origin']='fixed_wait'
            else:
                for entry in data['routes']:
                    entry['source']['visual_lines']=1;entry['source']['context']=entry['source']['context'].replace('\n',' ')
            with self.subTest(change=change):self.assertFalse(check_games.game_report(data)['passed'])

    def test_read_only_tap_calls_original_once_and_returns_identical_object_even_if_observer_fails(self):
        result=object();calls=[];errors=[]
        def original():calls.append('called');return result
        def observer(*unused):raise RuntimeError('controlled_observer_failure')
        wrapped=check_games.tap(original,observer,errors.append)
        self.assertIs(wrapped(),result);self.assertEqual(calls,['called']);self.assertEqual(errors,['RuntimeError'])

    def test_reused_request_wrong_source_identity_and_raw_sequence_reject(self):
        for change in ('duplicate','source','sequence','span'):
            data=record();first,second=data['routes']
            if change=='duplicate':
                second['timing']=deepcopy(first['timing']);second['overlay']=deepcopy(first['overlay'])
                for key in ('pid','run','request','capture_start_ns','capture_end_ns'):second['source'][key]=first['source'][key]
            elif change=='source':second['source'].update(pid=999,run=999,request=999)
            elif change=='sequence':second['timing']['input_sequence']=99
            else:second['source']['span']=[0,3]
            with self.subTest(change=change):self.assertFalse(check_games.game_report(data)['passed'])

    def test_tap_error_logging_cannot_change_original_result_or_exception(self):
        result=object()
        def fail(*unused):raise OSError('controlled_logging_failure')
        self.assertIs(check_games.tap(lambda:result,fail,fail)(),result)
        original_error=ValueError('original_error')
        def original():raise original_error
        with self.assertRaises(ValueError) as caught:check_games.tap(original,fail,fail)()
        self.assertIs(caught.exception,original_error)

    def test_multiline_is_required_across_game_not_every_changed_scene(self):
        data=record();data['routes'][1]['source']['visual_lines']=1
        data['routes'][1]['source']['context']=data['routes'][1]['source']['context'].replace('\n',' ')
        self.assertTrue(check_games.game_report(data)['passed'])

    def test_only_matching_new_production_error_ends_route(self):
        trigger=dict(pid=20,run=200,request=3,mono_ns=1000)
        wrong=[dict(trigger,stage=6,pid=21,mono_ns=2000),dict(trigger,stage=6,request=2,mono_ns=2000),dict(trigger,stage=6,mono_ns=900)]
        self.assertIsNone(check_games.request_error(wrong,trigger,950))
        error=dict(trigger,stage=6,mono_ns=1500)
        self.assertIs(check_games.request_error(wrong+[error],trigger,950),error)

    def test_source_span_uses_canonical_boundary_punctuation_without_changing_raw_span(self):
        for token,accepted in (('MOVE,',True),('move now',False),('mo-ve',False),('m.ove',False),('time',False)):
            data=record();source=data['routes'][0]['source'];source['context']='Now '+token+'\nto the marked keep.'
            source['span']=[4,4+len(token)];raw=source['context'][slice(*source['span'])]
            with self.subTest(token=token):
                self.assertEqual(check_games.game_report(data)['passed'],accepted)
                self.assertEqual(source['context'][slice(*source['span'])],raw)
