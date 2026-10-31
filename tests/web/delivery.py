"""Validate an offline bundle with a Docker daemon in its own network namespace."""
import argparse
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import tarfile
import tempfile
import time
import urllib.request
import uuid

p = argparse.ArgumentParser()
p.add_argument('--archive', required=True)
p.add_argument('--out', required=True)
a = p.parse_args()
archive = Path(a.archive).resolve()
out = Path(a.out).resolve()
out.mkdir(parents=True, exist_ok=False)
image = 'lidar-simonly-web:1.2.1'
checks = []


def check(name, passed):
    checks.append({'name': name, 'passed': bool(passed)})
    print(('PASS ' if passed else 'FAIL ') + name, flush=True)
    (out / 'delivery-results.json').write_text(json.dumps({
        'checks': checks, 'failures': sum(not c['passed'] for c in checks)
    }, indent=2))
    if not passed:
        raise RuntimeError(name)


def call(args, timeout=60, report_failure=True, **kwargs):
    try:
        return subprocess.check_output(args, stderr=subprocess.STDOUT, text=True,
                                       timeout=timeout, **kwargs).strip()
    except subprocess.CalledProcessError as error:
        if report_failure:
            print(error.output, flush=True)
            (out / 'command-failure.log').write_text(error.output)
        raise


host = ['sudo', '-n', 'docker']
original = json.loads(call([*host, 'image', 'inspect', image]))[0]
with tarfile.open(archive) as package:
    members = package.getmembers()
    roots = {Path(m.name).parts[0] for m in members}
    check('archive has one self-contained Web bundle',
          roots == {'LiDAR-simonly-1.2.1-linux-amd64-web'})
    package.extractall(out / 'extracted', filter='data')
bundle = out / 'extracted' / next(iter(roots))
check('bundle contains no collected output, passwords or host display credentials',
      not (bundle / 'web-state').exists()
      and not any(x in m.name.lower() for m in members for x in ['vnc-password', 'xauthority']))
check('all bundled checksums match', 'FAILED' not in call(['sha256sum', '-c', 'SHA256SUMS'], cwd=bundle))

