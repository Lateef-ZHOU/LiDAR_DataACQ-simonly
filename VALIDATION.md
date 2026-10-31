# 验证记录

## 2026-10-31：提交并推送现有 Web Docker 源码

- 用户确认本次“推送所有修改”包含上一轮未提交的 Web Docker 源码、说明与测试。提交新增 docker/web、tests/web 及已有说明修改；六个 shell 入口在 Git 中保留可执行位，不修改应用 C++/QML、已有依赖、镜像或 dist 交付文件。
- 本次对实际待提交内容归档后，在 ArchHFNL 检查六个脚本的 Bash 语法、Python 编译和入口可执行权限，全部通过；本机 Python AST 与 Openbox XML 检查通过。既有 Web 58/58、生产 CLI 32/32、离线包 17/17 等实际运行证据保留如下，未将这些历史结果当成本次重跑。
- 本次不重建 Docker、不重启现有容器、不重新打包。源码检查归档为 build/web-publish-source.tar，Linux 检查目录为 ~/.cache/simonly-web-publish-20261031。

## 2026-10-29 仅保留最新版运行部署

按用户要求清理 ArchHFNL Docker。操作前共有 7 个容器，其中仅 `lidar-sim-web` 运行，其他 6 个均已停止；15 个镜像中仅保留当前 `lidar-simonly-web:1.2.1`。逐项核对容器与镜像完整 ID 后，删除 6 个旧容器和 14 个旧版、测试及基础镜像。旧容器的配置/采集数据均为宿主绑定目录，未删除这些文件；未清理卷、构建缓存或离线包。

北京时间 17:58:13 验证：容器列表和镜像列表各只剩一项；运行容器 ID 仍为 `bedb4f66b91141ce8723b100d844d29e3658b8ee66387c5654527fef6c2ba5cd`，镜像 ID 仍为 `sha256:28ff9d6e67ede41bc2fab9369ff93c787133e43d07b4c31053d75adaabcf352e`。容器 PID、StartedAt 与 RestartCount=0 不变，健康，HTTP 200，配置 SHA256 不变。原桌面和 Web 离线交付文件均保留。证据为部署目录 `evidence-cleanup-20261029/` 的清理前清单、删除日志和清理后核验；下方保留旧容器/镜像的描述均是历史状态。

## 2026-10-29 断电后恢复

用户询问断电是否中断上次交付。重新校验本地 Web 包和原桌面包，两者 SHA256 均与下方记录一致，说明及校验文件完整，原包级验证报告仍为 17/17。

ArchHFNL 于北京时间 17:39:30 重启；Docker 服务原本未设置开机启动，本次手动启动服务。原 Web 容器异常断电后保留 `/tmp/.X99-lock`，恢复时反复退出，原 Docker 日志还出现无法解码的零字节。保留原容器为 `lidar-sim-web-before-power-recovery-20261029`，使用同一镜像、配置与输出目录重建 `lidar-sim-web`，未删除历史数据或修改交付镜像。此为现场恢复，没有宣称旧容器已具备异常断电后的自动恢复能力。

新容器 ID `bedb4f66b91141ce8723b100d844d29e3658b8ee66387c5654527fef6c2ba5cd`，UTC `2026-10-29T09:44:51.524699816Z` 启动。17:45:53 核验健康、RestartCount=0，本地访问原地址 HTTP 200；新会话的 `Windprofile/SIM_20261029_094452_SimCard.txt` 已保存 450 层，450 层的高度、水平风速、风向和垂直风速均有限。配置 SHA256 保持 `a7461f2d4b653bd446a584998ad1bbe699509b4e1adbacedccffc115774880c0`。证据为部署目录 `evidence-power-recovery-20261029/restored.json`。未改开机启动策略、业务代码或离线包。

## 2026-10-29 后续：独立 Web 离线交付包

用户要求将现有 Web Docker 打成可直接发给甲方的独立离线包，并保留原交付包。本次仅增加镜像导出、交付脚本、部署说明及包级验证；使用已经验证的 Web 镜像，不重建或修改应用 C++/QML、依赖及原桌面入口。

