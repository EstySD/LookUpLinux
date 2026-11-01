"""Independent post-manual cleanup, with no pre-manual restore path."""
import hashlib,json,os,signal,sqlite3,subprocess,time
from pathlib import Path
assert Path('/sys/class/dmi/id/product_uuid').read_text().strip()=='097920cf-b594-494b-8bd8-ccff973c1dc8'
base=Path('/home/arch/lookup-final-07');record={}
def attempt(name,operation):
    try:record[name]=dict(ok=True,result=operation())
    except BaseException as error:record[name]=dict(ok=False,error=repr(error))
    (base/'cleanup.json').write_text(json.dumps(record,indent=2))
assert base.is_dir() and (base/'baseline.json').is_file(),'No current post-manual baseline; refusing stale restore'
baseline=json.loads((base/'baseline.json').read_text())
def stop():
    stopped=[]
    for process in Path('/proc').glob('[0-9]*'):
        try:
            if process.stat().st_uid!=1001:continue
            argv=(process/'cmdline').read_bytes().split(b'\0');fields=(process/'stat').read_text().split(') ',1)[1].split()
            owned=argv[:2]==[b'/usr/bin/python',b'/usr/bin/lookup'] and any(value in argv for value in (b'--app',b'--autostart'))
            if owned and fields[0]!='Z':os.kill(int(process.name),signal.SIGTERM);stopped.append(dict(pid=int(process.name),start=int(fields[19])))
        except (FileNotFoundError,ProcessLookupError):pass
    time.sleep(1);remaining=[]
    for row in stopped:
        process=Path('/proc',str(row['pid']))
        try:
            fields=(process/'stat').read_text().split(') ',1)[1].split()
            if process.stat().st_uid==1001 and int(fields[19])==row['start'] and fields[0]!='Z':remaining.append(row)
        except (FileNotFoundError,ProcessLookupError):pass
    return dict(stopped=stopped,remaining=remaining,at_ns=time.monotonic_ns())
attempt('fallback_stop_only_owned',stop)
def retain():
    files={}
    for name,old in baseline['files'].items():
        if '.db' in Path(name).name:continue
        path=Path(name);files[name]=path.is_file() and not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest()==old['sha256']
    databases={}
    for name,old in baseline['logical_counts'].items():
        with sqlite3.connect('file:'+name+'?mode=ro',uri=True) as actual,sqlite3.connect('file:'+str(base/(Path(name).name+'.backup'))+'?mode=ro',uri=True) as backup:
            left=hashlib.sha256('\n'.join(actual.iterdump()).encode()).hexdigest();right=hashlib.sha256('\n'.join(backup.iterdump()).encode()).hexdigest()
            databases[name]=dict(actual_logical_sha256=left,postmanual_backup_sha256=right,retained=left==right,integrity=actual.execute('PRAGMA integrity_check').fetchone()[0])
    return dict(files=files,databases=databases,preserved=all(files.values()) and all(row['retained'] and row['integrity']=='ok' for row in databases.values()))
attempt('postmanual_retention',retain)
def fixture():
    home=Path('/home/lookup07/.local/state/lookup-final-07')
    if not (home/'fixture.json').exists():return dict(not_created=True)
    child=subprocess.run(['sudo','-n','-H','-u','lookup07','python',str(home/'registry.py'),'cleanup-fixture'],capture_output=True,text=True,timeout=25)
    assert child.returncode==0,child.stderr
    return json.loads(child.stdout)
attempt('fixture_restore',fixture)
def package():
    result=subprocess.run(['pacman','-Q','lookup-linux'],capture_output=True,text=True)
    if result.returncode:return dict(already_absent=True)
    child=subprocess.run(['pacman','-R','--noconfirm','lookup-linux'],capture_output=True,text=True,timeout=30)
    assert child.returncode==0,child.stderr
    return dict(exit=child.returncode,stdout=child.stdout,stderr=child.stderr,absent=subprocess.run(['pacman','-Q','lookup-linux'],capture_output=True).returncode!=0)
attempt('package_remove_preserve_profiles',package)
attempt('post_removal_retention',retain)
record['current_baseline_only']=True
print(json.dumps(record))
