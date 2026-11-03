"""Check downloaded third-party DSL/MDX against independently read source data."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lookup import dicts,translate
from lookup.config import Config


def digest(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1 << 20),b''):value.update(block)
    return value.hexdigest()


def check(source,output):
    report={'acceptance':'agent','files':{},'dictionaries':{},'source_hashes':{
        str(p.relative_to(Path(__file__).resolve().parents[1])):digest(p)
        for p in sorted(Path(__file__).resolve().parents[1].joinpath('lookup').glob('*.py'))}}
    for name in ('direct-en-ru_wikidict.dsl','direct-ecdict-mdx-headless-28.zip','direct-ecdict.csv'):
        report['files'][name]=digest(source/name)
    raw=(source/'direct-en-ru_wikidict.dsl').read_text(encoding='utf-8')
    dsl_cases={}
    for word in ('Africa','Japan','South America'):
        # Read the published DSL text directly, independently of lookup.dsl.
        block=next(b for b in raw.split('\n\n') if word in b.split('\n\t',1)[0].splitlines())
        text='\n'.join(line.strip() for line in block.splitlines() if line.startswith('\t'))
        expected=re.findall(r'\[m1\]([^\[]+)\[/m\]',text)
        dsl_cases[word]=next(value for value in expected if re.search('[\u0400-\u04ff]',value))
    del raw
    with (source/'direct-ecdict.csv').open(encoding='utf-8-sig',newline='') as stream:
        rows={row['word']:row for row in csv.DictReader(stream) if row['word'] in ('cat','dog','bank')}
    mdx_cases={word:row['translation'].split('\\n')[0].split(',')[0].split('. ',1)[-1].strip()
               for word,row in rows.items()}
    assert len(mdx_cases)==3
    with tempfile.TemporaryDirectory(prefix='lookup-real-dicts-') as temporary:
        root=Path(temporary)
        os.environ['LOOKUP_CACHE']=str(root/'cache')
        with zipfile.ZipFile(source/'direct-ecdict-mdx-headless-28.zip') as archive:
            members=[m for m in archive.infolist() if m.filename.casefold().endswith('.mdx')]
            assert len(members)==1 and members[0].file_size<=256 << 20
            mdx=root/'ecdict.mdx'
            # Never use archive member names as filesystem paths.
            with archive.open(members[0]) as incoming,mdx.open('wb') as target:
                size=0
                while block:=incoming.read(1 << 20):
                    size+=len(block)
                    assert size<=256 << 20
                    target.write(block)
        for fmt,path,cases in [('dsl',source/'direct-en-ru_wikidict.dsl',dsl_cases),('mdx',mdx,mdx_cases)]:
            result={'cases':{},'expected_source':'published DSL article' if fmt=='dsl' else 'published ECDICT CSV translation'}
            started=time.monotonic()
            dictionaries=None
            try:
                # The exact same reader registry and orchestrator as normal lookup.
                from unittest import mock
                with mock.patch.object(dicts,'discover',return_value=[dicts.Found(path.name,path,fmt,0)]):
                    dictionaries=dicts.open_all(config=Config(),roots=[path.parent])
                result['open_seconds']=time.monotonic()-started
                result['problems']=dictionaries.problems
                result['entries']=dictionaries.info()[0].entries
                for word,expected in cases.items():
                    answer=translate.lookup(word,dictset=dictionaries,online=False,save=False)
                    matched=any(expected in article.text for article in answer.articles)
                    result['cases'][word]={'passed':matched,'expected':expected,'article_count':len(answer.articles)}
                result['passed']=not result['problems'] and all(row['passed'] for row in result['cases'].values())
            except Exception as error:result.update(passed=False,error=type(error).__name__)
            finally:
                if dictionaries is not None:dictionaries.close()
            report['dictionaries'][fmt]=result
    report['passed']=all(value['passed'] for value in report['dictionaries'].values())
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=True,indent=2),encoding='utf-8')
    print(json.dumps(report['dictionaries'],ensure_ascii=True))
    return 0 if report['passed'] else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('source',type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();raise SystemExit(check(args.source,args.output))
