# 第三方依赖与分发

本仓自有代码采用 MIT，参见 LICENSE。依赖不会因此改为 MIT。

- 公共库及五个官邸通过 GitHub 固定提交引用，均保留自身 LICENSE 和第三方说明。
- Qt Core/Gui/Qml/Quick/ShaderTools 使用其各模块许可，可选择满足条件的 LGPLv3/GPL 或商业许可。交付动态库时保留相应版权/许可、源代码获取方式及 LGPL 要求的替换/重新链接能力；商业 Qt 按所购许可处理。不能以应用的 MIT 代替 Qt 授权。Qt 许可入口：https://doc.qt.io/qt-6/licensing.html ，对应源代码：https://download.qt.io/archive/qt/6.11/6.11.2/ 。
- Docker 内 Ubuntu 系统包、Noto 字体、GCC/OpenMP 运行库等分别适用各包许可。镜像保留系统包管理器和 `/usr/share/doc` 中的说明；Qt 使用 `docker/qt-6.11.2.lock` 固定官方归档及 SHA256。
- 本仿真应用不启用串口或抓包 Handle，不打包 libserialport、libpcap、Npcap SDK/驱动；无需实物设备驱动授权。

源代码仓库不包含第三方 SDK 或编译后的运行库。对外分发镜像/二进制时，应随包保留本说明、自有 LICENSE 和所用 Qt/系统包的许可材料。
