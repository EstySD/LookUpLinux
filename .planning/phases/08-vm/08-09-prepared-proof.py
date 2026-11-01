"""Read-only native preparation replay for the two exact retained game sources."""
import base64,json,runpy
from pathlib import Path
root=Path('.planning/phases/08-vm');n=runpy.run_path(str(root/'08-09-native.py'));rows=[]
for index in (1,2):
    raw=json.loads((root/('08-09-game-route'+str(index)+'.json')).read_text())['lookup_observation']['source_observation']
    code='''from pathlib import Path
import sys,hashlib,json,base64,os
sys.path.insert(0,'/usr/lib/lookup/app')
from lookup import ocr,capture,platform
os.environ.update(platform.session_env())
from PyQt6.QtGui import QImage,QGuiApplication
application=QGuiApplication([])
path=Path('''+repr(raw['image_path'])+''')
png,transform=ocr._prepare_image(path.read_bytes(),'''+repr(raw['cursor'])+''',ocr.DEFAULT_ENLARGE,ocr.DEFAULT_INVERT)
image=capture._png_image(png).convertToFormat(QImage.Format.Format_RGBA8888)
print(json.dumps(dict(source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),prepared_sha256=hashlib.sha256(png).hexdigest(),
    prepared_pixels_sha256=hashlib.sha256(image.constBits().asstring(image.sizeInBytes())).hexdigest(),transform=transform.__dict__,png_base64=base64.b64encode(png).decode())))'''
    out=n['guest']("import subprocess;p=subprocess.run(['sudo','-n','-H','-u','lookup07','python','-c',"+repr(code)+"],capture_output=True,text=True,timeout=8);print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)")
    row=json.loads(out);(root/('08-09-game-route'+str(index)+'-prepared.png')).write_bytes(base64.b64decode(row.pop('png_base64')))
    row['route']=index;row['matches_observed_process_input']=all(item['input_sha256']==row['prepared_sha256'] for item in raw['ocr_passes']);assert row['matches_observed_process_input']
    rows.append(row)
(root/'08-09-game-prepared-proof.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows))
