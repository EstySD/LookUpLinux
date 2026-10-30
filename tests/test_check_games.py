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


def captured_record():
    data=record();data.update(name='Freedoom Phase 2',engine='Chocolate Doom',engine_version='3.1.1',version='0.13.0')
    data['process']['executable']='/home/lookup07/.local/state/lookup-games-08/doom/chocolate-doom'
    data['acquisition']=dict(source_url='https://api.github.com/repos/chocolate-doom/chocolate-doom/tarball/chocolate-doom-3.1.1',
        source_sha256='c'*64,assets_url='https://github.com/freedoom/freedoom/releases/download/v0.13.0/freedoom-0.13.0.zip',
        assets_sha256='d'*64,wad_sha256='e'*64,checksum_status='not_published',checksum_absence_evidence='official release API assets and404')
    for entry in data['routes']:
        entry['scene']='map01_captured_prompt';stamp=entry['timing']['input_ns']
        entry['grab']=dict(relative=True,observed=True,pid=500,start=5000,at_ns=stamp-1000,
            protocol='zwp_locked_pointer_v1',lock_event_ns=stamp-2000,events_sha256='f'*64)
        for offset,(key,kind) in enumerate((('camera','relative_pointer'),('movement','movement_key'))):
            entry['gameplay'][key]=dict(physical=True,game_active=True,game_pid=500,game_start=5000,
                kind=kind,input_ns=entry['gameplay']['input_ns']+offset,
                before_sha256=f"{entry['sequence']*4+offset:x}"*64,after_sha256=f"{entry['sequence']*4+offset+1:x}"*64)
    return data


def assaultcube_record():
    import hashlib,json
    data=captured_record();data.update(name='AssaultCube',engine='AssaultCube',engine_version='1.3.0.2',version='1.3.0.2')
    data['process']['executable']='/home/lookup07/.local/state/lookup-games-08/assaultcube/package/bin_unix/linux_64_client'
    data['acquisition']=dict(url='https://github.com/assaultcube/AC/releases/download/v1.3.0.2/AssaultCube_v1.3.0.2_LockdownEdition_RC1.tar.bz2',
        bytes=52071427,sha256='9b3118e7929253f0114fa06cad8310faab646d177b4660406011152f34086b55',release_asset='RC1')
    text='AssaultCube 1.3.0.2\nRenderer: llvmpipe (LLVM 21.1) (Mesa)\nDriver: 4.5 Mesa 25.3\n'
    data['renderer']=dict(name='llvmpipe (LLVM 21.1) (Mesa)',observed=True,pid=500,start=5000,kind='game_gl_log',
        text=text,log_sha256=hashlib.sha256(text.encode()).hexdigest())
    for entry in data['routes']:
        entry['scene']='local_map_scoreboard';stamp=entry['timing']['input_ns'];grab=entry['grab']
        events=[dict(pid=500,at_ns=stamp-2000,message='zwp_locked_pointer_v1#12.locked()')]
        relative=[dict(pid=500,at_ns=stamp-3000,operation='relative',requested=1,result=0,state=1,driver='wayland')]
        grab.update(events_sha256=hashlib.sha256(json.dumps(events).encode()).hexdigest(),events=events,
            sdl=relative,driver='wayland')
        for kind in ('camera','movement'):
            entry['gameplay'][kind]['world_change']=dict(rect=[128,160,384,360],pixels=138240,changed_pixels=10000,
                before_sha256='1'*64,after_sha256='2'*64)
        camera=entry['gameplay']['camera'];stamp=camera['input_ns']
        camera.update(input_events=[dict(type=2,code=0,value=60,input_ns=stamp),dict(type=2,code=0,value=60,input_ns=stamp+100)],capture_end_ns=stamp+200)
    return data


