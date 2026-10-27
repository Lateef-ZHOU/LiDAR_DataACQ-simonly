# 只供验证使用：独立、有认证的 X 服务，不进入交付镜像。
FROM ubuntu:24.04@sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac
RUN apt-get update && apt-get install -y --no-install-recommends xvfb xauth x11-utils \
    && rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["Xvfb"]
