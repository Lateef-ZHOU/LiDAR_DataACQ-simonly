# 验证入口

`cmake` 配置默认启用测试，`ctest --test-dir build -C Release --output-on-failure` 执行六项：五个官邸分别创建全功能/simonly 页面，检查唯一后端、所有权、销毁和精简分区；应用测试检查 JSON 校验与往返、八种风场组合、三任务隐藏采样、零 Surface 绘制、主线程取消和释放设备锁。

官邸测试还逐头严格编译公开接口。运行测试使用生产 QML 与 C++，不创建实物设备连接；测试输出位于构建目录的 tests/runtime-results。

生产可执行文件的黑盒验证：

```sh
python3 tests/sim-runtime/cli.py --exe build/LiDAR_DataACQ --out build/cli-results
```

Windows 将路径改为 `build/Release/LiDAR_DataACQ.exe`，并把 Qt 的 bin 放入 PATH。测试使用独立工作目录与实际系统信号；Windows 覆盖界面离屏冒烟、单轴保存和累积中 Ctrl+C；Linux 另覆盖三个编排的持续谱/径向风、四束风廓线、只读 JSON、SIGTERM 与 SIGINT。原生测试不要求机器没有显卡，Docker 验证才检查未挂载 GPU 和显示服务。

Docker 验证入口为 `tests/docker/verify.py`，需要 Linux、Python 3 和已构建镜像。它创建独立容器及结果目录，只删除自己创建的容器，保留日志和文件。测试不要求退出保存排空。
