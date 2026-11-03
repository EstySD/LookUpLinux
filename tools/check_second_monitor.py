"""Native second-output lookup with physical input and the real product."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.check_frozen_product import write


def host(output):
    output.mkdir(parents=True,exist_ok=True)
    root=Path(__file__).resolve().parents[1]
    ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','HostKeyAlias=lookup-gsd-07',
        '-o','UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts','-p','2227','archvm']
    snapshot='/tmp/lookup-frozen-product-11/snapshot'
    guest='/tmp/lookup-frozen-product-11/monitor-'+str(int(time.time()))
    prelude="from pathlib import Path\nimport os,json,time\nfrom lookup import platform\nfrom tools.check_frozen_product import control,environment,borderless_window\nenvironment()\nr=Path('"+guest+"')\n"
    report={'acceptance':'agent','guest_root':guest,'scales':[],'errors':[]}
    def remote(code):
        encoded=base64.b64encode((prelude+code).encode()).decode()
        command='echo '+encoded+' | base64 -d | sudo -n -H -u lookup07 env PYTHONPATH='+snapshot+' python -'
        value=subprocess.run([*ssh,command],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30)
        if value.returncode:raise RuntimeError(value.stderr[-1200:])
        return json.loads(value.stdout)
    def physical(action,**values):
        command=['powershell','-NoProfile','-File',str(root/'tools/check_package_vm.ps1'),'-Action',action]
        for key,value in values.items():command+=['-'+key,str(round(value)) if isinstance(value,float) else str(value)]
        subprocess.run(command,check=True,capture_output=True,timeout=15)
    def state():return remote("print(json.dumps(control(r,'status')))\n")
    def wait(predicate,limit=15):
        deadline=time.monotonic()+limit
        while time.monotonic()<deadline:
            value=state()
            if predicate(value):return value
            time.sleep(.15)
        raise RuntimeError('bounded_wait_expired')
    position=[0,0]
    def move(point,scale):
        # VBox absolute coordinates address the first framebuffer; its input
        # spans the entire desktop. Confirm delivery before sending buttons.
        raw_x=(1280+(point[0]-1280)*scale)/2
        raw_y=point[1]*scale
        for _ in range(16):
            physical('Pointer',X=raw_x,Y=raw_y)
            actual=remote("print(json.dumps(platform.cursor_position(os.environ)))\n")
            dx,dy=point[0]-actual[0],point[1]-actual[1]
            if abs(dx)<=2 and abs(dy)<=2:
                position[:]=[raw_x,raw_y]
                return actual
            raw_x+=dx*scale/2;raw_y+=dy*scale
        raise RuntimeError('cursor_did_not_reach_target')
    def escape():physical('Keys',Codes='01 81')
    try:
        physical('Check')
        subprocess.run([*ssh,'sudo -n install -d -m 700 -o lookup07 -g lookup07 '+guest],check=True,capture_output=True)
        report['prepare']=remote("print(json.dumps(control(r,'prepare')))\n")
        remote("(r/'no-tooltip').touch();control(r,'source');control(r,'product');print(json.dumps({'started':True}))\n")
        wait(lambda v:v['source'] and v['product'])
        report['effective_keys']=remote("from lookup import lifecycle;print(json.dumps([lifecycle.key_text(k) for k in lifecycle.inspect_shortcut().keys]))\n")
        key=report['effective_keys'][0]
        assert key in ('Meta+Shift+D','Meta+Shift+E'),key
        scan='20' if key.endswith('+D') else '12'
        for scale in (1,1.25):
            case={'scale':scale,'passed':False}
            try:
                setup="outputs=platform.parse_monitors(platform.run(['kscreen-doctor','-j'],os.environ,timeout=15));assert len(outputs)==2;second=sorted(outputs,key=lambda m:m.x)[1];platform.run(['kscreen-doctor','output.'+second.name+'.scale.'+str("+str(scale)+")],os.environ,timeout=15);time.sleep(1);s=control(r,'status')['source'];window=borderless_window(s['pid'],r/'source',1);outputs=platform.parse_monitors(platform.run(['kscreen-doctor','-j'],os.environ,timeout=15));print(json.dumps({'window':window,'monitors':[m.__dict__ for m in outputs]}))\n"
                case['setup']=remote(setup)
                second=sorted(case['setup']['monitors'],key=lambda m:m['x'])[1]
                time.sleep(.4);before=state();point=before['source']['points']['river']
                case['cursor']=move(point,scale)
                physical('Keys',Codes='e0 5b 2a '+scan+' '+('a0' if scan=='20' else '92')+' aa e0 db')
                selected=wait(lambda v:v['product']['layer'] and v['product']['events'][-1]['stage'] in ('ready','context','error'))
                case['river']=selected
                frame=selected['product']['frame'];session=selected['product']['scene_id']
                layer=selected['product']['layer_geometry']
                assert selected['product']['events'][-1].get('word')=='river',selected['product']['events'][-1]
                assert layer==[second[k] for k in ('x','y','width','height')],layer
                wait(lambda v:v['product'].get('popup_armed') and v['product'].get('popup_uuid'))
                case['popup_native']=remote("s=control(r,'status')['product'];print(json.dumps(platform.window_geometry(os.environ,s['pid'],s['popup_uuid'])))\n")
                point=selected['source']['points']['bright'];move(point,scale)
                prior=selected['product']['events'][-1]['id']
                physical('Pointer',X=position[0],Y=position[1],Buttons=1)
                physical('Pointer',X=position[0],Y=position[1],Buttons=0)
                case['clicked_cursor']=remote("print(json.dumps(platform.cursor_position(os.environ)))\n")
                chosen=wait(lambda v:v['product']['events'][-1]['id']>prior and v['product']['events'][-1]['stage'] in ('ready','context','error'))
                case['bright']=chosen
                image=remote("import base64;print(json.dumps(base64.b64encode((r/'product/capture.png').read_bytes()).decode()))\n")
                (output/('capture-'+str(scale)+'.png')).write_bytes(base64.b64decode(image))
                event=chosen['product']['events'][-1];geometry=chosen['product']['popup_geometry']
                assert event.get('word')=='bright' and event.get('translation'),event
                assert chosen['product']['frame']==frame and chosen['product']['scene_id']==session
                assert second['x']<=geometry[0] and second['y']<=geometry[1]
                assert geometry[0]+geometry[2]<=second['x']+second['width'] and geometry[1]+geometry[3]<=second['y']+second['height'],geometry
                assert selected['source']['count']==chosen['source']['count']
                escape();wait(lambda v:not v['product']['layer'])
                move((second['x']+400,second['y']+350),scale)
                after=wait(lambda v:v['source']['count']>chosen['source']['count'])
                case['after']=after;case['passed']=True
            except Exception as error:
                case['error']=str(error)[-1500:]
                try:case['last_observation']=state()
                except Exception as read_error:case['observation_error']=str(read_error)[-500:]
                try:
                    image=remote("import base64;print(json.dumps(base64.b64encode((r/'product/capture.png').read_bytes()).decode()))\n")
                    (output/('capture-'+str(scale)+'.png')).write_bytes(base64.b64decode(image))
                except Exception as image_error:case['image_error']=str(image_error)[-500:]
            finally:
                escape()
            report['scales'].append(case)
            write(output/'report.json',report)
    except Exception as error:report['errors'].append(str(error)[-1500:])
    finally:
        try:
            remote("outputs=platform.parse_monitors(platform.run(['kscreen-doctor','-j'],os.environ,timeout=15));platform.run(['kscreen-doctor',*['output.'+m.name+'.scale.1' for m in outputs]],os.environ,timeout=15);print(json.dumps({'restored':True}))\n")
            report['cleanup']=remote("print(json.dumps(control(r,'stop')))\n")
        except Exception as error:report['cleanup_error']=str(error)[-1500:]
        report['passed']=len(report['scales'])==2 and all(case['passed'] for case in report['scales']) and not report['errors'] and not report.get('cleanup_error') and all(report.get('cleanup',{}).get('profiles',{}).values())
        write(output/'report.json',report)
    print(json.dumps({'passed':report['passed'],'scales':[{k:c[k] for k in ('scale','passed','error') if k in c} for c in report['scales']],'errors':report['errors']}))
    return int(not report['passed'])


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path)
    raise SystemExit(host(parser.parse_args().output))
