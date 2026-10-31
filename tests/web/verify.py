"""Web container integration; browser interaction is verified separately on a real browser."""
import argparse
import json
import math
import os
from pathlib import Path
import shlex
import struct
import subprocess
import time
import urllib.request
import uuid

p = argparse.ArgumentParser()
p.add_argument('--image', default='lidar-simonly-web:1.2.1')
p.add_argument('--base', default='lidar-simonly:1.2.1')
p.add_argument('--docker', default='docker')
p.add_argument('--out', required=True)
a = p.parse_args()
docker = shlex.split(a.docker)
repo = Path(__file__).resolve().parents[2]
out = Path(a.out).resolve()
out.mkdir(parents=True, exist_ok=True)
checks = []


def call(*args, timeout=45):
    return subprocess.check_output([*docker, *args], stderr=subprocess.STDOUT,
                                   text=True, timeout=timeout).strip()


def check(name, passed):
    checks.append({'name': name, 'passed': bool(passed)})
    print(('PASS ' if passed else 'FAIL ') + name, flush=True)
    (out / 'web-results.json').write_text(json.dumps({
        'checks': checks, 'failures': sum(not c['passed'] for c in checks)
    }, indent=2), encoding='utf-8')


def binary_hash(image):
    return call('run', '--rm', '--entrypoint', 'sha256sum', image,
                '/opt/lidar/bin/LiDAR_DataACQ').split()[0]


def valid_profile(path):
    try:
        profile = json.loads(path.read_text(encoding='utf-8'))
        columns = [profile[key] for key in ['HSpeed', 'HDir', 'VSpeed', 'High']]
        size = len(columns[0])
        return (size > 1 and all(len(column) == size for column in columns)
                and all(math.isfinite(height) for height in columns[3])
                and all(b > a for a, b in zip(columns[3], columns[3][1:]))
                and any(all(math.isfinite(value) for value in row)
                        for row in zip(*columns[:3]))
                and isinstance(profile['Date'], str) and bool(profile['Date']))
    except (OSError, ValueError, KeyError, TypeError):
        return False  # A file may still be in the existing asynchronous save operation.


check('application binary is unchanged from desktop image', binary_hash(a.image) == binary_hash(a.base))
check('version remains available without a display',
      '1.2.1-simonly' in call('run', '--rm', a.image, '--version'))
template = json.loads((repo / 'config/simulation.example.json').read_text())
template['gimbal']['panSpeedDegS'] = template['gimbal']['tiltSpeedDegS'] = 120

