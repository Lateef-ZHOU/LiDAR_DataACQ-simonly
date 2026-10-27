# LiDAR_DataACQ-simonly

使用中文沟通。开始先检查 Git 分支、未提交修改和固定依赖；技术入口见 README.md、cmake/Dependencies.cmake 和 tests/README.md。

本仓是装配应用，不 fork 或复制官邸 C++。设备、三个独立任务的功能在各自仓库维护，全功能和 simonly QML 共用后端。修改上游应先验证并发布完整提交，再更新固定引用。主程序 LiDAR_DataACQ 和旧 sim-ui/Docker 交付不随本仓修改。

simonly 无单卡测试、设备选择、保存开关或目录选择，任务总是保存到当前工作目录；保留所有风场、累积窗口和 QML 历史源。命令行任务默认打开 UI，显式 --headless 才隐藏；关窗、Ctrl+C/SIGTERM 先调用任务 stop()，沿现有主线程取消链退出，不新增保存排空。构造后先配置与场景快照，再连接和启动。

2026-10-27 任务创建契约：三个 simonly 官邸必须在创建时接收 azimuths/elevation/accum/settle，角度 alias 到唯一计划，时间由页面持有。自动启动与开始按钮统一调用无参 start()，停止调用无参 stop()；启动编排不再补写参数。设备参数仍由 JSON 提供，任务参数不写入 JSON。桌面停止按钮只停任务，允许再次启动；关窗或系统信号才退出。Docker 使用本机 X11 / XWayland、当前显示授权和 Mesa OpenGL，JSON 与输出挂载保持；无桌面服务器使用 --headless。不将离屏测试写成桌面实测，平台和显示验证边界见 VALIDATION.md。

不使用 friend，不增加假想接口、状态或转发层。QT_NO_KEYWORDS；提交使用中文 type(scope): 标题。验证至少包括 Release 构建、CTest、QML lint；涉及配置/采样/取消时跑生产命令行与 Docker 专项，不能把静态检查写成运行验证。说明记录真实执行的平台和 Qt 版本。推送须有用户指示。

2026-10-27 桌面交付：部署说明和便捷入口在 docker/delivery，离线包放 dist。新默认 JSON 与镜像资源均为线性剪切 + 随机起伏（linearShear/gust），其余数值不变，不覆盖已有 JSON。交付脚本以普通桌面用户运行，Docker 按需使用 sudo；缺显示变量时仅从当前用户已登录的 systemd 桌面会话补齐。真实 GNOME/XWayland 已由用户确认显示。simonly 仍不推送。
