"""Current installed smoke/doctor and historical-source compatibility, no queries."""
import base64,hashlib,json,runpy
from pathlib import Path
root=Path('.planning/phases/08-vm');n=runpy.run_path(str(root/'08-09-native.py'))
old=json.loads((root/'08-wesnoth-final-report.json').read_text())
files=['08-wesnoth-accepted-route1-source.png','08-wesnoth-accepted-route2-combat-source.png']
cases=[dict(image_base64=base64.b64encode((root/name).read_bytes()).decode(),source_file=name,expected={key:row['source'][key] for key in ('cursor','word','context','span')}) for name,row in zip(files,old['routes'])]
code='''import base64,hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,'/usr/lib/lookup/app');sys.path.insert(0,'/home/lookup07')
from lookup import ocr,platform,config,dicts
from check_games import observe_ocr_process,selection_evidence
os.environ.update(platform.session_env())
from PyQt6.QtGui import QGuiApplication
application=QGuiApplication([]);passes=[];ocr.subprocess.run=observe_ocr_process(ocr.subprocess.run,passes.append)
cases='''+repr(cases)+'''
rows=[]
with dicts.open_all(config.Config()) as dictionaries:
    for case in cases:
        expected=case['expected'];data=base64.b64decode(case['image_base64']);passes.clear()
        result=ocr.recognize_image(data,expected['cursor'])
        selected=selection_evidence(result);query=ocr.choose_query(result.selection,dictionaries) if result.selection else None
        row=dict(source_file=case['source_file'],source_sha256=hashlib.sha256(data).hexdigest(),cursor=expected['cursor'],selected=selected,query=query,passes=list(passes),expected=dict(word=expected['word'],context=expected['context'],span=expected['span']))
        row['compatible']=query==expected['word'] and selected['context']==expected['context'] and selected['span']==expected['span'] and [p['psm'] for p in passes]==[6]
        rows.append(row)
outputs={}
for name,argv in (('doctor',['/usr/bin/lookup','--doctor']),('smoke',['/usr/bin/lookup','--word','bank','--offline','--no-save'])):
    p=subprocess.run(argv,capture_output=True,text=True,timeout=20)
    outputs[name]=dict(exit=p.returncode,stdout=p.stdout,stderr=p.stderr)
print(json.dumps(dict(compatibility=rows,installed_checks=outputs)))'''
payload=n['guest']("import base64,os,subprocess;from pathlib import Path;path=Path('/home/lookup07/.local/state/lookup-hardening-09/readonly-final.py');path.write_bytes(base64.b64decode("+repr(base64.b64encode(code.encode()).decode())+"));os.chown(path,1001,1001);p=subprocess.run(['sudo','-n','-H','-u','lookup07','python',str(path)],capture_output=True,text=True,timeout=45);print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)",timeout=50)
value=json.loads(payload);(root/'08-09-current-installed-readonly.json').write_text(json.dumps(value,indent=2),encoding='utf-8')
print(json.dumps(dict(compatibility=[row['compatible'] for row in value['compatibility']],checks={name:row['exit'] for name,row in value['installed_checks'].items()})))
