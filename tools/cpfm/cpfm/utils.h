#ifndef UTILS_H
#define UTILS_H

#include <csignal>
#include <cstdlib>

static void terminate()
{
    std::exit(1);
    std::raise(SIGKILL);
}

#endif // UTILS_H
