# 验证入口

`cmake` 配置默认启用测试，`ctest --test-dir build -C Release --output-on-failure` 执行六项：五个官邸分别创建全功能/simonly 页面，检查唯一后端、所有权、销毁和精简分区；应用测试检查 JSON 校验与往返、八种风场组合、三任务显示/隐藏采样、隐藏时零 Surface 准备、显示时更新显示数据、主线程取消和释放设备锁。该集成测试使用 Null RHI，不替代下面的真实 OpenGL 绘制验证。

官邸测试还逐头严格编译公开接口。运行测试使用生产 QML 与 C++，不创建实物设备连接；测试输出位于构建目录的 tests/runtime-results。

任务官邸测试逐项省略四个必填创建参数并验证创建失败，检查角度属性与唯一计划双向一致、时间初值和无参 start/stop 的元对象调用。应用集成测试在尚未处理启动消息时检查三个任务页面已取得命令行参数，再运行实际设备采样、落盘与取消链。

生产可执行文件的黑盒验证：

```sh
python3 tests/sim-runtime/cli.py --exe build/LiDAR_DataACQ --out build/cli-results
```

Windows 将路径改为 `build/Release/LiDAR_DataACQ.exe`，并把 Qt 的 bin 放入 PATH。测试使用独立工作目录与实际系统信号；Windows 覆盖界面离屏冒烟、单轴保存和累积中 Ctrl+C；Linux 另覆盖三个编排的持续谱/径向风、四束风廓线、只读 JSON、SIGTERM 与 SIGINT。原生测试不要求机器没有显卡，Docker 验证才检查未挂载 GPU 和显示服务。

Docker 验证入口为 `tests/docker/verify.py`，需要 Linux、Python 3 和已构建镜像。它创建独立容器及结果目录，只删除自己创建的容器，保留日志和文件。测试不要求退出保存排空。

## Linux 桌面与 Docker 显示

`tests/desktop/verify.py` 使用生产可执行文件或 `docker/run-desktop.sh`，实际创建 X11 窗口、使用 Mesa OpenGL 绘制。建议在独立、带授权的 Xvfb 显示上运行，以免测试找错已有的 LiDAR 窗口。需要 Python 3、libX11、Xvfb 和 xauth：

```sh
xvfb-run -a -s '-screen 0 1920x1080x24' \
  python3 tests/desktop/verify.py --exe build/LiDAR_DataACQ --out build/desktop-results
xvfb-run -a -s '-screen 0 1920x1080x24' \
  python3 tests/desktop/verify.py --image lidar-simonly:1.2.1 --out build/docker-desktop-results
python3 tests/docker/verify.py --image lidar-simonly:1.2.1 --out build/docker-headless-results
```

三任务均检查实际窗口、连续采样、小端 double 谱与径向风；两种四轴任务另检查风廓线。截图检查曲面颜色，并保留 PNG 供人工复核。单轴通过 WM_DELETE_WINDOW 关窗，环形通过 SIGINT，蛇形通过 SIGTERM（容器用 docker stop）；另验证长累积中关窗，要求停止日志在事件循环退出前出现、正常返回且 JSON 不变。完整结果和日志在指定输出目录。

`tests/desktop/Dockerfile` 仅提供独立的测试显示服务，不进入交付镜像。Xvfb 验证证明 X11 通道和软件 OpenGL 窗口可用，不能代替具体桌面合成器、原生 Wayland 或硬件 GPU 的实机验证。

Qt 6.11.2 和本次原生环境的 Qt 6.12 qmllint 会把显式赋值的 required alias 误报为未赋值（任务的 azimuths/elevation）；独立最小例也可复现。本项目不抑制该类检查，也不为绕过检查增加参数副本；运行测试逐项验证省略必填参数拒绝创建、提供参数正确生效。其余静态告警仍应逐项处理。

## Web 容器

先按 `docker/web/README.md` 构建 Web 镜像，在无桌面的 Linux 服务器执行：

```sh
python3 tests/web/verify.py --docker 'sudo -n docker' --out build/web-results
python3 tests/docker/verify.py --docker 'sudo -n docker' \
  --image lidar-simonly-web:1.2.1 --out build/web-headless-results
```

专项核对应用二进制与桌面镜像完全相同；没有密码文件或密码环境变量仍正常启动，实际 RFB 握手无需密码；只发布浏览器端口，不挂载宿主显示/GPU；不传任务/时间参数即启动默认环形四轴并生成完整风廓线，检查高度网格和有效风速/风向数据；落地页使用画质 9/压缩 0、x11vnc 实际采用轮询/发送间隔；默认及三个显式任务无人连接时持续采样、谱数值与文件所有者、实际 OpenGL 曲面、四束风廓线；关窗、SIGINT、docker stop 和长累积取消正确转交原应用。截图和日志保留，测试创建的随机名容器在结束后删除。

浏览器验证另外记录：免密码直达、页面切换、任务参数编辑与开始/停止；采集过程中断开和重新连接，比较容器 ID、应用 PID、任务状态及新增文件；在浏览器网络不可达期间确认仍持续落盘。更新默认启动策略时，另重启实际部署容器，核对新应用自动开始采集、浏览器自动重新连接及服务端协商的画质/压缩等级。HTTP 页面可达或 X11 截图不能代替这段实际操作。

## Web 离线交付包

在已构建 Web 镜像的 Linux 主机打包，再执行真实导入与启动验证。测试要求 Python 3.12+、`unshare`、`dockerd` 和免交互 sudo；输出目录必须尚不存在，磁盘需容纳解压镜像及临时 Docker 数据。

```sh
bash docker/web/package.sh
python3 tests/web/delivery.py \
  --archive dist/LiDAR-simonly-1.2.1-linux-amd64-web.tar.gz \
  --out build/web-delivery-results
```

验证包内校验和、完整镜像层、空镜像库导入、缺少镜像时本地报错、禁用容器网络后默认环形生成完整 450 层风廓线、正常停止、任意工作目录运行包内入口及已有配置不被覆盖。独立 Docker 同时使用自己的数据目录、运行目录、containerd 命名空间和 `unshare --net` 网络命名空间；必须保留网络隔离，`--bridge=none` 本身仍可能让 dockerd 删除宿主的 docker0。包内脚本的端口访问在主 Docker 上使用随机容器名、独立状态目录和回环临时端口验证。结束只清理本测试创建的容器及已停止守护进程的临时数据，保留日志与采集证据。
