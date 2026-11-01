"""Physical known unrelated binding before/after exact product deactivation."""
import json,runpy,sys,time
from pathlib import Path
root=Path('.planning/phases/08-vm');host=runpy.run_path(str(root/'08-07-registry-host.py'));n=host['n']
phase=sys.argv[1];assert phase in ('before','after')
snapshot="import json,time;from pathlib import Path;p=Path('/home/lookup07/.local/state/lookup-final-07/marker.jsonl');print(json.dumps(dict(at_ns=time.monotonic_ns(),rows=[json.loads(line) for line in p.read_text().splitlines()] if p.exists() else [])))"
baseline=json.loads(n['guest'](snapshot));fixture=json.loads((root/'08-07-registry-retarget-fixture.json').read_text())['fixture']
code='57' if fixture['key'].endswith('F11') else '58';release='d7' if code=='57' else 'd8'
codes='e0 5b 1d 2a '+code+' '+release+' aa 9d e0 db'
started=time.time_ns();result=n['inputs']('Keys',Codes=codes)
deadline=time.monotonic()+5
while True:
    after=json.loads(n['guest'](snapshot))
    if len(after['rows'])==len(baseline['rows'])+1:break
    if time.monotonic()>deadline:
        (root/('08-07-unrelated-marker-'+phase+'-failed.json')).write_text(json.dumps(dict(before=baseline,after=after,fixture=fixture,input=dict(codes=codes,dispatch_host_wall_ns=started,result=result))))
        raise TimeoutError('Actual unrelated marker did not execute')
    time.sleep(.1)
new=after['rows'][-1];assert new['uid']==1001 and baseline['at_ns']<=new['at_ns']<=after['at_ns']
value=dict(phase=phase,fixture=fixture,input=dict(target=n['CLONE'],codes=codes,dispatch_host_wall_ns=started,exit=result['exit']),before=baseline,after=after,marker=new)
(root/('08-07-unrelated-marker-'+phase+'.json')).write_text(json.dumps(value,indent=2));print(json.dumps(value))