- 交付文件：`dist/LiDAR-simonly-1.2.1-linux-amd64-web.tar.gz`，**359568626 字节**（约 343 MiB）；SHA256：`36c60581ed628a426fc823cb897e970ca47ce73a280246a8bc05a086416a28e3`。同目录提供 `.tar.gz.sha256` 和 `LiDAR-simonly-1.2.1-linux-amd64-web-README.md`，从 ArchHFNL 复制到 Windows 后校验一致。
- 包内包含完整 `lidar-simonly-web:1.2.1` 镜像及基础层、`import.sh`、`start.sh`、Docker 权限辅助入口、默认 JSON、中文说明、版本清单、校验和及许可文本。不带现场配置、采集数据、密码或宿主显示授权。目标机需预装 Docker；导入、启动不联网，也无需旧桌面镜像。启动使用 `--pull=never`。
- 导出的镜像 ID 保持 `sha256:28ff9d6e67ede41bc2fab9369ff93c787133e43d07b4c31053d75adaabcf352e`。默认环形 `--cycleAxis 60 0 90 180 270`、10 秒累积/2 秒停稳、免密码、高画质及隐藏窗口按钮均保持。普通用户启动，配置与采集数据保存在包目录下的 `web-state`，已有配置不覆盖。
- ArchHFNL / Docker 29.9.2 / Linux amd64：包级专项 **17/17**。从零镜像的独立 Docker 导入，核对完整 RootFS 与原镜像一致；导入后以 `--network=none`、无宿主显示/GPU 运行，未连接浏览器、未传任务参数即生成含 **450 层**和有效风数据的完整四束风廓线；文件属于 UID 1001，正常取消退出 0。另实际运行包内脚本，验证任意当前目录启动、noVNC HTTP 访问、缺镜像时明确提示先导入、默认环形参数和重建容器保留已修改的配置。
- 初次包级验证的第二个 dockerd 虽使用独立数据目录与 `--bridge=none`，仍删除宿主 docker0，导致浏览器连接中断。已按原子网、网关、MAC 和 veth 恢复桥接，没有重启主 Docker 或采集容器。测试改为 `unshare --net`，实测守护进程与宿主网络命名空间不同后重新完整通过；测试结束宿主桥接和网页仍正常。此事件不写成首次测试通过。
- Windows 本地浏览器重新访问原地址，免密码连接并显示持续更新的风羽图。打包前后主容器 ID、应用宿主 PID **78770**、StartedAt `2026-10-29T07:16:09.64325162Z` 和 RestartCount=0 不变；UTC **07:35:04 → 07:49:27**，完整谱/径向风 **909/909 → 966/966**，风廓线 **18 → 33**；配置 SHA256 仍为 `a7461f2d4b653bd446a584998ad1bbe699509b4e1adbacedccffc115774880c0`。服务保持健康和持续采集。
- Windows / MSVC / Qt 6.11.2：Release 构建、CTest **6/6** 通过，qmllint 退出 0，保留既有六项 required alias 告警。原桌面压缩包 SHA256 仍为 `226ee9d61e4bef0661e151ea64472eb43a2935afc20cdb26447face931b2e8e5`；原交付说明和脚本无改动。未提交或推送 Git。

证据：ArchHFNL `/home/lateef_zhou/lidar-simonly-web-20261029/offline-release/` 为交付文件；`evidence-offline/package-tests-final/` 保存通过的报告、导入日志及真实离线采集产物，初次失败保留在 `package-tests/`。本地 `build/web-validation-offline/` 保存构建、回归、打包、包级测试日志、前后会话快照及浏览器恢复截图。

## 2026-10-29 后续：默认环形四轴并持续生成风廓线

用户要求容器启动后直接进行环形采集，默认单轴不能提供所需的四束风廓线。本次将 Web 入口缺省任务改为 `--cycleAxis 60 0 90 180 270`；保留原默认每束累积 10 秒、停稳 2 秒及显式任务/时间参数覆盖。业务 C++/QML、依赖、原桌面镜像和离线包未改。

