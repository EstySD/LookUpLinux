"""Owned-clone package lifecycle; synthetic data only, leave new package installed."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(sys.argv[1]).resolve()
REPORT={'gates':{},'baseline_package':None}
PY='/usr/bin/python'


def run(argv,**kwargs):
    print('RUN '+repr(argv),flush=True)
    return subprocess.run(argv,check=True,timeout=kwargs.pop('timeout',180),**kwargs)


def installed(code,profile):
    profile.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,PYTHONPATH='',PYTHONDONTWRITEBYTECODE='1',QT_QPA_PLATFORM='offscreen',
        LOOKUP_CONFIG=str(profile/'config.json'),LOOKUP_DB=str(profile/'history.db'),
        LOOKUP_DICTS=str(profile/'dicts'),LOOKUP_CACHE=str(profile/'cache'))
    result=run([PY,'-c',"import sys;sys.path.insert(0,'/usr/lib/lookup/app');"+code],env=env,capture_output=True,text=True,encoding='utf-8')
    return json.loads(result.stdout)


def snapshot(profile):
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in profile.iterdir() if p.is_file()}


def main():
    assert os.getuid()==1000 and ROOT.is_relative_to(Path('/home/arch'))
    package=None
    try:
        REPORT['baseline_package']=subprocess.check_output(['pacman','-Q','lookup-linux'],text=True).strip()
        build=ROOT/'aur'
        run(['makepkg','--verifysource','--noconfirm'],cwd=build,timeout=90)
        run(['makepkg','-s','--noconfirm'],cwd=build,timeout=600)
        packages=list(build.glob('lookup-linux-0.2.1-1-x86_64.pkg.tar.zst'));assert len(packages)==1
        package=packages[0];REPORT['package_sha256']=hashlib.sha256(package.read_bytes()).hexdigest()
        REPORT['package']=str(package)
        REPORT['gates']['normal_user_build']=True
        contents=subprocess.check_output(['bsdtar','-tf',str(package)],text=True)
        assert 'mueller' not in contents.lower()
        for name in ('usr/bin/lookup','usr/lib/qt6/plugins/kwin/plugins/lookupcapture.so',
                     'usr/share/licenses/lookup-linux/LICENSE','usr/share/licenses/lookup-linux/NOTICE-wordnet.txt'):
            assert name in contents,name
        REPORT['gates']['public_contents_and_licenses']=True
        run(['sudo','-n','pacman','-U','--noconfirm',str(package)])
        run(['/usr/bin/lookup','--help'],capture_output=True)
        clean=ROOT/'clean-profile'
        clean.mkdir();(clean/'dicts').mkdir()
        (clean/'dicts/public.dsl').write_text('#NAME "Release fixture"\n#INDEX_LANGUAGE "English"\n#CONTENTS_LANGUAGE "Russian"\nbank\n    банк\n',encoding='utf-16')
        (clean/'config.json').write_text('{"online":false,"autostart":false}')
        code="from lookup.store import open_store;from lookup.config import Config;from lookup.dicts import open_all;from lookup.translate import lookup;import json,os;c=open_store();d=open_all(Config(),[os.environ['LOOKUP_DICTS']]);v=lookup('bank',dictset=d,conn=c,online=False);print(json.dumps({'word':v.key,'translation':v.translation,'count':v.count}));d.close();c.close()"
        value=installed(code,clean);assert value=={'word':'bank','translation':'банк','count':1},value
        REPORT['gates']['clean_installed_lookup']=True
        old=Path('/home/arch/lookup-package-08-final-timer/lookup-linux-0.1.0-1-x86_64.pkg.tar.zst')
        assert old.is_file()
        REPORT['old_package_sha256']=hashlib.sha256(old.read_bytes()).hexdigest()
        run(['sudo','-n','pacman','-U','--noconfirm',str(old)])
        profile=ROOT/'upgrade-profile';profile.mkdir()
        (profile/'config.json').write_text('{"online":false,"autostart":false,"popup_timeout":42,"release_preserve":"keep"}')
        seed="from lookup.store import open_store,upsert_word;from lookup.learning import add_history_card;import json;c=open_store();[upsert_word(c,'bank',translation='банк',context='The bank approved the loan.',now=100+i) for i in range(3)];add_history_card(c,'bank',now=200);c.commit();print(json.dumps({'words':c.execute('SELECT * FROM words').fetchall(),'cards':c.execute('SELECT * FROM cards').fetchall()}));c.close()"
        before=installed(seed,profile);files=snapshot(profile)
        assert before['words'] and before['cards']
        run(['sudo','-n','pacman','-U','--noconfirm',str(package)])
        assert snapshot(profile)==files,'package upgrade changed synthetic user files'
        read="from lookup.store import open_store;import json;c=open_store();print(json.dumps({'words':c.execute('SELECT * FROM words').fetchall(),'cards':c.execute('SELECT * FROM cards').fetchall()}));c.close()"
        after=installed(read,profile);assert after==before
        REPORT['gates']['upgrade_v1_words_cards_settings']=True
        files=snapshot(profile)
        run(['sudo','-n','pacman','-R','--noconfirm','lookup-linux'])
        assert snapshot(profile)==files
        assert not Path('/usr/bin/lookup').exists()
        REPORT['gates']['removal_preserves_user_data']=True
    except Exception as error:
        REPORT['error']=type(error).__name__+': '+str(error)[-1500:]
    finally:
        if package is not None:
            try:
                run(['sudo','-n','pacman','-U','--noconfirm',str(package)])
                REPORT['final_package']=subprocess.check_output(['pacman','-Q','lookup-linux'],text=True).strip()
            except Exception as error:REPORT['cleanup_error']=str(error)[-1000:]
        REPORT['passed']=len(REPORT['gates'])==5 and all(REPORT['gates'].values()) and not REPORT.get('error') and not REPORT.get('cleanup_error')
        (ROOT/'package-report.json').write_text(json.dumps(REPORT,ensure_ascii=True,indent=2))
        print(json.dumps(REPORT,ensure_ascii=True),flush=True)
    return int(not REPORT['passed'])


if __name__=='__main__':raise SystemExit(main())
