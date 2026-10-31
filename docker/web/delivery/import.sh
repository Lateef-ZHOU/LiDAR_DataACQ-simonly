#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
sha256sum -c SHA256SUMS
bash ./docker.sh load --input lidar-simonly-web-1.2.1.tar
bash ./docker.sh image inspect lidar-simonly-web:1.2.1 --format 'Imported: {{.Os}}/{{.Architecture}} {{.Id}}'
printf '\n镜像导入完成。启动：WEB_BIND=服务器内网IP bash ./start.sh\n'
