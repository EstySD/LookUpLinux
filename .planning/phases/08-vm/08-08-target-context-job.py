"""Retain isolated scheduler retry separately and measure full144 context corpus."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
from lookup import ocr
root=Path.cwd();target=root/'08-08-target-context-progress.json';steps=[]
def save(state,active=None):target.write_text(json.dumps(dict(state=state,active=active,steps=steps)))
for name,command in (
    ('isolated_boundary',[sys.executable,'-m','unittest','tests.test_platform.BoundaryTests.test_child_deadline_and_output_cap']),
    ('context144',[sys.executable,'tools/check_context_images.py','--output','08-08-context-corpus'])):
    save('running',name);started=time.monotonic()
    result=subprocess.run(command,capture_output=True,text=True,timeout=900,env=dict(os.environ,QT_QPA_PLATFORM='offscreen',OMP_THREAD_LIMIT='1'))
    steps.append(dict(name=name,exit=result.returncode,elapsed_seconds=time.monotonic()-started,stdout=result.stdout,stderr=result.stderr))
prepared=[]
for case in json.loads((root/'tests/fixtures/ocr-games/manifest.json').read_text())['cases']:
    png,transform=ocr._prepare_image(root/'tests/fixtures/ocr-games'/case['path'],case['point'],2,'auto')
    prepared.append(dict(path=case['path'],actual_sha256=hashlib.sha256(png).hexdigest(),native_reference=case['prepared_sha256']))
steps.append(dict(name='prepared_hashes',cases=prepared,exit=0))
save('passed' if all(row['exit']==0 for row in steps) else 'failed')