- 新 Web 镜像 ID：`sha256:28ff9d6e67ede41bc2fab9369ff93c787133e43d07b4c31053d75adaabcf352e`。旧镜像保留为 `lidar-simonly-web:1.2.1-before-default-cycle-20261029`，旧容器正常退出 0 后保留为 `lidar-sim-web-before-default-cycle-20261029`。新部署容器仍名为 `lidar-sim-web`，ID `9a3944d52ef0cc3dd0190b18b3ea9ad3d3e5a37299481d276669b53b6ff53005`。
- Windows / MSVC / Qt 6.11.2：Release 构建、CTest **6/6**，qmllint 退出 0，仍为原六项 required alias 告警。Web 专项 **58/58**：默认用例不传任务/时间参数、不连接浏览器，实际执行环形四束并生成完整风廓线；校验同长的高度/水平风速/风向/垂直风速数组、递增有限高度和有效风数据。显式单轴/环形/蛇形和取消回归保持通过。镜像内生产 CLI 黑盒 **32/32**，包括三任务、只读配置、系统信号取消。
- 初次现场部署自动开始环形后，浏览器连接期间日志出现“任务已停止”，任务进入空闲；该停点未计作持续采集通过，记录保存在 `initial-stopped-session.log` 和 `initial-session.json`。随后实际执行 `docker restart --timeout 15 lidar-sim-web`，重新验证完整产物；没有通过浏览器点击开始。
- 重启后的容器配置命令仅为 `--config /config/simulation.json`，实际应用进程参数由 Web 入口补入 `--cycleAxis 60 0 90 180 270`。StartedAt 为 UTC `2026-10-29T07:16:09.64325162Z`，应用宿主 PID **78770**，浏览器显示“环形四轴”运行中、四个方位及 10 秒/2 秒参数。
- 连续两轮风廓线已保存至 `state/output/Windprofile/SIM_20261029_071610_SimCard.txt` 与 `SIM_20261029_071710_SimCard.txt`，产物时间分别为 UTC **07:17:10**、**07:18:10**；各有 **450** 个递增高度层，450 层均存在有限的水平风速、风向和垂直风速，文件所有者 UID 1001。实际浏览器“风羽图”显示已生成的风廓线。此验证确认生成与持续更新，不代替算法精度评估。
- 最终快照完整谱/径向风 **843/843**、风廓线 **2**，容器健康，应用保持同一 PID 继续采集；配置 SHA256 仍为 `a7461f2d4b653bd446a584998ad1bbe699509b4e1adbacedccffc115774880c0`。免密码访问、画质 9/压缩 0、隐藏窗口标题栏和仅发布原内网地址均保留。未提交或推送 Git。

证据：ArchHFNL 部署目录 `evidence-default-cycle/`；本地 `build/web-validation-default-cycle/`。`profile-after-restart.json` 保存两份产物的层数、有效层数和采样值，`browser-cycle-task.jpg`、`browser-wind-profile.jpg` 为实际浏览器画面。下方早期默认单轴描述保留历史，以本节为当前启动行为。

## 2026-10-29 后续：取消 VNC 密码

用户要求优先删除 VNC 密码，可以删除则无需改成简单密码。本次取消 Web 入口的密码认证，浏览器直接连接。

- 删除入口的密码文件校验、转换及 `-rfbauth`，x11vnc 使用无密码连接；启动脚本不再生成、读取或挂载密码，镜像删除 `VNC_PASSWORD_FILE`。Xauthority、X 禁用 TCP、VNC 内部回环监听、宿主端口绑定均保持。ArchHFNL 仍只发布 `192.168.128.254:6080`；可访问该网页地址的人可直接操作共享会话。
- Web 镜像 ID：`sha256:969c9901b749fd1031024745a77a31a666d839d8e6fcfb8627ebc9f027c4519c`。旧镜像保留为 `lidar-simonly-web:1.2.1-before-no-password-20261029`，旧容器正常退出 0 后保留为 `lidar-sim-web-before-no-password-20261029`。旧密码文件仅为旧部署回退保留，新容器只有配置和输出两个挂载，不再使用密码文件。
- Windows / MSVC / Qt 6.11.2：Release 构建、CTest **6/6** 通过；qmllint 退出 0，保留原六项 required alias 告警。Web 专项 **57/57**，用实际 RFB 3.8 协商验证仅提供 None 类型（1），无需提交凭据即返回成功；同时确认无密码挂载/环境变量。三个任务出图与保存、自动启动、信号取消和 Docker 正常停止保持通过。
- 实际本地浏览器新开原地址，未输入任何凭据即进入；刷新后自动重连，同样无密码提示，页面切换可用，系统标题栏和三个窗口按钮仍隐藏，任务显示“采集中”。新容器 ID `460b42bb9578d4dee7e8e29277971e179f6feab413e8baed15445ceb562b909a`。刷新前后应用宿主 PID **70992**、StartedAt、RestartCount=0 不变，完整谱/径向风从 **494/494** 增至 **497/497**；配置 SHA256 仍为 `a7461f2d4b653bd446a584998ad1bbe699509b4e1adbacedccffc115774880c0`，画质 9/压缩 0 保持。
- 当前部署健康并保持自动采集，业务代码和原桌面交付包不变；未提交或推送 Git。

