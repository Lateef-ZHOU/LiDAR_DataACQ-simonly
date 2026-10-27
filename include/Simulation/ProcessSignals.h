#pragma once
#include <atomic>
#include <csignal>
#include <QObject>
#include <QTimer>
#ifdef Q_OS_WIN
#include <qt_windows.h>
#endif

// 系统回调只写进程级无锁邮箱；Qt 主线程取走通知，再调用现有任务取消链。
// 邮箱不借用 QObject，已在途的系统回调不会访问析构中的对象。进程只创建一份接收器。
class ProcessSignals final : public QObject
{
    Q_OBJECT
public:
    explicit ProcessSignals(QObject *parent = nullptr) : QObject(parent)
    {
        static_assert(std::atomic<int>::is_always_lock_free);
        pending_.store(0);
        oldInt_ = std::signal(SIGINT, &receive);
        oldTerm_ = std::signal(SIGTERM, &receive);
#ifdef Q_OS_WIN
        SetConsoleCtrlHandler(nullptr, FALSE);
        consoleRegistered_ = SetConsoleCtrlHandler(&consoleEvent, TRUE) != FALSE;
#endif
        connect(&poll_, &QTimer::timeout, this, [this] {
            if (const int code = pending_.exchange(0); code != 0) Q_EMIT requested(code);
        });
        poll_.start(25);
    }
    ~ProcessSignals() override
    {
        poll_.stop();
#ifdef Q_OS_WIN
        if (consoleRegistered_) SetConsoleCtrlHandler(&consoleEvent, FALSE);
#endif
        if (oldInt_ != SIG_ERR) std::signal(SIGINT, oldInt_);
        if (oldTerm_ != SIG_ERR) std::signal(SIGTERM, oldTerm_);
    }
    [[nodiscard]] bool ready() const noexcept { return oldInt_ != SIG_ERR && oldTerm_ != SIG_ERR; }
Q_SIGNALS:
    void requested(int code);
private:
    static void receive(const int code) noexcept { pending_.store(code, std::memory_order_relaxed); }
#ifdef Q_OS_WIN
    static BOOL WINAPI consoleEvent(const DWORD event) noexcept
    {
        if (event != CTRL_C_EVENT && event != CTRL_BREAK_EVENT) return FALSE;
        receive(SIGINT);
        return TRUE;
    }
    bool consoleRegistered_ = false;
#endif
    inline static std::atomic<int> pending_{0};
    using Handler = void (*)(int);
    Handler oldInt_ = SIG_DFL, oldTerm_ = SIG_DFL;
    QTimer poll_;
};
