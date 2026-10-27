pragma ComponentBehavior: Bound
import QtQuick
import Lidar.SimGimbal
import Lidar.SimCard
import Lidar.FixedTask
import Lidar.CycleTask
import Lidar.SnakeTask

// 进程启动编排：只调用 QML 官邸，不借出后端；运行仍由三个独立任务负责。
QtObject {
    id: session
    objectName: "SimulationSession"
    required property SimGimbalSimOnlyModule gimbalPage
    required property SimCardSimOnlyModule cardPage
    readonly property bool ready: gimbalPage.isOpen && cardPage.isOpen
    required property FixedTaskSimOnlyModule fixedTask
    required property CycleTaskSimOnlyModule cycleTask
    required property SnakeTaskSimOnlyModule snakeTask
    property SimulationConfig configurationFile: null
    property var initialConfiguration: null
    property var startupRequest: null
    readonly property bool commandLine: startupRequest !== null
    property bool initialized: false
    property var pendingTask: null
    property var activeTask: null
    signal exitRequested(int code)
    signal logMessage(string message)

    function initialize(): void {
        if (initialConfiguration && !applyConfiguration(initialConfiguration)) {
            exitRequested(1)
            return
        }
        initialConfiguration = null // 不维护设置副本；保存时从拥有者收集。
        if (startupRequest) {
            pendingTask = startupRequest.kind === "fixedAxis" ? fixedTask
                : startupRequest.kind === "cycleAxis" ? cycleTask : snakeTask
        }
        initialized = true
        if (!(gimbalPage.open() && cardPage.open())) {
            exitRequested(1)
            return
        }
        Qt.callLater(startPending)
    }
    function startPending(): void {
        if (!pendingTask || !ready) return
        const task = pendingTask
        pendingTask = null
        activeTask = task
        if (!task.start()) {
            activeTask = null
            exitRequested(1)
        } else {
            logMessage(qsTr("设备已就绪，%1已启动；Ctrl+C / SIGTERM 停止").arg(task.name))
        }
    }
    function checkCompletion(): void {
        // 运行通知可能从协程恢复栈发出，延后检查，避免在该栈内销毁协程。
        if (activeTask && !activeTask.running) {
            activeTask = null
            logMessage(qsTr("采集任务已结束"))
            exitRequested(1)
        }
    }
    function cancel(): void {
        pendingTask = null
        activeTask = null
        for (const task of [fixedTask, cycleTask, snakeTask])
            if (task.running) task.stop()
        logMessage(qsTr("任务已取消，退出事件循环"))
        exitRequested(0)
    }
    function saveConfiguration(): void {
        if (initialized && configurationFile && !commandLine)
            configurationFile.save(configuration())
    }
    function applyConfiguration(value): bool {
        if (!gimbalPage.applyConfiguration(value.gimbal)) return false
        cardPage.applyConfiguration(value.field, value.detector, value.environment)
        return true
    }
    function configuration() {
        const scene = cardPage.configuration()
        return { version: 1, gimbal: gimbalPage.configuration(), field: scene.field,
            detector: scene.detector, environment: scene.environment }
    }
    onReadyChanged: Qt.callLater(startPending)
    property Connections gimbalConfiguration: Connections {
        target: session.gimbalPage
        function onConfigurationChanged(): void {
            if (session.initialized) Qt.callLater(session.saveConfiguration)
        }
    }
    property Connections cardConfiguration: Connections {
        target: session.cardPage
        function onConfigurationChanged(): void {
            if (session.initialized) Qt.callLater(session.saveConfiguration)
        }
    }
    property Connections taskConnection: Connections {
        target: session.activeTask
        function onRunningChanged(): void { Qt.callLater(session.checkCompletion) }
    }
    property Connections fixedLog: Connections {
        target: session.fixedTask
        function onLogMessage(text): void { session.logMessage(text) }
    }
    property Connections cycleLog: Connections {
        target: session.cycleTask
        function onLogMessage(text): void { session.logMessage(text) }
    }
    property Connections snakeLog: Connections {
        target: session.snakeTask
        function onLogMessage(text): void { session.logMessage(text) }
    }
    property Connections gimbalLog: Connections {
        target: session.gimbalPage
        function onLogMessage(text): void { session.logMessage(text) }
    }
    property Connections cardLog: Connections {
        target: session.cardPage
        function onLogMessage(text): void { session.logMessage(text) }
    }
    property Connections configLog: Connections {
        target: session.configurationFile
        function onSaveFailed(text): void { session.cardPage.logMessage(text) }
    }
}
