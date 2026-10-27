# LiDAR_DataACQ-simonly

独立的 LiDAR 数字样机应用，适用于 Windows 配置/演示和 Linux Docker 无窗口采集。通过固定提交引用公共库及五个官邸，无需从全功能主程序反复派生分支。

两个虚拟设备和三个任务仓库各提供全功能、simonly 两套 QML 页面，共用同一 C++ 后端。这里仅装配 simonly 页面：自动连接、固定设备，采集始终保存到当前工作目录；没有单卡试采、设备选择、保存开关或目录选择。保留累积/停稳设置、所有风场模式、图表和三个独立协程。

## Docker 快速使用

宿主需要 x86_64 Linux 和 Docker，不限定 Linux 发行版。无需显示器、GPU、Qt 或实物设备驱动。首次构建需要联网下载 Qt 和固定版本的依赖仓库。

```sh
git clone https://github.com/Lateef-ZHOU/LiDAR_DataACQ-simonly.git
cd LiDAR_DataACQ-simonly
docker build --platform linux/amd64 -t lidar-simonly:1.2.0 .
cp config/simulation.example.json simulation.json
mkdir -p output
```

修改 `simulation.json` 中的安装姿态、云台限速、风场、探测器和环境温度。所有字段均须保留；支持均匀/线性切变风场及稳态/正弦/过渡/阵风四种时间变化。参数不合法时启动失败，不静默采用默认值。命令行模式只读 JSON，修改后需重新启动。

选择一种任务运行，三种命令的挂载方式完全相同：

```sh
# 单轴：高度角 60°，方位角 0°，累积 2 秒，停稳 2 秒
docker run -d --name lidar-fixed --user "$(id -u):$(id -g)" \
  -v "$PWD/simulation.json:/config/simulation.json:ro" -v "$PWD/output:/data" \
  lidar-simonly:1.2.0 --config /config/simulation.json \
  --fixedAxis 60 0 --accumulate 2 --settle 2

# 环形四轴：按输入方位顺序循环
docker run -d --name lidar-cycle --user "$(id -u):$(id -g)" \
  -v "$PWD/simulation.json:/config/simulation.json:ro" -v "$PWD/output:/data" \
  lidar-simonly:1.2.0 --config /config/simulation.json \
  --cycleAxis 60 0 90 180 270 --accumulate 2 --settle 2

# 蛇形四轴：先采 0，再循环 1→2→3→2→1→0
docker run -d --name lidar-snake --user "$(id -u):$(id -g)" \
  -v "$PWD/simulation.json:/config/simulation.json:ro" -v "$PWD/output:/data" \
  lidar-simonly:1.2.0 --config /config/simulation.json \
  --snakeAxis 60 0 90 180 270 --accumulate 2 --settle 2
```

设备就绪后自动采集。按实际使用的容器名查看日志、停止和删除容器：

```sh
docker logs -f lidar-fixed
docker stop lidar-fixed
docker rm lidar-fixed
```

`docker logs -f` 中的 Ctrl+C 仅结束日志查看；`docker stop` 才向程序发 SIGTERM。采集程序直接作为 PID 1，主线程沿原有取消链停止任务并退出。退出不增加保存排空或等待；尚未处理的帧和未结束的保存允许中断。建议依次测试，避免多个进程共用输出目录时产生同名文件。

输出位于宿主 `output/`：`Rawspec/` 为无头、小端 double 功率谱，每帧 450×200、720000 字节；`Radialwind/` 为径向风；环形/蛇形完成四束后在 `Windprofile/` 写风廓线。启动后先运动、停稳，再累积采样，文件不会立即出现。

## 原生构建与运行

需要 C++20、CMake ≥3.28、Git 和 Qt ≥6.11.2（Core/Gui/Qml/Quick/GuiPrivate/ShaderTools，测试另需 Test）。Windows 使用 MSVC x64，Linux 使用 GCC/OpenMP。纯仿真不需要 libserialport、libpcap 或 Npcap。

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=/path/to/Qt
cmake --build build --config Release --parallel 2
ctest --test-dir build -C Release --output-on-failure
cmake --build build --config Release --target LiDAR_DataACQ_qmllint
```

Linux 执行 `./build/LiDAR_DataACQ`，Windows 在 Qt 运行环境执行 `build/Release/LiDAR_DataACQ.exe`，或用生成的 `build/run_LiDAR_DataACQ.cmd`。不带任务参数时显示配置界面，默认读写当前目录 `simulation.json`；文件不存在则生成默认配置。GUI 编辑会持久化，任务参数不写入 JSON。

```sh
./build/LiDAR_DataACQ --config simulation.json --fixedAxis 60 0 --accumulate 2 --settle 2
./build/LiDAR_DataACQ --config simulation.json --cycleAxis 60 0 90 180 270 --accumulate 2 --settle 2
./build/LiDAR_DataACQ --config simulation.json --snakeAxis 60 0 90 180 270 --accumulate 2 --settle 2
```

带任务参数时不显示窗口，仍创建角度与风场历史源，按实际累积窗口采样。原生终端 Ctrl+C、Linux SIGTERM 都触发取消并退出。累积默认 10 秒、范围 1–3600；停稳默认 2 秒、范围 2–600；角度使用世界系，命令参数始终高度角在前。

## 维护边界

- 本仓库：进程入口、JSON 校验/持久化、命令行和信号处理、五页静态装配、Docker 与集成测试。
- [SimGimbalDevice](https://github.com/Lateef-ZHOU/SimGimbalDevice)、[SimCardDevice](https://github.com/Lateef-ZHOU/SimCardDevice)：各自两套 QML 页面和唯一型号实现。
- [FixedTask](https://github.com/Lateef-ZHOU/FixedTask)、[CycleTask](https://github.com/Lateef-ZHOU/CycleTask)、[SnakeTask](https://github.com/Lateef-ZHOU/SnakeTask)：各自两套页面、计划与独立协程。
- TaskCore 的 `SimOnlyTaskModule` / `SimOnlyTaskRunSection` 为可选参考 UI；核心仍不依赖 QML。
- simonly 任务官邸创建时必须接收 `azimuths/elevation/accum/settle`；命令行直接初始化被选中的页面，未选中的页面显式使用默认值。启动编排只等待设备就绪后调用无参 `start()`，不再事后改写计划；停止统一调用无参 `stop()`。角度 alias 到唯一计划，时间由页面持有，开始按钮与自动启动共用同一入口。
- 所有依赖固定完整提交，见 `cmake/Dependencies.cmake`。不复制算法、设备或协程源码，不追踪浮动分支。

详细测试入口见 [tests/README.md](tests/README.md)，实际执行结果见 [VALIDATION.md](VALIDATION.md)。MIT，版权 2026 周涛（ZHOU TAO）；第三方依赖另见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。Docker 的 Ubuntu 用户空间和 Qt 6.11.2 独立依赖层保留，宿主不需要使用 Ubuntu。
