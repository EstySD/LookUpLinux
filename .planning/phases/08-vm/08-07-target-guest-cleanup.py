"""Stop only this private target job and verify post-manual user data retained."""
import hashlib,json,os,signal,sqlite3,time
from pathlib import Path
assert Path('/sys/class/dmi/id/product_uuid').read_text().strip()=='097920cf-b594-494b-8bd8-ccff973c1dc8'
stopped=[];remaining=[]
roots=[path for path in Path('/home/arch').glob('lookup-final-07-suite-*') if path.is_dir() and path.stat().st_uid==1000]
homes={os.fsencode(str(path/'home')) for path in roots}
for process in Path('/proc').glob('[0-9]*'):
    try:
        if process.stat().st_uid!=1000:continue
        environment=(process/'environ').read_bytes().split(b'\0')
        if not any(b'HOME='+home in environment for home in homes):continue
        fields=(process/'stat').read_text().split(') ',1)[1].split()
        if fields[0]=='Z':continue
        row=dict(pid=int(process.name),start=int(fields[19]),uid=1000);os.kill(row['pid'],signal.SIGTERM);stopped.append(row)
    except (FileNotFoundError,ProcessLookupError,PermissionError):pass
time.sleep(1)
for row in stopped:
    try:
        process=Path('/proc',str(row['pid']));fields=(process/'stat').read_text().split(') ',1)[1].split()
        if process.stat().st_uid==1000 and int(fields[19])==row['start'] and fields[0]!='Z':remaining.append(row)
    except (FileNotFoundError,ProcessLookupError):pass
base=Path('/home/arch/lookup-final-07');baseline=json.loads((base/'baseline.json').read_text());files={};databases={}
for name,old in baseline['files'].items():
    if '.db' in Path(name).name:continue
    files[name]=Path(name).is_file() and hashlib.sha256(Path(name).read_bytes()).hexdigest()==old['sha256']
for name in baseline['logical_counts']:
    with sqlite3.connect('file:'+name+'?mode=ro',uri=True) as actual,sqlite3.connect('file:'+str(base/(Path(name).name+'.backup'))+'?mode=ro',uri=True) as backup:
        left=hashlib.sha256('\n'.join(actual.iterdump()).encode()).hexdigest();right=hashlib.sha256('\n'.join(backup.iterdump()).encode()).hexdigest()
        databases[name]=dict(actual_logical_sha256=left,postmanual_backup_sha256=right,retained=left==right,integrity=actual.execute('PRAGMA integrity_check').fetchone()[0])
normal=[]
for process in Path('/proc').glob('[0-9]*'):
    try:
        if process.stat().st_uid==1001 and b'/usr/bin/lookup' in (process/'cmdline').read_bytes().split(b'\0'):normal.append(int(process.name))
    except (FileNotFoundError,ProcessLookupError):pass
record=dict(stopped=stopped,remaining=remaining,files=files,databases=databases,postmanual_retained=all(files.values()) and all(row['retained'] and row['integrity']=='ok' for row in databases.values()),
    package_absent=not Path('/usr/bin/lookup').exists(),normal_product_processes=normal,at_ns=time.monotonic_ns())
print(json.dumps(record))