证据：ArchHFNL 部署目录 `evidence-no-password/`；本地 `build/web-validation-no-password/`，包含构建/回归报告、会话快照和浏览器截图 `browser-direct-access.jpg`。下方关于密码的描述保留各次历史部署状态，以本节为当前行为。

## 2026-10-29 后续：移除 Web 窗口控制按钮

用户要求移除远程桌面右上角的最小化、最大化、关闭按钮，关闭操作留在 Docker。

- 仅修改 `docker/web/openbox.xml`：普通窗口使用 `decor=no` 并保持最大化，隐藏整条系统标题栏。同时修正原 `focusNew` 元素闭合标签错误，XML 解析通过，实际容器日志未出现 Openbox/XML 配置错误。不改业务 C++/QML 或原桌面包。
- 更新 Web 镜像 ID：`sha256:bf19f2d0a834b49aa83d107010c87e03ca93ad528f06e3f1365701230b679d74`。旧镜像保留为 `lidar-simonly-web:1.2.1-before-window-controls-20261029`，原运行容器通过 Docker 正常停止（退出 0、无 OOM），保留为 `lidar-sim-web-before-window-controls-20261029`。新容器仍使用原配置、密码、输出目录和访问地址。
- Windows / MSVC / Qt 6.11.2：Release 构建、CTest **6/6** 通过，qmllint 退出 0，保留原有六项 required alias 告警。Web 专项 **56/56**，包含原二进制不变、自动采集、三个任务出图与保存、关窗事件/SIGINT/Docker 停止和长累积取消；取消路径沿用原应用。
- 本地浏览器实测新容器 `25ecf4cd8f39452efe2e66dcb10d45483d00e7e68ea085f52b69a22c189a2b56`：标题栏及三个按钮消失，应用铺满虚拟屏幕；点击三个旧按钮位置后仍可切换任务页，任务显示“采集中”。两次快照中应用宿主 PID **66128**、StartedAt、RestartCount=0 不变，完整谱/径向风从 **309/309** 增至 **312/312**。原配置 SHA256 不变，服务端仍协商画质 9、压缩 0。
- 当前部署健康并持续采集；关闭使用 `sudo docker stop --timeout 15 lidar-sim-web`，页面的任务停止按钮仍仅停止采集。未提交或推送 Git。

证据：ArchHFNL 部署目录的 `evidence-window-controls/`；本地 `build/web-validation-window-controls/`，含构建/回归日志、更新前后快照和真实浏览器截图 `browser-without-window-buttons.jpg`。

## 2026-10-29 后续：启动即采集与局域网高画质

用户补充要求：Web Docker 启动后就是采集状态，局域网环境提高远程画面质量。此次只调整 Web 入口和参数，不修改应用业务代码或原桌面交付。

