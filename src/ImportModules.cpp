#include <QtQml/QQmlExtensionPlugin>
#include <QCoreApplication>
#include <QMetaType>
#include "Algorithm/Wind/VerticalWindProfile.h"

// 应用是处理线程与 QML 的接合点；按信号中的别名登记，算法库仍只依赖标准库。
static void registerApplicationTypes()
{
    qRegisterMetaType<VerticalWindProfilePtr>("VerticalWindProfilePtr");
}
Q_COREAPP_STARTUP_FUNCTION(registerApplicationTypes)

Q_IMPORT_QML_PLUGIN(LidarUIPlugin)
Q_IMPORT_QML_PLUGIN(LidarChartsPlugin)
Q_IMPORT_QML_PLUGIN(LidarTaskUIPlugin)
Q_IMPORT_QML_PLUGIN(LidarSimGimbalDevicePlugin)
Q_IMPORT_QML_PLUGIN(LidarSimCardDevicePlugin)
Q_IMPORT_QML_PLUGIN(LidarFixedTaskPlugin)
Q_IMPORT_QML_PLUGIN(LidarCycleTaskPlugin)
Q_IMPORT_QML_PLUGIN(LidarSnakeTaskPlugin)
