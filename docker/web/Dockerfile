# Web delivery extends the existing desktop image; the application and Qt stay unchanged.
ARG BASE_IMAGE=lidar-simonly:1.2.1
FROM ${BASE_IMAGE}
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb xauth x11-utils x11vnc novnc websockify openbox tini \
    && rm -rf /var/lib/apt/lists/*
COPY docker/web/entrypoint.sh docker/web/openbox.xml /opt/lidar/web/
COPY docker/web/index.html /usr/share/novnc/index.html
RUN chmod 755 /opt/lidar/web/entrypoint.sh
ENV WEB_RESOLUTION=1600x900
USER 1000:1000
WORKDIR /data
EXPOSE 6080
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:6080/vnc.html', timeout=3).close()"
STOPSIGNAL SIGTERM
ENTRYPOINT ["/usr/bin/tini", "--", "/opt/lidar/web/entrypoint.sh"]
CMD []
LABEL org.opencontainers.image.title="LiDAR DataACQ Simulation Web" \
    io.lidar.web.transport="Xvfb+x11vnc+noVNC"
