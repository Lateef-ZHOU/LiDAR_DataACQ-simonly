# 验证记录：2026-10-27

## Linux 桌面与 Docker 显示通道

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
