"""Real X11 windows and OpenGL charts, production sampling/files, window-close and OS signals.

Run on an isolated authenticated X11 display. Needs only Python's standard library and libX11.
Use --exe for a native build, or --image plus --docker for the desktop Docker launcher.
"""
import argparse
import json
import math
import os
from pathlib import Path
import shlex
import signal
import struct
import subprocess
import time
import uuid
from x11 import Desktop

p=argparse.ArgumentParser()
mode=p.add_mutually_exclusive_group(required=True)
mode.add_argument('--exe')
mode.add_argument('--image')
p.add_argument('--docker',default='docker')
p.add_argument('--out',required=True)
a=p.parse_args()
out=Path(a.out).resolve(); out.mkdir(parents=True,exist_ok=True)
repo=Path(__file__).resolve().parents[2]
docker=shlex.split(a.docker)
desktop=Desktop()
checks=[]

def check(name,ok):
    checks.append({'name':name,'passed':bool(ok)})
    print(('PASS ' if ok else 'FAIL ')+name,flush=True)
    (out/'desktop-results.json').write_text(json.dumps({'checks':checks,'failures':sum(not c['passed'] for c in checks)},indent=2))

def call(*args,timeout=30):
    return subprocess.check_output([*docker,*args],stderr=subprocess.STDOUT,text=True,timeout=timeout).strip()

template=json.loads((repo/'config/simulation.example.json').read_text())
template['gimbal']['panSpeedDegS']=template['gimbal']['tiltSpeedDegS']=120
wrapper=out/'docker-command'
if a.image:
    wrapper.write_text('#!/bin/sh\nexec '+shlex.join(docker)+' "$@"\n'); wrapper.chmod(0o700)

cases=[('fixedAxis','window'),('cycleAxis','interrupt'),('snakeAxis','terminate'),('fixedAxis','cancel-window')]
for task,ending in cases:
    folder=out/(task+'-'+ending+'-'+uuid.uuid4().hex[:8]); folder.mkdir()
    data=folder/'output'; data.mkdir(exist_ok=True)
    config=folder/'simulation.json'; config.write_text(json.dumps(template),encoding='utf-8')
    config.chmod(0o444); before=config.read_bytes()
    name='lidar-desktop-'+uuid.uuid4().hex[:10]
    angles=['60','0'] if task=='fixedAxis' else ['60','0','90','180','270']
    args=['--'+task,*angles,'--accumulate','30' if ending=='cancel-window' else '1','--settle','2']
    env=os.environ.copy()
    env.update(QT_QPA_PLATFORM='xcb',QSG_RHI_BACKEND='opengl',LIBGL_ALWAYS_SOFTWARE='1',QT_FORCE_STDERR_LOGGING='1')
    env.pop('QT_QUICK_BACKEND',None)
    proc=None; log=None; created=False
    try:
        if a.image:
            env.update(DOCKER=str(wrapper),IMAGE=a.image,CONTAINER_NAME=name,CONFIG_FILE=str(config),OUTPUT_DIR=str(data))
            launched=subprocess.run(['bash',str(repo/'docker/run-desktop.sh'),*args],env=env,
                                    stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=30)
            if launched.returncode:
                (folder/'launch.log').write_text(launched.stderr,encoding='utf-8')
                raise RuntimeError('Docker desktop launcher failed: '+launched.stderr)
            created=True
        else:
            log=(folder/'run.log').open('w')
            proc=subprocess.Popen([str(Path(a.exe).resolve()),'--config',str(config),*args],cwd=data,env=env,
                                  stdout=log,stderr=subprocess.STDOUT)
        def alive():
            return call('inspect',name,'--format','{{.State.Running}}')=='true' if a.image else proc.poll() is None
        deadline=time.monotonic()+15; window=None
        while time.monotonic()<deadline and alive():
            window=desktop.window()
            if window: break
            time.sleep(.2)
        check(task+' '+ending+' creates a mapped desktop window',window is not None)
        if not window: raise RuntimeError('No mapped window; inspect run.log or docker logs')
        if ending=='cancel-window':
            time.sleep(6)
            check('close during accumulation has no completed frame',not list(data.glob('Rawspec/**/*.bin')))
        else:
            deadline=time.monotonic()+120
            raws=[]; radial=[]; profiles=[]
            while time.monotonic()<deadline and alive():
                raws=[f for f in data.glob('Rawspec/**/*.bin') if f.stat().st_size==720000]
                radial=list(data.glob('Radialwind/**/*.txt'))
                profiles=list(data.glob('Windprofile/*.txt'))
                if len(raws)>=2 and radial and (task=='fixedAxis' or profiles): break
                time.sleep(.25)
            check(task+' desktop continuously samples and saves',len(raws)>=2 and bool(radial))
            if task!='fixedAxis': check(task+' desktop saves four-beam profile',bool(profiles))
            values=struct.unpack('<90000d',raws[0].read_bytes()) if raws else []
            check(task+' desktop little-endian double spectrum valid',
                  len(values)==90000 and max(values)>0 and all(math.isfinite(v) and 0<=v<=65535 for v in values))
            time.sleep(.5)
            window=desktop.window()
            picture=desktop.capture(*window,folder/'surface.png')
            (folder/'picture.json').write_text(json.dumps(picture,indent=2))
            check(task+' desktop surface has rendered spectrum colors',
                  picture['plot_colors']>80 and picture['plot_colored_samples']>3000)
        started=time.monotonic()
        if ending in ('window','cancel-window'):
            desktop.close(window[0])
        elif a.image:
            if ending=='interrupt': call('kill','--signal=SIGINT',name)
            else: call('stop','--time','15',name,timeout=25)
        else:
            proc.send_signal(signal.SIGINT if ending=='interrupt' else signal.SIGTERM)
        if a.image:
            code=int(call('wait',name,timeout=20))
            text=call('logs',name); (folder/'run.log').write_text(text,encoding='utf-8')
        else:
            code=proc.wait(timeout=20); log.close(); log=None
            text=(folder/'run.log').read_text(encoding='utf-8',errors='replace')
        check(task+' '+ending+' exits zero without forced kill',code==0 and time.monotonic()-started<15)
        stop=text.find('任务已停止'); quit=text.find('任务已取消，退出事件循环')
        check(task+' '+ending+' stops task before event-loop exit',0<=stop<quit)
        check(task+' configuration unchanged',config.read_bytes()==before)
        check(task+' no QML or graphics initialization errors',
              not any(x in text for x in ('QQmlApplicationEngine failed','ReferenceError:','TypeError:',
                  'Failed to create OpenGL context','Failed to initialize graphics backend','Binding loop detected',
                  'Cannot queue arguments')))
    finally:
        if a.image and created:
            (folder/'run.log').write_text(call('logs',name),encoding='utf-8')
            # Only the unique container created by this test is removed.
            subprocess.run([*docker,'rm','-f',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        if proc and proc.poll() is None: proc.kill(); proc.wait()
        if log: log.close()

(out/'desktop-results.json').write_text(json.dumps({'checks':checks,'failures':sum(not c['passed'] for c in checks)},indent=2))
raise SystemExit(any(not c['passed'] for c in checks))
