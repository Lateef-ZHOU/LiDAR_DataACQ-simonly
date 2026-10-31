#!/usr/bin/env bash
# Run as the ordinary Linux user who should own the configuration and output files.
set -euo pipefail
umask 077
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
image="${IMAGE:-lidar-simonly-web:1.2.1}"
name="${CONTAINER_NAME:-lidar-sim-web}"
state="${WEB_STATE_DIR:-$PWD/web-state}"
bind="${WEB_BIND:-127.0.0.1}"
port="${WEB_PORT:-6080}"
docker_cmd=(docker)
if ! docker info >/dev/null 2>&1; then docker_cmd=(sudo docker); fi
[[ "$port" =~ ^[0-9]+$ ]] && ((port>=1 && port<=65535)) || { echo 'Invalid WEB_PORT.' >&2; exit 2; }
mkdir -p "$state/config" "$state/output"
state="$(realpath "$state")"
if [[ ! -f "$state/config/simulation.json" ]]; then
    cp "$root/config/simulation.example.json" "$state/config/simulation.json"
fi
"${docker_cmd[@]}" run -d --pull=never --name "$name" --restart on-failure:3 \
    --user "$(id -u):$(id -g)" --shm-size=256m \
    --security-opt=no-new-privileges --cap-drop=ALL \
    -p "$bind:$port:6080" -e "WEB_RESOLUTION=${WEB_RESOLUTION:-1600x900}" \
    -v "$state/config:/config" -v "$state/output:/data" \
    "$image" --config /config/simulation.json "$@"
printf 'Browser: http://%s:%s/\nOutput: %s/output\n' "$bind" "$port" "$state"
