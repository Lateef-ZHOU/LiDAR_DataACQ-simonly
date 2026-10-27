# LiDAR_DataACQ-simonly

使用中文沟通。开始先检查 Git 分支、未提交修改和固定依赖；技术入口见 README.md、cmake/Dependencies.cmake 和 tests/README.md。

本仓是装配应用，不 fork 或复制官邸 C++。设备、三个独立任务的功能在各自仓库维护，全功能和 simonly QML 共用后端。修改上游应先验证并发布完整提交，再更新固定引用。主程序 LiDAR_DataACQ 和旧 sim-ui/Docker 交付不随本仓修改。

simonly 无单卡测试、设备选择、保存开关或目录选择，任务总是保存到当前工作目录；保留所有风场、累积窗口和 QML 历史源。命令行任务无窗口，Ctrl+C/SIGTERM 沿现有主线程取消链退出，不新增保存排空。构造后先配置与场景快照，再连接和启动。

2026-10-27 任务创建契约：三个 simonly 官邸必须在创建时接收 azimuths/elevation/accum/settle，角度 alias 到唯一计划，时间由页面持有。自动启动与开始按钮统一调用无参 start()，停止调用无参 stop()；启动编排不再补写参数。设备参数仍由 JSON 提供，任务参数不写入 JSON。Linux 桌面显示需求已确定，本次先完成此接口整理，窗口可见性与 Docker 显示通道尚未修改，不将无窗口测试视为桌面验证。

不使用 friend，不增加假想接口、状态或转发层。QT_NO_KEYWORDS；提交使用中文 type(scope): 标题。验证至少包括 Release 构建、CTest、QML lint；涉及配置/采样/取消时跑生产命令行与 Docker 专项，不能把静态检查写成运行验证。说明记录真实执行的平台和 Qt 版本。推送须有用户指示。
