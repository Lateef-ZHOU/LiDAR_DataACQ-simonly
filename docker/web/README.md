# 浏览器版 Docker

Web 镜像在 `lidar-simonly:1.2.1` 桌面镜像上叠加 Xvfb、x11vnc、noVNC/websockify、Openbox 和 tini。原程序、Qt、图表和三个任务实现直接复用。原 Dockerfile、桌面启动入口及历史离线包继续保留。

需要 x86_64 Linux、Docker 和浏览器。宿主不需要桌面会话、X11/Wayland 服务、显示器或 GPU；所有显示组件在容器内运行。使用 Mesa 软件 OpenGL，不设置 `QT_QUICK_BACKEND=software`，后者不支持现有曲面的 QQuickRhiItem。

## 构建

在本仓根目录执行。已有桌面镜像时跳过第一条：

```sh
docker build --platform linux/amd64 -t lidar-simonly:1.2.1 .
docker build --platform linux/amd64 -f docker/web/Dockerfile \
  --build-arg BASE_IMAGE=lidar-simonly:1.2.1 -t lidar-simonly-web:1.2.1 .
```

无 Docker 权限时在构建命令前加 `sudo`。不替换桌面镜像标签。`BASE_IMAGE` 也可指定已核对的本地镜像 ID。

## 独立离线交付

在有当前 Web 镜像的 Linux 主机执行 `bash docker/web/package.sh`，或传入输出目录。脚本导出完整镜像及基础层，生成 `LiDAR-simonly-1.2.1-linux-amd64-web.tar.gz`、同名 `.sha256` 和独立使用说明；已有同名压缩包不会被覆盖。原桌面交付包保持不变。

包内提供 `import.sh`、`start.sh`、配置模板、校验和与许可材料。导入和启动无需联网，也不依赖旧桌面镜像；启动只使用本机已有镜像，不自动拉取。甲方部署步骤见 [离线交付说明](delivery/README.md)。

## 启动与访问

以需要持有输出文件的普通用户运行，脚本会按需调用 sudo：

```sh
# 替换为服务器实际的内网 IP。
WEB_BIND=192.168.128.254 bash docker/web/run.sh
```

浏览器打开 `http://服务器内网IP:6080/` 即可进入，无需 VNC 密码。

容器启动后，在虚拟设备就绪时自动开始环形四轴采集，无需打开浏览器或点击开始。未传任务参数时采用世界高度角 60°，按方位角 0°、90°、180°、270° 顺序循环，每束累积 10 秒、停稳 2 秒。每束保存谱和径向风，完成四束后反演并保存风廓线；首份风廓线需等完整一轮运动、停稳和采集结束。

未指定 `WEB_BIND` 时只绑定服务器的 `127.0.0.1`。可从本地通过 SSH 转发访问：

```sh
ssh -N -L 6080:127.0.0.1:6080 用户@服务器
```

然后打开 `http://127.0.0.1:6080/`。内网直接访问使用 HTTP，不设 VNC 密码，能访问该地址的人均可查看和操作；跨不可信网络使用 SSH 转发，或由部署环境提供 HTTPS 和访问控制。仅发布 6080，5900 只监听容器内部回环地址，虚拟 X 服务仍使用独立 Xauthority 并禁用 TCP。

启动脚本不再生成、读取或挂载 VNC 密码文件，已有配置与输出继续保留。一个容器对应一个仿真程序，多个浏览器连接同一界面并共享操作。

Web 入口始终以自动任务方式启动，设备/风场参数从 `web-state/config/simulation.json` 读取。按原应用约定，自动任务模式下界面修改不写回 JSON；需要持久修改时编辑该文件再重启容器。任务角度和累积/停稳参数不写入 JSON。原桌面镜像的无任务交互配置模式保持不变。

可通过原命令行参数选择任务和覆盖默认时间：

```sh
WEB_BIND=192.168.128.254 bash docker/web/run.sh \
  --cycleAxis 60 0 90 180 270 --accumulate 2 --settle 2
```

显式参数仍可覆盖默认任务：蛇形使用 `--snakeAxis 60 0 90 180 270`；单轴使用 `--fixedAxis 60 0`，仅产生谱和径向风，不生成四束风廓线。带任务参数时配置仍按原应用约定只读，界面修改不持久化；不加 `--headless`。Web 镜像仍可执行原 `--headless`、`--help` 和 `--version`，这些入口直接运行原程序，不启动显示或网络服务。

## 局域网画质

根地址自动携带 noVNC `quality=9&compression=0`：JPEG 画质使用最高等级 9，压缩等级使用 0，优先画质和降低压缩开销。x11vnc 屏幕轮询为 20 ms、发送延迟为 5 ms；实际帧率受画面变化、渲染和网络影响。VNC 是按变化区域传输，没有固定 Mbps 码率，静止画面流量较低属于正常行为。

升级后从根地址 `/` 重新打开，以覆盖浏览器之前缓存的画质设置。noVNC 设置面板仍允许调整画质与压缩。虚拟分辨率继续由 `WEB_RESOLUTION` 控制，默认 1600×900。

| 环境变量 | 默认值 | 含义 |
|---|---|---|
| `IMAGE` | `lidar-simonly-web:1.2.1` | Web 镜像 |
| `CONTAINER_NAME` | `lidar-sim-web` | 容器名 |
| `WEB_STATE_DIR` | 当前目录下 `web-state` | 配置和输出的独立目录 |
| `WEB_BIND` | `127.0.0.1` | 发布端口的宿主地址 |
| `WEB_PORT` | `6080` | 浏览器端口 |
| `WEB_RESOLUTION` | `1600x900` | 虚拟屏幕尺寸，浏览器按比例缩放 |

输出始终写入 `web-state/output/` 下的 `Rawspec`、`Radialwind` 和 `Windprofile`，目录整体挂载到容器 `/data`。配置挂载整个可写目录，兼容 QSaveFile 的临时文件和原子替换。浏览器文件选择不会把服务器路径变成本地路径，当前 Web 入口不附加文件下载服务。

## 断线、停止与重启

关闭浏览器标签、点击 noVNC 断开或网络断开，都只切断远程连接，采集和落盘继续；重新连接返回同一个程序和任务。noVNC 页面启用自动重连，无需输入密码。Web 窗口铺满虚拟屏幕，隐藏整个系统标题栏及最小化、最大化、关闭按钮，避免误操作退出；关闭服务使用下面的 Docker 命令。任务页停止按钮只停止任务，窗口保持，可再次开始。

```sh
sudo docker logs -f lidar-sim-web
sudo docker stop --time 15 lidar-sim-web
sudo docker start lidar-sim-web
```

容器停止时 tini 把信号交给入口；入口先向应用发 SIGTERM，等待原主线程取消并退出，再停止 websockify、VNC、窗口管理器和 Xvfb。不增加保存排空，停止瞬间最后一帧仍沿用原边界。

应用正常退出时容器随之结束；异常退出最多自动重启三次，正常关闭不自动重新打开。`docker start` 创建新应用会话，并按启动参数自动重新采集，配置和已保存文件保留，任务不会从中断位置恢复。修改端口或分辨率等容器设置时，先停止并删除这个容器，再重新运行启动脚本；宿主状态目录不删除。

## 验证

`tests/web/verify.py` 验证 Web 镜像、三任务真实 X11/OpenGL 出图与落盘、无人连接时持续采集、信号转交及长累积取消；测试只删除自己创建的容器，保留结果目录。浏览器鼠标/键盘操作、断线重连另做实际浏览器验证，不能以 HTTP 返回成功代替。当前实测记录见仓库 `VALIDATION.md`。
