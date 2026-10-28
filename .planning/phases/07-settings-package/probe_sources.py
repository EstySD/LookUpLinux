"""Read-only public upstream provenance probes; never reads local secrets."""
import hashlib
import io
import json
import tarfile
import urllib.request
from pathlib import Path

BASE = Path(__file__).parent


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'LookUpLinux-research'}), timeout=20) as response:
        data = response.read(24 << 20)
    return data


def main():
    result = {}
    try:
        release = json.loads(get('https://api.github.com/repos/jinliu/kdotool/releases/tags/v0.3.0'))
        assets = [{key: item.get(key) for key in ('name', 'browser_download_url', 'digest', 'size')} for item in release['assets']]
        result['kdotool_release'] = dict(tag=release['tag_name'], assets=assets)
        for item in assets:
            if 'x86_64' in item['name']:
                data = get(item['browser_download_url'])
                archive = tarfile.open(fileobj=io.BytesIO(data))
                result['kdotool_asset'] = dict(url=item['browser_download_url'], sha256=hashlib.sha256(data).hexdigest(), files=archive.getnames())
    except Exception as error:
        result['kdotool_error'] = type(error).__name__ + ':' + str(error)[:120]
    for name, url in (
        ('mueller', 'https://qstardict.ylsoftware.com/files/mueller7.tar.bz2'),
        ('kdotool_source', 'https://codeload.github.com/jinliu/kdotool/tar.gz/refs/tags/v0.3.0'),
    ):
        try:
            data = get(url)
            archive = tarfile.open(fileobj=io.BytesIO(data))
            result[name] = dict(url=url, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), files=archive.getnames())
            texts = {}
            for item in archive.getmembers():
                if item.isfile() and (item.name.endswith(('.ifo', 'Cargo.toml')) or 'LICENSE' in item.name.upper() or 'COPYING' in item.name.upper()):
                    texts[item.name] = archive.extractfile(item).read(6000).decode('utf-8', 'replace')
            result[name]['metadata'] = texts
        except Exception as error:
            result[name] = dict(error=type(error).__name__ + ':' + str(error)[:120])
    (BASE/'source-probes.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    for name, value in result.items():
        print(name, json.dumps({k:v for k,v in value.items() if k not in ('metadata','files')}, ensure_ascii=True) if isinstance(value,dict) else value)


if __name__ == '__main__':
    main()
