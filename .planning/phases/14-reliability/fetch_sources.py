"""Bounded, explicit direct/proxy downloads with hashes and route receipts."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

OUT=Path(__file__).resolve().parent/'downloads'
LIMIT=128 << 20


def fetch(name,url,route):
    proxy=os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
    if route=='proxy' and not proxy:return {'name':name,'route':route,'error':'no configured proxy'}
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({'http':proxy,'https':proxy} if route=='proxy' else {}))
    started=time.monotonic()
    receipt={'name':name,'url':url,'route':route}
    try:
        request=urllib.request.Request(url,headers={'User-Agent':'LookUpLinux-compatibility-check','Accept':'application/vnd.github+json' if 'api.github.com' in url else '*/*'})
        with opener.open(request,timeout=40) as response:
            blob=response.read(LIMIT+1)
            if len(blob)>LIMIT:raise ValueError('download exceeds 128MiB cap')
            receipt.update(status=response.status,bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest())
        path=OUT/(route+'-'+name)
        path.write_bytes(blob)
        receipt['path']=str(path.relative_to(OUT.parent))
    except urllib.error.HTTPError as error:receipt.update(status=error.code,error=type(error).__name__)
    except Exception as error:receipt['error']=type(error).__name__
    receipt['seconds']=round(time.monotonic()-started,3)
    return receipt


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    jobs=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures=[pool.submit(fetch,name,url,route) for name,url in jobs.items() for route in ('direct','proxy')]
        receipts=[future.result() for future in futures]
    path=OUT/(Path(sys.argv[1]).stem+'-receipts.json')
    path.write_text(json.dumps(receipts,indent=2),encoding='utf-8')
    print(json.dumps(receipts))


if __name__=='__main__':main()
