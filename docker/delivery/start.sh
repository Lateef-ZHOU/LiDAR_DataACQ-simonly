#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ "$EUID" == 0 ]]; then
    echo "请以登录桌面的普通用户执行 ./start.sh；脚本会按需为 Docker 使用 sudo。" >&2
    exit 1
fi
if [[ $# == 0 ]]; then
    echo "用法：./start.sh --fixedAxis 60 0 --accumulate 2 --settle 2" >&2
    exit 1
fi
# SSH/非图形终端可能未继承显示变量。仅从当前用户已登录的桌面会话补齐，不猜测显示号。
if [[ -z "${DISPLAY:-}" ]] && command -v systemctl >/dev/null; then
    while IFS='=' read -r key value; do
        case "$key" in
            DISPLAY) export DISPLAY="$value" ;;
            XAUTHORITY) export XAUTHORITY="$value" ;;
        esac
    done < <(systemctl --user show-environment 2>/dev/null || true)
fi
export DOCKER="$PWD/docker.sh"
export CONFIG_FILE="${CONFIG_FILE:-$PWD/simulation.json}"
export OUTPUT_DIR="${OUTPUT_DIR:-$PWD/output}"
export CONTAINER_NAME="${CONTAINER_NAME:-lidar-sim}"
exec bash ./run-desktop.sh "$@"
