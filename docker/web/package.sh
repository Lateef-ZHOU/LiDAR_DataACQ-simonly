#!/usr/bin/env bash
# Export an existing verified Web image and assemble a self-contained Linux delivery.
set -euo pipefail
umask 022
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
image=lidar-simonly-web:1.2.1
name=LiDAR-simonly-1.2.1-linux-amd64-web
out="${1:-$root/dist}"
mkdir -p "$out"
out="$(realpath "$out")"
archive="$out/$name.tar.gz"
[[ ! -e "$archive" && ! -e "$archive.sha256" ]] || {
    echo "交付包已存在，不覆盖：$archive" >&2; exit 1;
}
docker_cmd=(docker)
if ! docker info >/dev/null 2>&1; then docker_cmd=(sudo docker); fi
[[ "$("${docker_cmd[@]}" image inspect "$image" --format '{{.Os}}/{{.Architecture}}')" == linux/amd64 ]] || {
    echo '需要已构建的 linux/amd64 Web 镜像。' >&2; exit 1;
}
image_id="$("${docker_cmd[@]}" image inspect "$image" --format '{{.Id}}')"
app_version="$("${docker_cmd[@]}" run --rm --pull=never "$image" --version)"
stage="$(mktemp -d "$out/.web-package.XXXXXX")"
trap 'rm -rf -- "$stage"' EXIT
bundle="$stage/$name"
mkdir -p "$bundle/config" "$bundle/docker/web" "$bundle/licenses"
cp "$root/docker/web/delivery/README.md" "$root/docker/web/delivery/"*.sh "$bundle/"
cp "$root/docker/web/run.sh" "$bundle/docker/web/"
cp "$root/config/simulation.example.json" "$bundle/config/"
cp "$root/LICENSE" "$root/THIRD_PARTY_NOTICES.md" "$bundle/"
chmod 755 "$bundle/"*.sh "$bundle/docker/web/run.sh"
for license in GPL-3 LGPL-3; do
    "${docker_cmd[@]}" run --rm --pull=never --entrypoint cat "$image" \
        "/usr/share/common-licenses/$license" > "$bundle/licenses/$license.txt"
done
printf 'Application: %s\nImage: %s\nExported image ID: %s\nPlatform: linux/amd64\nDefault task: --cycleAxis 60 0 90 180 270 --accumulate 10 --settle 2\nBrowser: no VNC password; quality=9, compression=0\nBuilt at (UTC): %s\n' \
    "$app_version" "$image" "$image_id" "$(date -u +%FT%TZ)" > "$bundle/VERSION.txt"
echo '正在导出完整 Web 镜像...'
"${docker_cmd[@]}" image save "$image" > "$bundle/lidar-simonly-web-1.2.1.tar"
(
    cd "$bundle"
    find . -type f ! -name SHA256SUMS -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > SHA256SUMS
)
echo '正在压缩离线交付包...'
tar -C "$stage" -czf "$stage/bundle.tar.gz" "$name"
mv -- "$stage/bundle.tar.gz" "$archive"
(
    cd "$out"
    sha256sum "$name.tar.gz" > "$name.tar.gz.sha256"
)
cp "$root/docker/web/delivery/README.md" "$out/$name-README.md"
printf '交付包：%s\n校验文件：%s.sha256\n' "$archive" "$archive"
