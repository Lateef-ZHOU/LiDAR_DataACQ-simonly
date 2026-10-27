#!/usr/bin/env bash
# 保持调用者的桌面身份，只在 Docker 命令需要时使用 sudo。
set -euo pipefail
if docker info >/dev/null 2>&1; then
    exec docker "$@"
else
    exec sudo docker "$@"
fi
