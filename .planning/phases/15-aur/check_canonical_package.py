"""Verify the downloaded CI binary and generate metadata from its source bytes."""
import base64
import json
from pathlib import Path
import subprocess
import time
from run_release_batch import SSH,SCP,ROOT

OUT=Path(__file__).resolve().parent/'release-1793725749'


def main():
    for _ in range(36):
        if subprocess.run([*SSH,'true'],capture_output=True).returncode==0:break
        time.sleep(2)
    else:raise RuntimeError('clone_ssh_unavailable')
    remote='/home/arch/lookup-release-021-canonical-'+str(int(time.time()))
    subprocess.run([*SSH,'mkdir -p '+remote],check=True,capture_output=True)
    subprocess.run([*SCP,str(OUT/'aur-canonical/PKGBUILD'),str(OUT/'github-assets/lookup-linux-0.2.1-1-x86_64.pkg.tar.zst'),'archvm:'+remote+'/'],check=True,capture_output=True)
    result=subprocess.run([*SSH,'cd '+remote+' && makepkg --printsrcinfo'],capture_output=True,check=True)
    (OUT/'aur-canonical/.SRCINFO').write_bytes(result.stdout)
    (ROOT/'packaging/aur/PKGBUILD').write_bytes((OUT/'aur-canonical/PKGBUILD').read_bytes())
    (ROOT/'packaging/aur/.SRCINFO').write_bytes(result.stdout)
    code='''import sys,os,json,pathlib,subprocess,hashlib
root=pathlib.Path(REMOTE)
pkg=root/'lookup-linux-0.2.1-1-x86_64.pkg.tar.zst'
subprocess.run(['sudo','-n','pacman','-U','--noconfirm',str(pkg)],check=True,stdout=subprocess.DEVNULL)
linkage=subprocess.check_output(['ldd','/usr/lib/qt6/plugins/kwin/plugins/lookupcapture.so'],text=True)
assert 'not found' not in linkage,linkage
sys.path.insert(0,'/usr/lib/lookup/app')
profile=root/'smoke';profile.mkdir();(profile/'dicts').mkdir()
(profile/'config.json').write_text('{"online":false,"autostart":false}')
(profile/'dicts/public.dsl').write_text('#NAME "Public fixture"\\n#INDEX_LANGUAGE "English"\\n#CONTENTS_LANGUAGE "Russian"\\nbank\\n    банк\\n',encoding='utf-16')
os.environ.update(LOOKUP_CONFIG=str(profile/'config.json'),LOOKUP_DB=str(profile/'history.db'),LOOKUP_DICTS=str(profile/'dicts'),LOOKUP_CACHE=str(profile/'cache'))
from lookup.store import open_store
from lookup.dicts import open_all
from lookup.config import Config
from lookup.translate import lookup
c=open_store();d=open_all(Config(),[profile/'dicts']);v=lookup('bank',dictset=d,conn=c,online=False)
assert v.translation=='банк' and v.count==1
print(json.dumps({'passed':True,'package_sha256':hashlib.sha256(pkg.read_bytes()).hexdigest(),'installed':subprocess.check_output(['pacman','-Q','lookup-linux'],text=True).strip(),'lookup':{'word':v.key,'translation':v.translation,'count':v.count},'plugin_dependencies_found':True}))
d.close();c.close()
'''.replace('REMOTE',repr(remote))
    encoded=base64.b64encode(code.encode()).decode()
    with (OUT/'canonical-package.log').open('w',encoding='utf-8') as log:
        result=subprocess.run([*SSH,'echo '+encoded+' | base64 -d | env PYTHONDONTWRITEBYTECODE=1 python -'],stdout=subprocess.PIPE,stderr=log,check=True,timeout=60)
    report=json.loads(result.stdout);(OUT/'canonical-package.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))


if __name__=='__main__':main()
