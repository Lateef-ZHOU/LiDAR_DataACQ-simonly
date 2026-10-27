# LiDAR 数字样机 1.2.1：Linux 桌面部署

本包包含 Docker 镜像、示例 JSON 和启动脚本，无需下载源码或编译。

## 1. 环境准备

- x86_64 / amd64 Linux，已安装并启动 Docker。
- 已登录图形桌面：X11，或开启 XWayland 的 Wayland 桌面。已在 GNOME Wayland / XWayland 上确认显示。
- Bash、xauth 和常用系统工具；镜像自带 Qt 6.11.2、中文字体和软件 OpenGL，不需要安装 Qt 或挂载 GPU。

安装 xauth（选择自己的发行版）：

```bash
# Ubuntu / Debian
sudo apt install xauth
# Arch Linux
sudo pacman -S --needed xorg-xauth
```

若 Docker 服务尚未启动：

```bash
sudo systemctl start docker
```

## 2. 解压并导入镜像

在压缩包所在目录执行：

```bash
tar -xzf LiDAR-simonly-1.2.1-linux-amd64-desktop.tar.gz
cd LiDAR-simonly-1.2.1-linux-amd64-desktop
sha256sum -c SHA256SUMS
./docker.sh load -i lidar-simonly-1.2.1.tar
```

`docker.sh` 在当前用户能直接操作 Docker 时直接执行，否则提示输入 sudo 密码。启动脚本本身请以普通桌面用户运行，不要执行 `sudo ./start.sh`。

## 3. 修改设备配置

用文本编辑器打开 `simulation.json`，按需要修改云台安装朝向、两轴速度、风场类型与时域变化、探测器参数和环境温度。保留全部字段及合法 JSON 格式。配置错误会拒绝启动，不会静默替换为默认值。

本版默认选择线性剪切（`kind: linearShear`）和随机起伏（`temporal: gust`）。其余数值保持原默认值：地面风速 10 m/s、风向 270°；风速梯度 5 m/s/km、风向梯度 30°/km、顶高 3000 m；起伏风速标准差 1 m/s、风向标准差 10°、时间尺度 30 s。

设备参数来自 JSON，任务类型、世界系角度和时间来自命令行。启动时 JSON 只读挂载；运行期间修改文件不会自动应用，应停止后重新启动。带命令行任务时，界面调整也不会写回 JSON。

## 4. 启动并显示界面

在已经登录的桌面终端中，从本目录选择一种命令执行。三种任务使用同一容器名，依次测试，不要同时启动：

```bash
# 单轴：高度角 60°，方位角 0°
./start.sh --fixedAxis 60 0 --accumulate 2 --settle 2

# 环形四轴：按输入方位顺序循环
./start.sh --cycleAxis 60 0 90 180 270 --accumulate 2 --settle 2

# 蛇形四轴：先采第 0 束，再循环 1→2→3→2→1→0
./start.sh --snakeAxis 60 0 90 180 270 --accumulate 2 --settle 2
```

高度角在方位角之前，单位为度；`accumulate` 为累积秒数，`settle` 为停稳秒数。界面任务页直接使用这些参数初始化，设备就绪后自动采集。运动、停稳、累积完成后才会更新功率谱。

脚本自动挂载：

- `simulation.json` → `/config/simulation.json`，只读。
- `output/` → `/data`，可写，文件归启动用户所有。
- 当前 X11/XWayland socket 与仅当前显示的临时认证，不需要 `xhost +` 或特权容器。

如果终端缺少显示变量，脚本尝试从当前用户已登录的 systemd 桌面会话取得 `DISPLAY` 和 `XAUTHORITY`。这不会创建桌面：机器仍需有人登录图形会话，窗口显示在那台机器的桌面上，不会出现在 SSH 客户端。若未取得授权，请回到桌面终端执行；不要手动猜测 `DISPLAY=:0`。

## 5. 查看日志、停止与重新启动

```bash
./docker.sh logs -f lidar-sim
```

日志查看中的 Ctrl+C 只结束查看。停止采集并退出程序：

```bash
./docker.sh stop lidar-sim
```

也可以直接关闭 UI 窗口。两者都会先停止任务，再退出事件循环。任务页的停止按钮只停止采集，保留窗口，允许再次开始。

切换任务或重新启动前，删除已停止的容器，然后重新执行第 4 步：

```bash
./docker.sh rm lidar-sim
```

不要用 `docker start` 复用停止的容器：显示认证是每次启动临时生成的。删除容器不会删除 `output/` 中的数据或 JSON。

## 6. 输出与常见情况

输出保存在本目录 `output/`：

- `Rawspec/`：无头、小端 double 功率谱，每帧 450×200，720000 字节。
- `Radialwind/`：径向风文件。
- `Windprofile/`：环形、蛇形完成四束后生成的风廓线。

停止时不额外等待保存队列排空，不保证保留最后一帧。

没有窗口时，先执行 `./docker.sh ps -a` 和 `./docker.sh logs lidar-sim`。若没有容器，检查启动脚本之前的错误、桌面登录状态和 xauth；若提示容器名已存在，先停止并删除旧容器。界面由 CPU 软件 OpenGL 绘制，性能取决于主机；不含远程桌面服务。

无窗口服务器也可使用同一镜像：

```bash
mkdir -p output
./docker.sh run -d --name lidar-sim --user "$(id -u):$(id -g)" \
  -v "$PWD/simulation.json:/config/simulation.json:ro" -v "$PWD/output:/data" \
  lidar-simonly:1.2.1 --headless --config /config/simulation.json \
  --fixedAxis 60 0 --accumulate 2 --settle 2
```

查看日志和停止命令相同。镜像和源码版本信息见 `VERSION.txt`，许可说明见 `LICENSE` 和 `THIRD_PARTY_NOTICES.md`。