- Web 入口未收到任务参数时追加 `--fixedAxis 60 0`；设备就绪后沿原应用流程自动开始，累积默认 10 秒、停稳 2 秒。显式单轴/环形/蛇形和时间参数保持优先，`--headless`、帮助、版本继续直接交原程序。自动任务模式下 JSON 仍遵守原应用只读约定，界面修改不写回；持久参数通过宿主配置文件修改后重启。
- noVNC 根入口增加 `quality=9&compression=0`，x11vnc 使用 `-wait 20 -defer 5`。实际本地浏览器设置显示画质 9、压缩 0，服务端在首次连接和重启后重连两次均记录 `Using image quality level 9`、`Using compression level 0`。VNC 流量取决于画面变化；未宣称固定 Mbps、固定帧率或无损 JPEG。
- 更新镜像 `lidar-simonly-web:1.2.1` ID：`sha256:18767159b6199f3f932a769ad530ebd7b98e28c7f00709e6ae5b9d2e5b01fdcf`。原 Web 镜像保留为 `lidar-simonly-web:1.2.1-manual-20261029`，原已退出的 Web 容器保留为 `lidar-sim-web-before-autostart-20261029`。桌面基础镜像、应用二进制和历史桌面压缩包不变。
- Windows / MSVC / Qt 6.11.2：Release 构建通过，CTest **6/6**；qmllint 退出 0，仍是此前六项 required alias 告警。Web 容器专项 **56/56**、原无窗口回归 **36/36**；新增默认启动用例不传任何任务/时间参数、不连接浏览器，实际自动出谱并绘制 OpenGL 曲面。
- ArchHFNL 新部署容器 ID `7dd9d4346040591c38181a8642956c6a30a16faa8b20dd9f20266220a40fc428`，配置命令只有 `--config /config/simulation.json`，入口实际启动应用时补入默认任务。浏览器首次登录前，完整功率谱和径向风已从旧有 **207/207** 增至 **212/212**，无需点击开始。
- 再执行实际 `docker restart --time 15 lidar-sim-web`：StartedAt 从 UTC `05:18:12` 变为 `05:20:48`，应用宿主 PID 从 **58706** 变为 **62130**。重启前完整谱/径向风 **221/221**，重启后 **235/235**；配置 SHA256 始终为 `a7461f2d4b653bd446a584998ad1bbe699509b4e1adbacedccffc115774880c0`。未点击开始，浏览器自动重新连接并显示新任务“采集中”，参数为 60°/0°、10 秒/2 秒。此处容器重启会创建新采集会话，区别于浏览器断线时应用会话保持。
- 本轮结束保持部署运行和持续采集，取代下方初次验证结束时停采的历史状态。未提交或推送 Git，未发布镜像注册表。

证据在 ArchHFNL 部署目录的 `evidence-autostart/`，本地为 `build/web-validation-autostart/`，包含构建/回归报告、重启前后快照、服务端协商日志及真实浏览器 JPG。下方记录保留初次部署时的镜像、行为和验证结果。

## 2026-10-29：Web Docker 与无桌面 ArchHFNL 浏览器实测

用户要求：在本仓增加 Xvfb + x11vnc + noVNC Web 交付，尽量不改业务代码，保留原包，部署 ArchHFNL 并从本地浏览器核对操作、断线重连和持续采集。

