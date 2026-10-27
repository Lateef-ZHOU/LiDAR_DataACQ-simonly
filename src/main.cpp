#include <cstdlib>
#include <cstring>
#include <QFont>
#include <QGuiApplication>
#include <QSurfaceFormat>
#include <QQuickWindow>
#include <QTextStream>

#include "Simulation/SimulationCommand.h"
#include "Simulation/SimulationConfig.h"
#include "Simulation/ProcessSignals.h"
#include "UI/Workbench/Workbench.h"

int main(int argc, char *argv[])
{
    // 只有显式无窗口模式和信息查询选择离屏；任务参数本身不决定显示方式。
    for (int i = 1; i < argc; ++i)
        if (!std::strcmp(argv[i], "--headless") || !std::strcmp(argv[i], "--help") ||
            !std::strcmp(argv[i], "-h") || !std::strcmp(argv[i], "--version")) {
            if (qEnvironmentVariableIsEmpty("QT_QPA_PLATFORM")) qputenv("QT_QPA_PLATFORM", "offscreen");
        }
    qputenv("QT_FORCE_STDERR_LOGGING", "1");
#ifdef Q_OS_WIN
    QQuickWindow::setGraphicsApi(QSGRendererInterface::Direct3D11);
#endif
    QSurfaceFormat surface = QSurfaceFormat::defaultFormat();
    surface.setSamples(4);
    QSurfaceFormat::setDefaultFormat(surface);
    QGuiApplication app(argc, argv);
    QGuiApplication::setApplicationVersion(QStringLiteral(LIDAR_VERSION_STRING));
    QGuiApplication::setFont(QFont(QStringLiteral(LIDAR_FONT_FAMILY)));
    app.setQuitOnLastWindowClosed(false);

    QString error;
    auto command = SimulationCommand::parse(app.arguments(), error);
    if (!command) { QTextStream(stderr) << error << Qt::endl; return EXIT_FAILURE; }
    if (command->help) { QTextStream(stdout) << SimulationCommand::usage(); return EXIT_SUCCESS; }
    if (command->version) { QTextStream(stdout) << app.applicationVersion() << Qt::endl; return EXIT_SUCCESS; }
    // 窗口关闭与系统信号均先经 QML stopSession 撤单，再主动退出事件循环。
    SimulationConfig config(command->config);
    auto initial = config.load(!command->explicitConfig, error);
    if (!initial) { QTextStream(stderr) << error << Qt::endl; return EXIT_FAILURE; }
    // 信号桥先于设备创建、晚于设备销毁；系统回调不执行 Qt 或业务操作。
    ProcessSignals signals;
    if (!signals.ready()) { QTextStream(stderr) << "Cannot install termination handlers\n"; return EXIT_FAILURE; }
    QVariantMap properties{{"configurationFile", QVariant::fromValue(&config)}, {"initialConfiguration", *initial},
                           {"headless", command->headless}};
    if (!command->task.isEmpty()) properties.insert("startupRequest", command->task);
    Workbench workbench(properties);
    initial.reset();
    properties.clear();
    command.reset();
    if (!workbench.ready()) return EXIT_FAILURE;
    QObject::connect(&signals, &ProcessSignals::requested, &workbench, &Workbench::cancel);
    QObject::connect(&workbench, &Workbench::exitRequested, &app, &QCoreApplication::exit);
    return QGuiApplication::exec();
}
