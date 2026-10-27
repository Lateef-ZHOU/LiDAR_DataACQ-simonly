// 使用实际 simonly 页面和同一后端，覆盖 JSON、八种风场、隐藏采样与取消。
#include <csignal>
#include <QThread>
#include "Simulation/SimulationConfig.h"
#include "Simulation/SimulationCommand.h"
#include "Simulation/ProcessSignals.h"

inline int runtimeProbe(const QString &directory)
{
    QDir output(directory);
    if (!output.mkpath(".") || !QDir::setCurrent(output.absolutePath())) return 2;
    QJsonArray checks;
    int failures = 0;
    const auto check = [&](const char *name, bool ok) {
        checks.append(QJsonObject{{"name", name}, {"passed", ok}});
        qInfo() << (ok ? "PASS" : "FAIL") << name;
        failures += !ok;
    };
    QString error;
    SimulationConfig config(output.absoluteFilePath("simulation.json"));
    auto initial = config.load(true, error);
    check("default JSON created and validated", initial.has_value());
    if (!initial) return 2;
    SimulationConfig missing(output.absoluteFilePath("missing.json"));
    check("explicit missing JSON rejected", !missing.load(false, error));
    const auto readBytes = [&] { QFile f(config.path()); if (!f.open(QIODevice::ReadOnly)) return QByteArray{}; return f.readAll(); };
    const auto original = readBytes();
    auto invalid = *initial;
    invalid.insert("unknown", true);
    check("unknown key rejected without replacing file", !config.save(invalid) && readBytes() == original);
    invalid = *initial;
    auto detector = invalid.value("detector").toMap(); detector["seed"] = 1.5; invalid["detector"] = detector;
    check("fractional seed rejected", !config.save(invalid) && readBytes() == original);
    detector["seed"] = 1; detector["lowC"] = 50; detector["highC"] = 20; invalid["detector"] = detector;
    check("inverted temperature bounds rejected", !config.save(invalid));
    auto field = initial->value("field").toMap(); field["temporal"] = "unknown";
    invalid = *initial; invalid["field"] = field;
    check("unknown wind type rejected", !config.save(invalid));
    const auto parsed = SimulationCommand::parse({"sim", "--fixedAxis", "60", "15", "--accumulate", "2", "--settle", "3"}, error);
    check("CLI elevation precedes azimuth and timings separated", parsed && parsed->task.value("elevation").toDouble() == 60
        && parsed->task.value("azimuths").toList()[0].toDouble() == 15
        && parsed->task.value("accumulate").toInt() == 2 && parsed->task.value("settle").toInt() == 3);
    for (const auto &args : QList<QStringList>{
        {"sim", "--fixedAxis", "nan", "0"}, {"sim", "--fixedAxis", "60"},
        {"sim", "--fixedAxis", "60", "0", "--cycleAxis", "60", "0", "90", "180", "270"},
        {"sim", "--fixedAxis", "60", "0", "--accumulate", "0"},
        {"sim", "--fixedAxis", "60", "0", "--settle", "1"},
        {"sim", "--fixedAxis", "60", "0", "--accumulate", "1", "--accumulate", "2"},
        {"sim", "--accumulate", "2"}, {"sim", "--fixedAxix", "60", "0"}})
        check("invalid CLI rejected", !SimulationCommand::parse(args, error));
    {
        QQmlApplicationEngine engine;
        engine.setInitialProperties({{"visible", false}, {"configurationFile", QVariant::fromValue(&config)}, {"initialConfiguration", *initial}});
        engine.loadFromModule("Lidar.SimOnly", "Workbench");
        if (engine.rootObjects().isEmpty()) return 2;
        auto *root = engine.rootObjects().front();
        auto *hub = root->findChild<QObject *>("SimulationSession");
        auto *gimbalModule = root->findChild<QObject *>("SimGimbalSimOnlyModule");
        auto *cardModule = root->findChild<QObject *>("SimCardSimOnlyModule");
        auto *gimbal = gimbalModule->findChild<SimGimbalDevice *>();
        auto *card = cardModule->findChild<SimCardDevice *>();
        check("configuration editor devices ready", QTest::qWaitFor([&] { return gimbal->device().isOpen() && card->device().isOpen(); }, 5000));
        auto settings = *initial;
        auto g = settings["gimbal"].toMap(); g["panSpeedDegS"] = 45; g["tiltSpeedDegS"] = 35; settings["gimbal"] = g;
        auto d = settings["detector"].toMap();
        d["cnrAt1kmDb"] = 15; d["extinctionDbPerKm"] = 3; d["overlapRangeM"] = 400;
        d["floorCounts"] = 4; d["peakWidthBins"] = 4; d["seed"] = 19;
        d["lowC"] = -15; d["highC"] = 35; d["dbPerDegBelow"] = .4; d["dbPerDegAbove"] = .6;
        settings["detector"] = d; settings["environment"] = QVariantMap{{"temperatureC", 25}};
        auto f = settings["field"].toMap();
        f["speedMS"] = 11; f["directionDeg"] = 240; f["verticalMS"] = 1;
        f["speedGainMSPerKm"] = 4; f["directionGainDegPerKm"] = 25; f["topM"] = 2500;
        f["swingSpeedMS"] = 2; f["swingDirectionDeg"] = 15; f["periodS"] = 45;
        f["rampSpeedMS"] = 3; f["rampDirectionDeg"] = 75; f["rampDurationS"] = 400;
        f["gustSpeedMS"] = 2; f["gustDirectionDeg"] = 12; f["gustScaleS"] = 25;
        for (const auto *kind : {"uniform", "linearShear"})
            for (const auto *temporal : {"steady", "swing", "ramp", "gust"}) {
                f["kind"] = kind; f["temporal"] = temporal; settings["field"] = f;
                bool accepted = false;
                const bool invoked = QMetaObject::invokeMethod(hub, "applyConfiguration", Q_RETURN_ARG(bool, accepted), Q_ARG(QVariant, settings));
                check("all field and temporal configurations accepted", invoked && accepted);
                check("QML edits persisted including inactive type parameters", QTest::qWaitFor([&] {
                    auto saved = config.load(false, error);
                    return saved && QJsonObject::fromVariantMap(*saved) == QJsonObject::fromVariantMap(settings);
                }, 2000));
            }
        check("configuration change not a task", !gimbal->device().isLocked() && !card->device().isLocked());
    }
    // 新引擎从 JSON 恢复，无窗口运行；先累积后停止，验证已有取消链及锁释放。
    for (const auto *kind : {"fixedAxis", "cycleAxis", "snakeAxis"}) {
        auto saved = config.load(false, error);
        if (!saved) return 2;
        QVariantList azimuths = QString::fromLatin1(kind) == "fixedAxis" ? QVariantList{15.0} : QVariantList{15.0, 105.0, 195.0, 285.0};
        const QVariantMap request{{"kind", kind}, {"elevation", 55.0}, {"azimuths", azimuths}, {"accumulate", 1}, {"settle", 3}};
        QQmlApplicationEngine engine;
        engine.setInitialProperties({{"configurationFile", QVariant::fromValue(&config)}, {"initialConfiguration", *saved}, {"startupRequest", request}});
        engine.loadFromModule("Lidar.SimOnly", "Workbench");
        if (engine.rootObjects().isEmpty()) return 2;
        auto *root = engine.rootObjects().front();
        auto *card = root->findChild<SimCardDevice *>();
        auto *gimbal = root->findChild<SimGimbalDevice *>();
        const auto taskName = QString::fromLatin1(kind).replace("Axis", "");
        QString moduleName = taskName; moduleName[0] = moduleName[0].toUpper(); moduleName += "TaskSimOnlyModule";
        auto *module = root->findChild<QObject *>(moduleName);
        auto *task = module->findChild<TaskBase *>();
        // 在处理任何排队初始化/连接消息之前，页面必须已经显示命令行给出的值。
        auto *plan = module->property("planPage").value<QObject *>();
        const auto angleProperty = plan->property("azimuths");
        const auto uiAngles = angleProperty.metaType() == QMetaType::fromType<QJSValue>()
            ? angleProperty.value<QJSValue>().toVariant().toList() : angleProperty.toList();
        check("CLI parameters initialize the plan during construction",
            plan->property("elevation").toDouble() == request.value("elevation").toDouble()
            && uiAngles == azimuths && module->property("accum").toInt() == 1
            && module->property("settle").toInt() == 3 && !task->running());
        check("task commands are parameterless", module->metaObject()->indexOfMethod("start()") >= 0
            && module->metaObject()->indexOfMethod("stop()") >= 0);
        check("CLI window stays hidden", !root->property("visible").toBool());
        QSignalSpy swaps(qobject_cast<QQuickWindow *>(root), &QQuickWindow::frameSwapped);
        QSignalSpy spectra(card, &SimCardDevice::specReady);
        check("automatic task start after device readiness", QTest::qWaitFor([&] { return task->running(); }, 5000));
        check("persisted scene restored before sampling", card->seed() == 19 && card->temperature() == 25
            && static_cast<WindFieldSource *>(card->fieldSource())->temporal() == 3);
        check("headless angle and scene histories produce spectrum", QTest::qWaitFor([&] { return !spectra.empty(); }, 15000));
        const auto surfaces = visualItems<SurfaceItem>(qobject_cast<QQuickWindow *>(root)->contentItem());
        check("hidden task receives spectra without rendering or preparing surfaces", swaps.empty() && !surfaces.empty()
            && std::all_of(surfaces.begin(), surfaces.end(), [](auto *surface) { return surface->surface().revision == 0; }));
        const auto persisted = readBytes();
        ProcessSignals signals;
        bool mainThread = false;
        QObject::connect(&signals, &ProcessSignals::requested, root, [&, root](int code) {
            mainThread = code == SIGTERM && QThread::currentThread() == qApp->thread();
            QMetaObject::invokeMethod(root, "stopSession");
        });
        QSignalSpy exited(root, SIGNAL(exitRequested(int)));
        std::raise(SIGTERM);
        check("SIGTERM delivered to main thread", QTest::qWaitFor([&] { return mainThread; }, 1000));
        check("cancel before event loop exit and release locks", !task->running() && !card->device().isLocked() && !gimbal->device().isLocked()
            && exited.count() == 1 && exited[0][0].toInt() == 0);
        check("CLI does not rewrite settings", readBytes() == persisted);
    }
    QFile report(output.absoluteFilePath("runtime-results.json"));
    if (!report.open(QIODevice::WriteOnly)) return 2;
    report.write(QJsonDocument(QJsonObject{{"failures", failures}, {"checks", checks}}).toJson());
    return failures ? 1 : 0;
}
