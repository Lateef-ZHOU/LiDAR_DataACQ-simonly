#pragma once
#include <QObject>
#include <QQmlApplicationEngine>
#include <QUrl>
#include <QDebug>

// 启动壳只持有引擎；业务对象全部由各自 QML 官邸拥有。
class Workbench final : public QObject
{
    Q_OBJECT
public:
    explicit Workbench(const QVariantMap &properties = {}, QObject *parent = nullptr) : QObject(parent)
    {
        engine_.setInitialProperties(properties);
        engine_.load(QUrl(QStringLiteral("qrc:/qt/qml/Lidar/SimOnly/Workbench.qml")));
        if (ready()) {
            auto *root = engine_.rootObjects().front();
            connect(root, SIGNAL(exitRequested(int)), this, SIGNAL(exitRequested(int)));
            if (!properties.value("startupRequest").toMap().isEmpty())
                connect(root, SIGNAL(sessionLog(QString)), this, SLOT(printLog(QString)));
        }
    }
    Q_SLOT void cancel() { if (ready()) QMetaObject::invokeMethod(engine_.rootObjects().front(), "stopSession"); }
    Q_SIGNAL void exitRequested(int code);
    [[nodiscard]] bool ready() const { return !engine_.rootObjects().isEmpty(); }
private:
    Q_SLOT void printLog(const QString &message) { qInfo().noquote() << message; }
    QQmlApplicationEngine engine_;
};