- 新增 `docker/web` 派生镜像、生命周期入口、启动脚本和说明，以及 `tests/web` 容器验证与会话快照工具。`src/`、`include/`、`cmake/`、CMakeLists、原 Dockerfile、原桌面入口和固定依赖未改。派生镜像内应用二进制与原桌面镜像 SHA256 完全相同，不重新编译应用或 Qt。
- 基础镜像仍为 `lidar-simonly:1.2.1`，ID `sha256:6717f5799e1be30cd089865dae2b3db7bc9ff0820a8229fdd2ac5172e2cb99fc`。Web 镜像独立为 `lidar-simonly-web:1.2.1`，ID `sha256:c17127d2f502ecb6261132b314fb6f1a9a41f5d5aeed76014d26c8357308e3c6`。没有推送镜像注册表或 Git。
- ArchHFNL 为 x86_64、Docker 29.9.2；部署时 DISPLAY/WAYLAND_DISPLAY 为空、display-manager inactive。容器不挂宿主显示或 GPU，普通 UID/GID 1001:1001，禁用提权并去掉 capabilities。虚拟显示有独立 Xauthority，X 禁用 TCP，VNC 只在容器回环监听；仅内网 `192.168.128.254:6080` 发布网页，使用 VNC 密码认证。
- 镜像包版本：Xvfb `2:21.1.12-1ubuntu1.9`、x11vnc `0.9.16-10`、noVNC `1:1.3.0-2`、websockify `0.10.0+dfsg1-5build2`、Openbox `3.6.1-12build5`、tini `0.19.0-1`。Qt 仍为 6.11.2，使用 xcb + Mesa 软件 OpenGL。
- Windows / MSVC / Qt 6.11.2：Release 构建无编译警告，CTest **6/6** 通过。qmllint 退出 0，仍有下方已记录的六项 required alias 告警，未新增、未抑制，不写成零告警。
- `tests/web/verify.py` **43/43**：二进制不变、无密码拒绝启动、noVNC 资源服务、端口/挂载边界、三个任务在没有浏览器连接时持续出谱与保存、完整小端 double 数值、输出所有者、三任务真实 OpenGL 曲面、两种四束风廓线、关窗/SIGINT/SIGTERM 及 30 秒累积期间取消。所有停止均正常退出 0，应用取消日志先于显示关闭，不增加保存排空。
- Web 镜像执行原 `tests/docker/verify.py` **36/36**：保留 `--headless` 直接运行原应用的入口，不启动 Web/显示组件；三任务采样、只读 JSON、输出和取消回归通过。
- 实际 Windows 本地浏览器访问远端地址，密码登录成功；通过鼠标切换设备/任务页，键盘将单轴累积由 10 秒改为 2 秒，点击开始、停止、再次开始；实际显示并拖动旋转功率谱曲面。停止后原窗口和应用进程保留。
- 断线证据：主动断开 noVNC，随后仅将该浏览器标签置为离线，尝试连接显示“无法连接到服务器”。完整功率谱/径向风从断开前 **27/27** 增至离线时 **44/44**，恢复网络、重新认证后增至 **76/76**。容器 ID `89a835937ca65217f150416da28b94e38688b4e251c72cc35ebbb129951df7ed`、应用宿主 PID **51466**、StartedAt 及 RestartCount=0 均保持；页面仍为同一任务的采集中状态。此次验证是主动断开、浏览器离线及手动重连，没有把它写成物理网线拔插或无人值守自动重连实测。
- 配置持久化：浏览器实际按键把风速改为 11，宿主 JSON 随之为 11，文件所有者仍为 1001；随后恢复 10。整个配置目录可写挂载，QSaveFile 原子替换可用；任务参数仍遵守原不写 JSON 的边界。
- 测试结束通过浏览器停止采集，保留健康 Web 容器、现有曲面和输出供用户检查；没有让测试任务无限产文件。旧 `lidar-fixed-ui` 容器未操作。
- 原离线桌面包 `dist/LiDAR-simonly-1.2.1-linux-amd64-desktop.tar.gz` 保留，SHA256 为 `226ee9d61e4bef0661e151ea64472eb43a2935afc20cdb26447face931b2e8e5`，与本轮开始时一致。

部署目录：ArchHFNL `/home/lateef_zhou/lidar-simonly-web-20261029/`；`source` 为本轮源码副本，`state/config`、`state/output`、`state/secrets` 分别保存配置、输出、密码，`evidence` 保存验证日志、报告、截图和会话快照。本地证据：`build/web-validation/`（含浏览器 JPG、构建、CTest、qmllint 和回收的远端证据）；认证文件只在忽略目录，不随源码或报告分享。部署入口详见 `docker/web/README.md`。

## 离线桌面交付与默认风场

用户定：默认 JSON 改为线性剪切与随机起伏（linearShear/gust），其余参数不变；既有文件不覆盖。示例、镜像内共享配置和程序首次生成的内嵌默认配置三者一致。

- Windows 增量构建、CTest 6/6、运行断言 98/98 通过。
- 重建 Qt 6.11.2 镜像后，三任务无窗口采样、保存、退出回归 36/36；交付专项 10/10，覆盖新默认值、首次生成配置、包内启动脚本从桌面会话补齐授权、实际采样与 stop 退出。
- 离线镜像重新导入成功。交付镜像 ID：`sha256:6717f5799e1be30cd089865dae2b3db7bc9ff0820a8229fdd2ac5172e2cb99fc`。下方先前显示验证的镜像记录保留当时版本；本轮只更新默认 JSON 和交付工具，没有改渲染、设备或任务运行逻辑。
- `docker/delivery` 的 README 面向首次使用者，覆盖环境、解压、校验、导入、JSON、三任务启动、日志、停止、重启和数据位置。交付包不含运行数据或显示认证，输出目录为空；不替换旧 sim-ui 交付包，不推送 simonly。

