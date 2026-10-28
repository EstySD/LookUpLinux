"""Create a deterministic, restricted local source snapshot for makepkg."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile

ROOT=Path(__file__).resolve().parents[1]
ASSETS={
    'kdotool':dict(url='https://github.com/jinliu/kdotool/releases/download/v0.3.0/kdotool-0.3.0-x86_64-unknown-linux-gnu.tar.gz',
                   sha256='2079cc1d492b6e83e04def4d9376e34fcb36a4e3bdc637c8c2ee6fa547ce90ff'),
    'mueller7':dict(url='https://qstardict.ylsoftware.com/files/mueller7.tar.bz2',
                   sha256='1c5e19b857eaa5fc98f77173e8baeb22cb654c407586465b4270e4286bf070ed'),
}


def stage(output,root=ROOT):
    root=Path(root).resolve();output=Path(output)
    if any((root/name).is_symlink() for name in ('lookup','packaging')):raise ValueError('unsafe_source')
    if output.is_symlink() or (output.exists() and (not output.is_dir() or any(output.iterdir()))):
        raise ValueError('build_directory_not_empty')
    files=[]
    for path in (root/'lookup').rglob('*'):
        if path.is_symlink():raise ValueError('unsafe_source')
        if path.is_file() and (path.suffix=='.py' or (path.parent==root/'lookup/data' and path.suffix=='.txt')):
            files.append(path)
    files += [root/'packaging'/name for name in ('lookup','org.lookup.Linux.desktop',
        'org.lookup.Linux.autostart.desktop','THIRD-PARTY.md')]
    if any(path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root) for path in files):
        raise ValueError('unsafe_source')
    names=[];buffer=io.BytesIO()
    with gzip.GzipFile(filename='',mode='wb',mtime=0,fileobj=buffer) as compressed:
        with tarfile.open(fileobj=compressed,mode='w',format=tarfile.USTAR_FORMAT) as archive:
            for path in sorted(files,key=lambda path:path.relative_to(root).as_posix()):
                name='lookup-source/'+path.relative_to(root).as_posix();data=path.read_bytes()
                entry=tarfile.TarInfo(name);entry.size=len(data);entry.mode=0o644
                archive.addfile(entry,io.BytesIO(data));names.append(name)
    data=buffer.getvalue();digest=hashlib.sha256(data).hexdigest()
    template=(root/'PKGBUILD').read_text(encoding='utf-8')
    if template.count('@LOCAL_SOURCE_SHA256@')!=1:raise ValueError('invalid_build_template')
    output.mkdir(parents=True,exist_ok=True)
    (output/'lookup-source.tar.gz').write_bytes(data)
    build=template.replace('@LOCAL_SOURCE_SHA256@',digest)
    (output/'PKGBUILD').write_text(build,encoding='utf-8',newline='\n')
    record=dict(archive='lookup-source.tar.gz',archive_sha256=digest,
                pkgbuild_sha256=hashlib.sha256(build.encode()).hexdigest(),files=names,upstream=ASSETS)
    (output/'SOURCE.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    return record


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:record=stage(args.output)
    except (OSError,ValueError):parser.exit(1,'Не удалось подготовить пакет: нужен пустой каталог и обычные исходные файлы.\n')
    print('Готово: PKGBUILD, lookup-source.tar.gz, SOURCE.json; SHA256='+record['archive_sha256'])


if __name__=='__main__':main()
