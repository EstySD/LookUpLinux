"""Exact official archive acquisition in the owned pilot directory."""
import hashlib,json,os,subprocess,tarfile,urllib.request
from pathlib import Path
assert os.getuid()==1001 and Path.home()==Path('/home/lookup07')
root=Path.home()/'.local/state/lookup-games-08/assaultcube';root.mkdir(exist_ok=True,parents=True)
baseline=root/'baseline.json'
if not baseline.exists():
    package_status=subprocess.run(['pacman','-Q','lookup-linux'],capture_output=True,text=True)
    assert package_status.returncode!=0
    paths=[path for base in (Path.home()/'.config/lookup',Path.home()/'.local/share/lookup') if base.exists() for path in base.rglob('*') if path.is_file()]
    baseline.write_text(json.dumps(dict(package_absent=True,retained={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths})))
url='https://github.com/assaultcube/AC/releases/download/v1.3.0.2/AssaultCube_v1.3.0.2_LockdownEdition_RC1.tar.bz2'
archive=root/'AssaultCube_v1.3.0.2_LockdownEdition_RC1.tar.bz2'
if not archive.exists():
    with urllib.request.urlopen(url,timeout=30) as response:archive.write_bytes(response.read())
digest=hashlib.sha256(archive.read_bytes()).hexdigest()
assert archive.stat().st_size==52071427 and digest=='9b3118e7929253f0114fa06cad8310faab646d177b4660406011152f34086b55'
target=root/'extracted'
if not target.exists():
    target.mkdir()
    with tarfile.open(archive) as source:source.extractall(target,filter='data')
bins=list(target.rglob('linux_64_client'));assert len(bins)==1
package=bins[0].parent.parent
link=root/'package'
if not link.exists():link.symlink_to(package,target_is_directory=True)
ldd=subprocess.run(['ldd',str(bins[0])],capture_output=True,text=True,timeout=10)
record=dict(url=url,bytes=archive.stat().st_size,sha256=digest,checksum_status='researched reproducibility pin; no signed upstream checksum',
    executable=str(link/'bin_unix/linux_64_client'),actual_package=str(package),ldd=ldd.stdout,ldd_exit=ldd.returncode,
    licenses=[dict(path=str(path.relative_to(package)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in package.glob('docs/*') if 'license' in path.name or 'copyright' in path.name])
(root/'acquisition.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