## Linux 桌面与 Docker 显示通道

后续真实桌面确认：用户在 GNOME Wayland 登录后，已通过当前用户会话的 DISPLAY/XAUTHORITY 启动同一镜像，确认 UI 正常显示；容器连续生成完整功率谱。之前无窗口的现场问题是启动终端未带显示环境、尚未创建容器，不是渲染失败。交付启动脚本据此支持从当前用户 systemd 桌面会话补齐显示变量；不猜测显示号，不修改显示服务权限。

版本 1.2.1-simonly。命令行任务默认显示窗口，显式 `--headless` 保留无窗口模式；创建期初始化参数、就绪后调用无参 start() 的契约不变。停止按钮保留 UI；关窗、Ctrl+C、SIGTERM 先经 stop() 撤单再退出。JSON、输出目录、三个独立协程和取消链保持，不新增保存排空。

- Windows / MSVC / Qt 6.11.2：Release 增量构建无编译警告，CTest 6/6、运行断言 97/97、生产 CLI 与控制台取消 19/19。
- 原生 Arch Linux / GCC / Qt 6.12：构建、公开头检查、CTest 6/6、运行断言 97/97；生产无窗口 CLI 32/32；真实 X11 窗口与 Mesa OpenGL 桌面检查 32/32。
- Docker / Qt 6.11.2：最终 Dockerfile 构建的 `lidar-simonly:1.2.1`，桌面 32/32、无窗口回归 36/36；插件依赖、非 root 输出权限、只读 JSON、无 GPU/显示挂载的 headless 模式均通过。镜像 ID 为 `sha256:97f71cf98c3dbfe0113b055796712a3c876feba5e17116231c632c3965f28029`，仅保存在验证主机，未推送镜像仓库。
- 容器桌面使用实际 `docker/run-desktop.sh`，挂载本机 X11 socket、仅当前显示的临时认证、只读 JSON 和输出目录，不用 xhost、特权模式或宿主 IPC。核验 Qt 6.11.2 的 `QT_XCB_NO_MITSHM` 开关；三任务截图中文字、控制栏与曲面均已人工复核。蛇形通过 docker stop，环形通过容器 SIGINT，单轴及长累积通过窗口关闭；均正常返回 0，无 SIGKILL。
- 桌面专项：三任务均实际显示曲面、连续采样、写入 450×200 小端 double 谱与径向风；环形和蛇形还生成四束风廓线。单轴关窗、环形 SIGINT、蛇形 SIGTERM，以及 30 秒累积中途关窗，均先停止任务后正常退出；JSON 未改写。另用应用测试确认停止按钮不会退出、可以再次无参 start()，隐藏模式不准备 Surface 数据。
- 截图发现并修复应用入口的两项显示适配：Linux 改用 Fusion，Windows 保持 FluentWinUI3；登记 VerticalWindProfilePtr 信号别名，处理线程到 QML 不再丢弃风廓线通知。没有修改上游设备、算法或任务实现。
- 测试主机没有已登录桌面或字体；显示验证使用独立、有认证的 Xvfb 服务，并为原生测试提供独立字体目录。实际运行 Qt xcb 插件与软件 OpenGL，检查映射窗口、保存截图并人工复核中文和曲面。不是 offscreen 冒烟，但不代表真实 XWayland 桌面合成器或硬件 GPU 已实测。
- QML 静态检查仍报告六项 azimuths/elevation 的 required alias 告警；Qt 6.11.2、6.12 的独立三行实例均复现“已显式赋值仍报缺失”。保留告警，不降低检查级别、不增加参数副本；既有官邸测试验证逐项漏参拒绝创建，应用测试验证提供参数后在启动前正确显示。修正本应用的 id 同名遮蔽后，无其他应用 QML 告警。

