"""Actual target OCR corpus job; no product launch or production image substitution."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path

root=Path.cwd();progress=root/'08-08-target-progress.json'
report=dict(source_sha256=hashlib.sha256((root/'lookup/ocr.py').read_bytes()).hexdigest(),steps=[])
def save(state):
    temporary=progress.with_suffix('.tmp');temporary.write_text(json.dumps(dict(state=state,**report)));temporary.replace(progress)
commands=[
    ('render16', [sys.executable,'tools/gen_ocr_fixtures.py','--output','tests/fixtures/ocr']),
    ('focused', [sys.executable,'-m','unittest','tests.test_ocr_game_sources','tests.test_ocr_fallback','tests.test_ocr_image','tests.test_context_images','tests.test_ocr','tests.test_platform']),
    ('context144',[sys.executable,'tools/check_context_images.py','--output','08-08-context-corpus'])]
try:
    for name,command in commands:
        report['active']=name;save('running');started=time.monotonic()
        result=subprocess.run(command,capture_output=True,text=True,timeout=900,env=dict(os.environ,QT_QPA_PLATFORM='offscreen',OMP_THREAD_LIMIT='1'))
        report['steps'].append(dict(name=name,exit=result.returncode,elapsed_seconds=time.monotonic()-started,stdout=result.stdout,stderr=result.stderr))
        if result.returncode:raise RuntimeError(name+'_failed')
    report.pop('active',None);save('passed')
except BaseException as error:
    report['error']=repr(error);save('failed');raise
