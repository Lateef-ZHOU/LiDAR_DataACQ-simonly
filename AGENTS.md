# LiDAR_DataACQ-simonly

2026-10-31 发布用户定：将此前 Web Docker 源码、部署/离线打包脚本和说明一并提交并推送 master。保留已有业务程序、桌面/Web 镜像及 dist 交付文件，不重建或重新部署容器。历史“未提交/未推送”描述的是当时阶段；验证记录见 VALIDATION.md。

2026-10-29 现场清理用户定：ArchHFNL 仅保留最新版 Web 镜像 `lidar-simonly-web:1.2.1`（28ff9d6）及运行容器 `lidar-sim-web`（bedb4f66）。6 个已停止的旧容器、14 个旧版/测试/基础镜像已删除；当前容器未重启，配置、采集数据和原桌面/Web 离线交付文件保留。下方关于保留回退容器及旧镜像的记录是清理前历史。后续如需桌面构建基底，可从原桌面离线包重新导入。

2026-10-29 独立 Web 离线交付：新增 `docker/web/package.sh` 和 `docker/web/delivery`，在已验证的 Web 镜像上导出完整基础层，不重建业务程序。新包为 `dist/LiDAR-simonly-1.2.1-linux-amd64-web.tar.gz`，另有 `.sha256` 和独立使用说明；原桌面包及其说明保留。目标机预装 Docker 后无需联网，启动脚本只使用本地镜像；默认环形、免密码、高画质和隐藏窗口按钮不变。空镜像库导入、禁用容器网络后的完整风廓线、包内启动脚本和配置保留专项 17/17。验证用独立 dockerd 必须通过 `unshare --net` 隔离网络，单独数据目录和 `--bridge=none` 不足以隔离宿主桥接。实际记录见 VALIDATION.md；未提交或推送。

2026-10-29 默认任务补充用户定：Web Docker 默认环形四轴，入口补入 `--cycleAxis 60 0 90 180 270`，每束累积 10 秒、停稳 2 秒。启动无需浏览器或手动开始，完整四束后生成风廓线；单轴仅在显式指定时运行。本项取代先前默认单轴行为。免密码、高画质、隐藏窗口按钮和原交付包保持。

2026-10-29 密码补充用户定：Web Docker 取消 VNC 密码，浏览器直达。启动入口和脚本不再生成、读取或挂载密码；仅发布配置的宿主地址和 6080，VNC 内部回环监听与 Xauthority 保持。可访问网页地址的人可直接操作同一会话；默认绑定仍为 127.0.0.1，ArchHFNL 使用既有内网地址。

2026-10-29 窗口控制补充用户定：Web Docker 隐藏系统标题栏及最小化、最大化、关闭按钮，窗口保持铺满虚拟屏幕，关闭留给 Docker。只调整 Openbox 配置，不改业务窗口实现；原桌面包保留原窗口行为。

2026-10-29 用户定：Web Docker 启动即自动采集，显式任务/时间参数优先，现行默认任务见上条。局域网默认 noVNC 画质 9、压缩 0，x11vnc 轮询 20 ms、发送延迟 5 ms；VNC 按画面变化传输，不承诺固定码率或帧率。无桌面 ArchHFNL 的 `lidar-sim-web` 已部署，浏览器无需连接即可采集，容器重启后自动启动任务；当前保持采集。自动任务模式沿用原应用约定：读取 JSON，界面修改不写回，持久修改需编辑配置文件再重启。

Web 交付在原 `lidar-simonly:1.2.1` 上叠加 Xvfb、x11vnc、noVNC/websockify、Openbox 和 tini；入口见 `docker/web/README.md`。不修改业务 C++/QML、固定依赖或原桌面镜像/交付包。一个容器为一个共享会话，浏览器断开不停止任务；SIGTERM 先等待应用取消退出，再关显示。配置/输出使用独立目录；验证证据及部署位置见 VALIDATION.md。仅本地改动，不推送。

使用中文沟通。开始先检查 Git 分支、未提交修改和固定依赖；技术入口见 README.md、cmake/Dependencies.cmake 和 tests/README.md。

本仓是装配应用，不 fork 或复制官邸 C++。设备、三个独立任务的功能在各自仓库维护，全功能和 simonly QML 共用后端。修改上游应先验证并发布完整提交，再更新固定引用。主程序 LiDAR_DataACQ 和旧 sim-ui/Docker 交付不随本仓修改。

simonly 无单卡测试、设备选择、保存开关或目录选择，任务总是保存到当前工作目录；保留所有风场、累积窗口和 QML 历史源。命令行任务默认打开 UI，显式 --headless 才隐藏；关窗、Ctrl+C/SIGTERM 先调用任务 stop()，沿现有主线程取消链退出，不新增保存排空。构造后先配置与场景快照，再连接和启动。

2026-10-27 任务创建契约：三个 simonly 官邸必须在创建时接收 azimuths/elevation/accum/settle，角度 alias 到唯一计划，时间由页面持有。自动启动与开始按钮统一调用无参 start()，停止调用无参 stop()；启动编排不再补写参数。设备参数仍由 JSON 提供，任务参数不写入 JSON。桌面停止按钮只停任务，允许再次启动；关窗或系统信号才退出。Docker 使用本机 X11 / XWayland、当前显示授权和 Mesa OpenGL，JSON 与输出挂载保持；无桌面服务器使用 --headless。不将离屏测试写成桌面实测，平台和显示验证边界见 VALIDATION.md。

不使用 friend，不增加假想接口、状态或转发层。QT_NO_KEYWORDS；提交使用中文 type(scope): 标题。验证至少包括 Release 构建、CTest、QML lint；涉及配置/采样/取消时跑生产命令行与 Docker 专项，不能把静态检查写成运行验证。说明记录真实执行的平台和 Qt 版本。推送须有用户指示。

2026-10-27 桌面交付：部署说明和便捷入口在 docker/delivery，离线包放 dist。新默认 JSON 与镜像资源均为线性剪切 + 随机起伏（linearShear/gust），其余数值不变，不覆盖已有 JSON。交付脚本以普通桌面用户运行，Docker 按需使用 sudo；缺显示变量时仅从当前用户已登录的 systemd 桌面会话补齐。真实 GNOME/XWayland 已由用户确认显示。simonly 仍不推送。