操作入口、桌面挂载和测试命令见 README、tests/README。simonly 本次只本地提交，不推送；旧 sim-ui、历史 Docker 交付和全功能主程序不变。

## 任务创建参数与无参启停

三个 simonly 任务官邸的 azimuths/elevation/accum/settle 改为创建时必填；角度直接 alias 到唯一计划。自动启动与运行按钮都调用无参 start()/stop()。全功能页面、三个 C++ 协程、设备配置及取消链没有修改。本轮没有改窗口可见性或 Docker 显示通道。

- Windows / MSVC / Qt 6.11.2：Release 构建、公开头编译、CTest 6/6，运行检查 63/63，生产 CLI/系统取消 19/19；完成应用与四个上游 QML 模块的 qmllint。先前“无 Warning/Error”的记录不准确：本轮从固定远端依赖复查发现 required alias 告警，独立复现及范围见上方。
- Linux / GCC / Qt 6.12：应用构建、CTest 6/6，生产 CLI/三任务采样保存/信号退出 32/32；TaskCore 独立构建及 3/3 测试通过，其中真实运行按钮只调用无参命令。
- 创建期专项：逐项省略四个参数均拒绝创建；非默认角度与时间在处理设备连接或自动启动消息之前已经进入页面；计划与官邸互相编辑反映到同一份值。
- Docker / Qt 6.11.2：独立开发测试镜像通过 36/36，覆盖三任务实际采样、落盘、只读 JSON 和累积途中 SIGTERM。镜像使用本轮源码覆盖验证，未替换已有交付镜像或压缩包；这些无窗口结果不代表 Linux 桌面显示已经验证。

四个上游已发布：TaskCore `a830298`、FixedTask `813781b`、CycleTask `26fca00`、SnakeTask `0696e7d`。Windows 与 Linux 均清除本地源码覆盖，从 GitHub 拉取本仓固定的完整提交；逐项核对检出版本一致，重新构建及 CTest 6/6 通过。simonly 应用本次只做本地提交。

## 独立应用初次发布

源代码与依赖见本仓固定提交清单，Qt 版本按实际运行环境分别记录。

| 环境 | 结果 |
|---|---|
| Windows/MSVC，Qt 6.11.2 | Release 构建与公开头严格编译通过，CTest 6/6；运行检查 57/57；生产程序 CLI/系统取消 19/19 |
| 原生 Linux/GCC，Qt 6.12 | 构建与 CTest 6/6；生产程序 CLI/三任务输出/信号退出 32/32 |
| Linux Docker，Qt 6.11.2 | 从远端固定版本构建；容器验证 36/36 |
| 上游全功能应用，Qt 6.11.2 | Release 构建、8 秒离屏冒烟日志与原基线一致；Direct3D 集成 777/777 |

覆盖两套 QML 页面的唯一具体后端及销毁；JSON 非法输入拒绝、配置往返、八种风场组合；三任务无窗口历史采样且 Surface 没有准备绘制；固定目录下的小端 double 谱、径向风及四束风廓线；只读配置不被改写；Ctrl+C/SIGTERM 经原取消链释放锁和退出。

Docker 镜像为 linux/amd64，Ubuntu 24.04 用户空间与官方 Qt 6.11.2 归档校验固定；本次构建复用同 SHA256 的既有归档缓存，设备和任务仍从 GitHub 固定提交拉取。没有挂载显示服务或 GPU，无 libpcap/libserialport 运行依赖，运行层无编译器。三任务均实际出谱，输出归启动用户所有；正常运行及 30 秒累积途中 docker stop 均正常退出，没有 SIGKILL。未增加退出保存排空，不承诺停止时保存最后一帧。

应用与五官邸、TaskUI 的 CMake qmllint 无 Warning/Error。Windows 新应用及全功能应用均清除本地源码覆盖后从远端构建，六项更新的实际检出 SHA 与固定值逐项一致。六个更新依赖库的 Windows/Linux GitHub Actions 均通过。

重复命令见 [README](README.md) 与 [tests/README.md](tests/README.md)。本次仅生成测试镜像，没有替换旧 sim-ui 交付包或向镜像注册表推送。
