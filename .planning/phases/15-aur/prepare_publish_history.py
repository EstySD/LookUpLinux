"""Remove only two oversized bundles from unpublished history; keep backup refs/files."""
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[3]
PATHS=['.planning/phases/12-yomitan/source.tar.gz','.planning/phases/13-gui/source.tar.gz']


def git(*args,**kwargs):
    return subprocess.check_output(['git',*args],cwd=ROOT,**kwargs)


def main():
    base=git('ls-remote','origin','refs/heads/main').decode().split()[0]
    tip=git('rev-parse','HEAD').decode().strip()
    subprocess.run(['git','merge-base','--is-ancestor',base,tip],cwd=ROOT,check=True)
    objects=git('rev-list','--objects',base+'..'+tip).decode().splitlines()
    names={line.split(' ',1)[0]:line.split(' ',1)[1] if ' ' in line else '' for line in objects}
    sizes=git('cat-file','--batch-check=%(objectname) %(objecttype) %(objectsize)',input=('\n'.join(names)+'\n').encode()).decode().splitlines()
    large=[{'path':names[oid],'bytes':int(size)} for oid,kind,size in (line.split() for line in sizes) if kind=='blob' and int(size)>100*1024*1024]
    assert {v['path'] for v in large}==set(PATHS),large
    backup='backup/publication-unfiltered-v0.2.1'
    subprocess.run(['git','branch',backup,tip],cwd=ROOT,check=True)
    for tag in ('v0.2.1','milestone/v1.1'):
        subprocess.run(['git','update-ref','refs/backup/'+tag,git('rev-parse',tag).decode().strip()],cwd=ROOT,check=True)
    gitdir=Path(git('rev-parse','--absolute-git-dir').decode().strip())
    index=gitdir/'publication-filter.index';assert not index.exists()
    environment=dict(os.environ,GIT_INDEX_FILE=str(index))
    mapping={}
    try:
        for old in git('rev-list','--reverse','--topo-order',base+'..'+tip).decode().splitlines():
            parents=git('show','-s','--format=%P',old).decode().split()
            newparents=[mapping.get(p,p) for p in parents]
            subprocess.run(['git','read-tree',old+'^{tree}'],cwd=ROOT,env=environment,check=True)
            subprocess.run(['git','update-index','--force-remove','--',*PATHS],cwd=ROOT,env=environment,check=True)
            tree=git('write-tree',env=environment).decode().strip()
            if tree==git('rev-parse',old+'^{tree}').decode().strip() and parents==newparents:
                mapping[old]=old;continue
            fields=git('show','-s','--format=%an%x00%ae%x00%aI%x00%cn%x00%ce%x00%cI',old).decode('utf-8').rstrip('\n').split('\0')
            env=dict(os.environ,**dict(zip(('GIT_AUTHOR_NAME','GIT_AUTHOR_EMAIL','GIT_AUTHOR_DATE','GIT_COMMITTER_NAME','GIT_COMMITTER_EMAIL','GIT_COMMITTER_DATE'),fields)))
            message=git('cat-file','commit',old).partition(b'\n\n')[2]
            argv=['commit-tree',tree]
            for parent in newparents:argv+=['-p',parent]
            mapping[old]=git(*argv,input=message,env=env).decode().strip()
        clean=mapping[tip]
        assert git('rev-parse',clean+'^{tree}')==git('rev-parse',tip+'^{tree}')
        subprocess.run(['git','update-ref','refs/heads/main',clean,tip],cwd=ROOT,check=True)
        for tag,message in [('milestone/v1.1','Complete milestone v1.1: 17 requirements verified'),('v0.2.1','LookUp Linux 0.2.1')]:
            subprocess.run(['git','tag','-f','-a',tag,clean,'-m',message],cwd=ROOT,check=True)
        receipt={'base':base,'original_tip':tip,'published_tip':clean,'backup':backup,'removed_from_unpublished_history':large,
            'files_preserved_on_disk':all((ROOT/p).is_file() for p in PATHS),'mapping':mapping}
        Path(__file__).with_name('publication-history.json').write_text(json.dumps(receipt,indent=2))
        print(json.dumps({k:v for k,v in receipt.items() if k!='mapping'}))
    finally:
        assert index.parent==gitdir
        if index.exists():index.unlink()


if __name__=='__main__':main()