token = uuid.uuid4().hex[:10]
runtime = Path(tempfile.mkdtemp(prefix='lidar-offline-'))
sock = runtime / 'docker.sock'
pidfile = runtime / 'daemon.pid'
config = out / 'daemon.json'
config.write_text(json.dumps({'features': {'containerd-snapshotter': False}}))
iso = ['sudo', '-n', 'docker', '--host', 'unix://' + str(sock)]
daemon_log = (out / 'daemon.log').open('w')
# Even --bridge=none may remove docker0 when dockerd initializes. A distinct
# network namespace is mandatory; flags alone cannot isolate the host network.
host_netns = call(['sudo', '-n', 'readlink', '/proc/1/ns/net'])
daemon = subprocess.Popen([
    'sudo', '-n', 'unshare', '--net', '--', 'dockerd', '--config-file', str(config),
    '--host', 'unix://' + str(sock), '--data-root', str(out / 'daemon-data'),
    '--exec-root', str(runtime / 'exec'), '--pidfile', str(pidfile),
    '--storage-driver=overlay2', '--bridge=none', '--iptables=false', '--ip6tables=false',
    '--ip-forward=false', '--ip-masq=false', '--containerd-namespace=web-offline-' + token,
    '--containerd-plugins-namespace=web-offline-plugins-' + token,
], stdout=daemon_log, stderr=subprocess.STDOUT)
offline_name = 'lidar-web-offline-' + token
script_name = 'lidar-web-package-' + token
try:
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline and daemon.poll() is None:
        try:
            info = json.loads(call([*iso, 'info', '--format', '{{json .}}'],
                                   timeout=3, report_failure=False))
            break
        except (subprocess.SubprocessError, ValueError):
            time.sleep(.3)
    else:
        raise RuntimeError('Isolated Docker did not start; see daemon.log')
    daemon_netns = call(['sudo', '-n', 'readlink', f'/proc/{pidfile.read_text().strip()}/ns/net'])
    check('test Docker has a separate network namespace from the host', daemon_netns != host_netns)
    check('isolated Docker starts with zero images', info['Images'] == 0)
    isolated_env = ['sudo', '-n', 'env', 'DOCKER_HOST=unix://' + str(sock)]
    missing = subprocess.run([*isolated_env, 'bash', str(bundle / 'start.sh')],
                             capture_output=True, text=True, timeout=15)
    check('start without imported image fails locally and requests import',
          missing.returncode != 0 and 'import.sh' in missing.stderr)
    imported = call([*isolated_env, 'bash', str(bundle / 'import.sh')], timeout=180)
    (out / 'import.log').write_text(imported)
    loaded = json.loads(call([*iso, 'image', 'inspect', image]))[0]
    check('imported image includes every original filesystem layer', loaded['RootFS'] == original['RootFS'])
    check('imported image is Linux amd64', loaded['Os'] == 'linux' and loaded['Architecture'] == 'amd64')
    data = out / 'offline-output'
    data.mkdir()
    call([*iso, 'run', '-d', '--pull=never', '--name', offline_name,
          '--network=none', '--user', f'{os.getuid()}:{os.getgid()}',
          '--cap-drop=ALL', '--security-opt=no-new-privileges', '--shm-size=256m',
          '-v', f'{bundle / "config"}:/config:ro', '-v', f'{data}:/data',
          image, '--config', '/config/simulation.example.json'])
    deadline = time.monotonic() + 110
    profile = None
    while time.monotonic() < deadline:
        for path in (data / 'Windprofile').glob('*.txt'):
            try:
                candidate = json.loads(path.read_text())
                columns = [candidate[k] for k in ['High', 'HSpeed', 'HDir', 'VSpeed']]
                if all(len(c) == 450 for c in columns) and any(
                        all(math.isfinite(v) for v in row) for row in zip(*columns)):
                    profile = path
                    break
            except (OSError, ValueError, KeyError):
                pass
        if profile:
            break
        time.sleep(.5)
    check('loaded image automatically saves a complete four-beam profile without networking', profile is not None)
    live = json.loads(call([*iso, 'inspect', offline_name]))[0]
    check('offline run has no external network or host display/GPU',
          live['HostConfig']['NetworkMode'] == 'none'
          and not live['HostConfig']['Devices']
          and all(m['Destination'] not in ['/tmp/.X11-unix', '/dev/dri'] for m in live['Mounts']))
    page = call([*iso, 'exec', offline_name, 'python3', '-c',
                 "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:6080/').read().decode())"])
    check('offline Web assets retain maximum quality and minimum compression', 'quality=9&amp;compression=0' in page)
    check('offline acquisition files belong to the invoking user', profile.stat().st_uid == os.getuid())
    call([*iso, 'stop', '--timeout', '15', offline_name])
    stopped = json.loads(call([*iso, 'inspect', offline_name]))[0]['State']
    logs = call([*iso, 'logs', offline_name])
    (out / 'offline-container.log').write_text(logs)
    check('offline container stops normally through application cancellation',
          stopped['ExitCode'] == 0 and not stopped['OOMKilled'] and '任务已取消，退出事件循环' in logs)
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    env = os.environ | {'WEB_BIND': '127.0.0.1', 'WEB_PORT': str(port),
                        'CONTAINER_NAME': script_name, 'WEB_STATE_DIR': str(out / 'script-state')}
    started = call(['bash', str(bundle / 'start.sh')], env=env, cwd='/tmp')
    (out / 'start-script.log').write_text(started)
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/vnc.html', timeout=2) as response:
                ready = b'noVNC' in response.read()
            if ready:
                break
        except OSError:
            pass
        time.sleep(.2)
    else:
        ready = False
    check('bundled start script serves noVNC from an arbitrary working directory', ready)
    processes = call([*host, 'top', script_name, '-eo', 'pid,args'])
    check('bundled start script keeps the default ring task', '--cycleAxis 60 0 90 180 270' in processes)
    current_config = out / 'script-state/config/simulation.json'
    check('first start seeds the provided default configuration',
          current_config.read_bytes() == (bundle / 'config/simulation.example.json').read_bytes())
    call([*host, 'stop', '--timeout', '15', script_name])
    # A distinguishable but valid JSON edit detects accidental replacement.
    retained = current_config.read_bytes() + b'\n'
    current_config.write_bytes(retained)
    call([*host, 'rm', script_name])
    call(['bash', str(bundle / 'start.sh')], env=env, cwd='/tmp')
    check('recreating the package container preserves existing configuration', current_config.read_bytes() == retained)
    call([*host, 'stop', '--timeout', '15', script_name])
except Exception as error:
    (out / 'delivery-results.json').write_text(json.dumps({
        'checks': checks, 'failures': max(1, sum(not c['passed'] for c in checks)),
        'error': str(error),
    }, indent=2))
    raise
finally:
    subprocess.run([*host, 'rm', '-f', script_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([*iso, 'rm', '-f', offline_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if daemon.poll() is None and pidfile.exists():
        subprocess.run(['sudo', '-n', 'kill', '-TERM', pidfile.read_text().strip()], check=True)
        daemon.wait(timeout=30)
    daemon_log.close()
    # Only delete this test's temporary store/runtime after its daemon has stopped.
    directory = out / 'daemon-data'
    if directory.exists() and directory.resolve().parent == out:
        subprocess.run(['sudo', '-n', 'rm', '-rf', '--', str(directory)], check=True)
    if runtime.resolve().parent == Path(tempfile.gettempdir()) and runtime.name.startswith('lidar-offline-'):
        subprocess.run(['sudo', '-n', 'rm', '-rf', '--', str(runtime)], check=True)
print('Offline package validation complete.', flush=True)
