pragma ComponentBehavior: Bound
import QtQuick
import Lidar.UI
import Lidar.SimGimbal
import Lidar.SimCard
import Lidar.FixedTask
import Lidar.CycleTask
import Lidar.SnakeTask

WorkbenchWindow {
    id: root
    title: qsTr("LiDAR 数字样机 %1").arg(Qt.application.version)
    visible: !headless
    currentPage: startupRequest === null ? 0 : 1 // 自动采集时先展示虚拟卡的功率谱。
    devicePages: [simGimbal, simCard]
    taskPages: [fixedPage, cyclePage, snakePage]
    property SimulationConfig configurationFile: null
    property var initialConfiguration: null
    property var startupRequest: null
    property bool headless: false
    signal exitRequested(int code)
    signal sessionLog(string message)
    function stopSession(): void { session.cancel() }
    onClosing: root.stopSession()

    SimGimbalSimOnlyModule { id: simGimbal }
    SimCardSimOnlyModule { id: simCard; gimbal: simGimbal.family }
    // 参数在创建期交入；未选中的页面保留显式默认值，不自动启动。
    FixedTaskSimOnlyModule {
        id: fixedPage
        gimbal: simGimbal.family; card: simCard.family
        azimuths: root.startupRequest?.kind === "fixedAxis" ? root.startupRequest.azimuths : [0]
        elevation: root.startupRequest?.kind === "fixedAxis" ? root.startupRequest.elevation : 60
        accum: root.startupRequest?.kind === "fixedAxis" ? root.startupRequest.accumulate : settingsParameters.accumDefault
        settle: root.startupRequest?.kind === "fixedAxis" ? root.startupRequest.settle : settingsParameters.settleDefault
    }
    CycleTaskSimOnlyModule {
        id: cyclePage
        gimbal: simGimbal.family; card: simCard.family
        azimuths: root.startupRequest?.kind === "cycleAxis" ? root.startupRequest.azimuths : [0, 90, 180, 270]
        elevation: root.startupRequest?.kind === "cycleAxis" ? root.startupRequest.elevation : 60
        accum: root.startupRequest?.kind === "cycleAxis" ? root.startupRequest.accumulate : settingsParameters.accumDefault
        settle: root.startupRequest?.kind === "cycleAxis" ? root.startupRequest.settle : settingsParameters.settleDefault
    }
    SnakeTaskSimOnlyModule {
        id: snakePage
        gimbal: simGimbal.family; card: simCard.family
        azimuths: root.startupRequest?.kind === "snakeAxis" ? root.startupRequest.azimuths : [0, 90, 180, 270]
        elevation: root.startupRequest?.kind === "snakeAxis" ? root.startupRequest.elevation : 60
        accum: root.startupRequest?.kind === "snakeAxis" ? root.startupRequest.accumulate : settingsParameters.accumDefault
        settle: root.startupRequest?.kind === "snakeAxis" ? root.startupRequest.settle : settingsParameters.settleDefault
    }
    SimulationSession {
        id: session
        gimbalPage: simGimbal
        cardPage: simCard
        fixedTask: fixedPage
        cycleTask: cyclePage
        snakeTask: snakePage
        configurationFile: root.configurationFile
        initialConfiguration: root.initialConfiguration
        startupRequest: root.startupRequest
        headless: root.headless
        onExitRequested: code => root.exitRequested(code)
        onLogMessage: message => root.sessionLog(message)
    }
    Component.onCompleted: Qt.callLater(function() { session.initialize(); root.initialConfiguration = null })
}
