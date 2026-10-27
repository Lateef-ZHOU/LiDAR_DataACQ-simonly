"""Production executable checks: invalid inputs, OS signals, headless sampling and saved products.
Run with the Qt runtime available; hardware transport libraries are not required.
"""
import argparse, json, math, os, pathlib, signal, struct, subprocess, sys, time
p = argparse.ArgumentParser()
p.add_argument('--exe', required=True); p.add_argument('--out', required=True)
a = p.parse_args(); exe = str(pathlib.Path(a.exe).resolve()); out = pathlib.Path(a.out).resolve()
out.mkdir(parents=True, exist_ok=True)
checks=[]
def check(name, passed):
    checks.append(dict(name=name, passed=bool(passed)))
    print(('PASS ' if passed else 'FAIL ') + name, flush=True)
env = os.environ.copy(); env['QT_QPA_PLATFORM']='offscreen'; env['QT_FORCE_STDERR_LOGGING']='1'
for name in ('DISPLAY', 'WAYLAND_DISPLAY'): env.pop(name, None)
for index, args in enumerate([
    ['--fixedAxis','60','0','--accumulate','0'], ['--config','absent.json','--fixedAxis','60','0'],
    ['--fixedAxis','60'], ['--snakeAxis','60','0','90','180'], ['--wrong'],
]):
    result=subprocess.run([exe,*args],cwd=out,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
    (out/f'invalid-{index}.log').write_bytes(result.stderr)
    check('invalid request exits without acquisition', result.returncode==1 and not (out/'Rawspec').exists())
(out/'invalid.json').write_text('{"version":1}',encoding='utf8')
result=subprocess.run([exe,'--config','invalid.json','--fixedAxis','60','0'],cwd=out,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
check('incomplete JSON fails and stays unchanged',result.returncode==1 and (out/'invalid.json').read_text()=='{"version":1}')
result=subprocess.run([exe,'--help'],cwd=out,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
check('help documents height then azimuth',result.returncode==0 and b'--fixedAxis HEIGHT AZIMUTH' in result.stdout)

def launch(args, folder, stdout, stderr):
    if any(x in args for x in ('--fixedAxis', '--cycleAxis', '--snakeAxis')):
        args = ['--headless', *args]
    options = {}
    if os.name == 'nt':
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW; startup.wShowWindow = 0
        options = dict(creationflags=subprocess.CREATE_NEW_CONSOLE, startupinfo=startup)
    return subprocess.Popen([exe, *args], cwd=folder, env=env, stdout=stdout, stderr=stderr, **options)

def interrupt(proc, sig=signal.SIGTERM):
    if os.name != 'nt':
        proc.send_signal(sig)
        return
    # 独立辅助进程只接入被测进程的独立控制台，不影响启动测试的终端。
    code='''import ctypes,time,sys
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.FreeConsole()
if not k.AttachConsole(int(sys.argv[1])): raise OSError(ctypes.get_last_error())
k.SetConsoleCtrlHandler(None,True)
if not k.GenerateConsoleCtrlEvent(0,0): raise OSError(ctypes.get_last_error())
time.sleep(.2)
k.FreeConsole()
'''
    subprocess.run([sys.executable,'-c',code,str(proc.pid)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5)

cases = ([('ui-smoke',0)] if os.name == 'nt' else []) + [('completed-frame',1),('cancel-window',30)]
for case, seconds in cases:
    folder=out/case; folder.mkdir(exist_ok=True)
    with (folder/'stdout.log').open('wb') as stdout, (folder/'stderr.log').open('wb') as stderr:
        args=[] if seconds==0 else ['--fixedAxis','60','0','--accumulate',str(seconds),'--settle','2']
        proc=launch(args, folder, stdout, stderr)
        try:
            limit=time.monotonic()+20
            if seconds==0:
                time.sleep(8)
                check('UI smoke does not start acquisition',not list(folder.glob('Rawspec/**/*.bin')))
            elif seconds==1:
                while proc.poll() is None and time.monotonic()<limit:
                    if any(f.stat().st_size==720000 for f in folder.glob('Rawspec/**/*.bin')): break
                    time.sleep(.1)
                check('real headless process writes double spectrum',any(f.stat().st_size==720000 for f in folder.glob('Rawspec/**/*.bin')))
            else:
                time.sleep(6) # 2 s 移动 + 2 s 停稳后，仍处于 30 s 累积窗。
                check('long accumulation has not completed',not list(folder.glob('Rawspec/**/*.bin')))
            check('task keeps event loop responsive',proc.poll() is None)
            start=time.monotonic(); interrupt(proc); proc.wait(timeout=10)
            check('OS interrupt cancels and exits zero promptly',proc.returncode==0 and time.monotonic()-start<5)
            check('default JSON generated',json.loads((folder/'simulation.json').read_text())['version']==1)
        finally:
            if proc.poll() is None: proc.kill(); proc.wait()
# Linux 真正向运行进程发信号，同时覆盖三个编排的完整落盘。
if os.name != 'nt':
    check('Linux runs without display server variables', not any(env.get(k) for k in ('DISPLAY', 'WAYLAND_DISPLAY')))
    template = json.loads((out/'completed-frame/simulation.json').read_text())
    template['gimbal']['panSpeedDegS'] = template['gimbal']['tiltSpeedDegS'] = 120
    for kind in ('fixedAxis', 'cycleAxis', 'snakeAxis'):
        folder=out/kind; folder.mkdir(exist_ok=True)
        config=folder/'input.json'; config.write_text(json.dumps(template))
        config.chmod(0o444); before=config.read_bytes()
        with (folder/'stdout.log').open('wb') as stdout, (folder/'stderr.log').open('wb') as stderr:
            axes=['60','0'] if kind=='fixedAxis' else ['60','0','90','180','270']
            proc=launch(['--config',str(config),'--'+kind,*axes,'--accumulate','1','--settle','2'],folder,stdout,stderr)
            try:
                deadline=time.monotonic()+100
                while proc.poll() is None and time.monotonic()<deadline:
                    raws=list(folder.glob('Rawspec/**/*.bin'))
                    radial=list(folder.glob('Radialwind/**/*.txt'))
                    profiles=list(folder.glob('Windprofile/*.txt'))
                    if len(raws)>=2 and radial and (kind=='fixedAxis' or profiles): break
                    time.sleep(.2)
                check(kind+' continuously writes spectra and radial wind',len(raws)>=2 and bool(radial))
                if kind!='fixedAxis': check(kind+' completes four-beam inversion and saves profile',bool(profiles))
                # 只检查已完整落盘的帧；退出不要求排空最后一帧。
                complete=[f for f in raws if f.stat().st_size==720000]
                values=struct.unpack('<90000d',complete[0].read_bytes()) if complete else []
                check(kind+' little-endian double shape/range/nonzero',len(values)==90000 and max(values)>0 and all(math.isfinite(v) and 0<=v<=65535 for v in values))
                start=time.monotonic(); interrupt(proc); proc.wait(timeout=15)
                check(kind+' OS SIGTERM normal exit',proc.returncode==0 and time.monotonic()-start<10)
                check(kind+' read-only JSON is untouched',config.read_bytes()==before)
            finally:
                if proc.poll() is None: proc.kill(); proc.wait()
    # 实际 SIGINT 与启动/运动中的 SIGTERM，另有上面的 30 s 累积中 SIGTERM。
    for name,sig,delay in [('sigint',signal.SIGINT,4),('early-term',signal.SIGTERM,.5)]:
        folder=out/name;folder.mkdir(exist_ok=True)
        with (folder/'stdout.log').open('wb') as stdout,(folder/'stderr.log').open('wb') as stderr:
            proc=launch(['--fixedAxis','60','0','--accumulate','30','--settle','2'],folder,stdout,stderr)
            try:
                time.sleep(delay); start=time.monotonic(); interrupt(proc,sig); proc.wait(timeout=15)
                check(name+' normal exit through cancellation',proc.returncode==0 and time.monotonic()-start<10)
            finally:
                if proc.poll() is None: proc.kill();proc.wait()
(out/'cli-results.json').write_text(json.dumps(dict(checks=checks,failures=sum(not c['passed'] for c in checks)),indent=2),encoding='utf8')
sys.exit(any(not c['passed'] for c in checks))
