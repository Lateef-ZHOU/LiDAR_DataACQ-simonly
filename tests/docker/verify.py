"""Linux Docker integration: read-only config, real products and SIGTERM cancellation."""
import argparse
import json
import math
import os
from pathlib import Path
import shlex
import struct
import subprocess
import time
import uuid

p = argparse.ArgumentParser()
p.add_argument('--image', default='lidar-simonly:1.2.1')
p.add_argument('--out', required=True)
p.add_argument('--docker', default='docker', help='For example: sudo -n docker')
a = p.parse_args()
out = Path(a.out).resolve()
out.mkdir(parents=True, exist_ok=True)
docker = shlex.split(a.docker)
checks = []


def call(*args, timeout=120):
    return subprocess.check_output([*docker, *args], stderr=subprocess.STDOUT,
                                   timeout=timeout, text=True).strip()


def check(name, ok):
    checks.append({'name': name, 'passed': bool(ok)})
    print(('PASS ' if ok else 'FAIL ') + name, flush=True)


check('x86_64 image', call('image', 'inspect', a.image, '--format', '{{.Architecture}}') == 'amd64')
check('no display or GPU required', call('run', '--rm', '--entrypoint', '/bin/sh', a.image,
      '-c', 'test ! -e /dev/dri && test -z "$DISPLAY$WAYLAND_DISPLAY" && echo ok') == 'ok')
check('no compiler in runtime image', call('run', '--rm', '--entrypoint', '/bin/sh', a.image,
      '-c', '! command -v g++ && ! command -v cmake && echo ok') == 'ok')
linked = call('run', '--rm', '--entrypoint', '/usr/bin/ldd', a.image, '/opt/lidar/bin/LiDAR_DataACQ')
check('no missing, serial or pcap runtime libraries', all(x not in linked for x in ['not found', 'libpcap', 'libserialport']))
template = json.loads((Path(__file__).resolve().parents[2] / 'config/simulation.example.json').read_text())
template['gimbal']['panSpeedDegS'] = template['gimbal']['tiltSpeedDegS'] = 120

for kind in ['fixedAxis', 'cycleAxis', 'snakeAxis', 'cancel-window']:
    folder = out / (kind + '-' + uuid.uuid4().hex[:8])
    folder.mkdir()
    config = folder / 'simulation.json'
    config.write_text(json.dumps(template), encoding='utf-8')
    config.chmod(0o444)
    before = config.read_bytes()
    data = folder / 'output'
    data.mkdir()
    name = 'lidar-test-' + uuid.uuid4().hex[:12]
    cancel = kind == 'cancel-window'
    task = 'fixedAxis' if cancel else kind
    angles = ['60', '0'] if task == 'fixedAxis' else ['60', '0', '90', '180', '270']
    call('run', '-d', '--name', name, '--user', f'{os.getuid()}:{os.getgid()}',
         '-v', f'{config}:/config/simulation.json:ro', '-v', f'{data}:/data', a.image,
         '--headless', '--config', '/config/simulation.json', '--'+task, *angles,
         '--accumulate', '30' if cancel else '1', '--settle', '2')
    try:
        deadline = time.monotonic() + (6 if cancel else 100)
        while time.monotonic() < deadline:
            raws = [f for f in data.glob('Rawspec/**/*.bin') if f.stat().st_size == 720000]
            radial = list(data.glob('Radialwind/**/*.txt'))
            profiles = list(data.glob('Windprofile/*.txt'))
            if not cancel and len(raws) >= 2 and radial and (task == 'fixedAxis' or profiles):
                break
            time.sleep(.2)
        check(kind+' running before stop', call('inspect', name, '--format', '{{.State.Running}}') == 'true')
        if cancel:
            check('cancel during accumulation has no completed frame', not raws)
        else:
            check(kind+' continuously saves spectra and radial wind', len(raws) >= 2 and radial)
            if task != 'fixedAxis':
                check(kind+' four-beam inversion saved', profiles)
            values = struct.unpack('<90000d', raws[0].read_bytes()) if raws else []
            check(kind+' double spectrum shape and values', len(values) == 90000 and max(values) > 0
                  and all(math.isfinite(v) and 0 <= v <= 65535 for v in values))
            check(kind+' output owned by calling user', raws and raws[0].stat().st_uid == os.getuid())
        start = time.monotonic()
        call('stop', '--time', '10', name, timeout=20)
        state = json.loads(call('inspect', name))[0]['State']
        check(kind+' SIGTERM exits zero without forced kill', state['ExitCode'] == 0
              and not state['OOMKilled'] and time.monotonic()-start < 10)
        log = call('logs', name)
        (folder/'container.log').write_text(log, encoding='utf-8')
        check(kind+' cancellation reaches main thread', '任务已取消' in log)
        check(kind+' no QML load or binding errors', not any(x in log for x in
              ['ReferenceError', 'TypeError', 'failed to load component', 'Binding loop']))
        check(kind+' read-only JSON unchanged', config.read_bytes() == before)
    finally:
        call('rm', '-f', name)

report = {'checks': checks, 'failures': sum(not c['passed'] for c in checks)}
(out/'docker-results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
raise SystemExit(bool(report['failures']))
