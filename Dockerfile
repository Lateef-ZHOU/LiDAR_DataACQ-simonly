# syntax=docker/dockerfile:1
# Ubuntu 是镜像内的用户空间，不要求宿主使用同一发行版。
FROM ubuntu:24.04@sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac AS system-runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates fonts-noto-cjk libdbus-1-3 libegl1 libfontconfig1 \
    libgl1 libopengl0 libgomp1 libglib2.0-0t64 libgssapi-krb5-2 \
    libxkbcommon0 libxcb-cursor0 libssl3t64 \
    && rm -rf /var/lib/apt/lists/*
ENV LANG=C.UTF-8 \
    QT_QPA_PLATFORM=offscreen \
    LD_LIBRARY_PATH=/opt/Qt/lib

# Qt 官方 Linux x86_64 归档固定版本及 SHA256，宿主 Qt 不参与构建。
FROM system-runtime AS qt-sdk
RUN test "$(dpkg --print-architecture)" = amd64 \
    && apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake ninja-build curl p7zip-full libgl1-mesa-dev libxkbcommon-dev \
    && rm -rf /var/lib/apt/lists/*
COPY docker/ /tmp/qt-fetch/
RUN sh /tmp/qt-fetch/fetch-qt.sh \
    && test "$(/opt/Qt/bin/qmake6 -query QT_VERSION)" = 6.11.2

FROM qt-sdk AS build
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY CMakeLists.txt ./
COPY cmake/ cmake/
COPY src/ src/
COPY include/ include/
COPY config/ config/
ARG BUILD_JOBS=4
RUN cmake -S . -B /build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=/opt/Qt -DBUILD_TESTING=OFF \
    && cmake --build /build --parallel "${BUILD_JOBS}"
# 只整理 Qt 自身的共享库、QML 和所需插件；glibc 等由 system-runtime 提供。
RUN mkdir -p /runtime/Qt/lib /runtime/Qt/plugins/platforms /runtime/lidar/bin \
    && cp -a /opt/Qt/lib/*.so* /runtime/Qt/lib/ \
    && cp -a /opt/Qt/qml /runtime/Qt/ \
    && cp -a /opt/Qt/plugins/imageformats /opt/Qt/plugins/iconengines /runtime/Qt/plugins/ \
    && cp -a /opt/Qt/plugins/platforms/libqoffscreen.so /runtime/Qt/plugins/platforms/ \
    && cp /build/LiDAR_DataACQ /runtime/lidar/bin/ \
    && printf '[Paths]\nPrefix=/opt/Qt\n' > /runtime/lidar/bin/qt.conf \
    && cp /tmp/qt-fetch/qt-6.11.2.lock /runtime/Qt/

FROM system-runtime AS runtime
COPY --from=build /runtime/Qt/ /opt/Qt/
COPY --from=build /runtime/lidar/ /opt/lidar/
COPY config/simulation.example.json /opt/lidar/share/simulation.example.json
COPY LICENSE THIRD_PARTY_NOTICES.md README.md /opt/lidar/share/
RUN mkdir /data && chown 1000:1000 /data \
    && /opt/lidar/bin/LiDAR_DataACQ --version
WORKDIR /data
# 挂载宿主目录时通过 --user 指定目录所有者的 UID/GID。
USER 1000:1000
STOPSIGNAL SIGTERM
ENTRYPOINT ["/opt/lidar/bin/LiDAR_DataACQ"]
CMD ["--help"]

FROM runtime AS final
ARG VCS_REF=unknown
LABEL org.opencontainers.image.title="LiDAR DataACQ Simulation" \
    org.opencontainers.image.version="1.2.0-simonly" \
    org.opencontainers.image.revision="${VCS_REF}" \
    io.lidar.qt.version="6.11.2"
