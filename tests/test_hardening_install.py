"""Clean-profile and real-login evidence must fail closed."""
from copy import deepcopy
import unittest
from tools import check_hardening_install as install


def baseline():
    return dict(vm=install.CLONE,disk=install.DISK,original_off=True,uid=1002,user='lookup08install',
        home='/home/lookup08install',home_owned=True,package_installed=False,lookup_paths=[],
        dependencies=[dict(name='python',version='3.14')],observed=True,at_ns=100)


def actual_install_fixture():
    import json
    from pathlib import Path
    root=Path('.planning/phases/08-vm')
    def read(name):return json.loads((root/('08-install-'+name+'.json')).read_text())
    return dict(baseline=read('clean-graphical-baseline'),gates={key:True for key in install.GATES},
        enabled_login=read('login-enabled'),disabled_login=read('login-disabled'),retention_before=read('retention-before-remove'),
        removed_physical=read('removed-physical-automatic'),installed=read('installed-identity'),physical_capture=read('physical-useful'),
        cleanup={key:True for key in ('owner_stopped','fixture_stopped','input_released','session_override_restored',
            'clone_powered_off','original_powered_off','clipboard_restored')})


class InstallEvidenceTests(unittest.TestCase):
    def test_partial_identity_retention_cleanup_and_wrong_login_role_cannot_pass(self):
        self.assertTrue(install.install_report(actual_install_fixture())['passed'])
        for change in ('files','hashes','cleanup','role'):
            data=actual_install_fixture()
            if change=='files':data['installed']['files']={}
            elif change=='hashes':
                data['retention_before']['hashes']={};data['removed_physical']['after_unrelated']['retention']['hashes']={}
            elif change=='cleanup':data['cleanup']={'done':True}
            else:data['disabled_login']=deepcopy(data['enabled_login'])
            with self.subTest(change=change):self.assertFalse(install.install_report(data)['passed'])
    def test_clean_owned_inventory_passes_but_old_profile_and_package_cannot(self):
        self.assertTrue(install.clean_baseline(baseline()))
        for change in ('vm','disk','original_off','uid','user','home','home_owned','package_installed','lookup_paths','dependencies','observed'):
            data=baseline()
            data[change]=({'vm':'original','disk':'other','uid':1001,'user':'lookup07','home':'/home/lookup07',
                'lookup_paths':['.config/lookup/config.json'],'dependencies':[]}.get(change,False if change!='package_installed' else True))
            with self.subTest(change=change):self.assertFalse(install.clean_baseline(data))

    def test_missing_install_login_and_active_key_preservation_evidence_rejects(self):
        for data in ({},dict(baseline=baseline()),dict(baseline=baseline(),gates={'package_removed':True})):
            self.assertFalse(install.install_report(data)['passed'])

    def test_stale_owner_and_manual_app_launch_cannot_prove_login(self):
        good=dict(observed=True,observer_launches_product=False,owner_before=False,session_before='1',session_after='2',
            session_type='wayland',user='lookup08install',uid=1002,login_ns=1000,observed_until_ns=12_000_001_000,
            enabled=True,owners=[dict(pid=40,start_ns=2000,uid=1002,argv=['/usr/bin/python','/usr/bin/lookup','--autostart'])])
        good['before']=dict(owner=False,sessions=[dict(Id='1')])
        good['samples']=[dict(at_ns=stamp,owner=True,process=deepcopy(good['owners'][0]),
            sessions=[dict(Id='2',Type='wayland',Service='sddm-autologin')]) for stamp in (3000,12_000_001_000)]
        self.assertTrue(install.login_evidence(good))
        for change in ('same_session','old_owner','manual','wrong_uid','short'):
            data=deepcopy(good)
            if change=='same_session':data['session_after']='1'
            elif change=='old_owner':data['owners'][0]['start_ns']=900
            elif change=='manual':data['observer_launches_product']=True
            elif change=='wrong_uid':data['owners'][0]['uid']=1001
            else:data['observed_until_ns']=2000
            with self.subTest(change=change):self.assertFalse(install.login_evidence(data))

    def test_empty_samples_or_multiple_owner_identities_cannot_prove_login(self):
        import json
        from pathlib import Path
        path=Path('.planning/phases/08-vm/08-install-login-enabled.json')
        data=json.loads(path.read_text())
        self.assertTrue(install.login_evidence(data))
        empty=deepcopy(data);empty['samples']=[]
        self.assertFalse(install.login_evidence(empty))
        other=deepcopy(data);extra=deepcopy(other['owners'][0]);extra['pid']+=1;other['owners'].append(extra)
        self.assertFalse(install.login_evidence(other))
        reverse=deepcopy(data);reverse['samples'].reverse()
        self.assertFalse(install.login_evidence(reverse))

    def test_observed_login_interval_and_owner_survival_are_required(self):
        import json
        from pathlib import Path
        root=Path('.planning/phases/08-vm')
        enabled=json.loads((root/'08-install-login-enabled.json').read_text());seen=False
        for sample in enabled['samples']:
            if seen:sample['owner']=False;sample.pop('process',None)
            elif sample['owner']:seen=True
        self.assertFalse(install.login_evidence(enabled))
        disabled=json.loads((root/'08-install-login-disabled.json').read_text());disabled['samples']=disabled['samples'][-2:]
        self.assertFalse(install.login_evidence(disabled))