for kind in ['default-auto', 'fixedAxis', 'cycleAxis', 'snakeAxis', 'cancel-window']:
    folder = out / (kind + '-' + uuid.uuid4().hex[:8])
    folder.mkdir()
    data = folder / 'output'
    data.mkdir()
    config = folder / 'simulation.json'
    config.write_text(json.dumps(template), encoding='utf-8')
    config.chmod(0o444)
    before = config.read_bytes()
    name = 'lidar-web-test-' + uuid.uuid4().hex[:10]
    cancel = kind == 'cancel-window'
    task = 'cycleAxis' if kind == 'default-auto' else 'fixedAxis' if cancel else kind
    angles = ['60', '0'] if task == 'fixedAxis' else ['60', '0', '90', '180', '270']
    # Omit TASK and timing completely to verify the shipping startup defaults.
    task_args = [] if kind == 'default-auto' else [
        '--' + task, *angles, '--accumulate', '30' if cancel else '1', '--settle', '2']
    call('run', '-d', '--name', name, '--user', f'{os.getuid()}:{os.getgid()}',
         '--cap-drop=ALL', '--security-opt=no-new-privileges', '--shm-size=256m',
         '-p', '127.0.0.1::6080',
         '-v', f'{config}:/config/simulation.json:ro', '-v', f'{data}:/data',
         a.image, '--config', '/config/simulation.json', *task_args)
    try:
        port = json.loads(call('inspect', name))[0]['NetworkSettings']['Ports']['6080/tcp'][0]['HostPort']
        url = f'http://127.0.0.1:{port}'
        ready = False
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(url + '/vnc.html', timeout=1) as response:
                    ready = b'noVNC' in response.read()
                if ready:
                    break
            except OSError:
                pass
            time.sleep(.2)
        check(kind + ' serves noVNC', ready)
        if kind == 'default-auto':
            with urllib.request.urlopen(url + '/', timeout=3) as response:
                landing = response.read().decode('utf-8')
            check('LAN landing page selects maximum quality and minimum compression',
                  'quality=9&amp;compression=0' in landing)
            processes = call('top', name, '-eo', 'pid,args')
            check('omitted task starts the default four-beam cycle task',
                  '/opt/lidar/bin/LiDAR_DataACQ --config /config/simulation.json --cycleAxis 60 0 90 180 270' in processes)
            check('LAN capture/dispatch intervals are applied', '-wait 20 -defer 5' in processes)
        inspect = json.loads(call('inspect', name))[0]
        if kind == 'default-auto':
            check('no VNC password file or environment setting is required',
                  all(not m['Destination'].startswith('/run/secrets') for m in inspect['Mounts'])
                  and not any(e.startswith('VNC_PASSWORD') for e in inspect['Config']['Env']))
            # Exercise the RFB security negotiation, not just the x11vnc command line.
            auth_probe = r'''
import json
import socket
with socket.create_connection(('127.0.0.1', 5900), timeout=3) as peer:
    def receive(size):
        result = b''
        while len(result) < size:
            chunk = peer.recv(size - len(result))
            if not chunk:
                raise RuntimeError('VNC closed during security negotiation')
            result += chunk
        return result
    assert receive(12).startswith(b'RFB ')
    peer.sendall(b'RFB 003.008\n')
    security_types = list(receive(receive(1)[0]))
    assert 1 in security_types, security_types
    peer.sendall(b'\x01')
    status = int.from_bytes(receive(4), 'big')
    print(json.dumps({'security_types': security_types, 'status': status}))
'''
            auth = json.loads(call('exec', name, 'python3', '-c', auth_probe))
            check('VNC accepts a connection without a password',
                  auth['security_types'] == [1] and auth['status'] == 0)
        check(kind + ' has no host display/GPU or privileges',
              not inspect['HostConfig']['Privileged']
              and not inspect['HostConfig']['Devices']
              and all(m['Destination'] not in ['/tmp/.X11-unix', '/dev/dri'] for m in inspect['Mounts']))
        check(kind + ' only publishes the browser port',
              set(inspect['HostConfig']['PortBindings']) == {'6080/tcp'})
        call('cp', str(repo / 'tests/desktop/x11.py'), name + ':/tmp/lidar_test_x11.py')
        script = (
            "import os,sys,json; from pathlib import Path; sys.path.insert(0,'/tmp'); "
            "os.environ['DISPLAY']=':99'; "
            "os.environ['XAUTHORITY']=str(next(Path('/tmp').glob('lidar-web.*/Xauthority'))); "
            "from lidar_test_x11 import Desktop; d=Desktop(); w=d.window(); "
            "assert w, 'no mapped application window'; "
        )
        deadline = time.monotonic() + (5 if cancel else 110)
        raws = []
        radial = []
        profiles = []
        while time.monotonic() < deadline:
            raws = [f for f in data.glob('Rawspec/**/*.bin') if f.stat().st_size == 720000]
            radial = list(data.glob('Radialwind/**/*.txt'))
            profiles = [f for f in data.glob('Windprofile/*.txt') if valid_profile(f)]
            if not cancel and len(raws) >= 2 and radial and (task == 'fixedAxis' or profiles):
                break
            time.sleep(.2)
        if cancel:
            check('long accumulation has not yet produced a frame', not raws)
        else:
            check(kind + ' samples without any browser connected', len(raws) >= 2 and radial)
            if task != 'fixedAxis':
                check(kind + ' saves complete four-beam profile with finite wind values', profiles)
            values = struct.unpack('<90000d', raws[0].read_bytes()) if raws else []
            check(kind + ' spectrum and output ownership are valid', len(values) == 90000
                  and max(values) > 0 and all(math.isfinite(v) and 0 <= v <= 65535 for v in values)
                  and raws[0].stat().st_uid == os.getuid())
            picture = json.loads(call('exec', name, 'python3', '-c', script +
                                     "print(json.dumps(d.capture(*w,'/tmp/web-surface.png')))"))
            call('cp', name + ':/tmp/web-surface.png', str(folder / 'surface.png'))
            check(kind + ' real OpenGL surface is rendered',
                  picture['plot_colors'] > 80 and picture['plot_colored_samples'] > 3000)
        started = time.monotonic()
        if kind == 'fixedAxis':
            call('exec', name, 'python3', '-c', script + 'd.close(w[0])')
        elif kind == 'cycleAxis':
            call('kill', '--signal=SIGINT', name)
        else:
            call('stop', '--time', '12', name, timeout=20)
        code = int(call('wait', name, timeout=15))
        state = json.loads(call('inspect', name))[0]['State']
        log = call('logs', name)
        (folder / 'container.log').write_text(log, encoding='utf-8')
        check(kind + ' exits zero without forced kill', code == 0 and not state['OOMKilled']
              and time.monotonic() - started < 12)
        stop = log.find('任务已停止')
        quit_at = log.find('任务已取消，退出事件循环')
        check(kind + ' cancellation runs before display shutdown', 0 <= stop < quit_at)
        check(kind + ' read-only configuration unchanged', config.read_bytes() == before)
        check(kind + ' no QML/OpenGL initialization errors', not any(x in log for x in [
            'ReferenceError:', 'TypeError:', 'Failed to create OpenGL context',
            'Failed to initialize graphics backend', 'QQmlApplicationEngine failed', 'Binding loop detected']))
    finally:
        (folder / 'container.log').write_text(call('logs', name), encoding='utf-8')
        call('rm', '-f', name)

raise SystemExit(any(not c['passed'] for c in checks))
