"""Record actual full discovery at the requested immutable source revision."""
import argparse,hashlib,json,os,re,subprocess,sys,time
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--revision',required=True);parser.add_argument('--role',choices=('host','target'),required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--mueller-manifest',type=Path)
args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();assert revision==args.revision
tree=subprocess.check_output(['git','rev-parse','HEAD^{tree}'],text=True).strip()
mueller_verified=False
if args.role=='target':
    assert os.getuid()==1000 and str(Path.home()).startswith('/home/arch/lookup-final-07-suite-')
    assert os.environ['QT_QPA_PLATFORM']=='offscreen' and os.environ['LOOKUP_TEST_OCR']=='1'
    assert all(name not in os.environ for name in ('DISPLAY','WAYLAND_DISPLAY','XAUTHORITY'))
    assert '/run/user/1001' not in os.environ['DBUS_SESSION_BUS_ADDRESS']
    assert Path(os.environ['XDG_RUNTIME_DIR']).stat().st_mode&0o777==0o700
    assert re.search(r'^NoNewPrivs:\s+1$',Path('/proc/self/status').read_text(),re.M)
    manifest=json.loads(args.mueller_manifest.read_text());directory=Path(os.environ['LOOKUP_TEST_DICTS'])
    observed={path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in directory.iterdir() if path.is_file()}
    mueller_verified=observed==manifest['package_members']==manifest['verified_members'];assert mueller_verified
command=['python','-m','unittest','discover','-s','tests'];log=args.output/(args.role+'-discovery.log')
started=time.time_ns();env=dict(os.environ,QT_QPA_PLATFORM='offscreen',PYTHONIOENCODING='utf-8')
with log.open('wb') as output:child=subprocess.run(command,stdout=output,stderr=subprocess.STDOUT,env=env,timeout=900)
raw=log.read_bytes();text=raw.decode('utf-8','replace');matches=re.findall(r'^Ran (\d+) tests? in ([0-9.]+)s\s*$',text,re.M)
count=int(matches[-1][0]) if len(matches)==1 else None
skip=re.search(r'^OK \(skipped=(\d+)\)\s*$',text,re.M);skips=int(skip[1]) if skip else 0
record=dict(role=args.role,revision=revision,tree=tree,command=command,exit=child.returncode,count=count,skips=skips,log_sha256=hashlib.sha256(raw).hexdigest(),ocr_enabled=os.environ.get('LOOKUP_TEST_OCR')=='1',mueller_verified=mueller_verified,
    started_ns=started,finished_ns=time.time_ns(),log=log.name,uid=os.getuid() if hasattr(os,'getuid') else None,
    python=sys.version,environment={key:os.environ.get(key) for key in ('HOME','XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_STATE_HOME','XDG_RUNTIME_DIR','LOOKUP_CONFIG','LOOKUP_DB','LOOKUP_CACHE','LOOKUP_DICTS','LOOKUP_TEST_OCR','LOOKUP_TEST_DICTS','QT_QPA_PLATFORM','DBUS_SESSION_BUS_ADDRESS','DBUS_SYSTEM_BUS_ADDRESS')})
(args.output/(args.role+'-suite.json')).write_text(json.dumps(record,indent=2),encoding='utf-8');print(json.dumps(record),flush=True)
raise SystemExit(child.returncode)
