"""Twenty additional physical fixed-game lookups and actual quiescent resources."""
import base64,hashlib,json,runpy,time
from pathlib import Path
from tools import check_hardening as hardening

root=Path('.planning/phases/08-vm');m=runpy.run_path(str(root/'08-09-games.py'));guest=m['guest']
pid=json.loads((root/'08-09-game-route2.json').read_text())['route']['timing']['pid']

def snapshot():
    code='''import base64,hashlib,json,os,re,sqlite3,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,'/home/lookup07')
from check_hardening import descendant_identities
pid='''+repr(pid)+'''
process=Path('/proc',str(pid));assert process.stat().st_uid==1001
stat=(process/'stat').read_text();start=int(stat.split(') ',1)[1].split()[19]);status=(process/'status').read_text()
root=Path('/home/lookup07/.local/state/lookup-games-08/assaultcube/lookup')
trace=(root/'daemon.log').read_text();events=[json.loads(line.split(':',1)[1]) for line in trace.splitlines() if line.startswith('lookup-timing:')]
run=next(row['run'] for row in reversed(events) if row['pid']==pid)
with sqlite3.connect('file:'+str(root/'data/history.db')+'?mode=ro',uri=True) as conn:
    history=dict(count=conn.execute('SELECT COALESCE(sum(count),0) FROM words').fetchone()[0],integrity=conn.execute('PRAGMA integrity_check').fetchone()[0])
env=dict(os.environ,XDG_RUNTIME_DIR='/run/user/1001',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/1001/bus')
def user(argv):return subprocess.run(['sudo','-n','-H','-u','lookup07',*argv],env=env,capture_output=True,timeout=5)
clipboard={}
for key,argv in (('primary',['wl-paste','--primary','--no-newline']),('clipboard',['wl-paste','--no-newline']),('klipper',['qdbus6','org.kde.klipper','/klipper','getClipboardHistoryMenu'])):
    child=user(argv);clipboard[key]=dict(exit=child.returncode,sha256=hashlib.sha256(child.stdout).hexdigest())
files=[]
for base in ('/tmp','/run/user/1001',str(root/'data')):
    for parent,dirs,names in os.walk(base,followlinks=False):
        dirs[:]=[name for name in dirs if not (Path(parent)/name).is_symlink()]
        for name in names:
            path=Path(parent)/name
            try:
                if not path.is_symlink() and path.is_file() and path.stat().st_uid==1001:
                    with path.open('rb') as stream:magic=stream.read(8)
                    if magic==b'\\x89PNG\\r\\n\\x1a\\n':files.append(str(path))
            except (OSError,PermissionError):pass
children=descendant_identities(pid,start,1001)
print(json.dumps(dict(identity=[pid,start,run],rss_bytes=int(re.search(r'^VmRSS:\\s+(\\d+)',status,re.M)[1])*1024,threads=len(list((process/'task').iterdir())),fds=len(list((process/'fd').iterdir())),
    owned_children=[row['pid'] for row in children],descendant_identities=children,observed=True,at_ns=time.monotonic_ns(),stat=stat,status=status,
    cmdline_base64=base64.b64encode((process/'cmdline').read_bytes()).decode(),history=history,privacy=clipboard,png_files=sorted(files),scanned=['/tmp','/run/user/1001',str(root/'data')])))'''
    return json.loads(guest(code))

if __name__=='__main__':
    destination=root/'08-09-fallback-attempts.json';assert not destination.exists()
    data=dict(declared_completions=20,resource_every=1,required_second_pass_completions=2,
        before=snapshot(),completions=[],resources=[],failures=[])
    hardening.write_record(destination,data)
    try:
        for index in range(1,21):
            path=root/('08-09-fallback-route'+str(index)+'.json')
            try:
                route=m['games'].run_lookup_route(path,'name',index+2,game_kind='assaultcube',point=[733,378])
                source=route['lookup_observation']['source_observation']
                data['completions'].append(dict(timing=route['route']['timing'],ocr_passes=source['ocr_passes'],actual_selection=source['production_selection'],raw_route=path.name))
                resource=snapshot();resource['after']=index;data['resources'].append(resource)
                print(json.dumps(dict(completed=index,passes=[item['psm'] for item in source['ocr_passes']],rss_bytes=resource['rss_bytes'])),flush=True)
            except BaseException as error:
                data['failures'].append(dict(attempt=index,error=repr(error)));raise
            finally:hardening.write_record(destination,data)
    finally:
        began=time.monotonic();time.sleep(5);data['cooldown']=snapshot();data['cooldown']['idle_ms']=(time.monotonic()-began)*1000
        data['history_delta']=data['cooldown']['history']['count']-data['before']['history']['count'];data['integrity']=data['cooldown']['history']['integrity']
        hardening.write_record(destination,data)
        report=hardening.fallback_stability_report(data)
        report['privacy_unchanged']=data['before']['privacy']==data['cooldown']['privacy']
        report['unexpected_capture_files']=sorted(set(data['cooldown']['png_files'])-set(data['before']['png_files']))
        hardening.write_record(root/'08-09-fallback-native-report.json',report);print(json.dumps(report),flush=True)
