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
    visible: startupRequest === null
    devicePages: [simGimbal, simCard]
    taskPages: [fixedTask, cycleTask, snakeTask]
    property SimulationConfig configurationFile: null
    property var initialConfiguration: null
    property var startupRequest: null
    signal exitRequested(int code)
    signal sessionLog(string message)
    function stopSession(): void { session.cancel() }

    SimGimbalSimOnlyModule { id: simGimbal }
    SimCardSimOnlyModule { id: simCard; gimbal: simGimbal.family }
    FixedTaskSimOnlyModule { id: fixedTask; gimbal: simGimbal.family; card: simCard.family }
    CycleTaskSimOnlyModule { id: cycleTask; gimbal: simGimbal.family; card: simCard.family }
    SnakeTaskSimOnlyModule { id: snakeTask; gimbal: simGimbal.family; card: simCard.family }
    SimulationSession {
        id: session
        gimbalPage: simGimbal
        cardPage: simCard
        fixedTask: fixedTask
        cycleTask: cycleTask
        snakeTask: snakeTask
        configurationFile: root.configurationFile
        initialConfiguration: root.initialConfiguration
        startupRequest: root.startupRequest
        onExitRequested: code => root.exitRequested(code)
        onLogMessage: message => root.sessionLog(message)
    }
    Component.onCompleted: Qt.callLater(function() { session.initialize(); root.initialConfiguration = null })
}
