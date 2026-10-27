#!/bin/sh
set -eu
mkdir -p /opt/Qt
while read -r checksum url; do
    archive="/tmp/qt-fetch/archives/${url##*/}"
    if [ ! -f "$archive" ]; then
        mkdir -p /tmp/qt-fetch/archives
        curl --fail --silent --show-error --location --connect-timeout 30 --max-time 900 --retry 3 --output "$archive" "$url"
    fi
    printf '%s  %s\n' "$checksum" "$archive" | sha256sum --check --strict
    7z x -y -o/opt/Qt "$archive" >/dev/null
    rm "$archive"
done < /tmp/qt-fetch/qt-6.11.2.lock
# ICU 归档位于包根，统一放到本镜像的 Qt 库目录，保留相对符号链接。
mv /opt/Qt/libicu*.so* /opt/Qt/lib/
printf '[Paths]\nPrefix=..\n' > /opt/Qt/bin/qt.conf
