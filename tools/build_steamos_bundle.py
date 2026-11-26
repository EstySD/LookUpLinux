#!/usr/bin/env python3
"""Build a deterministic, offline SteamOS bundle with checksums and licenses.

The runtime directory is optional because platform binaries (PyQt6 wheels,
tesseract eng data, kdotool, wl-clipboard) cannot be produced on this host.
When present, its files are copied verbatim into the bundle's runtime/.
"""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile
import sys

ROOT=Path(__file__).resolve().parents[1]
MAX_FILE=64<<20
MAX_TOTAL=512<<20
TEXT_SUFFIXES=('.py','.txt','.md','.json','.desktop','.sh','.xml')
ALWAYS_TEXT=('LICENSE','COPYING.md','SHA256SUMS','MANIFEST.json')


def _collect(runtime=None):
    files=[]
    folders=(('lookup','lookup'),('docs','docs'),('tools','tools'))
    for source,target in folders:
        for path in (ROOT/source).rglob('*'):
            if not path.is_file() or '__pycache__' in path.parts:continue
            if path.suffix=='.pyc':continue
            files.append(((Path(target)/path.relative_to(ROOT/source)).as_posix(),path))
    for name in ('README.md','COPYING.md','LICENSE','packaging/THIRD-PARTY.md'):
        files.append((name,ROOT/name))
    if runtime is not None:
        runtime=Path(runtime)
        if not runtime.is_dir():raise ValueError('runtime_not_found')
        for path in runtime.rglob('*'):
            if path.is_file() and not path.is_symlink():
                files.append(((Path('runtime')/path.relative_to(runtime)).as_posix(),path))
    total=0
    for name,path in files:
        if path.is_symlink() or not path.is_file():raise ValueError('unsafe_bundle_input')
        size=path.stat().st_size
        if size>MAX_FILE:raise ValueError('bundle_file_too_large')
        total+=size
    if total>MAX_TOTAL:raise ValueError('bundle_too_large')
    return sorted(set(files))


def build(output,*,version='1.2.0',runtime=None):
    output=Path(output)
    if output.is_symlink() or (output.exists() and (not output.is_file() or output.stat().st_size)):
        raise ValueError('output_must_be_new_or_empty')
    output.parent.mkdir(parents=True,exist_ok=True)
    files=_collect(runtime)
    manifest={
        'product':'LookUp Linux SteamOS portable bundle',
        'version':str(version),
        'offline_runtime':bool(runtime),
        'files':[],
        'license_notices':['GPL-3.0-or-later','packaging/THIRD-PARTY.md'],
    }
    checksums=[]
    buffer=io.BytesIO()
    with gzip.GzipFile(filename='',mode='wb',mtime=0,fileobj=buffer) as compressed:
        with tarfile.open(fileobj=compressed,mode='w',format=tarfile.USTAR_FORMAT) as archive:
            for name,path in files:
                data=path.read_bytes()
                if path.suffix in TEXT_SUFFIXES or path.name in ALWAYS_TEXT:
                    data=data.replace(b'\r\n',b'\n')
                digest=hashlib.sha256(data).hexdigest()
                manifest['files'].append(dict(path=name,sha256=digest,size=len(data)))
                checksums.append(digest+'  '+name+'\n')
                info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644
                archive.addfile(info,io.BytesIO(data))
            payload=json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2).encode('utf-8')+b'\n'
            info=tarfile.TarInfo('MANIFEST.json');info.size=len(payload);info.mode=0o644
            archive.addfile(info,io.BytesIO(payload))
            sums=''.join(checksums).encode('utf-8')
            info=tarfile.TarInfo('SHA256SUMS');info.size=len(sums);info.mode=0o644
            archive.addfile(info,io.BytesIO(sums))
    output.write_bytes(buffer.getvalue())
    return manifest


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--runtime',type=Path)
    parser.add_argument('--version',default='1.2.0')
    args=parser.parse_args(argv)
    try:
        manifest=build(args.output,version=args.version,runtime=args.runtime)
    except (ValueError,OSError) as error:
        print('build_steamos_bundle: '+str(error),file=sys.stderr)
        return 1
    print('Built '+str(args.output)+' with '+str(len(manifest['files']))+' files (offline runtime: '+
          ('yes' if manifest['offline_runtime'] else 'no')+')')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
