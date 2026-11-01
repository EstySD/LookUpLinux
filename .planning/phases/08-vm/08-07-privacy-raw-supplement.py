"""Read-only retrieval of the already-observed09 privacy source and numeric trace."""
import base64,hashlib,json,runpy
from pathlib import Path
root=Path('.planning/phases/08-vm');n=runpy.run_path(str(root/'08-07-native.py'))
privacy=json.loads((root/'08-09-privacy-proof.json').read_text());source=privacy['source']
code='''import base64,hashlib,json
from pathlib import Path
root=Path('/home/lookup07/.local/state/lookup-games-08/assaultcube/lookup')
source=Path('''+repr(source['image_path'])+''');assert source.resolve().is_relative_to(root/'observations') and not source.is_symlink() and source.stat().st_uid==1001
data=source.read_bytes();trace=(root/'daemon.log').read_bytes()
print(json.dumps(dict(source_path=str(source),source_sha256=hashlib.sha256(data).hexdigest(),source_base64=base64.b64encode(data).decode(),trace_sha256=hashlib.sha256(trace).hexdigest(),trace_base64=base64.b64encode(trace).decode())))'''
value=json.loads(n['guest'](code));assert value['source_sha256']==source['sha256']
for key,name in (('source_base64','08-07-privacy-observed-source.png'),('trace_base64','08-07-privacy-observed-trace.log')):
    (root/name).write_bytes(base64.b64decode(value.pop(key)))
value.update(origin='Retained original09 files retrieved readonly after manual; no new capture or input.',identity={key:source[key] for key in ('pid','run','request')})
(root/'08-07-privacy-raw-supplement.json').write_text(json.dumps(value,indent=2));print(json.dumps(value))
