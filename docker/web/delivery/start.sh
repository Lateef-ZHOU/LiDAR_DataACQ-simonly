#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
export IMAGE="${IMAGE:-lidar-simonly-web:1.2.1}"
if ! bash ./docker.sh image inspect "$IMAGE" >/dev/null 2>&1; then
    echo '本机未找到 Web 镜像，请先运行 bash ./import.sh。' >&2
    exit 1
fi
export WEB_STATE_DIR="${WEB_STATE_DIR:-$PWD/web-state}"
exec bash ./docker/web/run.sh "$@"
