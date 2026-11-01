"""One actual README makepkg build/install from the frozen staged bytes."""
import base64,hashlib,json,runpy,subprocess,time
from pathlib import Path

root=Path('.planning/phases/08-vm');native=runpy.run_path(str(root/'08-09-native.py'))
payload={name:base64.b64encode((root/'08-09-build'/name).read_bytes()).decode()
    for name in ('PKGBUILD','lookup-source.tar.gz','SOURCE.json')}
expected=json.loads((root/'08-09-build/SOURCE.json').read_text())
script='''import base64,hashlib,json,os,subprocess,time
from pathlib import Path
root=Path('/home/arch/lookup-cascade-09-build')
assert not root.exists(),'09build_already_exists'
assert subprocess.run(['pacman','-Q','lookup-linux'],capture_output=True).returncode!=0,'package_present'
root.mkdir(mode=0o700);os.chown(root,1000,1000)
payload='''+repr(payload)+'''
for name,encoded in payload.items():
    path=root/name;path.write_bytes(base64.b64decode(encoded));os.chown(path,1000,1000)
assets='''+repr(expected['upstream'])+'''
for name,metadata in assets.items():
    filename={'kdotool':'kdotool-0.3.0.tar.gz','mueller7':'mueller7.tar.bz2'}[name]
    data=(Path('/home/arch/lookup-readme-08-build')/filename).read_bytes()
    assert hashlib.sha256(data).hexdigest()==metadata['sha256']
    path=root/filename;path.write_bytes(data);os.chown(path,1000,1000)
record=dict(baseline_absent=True,build_directory=str(root),source_sha256=hashlib.sha256((root/'lookup-source.tar.gz').read_bytes()).hexdigest())
with (root/'makepkg.log').open('w') as log:
    child=subprocess.run(['sudo','-n','-H','-u','arch','bash','-c','cd /home/arch/lookup-cascade-09-build && makepkg -si --noconfirm'],stdout=log,stderr=subprocess.STDOUT,timeout=360)
record.update(build_exit=child.returncode,install_exit=child.returncode,completed_ns=time.monotonic_ns(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
record['log']=(root/'makepkg.log').read_text()
packages=list(root.glob('lookup-linux-*.pkg.tar.zst'));assert len(packages)==1,record
record['package_path']=str(packages[0]);record['package_sha256']=hashlib.sha256(packages[0].read_bytes()).hexdigest()
(root/'actual-build.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
'''
result=json.loads(native['guest'](script,timeout=390))
(root/'08-09-actual-build.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result),flush=True)
