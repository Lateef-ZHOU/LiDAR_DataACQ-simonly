#pragma once
#include <cmath>
#include <optional>
#include <QVariantMap>
#include <QStringList>

// 只描述一次进程启动；任务配置按值交给已有 QML 官邸，不进入 JSON。
struct SimulationCommand
{
    QString config = QStringLiteral("simulation.json");
    bool explicitConfig = false;
    bool help = false, version = false;
    bool headless = false;
    QVariantMap task;

    static QString usage()
    {
        return QStringLiteral(
            "LiDAR_DataACQ [--config FILE] [--headless] [TASK --accumulate SECONDS --settle SECONDS]\n"
            "  --fixedAxis HEIGHT AZIMUTH\n"
            "  --cycleAxis HEIGHT AZIMUTH1 AZIMUTH2 AZIMUTH3 AZIMUTH4\n"
            "  --snakeAxis HEIGHT AZIMUTH1 AZIMUTH2 AZIMUTH3 AZIMUTH4\n"
            "Angles: world coordinates in degrees; height first.\n"
            "--accumulate: 1..3600 s (default 10); --settle: 2..600 s (default 2).\n"
            "No TASK: open the configuration UI and persist edits to JSON.\n"
            "With TASK: show UI and start automatically when devices are ready; save to current directory.\n"
            "--headless: run TASK without a window (requires TASK).\n"
            "Close window / Ctrl+C / SIGTERM: stop tasks, then exit.\n"
            "Default config: ./simulation.json (created if missing). Explicit FILE must exist.\n"
            "  --help  --version\n");
    }
    static std::optional<SimulationCommand> parse(const QStringList &args, QString &error)
    {
        SimulationCommand result;
        QStringList seen;
        int accumulate = 10, settle = 2;
        const auto fail = [&](const QString &reason) -> std::optional<SimulationCommand> { error = reason; return std::nullopt; };
        for (qsizetype i = 1; i < args.size(); ++i) {
            const auto option = args[i];
            if (seen.contains(option)) return fail(QStringLiteral("重复参数：") + option);
            seen.append(option);
            if (option == "--help" || option == "-h") { result.help = true; continue; }
            if (option == "--version") { result.version = true; continue; }
            if (option == "--headless") { result.headless = true; continue; }
            if (option == "--config") {
                if (++i >= args.size() || args[i].isEmpty() || args[i].startsWith("--")) return fail(QStringLiteral("--config 缺少文件名"));
                result.config = args[i]; result.explicitConfig = true; continue;
            }
            if (option == "--accumulate" || option == "--settle") {
                if (++i >= args.size()) return fail(option + QStringLiteral(" 缺少秒数"));
                bool ok = false;
                const auto seconds = args[i].toInt(&ok);
                const bool accumulation = option == "--accumulate";
                if (!ok || seconds < (accumulation ? 1 : 2) || seconds > (accumulation ? 3600 : 600))
                    return fail(option + QStringLiteral(" 秒数非法或超限"));
                (accumulation ? accumulate : settle) = seconds;
                continue;
            }
            if (option == "--fixedAxis" || option == "--cycleAxis" || option == "--snakeAxis") {
                if (!result.task.isEmpty()) return fail(QStringLiteral("一次只能指定一种采集任务"));
                const int beams = option == "--fixedAxis" ? 1 : 4;
                if (args.size() - i - 1 < beams + 1) return fail(option + QStringLiteral(" 需要高度角及对应束数的方位角"));
                QVariantList azimuths;
                double elevation = 0;
                for (int a = 0; a <= beams; ++a) {
                    bool ok = false;
                    const auto angle = args[++i].toDouble(&ok);
                    if (!ok || !std::isfinite(angle) || angle < (a == 0 ? -180 : 0) || angle > (a == 0 ? 180 : 360))
                        return fail(option + QStringLiteral(" 角度非法或超限"));
                    if (a == 0) elevation = angle;
                    else azimuths.append(angle);
                }
                result.task = {{"kind", option.mid(2)}, {"elevation", elevation}, {"azimuths", azimuths}};
                continue;
            }
            return fail(QStringLiteral("未知参数：") + option);
        }
        if (result.task.isEmpty() && (seen.contains("--accumulate") || seen.contains("--settle")))
            return fail(QStringLiteral("时间参数必须与采集任务一起指定"));
        if (result.headless && result.task.isEmpty() && !result.help && !result.version)
            return fail(QStringLiteral("--headless 必须与采集任务一起指定"));
        if (!result.task.isEmpty()) { result.task.insert("accumulate", accumulate); result.task.insert("settle", settle); }
        return result;
    }
};
