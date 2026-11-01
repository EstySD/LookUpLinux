"""Transfer one source-bound Git bundle and start unprivileged isolated discovery."""
import base64,hashlib,json,runpy,subprocess,sys
from pathlib import Path
root=Path('.planning/phases/08-vm');n=runpy.run_path(str(root/'08-07-native.py'));revision=sys.argv[1]
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==revision
bundle=Path('D:/vm/machines/lookup-gsd-07')/('lookup-final-07-'+revision[:12]+'.bundle')
assert not bundle.exists();subprocess.run(['git','bundle','create',str(bundle),'HEAD'],check=True)
data=bundle.read_bytes();digest=hashlib.sha256(data).hexdigest()
code='''import base64,hashlib,json,os,subprocess,time,tarfile
from pathlib import Path
revision='''+repr(revision)+'''
root=Path('/home/arch/lookup-final-07-suite-'+revision[:12]);assert not root.exists();root.mkdir(mode=0o700);os.chown(root,1000,1000)
bundle=root/'source.bundle';bundle.write_bytes(base64.b64decode('''+repr(base64.b64encode(data).decode())+'''));assert hashlib.sha256(bundle.read_bytes()).hexdigest()=='''+repr(digest)+'''
os.chown(bundle,1000,1000)
def arch(argv,**kw):return subprocess.run(['sudo','-n','-H','-u','arch',*argv],capture_output=True,text=True,check=True,**kw)
source=root/'source';arch(['git','clone',str(bundle),str(source)],timeout=180);arch(['git','-C',str(source),'checkout','--detach',revision],timeout=60)
assert arch(['git','-C',str(source),'rev-parse','HEAD']).stdout.strip()==revision
home=root/'home';home.mkdir(mode=0o700);os.chown(home,1000,1000)
for name in ('config','data','cache','state','runtime','results'):
    path=home/name;path.mkdir(mode=0o700);os.chown(path,1000,1000)
package=Path('/home/arch/lookup-cascade-09-build/lookup-linux-0.1.0-1-x86_64.pkg.tar.zst')
assert hashlib.sha256(package.read_bytes()).hexdigest()=='7981792e6b2b7a512ebd3465331a9f58ec717c6d6b7d7c24b2046187c6c4d7ea'
mueller=root/'verified-mueller';mueller.mkdir(mode=0o700);os.chown(mueller,1000,1000)
with tarfile.open(package) as archive:
    package_members={}
    for member in archive:
        if not member.isfile() or not member.name.removeprefix('./').startswith('usr/share/lookup/dicts/mueller7/'):continue
        name=member.name.rsplit('/',1)[-1];assert name and name not in ('.','..') and name not in package_members
        data=archive.extractfile(member).read();package_members[name]=hashlib.sha256(data).hexdigest()
        path=mueller/name;path.write_bytes(data);os.chown(path,1000,1000);path.chmod(0o400)
dictionary={path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in mueller.iterdir() if path.is_file()}
assert dictionary==package_members and package_members
assert (mueller/'mueller7.ifo').is_file()
manifest=root/'dictionary-verified.json';manifest.write_text(json.dumps(dict(package_members=package_members,verified_members=dictionary,origin='Private read-only extraction from the actual hash-verified reviewed package; product remains uninstalled.')))
settings=dict(PATH='/usr/bin',HOME=str(home),USER='arch',LOGNAME='arch',LANG='C.UTF-8',LC_ALL='C.UTF-8',PYTHONIOENCODING='utf-8',QT_QPA_PLATFORM='offscreen',
    XDG_CONFIG_HOME=str(home/'config'),XDG_DATA_HOME=str(home/'data'),XDG_CACHE_HOME=str(home/'cache'),XDG_STATE_HOME=str(home/'state'),XDG_RUNTIME_DIR=str(home/'runtime'),
    LOOKUP_CONFIG=str(home/'config/lookup.json'),LOOKUP_DB=str(home/'data/lookup.db'),LOOKUP_CACHE=str(home/'cache/lookup'),LOOKUP_DICTS=str(mueller.parent),
    LOOKUP_TEST_OCR='1',LOOKUP_TEST_DICTS=str(mueller),DBUS_SYSTEM_BUS_ADDRESS='unix:path=/nonexistent/lookup-final-07-system-bus',NO_AT_BRIDGE='1',GTK_USE_PORTAL='0')
runner=source/'.planning/phases/08-vm/08-07-suite-runner.py'
argv=['sudo','-n','-H','-u','arch','env','-i',*[key+'='+value for key,value in settings.items()],'setpriv','--no-new-privs','dbus-run-session','--','python',str(runner),'--revision',revision,'--role','target','--output',str(home/'results'),'--mueller-manifest',str(manifest)]
log=root/'launcher.log'
with log.open('wb') as output:child=subprocess.Popen(argv,cwd=source,stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
record=dict(revision=revision,source=str(source),home=str(home),launcher_pid=child.pid,launcher_start=int(Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split()[19]),bundle_sha256='''+repr(digest)+''',dictionary_members=dictionary,argv=argv)
(root/'launch.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))'''
record=json.loads(n['guest'](code,timeout=300));(root/'08-07-target-launch.json').write_text(json.dumps(record,indent=2));print(json.dumps(record),flush=True)
