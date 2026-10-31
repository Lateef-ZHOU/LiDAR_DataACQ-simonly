"""Read-only evidence for manual browser disconnect/reconnect checks."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
from datetime import datetime, timezone

p = argparse.ArgumentParser()
p.add_argument('--container', default='lidar-sim-web')
p.add_argument('--state', required=True)
p.add_argument('--docker', default='docker')
p.add_argument('--out', required=True)
a = p.parse_args()
docker = shlex.split(a.docker)
state = Path(a.state).resolve()


def call(*args):
    return subprocess.check_output([*docker, *args], text=True, timeout=15)


info = json.loads(call('inspect', a.container))[0]
processes = call('top', a.container, '-eo', 'pid,comm').splitlines()[1:]
application_pids = [int(line.split()[0]) for line in processes if line.split()[-1] == 'LiDAR_DataACQ']
spectra = [f for f in (state / 'output').glob('Rawspec/**/*.bin') if f.stat().st_size == 720000]
report = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'container': info['Id'],
    'started_at': info['State']['StartedAt'],
    'restart_count': info['RestartCount'],
    'application_pids': application_pids,
    'complete_spectra': len(spectra),
    'radial_files': len(list((state / 'output').glob('Radialwind/**/*.txt'))),
    'profile_files': len(list((state / 'output').glob('Windprofile/*.txt'))),
    'newest_spectrum_mtime': max((f.stat().st_mtime for f in spectra), default=None),
    'configuration_sha256': hashlib.sha256((state / 'config/simulation.json').read_bytes()).hexdigest(),
}
Path(a.out).write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
