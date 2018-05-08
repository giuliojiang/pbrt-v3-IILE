#ifndef IILECONDITIONVARIABLE_H
#define IILECONDITIONVARIABLE_H

#include <thread>
#include <mutex>
#include <condition_variable>


class IileConditionVariable
{
private:
    std::mutex mutex;
    std::condition_variable cv;

public:
    IileConditionVariable();

    void wait()
    {
        std::unique_lock<std::mutex> lck (mutex);
        cv.wait(lck);
    }

    void notify()
    {
        cv.notify_all();
    }
};

#endif // IILECONDITIONVARIABLE_H