class GameContractTests(unittest.TestCase):
    def test_cleanup_release_and_guest_failure_cannot_skip_shutdown_or_off_restore(self):
        from unittest.mock import patch
        clone='cf207909-94b5-4b49-8bd8-ccff973c1dc8';calls=[]
        machine=dict(UUID='"'+clone+'"',VMState='"running"',clipboard='"disabled"',accelerate3d='"off"',
            **{'"SATA-ImageUUID-0-0"':'"2712d710-daaa-449c-843d-d570091127bc"'})
        prior=dict(machine,clipboard='"bidirectional"',accelerate3d='"on"')
        def info(identity):return dict(machine) if identity==clone else dict(VMState='"poweroff"')
        def guest(command):
            calls.append(command)
            if 'pilot-cleanup' in command:raise OSError('controlled SSH failure')
            machine['VMState']='"poweroff"'
            return ''
        def run(*args):calls.append(args);machine.update(clipboard=prior['clipboard'],accelerate3d=prior['accelerate3d']);return dict(exit=0)
        def inputs(*args,**kwargs):raise OSError('controlled release failure')
        with patch('tools.check_games.time.sleep'):
            result=check_games.pilot_cleanup_steps(prior,{},info,run,guest,inputs)
        self.assertFalse(result['release']['ok']);self.assertFalse(result['guest_cleanup']['ok'])
        self.assertTrue(result['clone_off']);self.assertTrue(result['settings_restored'])
        self.assertIn('sudo -n systemctl poweroff',calls)
        self.assertTrue(any(isinstance(call,tuple) and 'modifyvm' in call for call in calls))
    def test_assaultcube_explicit_gl_and_actual_relative_evidence(self):
        self.assertTrue(check_games.captured_game_report(assaultcube_record())['passed'])
        for change in ('url','bytes','hash','executable','uid','gl_missing','gl_digest','gl_identity','driver',
                       'relative_failure','relative_disabled','unlock','stale_state','no_query','box','overlay','idle_only'):
            data=assaultcube_record();row=data['routes'][0]
            if change=='url':data['acquisition']['url']='https://example.invalid/game'
            elif change=='bytes':data['acquisition']['bytes']-=1
            elif change=='hash':data['acquisition']['sha256']='a'*64
            elif change=='executable':data['process']['executable']='/tmp/game'
            elif change=='uid':data['process']['uid']=1000
            elif change=='gl_missing':data['renderer'].pop('text')
            elif change=='gl_digest':data['renderer']['text']+='different'
            elif change=='gl_identity':data['renderer']['start']=999
            elif change=='driver':row['grab']['sdl'][-1]['driver']='x11'
            elif change=='relative_failure':row['grab']['sdl'][-1]['result']=-1
            elif change=='relative_disabled':row['grab']['sdl'][-1]['state']=0
            elif change=='unlock':
                import hashlib,json
                row['grab']['events'].append(dict(pid=500,at_ns=row['timing']['input_ns']-500,message='zwp_locked_pointer_v1#12.unlocked()'))
                row['grab']['events_sha256']=hashlib.sha256(json.dumps(row['grab']['events']).encode()).hexdigest()
            elif change=='stale_state':row['grab']['sdl'][-1]['at_ns']=row['timing']['input_ns']+1
            elif change=='no_query':row['source'].pop('query')
            elif change=='box':row['source']['word_rect']=[0,0,1,1]
            elif change=='idle_only':row['gameplay']['camera']['world_change']['changed_pixels']=6
            else:row['overlay']['useful']=False
            with self.subTest(change=change):self.assertFalse(check_games.captured_game_report(data)['passed'])

    def test_actual_rejected_first_camera_differs_only_in_idle_overlay_not_world(self):
        from pathlib import Path
        root=Path('.planning/phases/08-vm')
        value=check_games.world_change((root/'08-06-raw-control-522383335795-before.png').read_bytes(),
            (root/'08-06-raw-control-522383335795-after.png').read_bytes())
        self.assertLess(value['changed_pixels'],1383)
        rotation=check_games.world_change((root/'08-06-raw-control-583541202128-before.png').read_bytes(),
            (root/'08-06-raw-control-583541202128-after.png').read_bytes())
        self.assertGreaterEqual(rotation['changed_pixels'],1383)
        data=assaultcube_record();data['routes'][0]['gameplay']['camera']['input_events'].pop()
        self.assertFalse(check_games.captured_game_report(data)['passed'])
    def test_captured_game_rejects_missing_actual_provenance_grab_and_camera_proof(self):
        for value in ({},record(),dict(record(),name='Freedoom Phase 2',relative=True)):
            self.assertFalse(check_games.captured_game_report(value)['passed'])

    def test_captured_route_requires_each_physical_camera_and_movement_change(self):
        data=record();data.update(name='Freedoom Phase 2',engine='Chocolate Doom',engine_version='3.1.1')
        data['acquisition']=dict(source_url='https://api.github.com/repos/chocolate-doom/chocolate-doom/tarball/chocolate-doom-3.1.1',
            source_sha256='c'*64,assets_url='https://github.com/freedoom/freedoom/releases/download/v0.13.0/freedoom-0.13.0.zip',
            assets_sha256='d'*64,checksum_verified=True,wad_sha256='e'*64)
        self.assertFalse(check_games.captured_game_report(data)['passed'])

    def test_captured_contract_accepts_supported_proof_but_rejects_missing_individual_gates(self):
        self.assertTrue(check_games.captured_game_report(captured_record())['passed'])
        for change in ('grab','old_grab','grab_identity','events','camera','movement','kind','checksum','hash','source'):
            data=captured_record();entry=data['routes'][1]
            if change=='grab':entry['grab']['relative']=False
            elif change=='old_grab':entry['grab']['at_ns']-=3_000_000_000
            elif change=='grab_identity':entry['grab']['start']=99
            elif change=='events':entry['grab'].pop('events_sha256')
            elif change in ('camera','movement'):entry['gameplay'][change]['after_sha256']=entry['gameplay'][change]['before_sha256']
            elif change=='kind':entry['gameplay']['camera']['kind']='absolute_pointer'
            elif change=='checksum':data['acquisition'].pop('checksum_absence_evidence')
            elif change=='hash':data['acquisition']['wad_sha256']='invented'
            else:entry['source']['pid']=999
            with self.subTest(change=change):self.assertFalse(check_games.captured_game_report(data)['passed'])

    def test_captured_controls_reject_other_process_and_reused_action_evidence(self):
        for change in ('pid','start','same_input','same_frames'):
            data=captured_record();play=data['routes'][0]['gameplay']
            if change=='pid':play['camera']['game_pid']=999
            elif change=='start':play['movement']['game_start']=999
            elif change=='same_input':play['movement']['input_ns']=play['camera']['input_ns']
            else:
                for key in ('before_sha256','after_sha256'):play['movement'][key]=play['camera'][key]
            with self.subTest(change=change):self.assertFalse(check_games.captured_game_report(data)['passed'])

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
        data=record();source=data['routes'][0]['source'];source.update(word='m.ove',query='m.ove',context='Now m.ove\nto the keep.',span=[4,9])
        data['routes'][0]['overlay']['current_word']='m.ove'
        self.assertFalse(check_games.game_report(data)['passed'])
