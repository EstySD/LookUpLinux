import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('vm_spike', Path(__file__).resolve().parents[1]/'tools/vm_spike.py')
spike = importlib.util.module_from_spec(spec)
spec.loader.exec_module(spike)


class SpikeTests(unittest.TestCase):
    def test_token_cap_and_desktop_exec(self):
        for token in ('', 'token', 'x'*4096):
            self.assertTrue(spike.valid_token(token))
        for token in ('x'*4097, '\x00', None, '\ud800'):
            self.assertFalse(spike.valid_token(token))
        text = spike.desktop_text(Path('/usr/bin/python3').resolve(), Path('/tmp/spike $ " %.py').resolve())
        self.assertIn('X-KDE-Shortcuts=Meta+Shift+D', text)
        self.assertIn('%%.py', text)
        self.assertIn('\\$', text)
        with self.assertRaises(ValueError):
            spike.desktop_text('relative', 'script.py')

    def test_pipeline_order_geometry_and_private_word(self):
        from types import SimpleNamespace
        monitor = spike.platform.Monitor('m', -100, 0, 100, 100, 2)
        order = []
        with patch.object(spike.platform, 'cursor_position', side_effect=lambda e: order.append('cursor') or (-75, 50)), \
             patch.object(spike.platform, 'monitors', return_value=(monitor,)), \
             patch.object(spike.capture, 'capture_monitor', side_effect=lambda *a: order.append('capture') or SimpleNamespace(png=b'png',width=200,height=200,elapsed_ms=10)), \
             patch.object(spike.ocr, 'recognize_image', side_effect=lambda data,point: order.append(('ocr',point)) or SimpleNamespace(selection=SimpleNamespace(word='private'),timings={'total':20})):
            result = spike.pipeline({}, 'screenshot2', False)
        self.assertEqual(order, ['cursor', 'capture', ('ocr', (50, 100))])
        self.assertIsNone(result['word'])
        self.assertTrue(result['found'])

    def test_wait_is_bounded_and_accepts_only_observation(self):
        from tools.check_vm_spike import wait_for
        observations=iter([{'ready':False},{'ready':True}])
        self.assertEqual(wait_for(lambda:next(observations),lambda s:s['ready'],1),{'ready':True})
        with self.assertRaisesRegex(RuntimeError,'gate_timeout'):
            wait_for(lambda:False,bool,.02)
        with patch('tools.check_vm_spike.time.sleep'), patch('tools.check_vm_spike.remote',side_effect=[RuntimeError('owner starting'),{'ready':True}]) as read:
            self.assertEqual(wait_for(lambda:read(),lambda s:s.get('ready'),1),{'ready':True})

    def test_guest_input_forces_distinct_position_and_hides_helper(self):
        from tools import check_vm_spike as harness
        with patch.object(harness.subprocess,'CREATE_NO_WINDOW',0x08000000,create=True), \
             patch.object(harness.subprocess,'run') as process, patch.object(harness.time,'sleep'):
            harness.pointer(100,200)
        command=process.call_args.args[0][-1]
        self.assertIn('PutMouseEventAbsolute(102,201,0,0,0)',command)
        self.assertIn('PutMouseEventAbsolute(101,201,0,0,0)',command)
        self.assertIn('finally { $s.UnlockMachine() }',command)
        self.assertEqual(process.call_args.kwargs['creationflags'],0x08000000)

    def test_setup_failure_at_registration_and_between_launches_rolls_back(self):
        from tools.check_vm_spike import setup_owned
        import tempfile
        for failure in ('register','launch'):
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as folder:
                desktop=Path(folder)/'owned.desktop'
                snapshots=[]
                launch=unittest.mock.Mock(side_effect=[123,RuntimeError('launch failed')])
                register=unittest.mock.Mock(side_effect=RuntimeError('register failed') if failure=='register' else None)
                def rollback():
                    desktop.unlink()
                with self.assertRaises(RuntimeError):
                    setup_owned(desktop,'owned',register,launch,lambda p:snapshots.append(list(p)),rollback)
                self.assertFalse(desktop.exists())
                self.assertEqual(snapshots,[[]] if failure=='register' else [[],[123]])

    def test_failed_setup_and_key_release_still_restore_and_write_evidence(self):
        from tools import check_vm_spike as harness
        import tempfile,json
        def remote(action,payload):
            if action=='setup':
                raise RuntimeError('response lost after setup')
            return dict(display_restored=True,desktop_restored=True,processes_stopped=True,shortcut_restored=True)
        with tempfile.TemporaryDirectory() as folder, patch.object(harness,'remote',side_effect=remote) as request, \
             patch.object(harness,'keys',side_effect=RuntimeError('key release failed')),patch('builtins.print'):
            output=Path(folder)/'result.json'
            self.assertEqual(harness.host(output),1)
            evidence=json.loads(output.read_text())
            self.assertIn('key_release_error',evidence)
            self.assertTrue(evidence['restoration']['desktop_restored'])
            self.assertEqual([call.args[0] for call in request.call_args_list],['setup','finish'])
            self.assertEqual(request.call_args_list[0].args[1]['run_id'],request.call_args_list[1].args[1]['run_id'])

    def test_every_required_restoration_flag_is_mandatory(self):
        from tools.check_vm_spike import accepted
        flags=dict(display_restored=True,desktop_restored=True,processes_stopped=True,shortcut_restored=True)
        self.assertTrue(accepted(dict(restoration=flags,required_remaining=[])))
        for name in flags:
            self.assertFalse(accepted(dict(restoration=dict(flags,**{name:False}),required_remaining=[])))
        self.assertFalse(accepted(dict(restoration=flags,required_remaining=[],restoration_error='failed')))

    def test_vm_unlock_rechecks_and_targets_only_owned_wayland_session(self):
        from tools import check_vm_spike as harness
        rows=b'1 1000 arch seat0\n2 2000 other seat1\n3 1000 arch -\n'
        def run(argv,env):
            if argv[1]=='list-sessions':return rows
            if argv[1]=='show-session':return b'wayland\n' if argv[2]=='1' else b'tty\n'
            return b''
        with patch.object(harness.platform,'run',side_effect=run) as command:
            locked=iter([True,False])
            self.assertTrue(harness.ensure_unlocked({},lambda:next(locked),1000))
        unlocks=[c.args[0] for c in command.call_args_list if c.args[0][1]=='unlock-session']
        self.assertEqual(unlocks,[['loginctl','unlock-session','1']])

    def test_relative_input_fallback_requires_observed_convergence(self):
        from tools import check_vm_spike as harness
        with patch.object(harness,'pointer'),patch.object(harness,'wait_for',side_effect=harness.GateTimeout([0,0])), \
             patch.object(harness,'relative_pointer') as movement:
            points=iter([[0,0],[100,50]])
            self.assertEqual(harness.move_pointer((100,50),1,lambda action:next(points)),'relative_feedback')
            movement.assert_called_once_with(100,50)
        with patch.object(harness,'pointer'),patch.object(harness,'wait_for',side_effect=harness.GateTimeout([0,0])), \
             patch.object(harness,'relative_pointer'):
            with self.assertRaises(harness.GateTimeout):
                harness.move_pointer((100,50),1,lambda action:[0,0])


if __name__ == '__main__':
    unittest.main()
