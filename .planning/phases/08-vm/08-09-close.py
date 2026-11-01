"""Freeze actual cleanup before the separately authorized interactive reboot."""
import json
from pathlib import Path
root=Path('.planning/phases/08-vm')
read=lambda name:json.loads((root/name).read_text(encoding='utf-8'))
controller=read('08-09-native-cleanup.json');nested=read('08-09-guest-cleanup.json');key=read('08-09-product-key-cleared.json')
product=json.loads(next(line for line in nested['product'].splitlines() if line.startswith('{')))
current=json.loads(next(line.split(':',1)[1] for line in nested['product'].splitlines() if line.startswith('lookup09-retention:')))
registry=json.loads(product['registry']['stdout'])
gates=dict(input_released=controller['release']['ok'] and controller['mouse_release']['ok'],owner_stopped=registry['owner'] is False,
    owned_processes_stopped=product['remaining']==current['remaining']==[],package_removed=product['package']['exit']==0 and product['package_absent'] and current['package_absent'],
    key_inactive=registry['keys']==key['after']==[],unrelated_shortcuts_preserved=key['unrelated_preserved'],
    original_data_retained=product['original_data_retained'],current_profiles_retained=current['retained'] and current['expected']==current['observed'],
    normal_profile_restored=nested['cleanup-profile']['retained_config_restored'] and nested['cleanup-profile']['environment_script_removed'],
    clone_off=controller['clone_off'],settings_restored=controller['settings_restored'],original_state_respected=controller['original_state_respected'])
assert not any('error' in nested[name] for name in ('stop-owner','cleanup-profile'))
result=dict(passed=all(value is True for value in gates.values()),gates=gates,controller_finished=read('08-09-native-controller-state.json')['state']=='finished',
    controller='08-09-native-cleanup.json',nested_cleanup='08-09-guest-cleanup.json',shutdown_transport=controller['shutdown'],
    current_retention=current,policy='USER_KEEP_RUNNING external original untouched; subsequent user-requested clone interactive boot is separate from this completed OFF cleanup.')
(root/'08-09-cleanup-final.json').write_text(json.dumps(result,indent=2));print(json.dumps(dict(passed=result['passed'],gates=gates)))
old=read('08-09-fallback-native-report.json');(root/'08-09-fast6-unaccepted-report.json').write_text(json.dumps(old,indent=2))
old['privacy_accepted']=False;old['limits']=['Twenty same-game completions all used fast6, so this is not accepted fallback coverage.','Raw equal clipboard probes lacked validated stderr; no privacy acceptance from them.']
(root/'08-09-fast6-unaccepted-report.json').write_text(json.dumps(old,indent=2))
support=read('08-09-fixture-support-report.json');privacy=read('08-09-privacy-proof.json');burst=read('08-09-burst-attempt-report.json')
final=dict(passed=support['passed'] and privacy['passed'] and burst['passed'] and result['passed'],
    changed_path=support,physical_burst=burst,classified_privacy=privacy['passed'],cleanup=result['passed'],
    raw=dict(completions='08-09-fixture-support-attempts.json',privacy='08-09-privacy-proof.json',burst='08-09-burst-attempt.json'),
    rejected_support='08-09-fast6-unaccepted-report.json',kind='Non-game resource support on unchanged original captured sparse source; not counted as game routes.')
(root/'08-09-fallback-native-report.json').write_text(json.dumps(final,indent=2))
