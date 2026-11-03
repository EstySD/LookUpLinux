"""Verify retained evidence against current product/tests and emit one receipt."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]


def read(name):
    return json.loads((OUT/name).read_text(encoding='utf-8'))


def main():
    manifest=read('native-manifest.json')
    for name,digest in manifest['source_hashes'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    suites={}
    for host in ('host','target'):
        log=(OUT/('native-'+host+'-full.log')).read_text(encoding='utf-8',errors='replace')
        assert 'Ran 868 tests' in log and re.search(r'^OK \(skipped=\d+\)',log,re.M),host
        suites[host]={'tests':868,'failures':0,'errors':0,'skips':int(re.search(r'OK \(skipped=(\d+)\)',log)[1])}
    provider=read('native-provider.json');assert provider['passed'] and len(provider['cases'])==6
    exits=read('borderless/11-native-batch.json')
    assert len(exits['cases'])==7 and all(v['status']=='passed' for v in exits['cases'].values())
    word=read('borderless-word/11-native-batch.json');assert not word['errors'] and word['word_lookup']['same_frame']
    second=read('second-monitor/report.json');assert second['passed'] and len(second['scales'])==2
    monitors=[]
    for case in second['scales']:
        monitor=sorted(case['setup']['monitors'],key=lambda m:m['x'])[1]
        x,y,w,h=case['popup_native']
        assert monitor['x']<=x and monitor['y']<=y and x+w<=monitor['x']+monitor['width'] and y+h<=monitor['y']+monitor['height']
        assert case['river']['product']['frame']==case['bright']['product']['frame']
        assert case['bright']['product']['events'][-1]['translation']=='яркий'
        monitors.append({'scale':case['scale'],'monitor':monitor,'popup_native':case['popup_native'],
            'first_word':'river','second_word':'bright','frame':case['bright']['product']['frame'],'passed':True})
    for host in ('host','target'):
        dictionaries=read(host+'-real-dicts.json');assert dictionaries['passed']
        assert sum(len(d['cases']) for d in dictionaries['dictionaries'].values())==6
    cleanup=read('native-target-report.json');assert cleanup['poweroff'] and cleanup['vm_settings_restored']
    vm=subprocess.check_output(['C:/Program Files/Oracle/VirtualBox/VBoxManage.exe','showvminfo',
        'cf207909-94b5-4b49-8bd8-ccff973c1dc8','--machinereadable'],text=True)
    assert all(value in vm for value in ('VMState="poweroff"','graphicscontroller="vmsvga"','monitorcount=1','clipboard="bidirectional"'))
    receipt={'acceptance':'agent','requirements':{'TRAN-07':'passed','DICT-06':'passed','CAPT-09':'passed','GAME-02':'passed'},
        'suites':suites,'provider':provider['provider'],'provider_cases':6,'dictionary_cases':12,
        'borderless_exits':{k:v['status'] for k,v in exits['cases'].items()},'borderless_word':word['word_target'],
        'monitors':monitors,'cleanup':{'poweroff':True,'settings_restored':True,'original_controlled':False},
        'source_hashes':manifest['source_hashes'],
        'limits':['VirtualBox owned clone; KDE Wayland. No human or physical-hardware acceptance.',
                  'Public Google endpoint is undocumented; client fallback cannot guarantee future availability.',
                  'Native probe setup retries remain on disk; no failed attempt was converted to a pass.',
                  'Unchanged product/test full-suite results and dictionary-reader evidence were reused.']}
    (OUT/'14-ACCEPTANCE.json').write_text(json.dumps(receipt,ensure_ascii=True,indent=2),encoding='utf-8')
    print(json.dumps({'requirements_passed':4,'requirements_failed':0,'requirements_blocked':0,'suites':suites,'functional_cases':28,'receipt':str(OUT/'14-ACCEPTANCE.json')}))


if __name__=='__main__':main()
