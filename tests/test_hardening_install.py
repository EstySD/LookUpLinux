"""Clean-profile and real-login evidence must fail closed."""
from copy import deepcopy
import unittest
from tools import check_hardening_install as install


def baseline():
    return dict(vm=install.CLONE,disk=install.DISK,original_off=True,uid=1002,user='lookup08install',
        home='/home/lookup08install',home_owned=True,package_installed=False,lookup_paths=[],
        dependencies=[dict(name='python',version='3.14')],observed=True,at_ns=100)


class InstallEvidenceTests(unittest.TestCase):
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
