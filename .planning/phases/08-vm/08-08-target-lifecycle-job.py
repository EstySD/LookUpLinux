"""Final task3 focused target run, with current code hashes and retained output."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
root=Path.cwd();report=root/'08-08-target-lifecycle.json'
names=['lookup/ocr.py','tools/check_games.py','tools/calibrate_ocr.py','tests/test_app.py','tests/test_app_gui.py','tests/test_check_games.py']
result=dict(state='running',files={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in names})
report.write_text(json.dumps(result))
run=subprocess.run([sys.executable,'-m','unittest','tests.test_app','tests.test_app_gui','tests.test_check_games','tests.test_translate_ready','tests.test_learning','tests.test_ocr_fallback'],capture_output=True,text=True,timeout=300,env=dict(os.environ,QT_QPA_PLATFORM='offscreen'))
result.update(state='passed' if run.returncode==0 else 'failed',exit=run.returncode,stdout=run.stdout,stderr=run.stderr)
report.write_text(json.dumps(result))
