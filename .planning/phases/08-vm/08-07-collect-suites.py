"""Load actual completed full-suite receipts/log bytes without inventing outcomes."""
import argparse,base64,hashlib,json,runpy
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--host',type=Path);args=parser.parse_args()
root=Path('.planning/phases/08-vm');n=runpy.run_path(str(root/'08-07-native.py'))
destination=root/'08-gap-final-suites.json';suites=json.loads(destination.read_text()) if destination.exists() else {}
if args.host:
    record=json.loads((args.host/'host-suite.json').read_text());data=(args.host/record['log']).read_bytes()
    assert hashlib.sha256(data).hexdigest()==record['log_sha256']
    record['log']='08-gap-final-host.log';(root/record['log']).write_bytes(data);suites['host']=record
else:
    launch=json.loads((root/'08-07-target-launch.json').read_text());directory=launch['home'].rstrip('/')+'/results'
    script='''import base64,json
from pathlib import Path
root=Path('''+repr(str(directory))+''');receipt=root/'target-suite.json'
if not receipt.exists():
    log=root.parent.parent/'launcher.log';print(json.dumps(dict(status='running',tail=log.read_text()[-3000:] if log.exists() else 'launcher log missing')))
else:
    record=json.loads(receipt.read_text());print(json.dumps(dict(status='finished',record=record,log_base64=base64.b64encode((root/record['log']).read_bytes()).decode())))'''
    value=json.loads(n['guest'](script))
    if value['status']!='finished':print(json.dumps(value));raise SystemExit(0)
    record=value['record'];data=base64.b64decode(value['log_base64']);assert hashlib.sha256(data).hexdigest()==record['log_sha256']
    record['log']='08-gap-final-target.log';(root/record['log']).write_bytes(data);suites['target']=record
destination.write_text(json.dumps(suites,indent=2));print(json.dumps({name:{key:row[key] for key in ('revision','tree','exit','count','skips')} for name,row in suites.items()}))
