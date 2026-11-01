"""Freeze the owned cleanup's additional current-profile readback before shutdown."""
import hashlib,json,runpy
from pathlib import Path
root=Path('.planning/phases/08-vm');n=runpy.run_path(str(root/'08-09-native.py'))
original=n['guest']("from pathlib import Path;path=Path('/home/arch/lookup-games-08-pilot-cleanup.py');assert not path.is_symlink();print(path.read_text())")
(root/'08-09-guest-cleanup-original.py').write_text(original,encoding='utf-8',newline='\n')
supplement='''
# Phase09 current-profile readback, after the original owned removal procedure.
assert Path('/sys/class/dmi/id/product_uuid').read_text().strip()=='097920cf-b594-494b-8bd8-ccff973c1dc8'
expected09=json.loads(Path('/home/arch/lookup-cascade-09-retention.json').read_text())
observed09={name:hashlib.sha256(Path(name).read_bytes()).hexdigest() if Path(name).is_file() and not Path(name).is_symlink() else None for name in expected09}
remaining09=[]
for process09 in Path('/proc').glob('[0-9]*'):
    try:
        if process09.stat().st_uid!=1001:continue
        argv09=(process09/'cmdline').read_bytes().split(b'\\0');fields09=(process09/'stat').read_text().split(') ',1)[1].split()
        owned09=any(value in argv09 for value in (b'/home/lookup07/check_games.py',b'/home/lookup07/check_hardening_09.py',b'/home/lookup07/check_fallback_09.py',b'/usr/bin/lookup',b'/home/lookup07/.local/state/lookup-games-08/assaultcube/package/bin_unix/linux_64_client'))
        if owned09 and fields09[0]!='Z':remaining09.append(dict(pid=int(process09.name),start=int(fields09[19]),argv=[os.fsdecode(value) for value in argv09 if value]))
    except (FileNotFoundError,ProcessLookupError):pass
supplement09=dict(expected=expected09,observed=observed09,retained=observed09==expected09,remaining=remaining09,package_absent=run(['pacman','-Q','lookup-linux'])['exit']!=0,at_ns=time.monotonic_ns())
Path('/home/arch/lookup-cascade-09-cleanup-readback.json').write_text(json.dumps(supplement09,indent=2))
print('lookup09-retention:'+json.dumps(supplement09))
'''
source=original+supplement;compile(source,'09-owned-cleanup','exec')
(root/'08-09-guest-cleanup-executed.py').write_text(source,encoding='utf-8',newline='\n')
result=n['guest']("import hashlib;from pathlib import Path;path=Path('/home/arch/lookup-games-08-pilot-cleanup.py');assert hashlib.sha256((path.read_text()+'\\n').encode()).hexdigest()=="+repr(hashlib.sha256(original.encode()).hexdigest())+";path.write_text("+repr(source)+");print(hashlib.sha256(path.read_bytes()).hexdigest())")
(root/'08-09-cleanup-source-receipt.json').write_text(json.dumps(dict(executed_source_sha256=result.strip(),note='Original cleanup bytes retained; this actual subprocess will load the recorded supplemental file before shutdown. Existing controller was not hot-reloaded.'),indent=2))
print(result)
