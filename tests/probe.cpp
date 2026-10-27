#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQuickWindow>
#include <QQuickItem>
#include <QSignalSpy>
#include <QTest>
#include <QDir>
#include <QJsonArray>
#include "Device/GMB/Sim/SimGimbalDevice.h"
#include "Device/DAQ/Sim/SimCardDevice.h"
#include "Task/TaskBase.h"
#include "UI/Chart/Surface/SurfaceItem.h"


template<class T> QList<T *> visualItems(QQuickItem *root)
{
    QList<T *> result;
    if (auto *item = qobject_cast<T *>(root)) result.append(item);
    for (auto *child : root->childItems()) result.append(visualItems<T>(child));
    return result;
}
#include "runtime.h"
int main(int argc, char **argv)
{
    QGuiApplication app(argc, argv);
    app.setQuitOnLastWindowClosed(false);
    if (argc != 2) return 2;
    return runtimeProbe(QString::fromLocal8Bit(argv[1]));
}
