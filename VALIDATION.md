# 验证记录：2026-10-27

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
