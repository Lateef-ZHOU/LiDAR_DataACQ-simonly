#!/usr/bin/env bash
set -euo pipefail
umask 077

# These non-interactive commands retain the original image's CLI behavior.
for arg in "$@"; do
    case "$arg" in
        --headless|--help|-h|--version) exec /opt/lidar/bin/LiDAR_DataACQ "$@" ;;
    esac
done

# The Web service always starts a task. Explicit task/time arguments keep their values.
has_task=false
for arg in "$@"; do
    case "$arg" in
        --fixedAxis|--cycleAxis|--snakeAxis) has_task=true ;;
    esac
done
if [[ "$has_task" == false ]]; then
    set -- "$@" --cycleAxis 60 0 90 180 270
fi

resolution="${WEB_RESOLUTION:-1600x900}"
[[ "$resolution" =~ ^[1-9][0-9]{2,3}x[1-9][0-9]{2,3}$ ]] || {
    echo 'WEB_RESOLUTION must be WIDTHxHEIGHT, for example 1600x900.' >&2; exit 2;
}
runtime="$(mktemp -d /tmp/lidar-web.XXXXXX)"
app_pid=''
service_pids=()
cleanup() {
    trap - EXIT TERM INT
    # Keep X alive until the original application's SIGTERM cancellation has finished.
    if [[ -n "$app_pid" ]] && kill -0 "$app_pid" 2>/dev/null; then
        kill -TERM "$app_pid" 2>/dev/null || true
        wait "$app_pid" || true
    fi
    for ((i=${#service_pids[@]}-1; i>=0; --i)); do
        kill -TERM "${service_pids[i]}" 2>/dev/null || true
    done
    for pid in "${service_pids[@]}"; do wait "$pid" 2>/dev/null || true; done
    rm -rf -- "$runtime"
}
trap cleanup EXIT
trap 'exit 0' TERM INT

export DISPLAY=:99 QT_QPA_PLATFORM=xcb QT_XCB_NO_MITSHM=1
export QSG_RHI_BACKEND=opengl LIBGL_ALWAYS_SOFTWARE=1
export XAUTHORITY="$runtime/Xauthority" XDG_RUNTIME_DIR="$runtime/xdg"
export XDG_CONFIG_HOME="$runtime/config" XDG_CACHE_HOME="$runtime/cache"
mkdir -p "$XDG_RUNTIME_DIR" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME"
touch "$XAUTHORITY"
cookie="$(od -An -N16 -tx1 /dev/urandom | tr -d ' \n')"
xauth -f "$XAUTHORITY" add "$DISPLAY" . "$cookie"
unset cookie

Xvfb "$DISPLAY" -screen 0 "${resolution}x24" -nolisten tcp -auth "$XAUTHORITY" &
service_pids+=("$!")
ready=false
for ((i=0; i<100; ++i)); do
    if xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then ready=true; break; fi
    kill -0 "${service_pids[0]}" 2>/dev/null || break
    sleep 0.1
done
[[ "$ready" == true ]] || { echo 'Virtual display did not become ready.' >&2; exit 1; }

openbox --sm-disable --config-file /opt/lidar/web/openbox.xml &
service_pids+=("$!")
# Browser access is password-free on the configured host interface; X stays authenticated.
x11vnc -display "$DISPLAY" -auth "$XAUTHORITY" -nopw \
    -rfbport 5900 -localhost -forever -shared -nolookup -noxdamage -wait 20 -defer 5 &
service_pids+=("$!")
websockify --web=/usr/share/novnc 6080 127.0.0.1:5900 &
service_pids+=("$!")
/opt/lidar/bin/LiDAR_DataACQ "$@" &
app_pid=$!
echo "LiDAR Web ready: display=$DISPLAY, resolution=$resolution, application_pid=$app_pid"

# A disconnected browser is not a service exit. A closed app ends this container.
result=0
wait -n -p ended "$app_pid" "${service_pids[@]}" || result=$?
if [[ "$ended" != "$app_pid" ]]; then
    echo "Display/web service $ended exited unexpectedly (status $result)." >&2
    [[ "$result" != 0 ]] || result=1
fi
exit "$result"
