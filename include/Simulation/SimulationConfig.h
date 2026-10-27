#pragma once
#include <cmath>
#include <optional>
#include <QFile>
#include <QFileInfo>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonParseError>
#include <QObject>
#include <QSaveFile>
#include <QVariantMap>
#include <QStringList>
#include <QtQml/qqmlregistration.h>

// 仿真配置的文件边界：只持文件路径；运行参数仍归各自官邸，不保存第二份配置状态。
class SimulationConfig final : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_UNCREATABLE("由进程入口指定配置文件")
public:
    explicit SimulationConfig(QString path, QObject *parent = nullptr)
        : QObject(parent), path_(QFileInfo(path).absoluteFilePath()) {}
    [[nodiscard]] const QString &path() const { return path_; }
    [[nodiscard]] static QJsonObject defaults()
    {
        QFile file(QStringLiteral(":/simulation.example.json"));
        if (!file.open(QIODevice::ReadOnly)) return {};
        return QJsonDocument::fromJson(file.readAll()).object();
    }
    [[nodiscard]] std::optional<QVariantMap> load(bool createMissing, QString &error) const
    {
        QFile file(path_);
        if (!file.exists() && createMissing) {
            const auto initial = defaults();
            if (!write(initial, error)) return std::nullopt;
        }
        if (!file.open(QIODevice::ReadOnly)) { error = file.errorString(); return std::nullopt; }
        QJsonParseError parse;
        const auto document = QJsonDocument::fromJson(file.readAll(), &parse);
        if (parse.error != QJsonParseError::NoError || !document.isObject()) {
            error = QStringLiteral("JSON 格式错误：%1").arg(parse.errorString()); return std::nullopt;
        }
        if (!validate(document.object(), error)) return std::nullopt;
        return document.object().toVariantMap();
    }
    Q_INVOKABLE bool save(const QVariantMap &values) const
    {
        QString error;
        if (write(QJsonObject::fromVariantMap(values), error)) return true;
        Q_EMIT saveFailed(QStringLiteral("配置未保存：%1").arg(error));
        return false;
    }
    [[nodiscard]] static bool validate(const QJsonObject &object, QString &error)
    {
        const auto shape = defaults();
        if (shape.isEmpty()) { error = QStringLiteral("缺少内置配置样例"); return false; }
        if (!sameShape(object, shape, {}, error)) return false;
        struct Number { const char *path; double low, high; bool integer = false; };
        static constexpr Number rules[] = {
            {"version", 1, 1, true},
            {"gimbal.mounting.azimuthDeg", 0, 360}, {"gimbal.mounting.elevationDeg", -180, 180},
            {"gimbal.mounting.rollDeg", -180, 180}, {"gimbal.panSpeedDegS", .1, 120}, {"gimbal.tiltSpeedDegS", .1, 120},
            {"field.speedMS", 0, 100}, {"field.directionDeg", 0, 360}, {"field.verticalMS", -20, 20},
            {"field.speedGainMSPerKm", -50, 50}, {"field.directionGainDegPerKm", -180, 180}, {"field.topM", 10, 20000},
            {"field.swingSpeedMS", 0, 50}, {"field.swingDirectionDeg", 0, 180}, {"field.periodS", 1, 86400},
            {"field.rampSpeedMS", -50, 50}, {"field.rampDirectionDeg", -180, 180}, {"field.rampDurationS", 1, 86400},
            {"field.gustSpeedMS", 0, 20}, {"field.gustDirectionDeg", 0, 90}, {"field.gustScaleS", 1, 3600},
            {"detector.cnrAt1kmDb", -30, 60}, {"detector.extinctionDbPerKm", 0, 50},
            {"detector.overlapRangeM", 1, 5000}, {"detector.floorCounts", .1, 1000}, {"detector.peakWidthBins", .5, 50},
            {"detector.seed", 0, 2147483647, true}, {"detector.lowC", -80, 100}, {"detector.highC", -80, 100},
            {"detector.dbPerDegBelow", 0, 10}, {"detector.dbPerDegAbove", 0, 10}, {"environment.temperatureC", -60, 80}
        };
        for (const auto &rule : rules) {
            QJsonValue value(object);
            for (const auto &part : QString::fromLatin1(rule.path).split('.')) value = value.toObject().value(part);
            const double number = value.toDouble();
            if (!value.isDouble() || !std::isfinite(number) || number < rule.low || number > rule.high
                || (rule.integer && std::trunc(number) != number)) {
                error = QStringLiteral("%1 必须为 %2～%3 内的%4数值").arg(QLatin1String(rule.path))
                    .arg(rule.low).arg(rule.high).arg(rule.integer ? QStringLiteral("整数") : QString());
                return false;
            }
        }
        const auto field = object.value("field").toObject();
        if (!QStringList{"uniform", "linearShear"}.contains(field.value("kind").toString())
            || !QStringList{"steady", "swing", "ramp", "gust"}.contains(field.value("temporal").toString())) {
            error = QStringLiteral("field.kind 或 field.temporal 类型未知"); return false;
        }
        const auto detector = object.value("detector").toObject();
        if (detector.value("lowC").toDouble() > detector.value("highC").toDouble()) {
            error = QStringLiteral("detector.lowC 不能大于 detector.highC"); return false;
        }
        return true;
    }
Q_SIGNALS:
    void saveFailed(const QString &message) const;
private:
    static bool sameShape(const QJsonObject &value, const QJsonObject &shape, const QString &prefix, QString &error)
    {
        for (auto it = shape.begin(); it != shape.end(); ++it) {
            const auto path = prefix + it.key();
            if (!value.contains(it.key()) || value.value(it.key()).type() != it.value().type()) {
                error = path + QStringLiteral(" 缺失或类型错误"); return false;
            }
            if (it->isObject() && !sameShape(value.value(it.key()).toObject(), it->toObject(), path + '.', error)) return false;
        }
        for (auto it = value.begin(); it != value.end(); ++it)
            if (!shape.contains(it.key())) { error = prefix + it.key() + QStringLiteral(" 是未知配置项"); return false; }
        return true;
    }
    bool write(const QJsonObject &values, QString &error) const
    {
        if (!validate(values, error)) return false;
        QSaveFile file(path_);
        if (!file.open(QIODevice::WriteOnly)) { error = file.errorString(); return false; }
        const auto bytes = QJsonDocument(values).toJson(QJsonDocument::Indented);
        if (file.write(bytes) != bytes.size() || !file.commit()) { error = file.errorString(); return false; }
        return true;
    }
    const QString path_;
};
