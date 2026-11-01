"""Build public source/build-kit assets without workspace or dictionary leakage."""
import argparse
import gzip
import hashlib
import io
from pathlib import Path
import re
import tarfile
import tempfile

if __package__:
    from .stage_package import ROOT, stage
else:
    from stage_package import ROOT, stage


def archive(destination, files):
    with destination.open('wb') as raw:
        with gzip.GzipFile(filename='', mode='wb', mtime=0, fileobj=raw) as compressed:
            with tarfile.open(fileobj=compressed, mode='w', format=tarfile.USTAR_FORMAT) as tar:
                for name, path in sorted(files):
                    if path.is_symlink() or not path.is_file():
                        raise ValueError('unsafe release input: '+str(path))
                    data = path.read_bytes()
                    if path.suffix in ('.py', '.sh', '.js', '.xml', '.json', '.md', '.yml', '.svg', '.txt') or path.name.startswith('PKGBUILD') or path.name in ('lookup', 'LICENSE'):
                        data = data.replace(b'\r\n', b'\n')
                    info = tarfile.TarInfo(name)
                    info.size = len(data)
                    info.mode = 0o644
                    tar.addfile(info, io.BytesIO(data))


def build(output, tag):
    if not re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+', tag):
        raise ValueError('expected a release tag such as v0.1.0')
    for recipe in ('PKGBUILD', 'packaging/PKGBUILD.public'):
        version = re.search(r'^pkgver=(.+)$', (ROOT/recipe).read_text(), re.M)
        if version is None or version[1] != tag[1:]:
            raise ValueError('tag and package version disagree')
    output = Path(output)
    if output.is_symlink() or (output.exists() and any(output.iterdir())):
        raise ValueError('release output must be a new or empty directory')
    output.mkdir(parents=True, exist_ok=True)
    prefix = 'lookup-linux-'+tag[1:]
    with tempfile.TemporaryDirectory() as directory:
        kit = Path(directory)/'kit'
        stage(kit, public=True)
        archive(output/(prefix+'-archlinux-x86_64-build-kit.tar.gz'),
                [(prefix+'-build-kit/'+p.name, p) for p in kit.iterdir()])
    files = []
    # Explicit roots: never archive .omx, planning, research, personal dictionaries or Git state.
    for folder in ('lookup', 'tests', 'packaging', 'tools', '.github', 'docs/assets'):
        for path in (ROOT/folder).rglob('*'):
            if '__pycache__' in path.parts:
                continue
            if path.is_symlink():
                raise ValueError('symlink in release input')
            if path.is_file() and (path.suffix in ('.py', '.sh', '.js', '.md', '.txt', '.yml', '.svg', '.png', '.json', '.xml', '.in', '.desktop', '.public') or path.name == 'lookup'):
                files.append((prefix+'/'+path.relative_to(ROOT).as_posix(), path))
    for name in ('LICENSE', 'COPYING.md', 'README.md', 'CONTRIBUTING.md', 'SECURITY.md', 'CHANGELOG.md', 'PKGBUILD',
                 'docs/README.ru.md', 'docs/DICTIONARIES.md', 'docs/RELEASING.md', 'docs/RELEASE_NOTES.md',
                 'docs/UBUNTU.md', 'docs/ubuntu-vm-validation.md'):
        files.append((prefix+'/'+name, ROOT/name))
    archive(output/(prefix+'-source.tar.gz'), files)
    (output/'SHA256SUMS').write_text(''.join(
        hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n'
        for p in sorted(output.glob('*.tar.gz'))), encoding='utf-8', newline='\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build(args.output, args.tag)
    print('Public release assets created in '+str(args.output))
