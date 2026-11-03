"""Prepare the public AUR recipe for an exact, unpublished release archive."""
import argparse
import hashlib
import json
from pathlib import Path,PurePosixPath
import re
import tarfile

ROOT=Path(__file__).resolve().parents[1]


def stage(source,output,root=ROOT):
    source=Path(source);output=Path(output)
    template=(Path(root)/'packaging/PKGBUILD.public').read_text(encoding='utf-8')
    match=re.search(r'^pkgver=(\d+\.\d+\.\d+)$',template,re.M)
    if match is None or template.count('@LOCAL_SOURCE_SHA256@')!=1:raise ValueError('invalid_public_template')
    version=match[1];prefix='lookup-linux-'+version
    with tarfile.open(source,'r:gz') as archive:
        names=set()
        for member in archive.getmembers():
            parts=PurePosixPath(member.name).parts
            if (not member.isfile() or '\\' in member.name or ':' in member.name or member.name in names or not member.name.startswith(prefix+'/') or
                    any(part in ('..','.planning','.omx','.git','__pycache__') for part in parts) or
                    member.name.endswith(('.db','.pyc'))):raise ValueError('unsafe_release_archive')
            names.add(member.name)
        for name in ('LICENSE','COPYING.md','lookup/__main__.py','native/kwin-capture/CMakeLists.txt','native/kwin-capture/capture.cpp'):
            if prefix+'/'+name not in names:raise ValueError('incomplete_release_archive')
    if output.is_symlink() or (output.exists() and (not output.is_dir() or any(output.iterdir()))):
        raise ValueError('output_not_empty')
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    url='https://github.com/EstySD/LookUpLinux/releases/download/v'+version+'/'+prefix+'-source.tar.gz'
    recipe=template.replace("source=('lookup-source.tar.gz'","source=('"+url+"'")
    if recipe==template:raise ValueError('invalid_public_source')
    recipe=recipe.replace('lookup-source/',prefix+'/').replace('@LOCAL_SOURCE_SHA256@',digest)
    output.mkdir(parents=True,exist_ok=True)
    (output/'PKGBUILD').write_text(recipe,encoding='utf-8',newline='\n')
    receipt={'version':version,'source_url':url,'source_sha256':digest,'publication':'not_published',
             'recipe_sha256':hashlib.sha256(recipe.encode()).hexdigest()}
    (output/'AUR.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
    print(json.dumps(stage(args.source,args.output)))
