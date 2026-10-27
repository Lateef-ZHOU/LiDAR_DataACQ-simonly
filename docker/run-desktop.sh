#!/usr/bin/env bash
# 在当前 Linux 桌面会话运行；仅传入当前 DISPLAY 的认证，不修改显示服务的访问规则。
set -euo pipefail
docker_bin="${DOCKER:-docker}"
image="${IMAGE:-lidar-simonly:1.2.1}"
name="${CONTAINER_NAME:-lidar-sim}"
config="${CONFIG_FILE:-$PWD/simulation.json}"
output="${OUTPUT_DIR:-$PWD/output}"
if [[ -z "${DISPLAY:-}" || ! -d /tmp/.X11-unix ]]; then
    echo "需要本机 X11 桌面，或启用了 XWayland 的 Wayland 桌面；请在该桌面的终端运行。" >&2
    exit 1
fi
if [[ "$DISPLAY" != :* && "$DISPLAY" != unix:* ]]; then
    echo "此入口使用本机显示 socket，不接受 SSH/TCP DISPLAY。" >&2
    exit 1
fi
command -v "$docker_bin" >/dev/null
command -v xauth >/dev/null || { echo "请先安装 xauth。" >&2; exit 1; }
[[ -f "$config" ]] || { echo "JSON 配置不存在：$config" >&2; exit 1; }
config="$(realpath "$config")"
mkdir -p "$output"
output="$(realpath "$output")"
auth="$(mktemp)"
trap 'rm -f -- "$auth"' EXIT
chmod 600 "$auth"
cookie="$(xauth nlist "$DISPLAY")"
[[ -n "$cookie" ]] || { echo "未找到当前 DISPLAY 的认证；请检查 XAUTHORITY。" >&2; exit 1; }
# 容器与宿主主机名不同；只将本次显示连接的记录改为 FamilyWild。
printf '%s\n' "$cookie" | sed 's/^..../ffff/' | xauth -f "$auth" nmerge -
"$docker_bin" run -d --name "$name" --user "$(id -u):$(id -g)" \
    -e DISPLAY -e QT_QPA_PLATFORM=xcb -e QT_XCB_NO_MITSHM=1 \
    -e XAUTHORITY=/tmp/lidar-display.auth \
    -v /tmp/.X11-unix:/tmp/.X11-unix:ro -v "$auth:/tmp/lidar-display.auth:ro" \
    -v "$config:/config/simulation.json:ro" -v "$output:/data" \
    "$image" --config /config/simulation.json "$@"
# 绑定已经建立，容器仍可读取认证文件。保留停止后的容器日志；重启请删除旧容器再执行本脚本。
